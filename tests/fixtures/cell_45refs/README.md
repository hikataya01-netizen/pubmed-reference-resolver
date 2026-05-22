# tests/fixtures/cell_45refs/

**Cell-style 45-ref 統合 baseline (Day17 由来)**

## 由来

このディレクトリは、PMC OA 3 iScience (Cell Press) 論文から 15 件ずつ計 45 件の Cell-style 参考文献を JATS XML 経由で抽出し、`tools/build_cell_fixture.py` で番号付き段落 docx に統合した fixture を、Day9 Vancouver Veto + Day16 拡張 regex の Cell 適用 regression 保護と LLM 経由 parsing の document-of-record として固定保管する.

## ソース 3 論文 (Day17 Task 0 でユーザー承認)

| 領域 | PMC ID | DOI | Journal | 出版年 | LICENSE |
|:---|:---|:---|:---|:---:|:---|
| Molecular Biology | PMC13080398 | 10.1016/j.isci.2025.113995 | iScience (Cell Press) | 2026 | CC BY 4.0 |
| Biomedical / Nanomedicine | PMC12918234 | 10.1016/j.isci.2025.114547 | iScience (Cell Press) | 2026 | CC BY 4.0 |
| AI / Agricultural Engineering | PMC12915276 | 10.1016/j.isci.2025.114411 | iScience (Cell Press) | 2026 | CC BY 4.0 |

各論文の先頭 15 件を抽出. 抽出範囲は引用論文の bibliographic information (factual data) のみで、creative expression (abstract 本文等) は含まない. PMC OA CC BY 4.0 ライセンスの帰属表示として本 table にて明示.

選定タイトル:
- PMC13080398: "Two domains of Nrf2 cooperatively bind CBP, a CREB binding protein, and synergistically activate transcription"
- PMC12918234: "Nanoencapsulated senotherapeutic compounds targeting connexin-43 for enhanced wound healing"
- PMC12915276: "Explainable transformer framework for fast cotton leaf diagnostics and fabric defect detection"

## ファイル一覧と命名規約 (Day11 ハイブリッド)

| ファイル | 種別 | サイズ |
|:---|:---|---:|
| `input_References.docx` | 入力 (tools/build_cell_fixture.py で生成) | 41,548 |
| `expected_phase1_intermediate.json` | golden (deterministic, parser-only) | 13,931 |
| `baseline_phase3_resolved.json` | document-of-record (LLM + PubMed variability) | 201,852 |
| `baseline_report.md` | document-of-record (Phase 4 audit output) | 18,067 |
| `baseline_three_class_classification.json` | document-of-record (Day15 三分類 audit sidecar) | 4,055 |
| `README.md` | 本書 | — |

## baseline 生成時のメタ情報

- 実行日時: 2026-05-18 09:19 (Day17 Phase 0b)
- LLM model: claude-sonnet-4-6-20260301 (`.env` の `ANTHROPIC_MODEL`)
- PubMed snapshot: 2026-05-18 (NCBI 側 latest)
- main.py version: post-Day16 (commit `705b141`)
- pipeline 実測値:
  - **Phase 3 解決件数**: 30/45 (66.7%)
  - **三分類分布**: A=1, B=6, C=0, unknown=8 (Day20 改修後実測、Day17 baseline A=14 から大幅減少) (合計 15 件 = 未解決 ref の audit)
  - **report.md 重大件数**: 0

### Vancouver / APA fixture との対比

| 指標 | cell_45refs (Day17) | apa_45refs (Day16) | vancouver_24refs (Day11) |
|:---|:---:|:---:|:---:|
| 解決率 | 30/45 = 66.7% | 25/45 = 55.6% | 22/24 = 91.7% |
| 重大件数 | 0 | 0 | 0 |
| 領域 | 分子生物 + 生医 + AI 工学 | Psychology + Public Health | 緩和ケア |
| ソース | PMC OA 合成 (Cell Press) | PMC OA 合成 (Routledge/Frontiers) | OneDrive 実機 |
| 三分類 A 件数 | 14 (Crossref で 404 多発) | 4 | (3 分類 audit は Day15 で追加、Day11 baseline では未計測) |

### Day16 との対比: 三分類分布の差異

Day16 (apa_45refs) では SSL 問題で大半が unknown (16/20) に倒れたが、Day17 (cell_45refs) では unknown=1 / A=14 という分布で、Crossref API が正常動作した結果. A=14 の多さは AI 工学領域 (PMC12915276) の book chapter / web page / industry report 系 references が Crossref で 404 を返した結果と推定. 真の捏造ではなく Crossref 未登録の正当な refs を A 分類している可能性 → Day18+ で false positive 抑制の改修候補 (例: book chapter の `<element-citation publication-type="book">` 等を `<collab>`+book 信号で B 分類に振る).

## 関連 test (`tests/test_integration_cell_45refs.py`、Day17)

| # | test 名 | 性質 | 検証 |
|:---:|:---|:---|:---|
| 1 | `test_cell_45refs_routes_all_to_llm_path` | regression (deterministic) | 45 件全てが `is_mdpi_style()` で False を返す (Vancouver Veto + Day16 拡張 regex 適用) |
| 2 | `test_phase1_reference_blocks_match_expected` | byte/structural (deterministic) | Phase 1 抽出が `expected_phase1_intermediate.json` と一致 |
| 3 | `test_phase1_extracts_45_reference_blocks` | 件数 (deterministic) | block 数 = 45 |
| 4 | `test_baseline_phase3_documents_resolution_count` | document-of-record | 解決件数 = `30/45` 一致 |
| 5 | `test_baseline_report_documents_audit_summary` | document-of-record | report.md 重大件数 = `0` 一致 |
| 6 | `test_cell_paren_year_pattern_detected_in_all_refs` | parser-only | 全 45 件に `(YYYY[a-z]?)` 含む |
| 7 | `test_cell_and_author_separator_present` | structural | ≥20 件が `, and ` を含む |
| 8 | `test_baseline_three_class_classification_distribution` | document-of-record | 三分類分布 = `{A=1, B=6, C=0, unknown=8}` 一致 (Day20 改修後) |

**API key 不要**: 全 8 test は parser-only もしくは fixture 直読のため、`ANTHROPIC_API_KEY` / `NCBI_API_KEY` なしで CI 実行可能.

## baseline 更新の運用 (Day11 と同型)

| 変動原因 | 検出 | 対応 |
|:---|:---|:---|
| Anthropic LLM model upgrade | test 4-5, 8 で乖離 | Day17 相当の Phase 0b retry + baseline 更新 + test 期待値更新 (別 commit) |
| PubMed/Crossref/NLM 更新 | 同上 | 同上 |
| parser/main.py 改修 | test 1-3, 6-7 fail | 意図確認、意図的なら expected 更新、意図外なら revert |

## 命名対比 (既存 fixture との関係)

| 観点 | `mdpi_149refs/` | `vancouver_24refs/` | `apa_45refs/` | `cell_45refs/` (本ディレクトリ) |
|:---|:---|:---|:---|:---|
| 全件 `expected_*` | ○ | × | × | × |
| `baseline_*` 使用 | × | ○ | ○ | ○ |
| 件数 | 149 | 24 | 45 | 45 |
| ソース | OneDrive (実機) | OneDrive (実機) | PMC OA (Routledge/T&F/Frontiers) | PMC OA (Cell Press 1 publisher) |
| 領域多様性 | 低 | 低 | 中 | 高 (3 域、内 license 全 CC BY) |
| 三分類 audit 動作 | (未測定) | (未測定) | 大半 unknown (SSL 問題) | A=14 多発 (Crossref 正常動作) |

---

**作成日**: 2026-05-18 (Day17 Phase 0b)
**作成者**: Claude Code (Sonnet 4.6)
**承認**: 片山英樹 (Hideki Katayama)
**関連 SPEC**: `docs/sessions/day17/SPEC_cell_45refs_fixture.md` (commit `c4ac9c8`)
**関連 PLAN**: `docs/sessions/day17/PLAN_cell_45refs_fixture.md` (commit `4fcb1a6`)
