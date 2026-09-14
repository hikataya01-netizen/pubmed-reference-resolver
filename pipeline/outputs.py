"""Stage 7: 出力生成。成果物は 3 本に固定する。

  ① references_audit_report.docx  (build_docx.js が report_data.json から生成)
  ② references_pubmed.csv         (UTF-8 BOM)
  ③ references_abstracts.txt      (78 字ラップ)

旧実装の unresolved.csv は廃止し、内容は出力① §3「要確認項目」へ統合した。
ファイル名は OUT_DOCX / OUT_CSV / OUT_TXT で一元管理する。
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

OUT_DOCX = "references_audit_report.docx"
OUT_CSV = "references_pubmed.csv"
OUT_TXT = "references_abstracts.txt"
REPORT_JSON = "report_data.json"

WRAP = 78

CSV_COLUMNS = [
    "Ref_No", "Match_Status",
    "PMID", "PMCID", "Title", "Authors", "First_Author", "Journal", "Year",
    "Volume", "Issue", "Pages", "DOI", "Publication_Types",
    "Claimed_PMID", "Claimed_DOI", "Claimed_Year", "Claimed_First_Author",
    "Claimed_Journal", "Claimed_Title",
    "Resolution_Path",
    # --- v2 文献評価列 (assess.py の assessment dict から転記) -----------------
    "Retraction_Status", "Retraction_Notice", "Recency", "Originality",
    "Evidence_Level", "Indexing_Status", "Predatory_Risk", "Claim_Support",
]

PATH_LABELS = {
    "L1": "Level 1: PMID 直接 (一括 efetch)",
    "L2": "Level 2: DOI 検索 (esearch → 一括 efetch)",
    "L3a": "Level 3a: 著者 + タイトル重要語 + 年",
    "L3b": "Level 3b: 著者 + 雑誌 + 年 + タイトル重要語",
    "L3c": "Level 3c: 著者 + 雑誌 + 年",
    "L3d": "Level 3d: タイトル重要語のみ + 年",
    "NON_PUBMED": "Skip: PubMed 非対象",
    "UNRESOLVED": "未解決",
}


# ---------------------------------------------------------------------------
# 出力② CSV
# ---------------------------------------------------------------------------

def write_csv(refs: list[dict], resolutions: list[dict], out_dir: Path) -> Path:
    by_no = {r["ref_no"]: r for r in refs}
    path = out_dir / OUT_CSV
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for res in resolutions:
            ref = by_no.get(res["ref_no"], {})
            m = res.get("metadata") or {}
            a = res.get("assessment") or {}
            w.writerow({
                "Ref_No": res["ref_no"],
                "Match_Status": res.get("match_status") or "",
                "PMID": res.get("pmid") or "",
                "PMCID": m.get("pmcid") or "",
                "Title": m.get("title") or (ref.get("claimed_title") if res.get("match_status") == "NON_PUBMED" else "") or "",
                "Authors": "; ".join(m.get("authors") or []) or (ref.get("claimed_first_author") or "" if res.get("match_status") == "NON_PUBMED" else ""),
                "First_Author": m.get("first_author") or (ref.get("claimed_first_author") or "" if res.get("match_status") == "NON_PUBMED" else ""),
                "Journal": m.get("journal") or (ref.get("claimed_journal") or "" if res.get("match_status") == "NON_PUBMED" else ""),
                "Year": m.get("year") or (ref.get("claimed_year") or "" if res.get("match_status") == "NON_PUBMED" else ""),
                "Volume": m.get("volume") or "",
                "Issue": m.get("issue") or "",
                "Pages": m.get("pages") or "",
                "DOI": m.get("doi") or "",
                "Publication_Types": m.get("publication_types") or "",
                "Claimed_PMID": ref.get("pmid") or "",
                "Claimed_DOI": ref.get("doi") or "",
                "Claimed_Year": ref.get("claimed_year") or "",
                "Claimed_First_Author": ref.get("claimed_first_author") or "",
                "Claimed_Journal": ref.get("claimed_journal") or "",
                "Claimed_Title": ref.get("claimed_title") or "",
                "Resolution_Path": res.get("resolution_path") or "",
                "Retraction_Status": a.get("retraction_status") or "",
                "Retraction_Notice": a.get("retraction_notice") or "",
                "Recency": a.get("recency") or "",
                "Originality": a.get("originality") or "",
                "Evidence_Level": a.get("evidence_level") or "",
                "Indexing_Status": a.get("indexing") or "",
                "Predatory_Risk": a.get("predatory_risk") or "",
                "Claim_Support": a.get("claim_support") or "",
            })
    return path


# ---------------------------------------------------------------------------
# 出力③ abstract 一覧
# ---------------------------------------------------------------------------

def _dw(ch: str) -> int:
    """表示幅。全角 (W/F) と一部の曖昧幅 (A) を 2 桁として数える。"""
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F", "A") else 1


def disp_len(s: str) -> int:
    return sum(_dw(c) for c in s)


def _wrap_line(line: str, width: int, indent: str = "") -> list[str]:
    """CJK 対応の折返し。ラテン語は単語境界、CJK は文字境界で折る。"""
    out: list[str] = []
    cur, cur_w = indent, disp_len(indent)
    # 単語トークン（空白区切り）と CJK 文字を混在させて処理する
    tokens: list[str] = []
    for word in re.split(r"(\s+)", line):
        if not word:
            continue
        if any(_dw(c) == 2 for c in word):
            tokens.extend(list(word))
        else:
            tokens.append(word)
    for tok in tokens:
        tw = disp_len(tok)
        if cur_w + tw > width and cur.strip():
            out.append(cur.rstrip())
            cur, cur_w = indent, disp_len(indent)
            if tok.isspace():
                continue
        cur += tok
        cur_w += tw
    if cur.strip():
        out.append(cur.rstrip())
    return out or [""]


def _wrap(text: str, indent: str = "") -> str:
    if not text:
        return ""
    out: list[str] = []
    for para in str(text).split("\n"):
        if not para.strip():
            out.append("")
            continue
        out.extend(_wrap_line(para, WRAP, indent))
    return "\n".join(out)


def _center(text: str, width: int = WRAP) -> str:
    pad = max(0, (width - disp_len(text)) // 2)
    return " " * pad + text


def write_abstracts(refs: list[dict], resolutions: list[dict],
                    out_dir: Path, subject: str = "") -> Path:
    by_no = {r["ref_no"]: r for r in refs}
    L: list[str] = []
    L.append("=" * WRAP)
    L.append(_center("参照文献 抄録集"))
    if subject:
        L.append(_center(subject) if disp_len(subject) <= WRAP else _wrap(subject))
    L.append("=" * WRAP)
    L.append("")
    L.append(_wrap("PubMed 逆引き照合により取得した抄録を参照番号順に収載する。"
                   "PubMed 非対象および未解決の参照は、抄録を掲載せず判定根拠のみを示す。"))
    L.append("")

    for res in resolutions:
        no = res["ref_no"]
        ref = by_no.get(no, {})
        m = res.get("metadata") or {}
        status = res.get("match_status")
        L.append("-" * WRAP)

        if status == "RESOLVED":
            authors = m.get("authors") or []
            shown = "; ".join(authors[:20]) + ("; et al." if len(authors) > 20 else "")
            L.append(_wrap(f"{no}. {shown}", ""))
            L.append("")
            L.append(_wrap(m.get("title") or ""))
            L.append("")
            cite = f"{m.get('journal','')}. {m.get('year','')}"
            if m.get("volume"):
                cite += f";{m['volume']}"
            if m.get("issue"):
                cite += f"({m['issue']})"
            if m.get("pages"):
                cite += f":{m['pages']}"
            L.append(_wrap(cite + "."))
            ids = [f"PMID: {res.get('pmid')}"]
            if m.get("pmcid"):
                ids.append(f"PMCID: {m['pmcid']}")
            if m.get("doi"):
                ids.append(f"DOI: {m['doi']}")
            L.append(_wrap("  ".join(ids)))
            L.append(f"[解決経路: {PATH_LABELS.get(res.get('resolution_path'), res.get('resolution_path'))}]")
            a = res.get("assessment") or {}
            if a:
                ev = (f"[評価: {a.get('originality', '—')} / 水準 {a.get('evidence_level', '—')}"
                      f" / {a.get('recency', '—')}"
                      + (f"({m.get('year')})" if m.get("year") else "")
                      + f" / 収載 {a.get('indexing', '—')}"
                      + (f" / Predatoryリスク {a['predatory_risk']}"
                         if a.get("predatory_risk") not in (None, "", "低") else "")
                      + (f" / 主張支持 {a['claim_support']}"
                         if a.get("claim_support") not in (None, "", "NOT_ASSESSED") else "")
                      + "]")
                L.append(_wrap(ev))
            L.append("")
            if a.get("retraction_status") in ("RETRACTED", "PARTIAL_RETRACTION"):
                L.append("!" * WRAP)
                L.append(_wrap("【警告】本論文は撤回されている。引用の妥当性を必ず再検討する"
                               "こと。引用が不可避な場合は撤回済みである旨を本文に明記する"
                               "必要がある。"))
                if a.get("retraction_notice"):
                    L.append(_wrap(f"撤回通知: {a['retraction_notice']}"))
                L.append("!" * WRAP)
                L.append("")
            elif a.get("retraction_status") == "EXPRESSION_OF_CONCERN":
                L.append(_wrap("【注意】本論文には Expression of Concern (懸念表明) が付されて"
                               f"いる。{a.get('retraction_notice') or ''}"))
                L.append("")
            if m.get("abstract"):
                L.append(_wrap(m["abstract"]))
            else:
                L.append("(抄録なし — PubMed に抄録が登録されていない)")

        elif status == "NON_PUBMED":
            L.append(_wrap(f"{no}. {ref.get('claimed_first_author','')}", ""))
            L.append("")
            L.append(_wrap(ref.get("claimed_title") or ""))
            L.append("")
            L.append(_wrap(f"{ref.get('claimed_journal','')}. {ref.get('claimed_year','')}."))
            L.append("")
            L.append(_wrap(f"【PubMed 非対象】{ref.get('non_pubmed_reason') or '理由未記載'}"))
            L.append("抄録は掲載しない。")

        else:  # UNRESOLVED
            L.append(_wrap(f"{no}. {ref.get('claimed_first_author','')}", ""))
            L.append("")
            L.append(_wrap(ref.get("claimed_title") or ""))
            L.append("")
            L.append(_wrap(f"{ref.get('claimed_journal','')}. {ref.get('claimed_year','')}."))
            L.append("")
            note = ref.get("non_pubmed_note_if_unresolved") or \
                "MEDLINE 非収録誌の可能性。CrossRef 等での確認を推奨"
            L.append(_wrap(f"【未解決】{note}"))
            tried = ", ".join(a["level"] for a in res.get("attempts") or [])
            L.append(_wrap(f"試行経路: {tried or 'なし'}"))
            L.append("抄録は掲載しない。")
        L.append("")

    L.append("=" * WRAP)
    L.append(f"総参照数 {len(resolutions)} 件 / 抄録収載 "
             f"{sum(1 for r in resolutions if (r.get('metadata') or {}).get('abstract'))} 件")
    L.append("=" * WRAP)

    path = out_dir / OUT_TXT
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# 出力① 用の中間 JSON
# ---------------------------------------------------------------------------

def build_report_data(refs: list[dict], resolutions: list[dict], issues: list[dict],
                      meta: dict, out_dir: Path, self_check_notes: list[str]) -> Path:
    by_no = {r["ref_no"]: r for r in refs}
    status_count = Counter(r.get("match_status") for r in resolutions)
    path_count = Counter(r.get("resolution_path") for r in resolutions)
    sev_count = Counter(i["severity"] for i in issues)

    details = []
    for res in resolutions:
        ref = by_no.get(res["ref_no"], {})
        m = res.get("metadata") or {}
        mark = {"RESOLVED": "✓", "NON_PUBMED": "⊘", "UNRESOLVED": "✗"}.get(res.get("match_status"), "?")
        details.append({
            "ref_no": res["ref_no"], "mark": mark,
            "status": res.get("match_status"),
            "pmid": res.get("pmid") or "—",
            "author": m.get("first_author") or ref.get("claimed_first_author") or "—",
            "title": m.get("title") or ref.get("claimed_title") or "—",
            "journal": m.get("journal") or ref.get("claimed_journal") or "—",
            "year": m.get("year") or ref.get("claimed_year") or "—",
        })

    unresolved = [{
        "ref_no": r["ref_no"],
        "title": by_no.get(r["ref_no"], {}).get("claimed_title") or "—",
        "journal": by_no.get(r["ref_no"], {}).get("claimed_journal") or "—",
        "tried": ", ".join(a["level"] for a in r.get("attempts") or []) or "なし",
        "note": by_no.get(r["ref_no"], {}).get("non_pubmed_note_if_unresolved")
                or "MEDLINE 非収録誌の可能性",
    } for r in resolutions if r.get("match_status") == "UNRESOLVED"]

    non_pubmed = [{
        "ref_no": r["ref_no"],
        "title": by_no.get(r["ref_no"], {}).get("claimed_title") or "—",
        "reason": by_no.get(r["ref_no"], {}).get("non_pubmed_reason") or "—",
    } for r in resolutions if r.get("match_status") == "NON_PUBMED"]

    # --- v2 文献評価 (docx §5 用) ---------------------------------------------
    assessments = []
    retractions = []
    for res in resolutions:
        a = res.get("assessment")
        if not a:
            continue
        m = res.get("metadata") or {}
        assessments.append({
            "ref_no": res["ref_no"],
            "retraction": a.get("retraction_status") or "—",
            "originality": a.get("originality") or "—",
            "evidence_level": a.get("evidence_level") or "—",
            "recency": (a.get("recency") or "—")
                       + (f" ({m.get('year')})" if m.get("year") else ""),
            "indexing": a.get("indexing") or "—",
            "predatory_risk": a.get("predatory_risk") or "—",
            "claim_support": a.get("claim_support") or "NOT_ASSESSED",
        })
        if a.get("retraction_status") in ("RETRACTED", "PARTIAL_RETRACTION",
                                          "EXPRESSION_OF_CONCERN"):
            retractions.append({
                "ref_no": res["ref_no"],
                "status": a["retraction_status"],
                "title": m.get("title") or "—",
                "notice": a.get("retraction_notice") or "—",
            })
    a_counter = Counter()
    for a in assessments:
        if a["retraction"] in ("RETRACTED", "PARTIAL_RETRACTION"):
            a_counter["retracted"] += 1
        if a["retraction"] == "EXPRESSION_OF_CONCERN":
            a_counter["concern"] += 1
        if a["recency"].startswith("古い"):
            a_counter["outdated"] += 1
        if a["predatory_risk"] == "要確認":
            a_counter["predatory_flagged"] += 1
    assessment_summary = {
        "retracted": a_counter.get("retracted", 0),
        "concern": a_counter.get("concern", 0),
        "outdated": a_counter.get("outdated", 0),
        "predatory_flagged": a_counter.get("predatory_flagged", 0),
        "originality": dict(Counter(a["originality"] for a in assessments)),
    }

    data = {
        "meta": meta,
        "summary": {
            "total": len(resolutions),
            "resolved": status_count.get("RESOLVED", 0),
            "non_pubmed": status_count.get("NON_PUBMED", 0),
            "unresolved": status_count.get("UNRESOLVED", 0),
            "severity": {k: sev_count.get(k, 0) for k in ("MAJOR", "MODERATE", "MINOR", "INFO")},
        },
        "paths": [{"path": p, "label": PATH_LABELS.get(p, p), "count": c}
                  for p, c in sorted(path_count.items(), key=lambda x: str(x[0]))],
        "issues": issues,
        "details": details,
        "unresolved": unresolved,
        "non_pubmed": non_pubmed,
        "assessments": assessments,
        "assessment_summary": assessment_summary,
        "retractions": retractions,
        "self_check": self_check_notes,
        "files": {"docx": OUT_DOCX, "csv": OUT_CSV, "txt": OUT_TXT},
    }
    path = out_dir / REPORT_JSON
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
