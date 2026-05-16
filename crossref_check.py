"""crossref_check — Crossref API client for DOI existence verification.

Day15 SPEC §3.3 で定義された module. Day13 INVESTIGATION で発見した
「PubMed 未ヒット 3 分類」の判定 (`three_class_classifier.py` で統合) に
おいて、A 分類 (真の捏造) vs B/C 分類 (実在論文) の決定的な判定根拠を
提供する.

依存: 標準ライブラリのみ (urllib, json) — 追加依存なし.

Usage:
    from pathlib import Path
    import crossref_check

    # production (live API):
    result = crossref_check.check_doi_exists("10.1037/1091-7527.21.3.245")

    # test (fixture 経由):
    result = crossref_check.check_doi_exists(
        "10.1037/1091-7527.21.3.245",
        fixture_path=Path("tests/fixtures/.../expected_crossref_*.json"),
    )

Returns:
    {
        "exists": True | False | None,  # None = unknown (graceful, network エラー等)
        "metadata": dict | None,         # journal/title/authors 等 (実在時)
        "error": str | None,             # network エラー等のメッセージ
    }

Day15 SPEC §3.3 (signature) + §Q4 (graceful unknown on network error,
timeout 10s, retry 1 回, stderr WARN) に準拠.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

CROSSREF_BASE = "https://api.crossref.org/works/"
TIMEOUT_SECONDS = 10
USER_AGENT = "pubmed-reference-resolver Day15 three_class_audit"


def _result(
    exists: bool | None,
    metadata: dict | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Standard return shape."""
    return {"exists": exists, "metadata": metadata, "error": error}


def check_doi_exists(
    doi: str,
    *,
    fixture_path: Path | None = None,
) -> dict[str, Any]:
    """Crossref API で DOI 実在確認.

    Args:
        doi: 検査対象 DOI (例: "10.1037/1091-7527.21.3.245")
        fixture_path: 指定時は live API call せず fixture file から JSON 読出
                      (test 用)

    Returns:
        標準 dict shape (上記 Usage 参照)
    """
    if fixture_path is not None:
        try:
            data = json.loads(fixture_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            return _result(None, error=f"fixture read failed: {e}")
    else:
        data = _fetch_live(doi)
        if data is None:
            return _result(None, error="network failed (after 1 retry)")
        if isinstance(data, dict) and data.get("_http_status") == 404:
            return _result(False)
        if isinstance(data, dict) and data.get("_http_status") not in (None, 200):
            return _result(None, error=f"HTTP {data.get('_http_status')}")

    # Parse response (live or fixture, post-parse shape は同一)
    if data.get("status") == "ok":
        return _result(True, metadata=data.get("message"))
    if data.get("status") == "error":
        return _result(False)
    return _result(None, error="unexpected response shape")


def _fetch_live(doi: str) -> dict | None:
    """Live Crossref fetch with 1 retry (graceful on network error).

    Returns:
        - dict (parsed JSON): success
        - {"_http_status": code}: HTTP error (404 など)
        - None: network failed after retry
    """
    url = CROSSREF_BASE + urllib.parse.quote(doi, safe="/")
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return {"_http_status": e.code}
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == 2:
                print(
                    f"WARN: crossref_check.check_doi_exists failed for "
                    f"DOI={doi!r}: {e}",
                    file=sys.stderr,
                )
                return None
            continue  # retry
    return None
