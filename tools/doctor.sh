#!/usr/bin/env bash
# pubmed-reference-resolver 環境診断
#
# 新しいパソコンでのセットアップ後、または動かなくなったときに実行する。
# API キーの値は表示しない。
#
# 使い方:
#   tools/doctor.sh            全項目 (外部 API への疎通確認を含む)
#   tools/doctor.sh --offline  外部通信を行わない
#
# 終了コード: 0 = 問題なし (警告のみ含む) / 1 = 要対処の問題あり

set -u

OFFLINE=0
for arg in "$@"; do
  case "$arg" in
    --offline) OFFLINE=1 ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "不明な引数: $arg" >&2; exit 2 ;;
  esac
done

# --- リポジトリの場所 (このスクリプトの実体から逆算、symlink 経由でも可) ---
src="$0"
while [ -L "$src" ]; do
  dir="$(cd -P "$(dirname "$src")" && pwd)"
  src="$(readlink "$src")"
  case "$src" in /*) ;; *) src="$dir/$src" ;; esac
done
REPO="$(cd -P "$(dirname "$src")/.." && pwd)"
PY="$REPO/.venv/bin/python"
SKILL_LINK="$HOME/.claude/skills/pubmed-reference-resolver"
ENV_FILE="$HOME/.pubmed-reference-resolver.env"

if [ -t 1 ]; then
  C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_NG=$'\033[31m'; C_B=$'\033[1m'; C_0=$'\033[0m'
else
  C_OK=; C_WARN=; C_NG=; C_B=; C_0=
fi

FAIL=0
WARN=0
ok()   { printf '  %s✔%s %s\n' "$C_OK" "$C_0" "$1"; }
warn() { printf '  %s⚠%s %s\n' "$C_WARN" "$C_0" "$1"; [ -n "${2:-}" ] && printf '      → %s\n' "$2"; WARN=$((WARN + 1)); }
ng()   { printf '  %s✘%s %s\n' "$C_NG" "$C_0" "$1"; [ -n "${2:-}" ] && printf '      → %s\n' "$2"; FAIL=$((FAIL + 1)); }
section() { printf '\n%s[%s]%s\n' "$C_B" "$1" "$C_0"; }

echo "pubmed-reference-resolver doctor"
echo "リポジトリ: $REPO"

# --- 1. Python 環境 ---
section "1. Python 環境"
if command -v uv >/dev/null 2>&1; then
  ok "uv: $(uv --version 2>/dev/null)"
else
  ng "uv が見つからない" "brew install uv  (または https://docs.astral.sh/uv/ の手順)"
fi

PY_OK=0
if [ -x "$PY" ]; then
  if "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
    ok ".venv の Python: $("$PY" --version 2>&1)"
    PY_OK=1
  else
    ng ".venv の Python が 3.11 未満: $("$PY" --version 2>&1)" "cd \"$REPO\" && rm -rf .venv && uv sync --frozen"
  fi
else
  ng ".venv が無い" "cd \"$REPO\" && uv sync --frozen"
fi

if [ "$PY_OK" = 1 ]; then
  missing="$("$PY" - <<'EOF'
import importlib.util as u
mods = ["pypdf", "docx", "rapidfuzz", "yaml", "requests", "tenacity", "anthropic", "certifi"]
print(" ".join(m for m in mods if u.find_spec(m) is None))
EOF
)"
  if [ -z "$missing" ]; then
    ok "依存ライブラリ 8 件すべて導入済み"
  else
    ng "依存ライブラリ不足: $missing" "cd \"$REPO\" && uv sync --frozen"
  fi

  if (cd "$REPO" && "$PY" -c 'import main, journal_audit, mdpi_parser, three_class_classifier, crossref_check, nlm_catalog_check' >/dev/null 2>&1); then
    ok "本体モジュール 6 件を読み込み可能"
  else
    ng "本体モジュールの読み込みに失敗" "cd \"$REPO\" && .venv/bin/python -c 'import main' でエラー内容を確認"
  fi
fi

if command -v uv >/dev/null 2>&1 && [ -f "$REPO/uv.lock" ]; then
  if (cd "$REPO" && uv lock --check >/dev/null 2>&1); then
    ok "uv.lock は pyproject.toml と一致"
  else
    warn "uv.lock が pyproject.toml と一致しない" "cd \"$REPO\" && uv lock && uv sync"
  fi
fi

# --- 2. API キー ---
section "2. API キー"
if [ -f "$ENV_FILE" ]; then
  perm="$(stat -f '%Lp' "$ENV_FILE" 2>/dev/null || stat -c '%a' "$ENV_FILE" 2>/dev/null)"
  if [ "$perm" = "600" ]; then
    ok "$ENV_FILE (権限 600)"
  else
    warn "$ENV_FILE の権限が $perm" "chmod 600 \"$ENV_FILE\""
  fi
  for key in ANTHROPIC_API_KEY NCBI_API_KEY; do
    if grep -Eq "^${key}=['\"]?[^'\"[:space:]]+" "$ENV_FILE"; then
      ok "$key が設定されている (値は非表示)"
    elif [ "$key" = ANTHROPIC_API_KEY ]; then
      ng "$key が未設定または空" "$ENV_FILE に ${key}=... を追記 (MDPI 以外の参照の構造化に必須)"
    else
      warn "$key が未設定または空" "任意。設定すると PubMed 検索が 3→10 req/sec に高速化"
    fi
  done
else
  ng "$ENV_FILE が無い" "cp \"$REPO/.env.example\" \"$ENV_FILE\" && chmod 600 \"$ENV_FILE\" し、キーを記入 (docs/operations/SETUP_API_KEYS.md)"
fi

for stray in "$REPO/skill_package/.env" "$REPO/.env"; do
  [ -f "$stray" ] && warn "別の .env がある: $stray" "キーの管理場所を $ENV_FILE に一本化することを推奨"
done

if [ "$PY_OK" = 1 ]; then
  # 実際のローダーで、cwd に依存せず読み込めるかを確認 (キー名のみ出力)
  loaded="$(cd / && env -u ANTHROPIC_API_KEY -u NCBI_API_KEY "$PY" - "$REPO" <<'EOF' 2>/dev/null
import os, sys
sys.path.insert(0, sys.argv[1])
import main
main.load_env_files(None)
print(" ".join(k for k in ("ANTHROPIC_API_KEY", "NCBI_API_KEY") if os.environ.get(k)))
EOF
)"
  case " $loaded " in
    *" ANTHROPIC_API_KEY "*) ok "main.py のローダーで読み込み確認 (cwd=/): $loaded" ;;
    *) ng "main.py のローダーで ANTHROPIC_API_KEY を読み込めない" "$ENV_FILE の書式 (KEY=VALUE) を確認" ;;
  esac
fi

# --- 3. スキル登録 ---
section "3. Claude Code スキル登録"
if [ -L "$SKILL_LINK" ]; then
  target="$(cd -P "$SKILL_LINK" 2>/dev/null && pwd)"
  if [ "$target" = "$REPO/skill_package" ]; then
    ok "$SKILL_LINK → skill_package"
  else
    ng "symlink の向き先が違う: ${target:-(リンク切れ)}" "ln -sfn \"$REPO/skill_package\" \"$SKILL_LINK\""
  fi
elif [ -e "$SKILL_LINK" ]; then
  warn "$SKILL_LINK が symlink ではない (コピー)" "更新が反映されないため symlink に置換を推奨: 退避後 ln -s \"$REPO/skill_package\" \"$SKILL_LINK\""
else
  ng "スキルが登録されていない" "mkdir -p \"$HOME/.claude/skills\" && ln -s \"$REPO/skill_package\" \"$SKILL_LINK\""
fi
for f in SKILL.md main.py journal_audit.py mdpi_parser.py manual_overrides.yaml; do
  [ -e "$REPO/skill_package/$f" ] || ng "skill_package/$f が無い、またはリンク切れ" "cd \"$REPO\" && git status / git checkout -- skill_package"
done

# --- 4. 動作確認 (オフライン) ---
section "4. 動作確認 (Phase 1、外部通信なし)"
SAMPLE="$REPO/skill_package/examples/sample_reference_section.pdf"
if [ "$PY_OK" = 1 ] && [ -f "$SAMPLE" ]; then
  tmp="$(mktemp -d)"
  if (cd / && "$PY" "$REPO/main.py" "$SAMPLE" -o "$tmp" --phase 1 --no-env-file --quiet >"$tmp/log.txt" 2>&1) \
     && [ -s "$tmp/phase1_intermediate.json" ]; then
    ok "サンプル PDF の抽出に成功"
  else
    ng "サンプル PDF の抽出に失敗" "ログ: $tmp/log.txt"
    tmp=""
  fi
  [ -n "$tmp" ] && rm -rf "$tmp"
else
  warn "スキップ (.venv またはサンプル PDF が無い)"
fi

# --- 5. 外部 API 疎通 ---
section "5. 外部 API 疎通"
if [ "$OFFLINE" = 1 ]; then
  echo "  (--offline のためスキップ)"
else
  probe() {  # name url expect(2xx|any)
    code="$(curl -s -o /dev/null -m 15 -w '%{http_code}' "$2")"
    if [ "$code" = 000 ] || [ -z "$code" ]; then
      warn "$1 に接続できない" "ネットワーク/プロキシ設定を確認。該当 Phase が失敗する"
    elif [ "$3" = any ] || [ "${code#2}" != "$code" ]; then
      ok "$1 (HTTP $code)"
    else
      warn "$1 が異常応答 (HTTP $code)" "サービス障害の可能性。時間をおいて再実行"
    fi
  }
  probe "NCBI E-utilities (Phase 3)" "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi?db=pubmed&retmode=json" 2xx
  probe "Crossref (Phase 4)" "https://api.crossref.org/works/10.1136/bmj.n160" 2xx
  probe "NLM Catalog (Phase 4)" "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nlmcatalog&term=BMJ&retmode=json" 2xx
  # ルートは 404 を返すため到達性のみ確認 (キーの有効性は課金を避けて検証しない)
  probe "Anthropic API (Phase 2、到達性のみ)" "https://api.anthropic.com/" any
fi

# --- 結果 ---
printf '\n'
if [ "$FAIL" -gt 0 ]; then
  printf '%s要対処 %d 件%s / 警告 %d 件。→ の手順で直してから再実行してください。\n' "$C_NG" "$FAIL" "$C_0" "$WARN"
  exit 1
fi
printf '%s問題なし%s (警告 %d 件)\n' "$C_OK" "$C_0" "$WARN"
exit 0
