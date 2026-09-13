"""v2 パイプラインのテスト用: NCBI/DOAJ 応答の記録・再生と日付固定。

テストはネットワークに出ない。未記録の NCBI リクエストは ReplayClient.unrecorded に
記録したうえで AssertionError を送出する。ただし pipeline/enrich.py の
_medline_indexed (エンドポイントごとの try/except) と enrich_journals
(呼び出し全体を包む try/except) はいずれも Exception を握りつぶす防御的設計のため、
AssertionError もそこで飲み込まれ呼び出し元まで伝播しない。したがってテストは
戻り値だけで「未記録リクエストがなかった」とは判定できず、client.unrecorded が
空であることを明示的に assert しなければならない。
"""

from __future__ import annotations

import datetime
import json
import types
from pathlib import Path

from pipeline import assess, enrich, resolve

FIX = Path(__file__).resolve().parent / "fixtures" / "v2_synthetic_7refs"

# 最新性評価 (assess.classify_recency) を実行年に依存させない
FROZEN_DATETIME = types.SimpleNamespace(
    date=types.SimpleNamespace(today=lambda: datetime.date(2026, 9, 14))
)


def request_key(endpoint: str, params: dict) -> str:
    """tool / api_key を除いた (endpoint, params) の正規化キー。"""
    p = {k: str(v) for k, v in params.items() if k not in ("tool", "api_key")}
    return json.dumps([endpoint, sorted(p.items())], ensure_ascii=False)


class RecordingClient(resolve.PubMedClient):
    """実通信しつつ応答本文を store に記録する (tools/record_v2_fixture.py 用)。"""

    def __init__(self, store: dict, api_key: str | None = None, **kw):
        super().__init__(api_key=api_key, **kw)
        self.store = store

    def _get(self, endpoint: str, params: dict, retries: int = 3) -> str:
        body = super()._get(endpoint, params, retries)
        self.store[request_key(endpoint, params)] = body
        return body


class ReplayClient(resolve.PubMedClient):
    """記録済み応答だけを返す。throttle・通信なし。

    未記録リクエストは self.unrecorded にキーを積んだうえで AssertionError を
    送出する。pipeline/enrich.py 側で例外が握りつぶされる経路があるため、
    テストは戻り値だけでなく client.unrecorded が空であることを確認すること。
    """

    def __init__(self, responses: dict, api_key: str | None = None, **kw):
        super().__init__(api_key=api_key, **kw)
        self.responses = responses
        self.unrecorded: list[str] = []

    def _get(self, endpoint: str, params: dict, retries: int = 3) -> str:
        key = request_key(endpoint, params)
        if key not in self.responses:
            self.unrecorded.append(key)
            raise AssertionError(f"unrecorded NCBI request: {key}")
        self.n_requests += 1
        return self.responses[key]


def load_json(name: str):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def replay_patches(captured: dict | None = None) -> list[tuple[object, str, object]]:
    """(対象, 属性名, 置換値) の一覧。monkeypatch.setattr / mock.patch.object で適用する。

    captured を渡すと、audit が PubMedClient に渡した api_key を captured["api_key"] に入れる。
    """
    ncbi = load_json("ncbi_responses.json")
    doaj = load_json("doaj_responses.json")

    def client_factory(api_key=None, **kw):
        if captured is not None:
            captured["api_key"] = api_key
        client = ReplayClient(ncbi, api_key=api_key)
        if captured is not None:
            captured.setdefault("clients", []).append(client)
        return client

    return [
        (resolve, "PubMedClient", client_factory),
        (enrich, "_doaj_listed", lambda issn: doaj.get(issn)),
        (enrich.time, "sleep", lambda s: None),
        (assess, "datetime", FROZEN_DATETIME),
    ]
