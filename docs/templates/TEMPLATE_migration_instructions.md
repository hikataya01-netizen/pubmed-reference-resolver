# MIGRATION_INSTRUCTIONS_{{MIGRATION_VERSION}}.md

**作成日**: {{DATE}} ({{DAY_N}} = Phase {{PHASE_GREEK}})
**作成者**: Claude Opus {{CLAUDE_VERSION}}
**対象**: {{TARGET_RECIPIENT}} (典型的には先生)
**目的**: {{PURPOSE_TWO_LINES}}
**前 version からの差分**: {{DIFF_FROM_PREVIOUS_VERSION}}

---

## I. 前 version からの主要変更点

| 項目 | 旧 ({{PREVIOUS_VERSION}}) | 新 ({{MIGRATION_VERSION}}, 本書) | 修正理由 |
|:---|:---|:---|:---|
| {{CHANGE_1_NAME}} | {{CHANGE_1_OLD}} | {{CHANGE_1_NEW}} | {{CHANGE_1_REASON}} |
| {{CHANGE_2_NAME}} | {{CHANGE_2_OLD}} | {{CHANGE_2_NEW}} | {{CHANGE_2_REASON}} |
| (必要に応じて続く) | | | |

---

## II. 本日の作業全体像 ({{PHASE_GREEK_LIST}})

### II-1. {{N_TASKS}} タスクの一覧と依存関係

| 手順 | 略称 | 内容 | 担当 | 依存 |
|:---:|:---|:---|:---|:---|
| 1 | (pre-flight) | 事前確認 | Claude Code | なし |
| 2 | {{TASK_2_LABEL}} | {{TASK_2_CONTENT}} | Claude Code | 手順 1 完了 |
| 3 | {{TASK_3_LABEL}} | {{TASK_3_CONTENT}} | Claude Code | {{TASK_3_DEPENDENCY}} |
| ... | | | | |
| N | (final-check) | 最終確認 | Claude Code | 全手順完了 |

### II-2. 順序設計の根拠

(Day6 学び P13 = 順序設計の事前見直し に基づき、ここで順序の妥当性を明文化する)

- **{{ORDER_RATIONALE_1}}**
- **{{ORDER_RATIONALE_2}}**
- **{{ORDER_RATIONALE_3}}**

### II-3. 所要時間見積り

{{EXPECTED_DURATION}}。

---

## III. 採用方針: {{ADOPTED_APPROACH_NAME}}

### III-1. {{ADOPTED_APPROACH_NAME}} の本質

{{APPROACH_ESSENCE_DESCRIPTION}}

```
{{APPROACH_DIAGRAM}}
```

### III-2. 動作原理 (技術的詳細)

{{TECHNICAL_DETAILS}}

### III-3. {{ADOPTED_APPROACH_NAME}} を採用した {{N_RATIONALES}} つの根拠

1. **{{RATIONALE_1_NAME}}**: {{RATIONALE_1_BODY}}
2. **{{RATIONALE_2_NAME}}**: {{RATIONALE_2_BODY}}
3. **{{RATIONALE_3_NAME}}**: {{RATIONALE_3_BODY}}

### III-4. 採用に伴う既知の制約

- **{{CONSTRAINT_1}}**: {{CONSTRAINT_1_DESCRIPTION}}
- **{{CONSTRAINT_2}}**: {{CONSTRAINT_2_DESCRIPTION}}

これらは現時点では許容され、将来の段階で再評価する設計判断である。

---

## IV. 変更前後の状態比較

### IV-1. 変更前 ({{PREVIOUS_DAY}} 完了時 = {{CURRENT_DAY}} 開始時)

```
{{BEFORE_STATE_TREE}}
```

### IV-2. 変更後 ({{CURRENT_DAY}} 完了時)

```
{{AFTER_STATE_TREE}}
```

### IV-3. 変更による効果の検証可能性

| 検証項目 | コマンド | 期待結果 |
|:---|:---|:---|
| {{VERIFY_1_NAME}} | `{{VERIFY_1_COMMAND}}` | {{VERIFY_1_EXPECTED}} |
| {{VERIFY_2_NAME}} | `{{VERIFY_2_COMMAND}}` | {{VERIFY_2_EXPECTED}} |
| (必要に応じて続く) | | |

---

## V. ロールバック手順

万一、本作業の途中または完了後に問題が発生した場合の復旧手順を以下に記載する。

### V-1. 手順 N ({{TASK_N}}) のロールバック

```bash
{{ROLLBACK_COMMANDS_FOR_TASK_N}}
```

これにより{{ROLLBACK_RESULT_DESCRIPTION}}。

### V-2. 全体ロールバック手順

V-1 → V-2 → ... の順で実行することで、{{CURRENT_DAY}} 開始時の状態に完全復帰する。

---

## VI. Claude Code への投入方法

### VI-1. 投入ファイル

`PHASE_{{PHASE_NAME_UPPER}}_INSTRUCTIONS.md` (約 {{INSTRUCTION_LINE_COUNT}} 行を予定、別ファイルとして提供)

### VI-2. 投入時の指示プロンプト (推奨テンプレート)

```
PHASE_{{PHASE_NAME_UPPER}}_INSTRUCTIONS.md に従って、{{PROJECT_NAME}} の
{{PHASE_GREEK_LIST}} ({{CURRENT_DAY}} 作業) を実施してください。

各手順での確認結果は手順番号付きで報告してください。
想定外事象 (stop-and-report 条件) に該当した場合は即座に停止し、
状況を報告してください。

プロジェクトルート: {{PROJECT_ROOT}}
```

### VI-3. Claude Code の振る舞いに関する想定

- **想定通りに進む場合**: 手順 1 から N まで順次実行し、最終確認の出力を全項目 OK として報告。
- **想定外事象が発生する場合**: 該当手順で stop-and-report を発動し、状況を報告。先生が判断して再開指示または別途対応。

### VI-4. 想定外事象の典型例

| シナリオ | 対応 |
|:---|:---|
| {{ANTICIPATED_ISSUE_1}} | {{RESPONSE_1}} |
| {{ANTICIPATED_ISSUE_2}} | {{RESPONSE_2}} |
| (必要に応じて続く) | |

---

## VII. 完了後の状態

本作業完了後、以下が達成される。

1. **{{ACHIEVEMENT_1}}**
2. **{{ACHIEVEMENT_2}}**
3. **{{ACHIEVEMENT_3}}**
4. **{{ACHIEVEMENT_4}}** (必要に応じて続く)

---

## VIII. 残存タスク (本作業後)

本作業完了後も以下のタスクが残る。これらは別セッションで対応する。

| 優先度 | タスク | 関連 |
|:---:|:---|:---|
| ★★★ | {{REMAINING_1}} | {{REMAINING_1_RELATED}} |
| ★★☆ | {{REMAINING_2}} | {{REMAINING_2_RELATED}} |
| ★☆☆ | {{REMAINING_3}} | {{REMAINING_3_RELATED}} |

---

**記録**: 本書は `MIGRATION_INSTRUCTIONS_{{PREVIOUS_VERSION}}.md` (前 version) の改訂版である。前 version の内容は当時のスナップショットとして保持し、本書 {{MIGRATION_VERSION}} を{{CURRENT_DAY}} 以降の正本とする。

**作成日**: {{DATE}}
**作成者**: Claude Opus {{CLAUDE_VERSION}}
**ファイル名**: `MIGRATION_INSTRUCTIONS_{{MIGRATION_VERSION}}.md`
**対応指示書**: `PHASE_{{PHASE_NAME_UPPER}}_INSTRUCTIONS.md` (同梱)
**ステータス**: 設計確定、Claude Code への投入準備完了

---

## テンプレート使用上の注記 (実利用時には削除)

### 必須プレースホルダ

| プレースホルダ | 例 |
|:---|:---|
| `{{MIGRATION_VERSION}}` | `v2`, `v3` |
| `{{PHASE_GREEK}}` | `δ`, `ε`, `ζ` |
| `{{PHASE_GREEK_LIST}}` | "Phase δ + ε" |
| `{{ADOPTED_APPROACH_NAME}}` | "C-1-β (symlink architecture)" |
| `{{N_TASKS}}` | `5`, `7` |

### 強く推奨プレースホルダ

| プレースホルダ | 例 |
|:---|:---|
| `{{BEFORE_STATE_TREE}}` | (ディレクトリ構造図) |
| `{{AFTER_STATE_TREE}}` | (ディレクトリ構造図) |
| `{{TECHNICAL_DETAILS}}` | (動作原理の説明、典型的に 1-3 段落) |
| `{{ROLLBACK_COMMANDS_FOR_TASK_N}}` | (具体的な bash コマンド) |
