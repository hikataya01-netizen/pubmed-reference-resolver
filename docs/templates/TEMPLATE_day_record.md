# {{PROJECT_NAME}} 統合作業セッション {{DAY_N}} (完全記録)

**日付**: {{DATE}}
**対象**: {{DAY_OBJECTIVE}}
**参加者**: {{PARTICIPANTS}}
**環境**: {{ENVIRONMENT}}
**ブランチ**: {{BRANCH}}
**前日記録**: {{PREVIOUS_DAY_RECORD_FILE}}

---

## セッション概要

{{SESSION_OVERVIEW_PARAGRAPH}}

### {{DAY_N}} の特殊性

{{DAY_N}} は{{COMPARISON_REFERENCE_DAYS}}と以下の点で性格を異にする。

| 観点 | {{COMPARISON_REFERENCE_DAYS}} | {{DAY_N}} |
|:---|:---|:---|
| 主目的 | {{COMPARISON_PURPOSE_OLD}} | {{DAY_N_PURPOSE}} |
| 主作業 | {{COMPARISON_WORK_OLD}} | {{DAY_N_WORK}} |
| 想定外事象 | {{COMPARISON_UNEXPECTED_OLD}} | {{DAY_N_UNEXPECTED}} |
| 副次的成果 | {{COMPARISON_SIDE_EFFECT_OLD}} | {{DAY_N_SIDE_EFFECT}} |
| 所要時間 | {{COMPARISON_DURATION_OLD}} | {{DAY_N_DURATION}} |

### {{DAY_N}} の成果

| 段階 | 内容 | 担当 | 所要時間 |
|:---:|:---|:---|:---:|
| 1 | {{STAGE_1_CONTENT}} | {{STAGE_1_OWNER}} | {{STAGE_1_TIME}} |
| 2 | {{STAGE_2_CONTENT}} | {{STAGE_2_OWNER}} | {{STAGE_2_TIME}} |
| ... | | | |
| **合計** | | | **{{TOTAL_TIME}}** |

最終 commit `{{FINAL_COMMIT}}` により、本日の作業は clean に締め括られた。

---

## 本記録の構成

- **I. {{PREVIOUS_DAY}} からの継続点と {{DAY_N}} 着手の経緯**
- **II. 段階 1-2: 設計確定と文書生成 (Claude Opus 作業)**
- **III. 段階 3: Claude Code による {{N_STEPS}} 手順の実施**
- **IV. 手順別実施結果と達成事項の詳細**
- **V. 副次的成果 — {{SIDE_EFFECT_TITLE}}**
- **VI. {{CHAPTER_VI_TITLE}}**
- **VII. main branch の最終形状 ({{FINAL_COMMIT_COUNT}} commits)**
- **VIII. {{DAY_N}} で抽出された新規学び ({{NEW_LESSONS}})**
- **IX. {{N_DAYS}} 日間全体を通じた方法論的資産の更新**
- **X. 残存タスクと次回セッションへの橋渡し**
- **XI. 付録**

---

## I. {{PREVIOUS_DAY}} からの継続点と {{DAY_N}} 着手の経緯

### I-1. {{PREVIOUS_DAY}} 完了時点の状態整理

(前日完了時の状態を箇条書き or 表形式で列挙)

### I-2. {{DAY_N}} 開始時の先生のメッセージ

{{OPENING_MESSAGE_QUOTE_OR_DESCRIPTION}}

### I-3. {{N_DECISIONS}} 決定事項の確定

(本日の作業範囲を確定するための主要論点と先生のご判断を表形式で記録)

| 論点 | 提示した選択肢 | 私の推奨 | 先生のご判断 |
|:---|:---|:---|:---|
| {{ISSUE_1}} | {{OPTIONS_1}} | {{RECOMMEND_1}} | **{{DECISION_1}}** |
| ... | | | |

### I-4. {{ADDITIONAL_PRE_SECTION_TITLE}}

(必要に応じて、設計の事前見直し等を記録)

---

## II. 段階 1-2: 設計確定と文書生成 (Claude Opus 作業)

### II-1. 生成された {{N_FILES}} ファイル

| ファイル | 行数 | サイズ | 役割 |
|:---|:---:|:---:|:---|
| {{FILE_1_NAME}} | {{FILE_1_LINES}} | {{FILE_1_BYTES}} | {{FILE_1_ROLE}} |
| ... | | | |

### II-2. {{KEY_DOCUMENT_NAME}} の構造

(主要文書の構造を表形式で記録)

### II-3. {{KEY_DOCUMENT_NAME}} の主要な変更点

(前 version との対比、もしあれば)

---

## III. 段階 3: Claude Code による {{N_STEPS}} 手順の実施

### III-1. Claude Code への投入

(投入プロンプトを記録)

### III-2. 実行タイムライン

| 時刻 | 手順 | 内容 |
|:---:|:---:|:---|
| {{TIME_START}} | 1 | {{STEP_1}} |
| (continued) | 2-{{N_STEPS_MINUS_1}} | 順次実行 |
| {{TIME_END}} | {{N_STEPS}} | 最終確認の完了 |
| **合計** | | **{{TOTAL_DURATION}}** |

### III-3. stop-and-report 発動の有無

(発動有無と、発動した場合は内容を記録)

### III-4. 唯一の事前情報共有事項

(Day6 P14 の予防的事前情報共有レイヤーが発動した場合、ここに記録)

---

## IV. 手順別実施結果と達成事項の詳細

(各手順について以下の構造で記録)

### IV-{{N}}. 手順 {{N}}: {{STEP_TITLE}}

| 項目 | 値 |
|:---|:---|
| {{ITEM_1}} | {{VALUE_1}} |
| {{ITEM_2}} | {{VALUE_2}} |
| ... | |

(主要な達成内容を 1-2 段落で記述)

---

## V. 副次的成果 — {{SIDE_EFFECT_TITLE}}

(Day6 P12 = 副次的成果としてのリアルタイム検証 を意識的に記録するセクション)

### V-1. 事象の概要

{{SIDE_EFFECT_DESCRIPTION}}

### V-2. この事象が示す検証の多層性

(可能なら検証の多層構造を表形式で示す)

### V-3. なぜこれが本質的に重要か

{{IMPORTANCE_RATIONALE}}

### V-4. 学び抽出への結晶化

これらは {{DAY_N}} 学び {{NEW_LESSON_REFERENCE}} として後述章で結晶化される。

---

## VI. {{CHAPTER_VI_TITLE}}

(本 Day 固有のトピックを 1 章として記録。例: identity 履歴境界、設計判断のトレードオフ等)

---

## VII. main branch の最終形状 ({{FINAL_COMMIT_COUNT}} commits)

```
{{COMMIT_HISTORY}}
```

### VII-1. プロジェクトとしての到達点 ({{DAY_N}} 完了時)

(達成事項を番号付きで列挙)

---

## VIII. {{DAY_N}} で抽出された新規学び ({{NEW_LESSONS}})

(各新規学びを以下の構造で記録)

### VIII-{{N}}. 学び {{LESSON_NUMBER}}: {{LESSON_TITLE}}

(本質、応用先、Day1-{{PREVIOUS_DAY_NUMBER}} 既存学びとの関係を記述)

**本質**: {{ESSENCE}}

**応用先**:
- {{APPLICATION_1}}
- {{APPLICATION_2}}

**{{RELATED_LESSON}}との関係**: {{RELATIONSHIP}}

---

## IX. {{N_DAYS}} 日間全体を通じた方法論的資産の更新

### IX-1. 学び A-H + P1-{{LATEST_LESSON}} の全体像 (更新版)

| Day | 番号 | 内容 (要約) |
|:---|:---|:---|
| Day3 | A | fixture が仕様書として成立しているかを吟味する |
| Day3 | B | 調査フェーズを独立させる価値 |
| ... | ... | ... |
| **{{DAY_N}}** | **{{NEW_LESSON_1}}** | **{{NEW_LESSON_1_TITLE}}** |
| ... | | |

### IX-2. {{N_DAYS}} 日間の最上位原則 (再定式化)

(必要に応じて Day5/6 で確立された最上位原則を更新)

### IX-3. 三者協働モデルの最終形 ({{DAY_N}} 完了時)

(役割分担表を更新)

---

## X. 残存タスクと次回セッションへの橋渡し

### X-1. 短期タスク (1 週間以内)

| 優先度 | タスク | 関連 |
|:---:|:---|:---|
| ★★★ | {{ST_TASK_1}} | {{ST_RELATED_1}} |
| ... | | |

### X-2. 中期タスク (1 ヶ月以内)

(同様)

### X-3. 長期タスク (時期未定)

(同様)

### X-4. 次回セッション再開時のプロンプトテンプレート

**パターン 1: {{PATTERN_1_TITLE}}**

```
{{PATTERN_1_PROMPT}}
```

**パターン 2: {{PATTERN_2_TITLE}}**

```
{{PATTERN_2_PROMPT}}
```

(以下、必要に応じて続く)

---

## XI. 付録

### 付録 A: {{DAY_N}} の commit 履歴

```
{{NEW_COMMITS_LIST}}
```

### 付録 B: {{DAY_N}} の生成ファイル一覧 (Claude Opus 作成)

| ファイル | 行数 | サイズ | 役割 |
|:---|:---:|:---:|:---|
| ... | | | |

### 付録 C: {{DAY_N}} の stop-and-report 事例

(発動なしの場合は明記)

### 付録 D: {{DAY_N}} の予防的事前情報共有事例

(発動なしの場合は明記)

### 付録 E: {{N_DAYS}} 日間の所要時間総括

| Day | 完了内容 | 所要時間 |
|:---:|:---|:---:|
| Day1 | ... | ... |
| ... | | |
| **{{DAY_N}}** | **{{DAY_N_CONTENT}}** | **{{DAY_N_DURATION}}** |
| **合計** | | **{{TOTAL_HOURS}}** |

### 付録 F: {{N_DAYS}} 日間で確立された主要プロトコルの一覧 (更新版)

(12 プロトコル + 新追加プロトコルを番号付きで列挙)

### 付録 G: Day1-{{DAY_N}} 全体の主要な設計判断リファレンス (更新版)

| 日付 | 判断 | 参照セクション |
|:---|:---|:---|
| ... | | |
| **{{DAY_N}}** | **{{DAY_N_DECISION_1}}** | **{{DAY_N}} 記録 {{SECTION_REF}}** |

(必要に応じて付録 H 以降を追加)

---

**記録作成日**: {{DATE}}
**記録作成者**: Claude Opus {{CLAUDE_VERSION}}
**ファイル名**: `{{PROJECT_NAME}}-integration-chat-{{DAY_N_LOWER}}.md`
**対応 Day1 記録**: `{{PROJECT_NAME}}-integration-chat.md`
**対応 Day{{N-1}} 記録**: `{{PROJECT_NAME}}-integration-chat-{{DAY_N_MINUS_1_LOWER}}.md`
**ステータス**: {{COMPLETION_STATUS}}
**次回候補タスク**: {{NEXT_CANDIDATES}}

---

## テンプレート使用上の注記 (実利用時には削除)

### 章構成の遵守

I-XI 章構成 + 付録 A-G (場合により H 以上) は **Day3-Day6 で確立された Day 記録の標準構造**。本テンプレートを使用する際は、章順序を保持すること。

### 章ごとの最低限要素

| 章 | 必須要素 |
|:---|:---|
| I | 前日からの継続点、開始時メッセージ、決定事項 |
| II | 生成ファイル一覧、主要文書の構造 |
| III | 実行タイムライン、stop-and-report 有無 |
| IV | 手順別の達成事項 |
| V | 副次的成果 (なければ「該当なし」と明記) |
| VI | 当日固有のトピック |
| VII | commit 履歴、到達点 |
| VIII | 新規学び (なければ「新規学び抽出なし」と明記) |
| IX | 学び体系の更新 |
| X | 残存タスク + 次回プロンプトテンプレート |
| XI | 付録 (commit 一覧、生成ファイル、所要時間等) |

### 最低分量

- 全体: 400-700 行を目安
- 各章: 30-100 行を目安 (章 V, VIII は内容次第で 20 行以下も可)

### スタイル指針

- **形式**: 表形式を活用 (記述ばかりにならない)
- **トーン**: 形式日本語、私的感情を抑制
- **引用**: Claude Code・先生の発言は ` > 引用` 形式
- **コードブロック**: bash, ファイルツリー、commit log で活用
