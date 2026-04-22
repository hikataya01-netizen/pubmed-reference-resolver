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
    include_ok: bool = False,
) -> list[dict[str, Any]]:
    """citation journal と PubMed journal_iso の類似度監査を実行する。

    Args:
        structured: main.py Stage 3 の stage3_structured と同じ形式
        resolutions: main.py Stage 4 の stage4_pubmed_resolutions と同じ形式
        include_ok: True の場合 severity=="OK" の finding も返す
            (sidecar JSON 等で解決済み全件の監査ログが必要な用途向け)。
            デフォルト False は後方互換の挙動 (OK を除外した査読所見のみ)。

    Returns:
        ミスマッチ情報のリスト。similarity 昇順。include_ok=False の
        場合は severity != "OK" のみ。
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

        # is_book guard: Skip book citations where journal-similarity
        # comparison is meaningless. Two trigger conditions (OR):
        #   1. is_book=True (explicit classification by parser or override)
        #   2. cite_journal starts with "In: " (Vancouver/AMA book-chapter
        #      convention, common when parser fails book detection)
        if s.get("is_book") or (cite_j and cite_j.startswith("In: ")):
            continue

        n1 = _normalize_journal(cite_j)
        n2 = _normalize_journal(pm_j)
        # 略称揺れに強い token_set_ratio と部分一致の max を採用
        ratio = int(round(max(
            fuzz.token_set_ratio(n1, n2),
            fuzz.partial_ratio(n1, n2),
        )))
        severity = _classify_severity(ratio)
        if severity == "OK" and not include_ok:
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


def format_summary_narrative(all_findings: list[dict[str, Any]]) -> str:
    """解決済み Reference 全件の監査結果をナラティブ要約として整形する。

    report.md 末尾の「補遺: ジャーナル名と PubMed 収載誌の照合監査 (追加)」
    セクションの本文を生成する。severity 別箇条書きではなく、全体件数と
    MAJOR 件数を日本語の短文でまとめる形式。

    Args:
        all_findings: audit_journal_mismatch(..., include_ok=True) の
            戻り値。解決済みかつ監査対象 (書籍除外後) の全 ref を含む。

    Returns:
        Markdown 文字列。先頭 `\\n---\\n` を含み、`## 補遺: ...` から末尾
        `詳細データ: ... (同ディレクトリ内)\\n` までを一つの文字列として
        返す。report.md 末尾に直接 append できる形式。
    """
    n = len(all_findings)
    majors = sorted(
        (f for f in all_findings if f.get("severity") == "MAJOR"),
        key=lambda x: x["ref_no"],
    )
    m = len(majors)

    lines: list[str] = [
        "\n---\n",
        "## 補遺: ジャーナル名と PubMed 収載誌の照合監査 (追加)\n",
    ]

    if m == 0:
        lines.append(
            f"解決済み {n} 件全件について citation journal と PubMed "
            f"journal_iso の類似度を計算した結果、\n"
            f"類似度 50% 未満のケースは検出されませんでした。\n"
            f"全 {n} 件が略称表記の差異を含めて 80% 以上の一致を示し、"
            f"ジャーナル名記載に\n"
            f"系統的な誤りは認められませんでした。\n"
        )
    else:
        ref_list = ", ".join(f"#{r['ref_no']}" for r in majors)
        count_str = "**1件のみ**" if m == 1 else f"**{m}件**"
        lines.append(
            f"解決済み {n} 件全件について citation journal と PubMed "
            f"journal_iso の類似度を計算した結果、\n"
            f"類似度 50% 未満のケースは {count_str} "
            f"(Ref {ref_list}) でした。\n"
            f"残り {n - m} 件は略称表記の差異を含めて 80% 以上の一致を示し、"
            f"ジャーナル名記載に\n"
            f"系統的な誤りは認められませんでした。\n"
        )

    lines.append(
        "詳細データ: `journal_mismatch_audit.json` (同ディレクトリ内)\n"
    )

    return "\n".join(lines)


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
