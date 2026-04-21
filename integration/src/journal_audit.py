"""
journal_audit.py — Citation journal と PubMed journal_iso の整合性監査

目的:
    本スキル既存の Stage 5 (report.md 合成) が検出するのは「タイトル類似度
    低下」「引用年乖離」「重複引用」のみだが、実運用で遭遇する査読重要事象
    の一つに「著者による引用ジャーナル名誤記」がある (例: References.docx の
    Ref #13 は DOI が指す雑誌は Jpn J Clin Oncol だが、引用では Ultrasound
    Med. Biol. と誤記)。

    本モジュールはこれを独立した監査パスとして、解決済み全件について
    citation_journal と PubMed journal_iso/journal_full の類似度を計算し、
    下記の三段階で査読所見を生成する。

    - similarity < 50%  → MAJOR (別論文または重大誤記の可能性大)
    - 50 ≤ similarity < 70 → WARN (略称の揺れを超える可能性あり、要確認)
    - 70 ≤ similarity < 80 → INFO (通常の略称差、参考情報)

依存:
    rapidfuzz (既存の PubMed カスケードで既にインストール済み)

出力:
    {
        "ref_no": int,
        "cite_journal": str,   # 引用側の記載
        "pm_journal": str,     # PubMed の journal_iso または journal_full
        "pmid": str,
        "similarity": int,     # 0-100 integer
        "severity": "MAJOR" | "WARN" | "INFO" | "OK",
    }
    のリスト。severity == "OK" は 80% 以上で除外される。
"""

from __future__ import annotations

import re
from typing import Any


def _normalize_journal(j: str | None) -> str:
    if not j:
        return ""
    j = j.strip().lower()
    j = re.sub(r"[.,;:&]", " ", j)
    j = re.sub(r"\s+", " ", j)
    return j.strip()


def _classify_severity(similarity: int) -> str:
    if similarity < 50:
        return "MAJOR"
    if similarity < 70:
        return "WARN"
    if similarity < 80:
        return "INFO"
    return "OK"


def audit_journal_mismatch(
    structured: list[dict[str, Any]],
    resolutions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """citation journal と PubMed journal_iso の類似度監査を実行する。

    Args:
        structured: main.py Stage 3 の stage3_structured と同じ形式
        resolutions: main.py Stage 4 の stage4_pubmed_resolutions と同じ形式

    Returns:
        severity が OK 以外のミスマッチ情報のリスト。similarity 昇順。
    """
    try:
        from rapidfuzz import fuzz
    except ImportError as e:
        raise RuntimeError(
            "rapidfuzz is required. Install: pip install rapidfuzz"
        ) from e

    structured_by_refno = {s["ref_no"]: s for s in structured}
    findings: list[dict[str, Any]] = []

    for r in resolutions:
        if not r.get("pmid"):
            continue
        refno = r["ref_no"]
        s = structured_by_refno.get(refno, {})
        cite_j = s.get("journal")
        meta = r.get("metadata") or {}
        pm_j = (
            meta.get("journal_iso")
            or meta.get("journal_full")
            or meta.get("journal")
        )
        if not cite_j or not pm_j:
            continue

        n1 = _normalize_journal(cite_j)
        n2 = _normalize_journal(pm_j)
        # 略称揺れに強い token_set_ratio と部分一致の max を採用
        ratio = int(round(max(
            fuzz.token_set_ratio(n1, n2),
            fuzz.partial_ratio(n1, n2),
        )))
        severity = _classify_severity(ratio)
        if severity == "OK":
            continue
        findings.append({
            "ref_no": refno,
            "cite_journal": cite_j,
            "pm_journal": pm_j,
            "pmid": r["pmid"],
            "similarity": ratio,
            "severity": severity,
        })

    findings.sort(key=lambda x: (x["severity"], x["similarity"]))
    return findings


def format_findings_markdown(findings: list[dict[str, Any]]) -> str:
    """report.md 追記用のセクション文字列を生成する。"""
    if not findings:
        return (
            "\n---\n\n"
            "## 補遺: ジャーナル名と PubMed 収載誌の照合監査\n\n"
            "解決済み全件について citation journal と PubMed journal_iso の"
            "類似度を計算した結果、\n"
            "類似度 80% 未満のケースは **検出されませんでした**。\n"
            "ジャーナル名記載に系統的な誤りは認められません。\n"
        )

    by_severity: dict[str, list[dict[str, Any]]] = {
        "MAJOR": [], "WARN": [], "INFO": []
    }
    for f in findings:
        by_severity[f["severity"]].append(f)

    lines: list[str] = [
        "\n---\n",
        "## 補遺: ジャーナル名と PubMed 収載誌の照合監査\n",
        "解決済み Reference 全件について、"
        "citation journal と PubMed `journal_iso` の類似度を計算。\n",
    ]

    if by_severity["MAJOR"]:
        lines.append("\n### [MAJOR] 重大な不一致 (類似度 < 50%)\n")
        lines.append(
            "**別論文または重大な記載誤りの可能性。必ず査読コメントで指摘推奨。**\n"
        )
        for f in by_severity["MAJOR"]:
            lines.append(
                f"- **Ref #{f['ref_no']} 類似度 {f['similarity']}% "
                f"(PMID: {f['pmid']})**\n"
                f"  - 引用側: `{f['cite_journal']}`\n"
                f"  - PubMed: `{f['pm_journal']}`\n"
            )

    if by_severity["WARN"]:
        lines.append("\n### [WARN] 要確認 (類似度 50-69%)\n")
        lines.append(
            "略称の揺れを超える乖離。著者に確認を検討。\n"
        )
        for f in by_severity["WARN"]:
            lines.append(
                f"- Ref #{f['ref_no']} 類似度 {f['similarity']}% "
                f"(PMID: {f['pmid']}): "
                f"`{f['cite_journal']}` vs PubMed `{f['pm_journal']}`\n"
            )

    if by_severity["INFO"]:
        lines.append("\n### [INFO] 軽微な差異 (類似度 70-79%)\n")
        lines.append(
            "通常の略称表記揺れ。参考情報として記載。\n"
        )
        for f in by_severity["INFO"]:
            lines.append(
                f"- Ref #{f['ref_no']} 類似度 {f['similarity']}%: "
                f"`{f['cite_journal']}` vs `{f['pm_journal']}` "
                f"(PMID: {f['pmid']})\n"
            )

    return "\n".join(lines)
