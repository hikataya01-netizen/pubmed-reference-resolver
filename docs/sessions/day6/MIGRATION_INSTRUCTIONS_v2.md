# MIGRATION_INSTRUCTIONS_v2.md

**作成日**: 2026/05/02 (Day6 = Phase δ + ε)
**作成者**: Claude Opus 4.7
**対象**: 片山英樹先生
**目的**: pubmed-reference-resolver スキル化作業 (Phase δ + ε) の概念解説と、Claude Code 向け実行指示書 (`PHASE_DELTA_INSTRUCTIONS.md`) を投入する際のガイダンス
**v1 (2026/05/01) からの差分**: パス前提誤りの修正、deployment 戦略の確定 (C-1-β)、git committer 正規化の追加

---

## I. v1 からの主要変更点

| 項目 | v1 (Day5) | v2 (Day6, 本書) | 修正理由 |
|:---|:---|:---|:---|
| スキル配置パス | `~/Library/Application Support/Claude/skills/` 想定 | **`~/.claude/skills/`** 確定 | Day5 Phase β の調査で実在パスが判明 |
| Deployment 戦略 | 未決定 | **C-1-β (symlink 方式)** で確定 | 単一情報源原則と即時反映性を優先 |
| 既存スキルフォルダの扱い | 上書き想定 | **`.old.20260502` にバックアップ後 symlink で置換** | ロールバック可能性の確保 |
| git committer 正規化 | スコープ外 | **本セッションの手順 2 として組込** | Day5 末で発見された未設定問題への対処 |
| バックアップ整理 | スコープ外 | **手順 5 (ε-1) として組込** | Day5 末で残存していた `/tmp/` バックアップの整理 |

---

## II. 本日の作業全体像 (Phase δ + ε)

### II-1. 5 タスクの一覧と依存関係

| 手順 | 略称 | 内容 | 担当 | 依存 |
|:---:|:---|:---|:---|:---|
| 1 | (pre-flight) | 事前確認 | Claude Code | なし |
| 2 | δ-4 (再配置) | git committer 正規化 (`--global`) | Claude Code | 手順 1 完了 |
| 3 | δ-2 | A-1: root の baseline 古版 2 ファイルの `git rm` + commit | Claude Code | 手順 2 完了 (commit identity が必要) |
| 4 | δ-3 | C-1: `~/.claude/skills/pubmed-reference-resolver` を skill_package/ への symlink に切替 | Claude Code | 手順 3 とは独立 |
| 5 | ε-1 | `/tmp/skill_package_backup_20260501/` の削除 | Claude Code | 手順 4 (C-1) 完了後 |
| 6 | (final-check) | 最終確認 | Claude Code | 全手順完了 |

### II-2. 順序設計の根拠

- **手順 2 (git committer 正規化) を手順 3 (A-1 commit) より前に置く**: 手順 3 で生成される新 commit に正規化済 identity (`Hideki Katayama <hikataya01@gmail.com>`) を記録するため。これは Day5 学び P11 (真正性の中間検証) の精神に沿う。
- **手順 4 (C-1) を手順 3 (A-1) と独立扱い**: A-1 はプロジェクト内の git 操作、C-1 は `~/.claude/skills/` への filesystem 操作で、依存関係はない。順序入替は実害なし。
- **手順 5 (ε-1) を手順 4 (C-1) 後に置く**: バックアップ削除は最後に行うことで、C-1 で問題が発生した場合のロールバック余地を確保。

### II-3. 所要時間見積り

30〜60 分。Day5 完了後の clean な状態から開始し、stop-and-report 発動なしで完遂した場合の見積り。

---

## III. 採用方針: C-1-β (symlink architecture)

### III-1. C-1-β の本質

`~/.claude/skills/pubmed-reference-resolver` 自体を、プロジェクト内の `skill_package/` へのシンボリックリンク (symlink) として作成する方式。

```
~/.claude/skills/pubmed-reference-resolver
            ↓ (symlink)
/Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver/skill_package/
```

### III-2. 二段 symlink 解決の動作原理

skill_package/ 内には既に 4 件の相対 symlink が存在する:

```
skill_package/main.py             → ../main.py
skill_package/journal_audit.py    → ../journal_audit.py
skill_package/mdpi_parser.py      → ../mdpi_parser.py
skill_package/manual_overrides.yaml → ../integration/src/manual_overrides.yaml
```

`~/.claude/skills/pubmed-reference-resolver/main.py` をアクセスする際の解決過程:

1. OS が `~/.claude/skills/pubmed-reference-resolver` の symlink を解決し、`/Users/.../pubmed-reference-resolver/skill_package` に到達
2. 当該位置の `main.py` を読み出そうとするが、これも symlink (`../main.py`)
3. **相対 symlink は symlink の実在位置 (=skill_package/) を起点に解決される**ため、`/Users/.../pubmed-reference-resolver/main.py` (実体) に到達
4. 実体ファイルが返却される

この二段解決は POSIX 仕様に準拠した動作であり、macOS でも Linux でも同様に機能する。

### III-3. C-1-β を採用した 3 つの根拠

1. **Day5 学び P11 (真正性の中間検証) との整合**: 単一情報源を維持することで、skill 側と project 側の真正性差分が原理的に発生しない。
2. **Day3 学び E (既存 API を無改修に保つ) の精神の延長**: 開発と配布を分離せず、開発成果がそのまま配布形態として機能する。
3. **個人利用前提の即時反映性**: 現時点では先生個人での利用が想定されるため、portability (移植性) より即時反映性が優先される。

### III-4. 採用に伴う既知の制約

- **プロジェクト移動時の脆弱性**: `~/Desktop/Claude/査読用/...` から pubmed-reference-resolver/ プロジェクトを移動した瞬間に skill が機能しなくなる。
- **複数端末での非可搬性**: 別の Mac に skill だけコピーしても動作しない (プロジェクト全体のコピーが必要)。
- **将来の GitHub 公開時の課題**: 公開配布フェーズでは C-1-α (実体化) への切替が必要となる可能性が高い。

これらは現時点では許容され、将来の段階で再評価する設計判断である。

---

## IV. 変更前後の状態比較

### IV-1. 変更前 (Day5 完了時 = Day6 開始時)

```
~/.claude/skills/
└── pubmed-reference-resolver/      ← 旧スキル (Phase 0-4 期実装、実体)
    ├── SKILL.md                    ← 旧版
    └── ...

~/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver/
├── SKILL.md                        ← HEAD 版 (旧、git 管理下、clean)
├── DEVELOPMENT_NOTES.md            ← HEAD 版 (旧、git 管理下、clean)
├── main.py                         ← 実装本体
├── journal_audit.py
├── mdpi_parser.py
├── integration/src/manual_overrides.yaml
└── skill_package/                  ← Day5 で構築 (commit 5825c86)
    ├── SKILL.md                    ← 新版 (実体、13070 bytes)
    ├── DEVELOPMENT_NOTES.md        ← 新版 (実体、16320 bytes)
    └── (symlink 4 件 + references/ + examples/)

/tmp/
└── skill_package_backup_20260501/  ← Day5 のバックアップ (残存)

git config (global): user.name / user.email 未設定
```

### IV-2. 変更後 (Day6 完了時)

```
~/.claude/skills/
├── pubmed-reference-resolver       ← symlink (新)
│         ↓
│   /Users/.../pubmed-reference-resolver/skill_package/
└── pubmed-reference-resolver.old.20260502/  ← バックアップ (旧スキル、削除待ち)
    └── ...

~/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver/
├── (root の SKILL.md / DEVELOPMENT_NOTES.md は削除済、新 commit に記録)
├── main.py                         ← 実装本体 (変更なし)
├── journal_audit.py
├── mdpi_parser.py
├── integration/src/manual_overrides.yaml
└── skill_package/                  ← 変更なし
    ├── SKILL.md                    ← 新版 (これが skill 本体として機能)
    └── ...

/tmp/                               ← skill_package_backup_20260501/ 削除済

git config (global):
  user.name = Hideki Katayama
  user.email = hikataya01@gmail.com

main branch: 18 commits (Day6 で +1)
  最新: chore(cleanup): remove deprecated baseline SKILL.md/DEVELOPMENT_NOTES.md
```

### IV-3. 変更による効果の検証可能性

| 検証項目 | コマンド | 期待結果 |
|:---|:---|:---|
| skill symlink の張替確認 | `ls -la ~/.claude/skills/pubmed-reference-resolver` | `pubmed-reference-resolver -> /Users/.../skill_package` 表示 |
| skill 経由での新版 SKILL.md アクセス | `wc -c ~/.claude/skills/pubmed-reference-resolver/SKILL.md` | `13070` |
| symlink 二段解決の動作確認 | `head -5 ~/.claude/skills/pubmed-reference-resolver/main.py` | プロジェクト本体の main.py 冒頭が表示される |
| git committer 反映確認 | `git log -1 --format='%an <%ae>'` | `Hideki Katayama <hikataya01@gmail.com>` |
| バックアップ削除確認 | `ls /tmp/ \| grep skill_package_backup` | (出力なし) |

---

## V. ロールバック手順

万一、本作業の途中または完了後に問題が発生した場合の復旧手順を以下に記載する。

### V-1. 手順 4 (C-1 symlink 切替) のロールバック

```bash
# symlink を削除し、バックアップを復元
rm ~/.claude/skills/pubmed-reference-resolver
mv ~/.claude/skills/pubmed-reference-resolver.old.20260502 ~/.claude/skills/pubmed-reference-resolver

# 確認
ls -la ~/.claude/skills/pubmed-reference-resolver
```

これにより旧スキル状態に完全復帰する。

### V-2. 手順 3 (A-1 git rm) のロールバック

```bash
cd ~/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver
git revert HEAD
# または直前の commit を未 push のうちに巻き戻す:
# git reset --hard HEAD~1
```

### V-3. 手順 2 (git committer 正規化) のロールバック

```bash
git config --global --unset user.name
git config --global --unset user.email
# (元の状態は「未設定」だったため、unset で完全復旧)
```

### V-4. 全体ロールバック手順

V-1 → V-2 → V-3 の順で実行することで、Day6 開始時の状態に完全復帰する。なお、`/tmp/skill_package_backup_20260501/` は削除済のため復旧できないが、これは元来 Phase β の中間バックアップであり、現時点では有用性が低い。

---

## VI. Claude Code への投入方法

### VI-1. 投入ファイル

`PHASE_DELTA_INSTRUCTIONS.md` (約 600〜700 行を予定、別ファイルとして提供)

### VI-2. 投入時の指示プロンプト (推奨テンプレート)

```
PHASE_DELTA_INSTRUCTIONS.md に従って、pubmed-reference-resolver の
Phase δ + ε (Day6 作業) を実施してください。

各手順での確認結果は手順番号付きで報告してください。
想定外事象 (stop-and-report 条件) に該当した場合は即座に停止し、
状況を報告してください。

プロジェクトルート: ~/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver
```

### VI-3. Claude Code の振る舞いに関する想定

- **想定通りに進む場合**: 手順 1 から 6 まで順次実行し、最終確認 (手順 6) の出力を全項目 OK として報告。
- **想定外事象が発生する場合**: 該当手順で stop-and-report を発動し、状況を報告。先生が判断して再開指示または別途対応。

### VI-4. 想定外事象の典型例 (Day5 の経験から)

| シナリオ | 対応 |
|:---|:---|
| working tree が dirty (modified ファイルあり) | 手順 1 で停止、状況報告 |
| `~/.claude/skills/` 自体が存在しない | 手順 4 前段で停止、ディレクトリ作成の可否を確認 |
| `/tmp/skill_package_backup_20260501/` が既に削除済 | 手順 5 をスキップ可と判断、続行 |
| symlink 作成後の検証で main.py が読めない | 手順 4 内で停止、symlink 解決経路を再点検 |

---

## VII. 完了後の状態

本作業完了後、以下が達成される。

1. **スキルの完全反映**: `~/.claude/skills/pubmed-reference-resolver` 経由で新版 (Day1-5 統合実装) が利用可能。
2. **プロジェクトの clean 化**: root の baseline 古版 SKILL.md/DEVELOPMENT_NOTES.md が git history に削除記録として残り、現状はクリーン。
3. **git identity の確立**: `Hideki Katayama <hikataya01@gmail.com>` で全 commit が記録される基盤が整い、将来の GitHub push 時の identity 一貫性が確保される。
4. **バックアップの整理**: `/tmp/` 配下の中間バックアップが削除され、disk 領域の節約と作業履歴の clean 化が実現。
5. **次セッションへの橋渡し**: Day6 記録 (`pubmed-reference-resolver-integration-chat-day6.md`) を作成することで、5 日間の協働体系の継続性が保たれる。

---

## VIII. 残存タスク (Day6 後)

本作業完了後も以下のタスクが残る。これらは別セッションで対応する。

| 優先度 | タスク | 関連 |
|:---:|:---|:---|
| ★★★ | 実データ Phase 0 検証 | NCBI API Key 取得後 |
| ★★☆ | ライセンス方針決定 | 岡山大学知財規則確認 |
| ★★☆ | GitHub remote 追加と push | ライセンス決定との連動 |
| ★☆☆ | `~/.claude/skills/pubmed-reference-resolver.old.20260502` の最終削除 | 1〜2 週間の動作確認後 |
| ★☆☆ | integration/ 全体再編 | 構造判断作業 |

---

**記録**: 本書は MIGRATION_INSTRUCTIONS.md (v1, Day5 作成) の改訂版である。v1 の内容は Day5 のスナップショットとして保持し、本書 v2 を Day6 以降の正本とする。

**作成日**: 2026/05/02
**作成者**: Claude Opus 4.7
**ファイル名**: `MIGRATION_INSTRUCTIONS_v2.md`
**対応指示書**: `PHASE_DELTA_INSTRUCTIONS.md` (同梱)
**ステータス**: 設計確定、Claude Code への投入準備完了
