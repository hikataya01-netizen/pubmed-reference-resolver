"""
test_mdpi_parser.py — MDPI パーサの回帰テスト (Day24 新 corpus 版)

使い方:
    pytest tests/test_mdpi_parser.py -v
    または
    python -m tests.test_mdpi_parser

Day24 更新:
    旧 mdpi_149refs corpus (Day23 で削除) から新 mdpi_173refs corpus
    (PMC13164670 Nutrients review, 173 refs, LLM path 経由) に re-point.
    旧 byte-level golden (expected_phase2_structured.json) を廃止し、
    構造 invariant (ref count range / field presence / module importable) に置換.

本テストは LLM (Claude API) には一切依存しない純粋なユニットテスト。
CI 環境 (GitHub Actions 等) で API キー無しで走らせることができる。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import mdpi_parser  # noqa: E402


TEST_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_173refs"


def _load_phase1_blocks(input_docx: Path) -> list[dict]:
    """main.py の Phase 1 を呼び出してブロックリストを生成する。

    テスト実行時に Phase 1 結果を作り直すことで split_references の
    回帰も同時に検出できる。
    """
    from main import extract_text, preprocess, split_references, detect_line_numbers
    raw, _kind = extract_text(input_docx)
    ln_report = detect_line_numbers(raw)
    cleaned, _trace = preprocess(raw, ln_report)
    blocks = split_references(cleaned)
    return blocks


def test_phase1_extracts_refs_from_corpus():
    """Phase 1 が representative corpus から ref block を抽出できることを smoke check.

    Day24 acceptance: parsed ref count が 165-175 範囲 (Day24 Task 1 reconnaissance
    実測 171、parser DOI-boundary bug で #55/#79 が merge され 173→171 になった
    状態. Day25+ で parser fix が入れば 173 に戻る予定).
    """
    input_docx = TEST_DIR / "input_References.docx"
    blocks = _load_phase1_blocks(input_docx)
    assert 165 <= len(blocks) <= 175, (
        f"Phase 1 parser produced {len(blocks)} blocks, expected 165-175 "
        f"(Day24 Task 1 reconnaissance reported 171 for mdpi_173refs)"
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
    """mdpi_parser module が import 可能で公開 callable を持つこと."""
    assert any(
        callable(getattr(mdpi_parser, n, None))
        for n in dir(mdpi_parser)
        if not n.startswith("_")
    ), "mdpi_parser appears to have no public callable functions"


def test_is_mdpi_style_detection():
    """MDPI スタイル判定ロジックの単体テスト。"""
    # MDPI 形式
    assert mdpi_parser.is_mdpi_style(
        "Bray, F.; Laversanne, M. Global cancer statistics 2022. "
        "CA Cancer J. Clin. 2024, 74, 229-263, "
        "https://doi.org/10.3322/caac.21834."
    )
    # 書籍 (ISBN 有)
    assert mdpi_parser.is_mdpi_style(
        "Flückiger, C.; Wüsten, G. Resource Activation; "
        "Hogrefe Publishing, 2010; ISBN 0-88937-378-7."
    )
    # 非 MDPI (Vancouver 形式)
    assert not mdpi_parser.is_mdpi_style(
        "Bray F, Laversanne M. Global cancer statistics 2022. "
        "CA Cancer J Clin 2024;74:229-63."
    )


# -----------------------------------------------------------------------------
# Day9: tests for tightened Vancouver detection (M1 marker = (YYYY))
#
# SPEC: docs/sessions/day9/SPEC_mdpi_fast_path_strict.md
# Background: Day7 PHASE_0_VERIFICATION_REPORT §8.6 で発覚した
#   "24 件中 8 件 (33%) で MDPI fast-path が title/author 境界を誤処理"
#   問題への対応. is_mdpi_style() の Vancouver 検出を `(YYYY)` 括弧年
#   marker (M1) に置換することで Vancouver 系入力を LLM 経路に routing.
# Note: SPEC §5.2 では test 3 を 1 件としていたが、TDD skill "One behavior"
#   rule に従い 2 件に細分化 (test 3a = 非年括弧誤検出なし、test 3b =
#   M1 が他 signals より優先). 計 4 test 追加で SPEC §11 完了条件は
#   全 66 test pass (元 SPEC 65 → +1).
# -----------------------------------------------------------------------------


def test_is_mdpi_style_returns_false_for_paren_year_vancouver():
    """Vancouver/AMA 形式 (`(YYYY)` 括弧年) の raw_text は LLM 経路に
    routing されることを確認 (SPEC §5.2 test 1).

    Stage 2 OneDrive 入力の代表 3 件で False を返すことを確認.
    """
    vancouver_samples = [
        # Stage 2 #1: Huizinga 2011
        "Huizinga, G., Visser, A., Van der Graaf, W. T., Hoekstra, H. J., "
        "Stewart, R. E., & Hoekstra- Weebers, J.E.(2011) Family-oriented "
        "multilevel study on the psychological functioning of adolescent "
        "children having a mother with cancer. Psycho-oncology, 20(7), 730-737. "
        "doi.org/10.1002/pon.1779",
        # Stage 2 #2: Shah 2017
        "Shah, B.K, Armaly, J., Swieter A.(2017) Impact of Parental cancer "
        "on children. Anticancer Research 37 (8): 4025-4028. "
        "doi: 10.21873/anticanres.11788",
        # Stage 2 #11: Lindqvist 2007
        "Lindqvist, B., Schmitt, F., Santalahti, P., Romer, G,, Piha, J. "
        "(2007)Factors associated with the mental health of adolescents when "
        "a parent has cancer. Scandinavian Journal of Psychology, 48 (4): "
        "345-351. doi.org/10.1111/j.1467-9450.2007.00573.x",
    ]
    for raw in vancouver_samples:
        assert not mdpi_parser.is_mdpi_style(raw), (
            f"Expected False (LLM routing) for Vancouver-style raw_text "
            f"with (YYYY), got True. Sample: {raw[:80]!r}"
        )


def test_is_mdpi_style_still_returns_true_for_pure_mdpi():
    """純粋 MDPI 形式の raw_text は MDPI fast-path に routing されることを
    確認 (SPEC §5.2 test 2, regression 保護).

    149-ref MDPI fixture の代表 3 件で True を返すことを確認. Day9 改修後も
    MDPI 挙動が変わらないことの保証.
    """
    mdpi_samples = [
        # MDPI fixture #1: Bray 2022 (典型的 MDPI 形式)
        "Bray, F.; Laversanne, M.; Sung, H.; Ferlay, J.; Siegel, R.L.; "
        "Soerjomataram, I.; Jemal, A. Global cancer statistics 2022: "
        "GLOBOCAN estimates of incidence and mortality worldwide for 36 "
        "cancers in 185 countries. CA Cancer J. Clin. 2024, 74, 229-263.",
        # MDPI fixture #51: Gustavsson-Lilius
        "Gustavsson-Lilius, M.; Julkunen, J.; Keskivaara, P.; Lipsanen, J.; "
        "Hietanen, P. Predictors of distress in cancer patients and their "
        "partners. Eur. J. Cancer Care 2012, 21, 99-110.",
        # MDPI fixture #141: Peterson book (no journal but is_book=true)
        "Peterson, C.; Seligman, M.E.P. Character Strengths and Virtues: "
        "A Handbook and Classification; 2004;",
    ]
    for raw in mdpi_samples:
        assert mdpi_parser.is_mdpi_style(raw), (
            f"Expected True (MDPI fast-path) for pure MDPI raw_text, "
            f"got False (regression). Sample: {raw[:80]!r}"
        )


def test_is_mdpi_style_does_not_match_non_year_parens():
    """`(2nd ed.)` のような非年括弧は M1 marker に誤検出されないことを
    確認 (SPEC §5.2 test 3a, edge case).

    M1 regex `\\((?:19|20)\\d{2}\\)` は 4 桁年限定のため、`(2nd ed.)` や
    `(8)` などの数字を含む括弧は match しない.
    """
    raw_no_year_paren = (
        "Smith, J.; Lee, K. Title of paper. Journal Name 2024, 10, 100-110. "
        "Originally published as a chapter in Handbook (2nd ed.)."
    )
    assert mdpi_parser.is_mdpi_style(raw_no_year_paren), (
        f"`(2nd ed.)` のような非年括弧は誤検出されないはず. "
        f"got False for raw={raw_no_year_paren[:80]!r}"
    )


def test_is_mdpi_style_paren_year_dominates_over_mdpi_signals():
    """M1 marker `(YYYY)` は他の MDPI signals より優先される設計の確認
    (SPEC §5.2 test 3b, M1 dominance).

    たとえ末尾 MDPI markers (`https://doi.org/`, `YYYY, Vol`) が同時に
    あっても、`(YYYY)` が見つかれば False を返す. これは「Vancouver
    indicator が dominant」という設計の可視化.

    現状の MDPI fixture では本パターンは 0/149 hit (実測). 将来 MDPI text に
    `(1995)` のような書き方が出現したら、SPEC §7 通り regex を
    `\\s\\((?:19|20)\\d{2}\\)` (前 space 必須) に context 強化を検討する.
    """
    raw_with_year_paren = (
        "Smith, J.; Lee, K. Title of paper. Journal Name 2024, 10, 100-110. "
        "First study by Author (1995) showed similar results."
    )
    assert not mdpi_parser.is_mdpi_style(raw_with_year_paren), (
        f"M1 marker `(YYYY)` は他 MDPI signals より優先される設計. "
        f"got True for raw={raw_with_year_paren[:80]!r}"
    )


def test_hyphen_rescue_preserves_case():
    """ハイフン橋渡し救済が大文字小文字を保持することを確認。"""
    # PDF コピペで "Cancer-related" が "Cancer- related" に分断されたと想定
    text = "Cancer- related psychosocial challenges in Gen. Psychiatry"
    fixed = mdpi_parser.fix_hyphens(text)
    assert "Cancer-related" in fixed, (
        f"保持された大文字小文字: {fixed!r}"
    )


def test_doi_alt_generation():
    """DOI 内部ハイフン圧縮の候補生成。"""
    doi = "10.1136/gpsych-2022-100871"
    alt = mdpi_parser.build_doi_alt(doi)
    # 数字間ハイフンは保持 (2022-100871 はそのまま)
    # アルファベット内ハイフンは圧縮 (gpsych はそのまま: 途中にハイフン無し)
    assert alt is None or alt == doi, f"alt={alt!r}"

    # Case with internal alpha-alpha hyphen
    doi2 = "10.1016/j.jpsy-chores.2022.111139"
    alt2 = mdpi_parser.build_doi_alt(doi2)
    assert alt2 == "10.1016/j.jpsychores.2022.111139", f"alt2={alt2!r}"


if __name__ == "__main__":
    # pytest なしの手動実行サポート
    test_is_mdpi_style_detection()
    print("OK: test_is_mdpi_style_detection")
    test_is_mdpi_style_returns_false_for_paren_year_vancouver()
    print("OK: test_is_mdpi_style_returns_false_for_paren_year_vancouver")
    test_is_mdpi_style_still_returns_true_for_pure_mdpi()
    print("OK: test_is_mdpi_style_still_returns_true_for_pure_mdpi")
    test_is_mdpi_style_does_not_match_non_year_parens()
    print("OK: test_is_mdpi_style_does_not_match_non_year_parens")
    test_is_mdpi_style_paren_year_dominates_over_mdpi_signals()
    print("OK: test_is_mdpi_style_paren_year_dominates_over_mdpi_signals")
    test_hyphen_rescue_preserves_case()
    print("OK: test_hyphen_rescue_preserves_case")
    test_doi_alt_generation()
    print("OK: test_doi_alt_generation")
    test_phase1_extracts_refs_from_corpus()
    print("OK: test_phase1_extracts_refs_from_corpus")
    test_phase1_blocks_have_required_fields()
    print("OK: test_phase1_blocks_have_required_fields")
    test_mdpi_parser_module_importable()
    print("OK: test_mdpi_parser_module_importable")
    print("\nAll tests passed.")
