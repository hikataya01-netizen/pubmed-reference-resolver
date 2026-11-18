"""NCBI esearch 障害時の挙動テスト（ネットワーク不要）。

実行: uv run pytest tests/test_resolve_fallback.py -q

NCBI esearch が検索障害（HTTP 5xx 継続・HTTP 200 + ERROR 応答・非 JSON）のとき、
「ヒットなし」と取り違えず、Europe PMC へ自動フォールバックすることを確かめる。
設計と経緯は pubmed-reference-resolver-v2 の docs/superpowers/specs（同じ修正を先に入れたリポジトリ）を参照。
"""
import json
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import resolve  # noqa: E402
from pipeline.resolve import PubMedClient, SearchBackendError  # noqa: E402


def make_client() -> PubMedClient:
    c = PubMedClient()
    c.min_interval = 0  # テストを待たせない
    return c


class EsearchErrorDetection(unittest.TestCase):
    def test_200_with_error_raises_instead_of_empty(self):
        body = json.dumps({"esearchresult": {"ERROR": "Search Backend failed: ..."}})
        c = make_client()
        with mock.patch.object(c, "_get", return_value=body):
            with self.assertRaises(SearchBackendError):
                c.esearch("x[DOI]")

    def test_http_500_exhausted_raises_backend_error(self):
        c = make_client()
        with mock.patch.object(c, "_get", side_effect=RuntimeError("500")):
            with self.assertRaises(SearchBackendError):
                c.esearch("x[DOI]")

    def test_non_json_raises(self):
        c = make_client()
        with mock.patch.object(c, "_get", return_value="<html>oops</html>"):
            with self.assertRaises(SearchBackendError):
                c.esearch("x[DOI]")

    def test_genuine_zero_hits_is_empty_list_not_error(self):
        body = json.dumps({"esearchresult": {"count": "0", "idlist": []}})
        c = make_client()
        with mock.patch.object(c, "_get", return_value=body):
            self.assertEqual(c.esearch("x[DOI]"), [])

    def test_hits_returned(self):
        body = json.dumps({"esearchresult": {"idlist": ["123", "456"]}})
        c = make_client()
        with mock.patch.object(c, "_get", return_value=body):
            self.assertEqual(c.esearch("x[DOI]"), ["123", "456"])


class FallbackBehaviour(unittest.TestCase):
    def test_falls_back_to_europepmc_and_counts(self):
        c = make_client()
        with mock.patch.object(c, "esearch", side_effect=SearchBackendError("down")), \
             mock.patch.object(c, "epmc_search", return_value=["26977696"]) as ep:
            ids, via = c.search("t", 'DOI:"d"')
        self.assertEqual((ids, via), (["26977696"], "europepmc"))
        ep.assert_called_once_with('DOI:"d"', 5)
        self.assertEqual(c.n_fallback, 1)
        self.assertTrue(c.esearch_is_down())

    def test_cooldown_skips_ncbi_on_subsequent_calls(self):
        c = make_client()
        with mock.patch.object(c, "esearch", side_effect=SearchBackendError("down")) as es, \
             mock.patch.object(c, "epmc_search", return_value=["1"]):
            c.search("t1", "q1")
            c.search("t2", "q2")
        self.assertEqual(es.call_count, 1)  # 2 回目は NCBI を試さない
        self.assertEqual(c.n_fallback, 2)

    def test_ncbi_retried_after_cooldown_expires(self):
        c = make_client()
        with mock.patch.object(c, "esearch", side_effect=SearchBackendError("down")), \
             mock.patch.object(c, "epmc_search", return_value=["1"]):
            c.search("t", "q")
        c._esearch_down_until = time.time() - 1  # クールダウン経過
        with mock.patch.object(c, "esearch", return_value=["9"]) as es:
            ids, via = c.search("t", "q")
        self.assertEqual((ids, via), (["9"], "ncbi"))
        es.assert_called_once()

    def test_no_fallback_query_propagates_error(self):
        c = make_client()
        with mock.patch.object(c, "esearch", side_effect=SearchBackendError("down")):
            with self.assertRaises(SearchBackendError):
                c.search("t", None)

    def test_both_down_raises(self):
        c = make_client()
        with mock.patch.object(c, "esearch", side_effect=SearchBackendError("down")), \
             mock.patch.object(c, "epmc_search", side_effect=RuntimeError("both down")):
            with self.assertRaises(RuntimeError):
                c.search("t", "q")

    def test_healthy_ncbi_never_touches_europepmc(self):
        c = make_client()
        with mock.patch.object(c, "esearch", return_value=["7"]), \
             mock.patch.object(c, "epmc_search") as ep:
            ids, via = c.search("t", "q")
        self.assertEqual((ids, via), (["7"], "ncbi"))
        ep.assert_not_called()
        self.assertEqual(c.n_fallback, 0)


class EndToEndResolveUnderOutage(unittest.TestCase):
    """esearch 全面停止でも DOI 参照が RESOLVED になり、unresolved 誤判定にならない。"""

    def test_doi_ref_resolved_via_fallback(self):
        meta = {"pmid": "26977696", "title": "CDC Guideline for Prescribing Opioids for "
                "Chronic Pain-United States, 2016.", "first_author": "Dowell D",
                "authors": ["Dowell D"], "doi": "10.1001/jama.2016.1464"}
        c = make_client()
        refs = [{"ref_no": 1, "pmid": None, "doi": "10.1001/jama.2016.1464",
                 "claimed_first_author": "Dowell D", "claimed_year": 2016,
                 "claimed_journal": "JAMA", "claimed_title": meta["title"],
                 "is_non_pubmed": False}]
        with mock.patch.object(c, "esearch", side_effect=SearchBackendError("down")), \
             mock.patch.object(c, "epmc_search", return_value=["26977696"]), \
             mock.patch.object(c, "efetch_many", return_value={"26977696": meta}):
            out = resolve.resolve_all(refs, c, verbose=False)
        self.assertEqual(out[0]["match_status"], "RESOLVED")
        self.assertEqual(out[0]["resolution_path"], "L2")
        self.assertIn("Europe PMC", out[0]["attempts"][0]["query"])

    def test_l3_fallback_still_rejected_by_double_guard(self):
        """フォールバック経由でも誤マッチガード（類似度+筆頭著者）は有効。"""
        wrong = {"pmid": "111", "title": "Unrelated forensic study of something else",
                 "first_author": "Smith J", "authors": ["Smith J"]}
        c = make_client()
        refs = [{"ref_no": 1, "pmid": None, "doi": None,
                 "claimed_first_author": "Nonexistent A", "claimed_year": 2023,
                 "claimed_journal": "J Fabricated Medicine",
                 "claimed_title": "A completely fabricated citation that should never resolve",
                 "is_non_pubmed": False}]
        with mock.patch.object(c, "esearch", side_effect=SearchBackendError("down")), \
             mock.patch.object(c, "epmc_search", return_value=["111"]), \
             mock.patch.object(c, "efetch_many", return_value={"111": wrong}):
            out = resolve.resolve_all(refs, c, verbose=False)
        self.assertEqual(out[0]["match_status"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
