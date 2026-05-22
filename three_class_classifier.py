"""three_class_classifier — 「PubMed 未ヒット 3 分類」統合 logic.

Day13 INVESTIGATION で発見、Day15 SPEC §3.3 で定義された統合 module.

3 分類:
  A. 真の捏造 (DOI 実在せず, LLM ハルシネーション候補) — 重大
  B. MEDLINE 非収録誌の正規論文 (predatory journal 含む) — 軽微
  C. MEDLINE 収録誌の indexing 漏れ論文 — 軽微 (人手確認推奨)
  unknown. 判定不可 (network エラー等, graceful fail-soft)

Day13 §3.4 擬似コードを実装:
    if not ref.get('doi'):
        return 'A'
    if not check_crossref(doi).exists:
        return 'A'  (404 = DOI 実在せず)
    nlm = get_nlm_status(journal/issn)
    if nlm.status == 'N': return 'B'
    if nlm.status == 'Y': return 'C'
    return 'unknown'

依存性注入 (DI) パターン: production では crossref_check / nlm_catalog_check
の関数を default で使用、test では fixture-bound fake を渡せる.

Usage:
    import three_class_classifier

    # production:
    result = three_class_classifier.classify_unresolved_refs(unresolved_refs)

    # test:
    result = three_class_classifier.classify_unresolved_refs(
        unresolved_refs,
        crossref_fn=fake_crossref,
        nlm_fn=fake_nlm,
    )

Returns:
    list of dict, each:
      {
          "ref_no": int,
          "class": "A" | "B" | "C" | "unknown",
          "reason": str,
          "doi_resolved": bool | None,
          "journal_indexing": "Y" | "N" | None,
          "details": dict
      }

参照: docs/sessions/day15/SPEC_three_class_audit.md §3.3, §4.
"""
from __future__ import annotations

import re
from typing import Any, Callable

import crossref_check
import nlm_catalog_check


_CONFERENCE_PATTERNS = re.compile(
    r"\b(?:conference|conf\.|proceedings|proc\.|workshop|symposium|"
    r"symp\.|congress|meeting)\b",
    re.IGNORECASE,
)


def _detect_book(ref: dict[str, Any]) -> bool:
    """ref が book chapter か判定 (Day20 Rule 1).

    is_book=True なら book と確定. フォールバック: raw_text に 'isbn'
    含む or publisher field 在り.
    """
    if ref.get("is_book") is True:
        return True
    raw = (ref.get("raw_text") or "").lower()
    if "isbn" in raw:
        return True
    if "publisher" in raw and ref.get("publisher"):
        return True
    return False


def _detect_conference(journal: str | None) -> bool:
    """journal 名に conference/proceedings/workshop 等を含むか判定 (Day20 Rule 2).

    \\b 単語境界で false positive 抑制 (例: 'Annals' の 'ann' は誤検出しない).
    """
    if not journal:
        return False
    return bool(_CONFERENCE_PATTERNS.search(journal))


def _classify_via_nlm_only(
    ref_no: int,
    journal: str,
    nlm_fn: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """DOI 欠落だが journal 名は判明している case の NLM 直接検索 (Day20 Rule 3).

    Crossref skip して NLM Catalog で journal indexing 確認.
    status=N → B / status=Y → C / status=None → unknown.
    """
    nlm = nlm_fn(journal_name=journal)
    status = nlm.get("status")
    base = {
        "ref_no": ref_no,
        "doi_resolved": None,
        "journal_indexing": status,
        "details": {
            "doi": None,
            "crossref_journal": journal,
            "nlm_id": nlm.get("nlm_id"),
            "nlm_medlineta": nlm.get("medlineta"),
        },
    }
    if status == "N":
        return {
            **base,
            "class": "B",
            "reason": (
                f"DOI 欠落だが journal '{journal}' は MEDLINE 非収録 "
                "(NLM 直接検索)"
            ),
        }
    if status == "Y":
        return {
            **base,
            "class": "C",
            "reason": (
                f"DOI 欠落、journal '{journal}' は MEDLINE 収録だが "
                "本論文単体は indexing なし"
            ),
        }
    return {
        **base,
        "class": "unknown",
        "reason": f"DOI 欠落 + NLM 検索でも判定不可: {nlm.get('error')}",
    }


def classify_unresolved_refs(
    unresolved_refs: list[dict[str, Any]],
    *,
    crossref_fn: Callable[[str], dict] | None = None,
    nlm_fn: Callable[..., dict] | None = None,
) -> list[dict[str, Any]]:
    """未解決 ref に 3 分類 (A/B/C/unknown) を付与.

    Args:
        unresolved_refs: list of dicts, each with keys:
            ref_no (int), doi (str|None), journal (str|None)
        crossref_fn: crossref_check.check_doi_exists 互換の関数 (DI、test 用)
        nlm_fn: nlm_catalog_check.get_journal_indexing_status 互換 (DI)

    Returns:
        list of classification dicts (上記 module docstring 参照)
    """
    if crossref_fn is None:
        crossref_fn = crossref_check.check_doi_exists
    if nlm_fn is None:
        nlm_fn = nlm_catalog_check.get_journal_indexing_status

    results: list[dict[str, Any]] = []
    for ref in unresolved_refs:
        results.append(_classify_single(ref, crossref_fn, nlm_fn))
    return results


def _classify_single(
    ref: dict[str, Any],
    crossref_fn: Callable[[str], dict],
    nlm_fn: Callable[..., dict],
) -> dict[str, Any]:
    """単一 ref に 3 分類を付与."""
    ref_no = ref.get("ref_no")
    doi = ref.get("doi")
    journal = ref.get("journal")

    # Day20 改修: DOI 欠落 case を 4 rule 順次評価に拡張
    if not doi or not str(doi).startswith("10."):
        # Rule 1: is_book → B (book は MEDLINE 対象外)
        if _detect_book(ref):
            return {
                "ref_no": ref_no,
                "class": "B",
                "reason": "book chapter (DOI 欠落だが MEDLINE 対象外)",
                "doi_resolved": None,
                "journal_indexing": None,
                "details": {"doi": doi, "journal": journal, "is_book": True},
            }

        # Rule 2: conference proceedings → B (MEDLINE 非収録が標準)
        if _detect_conference(journal):
            return {
                "ref_no": ref_no,
                "class": "B",
                "reason": (
                    f"conference/proceedings '{journal}' "
                    "(MEDLINE 非収録が標準)"
                ),
                "doi_resolved": None,
                "journal_indexing": None,
                "details": {
                    "doi": doi, "journal": journal, "conference": True,
                },
            }

        # Rule 3: journal 名あり → NLM 直接検索 (B/C/unknown)
        if journal:
            return _classify_via_nlm_only(ref_no, journal, nlm_fn)

        # Rule 4: 全て該当せず → A (真の判定不可)
        return {
            "ref_no": ref_no,
            "class": "A",
            "reason": (
                "DOI 欠落 + journal 不明 (真の判定不可、"
                "LLM ハルシネーション候補)"
            ),
            "doi_resolved": None,
            "journal_indexing": None,
            "details": {"doi": doi, "journal": journal},
        }

    # Crossref で DOI 実在確認
    cr = crossref_fn(doi)
    if cr.get("exists") is False:
        return {
            "ref_no": ref_no,
            "class": "A",
            "reason": "Crossref で DOI 解決失敗 (DOI 実在せず, LLM ハルシネーション候補)",
            "doi_resolved": False,
            "journal_indexing": None,
            "details": {"doi": doi, "crossref_error": cr.get("error")},
        }
    if cr.get("exists") is None:
        return {
            "ref_no": ref_no,
            "class": "unknown",
            "reason": f"Crossref network error (graceful unknown): {cr.get('error')}",
            "doi_resolved": None,
            "journal_indexing": None,
            "details": {"doi": doi},
        }

    # cr.exists == True → NLM Catalog で journal status 確認
    crossref_meta = cr.get("metadata") or {}
    issns = crossref_meta.get("ISSN") or []
    container = crossref_meta.get("container-title") or []
    crossref_journal = container[0] if container else journal
    crossref_publisher = crossref_meta.get("publisher")

    if issns:
        nlm = nlm_fn(issn=issns[0])
    elif crossref_journal:
        nlm = nlm_fn(journal_name=crossref_journal)
    else:
        nlm = {"status": None, "error": "no journal info from crossref or ref"}

    nlm_status = nlm.get("status")
    base_details = {
        "doi": doi,
        "crossref_journal": crossref_journal,
        "crossref_publisher": crossref_publisher,
        "nlm_id": nlm.get("nlm_id"),
        "nlm_medlineta": nlm.get("medlineta"),
    }

    if nlm_status == "N":
        return {
            "ref_no": ref_no,
            "class": "B",
            "reason": (
                f"journal '{crossref_journal}' は MEDLINE 非収録 "
                f"(currentindexingstatus=N"
                + (f", publisher={crossref_publisher}" if crossref_publisher else "")
                + ")"
            ),
            "doi_resolved": True,
            "journal_indexing": "N",
            "details": base_details,
        }
    if nlm_status == "Y":
        return {
            "ref_no": ref_no,
            "class": "C",
            "reason": (
                f"journal '{crossref_journal}' は MEDLINE 収録 "
                f"(currentindexingstatus=Y) だが本論文単体は indexing なし"
            ),
            "doi_resolved": True,
            "journal_indexing": "Y",
            "details": base_details,
        }

    # nlm_status is None or unexpected → unknown
    return {
        "ref_no": ref_no,
        "class": "unknown",
        "reason": f"NLM Catalog status 不明: {nlm.get('error')}",
        "doi_resolved": True,
        "journal_indexing": None,
        "details": base_details,
    }
