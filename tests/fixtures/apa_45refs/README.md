# tests/fixtures/apa_45refs/

**APA 系 45-ref 統合 baseline (Day16 由来)**

## 由来

このディレクトリは、PMC OA 3 領域 (Psychology / Public Health / Psychology+Religion) の論文から 15 件ずつ計 45 件の APA 7 参考文献を JATS XML 経由で抽出し、`tools/build_apa_fixture.py` で番号付き段落 docx に統合した fixture を、Day9 Vancouver Veto の APA 適用 regression 保護と LLM 経由 parsing の document-of-record として固定保管する.

## ソース 3 論文 (Day16 Task 0 でユーザー承認)

| 領域 | PMC ID | DOI | Journal | 出版年 | LICENSE |
|:---|:---|:---|:---|:---:|:---|
| Psychology / Bereavement | PMC11601046 | 10.1080/07481187.2023.2203680 | Death Studies (Routledge) | 2023 | CC BY 4.0 |
| Public Health / Communication | PMC11404860 | 10.1080/10410236.2023.2255795 | Health Communication (T&F) | 2023 | CC BY 4.0 |
| Psychology / Religion & Death anxiety | PMC11165362 | 10.3389/fpsyg.2024.1398620 | Frontiers in Psychology | 2024 | CC BY 4.0 |

各論文の先頭 15 件を抽出. 抽出範囲は引用論文の bibliographic information (factual data) のみで、creative expression (abstract 本文等) は含まない. PMC OA CC BY 4.0 ライセンスの帰属表示として本 table にて明示.

選定タイトル:
- PMC11601046: "Development of an online service for coping with spousal loss by means of human-centered and stakeholder-inclusive design: the case of LEAVES"
- PMC11404860: "The Basis of Patient Resistance to Opportunistic Discussions About Weight in Primary Care"
- PMC11165362: "Death anxiety and religiosity in a multicultural sample: a pilot study examining curvilinearity, age and gender in Singapore"

注: 当初目標 (Psychology + Nursing + Public Health 各 1) のうち Nursing は CC BY + APA 7 + PMC OA を同時に満たす論文が確認できず、Psychology 2 + Public Health 1 の構成に変更.

## ファイル一覧と命名規約 (Day11 ハイブリッド)

| ファイル | 種別 | サイズ |
|:---|:---|---:|
| `input_References.docx` | 入力 (tools/build_apa_fixture.py で生成) | 41,238 |
| `expected_phase1_intermediate.json` | golden (deterministic, parser-only) | 14,089 |
| `baseline_phase3_resolved.json` | document-of-record (LLM + PubMed variability) | 189,420 |
| `baseline_report.md` | document-of-record (Phase 4 audit output) | 23,016 |
| `baseline_three_class_classification.json` | document-of-record (Day15 三分類 audit sidecar) | 5,239 |
| `README.md` | 本書 | — |

## baseline 生成時のメタ情報

- 実行日時: 2026-05-17 (Day16 Phase 0b)
- LLM model: claude-sonnet-4-6-20260301 (`.env` の `ANTHROPIC_MODEL`)
- PubMed snapshot: 2026-05-17 (NCBI 側 latest)
- main.py version: post-Day15 (commit `f2b497f`)
- pipeline 実測値:
  - **Phase 3 解決件数**: 25/45 (55.6%)
  - **三分類分布**: A=0, B=3, C=0, unknown=17 (Day22 SSL fix 後実測、Day20 baseline と同一: apa refs の unknown は非 MEDLINE 誌のため NLM SSL fix 対象外)
  - **report.md 重大件数**: 0

### Day22 SSL fix 後の更新 (2026-05-24)

Day22 で `nlm_catalog_check` に certifi 経由の SSL context を注入し
(commit `fix(nlm): inject certifi SSL context into _fetch_json`, SHA `685a600`)、
Rule 3 NLM Catalog 検索が正常に動作するようになった。

**apa_45refs では三分類分布の変化なし** (A=0, B=3, C=0, unknown=17 で Day20 と同一)。

理由: apa fixture の unknown 17 件は Psychology/Religion 系の非 MEDLINE 誌
(Religions, Death Studies etc.) への収録誌であり、NLM Catalog に ID そのものが
存在しないため、SSL fix 後も "esearch returned no NLM ID" で unknown に分類される。
(Day20 では "esearch network failed" で unknown に倒れていたが、原因区別が異なる
だけで最終分類は変わらない。)

report.md の軽微な差分 (ref #37 の reason 文言、ref #32/#34 の journal 名表示) は
Day22 実行時の Crossref API レスポンス変化によるもので、三分類分布への影響はない。

| 三分類 | Day20 (SSL 不良) | Day22 (SSL fix 後) |
|:---:|:---:|:---:|
| A | 0 | 0 |
| B | 3 | 3 |
| C | 0 | 0 |
| unknown | 17 | 17 |

### Vancouver fixture (24refs) との対比

| 指標 | apa_45refs (Day16) | vancouver_24refs (Day11) |
|:---|:---:|:---:|
| 解決率 | 25/45 = 55.6% | 22/24 = 91.7% |
| 重大件数 | 0 | 0 |
| 領域 | 多領域 (Psychology + Public Health) | 緩和ケア (Vancouver) |
| ソース | PMC OA 合成 | OneDrive 実機 |

APA 解決率が Vancouver より低い理由 (推定):
- Frontiers Psychology の社会心理 references の PubMed 非収録
- 政府文書 (#28 UK DHSC "Tackling Obesity")、書籍 (#30 "Laughter in interaction")、web page (#37 "Active ageing Centres") の含有
- 一部 ref で LLM Phase 2 が著者名を title に誤抽出 (#32, #34)

## 関連 test (`tests/test_integration_apa_45refs.py`、Day16)

| # | test 名 | 性質 | 検証 |
|:---:|:---|:---|:---|
| 1 | `test_apa_45refs_routes_all_to_llm_path` | regression (deterministic) | 45 件全てが `is_mdpi_style()` で False を返す (Vancouver Veto 適用) |
| 2 | `test_phase1_reference_blocks_match_expected` | byte/structural (deterministic) | Phase 1 抽出が `expected_phase1_intermediate.json` と一致 |
| 3 | `test_phase1_extracts_45_reference_blocks` | 件数 (deterministic) | block 数 = 45 |
| 4 | `test_baseline_phase3_documents_resolution_count` | document-of-record | 解決件数 = `25/45` 一致 |
| 5 | `test_baseline_report_documents_audit_summary` | document-of-record | report.md 重大件数 = `0` 一致 |
| 6 | `test_apa_paren_year_pattern_detected_in_all_refs` | parser-only | 全 45 件に `(YYYY)` 含む |
| 7 | `test_apa_ampersand_author_separator_present` | structural | ≥20 件が `, & ` を含む |
| 8 | `test_baseline_three_class_classification_distribution` | document-of-record | 三分類分布 = `{A=0, B=3, C=0, unknown=17}` 一致 (Day22 SSL fix 後も同一) |

**API key 不要**: 全 8 test は parser-only もしくは fixture 直読のため、`ANTHROPIC_API_KEY` / `NCBI_API_KEY` なしで CI 実行可能.

## baseline 更新の運用 (Day11 と同型)

| 変動原因 | 検出 | 対応 |
|:---|:---|:---|
| Anthropic LLM model upgrade | test 4-5, 8 で乖離 | Day16 相当の Phase 0b retry + baseline 更新 + test 期待値更新 (別 commit) |
| PubMed/Crossref/NLM 更新 | 同上 | 同上 |
| parser/main.py 改修 | test 1-3, 6-7 fail | 意図確認、意図的なら expected 更新、意図外なら revert |

## 命名対比 (既存 fixture との関係)

| 観点 | `mdpi_149refs/` | `vancouver_24refs/` | `apa_45refs/` (本ディレクトリ) |
|:---|:---|:---|:---|
| 全件 `expected_*` | ○ (fast-path byte 一致) | × (LLM variability) | × (LLM variability) |
| `baseline_*` 使用 | × | ○ | ○ |
| 件数 | 149 | 24 | 45 |
| ソース | OneDrive (実機) | OneDrive (実機) | PMC OA (合成) |
| 領域多様性 | 低 (1 docx) | 低 (1 docx) | 中 (3 領域、PMC 3 論文混在) |

---

**作成日**: 2026-05-17 (Day16 Phase 0b)
**作成者**: Claude Code (Sonnet 4.6)
**承認**: 片山英樹 (Hideki Katayama)
**関連 SPEC**: `docs/sessions/day16/SPEC_apa_45refs_fixture.md` (commit `4f1181d`、Task 0 で §3.2 確定値更新)
**関連 PLAN**: `docs/sessions/day16/PLAN_apa_45refs_fixture.md` (commit `0f0ed39`)
