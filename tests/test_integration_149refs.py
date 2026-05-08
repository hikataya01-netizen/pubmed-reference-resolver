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

import difflib
import json
import os
import re
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


def test_structure_all_references_with_overrides_applied():
    """fast-path + overrides: 4 flagged refs are corrected per manual_overrides.yaml."""
    import main as main_mod

    OVERRIDES_YAML = (
        Path(__file__).parent.parent / "integration" / "src" / "manual_overrides.yaml"
    )

    blocks, ln_report = _load_phase1_blocks_with_ln_report()
    overrides = main_mod._load_overrides_yaml(OVERRIDES_YAML)

    result = main_mod.structure_all_references(
        blocks,
        ln_report,
        api_key=None,
        verbose=False,
        enable_mdpi_fast_path=True,
        overrides=overrides,
    )

    result_by_refno = {r["ref_no"]: r for r in result}

    # Ref #66: journal corrected
    assert result_by_refno[66]["journal"] == "Psicooncología"
    assert "override applied" in (result_by_refno[66].get("notes") or "")

    # Ref #137: journal corrected (city retained)
    assert result_by_refno[137]["journal"] == "Basic Book: New York"

    # Ref #141: is_book True, year 2004 (book classification recovered)
    assert result_by_refno[141]["is_book"] is True
    assert result_by_refno[141]["year"] == 2004

    # Ref #148: title/journal boundary corrected
    assert "Perspect" not in result_by_refno[148]["title"]
    assert result_by_refno[148]["journal"] == "Perspect. Psychol. Sci."

    # Non-override refs are not affected
    assert "override applied" not in (result_by_refno[1].get("notes") or "")


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


# ============================================================================
# Step 6: synthesize_outputs (Phase 4+5) integration
# ============================================================================

_TIMESTAMP_RE = re.compile(
    r"\*\*実行\*\*: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
)
_INPUT_FILE_RE = re.compile(
    r"\*\*入力\*\*: `[^`]+`"
)


def _scrub_volatile_lines(s: str) -> str:
    """report.md の environment-dependent 行を固定文字列に置換し、
    byte 比較可能にする.

    対象 (Day8 (W) 拡張):
    - **実行**: YYYY-MM-DD HH:MM:SS  →  **実行**: <TS>
    - **入力**: `<path>`             →  **入力**: `<INPUT>`

    Day7 PHASE_0_VERIFICATION_REPORT §9.1 で指摘された 2 つの
    volatile field を一括して masking する. cwd や入力ファイル選択に
    依存しない byte 比較が可能になる.
    """
    s = _TIMESTAMP_RE.sub("**実行**: <TS>", s)
    s = _INPUT_FILE_RE.sub("**入力**: `<INPUT>`", s)
    return s


# -----------------------------------------------------------------------------
# Day8 (W): unit tests for _scrub_volatile_lines (the expanded scrubber that
# normalizes both **実行** timestamp and **入力** file-path lines).
#
# Rationale: Day7 PHASE_0_VERIFICATION_REPORT §9.1 flagged that the existing
# _scrub_timestamp masks only the timestamp; the input_file path is also
# baked into report.md (line: `**入力**: \`tests/fixtures/...docx\`  |  **実行**: ...`)
# and is sensitive to cwd / input choice. Future re-runs from a different
# directory would falsely fail the byte-identity test even though the
# substantive output is identical.
#
# Solution: rename _scrub_timestamp to _scrub_volatile_lines and add
# input_file path masking.
# -----------------------------------------------------------------------------


def test__scrub_volatile_lines_normalizes_timestamp():
    """timestamp 行は固定 <TS> に置換される (既存挙動の保護)."""
    a = "**実行**: 2026-05-07 18:00:00"
    b = "**実行**: 2026-12-31 23:59:59"
    assert _scrub_volatile_lines(a) == _scrub_volatile_lines(b) == "**実行**: <TS>"


def test__scrub_volatile_lines_normalizes_input_file_path():
    """入力ファイルパス行は固定 <INPUT> に置換される (Day8 (W) 新挙動)."""
    a = "**入力**: `tests/fixtures/mdpi_149refs/input_References.docx`"
    b = "**入力**: `/abs/path/to/other.docx`"
    assert _scrub_volatile_lines(a) == _scrub_volatile_lines(b) == "**入力**: `<INPUT>`"


def test__scrub_volatile_lines_normalizes_both_in_same_line():
    """report.md の冒頭は両者を同一行に持つ. 両方とも masking される."""
    a = "**入力**: `path/A.docx`  |  **実行**: 2026-05-07 18:00:00"
    b = "**入力**: `path/B.docx`  |  **実行**: 2026-12-31 23:59:59"
    assert _scrub_volatile_lines(a) == _scrub_volatile_lines(b)
    assert "<INPUT>" in _scrub_volatile_lines(a)
    assert "<TS>" in _scrub_volatile_lines(a)
    # 元の path / TS が残らない
    assert "path/A.docx" not in _scrub_volatile_lines(a)
    assert "2026-05-07" not in _scrub_volatile_lines(a)


@pytest.fixture(scope="module")
def synthesize_output(tmp_path_factory):
    """expected_phase3_resolved.json を入力として synthesize_outputs を
    1 度だけ実行し、(output_dir, result) を返す module-scoped fixture。

    下流 3 テスト (report / sidecar / result dict) で共用して合成処理を
    1 回に抑える。
    """
    import main as main_mod

    data = json.loads(
        (FIXTURES / "expected_phase3_resolved.json").read_text(encoding="utf-8")
    )
    output_dir = tmp_path_factory.mktemp("synthesize_outputs_149refs")
    main_mod.synthesize_outputs(data, output_dir)
    return output_dir, data


def test_synthesize_outputs_report_matches_expected(synthesize_output):
    """生成 report.md が expected_report.md と byte 一致する
    (timestamp 行は両者から除去して比較)。"""
    output_dir, _ = synthesize_output

    generated = (output_dir / "report.md").read_text(encoding="utf-8")
    expected = (FIXTURES / "expected_report.md").read_text(encoding="utf-8")

    gen_scrubbed = _scrub_volatile_lines(generated)
    exp_scrubbed = _scrub_volatile_lines(expected)

    if gen_scrubbed != exp_scrubbed:
        diff = list(difflib.unified_diff(
            exp_scrubbed.splitlines(keepends=True),
            gen_scrubbed.splitlines(keepends=True),
            fromfile="expected_report.md",
            tofile="generated report.md",
            n=2,
        ))
        preview = "".join(diff[:20])
        pytest.fail(
            f"report.md does not byte-match expected (timestamp + input_file scrubbed).\n"
            f"First 20 diff lines:\n{preview}"
        )


def test_synthesize_outputs_sidecar_matches_expected(synthesize_output):
    """生成 journal_mismatch_audit.json が expected_journal_audit.json と
    byte 一致する。"""
    output_dir, _ = synthesize_output

    generated = (output_dir / "journal_mismatch_audit.json").read_text(
        encoding="utf-8"
    )
    expected = (FIXTURES / "expected_journal_audit.json").read_text(
        encoding="utf-8"
    )

    if generated != expected:
        diff = list(difflib.unified_diff(
            expected.splitlines(keepends=True),
            generated.splitlines(keepends=True),
            fromfile="expected_journal_audit.json",
            tofile="generated sidecar",
            n=2,
        ))
        preview = "".join(diff[:20])
        pytest.fail(
            f"journal_mismatch_audit.json does not byte-match expected.\n"
            f"First 20 diff lines:\n{preview}"
        )


def test_synthesize_outputs_result_has_stage5_audit(synthesize_output):
    """synthesize_outputs 実行後、入力 data dict に stage5_journal_audit
    が追加され、Ref #13 の MAJOR finding を保持している。"""
    _, data = synthesize_output

    audit = data.get("stage5_journal_audit")
    assert isinstance(audit, list), "stage5_journal_audit must be a list"
    assert len(audit) == 1, f"expected 1 MAJOR finding, got {len(audit)}"

    finding = audit[0]
    assert finding["ref_no"] == 13
    assert finding["severity"] == "MAJOR"
    assert finding["pmid"] == "28591864"
    assert finding["pm_journal"] == "Jpn J Clin Oncol"
