"""Stage 5.5: 雑誌収載状況の照会 (Predatory Journal リスク評価の材料収集)。

設計上の要点
------------
1. 依存ゼロ: urllib + json のみ。認証不要・無料・読み取り専用の API のみを使う。
   - NLM Catalog (E-utilities db=nlmcatalog): MEDLINE 収載状況 (currentindexingstatus)
     照会経路は esearch {issn}[ISSN] → esummary。NlmUniqueID の直接 esummary は
     内部 uid と一致せず error を返すため使わない (2026/08/22 実レスポンスで確認)。
   - DOAJ (https://doaj.org/api/search/journals/issn%3A{issn}): DOAJ 収載の有無。
2. ユニーク雑誌単位でキャッシュする。参照 100 件でも照会は雑誌数ぶんに留まる。
3. 全体を防御的に書く: どの照会が失敗しても None (未評価) に降格し、実行は止めない。
   本モジュールの失敗は Predatory リスク評価の欠測であって、監査全体の失敗ではない。
4. ここでは「シグナル収集」のみを行う。リスク判定そのもの (シグナルの複合) は
   assess.py が担う。収載状況は Predatory と同義ではない (購読誌は DOAJ に載らない)。
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

DOAJ_URL = "https://doaj.org/api/search/journals/issn%3A{issn}"
DOAJ_MIN_INTERVAL = 1.0  # DOAJ への礼儀的スロットル (仕様上の要求はないが自主的に)

_UA = {"User-Agent": "pubmed-reference-resolver/2.0 (academic reference audit)"}


def journal_key(meta: dict) -> str:
    """解決メタデータから雑誌キャッシュキーを作る。優先順: ISSNLinking > ISSN > NlmUniqueID > 誌名。"""
    for k in ("issn_linking", "issn", "nlm_unique_id"):
        v = (meta.get(k) or "").strip()
        if v:
            return v
    return (meta.get("journal") or "").strip().lower()


def _doaj_listed(issn: str) -> bool | None:
    """DOAJ 収載の有無。失敗時は None (未評価)。"""
    if not issn:
        return None
    url = DOAJ_URL.format(issn=urllib.parse.quote(issn))
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8", errors="replace"))
        return bool(data.get("total", 0) > 0)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None


def _medline_indexed(client, issn: str) -> bool | None:
    """NLM Catalog の currentindexingstatus (Y/N)。失敗・不明時は None (未評価)。

    client は resolve.PubMedClient (throttle / retry / api_key を共用する)。
    """
    if not issn:
        return None
    try:
        body = client._get("esearch.fcgi", {
            "db": "nlmcatalog", "term": f"{issn}[ISSN]", "retmax": "3", "retmode": "json",
        })
        ids = list(json.loads(body).get("esearchresult", {}).get("idlist", []) or [])
        if not ids:
            return None
        body = client._get("esummary.fcgi", {
            "db": "nlmcatalog", "id": ",".join(ids), "retmode": "json",
        })
        res = json.loads(body).get("result", {})
        statuses = []
        for uid in res.get("uids", []):
            doc = res.get(uid) or {}
            s = str(doc.get("currentindexingstatus", "")).strip().upper()
            if s in ("Y", "N"):
                statuses.append(s)
        if not statuses:
            return None  # フィールド欠落・形式変更時は未評価に倒す
        return "Y" in statuses
    except Exception:
        return None


def enrich_journals(resolutions: list[dict], client,
                    verbose: bool = True) -> tuple[dict[str, dict], list[str]]:
    """RESOLVED 参照の雑誌ごとに収載状況シグナルを照会する。

    戻り値: (journal_info, notes)
      journal_info[key] = {"issn": str, "journal": str,
                           "medline_indexed": True|False|None,
                           "doaj_listed": True|False|None}
      notes: self_check へ渡す注記 (照会失敗があった場合のみ)
    """
    journal_info: dict[str, dict] = {}
    notes: list[str] = []
    last_doaj = 0.0
    n_fail = 0

    uniq: dict[str, dict] = {}
    for res in resolutions:
        if res.get("match_status") != "RESOLVED":
            continue
        m = res.get("metadata") or {}
        key = journal_key(m)
        if key and key not in uniq:
            uniq[key] = m

    if verbose and uniq:
        print(f"[Stage5.5] 雑誌収載状況の照会: ユニーク雑誌 {len(uniq)} 誌 "
              f"(NLM Catalog + DOAJ)")

    for key, m in uniq.items():
        issn = (m.get("issn_linking") or m.get("issn") or "").strip()
        try:
            medline = _medline_indexed(client, issn)
            gap = time.time() - last_doaj
            if gap < DOAJ_MIN_INTERVAL:
                time.sleep(DOAJ_MIN_INTERVAL - gap)
            doaj = _doaj_listed(issn)
            last_doaj = time.time()
        except Exception:
            medline = doaj = None
        if medline is None and doaj is None:
            n_fail += 1
        journal_info[key] = {
            "issn": issn,
            "journal": m.get("journal") or m.get("journal_full") or "",
            "medline_indexed": medline,
            "doaj_listed": doaj,
        }

    if n_fail:
        notes.append(f"雑誌収載状況の照会が {n_fail}/{len(uniq)} 誌で失敗または不明であった。"
                     "該当誌の Predatory リスク・収載状況は「未評価」であり、"
                     "リスクなしを意味しない。")
    return journal_info, notes
