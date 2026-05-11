# DAY9_LESSONS_LEARNED.md

**Day9 = Vancouver/AMA 系 parser 改善 (brainstorming → SPEC → TDD → 実機検証)**

**作成日**: 2026/05/11
**作成者**: Claude Code (Sonnet 4.6)
**配置**: `docs/sessions/day9/DAY9_LESSONS_LEARNED.md`
**対応 commit 範囲**: `5f8bbf0` 〜 `0c1b56d` + 本書の archive commit (計 4 commits)
**対応する指示書**: なし (先生からの単一プロンプトで開始、Day7 §8.6 §9.2 を起点とする)

---

## 0. 本書の位置づけ

Day9 は Day7 PHASE_0_VERIFICATION_REPORT §9.2 の中期タスク 1 件 (「Vancouver/AMA 系 parser 改善」) を **brainstorming → SPEC → TDD → 実機検証**の 4 段階フローで対応した. Day8 までの「単一プロンプト → 直接 TDD」より一段階手厚いプロセスを採用したのは、先生のプロンプト中の「**TDD で検討してください**」というキーワードが「実装前の design 議論」を示唆していたため.

本書は以下を記録する:

1. brainstorming Q1-Q3 議論の詳細 (data-driven な合意形成)
2. SPEC 文書化と TDD 実装の流れ
3. **(Z) 実機検証で得られた劇的な成果** (解決率 14/24 → 22/24)
4. Day9 で抽出された教訓 4 件 (D9-1 〜 D9-4)
5. main branch 最終形状と Day10 への引継ぎ

---

## 1. Day9 のフェーズ構成

4 commits は 4 つの自然な作業フェーズに対応:

| フェーズ | commit | 達成 | 採用 skill |
|:---:|:---:|:---|:---|
| 1 | `5f8bbf0` | brainstorming → SPEC 初版 commit | brainstorming |
| 2 | `ab25630` | TDD で実装 (RED → GREEN cycle) | test-driven-development |
| 3 | `0c1b56d` | (Z) 実機検証後、SPEC update commit | (なし、SPEC update は標準作業) |
| 4 | (本 commit) | Day9 archive (README + LESSONS) commit | (なし、archive 慣例) |

---

## 2. フェーズ 1: brainstorming → SPEC (`5f8bbf0`)

### 2.1 起点

先生の指示「TDD で検討」を受けて brainstorming skill を起動. brainstorming skill の HARD-GATE は「**設計が user 承認されるまで実装に入らない**」.

### 2.2 探索フェーズ

`mdpi_parser.py:is_mdpi_style()` の現状ロジック (line 372-412) を読み、Stage 2 OneDrive 入力 24 件の raw_text を全件確認. MDPI 形式 vs Vancouver/AMA 形式の決定的な区別 markers を 4 観点 (著者区切り / 年位置 / pages / DOI prefix) で整理.

### 2.3 Q1-Q3 議論 (data-driven)

**Q1: 改修方針の大筋** → 案 A (regex 追加で is_mdpi_style 強化) を採用 (案 C ホワイトリスト全面 refactor / A+C 組合せ は規模過大で不採用).

**Q2: 採用 marker のセット** → **M1 (`(YYYY)` 括弧年) のみ**. 4 markers × 2 corpus の hit rate を実測:

| Marker | MDPI 149-ref hit | Vancouver 24-ref hit |
|:---|:---:|:---:|
| **M1: `(YYYY)` 括弧年** | **0/149** | **24/24** |
| M2: Vol(Iss):Pages | 0/149 | 15/24 |
| M3: doi: 10.xxx (https なし) | **1/149 (#124)** ⚠️ | 19/24 |
| M4: カンマ区切り著者連鎖 | **2/149 (#126, #132)** ⚠️ | 7/24 |

→ M1 単独で **MDPI 0 件影響 + Vancouver 100% 捕捉** という完璧な結果. M2-M4 は M1 の真サブセットまたは regression リスクあり.

**Q3: 既存 Vancouver markers の扱い** → **撤去**. 既存 markers (line 405-408) を実測:
- 既存 marker A (`Smith J, Lee K,`): Vancouver 1/24 (#6 のみ)
- 既存 marker B (`;Vol:Pages`): Vancouver 0/24 (完全に機能していない)

→ Day8 D8-2 (重複 code smell の事前検出) の応用. M1 単独で全件捕捉するため、既存 markers は撤去.

### 2.4 SPEC 文書化

`docs/sessions/day9/SPEC_mdpi_fast_path_strict.md` (300 行) を作成. brainstorming skill default の `docs/superpowers/specs/` ではなく、本プロジェクト慣例 `docs/sessions/dayN/` に配置 (Day9 archive 統合性を優先). user review approval 取得後、commit `5f8bbf0`.

---

## 3. フェーズ 2: TDD 実装 (`ab25630`)

### 3.1 RED — 4 新 test を `tests/test_mdpi_parser.py` に追加

SPEC §5.2 では test 3 を 1 件としていたが、TDD skill "One behavior" rule に従い 2 件に細分化:

| # | test 名 | 性質 |
|:---:|:---|:---|
| 1 | `test_is_mdpi_style_returns_false_for_paren_year_vancouver` | RED → GREEN, Stage 2 #1/#2/#11 で False 期待 |
| 2 | `test_is_mdpi_style_still_returns_true_for_pure_mdpi` | regression 保護, MDPI #1/#51/#141 で True 期待 |
| 3a | `test_is_mdpi_style_does_not_match_non_year_parens` | edge case, `(2nd ed.)` 等で True 維持 |
| 3b | `test_is_mdpi_style_paren_year_dominates_over_mdpi_signals` | M1 dominance, MDPI text + `(1995)` で False |

**RED 確認**: 2 件 fail (`feature missing` for new behavior、typo / setup ミスではない).

### 3.2 GREEN — 順序問題の発覚と修正

SPEC §4.2 では M1 を旧 (d) ブロック位置に置く設計だったが、TDD GREEN verify 段階で **想定外の test fail** が発覚:

```
AssertionError: M1 marker `(YYYY)` は他 MDPI signals より優先される設計.
got True for raw='Smith, J.; Lee, K. Title of paper. Journal Name 2024, 10, 100-110. First study b...'
```

真因解析: M1 が (d) 位置だと、(b) `doi.org/` または (a) `\s\d{4}\s*,\s*\d+` で先に True を返してしまい、M1 まで到達しない. Stage 2 の Vancouver ref はほぼ全件が `doi.org/` を含むため、(b) で MDPI 判定される.

**修正**: M1 を**著者チェック直後**に moved up (Vancouver Veto = 最優先 early return). 設計の本質 (Vancouver indicator が dominant) は SPEC 初版から不変、配置位置のみ実装段階で修正.

### 3.3 GREEN 確認

- mdpi_parser test: **8/8 passed** (既存 4 + 新 4)
- 全体: **66 passed, 1 skipped** (Day8 末 62 → +4)

### 3.4 commit と SPEC deviation の明記

commit `ab25630` の commit message に 2 deviation (test 細分化 / 順序修正) を完全に documented. これにより後日の git log だけで実装段階の発見を追える.

---

## 4. フェーズ 3: (Z) 実機検証

### 4.1 検証目的

Day8 D8-1 (TDD だけでは捕捉できない問題は production-like 検証で補完する) の実践. Day7 で失敗した Stage 2 retry を以下の組合せで再実行:

| 比較対象 | env -u | main.py | mdpi_parser.py |
|:---|:---:|:---|:---|
| `bnbhm6n67` (Day7 retry) | 有り (workaround) | 旧 | 旧 |
| `bvmp5zypx` (Day8 (V)) | 無し | 修正 | 旧 |
| **`btjq02ug7` (Day9 (Z))** | **無し** | **修正** | **修正 (Veto)** |

### 4.2 検証結果 — 劇的な成果

| 項目 | Day7-8 retry | **Day9 (Z)** | 効果 |
|:---:|:---:|:---:|:---|
| MDPI fast-path 件数 | 21/24 | **0/24** | ✅ Vancouver Veto 完璧発動 |
| LLM path 件数 | 3/24 | **24/24** | ✅ 全件 LLM 経路 |
| **解決率** | 14/24 (58.3%) | **22/24 (91.7%)** | **+8 件 / +33% pt** |
| **重大エラー** | 4 件 (3 件 false positive + 1 件本物) | **0 件** | **すべて parser 起因の false positive と判明** |
| **重複引用** | 1 件 (Ref #21=#8) | **0 件** | Day7 「本物の MAJOR」も実は false positive と判明 |
| journal_mismatch_audit | 3 件 | 22 件 (richness 増、全件 67-100% 一致) | LLM 抽出により audit data 品質向上 |
| 所要時間 | 35-61 秒 | 148 秒 | 4x 増 (LLM ボトルネック) |

### 4.3 Title 抽出品質の劇的改善 (8 件全て修正)

| ref | OLD (parser 誤認) | **NEW (LLM 正解)** |
|:---:|:---|:---|
| 1 | `, & HoekstraWeebers, J.E` | `Family-oriented multilevel study on the psychological f...` |
| 2 | `K, Armaly, J., Swieter A` | `Impact of Parental cancer on children` |
| 7 | `K, Baer, L., Pirl, W.F.,Muriel, A.C` | `Parenting Changes in Adults Cancer` |
| 11 | `Romer, G,, Piha, J` | `Factors associated with the mental health of adolescent...` |
| 16 | `Kroll L., Burke, O., Lee, J., Jones ,A., Stein A` | `Qualitative interview study of communication between pa...` |
| 19 | (空) | `Breast cancer in the family--children's perceptions of ...` |
| 21 | (空) | `Parenting experiences during cancer` |
| 22 | `and Jankovic, M` | `How to explain the parents cancer to their children: a ...` |

→ Day7 §8.5 の「parser 起因 false positive 重大エラー 3 件」+ §8.6 の「未解決 5 件 (title 空)」が **すべて解消**.

### 4.4 残存 2 件の傾向

未解決 22 → 残り 2 件 (Ref #17 Davey 2003 / Ref #22 Gallina 2016) は LLM 解析でも title は正しく取れているが PubMed/DOI で hit しない. **MEDLINE 非収録誌の可能性が高い** (parser/LLM の問題ではなく対象論文側の問題).

---

## 5. フェーズ 4: SPEC update (`0c1b56d`)

(Z) 実機検証で得たデータと、TDD 実装段階で発覚した順序問題を SPEC に反映:

- §4.1: Vancouver Veto 配置位置の修正を明記
- §4.2: Before/After を「旧設計」「実装版」の 2 段表記に
- §5.2: test 件数 3 → 4 件 (細分化)、§5.3-5.4 を「実測」に書き換え
- §11: 完了条件チェックリストに `[x]` mark + 実機検証項目追加

旧 SPEC の Before は historical record として残置. live document としての update なので、Day9 archive 閲覧者が SPEC → 実装 → deviation の流れを 1 文書で追える.

---

## 6. Day9 で抽出された教訓 4 件

### 学び D9-1: brainstorming SPEC は実装段階で adjust 余地を残すべき

**本質**: SPEC §4.2 の Before/After は「ロジックの置換」を提示したが、**配置位置 (順序) の議論は欠落**していた. TDD GREEN verify 段階で順序問題が発覚し、結果として「著者直後」への moved up が必要となった.

**応用先**:
- SPEC レビュー時に「順序」「early return の優先度」「caller 側の挙動」も必ず確認する項目に入れる
- brainstorming skill の checklist に「実装の data flow / 制御 flow を疑似コードで描く」を追加検討
- spec deviation は commit message で完全に記録 (本 Day9 で実践済)

**Day1-8 既存学びとの関係**:
Day8 D8-1 (TDD だけでは捕捉できない問題は production 検証で補完) の SPEC vs 実装版. 「SPEC だけでは捕捉できない実装詳細は TDD で補完する」.

### 学び D9-2: Vancouver Veto 1 行で解決率 +33% pt の劇的効果 (small change, big impact)

**本質**: 改修は実質 1 行 (`if re.search(r"\((?:19|20)\d{2}\)", raw): return False`) の追加だが、効果は劇的:
- 解決率 14/24 → 22/24 (+33% pt)
- 重大エラー 4 件 → 0 件
- title 抽出品質 8 件で完全修正

**応用先**:
- データドリブンな brainstorming で「最小修正で最大効果」の道筋を発見可能 (4 markers 評価で M1 単独優位を確認した過程)
- 「なぜ 1 行で済むか」の根拠を SPEC で defendable に書くと、code review の説得性が増す

**Day1-8 既存学びとの関係**:
Day8 D8-3 (関数 extract で重複排除 + 将来 regression 予防) の上位概念. D9-2 は「規則の本数を増やすより、既存規則の正しい配置で問題解決」の例.

### 学び D9-3: parser → LLM の switch で false positive 重大エラーが解消される

**本質**: Day7 で「本物の MAJOR (重複引用 Ref #21=#8)」と判定したエラーが、Day9 LLM 解析では別物として正しく解決された. **parser の title 抽出失敗が連鎖的に「重複判定」「類似度判定」の false positive を生成していた**. parser 限界が intrastructure-wide な精度低下を引き起こしていた.

**応用先**:
- 「重大エラー」検出ロジックは upstream (parser) の品質に依存. parser 改善で downstream の audit 品質も向上
- false positive vs true positive の判定には実測比較 (Day7 vs Day9) が不可欠
- ChatGPT 等 LLM の引用検証で「重大エラー」が出た場合、まず parser の title 抽出が正しいか確認する手順を USAGE_QUICKSTART に追加検討

**Day1-8 既存学びとの関係**:
新規教訓. Day7 §8.5 で「parser 起因 false positive 3 件」を発見していたが、「本物の MAJOR」も実は false positive だったという発見は Day9 (Z) で初確認.

### 学び D9-4: 「設計を可視化する test」は spec を補完する

**本質**: `test_paren_year_dominates_over_mdpi_signals` (test 3b) は機能的には「(YYYY) があれば False」を assert するだけだが、その意図は「**M1 が他 MDPI signals より優先されるべき**」という設計判断の可視化. この test があったことで、TDD GREEN verify 段階で順序問題が即座に表面化した.

**応用先**:
- 「設計判断を可視化する test」を意識的に追加する (`test_*_dominates_over_*`, `test_*_takes_precedence_over_*` などの命名規約)
- これらの test は coverage rate には現れにくいが、**設計レビュー・将来の refactor 時に最も価値を発揮**
- brainstorming SPEC の §5 test plan に「設計可視化 test」のセクションを追加検討

**Day1-8 既存学びとの関係**:
TDD skill の「test as documentation」原則の具体例. Day8 でも `_inject_env_kv_handles_multiple_keys` 等で multi-key 挙動を test で documentation していた.

---

## 7. main branch の最終形状 (Day9 完了時)

### 7.1 commit history

```
(本 commit)  docs(sessions): archive day9 SPEC + lessons learned
0c1b56d      docs(spec): update Day9 SPEC with TDD implementation findings
ab25630      fix(mdpi-parser): tighten Vancouver detection via (YYYY) marker
5f8bbf0      docs(spec): add Day9 SPEC for MDPI fast-path Vancouver detection
c6f63ed      docs(sessions): archive day8 lessons learned                       ← Day8 末
... (Day1-Day8 commits omitted)
```

### 7.2 統計

| 指標 | 値 |
|:---|:---:|
| main commit count (Day9 完了時) | **35** + 本 commit = **36** (Day8 末 32 → +4) |
| test 健全性 | **66 passed, 1 skipped** (Day8 末 62 → +4) |
| 改修ファイル | `mdpi_parser.py`, `tests/test_mdpi_parser.py` |
| 新規 archive | `docs/sessions/day9/` (3 ファイル: SPEC + LESSONS + README) |
| identity | 全 commit `Hideki Katayama <hikataya01@gmail.com>` |

### 7.3 Day9 の本質的な達成

1. **brainstorming → SPEC → TDD → 実機検証** という 4 段階フローを確立 (Day8 までの「単一プロンプト → 直接 TDD」を発展)
2. **データドリブン**な設計合意形成 (4 markers 実測 → M1 単独採用)
3. **小さな修正で大きな効果** (1 行追加で解決率 +33% pt)
4. **parser 起因 false positive の完全解消** (Day7 で発見した 4 件すべてが parser 限界由来と判明)

---

## 8. 残存タスク (Day10 以降)

Day7 PHASE_0_VERIFICATION_REPORT §9 の更新版 (Day9 完了反映):

### 8.1 短期 (Day8 で完了)

- [x] main.py env loader の空値上書き対応 (Day8: d49dc58 + 7bc009b)
- [x] 環境依存フィールドの test 正規化拡張 (Day8: b8c0e5b)

### 8.2 中期 (Day9 で 1 件完了)

- [x] **Vancouver/AMA 系 parser 改善** (Day9: ab25630, 解決率 +33% pt)
- [ ] **USAGE_QUICKSTART に parser 限界注記 + Vancouver Veto 効果の記載**
  - Day9 (Z) のデータ (14/24 → 22/24, 重大 4 → 0) を反映
  - Vancouver 系では LLM 経路推奨、コスト ~$0.20/24refs
- [ ] API key セットアップ手順 docs 化 (`docs/operations/SETUP_API_KEYS.md` 等)
- [ ] `~/.claude/skills/pubmed-reference-resolver.old.20260502/` 最終削除 (Day6 残課題、1-2 週間後の予定)

### 8.3 長期 (Day10+ 想定)

- [ ] 別ドメイン golden fixture (Vancouver / APA / Cell 等) — Day9 で Vancouver の挙動が確認できたので fixture 化候補
- [ ] MCP/hook 経由 Claude UI 起動配線 (Stage 3)
- [ ] Day9 (Z) で残った未解決 2 件 (#17 Davey, #22 Gallina) の調査 (MEDLINE 非収録の可能性)

---

## 9. 次セッション再開時のプロンプトテンプレート

### パターン 1: USAGE_QUICKSTART 更新

```
Day10 として、skill_package/references/USAGE_QUICKSTART.md に
Day9 の Vancouver Veto 効果 (解決率 14/24 → 22/24, +33% pt,
docs/sessions/day9/DAY9_LESSONS_LEARNED.md §4.2) を反映する更新を
実施します。Vancouver 系入力の場合のコスト試算 (~$0.20/24refs) と
LLM 経路推奨の警告セクションを追加してください。
```

### パターン 2: 別ドメイン golden fixture 追加

```
Day10 として、Vancouver/AMA 系の golden fixture を新規追加します
(Day7 §9.3 長期タスク). Day9 (Z) で取得した Stage 2 の出力を
tests/fixtures/vancouver_24refs/ に baseline として配置し、
test_integration_vancouver_24refs.py を新設してください.
TDD で進めてください.
```

### パターン 3: 未解決 2 件の調査

```
Day10 として、Day9 (Z) で残った未解決 2 件
(Ref #17 Davey 2003, Ref #22 Gallina 2016) を調査します.
docs/sessions/day9/DAY9_LESSONS_LEARNED.md §4.4 を参照し、
MEDLINE 非収録の可能性を検証してください.
```

---

**記録完了日**: 2026/05/11
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day9 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day9.md` (Claude Opus 作成予定)
**ステータス**: Day9 archive 完成、Day10 着手準備完了
