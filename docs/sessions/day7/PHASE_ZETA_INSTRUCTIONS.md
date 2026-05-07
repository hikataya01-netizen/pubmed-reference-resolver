# PHASE_ZETA_INSTRUCTIONS.md

**作成日**: 2026/05/02 (Day7 = Phase ζ)
**作成者**: Claude Opus 4.7
**対象**: Claude Code (xhigh mode 想定)
**目的**: pubmed-reference-resolver プロジェクトに `docs/sessions/day6/` への session 記録移動、`docs/templates/` の再利用基盤、`skill_package/references/USAGE_QUICKSTART.md` の即時利用ガイドを追加し、3 commits に分離して main branch に統合する
**前提**: Day6 完了状態 (commit `2f38128`, main branch 18 commits)
**プロジェクトルート**: `~/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver`

---

## 全体フロー

```
[手順 1] 事前確認 (pre-flight)
   ↓
[手順 2] ディレクトリ構造の作成 (docs/sessions/day6/, docs/templates/, skill_package/references/)
   ↓
[手順 3] root の指示書 2 件を docs/sessions/day6/ に移動
   ↓
[手順 4] 新規 6 ファイルの配置確認 (Claude Opus 提供、先生によって配置済の前提)
   ↓
[手順 5] commit 1: docs(sessions): archive day6 instruction documents
   ↓
[手順 6] commit 2: docs(templates): add reusable templates for phase/migration/day-record
   ↓
[手順 7] commit 3: docs(skill): add USAGE_QUICKSTART for immediate skill utilization
   ↓
[手順 8] 最終確認 (commit 数 21、3 件の新 commit 確認)
```

---

## 共通ルール

### 報告様式 (Day6 と同一)

各手順の完了時、以下の形式で簡潔に報告すること:

```
## 手順 N: [タイトル] 完了

### 実行結果
- 項目 N.1: <出力サマリー>
- ...

### 判定
- 期待結果との一致: <○ / × / 部分一致>
- 想定外事象: <なし / あり: 具体的内容>

### 次手順への進行可否
- <進行可 / 停止して指示待ち>
```

### stop-and-report 発動条件

Day6 の共通条件に加え、本セッション固有の以下を追加:

- 手順 4 で**期待される 6 ファイルが配置されていない**
- 手順 5-7 で commit が空になる (move/add 漏れ)

---

## 手順 1: 事前確認

### 実行コマンド

```bash
cd ~/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver

# 1.1 working tree の現状
git status

# 1.2 HEAD の確認 (Day6 末 = 2f38128)
git log -1 --format='%h %s'

# 1.3 root の untracked ファイル (移動対象 2 件) の確認
ls -la MIGRATION_INSTRUCTIONS_v2.md PHASE_DELTA_INSTRUCTIONS.md 2>&1

# 1.4 既存 docs/ ディレクトリの有無
ls -la docs/ 2>&1 || echo "(docs/ does not yet exist)"

# 1.5 既存 skill_package/references/ の確認
ls -la skill_package/references/

# 1.6 main branch commit 数
git rev-list --count main

# 1.7 git committer (Day6 で正規化済の確認)
git config --global user.name
git config --global user.email
```

### 期待される出力

| 項目 | 期待値 |
|:---|:---|
| 1.2 | `2f38128 chore(cleanup): remove deprecated baseline...` |
| 1.3 | 2 件存在 (untracked) |
| 1.4 | docs/ は存在しない |
| 1.5 | citation_style_examples.md, llm_parsing_prompt.md, pubmed_csv_schema.md (Day5 配置) |
| 1.6 | `18` |
| 1.7 | `Hideki Katayama` / `hikataya01@gmail.com` |

### stop-and-report 条件

- 1.2 で HEAD が `2f38128` でない
- 1.3 で対象 2 件が見当たらない (Day6 完了後に削除済の場合)
- 1.4 で docs/ が既に存在 (上書き判断が必要)

---

## 手順 2: ディレクトリ構造の作成

### 実行コマンド

```bash
# 2.1 docs/sessions/day6/ を作成
mkdir -p docs/sessions/day6

# 2.2 docs/templates/ を作成
mkdir -p docs/templates

# 2.3 確認
ls -la docs/
ls -la docs/sessions/
ls -la docs/templates/

# 2.4 skill_package/references/ の存在確認 (既存)
ls -la skill_package/references/
```

### 期待される出力

- 2.3 で `docs/`, `docs/sessions/`, `docs/sessions/day6/`, `docs/templates/` が空ディレクトリとして存在

---

## 手順 3: root の指示書 2 件を docs/sessions/day6/ に移動

### 実行コマンド

```bash
# 3.1 移動 (git mv は untracked ファイルでは使えないので mv を使用)
mv MIGRATION_INSTRUCTIONS_v2.md docs/sessions/day6/
mv PHASE_DELTA_INSTRUCTIONS.md docs/sessions/day6/

# 3.2 移動結果の確認
ls -la docs/sessions/day6/
ls MIGRATION_INSTRUCTIONS_v2.md PHASE_DELTA_INSTRUCTIONS.md 2>&1 || echo "(root 不在を確認)"
```

### 期待される出力

| 項目 | 期待値 |
|:---|:---|
| 3.2 | `docs/sessions/day6/` に 2 件、root に不在 |

### stop-and-report 条件

- 3.1 で移動が失敗 (権限エラー等)

---

## 手順 4: 新規 6 ファイルの配置確認

### 説明

Claude Opus が以下の 6 ファイルを生成済。先生がプロジェクトルート以下の正しい位置に配置する作業を、Claude Code 起動前に完了している前提とする。

| ファイル | 配置先 |
|:---|:---|
| README.md (sessions/day6/) | `docs/sessions/day6/README.md` |
| README.md (templates/) | `docs/templates/README.md` |
| TEMPLATE_phase_instructions.md | `docs/templates/TEMPLATE_phase_instructions.md` |
| TEMPLATE_migration_instructions.md | `docs/templates/TEMPLATE_migration_instructions.md` |
| TEMPLATE_day_record.md | `docs/templates/TEMPLATE_day_record.md` |
| USAGE_QUICKSTART.md | `skill_package/references/USAGE_QUICKSTART.md` |

### 実行コマンド

```bash
# 4.1 docs/sessions/day6/ の中身 (合計 3 ファイル)
ls -la docs/sessions/day6/

# 4.2 docs/templates/ の中身 (合計 4 ファイル)
ls -la docs/templates/

# 4.3 skill_package/references/ の中身 (既存 3 + 新 USAGE_QUICKSTART = 4 ファイル)
ls -la skill_package/references/

# 4.4 各新ファイルの行数確認 (空でないことの確認)
wc -l docs/sessions/day6/README.md
wc -l docs/templates/README.md
wc -l docs/templates/TEMPLATE_phase_instructions.md
wc -l docs/templates/TEMPLATE_migration_instructions.md
wc -l docs/templates/TEMPLATE_day_record.md
wc -l skill_package/references/USAGE_QUICKSTART.md
```

### 期待される出力

- 4.1: 3 ファイル (README.md + MIGRATION_INSTRUCTIONS_v2.md + PHASE_DELTA_INSTRUCTIONS.md)
- 4.2: 4 ファイル (README.md + TEMPLATE_*.md × 3)
- 4.3: 4 ファイル (既存 3 + USAGE_QUICKSTART.md)
- 4.4: 全ファイルが 30 行以上 (空でないことの確認)

### stop-and-report 条件

- 4.1-4.3 でいずれかの新ファイルが配置されていない
- 4.4 でいずれかが極端に少ない (例: 5 行未満)

---

## 手順 5: commit 1 — docs/sessions/day6/ の git 追加

### 実行コマンド

```bash
# 5.1 staging
git add docs/sessions/day6/

# 5.2 staged 状態の確認
git status
git diff --cached --stat

# 5.3 commit 作成
git commit -m "docs(sessions): archive day6 instruction documents

Move the two instruction documents created during Day6 (Phase delta + epsilon)
from project root to docs/sessions/day6/ for permanent archival:

- MIGRATION_INSTRUCTIONS_v2.md (Sensei-facing concept document)
- PHASE_DELTA_INSTRUCTIONS.md (Claude Code-facing execution instructions)

Add docs/sessions/day6/README.md to explain the contents of this directory
and serve as the index for future Day7+ sessions in docs/sessions/day7/, etc.

This establishes the docs/sessions/dayN/ convention for session archival,
enabling archaeological review of the entire 6-day collaboration record
within the project repository.

Refs: Day6 record X-1 (instruction file git management decision),
      Day6 record VIII (4 new lessons P12-P15)"

# 5.4 commit 確認
git log -1 --format='%h %s'
```

### 期待される出力

- 5.2 で 3 ファイル (README.md + 移動 2 件) が staged
- 5.4 で新 commit hash が `docs(sessions): archive day6 instruction documents`

### stop-and-report 条件

- 5.2 で staging が想定数 (3 ファイル) と異なる

---

## 手順 6: commit 2 — docs/templates/ の git 追加

### 実行コマンド

```bash
# 6.1 staging
git add docs/templates/

# 6.2 staged 状態の確認
git status
git diff --cached --stat

# 6.3 commit 作成
git commit -m "docs(templates): add reusable templates for phase/migration/day-record

Establish docs/templates/ as the canonical location for reusable templates
distilled from the Day1-6 collaboration methodology. Three templates added:

- TEMPLATE_phase_instructions.md: Skeleton for PHASE_*_INSTRUCTIONS.md
  (Claude Code-facing execution instructions)
- TEMPLATE_migration_instructions.md: Skeleton for MIGRATION_*.md
  (Sensei-facing concept and rollback documents)
- TEMPLATE_day_record.md: Skeleton for Day records following the
  Day3-6 chapter convention (I-XII chapter structure)

All templates use {{VAR}} placeholder syntax for variable substitution.
Includes README.md explaining usage workflow and protocol references.

These templates encode the 12 protocols established across Day1-6:
1. 5-stage prior consultation (Day4 P4)
2. Stop-and-report protocol (Day1-Day6)
3. Investigation phase isolation (Day3 B / Day5)
4. Two-stage instruction approach (Day5 P10)
5. Authenticity verification mid-insertion (Day5 P11)
6. Principle tension arbitration (Day3 F)
7. Day record chapter template (Day3-Day6)
8. Commit message convention (Day1-Day6)
9. Real-time validation as side effect (Day6 P12)
10. Pre-execution sequence review (Day6 P13)
11. Three-tier reporting model (Day6 P14)
12. Dynamic pre-check calibration (Day6 P15)

Future skill development (lecture-architect, script-generator,
paper-summarizer, anonymization pipeline) can immediately apply
these templates by substituting placeholders.

Refs: Day6 record IX (lessons P12-P15),付録 F (12 protocols list)"

# 6.4 commit 確認
git log -1 --format='%h %s'
```

### 期待される出力

- 6.2 で 4 ファイル (README.md + TEMPLATE × 3) が staged

### stop-and-report 条件

- 6.2 で staging が想定数 (4 ファイル) と異なる

---

## 手順 7: commit 3 — skill_package/references/USAGE_QUICKSTART.md の git 追加

### 実行コマンド

```bash
# 7.1 staging
git add skill_package/references/USAGE_QUICKSTART.md

# 7.2 staged 状態の確認
git status
git diff --cached --stat

# 7.3 commit 作成
git commit -m "docs(skill): add USAGE_QUICKSTART for immediate skill utilization

Add skill_package/references/USAGE_QUICKSTART.md as the canonical
quickstart guide for end-users of the pubmed-reference-resolver skill.

The guide covers three primary scenarios with concrete invocation prompts:
1. Single-paper reference verification (peer review use case)
2. Multi-paper batch verification (systematic review use case)
3. AI-fabricated citation detection (LLM hallucination check)

Each scenario provides:
- Trigger phrase template (Japanese)
- Expected input format
- Expected output deliverables (CSV / Abstract text / audit report)
- Common pitfalls and mitigations

The file is placed in skill_package/references/ so that it is accessible
via the symlinked skill folder (~/.claude/skills/pubmed-reference-resolver/
references/USAGE_QUICKSTART.md), making it immediately discoverable when
the skill is triggered.

Refs: Day6 record V (real-time validation of C-1-beta deployment),
      Day6 record IX-3 (three-actor collaboration model)"

# 7.4 commit 確認
git log -1 --format='%h %s'
```

### 期待される出力

- 7.2 で 1 ファイルが staged

---

## 手順 8: 最終確認

### 実行コマンド

```bash
# 8.1 working tree が clean であることを確認
git status

# 8.2 main branch の最終 commit 数
git rev-list --count main

# 8.3 直近 5 commit の確認 (3 新 commit + Day6 + Day5)
git log -5 --format='%h %s'

# 8.4 docs/ 階層の最終構造
find docs/ -type f | sort

# 8.5 skill_package/references/ の最終構造
ls -la skill_package/references/

# 8.6 symlink 経由でも USAGE_QUICKSTART が読めることを確認
wc -l ~/.claude/skills/pubmed-reference-resolver/references/USAGE_QUICKSTART.md
```

### 期待される最終状態

| 検証項目 | 期待値 |
|:---|:---|
| 8.1 (`git status`) | `nothing to commit, working tree clean` (`.DS_Store` 等は許容) |
| 8.2 (commit 数) | `21` (Day6 末 18 から +3) |
| 8.3 (直近 5) | 3 新 commit + `2f38128` + `5825c86` |
| 8.4 (docs/) | 7 ファイル (sessions/day6/ 3 件 + templates/ 4 件) |
| 8.5 (skill_package/references/) | 4 ファイル |
| 8.6 (symlink 経由) | USAGE_QUICKSTART.md が読める (二段 symlink 解決確認) |

### 完了報告様式

```
## Phase ζ (Day7 docs 整備) 完了報告

### 達成項目
- [x] docs/sessions/day6/ への移動 + README.md 追加 (commit <hash1>)
- [x] docs/templates/ + 4 ファイル追加 (commit <hash2>)
- [x] skill_package/references/USAGE_QUICKSTART.md 追加 (commit <hash3>)
- [x] symlink 経由での USAGE_QUICKSTART 読み出し成功

### main branch 最終形状
- 総 commit 数: 21 (Day6 末 18 から +3)
- 新 commit (古い順):
  - <hash1> docs(sessions): archive day6 instruction documents
  - <hash2> docs(templates): add reusable templates for phase/migration/day-record
  - <hash3> docs(skill): add USAGE_QUICKSTART for immediate skill utilization

### 想定外事象
- なし / あり: <内容>

### 所要時間
- 開始: <時刻>
- 終了: <時刻>
- 総所要: <分>
```

---

## トラブルシューティング (FAQ)

### Q1. 手順 4 で先生が新ファイルを配置していない場合は?

→ stop-and-report を発動し、配置を依頼。Claude Code は手順 5 以降に進まないこと。

### Q2. 手順 5-7 で commit message が長すぎてエラーになる場合

→ macOS の標準 git は数千行の commit message を許容するため通常エラーにならないが、もしエラーになる場合は heredoc を使用:
```bash
git commit -F - <<EOF
docs(sessions): archive day6 instruction documents

[本文]
EOF
```

### Q3. 手順 8.6 で symlink 経由読み出しが失敗

→ Day6 の C-1-β の symlink 切替に問題がある可能性。`ls -la ~/.claude/skills/pubmed-reference-resolver` で symlink の状態を確認し、必要に応じて Day6 のロールバック手順を参照。

---

**作成日**: 2026/05/02
**作成者**: Claude Opus 4.7
**ファイル名**: `PHASE_ZETA_INSTRUCTIONS.md`
**前提**: Day6 完了状態 (commit `2f38128`, main 18 commits)
**完了後の状態**: main 21 commits、docs/ 階層確立、USAGE_QUICKSTART で即時利用可能
**完了後の予定**: 先生 → Claude Opus へ完了報告 → Day7 記録の作成 (本指示書実行は Day7 = Phase ζ として記録される)
