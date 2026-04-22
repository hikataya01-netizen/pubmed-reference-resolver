"""
test_post_integration.py — 統合パッチ適用後の期待値テスト

baseline から更新: 149 refs 完全検出を期待する。
"""
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_149refs"


@pytest.fixture(scope="module")
def main_module():
    sys.path.insert(0, str(REPO_ROOT))
    # cached import を避ける
    if "main" in sys.modules:
        del sys.modules["main"]
    import main
    return main


@pytest.fixture(scope="module")
def phase1_blocks(main_module):
    docx = FIXTURE_DIR / "input_References.docx"
    raw, _ = main_module.extract_text(docx)
    ln_report = main_module.detect_line_numbers(raw)
    cleaned, _ = main_module.preprocess(raw, ln_report)
    return main_module.split_references(cleaned)


# 統合後の期待値
EXPECTED_BLOCKS_AFTER_INTEGRATION = 149
EXPECTED_MISSING_REFS_AFTER_INTEGRATION = []


class TestPhase1AfterIntegration:
    def test_all_149_refs_detected(self, phase1_blocks):
        assert len(phase1_blocks) == EXPECTED_BLOCKS_AFTER_INTEGRATION

    def test_no_missing_refs(self, phase1_blocks):
        ref_nos = sorted(b.ref_no for b in phase1_blocks)
        missing = [n for n in range(1, 150) if n not in ref_nos]
        assert missing == EXPECTED_MISSING_REFS_AFTER_INTEGRATION

    def test_ref40_is_van_der_biessen(self, phase1_blocks):
        """Ref #40 が独立して存在し、正しい著者を含むこと。"""
        b = next((b for b in phase1_blocks if b.ref_no == 40), None)
        assert b is not None, "Ref #40 が欠落 (統合が不完全)"
        assert "van der Biessen" in b.raw_text

    def test_ref140_is_van_zyl(self, phase1_blocks):
        b = next((b for b in phase1_blocks if b.ref_no == 140), None)
        assert b is not None, "Ref #140 が欠落"
        assert "van Zyl" in b.raw_text
