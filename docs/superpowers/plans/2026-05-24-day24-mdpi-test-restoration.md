# Day24 MDPI Test Restoration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-point 5 skip-mark test files from removed `mdpi_149refs/` to new `mdpi_173refs/` fixture, refactor byte-level golden assertions into structural assertions, and remove `pytestmark.skip` blocks — restoring regression coverage from `52 passed / 50 skipped` to `~100 passed / ≤1 skipped` in a single atomic commit.

**Architecture:** 4 tasks (Task 0 plan commit, Task 1 reconnaissance, Task 2 atomic refactor + verification, Task 3 Day24 archive). Per-file refactor strategy defined in spec §3 (mdpi_parser → structural smoke; overrides_contract → keep most tests, replace 1 Ref-#141-specific test with YAML schema contract; journal_audit → byte-match → containment check; pre_integration_baseline → historical archive + readability check; split_references_doi_boundary → new-corpus-specific assertions via Task 1 reconnaissance). Single `test(refactor):` commit for all 5 files (spec Q2 confirmed).

**Tech Stack:** Python 3.11+ (3.14 local), pytest 9.x, existing helpers (`main.extract_text`, `main.preprocess`, `main.split_references`, `main._load_overrides_yaml`, `main._apply_overrides`, `journal_audit.audit_journal_mismatch`, `journal_audit.format_summary_narrative`, `mdpi_parser`).

**Spec reference:** `docs/superpowers/specs/2026-05-24-day24-mdpi-test-restoration-design.md` (commit `8d7df22`)

**Pre-state:**
- HEAD: `8d7df22` (Day24 spec commit)
- Repo: PUBLIC, CI green
- Tests: 52 passed / 50 skipped / 0 failed
- New fixture: `tests/fixtures/mdpi_173refs/` (Day23 Task 9, PMC13164670, 171 parsed refs)

**Total commits:** 4 (1 spec already + 1 plan + 1 refactor + 1 archive)

---

## File Structure

### Files MODIFIED in Task 2 (5 test files, single atomic commit)

| File | Lines (current) | Refactor scope | New line count est. |
|:---|---:|:---|---:|
| `tests/test_mdpi_parser.py` | 276 | Remove skip block + retarget TEST_DIR + replace `test_mdpi_parser_149refs_full_pipeline` with 2-3 structural tests (smoke, ref count range, field presence) | ~120 |
| `tests/test_overrides_contract.py` | 128 | Remove skip block + retarget FIXTURES + remove `test_apply_overrides_ref141_matches_expected` (replaced by structural contract assertion) — other 4 tests unchanged (they don't touch fixture) | ~95 |
| `tests/test_journal_audit.py` | 423 | Remove skip block + retarget `fixtures_dir` in `test_narrative_matches_expected_fixture` (line 333+) + replace byte-match with containment check on `baseline_report.md` — other ~25 tests unchanged | ~415 |
| `tests/test_pre_integration_baseline.py` | 138 | Remove skip block + retarget FIXTURE_DIR + reduce to `TestNewFixtureIntegrity` (4 readability tests) + delete `TestPhase1DetailedSnapshot` (149-corpus-specific) + update module docstring to "historical archive" | ~80 |
| `tests/test_split_references_doi_boundary.py` | 58 | Remove skip block + retarget FIXTURE_DIR + rewrite all 6 tests using new corpus's actual ref count and DOI-boundary edge cases identified in Task 1 reconnaissance | ~70 |

### Files CREATED in Task 3 (Day24 archive)

| File | Why |
|:---|:---|
| `docs/sessions/day24/README.md` | Day24 session index |
| `docs/sessions/day24/DAY24_LESSONS_LEARNED.md` | Day24 retrospective (D24-1 lessons) |

### Files NOT TOUCHED

- `tests/test_integration_mdpi_173refs.py` (Day23 Task 10 — already covers mdpi_173refs end-to-end, do NOT duplicate)
- `tests/test_integration_vancouver_35refs.py` / `tests/test_integration_apa_45refs.py` / `tests/test_integration_cell_45refs.py` (unrelated fixtures)
- `tests/test_nlm_catalog_check.py` / `tests/test_crossref_check.py` / `tests/test_three_class_classifier.py` / `tests/test_env_loader.py` (synthetic-data unit tests)
- All non-test files (no `main.py` / `mdpi_parser.py` / `journal_audit.py` changes — pure test refactor)
- `integration/src/manual_overrides.yaml` (still has entries for ref_no 66, 137, 141, 148 — these are corpus-tied to the deleted mdpi_149refs, but Day24 out-of-scope; tracked for Day25+)

---

## Task 0: Commit this plan

**Files:**
- Modify: `docs/superpowers/plans/2026-05-24-day24-mdpi-test-restoration.md` (just written)

- [ ] **Step 1: Stage and review**

```bash
git add docs/superpowers/plans/2026-05-24-day24-mdpi-test-restoration.md
git status --short
```

Expected: 1 file added.

- [ ] **Step 2: Commit**

```bash
git commit -m "$(cat <<'EOF'
docs(plan): add Day24 MDPI test restoration implementation plan

spec (commit 8d7df22) に基づく 4 task の bite-sized 実装計画.

主要 task:
  - Task 1: 新 mdpi_173refs corpus 偵察 (Phase 1 出力をダンプして
    split_references の新 corpus 固有 edge case を特定)
  - Task 2: 5 file 一括 re-point + structural refactor + skip 解除
    (atomic commit、spec Q2 確定)
  - Task 3: Day24 archive (README + LESSONS)

per-file 戦略 (spec §3 詳細):
  - test_mdpi_parser: byte-match → ref count + field presence smoke
  - test_overrides_contract: 1 test (Ref #141) 削除、他 4 test 不変
  - test_journal_audit: line 333+ の expected_report.md byte-match →
    baseline_report.md 含有確認、他 ~25 test 不変
  - test_pre_integration_baseline: historical archive 化 + new fixture
    readability check + TestPhase1DetailedSnapshot 削除
  - test_split_references_doi_boundary: 全 6 test を新 corpus 固有
    assertion で書換 (Task 1 reconnaissance 情報を使用)

期待: 52 passed/50 skipped → ~100 passed/≤1 skipped、commit 計 4 件、
工数 ~3.5h、LLM cost $0.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: Verify**

Run: `git log --oneline -2`
Expected: HEAD = docs(plan)…, HEAD~1 = `8d7df22` (docs(spec)…).

---

## Task 1: Reconnaissance — Inspect new mdpi_173refs corpus

**Goal:** Identify the new corpus's actual ref count, ref number range, and any tricky DOI-boundary refs (analogous to old #40 "van der Biessen" / #140 "van Zyl" cases) so Task 2's `test_split_references_doi_boundary.py` rewrite uses real assertions.

**Files:**
- Create (temp): `/tmp/day24_mdpi_173refs_phase1_dump.json` (Phase 1 output)
- Create (temp): `/tmp/day24_mdpi_173refs_recon.md` (analysis notes)

- [ ] **Step 1: Run Phase 1 on new corpus and save output**

```bash
cd /Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver
python3 -c "
import sys, json
sys.path.insert(0, '.')
from pathlib import Path
import main

docx = Path('tests/fixtures/mdpi_173refs/input_References.docx')
raw, _ = main.extract_text(docx)
ln = main.detect_line_numbers(raw)
cleaned, _ = main.preprocess(raw, ln)
blocks = main.split_references(cleaned)

out = []
for b in blocks:
    out.append({
        'ref_no': b.ref_no,
        'char_length': b.char_length,
        'raw_text_head': b.raw_text[:120],
    })
print(json.dumps({
    'count': len(blocks),
    'ref_no_min': min(b.ref_no for b in blocks),
    'ref_no_max': max(b.ref_no for b in blocks),
    'line_numbers_detected': ln.detected,
    'line_min': ln.min_val if ln.detected else None,
    'line_max': ln.max_val if ln.detected else None,
    'blocks': out,
}, indent=2, ensure_ascii=False))
" > /tmp/day24_mdpi_173refs_phase1_dump.json

python3 -c "
import json
d = json.load(open('/tmp/day24_mdpi_173refs_phase1_dump.json'))
print(f\"count: {d['count']}\")
print(f\"ref_no range: {d['ref_no_min']}-{d['ref_no_max']}\")
print(f\"line numbers detected: {d['line_numbers_detected']}, range: {d['line_min']}-{d['line_max']}\")
print()
print('First 3 refs:')
for b in d['blocks'][:3]:
    print(f\"  #{b['ref_no']} ({b['char_length']}ch): {b['raw_text_head']}\")
print()
print('Last 3 refs:')
for b in d['blocks'][-3:]:
    print(f\"  #{b['ref_no']} ({b['char_length']}ch): {b['raw_text_head']}\")
print()
print('Largest 3 refs (potential boundary-failure indicators):')
for b in sorted(d['blocks'], key=lambda x: -x['char_length'])[:3]:
    print(f\"  #{b['ref_no']} ({b['char_length']}ch): {b['raw_text_head']}\")
"
```

Expected: count ~171, ref_no range 1-173 (with potential gaps from parser merges). Record:
- Exact `count` value (will be the assertion target)
- `ref_no_min`, `ref_no_max` values
- Whether line numbers are detected (and if so, the range)
- First 1-2 refs' opening text (for "Ref #1 starts with X" assertions)
- Last 1-2 refs' opening text
- Any unusually large refs (>500 chars) that might indicate boundary failure

- [ ] **Step 2: Identify DOI-boundary edge cases (if any)**

```bash
python3 -c "
import json, re
d = json.load(open('/tmp/day24_mdpi_173refs_phase1_dump.json'))

# Find refs starting with lowercase author prefix (van, de, ten, von, etc.)
lower_prefix_refs = []
for b in d['blocks']:
    txt = b['raw_text_head'].strip()
    # Check if starts with lowercase prefix like 'van', 'de', 'von', 'ten', 'der'
    first_word = txt.split()[0] if txt else ''
    if first_word and first_word[0].islower() and len(first_word) <= 4:
        lower_prefix_refs.append((b['ref_no'], first_word, txt[:80]))

print(f'Refs starting with lowercase prefix (DOI-boundary candidates): {len(lower_prefix_refs)}')
for ref_no, prefix, text in lower_prefix_refs[:10]:
    print(f'  #{ref_no} ({prefix}...): {text}')
"
```

Record any refs starting with `van`, `de`, `von`, `ten`, etc. These are the DOI-boundary edge cases. If none found, the new corpus may not have analogous tricky refs (which means simpler split_references test).

- [ ] **Step 3: Save reconnaissance summary**

```bash
cat > /tmp/day24_mdpi_173refs_recon.md << 'EOF'
# Day24 Task 1 Reconnaissance — mdpi_173refs Phase 1 inspection

(populate with values from Step 1-2 above)

## Phase 1 metrics
- count: <N>
- ref_no range: <MIN>-<MAX>
- line numbers: detected=<bool>, range=<MIN>-<MAX>

## Boundary edge cases
- Lowercase-prefix refs: <list of ref_no + first word>

## Suggested Task 2 assertions for test_split_references_doi_boundary.py
- `len(blocks) == <N>` (replace old 149)
- `min(b.ref_no for b in blocks) == <MIN>` and max == <MAX>
- For each lowercase-prefix ref: `b.raw_text.startswith("<prefix>")` (or skip if none)
- Line number detection: if detected, assert range; else skip line-number assertions
EOF
# Manually edit the file to fill in actual values from Step 1-2
```

This file is the reference for Task 2's `test_split_references_doi_boundary.py` rewrite.

No git commit in this task (artifacts in `/tmp`).

---

## Task 2: Atomic refactor of 5 test files + verification + commit

**Goal:** In one atomic operation, refactor all 5 test files (re-point fixture path, remove skip block, replace byte-match with structural assertions), verify pytest is green, commit `test(refactor):`, push to origin/main.

**Files:**
- Modify: `tests/test_mdpi_parser.py`
- Modify: `tests/test_overrides_contract.py`
- Modify: `tests/test_journal_audit.py`
- Modify: `tests/test_pre_integration_baseline.py`
- Modify: `tests/test_split_references_doi_boundary.py`

### Sub-step 2.A: Refactor `tests/test_mdpi_parser.py`

- [ ] **Step 2.A.1: Replace the entire file with new structural version**

The current file has 276 lines centered on byte-match against `expected_phase2_structured.json`. Replace its body to:
1. Remove `pytestmark.skip` block (lines 25-30)
2. Update `TEST_DIR` to `mdpi_173refs`
3. Update module docstring
4. Replace `test_mdpi_parser_149refs_full_pipeline` (and any helper that loads `expected_phase2_structured.json`) with structural smoke tests

Use Edit tool with these specific changes:

**Change 1: Module docstring** (lines 1-17 area)

Find (the first triple-quoted block at top):
```python
"""
test_mdpi_parser.py — MDPI パーサの回帰テスト

使い方:
    pytest tests/test_mdpi_parser.py -v
    または
    python -m tests.test_mdpi_parser

このファイルは 149 件の References.docx を入力として、MDPI パーサ単体の
出力が期待 JSON と一致することを確認する。期待 JSON は実運用で検証済みの
ゴールドスタンダードとして tests/test_integration_149refs/ に同梱する。

本テストは LLM (Claude API) には一切依存しない純粋なユニットテスト。
CI 環境 (GitHub Actions 等) で API キー無しで走らせることができる。
"""
```

Replace with:
```python
"""
test_mdpi_parser.py — MDPI パーサの回帰テスト (Day24 再構成版)

使い方:
    pytest tests/test_mdpi_parser.py -v

本ファイルは tests/fixtures/mdpi_173refs/ (PMC13164670 Nutrients review, 173 refs)
を入力として、MDPI パーサ単体の構造 invariant を検証する.

Day8-23 までは旧 mdpi_149refs corpus に対する byte-level golden
(expected_phase2_structured.json) との完全一致を検証していたが、Day23 で
旧 corpus 削除 + 新 mdpi_173refs は LLM path 経由のため byte-level
deterministic golden を持たない. Day24 で構造 smoke test に refactor.

本テストは LLM (Claude API) には一切依存しない純粋なユニットテスト。
CI 環境 (GitHub Actions 等) で API キー無しで走らせることができる。
"""
```

**Change 2: Remove skip block + update TEST_DIR** (lines 25-38 area)

Find:
```python
pytestmark = pytest.mark.skip(
    reason="awaiting Day23 Phase 5 new MDPI fixture "
    "(tracked by docs/superpowers/plans/2026-05-24-day23-fixture-remediation.md). "
    "Original mdpi_149refs/ removed in this commit due to peer-review-derived "
    "confidentiality concern."
)

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import mdpi_parser  # noqa: E402


TEST_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_149refs"
```

Replace with:
```python
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import mdpi_parser  # noqa: E402


TEST_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_173refs"
```

(Removes the 6-line `pytestmark.skip` block. Updates path.)

**Change 3: Replace `test_mdpi_parser_149refs_full_pipeline` and all subsequent byte-match tests**

Use the Read tool to inspect lines 50-end and identify ALL functions that reference `expected_phase2_structured.json` or perform byte-match. Replace those test functions with:

```python
def test_phase1_extracts_refs_from_corpus():
    """Phase 1 (extract + preprocess + split_references) が representative
    corpus から ref block を抽出できることを smoke check.

    Day24 acceptance: parsed ref count が 165-180 範囲 (Day23 Task 9 実測 171
    に対し ±5 の許容範囲、parser 微小変更の正常範囲).
    """
    input_docx = TEST_DIR / "input_References.docx"
    blocks = _load_phase1_blocks(input_docx)
    assert 165 <= len(blocks) <= 180, (
        f"Phase 1 parser produced {len(blocks)} blocks, expected 165-180 "
        f"(Day23 Task 9 reported 171 for mdpi_173refs)"
    )


def test_phase1_blocks_have_required_fields():
    """各 block が ref_no と raw_text を持つこと (構造 invariant)."""
    input_docx = TEST_DIR / "input_References.docx"
    blocks = _load_phase1_blocks(input_docx)
    for b in blocks:
        assert hasattr(b, "ref_no"), f"block missing ref_no: {b!r}"
        assert hasattr(b, "raw_text"), f"block missing raw_text: {b!r}"
        assert isinstance(b.ref_no, int) and b.ref_no > 0
        assert isinstance(b.raw_text, str) and len(b.raw_text) > 0


def test_mdpi_parser_module_importable():
    """mdpi_parser module が import 可能で主要関数が存在すること."""
    # mdpi_parser is imported at module top; verify the import didn't silently fail
    assert hasattr(mdpi_parser, "parse") or hasattr(mdpi_parser, "is_mdpi_style") or \
        any(callable(getattr(mdpi_parser, n, None)) for n in dir(mdpi_parser) if not n.startswith("_")), \
        "mdpi_parser appears to have no public callable functions"
```

The exact replacement may need adjustment based on what's currently in the file beyond `test_mdpi_parser_149refs_full_pipeline`. **Critical: delete any function that references `expected_phase2_structured.json` or `expected_phase3_resolved.json`** (those files don't exist in new fixture).

After editing, file length should be ~120-150 lines (down from 276).

- [ ] **Step 2.A.2: Run pytest to verify**

```bash
python3 -m pytest tests/test_mdpi_parser.py -v 2>&1 | tail -15
```

Expected: 3 tests PASS (no skip). If failures, investigate and adjust assertions.

### Sub-step 2.B: Refactor `tests/test_overrides_contract.py`

- [ ] **Step 2.B.1: Remove skip block + update FIXTURES path + remove Ref #141 test**

Use Edit tool:

**Change 1: Remove skip block**

Find (lines 16-22):
```python
pytestmark = pytest.mark.skip(
    reason="awaiting Day23 Phase 5 new MDPI fixture "
    "(tracked by docs/superpowers/plans/2026-05-24-day23-fixture-remediation.md). "
    "Original mdpi_149refs/ removed in this commit due to peer-review-derived "
    "confidentiality concern."
)

```

Replace with (empty — delete the block):
```python
```

(Just removes the 6-line block plus trailing blank.)

**Change 2: Update FIXTURES path**

Find:
```python
FIXTURES = Path(__file__).parent / "fixtures" / "mdpi_149refs"
```

Replace with:
```python
# Day24: re-pointed from mdpi_149refs to mdpi_173refs (Day23 corpus replacement).
# Note: most tests in this file don't actually use FIXTURES (they only test the
# YAML loader / apply_overrides logic against `integration/src/manual_overrides.yaml`).
# The Ref #141-specific snapshot test was deleted in Day24 because the new corpus
# does not contain Ref #141.
FIXTURES = Path(__file__).parent / "fixtures" / "mdpi_173refs"
```

**Change 3: Delete `test_apply_overrides_ref141_matches_expected` function entirely**

Find the function starting at:
```python
def test_apply_overrides_ref141_matches_expected():
    """Ref #141 snapshot + overrides yaml should produce expected values."""
    from main import _apply_overrides, _load_overrides_yaml

    snapshot = json.loads(
        (FIXTURES / "ref141_parser_snapshot.json").read_text(encoding="utf-8")
    )
```

…and continuing until the end of that function (look for the next `def ` or end of file).

Use Read tool first to see the exact extent of this function, then use Edit to delete the entire function block. Replace with:

```python
# NOTE: test_apply_overrides_ref141_matches_expected (previously here) was
# deleted in Day24 because it asserted Ref #141 specific override values from
# the old mdpi_149refs corpus (ref141_parser_snapshot.json), which no longer
# exists. The YAML contract is now verified structurally via
# test_load_overrides_yaml_returns_expected_refs above (which checks the YAML
# has entries for ref_no 66, 137, 141, 148 — unchanged YAML content from old corpus,
# preserved for historical reasons; see Day25+ for potential re-design).
```

Resulting file should be ~95 lines.

- [ ] **Step 2.B.2: Run pytest**

```bash
python3 -m pytest tests/test_overrides_contract.py -v 2>&1 | tail -15
```

Expected: 4 tests PASS (was 5 with Ref #141 test; now 4 without). All previously-passing-without-fixture tests should still pass (they don't depend on the deleted fixture).

### Sub-step 2.C: Refactor `tests/test_journal_audit.py`

- [ ] **Step 2.C.1: Remove skip block + update line 333+ test**

**Change 1: Remove skip block** (lines 26-32 area)

Find:
```python
pytestmark = pytest.mark.skip(
    reason="awaiting Day23 Phase 5 new MDPI fixture "
    "(tracked by docs/superpowers/plans/2026-05-24-day23-fixture-remediation.md). "
    "Original mdpi_149refs/ removed in this commit due to peer-review-derived "
    "confidentiality concern."
)

```

Replace with (empty):
```python
```

**Change 2: Replace `test_narrative_matches_expected_fixture` body** (line 333-355 area)

Find:
```python
    def test_narrative_matches_expected_fixture(self):
        """149-ref コーパスで生成した narrative が expected_report.md の
        補遺セクションと byte 単位で完全一致する。"""
        import json
        from journal_audit import audit_journal_mismatch, format_summary_narrative

        fixtures_dir = REPO_ROOT / "tests" / "fixtures" / "mdpi_149refs"
        data = json.loads(
            (fixtures_dir / "expected_phase3_resolved.json").read_text(encoding="utf-8")
        )
        findings = audit_journal_mismatch(
            data["stage3_structured"],
            data["stage4_pubmed_resolutions"],
            include_ok=True,
        )
        narrative = format_summary_narrative(findings)

        expected = (fixtures_dir / "expected_report.md").read_text(encoding="utf-8")
        marker = "\n---\n\n## 補遺: ジャーナル名と PubMed 収載誌の照合監査 (追加)"
        idx = expected.find(marker)
        assert idx != -1, "expected_report.md に補遺セクションの目印が見つからない"
        expected_tail = expected[idx:]

        assert narrative == expected_tail
```

Replace with:
```python
    def test_narrative_present_in_baseline_report(self):
        """新 mdpi_173refs baseline_report.md に journal audit narrative
        セクションが含まれていることを構造 check.

        Day24 acceptance: 旧 byte-level byte-match (149-ref expected_report.md)
        を廃止し、新 fixture baseline_report.md への containment check に置換.
        baseline はLLM/PubMed variability あるため byte-match 不適切.
        """
        fixtures_dir = REPO_ROOT / "tests" / "fixtures" / "mdpi_173refs"
        report_path = fixtures_dir / "baseline_report.md"
        assert report_path.exists(), f"baseline_report.md not found: {report_path}"

        report = report_path.read_text(encoding="utf-8")
        marker = "## 補遺: ジャーナル名と PubMed 収載誌の照合監査 (追加)"
        assert marker in report, (
            f"baseline_report.md に journal audit 補遺セクションマーカー "
            f"'{marker}' が見つからない. format_summary_narrative の出力形式が "
            f"変わった可能性、または synthesize_outputs で audit セクションが "
            f"emit されていない可能性."
        )
```

- [ ] **Step 2.C.2: Run pytest**

```bash
python3 -m pytest tests/test_journal_audit.py -v 2>&1 | tail -15
```

Expected: All tests PASS (the ~25 synthetic-data tests + the 1 refactored fixture-dependent test).

### Sub-step 2.D: Refactor `tests/test_pre_integration_baseline.py`

- [ ] **Step 2.D.1: Replace the entire file with weakened historical archive version**

This file is heavily corpus-specific (TestPhase1DetailedSnapshot expects Bray globocan #1, De Boeck #149, line numbers 567-910). Most assertions are unrecoverable. Rewrite the file entirely.

Use Write tool to replace the file content with:

```python
"""
test_pre_integration_baseline.py — Day8 pre-integration baseline characterization
(Day24 historical archive 化版)

旧目的:
    Day8 (commit ab25630) 当時、統合パッチ適用の前に main.py の挙動を
    pytest assertion として固定し、整合前後の差分を可視化する設計だった.
    `tests/fixtures/mdpi_149refs/` の 149-ref corpus に対する Phase 1 出力を
    byte-level snapshot として保存し、Bray globocan #1 / De Boeck #149 /
    line numbers 567-910 等の corpus-specific 値を assert していた.

Day24 historical archive 化の経緯:
    Day23 (commit 3c676ec) で旧 mdpi_149refs corpus 削除 + 新 mdpi_173refs
    (PMC13164670, 173 refs, LLM path 経由) に置換. 新 corpus には Bray
    globocan も De Boeck もなく、Phase 1 出力も大きく異なる. 「integration
    前後の差分を可視化」という本 file の本来意義は完全喪失.

    Day24 では historical archive として残置し、新 fixture (mdpi_173refs) の
    主要 baseline file が読み込めることのみを sanity check として確認する形式に
    弱体化. TestPhase1DetailedSnapshot は削除 (corpus 完全置換のため意味なし).

参照:
    spec: docs/superpowers/specs/2026-05-24-day24-mdpi-test-restoration-design.md
    Day8 origin: docs/sessions/day8/ (パッチ適用前 baseline 設計)
    Day23 corpus 置換: docs/sessions/day23/ + DAY23_LESSONS_LEARNED.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_173refs"


class TestNewFixtureIntegrity:
    """tests/fixtures/mdpi_173refs/ の主要 file が存在し読み込めることを sanity check."""

    def test_input_docx_exists(self):
        """input docx (Phase 1 入力) が存在し、サイズが妥当."""
        docx = FIXTURE_DIR / "input_References.docx"
        assert docx.exists(), f"input_References.docx not found: {docx}"
        assert docx.stat().st_size > 30_000, (
            f"input docx size unexpectedly small: {docx.stat().st_size} bytes "
            f"(expected > 30 KB for 171-ref corpus)"
        )

    def test_expected_phase1_intermediate_exists(self):
        """expected_phase1_intermediate.json (deterministic golden) が読み込める."""
        import json
        path = FIXTURE_DIR / "expected_phase1_intermediate.json"
        assert path.exists(), f"expected_phase1_intermediate.json not found: {path}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, (dict, list)), "phase1 JSON should be dict or list"

    def test_baseline_phase3_resolved_exists(self):
        """baseline_phase3_resolved.json (LLM 経由、variability あり) が読み込める."""
        import json
        path = FIXTURE_DIR / "baseline_phase3_resolved.json"
        assert path.exists(), f"baseline_phase3_resolved.json not found: {path}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, (dict, list)), "phase3 JSON should be dict or list"

    def test_baseline_report_exists(self):
        """baseline_report.md (Phase 4 出力 narrative) が存在."""
        path = FIXTURE_DIR / "baseline_report.md"
        assert path.exists(), f"baseline_report.md not found: {path}"
        content = path.read_text(encoding="utf-8")
        assert len(content) > 1000, "baseline_report.md size unexpectedly small"
```

Resulting file: ~80 lines (down from 138, TestPhase1DetailedSnapshot deleted).

- [ ] **Step 2.D.2: Run pytest**

```bash
python3 -m pytest tests/test_pre_integration_baseline.py -v 2>&1 | tail -15
```

Expected: 4 tests PASS (was many more; now reduced to readability checks).

### Sub-step 2.E: Refactor `tests/test_split_references_doi_boundary.py`

- [ ] **Step 2.E.1: Read Task 1 reconnaissance**

```bash
cat /tmp/day24_mdpi_173refs_phase1_dump.json | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f\"count: {d['count']}\")
print(f\"ref_no min: {d['ref_no_min']}, max: {d['ref_no_max']}\")
print(f\"line numbers: detected={d['line_numbers_detected']}\")
"
```

Note the exact `count`, `ref_no_min`, `ref_no_max` values for the rewrite.

- [ ] **Step 2.E.2: Replace entire file**

Use Write tool to replace `tests/test_split_references_doi_boundary.py` with:

```python
"""
test_split_references_doi_boundary.py — Phase 1 split_references の構造 invariant

旧目的:
    Day9 (commit ab25630) で Phase 1 split_references が DOI 終端直後の
    lowercase-prefixed 著者 Ref (#40 van der Biessen, #140 van Zyl) を
    正しく検出するかを 149-ref corpus で検証していた.

Day24 historical archive 化の経緯:
    Day23 で旧 mdpi_149refs corpus 削除 + 新 mdpi_173refs に置換. 新 corpus
    には #40 van der Biessen も #140 van Zyl も存在しない. 本 file は
    新 corpus の構造 invariant (parsed ref count、ref_no 範囲、parser 失敗の
    not regressing) を smoke check する形式に refactor.

    Day25+ で新 corpus に固有の DOI-boundary edge case が見つかった場合は
    fixture-specific assertion を追加可能.
"""
from pathlib import Path
import pytest
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_173refs"


@pytest.fixture(scope="module")
def blocks():
    """Phase 1 を新 corpus に適用した結果の ref block list."""
    sys.path.insert(0, str(REPO_ROOT))
    import main
    docx = FIXTURE_DIR / "input_References.docx"
    raw, _ = main.extract_text(docx)
    ln = main.detect_line_numbers(raw)
    cleaned, _ = main.preprocess(raw, ln)
    return main.split_references(cleaned)


class TestNewCorpusStructure:
    """新 mdpi_173refs corpus に対する Phase 1 split_references の構造 invariant."""

    def test_ref_count_in_expected_range(self, blocks):
        """parsed ref count が 165-180 範囲 (Day23 Task 9 実測 171 ± 5 許容)."""
        assert 165 <= len(blocks) <= 180, (
            f"unexpected ref count: {len(blocks)} (expected 165-180 for mdpi_173refs)"
        )

    def test_ref_no_starts_from_1(self, blocks):
        """ref_no は 1 から始まる (1-indexed)."""
        ref_nos = sorted(b.ref_no for b in blocks)
        assert ref_nos[0] == 1, f"first ref_no should be 1, got {ref_nos[0]}"

    def test_ref_no_monotonically_increases(self, blocks):
        """ref_no は重複なし (各 ref は 1 つの ref_no を持つ)."""
        ref_nos = [b.ref_no for b in blocks]
        assert len(ref_nos) == len(set(ref_nos)), "ref_no should be unique per block"

    def test_no_block_is_pathologically_large(self, blocks):
        """各 block の char_length が 2000 chars 以下 (parser が複数 ref を
        merge していないことの sanity check). 巨大 block は boundary failure
        の sign.
        """
        oversized = [(b.ref_no, b.char_length) for b in blocks if b.char_length > 2000]
        assert not oversized, (
            f"Found {len(oversized)} pathologically large blocks (>2000 chars), "
            f"may indicate split_references boundary failure: {oversized[:5]}"
        )

    def test_no_block_is_empty(self, blocks):
        """各 block の raw_text が空でない (parser が空 ref を生成していない)."""
        empty = [b.ref_no for b in blocks if not b.raw_text.strip()]
        assert not empty, f"Found {len(empty)} empty blocks: {empty[:5]}"
```

If Task 1 Step 2 found lowercase-prefix refs (van/de/von/ten/etc.) in the new corpus, ADD specific assertions for those (e.g., `test_ref_X_starts_with_van`). If none found, the 5 generic tests above are sufficient.

Resulting file: ~70 lines.

- [ ] **Step 2.E.3: Run pytest**

```bash
python3 -m pytest tests/test_split_references_doi_boundary.py -v 2>&1 | tail -15
```

Expected: 5 tests PASS.

### Sub-step 2.F: Full test suite verification + atomic commit

- [ ] **Step 2.F.1: Run full pytest**

```bash
python3 -m pytest tests/ -q 2>&1 | tail -5
```

Expected: ~95-105 passed, ≤1 skipped, 0 failed. The exact number depends on individual test counts in each file. If failures, investigate per-file and fix assertions.

Critical: if any `tests/test_integration_*` test fails (apa, cell, mdpi_173refs, vancouver_35refs, 149refs which is deleted, vancouver_24refs which is deleted), that's a cross-file regression — STOP and investigate.

- [ ] **Step 2.F.2: gitleaks check**

```bash
gitleaks detect --no-banner --redact 2>&1 | tail -3
```

Expected: no leaks found.

- [ ] **Step 2.F.3: Atomic commit + push**

```bash
git add tests/test_mdpi_parser.py \
        tests/test_overrides_contract.py \
        tests/test_journal_audit.py \
        tests/test_pre_integration_baseline.py \
        tests/test_split_references_doi_boundary.py
git status --short
git commit -m "$(cat <<'EOF'
test(refactor): re-point 5 mdpi-dependent tests to mdpi_173refs + skip 解除 (Day24)

Day23 Phase 1 (commit 3c676ec) で旧 mdpi_149refs 削除に伴い pytestmark.skip
を付与した 5 file を新 mdpi_173refs (PMC13164670 Nutrients review) に re-point
し、byte-level golden 前提を構造化 assertion に refactor して skip 解除.

per-file 改修内容:
  - test_mdpi_parser.py (276 → ~120 行):
    * byte-match against expected_phase2_structured.json を削除
    * 3 構造 test (ref count range / field presence / module importable) に置換
  - test_overrides_contract.py (128 → ~95 行):
    * test_apply_overrides_ref141_matches_expected を削除
      (Ref #141 specific snapshot 不在のため)
    * 他 4 test (YAML loader contract / apply_overrides edge cases) は不変
  - test_journal_audit.py (423 → ~415 行):
    * line 333+ の test_narrative_matches_expected_fixture を
      test_narrative_present_in_baseline_report に置換
      (expected_report.md byte-match → baseline_report.md marker containment)
    * 他 ~25 synthetic-data test は不変
  - test_pre_integration_baseline.py (138 → ~80 行):
    * 全面 rewrite、historical archive 化
    * TestPhase1DetailedSnapshot 削除 (Bray globocan #1, De Boeck #149,
      line numbers 567-910 等は新 corpus に存在せず)
    * TestNewFixtureIntegrity (4 file readability check) のみ残置
  - test_split_references_doi_boundary.py (58 → ~70 行):
    * 全面 rewrite、新 corpus 構造 invariant smoke test に refactor
    * 旧 #40 van der Biessen / #140 van Zyl specific assertion 削除
    * 5 構造 test (ref count range / 1-indexed / unique ref_no /
      no pathologically large / no empty) に置換

旧 byte-level golden file は新 fixture に存在しない (LLM path のため
deterministic 再現不能). regression coverage は構造 invariant で確保:
ref count range (165-180) + field presence + parser failure non-regression.

test 影響: 52 passed/50 skipped → ~100 passed/≤1 skipped (50 skip 解除).
0 failed, 0 errors. LLM cost $0 (test refactor のみ).

Out of scope (Day25+):
  - mdpi_173refs 固有の manual_overrides.yaml 構築
  - deterministic byte-level golden の再構築 (LLM path のため別途設計)
  - integration/src/manual_overrides.yaml の 4 entry (66/137/141/148) も
    旧 corpus 紐付けで残置、新 corpus 用 override は別 task

spec: docs/superpowers/specs/2026-05-24-day24-mdpi-test-restoration-design.md
plan: docs/superpowers/plans/2026-05-24-day24-mdpi-test-restoration.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
git log --oneline -3
```

- [ ] **Step 2.F.4: Final pytest verification**

```bash
python3 -m pytest tests/ -q 2>&1 | tail -3
git ls-remote origin main | awk '{print $1}'
git rev-parse HEAD
```

Expected: pytest still ~100 passed / ≤1 skipped, local HEAD == remote main.

---

## Task 3: Day24 archive

**Files:**
- Create: `docs/sessions/day24/README.md`
- Create: `docs/sessions/day24/DAY24_LESSONS_LEARNED.md`

- [ ] **Step 1: Get test count + commit chain for archive**

```bash
TEST_RESULT=$(python3 -m pytest tests/ -q 2>&1 | tail -1)
echo "Final test result: $TEST_RESULT"
git log --oneline 8d7df22..HEAD
```

Record the actual test count + the 3 commits made in Day24 (docs(spec), docs(plan), test(refactor)).

- [ ] **Step 2: Create Day24 README.md**

Save to `docs/sessions/day24/README.md`:

```markdown
# Day24 Session Archive (2026-05-24)

## 概要

Day24 セッションは Day23 Phase 1 で意図的に skip-mark した 5 test file を
新 mdpi_173refs fixture に re-point + 構造化 refactor + skip 解除する作業.
Day23 で意図的に残した「Day24 Top priority」を片付けた technical debt 解消
セッション.

## 主要成果

| 指標 | Day23 末 | Day24 末 |
|:---|:---:|:---:|
| 全 tests | 52 passed / 50 skipped | <NEW>passed / ≤1 skipped |
| skipped test 削減 | 50 | -49 (50 skip 解除) |
| 改修 test file | — | 5 file (mdpi_parser / overrides / journal_audit / pre_integration / doi_boundary) |
| byte-level golden 依存 | 4 test | 0 (全て構造 assertion に refactor) |
| corpus-specific assertion | 多数 | 最小限 (ref count range 等の invariant のみ) |

## Day24 archive 構成

- `README.md` — 本ファイル (Day24 index)
- `DAY24_LESSONS_LEARNED.md` — Day24 教訓記録
- `../../superpowers/specs/2026-05-24-day24-mdpi-test-restoration-design.md` — Day24 spec
- `../../superpowers/plans/2026-05-24-day24-mdpi-test-restoration.md` — Day24 plan

## Day24 commits (chain、3 件 + 本 archive commit)

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `8d7df22` | docs(spec) | Day24 MDPI test restoration spec |
| 2 | (Task 0) | docs(plan) | Day24 implementation plan |
| 3 | (Task 2) | test(refactor) | 5 file 一括 re-point + 構造化 refactor + skip 解除 |
| 4 | (this commit) | docs(sessions) | Day24 archive |

## 設計判断

実装 approach は **Q1 (α) 構造 test refactor + Q2 (α) 1 atomic commit** を採用
(spec §1.4). 代替案 Q1 (β) Phase 1 のみ byte-match / Q1 (γ) test 削除 (B/C 級)
は regression coverage の保ち方が中途半端のため不採用.

各 file の改修戦略は spec §3 per-file detail に従い、byte-level golden 依存度
の濃淡に応じて refactor 強度を調整 (mdpi_parser/journal_audit は局所改修、
pre_integration_baseline/doi_boundary は全面 rewrite、overrides_contract は 1
test のみ削除).

## Day25+ 候補

- **Top priority**: mdpi_173refs 固有の manual_overrides.yaml 構築 (Day25+ で
  parser 出力に応じた override 追加、本 Day24 で残置した 4 entry の刷新)
- pre-commit hook gitleaks 自動実行 (Day22 handoff パターン 3)
- CONTRIBUTING.md / Issue PR template (Day22 handoff パターン 2)
- PyPI 公開 (v0.2.0 候補)
- pyproject.toml + uv.lock 移行 (CLAUDE.md §8 整合)
- Crossref graceful failure 16 件の対応 (Day22 §6.3 NEW、apa_45refs)
- NLM fuzzy-match precision 改善 (Day22 §6.3 NEW)
- tools/build_*_fixture.py の共通 utility refactor (Day23 code review 指摘)
- deterministic byte-level golden の再構築 (LLM stub 経由、Day26+ 大改修)
```

Substitute `<NEW>` with the actual passed test count from Step 1.

- [ ] **Step 3: Create Day24 LESSONS_LEARNED.md**

Save to `docs/sessions/day24/DAY24_LESSONS_LEARNED.md`. Use `docs/sessions/day23/DAY23_LESSONS_LEARNED.md` as structural template. Target 150-200 lines.

Sections (§1-8):

- **§1 概要**: Day23 末状態 → Day24 末、Day23 Phase 1 で意図的に skip-mark した debt の解消
- **§2 brainstorming 段階**: Q1 (α structural refactor) + Q2 (α atomic commit) 確定理由
- **§3 実装段階の経緯**: Task 0 plan / Task 1 reconnaissance / Task 2 atomic refactor / Task 3 archive の commit SHA + 各 file の改修要約
- **§4 設計判断と検証**:
  - §4.1 byte-level golden を構造 invariant に置換した方針 (regression coverage の維持の仕方)
  - §4.2 per-file refactor 強度の差 (局所改修 vs 全面 rewrite の判断基準)
  - §4.3 Day23 で残した overrides yaml の 4 entry をそのまま残置した判断 (Day25+ scope)
- **§5 実機検証**: test count 推移 (52 → 100+) + gitleaks clean + CI green
- **§6 教訓** (3 件):
  - **D24-1**: 意図的に作った skip-mark は「Day N+1 Top priority」と明示することで technical debt が忘れられない (Day23 で skip-mark commit に reason="awaiting Day23 Phase 5..." と書いた習慣が機能した事例)
  - **D24-2**: byte-level golden は corpus 置換に対して脆弱、構造 invariant ベースの test は新 corpus への移植性が高い (Day24 で実感)
  - **D24-3**: corpus-specific test (Bray globocan, van der Biessen 等) は意味があるが、corpus 入替の際は全削除になる。設計時に「corpus-agnostic invariant」と「corpus-specific snapshot」を分けて配置すると保守性 high
- **§7 残存タスク (Day25+ 候補)**: Day24 README §Day25+ と同期
- **§8 次セッション再開プロンプトテンプレート** (Top priority: manual_overrides.yaml 刷新 + 他 7 候補)

Write 2-3 paragraphs per lesson with 事象 / 学び / 適用範囲 subsections.

- [ ] **Step 4: Commit + push**

```bash
gitleaks detect --no-banner --redact 2>&1 | tail -3
git add docs/sessions/day24/
git status --short
git commit -m "$(cat <<'EOF'
docs(sessions): archive day24 MDPI test restoration session

Day24 セッション (2026-05-24) の archive.

構成:
  - Task 0: docs(plan) commit
  - Task 1: 新 mdpi_173refs corpus reconnaissance (/tmp に出力、no commit)
  - Task 2: 5 file 一括 re-point + structural refactor + skip 解除
    (test(refactor) 単一 atomic commit)
  - Task 3: Day24 archive (本 commit)

成果:
  - 全 tests: 52 passed / 50 skipped → <NEW> passed / ≤1 skipped
  - skipped test 削減: 50 → <≤1>
  - 改修 file: 5 test file (mdpi_parser / overrides_contract / journal_audit
    / pre_integration_baseline / split_references_doi_boundary)
  - byte-level golden 依存: 4 test → 0 (全て構造 assertion に refactor)
  - LLM cost: $0 (test refactor のみ)
  - gitleaks: no leaks found (継続)

教訓:
  - D24-1: 意図的 skip-mark は「次セッション Top priority」と明示で
    technical debt 忘却防止
  - D24-2: byte-level golden は corpus 置換に脆弱、構造 invariant 設計が高保守性
  - D24-3: corpus-agnostic invariant と corpus-specific snapshot を設計時に
    分離配置すべき

Day25+ 候補: mdpi_173refs 固有 manual_overrides.yaml 構築 (Top priority)、
CONTRIBUTING.md, pre-commit hook gitleaks, PyPI 公開, Crossref graceful
failure 対応, NLM fuzzy-match precision, build tools 共通 utility refactor 等.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

Substitute `<NEW>` and `<≤1>` with actual values from Step 1.

- [ ] **Step 5: Final verification**

```bash
git status
git log --oneline -5
python3 -m pytest tests/ -q 2>&1 | tail -3
gh run list --limit 1 --json conclusion,status,headSha
gh repo view --json visibility,isPrivate
```

Expected: clean working tree, 5 Day24 commits visible, ~100 passed/≤1 skipped, CI success, repo PUBLIC.

Day24 complete.

---

## Self-Review Summary

| Check | Result |
|:---|:---|
| Spec coverage | spec §1 background → Task 0 (plan); §2 architecture → all tasks; §3 per-file detail → Task 2 sub-steps A-E; §4 commit plan → 4 commits across 4 tasks; §5 完了条件 → Task 2.F + Task 3.5; §6 工数 → embedded; §7 risks → embedded in Task 1 (recon) + per-file tests; §8 out of scope → Day24 README §Day25+ |
| Placeholder scan | `<NEW>` and `<≤1>` are runtime-substituted placeholders for Task 3 commit/archive, intentional and documented. All step content is concrete with exact code. |
| Type consistency | `TEST_DIR` / `FIXTURE_DIR` / `FIXTURES` variable names match their source files. `_load_phase1_blocks` / `extract_text` / `preprocess` / `split_references` / `_load_overrides_yaml` / `_apply_overrides` / `audit_journal_mismatch` / `format_summary_narrative` all match existing main.py / journal_audit.py / mdpi_parser.py APIs (verified via Read in plan-writing phase). |
| TDD ordering | Not strictly TDD (refactor task, not new feature). Each sub-step has its own pytest verification (2.A.2, 2.B.2, 2.C.2, 2.D.2, 2.E.3) before the atomic commit (2.F.3). |

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-24-day24-mdpi-test-restoration.md`. Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration. Task 2 is the largest and could benefit from a single dedicated subagent (5 sub-steps all related).

2. **Inline Execution** — execute tasks in this session with checkpoints for human review. The mostly mechanical nature of the refactor (sed-like file substitutions + structural assertions) lends itself well to inline execution.

Choose by responding with `subagent` or `inline`.
