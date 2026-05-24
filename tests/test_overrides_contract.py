"""
Contract test for _apply_overrides().

Verifies the override mechanism contract via structural assertions.
Day24: re-pointed from deleted mdpi_149refs to mdpi_173refs; the
byte-level Ref #141 snapshot test was removed (see NOTE below).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Day24: updated from mdpi_149refs (deleted Day23) to mdpi_173refs
FIXTURES = Path(__file__).parent / "fixtures" / "mdpi_173refs"
OVERRIDES_YAML = REPO_ROOT / "integration" / "src" / "manual_overrides.yaml"


def test_load_overrides_yaml_returns_expected_refs():
    """manual_overrides.yaml loader should return dict with 4 ref_nos."""
    from main import _load_overrides_yaml

    overrides = _load_overrides_yaml(OVERRIDES_YAML)
    assert isinstance(overrides, dict)
    assert set(overrides.keys()) == {66, 137, 141, 148}
    for ref_no, entry in overrides.items():
        assert "reason" in entry, f"Ref #{ref_no} missing 'reason'"
        assert "fields" in entry, f"Ref #{ref_no} missing 'fields'"
        assert isinstance(entry["fields"], dict)


def test_load_overrides_yaml_missing_file_raises():
    """Non-existent path should raise FileNotFoundError."""
    from main import _load_overrides_yaml

    with pytest.raises(FileNotFoundError):
        _load_overrides_yaml(Path("/nonexistent/path.yaml"))


def test_apply_overrides_none_passes_through():
    """overrides=None should return input unchanged."""
    from main import _apply_overrides

    sample = [{"ref_no": 1, "title": "Sample"}]
    result = _apply_overrides(sample, None)
    assert result == sample


def test_apply_overrides_empty_passes_through():
    """Empty overrides dict should return input unchanged."""
    from main import _apply_overrides

    sample = [{"ref_no": 1, "title": "Sample"}]
    result = _apply_overrides(sample, {})
    assert result == sample


# NOTE: test_apply_overrides_ref141_matches_expected (previously here) was
# deleted in Day24 because it asserted Ref #141 specific override values from
# the old mdpi_149refs corpus (ref141_parser_snapshot.json), which no longer
# exists. The YAML contract is now verified structurally via
# test_load_overrides_yaml_returns_expected_refs above (which checks the YAML
# has entries for ref_no 66, 137, 141, 148 — unchanged YAML content from old corpus,
# preserved for historical reasons; see Day25+ for potential re-design).


def test_apply_overrides_preserves_non_override_refs():
    """Refs not in overrides should pass through unchanged."""
    from main import _apply_overrides

    sample = [
        {"ref_no": 1, "title": "First"},
        {"ref_no": 141, "title": "Pre-override", "is_book": False},
        {"ref_no": 200, "title": "Last"},
    ]
    overrides = {141: {"fields": {"is_book": True}}}
    result = _apply_overrides(sample, overrides)

    assert result[0] == sample[0]
    assert result[1]["is_book"] is True
    assert result[2] == sample[2]


def test_apply_overrides_unknown_refno_silently_ignored():
    """Override entries for refs not in structured should not raise."""
    from main import _apply_overrides

    sample = [{"ref_no": 1, "title": "Only"}]
    overrides = {999: {"fields": {"title": "Never applied"}}}
    result = _apply_overrides(sample, overrides)
    assert result == sample
