# Day26 bare [A-Z] consistency + DRY refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract module-level constant `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` and unify all 8 ref-boundary regex sites in `main.py` (5 from Day25 in `split_references` + 3 newly identified bare `[A-Z]` in `_strip_pre_references`/`preprocess`) to use `rf"...[{_UPPERCASE_LATIN1}]..."` f-string interpolation, eliminating the bare `[A-Z]` ASCII-only character classes that cause latent inline-header parsing bugs with non-ASCII Latin uppercase author surnames (Å, Ö, É, etc.).

**Architecture:** Strict TDD 2-commit cycle (Day25 pattern). Commit N: append 4 unit tests to existing `tests/test_main_split_references.py` (case 2 inline header + Å, case 2 ASCII baseline, case 3 fallback + Ö, preprocess counter accuracy) — 3 fail RED, 1 passes baseline. Commit N+1: refactor `main.py` by adding `_UPPERCASE_LATIN1` constant near `_strip_pre_references` (Stage 2 section start) + replacing 8 regex literals with `rf"...[{_UPPERCASE_LATIN1}]..."` + compressing Day25's 5-line duplicate docstring into 3-line reference — all 4 new tests + existing 107 must pass = 111 passed.

**Tech Stack:** Python 3.11+ (3.14 local), pytest 9.x, stdlib `re` only (no new dependencies). Constant value: `"A-ZÀ-ÖØ-Þ"` covers ASCII A-Z (U+0041-U+005A) + Latin-1 Supplement uppercase À-Ö (U+00C0-U+00D6) + Ø-Þ (U+00D8-U+00DE), excluding U+00D7 (×).

**Spec reference:** `docs/superpowers/specs/2026-05-24-day26-bare-uppercase-consistency-design.md` (commit `36c49e6`)

**Pre-state:**
- HEAD: `36c49e6` (Day26 spec)
- Repo: PUBLIC, CI green
- Tests: 107 passed / 0 skipped / 0 failed
- Day25 added literal `[A-ZÀ-ÖØ-Þ]` in 5 places in `split_references` (lines ~423, ~441 area)
- Day25 code review identified 3 bare `[A-Z]` remaining (lines 299, 303, 353)

**Total commits:** 5 (1 spec already + 1 plan + 1 TDD RED + 1 TDD GREEN/refactor + 1 archive)

---

## File Structure

### Files MODIFIED in Task 1 (TDD RED)

| File | Lines added | Responsibility |
|:---|:---:|:---|
| `tests/test_main_split_references.py` | +~70 | Append 4 Day26 unit tests after existing Day25 tests: case 2 inline header (Å + ASCII baseline), case 3 fallback (Ö), preprocess counter accuracy |

### Files MODIFIED in Task 2 (TDD GREEN/refactor)

| File | Lines changed | Why |
|:---|:---:|:---|
| `main.py` | +~13 (constant + comment) / -2 (docstring compress) / 8 string-literal refactor | Add `_UPPERCASE_LATIN1` constant + comment block near `_strip_pre_references` (Stage 2 section start) + refactor 8 regex sites (5 Day25 + 3 Day26 new) to `rf"...[{_UPPERCASE_LATIN1}]..."` + compress Day25's duplicate 5-line docstring in `split_references` to 3-line reference |

### Files CREATED in Task 3 (Day26 archive)

| File | Why |
|:---|:---|
| `docs/sessions/day26/README.md` | Day26 session index |
| `docs/sessions/day26/DAY26_LESSONS_LEARNED.md` | Day26 retrospective (D26-1, D26-2 lessons) |

### Files NOT TOUCHED

- All other modules (`mdpi_parser.py`, `crossref_check.py`, `nlm_catalog_check.py`, `three_class_classifier.py`, `journal_audit.py`)
- All fixtures (apa_45refs, cell_45refs, mdpi_173refs, vancouver_35refs, three_class_classification) — Phase 1 output unchanged after refactor (refactor is semantics-preserving)
- Other test files (`test_split_references_doi_boundary.py`, `test_integration_*.py`, etc.)
- `requirements.txt` (no new deps)

---

## Task 0: Commit this plan

**Files:**
- Modify: `docs/superpowers/plans/2026-05-24-day26-bare-uppercase-consistency.md` (just written)

- [ ] **Step 1: Stage and review**

```bash
git add docs/superpowers/plans/2026-05-24-day26-bare-uppercase-consistency.md
git status --short
```

Expected: 1 file added.

- [ ] **Step 2: Commit**

```bash
git commit -m "$(cat <<'EOF'
docs(plan): add Day26 bare [A-Z] consistency + DRY refactor plan

spec (commit 36c49e6) に基づく 4 task の bite-sized 実装計画.

主要 task:
  - Task 1: TDD RED — tests/test_main_split_references.py に Day26 用
    4 unit test 追記 (case 2 inline header + Å, case 2 ASCII baseline,
    case 3 fallback + Ö, preprocess counter accuracy), 3 件 FAIL 確認
  - Task 2: TDD GREEN/refactor — main.py に _UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"
    定数追加 + 8 箱所 (Day25 既存 5 + Day26 新規 3) を
    rf"...[{_UPPERCASE_LATIN1}]..." f-string 参照に統一 + Day25 docstring
    圧縮 (5 行 → 3 行 reference)
  - Task 3: Day26 archive (README + LESSONS) + push + CI verify

期待: 107 passed/0 skipped → 111 passed/0 skipped、commit 計 5 件、
工数 ~2h、LLM cost \$0.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: Verify**

Run: `git log --oneline -2`
Expected: HEAD = `docs(plan):` ..., HEAD~1 = `36c49e6` (`docs(spec):` ...).

---

## Task 1: TDD RED — append 4 unit tests (`test(prep)` commit)

**Files:**
- Modify: `tests/test_main_split_references.py` (append at end)

- [ ] **Step 1: Verify current file state**

```bash
wc -l tests/test_main_split_references.py
tail -10 tests/test_main_split_references.py
```

Expected: file exists from Day25 (~80 lines), ends with `test_split_references_does_not_detect_inside_doi_url` function. New tests will be appended after this.

- [ ] **Step 2: Append 4 Day26 unit tests**

Use Edit tool to append the following block after the last existing test. Find the last line of the file (likely `assert "ijms20092358" in blocks[0].raw_text` or similar) and append after it (with 2 blank lines separator):

```python


# ============================================================================
# Day26: _strip_pre_references + preprocess の Latin-1 uppercase 対応 unit test
# ============================================================================


def test_strip_pre_references_case2_inline_header_with_aring():
    """Case 2 (inline "References 1. Author...") で Å (U+00C5) 先頭著者を
    boundary として認識する.

    Day26: bare [A-Z] → [A-ZÀ-ÖØ-Þ] 統一前は inline header 検出失敗 →
    Case 3 fallback も同じ理由で失敗 → 結果 pre-references 部分が strip
    されず本文が parser に流入する bug.
    現状 (Day25 末) FAIL、Day26 fix で GREEN 化予定.
    """
    text = "Some intro paragraph blah blah References 1. Åberg S. Title. Journal 2020."
    stripped, found = main._strip_pre_references(text)
    assert found is True, "inline header should be detected"
    assert stripped.startswith("1. Åberg"), (
        f"expected stripped text to start with '1. Åberg', got: {stripped[:40]}"
    )


def test_strip_pre_references_case2_inline_header_with_ascii_baseline():
    """Case 2 で ASCII 著者の場合の baseline 動作 (refactor 後も不変)."""
    text = "Some intro References 1. Smith J. Title. Journal 2020."
    stripped, found = main._strip_pre_references(text)
    assert found is True
    assert stripped.startswith("1. Smith")


def test_strip_pre_references_case3_fallback_with_oumlaut():
    """Case 3 fallback で Ö (U+00D6) 先頭著者を boundary として認識する.

    Case 1 (独立行 References ヘッダー) なし、Case 2 (inline) なしの corpus
    で、最初の "1. {大文字}" にジャンプする保守的フォールバック.
    Day25 fix の延長で Case 3 でも Latin-1 を cover.
    """
    text = "Random preamble text with no References heading. 1. Özcan U. Title. Journal 2020."
    stripped, found = main._strip_pre_references(text)
    # Case 3 は found=False で返る (fallback fix なので確実な strip ではない)
    assert found is False
    assert stripped.startswith("1. Özcan"), (
        f"expected stripped text to start with '1. Özcan', got: {stripped[:40]}"
    )


def test_preprocess_counts_aring_refs_correctly():
    """preprocess() の PreprocessTrace.ref_blocks_found counter が
    Latin-1 uppercase 著者の ref も正しくカウントする (Day26 fix).

    旧 bare [A-Z] では counter が undercount、診断 log の信頼性低下.
    """
    # 3 refs: 1 ASCII + 2 Latin-1
    text = "1. Smith J. Title A. Journal 2020.\n2. Åkra S. Title B. Journal 2021.\n3. Özcan U. Title C. Journal 2022."
    _cleaned, trace = main.preprocess(text, main.detect_line_numbers(text))
    assert trace.ref_blocks_found == 3, (
        f"ref_blocks_found counter should detect all 3 refs (1 ASCII + 2 Latin-1), "
        f"got {trace.ref_blocks_found}"
    )
```

- [ ] **Step 3: Run new tests to verify TDD RED**

```bash
python3 -m pytest tests/test_main_split_references.py::test_strip_pre_references_case2_inline_header_with_aring tests/test_main_split_references.py::test_strip_pre_references_case2_inline_header_with_ascii_baseline tests/test_main_split_references.py::test_strip_pre_references_case3_fallback_with_oumlaut tests/test_main_split_references.py::test_preprocess_counts_aring_refs_correctly -v 2>&1 | tail -25
```

Expected: **1 passed + 3 failed**:
- `test_strip_pre_references_case2_inline_header_with_aring` → FAIL (current bare `[A-Z]` doesn't match `Å`, falls through to Case 3 which also fails, returns unstripped text)
- `test_strip_pre_references_case2_inline_header_with_ascii_baseline` → PASS (ASCII works fine)
- `test_strip_pre_references_case3_fallback_with_oumlaut` → FAIL (current bare `[A-Z]` doesn't match `Ö`, returns unstripped text)
- `test_preprocess_counts_aring_refs_correctly` → FAIL (current bare `[A-Z]` only counts the ASCII ref #1, undercount)

If different results:
- All 4 PASS: bug already fixed somehow — investigate
- All 4 FAIL: ASCII baseline shouldn't fail — investigate (could be import error or test infrastructure)

Record the failure messages for review.

- [ ] **Step 4: Confirm existing tests still pass**

```bash
python3 -m pytest tests/ -q 2>&1 | tail -5
```

Expected: 107 passed + 3 failed + 1 passed (from new tests) = `108 passed, 3 failed, 0 skipped` or similar. The 3 failures are the new Day26 RED tests; existing 107 still pass.

- [ ] **Step 5: Commit (TDD RED)**

```bash
git add tests/test_main_split_references.py
git commit -m "$(cat <<'EOF'
test(prep): add failing unit tests for _strip_pre_references + preprocess Latin-1 support (Day26 Task 1 TDD RED)

Day25 Task 2 code review で発見された main.py 内 bare [A-Z] 3 箱所
(L299 _strip_pre_references Case 2, L303 Case 3, L353 preprocess
ref_blocks_found counter) の latent bug を corpus 非依存合成 input
で再現する unit test 4 件追加.

新規 test (tests/test_main_split_references.py 末尾追記):
  - test_strip_pre_references_case2_inline_header_with_aring: FAIL
    (Å U+00C5 inline header detection、L299 bare [A-Z] が原因)
  - test_strip_pre_references_case2_inline_header_with_ascii_baseline: PASS
    (refactor 後も挙動不変の sanity check)
  - test_strip_pre_references_case3_fallback_with_oumlaut: FAIL
    (Ö U+00D6 fallback detection、L303 bare [A-Z] が原因)
  - test_preprocess_counts_aring_refs_correctly: FAIL
    (Å/Ö 著者 ref の counter undercount、L353 bare [A-Z] が原因)

期待 TDD RED 結果: 1 passed (ASCII baseline) + 3 failed (Å/Ö 関連).

次 commit (refactor(parse)) で main.py に _UPPERCASE_LATIN1 定数を導入
+ 8 箱所 (Day25 既存 5 + Day26 新規 3) を rf"...[{_UPPERCASE_LATIN1}]..."
f-string 参照に統一、本 3 件を GREEN 化予定.

spec: docs/superpowers/specs/2026-05-24-day26-bare-uppercase-consistency-design.md
plan: docs/superpowers/plans/2026-05-24-day26-bare-uppercase-consistency.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: Verify commit history**

Run: `git log --oneline -4`
Expected: HEAD = `test(prep): add failing unit tests…`, HEAD~1 = `docs(plan): …`, HEAD~2 = `36c49e6` (docs(spec): …).

No push (push reserved for Task 2/3).

---

## Task 2: TDD GREEN/refactor — `_UPPERCASE_LATIN1` constant + 8-site unification (`refactor(parse)` commit)

**Files:**
- Modify: `main.py` (add constant near line ~290, refactor lines 299, 303, 353, ~423, ~441, compress docstring around 414)

### Sub-step 2.A: Add `_UPPERCASE_LATIN1` constant

- [ ] **Step 2.A.1: Read context around `_strip_pre_references`**

```bash
sed -n '285,300p' main.py
```

Identify the Stage 2 section header (or the line immediately before `def _strip_pre_references`).

- [ ] **Step 2.A.2: Insert constant definition before `def _strip_pre_references`**

Use Edit tool. Find:

```python
def _strip_pre_references(text: str) -> tuple[str, bool]:
```

Replace with:

```python
# Character class fragment for non-ASCII Latin uppercase author surnames.
# Used in ref-boundary regex lookaheads across split_references(),
# _strip_pre_references(), and preprocess() to recognize Norwegian/German/
# French/Spanish/Portuguese surnames starting with Å Ö É Ñ Ø Ý Þ etc.
# - A-Z: ASCII uppercase (U+0041-U+005A)
# - À-Ö: Latin-1 Supplement uppercase A-O (U+00C0-U+00D6)
# - Ø-Þ: Latin-1 Supplement uppercase remainder (U+00D8-U+00DE)
# - U+00D7 (× multiplication sign) is intentionally EXCLUDED.
# Day25 (split_references) と Day26 (_strip_pre_references + preprocess
# ref_blocks_found counter) で導入. Day27+ で Latin Extended-A (Š Č Ł 等)
# 拡張時は本定数を 1 行 update で 8 箇所へ伝播.
_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"


def _strip_pre_references(text: str) -> tuple[str, bool]:
```

### Sub-step 2.B: Refactor 3 new bare `[A-Z]` sites (Day26 target)

- [ ] **Step 2.B.1: L299 `_strip_pre_references` Case 2 inline header**

Use Edit tool. Find:

```python
    m = re.search(r"(?i)\b(references|bibliography)\s+(?=\d+\.\s+[A-Z])", text)
```

Replace with:

```python
    m = re.search(rf"(?i)\b(references|bibliography)\s+(?=\d+\.\s+[{_UPPERCASE_LATIN1}])", text)
```

- [ ] **Step 2.B.2: L303 `_strip_pre_references` Case 3 fallback**

Use Edit tool. Find:

```python
    m = re.search(r"(?<![\d.])1\.\s+[A-Z]", text)
```

Replace with:

```python
    m = re.search(rf"(?<![\d.])1\.\s+[{_UPPERCASE_LATIN1}]", text)
```

- [ ] **Step 2.B.3: L353 `preprocess` ref_blocks_found counter**

Use Edit tool. Find:

```python
    blocks = re.findall(r"(?<![\d.])\d+\.\s+[A-Z]", text)
```

Replace with:

```python
    blocks = re.findall(rf"(?<![\d.])\d+\.\s+[{_UPPERCASE_LATIN1}]", text)
```

### Sub-step 2.C: Refactor Day25 existing 5 sites in `split_references`

- [ ] **Step 2.C.1: Update `matcher` regex (around line 423)**

Use Edit tool. Find:

```python
    matcher = re.compile(
        r"(?<![\d.])(\d+)[\.\s]+"
        r"(?=[A-ZÀ-ÖØ-Þ]|van\s|de\s+[A-ZÀ-ÖØ-Þ]|du\s+[A-ZÀ-ÖØ-Þ]|den\s+[A-ZÀ-ÖØ-Þ]|von\s+[A-ZÀ-ÖØ-Þ])"
    )
```

Replace with:

```python
    matcher = re.compile(
        rf"(?<![\d.])(\d+)[\.\s]+"
        rf"(?=[{_UPPERCASE_LATIN1}]|van\s|de\s+[{_UPPERCASE_LATIN1}]|du\s+[{_UPPERCASE_LATIN1}]|den\s+[{_UPPERCASE_LATIN1}]|von\s+[{_UPPERCASE_LATIN1}])"
    )
```

- [ ] **Step 2.C.2: Update `standard` fallback regex (around line 441)**

Use Edit tool. Find:

```python
        standard = re.compile(
            r"(?<![\d.])(\d+)\.\s+"
            r"(?=[A-ZÀ-ÖØ-Þ]|van\s|de\s+[A-ZÀ-ÖØ-Þ]|du\s+[A-ZÀ-ÖØ-Þ]|den\s+[A-ZÀ-ÖØ-Þ]|von\s+[A-ZÀ-ÖØ-Þ])"
        )
```

Replace with:

```python
        standard = re.compile(
            rf"(?<![\d.])(\d+)\.\s+"
            rf"(?=[{_UPPERCASE_LATIN1}]|van\s|de\s+[{_UPPERCASE_LATIN1}]|du\s+[{_UPPERCASE_LATIN1}]|den\s+[{_UPPERCASE_LATIN1}]|von\s+[{_UPPERCASE_LATIN1}])"
        )
```

### Sub-step 2.D: Compress Day25 docstring (around line 414)

- [ ] **Step 2.D.1: Replace Day25's 5-line duplicate explanation with 3-line reference**

Use Edit tool. Find:

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
```

Replace with:

```python
    # より寛容な候補検出: ピリオド or 空白で数字と著者を区切る
    # NOTE: lookahead allows lowercase prefixes for Dutch/French surnames
    # (van, de, du, den, von) which start with lowercase letters.
    # Without this, refs like "40. van der Biessen" are silently dropped.
    # Latin-1 Supplement uppercase support は _UPPERCASE_LATIN1 定数 (本 file
    # 上部、Stage 2 セクション開始部) で定義. Day25 で split_references()、
    # Day26 で _strip_pre_references() + preprocess() に統一適用.
```

### Sub-step 2.E: Verify + commit + push

- [ ] **Step 2.E.1: Verify bare `[A-Z]` no longer present in main.py**

```bash
grep -nE '\[A-Z\]' main.py
```

Expected: NO output (0 hits). The constant value `"A-ZÀ-ÖØ-Þ"` does not contain `[` brackets, so this grep should miss it.

- [ ] **Step 2.E.2: Verify `_UPPERCASE_LATIN1` usage count**

```bash
grep -c "_UPPERCASE_LATIN1" main.py
```

Expected: **≥ 11** (1 constant definition + 5 in matcher + 5 in standard fallback). Actually more precisely:
- 1 definition line
- 5 in `matcher` regex (1 standalone + 4 inside van/de/du/den/von)
- 5 in `standard` regex (same structure)
- 3 in single-occurrence regexes (L299, L303, L353)
- Plus comments mentioning `_UPPERCASE_LATIN1`

Total: ~14+ occurrences. The grep should return at least 9 (lower bound from spec §6 condition #1).

- [ ] **Step 2.E.3: Run Day26 new tests (should now PASS)**

```bash
python3 -m pytest tests/test_main_split_references.py::test_strip_pre_references_case2_inline_header_with_aring tests/test_main_split_references.py::test_strip_pre_references_case2_inline_header_with_ascii_baseline tests/test_main_split_references.py::test_strip_pre_references_case3_fallback_with_oumlaut tests/test_main_split_references.py::test_preprocess_counts_aring_refs_correctly -v 2>&1 | tail -15
```

Expected: **4 passed** (3 previously failing now GREEN + 1 baseline still passing).

- [ ] **Step 2.E.4: Run full pytest**

```bash
python3 -m pytest tests/ -q 2>&1 | tail -5
```

Expected: **111 passed, 0 skipped, 0 failed** (107 baseline + 4 new Day26 tests).

If failures, investigate:
- If `test_split_references_doi_boundary.py` fails: refactor changed behavior — check regex equivalence
- If `test_integration_mdpi_173refs.py` or other integration tests fail: parser output changed — investigate

- [ ] **Step 2.E.5: Verify Day25 docstring compression**

```bash
grep -A2 "Latin-1 Supplement uppercase support は _UPPERCASE_LATIN1 定数" main.py
```

Expected: hits the new 3-line reference comment.

- [ ] **Step 2.E.6: gitleaks check**

```bash
gitleaks detect --no-banner --redact 2>&1 | tail -3
```

Expected: `no leaks found`.

- [ ] **Step 2.E.7: Atomic commit + push**

```bash
git add main.py
git status --short
git commit -m "$(cat <<'EOF'
refactor(parse): extract _UPPERCASE_LATIN1 constant + unify 8 bare/literal regex sites (Day26 Task 2 TDD GREEN)

Day25 fix(split) で導入した literal [A-ZÀ-ÖØ-Þ] 5 箱所 + Day25 code
review で発見された bare [A-Z] 3 箱所の計 8 箱所を、module-level 定数
_UPPERCASE_LATIN1 の f-string 参照に統一する DRY refactor.

新規定数定義 (main.py 上部、Stage 2 セクション開始部、_strip_pre_references
直前):
  _UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"

定数値の範囲:
  - A-Z: ASCII uppercase (U+0041-U+005A)
  - À-Ö: Latin-1 Supplement uppercase A-O (U+00C0-U+00D6)
  - Ø-Þ: Latin-1 Supplement uppercase remainder (U+00D8-U+00DE)
  - U+00D7 (× multiplication sign) は意図的に EXCLUDED

統一対象 8 箱所:
  - L299 _strip_pre_references Case 2 inline header lookahead (bare [A-Z] → [{_UPPERCASE_LATIN1}])
  - L303 _strip_pre_references Case 3 fallback (bare [A-Z] → [{_UPPERCASE_LATIN1}])
  - L353 preprocess ref_blocks_found counter (bare [A-Z] → [{_UPPERCASE_LATIN1}])
  - L423 split_references matcher: 5 positions ([A-ZÀ-ÖØ-Þ] → [{_UPPERCASE_LATIN1}])
  - L441 split_references standard fallback: 5 positions (same)

副作用:
  - Day25 既存 docstring (L414-419) の 5 行重複説明を 3 行 reference に圧縮
    (Latin-1 説明は本 file 上部の定数定義 comment block に集約)
  - 全 f-string は rf"..." prefix (raw + f-string) で regex バックスラッシュ
    エスケープ保持

潜在的 bug 修正:
  L299/L303 の bare [A-Z] により、別 corpus で inline header + 非 ASCII
  著者 (例: "References 1. Åberg") の組合せが出ると pre-references strip
  失敗 → 本文流入の latent bug あり. 本 commit で予防.
  L353 は診断 counter のみで parser 動作影響なしだが、log 信頼性回復.

Day27+ benefit:
  Latin Extended-A (Š Č Ž / Ł Ć Ń Ą Ę 等) 拡張時は _UPPERCASE_LATIN1
  定数 1 行 update で 8 箱所に伝播、保守コスト削減.

Test 結果:
  - Day26 Task 1 RED test 3 件が GREEN 化 (Å/Ö/preprocess counter)
  - 全 tests: 107 passed → 111 passed / 0 skipped / 0 failed.

spec: docs/superpowers/specs/2026-05-24-day26-bare-uppercase-consistency-design.md
plan: docs/superpowers/plans/2026-05-24-day26-bare-uppercase-consistency.md

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
git log --oneline -5
```

- [ ] **Step 2.E.8: Verify push state**

```bash
python3 -m pytest tests/ -q 2>&1 | tail -3
git rev-parse HEAD
git ls-remote origin main | awk '{print $1}'
```

Expected: 111 passed/0 skipped/0 failed, local HEAD == remote main.

---

## Task 3: Day26 archive + CI verification (`docs(sessions)` commit)

**Files:**
- Create: `docs/sessions/day26/README.md`
- Create: `docs/sessions/day26/DAY26_LESSONS_LEARNED.md`

- [ ] **Step 1: Capture final state metrics**

```bash
TEST_RESULT=$(python3 -m pytest tests/ -q 2>&1 | tail -1)
echo "Final test result: $TEST_RESULT"
git log --oneline 36c49e6..HEAD
```

Record:
- Final test count (expected 111 passed / 0 skipped)
- The 4 commits made in Day26 so far (docs(spec) `36c49e6`, docs(plan) Task 0, test(prep) Task 1, refactor(parse) Task 2)

- [ ] **Step 2: Create `docs/sessions/day26/README.md`**

Use Write tool. Substitute `<TASK0_SHA>`, `<TASK1_SHA>`, `<TASK2_SHA>`, `<TASK3_SHA>` with actual SHAs (TASK3 = `(this commit)` placeholder):

```markdown
# Day26 Session Archive (2026-05-24)

## 概要

Day26 セッションは Day25 Task 2 code quality review で発見された `main.py`
内の 3 箱所の bare `[A-Z]` (`_strip_pre_references` Case 2/Case 3 +
`preprocess` ref_blocks_found counter) を `[A-ZÀ-ÖØ-Þ]` に統一しつつ、
Day25 で導入した 5 箱所と合わせて計 8 箱所を **module-level 定数
`_UPPERCASE_LATIN1` の参照**に refactor する DRY 整理セッション.

潜在的 bug 予防 (inline header + 非 ASCII 著者 corpus で pre-references
strip 失敗) + Day27+ Latin Extended-A 拡張時の保守コスト削減 + Day25
docstring の重複説明圧縮を同時達成.

## 主要成果

| 指標 | Day25 末 | Day26 末 |
|:---|:---:|:---:|
| 全 tests | 107 passed / 0 skipped | **111 passed / 0 skipped / 0 failed** |
| 新規 unit test | — | 4 件 (case 2 Å/ASCII baseline + case 3 Ö + preprocess counter) |
| main.py 内 bare `[A-Z]` | 3 箱所残存 (L299, L303, L353) | **0 (完全除去)** |
| `_UPPERCASE_LATIN1` 参照 | — | **8 箱所**で f-string 参照に統一 |
| Day25 docstring | 5 行重複説明 | **3 行 reference に圧縮** (定数定義 comment に集約) |
| LLM cost | — | **$0** (refactor + test 追加のみ) |

## Day26 archive 構成

- `README.md` — 本ファイル (Day26 index)
- `DAY26_LESSONS_LEARNED.md` — Day26 教訓記録 (D26-1, D26-2)
- `../../superpowers/specs/2026-05-24-day26-bare-uppercase-consistency-design.md` — Day26 spec
- `../../superpowers/plans/2026-05-24-day26-bare-uppercase-consistency.md` — Day26 plan

## Day26 commits (chain、5 件)

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `36c49e6` | docs(spec) | Day26 bare [A-Z] consistency + DRY refactor spec |
| 2 | `<TASK0_SHA>` | docs(plan) | Day26 implementation plan |
| 3 | `<TASK1_SHA>` | test(prep) | TDD RED: 4 unit test (case 2 Å/ASCII baseline + case 3 Ö + preprocess counter) |
| 4 | `<TASK2_SHA>` | refactor(parse) | TDD GREEN: _UPPERCASE_LATIN1 定数抽出 + 8 箱所統一 + Day25 docstring 圧縮 |
| 5 | `<TASK3_SHA>` | docs(sessions) | Day26 archive (本 commit) |

## 設計判断

実装 approach は **Q1 (B) module-level 定数抽出 + Q2 (α) 3 箱所全 unit test + Q3 (α) Strict TDD 2-commit** を採用 (spec §1.4). 代替案 Q1 (A) Inline fix のみ / (C) helper function は DRY 違反 or overengineering のため不採用. Q2 (β) 部分 test / (γ) test なし は coverage 不足のため不採用. Q3 (β) 1 atomic は history で「何を fix したか」が不明瞭になるため不採用.

`_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` は Python stdlib re のみ、Latin-1 Supplement uppercase block (À-Ö U+00C0-U+00D6, Ø-Þ U+00D8-U+00DE、× U+00D7 は意図的 excluded) を cover. Day27+ で Latin Extended-A (Š Č Ł 等) 拡張時は本定数 1 行 update で 8 箱所に伝播する設計.

## Day27+ 候補

- **Top priority (Day25 D25-2 延長 + Day26 で機構整備済)**: Latin Extended-A 範囲拡張 (Š Č Ž / Ł Ć Ń Ą Ę / Ő Ű / Ș Ț 等) — `_UPPERCASE_LATIN1` 定数を `"A-ZÀ-ÖØ-ÞĀ-ſ"` 等に拡張する 1 行 update で 8 箱所に伝播 (Day26 で機構整備済のため工数大幅削減)
- mdpi_173refs 固有の manual_overrides.yaml 構築 (Day24 から継承)
- pre-commit hook gitleaks 自動実行 (Day22 handoff パターン 3)
- CONTRIBUTING.md / Issue PR template (Day22 handoff パターン 2)
- PyPI 公開 (v0.2.0 候補)
- pyproject.toml + uv.lock 移行 (CLAUDE.md §8 整合)
- Crossref graceful failure 16 件の対応 (Day22 §6.3 NEW、apa_45refs)
- NLM fuzzy-match precision 改善 (Day22 §6.3 NEW)
- tools/build_*_fixture.py の共通 utility refactor (Day23 code review 指摘)
- deterministic byte-level golden の再構築 (LLM stub 経由、Day28+ 大改修)
```

Substitute `<TASK0_SHA>` etc. with actual SHAs captured in Step 1.

- [ ] **Step 3: Create `docs/sessions/day26/DAY26_LESSONS_LEARNED.md`**

Use Day25 LESSONS as structural reference:
```bash
wc -l docs/sessions/day25/DAY25_LESSONS_LEARNED.md
sed -n '1,40p' docs/sessions/day25/DAY25_LESSONS_LEARNED.md
```

Write `docs/sessions/day26/DAY26_LESSONS_LEARNED.md` with substantive content (target 150-200 lines, smaller than Day25 since scope is smaller). Sections §1-8:

- **§1 概要**: Day25 末 (107 passed, 3 bare [A-Z] 残存) → Day26 末 (111 passed, 8 箱所統一済).
- **§2 brainstorming 段階**: Q1 (B 定数抽出) + Q2 (α 全 3 箱所 unit test) + Q3 (α Strict TDD 2-commit) 確定理由表. 代替案 A/C, β/γ を不採用とした根拠を簡潔に.
- **§3 実装段階の経緯**: 5 commit chain table + Task 2 sub-step (A 定数追加 / B 新規 3 箱所 / C Day25 既存 5 箱所 / D docstring 圧縮 / E verify+commit) の細分化.
- **§4 設計判断と検証**:
  - §4.1 module-level 定数 vs Inline fix 比較 (Day27+ 拡張コスト + cognitive load 観点)
  - §4.2 定数定義位置の選択理由 (Stage 2 セクション開始部、`_strip_pre_references` 直前 が natural)
  - §4.3 docstring の重複説明圧縮の判断 (Day25 説明は定数定義 comment に集約、`split_references` docstring は reference 3 行のみ)
  - §4.4 `rf"..."` (raw + f-string) prefix の必須性 (backslash escape 保持 + 補間両立)
- **§5 実機検証**: test count 推移 (107 → 111) + bare [A-Z] grep 0 hit + _UPPERCASE_LATIN1 usage count + gitleaks clean + CI green.
- **§6 教訓** (D26-1, D26-2、各 事象/学び/適用範囲 subsection):
  - **D26-1**: code review で発見された latent bug は同 session 内で fix するか、明確な「次 session top priority」として記録するか、二択を意識的に. Day25 review で発見した 3 箱所を Day26 で fix できたのは Day25 LESSONS で「Day26+ Top priority」と明示した結果.
  - **D26-2**: 同種パターンが 5 箱所以上に達したら DRY refactor の閾値. Day25 で 5 箱所 literal、Day26 で 3 箱所追加 = 計 8 箱所 → module-level 定数化が自然な節目. 8 箱所すべての update を機械的に grep + replace で済ませられる設計が Day27+ 拡張コストを 5-10 倍削減.
- **§7 残存タスク (Day27+ 候補)**: README §Day27+ と同期 (Latin Extended-A が Top priority、機構整備済なので工数小).
- **§8 次セッション再開プロンプトテンプレート** (3 patterns):
  - パターン 1 (推奨): Latin Extended-A 拡張 (Day26 で機構整備済、定数 1 行 update)
  - パターン 2: mdpi_173refs 固有 manual_overrides.yaml 構築
  - パターン 3: CONTRIBUTING.md / Issue PR template

Target: 150-200 lines.

- [ ] **Step 4: gitleaks final check + commit + push**

```bash
gitleaks detect --no-banner --redact 2>&1 | tail -3
git add docs/sessions/day26/
git status --short
git commit -m "$(cat <<'EOF'
docs(sessions): archive day26 bare [A-Z] consistency + DRY refactor session

Day26 セッション (2026-05-24) の archive.

構成:
  - Task 0: docs(plan) commit
  - Task 1: TDD RED — tests/test_main_split_references.py に 4 unit test
    追記 (test(prep))
  - Task 2: TDD GREEN/refactor — main.py に _UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"
    定数追加 + 8 箱所 (Day25 既存 5 + Day26 新規 3) を rf"...[{_UPPERCASE_LATIN1}]..."
    f-string 参照に統一 + Day25 docstring 圧縮 (refactor(parse) 単一 atomic commit)
  - Task 3: Day26 archive (本 commit)

成果:
  - 全 tests: 107 passed / 0 skipped → **111 passed / 0 skipped / 0 failed**
  - main.py 内 bare [A-Z]: 3 箱所残存 → **0 (完全除去)**
  - _UPPERCASE_LATIN1 参照: 8 箱所で f-string 統一
  - Day25 docstring: 5 行重複説明 → 3 行 reference (定数定義 comment に集約)
  - LLM cost: \$0 (refactor + test 追加のみ)
  - gitleaks: no leaks found (継続)

教訓:
  - D26-1: code review で発見された latent bug は同 session 内 fix か
    「次 session top priority」明示記録の二択を意識的に. Day25 review で
    発見 → Day26 で確実に fix できた.
  - D26-2: 同種 pattern 5 箱所以上で DRY refactor の閾値. Day25 で 5 +
    Day26 で 3 = 計 8 箱所 → 定数化が自然な節目. 機械的 grep+replace で
    Day27+ 拡張コスト 5-10 倍削減.

Day27+ 候補: Latin Extended-A 範囲拡張 (Top priority、Day26 機構整備済
で工数小)、mdpi_173refs 用 manual_overrides.yaml 構築、CONTRIBUTING.md,
pre-commit hook gitleaks, PyPI 公開, Crossref graceful failure 対応,
NLM fuzzy-match precision, build tools 共通 utility refactor 等.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
git log --oneline -7
```

- [ ] **Step 5: Verify CI**

```bash
sleep 30
gh run list --limit 3 --json conclusion,name,headSha,status
```

Expected: most recent run for current HEAD shows `success` or `in_progress`.

- [ ] **Step 6: Final verification**

```bash
git status
git log --oneline -7
python3 -m pytest tests/ -q 2>&1 | tail -3
gh repo view --json visibility,isPrivate
gh release view v0.1.0 --json tagName,isDraft
gh run list --limit 1 --json conclusion,status
```

Expected: clean tree, 5 Day26 commits visible, 111 passed/0 skipped, PUBLIC, release intact, CI success. **Day26 COMPLETE.**

---

## Self-Review Summary

| Check | Result |
|:---|:---|
| Spec coverage | spec §1 background → Task 0 (plan); §2 architecture → all tasks; §3 refactor detail → Task 2 (sub-steps A-D); §4 TDD flow → Task 1 (RED) + Task 2 (GREEN); §5 commits → 5 commits across 4 tasks (spec done); §6 完了条件 → Task 2.E + Task 3.5/6; §7 工数 → embedded; §8 risks → embedded in Task 2 sub-steps; §9 out of scope → Day26 README §Day27+ |
| Placeholder scan | `<TASK0_SHA>` / `<TASK1_SHA>` / `<TASK2_SHA>` / `<TASK3_SHA>` are runtime-substituted SHA placeholders for Task 3 archive (intentional, documented). All step content is concrete with exact code/commands. |
| Type consistency | `_UPPERCASE_LATIN1` constant name matches across spec/plan and 8 usage sites. `_strip_pre_references` / `preprocess` / `detect_line_numbers` / `PreprocessTrace` references match main.py current signatures (verified via Read). `rf"..."` prefix pattern consistent across all 8 sites. |
| TDD ordering | Task 1 (RED) → Task 2 (GREEN) strict ordering. Task 1 Step 3 explicitly expects 3 FAILs + 1 PASS before commit. Task 2 Step 2.E.3 verifies the same tests now PASS before commit. |

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-24-day26-bare-uppercase-consistency.md`. Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks. Task 2 has 5 sub-steps (constant add / 3 new sites / Day25 5 sites / docstring compress / verify+commit) — single subagent handles them atomically.

2. **Inline Execution** — execute tasks in this session with checkpoints. Mostly mechanical refactor with high text-match precision.

Choose by responding with `subagent` or `inline`.
