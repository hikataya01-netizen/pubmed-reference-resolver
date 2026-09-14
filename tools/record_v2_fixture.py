#!/usr/bin/env python3
"""v2 合成 7 件 fixture の NCBI / DOAJ 応答を記録し、期待出力を再生成する。

**実通信あり** (NCBI E-utilities・NLM Catalog・DOAJ。いずれも無料・認証不要)。
API キーは使わない。PubMed 側の書誌更新で期待出力を作り直すときだけ実行する。

    .venv/bin/python tools/record_v2_fixture.py

efetch (`efetch.fcgi`) 応答中の `<AbstractText>` 本文は、書誌メタデータと異なり
出版社 (Lancet/NEJM/Cochrane 等、非 OA) の著作物であるため、本リポジトリが公開
であることを踏まえてプレースホルダに置換して記録する (`sanitize_efetch_xml`)。
既存の記録済み fixture を再取得なしでサニタイズし直したいだけなら:

    HOME="$(mktemp -d)" env -u NCBI_API_KEY .venv/bin/python tools/record_v2_fixture.py --sanitize-only
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from contextlib import ExitStack
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import audit  # noqa: E402
from pipeline import enrich, resolve  # noqa: E402
from tests.v2_replay import FIX, RecordingClient, replay_patches  # noqa: E402

_ABSTRACT_TEXT_RE = re.compile(r"(<AbstractText\b[^>]*>).*?(</AbstractText>)", re.DOTALL)
_PLACEHOLDER = "[abstract omitted from fixture: publisher text]"


def _dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def sanitize_efetch_xml(body: str) -> str:
    """efetch 応答 XML の `<AbstractText ...>...</AbstractText>` 本文をプレースホルダに置換する。

    属性 (Label="BACKGROUND" 等) は保持し、要素の存在自体はテストの検証対象
    (`AbstractText` の有無・撤回検出など) を壊さないよう残す。非貪欲・DOTALL で
    複数行にまたがる本文にも対応する。
    """
    return _ABSTRACT_TEXT_RE.sub(rf"\1{_PLACEHOLDER}\2", body)


def _is_efetch_key(key: str) -> bool:
    """request_key() が生成した `[endpoint, [[k, v], ...]]` 形式のキーから endpoint を判定する。"""
    try:
        endpoint = json.loads(key)[0]
    except (ValueError, TypeError, IndexError):
        return False
    return endpoint == "efetch.fcgi"


def sanitize_ncbi_responses(ncbi: dict[str, str]) -> dict[str, str]:
    return {k: (sanitize_efetch_xml(v) if _is_efetch_key(k) else v) for k, v in ncbi.items()}


def record() -> None:
    ncbi: dict[str, str] = {}
    doaj: dict[str, bool | None] = {}
    real_doaj = enrich._doaj_listed

    def doaj_rec(issn: str):
        doaj[issn] = real_doaj(issn)
        return doaj[issn]

    with tempfile.TemporaryDirectory() as tmp, ExitStack() as st:
        st.enter_context(mock.patch.object(
            resolve, "PubMedClient", lambda api_key=None, **kw: RecordingClient(ncbi)))
        st.enter_context(mock.patch.object(enrich, "_doaj_listed", doaj_rec))
        rc = audit.main(["--structured", str(FIX / "refs.json"), "-o", tmp, "--no-docx", "--no-env-file"])
        if rc != 0:
            raise SystemExit(f"recording run failed: rc={rc}")
    _dump(FIX / "ncbi_responses.json", sanitize_ncbi_responses(ncbi))
    _dump(FIX / "doaj_responses.json", doaj)
    print(f"recorded {len(ncbi)} NCBI responses, {len(doaj)} DOAJ lookups (abstracts sanitized)")


def sanitize_only() -> None:
    """既存の ncbi_responses.json をサニタイズし直し、期待出力を再生成する (実通信なし)。"""
    ncbi = json.loads((FIX / "ncbi_responses.json").read_text(encoding="utf-8"))
    _dump(FIX / "ncbi_responses.json", sanitize_ncbi_responses(ncbi))
    regenerate_expected()


def regenerate_expected() -> None:
    captured: dict = {}
    with tempfile.TemporaryDirectory() as tmp, ExitStack() as st:
        for obj, attr, val in replay_patches(captured):
            st.enter_context(mock.patch.object(obj, attr, val))
        rc = audit.main(["--structured", str(FIX / "refs.json"), "-o", tmp, "--no-docx", "--no-env-file"])
        if rc != 0:
            raise SystemExit(f"replay run failed: rc={rc}")
        unrecorded = [k for c in captured.get("clients", []) for k in c.unrecorded]
        if unrecorded:
            raise SystemExit(f"unrecorded NCBI requests during replay: {unrecorded}")
        out = Path(tmp)
        shutil.copyfile(out / "references_pubmed.csv", FIX / "expected_references_pubmed.csv")
        shutil.copyfile(out / "references_abstracts.txt", FIX / "expected_references_abstracts.txt")
        shutil.copyfile(out / "issues.json", FIX / "expected_issues.json")
        shutil.copyfile(out / "resolved.json", FIX / "resolved.json")
    print("regenerated expected outputs (today fixed to 2026-09-14)")


if __name__ == "__main__":
    if "--sanitize-only" in sys.argv[1:]:
        sanitize_only()
    else:
        record()
        regenerate_expected()
