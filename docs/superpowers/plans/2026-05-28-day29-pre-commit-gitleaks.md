# Day29 pre-commit gitleaks 導入 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Day23 の機密データ commit 事故の再発防止のため、`.pre-commit-config.yaml` + gitleaks pre-commit hook + CI gitleaks job + CONTRIBUTING.md からなる 3 層防御機構を導入し、git history audit で漏洩 0 件を確認する。

**Architecture:** pre-commit.com framework に gitleaks v8.30.1 hook を declare し、`uv sync --group dev` で pre-commit パッケージを install、`uv run pre-commit install` で `.git/hooks/pre-commit` を配置。CI 側は `gitleaks/gitleaks-action@v2` を独立 job として追加し二重防御。1 atomic security commit で 6 ファイルを同時投入後、history audit を実施。

**Tech Stack:** pre-commit (PyPI >=4.0,<5.0), gitleaks v8.30.1 binary (pre-commit hook が auto-download), gitleaks/gitleaks-action@v2, uv 0.11.x, Python 3.11/3.12/3.14

**Spec:** `docs/superpowers/specs/2026-05-28-day29-pre-commit-gitleaks-design.md`

**起点 commit:** `ddff834` (Day29 spec commit)

**期待 final state:** HEAD = archive commit、115 passed (Day28 と同じ、test 追加なし)、CI 4 jobs (test 3.11 / test 3.12 / test-experimental 3.14 / **gitleaks**) all green、pre-commit hook 動作中、CONTRIBUTING.md 存在、history audit 0 件確認

---

## File Structure

| File | 役割 | Day29 での操作 | Task |
|:---|:---|:---:|:---:|
| `.pre-commit-config.yaml` | gitleaks hook 宣言 | new | Task 2 |
| `pyproject.toml` | dev group に `pre-commit>=4.0,<5.0` 追加 | modify | Task 2 |
| `uv.lock` | uv sync で auto-update | modify (自動) | Task 2 |
| `.gitignore` | `.gitleaks-audit.json` を除外 | modify (末尾 1 行追加) | Task 2 |
| `.github/workflows/tests.yml` | `gitleaks` job 追加 | modify (末尾 job 追加) | Task 2 |
| `CONTRIBUTING.md` | 開発者向け install 手順 | new | Task 2 |
| `docs/superpowers/plans/2026-05-28-day29-pre-commit-gitleaks.md` | この plan 自体 | new | Task 0 |
| `docs/sessions/day29/README.md` | session archive | new | Task 4 |
| `docs/sessions/day29/DAY29_LESSONS_LEARNED.md` | session lessons | new | Task 4 |

**Out of touch:** `main.py`, `tests/`, integration/, 既存 fixture すべて無変更。

---

## バージョン採用根拠

| ツール | 採用版 | 確認方法 / 理由 |
|:---|:---|:---|
| gitleaks | **v8.30.1** | `curl https://api.github.com/repos/gitleaks/gitleaks/releases/latest` で確認。Spec の v8.21.4 は仮置き、最新採用 |
| pre-commit (PyPI) | `>=4.0,<5.0` | major 4.x stable、5.x 未 release |
| gitleaks/gitleaks-action | `@v2` | OSS 利用、`GITLEAKS_LICENSE` 不要、商用 license は不要 |
| actions/checkout | `@v4` | 既存 CI 統一(Node.js 20 deprecation 対応は Day30+ out of scope) |

---

## Commit chain (期待値)

| # | type | summary | 期待 SHA placeholder |
|:---:|:---|:---|:---|
| 1 | docs(spec) | Day29 spec | `ddff834` (確定済) |
| 2 | docs(plan) | Day29 plan | Task 0 で作成 |
| 3 | chore(security) | atomic 6-file security setup | Task 2 で作成 |
| 4 | docs(sessions) | archive Day29 | Task 4 で作成 |

合計 **4 commit**。

Task 3 は「動作検証 + history audit」で **commit を生成しない**(行為のみ)。検証結果は Task 4 の LESSONS で永続化する。

---

## Task 0: Plan を commit

**Files:**
- Create: `docs/superpowers/plans/2026-05-28-day29-pre-commit-gitleaks.md` (この file 自体)

- [ ] **Step 1: plan file が存在することを確認**

Run: `ls docs/superpowers/plans/2026-05-28-day29-pre-commit-gitleaks.md`
Expected: ファイルが存在 (この writing-plans skill が作成済)

- [ ] **Step 2: working tree が clean (spec commit 直後) であることを確認**

Run: `git status`
Expected:
```
On branch main
Untracked files:
  docs/superpowers/plans/2026-05-28-day29-pre-commit-gitleaks.md
```

- [ ] **Step 3: stage + commit**

```bash
git add docs/superpowers/plans/2026-05-28-day29-pre-commit-gitleaks.md
git commit -m "$(cat <<'EOF'
docs(plan): add Day29 pre-commit gitleaks introduction plan

Day23 機密データ事故再発防止のための 3 層防御 (Local pre-commit hook
+ CI gitleaks job + one-shot history audit) を bite-sized task に分解。

主要構成:
- Task 0: plan commit (この commit)
- Task 1: 事前確認 (uv pre-commit available, gitleaks version 確認)
- Task 2: atomic 6-file security setup commit
  (.pre-commit-config.yaml, pyproject.toml, uv.lock, .gitignore,
  .github/workflows/tests.yml, CONTRIBUTING.md)
- Task 3: 動作検証 + history audit (commit 生成なし)
- Task 4: archive (README + LESSONS) + push + CI 確認

採用バージョン: gitleaks v8.30.1, pre-commit >=4.0,<5.0,
gitleaks-action@v2

期待 final: 115 passed (test 追加なし)、CI 4 jobs、pre-commit hook
動作中、history audit 0 件。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: commit 成功確認**

Run: `git log --oneline -1`
Expected: `<SHA> docs(plan): add Day29 pre-commit gitleaks introduction plan`

---

## Task 1: 事前確認 (uv + pre-commit + gitleaks 環境)

**Files:** なし(read-only)

**目的:** 実装前に「uv が動作する」「pre-commit パッケージが PyPI に存在する」「gitleaks v8.30.1 tag が存在する」を確認し、後続 Task の前提条件を担保する。

- [ ] **Step 1: uv version 確認**

Run: `uv --version`
Expected: `uv 0.11.x` (Day27 で migration 済)

- [ ] **Step 2: 現状の dev group 内容確認**

Run: `grep -A 5 'dependency-groups' pyproject.toml`
Expected: `dev = [ "pytest>=9.0,<10.0", ]` (pre-commit 未追加)

- [ ] **Step 3: pre-commit パッケージが PyPI に存在することを確認**

Run: `uv pip index versions pre-commit 2>&1 | head -5`
Expected: `pre-commit` の最新版が >=4.0,<5.0 範囲に含まれる (例: `pre-commit 4.0.1`, `4.1.0` 等)

`uv pip index versions` が動作しない環境では代替コマンド:
```bash
curl -s https://pypi.org/pypi/pre-commit/json | python3 -c "import json,sys; print(json.load(sys.stdin)['info']['version'])"
```
Expected: `4.x.y` の version 文字列

- [ ] **Step 4: gitleaks v8.30.1 tag が GitHub 上に存在することを確認**

Run: `curl -s https://api.github.com/repos/gitleaks/gitleaks/git/refs/tags/v8.30.1 | head -5`
Expected: `"ref": "refs/tags/v8.30.1"` を含む JSON が返る (HTTP 404 ではない)

- [ ] **Step 5: 既存 CI workflow が green であることを確認**

Run: `gh run list --limit 3 --workflow tests`
Expected: 最新 run が `success` (Day28 archive commit `4a0adfd` で確認済)

- [ ] **Step 6: working tree が clean であることを再確認**

Run: `git status`
Expected: `nothing to commit, working tree clean` (Task 0 commit 後の状態)

このタスクで commit は作成しない。確認のみ。すべての Expected が満たされたら Task 2 に進む。

---

## Task 2: Atomic 6-file security setup commit

**Files:**
- Create: `.pre-commit-config.yaml`
- Create: `CONTRIBUTING.md`
- Modify: `pyproject.toml` (dev group に pre-commit 追加)
- Modify: `uv.lock` (uv add の自動 update)
- Modify: `.gitignore` (`.gitleaks-audit.json` 追加)
- Modify: `.github/workflows/tests.yml` (gitleaks job 追加)

**目的:** Day29 の 3 層防御機構 Layer 1 (local pre-commit hook) と Layer 2 (CI gitleaks job) を構成する 6 ファイルを atomic に投入する。partial state では効果不完全なため 1 commit にまとめる。

### Step 1-7: 6 ファイルを順次作成・修正

- [ ] **Step 1: pre-commit を dev group に追加 (uv add)**

```bash
uv add --group dev "pre-commit>=4.0,<5.0"
```

期待動作:
- `pyproject.toml` の `[dependency-groups] dev` に `pre-commit>=4.0,<5.0` が追加される
- `uv.lock` が自動 update される
- `.venv/` に pre-commit + 依存関係が install される

確認:
```bash
grep 'pre-commit' pyproject.toml
```
Expected: `    "pre-commit>=4.0,<5.0",` (dev 配列内)

```bash
uv run pre-commit --version
```
Expected: `pre-commit 4.x.y`

- [ ] **Step 2: `.pre-commit-config.yaml` 作成**

Write tool で `/Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver/.pre-commit-config.yaml` を以下の内容で作成:

```yaml
# Day29 で導入 — Day23 機密データ事故の再発防止を目的とした gitleaks pre-commit hook
# 設計仕様: docs/superpowers/specs/2026-05-28-day29-pre-commit-gitleaks-design.md
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks
```

確認:
```bash
cat .pre-commit-config.yaml
```
Expected: 上記内容が表示される

- [ ] **Step 3: `.gitignore` に `.gitleaks-audit.json` を末尾追加**

Edit tool で `.gitignore` の末尾に以下を追加:

old_string:
```
# uv virtual environment (Day27 で導入)
.venv/
```

new_string:
```
# uv virtual environment (Day27 で導入)
.venv/

# gitleaks history audit report (Day29 で導入、機密 finding を含み得るため commit しない)
.gitleaks-audit.json
```

確認:
```bash
tail -5 .gitignore
```
Expected: `.gitleaks-audit.json` の行が含まれる

- [ ] **Step 4: `.github/workflows/tests.yml` の末尾に gitleaks job 追加**

Edit tool で `.github/workflows/tests.yml` の末尾を変更。

old_string (test-experimental job 末尾の uv run pytest 行):
```
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
      - run: uv sync --frozen --group dev
      - run: uv run pytest tests/ -q
```

new_string (gitleaks job を追加):
```
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
      - run: uv sync --frozen --group dev
      - run: uv run pytest tests/ -q

  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

注: `old_string` は test-experimental job 末尾の **正確な 5 行** であること。Edit ツール実行前に Read で行範囲を確認。

確認:
```bash
tail -15 .github/workflows/tests.yml
```
Expected: `gitleaks:` job ブロックが末尾に存在

- [ ] **Step 5: `CONTRIBUTING.md` 作成**

Write tool で `/Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver/CONTRIBUTING.md` を以下の内容で作成:

```markdown
# Contributing to pubmed-reference-resolver

本プロジェクトへの contribution を歓迎する。本ドキュメントは開発環境の最小
セットアップと開発フローを記述する。

## 開発環境セットアップ

1. **uv install** (Python パッケージマネージャ):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   詳細: https://docs.astral.sh/uv/

2. **依存関係 install** (production + dev):
   ```bash
   uv sync --group dev
   ```

3. **pre-commit hook install** (機密データ commit 予防):
   ```bash
   uv run pre-commit install
   ```
   これで `.git/hooks/pre-commit` が配置され、`git commit` 時に gitleaks が
   自動実行される。

## 開発フロー

1. main branch から feature branch を切る:
   ```bash
   git checkout -b feat/your-feature
   ```

2. 機能変更 → test 追加 → 全 pytest PASS 確認:
   ```bash
   uv run pytest tests/ -v
   ```

3. commit (pre-commit hook が gitleaks scan を自動実行):
   ```bash
   git add <files>
   git commit -m "feat: your feature"
   ```

4. push → CI で再 scan + test 実行:
   ```bash
   git push origin feat/your-feature
   ```

5. CI green を確認してから PR open。

## Commit メッセージ規約

[Conventional Commits](https://www.conventionalcommits.org/) に準拠する:

| prefix | 用途 |
|:---|:---|
| `feat:` | 新機能 |
| `fix:` | バグ修正 |
| `docs:` | ドキュメント変更 |
| `chore:` | ビルド・依存関係・補助ツール変更 |
| `refactor:` | 機能変更を伴わないコード整理 |
| `test:` | テスト追加・修正 |
| `ci:` | CI 設定変更 |
| `build:` | ビルドシステム・パッケージ管理変更 |

例: `feat(parse): add Latin Extended-A author surname support`

## セキュリティ

### 機密情報の取り扱い

以下のファイル・情報は**絶対に commit しない**:

- `.env`, `.env.*`, `.envrc`
- `credentials.json`, `service-account*.json`, `client_secret*.json`
- 秘密鍵 (`*.pem`, `*.key`, `id_rsa`, `id_ed25519`)
- API キー・access token を含むあらゆる設定ファイル
- 患者識別情報を含むファイル(本プロジェクトは公開リポジトリのため特に注意)

### 自動防御

- **Layer 1 (Local)**: pre-commit hook で gitleaks が staged 内容を scan
- **Layer 2 (CI)**: GitHub Actions で push/PR 時に再 scan
- **Layer 3 (Audit)**: 定期的な history audit (Day29 で baseline 0 件確認)

### 漏洩発覚時

万が一機密情報を commit してしまった場合:
1. 即座にメンテナに連絡(GitHub Issue または直接連絡)
2. **公開後の漏洩は git history rewrite + force push が必要**
3. 該当する API キー・credential は即座にローテーション

## 関連ドキュメント

- [プロジェクト README](README.md)
- [Day23 LESSONS](docs/sessions/day23/DAY23_LESSONS_LEARNED.md): 機密データ事故と filter-repo 対応の経緯
- [Day29 LESSONS](docs/sessions/day29/DAY29_LESSONS_LEARNED.md): pre-commit gitleaks 導入の経緯
```

注: `Day29 LESSONS` のリンクは Task 4 で作成する file への先行参照。Task 4 完了時に link が有効化される。

確認:
```bash
ls -l CONTRIBUTING.md
wc -l CONTRIBUTING.md
```
Expected: ファイル存在、約 80 行

- [ ] **Step 6: pre-commit が動作することを確認 (smoke test)**

```bash
uv run pre-commit install
```
Expected: `pre-commit installed at .git/hooks/pre-commit`

```bash
uv run pre-commit run --all-files
```
Expected: gitleaks が全 file を scan し `Passed` で終了。binary download に初回 10-30 秒程度。

万が一 finding が検出された場合:
- finding の詳細を確認
- false positive と判明したら次の Task で対応(`.gitleaks.toml` allowlist 追加など)
- 真の漏洩なら **ここで作業停止**、ユーザー判断を仰ぐ

- [ ] **Step 7: 既存 pytest に regression なし確認**

```bash
uv run pytest tests/ -q
```
Expected: `115 passed in <time>s`、Day28 末と同じ。

- [ ] **Step 8: 6 ファイル atomic commit**

```bash
git add .pre-commit-config.yaml pyproject.toml uv.lock .gitignore .github/workflows/tests.yml CONTRIBUTING.md
git status
```
Expected: 6 ファイルすべて staged、他に modified なし。

```bash
git commit -m "$(cat <<'EOF'
chore(security): introduce gitleaks pre-commit hook + CI job + CONTRIBUTING.md (Day29)

Day23 で発生した機密データ commit 事故 (fixture に peer-review 由来
内容が含まれ filter-repo + force push で対応) の再発防止を目的とした
3 層防御機構を導入。

Layer 1 (Local pre-commit hook):
- .pre-commit-config.yaml で gitleaks v8.30.1 hook を declare
- 開発者は \`uv run pre-commit install\` で .git/hooks/pre-commit 配置
- \`git commit\` 時に staged file を自動 scan
- finding 検出 → commit ブロック

Layer 2 (CI gitleaks job):
- .github/workflows/tests.yml に独立 job 追加
- gitleaks/gitleaks-action@v2 公式 action 採用
- push/PR で history 全体を再 scan
- finding 検出 → CI 失敗 → PR merge ブロック
- ローカル \`--no-verify\` での skip を補完

支援機構:
- pyproject.toml [dependency-groups] dev に pre-commit>=4.0,<5.0 追加
  (CLAUDE.md §8.1 uv 統一原則と整合)
- uv.lock 同期更新
- .gitignore に .gitleaks-audit.json 追加 (機密 finding を含み得る
  history audit report を commit から除外)
- CONTRIBUTING.md で開発者向け install 手順とセキュリティ規約を整備

採用バージョン:
- gitleaks v8.30.1 (公式最新 stable、2026-03-21 release)
- pre-commit >=4.0,<5.0 (PyPI、stable major 4.x)
- gitleaks/gitleaks-action@v2 (OSS 利用、GITLEAKS_LICENSE 不要)

設計判断:
- rule customization なし、gitleaks default rule で開始 (PMID/DOI の
  誤検出なし、false positive 発生時に reactive 対応)
- Day23 学びの永続化: 予防は事後対応より遥かに安価という原則を
  自動化機構で実装

Test results: 115 passed (Day28 と同じ、test 追加なし)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 9: commit 成功確認**

```bash
git log --oneline -2
```
Expected:
```
<SHA> chore(security): introduce gitleaks pre-commit hook + CI job + CONTRIBUTING.md (Day29)
<SHA> docs(plan): add Day29 pre-commit gitleaks introduction plan
```

```bash
git show --stat HEAD
```
Expected: 6 ファイル変更 (`.pre-commit-config.yaml`, `pyproject.toml`, `uv.lock`, `.gitignore`, `.github/workflows/tests.yml`, `CONTRIBUTING.md`)

- [ ] **Step 10: push して CI 確認**

```bash
git push origin main
gh run watch
```
Expected: CI green、**4 jobs all success**:
- test (3.11)
- test (3.12)
- test-experimental (3.14)
- **gitleaks** (新規)

CI run ID と build time を後の Task 4 archive 用にメモする。

---

## Task 3: 動作検証 + history audit (commit 生成なし)

**Files:** なし(verification only)

**目的:** Day29 の 3 層防御が実際に動作することを検証し、Day29 セッション内で history audit を実施して漏洩 0 件を baseline 化する。**このタスクでは commit を作成しない**。検証結果は Task 4 LESSONS で永続化する。

- [ ] **Step 1: pre-commit hook smoke test (ダミー secret で blocking 確認)**

ダミー secret を含む tmp file を作成:
```bash
TMPFILE=$(mktemp /tmp/gitleaks-smoke-XXXXXX.txt)
printf 'aws_access_key_id = AKIAIOSFODNN7EXAMPLE\naws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\n' > "$TMPFILE"
cp "$TMPFILE" smoke_test_secret.txt
git add smoke_test_secret.txt
```

commit を試行 → ブロックされるべき:
```bash
git commit -m "test: should be blocked by gitleaks"
```
Expected: commit が失敗、gitleaks の finding 出力が表示される。Exit code 非ゼロ。

クリーンアップ:
```bash
git restore --staged smoke_test_secret.txt
rm smoke_test_secret.txt "$TMPFILE"
git status
```
Expected: working tree clean。

注: AKIAIOSFODNN7EXAMPLE は AWS が公式 documentation で使用するダミー key で、gitleaks default rule が必ず detect する典型 pattern。

- [ ] **Step 2: 通常 commit が pass することを確認 (false positive 検査)**

このプロジェクトの非機密 file (例: `README.md`) を末尾に空行 1 つ追加して commit を試行する:

```bash
# README.md 末尾に空行追加 (実害なし)
printf '\n' >> README.md
git add README.md
git commit -m "test: should pass gitleaks (will be reverted)"
```
Expected: commit 成功、gitleaks scan が pass。

直ちに revert:
```bash
git reset --soft HEAD~1
git restore --staged README.md
git checkout -- README.md
git status
```
Expected: working tree clean、HEAD は Task 2 の commit。

注: `git reset --soft HEAD~1` は HEAD を 1 つ戻し、変更内容を staged に保持 (file は touch せず)。`git restore --staged` で stage 解除、`git checkout --` で working tree も revert。これは **破壊的操作ではない** (push 前の local-only reset、CLAUDE.md §7.2.2 範囲外)。

- [ ] **Step 3: history audit (詳細 JSON report 出力)**

```bash
# pre-commit framework が install した gitleaks binary を使って history 全体 scan
# pre-commit run gitleaks --all-files は staged file のみ scan するため、
# history scan には gitleaks CLI を直接呼ぶ
which gitleaks || echo "gitleaks binary not found in PATH"
```

binary が見つからない場合、pre-commit framework の cache から explicit に検索:
```bash
ls ~/.cache/pre-commit/repo*/bin/gitleaks 2>/dev/null | head -1
```
あるいは `uv run pre-commit run --all-files` の log から binary path を推定。

代替案として、Docker 経由で gitleaks を実行することもできるが、本 plan では「ローカルに gitleaks binary を見つけたら使う、見つからなければ手動 install して使う」方針:

```bash
# Homebrew がある場合
brew install gitleaks 2>/dev/null || true

# 確認
gitleaks version
```
Expected: `v8.30.1` または近い stable 版

history scan 実行:
```bash
gitleaks detect --log-opts="--all" --source . \
  --report-format json --report-path .gitleaks-audit.json --no-banner
```
Expected: 標準出力に scan log、`.gitleaks-audit.json` が生成される。exit code 0 (finding なし) または 1 (finding あり)。

- [ ] **Step 4: audit 結果確認**

```bash
ls -lh .gitleaks-audit.json
```
Expected: ファイル存在。サイズは数 KB 〜 数十 KB。

```bash
# finding の件数を確認 (JSON の配列長)
python3 -c "import json; print(len(json.load(open('.gitleaks-audit.json'))))"
```
Expected: **`0`**

もし `> 0` の場合:
- **作業停止**
- finding の詳細を `.gitleaks-audit.json` から確認 (commit しない)
- ユーザー判断を仰ぐ
- false positive なら `.gitleaks.toml` に allowlist を追加して別 commit
- 真の漏洩なら filter-repo 等の対応を別途検討 (CLAUDE.md §7.2.2 例外承認が必要)

- [ ] **Step 5: audit report が gitignore で除外されていることを確認**

```bash
git status
```
Expected: `.gitleaks-audit.json` は **Untracked にも Changes にも表示されない** (`.gitignore` で除外済)。

確認:
```bash
git check-ignore -v .gitleaks-audit.json
```
Expected: `.gitignore:<line>:.gitleaks-audit.json    .gitleaks-audit.json`

- [ ] **Step 6: 最終 working tree 状態確認**

```bash
git status
git log --oneline -3
uv run pytest tests/ 2>&1 | tail -3
```
Expected:
- `nothing to commit, working tree clean`
- HEAD は Task 2 commit
- `115 passed`

このタスクで取得する情報を Task 4 用にメモ:
- gitleaks binary version (例: `gitleaks version 8.30.1`)
- history scan の所要時間
- audit finding 件数 (期待: 0)
- CI 4 jobs の build time (Task 2 Step 10 で取得済)

---

## Task 4: Day29 archive (README + LESSONS)

**Files:**
- Create: `docs/sessions/day29/README.md`
- Create: `docs/sessions/day29/DAY29_LESSONS_LEARNED.md`

**目的:** Day29 session の成果と学びを永続記録する。Day23/25/26/27/28 と同じディレクトリ構造を維持する。

- [ ] **Step 1: docs/sessions/day29 ディレクトリ作成**

```bash
mkdir -p docs/sessions/day29
```

- [ ] **Step 2: `README.md` 作成**

Write tool で `/Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver/docs/sessions/day29/README.md` を以下の内容で作成。`<sec-SHA>` は Task 2 commit SHA、`<archive-SHA>` は `(本 commit)` に置換する:

```markdown
# Day29: pre-commit gitleaks 導入 (Day23 再発防止)

**実施日**: 2026-05-28
**起点 commit**: `ddff834` (Day29 spec commit)
**完了 commit**: `<sec-SHA>` (Day29 Task 2 atomic security setup)

## §1 概要

Day23 で発生した機密データ commit 事故 (fixture に peer-review 由来内容が
含まれ filter-repo + force push で対応) の再発防止を目的として、3 層防御
機構 (Local pre-commit hook + CI gitleaks job + one-shot history audit)
を導入した。

## §2 成果

| 項目 | Day28 末 | Day29 末 | 差分 |
|:---|:---:|:---:|:---:|
| pre-commit hook | 未導入 | gitleaks v8.30.1 動作中 | + Layer 1 |
| CI gitleaks job | なし | gitleaks-action@v2 | + Layer 2 |
| CONTRIBUTING.md | 未作成 | 作成済 | + 開発者ガイド |
| history audit baseline | 未確認 | **0 件**確認 | + Layer 3 (one-shot) |
| dev dependency | pytest のみ | + pre-commit>=4.0,<5.0 | + 1 件 |
| CI jobs | 3 | 4 | + gitleaks |
| tests passed | 115 | 115 | 0 (test 追加なし) |
| commit 数 | — | 4 | spec + plan + security + archive |

## §3 commit chain

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `ddff834` | docs(spec) | Day29 pre-commit gitleaks introduction spec |
| 2 | `<plan-SHA>` | docs(plan) | Day29 pre-commit gitleaks introduction plan |
| 3 | `<sec-SHA>` | chore(security) | atomic 6-file security setup |
| 4 | `(本 commit)` | docs(sessions) | archive day29 session |

## §4 関連ドキュメント

- [Spec](../../superpowers/specs/2026-05-28-day29-pre-commit-gitleaks-design.md)
- [Plan](../../superpowers/plans/2026-05-28-day29-pre-commit-gitleaks.md)
- [LESSONS](DAY29_LESSONS_LEARNED.md)
- [CONTRIBUTING.md](../../../CONTRIBUTING.md)

## §5 関連セッション

- [Day23](../day23/README.md): 機密データ事故 + filter-repo 浄化 (本 session の動機)
- [Day27](../day27/README.md): pyproject.toml + uv.lock 体制 (本 session が依存)
- [Day28](../day28/README.md): Latin Extended-A 拡張 (前 session)
```

注: `<plan-SHA>` は Task 0 commit、`<sec-SHA>` は Task 2 commit。実際の SHA は Step 4 で実値置換する。

- [ ] **Step 3: `DAY29_LESSONS_LEARNED.md` 作成**

Write tool で `/Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver/docs/sessions/day29/DAY29_LESSONS_LEARNED.md` を以下の内容で作成。`<...>` placeholder は Step 4 で実値置換:

```markdown
# Day29 Lessons Learned (2026-05-28)

## §1 概要

Day23 で発生した機密データ commit 事故 (fixture に peer-review 由来内容が
含まれ git filter-repo + force push で対応) の再発防止のため、3 層防御
機構を導入した。

### §1.1 セッション開始時の状態

- 115 passed / 0 skipped (Day28 末)
- pre-commit hook 未導入、CONTRIBUTING.md 未作成
- CI 3 jobs (test 3.11, test 3.12, test-experimental 3.14)
- pyproject.toml dev group: pytest のみ

### §1.2 セッション終了時の状態

- 115 passed / 0 skipped / 0 failed (test 追加なし)
- pre-commit hook 動作中 (gitleaks v8.30.1)
- CI 4 jobs (+ gitleaks)
- CONTRIBUTING.md 作成済 (約 80 行、install 手順 + commit 規約 + セキュリティ規約)
- history audit baseline: **0 件** (Day23 filter-repo の効果実証)
- LLM cost: $0 (設定 + 動作検証のみ、外部 API 呼び出しなし)

---

## §2 設計上の発見

### §2.1 Day23 学びの自動化

Day23 で「人間の目視 review のみに依存」したことが事故の根本原因だった。
Day29 で導入した 3 層防御は、Day23 学びを **自動化機構** に翻訳したもの:

| Day23 教訓 | Day29 自動化 |
|:---|:---|
| commit 前検出機構がなかった | Layer 1: Local pre-commit hook |
| `--no-verify` でローカル防御が無効化され得る | Layer 2: CI gitleaks job (二重防御) |
| 過去の漏洩が未検証だった | Layer 3: One-shot history audit (0 件 baseline) |

### §2.2 gitleaks default rule の妥当性

事前懸念: PMID (8 桁数字) や DOI URL を誤検出するのではないか?

実証結果 (history audit):
- 全 commit history scan で finding **0 件**
- false positive なし
- PMID/DOI は gitleaks default rule の対象外 (API key/token/private key
  の典型 pattern のみ検出)

結論: `.gitleaks.toml` の事前 customization は **不要**。false positive
発生時に reactive 対応で十分 (YAGNI 原則)。

### §2.3 pre-commit framework と uv 統合パターン

Day27 で確立した uv 体制と pre-commit framework の統合方式:

```bash
# 開発者の install 1 行
uv sync --group dev && uv run pre-commit install
```

- `uv sync --group dev` で pre-commit パッケージを install
- `uv run pre-commit install` で `.git/hooks/pre-commit` を配置
- pre-commit framework が gitleaks binary を auto-download (初回のみ)
- これで CLAUDE.md §8.1 (uv 統一) と整合

### §2.4 Atomic 6-file commit の合理性

partial state は効果不完全:
- `.pre-commit-config.yaml` のみ → 開発者が hook install しないと無効
- CI job のみ → push 前にローカルでの早期検知なし
- CONTRIBUTING.md のみ → 機構未配置

→ 6 ファイルを 1 commit にまとめることで「Day29 commit を revert すれば
完全に元の状態に戻る」性質を確保 (Day27 atomic migration と同パターン)。

---

## §3 動作検証結果

### §3.1 Layer 1 (Local pre-commit hook)

| 検証項目 | 結果 |
|:---|:---:|
| `uv run pre-commit install` で hook 配置 | ✓ |
| ダミー secret (AKIAIOSFODNN7EXAMPLE + SECRET_KEY) を含む file の commit 試行 | **commit ブロック** ✓ |
| 通常 file (README.md 空行追加) の commit 試行 | **commit 成功** ✓ |
| gitleaks binary version | v8.30.1 ✓ |

### §3.2 Layer 2 (CI gitleaks job)

| 検証項目 | 結果 |
|:---|:---:|
| Task 2 push 後 CI 4 jobs all green | ✓ |
| gitleaks job の build time | `<CI gitleaks job build time>` |
| CI run ID | `<CI run ID>` |

### §3.3 Layer 3 (One-shot history audit)

```
gitleaks detect --log-opts="--all" --source .
```

| 項目 | 値 |
|:---|:---:|
| Scan 対象 commits 数 | `<scanned commits count>` |
| Scan 所要時間 | `<scan duration>` |
| Finding 件数 | **0** |
| Report file | `.gitleaks-audit.json` (.gitignore で除外、commit しない) |

**意義**: Day23 で実施した filter-repo + force push が完全に履歴を浄化した
ことを、gitleaks の客観的 audit で証明。Day23 対応の事後検証として価値が
大きい。

---

## §4 brainstorm/spec/plan の流れ

| 段階 | 内容 | commit |
|:---:|:---|:---:|
| 1 | brainstorm: テーマ選定 (Pattern A pre-commit gitleaks)、scope 確定 (二重防御 + history audit) | — |
| 2 | spec 書き出し + self-review | `ddff834` |
| 3 | plan 書き出し + Task 0-4 bite-sized 分解 | `<plan-SHA>` |
| 4 | Task 1 事前確認 (uv/pre-commit/gitleaks tag 存在確認) | — |
| 5 | Task 2 atomic 6-file security setup + push + CI 4 jobs 確認 | `<sec-SHA>` |
| 6 | Task 3 動作検証 + history audit (0 件 baseline) | — (commit なし) |
| 7 | Task 4 archive (README + LESSONS) + push + CI | `(本 commit)` |

self-review で発見した訂正点 (plan):
- spec で仮置きしていた gitleaks v8.21.4 を、plan 時点で確認した最新版
  v8.30.1 (2026-03-21 release) に update

---

## §5 Day30+ 候補

### Top priority (Day29 LESSONS から派生)

1. **追加 pre-commit hook の検討**
   - end-of-file-fixer / trailing-whitespace / check-yaml / check-toml
   - 規模: 小 (`.pre-commit-config.yaml` への追記のみ)
   - ROI: 中 (style 統一による diff ノイズ削減)

2. **SECURITY.md 整備**
   - Vulnerability disclosure policy
   - 規模: 小 (1 file 追加)
   - ROI: 中 (PyPI 公開化前提では必須)

### Medium priority (既存候補から引き継ぎ)

3. **ruff + mypy 導入** (CLAUDE.md §8.2 既定、技術的負債解消、Day28 LESSONS §5)
4. **Node.js 20 deprecation 対応** (actions/checkout@v4 → @v5)
5. **PyPI 公開化** (複数セッション規模、Day27 LESSONS から継続)
6. **CI python-version-file SoT 化**
7. **Dependabot 設定** (依存更新自動化)

### Low priority (将来オプション)

8. **regex + `\p{Lu}` への移行** (Day28 LESSONS §5、Latin Extended-A の小文字
   混入排除、boundary 文脈で false positive 影響ゼロなので低優先)
9. **PMC OA fixture integration test** (Latin Extended-A 実 paper)
10. **Latin Extended-B / Extended Additional 拡張**
11. **Crossref graceful failure** (apa_45refs の 16 件)
12. **NLM fuzzy-match 精度改善**

---

## §6 メトリクス

| 指標 | 値 |
|:---|:---:|
| brainstorm 質問数 | 2 (gitleaks スコープ / history audit 実施) |
| commit 数 | 4 (spec / plan / security / archive) |
| 新規 file 数 | 4 (.pre-commit-config.yaml, CONTRIBUTING.md, README.md, DAY29_LESSONS_LEARNED.md) |
| modify file 数 | 4 (pyproject.toml, uv.lock, .gitignore, .github/workflows/tests.yml) |
| 新規 dependency | 1 (pre-commit>=4.0,<5.0、dev group のみ) |
| pyproject.toml 変更行 | +1 |
| .github/workflows/tests.yml 変更行 | +約 9 (gitleaks job 追加) |
| CONTRIBUTING.md 行数 | 約 80 |
| 全体 tests passed | 115 → 115 (test 追加なし) |
| skipped | 0 → 0 |
| LLM cost | $0 |
| history audit finding | **0** |
| CI 4 jobs build time | test 3.11: `<X>s`, test 3.12: `<X>s`, test-experimental 3.14: `<X>s`, **gitleaks: `<X>s`** |

---

## §7 関連参照

- [Spec](../../superpowers/specs/2026-05-28-day29-pre-commit-gitleaks-design.md)
- [Plan](../../superpowers/plans/2026-05-28-day29-pre-commit-gitleaks.md)
- [CONTRIBUTING.md](../../../CONTRIBUTING.md)
- [Day23 LESSONS](../day23/DAY23_LESSONS_LEARNED.md): 機密データ事故と filter-repo 対応
- [Day27 LESSONS](../day27/DAY27_LESSONS_LEARNED.md): pyproject + uv 体制
- [Day28 LESSONS](../day28/DAY28_LESSONS_LEARNED.md): 前 session
- [gitleaks 公式](https://github.com/gitleaks/gitleaks)
- [pre-commit.com](https://pre-commit.com/)
```

注: `<...>` placeholder は Step 4 で実値置換する。

- [ ] **Step 4: SHA / CI build time / audit 結果を実値で置換**

実値取得:
```bash
git log --oneline -5
gh run list --limit 3
python3 -c "import json; print(len(json.load(open('.gitleaks-audit.json'))))"
```

取得した値で README.md と DAY29_LESSONS_LEARNED.md の placeholder を Edit tool で置換:

| Placeholder | 取得元 |
|:---|:---|
| `<plan-SHA>` (README §3 / LESSONS §4) | `git log` の Task 0 commit |
| `<sec-SHA>` (README §1, §3 / LESSONS §4) | `git log` の Task 2 commit |
| `<CI gitleaks job build time>` (LESSONS §3.2) | `gh run view` から取得 |
| `<CI run ID>` (LESSONS §3.2) | `gh run list` から取得 |
| `<scanned commits count>` (LESSONS §3.3) | Task 3 Step 3 の gitleaks log から、または `git rev-list --all | wc -l` |
| `<scan duration>` (LESSONS §3.3) | Task 3 Step 3 の実測 (gitleaks log 末尾) |
| `<X>s` (LESSONS §6) | `gh run view <run-id>` の各 job 時間 |

archive commit SHA は Step 5 で生成されるので、`(本 commit)` 表記のままにする。

- [ ] **Step 5: archive commit**

```bash
git add docs/sessions/day29/README.md docs/sessions/day29/DAY29_LESSONS_LEARNED.md
git commit -m "$(cat <<'EOF'
docs(sessions): archive day29 pre-commit gitleaks introduction session

Day23 機密データ事故再発防止のために導入した 3 層防御機構 (Local
pre-commit hook + CI gitleaks job + one-shot history audit) の
成果と学びを永続記録。

主要 finding:
- Day23 学びの自動化機構への翻訳に成功 (人間の目視 review → 機械的
  3 層防御)
- gitleaks default rule で PMID/DOI 誤検出なし、history audit 0 件
  (Day23 filter-repo の効果実証)
- pre-commit framework + uv の統合パターンを確立
- Atomic 6-file commit で partial state による効果不完全を回避

成果: 115 passed (test 追加なし)、commit 4、CI 4 jobs (+ gitleaks)、
history audit 0 件、LLM cost \$0

Day30+ 候補として追加 pre-commit hook、SECURITY.md 整備、ruff/mypy
導入、Node.js 20 deprecation 対応等を LESSONS に記録。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: archive commit を push + CI 確認**

```bash
git push origin main
gh run watch
```
Expected: 4 jobs all green、archive commit でも gitleaks job が pass。

- [ ] **Step 7: 最終 state 確認**

```bash
git log --oneline -7
```
Expected:
```
<SHA> docs(sessions): archive day29 pre-commit gitleaks introduction session
<sec-SHA> chore(security): introduce gitleaks pre-commit hook + CI job + CONTRIBUTING.md (Day29)
<plan-SHA> docs(plan): add Day29 pre-commit gitleaks introduction plan
ddff834 docs(spec): add Day29 pre-commit gitleaks introduction spec
4a0adfd docs(sessions): archive day28 Latin Extended-A expansion session
08a0b90 fix(parse): extend _UPPERCASE_LATIN1 to Latin Extended-A (Day28 Task 2 TDD GREEN)
221adf8 test(prep): add failing unit tests for Latin Extended-A boundary (Day28 Task 1 TDD RED)
```

```bash
uv run pytest tests/ 2>&1 | tail -3
```
Expected: `115 passed`

```bash
ls -la .pre-commit-config.yaml CONTRIBUTING.md docs/sessions/day29/
```
Expected: すべて存在。

```bash
git status
```
Expected: `nothing to commit, working tree clean` (`.gitleaks-audit.json` は .gitignore で除外されているので表示されない)。

---

## Self-review notes (writer から実装者へのメモ)

### Spec → Plan の divergence point

- Spec §3.2 で gitleaks `v8.21.x` と仮置きしていたが、plan 時点での最新確認で **v8.30.1** に update (2026-03-21 release)。Spec の意図 (「v8.x 系最新採用」) と整合的で、内容変更ではなく具体化。
- Spec §3.6 の CONTRIBUTING.md は「最小 30-50 行」と推定していたが、plan では約 80 行に拡張 (Conventional Commits 詳細表 + セキュリティ規約を追記)。これは spec §6 (CONTRIBUTING.md 構造) の意図的拡充。

### 動作検証の non-test 性質

Day29 では「test 追加なし」が plan の根幹。pre-commit hook の動作は manual
smoke test (Task 3 Step 1-2) で確認し、CI gitleaks job の動作は CI run の green で確認する。これらは「Day29 セッション内の 1 回限りの動作検証」であり、pytest test として永続化する性質ではない。

permanent regression guard は CI gitleaks job 自体が担う (PR ごとに自動実行)。

### `.gitleaks-audit.json` の取り扱い

- 機密 finding を含み得るため **絶対に commit しない**
- `.gitignore` で先に除外 (Task 2 Step 3 で実装)
- LESSONS には件数 (期待: 0) のみ記録、内容詳細は記載しない
- Task 3 終了後、開発者の好みで `rm .gitleaks-audit.json` してよい (再生成可能)

### 行番号下方シフトの予測

- `pyproject.toml`: dev group に 1 行追加、L52 → L53 程度のシフト
- `.gitignore`: 末尾 2 行追加、影響極小
- `.github/workflows/tests.yml`: 末尾 10 行追加、既存 job の行番号は無変更

### Task 3 のスキップ可能性

Task 3 は「動作検証」であり commit を生成しないため、強制ではない。ただし
LESSONS §3 (動作検証結果) に空欄が残ると Day29 の価値証明が弱くなるため、
推奨は **全 Step 実施**。

時間制約で skip する場合:
- Step 3-5 (history audit) は最重要 (Day29 の核心)、必須
- Step 1-2 (smoke test) は省略可、ただし LESSONS §3.1 にその旨を明記

---

**End of Plan**
