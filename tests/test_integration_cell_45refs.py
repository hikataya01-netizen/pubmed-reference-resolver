"""
Integration test for the Cell-style 45-ref Day17 baseline.

Background:
    Day9 (commit ab25630) introduced the Vancouver Veto in is_mdpi_style()
    so that references with `(YYYY)` paren year are routed to the LLM path
    instead of the MDPI fast-path. Day16 extended the Veto regex to
    `\\((?:19|20)\\d{2}[a-z]?\\)` to handle APA 7 disambiguation suffixes
    like `(2020a)`. Day17 adds Cell-style 45-ref fixture as the third golden
    for this regression, extending coverage to Cell Press citation style
    (compressed initials `J.A.` + `, and ` connector + no issue number).

    PMC OA 3 iScience (Cell Press) papers (Molecular Biology / Biomedical /
    AI Engineering) provide 15 refs each, all in Cell style with `(YYYY)`
    paren year. All 3 papers under CC BY 4.0.

Fixture file naming convention (Day11 hybrid):
    expected_*  : deterministic output (byte/structural match required)
    baseline_*  : variability-bearing output (LLM/PubMed-dependent)

API key requirement: NONE.
    Tests 1-3, 6-7 use parser-only paths (no LLM).
    Tests 4-5, 8 read baseline files directly without re-running Phase 2-4.

Refs: docs/sessions/day17/SPEC_cell_45refs_fixture.md (commit c4ac9c8);
      docs/sessions/day17/PLAN_cell_45refs_fixture.md (commit 4fcb1a6);
      tests/fixtures/cell_45refs/README.md.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

FIXTURES = Path(__file__).parent / "fixtures" / "cell_45refs"
INPUT_DOCX = FIXTURES / "input_References.docx"
EXPECTED_PHASE1 = FIXTURES / "expected_phase1_intermediate.json"
BASELINE_PHASE3 = FIXTURES / "baseline_phase3_resolved.json"
BASELINE_REPORT = FIXTURES / "baseline_report.md"
BASELINE_THREE_CLASS = FIXTURES / "baseline_three_class_classification.json"


# Day17 Phase 0b 実測値 (document-of-record baseline 凍結).
# LLM/PubMed/Crossref/NLM の揺らぎで本値が変動する場合は、
# Phase 2-4 を再実行し baseline_*.json/md を再生成した上で、
# 本定数も更新する運用とする (Day11 Vancouver と同じ思想).
EXPECTED_RESOLVED_COUNT = 30  # Day17 Phase 0b 実測 (README.md 参照)
EXPECTED_REPORT_CRITICAL_COUNT = 0  # Day17 Phase 0b 実測


# -----------------------------------------------------------------------------
# Helper (pattern borrowed from test_integration_vancouver_24refs.py)
# -----------------------------------------------------------------------------


def _load_phase1_blocks_with_ln_report():
    """Phase 1 を再実行し (blocks, ln_report) を返す.

    Returns ReferenceBlock instances matching the signature expected by
    structure_all_references() and is_mdpi_style().
    """
    from main import (  # noqa: E402
        extract_text,
        preprocess,
        split_references,
        detect_line_numbers,
    )

    raw, _kind = extract_text(INPUT_DOCX)
    ln_report = detect_line_numbers(raw)
    cleaned, _trace = preprocess(raw, ln_report)
    blocks = split_references(cleaned)
    return blocks, ln_report


# -----------------------------------------------------------------------------
# Test 1: Vancouver Veto routing for Cell (deterministic)
# -----------------------------------------------------------------------------


def test_cell_45refs_routes_all_to_llm_path():
    """Day9 + Day16 拡張 Vancouver Veto regex の Cell 適用: 45 件すべてが
    is_mdpi_style() で False を返し、LLM path に routing されることを確認.

    Day17 で本 fixture を追加することで、Vancouver Veto の regression 保護を
    Cell-style 表記にも拡張する (Day11 vancouver_24refs / Day16 apa_45refs に
    続く 3 番目の LLM-path 用 golden).
    """
    import mdpi_parser  # noqa: E402

    blocks, _ = _load_phase1_blocks_with_ln_report()
    assert len(blocks) == 45, f"Expected 45 blocks, got {len(blocks)}"

    fast_path_blocks = []
    for b in blocks:
        if mdpi_parser.is_mdpi_style(b.raw_text):
            fast_path_blocks.append(b.ref_no)

    assert fast_path_blocks == [], (
        f"Day16 APA Vancouver Veto regression: {len(fast_path_blocks)} block(s) "
        f"routed to MDPI fast-path (should be 0). "
        f"Affected ref_no: {fast_path_blocks[:5]}"
    )


# -----------------------------------------------------------------------------
# Test 2: Phase 1 reference_blocks deterministic (byte/structural match)
# -----------------------------------------------------------------------------


def test_phase1_reference_blocks_match_expected():
    """Phase 1 (parser-only) の reference_blocks 抽出が expected と一致.

    `input_file` 等の cwd 依存メタフィールドは比較せず、
    stage3_reference_blocks のみを比較 (Day8 _scrub_volatile_lines と同じ思想).
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()

    expected_doc = json.loads(EXPECTED_PHASE1.read_text(encoding="utf-8"))
    expected_blocks = expected_doc["stage3_reference_blocks"]

    assert len(blocks) == len(expected_blocks), (
        f"Block count mismatch: got {len(blocks)}, expected {len(expected_blocks)}"
    )

    for b, exp in zip(
        sorted(blocks, key=lambda x: x.ref_no),
        sorted(expected_blocks, key=lambda x: x["ref_no"]),
    ):
        assert b.ref_no == exp["ref_no"], (
            f"ref_no mismatch: got {b.ref_no}, expected {exp['ref_no']}"
        )
        assert b.raw_text == exp["raw_text"], (
            f"Ref #{b.ref_no} raw_text mismatch.\n"
            f"  got:      {b.raw_text[:80]!r}\n"
            f"  expected: {exp['raw_text'][:80]!r}"
        )
        assert b.char_length == exp["char_length"], (
            f"Ref #{b.ref_no} char_length mismatch: "
            f"got {b.char_length}, expected {exp['char_length']}"
        )


# -----------------------------------------------------------------------------
# Test 3: Reference count = 45
# -----------------------------------------------------------------------------


def test_phase1_extracts_45_reference_blocks():
    """Phase 1 が APA 45-ref fixture から 45 件の reference を抽出.

    deterministic, helps catch parser regressions that change the count.
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()
    assert len(blocks) == 45, f"Expected 45 blocks, got {len(blocks)}"


# -----------------------------------------------------------------------------
# Test 4: Baseline PubMed resolution count (variability-aware)
# -----------------------------------------------------------------------------


def test_baseline_phase3_documents_resolution_count():
    """baseline_phase3_resolved.json (Day16 Phase 0b 実測) に
    解決件数 25/45 (55.6%) が記録されていることを確認.

    本 test は LLM/PubMed を再実行せず baseline file の中身を
    document-of-record として assert する.

    将来の LLM/PubMed 変動で baseline 更新が必要になったら、
    Phase 2-4 を再実行し baseline を更新してから
    本 test の EXPECTED_RESOLVED_COUNT 定数を更新する.
    """
    data = json.loads(BASELINE_PHASE3.read_text(encoding="utf-8"))
    resolutions = data["stage4_pubmed_resolutions"]

    assert len(resolutions) == 45, (
        f"Expected 45 resolution attempts, got {len(resolutions)}"
    )

    resolved_count = sum(1 for r in resolutions if r.get("pmid"))
    assert resolved_count == EXPECTED_RESOLVED_COUNT, (
        f"Day16 APA baseline regression: "
        f"resolved {resolved_count}/45, expected {EXPECTED_RESOLVED_COUNT}/45. "
        f"If LLM/PubMed drift is the cause, regenerate baseline and update test."
    )


# -----------------------------------------------------------------------------
# Test 5: Baseline report quality (zero 重大 errors)
# -----------------------------------------------------------------------------


def test_baseline_report_documents_audit_summary():
    """baseline_report.md (Day16 Phase 0b 実測) のダッシュボードに
    「査読コメント: 重大 | 0」が記録されていることを確認.

    APA 45-ref fixture では Vancouver Veto により MDPI fast-path 起因の
    false positive が抑制され、重大 0 件を達成. 本 test は
    baseline-as-document として、その達成を凍結記録する.
    """
    report = BASELINE_REPORT.read_text(encoding="utf-8")

    # ダッシュボード行: "| 査読コメント: 重大 | 0 | ..."
    # 表記揺れに対応するため柔軟な regex でカウントを抽出
    pattern = re.compile(r"重大\s*\|\s*(\d+)\s*\|", re.MULTILINE)
    match = pattern.search(report)

    assert match is not None, (
        f"baseline_report.md ダッシュボードに「重大 | <N> |」が見つからない. "
        f"report 先頭 500 文字: {report[:500]!r}"
    )

    critical_count = int(match.group(1))
    assert critical_count == EXPECTED_REPORT_CRITICAL_COUNT, (
        f"Day16 APA baseline regression: "
        f"重大 {critical_count} 件, expected {EXPECTED_REPORT_CRITICAL_COUNT} 件. "
        f"If audit logic drift is the cause, regenerate baseline and update test."
    )


# -----------------------------------------------------------------------------
# Test 6: Cell paren year pattern detected in all refs (parser-only)
# -----------------------------------------------------------------------------


def test_cell_paren_year_pattern_detected_in_all_refs():
    """全 45 件の raw text に `(YYYY)` または `(YYYYa)` 等の paren year
    パターンが含まれることを確認 (Cell style の中核特徴を fixture data
    自体が満たすことの assert).

    Day9 + Day16 拡張 Vancouver Veto regex (`\\((?:19|20)\\d{2}[a-z]?\\)`)
    と同じ regex で検証. Cell style は通常 disambiguation suffix を
    使わないが、念のため Day16 拡張 pattern も対応する形で assert.
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()
    paren_year_pattern = re.compile(r"\((?:19|20)\d{2}[a-z]?\)")
    refs_without_paren_year = [
        b.ref_no for b in blocks
        if not paren_year_pattern.search(b.raw_text)
    ]
    assert refs_without_paren_year == [], (
        f"Cell fixture health regression: {len(refs_without_paren_year)} "
        f"ref(s) lack `(YYYY)` pattern. ref_no: {refs_without_paren_year[:5]}"
    )


# -----------------------------------------------------------------------------
# Test 7: Cell `, and ` author separator presence (structural)
# -----------------------------------------------------------------------------


def test_cell_and_author_separator_present():
    """45 件中、最低 20 件が `, and ` を含むことを確認.

    Cell style 規約: 3+ 著者列挙時の最終境界は `, and ` (APA 7 の
    `, & ` に相当). 本 test は fixture が Cell 規約を満たしている
    ことを保証する (build_cell_fixture.py の _format_authors(cell_mode=True)
    出力品質の test data 健全性保護).

    20 という閾値は: 単著 ref / 2 著者 ref / 組織著者 ref がある程度
    含まれることを許容しつつ、3+ 著者 ref が過半数を超えるという経験則
    に基づく.
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()
    refs_with_and = [
        b.ref_no for b in blocks if ", and " in b.raw_text
    ]
    assert len(refs_with_and) >= 20, (
        f"Cell style structural regression: only {len(refs_with_and)}/45 "
        f"refs contain `, and ` (Cell author separator). "
        f"Expected >=20. Refs with separator: {refs_with_and}"
    )


# -----------------------------------------------------------------------------
# Test 8: Three-class classification distribution (document-of-record)
# -----------------------------------------------------------------------------

EXPECTED_THREE_CLASS_DISTRIBUTION = {
    "A": 14,
    "B": 0,
    "C": 0,
    "unknown": 1,
}  # Day17 Phase 0b 実測 (README.md 参照)


def test_baseline_three_class_classification_distribution():
    """baseline_three_class_classification.json の A/B/C/unknown 分布が
    Day17 Phase 0b 実測値と一致することを確認.

    Day15 で実装した三分類 audit logic (crossref_check + nlm_catalog_check)
    が Cell-style 入力に対しても正しく動作する baseline を document-of-record
    として凍結する.

    Day17 baseline では A=14 と多発 (Day16 は SSL 問題で unknown 大半に
    倒れた事象と対照的). AI 工学領域 (PMC12915276) の book/web/proceedings
    refs が Crossref で 404 を返した結果と推定. 将来 false positive 抑制
    改修が入れば baseline 更新を要する.
    """
    classifications = json.loads(BASELINE_THREE_CLASS.read_text(encoding="utf-8"))
    actual = {"A": 0, "B": 0, "C": 0, "unknown": 0}
    for c in classifications:
        cls = c.get("class", "unknown")
        if cls not in actual:
            actual[cls] = 0
        actual[cls] += 1
    assert actual == EXPECTED_THREE_CLASS_DISTRIBUTION, (
        f"Day15 三分類 audit regression on Cell fixture: "
        f"got {actual}, expected {EXPECTED_THREE_CLASS_DISTRIBUTION}"
    )
