# Day30 セキュリティ・品質強化 (3 本立て) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Day29 派生の 3 候補 — gitleaks smoke test 自動化、追加 pre-commit hook (end-of-file-fixer / trailing-whitespace / check-yaml / check-toml)、SECURITY.md 整備 — を 1 セッションで実装し、機密 scan の回帰 guard と style 統一と脆弱性報告窓口を確立する。

**Architecture:** Day29 で導入した `.pre-commit-config.yaml` (gitleaks) に pre-commit-hooks v6.0.0 の 4 hook を per-hook exclude 付きで追加し、既存 style 違反を一括 normalization。gitleaks の secret 検出能力は `pre-commit run gitleaks --files` 経由の pytest smoke test で永続保証。SECURITY.md で GitHub Security Advisories を報告窓口として整備。

**Tech Stack:** pre-commit (PyPI >=4.0,<5.0), pre-commit-hooks v6.0.0, gitleaks v8.30.1, pytest 9.x, uv 0.11.x, Python 3.11/3.12/3.14

**Spec:** `docs/superpowers/specs/2026-05-28-day30-security-quality-hardening-design.md`

**起点 commit:** `04f3c19` (Day30 spec commit)

**期待 final state:** HEAD = archive commit、**117 passed** (115 + smoke 2)、pre-commit 5 hook、SECURITY.md 存在、CI 4 jobs green、既存 style 違反 0 (fixture/patch 外)、fixture byte 一致維持

---

## File Structure

| File | 役割 | Day30 での操作 | Task |
|:---|:---|:---:|:---:|
| `.pre-commit-config.yaml` | 4 hook 追加 + per-hook exclude | modify | Task 1 |
| (fixture/patch 外 ~30 file) | 既存 style 違反の一括 normalization | modify (自動) | Task 2 |
| `tests/test_gitleaks_smoke.py` | gitleaks 検出能力の回帰 guard | new | Task 3 |
| `.gitignore` | smoke test 一時ディレクトリ除外 | modify (末尾追加) | Task 3 |
| `SECURITY.md` | 脆弱性報告窓口 | new | Task 4 |
| `docs/superpowers/plans/2026-05-28-day30-security-quality-hardening.md` | この plan | new | Task 0 |
| `docs/sessions/day30/README.md` | session archive | new | Task 5 |
| `docs/sessions/day30/DAY30_LESSONS_LEARNED.md` | session lessons | new | Task 5 |

**Out of touch:** `main.py`, 既存 `tests/*.py` (smoke 以外), integration/, 既存 fixture, `pyproject.toml`, `uv.lock`。

---

## バージョン採用根拠

| ツール | 採用版 | 理由 |
|:---|:---|:---|
| pre-commit-hooks | **v6.0.0** | `curl .../releases/latest` で確認。Spec の v5.0.0 は仮置き、最新採用 |
| gitleaks | v8.30.1 | Day29 で導入済、無変更 |
| pre-commit (PyPI) | >=4.0,<5.0 | Day29 で導入済、無変更 |

---

## 重要な前提知識 (実装前に必読)

### 既存 style 違反の実測 (起点 `04f3c19`)

trailing whitespace を含む **fixture 外** ファイル (6 件):
```
docs/sessions/day17/PLAN_cell_45refs_fixture.md
docs/sessions/day18/PLAN_github_private_push.md
examples/sample_reference_section.pdf                          ← PDF (binary)
integration/patches/02_mdpi_fast_path.patch                    ← patch (行末空白が意味を持つ)
integration/tests/test_integration_149refs/input_References.docx  ← DOCX (binary)
skill_package/examples/sample_reference_section.pdf            ← PDF (binary)
```

**重大な注意**:
- **PDF / DOCX**: pre-commit の `trailing-whitespace` / `end-of-file-fixer` は
  `identify` ライブラリで binary を自動判定し **skip する**。よって PDF/DOCX は
  hook 対象外 (grep でヒットしても触られない)。
- **`.patch` ファイル**: unified diff のコンテキスト行・追加行の末尾空白は
  **意味を持つ** (patch 適用に影響)。`trailing-whitespace` が text 扱いで
  これを削ると patch が壊れる。→ **exclude 必須**。
- よって exclude pattern は `^tests/fixtures/` に加えて
  `^integration/patches/` も含める。

### exclude pattern (最終形)

auto-fix 系 2 hook (end-of-file-fixer / trailing-whitespace) に付与:
```yaml
exclude: '^(tests/fixtures/|integration/patches/)'
```

- `tests/fixtures/`: golden fixture の byte 一致保護 (spec §2.3)
- `integration/patches/`: patch ファイルの末尾空白保護 (本 plan の追加判断)

check-yaml / check-toml は検証のみ・fixture/patch 配下に該当拡張子なしのため
exclude 不要。gitleaks (別 repo block) は無変更で全 file scan 継続。

### pre-commit run --files の挙動

`pre-commit run <hook> --files <path>` は指定パスを hook に渡して scan する。
**pre-commit は cwd が git repo root である必要があり、--files のパスは repo
内が前提**。repo 外 (/tmp 等) のパスは未定義動作。よって smoke test は
**repo 内の一時ディレクトリ** (`.gitleaks_smoke_tmp/`) を使い、`.gitignore` で
除外する (Task 3)。

---

## Commit chain (期待値)

| # | type | summary |
|:---:|:---|:---|
| 1 | docs(spec) | Day30 spec (`04f3c19`、確定済) |
| 2 | docs(plan) | Day30 plan (Task 0) |
| 3 | chore(pre-commit) | 4 hook 追加 + exclude (Task 1, B-1) |
| 4 | style | 既存違反一括 normalization (Task 2, B-2) |
| 5 | test(security) | gitleaks smoke test (Task 3, A) |
| 6 | docs(security) | SECURITY.md (Task 4, C) |
| 7 | docs(sessions) | archive Day30 (Task 5) |

合計 **7 commit**。実装順序: spec → plan → B-1 → B-2 → A → C → archive。

---

## Task 0: Plan を commit

**Files:**
- Create: `docs/superpowers/plans/2026-05-28-day30-security-quality-hardening.md` (この file)

- [ ] **Step 1: plan file 存在確認**

Run: `ls docs/superpowers/plans/2026-05-28-day30-security-quality-hardening.md`
Expected: ファイル存在

- [ ] **Step 2: working tree clean 確認**

Run: `git status`
Expected: spec commit 後、plan file が Untracked

- [ ] **Step 3: stage + commit**

```bash
git add docs/superpowers/plans/2026-05-28-day30-security-quality-hardening.md
git commit -m "$(cat <<'EOF'
docs(plan): add Day30 security/quality hardening plan

3 候補 (smoke test 自動化 / 追加 pre-commit hook / SECURITY.md) を
bite-sized task に分解。

主要構成:
- Task 0: plan commit
- Task 1: pre-commit-hooks v6.0.0 の 4 hook 追加 + per-hook exclude
  (fixtures + patches)
- Task 2: 既存 style 違反一括 normalization
- Task 3: gitleaks smoke test (pre-commit run 経由、repo 内 tmp dir)
- Task 4: SECURITY.md (GitHub Security Advisories)
- Task 5: archive + push + CI

採用バージョン: pre-commit-hooks v6.0.0 (spec の v5.0.0 から update)

exclude 追加判断: ^integration/patches/ も exclude (patch の末尾空白保護)

期待 final: 117 passed (115 + smoke 2)、pre-commit 5 hook、CI 4 jobs。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: commit 確認**

Run: `git log --oneline -1`
Expected: `<SHA> docs(plan): add Day30 security/quality hardening plan`

---

## Task 1 (B-1): pre-commit-hooks 4 hook 追加

**Files:**
- Modify: `.pre-commit-config.yaml`

**目的:** pre-commit-hooks v6.0.0 から 4 hook を追加し、auto-fix 系 2 hook に exclude を付与する。この Task では既存ファイルの一括修正は **行わない** (Task 2 で実施)。

- [ ] **Step 1: 現状の `.pre-commit-config.yaml` 確認**

Run: `cat .pre-commit-config.yaml`
Expected (Day29 末の状態):
```yaml
# Day29 で導入 — Day23 機密データ事故の再発防止を目的とした gitleaks pre-commit hook
# 設計仕様: docs/superpowers/specs/2026-05-28-day29-pre-commit-gitleaks-design.md
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks
```

- [ ] **Step 2: pre-commit-hooks v6.0.0 tag 存在確認**

Run: `curl -s https://api.github.com/repos/pre-commit/pre-commit-hooks/git/refs/tags/v6.0.0 | head -3`
Expected: `"ref": "refs/tags/v6.0.0"` を含む JSON (404 でない)

- [ ] **Step 3: `.pre-commit-config.yaml` に 4 hook 追加**

Edit tool で gitleaks block の後に pre-commit-hooks block を追加する。

old_string:
```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks
```

new_string:
```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks

  # Day30 で追加 — 基本的な file hygiene (末尾改行 / 行末空白 / YAML / TOML 検証)
  # auto-fix 系 (end-of-file-fixer / trailing-whitespace) は tests/fixtures/
  # (byte 一致 golden) と integration/patches/ (patch の末尾空白が意味を持つ)
  # を exclude する。
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: end-of-file-fixer
        exclude: '^(tests/fixtures/|integration/patches/)'
      - id: trailing-whitespace
        exclude: '^(tests/fixtures/|integration/patches/)'
      - id: check-yaml
      - id: check-toml
```

- [ ] **Step 4: YAML 妥当性 + hook 認識確認**

```bash
uv run pre-commit validate-config
```
Expected: 出力なし or `valid` (exit code 0)

```bash
cat .pre-commit-config.yaml
```
Expected: gitleaks block + pre-commit-hooks block (4 hook + exclude 2 箇所)

- [ ] **Step 5: B-1 commit (hook 追加のみ、既存修正なし)**

この commit では `.pre-commit-config.yaml` のみを stage する。`pre-commit run`
はまだ実行しない (Task 2 で一括修正)。ただし commit 時に gitleaks + 新規 4 hook
が走り、`.pre-commit-config.yaml` 自身は pass するはず。

注: commit 時に新 hook が走り、もし `.pre-commit-config.yaml` 以外の staged
ファイルがあれば auto-fix される。本 commit では config のみ stage するので
影響は config 自身に限定。config に末尾改行・行末空白問題があれば auto-fix
されるので、その場合は再 stage して commit。

```bash
git add .pre-commit-config.yaml
git commit -m "$(cat <<'EOF'
chore(pre-commit): add end-of-file/whitespace/yaml/toml hooks (Day30 Task 1)

Day29 の gitleaks hook に pre-commit-hooks v6.0.0 の 4 hook を追加:
- end-of-file-fixer (auto-fix、末尾改行統一)
- trailing-whitespace (auto-fix、行末空白除去)
- check-yaml (検証、YAML 構文)
- check-toml (検証、TOML 構文、pyproject.toml 保護)

auto-fix 系 2 hook には per-hook exclude を付与:
  exclude: '^(tests/fixtures/|integration/patches/)'
- tests/fixtures/: byte 一致 golden fixture を auto-fix から保護
- integration/patches/: patch の末尾空白 (適用に影響) を保護

top-level exclude を使わない理由: gitleaks (別 repo block) の fixture
scan を無効化しないため。check-yaml/check-toml は検証のみで fixture/patch
配下に該当拡張子がないため exclude 不要。

本 commit は hook 追加のみ。既存 style 違反の一括修正は次の commit
(style) で実施する。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: commit 確認**

Run: `git log --oneline -2`
Expected:
```
<SHA> chore(pre-commit): add end-of-file/whitespace/yaml/toml hooks (Day30 Task 1)
<SHA> docs(plan): add Day30 security/quality hardening plan
```

---

## Task 2 (B-2): 既存 style 違反の一括 normalization

**Files:**
- Modify: fixture/patch 外の既存違反ファイル (~30 件、auto-fix による)

**目的:** Task 1 で追加した auto-fix hook を `--all-files` で実行し、既存の末尾改行・行末空白違反を一括修正する。fixture / patch / binary が変更対象になっていないことを検証する。

- [ ] **Step 1: 一括 auto-fix を dry-run 的に実行 (1 回目、修正が走る)**

```bash
uv run pre-commit run end-of-file-fixer --all-files
uv run pre-commit run trailing-whitespace --all-files
```
Expected: 初回は `Failed` (auto-fix が走りファイルが書き換わる)。2 回目は `Passed`。

- [ ] **Step 2: 変更対象を確認 — fixture / patch / binary が含まれないこと**

```bash
git status --short
```
Expected: 変更ファイルが表示される。以下を **厳格に確認**:
- `tests/fixtures/` 配下が **変更されていない** (exclude 効果)
- `integration/patches/` 配下が **変更されていない** (exclude 効果)
- `*.pdf` / `*.docx` が **変更されていない** (binary 自動 skip)

確認コマンド:
```bash
git status --short | grep -E 'tests/fixtures/|integration/patches/|\.pdf$|\.docx$' && echo "NG: protected file changed" || echo "OK: no protected file changed"
```
Expected: `OK: no protected file changed`

**もし NG なら作業停止**: exclude 設定を見直す。binary が変更されていたら
`git checkout -- <file>` で revert し、exclude pattern に追加。

- [ ] **Step 3: 変更内容が末尾改行・行末空白のみであることを抜き取り確認**

```bash
git diff --stat | tail -20
```
Expected: 変更は概ね `+1 -1` や `+1 -0` 程度の小規模 (末尾改行 / 空白除去)。
大きな diff があるファイルがあれば内容を `git diff <file>` で確認。

- [ ] **Step 4: 2 回目の実行で全 pass 確認 (冪等性)**

```bash
uv run pre-commit run end-of-file-fixer --all-files
uv run pre-commit run trailing-whitespace --all-files
uv run pre-commit run check-yaml --all-files
uv run pre-commit run check-toml --all-files
```
Expected: 全 hook `Passed`

- [ ] **Step 5: 既存 pytest に regression なし確認 (fixture 保護の検証)**

```bash
uv run pytest tests/ -q
```
Expected: `115 passed` (Day29 末と同じ)。

**もし fixture 関連 test が FAIL したら**: exclude が効いておらず fixture が
変更された証拠。Step 2 に戻り revert + exclude 修正。

- [ ] **Step 6: B-2 commit (style 一括修正)**

```bash
git add -A
git status
```
Expected: fixture/patch/binary 以外の ~30 ファイルが staged。

```bash
git commit -m "$(cat <<'EOF'
style: normalize end-of-file and trailing whitespace (Day30 Task 2)

Day30 Task 1 で追加した end-of-file-fixer / trailing-whitespace hook を
`pre-commit run --all-files` で実行し、既存の末尾改行欠落・行末空白を
一括 normalization。

対象外 (exclude / binary skip):
- tests/fixtures/ (byte 一致 golden、exclude)
- integration/patches/ (patch 末尾空白、exclude)
- *.pdf / *.docx (binary、pre-commit が identify で自動 skip)

機械的修正のみ。コードロジック・テスト・fixture の semantics 変更なし。
115 passed を維持 (fixture 保護を検証済)。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

注: この commit 時に pre-commit hook が走るが、既に全 file が normalize 済
なので auto-fix は走らず pass する。

- [ ] **Step 7: commit 確認**

Run: `git log --oneline -3`
Expected:
```
<SHA> style: normalize end-of-file and trailing whitespace (Day30 Task 2)
<SHA> chore(pre-commit): add end-of-file/whitespace/yaml/toml hooks (Day30 Task 1)
<SHA> docs(plan): add Day30 security/quality hardening plan
```

---

## Task 3 (A): gitleaks smoke test

**Files:**
- Create: `tests/test_gitleaks_smoke.py`
- Modify: `.gitignore` (smoke 一時 dir 除外)

**目的:** gitleaks の secret 検出能力を pytest で回帰 guard する。`pre-commit run gitleaks --files` を subprocess 実行し、ダミー slack token を含むファイルが detect され、通常ファイルが pass することを検証する。

- [ ] **Step 1: `.gitignore` に smoke 一時 dir を追加**

Edit tool で `.gitignore` の末尾に追加。

old_string:
```
# gitleaks history audit report (Day29 で導入、機密 finding を含み得るため commit しない)
.gitleaks-audit.json
```

new_string:
```
# gitleaks history audit report (Day29 で導入、機密 finding を含み得るため commit しない)
.gitleaks-audit.json

# gitleaks smoke test の一時ディレクトリ (Day30 で導入、test 実行時のみ生成)
.gitleaks_smoke_tmp/
```

- [ ] **Step 2: `tests/test_gitleaks_smoke.py` を作成**

Write tool で以下を作成:

```python
"""tests/test_gitleaks_smoke.py — gitleaks secret 検出能力の回帰 guard (Day30)。

Day29 で導入した gitleaks pre-commit hook が、将来の rule database 変更で
secret を検出しなくなる回帰を pytest で検知する。`pre-commit run gitleaks
--files` を subprocess 実行し、ダミー slack token の検出と通常ファイルの
pass を検証する。

pre-commit は cwd=repo root + repo 内パスを前提とするため、一時ファイルは
repo 内 .gitleaks_smoke_tmp/ に置く (.gitignore で除外)。
"""
from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_SMOKE_DIR = REPO_ROOT / ".gitleaks_smoke_tmp"

# uv が無い環境では skip (CI / 開発機ともに uv は存在する想定だが安全側)
_HAS_UV = shutil.which("uv") is not None
_SKIP_REASON = "uv not available; cannot run pre-commit gitleaks"


@pytest.fixture
def smoke_dir() -> Iterator[Path]:
    """repo 内の一時ディレクトリを生成し、test 後に削除する。"""
    _SMOKE_DIR.mkdir(exist_ok=True)
    try:
        yield _SMOKE_DIR
    finally:
        shutil.rmtree(_SMOKE_DIR, ignore_errors=True)


def _run_gitleaks_on(path: Path) -> subprocess.CompletedProcess[str]:
    """pre-commit の gitleaks hook を指定ファイルに対して実行する。"""
    return subprocess.run(
        ["uv", "run", "pre-commit", "run", "gitleaks", "--files", str(path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


@pytest.mark.skipif(not _HAS_UV, reason=_SKIP_REASON)
def test_gitleaks_detects_slack_bot_token(smoke_dir: Path) -> None:
    """ダミー slack bot token を含むファイルが gitleaks で detect される。

    回帰 guard: gitleaks の rule が slack-bot-token を検出しなくなったら FAIL。
    token はリテラルで書くとこの test ファイル自身が gitleaks scan で
    ブロックされるため、実行時に文字列連結で組み立てる。
    """
    token = "xoxb" + "-" + "2222222222" + "-" + "1111111111111" + "-" + ("A" * 24)
    leak_file = smoke_dir / "leak.txt"
    leak_file.write_text(f"slack_token = {token}\n", encoding="utf-8")

    result = _run_gitleaks_on(leak_file)

    assert result.returncode != 0, (
        "expected gitleaks to DETECT the slack token (returncode != 0), "
        f"but got returncode 0.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


@pytest.mark.skipif(not _HAS_UV, reason=_SKIP_REASON)
def test_gitleaks_passes_clean_file(smoke_dir: Path) -> None:
    """機密を含まない通常ファイルは gitleaks を pass する (false positive guard)。"""
    clean_file = smoke_dir / "clean.txt"
    clean_file.write_text(
        "This is a normal reference list.\nSmith J, Brown K. Title. Journal 2024.\n",
        encoding="utf-8",
    )

    result = _run_gitleaks_on(clean_file)

    assert result.returncode == 0, (
        "expected gitleaks to PASS the clean file (returncode 0), "
        f"but got returncode {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
```

- [ ] **Step 3: smoke test を実行して 2 件 pass 確認**

```bash
uv run pytest tests/test_gitleaks_smoke.py -v
```
Expected: `2 passed` (`test_gitleaks_detects_slack_bot_token` PASSED,
`test_gitleaks_passes_clean_file` PASSED)

**もし `test_gitleaks_detects_slack_bot_token` が FAIL (returncode 0) の場合**:
- gitleaks が slack token を検出していない
- ダミー token の形式を確認 (xoxb- prefix + 適切な長さ)
- `_run_gitleaks_on` の戻り値 stdout/stderr を確認

**もし pre-commit run --files が repo 内 tmp でも動かない場合**:
- エラーメッセージを確認
- `--files` ではなく一時的に git add してから `pre-commit run gitleaks`
  (staged 対象) に切り替える設計を検討。ただし add した一時ファイルは
  test 後に `git reset` で確実に unstage すること

- [ ] **Step 4: test ファイル自身が gitleaks scan を pass することを確認**

```bash
uv run pre-commit run gitleaks --files tests/test_gitleaks_smoke.py
```
Expected: `Passed` (token が文字列連結のためリテラル検出されない)

**もし FAIL したら**: `.gitleaksignore` に fingerprint 追加を検討。ただし
まず token 組み立てが連結形式になっているか確認。

- [ ] **Step 5: 全体 pytest で 117 passed 確認**

```bash
uv run pytest tests/ -q
```
Expected: `117 passed` (115 + smoke 2)

- [ ] **Step 6: 一時 dir が残っていないこと + gitignore 確認**

```bash
ls -d .gitleaks_smoke_tmp 2>/dev/null && echo "NG: tmp dir remains" || echo "OK: tmp dir cleaned"
git check-ignore -v .gitleaks_smoke_tmp/ 2>/dev/null || git status --short
```
Expected: `OK: tmp dir cleaned`、`.gitleaks_smoke_tmp/` は git status に出ない

- [ ] **Step 7: Task A commit**

```bash
git add tests/test_gitleaks_smoke.py .gitignore
git commit -m "$(cat <<'EOF'
test(security): add gitleaks secret-detection smoke test (Day30 Task 3)

Day29 で導入した gitleaks hook の secret 検出能力を pytest で回帰 guard
する。`pre-commit run gitleaks --files` を subprocess 実行し、2 ケースを
検証:
- test_gitleaks_detects_slack_bot_token: ダミー slack token を DETECT
  (returncode != 0)
- test_gitleaks_passes_clean_file: 通常ファイルを PASS (false positive
  guard、returncode 0)

設計:
- pre-commit は cwd=repo root + repo 内パスを前提とするため、一時ファイルは
  repo 内 .gitleaks_smoke_tmp/ に置き .gitignore で除外
- ダミー token はリテラルで書くと test ファイル自身が gitleaks に
  ブロックされるため、実行時に文字列連結で組み立て (xoxb + - + ...)
- uv 不在環境では skipif で skip

性質: Day24 tripwire と同じ回帰 guard。gitleaks rule database が将来
slack-bot-token を検出しなくなったら FAIL し回帰を検知する。

Test results: 115 passed → 117 passed (+ 2 smoke tests)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 8: commit 確認**

Run: `git log --oneline -4`
Expected: 先頭が `test(security): add gitleaks secret-detection smoke test (Day30 Task 3)`

---

## Task 4 (C): SECURITY.md

**Files:**
- Create: `SECURITY.md` (repo root)

**目的:** 脆弱性報告窓口を GitHub Security Advisories として整備し、PyPI 公開の前提を満たす。

- [ ] **Step 1: `SECURITY.md` を作成**

Write tool で `/Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver/SECURITY.md` を以下の内容で作成:

```markdown
# Security Policy

## Supported Versions

セキュリティ更新の対象バージョン:

| Version | Supported |
|:---|:---:|
| 0.1.x | :white_check_mark: |
| < 0.1 | :x: |

## Reporting a Vulnerability

脆弱性を発見した場合は、**公開 Issue では報告しないでください**。

本リポジトリの [GitHub Security Advisories](https://github.com/hikataya01-netizen/pubmed-reference-resolver/security/advisories/new)
の private vulnerability reporting 機能を使用して報告してください
(リポジトリの **Security** タブ → **Report a vulnerability**)。

報告には以下を含めてください:

- 脆弱性の概要と影響範囲
- 再現手順 (可能であれば最小再現コード)
- 想定される攻撃シナリオ
- 修正案 (あれば)

## Response

- 報告受領後、合理的な期間内に初期応答します。
- 脆弱性の妥当性を確認し、修正方針と公開時期を報告者と調整します。
- 修正後、GitHub Security Advisory として公開し、報告者をクレジットします
  (希望する場合)。

## Scope and Data Handling

本プロジェクトは学術論文の参照文献を PubMed で検証する査読支援ツールです。
以下の点に特に留意してください:

- 本ツールは査読対象論文・医療関連データを処理する可能性があります。
- 脆弱性報告に患者識別情報・未公開の査読データを **含めないでください**。
  再現に必要な場合は、仮名化・匿名化したサンプルを使用してください。
- API キー (NCBI / Claude 等) の取り扱いについては
  [CONTRIBUTING.md](CONTRIBUTING.md) のセキュリティ節を参照してください。

## Related

- [CONTRIBUTING.md](CONTRIBUTING.md) — 開発フローと機密情報の取り扱い
- 機密 commit の自動防御: pre-commit gitleaks hook + CI gitleaks job
  (Day29 で導入)
```

注: リポジトリ URL は `hikataya01-netizen/pubmed-reference-resolver`
(Day29 で確認済の実 URL)。

- [ ] **Step 2: SECURITY.md が gitleaks + 新 hook を pass することを確認**

```bash
uv run pre-commit run --files SECURITY.md
```
Expected: 全 hook `Passed` (gitleaks / end-of-file-fixer / trailing-whitespace
/ check-yaml / check-toml)。SECURITY.md は末尾改行ありで作成すること。

- [ ] **Step 3: Task C commit**

```bash
git add SECURITY.md
git commit -m "$(cat <<'EOF'
docs(security): add SECURITY.md with GitHub Security Advisories policy (Day30 Task 4)

PyPI 公開の前提として脆弱性報告窓口を整備。

構造 (GitHub 標準テンプレート準拠):
- Supported Versions: 0.1.x
- Reporting a Vulnerability: GitHub Security Advisories の private
  vulnerability reporting 経由 (公開 Issue 禁止)
- Response: 初期応答 + 修正方針調整 + advisory 公開フロー
- Scope and Data Handling: 査読・医療データの取り扱い注意
  (患者識別情報を報告に含めない、CLAUDE.md §7.3 準拠)

email を記載せず GitHub Security Advisories に一本化することで、公開 repo
への個人 email 露出を回避。Day29 CONTRIBUTING.md のセキュリティ節と
相互リンク。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: commit 確認 + push + CI**

```bash
git log --oneline -5
git push origin main
gh run watch
```
Expected: CI 4 jobs all green。smoke test は CI でも実行され pass。

CI run ID と build time をメモ (Task 5 archive 用)。

注: CI の `test` job は `uv run pytest tests/ -q` を実行する。smoke test も
含まれ 117 passed になる。gitleaks binary は pre-commit が auto-build する
ため smoke test も CI で動作する。

---

## Task 5: Day30 archive

**Files:**
- Create: `docs/sessions/day30/README.md`
- Create: `docs/sessions/day30/DAY30_LESSONS_LEARNED.md`

**目的:** Day30 session の成果と学びを永続記録する。Day23-29 と同じ構造を維持。

- [ ] **Step 1: ディレクトリ作成**

```bash
mkdir -p docs/sessions/day30
```

- [ ] **Step 2: `docs/sessions/day30/README.md` 作成**

Write tool で作成 (`<plan-SHA>` `<b1-SHA>` `<b2-SHA>` `<a-SHA>` `<c-SHA>` は
Step 4 で実 SHA に置換、archive は `(本 commit)`):

```markdown
# Day30: セキュリティ・品質強化 (3 本立て)

**実施日**: 2026-05-28
**起点 commit**: `04f3c19` (Day30 spec commit)
**完了 commit**: `<c-SHA>` (Day30 Task 4 SECURITY.md)

## §1 概要

Day29 LESSONS §5 Top priority 3 候補を 1 セッションで実装した:
- gitleaks smoke test 自動化 (回帰 guard)
- 追加 pre-commit hook (end-of-file-fixer / trailing-whitespace /
  check-yaml / check-toml)
- SECURITY.md 整備 (GitHub Security Advisories)

## §2 成果

| 項目 | Day29 末 | Day30 末 | 差分 |
|:---|:---:|:---:|:---:|
| pre-commit hooks | 1 (gitleaks) | 5 (+ 4 hook) | + 4 |
| tests passed | 115 | 117 | + 2 (smoke) |
| SECURITY.md | なし | あり | + 報告窓口 |
| 既存 style 違反 (fixture/patch 外) | ~30 | 0 | 一括修正 |
| CI jobs | 4 | 4 | 0 |
| commit 数 | — | 7 | spec/plan/B-1/B-2/A/C/archive |

## §3 commit chain

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `04f3c19` | docs(spec) | Day30 security/quality hardening spec |
| 2 | `<plan-SHA>` | docs(plan) | Day30 plan |
| 3 | `<b1-SHA>` | chore(pre-commit) | 4 hook 追加 + exclude |
| 4 | `<b2-SHA>` | style | 既存違反一括 normalization |
| 5 | `<a-SHA>` | test(security) | gitleaks smoke test |
| 6 | `<c-SHA>` | docs(security) | SECURITY.md |
| 7 | `(本 commit)` | docs(sessions) | archive day30 |

## §4 関連ドキュメント

- [Spec](../../superpowers/specs/2026-05-28-day30-security-quality-hardening-design.md)
- [Plan](../../superpowers/plans/2026-05-28-day30-security-quality-hardening.md)
- [LESSONS](DAY30_LESSONS_LEARNED.md)
- [SECURITY.md](../../../SECURITY.md)
- [CONTRIBUTING.md](../../../CONTRIBUTING.md)

## §5 関連セッション

- [Day29](../day29/README.md): pre-commit gitleaks 3 層防御 (本 session の基盤)
- [Day24](../day24/README.md): tripwire test pattern (smoke test の先例)
- [Day23](../day23/README.md): 機密データ事故 (Day29/30 の根本動機)
```

- [ ] **Step 3: `docs/sessions/day30/DAY30_LESSONS_LEARNED.md` 作成**

Write tool で作成 (`<...>` placeholder は Step 4 で実値置換):

```markdown
# Day30 Lessons Learned (2026-05-28)

## §1 概要

Day29 LESSONS §5 Top priority 3 候補 (smoke test 自動化 / 追加 pre-commit
hook / SECURITY.md) を 1 セッションで実装した。

### §1.1 セッション開始時の状態

- 115 passed / 0 skipped (Day29 末)
- pre-commit hook: gitleaks 1 件のみ
- SECURITY.md 未作成
- 既存 style 違反 (fixture/patch 外): ~30 ファイル

### §1.2 セッション終了時の状態

- 117 passed / 0 skipped / 0 failed (+ smoke 2)
- pre-commit hook: 5 件 (gitleaks + end-of-file-fixer + trailing-whitespace
  + check-yaml + check-toml)
- SECURITY.md 作成済 (GitHub Security Advisories 報告窓口)
- 既存 style 違反 (fixture/patch 外): 0
- CI 4 jobs green、smoke test も CI で pass
- LLM cost: $0

---

## §2 設計上の発見

### §2.1 auto-fix hook と byte 敏感ファイルの衝突

end-of-file-fixer / trailing-whitespace は auto-fix 系で、以下を破壊し得る:

| ファイル種別 | リスク | 対処 |
|:---|:---|:---|
| `tests/fixtures/` golden | byte 一致検証が壊れる | exclude |
| `integration/patches/*.patch` | 末尾空白が patch 適用に影響 | exclude |
| `*.pdf` / `*.docx` | binary 破壊 | pre-commit が identify で自動 skip |

実装前の実測で fixture 外の trailing whitespace 違反に PDF/DOCX/patch が
含まれることを発見し、**exclude pattern を `^(tests/fixtures/|integration/patches/)`
に拡張** した (spec の `^tests/fixtures/` のみから plan で追加判断)。

PDF/DOCX は pre-commit の `identify` ライブラリが binary 判定して自動 skip
するため exclude 不要だったが、念のため一括修正後に `git status` で binary
が変更されていないことを検証した。

### §2.2 top-level exclude の罠

pre-commit の **top-level `exclude` は全 repo の全 hook に適用される**。
gitleaks (別 repo block) も対象になるため、top-level で `^tests/fixtures/`
を exclude すると gitleaks の fixture scan が無効化される。fixture も機密
scan 対象に保ちたいため、**per-hook exclude** を採用した。

### §2.3 pre-commit run --files の repo 内パス制約

`pre-commit run <hook> --files <path>` は cwd=repo root + repo 内パスを
前提とする。smoke test の一時ファイルを `/tmp` (repo 外) に置くと動作
しないため、repo 内 `.gitleaks_smoke_tmp/` に置き `.gitignore` で除外した。
<実装時の実際の挙動を記録 — repo 外 tmp_path で動いたか否か>

### §2.4 smoke test の secret リテラル回避

smoke test はダミー slack token を使うが、token をソースに **リテラルで
書くと test ファイル自身が gitleaks にブロックされる**。実行時に文字列連結
(`"xoxb" + "-" + ...`) で組み立てることで、静的 scan を回避しつつ実行時には
有効な token 文字列を生成する。これは「secret 検出ツールを test する」際の
普遍的なジレンマへの対処パターン。

### §2.5 smoke test の回帰 guard 性質

smoke test は新機能ではなく Day24 tripwire と同類の「回帰 guard」。test 追加
= 即 GREEN (gitleaks は既に detect 可能)。将来 gitleaks の rule database が
変わり slack-bot-token を検出しなくなった場合に FAIL し、防御層の劣化を検知
する。

---

## §3 実装結果

### §3.1 一括 normalization の実測

| 指標 | 値 |
|:---|:---:|
| 実測した trailing whitespace 違反 (fixture 外) | 6 (うち binary/patch 4) |
| 実際に修正されたファイル数 | <実値> |
| 末尾改行追加ファイル数 | <実値> |
| fixture / patch / binary の変更 | 0 (保護成功) |

### §3.2 smoke test

| 検証 | 結果 |
|:---|:---:|
| test_gitleaks_detects_slack_bot_token | PASSED |
| test_gitleaks_passes_clean_file | PASSED |
| test ファイル自身の gitleaks scan | Passed (リテラル回避成功) |
| 全体 pytest | 117 passed |

### §3.3 CI

| Job | Status | Build time |
|:---|:---:|:---:|
| test (3.11) | <status> | <X>s |
| test (3.12) | <status> | <X>s |
| test-experimental (3.14) | <status> | <X>s |
| gitleaks | <status> | <X>s |

CI run ID: `<run-id>`

---

## §4 brainstorm/spec/plan の流れ

| 段階 | 内容 | commit |
|:---:|:---|:---:|
| 1 | brainstorm: 3 候補 scope + smoke 方式 + 既存違反扱い + 報告先確定 | — |
| 2 | spec 書き出し + self-review (top-level exclude 矛盾を修正) | `04f3c19` |
| 3 | plan 書き出し (pre-commit-hooks v6.0.0、patch exclude 追加判断) | `<plan-SHA>` |
| 4 | Task 1 (B-1): 4 hook 追加 + exclude | `<b1-SHA>` |
| 5 | Task 2 (B-2): 既存違反一括 normalization | `<b2-SHA>` |
| 6 | Task 3 (A): smoke test + .gitignore | `<a-SHA>` |
| 7 | Task 4 (C): SECURITY.md + push + CI | `<c-SHA>` |
| 8 | Task 5: archive | `(本 commit)` |

self-review で発見した訂正点:
- spec: top-level exclude が gitleaks の fixture scan を無効化する矛盾を
  per-hook exclude に修正
- plan: pre-commit-hooks `v5.0.0` (spec 仮置き) → `v6.0.0` (最新) に update
- plan: exclude に `^integration/patches/` を追加 (patch 末尾空白保護)

---

## §5 Day31+ 候補

### Top priority

1. **ruff + mypy 導入** (CLAUDE.md §8.2 既定、Day28/29 から継続の技術的負債)
   - pre-commit hook としても追加可能 (今回の基盤が活きる)

2. **Node.js 20 deprecation 対応** (actions/checkout@v4 → @v5、CI annotation)

### Medium priority

3. **PyPI 公開化本体** (SECURITY.md / CONTRIBUTING.md / LICENSE 等の前提は整備済)
4. **Dependabot 設定** (pre-commit hook の rev 自動更新も含む)
5. **CI `branches:` trigger 整理** (`feature/mdpi-fast-path` 残存)
6. **追加 pre-commit hook 拡張** (check-added-large-files, mixed-line-ending,
   check-merge-conflict 等)

### Low priority

7. **regex + `\p{Lu}` 移行** (Day28 LESSONS)
8. **PMC OA fixture integration test** (Latin Extended-A 実 paper)
9. **Crossref graceful failure** (apa_45refs の 16 件)
10. **project-overview.html の配置確定** (現在親ディレクトリに存在)

---

## §6 メトリクス

| 指標 | 値 |
|:---|:---:|
| brainstorm 質問数 | 4 (scope / smoke 方式 / 既存違反 / 報告先) |
| commit 数 | 7 (spec/plan/B-1/B-2/A/C/archive) |
| 新規 file 数 | 4 (test_gitleaks_smoke.py, SECURITY.md, README.md, LESSONS.md) |
| modify file 数 | 2 + ~30 (config/gitignore + style 一括) |
| 新規 dependency | 0 (pre-commit-hooks は pre-commit が管理、PyPI dep ではない) |
| 新規 pre-commit hook | 4 |
| 新規 unit test | 2 (smoke) |
| 全体 tests passed | 115 → 117 |
| skipped | 0 → 0 (uv 利用可のため smoke も実行) |
| LLM cost | $0 |
| 既存 style 違反 (fixture/patch 外) | ~30 → 0 |

---

## §7 関連参照

- [Spec](../../superpowers/specs/2026-05-28-day30-security-quality-hardening-design.md)
- [Plan](../../superpowers/plans/2026-05-28-day30-security-quality-hardening.md)
- [SECURITY.md](../../../SECURITY.md)
- [CONTRIBUTING.md](../../../CONTRIBUTING.md)
- [Day29 LESSONS](../day29/DAY29_LESSONS_LEARNED.md): 本 session の動機元
- [Day24 LESSONS](../day24/DAY24_LESSONS_LEARNED.md): tripwire test pattern
- [pre-commit-hooks 公式](https://github.com/pre-commit/pre-commit-hooks)
- [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories)
```

- [ ] **Step 4: SHA / CI build time / 実測値を置換**

実値取得:
```bash
git log --oneline -8
gh run list --limit 3
```

README.md と LESSONS.md の `<plan-SHA>` `<b1-SHA>` `<b2-SHA>` `<a-SHA>`
`<c-SHA>` `<run-id>` `<X>s` `<status>` `<実値>` を Edit tool で実値に置換。
archive 自己参照は `(本 commit)` のまま。

§3.1 の「実際に修正されたファイル数」は Task 2 Step 6 の `git show --stat`
から取得。

- [ ] **Step 5: archive commit**

```bash
git add docs/sessions/day30/README.md docs/sessions/day30/DAY30_LESSONS_LEARNED.md
git commit -m "$(cat <<'EOF'
docs(sessions): archive day30 security/quality hardening session

Day29 LESSONS §5 Top priority 3 候補 (smoke test 自動化 / 追加
pre-commit hook / SECURITY.md) を 1 セッションで実装した成果と学びを
永続記録。

主要 finding:
- auto-fix hook と byte 敏感ファイル (fixture/patch/binary) の衝突を
  per-hook exclude + binary 自動 skip で回避
- top-level exclude は gitleaks の fixture scan を無効化するため不採用
- pre-commit run --files の repo 内パス制約に対応 (.gitleaks_smoke_tmp/)
- smoke test の secret リテラル回避 (文字列連結で静的 scan を回避)

成果: 115 passed → 117 passed (+ smoke 2)、pre-commit 5 hook、SECURITY.md
追加、既存 style 違反一括解消、commit 7、CI 4 jobs green、LLM cost \$0

Day31+ 候補として ruff/mypy 導入、Node.js 20 deprecation 対応、PyPI
公開化本体等を LESSONS に記録。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: archive push + CI 確認**

```bash
git push origin main
gh run watch
```
Expected: 4 jobs all green。

- [ ] **Step 7: 最終 state 確認**

```bash
git log --oneline -8
uv run pytest tests/ -q 2>&1 | tail -3
uv run pre-commit run --all-files 2>&1 | tail -10
git status
```
Expected:
- 7 commit chain (spec → ... → archive) + 起点
- `117 passed`
- 全 pre-commit hook `Passed`
- `nothing to commit, working tree clean` (`.gitleaks_smoke_tmp/` は gitignore 除外)

---

## Self-review notes (writer から実装者へのメモ)

### Spec → Plan の divergence point

1. **pre-commit-hooks version**: spec `v5.0.0` → plan `v6.0.0` (実装時最新)
2. **exclude pattern 拡張**: spec `^tests/fixtures/` → plan
   `^(tests/fixtures/|integration/patches/)` (patch 末尾空白保護を追加)。
   実装前の実測で patch ファイルに trailing whitespace 違反を発見したため。
3. **smoke test 一時 dir**: spec で「plan で検証」とした pre-commit run の
   repo 内パス制約を、plan では確定して `.gitleaks_smoke_tmp/` 方式を採用。
   実装者は Task 3 Step 3 でこの方式が動くか最初に検証し、動かない場合は
   git add 方式に切り替える。

### 既存違反一括修正の安全ガード

Task 2 は機械的だが破壊リスクがある。必ず Step 2 で fixture/patch/binary が
変更対象に含まれないことを確認してから commit する。`git status` で protected
file が変わっていたら **作業停止**。

### smoke test の CI 動作

smoke test は CI の `test` job (`uv run pytest tests/ -q`) で実行される。
gitleaks binary は pre-commit が auto-build するため CI でも detect 動作する。
万一 CI で smoke test が skip された場合 (uv 不在等) も test 失敗にはならない。

### Task 数と commit 数

- Task: 0-5 の 6 Task
- commit: 7 (Task 3 が 1 commit、Task 5 が archive 1 commit、Task 2 と Task 1
  は別 commit)

---

**End of Plan**
