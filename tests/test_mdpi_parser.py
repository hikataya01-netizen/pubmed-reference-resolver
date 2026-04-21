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

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import mdpi_parser  # noqa: E402


TEST_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_149refs"


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


def test_mdpi_parser_149refs_full_pipeline():
    """149 件の References.docx 全体に MDPI パーサを適用する。"""
    input_docx = TEST_DIR / "input_References.docx"
    expected_json = TEST_DIR / "expected_phase2_structured.json"

    blocks = _load_phase1_blocks(input_docx)
    assert len(blocks) == 149, (
        f"Phase 1 split_references で 149 件を切り出せること "
        f"(actual: {len(blocks)})"
    )

    results = mdpi_parser.structure_all_mdpi(blocks, verbose=False)

    # サマリ一致テスト
    hi = sum(1 for r in results if r.get("parsing_confidence") == "high")
    md = sum(1 for r in results if r.get("parsing_confidence") == "medium")
    lo = sum(1 for r in results if r.get("parsing_confidence") == "low")
    book = sum(1 for r in results if r.get("is_book"))
    doi = sum(1 for r in results if r.get("doi"))

    # 許容範囲 (パーサ改善で微変動する可能性を考慮)
    assert hi >= 125, f"high={hi} は >= 125 であること"
    assert doi >= 125, f"DOI検出件数={doi} は >= 125 であること"
    assert book >= 10, f"is_book件数={book} は >= 10 であること"

    # 詳細一致テスト (ゴールドスタンダード比較)
    expected = json.loads(expected_json.read_text(encoding="utf-8"))
    expected_structured = expected.get("stage3_structured", expected)
    expected_by_refno = {r["ref_no"]: r for r in expected_structured}

    mismatches: list[str] = []
    for r in results:
        exp = expected_by_refno.get(r["ref_no"])
        if not exp:
            continue
        # core fields の一致を確認
        for key in ("title", "journal", "year", "doi", "is_book"):
            if r.get(key) != exp.get(key):
                mismatches.append(
                    f"Ref #{r['ref_no']} field={key} "
                    f"got={r.get(key)!r} expected={exp.get(key)!r}"
                )
    if mismatches:
        msg = "\n  ".join(mismatches[:20])
        assert False, f"{len(mismatches)} 件のフィールド不一致:\n  {msg}"


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
    test_hyphen_rescue_preserves_case()
    print("OK: test_hyphen_rescue_preserves_case")
    test_doi_alt_generation()
    print("OK: test_doi_alt_generation")
    test_mdpi_parser_149refs_full_pipeline()
    print("OK: test_mdpi_parser_149refs_full_pipeline")
    print("\nAll tests passed.")
