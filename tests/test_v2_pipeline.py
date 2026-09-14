"""v2 パイプライン (audit.py + pipeline/) のオフライン回帰テスト。"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

import audit
from pipeline import assess, enrich, resolve
from tests.v2_replay import FIX, ReplayClient, replay_patches

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def isolated_home(tmp_path_factory, monkeypatch):
    """実機の ~/.pubmed-reference-resolver.env を読ませない。"""
    monkeypatch.setenv("HOME", str(tmp_path_factory.mktemp("home")))
    # delenv だと元々未設定の場合は何も記録されず、他のテストで setenv された
    # 値がプロセス環境に残っていても検出できない。空値でセットし直すことで
    # _inject_env_kv の「空値は未設定とみなす」契約を使い、確実にリセットする。
    monkeypatch.setenv("NCBI_API_KEY", "")


@pytest.fixture
def replay(monkeypatch):
    captured: dict = {}
    for obj, attr, val in replay_patches(captured):
        monkeypatch.setattr(obj, attr, val)
    return captured


def _run(out: Path, *extra: str) -> int:
    return audit.main(["--structured", str(FIX / "refs.json"), "-o", str(out), "--no-docx",
                        "--no-env-file", *extra])


def _csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_golden_outputs_match_expected(tmp_path, replay):
    out = tmp_path / "out"
    assert _run(out) == 0
    assert (out / "references_pubmed.csv").read_bytes() == \
        (FIX / "expected_references_pubmed.csv").read_bytes()
    assert (out / "references_abstracts.txt").read_text(encoding="utf-8") == \
        (FIX / "expected_references_abstracts.txt").read_text(encoding="utf-8")
    assert json.loads((out / "issues.json").read_text(encoding="utf-8")) == \
        json.loads((FIX / "expected_issues.json").read_text(encoding="utf-8"))
    assert all(c.unrecorded == [] for c in replay["clients"])


def test_retracted_wakefield_is_flagged_major(tmp_path, replay):
    out = tmp_path / "out"
    assert _run(out) == 0
    row = {r["Ref_No"]: r for r in _csv_rows(out / "references_pubmed.csv")}["3"]
    assert row["PMID"] == "9500320"
    assert row["Retraction_Status"] == "RETRACTED"
    issues = json.loads((out / "issues.json").read_text(encoding="utf-8"))["issues"]
    assert any(i["ref_no"] == 3 and i["category"] == "retracted_publication"
               and i["severity"] == "MAJOR" for i in issues)
    assert all(c.unrecorded == [] for c in replay["clients"])


def test_medline_indexed_swallows_unrecorded_request_but_records_it():
    """pipeline/enrich.py の _medline_indexed は例外を握りつぶすため、

    ReplayClient.unrecorded で未記録リクエストを検出できることを保証する回帰テスト
    (この保証がないと、記録漏れが None 判定として静かに通ってしまう)。
    """
    client = ReplayClient({})
    result = enrich._medline_indexed(client, "0140-6736")
    assert result is None
    assert client.unrecorded != []


def test_load_refs_rejects_empty_and_duplicate(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"references": []}), encoding="utf-8")
    with pytest.raises(SystemExit):
        audit.load_refs(empty)
    dup = tmp_path / "dup.json"
    dup.write_text(json.dumps({"references": [{"ref_no": 1}, {"ref_no": 1}]}), encoding="utf-8")
    with pytest.raises(SystemExit):
        audit.load_refs(dup)


def test_load_refs_accepts_bare_list_and_fills_defaults(tmp_path):
    p = tmp_path / "list.json"
    p.write_text(json.dumps([{"claimed_title": "A"}, {"claimed_title": "B"}]), encoding="utf-8")
    refs, meta = audit.load_refs(p)
    assert meta == {}
    assert [r["ref_no"] for r in refs] == [1, 2]
    assert refs[0]["pmid"] is None and refs[0]["is_non_pubmed"] is False


@pytest.mark.parametrize(
    ("medline", "doaj", "path", "expected_risk"),
    [
        (False, False, "L3a", "要確認"),   # 両シグナル陰性 + L3 系 → 要確認
        (False, False, "L1", "低"),        # 識別子直接一致なら立てない
        (False, False, "L2", "低"),
        (True, False, "L3a", "低"),        # MEDLINE 収載
        (False, True, "L3c", "低"),        # DOAJ 収載
        (None, None, "L3a", "未評価"),     # 照会失敗
    ],
)
def test_predatory_requires_composite_signal(medline, doaj, path, expected_risk):
    risk, _ = assess.classify_predatory({}, {"medline_indexed": medline, "doaj_listed": doaj}, path)
    assert risk == expected_risk


def test_predatory_without_journal_info_is_unassessed():
    assert assess.classify_predatory({}, None, "L3a") == ("未評価", "未確認")


def test_offline_reuse_makes_no_network_calls(tmp_path, monkeypatch):
    # pipeline/enrich.py の _medline_indexed / enrich_journals は Exception を
    # 握りつぶすため、AssertionError を投げるだけでは「呼ばれなかった」ことの
    # 証明にならない (未評価への防御的フォールバックと結果的に区別できない)。
    # 呼び出し自体を calls に記録し、テスト末尾で明示的に空であることを確認する。
    calls: list[str] = []

    def no_network(*a, **kw):
        calls.append(repr((a, kw)))
        raise AssertionError("network access during --offline --reuse-resolved")

    class NoNetClient(resolve.PubMedClient):
        _get = no_network

    monkeypatch.setattr(resolve, "PubMedClient", lambda api_key=None, **kw: NoNetClient())
    monkeypatch.setattr(enrich, "_doaj_listed", no_network)
    out = tmp_path / "out"
    assert _run(out, "--reuse-resolved", str(FIX / "resolved.json"), "--offline") == 0
    resolved_rows = [r for r in _csv_rows(out / "references_pubmed.csv") if r["Match_Status"] == "RESOLVED"]
    assert resolved_rows
    assert {r["Predatory_Risk"] for r in resolved_rows} == {"未評価"}
    assert calls == []


def test_env_file_and_no_env_file_are_mutually_exclusive():
    with pytest.raises(SystemExit):
        audit.main(["--structured", str(FIX / "refs.json"),
                    "--env-file", str(FIX / "refs.json"), "--no-env-file"])


def test_symlinked_entrypoint_runs_via_skill_package(tmp_path):
    """spec §11: Claude Code スキルは symlink 経由 (skill_package/audit.py) で起動される。

    リポジトリ直下の audit.py を直接叩くテストだけでは symlink 越しの起動 (sys.path や
    __file__ 解決) を検証できないため、実際の起動経路を subprocess で再現する。
    """
    result = subprocess.run(
        [sys.executable, str(REPO / "skill_package" / "audit.py"),
         "--structured", str(FIX / "refs.json"),
         "--reuse-resolved", str(FIX / "resolved.json"),
         "--offline", "--no-env-file", "--no-docx", "-o", str(tmp_path)],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "references_pubmed.csv").is_file()


@pytest.mark.skipif(shutil.which("node") is None or not (REPO / "node_modules" / "docx").is_dir(),
                    reason="node または npm docx が未導入 (npm ci で導入)")
def test_docx_report_is_generated(tmp_path):
    out = tmp_path / "out"
    rc = audit.main(["--structured", str(FIX / "refs.json"), "-o", str(out),
                     "--reuse-resolved", str(FIX / "resolved.json"), "--offline",
                     "--no-env-file"])
    assert rc == 0
    docx = out / "references_audit_report.docx"
    assert docx.is_file()
    with zipfile.ZipFile(docx) as z:
        assert "word/document.xml" in z.namelist()
