# DAY14_LESSONS_LEARNED.md

**Day14 = Day13 INVESTIGATION (3 分類) を skill ユーザー向け docs に反映**

**作成日**: 2026/05/13
**作成者**: Claude Code (Sonnet 4.6)
**配置**: `docs/sessions/day14/DAY14_LESSONS_LEARNED.md`
**対応 commit 範囲**: `b659350` + 本書 archive commit (計 2 commits)
**対応する指示書**: なし (Day13 §6 推奨の B+C を user 単発指示「day14を続けて」で開始)

---

## 0. 本書の位置づけ

Day14 は Day13 で発見した「PubMed 未ヒット 3 分類」を skill ユーザー向け docs (SKILL.md description + USAGE_QUICKSTART.md) に反映した. Day13 (調査・知識生成) → Day14 (docs 反映) という **2 セッション分割パターン**の実例.

本書は以下を記録する:

1. Day14 のフェーズ構成 (1 commit + archive)
2. SKILL.md description vs USAGE_QUICKSTART の機能分離 (Day12 D12-2 の継続応用)
3. USAGE_QUICKSTART §X 変更履歴の運用継続 (Day10 で確立、Day14 で 1.2 bump)
4. Day14 で抽出された教訓 3 件 (D14-1, D14-2, D14-3)
5. main branch 最終形状と Day15 への引継ぎ

---

## 1. Day14 のフェーズ構成

| フェーズ | commit | 達成 |
|:---:|:---:|:---|
| 1 | `b659350` | SKILL.md description + USAGE_QUICKSTART 1.2 update (B+C を 1 commit に統合) |
| 2 | (本 commit) | Day14 archive (README + LESSONS) |

---

## 2. SKILL.md description vs USAGE_QUICKSTART の機能分離

### 2.1 反映先 2 ファイルの役割

Day12 D12-2 で確立した「読者ロール別の情報粒度設計」に従い、同じ「3 分類」を 2 ファイルで異なる粒度で表現:

| ファイル | 役割 | 3 分類の表現粒度 |
|:---|:---|:---|
| `skill_package/SKILL.md` (description) | skill discovery 入口 (Claude UI で skill 一覧表示時に見える) | **1 行サマリー** + 「詳細は references/USAGE_QUICKSTART.md §V Q4 参照」 |
| `skill_package/SKILL.md` (本文 line 135) | skill 概要を読む人向け中粒度説明 | **3 sub-bullet** (A/B/C を判定基準 + severity と共に列挙) |
| `skill_package/references/USAGE_QUICKSTART.md` §V Q4 | 利用者の Q&A、深掘り documentation | **table + 補助検証 curl コマンド + 現状制約 + 暫定的対処** (~50 行) |

### 2.2 段階的な情報露出

- **Skill 検索者** (1-2 秒): description の 1 行で「3 分類で扱う」を認知
- **Skill 概要を読む人** (1-2 分): SKILL.md 本文で A/B/C の判定基準と severity を把握
- **詳細を知りたい利用者 / 査読者** (5-10 分): USAGE_QUICKSTART.md §V Q4 で実例 + curl コマンド + 現状制約まで把握

→ 学び D14-2 (情報の階層化露出) として教訓化.

---

## 3. USAGE_QUICKSTART §X 変更履歴の運用継続

### 3.1 §X 変更履歴の累積記録

USAGE_QUICKSTART.md §X 変更履歴は Day10 (1.1) で初設置. Day14 で 1.2 entry を 1.1 entry の上に追加 (新版が上、旧版が下の慣例).

```
§X 変更履歴
  ├─ バージョン 1.2 (2026/05/13、Day14 更新) ← 本日追加
  │   - §V Q4 全面書き換え (3 分類)
  │   - メタ情報 + バージョン bump
  │   - 関連: SKILL.md description も同タイミング更新
  └─ バージョン 1.1 (2026/05/11、Day10 更新)
      - §I, §III, §V Q3, §VI 等を Vancouver Veto データ反映
```

### 3.2 メリット

1. **archaeological accountability**: 「いつ何を変更したか」が単一文書内で完結 (git log 横断不要)
2. **読者の信頼**: 「このドキュメントが最新で、こう変遷してきた」を transparency で示せる
3. **改修 ↔ docs の対応**: skill commit (e.g. ab25630 Day9) ↔ docs version (1.1 Day10) ↔ 後続 commit (b659350 Day14) ↔ docs version (1.2 Day14) という「commit ↔ docs version」の対応関係が追える

### 3.3 他プロジェクトへの応用

- 利用者向け docs (USER_GUIDE / QUICKSTART 等) には §X 変更履歴を必ず設ける慣行
- バージョン bump の判断基準: 「機能追加」「重要な記述変更」「外部仕様の変化」に該当すれば minor 以上
- 1.0 → 1.1 → 1.2 のような細粒度 bump で利用者は「最後に読んだ後何が変わったか」を確認しやすい

---

## 4. Day14 で抽出された教訓 3 件

### 学び D14-1: 「調査 (data-driven) → 反映 (docs)」の 2 セッション分割パターン

**本質**: Day13 で「PubMed 未ヒット 3 分類」を実証調査で発見、Day14 でその知見を skill ユーザー向け docs に反映. **1 つのテーマを 2 セッションに分けて完了**することで、各セッションが clean な範囲で完結し、相互参照が成立しやすくなる.

**応用先**:
- 大型改修も「調査 (1 セッション) → SPEC (1 セッション) → 実装 (1-N セッション)」のような分割が clean
- 各セッションは「前セッションの成果物を起点に着手」できる構造に (Day14 は Day13 INVESTIGATION §6 案 B+C を起点)
- archive 連鎖により「一連の知識生成 → 実装」の流れが永続記録される

**Day1-13 既存学びとの関係**:
Day9 brainstorming → SPEC → TDD → 実機検証 (4 段階フロー) の延長. Day9 は 1 セッション内 4 段階、Day13-14 は 2 セッション分割. 両者ともに「**段階を踏むことで品質と再利用性が増す**」という共通原則.

### 学び D14-2: skill 内の情報を読者ロール別に階層化する設計

**本質**: 同じ topic (3 分類) でも、Skill 検索者 (1 行サマリー)、概要を読む人 (sub-bullet)、深掘り利用者 (table + curl + Q&A) の 3 階層で情報露出を変える. SKILL.md description (最上位) → SKILL.md 本文 (中段) → references/USAGE_QUICKSTART.md §V Q4 (詳細) の 3 段階で、各階層の読者が必要な情報量を即取得できる.

**応用先**:
- 他 skill (claude-md / docs などの documentation 系) でも同パターンが適用可能
- description → 本文 → references/ の 3 段階は Claude Code skill plugin 一般の設計指針として成立
- 各段階で「次の段階のリンク」を必ず付与することで、利用者が探索可能 (Day14 では SKILL.md 本文 → "詳細: references/USAGE_QUICKSTART.md §V Q4")

**Day1-13 既存学びとの関係**:
Day12 D12-2 (USAGE_QUICKSTART vs SETUP_API_KEYS の機能分離) の上位概念. D12-2 は「**ファイル間**の機能分離」、D14-2 は「**1 ファイル内 + 関連 file 間**の階層化露出」. 両者を組合せると skill docs 全体の構造が読者ロールに最適化される.

### 学び D14-3: 利用者向け docs の §X 変更履歴は archaeological 価値を生む

**本質**: USAGE_QUICKSTART.md §X 変更履歴は Day10 で初設置、Day14 で 2 回目の bump (1.0 → 1.1 → 1.2). 「単一文書内で何がいつ変更されたか」が完結することで、git log 横断なしで利用者が変遷を追える. archive (DAY*_LESSONS_LEARNED) との二重記録となるが、利用者は archive を読まないため docs 内変更履歴が必須.

**応用先**:
- 利用者向け docs (QUICKSTART / USER_GUIDE 等) には必ず §変更履歴 / Changelog を設置
- バージョン bump の慣例: 機能追加 = minor (1.1 → 1.2), 重要な仕様変更 = major (1.x → 2.0)
- 各 entry には「変更内容」「日付/Day」「関連 commit hash or §」を記載

**Day1-13 既存学びとの関係**:
Day10 D10-3 (archive 連鎖の累積価値) の docs 内蔵版. archive 連鎖は session 単位、§変更履歴は docs 単位、両者で archaeological accountability を多層で担保.

---

## 5. main branch の最終形状 (Day14 完了時)

### 5.1 commit history (Day14 範囲)

```
(本 commit)  docs(sessions): archive day14 3-class docs reflection
b659350      docs(skill): apply Day13 "PubMed 未ヒット 3 分類" to SKILL.md + USAGE_QUICKSTART 1.2
a2ee5ae      docs(sessions): archive day13 MEDLINE non-indexing investigation         ← Day13 末
... (Day1-Day13 commits omitted)
```

### 5.2 統計

| 指標 | 値 |
|:---|:---:|
| main commit count (Day14 完了時、本 commit 含む) | **45** (Day13 末 43 → +2) |
| test 健全性 | **71 passed, 1 skipped** (Day13 末から不変、docs only) |
| 改修ファイル | `skill_package/SKILL.md`, `skill_package/references/USAGE_QUICKSTART.md` |
| 新規 archive | `docs/sessions/day14/` (2 ファイル: README + LESSONS) |
| identity | 全 commit `Hideki Katayama <hikataya01@gmail.com>` |

### 5.3 Day14 の本質的な達成

1. **Day13 §6 推奨 B + C を 1 commit で実施** (skill docs に 3 分類反映完了)
2. **USAGE_QUICKSTART 1.0 → 1.1 → 1.2 の version 連鎖継続** (Day10 から続く慣例)
3. **読者ロール別の情報階層化** を SKILL.md と USAGE_QUICKSTART で実装
4. **「調査 → 反映」の 2 セッション分割パターン** (Day13 → Day14) の実証
5. **archive 連鎖 9 連続達成** (Day6-14)

---

## 6. 残存タスク (Day15 以降)

### 6.1 Day13 §6 改修候補の継続

- [x] B. USAGE_QUICKSTART §V Q4 (Day14 完了)
- [x] C. SKILL.md description (Day14 完了)
- [ ] **A. audit_report に 3 分類 logic 追加** ← Day15+ 候補 (大規模、別 SPEC + brainstorming セッション必要)
  - 新モジュール: `crossref_check.py`, `nlm_catalog_check.py`
  - 既存 audit logic への統合
  - test 追加 (Day11 ハイブリッド命名規約 expected_*/baseline_* 適用)
  - USAGE_QUICKSTART §V Q4 の「現状制約」section を「機能実装済」に書き換え (1.3 bump)

### 6.2 Day7 §9.3 long-term task の残り

- [x] Vancouver golden fixture (Day11)
- [x] Day9 (Z) 未解決 2 件の MEDLINE 非収録調査 (Day13)
- [ ] APA / Cell 系 golden fixture
- [ ] MCP/hook 経由 Claude UI 起動配線 (Stage 3)
- [ ] GitHub remote 追加と push

---

## 7. 次セッション再開時のプロンプトテンプレート

### パターン 1: Day13 §6 案 A 実装 (大規模、本日 B+C 完了の継続)

```
Day15 として、Day13 §6 案 A (audit_report に「PubMed 未ヒット 3 分類」
logic 追加) を実装します. 大規模なので brainstorming → SPEC → TDD で
段階的に進めてください.

参照:
- docs/sessions/day13/INVESTIGATION_unresolved_2refs.md §3.4 (擬似コード)
- docs/sessions/day14/DAY14_LESSONS_LEARNED.md §6.1 (改修スコープ)
- skill_package/references/USAGE_QUICKSTART.md §V Q4 (1.2、3 分類仕様)

新モジュール候補: crossref_check.py, nlm_catalog_check.py.
既存 audit logic への統合と test 追加 (Day11 ハイブリッド命名規約)
を含めて設計してください.
```

### パターン 2: 別の long-term task

Day12 §7 / Day13 §6 のテンプレートをそのまま再利用可能 (APA fixture / GitHub push / Stage 3 配線).

---

**記録完了日**: 2026/05/13 (Day14)
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day14 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day14.md` (Claude Opus 作成予定)
**ステータス**: Day14 archive 完成、Day15 着手準備完了 (Day13 §6 案 A 実装 / 別 long-term task の選択型)
