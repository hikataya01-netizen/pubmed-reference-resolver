# SPEC: Cell 系 45-ref golden fixture 追加 (Day17)

**作成日**: 2026/05/17 (Day17 brainstorming 完了時)
**著者**: Claude Code (Sonnet 4.6) / 承認: 片山英樹
**位置付け**: Day7 §9.3 long-term task 残 3 件のうち 1 件 (APA / Cell 系 golden fixture) の **Cell 部分** を完了 (Day16 で APA を完了済)
**前提**: Day9 Vancouver Veto + Day16 拡張 regex (`\((?:19|20)\d{2}[a-z]?\)`) / Day11 ハイブリッド命名規約 (`expected_*` / `baseline_*`) / Day15 三分類 audit logic / Day16 で確立された `tools/build_apa_fixture.py` template

---

## 1. 背景と目的

### 1.1 残存タスクの位置付け

`docs/sessions/day16/DAY16_LESSONS_LEARNED.md` §6.1 で整理された Day7 §9.3 long-term task 残:

| タスク | 状態 (Day16 末) |
|:---|:---:|
| Vancouver golden fixture | ✅ Day11 |
| Day9 (Z) 未解決 2 件 MEDLINE 調査 | ✅ Day13 |
| Day13 §6 案 A: 3 分類 audit logic | ✅ Day15 |
| APA 系 golden fixture | ✅ Day16 |
| **Cell 系 golden fixture** | ⏳ **Day17** (本 SPEC) |
| MCP/hook 経由 Stage 3 配線 | ⏳ Day18+ |
| GitHub remote 追加と push | ⏳ Day18+ |

Day17 では Cell-style 表記 (Cell Press 系 journal の compressed initials + `, and ` connector + `(YYYY)` paren year) の fixture を Day16 同型 pattern で追加.

### 1.2 目的

1. **regression 保護**: Day9 Vancouver Veto + Day16 拡張 regex が **Cell 表記** も確実に reject し続けることを test で保証する (Day11 Vancouver / Day16 APA に続く 3 番目の LLM-path golden)
2. **document-of-record**: Cell 系 LLM 経由 parsing baseline を凍結し、将来の LLM model upgrade / PubMed snapshot 変動を検出可能にする
3. **Phase 1 抽出検証**: Cell docx からの reference block 抽出 (parser-only) が deterministic に動作することを byte-strict golden で保証する
4. **Day15 三分類 audit の Cell 適用検証**: Cell 入力でも正しく動作する baseline を取得する
5. **build script template の汎用性証明**: Day16 で確立された tool pattern が style variant にも適用可能であることを実証

### 1.3 設計判断の経緯 (brainstorming 質問、Day16 圧縮版)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | Day16 と同じ枠組みで進めるか | **(同型) PMC OA + 45 件 + 3 領域 + 8 tests** |
| Q2 | PMC OA 論文選定 | **3 iScience CC BY 4.0 papers** (Cell Press 配下) |

Day16 で Q1-Q5 + Approach の 6 質問を経て確立されたパターンを継承するため、Day17 では 2 質問のみに圧縮.

---

## 2. Architecture & ファイル配置

```
tests/fixtures/cell_45refs/
├── README.md                                   (Day17 新規、由来 + 規約 + LICENSE 明記)
├── input_References.docx                       (45 refs 統合 docx、Day17 で組成)
├── expected_phase1_intermediate.json           (parser-only output、byte-strict golden)
├── baseline_phase3_resolved.json               (LLM + PubMed output、document-of-record)
├── baseline_report.md                          (Phase 4 audit report、document-of-record)
└── baseline_three_class_classification.json    (Day15 三分類 audit sidecar、document-of-record)

tests/test_integration_cell_45refs.py           (Day17 新規、8 tests)

tools/build_cell_fixture.py                     (Day17 新規、build_apa_fixture.py を template に複写 + Cell 化)

docs/sessions/day17/
├── SPEC_cell_45refs_fixture.md                 (本 SPEC、brainstorming 確定後 commit)
├── PLAN_cell_45refs_fixture.md                 (writing-plans 出力)
├── DAY17_LESSONS_LEARNED.md                    (Day17 末 archive)
└── README.md                                   (day17 index)
```

### 命名規約 (Day11 ハイブリッド踏襲)

- **`expected_*`**: deterministic (parser-only) → test で byte-match 厳密検証
- **`baseline_*`**: variability-bearing (LLM/PubMed/Crossref/NLM 依存) → test で構造・件数 assert のみ

### 既存 production code 改変

Day16 で Vancouver Veto regex を `\((?:19|20)\d{2}[a-z]?\)` に拡張済. Cell-style の `(YYYY)` も既に reject 想定のため、**改修なし見込み**. 実装段階で改修必要と判明した場合は本 SPEC を改訂する.

---

## 3. PMC OA 論文選定 (Day17 Task 0 で確定、ユーザー承認済)

### 3.1 選定確定論文

| 領域 | PMC ID | DOI | Journal | 出版年 | LICENSE | Refs |
|:---|:---|:---|:---|:---:|:---|---:|
| Molecular Biology | PMC13080398 | 10.1016/j.isci.2025.113995 | iScience (Cell Press) | 2026 | **CC BY 4.0** | 64 |
| Biomedical / Nanomedicine | PMC12918234 | 10.1016/j.isci.2025.114547 | iScience (Cell Press) | 2026 | **CC BY 4.0** | 114 |
| AI / Agricultural Engineering | PMC12915276 | 10.1016/j.isci.2025.114411 | iScience (Cell Press) | 2026 | **CC BY 4.0** | 55 |

各論文の先頭 15 件を抽出. 抽出範囲は引用論文の bibliographic information (factual data) のみで、creative expression は含まない. PMC OA CC BY 4.0 ライセンスの帰属表示として fixture README にて明示.

選定タイトル:
- PMC13080398: "Two domains of Nrf2 cooperatively bind CBP, a CREB binding protein, and synergistically activate transcription"
- PMC12918234: "Nanoencapsulated senotherapeutic compounds targeting connexin-43 for enhanced wound healing"
- PMC12915276: "Explainable transformer framework for fast cotton leaf diagnostics and fabric defect detection"

### 3.2 publisher 選定根拠

- Cell Press 系 journals (Cell / Cell Reports / iScience 等) は CC BY-NC-ND が主流だが、iScience は CC BY 4.0 を選択可能
- 3 候補すべて iScience に絞ることで license 一貫性 (Day16 の CC BY 4.0 統一を踏襲) と publisher 内領域多様性を両立
- 領域多様性: Molecular Biology + Biomedical + AI/Engineering の 3 域 (Day16 の Psychology 2 + Public Health 1 より多様性高)

### 3.3 Cell-style XML 構造の特徴

3 論文すべての `<mixed-citation>` は以下 pattern (Day16 Frontiers Psychology と同型):
- `<name>` 形式 (`<string-name>` ではない)
- tail commas 無し
- 例 (PMC13080398 ref 1): `<name><surname>Katoh</surname><given-names>Y.</given-names></name>` 連続

→ build script 側で **structured fields からの再組成** が必須 (Day16 で確立した `format_as_apa7` の structured-field 経路を Cell 用に複写・改変).

### 3.4 Cell 表記揺れの想定

抽出 45 件には以下 variant が含まれる見込み (parser routing 検証の網羅性向上):

- Compressed initials (`SmithJA` not `Smith, J.A.`)
- Journal abbreviation (`Nat. Rev. Mol. Cell Biol.`)
- No issue number (Cell style omits issue)
- DOI bare 形式 (`10.1038/nrm.2017.125`)
- `<collab>` (組織著者: AIRFLOW-3 Trial Study Group 等)

これらが Day9 + Day16 拡張 Vancouver Veto の `\((?:19|20)\d{2}[a-z]?\)` 検出を確実に通過することを test で確認.

---

## 4. Source-to-docx 組成パイプライン

### 4.1 Step 構成 (Phase 0a で実装)

| Step | 内容 | 出力 |
|:---:|:---|:---|
| A | PMC E-utilities `efetch` で 3 論文 XML 取得 (`db=pmc&id=PMCXXXXXXX&rettype=xml`) | local cache (`.cache/pmc_xml/PMCXXXXXXX.xml`、Day16 と共有) |
| B | JATS XML `<ref-list>` → Cell plain text 変換 (各論文先頭 15 件) | 内部 list[str] (45 件) |
| C | python-docx で番号付き段落 (`1.` 〜 `45.`) として統合 docx 生成 | `tests/fixtures/cell_45refs/input_References.docx` |
| D | docx + script を Git commit | (commit 3) |

### 4.2 `tools/build_cell_fixture.py` の Day16 build_apa_fixture.py との差分

`build_apa_fixture.py` を template に複写 (依存ではなく独立保持). 以下 2 関数を Cell 化:

#### `_normalize_initials(given, cell_mode=False)` (拡張)

```python
def _normalize_initials(given: str, cell_mode: bool = False) -> str:
    """
    APA 7 default: 'John Anthony' -> 'J. A.'  /  'JE' -> 'J. E.'  /  'K. G.' -> 'K. G.'
    Cell mode    : 'John Anthony' -> 'J.A.'   /  'JE' -> 'J.E.'   /  'K. G.' -> 'K.G.'
    """
    # ... (existing logic) ...
    # at end, if cell_mode: result = result.replace('. ', '.')
```

#### `_format_authors(cit_el, cell_mode=False)` (拡張)

APA 7 vs Cell connector:

| 人数 | APA 7 (default) | Cell (cell_mode=True) |
|:---:|:---|:---|
| 0 | `''` | `''` |
| 1 | `'Smith, J. A.'` | `'Smith, J.A.'` |
| 2 | `'Smith, J. A., & Brown, K. L.'` | `'Smith, J.A., and Brown, K.L.'` |
| 3+ | `'..., Brown, K. L., & Jones, M. P.'` | `'..., Brown, K.L., and Jones, M.P.'` |

#### `format_as_cell(cit_el)` (新規)

`format_as_apa7` のロジックをほぼ複写し、以下のみ変更:
- `_format_authors(cit_el, cell_mode=True)` 呼出
- Issue 部 (`(Issue)`) を出力に含めない
- Journal 名と volume 間に **comma を入れない** (`Cell 12, 100-110` vs APA `Cell, 12(3), 100-110`)

#### CLI

```bash
python3 tools/build_cell_fixture.py \
  --molecular-biology PMC13080398 \
  --biomedical PMC12918234 \
  --ai-engineering PMC12915276 \
  --output tests/fixtures/cell_45refs/input_References.docx \
  --refs-per-paper 15
```

CLI flag 名は領域別の意味付け (Day16 の `--psychology` / `--public-health` / `--psychology-religion` と同 pattern).

#### 共通コード再利用方針

以下は `build_apa_fixture.py` から **複写 (独立保持)**:
- `fetch_pmc_xml(pmc_id, api_key)`
- `extract_references(xml, limit)`
- `build_docx(refs, output_path)`
- `_collapse_whitespace`, `_full_text` 等ヘルパー

`from build_apa_fixture import ...` の依存はリスク (将来 build_apa_fixture.py 改修時に build_cell_fixture.py が壊れる可能性) のため避ける.

### 4.3 docx 内構造の方針 (Day16 同型)

- 各 ref = 番号付き 1 段落 (`1.`, `2.`, ..., `45.`)
- 領域境界マーカーは docx 内に**入れない** (3 領域混在を意図的に隠す = parser が領域非依存に動くことの検証)

### 4.4 sanity check (Step C 完了直後)

```bash
python3 -c "
from docx import Document
d = Document('tests/fixtures/cell_45refs/input_References.docx')
for i, p in enumerate(d.paragraphs):
    if i < 3 or i in (15, 30) or i > 43:
        print(f'{i:3d}: {p.text[:120]}')
"
```

- 全 45 番号付き段落 (heading + 45 = 46 paragraphs total)
- 各段落に `(YYYY)` (1900-2099) を 1 つ含む
- 3+ 著者 ref に `, and ` を含む

---

## 5. Baseline 生成手順 (Phase 0b で実行、1 回限り)

### 5.1 実行 protocol (Day16 同型)

#### Step 1: `.env` 健全性確認
```bash
uv run python -c "import os; from main import load_env_files; load_env_files(); print('ANTHROPIC:', bool(os.environ.get('ANTHROPIC_API_KEY'))); print('NCBI:', bool(os.environ.get('NCBI_API_KEY')))"
```

#### Step 2: 1 回限り full pipeline 実行
```bash
python3 main.py \
  tests/fixtures/cell_45refs/input_References.docx \
  --output-dir /tmp/cell_45refs_baseline_gen \
  --phase 4
```

#### Step 3: 出力 3 baseline ファイルを fixture に配置

| 出力 | 配置先 |
|:---|:---|
| `phase3_resolved.json` | `tests/fixtures/cell_45refs/baseline_phase3_resolved.json` |
| `report.md` | `tests/fixtures/cell_45refs/baseline_report.md` |
| `three_class_classification.json` | `tests/fixtures/cell_45refs/baseline_three_class_classification.json` |

#### Step 4: メタ情報を計測 (README に転記)

- Phase 3 解決件数 (`stage4_pubmed_resolutions` で `pmid` 持つ件数)
- 三分類分布 (A/B/C/unknown のカウント)
- Report.md 重大件数 (regex `r"重大\s*\|\s*(\d+)\s*\|"`)

### 5.2 LLM / API cost 見積

| API | 想定 call 数 | 合計 |
|:---|---:|---:|
| Claude Sonnet 4.6 | 45 | ~$0.5-1.0 |
| PubMed (NCBI key) | 45 | $0 |
| Crossref (未解決のみ) | ~10 | $0 |
| NLM Catalog (未解決のみ) | ~10 | $0 |
| **合計** | | **< $1.5** |

1 回限り実行. baseline 固定後 CI 再実行されない.

### 5.3 解決率の予測

| Fixture | 解決率 | 予測根拠 |
|:---|:---:|:---|
| vancouver_24refs (Day11) | 22/24 = 91.7% | 緩和ケア医学領域、PubMed coverage 高 |
| apa_45refs (Day16) | 25/45 = 55.6% | 社会心理 + 政府文書 + 書籍 |
| **cell_45refs (Day17)** | **~80%? (予測)** | 分子生物 + 生医 + 工学、Cell Press 領域は PubMed 比較的 well-indexed |

実測で確定し、test 4 の期待値に反映.

### 5.4 再現性メタ情報

`tests/fixtures/cell_45refs/README.md` に baseline 生成時のメタ情報を記録:
- 実行日時 (例: 2026-05-17)
- LLM model (`claude-sonnet-4-6-20260301`)
- PubMed snapshot 日 (NCBI 側 latest)
- `main.py` version (Day17 開始時の commit hash)

---

## 6. Test 設計 (8 tests)

`tests/test_integration_cell_45refs.py` を `tests/test_integration_apa_45refs.py` を template に新規追加.

### 6.1 同型 6 tests (Day16 そのまま、fixture path のみ差替)

| # | test 名 | 性質 | Day16 から変更 |
|:---:|:---|:---|:---|
| 1 | `test_cell_45refs_routes_all_to_llm_path` | regression (deterministic) | 関数名 + fixture path のみ |
| 2 | `test_phase1_reference_blocks_match_expected` | byte/structural | fixture path のみ |
| 3 | `test_phase1_extracts_45_reference_blocks` | 件数 | fixture path のみ |
| 4 | `test_baseline_phase3_documents_resolution_count` | document-of-record | `EXPECTED_RESOLVED_COUNT` を Day17 Phase 0b 実測値に |
| 5 | `test_baseline_report_documents_audit_summary` | document-of-record | `EXPECTED_REPORT_CRITICAL_COUNT` を Day17 実測値に |
| 6 | `test_cell_paren_year_pattern_detected_in_all_refs` | parser-only | 関数名 + fixture path のみ (regex は Day16 拡張形式 `\((?:19|20)\d{2}[a-z]?\)` をそのまま使用) |

### 6.2 差分 2 tests

#### Test 7: `test_cell_and_author_separator_present` (構造、Day16 test 7 の Cell 化)

```python
def test_cell_and_author_separator_present():
    """45 件中、最低 20 件が `, and ` を含むことを確認.

    Cell style 規約: 3+ 著者列挙時の最終境界は `, and ` (APA 7 の `, & `
    に相当). 本 test は fixture が Cell 規約を満たしていることを保証する
    (build_cell_fixture.py の _format_authors(cell_mode=True) 出力品質の
    test data 健全性保護).

    20 という閾値は: 単著 / 2 著者 / 組織著者 ref がある程度含まれる
    ことを許容しつつ、3+ 著者 ref が過半数を超えるという経験則.
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()
    refs_with_and = [b.ref_no for b in blocks if ", and " in b.raw_text]
    assert len(refs_with_and) >= 20, (
        f"Cell style structural regression: only {len(refs_with_and)}/45 "
        f"refs contain `, and ` (Cell author separator). Expected >=20. "
        f"Refs with separator: {refs_with_and}"
    )
```

#### Test 8: `test_baseline_three_class_classification_distribution` (Day16 同型、値だけ更新)

`EXPECTED_THREE_CLASS_DISTRIBUTION` を Day17 Phase 0b 実測値で置換. 構造 (A/B/C/unknown dict) は Day16 と同じ.

### 6.3 共通仕様 (Day16 同型)

- 全 test API key 不要 (parser-only / fixture 直読)
- module-level `_load_phase1_blocks_with_ln_report()` helper
- 比較時の volatile field 除外は `_scrub_volatile()` (test 内 private 関数、必要に応じて)

### 6.4 失敗時の運用 (Day16 同型)

| 失敗パターン | 原因可能性 | 対応 |
|:---|:---|:---|
| test 4-5, 8 fail | baseline document-of-record 値乖離 (LLM upgrade / PubMed snapshot) | Phase 0b retry + baseline 更新 + test 期待値更新 (別 commit) |
| test 1-3, 6-7 fail | production code 改修の意図しない regression | 改修内容確認 → revert 検討 |

---

## 7. Commit 計画 (8 commits)

| 順 | commit 種別 | Phase | 内容 |
|:---:|:---|:---:|:---|
| (前) | `docs(spec)` | — | Day17 SPEC archive (本 commit) |
| (前) | `docs(plan)` | — | Day17 PLAN archive |
| 1 | `test(fixtures)` | 0a | `tools/build_cell_fixture.py` + `tests/fixtures/cell_45refs/input_References.docx` + `expected_phase1_intermediate.json` |
| 2 | `test(fixtures)` | 0b | `baseline_phase3_resolved.json` + `baseline_report.md` + `baseline_three_class_classification.json` + `README.md` |
| 3 | `test(integration)` | 1 | `tests/test_integration_cell_45refs.py` の base 5 tests + test 6 |
| 4 | `test(integration)` | 2 | Cell 固有 2 tests (test 7 `, and ` separator + test 8 三分類) |
| 5 | `docs(skill)` | 3 | `skill_package/references/USAGE_QUICKSTART.md` 1.4 → 1.5 bump |
| 6 | `docs(sessions)` | 4 | `docs/sessions/day17/{README,DAY17_LESSONS_LEARNED}.md` archive |

→ 合計 **6 phase commits + 2 pre-commits = 8 commits** (Day16 同型).

---

## 8. 完了条件 (12 項目)

| # | 条件 | 確認方法 |
|:---:|:---|:---|
| 1 | `tools/build_cell_fixture.py` 存在 + 実行可能 | `python3 tools/build_cell_fixture.py --help` |
| 2 | `input_References.docx` 存在 (45 段落) | `python3 -c "from docx import Document; d=Document('...'); assert len(d.paragraphs)>=46"` |
| 3 | `expected_phase1_intermediate.json` 存在 | `jq '.stage3_reference_blocks \| length' < ...` = 45 |
| 4 | `baseline_phase3_resolved.json` 存在 | file 存在 + JSON parseable |
| 5 | `baseline_report.md` 存在 | file 存在 + ダッシュボード行 (`重大 \| N \|`) 有 |
| 6 | `baseline_three_class_classification.json` 存在 | file 存在 + JSON parseable |
| 7 | `tests/fixtures/cell_45refs/README.md` 存在 (3 論文 citation + LICENSE 明記) | file 存在 |
| 8 | `tests/test_integration_cell_45refs.py` 存在 (8 tests) | `pytest tests/test_integration_cell_45refs.py --collect-only` = 8 items |
| 9 | 全 8 tests pass | `pytest tests/test_integration_cell_45refs.py -v` |
| 10 | 既存 89 → 97 passed (regression なし) | `pytest tests/ -v` = **97 passed / 1 skipped** |
| 11 | `docs/sessions/day17/SPEC_cell_45refs_fixture.md` archive 済み | file 存在 |
| 12 | `docs/sessions/day17/{README,DAY17_LESSONS_LEARNED,PLAN}.md` archive 済み | 3 files 存在 |

---

## 9. Out of Scope (Day18+ 候補)

- **APA fixture の領域追加** (現状 3 領域、将来 6 領域等)
- **live API test** (Day15 SPEC §8 と同様 skip-by-default 必要)
- **parser 改修** (現時点で必要性ゼロ見込み、実装段階で必要性発覚なら別 SPEC)
- **PMC OA 外の source** (preprint server、商業 journal の paywall 越え等)
- **三分類 baseline の SSL 問題解消後再生成** (Day16 と同じく Day17 でも B=0, C=0 想定、Day18+ で対応)

---

## 10. 工数見積もり

| Phase | 内容 | 見積 |
|:---:|:---|---:|
| Pre | SPEC + PLAN archive | 20min |
| Phase 0a | build script + docx + Phase 1 expected | 45min |
| Phase 0b | full pipeline + baselines + README | 30min |
| Phase 1-2 | 8 tests TDD | 60min |
| Phase 3 | USAGE_QUICKSTART | 10min |
| Phase 4 | day17 archive | 25min |
| **合計** | | **~3h** |

Day16 (~3h) と同等. Day16 で確立された template + Q1-Q5 圧縮により brainstorming 時間が短縮された分、実装に集中可能.

---

## 11. 想定リスク

| リスク | 確率 | 影響 | 対応 |
|:---|:---:|:---:|:---|
| Cell 固有 build script bug (`_format_authors(cell_mode=True)` 出力不正) | 中 | 中 | Phase 0a sanity check で発見 → inline fix (Day16 `<collab>` 対応漏れと同様) |
| Phase 3 resolution rate が予測 (~80%) と乖離 | 低 | 低 | 実測値で確定 → test 4 期待値に反映 |
| 三分類 baseline で B/C が出現しない (SSL 問題) | 高 | 低 | Day16 同様、容認 (Day18+ で別 task として解消) |
| 既存 test の意図しない regression | 低 | 高 | Phase 1-2 で `pytest tests/ -v` 実行 → 97 passed 確認 |
| LLM cost 超過 ($1.5 超え) | 低 | 低 | `--reuse-phase2`/`--reuse-phase3` で部分再実行可 |

---

## 12. 参照

- Day9 SPEC: `docs/sessions/day9/SPEC_mdpi_fast_path_strict.md` (Vancouver Veto 設計の源流)
- Day11 fixture: `tests/fixtures/vancouver_24refs/README.md` (本 SPEC が踏襲する Day11 規約)
- Day15 SPEC: `docs/sessions/day15/SPEC_three_class_audit.md` (本 fixture が三分類 audit baseline 生成にも使われる根拠)
- **Day16 SPEC**: `docs/sessions/day16/SPEC_apa_45refs_fixture.md` (本 SPEC の直接 template)
- **Day16 PLAN**: `docs/sessions/day16/PLAN_apa_45refs_fixture.md` (Day17 PLAN の template)
- **Day16 LESSONS**: `docs/sessions/day16/DAY16_LESSONS_LEARNED.md` (D16-1 教訓: Vancouver Veto regex 拡張)
- **Day16 build script**: `tools/build_apa_fixture.py` (Day17 build_cell_fixture.py の直接 template)
- **Day16 test**: `tests/test_integration_apa_45refs.py` (Day17 test の直接 template)

---

**承認**: 片山英樹 (brainstorming Q1-Q2 + design 全 4 sections)
**次工程**: writing-plans skill で implementation plan を作成
