"""
test_pre_integration_baseline.py — Day8 pre-integration baseline characterization
(Day24 historical archive 化版)

旧目的:
    Day8 (commit ab25630) 当時、統合パッチ適用の前に main.py の挙動を
    pytest assertion として固定し、整合前後の差分を可視化する設計だった.
    `tests/fixtures/mdpi_149refs/` の 149-ref corpus に対する Phase 1 出力を
    byte-level snapshot として保存し、Bray globocan #1 / De Boeck #149 /
    line numbers 567-910 等の corpus-specific 値を assert していた.

Day24 historical archive 化の経緯:
    Day23 (commit 3c676ec) で旧 mdpi_149refs corpus 削除 + 新 mdpi_173refs
    (PMC13164670, 173 refs, LLM path 経由) に置換. 新 corpus には Bray
    globocan も De Boeck もなく、Phase 1 出力も大きく異なる. 「integration
    前後の差分を可視化」という本 file の本来意義は完全喪失.

    Day24 では historical archive として残置し、新 fixture (mdpi_173refs) の
    主要 baseline file が読み込めることのみを sanity check として確認する形式に
    弱体化. TestPhase1DetailedSnapshot は削除 (corpus 完全置換のため意味なし).

参照:
    spec: docs/superpowers/specs/2026-05-24-day24-mdpi-test-restoration-design.md
    Day8 origin: docs/sessions/day8/ (パッチ適用前 baseline 設計)
    Day23 corpus 置換: docs/sessions/day23/ + DAY23_LESSONS_LEARNED.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_173refs"


class TestNewFixtureIntegrity:
    """tests/fixtures/mdpi_173refs/ の主要 file が存在し読み込めることを sanity check."""

    def test_input_docx_exists(self):
        """input docx (Phase 1 入力) が存在し、サイズが妥当."""
        docx = FIXTURE_DIR / "input_References.docx"
        assert docx.exists(), f"input_References.docx not found: {docx}"
        assert docx.stat().st_size > 30_000, (
            f"input docx size unexpectedly small: {docx.stat().st_size} bytes "
            f"(expected > 30 KB for 171-ref corpus)"
        )

    def test_expected_phase1_intermediate_exists(self):
        """expected_phase1_intermediate.json (deterministic golden) が読み込める."""
        import json
        path = FIXTURE_DIR / "expected_phase1_intermediate.json"
        assert path.exists(), f"expected_phase1_intermediate.json not found: {path}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, (dict, list)), "phase1 JSON should be dict or list"

    def test_baseline_phase3_resolved_exists(self):
        """baseline_phase3_resolved.json (LLM 経由、variability あり) が読み込める."""
        import json
        path = FIXTURE_DIR / "baseline_phase3_resolved.json"
        assert path.exists(), f"baseline_phase3_resolved.json not found: {path}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data, (dict, list)), "phase3 JSON should be dict or list"

    def test_baseline_report_exists(self):
        """baseline_report.md (Phase 4 出力 narrative) が存在."""
        path = FIXTURE_DIR / "baseline_report.md"
        assert path.exists(), f"baseline_report.md not found: {path}"
        content = path.read_text(encoding="utf-8")
        assert len(content) > 1000, "baseline_report.md size unexpectedly small"
