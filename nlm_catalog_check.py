"""nlm_catalog_check — NLM Catalog API client for journal MEDLINE indexing status.

Day15 SPEC §3.3 で定義された module. Day13 INVESTIGATION で発見した
「PubMed 未ヒット 3 分類」の判定 (`three_class_classifier.py` で統合) に
おいて、B 分類 (MEDLINE 非収録誌) vs C 分類 (収録誌の indexing 漏れ) の
決定的な判定根拠を提供する.

NLM Catalog API は 2-step:
  1. esearch: ISSN または journal name から NLM ID 取得
  2. esummary: NLM ID から currentindexingstatus 取得

依存: 標準ライブラリのみ (urllib, json) — 追加依存なし.
NCBI API key は任意 (環境変数 NCBI_API_KEY が設定されていれば自動利用,
rate limit 3 → 10 req/s).

Usage:
    from pathlib import Path
    import nlm_catalog_check

    # production (live API):
    result = nlm_catalog_check.get_journal_indexing_status(issn="1091-7527")

    # test (fixture 経由):
    result = nlm_catalog_check.get_journal_indexing_status(
        issn="1091-7527",
        fixture_search_path=Path("tests/fixtures/.../expected_nlm_search_1091-7527.json"),
        fixture_summary_path=Path("tests/fixtures/.../expected_nlm_summary_9610836.json"),
    )

Returns:
    {
        "status": "Y" | "N" | None,    # None = unknown (graceful, network 等)
        "nlm_id": str | None,
        "medlineta": str | None,        # journal 略称
        "error": str | None,
    }

Day15 SPEC §3.3 (signature) + §Q4 (graceful unknown on network error,
timeout 10s, retry 1 回, stderr WARN) に準拠.
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import certifi

NLM_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
TIMEOUT_SECONDS = 10

# Module-level SSL context with certifi-provided Mozilla CA bundle.
# Day22 fix: Python.org installer (Mac) ships an empty cert.pem at
# /Library/Frameworks/Python.framework/Versions/3.X/etc/openssl/,
# causing urllib default verification to fail with SSLCertVerificationError
# against https://eutils.ncbi.nlm.nih.gov/. Using certifi.where() works on
# all OSes (Linux/Mac/Windows) deterministically.
_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def _result(
    status: str | None,
    nlm_id: str | None = None,
    medlineta: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Standard return shape."""
    return {
        "status": status,
        "nlm_id": nlm_id,
        "medlineta": medlineta,
        "error": error,
    }


def get_journal_indexing_status(
    journal_name: str | None = None,
    issn: str | None = None,
    *,
    fixture_search_path: Path | None = None,
    fixture_summary_path: Path | None = None,
) -> dict[str, Any]:
    """NLM Catalog で journal の currentindexingstatus 取得.

    Search priority: ISSN (最優先) > journal_name.
    両方 None なら error.

    Args:
        journal_name: journal の正式名 or 部分文字列 (esearch term)
        issn: ISSN (より精確、推奨)
        fixture_search_path: 指定時 esearch を skip して fixture 読出 (test 用)
        fixture_summary_path: 指定時 esummary を skip して fixture 読出 (test 用)

    Returns:
        標準 dict shape (上記 Usage 参照)
    """
    if not issn and not journal_name:
        return _result(None, error="neither issn nor journal_name provided")

    # Step 1: esearch で NLM ID 取得
    if fixture_search_path is not None:
        try:
            search_data = json.loads(
                fixture_search_path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as e:
            return _result(None, error=f"search fixture read failed: {e}")
    else:
        search_data = _esearch_live(issn=issn, journal_name=journal_name)
        if search_data is None:
            return _result(None, error="esearch network failed")

    idlist = (
        (search_data.get("esearchresult") or {}).get("idlist") or []
    )
    if not idlist:
        return _result(None, error="esearch returned no NLM ID")

    nlm_id = idlist[0]

    # Step 2: esummary で詳細 (currentindexingstatus, medlineta) 取得
    if fixture_summary_path is not None:
        try:
            summary_data = json.loads(
                fixture_summary_path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as e:
            return _result(None, error=f"summary fixture read failed: {e}")
    else:
        summary_data = _esummary_live(nlm_id)
        if summary_data is None:
            return _result(None, error="esummary network failed")

    item = (summary_data.get("result") or {}).get(nlm_id) or {}
    status = item.get("currentindexingstatus")
    medlineta = item.get("medlineta")

    if status not in ("Y", "N"):
        return _result(None, nlm_id=nlm_id, medlineta=medlineta,
                       error=f"unexpected currentindexingstatus={status!r}")

    return _result(status, nlm_id=nlm_id, medlineta=medlineta)


def _build_query_params(extra: dict[str, str]) -> str:
    """Build URL query string with optional NCBI API key."""
    params = dict(extra)
    api_key = os.environ.get("NCBI_API_KEY")
    if api_key:
        params["api_key"] = api_key
    return urllib.parse.urlencode(params)


def _esearch_live(
    *, issn: str | None = None, journal_name: str | None = None
) -> dict | None:
    """Live NLM Catalog esearch with 1 retry."""
    if issn:
        term = f"{issn}[ISSN]"
    else:
        term = f'"{journal_name}"[Journal]'
    qs = _build_query_params({
        "db": "nlmcatalog",
        "term": term,
        "retmode": "json",
    })
    return _fetch_json(NLM_BASE + "esearch.fcgi?" + qs, label="esearch")


def _esummary_live(nlm_id: str) -> dict | None:
    """Live NLM Catalog esummary with 1 retry."""
    qs = _build_query_params({
        "db": "nlmcatalog",
        "id": nlm_id,
        "retmode": "json",
    })
    return _fetch_json(NLM_BASE + "esummary.fcgi?" + qs, label="esummary")


def _fetch_json(url: str, *, label: str = "") -> dict | None:
    """Generic JSON fetch with 1 retry (graceful on network error)."""
    for attempt in (1, 2):
        try:
            with urllib.request.urlopen(
                url, timeout=TIMEOUT_SECONDS, context=_SSL_CONTEXT,
            ) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, OSError) as e:
            if attempt == 2:
                print(
                    f"WARN: nlm_catalog_check {label} failed: {e}",
                    file=sys.stderr,
                )
                return None
            continue  # retry
    return None
