"""
Integration test for the APA 45-ref Day16 baseline.

Background:
    Day9 (commit ab25630) introduced the Vancouver Veto in is_mdpi_style()
    so that references with `(YYYY)` paren year are routed to the LLM path
    instead of the MDPI fast-path. Day11 added Vancouver 24-ref fixture
    as the first golden for this regression. Day16 adds APA 45-ref fixture
    as the second golden, extending the regression coverage to APA 7 style.

    PMC OA 3 papers (Death Studies / Health Communication / Frontiers
    in Psychology) provide 15 refs each, all in APA 7 with `(YYYY)`
    paren year.

Fixture file naming convention (Day11 hybrid):
    expected_*  : deterministic output (byte/structural match required)
    baseline_*  : variability-bearing output (LLM/PubMed-dependent)

API key requirement: NONE.
    Tests 1-3, 6-7 use parser-only paths (no LLM).
    Tests 4-5, 8 read baseline files directly without re-running Phase 2-4.

Refs: docs/sessions/day16/SPEC_apa_45refs_fixture.md (commit 4f1181d);
      docs/sessions/day16/PLAN_apa_45refs_fixture.md (commit 0f0ed39);
      tests/fixtures/apa_45refs/README.md.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

FIXTURES = Path(__file__).parent / "fixtures" / "apa_45refs"
INPUT_DOCX = FIXTURES / "input_References.docx"
EXPECTED_PHASE1 = FIXTURES / "expected_phase1_intermediate.json"
BASELINE_PHASE3 = FIXTURES / "baseline_phase3_resolved.json"
BASELINE_REPORT = FIXTURES / "baseline_report.md"
BASELINE_THREE_CLASS = FIXTURES / "baseline_three_class_classification.json"


# Day16 Phase 0b 実測値 (document-of-record baseline 凍結).
# LLM/PubMed/Crossref/NLM の揺らぎで本値が変動する場合は、
# Phase 2-4 を再実行し baseline_*.json/md を再生成した上で、
# 本定数も更新する運用とする (Day11 Vancouver と同じ思想).
EXPECTED_RESOLVED_COUNT = 25
EXPECTED_REPORT_CRITICAL_COUNT = 0


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
# Test 1: Vancouver Veto routing for APA (deterministic)
# -----------------------------------------------------------------------------


def test_apa_45refs_routes_all_to_llm_path():
    """Day9 Vancouver Veto (APA 拡張版): 45 件すべてが is_mdpi_style() で
    False を返し、LLM path に routing されることを確認.

    APA 7 の `(YYYY)` paren year により MDPI fast-path から除外されるべき.
    deterministic test (parser-only, no LLM/PubMed call).
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
