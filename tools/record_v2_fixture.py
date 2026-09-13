#!/usr/bin/env python3
"""v2 合成 7 件 fixture の NCBI / DOAJ 応答を記録し、期待出力を再生成する。

**実通信あり** (NCBI E-utilities・NLM Catalog・DOAJ。いずれも無料・認証不要)。
API キーは使わない。PubMed 側の書誌更新で期待出力を作り直すときだけ実行する。

    .venv/bin/python tools/record_v2_fixture.py
"""

from __future__ import annotations

import json
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


def _dump(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


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
        rc = audit.main(["--structured", str(FIX / "refs.json"), "-o", tmp, "--no-docx"])
        if rc != 0:
            raise SystemExit(f"recording run failed: rc={rc}")
    _dump(FIX / "ncbi_responses.json", ncbi)
    _dump(FIX / "doaj_responses.json", doaj)
    print(f"recorded {len(ncbi)} NCBI responses, {len(doaj)} DOAJ lookups")


def regenerate_expected() -> None:
    with tempfile.TemporaryDirectory() as tmp, ExitStack() as st:
        for obj, attr, val in replay_patches():
            st.enter_context(mock.patch.object(obj, attr, val))
        rc = audit.main(["--structured", str(FIX / "refs.json"), "-o", tmp, "--no-docx"])
        if rc != 0:
            raise SystemExit(f"replay run failed: rc={rc}")
        out = Path(tmp)
        shutil.copyfile(out / "references_pubmed.csv", FIX / "expected_references_pubmed.csv")
        shutil.copyfile(out / "references_abstracts.txt", FIX / "expected_references_abstracts.txt")
        shutil.copyfile(out / "issues.json", FIX / "expected_issues.json")
        shutil.copyfile(out / "resolved.json", FIX / "resolved.json")
    print("regenerated expected outputs (today fixed to 2026-09-14)")


if __name__ == "__main__":
    record()
    regenerate_expected()
