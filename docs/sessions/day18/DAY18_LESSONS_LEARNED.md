# Day18 LESSONS LEARNED

**Day18 セッション (2026-05-18)**: GitHub Private repository 追加 + push (Day7 §9.3 long-term task 残 6 件目を完了) + 副次成果として **gitleaks ベース secret scan protocol** の確立 (Day19+ 公開切替時に流用可能)

---

## 1. セッション概要

### 1.1 背景

Day17 末時点で Day7 §9.3 long-term task の残 2 件 (GitHub push、MCP/hook 配線) のうち、ユーザーは Day18 task として **GitHub remote + push** を選択 (Day17 LESSONS §7 パターン 1).

### 1.2 brainstorming 段階 (Q1-Q4 + Approach)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | 公開 vs プライベート | (段階) Private push → Day19+ 公開切替 |
| Q2 | Day18 scope | (充実) remote+push + secret scan + .gitignore + README 更新 |
| Q3 | Repository 名 | `pubmed-reference-resolver` (同一) |
| Q4 | GitHub owner | `hikataya01` (個人アカウント、**Phase 3 で `hikataya01-netizen` に修正**) |
| Approach | 全体戦略 | (A) gitleaks + gh CLI + 実質的 README 更新 |

### 1.3 SPEC (commit `7d6a50e`)

404 行の SPEC を `docs/sessions/day18/SPEC_github_private_push.md` に archive. 11 章構成 (背景・アーキテクチャ・secret scan protocol・.gitignore 再確認・README 更新詳細・remote setup・commit 計画・完了条件・Out of Scope・工数・参照).

### 1.4 PLAN (commit `f5a44f1`)

1068 行の implementation plan を `docs/sessions/day18/PLAN_github_private_push.md` に archive. Task 1-5 + Verification で構成. fixture work と異なり、Task 4 (GitHub repo 作成 + push) は外部 system 操作で commit を生成しない特殊構造.

---

## 2. 実装段階の経緯 (7 commits + 外部操作)

### Phase 0: gitleaks secret scan (commit `8d8c7e3`)

- Task 1 (controller 直接実行): ユーザーが home dir で gitleaks を試行したが空 scan だったため、controller が repo dir で再実行.
- gitleaks 8.30.1 で **68 commits + 3.86 MB** scan → 1 件 false-positive 検出.
  - 検出: `tests/test_env_loader.py:40` の `NCBI_API_KEY=ncbi-test-67890` (synthetic test fixture、文字列内 `test` 含)
  - 対応: `.gitleaksignore` に fingerprint 追記して suppression、再 scan で 0 findings.
- 手動 grep 5 patterns (Anthropic / NCBI / Private key / Bearer / gmail) → 全 hit は Day18 PLAN ドキュメント自身 (commit `f5a44f1`) の self-reference のみ、実 leak なし.
- `docs/sessions/day18/SECRET_SCAN_REPORT.md` (~150 行) を作成、SAFE TO PUSH 確認.

### Phase 1: .gitignore 修正 (commit `7024fd9`)

- Task 2 (controller 直接実行): `.gitignore` に `.DS_Store` + `**/.DS_Store` 追加.
- Day15-17 で常に untracked として残ってきた macOS Finder metadata を最終 clean up. 追加直後に working tree clean 化.

### Phase 2: README 更新 (commit `7b2b851`)

- Task 3 (controller 直接実行): `README.md` を 5 箇所修正 (badge owner / git clone URL / test count 52→97 / 4 fixture 表 / プロジェクト構成 Day8-17 反映).
- 大規模な structural rewrite は Day19+ 公開切替時に実施.

### Phase 3 pre-fix: GitHub owner 修正 (commit `2b8e864`)

- `gh auth status` で **実際の GitHub username が `hikataya01-netizen` であることが判明** (当初 SPEC §3.2 で確定していた `hikataya01` から修正).
- README.md (badge + clone URL) / SPEC §3.2 + 全 URL/CLI 例 / PLAN 全 URL/CLI 例 + 期待出力 + commit message 例 を一括更新.
- email (`hikataya01@gmail.com`) と grep pattern 中の `hikataya01` substring は変更なし (実 email 参照 + `hikataya01-netizen` も substring match されるため exclusion regex として継続有効).

### Phase 3: GitHub repo 作成 + push + CI 確認 (commit なし)

- Task 4 (controller 直接実行、外部操作):
  - `gh` CLI インストール (`brew install gh`、2.92.0)
  - `gh auth login` (ユーザー操作、OAuth browser flow)
  - `gh repo create hikataya01-netizen/pubmed-reference-resolver --private --source=. --remote origin` で 1 コマンド作成 + remote 配線
  - SSH push 試行 → host key verification (`ssh-keyscan` で解決) → SSH passphrase 問題 → **HTTPS + gh token に切替**
  - 初回 push → `.github/workflows/tests.yml` で `workflow` scope 不足、`gh auth refresh -s workflow` (ユーザー操作) で解決
  - 再 push → `[new branch] main -> main` 成功
  - GitHub Actions が trigger され、tests workflow が **success** (23 秒) を確認

### Phase 4: Day18 archive (本 commit)

- Task 5 (controller 直接実行): README + LESSONS を archive.

---

## 3. 設計判断と検証

### 3.1 Phased 戦略 (Private → 公開切替) の根拠

公開判断は不可逆性が高い (一度 public にすると過去の commit が search engine にキャッシュされる). 以下を Day18 で前倒し:
- secret scan で履歴の clean さを確認 (`SECRET_SCAN_REPORT.md` evidence)
- `.gitignore` を最終化
- README を実情に合わせて更新

これらを Day18 で完了させることで、Day19+ の公開切替時は **LICENSE 追加 + visibility 変更 + 公開向け README polish** のみで済む状態に持って行ける.

### 3.2 secret scan protocol の選定根拠

gitleaks + 手動 grep の二重チェック:
- gitleaks: 100+ rule の自動 detect (industry standard)
- 手動 grep: false negative リスク低減 (Anthropic / NCBI / Bearer / gmail パターンを念のため確認)

trufflehog 等の代替 tool は今回未使用 (時間効率と false positive 抑制で gitleaks 単独で十分と判断). `.gitleaksignore` で false positive (synthetic test fixture) を documented suppression する pattern を確立.

### 3.3 commit 戦略 (Phase 3 は commit なし)

Phase 3 (GitHub repo 作成 + push) は外部 system 操作で git commit を生成しない. このため commit 計画は 7 commits (SPEC + PLAN + Phase 0/1/2/Phase 3 pre-fix/Phase 4) で完結. Day16-17 と異なる pattern.

### 3.4 HTTPS + gh token への fallback 判断

当初 SSH を想定したが、ユーザーの SSH 鍵に passphrase が設定されており非対話実行が困難. `gh auth setup-git` で HTTPS + token に切替で push 成功. SSH 設定は将来の cleanup task として残存 (Day19+).

---

## 4. 実機検証結果

### 4.1 gitleaks scan 結果

| Metric | 値 |
|:---|---:|
| gitleaks version | 8.30.1 |
| Scan commits | 68 (1 回目) / 70 (再 scan 時の HEAD) |
| Bytes scanned | 3.86 MB |
| Findings (`.gitleaksignore` 前) | 1 (synthetic test fixture) |
| Findings (`.gitleaksignore` 後) | **0** ✅ |
| 手動 grep patterns | 5 (Anthropic / NCBI / Private key / Bearer / gmail) |
| 手動 grep findings | 0 (PLAN self-reference + email + grep regex のみ) |

### 4.2 GitHub repo 状態

| 項目 | 値 |
|:---|:---|
| Owner | hikataya01-netizen |
| Repo name | pubmed-reference-resolver |
| Visibility | **PRIVATE** |
| Default branch | main |
| Pushed commits | 75 (Day18 archive 含む) |
| Remote URL (local) | https://github.com/hikataya01-netizen/pubmed-reference-resolver.git (HTTPS + gh token) |

### 4.3 CI 動作確認

| 項目 | 結果 |
|:---|:---|
| Workflow trigger | push (auto) |
| Workflow name | tests |
| Run conclusion | **success** ✅ |
| Run duration | 23 秒 |
| Python 3.11 tests | 97 passed, 1 skipped (期待値どおり) |
| Python 3.12 tests | 同上 |
| Python 3.14 tests | (継続実験枠、continue-on-error) |
| README badge | green (tests: passing) — Private repo のため認証済みブラウザで表示 |

---

## 5. 教訓 (D18-1〜D18-3)

### 5.1 D18-1: gitleaks 実行は repo dir で

**事象**: ユーザーが `~` (home dir) で `gitleaks detect --source .` を実行したため、`.git` が見つからず 0 commits scan で「no leaks found」と誤って成功表示された (実際は scan されていない).

**学び**: gitleaks 等の git 履歴 scan tool は **対象 repo dir 内で実行する必要がある**. `--source` 引数は対象ディレクトリを指定するが、git history scan はその dir の `.git` を参照する.

**適用範囲**: 将来 Day19+ の公開切替時、CI / pre-commit hook で gitleaks を integration する場合は同じ落とし穴 (path 指定漏れ) に注意.

### 5.2 D18-2: GitHub username の事前未確認リスク

**事象**: SPEC §3.2 で `hikataya01` を「個人アカウント」として確定したが、Phase 3 で `gh auth status` を実行したところ実際の username が `hikataya01-netizen` であることが判明 (`hikataya01` が既に他者に取得されていたため `-netizen` suffix が必要だった). 結果として README + SPEC + PLAN の URL/CLI 例を一括修正する追加 commit (`2b8e864`) が発生.

**学び**: GitHub URL を含む SPEC を書く前に、**ユーザーの実際の GitHub username を `gh auth status` または `gh api user` で必ず確認**する. メールアドレス (`hikataya01@gmail.com`) の local part = GitHub username とは限らない.

**適用範囲**: 将来 GitHub 関連 task (Day19+ public 切替、collaborator 追加、別 repo 作成等) では brainstorming Q1 段階で `gh auth status` 確認を必須化.

### 5.3 D18-3: Phased push 戦略の妥当性

**事象**: Day18 は Private push に絞り、公開切替を Day19+ に分離した. これにより:
- secret scan / .gitignore / README 更新を落ち着いて実施できた
- LICENSE 選定や CHANGELOG 整備等の追加判断は Day19+ で別途議論可能
- もし Day18 で問題発生 (実際 username 修正、SSH passphrase 障害、workflow scope 障害が連続発生) しても private 内で完結
- 実際に 3 件の障害が発生したが、いずれも public 切替前に解決でき、search engine への漏出リスクなし

**学び**: 不可逆操作 (公開化、外部 push、destructive git operation) は Phase 分割で安全側に倒すと判断負荷が下がる. 各 Phase で完結する目的を設定することで、中断・延期のオプションを残せる.

**適用範囲**: Day19+ 公開切替も同型の Phase 分割が有効 (e.g., LICENSE 追加 → CHANGELOG 整備 → README polish → visibility 変更 → 公開後 secret scan).

---

## 6. 残存タスク (Day19 以降)

### 6.1 Day7 §9.3 long-term task の達成状況 (Day18 末)

| タスク | 状態 | 残し方 |
|:---|:---:|:---|
| Vancouver golden fixture | ✅ Day11 | — |
| Day9 (Z) 未解決 2 件 MEDLINE 調査 | ✅ Day13 | — |
| Day13 §6 案 A: 3 分類 audit logic | ✅ Day15 | — |
| APA 系 golden fixture | ✅ Day16 | — |
| Cell 系 golden fixture | ✅ Day17 | — |
| GitHub remote + push (Private) | ✅ Day18 (本日) | — |
| **MCP/hook 経由 Stage 3 配線** | ⏳ Day19+ | 設計議論大、複数セッション |

### 6.2 Day18 が生成した新規候補

- [ ] **Public 切替** (LICENSE + visibility + README full restructure + CHANGELOG、推定 ~2h、最高優先度)
- [ ] **SSH 認証 cleanup** (SSH 鍵 passphrase 設定見直し or gh CLI 経由認証を default 化)
- [ ] **pre-commit hook での gitleaks 自動実行** (将来 ops 強化)
- [ ] **Branch protection rule 設定** (main への直接 push 禁止、collaborator 追加時)
- [ ] **Issue template / PR template 配置** (公開後の collaboration 受け入れ準備)
- [ ] **AI 工学 book/web refs 三分類改修** (Day17 D17 教訓由来)

### 6.3 Day19+ 推奨着手順

1. **Public 切替** (Day18 で前倒し済み、最も低コスト、~2h、最高優先度)
2. **AI 工学 book/web refs 三分類改修** (Day17 D17 起源、~2h)
3. **MCP/hook 経由 Stage 3 配線** (設計議論大、複数セッション)

---

## 7. 次セッション再開時のプロンプトテンプレート

### パターン 1: Day19 として Public 切替 (推奨)

```
Day19 として、Day18 で Private push した pubmed-reference-resolver を
GitHub Public に切り替えます. Day18 SECRET_SCAN_REPORT.md を再点検し、
LICENSE (MIT 推奨) を追加、README full restructure、CHANGELOG.md を
Day8-18 で整理、最後に gh repo edit --visibility public で公開. ~2h.
```

### パターン 2: Day19 として AI 工学 book/web refs 三分類改修

```
Day19 として、Day17 cell_45refs で発生した三分類 A 多発 (14/15) の
false positive 問題を改修します. AI 工学領域の book chapter / web page
/ industry report 系 references を「真の捏造 (A)」ではなく「MEDLINE
非収録 (B)」に振り直す logic を crossref_check / three_class_classifier
に追加. brainstorming → SPEC → TDD で進めてください.
```

### パターン 3: Day19 として MCP/hook 経由 Stage 3 配線 (大型)

```
Day19 として、Stage 3 (Claude UI 起動の自動配線) を実装します.
MCP server / hook 経由で Claude Code → ローカル command → docx 入力 →
audit 出力 → Claude UI への結果返却パイプラインを設計. 議論大規模の
ため SPEC 段階まで複数セッション覚悟.
```

---

**記録完了日**: 2026-05-18 (Day18)
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day18 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day18.md` (Claude Opus 作成予定)
**ステータス**: Day18 archive 完成、Day19 着手準備完了 (3 パターンプロンプトあり)
