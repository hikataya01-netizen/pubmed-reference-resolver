"""Stage 6.5: 文献評価 (撤回・原著性・エビデンス水準・最新性・Predatory リスク・主張支持性)。

設計上の要点
------------
1. 純関数・ネットワークなし。入力は解決済みメタデータ + enrich.py の収載状況 +
   (任意の) claim_support 判定のみ。
2. 「問題」でない評価結果 (最新・原著・高水準など) は issues を汚染しない。
   全評価は res["assessment"] dict に格納し、CSV 新 8 列と docx §5 に流す。
   有害所見 (撤回・懸念表明・Predatory リスク・10 年超・非原著情報源・主張不支持)
   のみ consistency._issue() スキーマで issues にも計上する。
3. 最新性の閾値 (≤5 年 = 最新 / ≤10 年 = 妥当 / >10 年 = 古い) は旧 Reference-review
   プロジェクト src/evaluator.py から移植した概念である (コードは標準ライブラリで再実装)。
4. Predatory リスクは「MEDLINE 非収載 AND DOAJ 非収載 AND L3 系解決」の複合条件での
   参考フラグに留める。単独シグナルでは判定しない。購読誌は DOAJ に載らないため、
   DOAJ 非収載単独は無意味である。断定表現は用いない。
5. エビデンス水準は PublicationType のみから導出する。Impact Factor 等の雑誌指標は
   無料で機械可読なデータ源が存在しないため、意図的に用いない。
"""

from __future__ import annotations

import datetime

from .consistency import _issue

# --- 撤回・懸念表明・訂正 -----------------------------------------------------

RETRACTION_REFTYPES = {"RetractionIn", "PartialRetractionIn"}
CONCERN_REFTYPES = {"ExpressionOfConcernIn"}
ERRATUM_REFTYPES = {"ErratumIn", "CorrectedandRepublishedIn"}

# --- 原著性・エビデンス水準 (PublicationType ベース、優先順に判定) ----------------
# (ptype 部分一致キーワード, 原著性ラベル, エビデンス水準ラベル)
_ORIGINALITY_RULES: list[tuple[tuple[str, ...], str, str]] = [
    (("Retraction of Publication", "Retracted Publication (notice)"),
     "その他(撤回通知)", "N/A"),
    (("Meta-Analysis", "Systematic Review"), "メタ解析/SR", "1 (メタ解析/SR)"),
    (("Practice Guideline", "Guideline", "Consensus Development Conference"),
     "ガイドライン", "N/A (規範文書)"),
    (("Randomized Controlled Trial",), "原著", "2 (RCT)"),
    (("Clinical Trial", "Controlled Clinical Trial", "Pragmatic Clinical Trial"),
     "原著", "2-3 (臨床試験)"),
    (("Observational Study", "Cohort Studies", "Case-Control Studies",
      "Cross-Sectional Studies", "Multicenter Study", "Comparative Study",
      "Validation Study", "Evaluation Study"),
     "原著", "3 (観察研究)"),
    (("Case Reports",), "症例報告", "4 (症例報告)"),
    (("Review", "Scoping Review", "Narrative Review"), "レビュー", "記述的 (レビュー)"),
    (("Letter", "Editorial", "Comment", "News", "Interview"),
     "レター/社説/コメント", "記述的 (意見)"),
]

_NON_ORIGINAL_PTYPES = {"Letter", "Editorial", "Comment", "Retraction of Publication",
                        "Expression of Concern"}


def classify_retraction(meta: dict) -> tuple[str, str]:
    """(retraction_status, retraction_notice) を返す。"""
    ptypes = meta.get("publication_types_list") or []
    ccs = meta.get("comments_corrections") or []
    notices = [f"{c['ref_type']}: {c['ref_source']}"
               + (f" (PMID {c['pmid']})" if c.get("pmid") else "")
               for c in ccs]
    notice = " / ".join(notices)

    ref_types = {c["ref_type"] for c in ccs}
    if "Retracted Publication" in ptypes or ref_types & RETRACTION_REFTYPES:
        if "PartialRetractionIn" in ref_types and "RetractionIn" not in ref_types \
                and "Retracted Publication" not in ptypes:
            return "PARTIAL_RETRACTION", notice
        return "RETRACTED", notice
    if ref_types & CONCERN_REFTYPES:
        return "EXPRESSION_OF_CONCERN", notice
    if ref_types & ERRATUM_REFTYPES:
        return "CORRECTED", notice
    return "CLEAN", ""


def classify_originality(meta: dict) -> tuple[str, str]:
    """(originality, evidence_level) を PublicationType から決定論的に返す。"""
    ptypes = meta.get("publication_types_list") or []
    joined = "; ".join(ptypes)
    for keywords, orig, level in _ORIGINALITY_RULES:
        if any(kw in joined for kw in keywords):
            return orig, level
    if "Journal Article" in ptypes:
        return "原著", "3 (観察研究/記載なし)"
    return "その他", "N/A"


def classify_recency(year: str | int | None, today_year: int) -> tuple[str, int | None]:
    """(recency, age_years)。閾値は旧 Reference-review evaluator.py から移植。"""
    y = str(year or "")[:4]
    if not y.isdigit():
        return "判定不能", None
    age = today_year - int(y)
    if age <= 5:
        return "最新", age
    if age <= 10:
        return "妥当", age
    return "古い", age


def classify_predatory(meta: dict, journal_info: dict | None,
                       resolution_path: str | None) -> tuple[str, str]:
    """(predatory_risk, indexing) を返す。リスクは複合条件の参考フラグ。"""
    if not journal_info:
        return "未評価", "未確認"
    medline = journal_info.get("medline_indexed")
    doaj = journal_info.get("doaj_listed")

    if medline is True:
        indexing = "MEDLINE"
    elif doaj is True:
        indexing = "DOAJ"
    elif medline is None and doaj is None:
        indexing = "未確認"
    else:
        indexing = "PubMed収録(要確認)"

    if medline is None and doaj is None:
        return "未評価", indexing
    if medline is True or doaj is True:
        return "低", indexing
    # 両シグナル陰性。ただし L1/L2 (PMID/DOI 直接一致) で解決した文献は
    # 書誌の実在自体は強く裏付けられているため、L3 系のみフラグを立てる。
    if (resolution_path or "").startswith("L3"):
        return "要確認", indexing
    return "低", indexing


def assess_all(refs: list[dict], resolutions: list[dict],
               journal_info: dict[str, dict] | None,
               claim_support: dict[int, dict] | None,
               today_year: int | None = None) -> tuple[list[dict], list[str]]:
    """全 RESOLVED 参照に res["assessment"] を付与し、有害所見の issues を返す。

    journal_info: enrich.enrich_journals() の戻り値 (offline 時は None)
    claim_support: {ref_no: {"verdict": "SUPPORTS|PARTIAL|DOES_NOT_SUPPORT",
                             "rationale": "..."}} (未実施時は None)
    """
    from .enrich import journal_key  # 循環回避のため遅延 import

    today_year = today_year or datetime.date.today().year
    by_no = {r["ref_no"]: r for r in refs}
    extra_issues: list[dict] = []
    notes: list[str] = []
    n_retracted = 0

    for res in resolutions:
        no = res["ref_no"]
        if res.get("match_status") != "RESOLVED":
            res["assessment"] = None
            continue
        m = res.get("metadata") or {}

        # --- 撤回 -----------------------------------------------------------
        r_status, r_notice = classify_retraction(m)
        if r_status in ("RETRACTED", "PARTIAL_RETRACTION"):
            n_retracted += 1
            extra_issues.append(_issue(
                no, "retracted_publication", "MAJOR",
                "撤回された論文の引用。引用の妥当性を必ず再検討し、"
                "引用が不可避な場合は撤回済みである旨を本文に明記すること",
                claimed=m.get("title") or "", found=r_notice or "撤回通知"))
        elif r_status == "EXPRESSION_OF_CONCERN":
            extra_issues.append(_issue(
                no, "expression_of_concern", "MODERATE",
                "Expression of Concern (懸念表明) が付された論文の引用。"
                "経緯の確認を推奨", found=r_notice))
        elif r_status == "CORRECTED":
            extra_issues.append(_issue(
                no, "erratum_notice", "INFO",
                "訂正 (Erratum/Corrected and Republished) が存在する。"
                "引用箇所が訂正の影響を受けないか確認を推奨", found=r_notice))

        # --- 原著性・エビデンス水準 ------------------------------------------
        originality, evidence_level = classify_originality(m)
        ptypes = m.get("publication_types_list") or []
        if any(p in _NON_ORIGINAL_PTYPES for p in ptypes) and "Review" not in "; ".join(ptypes):
            extra_issues.append(_issue(
                no, "non_original_source", "INFO",
                f"一次研究でない情報源 ({originality}) の引用。"
                "事実主張の根拠として引用している場合は原著への差し替えを検討",
                found="; ".join(ptypes)))

        # --- 最新性 ----------------------------------------------------------
        recency, age = classify_recency(m.get("year"), today_year)
        if recency == "古い":
            extra_issues.append(_issue(
                no, "outdated_citation", "INFO",
                f"発行から {age} 年経過。より新しいエビデンスの有無の確認を推奨",
                found=str(m.get("year") or "")))

        # --- Predatory リスク -------------------------------------------------
        ji = (journal_info or {}).get(journal_key(m))
        predatory, indexing = classify_predatory(m, ji, res.get("resolution_path"))
        if predatory == "要確認":
            extra_issues.append(_issue(
                no, "predatory_risk", "MODERATE",
                "MEDLINE 非収載かつ DOAJ 非収載の雑誌で、書誌直接一致 (PMID/DOI) でも"
                "解決していない。収載状況シグナルに基づく参考フラグであり、"
                "粗悪学術誌 (Predatory Journal) と断定するものではない。"
                "Think.Check.Submit 等での確認を推奨",
                found=m.get("journal") or ""))

        # --- 主張支持性 (呼び出し側 LLM の判定を取り込むのみ) --------------------
        cs = (claim_support or {}).get(no)
        cs_verdict = (cs or {}).get("verdict") or "NOT_ASSESSED"
        if cs_verdict == "DOES_NOT_SUPPORT":
            extra_issues.append(_issue(
                no, "claim_not_supported", "MODERATE",
                "引用箇所の主張を被引用論文の抄録が支持していない (LLM 読解判定)。"
                f" 根拠: {(cs or {}).get('rationale') or '—'}",
                claimed="; ".join(by_no.get(no, {}).get("citation_contexts") or [])[:200],
                found=m.get("title") or ""))
        elif cs_verdict == "PARTIAL":
            extra_issues.append(_issue(
                no, "claim_partially_supported", "INFO",
                "引用箇所の主張を被引用論文が部分的にのみ支持 (LLM 読解判定)。"
                f" 根拠: {(cs or {}).get('rationale') or '—'}",
                found=m.get("title") or ""))

        res["assessment"] = {
            "retraction_status": r_status,
            "retraction_notice": r_notice,
            "recency": recency,
            "age_years": age,
            "originality": originality,
            "evidence_level": evidence_level,
            "indexing": indexing,
            "predatory_risk": predatory,
            "claim_support": cs_verdict,
        }

    if n_retracted:
        notes.append(f"撤回済み論文の引用を {n_retracted} 件検出した。原稿がこの撤回に"
                     "言及しているかを必ず確認すること。撤回論文の引用自体が直ちに"
                     "不適切とは限らないが、無言の引用は重大な問題である。")
    if journal_info is None:
        notes.append("雑誌収載状況の照会を実施していない (--offline)。"
                     "Predatory リスク・収載状況の列は全件「未評価」である。")
    return extra_issues, notes
