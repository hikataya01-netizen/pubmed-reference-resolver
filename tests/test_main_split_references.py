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
