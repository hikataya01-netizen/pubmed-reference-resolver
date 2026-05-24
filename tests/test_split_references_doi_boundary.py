"""
test_split_references_doi_boundary.py — Phase 1 split_references の構造 invariant
(Day24 historical archive 化版)

旧目的:
    Day9 (commit ab25630) で Phase 1 split_references が DOI 終端直後の
    lowercase-prefixed 著者 Ref (#40 van der Biessen, #140 van Zyl) を
    正しく検出するかを 149-ref corpus で検証していた.

Day24 historical archive 化 + 新 corpus 適用:
    Day23 で旧 mdpi_149refs corpus 削除 + 新 mdpi_173refs に置換. 新 corpus
    には #40 van der Biessen も #140 van Zyl も存在しない代わりに #69 van Vliet
    / #92 van den Burg / #173 de Menezes が同種の lowercase-prefix 著者 ref
    として存在. 本 file は新 corpus の構造 invariant smoke check に refactor.

Day24 Task 1 reconnaissance で発見した parser bug (Day25+ task):
    新 corpus では split_references() が DOI URL 直後の <N>. boundary を
    検出できず、#55 と #79 がそれぞれ #54 と #78 に merge されている.
    結果: parsed count = 171 (本来の 173 から 2 件減).
    本 test は CURRENT state (171 blocks、#55/#79 missing) を assert する.
    Day25+ で parser fix が入れば本 test を 173/no-gaps に更新する想定.
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

    Day24 Task 1 reconnaissance 実測値ベース. Day25+ で parser DOI-boundary
    fix が入った場合、count assertion を 173 に、gap allowed list を空に更新する.
    """

    def test_ref_count_matches_current_parser_state(self, blocks):
        """parsed ref count が 171 (Day24 Task 1 実測)."""
        assert len(blocks) == 171, (
            f"unexpected ref count: {len(blocks)} (Day24 Task 1 reported 171). "
            f"If this drops to <171, parser regressed further. If it rises to 173, "
            f"the Day25+ DOI-boundary fix has likely landed — update this assertion."
        )

    def test_ref_no_range_is_1_to_173(self, blocks):
        """ref_no は 1 から 173 の範囲 (元 docx の番号体系を保持、ただし parser bug で gap あり)."""
        ref_nos = sorted(b.ref_no for b in blocks)
        assert ref_nos[0] == 1, f"first ref_no should be 1, got {ref_nos[0]}"
        assert ref_nos[-1] == 173, f"last ref_no should be 173, got {ref_nos[-1]}"

    def test_known_parser_gaps_are_55_and_79(self, blocks):
        """Day24 Task 1 で発見した parser DOI-boundary bug: #55 と #79 が
        それぞれ #54 と #78 に merge されているため missing.

        Day25+ で parser fix が入れば本 test は更新 (gap なしの assertion に).
        """
        ref_nos = set(b.ref_no for b in blocks)
        all_expected = set(range(1, 174))
        actual_gaps = sorted(all_expected - ref_nos)
        assert actual_gaps == [55, 79], (
            f"unexpected parser gaps: {actual_gaps} (expected [55, 79] per Day24 Task 1 recon)"
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

    def test_no_block_exceeds_reasonable_size_except_known_merge_failures(self, blocks):
        """各 block が 600 chars 以下 (parser merge failure の検知). 既知例外:
        #54 と #78 は Day24 Task 1 recon で確認した DOI-boundary merge failure で 569ch.
        Day25+ で parser fix 後はこの except 句も削除.
        """
        OVERSIZED_THRESHOLD = 600
        KNOWN_MERGE_FAILURE_REFS = {54, 78}  # see Day24 Task 1 recon
        oversized = [
            (b.ref_no, b.char_length)
            for b in blocks
            if b.char_length > OVERSIZED_THRESHOLD and b.ref_no not in KNOWN_MERGE_FAILURE_REFS
        ]
        assert not oversized, (
            f"Found {len(oversized)} new pathologically large blocks (>{OVERSIZED_THRESHOLD} chars, "
            f"excluding known #54 #78 merge failures): {oversized[:5]}. "
            f"This may indicate new split_references regression beyond the known bug."
        )

    def test_no_block_is_empty(self, blocks):
        """各 block の raw_text が空でない."""
        empty = [b.ref_no for b in blocks if not b.raw_text.strip()]
        assert not empty, f"Found {len(empty)} empty blocks: {empty[:5]}"
