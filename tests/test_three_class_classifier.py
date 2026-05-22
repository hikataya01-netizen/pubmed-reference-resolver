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
    """DOI 欠落 + journal も is_book も無い純粋 case → A 分類 (Rule 4 fallback).

    Day20 改修: 旧仕様 (DOI 欠落 = 無条件 A) から、4 rule 順次評価の
    最終 fallback (book/conference/journal 全て失敗時のみ A) に厳格化.
    本 test は Rule 4 fallback が動作することを保証する.
    """
    import three_class_classifier  # noqa: E402

    unresolved = [
        {"ref_no": 99, "doi": None, "journal": None, "is_book": False},
    ]
    result = three_class_classifier.classify_unresolved_refs(
        unresolved,
        crossref_fn=_fake_crossref_factory({}),
        nlm_fn=_fake_nlm_factory({}, {}),
    )
    assert len(result) == 1
    assert result[0]["class"] == "A", (
        f"DOI 欠落 + journal/is_book なし → A 期待 (Rule 4)、"
        f"got class={result[0].get('class')!r}"
    )
    assert result[0]["ref_no"] == 99
    assert (
        "journal 不明" in result[0]["reason"]
        or "ハルシネーション候補" in result[0]["reason"]
    )


def test_classify_returns_B_when_is_book_true():
    """is_book=True ref は DOI 欠落でも B 分類される (book は MEDLINE 対象外、Rule 1).

    Day20 改修: 旧仕様だと A 分類になっていたが、book は本質的に MEDLINE
    indexing 対象外であり「真の捏造」ではない. Day17 cell_45refs #31/#32/#37
    が該当.
    """
    import three_class_classifier  # noqa: E402

    unresolved = [
        {"ref_no": 31, "doi": None, "journal": "", "is_book": True},
    ]

    def fake_crossref(doi):
        raise AssertionError("Crossref should not be called for book")

    def fake_nlm(**kwargs):
        raise AssertionError("NLM should not be called for book")

    result = three_class_classifier.classify_unresolved_refs(
        unresolved,
        crossref_fn=fake_crossref,
        nlm_fn=fake_nlm,
    )
    assert len(result) == 1
    assert result[0]["class"] == "B", (
        f"is_book=True → B 期待 (Rule 1)、got class={result[0].get('class')!r}"
    )
    assert "book" in result[0]["reason"].lower()
    assert result[0]["ref_no"] == 31


def test_classify_returns_B_when_conference_proceedings():
    """journal 名に 'Conference' / 'Proceedings' / 'Workshop' 等を含む ref は B 分類 (Rule 2).

    Day20 改修: conference proceedings は MEDLINE 非収録が標準的.
    Day17 cell_45refs #34/#42/#43 が該当.
    """
    import three_class_classifier  # noqa: E402

    unresolved = [
        {"ref_no": 34, "doi": None,
         "journal": "International Conference on Trends in Electronics",
         "is_book": False},
        {"ref_no": 42, "doi": None,
         "journal": "Proceedings of the IEEE Workshop on ML",
         "is_book": False},
    ]

    def fake_crossref(doi):
        raise AssertionError("Crossref should not be called for conference")

    def fake_nlm(**kwargs):
        raise AssertionError("NLM should not be called for conference")

    result = three_class_classifier.classify_unresolved_refs(
        unresolved,
        crossref_fn=fake_crossref,
        nlm_fn=fake_nlm,
    )
    assert len(result) == 2
    assert all(r["class"] == "B" for r in result), (
        f"conference/proceedings → B 期待 (Rule 2)、"
        f"got classes={[r.get('class') for r in result]!r}"
    )
    reasons_lower = [r["reason"].lower() for r in result]
    assert any("conference" in r or "proceedings" in r for r in reasons_lower)


def test_classify_calls_nlm_when_doi_missing_with_journal():
    """DOI 欠落 + journal 名あり + 非 book + 非 conference → NLM 直接検索 (Rule 3).

    Day20 改修: 旧仕様だと A 分類になっていたが、journal 名が判明していれば
    NLM Catalog を直接検索して B/C 判定可能. Day17 cell_45refs
    #33/#36/#38/#40/#41/#44/#45 が該当.
    """
    import three_class_classifier  # noqa: E402

    unresolved = [
        {"ref_no": 33, "doi": None, "journal": "Eng", "is_book": False},
        {"ref_no": 38, "doi": None, "journal": "Journal of Engineered Fibers",
         "is_book": False},
    ]

    nlm_calls = []

    def fake_crossref(doi):
        raise AssertionError("Crossref should not be called when DOI is missing")

    def fake_nlm(**kwargs):
        nlm_calls.append(kwargs)
        if "Engineered" in (kwargs.get("journal_name") or ""):
            return {"status": "Y", "nlm_id": "12345", "medlineta": "JEF"}
        return {"status": "N", "nlm_id": None, "medlineta": None}

    result = three_class_classifier.classify_unresolved_refs(
        unresolved,
        crossref_fn=fake_crossref,
        nlm_fn=fake_nlm,
    )
    assert len(nlm_calls) == 2, (
        f"NLM should be called for each ref, got {len(nlm_calls)} calls"
    )
    assert result[0]["class"] == "B", (
        f"'Eng' (status=N) → B 期待、got {result[0]['class']!r}"
    )
    assert result[1]["class"] == "C", (
        f"'Engineered Fibers' (status=Y) → C 期待、got {result[1]['class']!r}"
    )


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
