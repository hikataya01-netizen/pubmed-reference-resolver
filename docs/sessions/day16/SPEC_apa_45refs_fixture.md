# SPEC: APA 系 45-ref golden fixture 追加 (Day16)

**作成日**: 2026/05/17 (Day16 brainstorming 完了時)
**著者**: Claude Code (Sonnet 4.6) / 承認: 片山英樹
**位置付け**: Day7 §9.3 long-term task 残 3 件のうち 1 件 (APA / Cell 系 golden fixture) を APA に絞って完了
**前提**: Day9 Vancouver Veto (`(YYYY)` 検出による LLM 経路強制) / Day11 ハイブリッド命名規約 (`expected_*` / `baseline_*`) / Day15 三分類 audit logic

---

## 1. 背景と目的

### 1.1 残存タスクの位置付け

`docs/sessions/day15/DAY15_LESSONS_LEARNED.md` §6.1 で整理された Day7 §9.3 long-term task 残:

| タスク | 状態 (Day15 末) |
|:---|:---:|
| Vancouver golden fixture | ✅ Day11 |
| Day9 (Z) 未解決 2 件 MEDLINE 調査 | ✅ Day13 |
| Day13 §6 案 A: 3 分類 audit logic | ✅ Day15 |
| **APA / Cell 系 golden fixture** | ⏳ **Day16** (本 SPEC) |
| MCP/hook 経由 Stage 3 配線 | ⏳ Day17+ |
| GitHub remote 追加と push | ⏳ Day17+ |

Day16 では scope を **APA に絞り** (Day17+ に Cell)、Day11 ハイブリッド規約に従って 45 件 fixture を追加する.

### 1.2 目的

1. **regression 保護**: Vancouver Veto (Day9) が APA 表記を確実に reject し続けることを test で保証する
2. **document-of-record**: APA 系 LLM 経由 parsing baseline を凍結し、将来の LLM model upgrade / PubMed snapshot 変動を検出可能にする
3. **Phase 1 抽出検証**: APA docx からの reference block 抽出 (parser-only) が deterministic に動作することを byte-strict golden で保証する
4. **Day15 三分類 audit の APA 適用検証**: Crossref + NLM 経由の A/B/C/unknown 分類が APA 入力でも正しく動作する baseline を取得する

### 1.3 設計判断の経緯 (brainstorming 質問)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | 入力 docx の入手方法 | **(c) PMC OA 論文から抽出** |
| Q2 | scope (APA + Cell or どちらか) | **(β) APA のみ Day16、Cell は Day17+** |
| Q3 | PMC OA 論文選定方法 | **(iii) 領域未指定 + Claude 選定** |
| Q4 | ref 件数規模 | **(γ) ~40-50 件 (2-3 論文)** |
| Q5 | test 構成粒度 | **(β) 5 base + APA 固有 2-3 = 8 tests** |
| Approach | 全体戦略 | **(A) 多領域 3 論文 × 15 件 ≈ 45 件** |

---

## 2. Architecture & ファイル配置

```
tests/fixtures/apa_45refs/
├── README.md                                   (Day16 新規、由来 + 規約 + LICENSE 明記)
├── input_References.docx                       (45 refs 統合 docx、Day16 で組成)
├── expected_phase1_intermediate.json           (parser-only output、byte-strict golden)
├── baseline_phase3_resolved.json               (LLM + PubMed output、document-of-record)
├── baseline_report.md                          (Phase 4 audit report、document-of-record)
└── baseline_three_class_classification.json    (Day15 三分類 audit sidecar、document-of-record)

tests/test_integration_apa_45refs.py            (Day16 新規、8 tests)

tools/build_apa_fixture.py                      (Day16 新規、JATS XML → docx 組成 script)

docs/sessions/day16/
├── SPEC_apa_45refs_fixture.md                  (本 SPEC、brainstorming 確定後 commit)
├── DAY16_LESSONS_LEARNED.md                    (Day16 末 archive)
└── README.md                                   (day16 index)
```

### 命名規約 (Day11 踏襲)

- **`expected_*`**: deterministic (parser-only) → test で byte-match 厳密検証
- **`baseline_*`**: variability-bearing (LLM/PubMed/Crossref/NLM 依存) → test で構造・件数 assert のみ

### 既存 production code 改変

Day9 Vancouver Veto により APA の `(YYYY)` も `is_mdpi_style()` で即 False に倒れるため、**改修なし見込み**. 実装段階で改修必要と判明した場合は本 SPEC を改訂する.

---

## 3. PMC OA 論文選定 protocol

### 3.1 Claude による選定手順

1. **NCBI E-utilities (`esearch` + `esummary`)** で以下 3 領域から PMC OA 論文を検索:
   - **Psychology 領域**: `("psycho-oncology"[Journal] OR "psychology"[All Fields]) AND "open access"[Filter] AND review[PT]`
   - **Nursing 領域**: `("J Adv Nurs"[Journal] OR "nursing"[All Fields]) AND "open access"[Filter] AND review[PT]`
   - **Public Health 領域**: `("Soc Sci Med"[Journal] OR "BMC Public Health"[Journal]) AND "open access"[Filter] AND review[PT]`
2. **絞り込み条件**: 各領域 hit から以下を満たす 1 本:
   - 過去 5 年以内 (2020 以降) 出版
   - reference list が 30 件以上 (先頭 15 件抽出のため)
   - **APA 第 7 版**採用 (instructions to authors / 実観察で確認)
   - PMC full-text XML 取得可能
3. **選定結果**: Phase 0 着手時に候補 3 論文を提示 → ユーザー承認後に確定 → SPEC §3.2 に追記 commit

### 3.2 選定確定論文 (Phase 0 で記入)

| 領域 | PMC ID | DOI | Journal | 出版年 | LICENSE |
|:---|:---|:---|:---|:---:|:---|
| Psychology | TBD (Phase 0) | TBD | TBD | TBD | CC BY (確認要) |
| Nursing | TBD (Phase 0) | TBD | TBD | TBD | CC BY (確認要) |
| Public Health | TBD (Phase 0) | TBD | TBD | TBD | CC BY (確認要) |

### 3.3 著作権・引用上の取扱い

- PMC OA = CC BY もしくは CC BY-NC ライセンス → 改変・再配布許諾
- 抽出するのは引用論文の **bibliographic information (factual data)** のみで、創作的表現 (本文 abstract 等) は含めない → 一般に著作権の対象外
- fixture README に source 3 論文の citation + LICENSE 明記で透明性確保

### 3.4 APA 表記揺れの想定

抽出 45 件には以下 variant が含まれる見込み (parser routing 検証の網羅性向上):

- ISSN / journal abbreviation 有無
- DOI URL / bare DOI 表記揺れ
- ページ範囲表記 (`45-67` / `45–67` / `45-67e1`)
- 著者 7+ 名 → `...` 短縮
- 章 / 書籍 entry の混在
- 電子のみ出版 (`e12345` 形式)

これらが Vancouver Veto の `(YYYY)` 検出を確実に通過することを test で確認.

---

## 4. Source-to-docx 組成パイプライン

### 4.1 Step 構成 (Phase 0 で実装)

| Step | 内容 | 出力 |
|:---:|:---|:---|
| A | PMC E-utilities `efetch` で 3 論文の reference XML 取得 (`db=pmc&id=PMCXXXXXX&rettype=xml`) | local cache (`.cache/pmc_xml/PMCXXXXXX.xml` 等) |
| B | JATS XML `<ref-list>` → APA 7 plain text 変換 (各論文先頭 15 件) | 内部 list[str] (45 件) |
| C | python-docx で番号付き段落 (`1.` 〜 `45.`) として統合 docx 生成 | `tests/fixtures/apa_45refs/input_References.docx` |
| D | docx を Git commit | (commit 1) |
| E | `tools/build_apa_fixture.py` を Git commit | (commit 1 と同時) |

### 4.2 docx 内構造の方針

- 各 ref = 番号付き 1 段落 (`1.`, `2.`, ..., `45.`)
- 領域境界マーカーは docx 内に**入れない** (3 領域混在を意図的に隠す = parser が領域非依存に動くことの検証)
- メタ情報 (source 3 論文の citation) は docx 末尾の separate page に記録 (parser 動作に影響しない、人間用の trail)

### 4.3 sanity check (Step C 完了直後)

```bash
python -c "
import docx
d = docx.Document('tests/fixtures/apa_45refs/input_References.docx')
for i, p in enumerate(d.paragraphs[:50]):
    print(f'{i:3d}: {p.text[:80]}')
"
```

- 全 45 番号付き段落が連続
- 各段落に `(YYYY)` (1900-2099) を 1 つ含む
- 著者 + タイトル + journal の構造が肉眼確認可能

### 4.4 Out of Scope (Phase 0 段階)

- 手動 Word 編集 (再現性が落ちる、script 一発が原則)
- 領域境界の docx 内可視化 (parser 動作影響回避)
- 45 件超過 (Q4 確定範囲外)

---

## 5. Baseline 生成手順 (Phase 0 完了後、1 回限り)

### 5.1 実行 protocol

#### Step 1: `.env` 健全性確認
```bash
uv run python -c "import os; from main import load_env_files; load_env_files(); print('ANTHROPIC:', bool(os.environ.get('ANTHROPIC_API_KEY'))); print('NCBI:', bool(os.environ.get('NCBI_API_KEY')))"
```

#### Step 2: 1 回限り full pipeline 実行
```bash
uv run python main.py \
  tests/fixtures/apa_45refs/input_References.docx \
  --output-dir /tmp/apa_45refs_baseline_gen \
  --phase 4
```
※ local docx を positional argument で直接渡し、`--phase 4` で Phase 1-4 全実行 (Stage 1 / OneDrive 概念は CLI には無く、引数で受け取った docx を Phase 1 入力として直読).

#### Step 3: 出力 4 ファイルを fixture に配置

| 出力 | 配置先 | 種別 |
|:---|:---|:---|
| `phase1_intermediate.json` | `tests/fixtures/apa_45refs/expected_phase1_intermediate.json` | deterministic (parser-only) |
| `phase3_resolved.json` | `tests/fixtures/apa_45refs/baseline_phase3_resolved.json` | LLM + PubMed variability |
| `report.md` | `tests/fixtures/apa_45refs/baseline_report.md` | Phase 4 audit output |
| `three_class_classification.json` | `tests/fixtures/apa_45refs/baseline_three_class_classification.json` | Day15 三分類 audit sidecar |

#### Step 4: 配置直後の sanity check
- `expected_phase1_intermediate.json` の `stage3_reference_blocks` 配列長 = 45
- `baseline_phase3_resolved.json` の解決率 (例: 40/45 = 88.9%) を README に記録
- `baseline_report.md` の重大エラー件数を README に記録
- `baseline_three_class_classification.json` の A/B/C/unknown 分布を README に記録

#### Step 5: 不安定 field の scrub 設計
Day8 `_scrub_volatile_lines` 思想に従い、`expected_phase1_intermediate.json` 比較対象から以下 field を除外:
- `input_file` (絶対 path、環境依存)
- `timestamp` 系 (生成日時)
- `mdpi_parser_version` 等の version 文字列 (将来 bump 時の test 不整合回避)

### 5.2 LLM / API cost 見積

| API | 想定 call 数 | 単価 | 合計 |
|:---|---:|:---|---:|
| Claude Sonnet 4.6 | 45 | ~$0.01-0.03/call | ~$0.5-1.0 |
| PubMed (NCBI key) | 45 | free | $0 |
| Crossref (未解決のみ) | ~5 | free | $0 |
| NLM Catalog (未解決のみ) | ~5 | free | $0 |
| **合計** | | | **< $1.5** |

1 回限り実行 → baseline 固定後 CI で再実行されない (Day11 同型運用).

### 5.3 再現性メタ情報

`tests/fixtures/apa_45refs/README.md` に baseline 生成時のメタ情報を記録:
- 実行日時 (例: 2026/05/17)
- LLM model (例: `claude-sonnet-4-6-20260301`)
- PubMed snapshot 日 (NCBI 側の latest)
- `main.py` version (現状未付与なら "post-Day15 (commit `f2b497f`)")

---

## 6. Test 設計 (8 tests)

`tests/test_integration_apa_45refs.py` を新規追加.

### 6.1 Base 5 tests (Vancouver 24refs と同型)

| # | test 名 | 性質 | 検証内容 |
|:---:|:---|:---|:---|
| 1 | `test_apa_45refs_routes_all_to_llm_path` | regression (deterministic) | 45 件全てが `is_mdpi_style()` で **False** を返す (Vancouver Veto が APA を確実に reject、Day9 効果の APA への拡張証明) |
| 2 | `test_phase1_reference_blocks_match_expected` | byte/structural (deterministic) | Phase 1 抽出結果が `expected_phase1_intermediate.json` の `stage3_reference_blocks` と一致 (volatile field 除外、Day8 `_scrub_volatile_lines` と同思想) |
| 3 | `test_phase1_extracts_45_reference_blocks` | 件数 (deterministic) | block 数 = 45 |
| 4 | `test_baseline_phase3_documents_resolution_count` | document-of-record | `baseline_phase3_resolved.json` の解決件数が README 記録値と一致 |
| 5 | `test_baseline_report_documents_audit_summary` | document-of-record | `baseline_report.md` ダッシュボードの「重大」件数が README 記録値と一致 |

### 6.2 APA 固有 3 tests (新規追加、Q5 (β) 承認)

| # | test 名 | 性質 | 検証内容 |
|:---:|:---|:---|:---|
| 6 | `test_apa_paren_year_pattern_detected_in_all_refs` | regression (parser-only) | 全 45 件 raw text に `(YYYY)` (1900-2099) パターン含む (APA 表記の中核特徴を fixture data 自体が満たすことを assert、test data 健全性保護) |
| 7 | `test_apa_ampersand_author_separator_present` | structural | 45 件中、最低 20 件以上が `, & ` (前著者列挙の最終境界 `& `) を含む (APA 7 規約特徴、parser 認識用) |
| 8 | `test_baseline_three_class_classification_distribution` | document-of-record | `baseline_three_class_classification.json` の A/B/C/unknown 分布が README 記録値と一致 (Day15 三分類 audit の APA 適用結果を凍結) |

### 6.3 共通仕様

- 全 test が **API key 不要** (parser-only / fixture 直読). CI で完全実行可能.
- pytest fixture `apa_45refs_dir` を module-scope で定義し path 解決を共通化.
- 比較時の volatile field 除外は既存 helper を再利用、無ければ `_scrub_volatile()` を test 内 private 関数で定義.

### 6.4 失敗時の運用

| 失敗パターン | 原因可能性 | 対応 |
|:---|:---|:---|
| test 4-5, 8 fail | baseline の document-of-record 値乖離 (LLM upgrade / PubMed snapshot / production code 改修) | Day9 (Z) 型の `pre-`/`post-` 検証で原因分析 → 意図的なら baseline & expected 更新の別 commit、意図外なら revert |
| test 1-3, 6-7 fail | production code 改修の意図しない regression | 改修内容確認 → APA routing の意図変更でなければ revert |

---

## 7. Commit 計画 (6-7 commits)

| 順 | commit 種別 | Phase | 内容 |
|:---:|:---|:---:|:---|
| (前) | `docs(spec)` | brainstorming 完了 | Day16 SPEC を `docs/sessions/day16/SPEC_apa_45refs_fixture.md` に archive |
| 1 | `test(fixtures)` | Phase 0a | `tools/build_apa_fixture.py` + `tests/fixtures/apa_45refs/input_References.docx` + `expected_phase1_intermediate.json` (Phase 0 sanity check 含む、ユーザー承認後の 3 論文反映) |
| 2 | `test(fixtures)` | Phase 0b | `baseline_phase3_resolved.json` + `baseline_report.md` + `baseline_three_class_classification.json` + `README.md` (1 回限り full pipeline 実行結果を凍結) |
| 3 | `test(integration)` | Phase 1 | `tests/test_integration_apa_45refs.py` の base 5 tests 追加 (Vancouver と同型) |
| 4 | `test(integration)` | Phase 2 | APA 固有 3 tests 追加 (test 6-8) |
| 5 | `docs(skill)` (optional) | Phase 3 | `skill_package/references/USAGE_QUICKSTART.md` 1.3 → 1.4 bump、APA 系も検証済み追記 (不要ならスキップ) |
| 6 | `docs(sessions)` | Phase 4 | `docs/sessions/day16/{README,DAY16_LESSONS_LEARNED}.md` archive |

→ 合計 **6-7 commits** (Day15 と同等規模).

---

## 8. 完了条件 (12 項目)

| # | 条件 | 確認方法 |
|:---:|:---|:---|
| 1 | `tools/build_apa_fixture.py` 存在 + 実行可能 | `uv run python tools/build_apa_fixture.py --help` |
| 2 | `input_References.docx` 存在 (45 段落) | `python -c "from docx import Document; d=Document('...'); assert len(d.paragraphs)>=45"` |
| 3 | `expected_phase1_intermediate.json` 存在 | `jq '.stage3_reference_blocks \| length' < ...` = 45 |
| 4 | `baseline_phase3_resolved.json` 存在 | file 存在 + JSON parseable |
| 5 | `baseline_report.md` 存在 | file 存在 + `## 1. ダッシュボード` 章節在り |
| 6 | `baseline_three_class_classification.json` 存在 | file 存在 + JSON parseable |
| 7 | `tests/fixtures/apa_45refs/README.md` 存在 (source 3 論文 citation + LICENSE 明記) | file 存在 + Markdown lint pass |
| 8 | `tests/test_integration_apa_45refs.py` 存在 (8 tests) | `uv run pytest tests/test_integration_apa_45refs.py --collect-only` = 8 items |
| 9 | 全 8 tests pass | `uv run pytest tests/test_integration_apa_45refs.py -v` |
| 10 | 既存 81 passed / 1 skipped が引き続き pass (regression なし) | `uv run pytest -v` = **89 passed / 1 skipped** |
| 11 | `docs/sessions/day16/SPEC_apa_45refs_fixture.md` archive 済み | file 存在 + Day15 SPEC と同等以上の構造 |
| 12 | `docs/sessions/day16/{README,DAY16_LESSONS_LEARNED}.md` archive 済み | Day9-15 と同型 |

---

## 9. Out of Scope (Day17+ 候補)

- **Cell 系 fixture** (Day17 で同型 pattern 適用予定)
- **APA fixture の領域追加** (現状 3 領域、将来 6 領域等)
- **live API test** (Day15 SPEC §8 と同様 skip-by-default 必要)
- **parser 改修** (現時点で必要性ゼロ見込み、実装段階で必要性発覚なら別 SPEC)
- **PMC OA 外の source** (preprint server、商業 journal の paywall 越え等)

---

## 10. 工数見積もり

| Phase | 内容 | 見積 | 累計 |
|:---:|:---|---:|---:|
| Pre | SPEC archive (本 commit) | 5min | 5min |
| Phase 0a | 論文選定 + docx 組成 + expected_phase1 生成 | 60min | 65min |
| Phase 0b | full pipeline 実行 + baseline 4 ファイル配置 + README 記載 | 30min | 95min |
| Phase 1 | base 5 tests 実装 (TDD) | 45min | 140min |
| Phase 2 | APA 固有 3 tests 実装 (TDD) | 30min | 170min |
| Phase 3 | USAGE_QUICKSTART bump (optional) | 15min | 185min |
| Phase 4 | day16 archive 作成 (README + LESSONS) | 30min | 215min |
| **合計** | | **~3.5h** | **3.5h** |

Day15 (~2h)、Day11 (~1h) との比較で妥当範囲 (45 件 baseline + 8 tests は工数増分が線形).

---

## 11. 参照

- Day9 SPEC: `docs/sessions/day9/SPEC_mdpi_fast_path_strict.md` (Vancouver Veto 設計の源流)
- Day11 fixture: `tests/fixtures/vancouver_24refs/README.md` (本 SPEC が踏襲する規約)
- Day15 SPEC: `docs/sessions/day15/SPEC_three_class_audit.md` (本 fixture が三分類 audit baseline 生成にも使われる根拠)
- Day15 LESSONS: `docs/sessions/day15/DAY15_LESSONS_LEARNED.md` §6.1, §7 (Day16 着手プロンプトテンプレート)

---

**承認**: 片山英樹 (brainstorming Q1-Q5 + Approach 全 6 sections)
**次工程**: writing-plans skill で implementation plan を作成
