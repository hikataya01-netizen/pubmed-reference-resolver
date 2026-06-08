# dev-light / dev-strict スキル作成 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** superpowers ワークフローの「重さプロファイル」を 2 つの user-level カスタムスキル (dev-light / dev-strict) として作成し、タスクの性質に応じて軽量/厳格を使い分けられるようにする。

**Architecture:** superpowers ラッパー型。各スキルは `~/.claude/skills/<name>/SKILL.md` として配置し、superpowers サブスキル (brainstorming / writing-plans / executing-plans / subagent-driven-development) を controller が呼ぶ順序とパラメータを規定する指示書。superpowers 本体は非改変、HARD-GATE 温存。

**Tech Stack:** Markdown (SKILL.md frontmatter + 本文)、superpowers プラグイン

**Spec:** `docs/superpowers/specs/2026-06-08-dev-light-dev-strict-skills-design.md`

**起点 commit:** `6b1bccc` (dev-light/dev-strict spec)

**期待 final state:** `~/.claude/skills/dev-light/SKILL.md` と `~/.claude/skills/dev-strict/SKILL.md` が存在、両者の description が意図通り区別され、内部記述に矛盾なし。plan は本 repo に commit。

---

## File Structure

| File | 役割 | git 管理 | Task |
|:---|:---|:---:|:---:|
| `~/.claude/skills/dev-light/SKILL.md` | dev-light スキル本体 | 管理外 (user-level) | Task 1 |
| `~/.claude/skills/dev-strict/SKILL.md` | dev-strict スキル本体 | 管理外 (user-level) | Task 2 |
| `docs/superpowers/plans/2026-06-08-dev-light-dev-strict-skills.md` | この plan | 管理 | Task 0 |

**注**: スキル本体は user-level のため pubmed-reference-resolver の git 外。git に commit するのは plan のみ。検証は skill 内容の論理チェック (実行コードでないため)。

---

## Task 0: Plan を commit

**Files:**
- Create: `docs/superpowers/plans/2026-06-08-dev-light-dev-strict-skills.md` (この file)

- [ ] **Step 1: plan file 存在確認**

Run: `ls docs/superpowers/plans/2026-06-08-dev-light-dev-strict-skills.md`
Expected: ファイル存在

- [ ] **Step 2: stage + commit**

```bash
git add docs/superpowers/plans/2026-06-08-dev-light-dev-strict-skills.md
git commit -m "$(cat <<'EOF'
docs(plan): add dev-light/dev-strict skills creation plan

2 つの SKILL.md (dev-light / dev-strict) の完全な内容と検証手順を
bite-sized task に分解。スキル本体は ~/.claude/skills/ (git 管理外)、
plan のみ本 repo に commit。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: commit 確認**

Run: `git log --oneline -1`
Expected: `<SHA> docs(plan): add dev-light/dev-strict skills creation plan`

---

## Task 1: dev-light/SKILL.md 作成

**Files:**
- Create: `~/.claude/skills/dev-light/SKILL.md`

- [ ] **Step 1: ディレクトリ作成**

```bash
mkdir -p ~/.claude/skills/dev-light
```

- [ ] **Step 2: SKILL.md を作成**

Write tool で `~/.claude/skills/dev-light/SKILL.md` を以下の内容で作成 (末尾改行あり):

```markdown
---
name: dev-light
description: "軽量・高速な開発ワークフロー。小〜中規模かつ低リスクの変更 (config・docs・style・単純な関数/test 追加・小さなバグ修正) を、subagent を使わず inline 実装で素早く仕上げる。superpowers の brainstorming(質問最小)→ spec+plan 統合 → executing-plans(inline)→ inline review の流れをオーケストレーションする。parser/正規表現/境界ロジック/アルゴリズム/複数ファイル統合/セキュリティ/データ破壊リスクを含む高リスク変更は dev-strict に切り替える。以下のリクエストで使用: 「dev-light で」「軽量に開発して」「素早く実装して」「小さな変更を inline で」「サクッと直して(設計を伴う場合)」。重い二段レビューが不要な低リスク開発タスク全般。"
---

# dev-light — 軽量開発ワークフロー

小〜中規模・低リスクの開発タスクを、subagent dispatch のオーバーヘッドなしで
素早く仕上げるためのオーケストレーション・スキル。superpowers の各サブスキルを
「軽い匙加減」で呼ぶ。

## 前提

- superpowers プラグインが利用可能であること (本スキルはラッパー型)
- ユーザーの明示指示 (CLAUDE.md) が最優先

## いつ使うか / いつ dev-strict に切り替えるか

**dev-light が適する**: config 追加・docs 作成・style 修正・単純な関数追加・
test 追加・小さなバグ修正など、変更の影響が局所的で読みやすいタスク。

**dev-strict に切り替えるべき (格上げ基準)**: 以下のいずれかを含む変更は、
個別 Task 単位で subagent + 二段 adversarial review に格上げするか、作業全体を
dev-strict に切り替える:

1. parser / 正規表現 / 境界ロジック / アルゴリズムの微妙な変更
2. 複数ファイルに跨り副作用が読みにくい統合
3. セキュリティ (認証・機密・権限) に関わる変更
4. データ破壊リスク (一括修正・削除・migration)

## フロー

1. **brainstorming** (superpowers:brainstorming を invoke)
   - HARD-GATE は維持 (design 承認まで実装しない)
   - ただし質問は「推奨即決」で最小化。明確な選択は推奨案を提示して即確認
2. **spec + plan を 1 doc に統合**
   - 別々の commit にせず、1 つの設計+計画 doc にまとめて 1 commit
   - bite-sized step は省略可。要点 (変更ファイル・手順・検証) のみ
3. **inline 実装** (superpowers:executing-plans を invoke)
   - controller (自分) が直接実装。subagent は dispatch しない
   - 格上げ基準に該当する Task のみ、例外的に subagent + 二段 review
4. **inline review** (superpowers:verification-before-completion を活用)
   - 自分でセルフチェック (test 実行・diff 確認・lint)
   - 格上げした Task は二段 adversarial review を適用
5. **archive** (オプション)
   - プロジェクトに archive/LESSONS の慣習があれば作成。なければ省略

## モデル階層化 (格上げした subagent を使う場合)

Agent tool の model パラメータ:

| タスク種別 | モデル |
|:---|:---|
| 機械的実装 (config/style/docs/単純 test) | haiku |
| 統合・判断を伴う実装、spec/quality review | sonnet |
| 設計判断・最終 review | opus (または親継承) |

原則: 各ロールを処理できる least powerful model を選ぶ。haiku で不足が出たら
sonnet に格上げ。

## superpowers サブスキルとの関係

- brainstorming: 質問最小化して使う (HARD-GATE は温存)
- writing-plans: フル bite-sized は省略、spec と統合
- executing-plans: inline 実装の土台
- subagent-driven-development: 格上げ Task のみ部分的に使う
- 重い変更全般 → dev-strict へ
```

- [ ] **Step 3: 作成確認**

```bash
cat ~/.claude/skills/dev-light/SKILL.md | head -5
wc -l ~/.claude/skills/dev-light/SKILL.md
```
Expected: frontmatter (name: dev-light) が表示される、約 70 行

---

## Task 2: dev-strict/SKILL.md 作成

**Files:**
- Create: `~/.claude/skills/dev-strict/SKILL.md`

- [ ] **Step 1: ディレクトリ作成**

```bash
mkdir -p ~/.claude/skills/dev-strict
```

- [ ] **Step 2: SKILL.md を作成**

Write tool で `~/.claude/skills/dev-strict/SKILL.md` を以下の内容で作成 (末尾改行あり):

```markdown
---
name: dev-strict
description: "品質最優先の厳格な開発ワークフロー。parser/アルゴリズムの中核ロジック変更・大規模 migration・破壊的操作・複数サブシステム統合・絶対に壊したくない高リスク変更を、フル subagent-driven-development + 二段 adversarial review (spec compliance → code quality) で実装する。superpowers の brainstorming(フル)→ writing-plans(フル bite-sized)→ subagent-driven-development(全 Task で implementer + 二段 review)→ archive の流れをオーケストレーションし、モデル階層化で速度を底上げする。以下のリクエストで使用: 「dev-strict で」「厳格に開発して」「フルレビューで」「品質最優先で」「高リスクな変更を慎重に」「parser/アルゴリズムを直して」「migration を安全に」。小〜中規模・低リスクの変更は dev-light に切り替える。"
---

# dev-strict — 厳格開発ワークフロー

高リスク・高重要度の開発タスクを、二段 adversarial review で確実に仕上げる
ためのオーケストレーション・スキル。Day22〜30 で実証した superpowers
フルフローそのままに、モデル階層化で速度を底上げする。

## 前提

- superpowers プラグインが利用可能であること (本スキルはラッパー型)
- ユーザーの明示指示 (CLAUDE.md) が最優先

## いつ使うか / いつ dev-light に切り替えるか

**dev-strict が適する**:

1. parser / アルゴリズムの中核ロジック変更
2. 大規模 migration、破壊的操作を伴う作業
3. 複数サブシステムに跨る統合
4. セキュリティ・データ破壊リスクのある変更
5. 「絶対に壊したくない」高リスク変更

**dev-light に切り替えるべき**: config・docs・style・単純な関数/test 追加など、
変更の影響が局所的で二段レビューが過剰なタスク。

## フロー

1. **brainstorming** (superpowers:brainstorming を invoke、フル)
   - HARD-GATE 厳守。論点を 1 つずつ詰める
   - 設計を spec doc に書き出し commit、user review gate を通す
2. **writing-plans** (superpowers:writing-plans を invoke、フル)
   - bite-sized task に分解、各 step に完全なコード・コマンド・期待値
   - plan を commit
3. **subagent-driven-development** (superpowers:subagent-driven-development を invoke)
   - 全 Task で fresh implementer subagent を dispatch
   - 各 Task 後に二段 review: (1) spec compliance → (2) code quality
   - reviewer が issue を出したら implementer が修正 → 再 review
4. **archive**
   - プロジェクトの慣習 (README + LESSONS 等) に従って成果と学びを記録

## モデル階層化 (速度底上げ)

Agent tool の model パラメータでタスク種別に割り当てる:

| タスク種別 | モデル | 例 |
|:---|:---|:---|
| 機械的実装 | haiku | config・style・docs・単純 test |
| 統合・判断を伴う実装 | sonnet | parser 修正・複数ファイル統合・デバッグ |
| spec compliance review | sonnet | 仕様準拠の照合 |
| code quality review | sonnet | 品質・保守性評価 |
| 設計判断・最終 review | opus (または親継承) | アーキテクチャ・横断的最終確認 |

原則: 各ロールを処理できる least powerful model を選ぶ。haiku で BLOCKED に
なったら sonnet、sonnet で判断に詰まったら opus に格上げ。

## 二段 adversarial review を省略しない

dev-strict の核心は「全 Task で spec compliance review → code quality review」
を通すこと。reviewer は repo を再走査して網羅検証する。これにより
plausible-but-wrong な実装が main に入るのを防ぐ。軽い変更で二段 review が
過剰と感じたら、その Task (または作業全体) を dev-light に切り替える。

## superpowers サブスキルとの関係

- brainstorming / writing-plans / subagent-driven-development をフルに使う
- 軽い変更全般 → dev-light へ
```

- [ ] **Step 3: 作成確認**

```bash
cat ~/.claude/skills/dev-strict/SKILL.md | head -5
wc -l ~/.claude/skills/dev-strict/SKILL.md
```
Expected: frontmatter (name: dev-strict) が表示される、約 75 行

---

## Task 3: 検証 (skill-reviewer) + 最終確認

**Files:** なし (検証のみ)

**目的:** 2 スキルの description トリガーと内部記述を検証し、矛盾・曖昧さがないことを確認する。

- [ ] **Step 1: 両 SKILL.md の存在と frontmatter 確認**

```bash
ls ~/.claude/skills/dev-light/SKILL.md ~/.claude/skills/dev-strict/SKILL.md
head -3 ~/.claude/skills/dev-light/SKILL.md
head -3 ~/.claude/skills/dev-strict/SKILL.md
```
Expected: 両ファイル存在、それぞれ `name: dev-light` / `name: dev-strict`

- [ ] **Step 2: トリガーの相互排他性チェック (controller が論理確認)**

以下を確認 (Read tool で両 description を読み、論理チェック):
- dev-light は「小〜中規模・低リスク」、dev-strict は「高リスク・中核ロジック」を担当
- 格上げ基準 (parser/正規表現/境界/統合/セキュリティ/データ破壊) が両者で一貫
- 相互参照 (dev-light → dev-strict、dev-strict → dev-light) が存在
- 同一タスクが両方に強くマッチする曖昧さがないか

- [ ] **Step 3: skill-reviewer で品質レビュー (任意、利用可能なら)**

`plugin-dev:skill-reviewer` agent または `superpowers:writing-skills` の検証手順で
2 スキルの description triggering 効果をレビューする。CRITICAL な曖昧さがあれば修正。

実行例 (skill-reviewer が利用可能な場合):
```
Agent tool で subagent_type: "plugin-dev:skill-reviewer" を dispatch し、
~/.claude/skills/dev-light/SKILL.md と ~/.claude/skills/dev-strict/SKILL.md を
レビュー。description のトリガー妥当性・本文の明瞭性・相互参照の整合を確認。
```

- [ ] **Step 4: 最終 state 確認**

```bash
ls -la ~/.claude/skills/ | grep -E 'dev-light|dev-strict'
git -C /Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver log --oneline -3
git -C /Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver status
```
Expected:
- dev-light / dev-strict ディレクトリが user-level skills に存在
- repo は spec + plan の 2 commit が記録され clean

注: スキル本体は git 管理外のため、最終的に repo に残るのは spec (`6b1bccc`) と
plan (Task 0) の 2 commit。スキル作成の記録はこの spec/plan に残る。

---

## Self-review notes

### スキル本体が git 管理外であること

dev-light/dev-strict の SKILL.md は user-level (`~/.claude/skills/`) のため
pubmed-reference-resolver の git に入らない。これは spec §8 の設計判断通り。
repo には設計記録 (spec/plan) のみ残る。バックアップが必要なら別途
dotfiles 管理等を検討 (本 plan のスコープ外)。

### 検証の限界

スキルは実行コードでないため、真の検証は「次回セッションで dev-light を実際に
使い、subagent 数・処理時間が削減されるか測定」となる。本 plan の Task 3 は
静的な論理チェック + skill-reviewer による description 品質確認まで。

### archive の扱い

このスキル作成タスク自体は軽量なので、専用の archive (README + LESSONS) は
作らない。spec/plan が記録を兼ねる。
```

---

**End of Plan**
