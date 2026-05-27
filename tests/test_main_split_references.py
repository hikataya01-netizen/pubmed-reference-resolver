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


# ============================================================================
# Day28: Latin Extended-A 大文字対応 unit test
# (Šafránek/Łukasiewicz/Čech/Żelazny で始まる ref boundary の検出)
# ============================================================================


def test_split_references_detects_czech_scaron_boundary():
    """Š (U+0160、チェコ語) で始まる著者の ref boundary が検出される.

    Day28 で Latin Extended-A 拡張するまでは FAIL (boundary loss).
    Day25/26 で対応した Latin-1 Supplement (À-Þ) では Š が範囲外のため
    `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` では recognize できない.
    """
    cleaned = "1. Smith J. Title A. Journal 2020.\n2. Šafránek M. Title B. Journal 2021."
    blocks = main.split_references(cleaned)
    assert len(blocks) == 2, f"expected 2 blocks, got {len(blocks)}"
    assert blocks[1].ref_no == 2
    assert blocks[1].raw_text.startswith("Šafránek")


def test_split_references_detects_polish_lstroke_boundary():
    """Ł (U+0141、ポーランド語) で始まる著者の ref boundary が検出される.

    Day28 で Latin Extended-A 拡張するまでは FAIL.
    """
    cleaned = "1. Smith J. Title A. Journal 2020.\n2. Łukasiewicz J. Title B. Journal 2021."
    blocks = main.split_references(cleaned)
    assert len(blocks) == 2, f"expected 2 blocks, got {len(blocks)}"
    assert blocks[1].ref_no == 2
    assert blocks[1].raw_text.startswith("Łukasiewicz")


def test_split_references_detects_czech_ccaron_boundary():
    """Č (U+010C、チェコ語) で始まる著者の ref boundary が検出される.

    Day28 で Latin Extended-A 拡張するまでは FAIL.
    Latin Extended-A の lower edge (U+0100-U+0136 範囲) をカバー.
    """
    cleaned = "1. Smith J. Title A. Journal 2020.\n2. Čech V. Title B. Journal 2021."
    blocks = main.split_references(cleaned)
    assert len(blocks) == 2, f"expected 2 blocks, got {len(blocks)}"
    assert blocks[1].ref_no == 2
    assert blocks[1].raw_text.startswith("Čech")


def test_split_references_detects_polish_zdot_boundary():
    """Ż (U+017B、ポーランド語) で始まる著者の ref boundary が検出される.

    Day28 で Latin Extended-A 拡張するまでは FAIL.
    Latin Extended-A の upper edge (U+014A-U+017D 範囲) をカバー.
    """
    cleaned = "1. Smith J. Title A. Journal 2020.\n2. Żelazny K. Title B. Journal 2021."
    blocks = main.split_references(cleaned)
    assert len(blocks) == 2, f"expected 2 blocks, got {len(blocks)}"
    assert blocks[1].ref_no == 2
    assert blocks[1].raw_text.startswith("Żelazny")
