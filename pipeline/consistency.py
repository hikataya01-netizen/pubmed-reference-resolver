"""Stage 6: 整合性チェック (指示書 Step 6 の 11 カテゴリ / 4 段階重要度)。

旧 main.py の `_classify_reviewer_issues` は 4 カテゴリ・3 段階しか実装しておらず、
pmid_mismatch / first_author_mismatch / journal_mismatch / doi_mismatch /
doi_suspicious_in_pubmed / missing_pmid / missing_doi が欠落していた。
本モジュールで 11 カテゴリ全てをコード化する。
"""

from __future__ import annotations

import re
from collections import defaultdict

from .resolve import norm_doi, norm_journal, similarity, surname

SEVERITIES = ("MAJOR", "MODERATE", "MINOR", "INFO")

# PubMed 側に稀に混入する無意味な旧形式 DOI: 10.1016/0000-0000(00)00000-0 等
SUSPICIOUS_DOI = re.compile(r"^10\.\d{4,5}/0{4}-0{4}\(\d{2}\)0{5}-\d$")


def _issue(ref_no: int, category: str, severity: str, detail: str,
           claimed: str = "", found: str = "") -> dict:
    return {
        "ref_no": ref_no, "category": category, "severity": severity,
        "detail": detail, "claimed": claimed, "found": found,
    }


def check_all(refs: list[dict], resolutions: list[dict]) -> list[dict]:
    by_no = {r["ref_no"]: r for r in refs}
    issues: list[dict] = []

    # ---- 重複引用 (複合キー: PMID / DOI / 正規化タイトル+筆頭著者+年) ----------
    seen: dict[tuple, int] = {}
    for res in resolutions:
        ref = by_no.get(res["ref_no"], {})
        m = res.get("metadata") or {}
        keys = []
        if res.get("pmid"):
            keys.append(("pmid", res["pmid"]))
        d = norm_doi(m.get("doi") or ref.get("doi"))
        if d:
            keys.append(("doi", d))
        for k in keys:
            if k in seen and seen[k] != res["ref_no"]:
                issues.append(_issue(
                    res["ref_no"], "duplicate_citation", "MAJOR",
                    f"Ref #{seen[k]} と同一文献の重複引用 ({k[0].upper()}: {k[1]})",
                    claimed=f"Ref #{res['ref_no']}", found=f"Ref #{seen[k]}"))
                break
            seen.setdefault(k, res["ref_no"])

    for res in resolutions:
        no = res["ref_no"]
        ref = by_no.get(no, {})
        status = res.get("match_status")

        # ---- 未解決 ---------------------------------------------------------
        if status == "UNRESOLVED":
            note = ref.get("non_pubmed_note_if_unresolved") or \
                "MEDLINE 非収録誌の可能性。CrossRef 等での確認を推奨"
            issues.append(_issue(no, "unresolved", "MAJOR",
                                 f"全戦略で PubMed 未ヒット。{note}",
                                 claimed=ref.get("claimed_title") or ""))
            continue
        if status == "NON_PUBMED":
            continue

        m = res.get("metadata") or {}

        # ---- PMID 不一致 ----------------------------------------------------
        c_pmid = str(ref.get("pmid") or "").strip()
        if c_pmid and res.get("pmid") and c_pmid != res["pmid"]:
            issues.append(_issue(no, "pmid_mismatch", "MAJOR",
                                 "引用元 PMID と解決 PMID が不一致",
                                 claimed=c_pmid, found=res["pmid"]))

        # ---- 筆頭著者 -------------------------------------------------------
        cs, ps = surname(ref.get("claimed_first_author")), surname(m.get("first_author"))
        if cs and ps and cs != ps:
            issues.append(_issue(no, "first_author_mismatch", "MAJOR",
                                 "筆頭著者の姓が不一致（著者順誤記の可能性）",
                                 claimed=ref.get("claimed_first_author") or "",
                                 found=m.get("first_author") or ""))

        # ---- タイトル -------------------------------------------------------
        if ref.get("claimed_title") and m.get("title"):
            s = similarity(ref["claimed_title"], m["title"])
            if s < 0.70:
                sev = "MAJOR"
            elif s < 0.90:
                sev = "MODERATE"
            elif s < 0.99:
                sev = "MINOR"
            else:
                sev = None
            if sev:
                issues.append(_issue(no, "title_major_diff", sev,
                                     f"タイトル一致度 {s * 100:.0f}%",
                                     claimed=ref["claimed_title"], found=m["title"]))

        # ---- 雑誌名 ---------------------------------------------------------
        if ref.get("claimed_journal") and m.get("journal"):
            a, b = norm_journal(ref["claimed_journal"]), norm_journal(m["journal"])
            s = 1.0 if (a == b or a in b or b in a) else similarity(a, b)
            if s < 0.60:
                sev = "MAJOR"
            elif s < 0.80:
                sev = "MODERATE"
            elif s < 1.0:
                sev = "MINOR"
            else:
                sev = None
            if sev:
                issues.append(_issue(no, "journal_mismatch", sev,
                                     f"雑誌名一致度 {s * 100:.0f}%",
                                     claimed=ref["claimed_journal"], found=m["journal"]))

        # ---- DOI ------------------------------------------------------------
        cd, pd = norm_doi(ref.get("doi")), norm_doi(m.get("doi"))
        if cd and pd and cd != pd:
            issues.append(_issue(no, "doi_mismatch", "MAJOR",
                                 "引用元 DOI と PubMed 側 DOI が不一致",
                                 claimed=cd, found=pd))
        if pd and SUSPICIOUS_DOI.match(pd):
            issues.append(_issue(no, "doi_suspicious_in_pubmed", "MODERATE",
                                 "PubMed 側 DOI が旧式プレースホルダ形式。出版社側の登録不備",
                                 found=pd))

        # ---- 発行年 ----------------------------------------------------------
        cy, py = str(ref.get("claimed_year") or "")[:4], str(m.get("year") or "")[:4]
        if cy.isdigit() and py.isdigit() and cy != py:
            diff = abs(int(cy) - int(py))
            sev = "MAJOR" if diff >= 3 else ("MODERATE" if diff == 2 else "MINOR")
            note = "Epub/Print 年の差の可能性" if diff == 1 else "別論文の可能性を要確認"
            issues.append(_issue(no, "year_mismatch", sev,
                                 f"発行年が {diff} 年相違。{note}", claimed=cy, found=py))

        # ---- 情報補完提案 ----------------------------------------------------
        if not c_pmid and res.get("pmid"):
            issues.append(_issue(no, "missing_pmid", "INFO",
                                 "引用元に PMID 記載なし。追記により参照性が向上",
                                 found=res["pmid"]))
        if not cd and pd:
            issues.append(_issue(no, "missing_doi", "INFO",
                                 "引用元に DOI 記載なし。追記により参照性が向上", found=pd))

    return sort_issues(issues)


def sort_issues(issues: list[dict]) -> list[dict]:
    """重要度順 → ref_no 順の正準ソート。assess.py 由来の issue との結合後にも使う。"""
    order = {s: i for i, s in enumerate(SEVERITIES)}
    issues.sort(key=lambda x: (order[x["severity"]], x["ref_no"], x["category"]))
    return issues


def summarize(issues: list[dict]) -> dict:
    sev = {s: 0 for s in SEVERITIES}
    cat: dict[str, int] = defaultdict(int)
    for i in issues:
        sev[i["severity"]] += 1
        cat[i["category"]] += 1
    return {"by_severity": sev, "by_category": dict(cat), "total": len(issues)}
