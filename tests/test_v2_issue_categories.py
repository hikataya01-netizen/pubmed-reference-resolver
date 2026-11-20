"""v2 の issue 19 カテゴリの網羅テスト（ネットワーク不要・API キー不要）。

実行: uv run pytest tests/test_v2_issue_categories.py -q

SKILL.md の「整合性チェック 19 カテゴリ」が、合成した入力で実際に発火し、仕様どおりの重要度になることを確かめる。
判定は consistency.check_all（書誌の整合性）と assess.assess_all（文献評価）の 2 箇所にあるため、両方を通す。
解決済みの記録（resolutions）は、PubMed への問い合わせの代わりに、テストの中で組み立てる。

背景: 2026-11-19 時点で、既存のテストが触れていたカテゴリは 19 種のうち 8 種ほどだった
（pmid_mismatch・year_mismatch・expression_of_concern・claim_not_supported など 11 種が未検証）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pytest

from pipeline import assess, consistency, enrich
from pipeline.resolve import similarity

TODAY = 2026

ALL_CATEGORIES = {
    "pmid_mismatch", "first_author_mismatch", "title_major_diff", "journal_mismatch", "doi_mismatch",
    "doi_suspicious_in_pubmed", "year_mismatch", "duplicate_citation", "unresolved", "missing_pmid",
    "missing_doi", "retracted_publication", "expression_of_concern", "erratum_notice", "outdated_citation",
    "non_original_source", "predatory_risk", "claim_not_supported", "claim_partially_supported",
}

# タイトル類似度の帯（resolve.similarity で実測した値。テストの中でも帯を検算する）
TITLE = "Global cancer statistics 2022: GLOBOCAN estimates of incidence and mortality worldwide for 36 cancers in 185 countries"
TITLE_MINOR = TITLE.replace(" worldwide", "")                         # 0.955 (0.90-0.99)
TITLE_MODERATE = TITLE.replace(" for 36 cancers in 185 countries", "")  # 0.842 (0.70-0.90)
TITLE_MAJOR = "Opioid prescribing trends in the United States, 2006-2015"  # 0.197 (<0.70)
TITLE_SAME = TITLE + "."                                              # 1.000


def make_ref(no: int = 1, **kw) -> dict:
    base = {"ref_no": no, "pmid": None, "doi": None, "claimed_first_author": None, "claimed_year": None,
            "claimed_journal": None, "claimed_title": None, "citation_contexts": None, "is_non_pubmed": False}
    base.update(kw)
    return base


def make_res(no: int = 1, pmid: str | None = "1000", status: str = "RESOLVED", path: str = "L1", **meta) -> dict:
    m = {"pmid": pmid, "title": TITLE_SAME, "first_author": "Smith J", "journal": "J Test", "year": "2025",
         "doi": "10.1000/x", "publication_types_list": ["Journal Article"], "comments_corrections": []}
    m.update(meta)
    return {"ref_no": no, "match_status": status, "pmid": pmid if status == "RESOLVED" else None,
            "resolution_path": path if status == "RESOLVED" else "UNRESOLVED",
            "metadata": m if status == "RESOLVED" else None, "attempts": []}


def run(refs, resolutions, journal_info=None, claim_support=None) -> list[dict]:
    issues = consistency.check_all(refs, resolutions)
    extra, _ = assess.assess_all(refs, resolutions, journal_info, claim_support, today_year=TODAY)
    return consistency.sort_issues(issues + extra)


def of(issues: list[dict], category: str) -> list[dict]:
    return [i for i in issues if i["category"] == category]


def one(ref_kw: dict | None = None, meta_kw: dict | None = None, **extras):
    """1 件の参照を作る。extras は journal_info / claim_support / path / pmid / status を渡す。"""
    res = make_res(1, **{k: extras.pop(k) for k in ("pmid", "status", "path") if k in extras}, **(meta_kw or {}))
    return {"refs": [make_ref(1, **(ref_kw or {}))], "resolutions": [res], **extras}


def two_duplicates():
    return {"refs": [make_ref(1, pmid="1000"), make_ref(2, pmid="1000")],
            "resolutions": [make_res(1, "1000"), make_res(2, "1000")]}


def predatory():
    meta = {"journal": "Obscure J", "issn": "1234-5678"}
    key = enrich.journal_key(meta)
    return one(meta_kw=meta, path="L3a", journal_info={key: {"medline_indexed": False, "doaj_listed": False}})


def claim(verdict: str):
    return one(ref_kw={"citation_contexts": ["本文の主張"]}, claim_support={1: {"verdict": verdict, "rationale": "抄録と対応しない"}})


@dataclass
class Case:
    id: str
    category: str
    severity: str
    build: Callable[[], dict]


CASES = [
    # --- consistency.check_all（書誌の整合性）---
    Case("pmid_mismatch", "pmid_mismatch", "MAJOR", lambda: one({"pmid": "111"}, pmid="222")),
    Case("first_author_mismatch", "first_author_mismatch", "MAJOR",
         lambda: one({"claimed_first_author": "Jones A"}, {"first_author": "Smith J"})),
    Case("title_major", "title_major_diff", "MAJOR", lambda: one({"claimed_title": TITLE_MAJOR}, {"title": TITLE})),
    Case("title_moderate", "title_major_diff", "MODERATE", lambda: one({"claimed_title": TITLE_MODERATE}, {"title": TITLE})),
    Case("title_minor", "title_major_diff", "MINOR", lambda: one({"claimed_title": TITLE_MINOR}, {"title": TITLE})),
    Case("journal_major", "journal_mismatch", "MAJOR", lambda: one({"claimed_journal": "Lancet"}, {"journal": "N Engl J Med"})),
    Case("journal_moderate", "journal_mismatch", "MODERATE", lambda: one({"claimed_journal": "Palliat Med"}, {"journal": "Palliative Medicine"})),
    Case("journal_minor", "journal_mismatch", "MINOR",
         lambda: one({"claimed_journal": "Support Care Cancer"}, {"journal": "Supportive Care in Cancer"})),
    Case("doi_mismatch", "doi_mismatch", "MAJOR", lambda: one({"doi": "10.1000/a"}, {"doi": "10.1000/b"})),
    Case("doi_suspicious_in_pubmed", "doi_suspicious_in_pubmed", "MODERATE",
         lambda: one({"doi": "10.1016/0000-0000(00)00000-0"}, {"doi": "10.1016/0000-0000(00)00000-0"})),
    Case("year_major", "year_mismatch", "MAJOR", lambda: one({"claimed_year": 2022}, {"year": "2025"})),
    Case("year_moderate", "year_mismatch", "MODERATE", lambda: one({"claimed_year": 2023}, {"year": "2025"})),
    Case("year_minor", "year_mismatch", "MINOR", lambda: one({"claimed_year": 2024}, {"year": "2025"})),
    Case("duplicate_citation", "duplicate_citation", "MAJOR", two_duplicates),
    Case("unresolved", "unresolved", "MAJOR", lambda: one(status="UNRESOLVED")),
    Case("missing_pmid", "missing_pmid", "INFO", lambda: one({"pmid": None, "doi": "10.1000/x"})),
    Case("missing_doi", "missing_doi", "INFO", lambda: one({"pmid": "1000", "doi": None})),
    # --- assess.assess_all（文献評価）---
    Case("retracted", "retracted_publication", "MAJOR",
         lambda: one(meta_kw={"publication_types_list": ["Journal Article", "Retracted Publication"],
                              "comments_corrections": [{"ref_type": "RetractionIn", "ref_source": "Lancet. 2010", "pmid": "2", "note": ""}]})),
    Case("partial_retraction", "retracted_publication", "MAJOR",
         lambda: one(meta_kw={"comments_corrections": [{"ref_type": "PartialRetractionIn", "ref_source": "J X. 2020", "pmid": "", "note": ""}]})),
    Case("expression_of_concern", "expression_of_concern", "MODERATE",
         lambda: one(meta_kw={"comments_corrections": [{"ref_type": "ExpressionOfConcernIn", "ref_source": "J X. 2021", "pmid": "", "note": ""}]})),
    Case("erratum_notice", "erratum_notice", "INFO",
         lambda: one(meta_kw={"comments_corrections": [{"ref_type": "ErratumIn", "ref_source": "J X. 2022", "pmid": "", "note": ""}]})),
    Case("non_original_source", "non_original_source", "INFO", lambda: one(meta_kw={"publication_types_list": ["Letter"]})),
    Case("outdated_citation", "outdated_citation", "INFO", lambda: one(meta_kw={"year": "2000"})),
    Case("predatory_risk", "predatory_risk", "MODERATE", predatory),
    Case("claim_not_supported", "claim_not_supported", "MODERATE", lambda: claim("DOES_NOT_SUPPORT")),
    Case("claim_partially_supported", "claim_partially_supported", "INFO", lambda: claim("PARTIAL")),
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.id)
def test_category_fires_with_expected_severity(case: Case):
    hits = of(run(**case.build()), case.category)
    assert hits, f"{case.category} が発火しない"
    assert hits[0]["severity"] == case.severity


def test_all_19_categories_are_covered():
    assert {c.category for c in CASES} == ALL_CATEGORIES
    assert len(ALL_CATEGORIES) == 19


def test_title_similarity_bands_are_as_documented():
    """タイトルの帯（MAJOR <0.70・MODERATE <0.90・MINOR <0.99・それ以上は指摘なし）の前提を検算する。"""
    assert similarity(TITLE, TITLE_MAJOR) < 0.70
    assert 0.70 <= similarity(TITLE, TITLE_MODERATE) < 0.90
    assert 0.90 <= similarity(TITLE, TITLE_MINOR) < 0.99
    assert similarity(TITLE, TITLE_SAME) >= 0.99


# --- 発火してはいけない形（誤検出の防止）---------------------------------------

def test_clean_reference_has_no_issue():
    ref = {"pmid": "1000", "doi": "10.1000/x", "claimed_first_author": "Smith J", "claimed_year": 2025,
           "claimed_journal": "J Test", "claimed_title": TITLE_SAME}
    assert run(**one(ref)) == []


@pytest.mark.parametrize("ref_kw,meta_kw,category", [
    ({"claimed_first_author": "Smith K"}, {"first_author": "Smith J"}, "first_author_mismatch"),   # 姓が同じならイニシャル違いは指摘しない
    ({"claimed_title": TITLE_SAME}, {"title": TITLE}, "title_major_diff"),                       # 一致度 0.99 以上は指摘しない
    ({"claimed_journal": "Cancer"}, {"journal": "Cancer Res"}, "journal_mismatch"),              # 部分一致は同一とみなす
    ({"doi": "https://doi.org/10.1000/X"}, {"doi": "10.1000/x"}, "doi_mismatch"),                # DOI の URL 形式・大文字は正規化する
    ({"claimed_year": 2025}, {"year": "2025"}, "year_mismatch"),
], ids=["same-surname", "title-0.99", "journal-substring", "doi-normalized", "same-year"])
def test_no_false_positive(ref_kw, meta_kw, category):
    assert of(run(**one(ref_kw, meta_kw)), category) == []


def test_predatory_flag_is_conservative():
    meta = {"journal": "Obscure J", "issn": "1234-5678"}
    key = enrich.journal_key(meta)
    both_negative = {key: {"medline_indexed": False, "doaj_listed": False}}
    # L1/L2（PMID・DOI の直接一致）で解決した文献は、両シグナル陰性でも立てない
    assert of(run(**one(meta_kw=meta, path="L1", journal_info=both_negative)), "predatory_risk") == []
    # どちらかが陽性、または両方不明なら立てない
    for ji in ({"medline_indexed": True, "doaj_listed": False}, {"medline_indexed": False, "doaj_listed": True},
               {"medline_indexed": None, "doaj_listed": None}):
        assert of(run(**one(meta_kw=meta, path="L3a", journal_info={key: ji})), "predatory_risk") == []


def test_recency_boundary_is_ten_years():
    assert of(run(**one(meta_kw={"year": str(TODAY - 10)})), "outdated_citation") == []
    assert len(of(run(**one(meta_kw={"year": str(TODAY - 11)})), "outdated_citation")) == 1


def test_review_letter_is_not_flagged_as_non_original():
    assert of(run(**one(meta_kw={"publication_types_list": ["Letter", "Review"]})), "non_original_source") == []


def test_claim_supported_and_unresolved_are_not_assessed():
    assert of(run(**claim("SUPPORTS")), "claim_not_supported") == []
    unresolved = one(status="UNRESOLVED", claim_support={1: {"verdict": "DOES_NOT_SUPPORT", "rationale": "x"}})
    issues = run(**unresolved)
    assert [i["category"] for i in issues] == ["unresolved"]


def test_issues_are_sorted_by_severity_and_summarized():
    issues = run(**one({"pmid": "111", "doi": None, "claimed_year": 2024}, pmid="222"))
    order = [i["severity"] for i in issues]
    assert order == sorted(order, key=lambda s: consistency.SEVERITIES.index(s))
    summary = consistency.summarize(issues)
    assert summary["total"] == len(issues)
    assert summary["by_category"]["pmid_mismatch"] == 1
