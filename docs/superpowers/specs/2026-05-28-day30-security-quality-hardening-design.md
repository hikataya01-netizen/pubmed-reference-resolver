# Day30: セキュリティ・品質強化 (3 本立て) — 設計仕様 (Design Spec)

**作成日**: 2026-05-28
**対象セッション**: Day30
**前提セッション**: Day29 (pre-commit gitleaks 3 層防御導入)
**起点 commit**: `3b3bdaa` (Day29 archive)

---

## §1 背景と目的

### §1.1 Day29 で構築した基盤

Day29 で機密データ commit 事故 (Day23) の再発防止のため、3 層防御 (Local
pre-commit hook + CI gitleaks job + history audit) を導入した。Day29 LESSONS
§5 で Top priority として 3 候補を残した。

### §1.2 Day30 で扱う 3 候補

| # | 候補 | Day29 LESSONS での位置づけ |
|:---:|:---|:---|
| A | smoke test 自動化 | Top priority #1 (gitleaks rule 変更時の回帰検知) |
| B | 追加 pre-commit hook | Top priority #2 (style 統一による diff ノイズ削減) |
| C | SECURITY.md 整備 | Top priority #3 (PyPI 公開前提の脆弱性報告窓口) |

3 候補はいずれも小規模で「Day29 の仕上げ」としてテーマが一貫しているため、
1 セッションで 3 Task として実装する。

### §1.3 目的

1. **回帰防止**: gitleaks の secret 検出能力を pytest で永続的に保証する
2. **品質統一**: end-of-file / trailing-whitespace / yaml / toml の機械的検証を自動化
3. **公開準備**: 脆弱性報告の正式窓口 (GitHub Security Advisories) を整備

---

## §2 設計上の Question と採用案

### §2.1 Q1: scope

| Option | 概要 | 採用可否 |
|:---|:---|:---:|
| **(A) 3 候補すべて** ✓ | 1 セッションで 3 Task、commit 分割 | **採用** |
| (B) smoke test のみ | 設計論点が深い 1 件に集中 | ✕ |
| (C) hook + SECURITY.md | smoke を除く 2 件 | ✕ |
| (D) SECURITY.md のみ | 最小スコープ | ✕ |

**採用根拠**: 3 候補とも小規模かつテーマ一貫。Day28/29 の workflow (spec →
plan → subagent-driven) で 3 Task を順次処理可能。

### §2.2 Q2: smoke test の実装方式

| Option | 概要 | 採用可否 |
|:---|:---|:---:|
| **(I) pre-commit run 経由** ✓ | `subprocess.run(["uv","run","pre-commit","run","gitleaks","--files",tmp])` | **採用** |
| (II) gitleaks CLI 直接 | binary path 解決が必要、環境依存増 | ✕ |
| (III) CI 専用 step | pytest 外、ローカル回帰 guard にならない | ✕ |

**採用根拠**:
- pre-commit framework に binary 管理を委ねられ CLAUDE.md §8 (uv 統一) と整合
- gitleaks binary 不在環境では `pytest.mark.skipif` で skip
- Day29 で `uv run pre-commit run gitleaks` の動作実績あり

### §2.3 Q3: 追加 hook 導入時の既存違反の扱い

| Option | 概要 | 採用可否 |
|:---|:---|:---:|
| **(α) fixture exclude + 一括修正** ✓ | tests/fixtures/ を exclude、それ以外を `--all-files` で一括 auto-fix | **採用** |
| (β) fixture exclude + 既存触らない | hook 追加のみ、段階的修正 | ✕ |
| (γ) 広く exclude | integration ゴールド等も exclude、適用を .py/docs に限定 | ✕ |

**採用根拠**:
- `tests/fixtures/` には byte 単位一致を検証する golden fixture (MDPI 173refs
  等) があり、auto-fix が走ると integration test が壊れる → **exclude 必須**
- 既存違反 (fixture 外 ~30 ファイル) を一括修正することで以降の diff がクリーン
- 機能追加 (hook) と機械的修正 (style) を別 commit に分離

**実測 (起点 `3b3bdaa`)**:
- trailing whitespace 含むファイル: 10
- 末尾改行なしファイル: 25 (概算)
- tracked 総数: 207
- yaml/toml ファイル: 5 (.github/workflows/tests.yml, .pre-commit-config.yaml,
  integration/src/manual_overrides.yaml, pyproject.toml,
  skill_package/manual_overrides.yaml)

### §2.4 Q4: SECURITY.md の脆弱性報告先

| Option | 概要 | 採用可否 |
|:---|:---|:---:|
| **(♦) GitHub Security Advisories** ✓ | private vulnerability reporting、非公開報告 | **採用** |
| (♥) email 連絡先記載 | 公開 repo に個人 email 露出 (spam リスク) | ✕ |
| (♣) 両方併記 | 冗長 | ✕ |

**採用根拠**: GitHub Security Advisories は脆弱性を public にせず報告可能な
GitHub 標準機構。公開リポジトリに個人 email を露出せず、医療系プロジェクト
(CLAUDE.md §7.3) の機密性配慮とも整合。

---

## §3 Architecture

### §3.1 Task A: smoke test 自動化

**新規ファイル**: `tests/test_gitleaks_smoke.py`

**設計**:
- `subprocess.run` で `uv run pre-commit run gitleaks --files <tmpfile>` を実行
- test 1: ダミー slack bot token (`xoxb-...`) を含む一時ファイル → **exit code 非ゼロ** (detect) を assert
- test 2: 通常テキスト (機密なし) を含む一時ファイル → **exit code 0** (pass) を assert (false positive guard)
- gitleaks / pre-commit binary 不在環境では `pytest.mark.skipif` で skip
- 一時ファイルは `tmp_path` fixture (pytest 標準) を使い test 後自動削除

**性質**: Day24 tripwire test と同じ「回帰 guard」。test 追加 = 即 GREEN
(gitleaks は既に detect 可能)。将来 gitleaks の rule database 変更で slack
token を検出しなくなった場合に test が FAIL し、回帰を検知する。

**ダミー token の安全性**:
- 使用する `xoxb-...` token は構文的に有効だが実在しない fake 値
- test ファイル自体が gitleaks scan 対象になると test ファイルが commit
  ブロックされる懸念 → `.gitleaksignore` に test ファイルの該当行 fingerprint
  を追加するか、token を実行時に文字列連結で組み立てて静的検出を回避する
- **採用**: 実行時文字列連結 (`"xoxb" + "-" + "..."` 形式) でリテラル回避。
  これにより test ファイル自身は gitleaks scan を pass する

### §3.2 Task B: 追加 pre-commit hook

**変更ファイル**: `.pre-commit-config.yaml`

**追加 hook (pre-commit/pre-commit-hooks 公式 repo)**:

```yaml
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: end-of-file-fixer
        exclude: ^tests/fixtures/
      - id: trailing-whitespace
        exclude: ^tests/fixtures/
      - id: check-yaml
      - id: check-toml
```

**exclude 設定**: golden fixture 保護のため、auto-fix 系 hook
(end-of-file-fixer / trailing-whitespace) に **hook 単位で**
`exclude: ^tests/fixtures/` を設定する。

**実装上の注意**:
- `end-of-file-fixer` / `trailing-whitespace` は auto-fix 系 → 既存違反を
  書き換える。fixture の byte 一致を壊さないよう exclude する
- `check-yaml` / `check-toml` は検証のみ (auto-fix しない)。fixture 配下に
  .yaml/.toml は存在しないため exclude 不要
- **top-level exclude は採用しない**: pre-commit の top-level `exclude` は
  全 repo の全 hook (gitleaks を含む) に適用されてしまう。gitleaks は fixture
  も機密 scan 対象に保ちたいため、top-level exclude を使うと gitleaks の
  fixture scan が無効化される。よって **per-hook exclude** を採用し、gitleaks
  (別 repo block) は無変更とする
- **採用**: auto-fix 系 2 hook にのみ `exclude: ^tests/fixtures/` を付与

**commit 分割**:
- B-1: `.pre-commit-config.yaml` 更新のみ (hook 追加 + exclude)
- B-2: `pre-commit run --all-files` による既存違反一括 normalization

### §3.3 Task C: SECURITY.md

**新規ファイル**: `SECURITY.md` (repo root)

**構造** (GitHub 標準テンプレート準拠):

```markdown
# Security Policy

## Supported Versions

| Version | Supported |
|:---|:---:|
| 0.1.x | ✓ |

## Reporting a Vulnerability

脆弱性は GitHub Security Advisories の private vulnerability reporting 機能で
報告する (Security タブ → Report a vulnerability)。公開 Issue では報告しない。

## Response

- 報告受領後、合理的な期間内に初期応答する
- 本プロジェクトは査読・医療データを扱う可能性があるため、患者識別情報を
  含む脆弱性報告は特に慎重に扱う (CLAUDE.md §7.3 準拠)
```

**相互リンク**: Day29 CONTRIBUTING.md の「セキュリティ」節と相互参照。

---

## §4 Implementation 詳細

### §4.1 Task A: smoke test コード骨子

```python
"""tests/test_gitleaks_smoke.py — gitleaks secret 検出能力の回帰 guard。"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# gitleaks / pre-commit / uv のいずれかが不在なら skip
_SKIP_REASON = "uv or pre-commit not available"
_HAS_TOOLS = shutil.which("uv") is not None


def _run_gitleaks_on(tmpfile: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "pre-commit", "run", "gitleaks", "--files", str(tmpfile)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


@pytest.mark.skipif(not _HAS_TOOLS, reason=_SKIP_REASON)
def test_gitleaks_detects_slack_bot_token(tmp_path: Path) -> None:
    """ダミー slack bot token を含むファイルが gitleaks で detect される。"""
    # リテラル回避: test ファイル自身が gitleaks scan を pass するため連結で組立
    token = "xoxb" + "-" + "2222222222" + "-" + "1111111111111" + "-" + "A" * 24
    leak_file = tmp_path / "leak.txt"
    leak_file.write_text(f"slack_token = {token}\n", encoding="utf-8")
    result = _run_gitleaks_on(leak_file)
    assert result.returncode != 0, (
        f"expected gitleaks to detect leak, got returncode 0\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


@pytest.mark.skipif(not _HAS_TOOLS, reason=_SKIP_REASON)
def test_gitleaks_passes_clean_file(tmp_path: Path) -> None:
    """機密を含まない通常ファイルは gitleaks を pass する (false positive guard)。"""
    clean_file = tmp_path / "clean.txt"
    clean_file.write_text("This is a normal reference list.\nSmith J. 2024.\n", encoding="utf-8")
    result = _run_gitleaks_on(clean_file)
    assert result.returncode == 0, (
        f"expected gitleaks to pass clean file, got returncode {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
```

**注**: 実装時に `pre-commit run --files` の正確な挙動 (tracked/untracked、
tmp_path が repo 外の場合の扱い) を検証する。pre-commit は git repo 内の
ファイルを対象とするため、`--files` に repo 外パスを渡すと動作しない可能性が
ある。その場合は repo 内 tmp ディレクトリ (例: `REPO_ROOT / ".tmp_smoke"`) を
使い、test 後に削除する設計に切り替える。この検証は plan の Task A で行う。

### §4.2 Task B: 既存違反一括修正の手順

```bash
# B-1: hook 追加後
git add .pre-commit-config.yaml
git commit -m "chore(pre-commit): add end-of-file/whitespace/yaml/toml hooks"

# B-2: 既存違反を一括修正 (auto-fix hook が書き換え)
uv run pre-commit run --all-files || true   # 初回は FAIL して auto-fix される
git add -A
git commit -m "style: normalize end-of-file and trailing whitespace"
```

**注**: B-2 の `git add -A` 前に、修正対象が fixture 外であることを
`git status` で確認する。fixture が変更されていたら exclude 設定の誤りなので
作業停止。

### §4.3 実装順序

```
spec → plan → B-1 (hook 追加) → B-2 (style 一括) → A (smoke test) → C (SECURITY.md) → archive
```

**根拠**: B-1 (hook 追加) を A/C より先に入れると、以降の新ファイル (smoke
test、SECURITY.md) が新 hook の対象になりクリーンに保たれる。

---

## §5 Error handling

### §5.1 smoke test が CI で skip される場合

- CI 環境で uv/pre-commit が利用可能なため通常は skip されない
- 万一 skip された場合も test 失敗にはならない (skipif の設計通り)
- gitleaks binary は pre-commit が auto-build するため CI でも detect 動作

### §5.2 一括修正が fixture に及んだ場合

- `git status` で fixture 変更を検知したら作業停止
- exclude 設定 (`^tests/fixtures/`) を見直し
- integration test (`uv run pytest tests/`) で byte 一致 fixture が壊れて
  いないか確認

### §5.3 smoke test ファイル自身が gitleaks に検出される場合

- token をリテラルで書くと test ファイルが commit ブロックされる
- §3.1 / §4.1 の通り実行時文字列連結でリテラルを回避
- 万一検出されたら `.gitleaksignore` に fingerprint 追加 (reactive)

---

## §6 Testing 戦略 + Commit 戦略

### §6.1 Testing

| 検証 | 手順 | 期待 |
|:---|:---|:---|
| smoke test | `uv run pytest tests/test_gitleaks_smoke.py -v` | 2 passed |
| 全体 regression | `uv run pytest tests/` | **117 passed** (115 + 2) |
| 追加 hook 動作 | `uv run pre-commit run --all-files` | 全 hook pass (一括修正後) |
| fixture 保護 | integration test | byte 一致維持 |
| CI | push 後 4 jobs | all green |

### §6.2 Commit 戦略 (7 commit)

| # | type | summary | files |
|:---:|:---|:---|:---|
| 1 | `docs(spec)` | Day30 spec | `docs/superpowers/specs/...` |
| 2 | `docs(plan)` | Day30 plan | `docs/superpowers/plans/...` |
| 3 | `chore(pre-commit)` | add 4 hooks + fixtures exclude (B-1) | `.pre-commit-config.yaml` |
| 4 | `style` | normalize EOF + trailing whitespace (B-2) | ~30 files (fixture 外) |
| 5 | `test(security)` | gitleaks smoke test (A) | `tests/test_gitleaks_smoke.py` |
| 6 | `docs(security)` | add SECURITY.md (C) | `SECURITY.md` |
| 7 | `docs(sessions)` | archive Day30 | `docs/sessions/day30/...` |

---

## §7 期待 final state

| 項目 | 値 |
|:---|:---:|
| HEAD | archive commit (Day30 7 commit chain の末尾) |
| tests passed | **117** (115 + smoke 2) |
| pre-commit hooks | 5 (gitleaks + end-of-file-fixer + trailing-whitespace + check-yaml + check-toml) |
| SECURITY.md | 存在 (GitHub Security Advisories 報告窓口) |
| CI jobs | 4 (変更なし) |
| 既存 style 違反 | 0 (fixture 外、一括 normalization 済) |
| fixture byte 一致 | 維持 (exclude 効果) |

---

## §8 Out of scope (Day31+ retain)

1. **ruff / mypy 導入** (Day28/29 LESSONS Medium priority)
2. **Node.js 20 deprecation 対応** (actions/checkout@v4 → @v5)
3. **PyPI 公開化本体** (SECURITY.md は前提整備のみ)
4. **Dependabot 設定** (依存更新自動化)
5. **CI `branches:` trigger 整理** (`feature/mdpi-fast-path` 残存)
6. **追加 pre-commit hook の拡張** (check-added-large-files, mixed-line-ending 等)
7. **regex + `\p{Lu}` 移行 / PMC OA integration test** (Day28 LESSONS)
8. **project-overview.html の配置確定** (現在親ディレクトリに存在、Day30 では扱わない)

---

## §9 LESSONS で記録すべき事項

1. **pre-commit run --files の挙動** (repo 内外、tracked/untracked の扱い)
2. **gitleaks リテラル回避パターン** (test の secret を文字列連結で組立)
3. **fixture exclude の重要性** (byte 一致 golden を auto-fix から保護)
4. **smoke test の回帰 guard 性質** (Day24 tripwire と同類、即 GREEN)
5. **既存違反一括修正の規模** (実測値と実際の修正ファイル数の対比)
6. **SECURITY.md と GitHub Security Advisories の連携**

---

## §10 関連参照

- [Day29 LESSONS](../../sessions/day29/DAY29_LESSONS_LEARNED.md): 本 spec の §5 で Day30 候補として提示
- [Day29 CONTRIBUTING.md](../../../CONTRIBUTING.md): セキュリティ節と相互リンク
- [Day24 LESSONS](../../sessions/day24/DAY24_LESSONS_LEARNED.md): tripwire test pattern
- [pre-commit-hooks 公式](https://github.com/pre-commit/pre-commit-hooks)
- [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories)

---

**End of Spec**
