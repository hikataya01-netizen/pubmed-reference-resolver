"""
Integration test for the MDPI 173-ref Day23 baseline.

Background:
    Day9 (commit ab25630) introduced the Vancouver Veto in is_mdpi_style()
    so that references with `(YYYY)` paren year are routed to the LLM path
    instead of the MDPI fast-path. Day23 adds MDPI 173-ref fixture
    (PMC13164670, Nutrients, 171 parsed refs) as a new MDPI-style golden,
    replacing the previously removed fixture that contained protected PMC
    content.

    Nutrients paper (MDPI publisher) provides 171 refs in MDPI/NLM style
    with semicolon-separated authors (`Author P; Author S.`). Unlike the
    original MDPI 149-ref fixture, this fixture uses the "Surname Initial;"
    format rather than "Surname, I.Y.;" — meaning is_mdpi_style() returns
    False for all refs and ALL refs are routed to the LLM path. The
    semicolon author separator and Year,Vol pattern are the defining MDPI
    structural characteristics verified in Tests 6-7.

Fixture file naming convention (Day11 hybrid):
    expected_*  : deterministic output (byte/structural match required)
    baseline_*  : variability-bearing output (LLM/PubMed-dependent)

API key requirement: NONE.
    Tests 1-3, 6-7 use parser-only paths (no LLM).
    Tests 4-5, 8 read baseline files directly without re-running Phase 2-4.

Refs: docs/superpowers/specs/2026-05-24-day23-fixture-remediation-design.md;
      docs/superpowers/plans/2026-05-24-day23-fixture-remediation.md;
      tests/fixtures/mdpi_173refs/README.md.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

FIXTURES = Path(__file__).parent / "fixtures" / "mdpi_173refs"
INPUT_DOCX = FIXTURES / "input_References.docx"
EXPECTED_PHASE1 = FIXTURES / "expected_phase1_intermediate.json"
BASELINE_PHASE3 = FIXTURES / "baseline_phase3_resolved.json"
BASELINE_REPORT = FIXTURES / "baseline_report.md"
BASELINE_THREE_CLASS = FIXTURES / "baseline_three_class_classification.json"


# Day23 Phase 0b 実測値 (document-of-record baseline 凍結).
# LLM/PubMed/Crossref/NLM の揺らぎで本値が変動する場合は、
# Phase 2-4 を再実行し baseline_*.json/md を再生成した上で、
# 本定数も更新する運用とする (Day11 Vancouver と同じ思想).
EXPECTED_RESOLVED_COUNT = 159
EXPECTED_REPORT_CRITICAL_COUNT = 2


# -----------------------------------------------------------------------------
# Helper (pattern borrowed from test_integration_apa_45refs.py)
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
# Test 1: LLM routing for MDPI Nutrients style (deterministic)
# -----------------------------------------------------------------------------


def test_mdpi_173refs_routes_all_to_llm_path():
    """173 件すべてが is_mdpi_style() で False を返し、LLM path に routing
    されることを確認.

    本 fixture の Nutrients 引用は `Author P; Author S.` 形式 (初期名のみ、
    コンマなし) のため、is_mdpi_style() 内部の `_AUTHOR_ITEM_RE` (Surname, I.;
    形式必須) にマッチせず MDPI fast-path から除外される. これは設計通りの
    フォールバック動作であり、全 ref が LLM 経路で処理される.
    deterministic test (parser-only, no LLM/PubMed call).

    Day25 fix(split): count updated 171 → 173 (#55 Åkra, #79 Özcan 復活).
    """
    import mdpi_parser  # noqa: E402

    blocks, _ = _load_phase1_blocks_with_ln_report()
    assert len(blocks) == 173, f"Expected 173 blocks, got {len(blocks)}"

    fast_path_blocks = []
    for b in blocks:
        if mdpi_parser.is_mdpi_style(b.raw_text):
            fast_path_blocks.append(b.ref_no)

    assert fast_path_blocks == [], (
        f"Day23 MDPI routing regression: {len(fast_path_blocks)} block(s) "
        f"unexpectedly routed to MDPI fast-path (should be 0 for this fixture). "
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
# Test 3: Reference count = 171
# -----------------------------------------------------------------------------


def test_phase1_extracts_173_reference_blocks():
    """Phase 1 が MDPI 173-ref fixture から 173 件の reference を抽出.

    deterministic, helps catch parser regressions that change the count.
    Day25 fix(split): regex を [A-Z] → [A-ZÀ-ÖØ-Þ] に拡張することで
    #55 Åkra と #79 Özcan が復活し、count が 171 → 173 に増加.
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()
    assert len(blocks) == 173, f"Expected 173 blocks, got {len(blocks)}"


# -----------------------------------------------------------------------------
# Test 4: Baseline PubMed resolution count (variability-aware)
# -----------------------------------------------------------------------------


def test_baseline_phase3_documents_resolution_count():
    """baseline_phase3_resolved.json (Day23 Phase 0b 実測) に
    解決件数 159/171 (93.0%) が記録されていることを確認.

    本 test は LLM/PubMed を再実行せず baseline file の中身を
    document-of-record として assert する.

    将来の LLM/PubMed 変動で baseline 更新が必要になったら、
    Phase 2-4 を再実行し baseline を更新してから
    本 test の EXPECTED_RESOLVED_COUNT 定数を更新する.
    """
    data = json.loads(BASELINE_PHASE3.read_text(encoding="utf-8"))
    resolutions = data["stage4_pubmed_resolutions"]

    assert len(resolutions) == 171, (
        f"Expected 171 resolution attempts, got {len(resolutions)}"
    )

    resolved_count = sum(1 for r in resolutions if r.get("pmid"))
    assert resolved_count == EXPECTED_RESOLVED_COUNT, (
        f"Day23 MDPI baseline regression: "
        f"resolved {resolved_count}/171, expected {EXPECTED_RESOLVED_COUNT}/171. "
        f"If LLM/PubMed drift is the cause, regenerate baseline and update test."
    )


# -----------------------------------------------------------------------------
# Test 5: Baseline report quality (critical error count)
# -----------------------------------------------------------------------------


def test_baseline_report_documents_audit_summary():
    """baseline_report.md (Day23 Phase 0b 実測) のダッシュボードに
    「査読コメント: 重大 | 2」が記録されていることを確認.

    MDPI 173-ref fixture では 2 件の重大な不整合 (タイトル低一致・ジャーナル名
    とDOI不一致) が検出されており、本 test はその実態を凍結記録する.
    """
    report = BASELINE_REPORT.read_text(encoding="utf-8")

    # ダッシュボード行: "| 査読コメント: 重大 | 2 | ..."
    # 表記揺れに対応するため柔軟な regex でカウントを抽出
    pattern = re.compile(r"重大\s*\|\s*(\d+)\s*\|", re.MULTILINE)
    match = pattern.search(report)

    assert match is not None, (
        f"baseline_report.md ダッシュボードに「重大 | <N> |」が見つからない. "
        f"report 先頭 500 文字: {report[:500]!r}"
    )

    critical_count = int(match.group(1))
    assert critical_count == EXPECTED_REPORT_CRITICAL_COUNT, (
        f"Day23 MDPI baseline regression: "
        f"重大 {critical_count} 件, expected {EXPECTED_REPORT_CRITICAL_COUNT} 件. "
        f"If audit logic drift is the cause, regenerate baseline and update test."
    )


# -----------------------------------------------------------------------------
# Test 6: MDPI semicolon author separator detected in majority of refs
# -----------------------------------------------------------------------------


def test_mdpi_semicolon_author_separator_detected_in_majority_of_refs():
    """171 件中 140 件以上の raw text に `;` 著者区切り記号が含まれることを確認.

    MDPI/NLM スタイル (本 fixture の Nutrients 誌) の核心特徴: 著者を `;` で
    区切るパターンが大多数の ref に存在することを検証.
    (`Author P; Author S.` または `Author AB; Author CD;` 形式).

    140 という閾値は: 単著 ref・書籍 ref・不完全 ref の混入を許容しつつ、
    80% 超が MDPI スタイルのセミコロン区切りであることを保証する.
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()
    refs_with_semicolon = [
        b.ref_no for b in blocks if "; " in b.raw_text
    ]
    assert len(refs_with_semicolon) >= 140, (
        f"MDPI fixture health regression: only {len(refs_with_semicolon)}/171 "
        f"refs contain `;` author separator. Expected >=140. "
        f"Refs with separator: {refs_with_semicolon[:10]}..."
    )


# -----------------------------------------------------------------------------
# Test 7: MDPI Year,Volume pattern detected in majority of refs (structural)
# -----------------------------------------------------------------------------


def test_mdpi_year_comma_volume_pattern_detected_in_majority_of_refs():
    """171 件中 160 件以上が `YYYY,<space>Vol` パターンを含むことを確認.

    MDPI 引用の書誌フォーマット特徴: "Journal 2023, 15, 100-120." のように
    年と巻号がコンマで繋がるパターン (Vancouver の `Year;Vol` とは対照的).
    本 test は fixture が MDPI 誌の書誌スタイルを満たしていることを保証する
    (build ツールの書誌フォーマット品質の test data 健全性保護).

    160 という閾値は: 書籍 ref・不完全 ref・非標準 ref の混入を許容しつつ、
    93% 超が MDPI 標準書誌形式であることを保証するための経験則.
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()
    year_comma_vol_pattern = re.compile(r"\d{4},\s*\d+")
    refs_with_pattern = [
        b.ref_no for b in blocks
        if year_comma_vol_pattern.search(b.raw_text)
    ]
    assert len(refs_with_pattern) >= 160, (
        f"MDPI structural regression: only {len(refs_with_pattern)}/171 "
        f"refs contain `Year,Vol` pattern. Expected >=160. "
        f"Refs with pattern: {refs_with_pattern[:10]}..."
    )


# -----------------------------------------------------------------------------
# Test 8: Three-class classification distribution (document-of-record)
# -----------------------------------------------------------------------------

EXPECTED_THREE_CLASS_DISTRIBUTION = {
    "A": 0,
    "B": 7,
    "C": 3,
    "unknown": 2,
}  # Day23 Phase 0b 実測値 (README.md 参照; unresolved 12 件の三分類分布)


def test_baseline_three_class_classification_distribution():
    """baseline_three_class_classification.json の A/B/C/unknown 分布が
    Day23 Phase 0b 実測値と一致することを確認.

    Day15 で実装した三分類 audit logic (crossref_check + nlm_catalog_check)
    が MDPI 171-ref 入力に対しても正しく動作する baseline を
    document-of-record として凍結する.

    Day23 baseline: B=7 (MEDLINE 収録誌と確認), C=3 (NLM Catalog で確認),
    unknown=2 (Crossref/NLM graceful fail-soft), A=0 (fast-path 起因の
    false positive がゼロ). 高解決率 (93%) により unresolved はわずか 12 件.

    D20-2 教訓 (実 fixture から逆算) に従い、期待値ではなく実測値で固定.
    """
    classifications = json.loads(BASELINE_THREE_CLASS.read_text(encoding="utf-8"))
    actual = {"A": 0, "B": 0, "C": 0, "unknown": 0}
    for c in classifications:
        cls = c.get("class", "unknown")
        if cls not in actual:
            actual[cls] = 0
        actual[cls] += 1
    assert actual == EXPECTED_THREE_CLASS_DISTRIBUTION, (
        f"Day23 三分類 audit regression on MDPI fixture: "
        f"got {actual}, expected {EXPECTED_THREE_CLASS_DISTRIBUTION}"
    )
