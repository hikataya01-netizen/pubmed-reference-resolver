# PHASE_DELTA_INSTRUCTIONS.md

**作成日**: 2026/05/02 (Day6)
**作成者**: Claude Opus 4.7
**対象**: Claude Code (xhigh mode 想定)
**目的**: pubmed-reference-resolver の Phase δ (A-1 + C-1 + git committer 正規化) と Phase ε (D: バックアップ削除) を統合した 6 手順 = 一括実行
**前提**: Day5 完了状態 (commit `5825c86`, main branch 17 commits)
**プロジェクトルート**: `~/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver`

---

## 全体フロー

```
[手順 1] 事前確認 (pre-flight)
   ↓ (全項目 OK の場合のみ進行)
[手順 2] git committer 正規化 (--global)
   ↓
[手順 3] A-1: root の古版 SKILL.md/DEVELOPMENT_NOTES.md の git rm + commit
   ↓ (新 commit に正規化 identity が反映されることを確認)
[手順 4] C-1: ~/.claude/skills/pubmed-reference-resolver を skill_package/ への symlink に切替
   ↓ (二段 symlink 解決の動作確認まで含む)
[手順 5] ε-1: /tmp/skill_package_backup_20260501/ の削除
   ↓
[手順 6] 最終確認 (全項目チェックリスト)
```

各手順は**完了を逐次報告**し、想定外事象に該当した場合は**直ちに停止して報告** (stop-and-report) すること。

---

## 共通ルール

### 報告の様式

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

### stop-and-report 発動条件 (全手順共通)

以下のいずれかに該当した場合、**当該手順内で即座に停止**し、状況を詳細に報告すること:

1. ファイル・ディレクトリの**期待されたサイズ・行数・内容と実測値の差異**
2. **未追跡ファイルや未コミット変更**の予期せぬ存在
3. **権限エラー**, **ディスク容量不足**, **コマンド未インストール**等のシステムレベル障害
4. **symlink の解決失敗** (broken link、循環参照、target not found)
5. **git config の競合** (既に異なる値が設定されている等)
6. その他、**判断に迷う事象**全般

---

## 手順 1: 事前確認 (Pre-flight Check)

### 目的

Day5 完了状態 (`5825c86`) からの clean な開始を保証し、後続手順の前提が成立していることを確認する。

### 実行コマンド

```bash
# 1.1 プロジェクトルートに移動
cd ~/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver

# 1.2 working tree が clean であることを確認
git status

# 1.3 HEAD が Day5 末の commit (5825c86) であることを確認
git log -1 --format='%h %s'

# 1.4 skill_package/ の構造を確認
ls -la skill_package/

# 1.5 skill_package/ 内 symlink の解決状況を確認
ls -laL skill_package/ 2>&1 | head -20

# 1.6 root の SKILL.md / DEVELOPMENT_NOTES.md がベースライン古版であることを確認
wc -c SKILL.md DEVELOPMENT_NOTES.md

# 1.7 ~/.claude/skills/pubmed-reference-resolver/ の現状を確認 (旧スキル)
ls -la ~/.claude/skills/pubmed-reference-resolver/

# 1.8 旧スキルの SKILL.md 冒頭を記録 (置換前の証拠保全)
head -5 ~/.claude/skills/pubmed-reference-resolver/SKILL.md

# 1.9 /tmp/ バックアップの存在確認
ls -la /tmp/skill_package_backup_20260501/

# 1.10 git config の現状確認 (--global)
git config --global user.name 2>&1 || echo "(unset)"
git config --global user.email 2>&1 || echo "(unset)"
```

### 期待される出力

| 項目 | 期待値 |
|:---|:---|
| 1.2 (`git status`) | `nothing to commit, working tree clean` (`.DS_Store` の untracked は許容) |
| 1.3 (`git log -1`) | `5825c86 feat(skill): add skill_package/ as Claude skill distribution package` |
| 1.4 (`ls skill_package/`) | `SKILL.md`, `DEVELOPMENT_NOTES.md`, 4 symlinks, `references/`, `examples/` |
| 1.6 (`wc -c SKILL.md DEVELOPMENT_NOTES.md`) | `10427 SKILL.md`, `7204 DEVELOPMENT_NOTES.md` |
| 1.7 (`ls ~/.claude/skills/...`) | 旧スキルのファイル一覧 (実体ファイル群) |
| 1.9 (`ls /tmp/...`) | バックアップディレクトリが存在 |
| 1.10 (`git config user.name/email`) | `(unset)` または `katayamahideki@Kata-MacbookAir.local` 等の自動推定値 |

### stop-and-report 条件 (手順 1 固有)

- 1.2 で modified/staged ファイルが検出される (`.DS_Store` 以外)
- 1.3 で HEAD が `5825c86` でない
- 1.4 で skill_package/ 内ファイルが不足している
- 1.6 でサイズが期待値と一致しない (root の古版が誤って書き換えられている)
- 1.7 で `~/.claude/skills/pubmed-reference-resolver/` が存在しない (手順 4 のロジック変更が必要)
- 1.9 で `/tmp/skill_package_backup_20260501/` が存在しない (手順 5 をスキップ可、要確認)

---

## 手順 2: git committer 正規化 (--global)

### 目的

Day5 末で発見された「`user.name` / `user.email` が global 未設定でホスト名から自動推定」という状態を解消し、次手順 (手順 3 = A-1 commit) で正規化された identity が記録されるようにする。

### 実行コマンド

```bash
# 2.1 user.name を設定 (global)
git config --global user.name "Hideki Katayama"

# 2.2 user.email を設定 (global, GitHub 登録メール)
git config --global user.email "hikataya01@gmail.com"

# 2.3 設定値の確認
git config --global user.name
git config --global user.email

# 2.4 (参考) 全 global config の表示
git config --global --list | grep -E '^(user\.|core\.)'
```

### 期待される出力

| 項目 | 期待値 |
|:---|:---|
| 2.3 (`git config user.name`) | `Hideki Katayama` |
| 2.3 (`git config user.email`) | `hikataya01@gmail.com` |

### stop-and-report 条件 (手順 2 固有)

- 2.1 / 2.2 で既に異なる値が設定されている (上書きの可否について先生の判断が必要)

---

## 手順 3: A-1 (root の古版 SKILL.md/DEVELOPMENT_NOTES.md の git rm + commit)

### 目的

skill_package/ に新版が既に格納されている状態で、root に残存する旧版 SKILL.md / DEVELOPMENT_NOTES.md を git history から削除する。これにより「正本は skill_package/ のみ」という単一情報源が確立する。

### 実行コマンド

```bash
# 3.1 プロジェクトルートに居ることを再確認
pwd
# 期待: ~/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver

# 3.2 削除対象ファイルの最終確認 (サイズ)
wc -c SKILL.md DEVELOPMENT_NOTES.md

# 3.3 git rm で削除
git rm SKILL.md DEVELOPMENT_NOTES.md

# 3.4 staged 状態を確認
git status

# 3.5 commit 作成
git commit -m "chore(cleanup): remove deprecated baseline SKILL.md and DEVELOPMENT_NOTES.md

These root-level files are the pre-Day5 baseline versions (10427/7204 bytes)
that were superseded by the new versions placed in skill_package/ during Day5
(commit 5825c86).

After Day5, skill_package/ became the single source of truth for the Claude
skill distribution. The root-level old versions had no consumer and were
preserved only for the symbolic gradual transition planned in Day5 records.

This commit completes that transition by removing them from the working tree
and git history (going forward from this commit). Files remain accessible via
git history (any commit before this one) if needed for reference.

Refs: Day5 record XI-1 (A-1 task), Day6 record (Phase delta)"

# 3.6 新 commit の identity 確認
git log -1 --format='%h %an <%ae> %s'

# 3.7 commit 後の git log を確認 (4 件分)
git log -4 --oneline
```

### 期待される出力

| 項目 | 期待値 |
|:---|:---|
| 3.2 (`wc -c`) | `10427 SKILL.md`, `7204 DEVELOPMENT_NOTES.md` |
| 3.3 (`git rm`) | `rm 'SKILL.md'` `rm 'DEVELOPMENT_NOTES.md'` |
| 3.4 (`git status`) | `Changes to be committed:` 配下に 2 件の `deleted:` |
| 3.5 (`git commit`) | `[main <hash>] chore(cleanup): remove deprecated baseline SKILL.md...` |
| 3.6 (`git log -1`) | `<hash> Hideki Katayama <hikataya01@gmail.com> chore(cleanup): ...` |
| 3.7 (`git log -4`) | 新 commit が最上位、その下に `5825c86`, `c404a05`, `1717963` が続く |

### stop-and-report 条件 (手順 3 固有)

- 3.2 でサイズが期待値と一致しない
- 3.6 で identity が `Hideki Katayama <hikataya01@gmail.com>` と一致しない
- pre-commit hook 等で commit が拒否される

---

## 手順 4: C-1 (~/.claude/skills/pubmed-reference-resolver を skill_package/ への symlink に切替)

### 目的

旧スキル (`~/.claude/skills/pubmed-reference-resolver/`, Phase 0-4 期実装) を `.old.20260502` にバックアップ後、同名で skill_package/ への symlink を作成する。これにより `~/.claude/skills/` 経由でアクセスする全ての操作が、Day1-5 統合実装 (新版) を参照するようになる。

### 実行コマンド

```bash
# 4.1 移動先パスの確認 (絶対パス必須)
SKILL_TARGET="/Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver/skill_package"
echo "Symlink target: $SKILL_TARGET"
ls -la "$SKILL_TARGET" | head -5

# 4.2 旧スキルを .old.20260502 にバックアップ (mv)
cd ~/.claude/skills/
mv pubmed-reference-resolver pubmed-reference-resolver.old.20260502

# 4.3 mv 結果の確認
ls -la pubmed-reference-resolver* 2>&1

# 4.4 symlink の作成
ln -s "$SKILL_TARGET" pubmed-reference-resolver

# 4.5 symlink 作成結果の確認
ls -la pubmed-reference-resolver

# 4.6 二段 symlink 解決の動作確認 (1 段目: skill ディレクトリ symlink)
cd ~/.claude/skills/pubmed-reference-resolver
ls -la

# 4.7 二段 symlink 解決の動作確認 (2 段目: skill_package/ 内の相対 symlink)
ls -laL ~/.claude/skills/pubmed-reference-resolver/main.py

# 4.8 SKILL.md が新版 (13070 bytes) であることを確認
wc -c ~/.claude/skills/pubmed-reference-resolver/SKILL.md

# 4.9 SKILL.md 冒頭の確認 (新版の表題が表示されること)
head -5 ~/.claude/skills/pubmed-reference-resolver/SKILL.md

# 4.10 main.py の冒頭を確認 (二段 symlink 経由でプロジェクト本体が読めること)
head -5 ~/.claude/skills/pubmed-reference-resolver/main.py

# 4.11 manual_overrides.yaml の冒頭を確認 (より深い相対 path 経由)
head -10 ~/.claude/skills/pubmed-reference-resolver/manual_overrides.yaml
```

### 期待される出力

| 項目 | 期待値 |
|:---|:---|
| 4.3 (`ls`) | `pubmed-reference-resolver.old.20260502/` (旧スキルディレクトリ実体) |
| 4.5 (`ls -la pubmed-reference-resolver`) | `lrwxr-xr-x ... pubmed-reference-resolver -> /Users/.../skill_package` |
| 4.6 (`ls -la` after cd) | skill_package/ 内のファイル一覧が表示される (SKILL.md, DEVELOPMENT_NOTES.md, references/, examples/, 4 symlinks) |
| 4.7 (`ls -laL main.py`) | `-rw-r--r-- ... main.py` (実体としてのファイル情報) |
| 4.8 (`wc -c SKILL.md`) | `13070` |
| 4.9 (`head -5 SKILL.md`) | 新版の冒頭 (旧版とは異なる内容) |
| 4.10 (`head -5 main.py`) | プロジェクト本体の main.py 冒頭 (Python コード) |
| 4.11 (`head manual_overrides.yaml`) | YAML 形式の手動補正ルール |

### stop-and-report 条件 (手順 4 固有)

- 4.2 で `mv` が失敗 (権限エラー等)
- 4.4 で `ln -s` が失敗
- 4.5 で symlink が作成されたが target path が想定と異なる
- 4.7 で main.py が「broken symlink」として表示される
- 4.8 で SKILL.md のサイズが 13070 と一致しない
- 4.10 / 4.11 で内容が読めない (二段 symlink 解決の失敗)

### 補足: 失敗時の即時ロールバック

万一 4.4 〜 4.11 のいずれかで問題が発生した場合、その場で以下を実行することで旧スキル状態に復帰可能:

```bash
cd ~/.claude/skills/
rm pubmed-reference-resolver  # broken symlink を削除
mv pubmed-reference-resolver.old.20260502 pubmed-reference-resolver
ls -la pubmed-reference-resolver
```

---

## 手順 5: ε-1 (/tmp/skill_package_backup_20260501/ の削除)

### 目的

Day5 Phase β 手順 β-1 で作成した `/tmp/` バックアップを整理する。手順 4 (C-1) が成功した後に実行することで、ロールバック可能性を確保しつつ最終的な disk クリーンアップを行う。

### 実行コマンド

```bash
# 5.1 削除対象の存在と内容を最終確認
ls -la /tmp/skill_package_backup_20260501/

# 5.2 サイズの確認 (削除前の disk 占有量を記録)
du -sh /tmp/skill_package_backup_20260501/

# 5.3 削除実行
rm -rf /tmp/skill_package_backup_20260501/

# 5.4 削除後の確認
ls /tmp/ | grep skill_package_backup || echo "(no backup directory remaining)"
```

### 期待される出力

| 項目 | 期待値 |
|:---|:---|
| 5.1 (`ls`) | `SKILL.md.new`, `DEVELOPMENT_NOTES.md.new` 等のバックアップファイル一覧 |
| 5.2 (`du -sh`) | サイズ (数十 KB 程度) |
| 5.4 (削除後の `ls`) | `(no backup directory remaining)` |

### stop-and-report 条件 (手順 5 固有)

- 5.1 でディレクトリが既に存在しない (手順 1 で確認済の場合は skip 可)
- 5.3 で `rm` が失敗 (権限エラー等)

---

## 手順 6: 最終確認 (Final Check)

### 目的

全手順完了後、Day6 完了状態が期待通りに達成されていることを包括的に検証する。

### 実行コマンド

```bash
# 6.1 プロジェクトルートに移動
cd ~/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver

# 6.2 git の最終状態
git status
git log -3 --format='%h %an <%ae> %s'

# 6.3 root に SKILL.md / DEVELOPMENT_NOTES.md が存在しないことを確認
ls -la SKILL.md DEVELOPMENT_NOTES.md 2>&1 || echo "(expected: files removed)"

# 6.4 skill_package/ が無傷であることを確認
ls -la skill_package/

# 6.5 ~/.claude/skills/ の最終状態
ls -la ~/.claude/skills/ | grep pubmed

# 6.6 symlink 経由でのアクセス確認 (最終)
wc -c ~/.claude/skills/pubmed-reference-resolver/SKILL.md
head -1 ~/.claude/skills/pubmed-reference-resolver/main.py

# 6.7 git config (--global) の最終確認
git config --global user.name
git config --global user.email

# 6.8 /tmp/ の clean 確認
ls /tmp/ | grep -i skill || echo "(no skill-related backup remaining)"

# 6.9 main branch の commit 数
git rev-list --count main
```

### 期待される最終状態

| 検証項目 | 期待値 | コマンド |
|:---|:---|:---|
| プロジェクト root に古版なし | files removed | 6.3 |
| skill_package/ 無傷 | 全ファイル存在 | 6.4 |
| symlink 切替済 | `pubmed-reference-resolver -> /Users/.../skill_package` | 6.5 |
| バックアップ存在 | `pubmed-reference-resolver.old.20260502/` | 6.5 |
| 新版 SKILL.md 経由アクセス | 13070 bytes | 6.6 |
| 二段 symlink 経由 main.py 読み込み | Python コード冒頭 | 6.6 |
| git committer | `Hideki Katayama` / `hikataya01@gmail.com` | 6.7 |
| /tmp/ clean | バックアップなし | 6.8 |
| main branch commit 数 | 18 | 6.9 |

### 完了報告の様式

最終確認 (手順 6) 完了後、以下の形式で総括報告すること:

```
## Phase δ + ε 完了報告

### 達成項目
- [x] git committer 正規化 (Hideki Katayama / hikataya01@gmail.com)
- [x] root の古版 SKILL.md/DEVELOPMENT_NOTES.md 削除 (commit <hash>)
- [x] ~/.claude/skills/pubmed-reference-resolver の symlink 切替
- [x] /tmp/skill_package_backup_20260501/ の削除
- [x] 全項目最終確認 OK

### main branch 最終形状
- 総 commit 数: 18 (Day5 末 17 から +1)
- 最新 commit: <hash> chore(cleanup): remove deprecated baseline ...

### 残存タスク (Day7 以降)
- 実データ Phase 0 検証
- ライセンス方針決定
- GitHub remote 追加と push
- ~/.claude/skills/pubmed-reference-resolver.old.20260502/ の最終削除 (1-2 週間後)

### 想定外事象
- なし / あり: <内容>

### 所要時間
- 開始: <時刻>
- 終了: <時刻>
- 総所要: <分>
```

---

## トラブルシューティング (FAQ)

### Q1. 手順 4 で symlink target に Japanese 文字 (查読用/查读reference用) が含まれているが大丈夫か?

→ macOS の APFS は Unicode normalization を NFD (分解形式) で行う。`ls -la` で表示される target が NFC (合成形式) と NFD で異なって見える可能性があるが、symlink 解決には影響しない。`head -5 SKILL.md` 等の動作確認が成功すれば問題なし。

### Q2. 手順 4.7 で `ls -laL` が `-l` のみと挙動が違う

→ `-L` オプションは symlink を辿った先の情報を表示するため、symlink 自身ではなく target の情報が出る。これは仕様通りの動作で、二段 symlink 解決の確認に有用。

### Q3. 手順 3 で commit が空 (nothing to commit) になる

→ 手順 1.6 で SKILL.md / DEVELOPMENT_NOTES.md がまだ root に存在することを確認済なので、これが起きる場合は `git rm` の後に `git status` を改めて確認し、staged 状態を検証すること。

### Q4. 手順 4 で `ln -s` が「File exists」エラーを返す

→ 手順 4.2 (`mv`) が成功していないため、旧スキルディレクトリが既に削除/移動されていない可能性。`ls -la ~/.claude/skills/` で現状を確認し、`mv` を再試行すること。

### Q5. 手順 4.10 で main.py が読めない (cat: ... No such file or directory)

→ 二段 symlink 解決の失敗。原因として: (a) skill_package/ 内の symlink 自体が壊れている、(b) target ファイル (`../main.py`) がプロジェクトに存在しない、(c) パス解決エラー。`ls -laL ~/.claude/skills/pubmed-reference-resolver/main.py` で詳細確認後、必要に応じて手順 4 の即時ロールバック手順を実行すること。

---

## 付録: Day5 学びとの対応

本指示書は Day5 で確立された学び P5-P11 を以下のように具体化している:

| 学び | 本指示書での具体化 |
|:---|:---|
| P5 (中間状態の発見と意図確認) | 各手順の stop-and-report 条件を明示 |
| P8 (時間経過によるコンテクスト同期) | 手順 1 で全前提を明示的に再確認 |
| P9 (整理工程の中間状態の文書化) | 手順報告様式を統一 |
| P10 (二段階指示書アプローチ) | 手順 1 (調査) と手順 2-5 (実装) の明確な分離 |
| P11 (バックアップによる真正性検証) | 手順 4 で旧スキルを `.old.20260502` に保全してから symlink 切替 |

---

**作成日**: 2026/05/02
**作成者**: Claude Opus 4.7
**ファイル名**: `PHASE_DELTA_INSTRUCTIONS.md`
**対応概念解説書**: `MIGRATION_INSTRUCTIONS_v2.md` (同梱)
**ステータス**: Claude Code への投入準備完了
**完了後の予定**: 先生 → Claude Opus へ完了報告 → Day6 記録 (`pubmed-reference-resolver-integration-chat-day6.md`) の作成
