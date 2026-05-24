# SPEC: Day24 — 5 skip-mark test の mdpi_173refs 復元 (構造化 refactor)

**作成日**: 2026-05-24 (Day24 brainstorming 完了時)
**著者**: Claude Code (Opus 4.7 / 1M context) / 承認: 片山英樹
**位置付け**: Day23 Phase 1 で mdpi_149refs cross-fixture coupling 回避のため `pytestmark = pytest.mark.skip(reason="awaiting Day23 Phase 5 new MDPI fixture")` を付与した 5 test file を、新 fixture `mdpi_173refs/` に re-point し、byte-level golden 前提を構造化 test に refactor して skip 解除する作業
**前提**: Day23 末 (HEAD `3313cab`、README fixup 含む) で main branch、52 passed / 50 skipped / 0 failed、repo PUBLIC、CI green、v0.1.0 release accessible

---

## 1. 背景と目的

### 1.1 検出事象

Day23 Phase 1 (commit `3c676ec`) で旧 `tests/fixtures/mdpi_149refs/` 削除を実行する際、5 test file が hard-code 参照しているため PLAN gap として inline detect → Pattern A (skip-mark) で対応:

| File | 旧 path 依存 |
|:---|:---|
| `tests/test_mdpi_parser.py` | `expected_phase2_structured.json` で MDPI parser byte-match |
| `tests/test_overrides_contract.py` | `ref141_parser_snapshot.json` で manual override Ref #141 検証 |
| `tests/test_journal_audit.py` | `expected_report.md` narrative section byte-match |
| `tests/test_pre_integration_baseline.py` | `expected_phase2_structured.json` + `expected_phase3_resolved.json` で integration 前状態 characterize |
| `tests/test_split_references_doi_boundary.py` | corpus docx 入力で DOI boundary parser test |

Day23 Phase 5 で新 `mdpi_173refs/` 構築済 (PMC13164670 Nutrients review)。Day24 でこの 5 file を新 fixture に re-point して skip 解除する。

### 1.2 旧 vs 新 fixture の semantic 不一致

| 観点 | 旧 mdpi_149refs | 新 mdpi_173refs |
|:---|:---|:---|
| Provenance | (Day23 で機密性懸念により削除済) | PMC13164670 Nutrients review 2026 (CC BY 4.0) |
| 処理 path | MDPI fast-path (LLM 不使用、決定論的) | LLM path (author 形式が fast-path 条件未満) |
| 同梱 file | `expected_phase2_structured.json` / `expected_phase3_resolved.json` / `expected_report.md` / `expected_journal_audit.json` / `ref141_parser_snapshot.json` (全 deterministic golden) | `expected_phase1_intermediate.json` (parser-only deterministic) + `baseline_phase3_resolved.json` / `baseline_report.md` / `baseline_three_class_classification.json` (LLM 経由のため variability あり) |
| corpus-specific feature | Ref #141 manual override 等 | (manual_overrides.yaml 未対応、別 task) |

→ 5 test の旧 byte-level assertion は新 fixture では原理的に再現不能、**構造化 test に refactor 必須**。

### 1.3 目的

1. **5 file の skip 解除**: Day23 で意図的に skip-mark した 5 file を再活性化、regression coverage 回復
2. **構造化 test への refactor**: byte-level golden 依存を廃し、ref count range・field presence・YAML schema 等の構造 invariant で regression を検出
3. **Day23 で破壊した coverage を回復**: 50 skipped → ≤1 skipped、52 passed → ~100-102 passed
4. **history readability**: 1 atomic commit `test(refactor): re-point 5 mdpi-dependent tests to mdpi_173refs (Day24)` で Day23 skip-mark commit `3c676ec` と対称な構造

### 1.4 設計判断の経緯 (brainstorming 質問)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | byte-level expected_* golden への対応 | **(α) 構造 test に軽量リファクタリング** |
| Q2 | commit 粒度 | **(α) 1 atomic commit に集約** |

---

## 2. Architecture & per-file refactor 戦略

### 2.1 改変対象 (5 test file)

| File | 種別 | 改変内容 |
|:---|:---|:---|
| `tests/test_mdpi_parser.py` (276 行) | refactor | byte-match → ref count + field presence の structural smoke test |
| `tests/test_overrides_contract.py` (128 行) | refactor | Ref #141 specific → YAML schema contract test |
| `tests/test_journal_audit.py` (423 行) | partial refactor | line 333+ の expected_report.md byte-match のみ structural 化、他 unit test は不変 |
| `tests/test_pre_integration_baseline.py` (138 行) | weaken to historical archive | byte-match 廃止、「baseline file が読み込めること」のみ assert、docstring で historical 化を明示 |
| `tests/test_split_references_doi_boundary.py` (58 行) | path 書換のみ | parser logic test、corpus 依存度低、FIXTURE_DIR 書換だけで動く |

### 2.2 改変対象外 (確認のみ)

- `tests/test_integration_mdpi_173refs.py` (Day23 Task 10 で追加済の 8-test integration、本 task で触らない)
- `tests/test_integration_vancouver_35refs.py` (同上)
- `tests/test_integration_apa_45refs.py` / `tests/test_integration_cell_45refs.py` (apa/cell 系、本 task と無関係)
- `tests/test_nlm_catalog_check.py` / `tests/test_crossref_check.py` / `tests/test_three_class_classifier.py` / `tests/test_env_loader.py` (unit test、corpus 非依存)

### 2.3 共通対応事項 (5 file 全件)

1. **module-level `pytestmark = pytest.mark.skip(...)` を削除** (Day23 Phase 1 で 5 file 共通に追加した block、約 6-8 行)
2. **module docstring 更新**: 「Day23 mdpi_149refs 削除後、Day24 で mdpi_173refs に re-point + 構造 test に refactor」と明示
3. **FIXTURE_DIR / TEST_DIR / FIXTURES path 一括書換**: `mdpi_149refs` → `mdpi_173refs`
4. **byte-match assertion 削除/置換**: `expected_phase2_structured.json` / `expected_phase3_resolved.json` / `expected_report.md` / `expected_journal_audit.json` / `ref141_parser_snapshot.json` への参照削除

### 2.4 新規作成 (Day24 archive)

| File | 用途 |
|:---|:---|
| `docs/superpowers/specs/2026-05-24-day24-mdpi-test-restoration-design.md` | 本 SPEC |
| `docs/superpowers/plans/2026-05-24-day24-mdpi-test-restoration.md` | writing-plans 出力 |
| `docs/sessions/day24/README.md` | Day24 archive index |
| `docs/sessions/day24/DAY24_LESSONS_LEARNED.md` | Day24 教訓記録 |

---

## 3. Per-file refactor 詳細

### 3.1 test_mdpi_parser.py

**変更前** (line 38, 57-58):

```python
TEST_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_149refs"
# ...
input_docx = TEST_DIR / "input_References.docx"
expected_json = TEST_DIR / "expected_phase2_structured.json"
```

**変更後**:

```python
TEST_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_173refs"
# expected_phase2_structured.json への参照削除 (新 fixture に存在せず)

def test_mdpi_parser_extracts_refs_from_corpus():
    """MDPI parser が representative corpus から ref を抽出できることを smoke check.

    Day23 mdpi_173refs 置換に伴い、旧 byte-level expected_phase2_structured.json
    との byte-match を廃止し structural check に変更. MDPI 173 refs review
    (PMC13164670) で parser regression を検出する設計.
    """
    input_docx = TEST_DIR / "input_References.docx"
    refs = run_phase2(input_docx)
    # parsed actual: 171 (Day23 Task 9 報告)
    assert 165 <= len(refs) <= 180, f"unexpected ref count: {len(refs)}"
    for r in refs:
        assert "title" in r or "raw_text" in r, f"ref missing title/raw_text: {r}"
        assert "authors" in r or "raw_text" in r, f"ref missing authors/raw_text: {r}"
```

### 3.2 test_overrides_contract.py

**変更前** (line 28, 76):

```python
FIXTURES = Path(__file__).parent / "fixtures" / "mdpi_149refs"
# ...
(FIXTURES / "ref141_parser_snapshot.json").read_text(encoding="utf-8")
```

**変更後**:

```python
FIXTURES = Path(__file__).parent / "fixtures" / "mdpi_173refs"  # Day24: re-pointed

def test_manual_overrides_yaml_contract():
    """manual_overrides.yaml の構造 contract を検証 (Day24 mdpi_173refs 置換後の汎用化版).

    旧 Day8-23 までは mdpi_149refs Ref #141 specific assertion を実施していたが、
    Day23 で旧 corpus 削除 + 新 mdpi_173refs に #141 該当なし.
    本 test は manual_overrides.yaml の load + schema 構造のみ検証する形式に書換.
    Day25+ で mdpi_173refs 用の override が必要になれば fixture-specific assertion を追加可能.
    """
    overrides = load_overrides()
    assert isinstance(overrides, dict), "overrides should load as dict"
    for ref_id, override in (overrides.get("overrides") or {}).items():
        assert isinstance(ref_id, (int, str)), f"ref_id type: {type(ref_id)}"
        assert isinstance(override, dict), f"override entry should be dict"
```

### 3.3 test_journal_audit.py

**変更前** (line 333+):

```python
fixtures_dir = REPO_ROOT / "tests" / "fixtures" / "mdpi_149refs"
phase3 = json.loads(
    (fixtures_dir / "expected_phase3_resolved.json").read_text(encoding="utf-8")
)
expected = (fixtures_dir / "expected_report.md").read_text(encoding="utf-8")
# ...
assert idx != -1, "expected_report.md に補遺セクションの目印が見つからない"
```

**変更後**:

```python
fixtures_dir = REPO_ROOT / "tests" / "fixtures" / "mdpi_173refs"
phase3 = json.loads(
    (fixtures_dir / "baseline_phase3_resolved.json").read_text(encoding="utf-8")
)
report = (fixtures_dir / "baseline_report.md").read_text(encoding="utf-8")
# byte-match → 含有確認に変更
assert "stage5_journal_audit" in report or "journal_audit" in report, \
    "baseline_report.md に journal audit セクションが見つからない"
```

line 333 以前の他の test (journal_audit module unit test) は不変。

### 3.4 test_pre_integration_baseline.py

**変更前** (line 47, 61, 84):

```python
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_149refs"
# ...
docx = FIXTURE_DIR / "input_References.docx"
# ...
"""tests/fixtures/mdpi_149refs/ の中身自体が破損していないことを確認。"""
```

**変更後**:

```python
"""Day8 pre-integration baseline characterization (Day24 archive 化).

旧 mdpi_149refs corpus の「integration 前の元状態」を byte-match で characterize する
ことが本 test の本来の役割だったが、Day23 で旧 corpus 削除 + 新 mdpi_173refs は
integration 概念がない (はじめから LLM path) ため本来の意味は喪失.

Day24 では historical archive として残置し、新 fixture (mdpi_173refs) の baseline file
が読み込めることのみを sanity check として確認する形式に弱体化.
"""

FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_173refs"
# byte-match 廃止、file readability check のみ

def test_baseline_fixture_files_loadable():
    """新 fixture の baseline file 群が読み込めることを sanity check."""
    docx = FIXTURE_DIR / "input_References.docx"
    assert docx.exists(), f"input_References.docx not found: {docx}"
    baseline_p3 = FIXTURE_DIR / "baseline_phase3_resolved.json"
    assert baseline_p3.exists()
    baseline_report = FIXTURE_DIR / "baseline_report.md"
    assert baseline_report.exists()
```

### 3.5 test_split_references_doi_boundary.py

**変更前** (line 13, 20):

```python
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_149refs"
# ...
docx = FIXTURE_DIR / "input_References.docx"
```

**変更後**:

```python
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_173refs"  # Day24: re-pointed
# parser logic test, corpus input only
docx = FIXTURE_DIR / "input_References.docx"
# 既存 assertion (DOI boundary 検出) はそのまま動く想定
```

---

## 4. Commit 計画 (4 commits)

| 順 | type | scope | 内容 |
|:---:|:---|:---|:---|
| 1 | `docs(spec)` | Pre | 本 SPEC を archive |
| 2 | `docs(plan)` | Pre | writing-plans 出力を `docs/superpowers/plans/` に commit |
| 3 | `test(refactor)` | Main | 5 file 一括 re-point + structural refactor + skip 解除 (atomic commit) |
| 4 | `docs(sessions)` | Post | Day24 archive (README + LESSONS) |

---

## 5. 完了条件 (8 項目)

| # | 条件 | 確認方法 |
|:---:|:---|:---|
| 1 | 5 file の FIXTURE_DIR/TEST_DIR/FIXTURES が `mdpi_173refs` を指す | `grep -c "mdpi_173refs" tests/test_mdpi_parser.py tests/test_overrides_contract.py tests/test_journal_audit.py tests/test_pre_integration_baseline.py tests/test_split_references_doi_boundary.py` で各 ≥1 |
| 2 | 5 file から `pytestmark = pytest.mark.skip` 削除 | 同 5 file に `pytestmark` grep が 0 hit |
| 3 | 旧 `expected_phase2_structured.json` 等への参照削除 | 5 file 内 grep 0 hit |
| 4 | 5 file の test 全 pass (構造 test) | `pytest tests/test_mdpi_parser.py tests/test_overrides_contract.py tests/test_journal_audit.py tests/test_pre_integration_baseline.py tests/test_split_references_doi_boundary.py -v` 全 PASS |
| 5 | 全 test pass (regression なし) | `pytest tests/ -q` で ~100+ passed / ≤1 skipped / 0 failed |
| 6 | gitleaks 継続 clean | `gitleaks detect --no-banner --redact` で `no leaks found` |
| 7 | 1 atomic commit + push 成功 | `git log --oneline -2` で `test(refactor):` 表示 + `git ls-remote` 一致 |
| 8 | CI green for HEAD | `gh run list --limit 1 --jq .[0].conclusion` = `success` |

---

## 6. 工数見積もり

| Phase | 内容 | 見積 |
|:---:|:---|---:|
| Pre | SPEC + PLAN archive | 30 min |
| 1 | 5 file refactor (各 20-30 min) | 2 h |
| 2 | pytest 全 pass 確認 + 1 atomic commit + push | 30 min |
| 3 | Day24 archive + CI 確認 | 30 min |
| **合計** | | **~3.5 h** |

LLM cost: **$0** (test refactor のみ、新規 baseline 生成なし)

---

## 7. 想定リスク

| リスク | 確率 | 影響 | 対応 |
|:---|:---:|:---:|:---|
| structural assertion が緩すぎて regression 検知力低下 | 中 | 中 | ref count range (±5) と field presence 両方 check で最低限 invariant 確保 |
| test_overrides_contract.py の汎用化で manual_overrides.yaml の意味が薄れる | 中 | 低 | docstring で「YAML schema contract only」と明示、Day25+ で fixture-specific override test 復活余地を残す |
| test_pre_integration_baseline.py の意味喪失が大きい | 低-中 | 低 | b 案で「historical archive」化、削除しない (Section 3.4 で確定) |
| 新 fixture の parser 出力 ref 数が想定外 (171 ではなく違う数) | 中 | 中 | 範囲 165-180 で許容、実測で確定 |
| test_split_references_doi_boundary.py が新 docx で DOI 形式違いで fail | 中 | 中 | execution 時に実際の parser 挙動を確認、必要なら assertion を緩める |
| journal_audit module の他 test も corpus 依存で failure | 低 | 中 | execution 時に発見した場合 Pattern: inline fix (Day20 D20-3 同型) |

---

## 8. Out of Scope (Day25+)

- **mdpi_173refs に対する manual_overrides.yaml 構築**: 新 corpus parser 出力に応じた override 追加 (Day25+ 別 task)
- **deterministic な byte-level golden の再構築**: 新 fixture が LLM path のため原理的に不可能、別 path (例: deterministic stub LLM) を作るのは Day26+ 大改修
- **MDPI parser fast-path 拡張で mdpi_173refs を fast-path target にする**: parser 自体の改修、scope 大きく別 brainstorming 必要
- **journal_audit module の structural test 拡張**: line 333+ 以外の既存 unit test は本 task で触らない
- **pre-commit hook gitleaks 自動実行** (Day22 handoff パターン 3、Day24 候補 Pattern 2)
- **CONTRIBUTING.md / Issue PR template 整備** (Day24 候補 Pattern 3)
- **PyPI 公開** (Day24 候補 Pattern 4)
- **pyproject.toml + uv.lock 移行** (Day24 候補 Pattern 5)
- **Crossref graceful failure 16 件の対応** (Day22 §6.3 NEW、Day24 候補 Pattern 6)
- **NLM fuzzy-match precision 改善** (Day22 §6.3 NEW、Day24 候補 Pattern 7)
- **tools/build_*_fixture.py の共通 utility refactor** (Day23 code review 指摘、Day24 候補 Pattern 8)

---

## 9. 参照

- Day22 brainstorming spec: `docs/superpowers/specs/2026-05-24-rule3-nlm-ssl-fix-design.md` (test refactor の参考 pattern)
- Day22 LESSONS: `docs/sessions/day22/DAY22_LESSONS_LEARNED.md` (Day24+ 候補 §6.3 NEW)
- Day23 spec: `docs/superpowers/specs/2026-05-24-day23-fixture-remediation-design.md` (旧 mdpi_149refs 削除 + 新 mdpi_173refs 追加の経緯)
- Day23 plan Task 2: 「Phase 1 で 5 file に pytestmark.skip 付与、Phase 5 で復活予定」と明示 → 本 task でその「復活」を実行
- Day23 archive `DAY23_LESSONS_LEARNED.md` §6 D23-X PLAN gap detection: 5 file cross-fixture coupling 発見の経緯
- 新 fixture: `tests/fixtures/mdpi_173refs/` (Day23 Task 9 で構築、6 file 構成、PMC13164670)
- 既存 apa/cell integration test 8-test template (本 task では直接適用しないが参考)

---

**承認**: 片山英樹 (brainstorming Q1-Q2 + design 全 3 sections)
**次工程**: writing-plans skill で bite-sized implementation plan を作成
