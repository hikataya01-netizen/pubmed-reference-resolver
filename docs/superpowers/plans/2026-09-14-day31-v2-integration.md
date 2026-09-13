# Day31 v2 正式版統合 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** v2 (`audit.py` + `pipeline/` + `build_docx.js`) を repo root に取り込み、オフラインテスト・env ローダー接続・doctor/CI 対応を加えて、スキルの正式版にする。

**Architecture:** v2 のロジックはスナップショットのまま移設し、`audit.py` にだけ既存 `main.load_env_files` を接続する。テストは NCBI/DOAJ への応答を一度だけ記録した fixture を再生し、ネットワークと API キーなしで回す。

**Tech Stack:** Python 3.11+ (標準ライブラリ + 既存 uv 環境)、pytest、Node.js ≥18 + npm `docx` ^9.7.1、bash (doctor)、GitHub Actions。

**Spec:** `docs/superpowers/specs/2026-09-14-day31-v2-integration-design.md`

## Global Constraints

- リポジトリ: `REPO=/Users/katayamaimac/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver`、ブランチ `feature/day31-v2-integration`
- Python 実行は必ず `$REPO/.venv/bin/python` (または `uv run`)。git commit 時は `PATH="$REPO/.venv/bin:$PATH"` を付ける (pre-commit フックが .venv にある)
- **v2 の判定ロジック・閾値・出力書式は変更しない** (`pipeline/*.py` と `build_docx.js` は無改修)。唯一のロジック変更は `audit.py` の env 接続
- 既存テスト 117 件は常に全件 pass
- テストはネットワーク・API キー不要。未記録リクエストはテスト失敗にする
- コミットメッセージは Conventional Commits + 日本語要約、末尾に `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`
- API キーの値を表示・ログ出力・コミットしない
- push・PR 作成は Task 5 でのみ行う

---

## File Structure

| パス | 責務 | Task |
|---|---|---|
| `audit.py` | v2 エントリポイント (v2/ から移設、Task 3 で env 接続) | 1, 3 |
| `pipeline/{__init__,resolve,enrich,consistency,assess,outputs}.py` | v2 パイプライン (無改修) | 1 |
| `build_docx.js`, `package.json`, `package-lock.json` | Word 出力 (無改修) | 1 |
| `skill_package/{audit.py,pipeline,build_docx.js}` | repo root への symlink | 1 |
| `skill_package/references/{llm_parsing_prompt,pubmed_csv_schema}.md` | v2 版に置換 | 1 |
| `tests/v2_replay.py` | 記録/再生クライアント、patch 一式、固定日付 | 2 |
| `tools/record_v2_fixture.py` | fixture 記録ツール (実通信) | 2 |
| `tests/fixtures/v2_synthetic_7refs/` | refs.json・記録応答・期待出力・resolved.json・README | 1, 2 |
| `tests/test_v2_pipeline.py` | ゴールデン・load_refs・撤回・Predatory・offline・docx | 2 |
| `tests/test_v2_env.py` | env ローダー接続 (RED → GREEN) | 2, 3 |
| `tools/doctor.sh` | Node/docx 診断、v2 オフライン Word 生成確認 | 3 |
| `.github/workflows/tests.yml` | setup-node + npm ci | 3 |
| `skill_package/SKILL.md`, `README.md`, `CLAUDE.md` | v2 正式版の記述 | 4 |
| `docs/sessions/day31/` | セッション記録 | 5 |

---

### Task 1: v2 を repo root へ移設 (無改修の移動)

**Files:**
- Move: `v2/audit.py` → `audit.py`; `v2/pipeline/*.py` → `pipeline/`; `v2/build_docx.js`, `v2/package.json`, `v2/package-lock.json` → root
- Move: `v2/references/llm_parsing_prompt.md`, `v2/references/pubmed_csv_schema.md` → `skill_package/references/` (上書き)
- Move: `v2/examples/expected_output/refs.json` → `tests/fixtures/v2_synthetic_7refs/refs.json`
- Delete: `v2/` の残り (`main.py`, `SKILL.md`, `SNAPSHOT_README.md`, `references/citation_style_examples.md`, `examples/`)
- Create: symlinks `skill_package/audit.py -> ../audit.py`, `skill_package/pipeline -> ../pipeline`, `skill_package/build_docx.js -> ../build_docx.js`
- Modify: `.gitignore` (追加 `node_modules/`)

**Interfaces:**
- Produces: `audit.main(argv: list[str] | None) -> int`、`audit.load_refs(path: Path) -> tuple[list[dict], dict]`、パッケージ `pipeline` (`resolve`, `enrich`, `consistency`, `assess`, `outputs`)

- [ ] **Step 1: 移設前の確認**

`v2/examples/sample_duplicates.txt` と `sample_reference_section.pdf` が `skill_package/examples/` と同一であることは確認済み (削除してよい)。`v2/references/citation_style_examples.md` も `skill_package/references/` と同一。`v2/main.py` は repo の `main.py` の旧フォークなので取り込まない。

```bash
cd "$REPO" && git status --short   # 期待: ?? docs/DEVELOPMENT_NOTES.md のみ
```

- [ ] **Step 2: git mv で移設**

```bash
cd "$REPO"
git mv v2/audit.py audit.py
mkdir -p pipeline && for f in __init__ resolve enrich consistency assess outputs; do git mv v2/pipeline/$f.py pipeline/$f.py; done
git mv v2/build_docx.js build_docx.js
git mv v2/package.json package.json
git mv v2/package-lock.json package-lock.json
git mv -f v2/references/llm_parsing_prompt.md skill_package/references/llm_parsing_prompt.md
git mv -f v2/references/pubmed_csv_schema.md skill_package/references/pubmed_csv_schema.md
mkdir -p tests/fixtures/v2_synthetic_7refs
git mv v2/examples/expected_output/refs.json tests/fixtures/v2_synthetic_7refs/refs.json
git rm -rq v2
ls v2 2>/dev/null; echo "v2 removed"
```

- [ ] **Step 3: symlink と .gitignore**

```bash
cd "$REPO/skill_package" && ln -s ../audit.py audit.py && ln -s ../pipeline pipeline && ln -s ../build_docx.js build_docx.js && cd "$REPO"
printf '\n# Node.js (build_docx.js 用、npm ci で復元)\nnode_modules/\n' >> .gitignore
npm ci
```
Expected: `npm ci` が `node_modules/docx` を導入 (エラーなし)。

- [ ] **Step 4: 動作確認**

```bash
cd / && "$REPO/.venv/bin/python" ~/.claude/skills/pubmed-reference-resolver/audit.py --help | head -3
cd "$REPO" && uv run pytest tests/ -q 2>&1 | tail -1
node -e "require('$REPO/node_modules/docx'); console.log('docx ok')"
```
Expected: `usage: audit.py [-h] --structured STRUCTURED ...` / `117 passed` / `docx ok`

- [ ] **Step 5: Commit**

```bash
cd "$REPO" && git add -A audit.py pipeline build_docx.js package.json package-lock.json skill_package tests/fixtures/v2_synthetic_7refs .gitignore v2
PATH="$REPO/.venv/bin:$PATH" git commit -m "refactor(v2): v2 を repo root へ移設し skill_package から symlink

pipeline/*.py・build_docx.js は無改修。v2/main.py (旧フォーク) は取り込まない。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```
`git status --short` が `?? docs/DEVELOPMENT_NOTES.md` のみであること。

---

### Task 2: 記録/再生 fixture と v2 テスト (RED)

**Files:**
- Create: `tests/v2_replay.py`, `tools/record_v2_fixture.py`, `tests/test_v2_pipeline.py`, `tests/test_v2_env.py`
- Create (記録ツールが生成): `tests/fixtures/v2_synthetic_7refs/{ncbi_responses.json,doaj_responses.json,expected_references_pubmed.csv,expected_references_abstracts.txt,expected_issues.json,resolved.json}`
- Create: `tests/fixtures/v2_synthetic_7refs/README.md`

**Interfaces:**
- Consumes: `audit.main`, `audit.load_refs`, `pipeline.resolve.PubMedClient` (`_get(endpoint: str, params: dict, retries: int = 3) -> str`, 属性 `n_requests`)、`pipeline.enrich._doaj_listed(issn: str) -> bool | None`、`pipeline.assess.classify_predatory(meta, journal_info, resolution_path) -> tuple[str, str]`
- Produces: `tests.v2_replay.FIX: Path`、`request_key(endpoint: str, params: dict) -> str`、`ReplayClient`、`RecordingClient`、`replay_patches(captured: dict | None = None) -> list[tuple[object, str, object]]`、`FROZEN_DATETIME`

- [ ] **Step 1: `tests/v2_replay.py` を作成**

```python
"""v2 パイプラインのテスト用: NCBI/DOAJ 応答の記録・再生と日付固定。

テストはネットワークに出ない。未記録の NCBI リクエストは AssertionError。
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
    """記録済み応答だけを返す。throttle・通信なし。"""

    def __init__(self, responses: dict, api_key: str | None = None, **kw):
        super().__init__(api_key=api_key, **kw)
        self.responses = responses

    def _get(self, endpoint: str, params: dict, retries: int = 3) -> str:
        key = request_key(endpoint, params)
        if key not in self.responses:
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
        return ReplayClient(ncbi, api_key=api_key)

    return [
        (resolve, "PubMedClient", client_factory),
        (enrich, "_doaj_listed", lambda issn: doaj.get(issn)),
        (enrich.time, "sleep", lambda s: None),
        (assess, "datetime", FROZEN_DATETIME),
    ]
```

- [ ] **Step 2: `tools/record_v2_fixture.py` を作成**

```python
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
```

- [ ] **Step 3: 記録ツールを実行 (実通信、ユーザー承認済み)**

`HOME` を空ディレクトリにして、実キーが読まれないようにする。

```bash
cd "$REPO" && HOME="$(mktemp -d)" env -u NCBI_API_KEY .venv/bin/python tools/record_v2_fixture.py
ls tests/fixtures/v2_synthetic_7refs/
grep -c "api_key" tests/fixtures/v2_synthetic_7refs/ncbi_responses.json
```
Expected: `recorded N NCBI responses, 4 DOAJ lookups` (N は 10 前後) / 7 ファイル / `api_key` の出現 0。
期待 CSV の 3 行目 (ref 3) の `Retraction_Status` が `RETRACTED` であることを目視確認:
```bash
.venv/bin/python -c "import csv;r=list(csv.DictReader(open('tests/fixtures/v2_synthetic_7refs/expected_references_pubmed.csv',encoding='utf-8-sig')));print([(x['Ref_No'],x['Match_Status'],x['Retraction_Status']) for x in r])"
```

- [ ] **Step 4: fixture README を作成**

`tests/fixtures/v2_synthetic_7refs/README.md`:
```markdown
# v2_synthetic_7refs

v2 (MacBook Air 版、2026-08-22) に同梱されていた合成テストセット `refs.json` (7 件)。
実在論文の書誌 (PubMed 公開メタデータ) と、意図的に誤った/存在しない参照から成る。

| ref | 内容 |
|---|---|
| 1 | GLOBOCAN 2022 (PMID 38572751) 正常 |
| 2 | ref 1 と同一 DOI (重複引用) |
| 3 | Wakefield 1998 Lancet (PMID 9500320、撤回論文) |
| 4 | 存在しない論文 (UNRESOLVED) |
| 5 | Temel 2010 NEJM (RCT) |
| 6 | Cochrane レビュー (メタ解析/SR) |
| 7 | 書籍 (NON_PUBMED) |

## ファイル

- `ncbi_responses.json` / `doaj_responses.json`: 2026-09-14 に記録した応答 (テストはこれを再生し、通信しない)
- `expected_*`: 再生 + 実行日 2026-09-14 固定で生成した期待出力
- `resolved.json`: `audit.py --reuse-resolved` 用 (doctor のオフライン確認でも使用)

## 再記録 (実通信あり)

    HOME="$(mktemp -d)" env -u NCBI_API_KEY .venv/bin/python tools/record_v2_fixture.py

PubMed 側の書誌更新でゴールデンテストが意図せず変わる場合のみ実行し、差分をレビューしてコミットする。
```

- [ ] **Step 5: `tests/test_v2_pipeline.py` を作成**

```python
"""v2 パイプライン (audit.py + pipeline/) のオフライン回帰テスト。"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

import audit
from pipeline import assess, enrich, resolve
from tests.v2_replay import FIX, replay_patches

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def isolated_home(tmp_path_factory, monkeypatch):
    """実機の ~/.pubmed-reference-resolver.env を読ませない。"""
    monkeypatch.setenv("HOME", str(tmp_path_factory.mktemp("home")))
    monkeypatch.delenv("NCBI_API_KEY", raising=False)


@pytest.fixture
def replay(monkeypatch):
    for obj, attr, val in replay_patches():
        monkeypatch.setattr(obj, attr, val)


def _run(out: Path, *extra: str) -> int:
    return audit.main(["--structured", str(FIX / "refs.json"), "-o", str(out), "--no-docx", *extra])


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


def test_retracted_wakefield_is_flagged_major(tmp_path, replay):
    out = tmp_path / "out"
    assert _run(out) == 0
    row = {r["Ref_No"]: r for r in _csv_rows(out / "references_pubmed.csv")}["3"]
    assert row["PMID"] == "9500320"
    assert row["Retraction_Status"] == "RETRACTED"
    issues = json.loads((out / "issues.json").read_text(encoding="utf-8"))["issues"]
    assert any(i["ref_no"] == 3 and i["category"] == "retracted_publication"
               and i["severity"] == "MAJOR" for i in issues)


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
    def no_network(*a, **kw):
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


@pytest.mark.skipif(shutil.which("node") is None or not (REPO / "node_modules" / "docx").is_dir(),
                    reason="node または npm docx が未導入 (npm ci で導入)")
def test_docx_report_is_generated(tmp_path):
    out = tmp_path / "out"
    rc = audit.main(["--structured", str(FIX / "refs.json"), "-o", str(out),
                     "--reuse-resolved", str(FIX / "resolved.json"), "--offline"])
    assert rc == 0
    docx = out / "references_audit_report.docx"
    assert docx.is_file()
    with zipfile.ZipFile(docx) as z:
        assert "word/document.xml" in z.namelist()
```

- [ ] **Step 6: `tests/test_v2_env.py` を作成**

```python
"""audit.py が ~/.pubmed-reference-resolver.env の NCBI_API_KEY を使うこと (Day31)。"""

from __future__ import annotations

import pytest

import audit
from tests.v2_replay import FIX, replay_patches


@pytest.fixture
def home_with_key(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (home / ".pubmed-reference-resolver.env").write_text("NCBI_API_KEY=ncbi-test-abc123\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("NCBI_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    return home


def _run_capturing(tmp_path, monkeypatch, *extra: str) -> dict:
    captured: dict = {}
    for obj, attr, val in replay_patches(captured):
        monkeypatch.setattr(obj, attr, val)
    rc = audit.main(["--structured", str(FIX / "refs.json"), "-o", str(tmp_path / "out"),
                     "--no-docx", "--offline", *extra])
    assert rc == 0
    return captured


def test_ncbi_key_is_loaded_from_home_env_file(tmp_path, monkeypatch, home_with_key):
    captured = _run_capturing(tmp_path, monkeypatch)
    assert captured["api_key"] == "ncbi-test-abc123"


def test_no_env_file_flag_skips_loading(tmp_path, monkeypatch, home_with_key):
    captured = _run_capturing(tmp_path, monkeypatch, "--no-env-file")
    assert captured["api_key"] is None


def test_explicit_api_key_wins_over_env_file(tmp_path, monkeypatch, home_with_key):
    captured = _run_capturing(tmp_path, monkeypatch, "--api-key", "cli-key-999")
    assert captured["api_key"] == "cli-key-999"
```

- [ ] **Step 7: RED を確認**

```bash
cd "$REPO" && uv run pytest tests/test_v2_pipeline.py -q 2>&1 | tail -2
uv run pytest tests/test_v2_env.py -q 2>&1 | tail -4
uv run pytest tests/ -q 2>&1 | tail -1
```
Expected: `test_v2_pipeline.py` 全 pass (docx テストは node_modules があるので pass) / `test_v2_env.py` は `test_ncbi_key_is_loaded_from_home_env_file` と `test_no_env_file_flag_skips_loading` が FAIL (前者は api_key が None、後者は argparse の unrecognized arguments で SystemExit)、`test_explicit_api_key_wins_over_env_file` は pass / 全体 `2 failed, N passed`。

- [ ] **Step 8: Commit**

```bash
cd "$REPO" && git add tests/v2_replay.py tests/test_v2_pipeline.py tests/test_v2_env.py tools/record_v2_fixture.py tests/fixtures/v2_synthetic_7refs
PATH="$REPO/.venv/bin:$PATH" git commit -m "test(prep): v2 パイプラインの記録再生テストと env 接続テスト (RED)

NCBI/NLM/DOAJ 応答を 2026-09-14 に記録し、オフラインで再生する。
test_v2_env の 2 件は audit.py の env 未接続により失敗する。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```
gitleaks が fixture 内の文字列で誤検知した場合は、値を変えず `.gitleaksignore` に fingerprint と理由を追記する (CLAUDE.md の規約)。

---

### Task 3: audit.py の env 接続・doctor・CI (GREEN)

**Files:**
- Modify: `audit.py` (import 部、`main()` の引数定義と client 生成部)
- Modify: `tools/doctor.sh` (1. Python 環境 / 3. スキル登録 / 4. 動作確認)
- Modify: `.github/workflows/tests.yml` (`test` と `test-experimental` の両ジョブ)

**Interfaces:**
- Consumes: `main.load_env_files(input_path: Path | None) -> list[str]`、`main._parse_env_file(path: Path) -> dict[str, str]`、`main._inject_env_kv(kv: dict[str, str]) -> int`
- Produces: `audit.py` の CLI 追加オプション `--env-file PATH`, `--no-env-file`

- [ ] **Step 1: audit.py の import に env ローダーを追加**

`from pipeline import assess, consistency, enrich, outputs, resolve  # noqa: E402` の直後に:
```python
from main import _inject_env_kv, _parse_env_file, load_env_files  # noqa: E402  (API キー .env ローダー)
```

- [ ] **Step 2: 引数定義を変更**

置換前:
```python
    ap.add_argument("--api-key", default=os.environ.get("NCBI_API_KEY"),
                    help="NCBI API key（任意。あれば 10 req/sec）")
```
置換後:
```python
    ap.add_argument("--api-key", default=None,
                    help="NCBI API key（任意。あれば 10 req/sec。省略時は環境変数 / .env から）")
    ap.add_argument("--env-file", type=Path, default=None,
                    help="明示的な .env ファイル（省略時は ~/.pubmed-reference-resolver.env 等を自動探索）")
    ap.add_argument("--no-env-file", action="store_true",
                    help=".env ファイルを読まない")
```

- [ ] **Step 3: client 生成前に env を読み込む**

置換前:
```python
    client = resolve.PubMedClient(api_key=args.api_key)
```
置換後:
```python
    # .env 読み込み (CLI --api-key と、既に非空で設定済みの環境変数が優先)
    if not args.no_env_file:
        if args.env_file:
            if args.env_file.is_file():
                _inject_env_kv(_parse_env_file(args.env_file))
                print(f"[env] loaded from {args.env_file}")
            else:
                print(f"WARN: --env-file not found: {args.env_file}", file=sys.stderr)
        else:
            for src in load_env_files(args.structured):
                print(f"[env] loaded from {src}")
    api_key = args.api_key or os.environ.get("NCBI_API_KEY") or None

    client = resolve.PubMedClient(api_key=api_key)
```

- [ ] **Step 4: GREEN を確認**

```bash
cd "$REPO" && uv run pytest tests/test_v2_env.py -q 2>&1 | tail -1
uv run pytest tests/ -q 2>&1 | tail -1
cd / && "$REPO/.venv/bin/python" ~/.claude/skills/pubmed-reference-resolver/audit.py --structured "$REPO/tests/fixtures/v2_synthetic_7refs/refs.json" --reuse-resolved "$REPO/tests/fixtures/v2_synthetic_7refs/resolved.json" --offline -o "$(mktemp -d)" 2>&1 | grep -E "^\[env\]|出力①|完了"
```
Expected: `3 passed` / 全件 pass (0 failed) / `[env] loaded from /Users/.../.pubmed-reference-resolver.env (2 vars)`、`[Stage7] 出力① references_audit_report.docx を生成`、`=== 完了`。

- [ ] **Step 5: doctor.sh を拡張**

(a) 「1. Python 環境」の `if [ "$PY_OK" = 1 ]; then missing=...` ブロック内、本体モジュール確認の import 行を置換:
```bash
  if (cd "$REPO" && "$PY" -c 'import main, journal_audit, mdpi_parser, three_class_classifier, crossref_check, nlm_catalog_check, audit; from pipeline import resolve, enrich, consistency, assess, outputs' >/dev/null 2>&1); then
    ok "本体モジュール (v2 audit/pipeline を含む) を読み込み可能"
```

(b) 「1. Python 環境」の uv.lock チェックの直後に Node セクションを追加:
```bash
# --- 1b. Node.js (Word 出力) ---
section "1b. Node.js (Word レポート生成)"
NODE_OK=0
if command -v node >/dev/null 2>&1; then
  node_major="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null)"
  if [ "${node_major:-0}" -ge 18 ] 2>/dev/null; then
    ok "node: $(node -v)"
    if [ -d "$REPO/node_modules/docx" ]; then
      ok "npm docx: $(node -p "require('$REPO/node_modules/docx/package.json').version" 2>/dev/null)"
      NODE_OK=1
    else
      ng "npm docx が未導入" "cd \"$REPO\" && npm ci"
    fi
  else
    ng "node が 18 未満: $(node -v)" "brew upgrade node"
  fi
else
  ng "node が見つからない (Word レポートを生成できない)" "brew install node && cd \"$REPO\" && npm ci"
fi
```

(c) 「3. スキル登録」の必須ファイル一覧を置換:
```bash
for f in SKILL.md audit.py pipeline build_docx.js main.py journal_audit.py mdpi_parser.py manual_overrides.yaml; do
```

(d) 「4. 動作確認」セクション全体を置換:
```bash
# --- 4. 動作確認 (オフライン) ---
section "4. 動作確認 (外部通信なし)"
FIXDIR="$REPO/tests/fixtures/v2_synthetic_7refs"
if [ "$PY_OK" = 1 ] && [ -f "$FIXDIR/refs.json" ] && [ -f "$FIXDIR/resolved.json" ]; then
  tmp="$(mktemp -d)"
  docx_flag=""
  [ "$NODE_OK" = 1 ] || docx_flag="--no-docx"
  if (cd / && "$PY" "$REPO/audit.py" --structured "$FIXDIR/refs.json" --reuse-resolved "$FIXDIR/resolved.json" \
        --offline --no-env-file $docx_flag -o "$tmp" >"$tmp/log.txt" 2>&1) \
     && [ -s "$tmp/references_pubmed.csv" ]; then
    if [ "$NODE_OK" = 1 ]; then
      if [ -s "$tmp/references_audit_report.docx" ]; then
        ok "v2 audit.py: CSV・abstract・Word レポートを生成"
      else
        ng "v2 audit.py: Word レポートが生成されない" "ログ: $tmp/log.txt"; tmp=""
      fi
    else
      warn "v2 audit.py: CSV・abstract のみ生成 (Word は Node.js 未整備のためスキップ)"
    fi
  else
    ng "v2 audit.py の実行に失敗" "ログ: $tmp/log.txt"; tmp=""
  fi
  [ -n "$tmp" ] && rm -rf "$tmp"
else
  warn "v2 動作確認をスキップ (.venv または fixture が無い)"
fi

SAMPLE="$REPO/skill_package/examples/sample_reference_section.pdf"
if [ "$PY_OK" = 1 ] && [ -f "$SAMPLE" ]; then
  tmp="$(mktemp -d)"
  if (cd / && "$PY" "$REPO/main.py" "$SAMPLE" -o "$tmp" --phase 1 --no-env-file --quiet >"$tmp/log.txt" 2>&1) \
     && [ -s "$tmp/phase1_intermediate.json" ]; then
    ok "参照文献の抽出 (main.py Phase 1、Stage 1-2 用) に成功"
  else
    ng "サンプル PDF の抽出に失敗" "ログ: $tmp/log.txt"; tmp=""
  fi
  [ -n "$tmp" ] && rm -rf "$tmp"
fi
```

(e) 5. 外部 API 疎通に DOAJ を追加 (Anthropic の行の直前):
```bash
  probe "DOAJ (v2 収載状況)" "https://doaj.org/api/search/journals/issn%3A0140-6736" 2xx
```
Anthropic の行のラベルを `"Anthropic API (旧版 main.py Phase 2 のみ、到達性のみ)"` に変更。

- [ ] **Step 6: doctor を検証**

```bash
cd "$REPO" && bash -n tools/doctor.sh && tools/doctor.sh --offline; echo "exit=$?"
H="$(mktemp -d)"; HOME="$H" tools/doctor.sh --offline >/dev/null; echo "fresh exit=$?"
mv node_modules node_modules.bak && tools/doctor.sh --offline | sed -n '/1b\./,/2\./p'; mv node_modules.bak node_modules
```
Expected: 全項目 ✔・exit=0 / fresh exit=1 / node_modules 退避時は「npm docx が未導入」✘ と `npm ci` の案内、4 で「CSV・abstract のみ生成」⚠。

- [ ] **Step 7: CI に Node を追加**

`.github/workflows/tests.yml` の `test` と `test-experimental` の両ジョブで、`- run: uv sync --frozen --group dev` の直前に:
```yaml
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: npm
      - run: npm ci
```

- [ ] **Step 8: Commit**

```bash
cd "$REPO" && git add audit.py tools/doctor.sh .github/workflows/tests.yml
PATH="$REPO/.venv/bin:$PATH" git commit -m "feat(v2): audit.py を API キー .env ローダーに接続し doctor・CI を v2 対応

- audit.py: ~/.pubmed-reference-resolver.env 等から NCBI_API_KEY を読む (--env-file / --no-env-file)
- doctor.sh: Node.js・npm docx 診断、v2 のオフライン Word 生成確認、DOAJ 疎通
- CI: setup-node + npm ci (Word 生成テストを CI でも実行)

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: SKILL.md・README・CLAUDE.md を v2 正式版に

**Files:**
- Modify: `skill_package/SKILL.md` (全面書き直し、v2 SKILL.md を土台に)
- Modify: `README.md`, `CLAUDE.md`

**Interfaces:**
- Consumes: Task 1-3 の CLI (`audit.py --structured --reuse-resolved --claim-support --offline --no-docx --env-file --no-env-file`)、出力名 `references_audit_report.docx` / `references_pubmed.csv` / `references_abstracts.txt` / 補助 `resolved.json` / `issues.json` / `report_data.json`
- 土台: `git show 533786d:v2/SKILL.md`

- [ ] **Step 1: SKILL.md を書き直す**

`git show 533786d:v2/SKILL.md > /tmp/v2_skill.md` を土台に、以下を行う。

1. frontmatter `description` を 1,000 字未満に短縮。必須で含める語: References の PubMed 逆引き / Word・CSV・abstract の 3 出力 / 実在性・書誌正確性・重複・撤回論文 / 原著性・エビデンス水準・最新性・Predatory リスク・主張支持性 / 捏造引用検出 / トリガー例 6 個程度 (「参照文献をPubMedで逆引きして」「Referencesを検証して」「撤回論文が含まれていないか」「捏造引用かチェックして」「Predatory Journalでないか」「引用の主張を論文が支持しているか」) / 和文文献は対象外
2. 冒頭の「本 SKILL.md がパイプライン仕様の正本」注記から「旧版 main.py…残置」を次に置換: 「旧版 `main.py` の Phase 2〜4 (パイプライン内 Anthropic API 呼出・`report.md` 出力) は非推奨。Stage 1-2 (抽出・行番号除去・分割) のみ利用する。」
3. 「実行方法」の前に次の節を追加:

````markdown
## 配置と実行環境 (最初に確認)

```bash
REPO="$(cd -P ~/.claude/skills/pubmed-reference-resolver/.. && pwd)"
PY="$REPO/.venv/bin/python"
```

- `~/.claude/skills/pubmed-reference-resolver` は `$REPO/skill_package/` への symlink。`audit.py`・`pipeline`・`build_docx.js` は `$REPO` 直下への symlink。
- **初回・別のパソコン・エラー時は `"$REPO/tools/doctor.sh"` を実行**し、✘ を → の手順で解消してから進む (キーの値を表示・入力しない)。
- Python は `$PY` を使う。Word 出力には Node.js と `$REPO/node_modules/docx` が必要 (無ければ `cd "$REPO" && npm ci`)。
- `NCBI_API_KEY` (任意) は `~/.pubmed-reference-resolver.env` (chmod 600) に置けば自動で読み込まれる (`[env] loaded from ...`)。v2 は Anthropic API キーを使わない。
````

4. 「実行方法」のコマンドをすべて `"$PY" "$REPO/audit.py" ...` に置換。`python3 audit.py` を残さない。CLI オプション表に `--env-file PATH` と `--no-env-file` を追加
5. 「実行方法」の最初に Stage 1-2 の手順を追加:

````markdown
### 手順

1. **参照文献を読む**: 入力が PDF / DOCX の場合、行番号の混入や改行分断を避けるため、まず抽出する (API 不使用・通信なし)。
   ```bash
   "$PY" "$REPO/main.py" INPUT.pdf --phase 1 --no-env-file -o OUT_DIR/extract
   ```
   `OUT_DIR/extract/phase1_intermediate.json` の参照ブロック (行番号除去・分割済み) を読む。TXT や短いリストは Read で直接読んでよい。
2. **構造化**: `references/llm_parsing_prompt.md` に従い、参照ごとに `refs.json` を書く (本文があれば `citation_contexts` も)。
3. **実行**: 下記コマンドで 3 出力を生成する。`-o` は論文ごとに別フォルダにする (既存ファイルは上書きされる)。
4. **報告**: `references_audit_report.docx` の §1 ダッシュボード・§3 要確認項目・§5 文献評価サマリを要約し、`[self-check]` の注記を必ず伝える。撤回論文・Predatory リスクは断定表現を避ける。
````

6. 「移行元プロジェクトについて」節を削除
7. 「ファイル構成」節を次に置換:

````markdown
## ファイル構成 ($REPO)

```
audit.py                 ← 正規エントリポイント
pipeline/                ← resolve / enrich / consistency / assess / outputs
build_docx.js            ← 出力① (docx-js)。package.json / package-lock.json、node_modules は npm ci
main.py                  ← 旧版。Stage 1-2 (抽出) のみ利用、Phase 2-4 は非推奨
tools/doctor.sh          ← 環境診断
tests/fixtures/v2_synthetic_7refs/ ← v2 回帰テスト用の合成 7 件と記録応答
```
````

8. 「非対応」に「PDF/DOCX から refs.json への自動変換 (Day32 予定)」「Crossref による未解決文献の 3 分類 (旧版にあり、v2 への統合は Day33 予定)」を追加

- [ ] **Step 2: SKILL.md を検証**

```bash
cd "$REPO" && awk '/^---/{c++; if(c==2) exit} c==1' skill_package/SKILL.md | wc -m
grep -n "python3 \|/Users/\|katayama\|Antigravity" skill_package/SKILL.md
REPO_T="$(cd -P ~/.claude/skills/pubmed-reference-resolver/.. && pwd)"; PY="$REPO_T/.venv/bin/python"; T="$(mktemp -d)"
cd / && "$PY" "$REPO_T/main.py" "$REPO_T/skill_package/examples/sample_reference_section.pdf" --phase 1 --no-env-file -o "$T/extract" >/dev/null && ls "$T/extract/phase1_intermediate.json"
```
Expected: frontmatter 1,000 字未満 / grep ヒットなし / `phase1_intermediate.json` が存在。

- [ ] **Step 3: README.md を更新**

1. 冒頭の説明文を v2 に: 「PubMed で逆引きし、Word 監査レポート・PubMed 互換 CSV (29 列)・abstract 集の 3 ファイルを生成。実在性・書誌正確性・重複・撤回論文を検証し、原著性・エビデンス水準・最新性・Predatory リスク・主張支持性を評価する。」
2. 「主な機能」に撤回論文検出・文献評価 5 基準・Word 出力を追加し、「MDPI 形式は決定論的 fast-path」「引用ジャーナル名と DOI の不整合を MAJOR/WARN/INFO」は「旧版 (main.py)」の小見出しの下へ移す
3. 「インストール」の `uv sync` の後に `npm ci   # Word レポート生成用 (Node.js 18+)` を追加
4. 「使用方法」を v2 に置換: `refs.json` の用意 (SKILL.md 参照) → `uv run python audit.py --structured refs.json -o out/`、出力ファイル 3 本 + 補助 JSON、`--offline` / `--reuse-resolved` / `--claim-support` の 1 行説明。旧版の `main.py` 実行例は「### 旧版 (非推奨)」へ
5. テスト件数を Task 3 Step 4 の実数に更新
6. プロジェクト構成に `audit.py`・`pipeline/`・`build_docx.js`・`package.json`・`tests/v2_replay.py`・`tools/record_v2_fixture.py` を追加

- [ ] **Step 4: CLAUDE.md を更新**

1. 「What this project is」: 出力を Word/CSV/abstract の 3 本 (v2) に、旧版 `report.md` は legacy と明記
2. 「Commands」: `npm ci` と `uv run python audit.py --structured refs.json -o out/` を追加、テスト件数を実数に、旧 `main.py` 実行例に `# legacy` コメント
3. 「Architecture」の先頭に v2 節を追加 (audit.py の Stage 3 外部注入 → Stage 4 `pipeline/resolve.py` L1〜L3d → 5.5 `enrich.py` → 6 `consistency.py` 19 カテゴリ → 6.5 `assess.py` → 7 `outputs.py` + `build_docx.js` → 8 `self_check`)。既存の main.py 記述は「Legacy pipeline (main.py)」見出しの下へ
4. テスト方針: v2 テストは `tests/v2_replay.py` の記録応答再生、再記録は `tools/record_v2_fixture.py` (実通信) と追記
5. 既知の誤りを修正:
   - Output files: `pubmed_csv-*.csv` → 旧版は `csv-{first_pmid}-set.csv` / `abstract-{first_pmid}-set.txt`
   - **`skill_package/` is a mirror** 節: 「byte-identical copies」→「repo root への symlink (`main.py`, `mdpi_parser.py`, `journal_audit.py`, `audit.py`, `pipeline`, `build_docx.js`, `manual_overrides.yaml`)。root を編集すれば反映される」
   - Secrets 節の探索順: 「`--env-file` 明示 > (自動探索) main.py 実体ディレクトリ `.env` > `$HOME/.pubmed-reference-resolver.env` > cwd `.env` > 入力ファイルのディレクトリ `.env`。既に非空で設定済みの環境変数は上書きしない」。推奨は `~/.pubmed-reference-resolver.env`

- [ ] **Step 5: 全体確認と Commit**

```bash
cd "$REPO" && uv run pytest tests/ -q 2>&1 | tail -1 && tools/doctor.sh --offline | tail -1
git add skill_package/SKILL.md README.md CLAUDE.md
PATH="$REPO/.venv/bin:$PATH" git commit -m "docs(skill): SKILL.md・README・CLAUDE.md を v2 正式版に更新

旧版 main.py は Stage 1-2 抽出のみ利用 (Phase 2-4 は非推奨) と明記。
CLAUDE.md の env 探索順・出力ファイル名・skill_package (symlink) の誤りを修正。

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: セッション記録・push・PR (コントローラーが実施)

**Files:**
- Create: `docs/sessions/day31/README.md`, `docs/sessions/day31/DAY31_LESSONS_LEARNED.md`

- [ ] **Step 1: 記録作成** — `docs/sessions/day30/` の形式に倣い、コミットチェーン (spec → plan → refactor → test(prep) RED → feat GREEN → docs → archive)、検証結果 (テスト件数、doctor、symlink 経由実行)、学び (v2 が git 管理外で PC 間に分岐していた経緯、iCloud 同期下の repo のリスク、記録再生テストの設計) を書く
- [ ] **Step 2: Commit** `docs(sessions): archive day31 v2 正式版統合`
- [ ] **Step 3: push と PR** — `git push -u origin feature/day31-v2-integration`、`gh pr create --base main` (本文末尾に `🤖 Generated with [Claude Code](https://claude.com/claude-code)`)。CI の結果を確認
- [ ] **Step 4: MacBook Air の手順をユーザーに案内** — PR マージ後 `cd ~/repos/pubmed-reference-resolver && git pull && uv sync --frozen && npm ci && tools/doctor.sh`
