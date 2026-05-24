# Day25 split_references non-ASCII Latin uppercase fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `main.split_references()` regex from `[A-Z]` to `[A-ZÀ-ÖØ-Þ]` so non-ASCII Latin uppercase author names (Å Ö É Ñ etc.) are correctly recognized as ref-block boundaries, restoring `#55 Åkra` and `#79 Özcan` in `mdpi_173refs` corpus (parsed count 171 → 173).

**Architecture:** Strict TDD 2-commit cycle (Day22 SSL fix pattern). Commit N: add 5 unit tests in new `tests/test_main_split_references.py` with synthetic input covering Norwegian/German/French/ASCII/DOI-URL — 4 will fail (RED). Commit N+1: extend regex in `main.py` (2 occurrences: matcher at line 415-417 and standard fallback at line 433-435), update 3 Day24 tripwire tests in `tests/test_split_references_doi_boundary.py` to reflect post-fix state (171→173, gaps→[], drop KNOWN_MERGE_FAILURE_REFS), add 2 positive integration tests (#55 starts_with Åkra, #79 starts_with Özcan), regenerate `tests/fixtures/mdpi_173refs/expected_phase1_intermediate.json`.

**Tech Stack:** Python 3.11+ (3.14 local), pytest 9.x, stdlib `re` only (no new dependencies). Latin-1 Supplement uppercase block: U+00C0-U+00D6 (À-Ö) + U+00D8-U+00DE (Ø-Þ), excluding U+00D7 (× multiplication sign).

**Spec reference:** `docs/superpowers/specs/2026-05-24-day25-split-references-non-ascii-fix-design.md` (commit `8f3bfb3`)

**Pre-state:**
- HEAD: `8f3bfb3` (Day25 spec)
- Repo: PUBLIC, CI green
- Tests: 100 passed / 0 skipped / 0 failed
- Day24 tripwire tests in `tests/test_split_references_doi_boundary.py` waiting (171, [55,79], {54,78}) — will be updated by Task 2

**Total commits:** 5 (1 spec already + 1 plan + 1 TDD RED + 1 TDD GREEN + 1 archive)

---

## File Structure

### Files CREATED in Task 1 (TDD RED)

| File | Lines (est.) | Responsibility |
|:---|---:|:---|
| `tests/test_main_split_references.py` | ~80 | unit tests for `main.split_references()` with synthetic input, corpus-independent regression guards for non-ASCII Latin uppercase boundary detection |

### Files MODIFIED in Task 2 (TDD GREEN)

| File | Lines changed | Why |
|:---|:---:|:---|
| `main.py` (lines 412-417 + 433-435) | +5 / -2 | regex extension `[A-Z]` → `[A-ZÀ-ÖØ-Þ]` in 2 regex blocks (matcher + standard fallback), 5 occurrences total within the 2 blocks (1 standalone `[A-Z]` + 4 inside `van/de/du/den/von` prefix groups). Docstring comment extended to document Day25 Latin-1 fix. |
| `tests/test_split_references_doi_boundary.py` | +30 / -15 | Update 3 tripwire tests to new state (171→173, gaps→[], KNOWN_MERGE_FAILURE_REFS removed) + add 2 positive integration tests (#55 Åkra, #79 Özcan) + update module docstring |
| `tests/fixtures/mdpi_173refs/expected_phase1_intermediate.json` | bytes change | Regenerate via `python3 main.py ... --phase 1` (171→173 refs, deterministic Phase 1 golden) |

### Files CREATED in Task 3 (Day25 archive)

| File | Why |
|:---|:---|
| `docs/sessions/day25/README.md` | Day25 session index |
| `docs/sessions/day25/DAY25_LESSONS_LEARNED.md` | Day25 retrospective (D25-1, D25-2 lessons) |

### Files NOT TOUCHED

- `mdpi_parser.py` (Phase 2 structuring, unaffected by Phase 1 boundary fix)
- `crossref_check.py` / `nlm_catalog_check.py` / `three_class_classifier.py` / `journal_audit.py`
- 4 other fixtures (apa_45refs, cell_45refs, vancouver_35refs, three_class_classification) — no non-ASCII Latin uppercase refs
- Other integration tests (test_integration_apa_45refs, test_integration_cell_45refs, test_integration_mdpi_173refs, test_integration_vancouver_35refs) — baseline_*.json files are variability-bearing and unaffected

---

## Task 0: Commit this plan

**Files:**
- Modify: `docs/superpowers/plans/2026-05-24-day25-split-references-non-ascii-fix.md` (just written)

- [ ] **Step 1: Stage and review**

```bash
git add docs/superpowers/plans/2026-05-24-day25-split-references-non-ascii-fix.md
git status --short
```

Expected: 1 file added.

- [ ] **Step 2: Commit**

```bash
git commit -m "$(cat <<'EOF'
docs(plan): add Day25 split_references non-ASCII Latin uppercase fix plan

spec (commit 8f3bfb3) に基づく 4 task の bite-sized 実装計画.

主要 task:
  - Task 1: TDD RED — tests/test_main_split_references.py 新規 5 unit test
    (ASCII baseline + Å/Ö/É boundary + DOI URL 誤検出回避)、4 件 FAIL 確認
  - Task 2: TDD GREEN — main.py regex 拡張 ([A-Z] → [A-ZÀ-ÖØ-Þ] 5 箇所)
    + tripwire 3 件更新 + #55/#79 positive test 2 件追加
    + expected_phase1_intermediate.json 再生成
  - Task 3: Day25 archive (README + LESSONS) + push + CI verify

期待: 100 passed/0 skipped → 107 passed/0 skipped、commit 計 5 件、
工数 ~2.5h、LLM cost \$0.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: Verify**

Run: `git log --oneline -2`
Expected: HEAD = `docs(plan):` …, HEAD~1 = `8f3bfb3` (`docs(spec):` …).

---

## Task 1: TDD RED — new unit test file (`test(split)` commit)

**Files:**
- Create: `tests/test_main_split_references.py`

- [ ] **Step 1: Create the new test file**

Use Write tool to create `tests/test_main_split_references.py` with exactly this content:

```python
"""
test_main_split_references.py — main.py split_references() の unit test
(Day25 TDD: non-ASCII Latin uppercase boundary detection の regression guard)

Day24 Task 1 reconnaissance で mdpi_173refs corpus 上 #55 (Åkra) と
#79 (Özcan) が parser に検出されず直前 ref に merge される事象を発見.
本 file は corpus 非依存の合成 input で同 bug の再現と修正検証を行う.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import main  # noqa: E402


def test_split_references_detects_ascii_uppercase_boundary():
    """ASCII [A-Z] で始まる著者の ref boundary が検出される (baseline)."""
    cleaned = "1. Smith J. Title A. Journal 2020.\n2. Brown K. Title B. Journal 2021."
    blocks = main.split_references(cleaned)
    assert len(blocks) == 2
    assert blocks[0].ref_no == 1 and blocks[0].raw_text.startswith("Smith")
    assert blocks[1].ref_no == 2 and blocks[1].raw_text.startswith("Brown")


def test_split_references_detects_norwegian_aring_boundary():
    """Å (U+00C5、ノルウェー語) で始まる著者の ref boundary が検出される.

    Day24 Task 1 で発見した #55 Åkra 事象の合成版 regression test.
    現状 (Day24 末) 失敗、Day25 fix(split) で GREEN 化予定.
    """
    cleaned = "1. Smith J. Title A. Journal 2020.\n2. Åkra S. Title B. Journal 2021."
    blocks = main.split_references(cleaned)
    assert len(blocks) == 2, f"expected 2 blocks, got {len(blocks)}"
    assert blocks[1].ref_no == 2
    assert blocks[1].raw_text.startswith("Åkra")


def test_split_references_detects_german_oumlaut_boundary():
    """Ö (U+00D6、ドイツ・トルコ語) で始まる著者の ref boundary が検出される.

    Day24 Task 1 で発見した #79 Özcan 事象の合成版 regression test.
    """
    cleaned = "1. Smith J. Title A. Journal 2020.\n2. Özcan U. Title B. Journal 2021."
    blocks = main.split_references(cleaned)
    assert len(blocks) == 2
    assert blocks[1].raw_text.startswith("Özcan")


def test_split_references_detects_french_acute_boundary():
    """É (U+00C9、フランス・スペイン語) で始まる著者の ref boundary が検出される.

    Latin-1 Supplement uppercase range の包括的 regression guard.
    """
    cleaned = "1. Smith J. Title A. Journal 2020.\n2. Étienne L. Title B. Journal 2021."
    blocks = main.split_references(cleaned)
    assert len(blocks) == 2
    assert blocks[1].raw_text.startswith("Étienne")


def test_split_references_does_not_detect_inside_doi_url():
    """DOI URL 内の数字 (例: 10.3390/ijms20092358) を ref boundary として誤検出しない (regression guard)."""
    cleaned = (
        "1. Smith J. Title A. Journal 2020, 10, 8. https://doi.org/10.3390/ijms20092358\n"
        "2. Brown K. Title B. Journal 2021."
    )
    blocks = main.split_references(cleaned)
    assert len(blocks) == 2
    # 1 番目の block に DOI URL が含まれる (誤検出されていない)
    assert "ijms20092358" in blocks[0].raw_text
```

- [ ] **Step 2: Run new test file to verify TDD RED**

```bash
python3 -m pytest tests/test_main_split_references.py -v 2>&1 | tail -20
```

Expected: **2 passed, 3 failed** (4 failed minus possibly Étienne if LIS accidentally allows it — but most likely 3 failed since Å/Ö/É share the same root cause).

Actually expected result is **2 passed (ASCII baseline + DOI URL excluded) + 3 failed (Å/Ö/É boundary)**. If the result differs:
- If all 5 pass: the bug is already fixed, STOP and investigate (Day24 recon may have been on different state)
- If more than 3 fail: investigate the additional failure modes (may be regression in ASCII test)

Record exact failure messages — they should mention "expected 2 blocks, got 1" or similar (the merge causes single block).

- [ ] **Step 3: Confirm rest of test suite is unaffected**

```bash
python3 -m pytest tests/ -q --ignore tests/test_main_split_references.py 2>&1 | tail -3
```

Expected: `100 passed, 0 skipped, 0 failed` (Day24 末 baseline unchanged).

- [ ] **Step 4: Commit (TDD RED)**

```bash
git add tests/test_main_split_references.py
git commit -m "$(cat <<'EOF'
test(split): add failing unit tests for non-ASCII Latin uppercase boundary (Day25 Task 1 TDD RED)

Day24 Task 1 で発見した parser bug の corpus 非依存合成 input regression test.

新規 test 5 件:
  - test_split_references_detects_ascii_uppercase_boundary: PASS (baseline)
  - test_split_references_detects_norwegian_aring_boundary: FAIL (Å U+00C5)
  - test_split_references_detects_german_oumlaut_boundary: FAIL (Ö U+00D6)
  - test_split_references_detects_french_acute_boundary: FAIL (É U+00C9)
  - test_split_references_does_not_detect_inside_doi_url: PASS (regression guard)

期待 TDD RED 結果: 2 passed, 3 failed.

主原因: main.py line 415-417 (matcher) + line 433-435 (standard fallback)
の regex lookahead `[A-Z]` が ASCII 範囲のみで、Latin-1 Supplement uppercase
(Å Ö É 等) で始まる著者姓を boundary として認識しない.

次 commit (fix(split)) で main.py regex を [A-Z] → [A-ZÀ-ÖØ-Þ] に拡張、
本 3 件を GREEN 化し、Day24 tripwire 3 件も同時更新予定.

spec: docs/superpowers/specs/2026-05-24-day25-split-references-non-ascii-fix-design.md
plan: docs/superpowers/plans/2026-05-24-day25-split-references-non-ascii-fix.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: Verify commit history**

Run: `git log --oneline -3`
Expected: HEAD = `test(split): add failing unit tests …`, HEAD~1 = `docs(plan): …`, HEAD~2 = `8f3bfb3` (docs(spec): …)

No push (push reserved for Task 3 to keep CI noise minimal for transient TDD RED state).

---

## Task 2: TDD GREEN — fix regex + update tripwires + add positives + regenerate fixture (`fix(split)` commit)

**Files:**
- Modify: `main.py` (lines 412-417 area, 433-435 area)
- Modify: `tests/test_split_references_doi_boundary.py`
- Regenerate: `tests/fixtures/mdpi_173refs/expected_phase1_intermediate.json`

### Sub-step 2.A: Fix `main.py` regex

- [ ] **Step 2.A.1: Update docstring + matcher regex (lines 411-418)**

Read the current state first:
```bash
sed -n '410,420p' main.py
```

Use Edit tool to apply this exact change:

**Find** (lines 411-418):
```python
    # より寛容な候補検出: ピリオド or 空白で数字と著者を区切る
    # NOTE: lookahead allows lowercase prefixes for Dutch/French surnames
    # (van, de, du, den, von) which start with lowercase letters.
    # Without this, refs like "40. van der Biessen" are silently dropped.
    matcher = re.compile(
        r"(?<![\d.])(\d+)[\.\s]+"
        r"(?=[A-Z]|van\s|de\s+[A-Z]|du\s+[A-Z]|den\s+[A-Z]|von\s+[A-Z])"
    )
```

**Replace with**:
```python
    # より寛容な候補検出: ピリオド or 空白で数字と著者を区切る
    # NOTE: lookahead allows lowercase prefixes for Dutch/French surnames
    # (van, de, du, den, von) which start with lowercase letters.
    # Without this, refs like "40. van der Biessen" are silently dropped.
    # Day25: lookahead also accepts Latin-1 Supplement uppercase
    # ([A-ZÀ-ÖØ-Þ] = ASCII + U+00C0-U+00D6 + U+00D8-U+00DE, excluding × U+00D7)
    # for Norwegian/German/French/Spanish/Portuguese surnames starting with
    # Å Ö É Ñ etc. Without [A-ZÀ-ÖØ-Þ], refs like "55. Åkra" or "79. Özcan"
    # are silently merged into the preceding ref (Day24 Task 1 reconnaissance
    # discovered this on mdpi_173refs corpus).
    matcher = re.compile(
        r"(?<![\d.])(\d+)[\.\s]+"
        r"(?=[A-ZÀ-ÖØ-Þ]|van\s|de\s+[A-ZÀ-ÖØ-Þ]|du\s+[A-ZÀ-ÖØ-Þ]|den\s+[A-ZÀ-ÖØ-Þ]|von\s+[A-ZÀ-ÖØ-Þ])"
    )
```

- [ ] **Step 2.A.2: Update standard fallback regex (lines 433-436)**

Read first:
```bash
sed -n '430,440p' main.py
```

**Find** (lines 433-436):
```python
        standard = re.compile(
            r"(?<![\d.])(\d+)\.\s+"
            r"(?=[A-Z]|van\s|de\s+[A-Z]|du\s+[A-Z]|den\s+[A-Z]|von\s+[A-Z])"
        )
```

**Replace with**:
```python
        standard = re.compile(
            r"(?<![\d.])(\d+)\.\s+"
            r"(?=[A-ZÀ-ÖØ-Þ]|van\s|de\s+[A-ZÀ-ÖØ-Þ]|du\s+[A-ZÀ-ÖØ-Þ]|den\s+[A-ZÀ-ÖØ-Þ]|von\s+[A-ZÀ-ÖØ-Þ])"
        )
```

- [ ] **Step 2.A.3: Verify Task 1 unit tests now PASS (TDD GREEN)**

```bash
python3 -m pytest tests/test_main_split_references.py -v 2>&1 | tail -15
```

Expected: **5 passed**. If any FAIL, investigate the regex (check exact Unicode codepoints, verify both regex blocks were updated).

### Sub-step 2.B: Update tripwire tests in `tests/test_split_references_doi_boundary.py`

- [ ] **Step 2.B.1: Read current file content**

```bash
cat tests/test_split_references_doi_boundary.py
```

Confirm it matches the Day24-end state (171 expected, [55, 79] gaps, {54, 78} KNOWN_MERGE_FAILURE_REFS).

- [ ] **Step 2.B.2: Replace the entire file with updated content**

Use Write tool to replace `tests/test_split_references_doi_boundary.py` with:

```python
"""
test_split_references_doi_boundary.py — Phase 1 split_references の構造 invariant
(Day25 fix(split) 適用後版)

旧目的:
    Day9 (commit ab25630) で Phase 1 split_references が DOI 終端直後の
    lowercase-prefixed 著者 Ref (#40 van der Biessen, #140 van Zyl) を
    正しく検出するかを 149-ref corpus で検証していた.

Day24 historical archive 化 + 新 corpus 適用:
    Day23 で旧 mdpi_149refs corpus 削除 + 新 mdpi_173refs に置換. 新 corpus
    には #40 van der Biessen も #140 van Zyl も存在しない代わりに #69 van Vliet
    / #92 van den Burg / #173 de Menezes が同種の lowercase-prefix 著者 ref
    として存在. 本 file は新 corpus の構造 invariant smoke check に refactor.

Day25 fix(split) で解消した parser bug:
    Day24 Task 1 で「DOI URL 直後の <N>. boundary 検出失敗」と仮説立てしたが、
    Day25 brainstorming で真因が「直後の著者姓が非 ASCII Latin uppercase
    (Å Ö 等)」だったと判明. main.py regex を [A-Z] → [A-ZÀ-ÖØ-Þ] に拡張する
    fix で #55 Åkra と #79 Özcan が復活、parsed count 171 → 173.
    本 test は新状態 (173 blocks、no gaps) を assert.
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
    """新 mdpi_173refs corpus に対する Phase 1 split_references の構造 invariant.

    Day25 fix(split) 適用後の updated assertions. count = 173, no gaps,
    no oversized blocks. Day26+ で新 parser regression が起きた場合に検出する.
    """

    def test_ref_count_is_173(self, blocks):
        """parsed ref count が 173 (Day25 fix(split) 後実測、Day24 末の 171 から +2 復活)."""
        assert len(blocks) == 173, (
            f"unexpected ref count: {len(blocks)} (Day25 fix(split) 後 173 が期待). "
            f"If this drops to <173, parser regressed. Day25 fix(split) restored "
            f"missing #55 and #79 (Latin-1 uppercase boundary detection)."
        )

    def test_ref_no_range_is_1_to_173(self, blocks):
        """ref_no は 1 から 173 の範囲."""
        ref_nos = sorted(b.ref_no for b in blocks)
        assert ref_nos[0] == 1, f"first ref_no should be 1, got {ref_nos[0]}"
        assert ref_nos[-1] == 173, f"last ref_no should be 173, got {ref_nos[-1]}"

    def test_no_parser_gaps_in_corpus(self, blocks):
        """Day25 fix(split) 後: ref_no に gap が無いこと (1-173 全件揃う).

        Day24 では gap [55, 79] を tripwire pattern で assert していた.
        Day25 fix(split) で gap 解消、本 test を空 list assertion に更新.
        """
        ref_nos = set(b.ref_no for b in blocks)
        all_expected = set(range(1, 174))
        actual_gaps = sorted(all_expected - ref_nos)
        assert actual_gaps == [], (
            f"unexpected parser gaps: {actual_gaps} (expected [] after Day25 fix(split))"
        )

    def test_lowercase_prefix_refs_correctly_split(self, blocks):
        """Day24 Task 1 reconnaissance で確認した 3 件の lowercase-prefix 著者 ref が
        正しく独立した block として認識されていること.
        """
        by_ref_no = {b.ref_no: b for b in blocks}
        assert 69 in by_ref_no and by_ref_no[69].raw_text.startswith("van Vliet"), \
            "ref #69 should start with 'van Vliet'"
        assert 92 in by_ref_no and by_ref_no[92].raw_text.startswith("van den Burg"), \
            "ref #92 should start with 'van den Burg'"
        assert 173 in by_ref_no and by_ref_no[173].raw_text.startswith("de Menezes"), \
            "ref #173 should start with 'de Menezes'"

    def test_ref55_starts_with_aring_author(self, blocks):
        """Day25 fix(split) で復活した #55 が "Åkra" で始まることを確認.

        Day24 Task 1 で merge 検出した bug の corpus-level regression guard.
        Latin-1 Supplement uppercase Å (U+00C5) の boundary detection.
        """
        by_ref_no = {b.ref_no: b for b in blocks}
        assert 55 in by_ref_no, "ref #55 missing (Day25 fix(split) may have regressed)"
        assert by_ref_no[55].raw_text.startswith("Åkra"), \
            f"ref #55 should start with 'Åkra', got: {by_ref_no[55].raw_text[:40]}"

    def test_ref79_starts_with_oumlaut_author(self, blocks):
        """Day25 fix(split) で復活した #79 が "Özcan" で始まることを確認.

        Day24 Task 1 で merge 検出した bug の corpus-level regression guard.
        Latin-1 Supplement uppercase Ö (U+00D6) の boundary detection.
        """
        by_ref_no = {b.ref_no: b for b in blocks}
        assert 79 in by_ref_no, "ref #79 missing (Day25 fix(split) may have regressed)"
        assert by_ref_no[79].raw_text.startswith("Özcan"), \
            f"ref #79 should start with 'Özcan', got: {by_ref_no[79].raw_text[:40]}"

    def test_no_block_exceeds_reasonable_size(self, blocks):
        """各 block が 600 chars 以下 (parser merge failure の検知).

        Day24 では known merge failure (#54, #78) を例外として excluded していたが、
        Day25 fix(split) で merge 解消、本 test の例外 set 削除.
        """
        OVERSIZED_THRESHOLD = 600
        oversized = [
            (b.ref_no, b.char_length)
            for b in blocks
            if b.char_length > OVERSIZED_THRESHOLD
        ]
        assert not oversized, (
            f"Found {len(oversized)} pathologically large blocks (>{OVERSIZED_THRESHOLD} chars): "
            f"{oversized[:5]}. This may indicate split_references boundary failure regression."
        )

    def test_no_block_is_empty(self, blocks):
        """各 block の raw_text が空でない."""
        empty = [b.ref_no for b in blocks if not b.raw_text.strip()]
        assert not empty, f"Found {len(empty)} empty blocks: {empty[:5]}"
```

This is a full file replacement, ~125 lines total. The changes vs Day24 state:
- Module docstring updated to reference Day25 fix
- Class docstring updated
- `test_ref_count_matches_current_parser_state` renamed to `test_ref_count_is_173`, asserts `== 173`
- `test_known_parser_gaps_are_55_and_79` renamed to `test_no_parser_gaps_in_corpus`, asserts `== []`
- `test_no_block_exceeds_reasonable_size_except_known_merge_failures` renamed to `test_no_block_exceeds_reasonable_size`, removes `KNOWN_MERGE_FAILURE_REFS = {54, 78}` exclusion
- NEW: `test_ref55_starts_with_aring_author` (positive integration test for Å boundary)
- NEW: `test_ref79_starts_with_oumlaut_author` (positive integration test for Ö boundary)
- Existing `test_lowercase_prefix_refs_correctly_split` + `test_no_block_is_empty` retained unchanged
- Total: 8 tests (was 6 in Day24 state, +2 positive)

### Sub-step 2.C: Regenerate `expected_phase1_intermediate.json`

- [ ] **Step 2.C.1: Run Phase 1 only on mdpi_173refs corpus**

```bash
mkdir -p /tmp/day25_mdpi_173refs_phase1
python3 main.py tests/fixtures/mdpi_173refs/input_References.docx \
  --output-dir /tmp/day25_mdpi_173refs_phase1 --phase 1
ls /tmp/day25_mdpi_173refs_phase1/
```

Expected: `phase1_intermediate.json` (and possibly other phase1_* files) generated.

- [ ] **Step 2.C.2: Inspect the new ref count before copying**

```bash
python3 -c "
import json
data = json.load(open('/tmp/day25_mdpi_173refs_phase1/phase1_intermediate.json'))
# data structure may be {'blocks': [...]} or [...] — handle both
if isinstance(data, dict):
    blocks = data.get('blocks') or data.get('reference_blocks') or list(data.values())[0]
else:
    blocks = data
print(f'phase1 block count: {len(blocks)}')
print(f'first block ref_no: {blocks[0].get(\"ref_no\") if isinstance(blocks[0], dict) else \"unknown\"}')"
```

Expected: count = 173. If 171, the regex fix didn't take effect in main.py — go back to Sub-step 2.A and verify.

- [ ] **Step 2.C.3: Copy the regenerated baseline into fixture dir**

```bash
cp /tmp/day25_mdpi_173refs_phase1/phase1_intermediate.json \
   tests/fixtures/mdpi_173refs/expected_phase1_intermediate.json
git diff --stat tests/fixtures/mdpi_173refs/expected_phase1_intermediate.json
```

Expected: file changed (byte-level diff with 2 additional refs and content shifts in #54/#78).

### Sub-step 2.D: Full verification + atomic commit + push

- [ ] **Step 2.D.1: Run full pytest**

```bash
python3 -m pytest tests/ -q 2>&1 | tail -5
```

Expected: **107 passed, 0 skipped, 0 failed** (100 baseline + 5 new unit + 2 new positive integration = 107). If failures, investigate:
- If `test_split_references_doi_boundary.py::test_no_block_exceeds_reasonable_size` fails: a block other than (formerly) #54/#78 exceeds 600 chars — investigate that block's content
- If `test_split_references_doi_boundary.py` rename causes pytest to skip something: check that pytest collected all renamed tests
- If unit tests in `test_main_split_references.py` fail: regex didn't update correctly

- [ ] **Step 2.D.2: gitleaks check**

```bash
gitleaks detect --no-banner --redact 2>&1 | tail -3
```

Expected: `no leaks found`.

- [ ] **Step 2.D.3: Stage and commit (TDD GREEN, atomic)**

```bash
git add main.py \
        tests/test_split_references_doi_boundary.py \
        tests/fixtures/mdpi_173refs/expected_phase1_intermediate.json
git status --short
git commit -m "$(cat <<'EOF'
fix(split): extend regex to recognize Latin-1 Supplement uppercase author names (Day25 Task 2 TDD GREEN)

Day24 Task 1 で発見した parser bug を fix.

Root cause (Day25 brainstorming で確定):
  main.py split_references() の regex lookahead `[A-Z]` が ASCII 範囲のみで、
  Å (U+00C5、ノルウェー Åkra) や Ö (U+00D6、ドイツ Özcan) 等の Latin-1
  Supplement uppercase で始まる著者姓を ref boundary として認識せず、
  #55/#79 がそれぞれ #54/#78 に silently merge されていた.
  Day24 仮説「DOI URL 直後の <N>. boundary 検出失敗」は誤り、真因は
  「直後の著者姓が非 ASCII Latin uppercase」だった.

Fix:
  main.py の regex 2 箇所 (line 415-417 matcher + line 433-435 standard
  fallback) で `[A-Z]` を `[A-ZÀ-ÖØ-Þ]` に拡張:
    - A-Z: ASCII uppercase (U+0041-U+005A、不変)
    - À-Ö: Latin-1 Supplement uppercase A-O (U+00C0-U+00D6)
    - Ø-Þ: Latin-1 Supplement uppercase remainder (U+00D8-U+00DE)
    - 飛ばす U+00D7: × multiplication sign (文字ではない、意図的に excluded)

  5 lookahead positions (1 standalone [A-Z] + 4 inside van/de/du/den/von
  prefix groups) を 2 regex blocks 内全て更新.

Test updates:
  - tests/test_main_split_references.py: Task 1 RED で書いた 5 unit test
    のうち 3 件 (Å/Ö/É) が GREEN 化
  - tests/test_split_references_doi_boundary.py: Day24 tripwire 3 件を
    新状態に更新 + #55 Åkra / #79 Özcan positive integration test 2 件追加
    + method 名を rename (現状を表現する名前に):
      * test_ref_count_matches_current_parser_state → test_ref_count_is_173
      * test_known_parser_gaps_are_55_and_79 → test_no_parser_gaps_in_corpus
      * test_no_block_exceeds_reasonable_size_except_known_merge_failures
        → test_no_block_exceeds_reasonable_size

Fixture regeneration:
  - tests/fixtures/mdpi_173refs/expected_phase1_intermediate.json:
    Phase 1 baseline を 171→173 entry で再生成 (deterministic golden、
    #55/#79 復活 + #54/#78 内容圧縮). LLM 不使用 (--phase 1 only).

test 影響: 100 passed/0 skipped → 107 passed/0 skipped/0 failed.

Day26+ candidate (Out of scope): Latin Extended-A 範囲 (Š Ž Č Ł 等
チェコ・ポーランド語) で始まる著者姓への対応は別 spec で検討.

spec: docs/superpowers/specs/2026-05-24-day25-split-references-non-ascii-fix-design.md
plan: docs/superpowers/plans/2026-05-24-day25-split-references-non-ascii-fix.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 2.D.4: Push to origin/main**

```bash
git push origin main
git log --oneline -5
```

Expected: push succeeds. Both `test(split):` (Task 1) and `fix(split):` (Task 2) commits land on remote.

- [ ] **Step 2.D.5: Verify push state**

```bash
git rev-parse HEAD
git ls-remote origin main | awk '{print $1}'
python3 -m pytest tests/ -q 2>&1 | tail -3
```

Expected: local HEAD == remote main, 107 passed / 0 skipped / 0 failed.

---

## Task 3: Day25 archive + CI verification (`docs(sessions)` commit)

**Files:**
- Create: `docs/sessions/day25/README.md`
- Create: `docs/sessions/day25/DAY25_LESSONS_LEARNED.md`

- [ ] **Step 1: Capture final state metrics for archive**

```bash
TEST_RESULT=$(python3 -m pytest tests/ -q 2>&1 | tail -1)
echo "Final test result: $TEST_RESULT"
git log --oneline 8f3bfb3..HEAD
```

Record:
- Final test count (expected 107 passed / 0 skipped)
- The 4 commits made in Day25 so far (docs(spec) `8f3bfb3`, docs(plan) Task 0, test(split) Task 1, fix(split) Task 2)

- [ ] **Step 2: Create `docs/sessions/day25/README.md`**

Use Write tool. Substitute `<TASK0_SHA>`, `<TASK1_SHA>`, `<TASK2_SHA>` with the SHAs captured in Step 1. Substitute `<TASK3_SHA>` with `(this commit)` placeholder.

```markdown
# Day25 Session Archive (2026-05-24)

## 概要

Day25 セッションは Day24 Task 1 reconnaissance で発見し tripwire pattern で
test に encode していた `split_references()` parser bug を root cause 特定 →
fix する作業. Day24 で立てた仮説「DOI URL 直後の <N>. boundary 検出失敗」が
Day25 brainstorming で実 cleaned text inspect の結果誤りと判明、真因は
「直後の著者姓が非 ASCII Latin uppercase (Å U+00C5, Ö U+00D6) で main.py
regex lookahead `[A-Z]` でマッチしない」と確定. Latin-1 Supplement uppercase
を cover する `[A-ZÀ-ÖØ-Þ]` への regex 拡張で fix.

## 主要成果

| 指標 | Day24 末 | Day25 末 |
|:---|:---:|:---:|
| 全 tests | 100 passed / 0 skipped | **107 passed / 0 skipped / 0 failed** |
| 新規 unit test | — | 5 件 (tests/test_main_split_references.py) |
| 新規 positive integration test | — | 2 件 (#55 Åkra / #79 Özcan) |
| Day24 tripwire test 更新 | — | 3 件 (171→173, gaps→[], KNOWN_MERGE 削除) |
| mdpi_173refs parsed count | 171 | **173 (+2 復活: #55 Åkra, #79 Özcan)** |
| #54 char_length | 569 ch (merged) | ~280 ch (cleaned) |
| #78 char_length | 569 ch (merged) | ~290 ch (cleaned) |
| LLM cost | — | **\$0** (parser fix のみ、--phase 1 only baseline) |

## Day25 archive 構成

- `README.md` — 本ファイル (Day25 index)
- `DAY25_LESSONS_LEARNED.md` — Day25 教訓記録 (D25-1, D25-2)
- `../../superpowers/specs/2026-05-24-day25-split-references-non-ascii-fix-design.md` — Day25 spec
- `../../superpowers/plans/2026-05-24-day25-split-references-non-ascii-fix.md` — Day25 plan

## Day25 commits (chain、5 件)

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `8f3bfb3` | docs(spec) | Day25 split_references non-ASCII Latin uppercase fix spec |
| 2 | `<TASK0_SHA>` | docs(plan) | Day25 implementation plan |
| 3 | `<TASK1_SHA>` | test(split) | TDD RED: 5 unit test (Å/Ö/É boundary + ASCII baseline + DOI URL guard) |
| 4 | `<TASK2_SHA>` | fix(split) | TDD GREEN: regex 拡張 [A-Z]→[A-ZÀ-ÖØ-Þ] + tripwire 3 更新 + positive test 2 + json 再生成 |
| 5 | `<TASK3_SHA>` | docs(sessions) | Day25 archive (本 commit) |

## 設計判断

実装 approach は **Q1 (A) 明示的 character class 拡張 + Q2 (α) Strict TDD 2-commit cycle** を採用 (spec §1.4). 代替案 Q1 (B) Latin Extended-A 拡張 / Q1 (C) 三方 regex library / Q1 (D) Pre-filter 方式 は false positive 増 / 依存追加 / コード複雑化のため不採用. Q2 (β) Integration TDD のみ / Q2 (γ) 両方は corpus 依存度過大化 / commit 数過多のため不採用.

`[A-ZÀ-ÖØ-Þ]` 拡張は Python stdlib re のみ、Latin-1 Supplement uppercase block (À-Ö U+00C0-U+00D6, Ø-Þ U+00D8-U+00DE、× U+00D7 は意図的に excluded) を cover. ノルウェー / スウェーデン / ドイツ / オランダ / フランス / スペイン / ポルトガル等の著者姓に対応.

## Day25 で確認した重要な反省事例

Day24 Task 1 で立てた仮説「DOI URL 直後の <N>. boundary 検出失敗」は **誤り**だった. 実際は「直後の著者姓が非 ASCII Latin uppercase」が真因. Day24 段階で実 cleaned text を inspect していなかったため、外形的な観察 (DOI URL の後で merge 発生) から仮説立て、それを tripwire test の docstring に encode してしまった.

Day25 で reconnaissance を継続 (実 cleaned text の repr() dump) した結果、真因が `Å` U+00C5 の lookahead 不一致だと特定. tripwire test 自体は正しく fail 信号を発しており、Day25 で test 更新時に「真因と一致する docstring」に書き換え.

→ 教訓: 仮説段階の bug 解説は「観察事実」と「推測される原因」を明確に分けるべき (D25-1 として記録).

## Day26+ 候補

- **Top priority**: Latin Extended-A 範囲 (チェコ語 Š Č Ž / ポーランド語 Ł Ć Ń Ą Ę / ハンガリー語 Ő Ű / ルーマニア語 Ș Ț) で始まる著者姓が出現する corpus が見つかったら `[A-ZÀ-ÖØ-Þ]` → `[A-ZÀ-ÖØ-ÞĀ-ſ]` 等に拡張
- mdpi_173refs 固有の manual_overrides.yaml 構築 (Day24 から継承)
- pre-commit hook gitleaks 自動実行 (Day22 handoff パターン 3)
- CONTRIBUTING.md / Issue PR template (Day22 handoff パターン 2)
- PyPI 公開 (v0.2.0 候補)
- pyproject.toml + uv.lock 移行 (CLAUDE.md §8 整合)
- Crossref graceful failure 16 件の対応 (Day22 §6.3 NEW、apa_45refs)
- NLM fuzzy-match precision 改善 (Day22 §6.3 NEW)
- tools/build_*_fixture.py の共通 utility refactor (Day23 code review 指摘)
- deterministic byte-level golden の再構築 (LLM stub 経由、Day26+ 大改修)
```

- [ ] **Step 3: Create `docs/sessions/day25/DAY25_LESSONS_LEARNED.md`**

Use Write tool. Structure follows Day24 LESSONS template (`docs/sessions/day24/DAY24_LESSONS_LEARNED.md`) but adapted for Day25.

Read the Day24 LESSONS as a structural reference first:
```bash
wc -l docs/sessions/day24/DAY24_LESSONS_LEARNED.md
head -40 docs/sessions/day24/DAY24_LESSONS_LEARNED.md
```

Then write `docs/sessions/day25/DAY25_LESSONS_LEARNED.md` with substantive content (target 150-200 lines) covering:

- **§1 概要**: Day24 末状態 (100 passed/0 skipped、tripwire 3 件待機) → Day25 末 (107 passed/0 skipped、tripwire 解消 + Latin-1 boundary 対応完了)
- **§2 brainstorming 段階**: Q1 (A character class 拡張) + Q2 (α Strict TDD 2-commit) 確定理由 (代替案 B/C/D + β/γ を不採用とした根拠を簡潔に)
- **§3 実装段階の経緯**: Task 0-3 の commit chain table (SHA + 要旨) + Task 2 sub-step (A regex / B tripwire / C json regen / D verify+commit) の細分化
- **§4 設計判断と検証**:
  - §4.1 Day25 brainstorming で発覚した Day24 仮説誤り (DOI URL 直後 → 真因は非 ASCII uppercase)
  - §4.2 `[A-ZÀ-ÖØ-Þ]` 範囲設計 (× U+00D7 を意図的 excluded、Latin Extended-A は Day26+ scope)
  - §4.3 tripwire test の rename + 再 utilize (旧 name `test_ref_count_matches_current_parser_state` は「現状」が変わると意味が陳腐化、新 name `test_ref_count_is_173` は「現状」を明示)
  - §4.4 strict TDD 2-commit cycle の効果 (RED commit が中間状態として残るが、history で「何を fix したか」が明示)
- **§5 実機検証**: test count 推移 (100 → 107) + #54/#78 char_length 比較 (569ch → ~280ch) + smoke check + gitleaks clean + CI green
- **§6 教訓** (各 事象/学び/適用範囲 subsection):
  - **D25-1**: 仮説段階の bug 解説は「観察事実」と「推測される原因」を明確に分けるべき. Day24 では「DOI URL 直後で merge 発生」(観察事実) を「DOI URL が boundary detection を妨げる」(推測原因) と混同して tripwire test docstring に encode してしまい、Day25 で実 cleaned text inspect の結果誤り判明.
  - **D25-2**: regex の character class は単純に見えて Unicode 範囲の罠が多い. `[A-Z]` は ASCII のみ、`\w` も Python re では Unicode を cover するが意味が広すぎる. 著者姓のような特殊用途は明示的 character class (`[A-ZÀ-ÖØ-Þ]` 等) で範囲を明示する方が安全. Day9 で van/de/du/den/von prefix を明示追加したのと同じ思想.
- **§7 残存タスク (Day26+ 候補)**: README §Day26+ 候補と同期 (Latin Extended-A が Top priority に昇格)
- **§8 次セッション再開プロンプトテンプレート** (3 patterns):
  - パターン 1 (推奨): Latin Extended-A 拡張 (Day25 D25-2 の延長)
  - パターン 2: mdpi_173refs 固有 manual_overrides.yaml 構築
  - パターン 3: CONTRIBUTING.md / Issue PR template

Target: 150-200 lines with substantive content for each §.

- [ ] **Step 4: gitleaks final check + commit + push**

```bash
gitleaks detect --no-banner --redact 2>&1 | tail -3
git add docs/sessions/day25/
git status --short
git commit -m "$(cat <<'EOF'
docs(sessions): archive day25 split_references non-ASCII Latin uppercase fix session

Day25 セッション (2026-05-24) の archive.

構成:
  - Task 0: docs(plan) commit
  - Task 1: TDD RED — tests/test_main_split_references.py 新規 5 unit test
    (test(split))
  - Task 2: TDD GREEN — main.py regex [A-Z] → [A-ZÀ-ÖØ-Þ] 拡張 + tripwire
    3 件更新 + #55/#79 positive test 2 件追加 + expected_phase1_intermediate.json
    再生成 (fix(split) 単一 atomic commit)
  - Task 3: Day25 archive (本 commit)

成果:
  - 全 tests: 100 passed / 0 skipped → **107 passed / 0 skipped / 0 failed**
  - mdpi_173refs parsed count: 171 → 173 (#55 Åkra / #79 Özcan 復活)
  - #54/#78 char_length: 569ch (merged) → ~280-290ch (cleaned)
  - LLM cost: \$0 (parser fix のみ、--phase 1 only baseline)
  - gitleaks: no leaks found (継続)

Day25 brainstorming で確定した重要な反省事例:
  Day24 Task 1 仮説「DOI URL 直後の <N>. boundary 検出失敗」は誤り、
  真因は「直後の著者姓が非 ASCII Latin uppercase」だった. 実 cleaned
  text を inspect することで Day25 で root cause 特定.

教訓:
  - D25-1: 仮説段階の bug 解説は「観察事実」と「推測される原因」を
    明確に分けるべき. Day24 で観察事実と推測原因を混同して tripwire
    test docstring に encode した反省.
  - D25-2: regex の character class は Unicode 範囲の罠が多い. 著者姓
    のような特殊用途は明示的 character class で範囲を明示する方が安全.
    Day9 lowercase prefix 追加と同じ思想.

Day26+ 候補: Latin Extended-A 範囲拡張 (Top priority、D25-2 延長)、
mdpi_173refs 用 manual_overrides.yaml 構築、CONTRIBUTING.md, pre-commit
hook gitleaks, PyPI 公開, Crossref graceful failure 対応, NLM fuzzy-match
precision, build tools 共通 utility refactor 等.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
git log --oneline -7
```

- [ ] **Step 5: Verify CI passes on new HEAD**

```bash
sleep 30
gh run list --limit 3 --json conclusion,name,headSha,status
```

Expected: most recent run for current HEAD shows `conclusion: success, status: completed`. If `in_progress`, wait 30-60 sec and re-check. If `failure`, run `gh run view <run-id> --log-failed | tail -50` to investigate.

- [ ] **Step 6: Final verification**

```bash
git status
git log --oneline -7
python3 -m pytest tests/ -q 2>&1 | tail -3
gh repo view --json visibility,isPrivate
gh release view v0.1.0 --json tagName,isDraft
gh run list --limit 1 --json conclusion,status
```

Expected:
- clean working tree
- 5 Day25 commits visible (spec / plan / test / fix / archive)
- 107 passed / 0 skipped / 0 failed
- repo PUBLIC, v0.1.0 release intact, CI success

Day25 COMPLETE.

---

## Self-Review Summary

| Check | Result |
|:---|:---|
| Spec coverage | spec §1 background → Task 0 (plan); §2 architecture → all tasks; §3 fix detail → Task 2 (sub-steps A); §4 TDD flow → Task 1 (RED) + Task 2 (GREEN); §5 commits → 5 commits across 4 tasks (spec done); §6 完了条件 → Task 2.D + Task 3.5/6; §7 工数 → embedded; §8 risks → embedded in Task 2 sub-step verifications; §9 out of scope → Day25 README §Day26+ |
| Placeholder scan | `<TASK0_SHA>` / `<TASK1_SHA>` / `<TASK2_SHA>` / `<TASK3_SHA>` are runtime-substituted SHA placeholders for Task 3 archive (intentional, documented in plan). All step content is concrete with exact code/commands. |
| Type consistency | `ReferenceBlock` dataclass fields (`ref_no`, `raw_text`, `char_length`) match across all tests. `main.split_references` / `main.extract_text` / `main.preprocess` / `main.detect_line_numbers` API matches existing main.py (verified via Read in plan-writing phase). `pytest.fixture(scope="module")` pattern for `blocks` matches Day24 implementation. |
| TDD ordering | Task 1 (RED) → Task 2 (GREEN) strict ordering. Task 1 Step 2 explicitly expects 4 FAILs before commit. Task 2 Step 2.A.3 verifies the same tests now PASS before proceeding to tripwire/json updates. |

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-24-day25-split-references-non-ascii-fix.md`. Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks, fast iteration. Task 2 has 4 sub-steps (regex / tripwire / json regen / commit) that benefit from a single dedicated subagent for atomic coordination.

2. **Inline Execution** — execute tasks in this session with checkpoints. The mostly mechanical regex change + json regen lends itself to inline execution.

Choose by responding with `subagent` or `inline`.
