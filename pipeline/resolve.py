"""Stage 4: PubMed カスケード照合 (標準ライブラリのみ / 一括 efetch 対応)。

設計上の要点
------------
1. 依存ゼロ: urllib + xml.etree + difflib のみ。rapidfuzz / tenacity / requests 不要。
2. 一括 efetch: PMID が確定した参照はまとめて 1 リクエストで取得する。
   実測 19 PMID の一括取得 = 0.39 秒 (逐次 10.3 秒 → 96% 短縮)。
3. XPath 限定: ReferenceList/Reference 内の ArticleIdList を拾わないよう、
   ./PubmedData/ArticleIdList/ArticleId と ./MedlineCitation/Article/ELocationID
   のみを対象にする (指示書 Step 5 落とし穴 1)。
4. タイトル検索に二重引用符を使わない (同 落とし穴 2)。
5. L3 系で得た PMID は タイトル類似度 >= 0.5 かつ 筆頭著者姓一致 を満たす場合のみ採用
   (同 落とし穴 3)。
"""

from __future__ import annotations

import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from difflib import SequenceMatcher

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
EPMC_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
EFETCH_CHUNK = 150  # NCBI は GET で 200 程度まで許容。余裕をみて 150。
ESEARCH_COOLDOWN = 300  # esearch 障害検知後、NCBI を再試行するまでの秒数


class SearchBackendError(RuntimeError):
    """NCBI esearch が検索不能（「ヒットなし」ではない）であることを示す。"""

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into",
    "is", "of", "on", "or", "the", "to", "with", "using", "based", "study",
    "among", "between", "after", "before", "during", "its", "their", "this",
    "that", "these", "those", "was", "were", "than", "then", "not", "no",
}


# ---------------------------------------------------------------------------
# 正規化ユーティリティ
# ---------------------------------------------------------------------------

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm_text(s: str | None) -> str:
    if not s:
        return ""
    s = strip_accents(str(s)).lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_journal(s: str | None) -> str:
    """雑誌名の比較用正規化。末尾ピリオド除去・略記ゆらぎ吸収。"""
    t = norm_text(s)
    t = re.sub(r"\bjournal\b", "j", t)
    t = re.sub(r"\bof\b|\bthe\b|\band\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def norm_doi(s: str | None) -> str:
    if not s:
        return ""
    t = str(s).strip().lower()
    t = re.sub(r"^https?://(dx\.)?doi\.org/", "", t)
    t = re.sub(r"^doi:\s*", "", t)
    return t.rstrip(" .")


def surname(author: str | None) -> str:
    """'Han B' / 'Han, Bingfeng' / 'B. Han' から姓を取り出す。"""
    if not author:
        return ""
    a = strip_accents(str(author)).strip()
    if "," in a:
        return norm_text(a.split(",")[0])
    toks = [t for t in re.split(r"\s+", a) if t]
    if not toks:
        return ""
    # 'B. Han' のように先頭がイニシャルなら末尾を姓とみなす
    if len(toks) >= 2 and re.fullmatch(r"[A-Z]\.?", toks[0]):
        return norm_text(toks[-1])
    return norm_text(toks[0])


def similarity(a: str | None, b: str | None) -> float:
    na, nb = norm_text(a), norm_text(b)
    if not na or not nb:
        return 0.0
    return SequenceMatcher(None, na, nb).ratio()


def title_keywords(title: str | None, limit: int = 6) -> list[str]:
    words = [w for w in norm_text(title).split() if w not in STOPWORDS and len(w) > 2]
    return words[:limit]


# ---------------------------------------------------------------------------
# E-utilities クライアント
# ---------------------------------------------------------------------------

@dataclass
class Attempt:
    level: str
    query: str
    n_hits: int = 0
    accepted: str | None = None
    rejected_reason: str | None = None


class PubMedClient:
    def __init__(self, api_key: str | None = None, tool: str = "pubmed-reference-resolver"):
        self.api_key = api_key
        self.tool = tool
        self.min_interval = 0.11 if api_key else 0.34
        self._last = 0.0
        self.n_requests = 0
        self.seconds_in_http = 0.0
        self._esearch_down_until = 0.0   # この時刻まで NCBI esearch を試さない
        self.n_fallback = 0              # Europe PMC へフォールバックした検索回数
        self.last_esearch_error: str | None = None

    def _throttle(self) -> None:
        gap = time.time() - self._last
        if gap < self.min_interval:
            time.sleep(self.min_interval - gap)
        self._last = time.time()

    def _get(self, endpoint: str, params: dict, retries: int = 3) -> str:
        params = {"tool": self.tool, **params}
        if self.api_key:
            params["api_key"] = self.api_key
        url = f"{NCBI_BASE}/{endpoint}?" + urllib.parse.urlencode(params)
        last_err: Exception | None = None
        for attempt in range(retries):
            try:
                self._throttle()
                t0 = time.time()
                with urllib.request.urlopen(url, timeout=60) as r:
                    body = r.read().decode("utf-8", errors="replace")
                self.seconds_in_http += time.time() - t0
                self.n_requests += 1
                return body
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
                last_err = e
                code = getattr(e, "code", None)
                if code is not None and code not in (429, 500, 502, 503, 504):
                    raise
                time.sleep(min(2 ** attempt * 2, 10))
        raise RuntimeError(f"NCBI request failed after {retries} attempts: {last_err}")

    def esearch(self, term: str, retmax: int = 5) -> list[str]:
        """NCBI esearch。障害（HTTP 5xx 継続・200 + ERROR 応答・非 JSON）は
        SearchBackendError を送出する。「ヒットなし」と「検索不能」を区別するため、
        障害時に空リストを返してはならない（実在文献が unresolved と誤判定される）。"""
        try:
            body = self._get("esearch.fcgi", {
                "db": "pubmed", "term": term, "retmax": str(retmax), "retmode": "json",
            })
        except RuntimeError as e:  # _get がリトライ上限到達で送出
            raise SearchBackendError(str(e)) from e
        try:
            result = json.loads(body)["esearchresult"]
        except (ValueError, KeyError, TypeError) as e:
            raise SearchBackendError(f"esearch の応答を解釈できません: {body[:120]!r}") from e
        if result.get("ERROR"):
            raise SearchBackendError(f"esearch ERROR: {str(result['ERROR'])[:160]}")
        return list(result.get("idlist", []) or [])

    def esearch_is_down(self) -> bool:
        return time.time() < self._esearch_down_until

    def search(self, term: str, epmc_query: str | None = None,
               retmax: int = 5) -> tuple[list[str], str]:
        """PMID 検索。NCBI esearch を優先し、障害時は Europe PMC へ自動フォールバックする。

        戻り値: (PMID リスト, 経路 "ncbi" | "europepmc")。
        フォールバックしても PMID の確定後は NCBI efetch で書誌を取得するため、
        メタデータの出所は変わらない。障害検知後 ESEARCH_COOLDOWN 秒は NCBI を
        試さず直接 Europe PMC へ向かう（毎回 3 回リトライの待ち時間を払わないため）。
        epmc_query が None（フォールバック不能）の場合は NCBI の障害をそのまま送出する。
        """
        if not self.esearch_is_down() or epmc_query is None:
            try:
                return self.esearch(term, retmax), "ncbi"
            except (SearchBackendError, urllib.error.URLError) as e:
                if epmc_query is None:
                    raise
                self._esearch_down_until = time.time() + ESEARCH_COOLDOWN
                self.last_esearch_error = str(e)
        ids = self.epmc_search(epmc_query, retmax)
        self.n_fallback += 1
        return ids, "europepmc"

    def epmc_search(self, query: str, retmax: int = 5) -> list[str]:
        """Europe PMC で検索し PubMed 収載記事（SRC:MED）の PMID を返す。"""
        params = {"query": f"({query}) AND SRC:MED", "format": "json",
                  "resultType": "lite", "pageSize": str(retmax)}
        url = EPMC_BASE + "?" + urllib.parse.urlencode(params)
        last_err: Exception | None = None
        for attempt in range(3):
            try:
                self._throttle()
                t0 = time.time()
                req = urllib.request.Request(url, headers={"User-Agent": self.tool})
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = json.loads(r.read().decode("utf-8", errors="replace"))
                self.seconds_in_http += time.time() - t0
                self.n_requests += 1
                results = data["resultList"]["result"]
                return [str(x["pmid"]) for x in results
                        if x.get("source") == "MED" and x.get("pmid")]
            except (urllib.error.URLError, TimeoutError, ValueError, KeyError, TypeError) as e:
                last_err = e
                time.sleep(min(2 ** attempt * 2, 10))
        raise RuntimeError(
            f"NCBI esearch と Europe PMC の両方が利用できません: {last_err}")

    def efetch_many(self, pmids: list[str]) -> dict[str, dict]:
        """複数 PMID を一括取得する。これが速度最適化の中核。"""
        out: dict[str, dict] = {}
        uniq = [p for p in dict.fromkeys(pmids) if p]
        for i in range(0, len(uniq), EFETCH_CHUNK):
            chunk = uniq[i:i + EFETCH_CHUNK]
            body = self._get("efetch.fcgi", {
                "db": "pubmed", "id": ",".join(chunk), "retmode": "xml",
            })
            out.update(parse_pubmed_xml_all(body))
        return out


# ---------------------------------------------------------------------------
# XML パース
# ---------------------------------------------------------------------------

def _text(node) -> str:
    return "".join(node.itertext()).strip() if node is not None else ""


def parse_pubmed_xml_all(xml_text: str) -> dict[str, dict]:
    """efetch の XML から PMID をキーに全記事のメタデータを取り出す。"""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {}
    out: dict[str, dict] = {}
    for art in list(root.findall(".//PubmedArticle")) + list(root.findall(".//PubmedBookArticle")):
        meta = _parse_one(art)
        if meta and meta.get("pmid"):
            out[meta["pmid"]] = meta
    return out


def _parse_one(art) -> dict | None:
    pmid = _text(art.find("./MedlineCitation/PMID"))
    if not pmid:
        pmid = _text(art.find(".//PMID"))
    if not pmid:
        return None

    article = art.find("./MedlineCitation/Article")
    title = _text(article.find("./ArticleTitle")) if article is not None else ""

    # --- 著者 -----------------------------------------------------------
    authors: list[str] = []
    if article is not None:
        for a in article.findall("./AuthorList/Author"):
            last = _text(a.find("./LastName"))
            init = _text(a.find("./Initials"))
            coll = _text(a.find("./CollectiveName"))
            if last:
                authors.append(f"{last} {init}".strip())
            elif coll:
                authors.append(coll)

    # --- 雑誌 / 巻号頁 / 年 ----------------------------------------------
    journal = volume = issue = pages = year = ""
    if article is not None:
        j = article.find("./Journal")
        if j is not None:
            journal = _text(j.find("./ISOAbbreviation")) or _text(j.find("./Title"))
            ji = j.find("./JournalIssue")
            if ji is not None:
                volume = _text(ji.find("./Volume"))
                issue = _text(ji.find("./Issue"))
                year = _text(ji.find("./PubDate/Year"))
                if not year:
                    md = _text(ji.find("./PubDate/MedlineDate"))
                    m = re.search(r"(19|20)\d{2}", md)
                    year = m.group(0) if m else ""
        pages = _text(article.find("./Pagination/MedlinePgn"))

    # --- ID (XPath を限定: 参照リスト内の ID を拾わない) --------------------
    doi = pmcid = ""
    for aid in art.findall("./PubmedData/ArticleIdList/ArticleId"):
        t = (aid.get("IdType") or "").lower()
        v = (aid.text or "").strip()
        if t == "doi" and not doi:
            doi = v
        elif t == "pmc" and not pmcid:
            pmcid = v
    if not doi and article is not None:
        for eid in article.findall("./ELocationID"):
            if (eid.get("EIdType") or "").lower() == "doi":
                doi = (eid.text or "").strip()
                break

    # --- 抄録 -------------------------------------------------------------
    abstract_parts: list[str] = []
    if article is not None:
        for ab in article.findall("./Abstract/AbstractText"):
            label = ab.get("Label")
            body = "".join(ab.itertext()).strip()
            abstract_parts.append(f"{label}: {body}" if label else body)
    abstract = "\n".join(p for p in abstract_parts if p)

    ptypes = [_text(p) for p in art.findall("./MedlineCitation/Article/PublicationTypeList/PublicationType")]

    # --- 雑誌識別子 (Predatory リスク評価用の収載状況照会に使う) ----------------
    issn = issn_linking = journal_full = nlm_unique_id = ""
    if article is not None:
        j = article.find("./Journal")
        if j is not None:
            issn = _text(j.find("./ISSN"))
            journal_full = _text(j.find("./Title"))
    mji = art.find("./MedlineCitation/MedlineJournalInfo")
    if mji is not None:
        issn_linking = _text(mji.find("./ISSNLinking"))
        nlm_unique_id = _text(mji.find("./NlmUniqueID"))

    # --- 撤回・懸念表明・訂正 (CommentsCorrectionsList) -----------------------
    # 注意: ここは記事自身に付与された通知のみを対象とする RefType 限定抽出であり、
    # 参照リスト (ReferenceList/Reference) 内の ID は引き続き拾わない。
    CC_REFTYPES = {"RetractionIn", "PartialRetractionIn", "ExpressionOfConcernIn",
                   "ErratumIn", "CorrectedandRepublishedIn"}
    comments_corrections: list[dict] = []
    for cc in art.findall("./MedlineCitation/CommentsCorrectionsList/CommentsCorrections"):
        rt = cc.get("RefType") or ""
        if rt in CC_REFTYPES:
            comments_corrections.append({
                "ref_type": rt,
                "ref_source": _text(cc.find("./RefSource")),
                "pmid": _text(cc.find("./PMID")),
                "note": _text(cc.find("./Note")),
            })

    return {
        "pmid": pmid, "title": title, "authors": authors,
        "first_author": authors[0] if authors else "",
        "journal": journal, "year": year, "volume": volume, "issue": issue,
        "pages": pages, "doi": doi, "pmcid": pmcid,
        "publication_types": "; ".join(ptypes), "abstract": abstract,
        "publication_types_list": ptypes,
        "issn": issn, "issn_linking": issn_linking,
        "journal_full": journal_full, "nlm_unique_id": nlm_unique_id,
        "comments_corrections": comments_corrections,
    }


# ---------------------------------------------------------------------------
# カスケード解決
# ---------------------------------------------------------------------------

TITLE_ACCEPT = 0.50   # L3 採用の下限 (指示書 Step 5-3)


def _accept(ref: dict, meta: dict) -> tuple[bool, str]:
    """L3 系ヒットの採否判定。タイトル類似度 + 筆頭著者姓の二重ガード。"""
    ts = similarity(ref.get("claimed_title"), meta.get("title"))
    claimed_sn = surname(ref.get("claimed_first_author"))
    pm_sn = surname(meta.get("first_author"))
    author_ok = (not claimed_sn) or (not pm_sn) or (claimed_sn == pm_sn)
    if ref.get("claimed_title") and ts < TITLE_ACCEPT:
        return False, f"title similarity {ts:.2f} < {TITLE_ACCEPT}"
    if not author_ok:
        return False, f"first author '{claimed_sn}' != '{pm_sn}'"
    return True, ""


def _tag(term: str, via: str) -> str:
    """フォールバック経由の検索は、解決経路の透明性トレースに分かるよう印を付ける。"""
    return term if via == "ncbi" else f"[Europe PMC フォールバック] {term}"


def resolve_all(refs: list[dict], client: PubMedClient, verbose: bool = True) -> list[dict]:
    """参照リスト全体を解決する。戻り値は ref ごとの解決レコード。"""
    rec: dict[int, dict] = {
        r["ref_no"]: {
            "ref_no": r["ref_no"], "pmid": None, "metadata": None,
            "resolution_path": None, "attempts": [], "match_status": None,
        } for r in refs
    }
    by_no = {r["ref_no"]: r for r in refs}

    # --- 事前分類: PubMed 非対象 -------------------------------------------
    targets = []
    for r in refs:
        if r.get("is_non_pubmed"):
            rec[r["ref_no"]].update(match_status="NON_PUBMED", resolution_path="NON_PUBMED")
        else:
            targets.append(r)
    if verbose:
        print(f"[Stage4] 対象 {len(targets)} 件 / 非対象 {len(refs) - len(targets)} 件")

    # --- L1: PMID 記載分を一括 efetch ---------------------------------------
    l1 = [r for r in targets if (r.get("pmid") or "").strip()]
    if l1:
        metas = client.efetch_many([str(r["pmid"]).strip() for r in l1])
        for r in l1:
            pm = str(r["pmid"]).strip()
            m = metas.get(pm)
            rec[r["ref_no"]]["attempts"].append(
                Attempt("L1", f"efetch id={pm}", 1 if m else 0,
                        pm if m else None, None if m else "PMID not found").__dict__)
            if m:
                rec[r["ref_no"]].update(pmid=pm, metadata=m,
                                        resolution_path="L1", match_status="RESOLVED")
        if verbose:
            print(f"[Stage4] L1 一括 efetch: {len(l1)} 件 → 解決 "
                  f"{sum(1 for r in l1 if rec[r['ref_no']]['pmid'])} 件 (1 リクエスト)")

    # --- L2: DOI 検索 (esearch は個別、efetch は一括) --------------------------
    l2 = [r for r in targets
          if not rec[r["ref_no"]]["pmid"] and norm_doi(r.get("doi"))]
    found: dict[int, str] = {}
    for r in l2:
        d = norm_doi(r["doi"])
        term = f"{d}[DOI]"
        ids, via = client.search(term, f'DOI:"{d}"', retmax=3)
        rec[r["ref_no"]]["attempts"].append(
            Attempt("L2", _tag(term, via), len(ids), ids[0] if ids else None,
                    None if ids else "no hit").__dict__)
        if ids:
            found[r["ref_no"]] = ids[0]
    if found:
        metas = client.efetch_many(list(found.values()))
        for ref_no, pm in found.items():
            m = metas.get(pm)
            if m:
                rec[ref_no].update(pmid=pm, metadata=m,
                                   resolution_path="L2", match_status="RESOLVED")
    if verbose and l2:
        print(f"[Stage4] L2 DOI 検索: {len(l2)} 件 → 解決 {len(found)} 件 "
              f"(esearch {len(l2)} + efetch 1 リクエスト)")

    # --- L3a-d: 個別カスケード -----------------------------------------------
    rest = [r for r in targets if not rec[r["ref_no"]]["pmid"]]
    for r in rest:
        _cascade_l3(r, rec[r["ref_no"]], client, verbose=verbose)

    for r in refs:
        if rec[r["ref_no"]]["match_status"] is None:
            rec[r["ref_no"]]["match_status"] = "UNRESOLVED"
            rec[r["ref_no"]]["resolution_path"] = "UNRESOLVED"

    if verbose:
        n_res = sum(1 for v in rec.values() if v["match_status"] == "RESOLVED")
        print(f"[Stage4] 完了: RESOLVED {n_res} / "
              f"UNRESOLVED {sum(1 for v in rec.values() if v['match_status'] == 'UNRESOLVED')} / "
              f"NON_PUBMED {sum(1 for v in rec.values() if v['match_status'] == 'NON_PUBMED')}  "
              f"HTTP {client.n_requests} req / {client.seconds_in_http:.2f} s")
        if client.n_fallback:
            print(f"[Stage4] NCBI esearch 障害のため Europe PMC へフォールバック: "
                  f"{client.n_fallback} 検索 ({client.last_esearch_error})")
    return [rec[r["ref_no"]] for r in refs]


def _cascade_l3(ref: dict, out: dict, client: PubMedClient, verbose: bool = False) -> None:
    """L3a → L3b → L3c → L3d の順に試行する。二重引用符は一切使わない。"""
    au = surname(ref.get("claimed_first_author"))
    yr = str(ref.get("claimed_year") or "").strip()[:4]
    jn = (ref.get("claimed_journal") or "").strip()
    kws = title_keywords(ref.get("claimed_title"))

    # 各プランは (レベル, NCBI 検索式, Europe PMC 検索式)。Europe PMC 側は NCBI 障害時の
    # フォールバック専用で、同じ意味の検索を AUTH/TITLE/JOURNAL/PUB_YEAR で表現する。
    # 採否は従来どおり efetch 後の _accept()（タイトル類似度 + 筆頭著者姓）で決まる。
    plans: list[tuple[str, str, str]] = []
    e_au = f'AUTH:"{au}"' if au else ""
    e_jn = f'JOURNAL:"{norm_text(jn)}"' if jn else ""
    e_yr = f"PUB_YEAR:{yr}" if yr else ""
    if au and kws:
        t = " AND ".join(f"{w}[Title]" for w in kws)
        q = f"{au}[Author] AND ({t})"
        e_t = " AND ".join(f'TITLE:"{w}"' for w in kws)
        plans.append(("L3a", q + (f" AND {yr}[PDAT]" if yr else ""),
                      " AND ".join(x for x in (e_au, f"({e_t})", e_yr) if x)))
    if au and jn and yr:
        plans.append(("L3b",
                      f"{au}[Author] AND {jn}[Journal] AND {yr}[PDAT]"
                      + (" AND (" + " OR ".join(f"{w}[Title]" for w in kws) + ")" if kws else ""),
                      f"{e_au} AND {e_jn} AND {e_yr}"
                      + (" AND (" + " OR ".join(f'TITLE:"{w}"' for w in kws) + ")" if kws else "")))
        plans.append(("L3c", f"{au}[Author] AND {jn}[Journal] AND {yr}[PDAT]",
                      f"{e_au} AND {e_jn} AND {e_yr}"))
    if kws:
        t = " AND ".join(f"{w}[Title]" for w in kws)
        e_t = " AND ".join(f'TITLE:"{w}"' for w in kws)
        plans.append(("L3d", t + (f" AND {yr}[PDAT]" if yr else ""),
                      e_t + (f" AND {e_yr}" if yr else "")))

    for level, term, epmc_q in plans:
        ids, via = client.search(term, epmc_q, retmax=5)
        term = _tag(term, via)
        if not ids:
            out["attempts"].append(Attempt(level, term, 0, None, "no hit").__dict__)
            continue
        metas = client.efetch_many(ids)
        for pm in ids:
            m = metas.get(pm)
            if not m:
                continue
            ok, why = _accept(ref, m)
            if ok:
                out["attempts"].append(Attempt(level, term, len(ids), pm, None).__dict__)
                out.update(pmid=pm, metadata=m, resolution_path=level, match_status="RESOLVED")
                return
        out["attempts"].append(Attempt(level, term, len(ids), None,
                                       f"all {len(ids)} hits rejected (last: {why})").__dict__)
