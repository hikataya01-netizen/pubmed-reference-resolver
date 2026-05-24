from pathlib import Path
import pytest
import sys

pytestmark = pytest.mark.skip(
    reason="awaiting Day23 Phase 5 new MDPI fixture "
    "(tracked by docs/superpowers/plans/2026-05-24-day23-fixture-remediation.md). "
    "Original mdpi_149refs/ removed in this commit due to peer-review-derived "
    "confidentiality concern."
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_149refs"


@pytest.fixture(scope="module")
def blocks():
    sys.path.insert(0, str(REPO_ROOT))
    import main
    docx = FIXTURE_DIR / "input_References.docx"
    raw, _ = main.extract_text(docx)
    ln = main.detect_line_numbers(raw)
    cleaned, _ = main.preprocess(raw, ln)
    return main.split_references(cleaned)


class TestDoiBoundaryRecovery:
    """Phase 1 が DOI 終端直後の lowercase-prefixed 著者 Ref を正しく検出するか。"""

    def test_149_refs_detected(self, blocks):
        assert len(blocks) == 149

    def test_no_missing_refs(self, blocks):
        ref_nos = sorted(b.ref_no for b in blocks)
        missing = [n for n in range(1, 150) if n not in ref_nos]
        assert missing == []

    def test_ref40_is_van_der_biessen(self, blocks):
        b = next((b for b in blocks if b.ref_no == 40), None)
        assert b is not None
        assert b.raw_text.startswith("van der Biessen")

    def test_ref140_is_van_zyl(self, blocks):
        b = next((b for b in blocks if b.ref_no == 140), None)
        assert b is not None
        assert b.raw_text.startswith("van Zyl")

    def test_ref39_does_not_contain_ref40(self, blocks):
        """Ref #39 が #40 を吸収して肥大化していないこと。"""
        b = next((b for b in blocks if b.ref_no == 39), None)
        assert b is not None
        assert "van der Biessen" not in b.raw_text
        assert b.char_length < 400  # 平均的な MDPI ref サイズ以内

    def test_ref139_does_not_contain_ref140(self, blocks):
        b = next((b for b in blocks if b.ref_no == 139), None)
        assert b is not None
        assert "van Zyl" not in b.raw_text
