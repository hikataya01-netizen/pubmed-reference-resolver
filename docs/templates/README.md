# docs/templates/

**Day1-6 で確立された 12 プロトコルから抽出された再利用可能なテンプレート**

このディレクトリは、pubmed-reference-resolver の 6 日間開発で確立された方法論を、**他スキル開発・他プロジェクトで即座に再利用できる骨格**として保管する。

## テンプレート一覧

| テンプレート | 対応文書 | 用途 |
|:---|:---|:---|
| `TEMPLATE_phase_instructions.md` | `PHASE_*_INSTRUCTIONS.md` | Claude Code 向け実行指示書 (例: PHASE_BETA, PHASE_DELTA, PHASE_ZETA) |
| `TEMPLATE_migration_instructions.md` | `MIGRATION_INSTRUCTIONS_*.md` | 先生向け概念解説書 (deployment 戦略、ロールバック手順等を含む) |
| `TEMPLATE_day_record.md` | `pubmed-reference-resolver-integration-chat-dayN.md` | Day 単位のセッション完全記録 (I-XII 章構成) |

## プレースホルダ規約

全テンプレートで `{{VAR}}` 形式のプレースホルダを使用。代表的な変数:

| プレースホルダ | 意味 | 例 |
|:---|:---|:---|
| `{{PROJECT_NAME}}` | プロジェクト名 | `pubmed-reference-resolver` |
| `{{PROJECT_ROOT}}` | プロジェクト絶対パス | `~/Desktop/Claude/査読用/...` |
| `{{DAY_N}}` | Day 番号 | `Day7` |
| `{{DATE}}` | 日付 (YYYY/MM/DD) | `2026/05/03` |
| `{{PHASE_NAME}}` | フェーズ名 | `Phase ζ` |
| `{{PHASE_GREEK}}` | ギリシャ文字 | `ζ` (zeta) |
| `{{PREVIOUS_COMMIT}}` | 前日末の commit hash | `2f38128` |
| `{{N_STEPS}}` | 手順数 | `6` |
| `{{TASK_LIST}}` | 本日のタスク一覧 | (Markdown 表) |
| `{{LESSON_NUMBERS}}` | 抽出予定の学び番号 | `P16-P19` |

## 使用ワークフロー

### 1. 新セッション開始時 (例: Day7 計画)

```bash
# テンプレートをコピーして編集 (project root の作業領域へ)
cp docs/templates/TEMPLATE_phase_instructions.md PHASE_THETA_INSTRUCTIONS.md
cp docs/templates/TEMPLATE_migration_instructions.md MIGRATION_INSTRUCTIONS_v3.md

# プレースホルダを sed/エディタで置換
sed -i '' 's/{{PHASE_GREEK}}/θ/g' PHASE_THETA_INSTRUCTIONS.md
sed -i '' 's/{{DAY_N}}/Day8/g' PHASE_THETA_INSTRUCTIONS.md
# ...等
```

### 2. Claude Opus への投入時

新セッション開始時、Claude Opus に以下のように依頼:

```
docs/templates/TEMPLATE_phase_instructions.md をベースに、
以下の作業のための PHASE_THETA_INSTRUCTIONS.md を生成してください。

- 作業概要: <内容>
- 対象タスク: <タスク 1, 2, 3>
- 前提 commit: <hash>
```

### 3. Day 記録作成時

セッション完了後、`docs/templates/TEMPLATE_day_record.md` をベースに Day 記録を作成。Claude Opus に Day1-6 記録と本テンプレートを渡せば、I-XII 章構成で自動生成可能。

## 12 プロトコルとの対応

各テンプレートに組込済のプロトコル:

### TEMPLATE_phase_instructions.md
- Protocol 2 (stop-and-report) — 各手順に発動条件を明記する section を組込
- Protocol 4 (二段階指示書) — 事前確認 (手順 1) と実装 (手順 2 以降) の分離
- Protocol 5 (真正性検証の中間挿入) — バックアップ → 操作 → diff 検証の 3 段階を骨格化
- Protocol 8 (commit message 規範) — `type(scope): brief` 形式の例示
- Protocol 11 (3 層報告モデル) — stop-and-report / 予防的事前情報共有 / standard reporting の使い分け
- Protocol 12 (動的事前確認調整) — 初回実行時の厳密事前確認、安定運用後の簡素化に向けた構造

### TEMPLATE_migration_instructions.md
- Protocol 1 (5 段階事前協議) — 事前確認 → 推奨提示 → 即決 → 統合指示書 → 実装の流れを骨格化
- Protocol 3 (調査フェーズの独立化) — Phase α (調査) と Phase β (実装) の分離テンプレート
- Protocol 6 (原則間 tension の調停) — 設計判断セクションでの選択肢比較表
- Protocol 9 (副次的成果のリアルタイム検証) — 検証セクションでの「期待される副次効果」項目
- Protocol 10 (順序設計の事前見直し) — 「順序の最終見直し」セクション

### TEMPLATE_day_record.md
- Protocol 7 (Day 記録章立て) — I-XII 章構成と付録 A-H の骨格

## 既存実例との対応

各テンプレートを使って実際に生成された具体例:

| テンプレート | 実例 |
|:---|:---|
| `TEMPLATE_phase_instructions.md` | `docs/sessions/day6/PHASE_DELTA_INSTRUCTIONS.md` |
| `TEMPLATE_migration_instructions.md` | `docs/sessions/day6/MIGRATION_INSTRUCTIONS_v2.md` |
| `TEMPLATE_day_record.md` | (本リポジトリ外保管: `pubmed-reference-resolver-integration-chat-day6.md` 等) |

## 他スキル開発への適用

本テンプレート群は、以下の他スキル開発で**即座に適用可能**:

- `lecture-architect` (5 phase pipeline orchestrator)
- `script-generator` (speaker profile schema)
- `paper-summarizer` (mind-map style PDF)
- `peer-reviewer` / `first-peer-review`
- `kakenhi-generator`
- 将来の anonymization pipeline、ePRO dashboards、NLP pipelines 等

各スキル開発で `{{PROJECT_NAME}}` を当該スキル名に置換することで、本プロジェクトと同じ品質保証プロセス (Day1-6 で確立) が即座に適用される。

## 運用上の注意

- **テンプレート自体の更新**: Day7 以降で新たな学び (P16+) が抽出された場合、対応するテンプレートを更新すること。`docs/templates/CHANGELOG.md` を将来追加することで更新履歴を追跡可能。
- **プロジェクト固有のカスタマイズ**: 各スキル特有の事情 (例: `lecture-architect` での 5 phase pipeline) はテンプレートに含めず、各プロジェクトの実装時に追加するのが望ましい。
- **プレースホルダの命名一貫性**: 新たな変数を導入する場合、本 README の命名表に追記する。

---

**作成日**: 2026/05/02 (Phase ζ で初版作成)
**起源**: Day1-6 で確立された 12 プロトコル
**メンテナ**: 片山英樹 (Hideki Katayama)
**参照**: `docs/sessions/day6/`, Day1-6 記録 (本リポジトリ外)
