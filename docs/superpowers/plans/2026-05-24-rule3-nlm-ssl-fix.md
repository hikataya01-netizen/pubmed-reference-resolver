# Rule 3 NLM SSL Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Inject a certifi-based SSL context into `nlm_catalog_check._fetch_json` so that Rule 3 (NLM Catalog 直接検索) succeeds on macOS Python.org installer environments, then regenerate `cell_45refs` + `apa_45refs` baselines to confirm Day20 改修 produces actual B/C classifications instead of falling to unknown.

**Architecture:** Add `certifi` as a runtime dependency. Create a module-level `_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())` singleton in `nlm_catalog_check.py` and pass it to every `urllib.request.urlopen` call via the `context` kwarg. Existing graceful fail-soft (network/HTTP/timeout errors return `_result(None, error=...)` → unknown) is preserved untouched. Regenerate baselines with `--reuse-phase3` to skip LLM calls (~$0 LLM cost, ~25 NLM API calls).

**Tech Stack:** Python 3.11+ (3.14 supported via CI experimental matrix), urllib.request (stdlib), `certifi>=2024.0,<2027.0` (new dep), pytest 9.x, monkeypatch.

**Spec reference:** `docs/superpowers/specs/2026-05-24-rule3-nlm-ssl-fix-design.md` (commit `af9e55a`)

**Total commits:** 5 (spec already committed as #1)

---

## File Structure

### Files modified

| File | Responsibility | Change |
|:---|:---|:---|
| `requirements.txt` | runtime + test dep manifest | +1 line: `certifi>=2024.0,<2027.0` |
| `nlm_catalog_check.py` | NLM Catalog API client (line 41-190 area) | +1 import (`ssl`, `certifi`), +1 module-level singleton (`_SSL_CONTEXT`), modify `_fetch_json:179` to pass `context=_SSL_CONTEXT` |
| `tests/test_nlm_catalog_check.py` | unit tests for nlm_catalog_check | +1 test (`test_fetch_json_uses_certifi_ssl_context`) |

### Files regenerated (baselines, byte-for-byte from Phase 4 rerun)

| File | Regeneration trigger |
|:---|:---|
| `tests/fixtures/cell_45refs/baseline_three_class_classification.json` | Rule 3 SSL fix changes unknown → B/C for 8 refs |
| `tests/fixtures/cell_45refs/baseline_report.md` | Three-class section reflects new distribution |
| `tests/fixtures/cell_45refs/README.md` | "Day22 改修後実測" section update |
| `tests/fixtures/apa_45refs/baseline_three_class_classification.json` | Rule 3 SSL fix changes unknown → B/C for 17 refs |
| `tests/fixtures/apa_45refs/baseline_report.md` | Same |
| `tests/fixtures/apa_45refs/README.md` | Same |
| `tests/test_integration_cell_45refs.py:286-291` | `EXPECTED_THREE_CLASS_DISTRIBUTION` literal updated to new actuals |
| `tests/test_integration_apa_45refs.py:284-289` | Same |
| `tests/fixtures/mdpi_149refs/expected_report.md` | **Only if** Phase 3 全 tests run reveals stub fixture is affected (Day20 §3.4 PLAN gap pattern) |

### Files created (Day22 archive)

| File | Responsibility |
|:---|:---|
| `docs/superpowers/plans/2026-05-24-rule3-nlm-ssl-fix.md` | This plan (Task 0) |
| `docs/sessions/day22/README.md` | Day22 index |
| `docs/sessions/day22/DAY22_LESSONS_LEARNED.md` | Day22 retrospective |

### Files NOT touched

`three_class_classifier.py`, `main.py`, `crossref_check.py`, `journal_audit.py`, `mdpi_parser.py`, other fixtures (vancouver_24refs, mdpi_149refs input + phase1-3 baseline), Day1-21 archive docs (履歴尊重).

---

## Task 0: Commit this plan

**Files:**
- Modify: `docs/superpowers/plans/2026-05-24-rule3-nlm-ssl-fix.md` (just written)

- [ ] **Step 1: Stage and review**

Run:
```bash
git add docs/superpowers/plans/2026-05-24-rule3-nlm-ssl-fix.md
git status --short
```

Expected: 1 file added under `docs/superpowers/plans/`.

- [ ] **Step 2: Commit**

```bash
git commit -m "$(cat <<'EOF'
docs(plan): add implementation plan for Rule 3 NLM SSL fix (Day22 Phase B)

Day22 Phase B writing-plans 完了 plan を archive.

spec (commit af9e55a) に基づく 5 commit + 14 step の bite-sized 実装計画:
  - Task 1: TDD RED unit test (test_fetch_json_uses_certifi_ssl_context)
  - Task 2: certifi 追加 + nlm_catalog_check.py に _SSL_CONTEXT 注入 (GREEN)
  - Task 3: cell_45refs + apa_45refs baseline 再生成 (--reuse-phase3 で
    LLM cost $0) + test 8 EXPECTED_THREE_CLASS_DISTRIBUTION 更新
  - Task 4: Day22 archive (README + LESSONS) + push + CI 確認

各 task は 2-5 min step に分割、exact file path + 完全 code + 期待出力を
含む. TDD 厳格 (test RED → production GREEN).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: Verify**

Run: `git log --oneline -2`
Expected: HEAD = this commit (docs(plan)…), HEAD~1 = `af9e55a` (docs(spec)…).

---

## Task 1: Add failing unit test (TDD RED)

**Files:**
- Modify: `tests/test_nlm_catalog_check.py` (append at end of file)

- [ ] **Step 1: Read current test file**

Run: `wc -l tests/test_nlm_catalog_check.py`
Expected: 78 lines (2 existing tests).

- [ ] **Step 2: Append the new test**

Open `tests/test_nlm_catalog_check.py` and append the following at the end of the file (line 79+):

```python


def test_fetch_json_uses_certifi_ssl_context(monkeypatch):
    """_fetch_json は certifi 由来の SSL context を urlopen に渡すこと.

    Day22 Rule 3 NLM SSL fix の regression guard. certifi.where() の
    cafile を持つ ssl.SSLContext が urlopen の context kwarg に渡る
    ことを mock で検証.
    """
    import io
    import ssl

    import nlm_catalog_check  # noqa: E402

    captured: dict = {}

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(url, timeout=None, context=None):
        captured["url"] = url
        captured["timeout"] = timeout
        captured["context"] = context
        return FakeResp(b'{"esearchresult": {"idlist": ["12345"]}}')

    monkeypatch.setattr(
        nlm_catalog_check.urllib.request, "urlopen", fake_urlopen
    )

    result = nlm_catalog_check._fetch_json(
        "https://eutils.ncbi.nlm.nih.gov/test", label="test"
    )

    assert result == {"esearchresult": {"idlist": ["12345"]}}
    assert isinstance(captured["context"], ssl.SSLContext), (
        f"Expected SSLContext, got {type(captured['context']).__name__}"
    )
    assert captured["context"] is nlm_catalog_check._SSL_CONTEXT, (
        "Expected the module-level _SSL_CONTEXT singleton (certifi-based)"
    )
    assert captured["timeout"] == nlm_catalog_check.TIMEOUT_SECONDS
```

- [ ] **Step 3: Run the test to verify it FAILS (TDD RED)**

Run: `python3 -m pytest tests/test_nlm_catalog_check.py::test_fetch_json_uses_certifi_ssl_context -v`

Expected: **FAIL** with `AttributeError: module 'nlm_catalog_check' has no attribute '_SSL_CONTEXT'`. This proves the test correctly probes the singleton that we are about to introduce. If the test instead PASSES, stop and investigate — the implementation may already be partially present.

- [ ] **Step 4: Confirm all OTHER tests still pass**

Run: `python3 -m pytest tests/ -q --deselect tests/test_nlm_catalog_check.py::test_fetch_json_uses_certifi_ssl_context 2>&1 | tail -5`

Expected: `100 passed, 1 skipped` (Day21 baseline, the new test deselected).

- [ ] **Step 5: Commit (TDD RED)**

```bash
git add tests/test_nlm_catalog_check.py
git commit -m "$(cat <<'EOF'
test(nlm): add failing test_fetch_json_uses_certifi_ssl_context (Day22 Phase B TDD RED)

Day22 Rule 3 NLM SSL fix の regression guard を TDD RED で先行追加.

検証内容:
  - nlm_catalog_check._fetch_json が urllib.request.urlopen を呼ぶ際、
    context kwarg に ssl.SSLContext (具体的には module-level の
    _SSL_CONTEXT singleton) を渡すこと
  - monkeypatch で urlopen を差し替えて context 引数を捕捉、type と
    identity を assert

現状 production code に _SSL_CONTEXT が未存在 → AttributeError で FAIL.
次 commit (fix(nlm)) で _SSL_CONTEXT 導入 + context 注入 → GREEN 化.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Add certifi dependency + inject SSL context (TDD GREEN)

**Files:**
- Modify: `requirements.txt`
- Modify: `nlm_catalog_check.py` (lines 41-54, 175-190)

- [ ] **Step 1: Add certifi to requirements.txt**

Open `requirements.txt`. Find the line:

```
PyYAML>=6.0,<7.0        # _load_overrides_yaml() — --overrides CLI flag
```

Insert immediately after it:

```
certifi>=2024.0,<2027.0 # Mac Python.org installer の空 cert.pem 対策。nlm_catalog_check
                        # の SSL context (Mozilla CA bundle) を deterministic に供給.
                        # Day22 Rule 3 NLM SSL fix で導入.
```

(The line before `pytest>=9.0,<10.0` should now be the certifi block.)

- [ ] **Step 2: Verify certifi is installed locally**

Run: `python3 -c "import certifi; print(certifi.__version__); print(certifi.where())"`

Expected: a version number ≥ 2024.0 and a real `.pem` path. If `ModuleNotFoundError`, run `python3 -m pip install certifi`.

- [ ] **Step 3: Modify nlm_catalog_check.py imports + add singleton**

Open `nlm_catalog_check.py`. Replace lines 41-54 (the import block + `NLM_BASE` + `TIMEOUT_SECONDS` declarations) with:

```python
from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import certifi

NLM_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
TIMEOUT_SECONDS = 10

# Module-level SSL context with certifi-provided Mozilla CA bundle.
# Day22 fix: Python.org installer (Mac) ships an empty cert.pem at
# /Library/Frameworks/Python.framework/Versions/3.X/etc/openssl/,
# causing urllib default verification to fail with SSLCertVerificationError
# against https://eutils.ncbi.nlm.nih.gov/. Using certifi.where() works on
# all OSes (Linux/Mac/Windows) deterministically.
_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
```

The diff is: +1 `import ssl`, +2 lines `import certifi` (with blank line), +7 lines of `_SSL_CONTEXT` block (with comment).

- [ ] **Step 4: Modify `_fetch_json` to pass `context=_SSL_CONTEXT`**

In the same file, find `_fetch_json` (currently around line 175-190 — line numbers shift slightly after Step 3). Replace the function body to add `context=_SSL_CONTEXT` to the `urlopen` call:

Find:

```python
def _fetch_json(url: str, *, label: str = "") -> dict | None:
    """Generic JSON fetch with 1 retry (graceful on network error)."""
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, OSError) as e:
            if attempt == 2:
                print(
                    f"WARN: nlm_catalog_check {label} failed: {e}",
                    file=sys.stderr,
                )
                return None
            continue  # retry
    return None
```

Replace with:

```python
def _fetch_json(url: str, *, label: str = "") -> dict | None:
    """Generic JSON fetch with 1 retry (graceful on network error)."""
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(
                url, timeout=TIMEOUT_SECONDS, context=_SSL_CONTEXT,
            ) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, OSError) as e:
            if attempt == 2:
                print(
                    f"WARN: nlm_catalog_check {label} failed: {e}",
                    file=sys.stderr,
                )
                return None
            continue  # retry
    return None
```

Only change: `urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS)` → `urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS, context=_SSL_CONTEXT,)` (split across 3 lines for readability).

- [ ] **Step 5: Run the previously-failing test to verify it PASSES (TDD GREEN)**

Run: `python3 -m pytest tests/test_nlm_catalog_check.py::test_fetch_json_uses_certifi_ssl_context -v`

Expected: **PASS**.

- [ ] **Step 6: Run the full test suite to confirm no regression**

Run: `python3 -m pytest tests/ -q 2>&1 | tail -5`

Expected: `101 passed, 1 skipped` (+1 new test, no regressions).

If integration tests fail with `EXPECTED_THREE_CLASS_DISTRIBUTION` mismatch, do **NOT** update those expectations here — that belongs in Task 3 after baseline regen. The failure should be in zero integration tests at this point because the SSL fix only affects *live* NLM calls, not fixture-driven tests.

- [ ] **Step 7: Verify live NLM API call now succeeds (smoke check)**

Run:
```bash
python3 -c "
import nlm_catalog_check
r = nlm_catalog_check.get_journal_indexing_status(issn='1091-7527')
print('status:', r.get('status'))
print('nlm_id:', r.get('nlm_id'))
print('medlineta:', r.get('medlineta'))
print('error:', r.get('error'))
"
```

Expected: `status: Y`, `nlm_id: 9610836`, `medlineta: Fam Syst Health`, `error: None`. If `error` contains `SSLCertVerificationError`, the fix is incomplete — re-examine Step 4.

- [ ] **Step 8: Commit (TDD GREEN)**

```bash
git add requirements.txt nlm_catalog_check.py
git commit -m "$(cat <<'EOF'
fix(nlm): inject certifi SSL context into _fetch_json (Day22 Phase B TDD GREEN)

Day22 Rule 3 NLM 検索の SSL 問題を解消.

根本原因:
  Python.org Python 3.X installer の
  /Library/Frameworks/Python.framework/Versions/3.X/etc/openssl/cert.pem
  が空ディレクトリ → urllib default SSL context が CA bundle を持たず
  https://eutils.ncbi.nlm.nih.gov/ への検証で SSLCertVerificationError
  ('self-signed certificate in certificate chain'). 結果として Day20 で
  導入した Rule 3 (NLM Catalog 直接検索) の大半が unknown に倒れていた
  (cell_45refs 8/15, apa_45refs 17/20).

修正:
  - requirements.txt に certifi>=2024.0,<2027.0 を runtime dep として追加
  - nlm_catalog_check.py module 直下に
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
    (singleton) を作成
  - _fetch_json の urllib.request.urlopen に context=_SSL_CONTEXT を渡す
  - 既存 graceful fail-soft (network/HTTP/timeout error → unknown) は不変

検証:
  - Task 1 RED で追加した test_fetch_json_uses_certifi_ssl_context が
    GREEN 化
  - 全 101 tests passed, 1 skipped (regression なし)
  - smoke: get_journal_indexing_status(issn='1091-7527') が
    status='Y', nlm_id='9610836' を取得 (Fam Syst Health)

baseline 再生成 (cell_45refs + apa_45refs) は次 commit で実施.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Regenerate cell_45refs + apa_45refs baselines + update test 8

**Files:**
- Regenerate: `tests/fixtures/cell_45refs/baseline_three_class_classification.json`
- Regenerate: `tests/fixtures/cell_45refs/baseline_report.md`
- Modify: `tests/fixtures/cell_45refs/README.md`
- Regenerate: `tests/fixtures/apa_45refs/baseline_three_class_classification.json`
- Regenerate: `tests/fixtures/apa_45refs/baseline_report.md`
- Modify: `tests/fixtures/apa_45refs/README.md`
- Modify: `tests/test_integration_cell_45refs.py:286-291`
- Modify: `tests/test_integration_apa_45refs.py:284-289`
- Possibly regenerate: `tests/fixtures/mdpi_149refs/expected_report.md` (only if affected)

**Strategy:** Use `--reuse-phase3` to skip Phase 1-3 (no LLM call, no Phase 3 PubMed re-resolution). Phase 4's `synthesize_outputs` → `three_class_classifier` → fixed `nlm_catalog_check` will produce new `three_class_classification.json` and `report.md`. Total NLM API call: ~8 (cell) + ~17 (apa) = 25 (rate-limited to ~3 req/s without API key, ~10 req/s with `NCBI_API_KEY` in `.env`).

- [ ] **Step 1: Source .env for NCBI_API_KEY**

Run:
```bash
set -a; source skill_package/.env; set +a
echo "NCBI key present: $([ -n "$NCBI_API_KEY" ] && echo yes || echo NO)"
```

Expected: `NCBI key present: yes` (if `skill_package/.env` exists). If `NO`, the regen still works but is rate-limited to 3 req/s (~10 sec for 25 calls). If `skill_package/.env` does not exist, skip the source — the LLM call key (`ANTHROPIC_API_KEY`) is not needed because we use `--reuse-phase3`.

- [ ] **Step 2: Regenerate cell_45refs baseline (Phase 4 only)**

Run:
```bash
mkdir -p /tmp/cell_45refs_day22_rerun
cp tests/fixtures/cell_45refs/baseline_phase3_resolved.json \
   /tmp/cell_45refs_day22_rerun/phase3_resolved.json
python3 main.py tests/fixtures/cell_45refs/input_References.docx \
  --output-dir /tmp/cell_45refs_day22_rerun --reuse-phase3
```

Expected:
- No "WARN: nlm_catalog_check esearch failed: ... SSLCertVerificationError" lines
- Possibly some "WARN: nlm_catalog_check esearch failed: ... HTTP 404" or "esearch returned no NLM ID" for genuinely missing journals — these are legitimate unknown
- Output files written to `/tmp/cell_45refs_day22_rerun/`: at minimum `three_class_classification.json` and `report.md`

If you see SSL errors, the fix from Task 2 is not effective — stop and investigate. If `--reuse-phase3` errors out (e.g. "phase3_resolved.json not found"), check the output dir name in `main.py` source — the expected filename may be slightly different. Adjust the `cp` target and retry.

- [ ] **Step 3: Inspect the new cell_45refs distribution**

Run:
```bash
python3 -c "
import json
data = json.loads(open('/tmp/cell_45refs_day22_rerun/three_class_classification.json').read())
dist = {'A': 0, 'B': 0, 'C': 0, 'unknown': 0}
for c in data:
    cls = c.get('class', 'unknown')
    if cls not in dist: dist[cls] = 0
    dist[cls] += 1
print('NEW cell_45refs:', dist)
print('Day20 baseline was: A=1, B=6, C=0, unknown=8')
"
```

Expected: `unknown` count should be **less than 8** (some refs moved to B or C). Record the new `A/B/C/unknown` numbers — you'll need them for Step 7. If `unknown` is still 8 (or higher), there's a deeper issue — stop and investigate Task 2 fix integrity.

- [ ] **Step 4: Copy regenerated cell baselines into fixture dir**

Run:
```bash
cp /tmp/cell_45refs_day22_rerun/three_class_classification.json \
   tests/fixtures/cell_45refs/baseline_three_class_classification.json
cp /tmp/cell_45refs_day22_rerun/report.md \
   tests/fixtures/cell_45refs/baseline_report.md
git diff --stat tests/fixtures/cell_45refs/
```

Expected: both files changed, line counts may differ from Day20.

- [ ] **Step 5: Regenerate apa_45refs baseline (Phase 4 only)**

Run:
```bash
mkdir -p /tmp/apa_45refs_day22_rerun
cp tests/fixtures/apa_45refs/baseline_phase3_resolved.json \
   /tmp/apa_45refs_day22_rerun/phase3_resolved.json
python3 main.py tests/fixtures/apa_45refs/input_References.docx \
  --output-dir /tmp/apa_45refs_day22_rerun --reuse-phase3
```

Expected: same as Step 2 but for apa fixture.

- [ ] **Step 6: Inspect new apa_45refs distribution + copy baselines**

Run:
```bash
python3 -c "
import json
data = json.loads(open('/tmp/apa_45refs_day22_rerun/three_class_classification.json').read())
dist = {'A': 0, 'B': 0, 'C': 0, 'unknown': 0}
for c in data:
    cls = c.get('class', 'unknown')
    if cls not in dist: dist[cls] = 0
    dist[cls] += 1
print('NEW apa_45refs:', dist)
print('Day20 baseline was: A=0, B=3, C=0, unknown=17')
"
cp /tmp/apa_45refs_day22_rerun/three_class_classification.json \
   tests/fixtures/apa_45refs/baseline_three_class_classification.json
cp /tmp/apa_45refs_day22_rerun/report.md \
   tests/fixtures/apa_45refs/baseline_report.md
git diff --stat tests/fixtures/apa_45refs/
```

Expected: `unknown` count should be **less than 17**. Record the new numbers.

- [ ] **Step 7: Update EXPECTED_THREE_CLASS_DISTRIBUTION in cell integration test**

Open `tests/test_integration_cell_45refs.py`. Replace lines 286-291 (the existing `EXPECTED_THREE_CLASS_DISTRIBUTION` block):

Find:
```python
EXPECTED_THREE_CLASS_DISTRIBUTION = {
    "A": 1,
    "B": 6,
    "C": 0,
    "unknown": 8,
}  # Day20 改修後実測 (README.md 参照、Day17 baseline A=14 から大幅減少)
```

Replace with (substitute `<A>`, `<B>`, `<C>`, `<unknown>` with the actual numbers from Step 3):
```python
EXPECTED_THREE_CLASS_DISTRIBUTION = {
    "A": <A>,
    "B": <B>,
    "C": <C>,
    "unknown": <unknown>,
}  # Day22 SSL fix 後実測 (README.md 参照、Day20 baseline unknown=8 から減少)
```

- [ ] **Step 8: Update EXPECTED_THREE_CLASS_DISTRIBUTION in apa integration test**

Open `tests/test_integration_apa_45refs.py`. Replace lines 284-289:

Find:
```python
EXPECTED_THREE_CLASS_DISTRIBUTION = {
    "A": 0,
    "B": 3,
    "C": 0,
    "unknown": 17,
}  # Day20 改修後実測 (README.md 参照、Day16 baseline A=4 から完全消失)
```

Replace with (substitute with actuals from Step 6):
```python
EXPECTED_THREE_CLASS_DISTRIBUTION = {
    "A": <A>,
    "B": <B>,
    "C": <C>,
    "unknown": <unknown>,
}  # Day22 SSL fix 後実測 (README.md 参照、Day20 baseline unknown=17 から減少)
```

- [ ] **Step 9: Update cell_45refs README.md with new 三分類 section**

Open `tests/fixtures/cell_45refs/README.md`. Locate the section that documents the three-class distribution (likely under a "三分類 audit" or "Day20 改修後" heading). Update the numbers to match Step 3 actuals. Add a 1-2 sentence note under or above the table:

```markdown
### Day22 SSL fix 後の更新 (2026-05-24)

Day22 で nlm_catalog_check に certifi 経由の SSL context を注入し
(commit fix(nlm)…)、Rule 3 NLM Catalog 検索が success するように
なった結果、Day20 では unknown に倒れていた 8 件 (Rule 3) の大部分が
B/C に正しく分類された。

| 三分類 | Day20 (SSL 不良) | Day22 (SSL fix 後) |
|:---:|:---:|:---:|
| A | 1 | <A> |
| B | 6 | <B> |
| C | 0 | <C> |
| unknown | 8 | <unknown> |
```

If the README already has a similar table for Day20, append the new "Day22" column rather than replacing.

- [ ] **Step 10: Update apa_45refs README.md analogously**

Open `tests/fixtures/apa_45refs/README.md`. Same pattern as Step 9 but with apa actuals and reference to Day20 baseline `A=0, B=3, C=0, unknown=17`.

- [ ] **Step 11: Run the integration tests to confirm GREEN**

Run:
```bash
python3 -m pytest tests/test_integration_cell_45refs.py::test_baseline_three_class_classification_distribution \
                   tests/test_integration_apa_45refs.py::test_baseline_three_class_classification_distribution \
                   -v
```

Expected: both PASS. If FAIL, the values in Step 7/8 don't match the regenerated baselines — re-run Step 3/6 inspection scripts to get the correct numbers and update the integration tests.

- [ ] **Step 12: Run the FULL test suite to detect any unexpected regressions (especially mdpi_149refs)**

Run:
```bash
python3 -m pytest tests/ -q 2>&1 | tail -10
```

Expected: `101 passed, 1 skipped`.

**If `tests/test_integration_149refs.py::test_synthesize_outputs_report_matches_expected` FAILS** (Day20 §3.4 PLAN gap pattern):

The mdpi_149refs stub fixture's `expected_report.md` was generated under the old SSL behavior. The SSL fix may change Phase 4 output for unresolved refs in this fixture too. To re-generate:

```bash
mkdir -p /tmp/mdpi_149refs_day22_rerun
cp tests/fixtures/mdpi_149refs/baseline_phase3_resolved.json \
   /tmp/mdpi_149refs_day22_rerun/phase3_resolved.json 2>/dev/null || true
# If the above fails (e.g. no baseline_phase3_resolved.json), examine
# tests/test_integration_149refs.py to see how the test invokes main.py
# and reproduce that exact invocation, then copy the regenerated
# expected_report.md back.
python3 main.py tests/fixtures/mdpi_149refs/input.docx \
  --output-dir /tmp/mdpi_149refs_day22_rerun --reuse-phase3 2>&1 | tail -5
cp /tmp/mdpi_149refs_day22_rerun/report.md \
   tests/fixtures/mdpi_149refs/expected_report.md
python3 -m pytest tests/test_integration_149refs.py -v 2>&1 | tail -5
```

If mdpi still fails after regeneration, **stop and ask for guidance** rather than forcing through — the mdpi_149refs fixture is the golden byte-for-byte regression test and a non-trivial change here warrants review.

- [ ] **Step 13: Commit baselines + integration test updates**

```bash
git add tests/fixtures/cell_45refs/ \
        tests/fixtures/apa_45refs/ \
        tests/test_integration_cell_45refs.py \
        tests/test_integration_apa_45refs.py
# Conditional: only if mdpi was regenerated in Step 12
git add tests/fixtures/mdpi_149refs/expected_report.md 2>/dev/null || true
git status --short
git commit -m "$(cat <<'EOF'
test(fixtures): regenerate cell + apa baselines after Rule 3 NLM SSL fix (Day22 Phase B)

Day22 fix(nlm) commit (certifi SSL context 注入) により Rule 3 NLM
Catalog 直接検索が成功するようになったため、以下を再生成:

  - tests/fixtures/cell_45refs/baseline_three_class_classification.json
  - tests/fixtures/cell_45refs/baseline_report.md
  - tests/fixtures/cell_45refs/README.md (Day22 SSL fix 後 section 追加)
  - tests/fixtures/apa_45refs/baseline_three_class_classification.json
  - tests/fixtures/apa_45refs/baseline_report.md
  - tests/fixtures/apa_45refs/README.md (同)
  - tests/test_integration_cell_45refs.py EXPECTED_THREE_CLASS_DISTRIBUTION
  - tests/test_integration_apa_45refs.py EXPECTED_THREE_CLASS_DISTRIBUTION

再生成は `main.py --reuse-phase3` で Phase 1-3 を skip し Phase 4 のみ
実行 (LLM cost $0). NLM API call は cell_45refs 8 件 + apa_45refs 17 件
程度.

[mdpi_149refs/expected_report.md が同時影響を受けた場合は本 commit に同梱.]

三分類分布の変化 (Day20 → Day22):
  - cell_45refs: A=1, B=6, C=0, unknown=8 → A=<A>, B=<B>, C=<C>, unknown=<U>
  - apa_45refs: A=0, B=3, C=0, unknown=17 → A=<A>, B=<B>, C=<C>, unknown=<U>

D20-2 教訓 (実 fixture から逆算) を踏襲し、期待値ではなく実測値で更新.

全 101 tests passed, 1 skipped.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

(Replace `<A>/<B>/<C>/<U>` placeholders in the commit message body with the actual numbers from Step 3/6 before committing.)

---

## Task 4: Day22 archive + push + CI verification

**Files:**
- Create: `docs/sessions/day22/README.md`
- Create: `docs/sessions/day22/DAY22_LESSONS_LEARNED.md`

- [ ] **Step 1: Create Day22 README.md (index)**

Create `docs/sessions/day22/README.md` with the following content. Adjust `<A>/<B>/<C>/<U>` placeholders to match the actuals from Task 3.

```markdown
# Day22 Session Archive (2026-05-24)

## 概要

Day22 セッションは 2 段構成:

- **Phase A (security)**: Day21 末セキュリティ監査で検出した 🔴 高優先 2 件を解消
  - A1: `.gitleaksignore` に Day19 報告書 4 fingerprint 追加 (commit `c0993f0`)
  - A2: GitHub Secret Scanning + Push Protection 有効化 (gh api PATCH)
- **Phase B (main)**: Rule 3 NLM 検索の SSL 問題を解消 (Day20 改修の真価発揮)

## Phase B 成果

| 指標 | Day21 末 | Day22 末 |
|:---|:---:|:---:|
| 全 tests | 100 passed / 1 skipped | 101 passed / 1 skipped |
| cell_45refs 三分類 | A=1, B=6, C=0, unknown=8 | A=<A>, B=<B>, C=<C>, unknown=<U> |
| apa_45refs 三分類 | A=0, B=3, C=0, unknown=17 | A=<A>, B=<B>, C=<C>, unknown=<U> |
| requirements.txt deps | 4 | 5 (+certifi) |

## Day22 archive 構成

- `README.md` — 本ファイル (Day22 index)
- `DAY22_LESSONS_LEARNED.md` — Day22 教訓記録
- `../../superpowers/specs/2026-05-24-rule3-nlm-ssl-fix-design.md` — Phase B brainstorming spec
- `../../superpowers/plans/2026-05-24-rule3-nlm-ssl-fix.md` — Phase B implementation plan

## Day22 commits

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `c0993f0` | chore(security) | Phase A1: Day19 報告書 4 fingerprint suppression |
| 2 | `af9e55a` | docs(spec) | Phase B brainstorming spec |
| 3 | (TBD) | docs(plan) | Phase B implementation plan |
| 4 | (TBD) | test(nlm) | TDD RED: certifi context unit test |
| 5 | (TBD) | fix(nlm) | TDD GREEN: certifi SSL context 注入 |
| 6 | (TBD) | test(fixtures) | cell + apa baseline 再生成 |
| 7 | (TBD) | docs(sessions) | Day22 archive (本 commit) |

## Day23+ 候補

- CONTRIBUTING.md / Issue PR template (Day22 handoff パターン 2)
- pre-commit hook gitleaks 自動実行 (Day22 handoff パターン 3 = Phase A B1)
- predatory journal データベース連携 (Beall's list)
- pyproject.toml + uv.lock 移行 (CLAUDE.md § 8 整合)
- SSL fix の corporate proxy 対応文書化 (USAGE_QUICKSTART)
```

Fill in the SHA placeholders (`(TBD)`) by running `git log --oneline -7` and substituting actual SHAs in order.

- [ ] **Step 2: Create Day22 LESSONS_LEARNED.md**

Create `docs/sessions/day22/DAY22_LESSONS_LEARNED.md`. Use the structure from `docs/sessions/day21/DAY21_LESSONS_LEARNED.md` as a template (sections: 概要 / brainstorming 段階 / 実装段階 / 設計判断 / 実機検証 / 教訓 / 残存タスク / 次セッション再開プロンプト). Key content:

  - §1 概要: Day21 末状態 (96 commits, 100 tests) → Day22 末 (102 commits, 101 tests)
  - §2 brainstorming Q1-Q3 + Approach A1 確定の表
  - §3 実装段階 (Phase A1/A2 + Phase B Task 0-4) の commit 一覧と各 commit 要旨
  - §4 設計判断: なぜ module-level singleton か (per-call vs build_opener vs requests 移行との比較、spec §3.3 を要約)
  - §5 実機検証: 三分類分布の Day20 vs Day22 比較 (cell + apa)
  - §6 教訓 (D22-1 と D22-2):
    - **D22-1**: Mac Python.org installer の SSL 落とし穴 (空 cert.pem の事象、certifi で deterministic 化)。OS 横断で deterministic な fix を選ぶ価値。
    - **D22-2**: Day20 で導入した logic の真価発揮には、依存環境の deterministic 化が必要だった事例。論理層と環境層を分けてデバッグする習慣。
  - §7 残存タスク (Day23+ 候補、Day22 README §Day23+ 候補と同期)
  - §8 次セッション再開時のプロンプトテンプレート (パターン 1: CONTRIBUTING.md、パターン 2: pre-commit hook、パターン 3: PyPI 公開等)

Write 2-3 paragraphs per section. Target total: 150-200 lines (Day21 LESSONS は 169 行を参考に).

- [ ] **Step 3: Verify gitleaks still clean**

Run: `gitleaks detect --no-banner --redact 2>&1 | tail -3`

Expected: `no leaks found`. If new leaks appear (unlikely from this change set), investigate before pushing.

- [ ] **Step 4: Run full test suite one more time**

Run: `python3 -m pytest tests/ -q 2>&1 | tail -5`

Expected: `101 passed, 1 skipped`.

- [ ] **Step 5: Commit Day22 archive**

```bash
git add docs/sessions/day22/
git status --short
git commit -m "$(cat <<'EOF'
docs(sessions): archive day22 Rule 3 NLM SSL fix session

Day22 セッション (2026-05-24) の archive.

構成:
  - Phase A (security): A1 = .gitleaksignore 拡張 (c0993f0),
    A2 = GitHub Secret Scanning + Push Protection 有効化
  - Phase B (main): Rule 3 NLM SSL fix (certifi 注入)
    + cell + apa baseline 再生成

成果:
  - 全 tests: 100 → 101 passed (+1 unit test for SSL context regression
    guard), 1 skipped
  - cell_45refs unknown: 8 → <U>
  - apa_45refs unknown: 17 → <U>
  - requirements.txt: certifi>=2024.0,<2027.0 を runtime dep に追加
  - gitleaks: no leaks found (継続)

教訓:
  - D22-1: Mac Python.org installer の空 cert.pem 落とし穴を certifi で
    deterministic 化、OS 横断で fix
  - D22-2: Day20 logic の真価発揮には依存環境の deterministic 化が必要
    だった、論理層と環境層を分けてデバッグする習慣

Day7 §9.3 long-term task は Day20 で完全クローズ済 (7/7).
v0.1.0 release は Day21 で公開済.
Day23+ 候補: CONTRIBUTING.md, pre-commit hook gitleaks, PyPI 公開等.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

(Replace `<U>` placeholders with actuals.)

- [ ] **Step 6: Push to origin/main**

```bash
git push origin main
git log --oneline -7
```

Expected: push succeeds without auth prompts (gh CLI is already configured). The 7 most recent commits should show the Day22 chain from `c0993f0` to the archive commit.

- [ ] **Step 7: Verify CI passes**

Run:
```bash
sleep 30  # give GitHub Actions time to start
gh run list --limit 3 --json conclusion,name,headSha,status
```

Expected: most recent run for our HEAD SHA shows `status: completed, conclusion: success`. If `in_progress`, re-run after another 30-60 sec. If `failure`, run `gh run view <run-id> --log-failed | tail -50` and address.

- [ ] **Step 8: Final verification**

Run:
```bash
git status
git log --oneline -7
python3 -m pytest tests/ -q 2>&1 | tail -3
gh release view v0.1.0 --json tagName,isDraft 2>&1 | head -3
```

Expected:
- working tree clean
- 7 Day22 commits in the log
- 101 passed, 1 skipped
- v0.1.0 release still exists (not damaged by this work)

Day22 complete.

---

## Self-Review Summary

| Check | Result |
|:---|:---|
| Spec coverage — every section in `2026-05-24-rule3-nlm-ssl-fix-design.md` mapped to a task | §1-2 background → Task 0 (plan); §3 implementation → Task 1+2; §4 testing → Task 1+3; §5 commits → Tasks 0-4; §6 完了条件 → Task 4 Step 8; §7 工数 → embedded; §8 リスク → embedded; §9 out of scope → Day22 archive Day23+ section |
| Placeholder scan | `<A>/<B>/<C>/<U>` in Task 3/4 are intentional runtime-substitution placeholders (numbers known only after baseline regen). `(TBD)` SHAs in archive README are also intentional (known after commits land). All other content is concrete. |
| Type consistency | `_SSL_CONTEXT` singleton name used consistently across Task 1 test, Task 2 implementation, and Task 2 verification. `EXPECTED_THREE_CLASS_DISTRIBUTION` constant name unchanged. `context=_SSL_CONTEXT` kwarg form consistent. |
| TDD ordering | Task 1 = RED (test fails) → Task 2 = GREEN (implementation makes test pass). Verified by Task 1 Step 3 expected output. |

---

## Execution Handoff

Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** — execute tasks in this session with checkpoints for human review

Choose by responding with `subagent` or `inline`.
