# PHASE_{{PHASE_NAME_UPPER}}_INSTRUCTIONS.md

**作成日**: {{DATE}} ({{DAY_N}} = Phase {{PHASE_GREEK}})
**作成者**: Claude Opus {{CLAUDE_VERSION}}
**対象**: Claude Code (xhigh mode 想定)
**目的**: {{PURPOSE_ONE_LINE}}
**前提**: {{PREVIOUS_DAY_STATE}} (commit `{{PREVIOUS_COMMIT}}`, main branch {{PREVIOUS_COMMIT_COUNT}} commits)
**プロジェクトルート**: `{{PROJECT_ROOT}}`

---

## 全体フロー

```
[手順 1] 事前確認 (pre-flight)
   ↓ (全項目 OK の場合のみ進行)
[手順 2] {{STEP_2_TITLE}}
   ↓
[手順 3] {{STEP_3_TITLE}}
   ↓
... (必要に応じて手順を追加)
[手順 N] 最終確認 (final check)
```

各手順は**完了を逐次報告**し、想定外事象に該当した場合は**直ちに停止して報告** (stop-and-report) すること。

---

## 共通ルール

### 報告様式

各手順の完了時、以下の形式で簡潔に報告すること:

```
## 手順 N: [タイトル] 完了

### 実行結果
- 項目 N.1: <出力サマリー>
- 項目 N.2: <出力サマリー>
- ...

### 判定
- 期待結果との一致: <○ / × / 部分一致>
- 想定外事象: <なし / あり: 具体的内容>

### 次手順への進行可否
- <進行可 / 停止して指示待ち>
```

### 報告様式の 3 層モデル (Day6 P14)

| 層 | 名称 | 発動条件 |
|:---:|:---|:---|
| 1 | **stop-and-report** | 想定外事象、判断不能 |
| 2 | **予防的事前情報共有** | 軽微な相違、進行への影響なし |
| 3 | **standard reporting** | 通常の手順完了報告 |

### stop-and-report 発動条件 (全手順共通)

以下のいずれかに該当した場合、**当該手順内で即座に停止**し、状況を詳細に報告:

1. ファイル・ディレクトリの**期待されたサイズ・行数・内容と実測値の差異**
2. **未追跡ファイルや未コミット変更**の予期せぬ存在
3. **権限エラー**, **ディスク容量不足**, **コマンド未インストール**等のシステムレベル障害
4. **symlink の解決失敗** (broken link、循環参照、target not found)
5. **git config の競合** (既に異なる値が設定されている等)
6. その他、**判断に迷う事象**全般

---

## 手順 1: 事前確認 (Pre-flight Check)

### 目的

{{PRE_FLIGHT_PURPOSE}}

### 実行コマンド

```bash
# 1.1 プロジェクトルートに移動
cd {{PROJECT_ROOT}}

# 1.2 working tree が clean であることを確認
git status

# 1.3 HEAD が想定 commit であることを確認
git log -1 --format='%h %s'

# 1.4 {{CHECK_4_DESCRIPTION}}
{{CHECK_4_COMMAND}}

# (必要に応じて 1.N まで追加)
```

### 期待される出力

| 項目 | 期待値 |
|:---|:---|
| 1.2 (`git status`) | `nothing to commit, working tree clean` |
| 1.3 (`git log -1`) | `{{PREVIOUS_COMMIT}} {{PREVIOUS_COMMIT_SUBJECT}}` |
| 1.4 ({{CHECK_4_NAME}}) | {{CHECK_4_EXPECTED}} |

### stop-and-report 条件 (手順 1 固有)

- 1.2 で modified/staged ファイルが検出される
- 1.3 で HEAD が `{{PREVIOUS_COMMIT}}` でない
- {{ADDITIONAL_STOP_CONDITIONS}}

---

## 手順 2: {{STEP_2_TITLE}}

### 目的

{{STEP_2_PURPOSE}}

### 実行コマンド

```bash
{{STEP_2_COMMANDS}}
```

### 期待される出力

| 項目 | 期待値 |
|:---|:---|
| {{STEP_2_CHECK_TABLE}} | |

### stop-and-report 条件 (手順 2 固有)

- {{STEP_2_STOP_CONDITIONS}}

---

## 手順 3: {{STEP_3_TITLE}}

### 目的

{{STEP_3_PURPOSE}}

### 実行コマンド

```bash
{{STEP_3_COMMANDS}}
```

### 期待される出力

(同様)

---

<!-- 必要に応じて手順を追加。常に以下の構造を保つ:
1. 目的 (なぜこの手順が必要か)
2. 実行コマンド (具体的な bash コマンド)
3. 期待される出力 (検証可能な値)
4. stop-and-report 条件 (この手順固有)
-->

## 手順 N: 最終確認 (Final Check)

### 目的

全手順完了後、{{DAY_N}} 完了状態が期待通りに達成されていることを包括的に検証する。

### 実行コマンド

```bash
# N.1 working tree の最終状態
git status

# N.2 main branch の最終 commit 数
git rev-list --count main

# N.3 直近 commit の確認
git log -{{NEW_COMMIT_COUNT_PLUS_2}} --format='%h %s'

# N.4 {{FINAL_CHECK_4_DESCRIPTION}}
{{FINAL_CHECK_4_COMMAND}}

# (必要に応じて N.N まで追加)
```

### 期待される最終状態

| 検証項目 | 期待値 |
|:---|:---|
| N.1 | clean |
| N.2 | `{{EXPECTED_FINAL_COMMIT_COUNT}}` |
| N.3 | 新 commit + 前日末 commit |
| {{ADDITIONAL_FINAL_CHECKS}} | |

### 完了報告様式

```
## Phase {{PHASE_GREEK}} ({{DAY_N}} {{TASK_SUMMARY}}) 完了報告

### 達成項目
{{ACHIEVEMENT_CHECKLIST}}

### main branch 最終形状
- 総 commit 数: {{EXPECTED_FINAL_COMMIT_COUNT}}
- 新 commit (古い順):
  - <hash1> {{COMMIT_1_SUBJECT}}
  - (必要に応じて続く)

### 想定外事象
- なし / あり: <内容>

### 所要時間
- 開始: <時刻>
- 終了: <時刻>
- 総所要: <分>
```

---

## トラブルシューティング (FAQ)

### Q1. {{COMMON_ISSUE_1}}

→ {{SOLUTION_1}}

### Q2. {{COMMON_ISSUE_2}}

→ {{SOLUTION_2}}

(典型的な問題と対処法を 3-5 項目記載)

---

## 付録: 適用される 12 プロトコルへの対応

本指示書が体現する Day1-6 学びとの対応:

| 学び | 本指示書での具体化 |
|:---|:---|
| P5 (中間状態の発見と意図確認) | 各手順の stop-and-report 条件を明示 |
| P10 (二段階指示書アプローチ) | 手順 1 (調査) と手順 2-N (実装) の明確な分離 |
| P11 (バックアップによる真正性検証) | {{BACKUP_VERIFICATION_DETAILS}} |
| P12 (副次的成果のリアルタイム検証) | {{REAL_TIME_VALIDATION_DETAILS}} |
| P13 (順序設計の事前見直し) | 本指示書生成前の順序最終見直し済 |
| P14 (3 層報告モデル) | 共通ルールに 3 層モデル明示 |
| P15 (動的事前確認調整) | 手順 1 のサブ項目数: {{PRE_FLIGHT_SUBSTEPS}} |

---

**作成日**: {{DATE}}
**作成者**: Claude Opus {{CLAUDE_VERSION}}
**ファイル名**: `PHASE_{{PHASE_NAME_UPPER}}_INSTRUCTIONS.md`
**対応概念解説書**: `MIGRATION_INSTRUCTIONS_{{MIGRATION_VERSION}}.md` (同梱の場合)
**ステータス**: Claude Code への投入準備完了
**完了後の予定**: 先生 → Claude Opus へ完了報告 → {{DAY_N}} 記録 (`{{PROJECT_NAME}}-integration-chat-{{DAY_N_LOWER}}.md`) の作成

---

## テンプレート使用上の注記 (実利用時には削除)

### プレースホルダ一覧

| プレースホルダ | 例 |
|:---|:---|
| `{{PHASE_NAME_UPPER}}` | `DELTA`, `EPSILON`, `ZETA` |
| `{{PHASE_GREEK}}` | `δ`, `ε`, `ζ` |
| `{{DAY_N}}` | `Day7`, `Day8` |
| `{{DAY_N_LOWER}}` | `day7`, `day8` |
| `{{DATE}}` | `2026/05/03` |
| `{{CLAUDE_VERSION}}` | `4.7` |
| `{{PURPOSE_ONE_LINE}}` | "skill_package/ をローカル環境に最終反映する" |
| `{{PREVIOUS_DAY_STATE}}` | "Day6 完了状態" |
| `{{PREVIOUS_COMMIT}}` | `2f38128` |
| `{{PREVIOUS_COMMIT_COUNT}}` | `18` |
| `{{PROJECT_ROOT}}` | `~/Desktop/Claude/.../pubmed-reference-resolver` |
| `{{PROJECT_NAME}}` | `pubmed-reference-resolver` |
| `{{STEP_N_TITLE}}` | "git committer 正規化", "C-1 symlink 切替" |
| `{{STEP_N_PURPOSE}}` | (各手順の 1-3 文程度の目的記述) |
| `{{STEP_N_COMMANDS}}` | (具体的な bash コマンド) |
| `{{EXPECTED_FINAL_COMMIT_COUNT}}` | `21` |
| `{{TASK_SUMMARY}}` | "docs 整備" |

### カスタマイズの優先順位

1. **必須**: `{{DATE}}`, `{{DAY_N}}`, `{{PHASE_GREEK}}`, `{{PROJECT_ROOT}}`, `{{PREVIOUS_COMMIT}}`
2. **強く推奨**: 手順 N の `{{STEP_N_*}}` 系全般、`{{EXPECTED_FINAL_COMMIT_COUNT}}`
3. **任意**: `{{COMMON_ISSUE_*}}`, `{{REAL_TIME_VALIDATION_DETAILS}}` 等の付録
