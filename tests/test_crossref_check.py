"""
Unit tests for crossref_check module (Day15 SPEC §3.3, §6.1).

API key 不要 (fixture 経由のみ使用、live API call なし).
fixture 配置: tests/fixtures/three_class_classification/expected_crossref_*.json
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

FIXTURES = (
    Path(__file__).parent / "fixtures" / "three_class_classification"
)


def test_check_doi_exists_returns_True_for_real_doi():
    """実在 DOI (Crossref hit) → exists=True, metadata 取得.

    Day13 INVESTIGATION で Davey 2003 (DOI 10.1037/1091-7527.21.3.245)
    が Crossref で hit することを確認済. 本 test は fixture 経由で
    その挙動を deterministic に検証.
    """
    import crossref_check  # noqa: E402

    fixture = FIXTURES / "expected_crossref_10_1037-1091-7527.json"
    result = crossref_check.check_doi_exists(
        "10.1037/1091-7527.21.3.245",
        fixture_path=fixture,
    )

    assert result["exists"] is True, (
        f"Expected exists=True for hit fixture, got {result.get('exists')}"
    )
    assert result["error"] is None, (
        f"Expected no error for hit fixture, got {result.get('error')!r}"
    )
    # metadata は dict で、journal/title 等の Crossref response field を含む
    assert isinstance(result["metadata"], dict)
    # Crossref response の "container-title" に journal 名が入る
    container = result["metadata"].get("container-title")
    assert container and "Families, Systems" in container[0], (
        f"Expected journal 'Families, Systems, & Health' in metadata, "
        f"got container-title={container!r}"
    )


def test_check_doi_exists_returns_False_for_404():
    """Crossref 404 (DOI 実在せず) → exists=False, metadata=None.

    架空 DOI (10.9999/fake-doi-for-test-fabrication-12345) を Crossref に
    投げると 404 が返る. これは A 分類 (真の捏造、LLM ハルシネーション
    候補) の判定根拠.
    """
    import crossref_check  # noqa: E402

    fixture = FIXTURES / "expected_crossref_404.json"
    result = crossref_check.check_doi_exists(
        "10.9999/fake-doi-for-test-fabrication-12345",
        fixture_path=fixture,
    )

    assert result["exists"] is False, (
        f"Expected exists=False for 404 fixture, got {result.get('exists')}"
    )
    assert result["metadata"] is None, (
        f"Expected metadata=None for 404, got {result.get('metadata')!r}"
    )
