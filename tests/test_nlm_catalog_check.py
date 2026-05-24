"""
Unit tests for nlm_catalog_check module (Day15 SPEC §3.3, §6.1).

API key 不要 (fixture 経由のみ使用、live API call なし).
fixture 配置: tests/fixtures/three_class_classification/expected_nlm_*.json
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


def test_get_journal_indexing_status_returns_Y_for_indexed_journal():
    """MEDLINE 収録誌 (currentindexingstatus=Y) → status='Y'.

    Day13 で確認: Families, Systems, & Health (ISSN 1091-7527) =
    NLM ID 9610836, currentindexingstatus='Y' (Fam Syst Health).
    本 test は C 分類 (収録誌の indexing 漏れ論文、#17 Davey) の
    判定根拠.
    """
    import nlm_catalog_check  # noqa: E402

    result = nlm_catalog_check.get_journal_indexing_status(
        issn="1091-7527",
        fixture_search_path=FIXTURES / "expected_nlm_search_1091-7527.json",
        fixture_summary_path=FIXTURES / "expected_nlm_summary_9610836.json",
    )

    assert result["status"] == "Y", (
        f"Expected status='Y' for Fam Syst Health (ISSN 1091-7527), "
        f"got {result.get('status')!r}"
    )
    assert result["nlm_id"] == "9610836", (
        f"Expected nlm_id='9610836', got {result.get('nlm_id')!r}"
    )
    assert result["medlineta"] == "Fam Syst Health", (
        f"Expected medlineta='Fam Syst Health', got {result.get('medlineta')!r}"
    )
    assert result["error"] is None


def test_get_journal_indexing_status_returns_N_for_unindexed_journal():
    """MEDLINE 非収録誌 (currentindexingstatus=N) → status='N'.

    Day13 で確認: Clinics in Mother and Child Health = NLM ID 101300689,
    currentindexingstatus='N' (Clin Mother Child Health, OMICS Publishing
    Group, predatory). 本 test は B 分類 (MEDLINE 非収録誌の正規論文、
    #22 Gallina) の判定根拠.
    """
    import nlm_catalog_check  # noqa: E402

    result = nlm_catalog_check.get_journal_indexing_status(
        journal_name="Clinics in Mother and Child Health",
        fixture_search_path=FIXTURES / "expected_nlm_search_clin_mother.json",
        fixture_summary_path=FIXTURES / "expected_nlm_summary_101300689.json",
    )

    assert result["status"] == "N", (
        f"Expected status='N' for Clin Mother Child Health (OMICS, predatory), "
        f"got {result.get('status')!r}"
    )
    assert result["nlm_id"] == "101300689", (
        f"Expected nlm_id='101300689', got {result.get('nlm_id')!r}"
    )
    assert result["medlineta"] == "Clin Mother Child Health", (
        f"Expected medlineta='Clin Mother Child Health', got {result.get('medlineta')!r}"
    )
    assert result["error"] is None


def test_fetch_json_uses_certifi_ssl_context(monkeypatch):
    """_fetch_json は certifi 由来の SSL context を urlopen に渡すこと.

    Day22 Rule 3 NLM SSL fix の regression guard. certifi.where() の
    cafile を持つ ssl.SSLContext が urlopen の context kwarg に渡る
    ことを mock で検証.
    """
    import io
    import ssl

    import nlm_catalog_check  # noqa: E402

    captured: dict = {}

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(url, timeout=None, context=None):
        captured["url"] = url
        captured["timeout"] = timeout
        captured["context"] = context
        return FakeResp(b'{"esearchresult": {"idlist": ["12345"]}}')

    monkeypatch.setattr(
        nlm_catalog_check.urllib.request, "urlopen", fake_urlopen
    )

    result = nlm_catalog_check._fetch_json(
        "https://eutils.ncbi.nlm.nih.gov/test", label="test"
    )

    assert result == {"esearchresult": {"idlist": ["12345"]}}
    assert isinstance(captured["context"], ssl.SSLContext), (
        f"Expected SSLContext, got {type(captured['context']).__name__}"
    )
    assert captured["context"] is nlm_catalog_check._SSL_CONTEXT, (
        "Expected the module-level _SSL_CONTEXT singleton (certifi-based)"
    )
    assert captured["timeout"] == nlm_catalog_check.TIMEOUT_SECONDS
