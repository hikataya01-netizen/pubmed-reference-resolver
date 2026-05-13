"""
Integration test for the Vancouver/AMA 24-ref Day9 (Z) baseline.

Background:
    Day9 (commit ab25630) introduced the Vancouver Veto in is_mdpi_style()
    so that Vancouver/AMA references (identified by `(YYYY)` paren year)
    are routed to the LLM path instead of the MDPI fast-path. Day9 (Z)
    production verification on the OneDrive 参照.docx (24 refs) achieved:
      - 24/24 LLM-path routing (0 fast-path)
      - 22/24 PubMed resolution (vs 14/24 with old parser)
      - 0 重大 errors (vs 4 with old parser)

    This test file freezes that Day9 (Z) baseline so future regressions
    in either:
      (a) is_mdpi_style() routing logic (test 1, deterministic)
      (b) Phase 1 parser extraction (test 2-3, deterministic)
      (c) PubMed resolution rate (test 4, baseline-as-document, captures
          variability)
      (d) audit dashboard quality (test 5, baseline-as-document)
    can be detected.

Fixture file naming convention:
    expected_*  : deterministic output (byte/structural match required)
    baseline_*  : variability-bearing output (LLM/PubMed-dependent;
                  stored as a baseline-of-record, not a strict golden)

API key requirement: NONE.
    Tests 1-3 use parser-only paths (no LLM).
    Tests 4-5 read the baseline files directly without re-running
    Phase 2/3/4 (which would require ANTHROPIC + NCBI keys and produce
    variable output anyway).

Refs: docs/sessions/day9/SPEC_mdpi_fast_path_strict.md;
      docs/sessions/day9/DAY9_LESSONS_LEARNED.md §4;
      Day11 (本 file) Day7 §9.3 long-term task 1 件目.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

FIXTURES = Path(__file__).parent / "fixtures" / "vancouver_24refs"
INPUT_DOCX = FIXTURES / "input_References.docx"
EXPECTED_PHASE1 = FIXTURES / "expected_phase1_intermediate.json"
BASELINE_PHASE3 = FIXTURES / "baseline_phase3_resolved.json"
BASELINE_REPORT = FIXTURES / "baseline_report.md"


# -----------------------------------------------------------------------------
# Helper (pattern borrowed from test_integration_149refs.py)
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
# Test 1: Vancouver Veto routing (deterministic)
# -----------------------------------------------------------------------------


def test_vancouver_24refs_routes_all_to_llm_path():
    """Day9 Vancouver Veto: 24 件すべてが is_mdpi_style() で False を返し、
    LLM path に routing されることを確認 (regression guard for Day9 ab25630).

    deterministic test (parser-only, no LLM/PubMed call).
    """
    import mdpi_parser  # noqa: E402

    blocks, _ = _load_phase1_blocks_with_ln_report()
    assert len(blocks) == 24, f"Expected 24 blocks, got {len(blocks)}"

    fast_path_blocks = []
    for b in blocks:
        if mdpi_parser.is_mdpi_style(b.raw_text):
            fast_path_blocks.append(b.ref_no)

    assert fast_path_blocks == [], (
        f"Day9 Vancouver Veto regression: {len(fast_path_blocks)} block(s) "
        f"routed to MDPI fast-path (should be 0). "
        f"Affected ref_no: {fast_path_blocks[:5]}"
    )


# -----------------------------------------------------------------------------
# Test 2: Phase 1 reference_blocks deterministic (byte-equivalent at the
#         stage3_reference_blocks level)
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
# Test 3: Reference count = 24
# -----------------------------------------------------------------------------


def test_phase1_extracts_24_reference_blocks():
    """Phase 1 が OneDrive 参照.docx から 24 件の reference を抽出.

    deterministic, helps catch parser regressions that change the count.
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()
    assert len(blocks) == 24, f"Expected 24 blocks, got {len(blocks)}"


# -----------------------------------------------------------------------------
# Test 4: Baseline PubMed resolution count (variability-aware)
# -----------------------------------------------------------------------------


def test_baseline_phase3_documents_resolution_count():
    """baseline_phase3_resolved.json (Day9 (Z) 22:30:15 実測) に
    解決件数 22/24 が記録されていることを確認.

    本 test は LLM/PubMed を再実行せず baseline file の中身を
    document-of-record として assert する.

    将来の LLM/PubMed 変動で baseline 更新が必要になったら、
    Day9 (Z) 相当の Stage 2 retry を実施し baseline を更新してから
    本 test の expected 値を更新する.
    """
    data = json.loads(BASELINE_PHASE3.read_text(encoding="utf-8"))
    resolutions = data["stage4_pubmed_resolutions"]

    assert len(resolutions) == 24, (
        f"Expected 24 resolution attempts, got {len(resolutions)}"
    )

    resolved_count = sum(1 for r in resolutions if r.get("pmid"))
    assert resolved_count == 22, (
        f"Day9 (Z) baseline regression: "
        f"resolved {resolved_count}/24, expected 22/24. "
        f"If LLM/PubMed drift is the cause, regenerate baseline and update test."
    )


# -----------------------------------------------------------------------------
# Test 5: Baseline report quality (zero 重大 errors)
# -----------------------------------------------------------------------------


def test_baseline_report_documents_zero_major_errors():
    """baseline_report.md (Day9 (Z) 実測) のダッシュボードに
    「査読コメント: 重大 | 0」が記録されていることを確認.

    Day7 では 4 件の重大 errors (うち 3 件 parser 起因 false positive) が
    あったが、Day9 Vancouver Veto により全 false positive 解消 (DAY9 §4.2).
    本 test は baseline-as-document として、その達成を凍結記録する.
    """
    report = BASELINE_REPORT.read_text(encoding="utf-8")

    # ダッシュボード行: "| 査読コメント: 重大 | 0 | ..."
    # 表記揺れに対応するため柔軟な regex
    pattern = re.compile(r"重大\s*\|\s*0\s*\|", re.MULTILINE)
    match = pattern.search(report)

    assert match is not None, (
        f"baseline_report.md ダッシュボードに「重大 | 0 |」が見つからない. "
        f"Day9 Vancouver Veto による false positive 解消 (0 重大) が "
        f"baseline で記録されているはず. report 先頭 500 文字: "
        f"{report[:500]!r}"
    )
