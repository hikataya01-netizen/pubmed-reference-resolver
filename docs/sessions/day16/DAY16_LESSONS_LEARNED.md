# Day16 LESSONS LEARNED

**Day16 セッション (2026-05-17)**: APA 系 45-ref golden fixture 追加 (Day7 §9.3 long-term task 残 4 件目を完了) + 副次成果として Vancouver Veto regex を APA 7 disambiguation suffix まで拡張 (Day9 不変性の APA 7 完全準拠化)

---

## 1. セッション概要

### 1.1 背景

Day15 末時点で Day7 §9.3 long-term task の残 3 件 (APA / Cell fixture、MCP/hook 配線、GitHub push) のうち、ユーザーは Day16 task として **APA / Cell 系 golden fixture** を選択. Day15 LESSONS §7 パターン 1 のテンプレート (Day7 §9.3 残 APA fixture) を起点として、brainstorming → SPEC → writing-plans → TDD (subagent-driven-development) の 4 段階フローを順に適用.

### 1.2 brainstorming 段階 (Q1-Q5 + Approach)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | 入力 docx の入手方法 | (c) PMC OA 論文から抽出 |
| Q2 | scope | (β) APA のみ Day16、Cell は Day17+ |
| Q3 | PMC OA 論文選定方法 | (iii) 領域未指定 + Claude 選定 |
| Q4 | ref 件数規模 | (γ) ~40-50 件 (2-3 論文) |
| Q5 | test 構成粒度 | (β) 5 base + APA 固有 3 = 8 tests |
| Approach | 全体戦略 | (A) 多領域 3 論文 × 15 件 ≈ 45 件 |

### 1.3 SPEC (commit `4f1181d`)

334 行の SPEC を `docs/sessions/day16/SPEC_apa_45refs_fixture.md` に archive. 11 章構成 (背景・アーキテクチャ・PMC OA 論文選定 protocol・docx 組成・baseline 生成・8 tests・commit 計画・12 完了条件・Out of Scope・工数見積もり・参照).

### 1.4 PLAN (commit `0f0ed39`)

1492 行の implementation plan を `docs/sessions/day16/PLAN_apa_45refs_fixture.md` に archive. Task 0-13 + Verification V1-V4 + Notes for Implementing Agent で構成. bite-sized step (2-5 分粒度) で記述.

---

## 2. 実装段階の経緯 (6 commits)

### Phase 0a: docx 組成 + Phase 1 expected (commit `c35211f`)

- Task 0 (ユーザー承認 gate): PMC OA 3 領域候補を NCBI esearch で探索. 当初 Psychology + Nursing + Public Health を目標も、Nursing で CC BY + APA 7 + PMC OA を同時に満たす論文が確認できず、最終 Psychology 2 + Public Health 1 の構成に変更. ユーザー承認後 SPEC §3.2 確定値で更新.
- Task 1 (subagent dispatch): `tools/build_apa_fixture.py` (~410 行) を実装. 二段レビュー (spec compliance + code quality) いずれも合格. CACHE_DIR を repo 絶対パスに変更、unused import 削除の 2 件を minor fix で適用.
- Task 2 (controller 直接実行): SSL 証明書問題で live API fetch 失敗 → Task 0 で取得済の `/tmp/sample_*.xml` を `.cache/pmc_xml/` にコピーして利用. 当初 Phase 1 抽出が 43/45 件で 2 件欠落 (refs 28, 37) を発見 → 原因は `<collab>` (組織著者) を build script が未対応 → `_format_authors` 拡張で 45/45 件抽出に解消.

### Phase 0b: full pipeline + 3 baselines (commit `d6e31c3`)

- Task 3 (controller 直接実行): `main.py --phase 4` で full pipeline 実行 (LLM cost ~$0.5). 出力:
  - Phase 3 解決 25/45 (55.6%) — Vancouver fixture 22/24 (91.7%) より低い
  - 重大 0 件
  - 三分類分布: A=4, B=0, C=0, unknown=16 (Crossref/NLM の SSL 問題で大半 unknown に倒れる graceful fail-soft 動作)
- README.md にメタ情報 (実行日時、LLM model、解決率、三分類分布、Vancouver fixture との対比) を記載.

### Phase 1: base 5 tests + regex 拡張 (commit `f7d5cb2`)

- Task 4-8 (subagent dispatch): base 5 tests を作成. Test 1 (Vancouver Veto routing) が #32, #34 で FAIL.
  - **発見**: APA 7 同一著者同一年 disambiguation suffix `(2020a)`, `(2020b)` を Vancouver Veto regex (4 桁固定) が捕捉せず、MDPI publisher (Religions 誌) の disambiguation 付き refs が fast-path に流れる事象.
  - subagent が CLAUDE.md §13 に従い独断改修せず BLOCKED で停止、Pattern A/B/C を提示.
  - ユーザーが Pattern B (regex 拡張 + LESSONS 記録) を承認.
  - mdpi_parser.py:403 の regex を `\((?:19|20)\d{2}[a-z]?\)` に拡張 (1 文字追加). Day9 不変性を APA 7 完全準拠に拡張. inline コメントで Day16 経緯明記.
  - 5 tests 全 PASS、既存 81 passed → 86 passed (regression なし).

### Phase 2: APA 固有 3 tests (commit `07eb100`)

- Task 9-11 (subagent dispatch): 3 tests を追加.
  - test 6: 全 45 件に `(YYYY[a-z]?)` 含む (健全性)
  - test 7: ≥20 件に `, & ` 含む (APA 7 author separator)、実測 38/45 で余裕クリア
  - test 8: 三分類分布 {A=4, unknown=16} 一致 (document-of-record)
- 全 8 tests PASS、86 → 89 passed.

### Phase 3: USAGE_QUICKSTART 1.4 bump (commit `464faff`)

- §X 変更履歴に「1.4 (Day16 更新)」 entry 追加. Day16 の 4 項目 (regression 保護拡張・regex 拡張・三分類 baseline・新 tool 追加) を要約.

### Phase 4: Day16 archive (本 commit、Phase 4 で実施)

- README.md / DAY16_LESSONS_LEARNED.md を archive.

---

## 3. 設計判断と検証

### 3.1 brainstorming Q1-Q5 各選択肢の trade-off

| Q | 採択 | 主な refused 案 | 採択根拠 |
|:---:|:---|:---|:---|
| Q1 | (c) PMC OA から抽出 | (a) 実機 docx 提供 / (b) 合成 / (d) 1 系統 | 実機データなし、合成は parser 検証品質が劣る、公開論文が最も再現可能性高 |
| Q2 | (β) APA のみ | (α) 両方 / (γ) Cell のみ / (δ) 混在 | scope 制御、Cell は Day17+ で同型 pattern 適用予定 |
| Q3 | (iii) Claude 領域未指定で選定 | (i) 緩和ケア限定 / (ii) ユーザー指定 / (iv) 1 大型 review | parser の汎用性検証に最適 |
| Q4 | (γ) 40-50 件 | (α) 10 件 / (β) 20 件 / (δ) 150 件 | Vancouver 24 件の 2 倍、parser 多様性検証に十分 |
| Q5 | (β) 5 base + APA 3 = 8 tests | (α) 5 tests / (γ) 3 tests / (δ) Claude 判断 | 高品質、APA 7 固有特徴の明示的 assert |

### 3.2 Approach A 採択根拠

3 publisher (Routledge 2 + Frontiers 1) で領域多様性確保しつつ、全 CC BY 4.0 で license 透明性高い. 工数 ~3.5h、LLM cost <$1.5 の見積りも適正.

### 3.3 PMC 論文選定の試行錯誤

当初 Psychology + Nursing + Public Health を目標としたが:

- **Psychooncology (Wiley)**: Vancouver numerical style → 不採用
- **Front Public Health (Frontiers)**: 一部 paper が Vancouver style → 不採用
- **BMC Nurs (BMC)**: Vancouver style → 不採用
- **Public Health Nurs (Wiley)**: CC BY-NC-ND + 混在 format → 不採用
- **Aging & Mental Health (Routledge)**: CC BY-NC-ND → 不採用 (license ND 制約)
- **J Health Psychol (Sage)**: 圧縮 initials (Sage variant) → 不採用 (APA 純粋性低)
- **J Behav Med (Springer)**: citation-alternatives 二重形式 → 不採用 (build script 複雑化)

最終採択:
- **Death Studies (Routledge, PMC11601046)**: 純 APA 7 ✓
- **Health Communication (T&F, PMC11404860)**: 純 APA 7 ✓
- **Frontiers in Psychology (PMC11165362)**: 純 APA 7 (XML `<name>` 形式のため build script 側で structured fields 再組成必須)

---

## 4. 実機検証結果

### 4.1 PMC OA 3 論文選定結果

| 領域 | PMC ID | DOI | Journal | 出版年 | LICENSE |
|:---|:---|:---|:---|:---:|:---|
| Psychology / Bereavement | PMC11601046 | 10.1080/07481187.2023.2203680 | Death Studies (Routledge) | 2023 | CC BY 4.0 |
| Public Health / Communication | PMC11404860 | 10.1080/10410236.2023.2255795 | Health Communication (T&F) | 2023 | CC BY 4.0 |
| Psychology / Religion & Death anxiety | PMC11165362 | 10.3389/fpsyg.2024.1398620 | Frontiers in Psychology | 2024 | CC BY 4.0 |

### 4.2 Phase 3 PubMed 解決率

| Fixture | 解決率 | 主因 (推定) |
|:---|:---:|:---|
| vancouver_24refs (Day11) | 22/24 = 91.7% | 医学領域に集中、PubMed coverage 高 |
| apa_45refs (Day16) | 25/45 = 55.6% | 社会心理 + 政府文書 + 書籍含む |

低解決率の主因:
- Frontiers Psychology の社会心理 references の PubMed 非収録 (~10 件)
- 政府文書 #28 (UK DHSC), 書籍 #30 (Glenn), web page #37 (AIC) (~3 件)
- 一部 ref で Phase 2 LLM が著者名を title に誤抽出 (#32, #34、約 2 件)

### 4.3 Day15 三分類分布

`baseline_three_class_classification.json` (20 entries = unresolved refs):
- **A** (真の捏造、Crossref 404): 4 件
- **B** (MEDLINE 非収録誌): 0 件
- **C** (収録誌 indexing 漏れ): 0 件
- **unknown** (network error fail-soft): 16 件

B=0 / C=0 は Crossref/NLM 通信時の SSL 証明書問題 (Mac Python chain) によるネットワークエラー → graceful unknown fail-soft (Day15 設計通り) が機能した結果. 将来 SSL 問題解消後の再生成では B/C 分布が出現するため、baseline 更新を要する.

---

## 5. 教訓 (D16-1)

### 5.1 D16-1: APA 7 disambiguation suffix の発見と Vancouver Veto 拡張

**事象**

- Test 1 (`test_apa_45refs_routes_all_to_llm_path`) が refs #32, #34 で FAIL.
- 該当 refs:
  - #32: `Ackert, M., ... (2020a). ... Religions, 11, 1-22. https://doi.org/10.3390/rel11020057`
  - #34: `Ackert, M., ... (2020b). ... Religions, 11, 1-35. https://doi.org/10.3390/rel11110577`
- 両者は MDPI publisher の "Religions" 誌掲載で、APA 7 同一著者同一年 disambiguation suffix (`2020a`, `2020b`) を持つ.

**原因**

Day9 Vancouver Veto regex `\((?:19|20)\d{2}\)` は paren 内に 4 桁数字のみを要求. APA 7 disambiguation suffix の `(2020a)` は 4 桁 + 1 字小文字なので捕捉漏れ. fast-path 判定の (a) パターン `\s\d{4}\s*,\s*\d+` (` 2020, 11`) でマッチし、誤って fast-path に流れた.

**学び**

1. **golden fixture の効用**: 単一系統 (Vancouver) で確認された invariant が、別系統 (APA) で意外な逸脱を示す事例. 多領域 fixture が Day9 不変性の robustness 検証に必須.
2. **regex の脆弱性**: 「4 桁年」は世界共通だが、表記 (`(2020)` vs `(2020a)` vs `(2020/2)`) は学術スタイルで異なる. 単純な「4 桁数字」regex は学術領域全体には不十分.
3. **subagent の judgment 力**: implementer subagent が CLAUDE.md §13 (想定外時の振る舞い) に従い独断改修せず BLOCKED で Pattern A/B/C を提示. これにより人間判断と適切な分担が成立.

**適用範囲**

- mdpi_parser.py の他の regex (例: pattern (a) `\s\d{4}\s*,\s*\d+`) も類似の表記揺れ感受性を持つ可能性. Cell fixture (Day17+) や APA 6 (`(2020)` だが period 後置等) を追加する際に再検証推奨.
- 同型の他 dependency (例: Phase 2 LLM prompt) が APA 7 disambiguation を理解しているかも未検証. Day17+ で改めて確認できる.

**Pattern B 採択の根拠**

- A (regex のみ拡張): 最小だが将来の保守者が変更意図を追えない
- B (regex + LESSONS 記録 + inline comment): バランス、Day9 不変性の意図的拡張を明示
- C (test 緩めて fast-path 受容): Day9 不変性 (全 paren year は LLM) を壊すため不採択

---

## 6. 残存タスク (Day17 以降)

### 6.1 Day7 §9.3 long-term task の達成状況 (Day16 末)

| タスク | 状態 | 残し方 |
|:---|:---:|:---|
| Vancouver golden fixture | ✅ Day11 | — |
| Day9 (Z) 未解決 2 件 MEDLINE 調査 | ✅ Day13 | — |
| Day13 §6 案 A: 3 分類 audit logic | ✅ Day15 | — |
| APA 系 golden fixture | ✅ Day16 (本日) | — |
| **Cell 系 golden fixture** | ⏳ Day17+ | Day16 PLAN 同型適用 |
| **MCP/hook 経由 Stage 3 配線** | ⏳ Day17+ | 設計議論大、複数セッション |
| **GitHub remote 追加と push** | ⏳ Day17+ | secret scan + README 整備、外部公開判断要 |

### 6.2 Day16 が生成した新規候補

- [ ] **Cell 系 fixture** (Day16 と同型 pattern を Cell Press 系 APA-like style 採用論文に適用)
- [ ] **APA fixture の領域拡充** (現状 3 領域 → 6 領域、Nursing 系を含めた多角化)
- [ ] **三分類 audit の SSL 問題解消後 baseline 再生成** (B/C 分布の document-of-record 確立)
- [ ] **`tools/build_apa_fixture.py` のテスト追加** (`_normalize_initials` の 5 cases unit test を `tests/` 配下に正式昇格)
- [ ] **Phase 2 LLM の APA 7 disambiguation 理解確認** (refs #32, #34 の title 誤抽出の根本原因解明)
- [ ] **`integration/tests/test_mdpi_parser.py` の `src` module 問題解消** (pre-existing collection error)

### 6.3 Day17+ 推奨着手順

1. Cell 系 fixture (本 plan 同型適用、所要 ~3h、最高優先度)
2. 三分類 audit の SSL 問題解消後 baseline 再生成 (中優先度)
3. GitHub remote + push (secret scan 要、公開判断要、~2h)
4. MCP/hook 経由 Stage 3 配線 (設計議論大、複数セッション、最後)

---

## 7. 次セッション再開時のプロンプトテンプレート

### パターン 1: Day17 として Cell 系 fixture

```
Day17 として、Cell 系の golden fixture を新規追加します
(Day16 apa_45refs と同型 pattern). PMC OA Cell Press / Mol Cell /
Cell Reports 等 (CC BY を要) で APA-like reference スタイル
採用論文を 3 本選定し、15 件 × 3 = 45 件抽出. TDD (subagent-driven)
で進めてください. tools/build_cell_fixture.py は
tools/build_apa_fixture.py を template に組み立て.
```

### パターン 2: Day16 §6.2 拡張 (三分類 baseline 再生成)

```
Day17 として、Day16 で凍結した apa_45refs 三分類 baseline の
SSL 問題解消後再生成を実施します. 環境の SSL 証明書を修復し
(certifi 等)、Crossref + NLM 経由で B/C 分類が確実に出現する
よう確認してから baseline を更新. test 8 の期待値も更新.
```

### パターン 3: GitHub remote + push (Day15 末から繰越)

```
Day17 として、本プロジェクトを GitHub に push します.
remote 設定 → 既存 59 commits + 全 fixture (mdpi_149refs,
vancouver_24refs, apa_45refs, three_class_classification) を
含めて push. 公開リポジトリ vs プライベート の選択、
README.md の整備、.gitignore 最終確認、secret scan を含めて
段階確認しながら進めてください.
```

### パターン 4: MCP/hook 経由 Stage 3 配線 (Day15 末から繰越)

```
Day17 として、Stage 3 (Claude UI 起動の自動配線) を実装します.
MCP server もしくは hook 経由で、Claude Code → ローカル
コマンド → docx 入力 → audit 出力 → Claude UI へ結果返却の
パイプラインを設計. 議論大規模のため SPEC 段階まで複数セッション
覚悟.
```

---

**記録完了日**: 2026-05-17 (Day16)
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day16 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day16.md` (Claude Opus 作成予定)
**ステータス**: Day16 archive 完成、Day17 着手準備完了 (4 パターンプロンプトあり)
