# SPEC: Day25 — `split_references()` non-ASCII Latin uppercase boundary fix

**作成日**: 2026-05-24 (Day25 brainstorming 完了時)
**著者**: Claude Code (Opus 4.7 / 1M context) / 承認: 片山英樹
**位置付け**: Day24 Task 1 reconnaissance で発見した `split_references()` parser bug (新 mdpi_173refs corpus で #55 と #79 が消失) の root cause を特定し fix する。Day24 で tripwire pattern で encode 済みの test 3 件 + 新規 unit test + positive integration test の更新も同時実施。
**前提**: Day24 末 (HEAD `988a5b1`、Day24 archive 含む) で main branch、100 passed / 0 skipped / 0 failed、repo PUBLIC、CI green、v0.1.0 release accessible、gitleaks clean (全 7 fingerprint Day23 で refresh 済)

---

## 1. 背景と目的

### 1.1 Day24 Task 1 reconnaissance の発見 (parser bug 検出)

Day24 Task 1 で新 mdpi_173refs corpus (PMC13164670 Nutrients review、本来 173 refs) に対し `main.split_references()` を実行した結果、**parsed count = 171** であり以下 2 件が消失していることを発見:

- `#55` (`Åkra S; Aksnes T; ...`) が `#54` (Longo M; Zatterale F; ...) に merge され、#54 が 569ch に肥大化
- `#79` (`Özcan U; Cao Q; ...`) が `#78` (Sakaguchi M; Fujisaka S; ...) に merge され、#78 が 569ch に肥大化

Day24 では recon 段階で「DOI URL 直後の `<N>.` boundary detection 失敗」と仮説立てし、`tests/test_split_references_doi_boundary.py` に tripwire pattern (Day24 D24-3 教訓) で current state を assert:
- `test_ref_count_matches_current_parser_state`: `len(blocks) == 171`
- `test_known_parser_gaps_are_55_and_79`: `actual_gaps == [55, 79]`
- `test_no_block_exceeds_reasonable_size_except_known_merge_failures`: `KNOWN_MERGE_FAILURE_REFS = {54, 78}` を exclude

これにより Day25+ で parser fix が入ると 3 件の test が自動 fail し、修正方向を明示する設計。

### 1.2 Day25 root cause 特定 (brainstorming で発覚)

Day25 brainstorming Q1 立てる前に `preprocess()` 後の cleaned text を実機で inspect した結果、Day24 recon 段階の仮説が誤りで、真の root cause が判明:

```
... https://doi.org/10.3390/ijms20092358\n55. Åkra S; Aksnes T; ...
... https://doi.org/10.1016/j.cmet.2016.12.008\n79. Özcan U; Cao Q; ...
```

DOI URL は無関係。`#55` と `#79` の直後の著者姓が `Åkra` (Å = U+00C5) と `Özcan` (Ö = U+00D6) であり、これら **Latin-1 Supplement uppercase** が `split_references()` の regex lookahead `[A-Z]` (ASCII U+0041-U+005A のみ) でマッチせず boundary detection が失敗していた。

該当 regex (`main.py` line 415-417 area):

```python
matcher = re.compile(
    r"(?<![\d.])(\d+)[\.\s]+"
    r"(?=[A-Z]|van\s|de\s+[A-Z]|du\s+[A-Z]|den\s+[A-Z]|von\s+[A-Z])"
)
```

`van/de/du/den/von` の lowercase prefix は既に明示的に handle (Day9 で `40. van der Biessen` 等のため追加) だが、Latin-1 Supplement uppercase は cover されていなかった。

### 1.3 目的

1. **Parser fix**: `split_references()` regex (matcher + standard fallback の 2 箇所) の `[A-Z]` を `[A-ZÀ-ÖØ-Þ]` に拡張、Latin-1 Supplement uppercase で始まる著者姓を boundary として認識
2. **TDD discipline**: 合成 input ベースの unit test (Å/Ö/É の 3 言語 + ASCII baseline + DOI URL 誤検出回避) を新規 `tests/test_main_split_references.py` に追加、TDD RED commit 先行
3. **Day24 tripwire 自動更新**: 3 件の tripwire test を新状態 (count=173 / gaps=[] / KNOWN_MERGE empty) に更新、#55/#79 positive integration test 2 件追加
4. **fixture baseline 再生成**: `tests/fixtures/mdpi_173refs/expected_phase1_intermediate.json` を 171→173 entry で再生成 (Phase 1 deterministic golden)

### 1.4 設計判断の経緯 (brainstorming 質問)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | regex 拡張 approach | **(A) 明示的 character class 拡張 `[A-ZÀ-ÖØ-Þ]`** (Python stdlib re のみ、Latin-1 Supplement uppercase block を cover、× U+00D7 を excluded) |
| Q2 | TDD + test 更新の組み合わせ | **(α) Strict TDD 2-commit**: TDD RED unit test commit → TDD GREEN fix + tripwire 更新 + positive integration test 追加 + json 再生成 (Day22 SSL fix と同 pattern) |

---

## 2. Architecture & ファイル配置

### 2.1 改変対象 (4 file)

| File | 種別 | 改変内容 | 影響行数 |
|:---|:---|:---|:---|
| `main.py` (line 415-417 + line 433-435 area) | 修正 | regex 2 箇所 (matcher + standard fallback) の `[A-Z]` を `[A-ZÀ-ÖØ-Þ]` に拡張、既存 `van/de/du/den/von` lowercase prefix 部分の `[A-Z]` 5 箇所も同様に拡張、docstring comment 拡張 | +2 行 (各 regex 1 文字追加) + comment +5 行 |
| `tests/test_main_split_references.py` (NEW) | 新規 | TDD RED 用 unit test 5 件 (ASCII baseline + Å/Ö/É boundary + DOI URL 誤検出回避) | 新規 ~80 行 |
| `tests/test_split_references_doi_boundary.py` | 更新 | tripwire 3 件を新状態 (count=173 / gaps=[] / KNOWN_MERGE 削除) に更新 + #55/#79 positive starts_with test 2 件追加 + docstring 更新 | +~30 行 / -~15 行 |
| `tests/fixtures/mdpi_173refs/expected_phase1_intermediate.json` | 再生成 | 171 → 173 refs の Phase 1 baseline 再生成 (deterministic golden、ref_no 増加 + #54/#78 内容圧縮) | byte レベル変更 |

### 2.2 改変対象外 (確認のみ)

- `mdpi_parser.py` (Phase 2 構造化、本 bug と無関係)
- `crossref_check.py` / `nlm_catalog_check.py` / `three_class_classifier.py` / `journal_audit.py`
- 他 4 fixture (apa_45refs / cell_45refs / vancouver_35refs / three_class_classification) — 影響なし (非 ASCII Latin uppercase で始まる ref を含まない、Day9-Day23 で確認済の英語著者 corpus)
- 他 integration test (apa_45refs / cell_45refs / mdpi_173refs / vancouver_35refs) — fixture baseline は variability-bearing なので影響受けず

### 2.3 新規作成 (Day25 archive)

| File | 用途 |
|:---|:---|
| `docs/superpowers/specs/2026-05-24-day25-split-references-non-ascii-fix-design.md` | 本 SPEC |
| `docs/superpowers/plans/2026-05-24-day25-split-references-non-ascii-fix.md` | writing-plans 出力 |
| `docs/sessions/day25/README.md` | Day25 archive index |
| `docs/sessions/day25/DAY25_LESSONS_LEARNED.md` | Day25 教訓記録 |

---

## 3. Fix 実装詳細 (Approach A)

### 3.1 main.py regex 拡張

**変更前** (line 415-417):

```python
matcher = re.compile(
    r"(?<![\d.])(\d+)[\.\s]+"
    r"(?=[A-Z]|van\s|de\s+[A-Z]|du\s+[A-Z]|den\s+[A-Z]|von\s+[A-Z])"
)
```

**変更後**:

```python
matcher = re.compile(
    r"(?<![\d.])(\d+)[\.\s]+"
    r"(?=[A-ZÀ-ÖØ-Þ]|van\s|de\s+[A-ZÀ-ÖØ-Þ]|du\s+[A-ZÀ-ÖØ-Þ]|den\s+[A-ZÀ-ÖØ-Þ]|von\s+[A-ZÀ-ÖØ-Þ])"
)
```

**変更前** (line 433-435 area、standard fallback):

```python
standard = re.compile(
    r"(?<![\d.])(\d+)\.\s+"
    r"(?=[A-Z]|van\s|de\s+[A-Z]|du\s+[A-Z]|den\s+[A-Z]|von\s+[A-Z])"
)
```

**変更後** (同じ拡張):

```python
standard = re.compile(
    r"(?<![\d.])(\d+)\.\s+"
    r"(?=[A-ZÀ-ÖØ-Þ]|van\s|de\s+[A-ZÀ-ÖØ-Þ]|du\s+[A-ZÀ-ÖØ-Þ]|den\s+[A-ZÀ-ÖØ-Þ]|von\s+[A-ZÀ-ÖØ-Þ])"
)
```

### 3.2 docstring + comment 更新 (line 412-414 area)

```diff
 # より寛容な候補検出: ピリオド or 空白で数字と著者を区切る
 # NOTE: lookahead allows lowercase prefixes for Dutch/French surnames
 # (van, de, du, den, von) which start with lowercase letters.
+# Day25: lookahead also accepts Latin-1 Supplement uppercase (À-Ö, Ø-Þ)
+# for Norwegian/German/French/Spanish/Portuguese surnames starting with
+# Å Ö É Ñ etc. Without [A-ZÀ-ÖØ-Þ], refs like "55. Åkra" or "79. Özcan"
+# are silently merged into the preceding ref (Day24 Task 1 reconnaissance
+# discovered this on mdpi_173refs corpus).
 # Without this, refs like "40. van der Biessen" are silently dropped.
```

### 3.3 `[A-ZÀ-ÖØ-Þ]` 範囲解説

- `A-Z` (U+0041-U+005A): ASCII uppercase
- `À-Ö` (U+00C0-U+00D6): Latin-1 Supplement uppercase A-O block: À Á Â Ã Ä Å Æ Ç È É Ê Ë Ì Í Î Ï Ð Ñ Ò Ó Ô Õ Ö
- 飛ばす U+00D7: `×` multiplication sign (文字ではない、意図的に excluded)
- `Ø-Þ` (U+00D8-U+00DE): Latin-1 Supplement uppercase remainder: Ø Ù Ú Û Ü Ý Þ

カバー範囲: ノルウェー / スウェーデン / デンマーク / ドイツ / オランダ / フランス / スペイン / ポルトガル / アイスランド (一部) / トルコ (一部) 等。

Out of scope: Latin Extended-A 範囲 (Š Ž Č 等チェコ・ポーランド語、Day26+ で必要時拡張)。

---

## 4. TDD flow 詳細 (2-commit cycle、Day22 SSL fix と同 pattern)

### 4.1 Commit N: TDD RED `tests/test_main_split_references.py` 新規

新規 file で 5 unit test を追加:

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

**期待される TDD RED 結果** (Commit N 直後):

| Test | Day24 末 (現状) | Day25 fix 後 |
|:---|:---:|:---:|
| `test_split_references_detects_ascii_uppercase_boundary` | PASS | PASS |
| `test_split_references_detects_norwegian_aring_boundary` | **FAIL** (RED) | PASS (GREEN) |
| `test_split_references_detects_german_oumlaut_boundary` | **FAIL** (RED) | PASS (GREEN) |
| `test_split_references_detects_french_acute_boundary` | **FAIL** (RED) | PASS (GREEN) |
| `test_split_references_does_not_detect_inside_doi_url` | PASS | PASS |

### 4.2 Commit N+1: TDD GREEN fix + tripwire update + positive integration test

#### (a) main.py regex 拡張 (§3.1 参照)

#### (b) `tests/test_split_references_doi_boundary.py` tripwire 更新

3 件の test assertion + method 名 rename:

```diff
- def test_ref_count_matches_current_parser_state(self, blocks):
+ def test_ref_count_is_173(self, blocks):
-     """parsed ref count が 171 (Day24 Task 1 実測)."""
+     """parsed ref count が 173 (Day25 fix(split) 後実測、Day24 末の 171 から +2 復活)."""
-     assert len(blocks) == 171, (
+     assert len(blocks) == 173, (
          f"unexpected ref count: {len(blocks)} ..."
      )

- def test_known_parser_gaps_are_55_and_79(self, blocks):
+ def test_no_parser_gaps_in_corpus(self, blocks):
-     """Day24 Task 1 で発見した parser DOI-boundary bug: #55 と #79 が..."""
+     """Day25 fix(split) 後: ref_no に gap が無いこと (1-173 全件揃う)."""
      ref_nos = set(b.ref_no for b in blocks)
      all_expected = set(range(1, 174))
      actual_gaps = sorted(all_expected - ref_nos)
-     assert actual_gaps == [55, 79], ...
+     assert actual_gaps == [], ...

- def test_no_block_exceeds_reasonable_size_except_known_merge_failures(self, blocks):
+ def test_no_block_exceeds_reasonable_size(self, blocks):
-     """各 block が 600 chars 以下... 既知例外: #54 と #78..."""
+     """各 block が 600 chars 以下 (parser merge failure の検知)."""
      OVERSIZED_THRESHOLD = 600
-     KNOWN_MERGE_FAILURE_REFS = {54, 78}
      oversized = [
          (b.ref_no, b.char_length)
          for b in blocks
-         if b.char_length > OVERSIZED_THRESHOLD and b.ref_no not in KNOWN_MERGE_FAILURE_REFS
+         if b.char_length > OVERSIZED_THRESHOLD
      ]
      assert not oversized, ...
```

#### (c) positive integration test 追加 (同 file に追記)

```python
    def test_ref55_starts_with_aring_author(self, blocks):
        """Day25 fix(split) で復活した #55 が "Åkra" で始まることを確認.

        Day24 Task 1 で merge 検出した bug の corpus-level regression guard.
        """
        by_ref_no = {b.ref_no: b for b in blocks}
        assert 55 in by_ref_no, "ref #55 missing (Day25 fix(split) may have regressed)"
        assert by_ref_no[55].raw_text.startswith("Åkra"), \
            f"ref #55 should start with 'Åkra', got: {by_ref_no[55].raw_text[:40]}"


    def test_ref79_starts_with_oumlaut_author(self, blocks):
        """Day25 fix(split) で復活した #79 が "Özcan" で始まることを確認."""
        by_ref_no = {b.ref_no: b for b in blocks}
        assert 79 in by_ref_no, "ref #79 missing (Day25 fix(split) may have regressed)"
        assert by_ref_no[79].raw_text.startswith("Özcan"), \
            f"ref #79 should start with 'Özcan', got: {by_ref_no[79].raw_text[:40]}"
```

#### (d) module docstring 更新

Day24 で書いた parser bug 記述 (line 16-21 area) を「Day25 fix 後の現状」に更新:

```diff
 Day24 Task 1 reconnaissance で発見した parser bug (Day25+ task):
-    新 corpus では split_references() が DOI URL 直後の <N>. boundary を
-    検出できず、#55 と #79 がそれぞれ #54 と #78 に merge されている.
-    結果: parsed count = 171 (本来の 173 から 2 件減).
-    本 test は CURRENT state (171 blocks、#55/#79 missing) を assert する.
-    Day25+ で parser fix が入れば本 test を 173/no-gaps に更新する想定.
+ Day25 fix(split) で解消した parser bug:
+    Day24 Task 1 で「DOI URL 直後の <N>. boundary 検出失敗」と仮説立てしたが、
+    Day25 brainstorming で真因が「直後の著者姓が非 ASCII Latin uppercase
+    (Å Ö 等)」だったと判明. main.py regex を [A-Z] → [A-ZÀ-ÖØ-Þ] に拡張する
+    fix で #55 Åkra と #79 Özcan が復活、parsed count 171 → 173.
+    本 test は新状態 (173 blocks、no gaps) を assert.
```

#### (e) `tests/fixtures/mdpi_173refs/expected_phase1_intermediate.json` 再生成

```bash
python3 main.py tests/fixtures/mdpi_173refs/input_References.docx \
  --output-dir /tmp/day25_mdpi_173refs_phase1 --phase 1
cp /tmp/day25_mdpi_173refs_phase1/phase1_intermediate.json \
   tests/fixtures/mdpi_173refs/expected_phase1_intermediate.json
```

ref count 171 → 173 になり、`expected_phase1_intermediate.json` の byte 内容が変化。LLM 不使用 (Phase 1 のみ)。

---

## 5. Commit 計画 (5 commits)

| 順 | type | scope | 内容 |
|:---:|:---|:---|:---|
| 1 | `docs(spec)` | Pre | 本 SPEC を archive |
| 2 | `docs(plan)` | Pre | writing-plans 出力を `docs/superpowers/plans/` に commit |
| 3 | `test(split)` | TDD RED | `tests/test_main_split_references.py` 新規 (5 unit test、4 件 FAIL 確認後 commit) |
| 4 | `fix(split)` | TDD GREEN | main.py regex 拡張 + tripwire 3 件更新 + #55/#79 positive test 2 件追加 + json 再生成 (全 pass 確認後 commit) |
| 5 | `docs(sessions)` | Post | Day25 archive (README + LESSONS) |

合計 **5 commits** (Day22 SSL fix と同型)。

---

## 6. 完了条件 (10 項目)

| # | 条件 | 確認方法 |
|:---:|:---|:---|
| 1 | `tests/test_main_split_references.py` 新規追加 | `ls tests/test_main_split_references.py` 存在 |
| 2 | `main.py` regex 2 箇所が `[A-ZÀ-ÖØ-Þ]` を含む | `grep -c "A-ZÀ-ÖØ-Þ" main.py` ≥ 2 |
| 3 | 新規 unit test の 4 件 (Å/Ö/É/non-DOI) が PASS | `pytest tests/test_main_split_references.py -v` で全 PASS |
| 4 | tripwire 3 件が新状態 (count=173 / gaps=[] / KNOWN_MERGE 削除) で PASS | `pytest tests/test_split_references_doi_boundary.py -v` 全 PASS |
| 5 | #55/#79 positive test (starts_with Åkra/Özcan) が PASS | 同上 |
| 6 | `expected_phase1_intermediate.json` 再生成 (171→173 entry に拡大) | `python3 -c "import json; print(len(json.load(open('tests/fixtures/mdpi_173refs/expected_phase1_intermediate.json'))))"` で実体確認 |
| 7 | 全 test pass (regression なし) | `pytest tests/ -q` で **107 passed / 0 skipped / 0 failed** (見込: 100 + 新規 unit 5 + positive integration 2) |
| 8 | gitleaks 継続 clean | `gitleaks detect --no-banner --redact` で `no leaks found` |
| 9 | TDD 2 commit 順序 (test RED → fix GREEN) | `git log --oneline -5` で `test(split):` が `fix(split):` より先 (HEAD~1 = fix、HEAD~2 = test) |
| 10 | CI green for HEAD | `gh run list --limit 1 --jq .[0].conclusion` = `success` |

---

## 7. 工数見積もり

| Phase | 内容 | 見積 |
|:---:|:---|---:|
| Pre | SPEC + PLAN archive | 30 min |
| Commit 1 (TDD RED) | 新 unit test file 作成 + pytest で 4 件 FAIL 確認 + commit | 30 min |
| Commit 2 (TDD GREEN) | main.py regex 拡張 + tripwire 3 件更新 + positive test 2 件追加 + json 再生成 + 全 pytest 確認 + commit | 60 min |
| Post | Day25 archive (README + LESSONS) + push + CI 確認 | 30 min |
| **合計** | | **~2.5 h** |

LLM cost: **$0** (parser fix のみ、baseline 再生成は Phase 1 のみで LLM 不使用)

---

## 8. 想定リスク

| リスク | 確率 | 影響 | 対応 |
|:---|:---:|:---:|:---|
| `À-Ö` 範囲に `×` (U+00D7) が混入する誤記 | 低 | 低 | regex 文字列 `[A-ZÀ-ÖØ-Þ]` で `Ö` (U+00D6) と `Ø` (U+00D8) の間に `×` (U+00D7) を意図的に excluded、目視確認 + Python 実機 verify |
| 新 unit test が予想 (4件 FAIL) と異なる結果 | 低 | 中 | TDD RED 段階で各 test の失敗 mode を inspect、もし `Étienne` が現状 LIS で偶然通る等の余事象あれば test を補強 |
| `expected_phase1_intermediate.json` 再生成で他 fixture/test が影響 | 低 | 中 | mdpi_173refs fixture のみ更新、他 fixture (apa/cell/vancouver_35refs) は無関係。`test_pre_integration_baseline.py::test_expected_phase1_intermediate_exists` は readability check のみで byte 内容 assert なし |
| Latin-1 範囲外の uppercase で始まる ref (例: チェコ語 Š = U+0160) が将来出る | 中 | 低 | Day25 では out of scope、Day26+ で Latin Extended-A 対応検討、本 spec §9 (Out of Scope) に記録 |
| LIS filter が拡張後 candidate 増で挙動変わる | 低-中 | 中 | LIS は monotonic 単純化なので候補増えても通常は良化方向、ただし pytest 全件 pass で final verify |
| TDD RED commit の中間状態で CI が fail | 中 | 低 | CI matrix は HEAD のみ run、TDD RED commit が CI 起動するが GREEN commit 直後にすぐ走るので一時的 fail は容認 (history は正しい順序) |
| fix で apa_45refs / cell_45refs / vancouver_35refs の Phase 1 parser 結果が変わる | 低 | 中 | 上記 3 fixture には非 ASCII Latin uppercase で始まる ref がない (apa は心理学英語、cell は AI 工学英語、vancouver は Supportive Care 英語)、影響なし見込 |

---

## 9. Out of Scope (Day26+ 候補)

- **Latin Extended-A 範囲** (チェコ語 Š Č Ž / ポーランド語 Ł Ć Ń Ą Ę / ハンガリー語 Ő Ű / ルーマニア語 Ș Ț) — Day25 では `[A-ZÀ-ÖØ-Þ]` で Latin-1 のみ cover、Extended-A 必要な corpus が出てきたら Day26+ で `[A-ZÀ-ÖØ-ÞĀ-ſ]` 等に拡張
- **Greek / Cyrillic uppercase** (Άθηνα, Иванов 等) — 学術論文の著者姓では稀、必要時に別途
- **mdpi_173refs 用 manual_overrides.yaml 構築** (Day24 Day25+ list)
- **pre-commit hook gitleaks 自動実行** (Day22 handoff パターン 3、Day25+ list)
- **CONTRIBUTING.md / Issue PR template / PyPI 公開 / pyproject.toml 移行** (Day25+ list)
- **Crossref graceful failure 16 件の対応 / NLM fuzzy-match precision 改善** (Day22 §6.3 NEW、Day25+ list)
- **tools/build_*_fixture.py の共通 utility refactor** (Day23 code review 指摘、Day25+ list)

---

## 10. 参照

- Day22 brainstorming spec: `docs/superpowers/specs/2026-05-24-rule3-nlm-ssl-fix-design.md` (TDD 2-commit pattern の参考)
- Day24 brainstorming spec: `docs/superpowers/specs/2026-05-24-day24-mdpi-test-restoration-design.md` (tripwire test の origin)
- Day24 LESSONS `DAY24_LESSONS_LEARNED.md` §6 D24-3 (corpus 偵察で発見した bug を tripwire pattern で test に encode → future fix 自動通知)
- Day24 LESSONS §Day25+ 候補 (本 fix が Top priority と明示)
- main.py `split_references()` (line 397-451): 修正対象関数
- `tests/test_split_references_doi_boundary.py` (Day24 で書いた tripwire test、本 commit で更新対象)
- `tests/fixtures/mdpi_173refs/`: 再生成対象 fixture (expected_phase1_intermediate.json のみ)
- Unicode reference: Latin-1 Supplement block (U+0080-U+00FF) の uppercase range は U+00C0-U+00DE excluding U+00D7
- Day9 commit ab25630: lowercase prefix (van/de/du/den/von) 対応の origin (本 fix と類似 pattern の先行事例)

---

**承認**: 片山英樹 (brainstorming Q1-Q2 + design 全 3 sections)
**次工程**: writing-plans skill で bite-sized implementation plan を作成
