"""
Integration test for structure_all_references() with MDPI fast-path enabled.

This test verifies that after Step 3 (MDPI fast-path wiring into
structure_all_references), calling the public API on the 149-ref MDPI corpus
produces the same structured output as calling mdpi_parser directly (as
verified in test_mdpi_parser.py).

Since fast-path should route all MDPI-style blocks to mdpi_parser without
LLM calls, the result must be deterministic and match the golden fixture
without requiring an ANTHROPIC_API_KEY.

Helper rationale:
    Phase 1 is re-executed from input_References.docx rather than loaded
    from a JSON fixture. This avoids fixture double-maintenance: Phase 1's
    behavior is already guaranteed by test_split_references_doi_boundary.py,
    and ReferenceBlock dataclass evolution does not require fixture updates.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

FIXTURES = Path(__file__).parent / "fixtures" / "mdpi_149refs"
INPUT_DOCX = FIXTURES / "input_References.docx"


def _load_phase1_blocks_with_ln_report():
    """Phase 1 を再実行し (blocks, ln_report) のタプルを返す。

    Note:
        Returns ReferenceBlock instances (not dicts), matching the signature
        expected by structure_all_references(blocks, ln_report, ...).
    """
    from main import extract_text, preprocess, split_references, detect_line_numbers

    raw, _kind = extract_text(INPUT_DOCX)
    ln_report = detect_line_numbers(raw)
    cleaned, _trace = preprocess(raw, ln_report)
    blocks = split_references(cleaned)
    return blocks, ln_report


def test_structure_all_references_with_fast_path_matches_golden():
    """fast-path enabled: 149 MDPI refs are processed without LLM and match golden."""
    import main as main_mod

    blocks, ln_report = _load_phase1_blocks_with_ln_report()
    assert len(blocks) == 149, f"Phase 1 should produce 149 blocks, got {len(blocks)}"

    # structure_all_references() を fast-path 有効で呼ぶ
    # ANTHROPIC_API_KEY 不要（全 149 件が MDPI 形式で fast-path に routing される想定）
    result = main_mod.structure_all_references(
        blocks,
        ln_report,
        api_key=None,
        verbose=False,
        enable_mdpi_fast_path=True,
    )

    # ゴールドと比較
    expected = json.loads(
        (FIXTURES / "expected_phase2_structured.json").read_text(encoding="utf-8")
    )
    expected_structured = expected.get("stage3_structured", expected)

    assert len(result) == len(expected_structured), (
        f"Result count mismatch: got {len(result)}, expected {len(expected_structured)}"
    )

    # ref_no でソートして比較
    result_sorted = sorted(result, key=lambda x: x["ref_no"])
    expected_sorted = sorted(expected_structured, key=lambda x: x["ref_no"])

    for r, exp in zip(result_sorted, expected_sorted):
        assert r["ref_no"] == exp["ref_no"]
        # 主要フィールドの検証（詳細は test_mdpi_parser.py で既に検証済み）
        for field in ("authors", "title", "journal", "year", "is_book"):
            assert r.get(field) == exp.get(field), (
                f"Ref #{r['ref_no']} field={field}: "
                f"got={r.get(field)!r} expected={exp.get(field)!r}"
            )


def test_structure_all_references_routes_all_149_refs_to_fast_path():
    """全 149 件が MDPI 形式と判定され fast-path に routing されることを検証。

    これが PASS することで、ANTHROPIC_API_KEY 未設定でも 149 件全件処理可能な
    ことが保証される (LLM path が 1 件も呼ばれていない)。
    """
    import mdpi_parser

    blocks, _ = _load_phase1_blocks_with_ln_report()
    assert len(blocks) == 149

    mdpi_count = sum(1 for b in blocks if mdpi_parser.is_mdpi_style(b.raw_text))
    non_mdpi_count = len(blocks) - mdpi_count

    # 149 件全てが MDPI 形式と判定されることを期待
    # (本ゴールドデータは MDPI 出版社の論文の References.docx なので)
    assert mdpi_count == 149, (
        f"Expected all 149 blocks to be MDPI-style, got mdpi={mdpi_count}, "
        f"non_mdpi={non_mdpi_count}"
    )


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set; LLM fallback path requires API access",
)
def test_structure_all_references_with_fast_path_disabled_uses_llm():
    """fast-path disabled: 全件 LLM path を経由する (API キー必要)。

    本テストは API キーがある環境でのみ実行。API コストが発生するため、
    サンプル数を絞って検証 (最初の 3 件のみ)。
    """
    import main as main_mod

    blocks, ln_report = _load_phase1_blocks_with_ln_report()
    sample_blocks = blocks[:3]

    result = main_mod.structure_all_references(
        sample_blocks,
        ln_report,
        verbose=False,
        enable_mdpi_fast_path=False,  # fast-path 無効 → 全件 LLM
    )

    assert len(result) == 3
    for r in result:
        assert "ref_no" in r
        # LLM path を通ったことを間接的に検証 (具体的内容は LLM 応答依存)
