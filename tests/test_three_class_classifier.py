"""
Integration tests for three_class_classifier module (Day15 SPEC §3.3, §6.1).

依存性注入 (DI) パターンで crossref_fn/nlm_fn を渡し、fixture-based test
を実現. API key 不要、live API call なし.

Test 5 件 (Day15 SPEC §6.1 #1-5):
1. A 分類 (DOI 欠落)
2. A 分類 (Crossref 404)
3. B 分類 (#22 Gallina, NLM status=N)
4. C 分類 (#17 Davey, NLM status=Y)
5. unknown (network error, fail-soft)
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


# -----------------------------------------------------------------------------
# Fixture-based fake functions for crossref_fn / nlm_fn (DI)
# -----------------------------------------------------------------------------


def _fake_crossref_factory(doi_to_fixture: dict[str, Path]):
    """DOI → fixture path の dict を closure で bind し、
    crossref_check.check_doi_exists 互換の関数を返す."""
    import crossref_check  # noqa: E402

    def fake(doi: str) -> dict:
        fp = doi_to_fixture.get(doi)
        if fp is None:
            return {"exists": None, "metadata": None,
                    "error": f"no fixture for DOI {doi!r}"}
        return crossref_check.check_doi_exists(doi, fixture_path=fp)

    return fake


def _fake_nlm_factory(
    issn_to_fixtures: dict[str, tuple[Path, Path]],
    journal_to_fixtures: dict[str, tuple[Path, Path]],
):
    """ISSN/journal → (search, summary) fixture path tuple を bind し、
    nlm_catalog_check.get_journal_indexing_status 互換の関数を返す."""
    import nlm_catalog_check  # noqa: E402

    def fake(journal_name=None, issn=None) -> dict:
        if issn and issn in issn_to_fixtures:
            search_p, summary_p = issn_to_fixtures[issn]
            return nlm_catalog_check.get_journal_indexing_status(
                issn=issn,
                fixture_search_path=search_p,
                fixture_summary_path=summary_p,
            )
        if journal_name and journal_name in journal_to_fixtures:
            search_p, summary_p = journal_to_fixtures[journal_name]
            return nlm_catalog_check.get_journal_indexing_status(
                journal_name=journal_name,
                fixture_search_path=search_p,
                fixture_summary_path=summary_p,
            )
        return {"status": None, "nlm_id": None, "medlineta": None,
                "error": "no fixture for query"}

    return fake


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------


def test_classify_returns_A_when_doi_missing():
    """DOI 欠落 ref → A 分類 (LLM ハルシネーション候補)."""
    import three_class_classifier  # noqa: E402

    unresolved = [
        {"ref_no": 99, "doi": None, "journal": "Some Journal"},
    ]
    result = three_class_classifier.classify_unresolved_refs(
        unresolved,
        crossref_fn=_fake_crossref_factory({}),
        nlm_fn=_fake_nlm_factory({}, {}),
    )
    assert len(result) == 1
    assert result[0]["class"] == "A", (
        f"DOI 欠落 → A 期待、got class={result[0].get('class')!r}"
    )
    assert result[0]["ref_no"] == 99


def test_classify_returns_A_when_crossref_404():
    """Crossref 404 (DOI 実在せず) → A 分類."""
    import three_class_classifier  # noqa: E402

    fake_doi = "10.9999/fake-doi-for-test-fabrication-12345"
    unresolved = [
        {"ref_no": 100, "doi": fake_doi, "journal": "Fake Journal"},
    ]
    result = three_class_classifier.classify_unresolved_refs(
        unresolved,
        crossref_fn=_fake_crossref_factory({
            fake_doi: FIXTURES / "expected_crossref_404.json",
        }),
        nlm_fn=_fake_nlm_factory({}, {}),
    )
    assert result[0]["class"] == "A", (
        f"Crossref 404 → A 期待、got class={result[0].get('class')!r}"
    )
    assert result[0]["doi_resolved"] is False


def test_classify_returns_B_when_nlm_status_N():
    """Day9 (Z) #22 Gallina (OMICS Predatory) → B 分類."""
    import three_class_classifier  # noqa: E402

    gallina_doi = "10.4172/2090-7214.1000217"
    unresolved = [
        {"ref_no": 22, "doi": gallina_doi,
         "journal": "Clinics in Mother and Child Health"},
    ]
    result = three_class_classifier.classify_unresolved_refs(
        unresolved,
        crossref_fn=_fake_crossref_factory({
            gallina_doi: FIXTURES / "expected_crossref_10_4172-2090-7214.json",
        }),
        nlm_fn=_fake_nlm_factory(
            issn_to_fixtures={
                # Crossref response の ISSN (Print + Online) で dispatch
                "1812-5840": (
                    FIXTURES / "expected_nlm_search_clin_mother.json",
                    FIXTURES / "expected_nlm_summary_101300689.json",
                ),
                "2090-7214": (
                    FIXTURES / "expected_nlm_search_clin_mother.json",
                    FIXTURES / "expected_nlm_summary_101300689.json",
                ),
            },
            journal_to_fixtures={
                "Clinics in Mother and Child Health": (
                    FIXTURES / "expected_nlm_search_clin_mother.json",
                    FIXTURES / "expected_nlm_summary_101300689.json",
                ),
            },
        ),
    )
    assert result[0]["class"] == "B", (
        f"#22 Gallina (NLM status=N) → B 期待、got class={result[0].get('class')!r}, "
        f"reason={result[0].get('reason')!r}"
    )
    assert result[0]["doi_resolved"] is True
    assert result[0]["journal_indexing"] == "N"


def test_classify_returns_C_when_nlm_status_Y():
    """Day9 (Z) #17 Davey (Fam Syst Health, MEDLINE 収録誌の indexing 漏れ) → C 分類."""
    import three_class_classifier  # noqa: E402

    davey_doi = "10.1037/1091-7527.21.3.245"
    unresolved = [
        {"ref_no": 17, "doi": davey_doi,
         "journal": "Families, Systems, & Health"},
    ]
    result = three_class_classifier.classify_unresolved_refs(
        unresolved,
        crossref_fn=_fake_crossref_factory({
            davey_doi: FIXTURES / "expected_crossref_10_1037-1091-7527.json",
        }),
        nlm_fn=_fake_nlm_factory(
            issn_to_fixtures={
                "1091-7527": (
                    FIXTURES / "expected_nlm_search_1091-7527.json",
                    FIXTURES / "expected_nlm_summary_9610836.json",
                ),
                "1939-0602": (
                    FIXTURES / "expected_nlm_search_1091-7527.json",
                    FIXTURES / "expected_nlm_summary_9610836.json",
                ),
            },
            journal_to_fixtures={},
        ),
    )
    assert result[0]["class"] == "C", (
        f"#17 Davey (NLM status=Y) → C 期待、got class={result[0].get('class')!r}, "
        f"reason={result[0].get('reason')!r}"
    )
    assert result[0]["doi_resolved"] is True
    assert result[0]["journal_indexing"] == "Y"


def test_classify_returns_unknown_on_network_error():
    """Crossref network エラー → unknown 分類 (graceful, fail-soft)."""
    import three_class_classifier  # noqa: E402

    def crossref_network_error(doi):
        return {"exists": None, "metadata": None,
                "error": "network failed (after 1 retry)"}

    unresolved = [
        {"ref_no": 200, "doi": "10.1234/some-real-looking-doi",
         "journal": "Some Journal"},
    ]
    result = three_class_classifier.classify_unresolved_refs(
        unresolved,
        crossref_fn=crossref_network_error,
        nlm_fn=_fake_nlm_factory({}, {}),
    )
    assert result[0]["class"] == "unknown", (
        f"Crossref network error → unknown 期待 (graceful), "
        f"got class={result[0].get('class')!r}"
    )
