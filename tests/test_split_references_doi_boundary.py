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
