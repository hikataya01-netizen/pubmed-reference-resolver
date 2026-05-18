# SPEC: GitHub Private repository 追加 + push (Day18)

**作成日**: 2026/05/18 (Day18 brainstorming 完了時)
**著者**: Claude Code (Sonnet 4.6) / 承認: 片山英樹
**位置付け**: Day7 §9.3 long-term task 残 2 件のうち 1 件目 (GitHub remote 追加と push) を **Phased 戦略の Phase 1 (Private push)** として完了. 公開切替は Day19+ で実施
**前提**: Day17 末 (commit `f6b874a`) で main branch 68 commits、4 fixture (mdpi/vancouver/apa/cell)、97 tests passed、working tree clean

---

## 1. 背景と目的

### 1.1 残存タスクの位置付け

`docs/sessions/day17/DAY17_LESSONS_LEARNED.md` §6.1 で整理された Day7 §9.3 long-term task 残:

| タスク | 状態 (Day17 末) |
|:---|:---:|
| Vancouver golden fixture | ✅ Day11 |
| Day9 (Z) 未解決 2 件 MEDLINE 調査 | ✅ Day13 |
| Day13 §6 案 A: 3 分類 audit logic | ✅ Day15 |
| APA 系 golden fixture | ✅ Day16 |
| Cell 系 golden fixture | ✅ Day17 |
| **GitHub remote 追加と push** | ⏳ **Day18** (本 SPEC、Phase 1 Private only) |
| MCP/hook 経由 Stage 3 配線 | ⏳ Day19+ |

Day18 では scope を **Private push に絞り** (公開切替は Day19+)、secret scan + .gitignore 再確認 + README 更新 + remote 設定 + push を完了する.

### 1.2 目的

1. **バックアップ確立**: ローカルのみで 68 commits 蓄積した状態を GitHub に退避し、HDD 故障等への耐性を獲得する
2. **CI 配線**: 既存 `.github/workflows/tests.yml` を GitHub Actions で自動実行可能にし、Python 3.11/3.12 環境での test pass を継続検証する
3. **公開準備**: Day19+ で public visibility に切り替える際に必要な事前作業 (secret scan / .gitignore 完備 / README 現状反映) を済ませる
4. **Day7 §9.3 残タスクの 6/7 達成**: long-term task の進捗を 5/7 → 6/7 に進める

### 1.3 設計判断の経緯 (brainstorming 質問)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | 公開 vs プライベート | **(段階) まず Private で push、後で公開切替** |
| Q2 | Day18 scope | **(充実) remote+push + secret scan + .gitignore + README 更新** |
| Q3 | Repository 名 | **`pubmed-reference-resolver` (同一)** |
| Q4 | GitHub owner | **`hikataya01-netizen` (個人アカウント、Phase 3 で `gh auth status` により判明、`hikataya01` から修正)** |
| Approach | 全体戦略 | **(A) gitleaks + gh CLI + 実質的 README 更新** |

---

## 2. Architecture & ファイル配置

### 改変対象 (3 ファイル)

| ファイル | 変更内容 |
|:---|:---|
| `.gitignore` | `.DS_Store` 等の追加 (2 行追加) |
| `README.md` | バッジ owner 置換 / test count 52→97 / 4 fixture 表追加 / プロジェクト構成更新 (5 箇所修正) |
| `CHANGELOG.md` | 内容確認のみ (修正なし、大幅更新は公開切替時) |

### 新規作成 (5 ファイル)

| ファイル | 用途 |
|:---|:---|
| `docs/sessions/day18/SPEC_github_private_push.md` | 本 SPEC、brainstorming 確定後 commit |
| `docs/sessions/day18/PLAN_github_private_push.md` | writing-plans skill 出力の実装計画 |
| `docs/sessions/day18/SECRET_SCAN_REPORT.md` | gitleaks scan 結果記録 (clean evidence、Day19+ 公開切替時の参考) |
| `docs/sessions/day18/README.md` | day18 セッション index |
| `docs/sessions/day18/DAY18_LESSONS_LEARNED.md` | Day18 末 archive |

### 改変なし (確認のみ)

- production code (`main.py`, `mdpi_parser.py`, `crossref_check.py`, `nlm_catalog_check.py`, `three_class_classifier.py`, `journal_audit.py`)
- 全 test ファイル (97 passed 維持)
- 全 fixture ファイル
- `.github/workflows/tests.yml` (既存 CI workflow、Private repo でも動作する)

### 外部システム変更

- GitHub 上に `hikataya01-netizen/pubmed-reference-resolver` (**Private**) を新規作成
- local repo に `origin` remote (SSH URL) を設定
- 全 68 commits + Day18 で追加される 4-6 commits を `git push -u origin main`

---

## 3. Secret scan protocol

### 3.1 Tool 選定

**gitleaks** (industry standard) を採択. 理由:
- 100+ rule の組込 (AWS / GCP / Anthropic / Stripe / private key / DB connection 等)
- Go binary、`brew install gitleaks` で即利用可
- false positive 抑制 logic が trufflehog より洗練
- JSON report 出力で機械可読

### 3.2 実行手順 (Phase 0 で実施)

#### Step 1: gitleaks インストール
```bash
brew install gitleaks
gitleaks version  # 期待: 8.x 以降
```

#### Step 2: Full git history scan
```bash
gitleaks detect --source . --verbose \
  --report-format json \
  --report-path /tmp/gitleaks_report.json
```

- `detect`: working tree + git history (全 68 commits) を scan
- 結果は `/tmp/gitleaks_report.json` に出力 (空 array `[]` = clean)

#### Step 3: 手動 grep 補完 (false negative リスク低減)
```bash
git log --all -p -S "ANTHROPIC_API_KEY=sk-" 2>&1 | head -5
git log --all -p -S "NCBI_API_KEY=" 2>&1 | head -5
git log --all -p -S "PRIVATE KEY" 2>&1 | head -5
git log --all -p -S "Bearer " 2>&1 | head -5
git log --all -p -S "@gmail.com" 2>&1 | grep -v "Co-Authored\|hikataya01" | head -5
```

すべて空 (または Co-Authored-By / 本人 email のみ) であることを確認.

#### Step 4: 結果記録

`docs/sessions/day18/SECRET_SCAN_REPORT.md` に以下を記録:
- 実行日時 + gitleaks version
- scan 範囲 (commit hash range: `aee0ae2`..最新)
- gitleaks finding count (0 期待、>0 なら詳細リスト)
- 手動 grep 5 patterns 結果
- 結論: **SAFE TO PUSH** (or 修正必要)

### 3.3 想定リスクと対応

| リスク | 検出時の対応 |
|:---|:---|
| gitleaks が API key 検出 | **push 中止**、git history rewrite (`git filter-repo` 等)、再 scan 後 push |
| 手動 grep で想定外パターン検出 | 同上、手動精査 |
| Co-Authored-By 表記内に email 含有 (Claude Opus 4.7 等) | 想定内 (`noreply@anthropic.com`)、許容 |
| 本人 email (`hikataya01@gmail.com`) が commit author に含まれる | 想定内 (`git config user.email`)、許容 |

### 3.4 Out of Scope

- Day19+ 公開切替時の追加 scan (将来 task)
- pre-commit hook での自動 scan 配線 (将来 ops 強化 task)

---

## 4. .gitignore 再確認

### 4.1 現状 (Day17 末)

```
.env / .env.local / .env.*.local      # API keys
out/ / out_*/ / *.skill                # Outputs
__pycache__/ / *.pyc / .pytest_cache/  # Python
.cache/                                 # PMC XML cache (Day16-17)
*.save                                  # Editor backups
```

### 4.2 追加 (Day18 で)

```diff
+ # macOS Finder metadata
+ .DS_Store
+ **/.DS_Store
```

`.DS_Store` は Day15-17 で常に untracked として残ってきた macOS Finder のメタデータ. push に含めても無害だが、CI noise 削減と将来公開時のクリーン化のため `.gitignore` に追加.

### 4.3 妥当性確認

他の追加候補 (`.idea/`, `.vscode/`, `*.bak`, `Thumbs.db` 等) は現状 untracked にも検出されていないため Day18 では追加しない. 必要発生時に対応.

---

## 5. README.md 更新

### 5.1 修正 5 箇所

#### (a) Line 1-9: CI badge owner 置換 + コメント削除

```diff
- <!--
-   NOTE: The CI badge URL below contains a <owner> placeholder.
-   When this repository is pushed to GitHub, replace <owner> with the
-   actual GitHub account / org name so the badge resolves.
- -->
-
  # pubmed-reference-resolver

- [![tests](https://github.com/<owner>/pubmed-reference-resolver/actions/workflows/tests.yml/badge.svg)](https://github.com/<owner>/pubmed-reference-resolver/actions/workflows/tests.yml)
+ [![tests](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml/badge.svg)](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml)
```

#### (b) Line 27-32: git clone URL 明示

```diff
  ```bash
- git clone <repository-url>
+ git clone git@github.com:hikataya01-netizen/pubmed-reference-resolver.git
  cd pubmed-reference-resolver
  pip install -r requirements.txt
  ```
```

#### (c) Line 60-66: テスト数 + skipped 設計の現状反映

```diff
  ```bash
  python -m pytest tests/ -q
  ```

- 現状 **52 passed + 1 skipped**。skipped 分は LLM path のシナリオで、`ANTHROPIC_API_KEY`
- 未設定時にスキップされる設計。
+ 現状 **97 passed + 1 skipped** (Day17 末)。
+ skipped 分は LLM path のシナリオで、`ANTHROPIC_API_KEY` 未設定時にスキップされる設計。
```

#### (d) Line 68-80: golden fixture section を 4 系統に拡張

```diff
- ## 149 件ゴールドスタンダード
-
- `tests/fixtures/mdpi_149refs/` に MDPI 形式 149 件参照のゴールドスタンダードを配備している。
+ ## ゴールドスタンダード fixture (4 系統)
+
+ `tests/fixtures/` に 4 系統の golden fixture を配備:
+
+ | Fixture | 件数 | スタイル | 由来 | 解決率 |
+ |:---|---:|:---|:---|---:|
+ | `mdpi_149refs/` | 149 | MDPI | OneDrive 実機 (Day1-7) | 全件 fast-path |
+ | `vancouver_24refs/` | 24 | Vancouver/AMA | OneDrive 実機 (Day9) | 22/24 = 91.7% |
+ | `apa_45refs/` | 45 | APA 7 | PMC OA 3 論文 (Day16) | 25/45 = 55.6% |
+ | `cell_45refs/` | 45 | Cell Press | PMC OA 3 iScience (Day17) | 30/45 = 66.7% |
+
+ Vancouver/APA/Cell は Day9 で導入された **Vancouver Veto** (`is_mdpi_style()` の `\((?:19|20)\d{2}[a-z]?\)` regex) により LLM path に強制 routing される. Day11 で確立された **`expected_*` (deterministic) / `baseline_*` (document-of-record)** ハイブリッド命名規約を踏襲.
```

#### (e) Line 82-110: プロジェクト構成更新 (Day8-17 で追加されたファイル群を反映)

production code 追加 (Day15 の 3 modules):
- `crossref_check.py`, `nlm_catalog_check.py`, `three_class_classifier.py`

tool 追加 (Day16-17):
- `tools/build_apa_fixture.py`, `tools/build_cell_fixture.py`

test 追加 (Day11/15/16/17):
- `test_integration_vancouver_24refs.py`, `test_integration_apa_45refs.py`, `test_integration_cell_45refs.py`
- `test_crossref_check.py`, `test_nlm_catalog_check.py`, `test_three_class_classifier.py`

fixture 追加 (Day11/15/16/17):
- `vancouver_24refs/`, `apa_45refs/`, `cell_45refs/`, `three_class_classification/`

docs 追加 (Day6+):
- `docs/sessions/dayN/` (Day6-18)
- `docs/operations/SETUP_API_KEYS.md` (Day12)
- `docs/templates/`

### 5.2 維持対象 (修正なし)

- 主な機能 (15-25) — 内容は Day7 時点でも今も正確
- 使用方法 (36-58) — 出力ファイル名等正確
- 主要な機能列挙、`--overrides` 説明など

---

## 6. Remote setup + push protocol

### 6.1 実行手順 (Phase 3 で実施)

#### Step 1: GitHub CLI 確認
```bash
gh --version
gh auth status
```

- 未インストール: `brew install gh`
- 未認証: `gh auth login` (browser 経由)

#### Step 2: Private repository 作成
```bash
gh repo create hikataya01-netizen/pubmed-reference-resolver \
  --private \
  --source=. \
  --description "PubMed reference resolver / 査読支援スキル (References → PubMed 逆引き + 統合監査レポート)" \
  --remote origin
```

#### Step 3: Remote URL 確認 + SSH 設定
```bash
git remote -v
# 期待: origin  git@github.com:hikataya01-netizen/pubmed-reference-resolver.git
```

HTTPS で設定された場合:
```bash
git remote set-url origin git@github.com:hikataya01-netizen/pubmed-reference-resolver.git
```

#### Step 4: Push main branch
```bash
git push -u origin main
```

#### Step 5: GitHub Actions 動作確認
```bash
gh run list --limit 3
gh run watch <run-id>
```

`.github/workflows/tests.yml` が Python 3.11/3.12 で 97 tests 全 pass することを確認.

#### Step 6: README badge 動作確認
```bash
gh repo view --web
```

ブラウザで README test バッジが green (`tests: passing`) であることを確認.

### 6.2 想定リスクと対応

| リスク | 確率 | 対応 |
|:---|:---:|:---|
| gitleaks で API key 検出 | 低 | push 中止、`git filter-repo` で history rewrite、再 scan |
| GitHub Actions CI failure | 低 | local で確認済の 97 passed が CI で異なる場合は環境差調査、修正 commit |
| SSH 認証失敗 | 中 | `gh auth status` 確認、再 login、もしくは HTTPS + PAT に変更 |
| Remote URL 既存 | 低 | `git remote remove origin` 後に再設定 |
| `gh repo create` 同名 repo 検出失敗 | 低 | `gh repo view` で確認、別名検討 (ユーザー再承認) |

---

## 7. Commit 計画 (6 commits)

| 順 | commit 種別 | Phase | 内容 |
|:---:|:---|:---:|:---|
| (前) | `docs(spec)` | — | Day18 SPEC archive (本 commit) |
| (前) | `docs(plan)` | — | Day18 PLAN archive |
| 1 | `chore(gitignore)` | 1 | `.DS_Store` 等の追加 |
| 2 | `docs(readme)` | 2 | README を Day17 末状態に更新 (5 箇所修正) |
| 3 | `docs(security)` | 0 (Phase 0 で実施、commit は Phase 3 前) | SECRET_SCAN_REPORT.md 追加 |
| 4 | `docs(sessions)` | 4 | Day18 archive (README + LESSONS) |

→ 合計 **6 commits** (SPEC + PLAN + 4 phase). Day16-17 と同等規模.

注: Phase 3 (remote 作成 + push) は git commit を生成しない (GitHub 上の操作のみ). Phase 0 の SECRET_SCAN_REPORT.md は Phase 3 push 前に commit する必要があるため commit 順序は Pre → 1 → 2 → 3 → 4 → 5.

---

## 8. 完了条件 (12 項目)

| # | 条件 | 確認方法 |
|:---:|:---|:---|
| 1 | gitleaks installed + Day18 で実行済 | `gitleaks version`、SECRET_SCAN_REPORT.md 存在 |
| 2 | gitleaks scan 結果 clean (0 findings) | `jq 'length == 0' /tmp/gitleaks_report.json` |
| 3 | 手動 grep 5 patterns clean | SECRET_SCAN_REPORT.md に結果記録 |
| 4 | `.gitignore` に `.DS_Store` 追加 | `grep '.DS_Store' .gitignore` |
| 5 | README badge owner 置換済 | `! grep '<owner>' README.md` (空) |
| 6 | README test count 97 反映 | `grep '97 passed' README.md` |
| 7 | README fixture table 4 行 | `grep -c 'mdpi_149refs\|vancouver_24refs\|apa_45refs\|cell_45refs' README.md` ≥ 4 |
| 8 | GitHub repo 作成済 (Private) | `gh repo view hikataya01-netizen/pubmed-reference-resolver --json visibility \| jq '.visibility'` = "PRIVATE" |
| 9 | local origin remote 設定済 (SSH) | `git remote -v` で `git@github.com:hikataya01-netizen/...` |
| 10 | main branch push 成功 | `git push -u origin main` 終了 + `git status` clean |
| 11 | GitHub Actions 1 回以上成功 | `gh run list --limit 1 \| grep success` |
| 12 | Day18 archive (5 files) commit + push | `ls docs/sessions/day18/`, all 5 files exist + pushed |

---

## 9. Out of Scope (Day19+ 候補)

- **LICENSE 追加** (公開切替時に MIT 等選定)
- **CHANGELOG.md 大幅更新** (release 時)
- **README full restructure** (badges、TOC、図解、公開切替時)
- **branch protection rule 設定** (collaborator 追加時)
- **pre-commit hook 自動 secret scan** (将来 ops 強化)
- **Day19+ 公開切替**: visibility public + LICENSE + 公開向け README polish + CHANGELOG 反映

---

## 10. 工数見積もり

| Phase | 内容 | 見積 |
|:---:|:---|---:|
| Pre | SPEC + PLAN archive | 25min |
| Phase 0 | gitleaks インストール + secret scan + SECRET_SCAN_REPORT 作成 + commit | 30min |
| Phase 1 | .gitignore 修正 + commit | 5min |
| Phase 2 | README 5 箇所修正 + commit | 30min |
| Phase 3 | GitHub repo 作成 + remote 設定 + push + CI 確認 | 30min |
| Phase 4 | Day18 archive 作成 (README + LESSONS) + 最終 commit + push | 20min |
| **合計** | | **~2.5h** |

Approach A 見積 (2-3h) と整合.

---

## 11. 参照

- Day7 §9.3 long-term task (Phase 0 検証で発見): `docs/sessions/day7/PHASE_0_VERIFICATION_REPORT.md`
- Day17 LESSONS (Day18+ プロンプトテンプレート): `docs/sessions/day17/DAY17_LESSONS_LEARNED.md` §7 パターン 1
- 既存 README: `README.md` (Day7 era、更新対象)
- 既存 .gitignore: `.gitignore` (Day1+ から漸進的に拡充、Day18 で `.DS_Store` 追加)
- 既存 CI workflow: `.github/workflows/tests.yml` (Python 3.11/3.12/3.14 で test 実行)

---

**承認**: 片山英樹 (brainstorming Q1-Q4 + Approach + design 全 4 sections)
**次工程**: writing-plans skill で implementation plan を作成
