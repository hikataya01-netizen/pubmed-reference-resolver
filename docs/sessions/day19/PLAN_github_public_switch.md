# GitHub Public Switch Implementation Plan (Day19)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Day18 で Private push 済の `hikataya01-netizen/pubmed-reference-resolver` を MIT License 追加 + CHANGELOG 整備 + README polish + visibility 変更によって Public に切り替え、Day7 §9.3 副次タスクの完了と外部公開によるプロジェクト到達性向上を実現する.

**Architecture:** Day18 で確立された Phased 戦略の Phase 2. production code / test / fixture には一切手を付けず、LICENSE 新規追加 + CHANGELOG.md milestone summary 追記 + README.md 4 箇所拡充 (badges + TOC + env install hint + License/Acknowledgments) + gitleaks 公開直前再 scan + `gh repo edit --visibility public` + topics 追加. env file 取扱いは Day18 で安全性確認済 (gitignored + never committed) のため Day19 では README install hint 追加のみで env-side リスクなし.

**Tech Stack:** gitleaks 8.x / GitHub CLI (`gh`) / git / GitHub Actions (既存 workflow + 自動 license detection)

**SPEC**: `docs/sessions/day19/SPEC_github_public_switch.md` (commit `40f5b2d` + extension `8baa81b`)
**直接 template**: `docs/sessions/day18/PLAN_github_private_push.md` (commit `f5a44f1`)

---

## File Structure

### 新規作成 (5 ファイル)

| ファイル | 責務 |
|:---|:---|
| `LICENSE` | MIT License SPDX 標準テキスト (Copyright (c) 2026 Hideki Katayama) |
| `docs/sessions/day19/SECRET_SCAN_REPORT.md` | 公開直前の gitleaks 再 scan 結果 (Day19 commits 含む) |
| `docs/sessions/day19/README.md` | Day19 セッション index |
| `docs/sessions/day19/DAY19_LESSONS_LEARNED.md` | Day19 末アーカイブ |
| `docs/sessions/day19/PLAN_github_public_switch.md` | 本 PLAN (既に作成中) |

### 修正対象 (2 ファイル)

| ファイル | 修正内容 |
|:---|:---|
| `CHANGELOG.md` | 新規 `## [Unreleased] - 2026-05-18` section を **既存 `[Unreleased] - 2026-04-23` の前**に挿入 (~60 行追加) |
| `README.md` | 4 箇所拡充: badges (2 個) + TOC + install env hint + License + Acknowledgments (~35 行追加、134 → 169 行見込) |

### 改変なし (確認のみ)

- production code (`main.py`, `mdpi_parser.py`, `crossref_check.py`, `nlm_catalog_check.py`, `three_class_classifier.py`, `journal_audit.py`)
- 全 test ファイル (97 passed 維持)
- 全 fixture ファイル
- `.gitignore` / `.gitleaksignore` / `.env.example` (Day18 で最終化済)
- 既存 docs (Day7-18 archive)

### 外部システム変更

- `gh repo edit hikataya01-netizen/pubmed-reference-resolver --visibility public --accept-visibility-change-consequences`
- `gh repo edit ... --add-topic pubmed --add-topic peer-review --add-topic claude-skill --add-topic medical-references --add-topic bibliographic-audit --add-topic reference-validation` (6 topics)

---

## Task 1: LICENSE (MIT) 配置 (Phase 1)

**Files:**
- Create: `LICENSE` (repo root)

- [ ] **Step 1: LICENSE ファイル作成**

Write `LICENSE` (repo root) with verbatim MIT License SPDX text:

```
MIT License

Copyright (c) 2026 Hideki Katayama

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: LICENSE 内容確認**

```bash
head -3 LICENSE && wc -l LICENSE
```

Expected:
```
MIT License

Copyright (c) 2026 Hideki Katayama
22 LICENSE
```

- [ ] **Step 3: GitHub が認識する SPDX 形式か確認**

```bash
file LICENSE && grep -c "MIT License" LICENSE
```

Expected: `LICENSE: ASCII text` + `1` (1 件マッチ).

Note: GitHub は repo root の `LICENSE` ファイルから SPDX 形式 (`MIT License` 1 行目) で自動 detect する. Public 切替後の sidebar に "MIT License" として表示される.

- [ ] **Step 4: Phase 1 commit**

```bash
git add LICENSE && \
git commit -m "$(cat <<'EOF'
docs(license): add MIT License (Day19 Phase 1)

Public 切替に向けて MIT License を repo root に配置.
SPDX 標準テキストの逐語コピー、Copyright (c) 2026 Hideki Katayama.

fixture (PMC OA 抽出 reference data) は MIT 適用範囲外:
- factual data として一般に著作権の対象外
- 各 fixture (vancouver/apa/cell) の README で CC BY 4.0 帰属表示済

Public 切替後の GitHub sidebar "About" section に License: MIT として
自動表示される (SPDX detection).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: CHANGELOG.md に Day8-18 milestone summary 追加 (Phase 2)

**Files:**
- Modify: `CHANGELOG.md` (新規 `## [Unreleased] - 2026-05-18` section を line 9 以前に挿入)

- [ ] **Step 1: 現状確認**

```bash
head -12 CHANGELOG.md
```

Expected: line 9 に `## [Unreleased] - 2026-04-23` (Day1-7 era section header) が見える.

- [ ] **Step 2: 新規 section を Day7-era section の前に挿入**

Edit `CHANGELOG.md`: line 9 の `## [Unreleased] - 2026-04-23` の **直前** (line 9 と同じ位置から) に以下 `## [Unreleased] - 2026-05-18` セクションを挿入. 既存の Day7-era section はそのまま下に移動する.

挿入する内容:

```markdown
## [Unreleased] - 2026-05-18

### Day8-18 統合: Vancouver Veto + 4 fixture + 3 分類 audit + GitHub 公開準備

Day8-18 で実装された主要機能を 6 カテゴリで集約.

### Added (新規追加)

- **Vancouver Veto** (`mdpi_parser.py` regex 強化, Day9 + Day16): `(YYYY)` および `(YYYYa)` を検出して MDPI fast-path から LLM path に強制 routing. APA 7 disambiguation suffix にも対応.
- **golden fixture 3 系統**: vancouver_24refs (Day11, OneDrive 24 件)、apa_45refs (Day16, PMC OA 3 論文計 45 件)、cell_45refs (Day17, iScience 3 論文計 45 件). Day11 で確立された `expected_*` / `baseline_*` ハイブリッド命名規約準拠.
- **3 分類 audit logic** (Day15, 新 3 module): `crossref_check.py` (Crossref DOI 実在確認)、`nlm_catalog_check.py` (NLM Catalog journal indexing 確認)、`three_class_classifier.py` (A=真の捏造 / B=MEDLINE 非収録 / C=収録誌 indexing 漏れ / unknown=fail-soft 分類). `main.py` Phase 4 で sidecar JSON 出力.
- **build script 群** (Day16-17): `tools/build_apa_fixture.py` / `tools/build_cell_fixture.py` (PMC OA JATS XML → APA/Cell plain text → docx 自動組成).
- **session archive 群** (Day8-18): `docs/sessions/day{8,...,18}/` に SPEC / PLAN / LESSONS / 補助 docs を継続蓄積. 全 11 セッション分.
- **API key setup docs** (Day12): `docs/operations/SETUP_API_KEYS.md`.
- **USAGE_QUICKSTART** 1.0 → 1.5 (Day10/14/15/17 各 bump): `skill_package/references/USAGE_QUICKSTART.md` に 3 分類 audit / 4 fixture 情報を追記.
- **GitHub Private push** (Day18): `hikataya01-netizen/pubmed-reference-resolver`、CI 動作確認、gitleaks-based secret scan protocol 確立.

### Changed (変更)

- **env loader** (`main.py:load_env_files`, Day8): 空値環境変数を上書き対応 (harness サブプロセス継承時の空値問題に対処).
- **SKILL.md / USAGE_QUICKSTART** (Day14-17): 「捏造引用 = PubMed 未ヒット」の単純化記述を 3 分類体系に書換.
- **`.gitignore`** (Day16/18): `.cache/`, `.DS_Store` 追加.

### Fixed (修正)

- **MDPI parser `<collab>` 対応** (Day16, `tools/build_apa_fixture.py`): 組織著者 `<collab>` 要素から author を抽出可能に. PMC OA refs 28/37 の空抽出問題を解決.

### Documentation

- README.md を Day17 末状態に更新 (Day18 Phase 2): 97 tests / 4 fixture / Day8-17 構成反映.

### Test 健全性推移

| Day | passed | 主な追加 |
|:---:|---:|:---|
| Day7 末 | 52 | (baseline) |
| Day8 末 | 56 | env loader test |
| Day11 末 | 60 | vancouver_24refs test |
| Day15 末 | 71 | 3 module test |
| Day16 末 | 81 | apa_45refs test |
| Day17 末 | 89 | cell_45refs test |
| Day19 末 (見込) | 89 | (公開化のみ、test 改変なし) |

詳細な経緯は `docs/sessions/day{8,...,18}/DAY*_LESSONS_LEARNED.md` を参照.

```

- [ ] **Step 3: 挿入結果確認**

```bash
grep -n "## \[Unreleased\]" CHANGELOG.md
```

Expected:
```
9:## [Unreleased] - 2026-05-18
NN:## [Unreleased] - 2026-04-23
```

(2026-05-18 section が 2026-04-23 section より前にあること、line 9 から始まること)

- [ ] **Step 4: 詳細内容確認**

```bash
grep -c "Day8-18 統合\|Vancouver Veto\|3 分類 audit\|golden fixture\|build script 群\|USAGE_QUICKSTART" CHANGELOG.md
```

Expected: `6` 以上 (6 主要 keyword 全部存在).

- [ ] **Step 5: Phase 2 commit**

```bash
git add CHANGELOG.md && \
git commit -m "$(cat <<'EOF'
docs(changelog): add Day8-18 milestone summary (Day19 Phase 2)

CHANGELOG.md に新規 [Unreleased] - 2026-05-18 section を追加.
既存 [Unreleased] - 2026-04-23 (Day1-7 era、Step 1-7) はそのまま下に残す.

Day8-18 の主要機能を 6 カテゴリで集約:
- Added: Vancouver Veto、4 fixture、3 分類 audit、build script 群、
  session archive 群、SETUP_API_KEYS、USAGE_QUICKSTART bump、
  GitHub Private push
- Changed: env loader、SKILL.md/USAGE_QUICKSTART 3 分類書換、.gitignore
- Fixed: <collab> 対応
- Documentation: README update
- Test 健全性推移表 (52 → 89 passed)

詳細経緯は docs/sessions/day{8,...,18}/ を参照. v0.1.0 tag 付与は
Day20+ で別途 (本 commit では [Unreleased] のまま).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: README.md 4 箇所拡充 (Phase 3)

**Files:**
- Modify: `README.md` (4 箇所: badges + TOC + install env hint + License/Acknowledgments)

- [ ] **Step 1: 現状確認**

```bash
wc -l README.md && head -5 README.md
```

Expected: 134 行 + line 3 に既存 tests badge.

- [ ] **Step 2: 修正 (a) — Badges 2 個追加 + TOC 追加 (line 3-4 拡張)**

Edit `README.md`: line 3 (既存 tests badge 行) の**直後**に License + Python badge 2 個を追加し、空行の後に Table of Contents を挿入:

旧 (line 1-5):
```markdown
# pubmed-reference-resolver

[![tests](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml/badge.svg)](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml)

査読対象論文の References セクション (PDF / DOCX / TXT) から各文献を PubMed で逆引き検索し、
```

新:
```markdown
# pubmed-reference-resolver

[![tests](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml/badge.svg)](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Table of Contents

- [主な機能](#主な機能)
- [インストール](#インストール)
- [使用方法](#使用方法)
- [テスト](#テスト)
- [ゴールドスタンダード fixture (4 系統)](#ゴールドスタンダード-fixture-4-系統)
- [プロジェクト構成](#プロジェクト構成)
- [License](#license)
- [Acknowledgments](#acknowledgments)

査読対象論文の References セクション (PDF / DOCX / TXT) から各文献を PubMed で逆引き検索し、
```

- [ ] **Step 3: 修正 (c-pre) — インストール section に env setup 手順追記**

Edit `README.md`: 既存の `pip install -r requirements.txt` の**直後** (同 code block 内) に env setup 手順 5 行を追記:

旧 (install section の code block):
```bash
git clone git@github.com:hikataya01-netizen/pubmed-reference-resolver.git
cd pubmed-reference-resolver
pip install -r requirements.txt
```

新:
```bash
git clone git@github.com:hikataya01-netizen/pubmed-reference-resolver.git
cd pubmed-reference-resolver
pip install -r requirements.txt

# API key 設定 (Anthropic + NCBI)
cp .env.example .env
# .env を編集して REPLACE-WITH-YOUR-KEY を実 key に置換
# 詳細: docs/operations/SETUP_API_KEYS.md
```

- [ ] **Step 4: 修正 (b) — ファイル末尾に License section 追加**

Edit `README.md`: ファイル末尾 (現 line 134 末) に append:

```markdown

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Hideki Katayama
```

- [ ] **Step 5: 修正 (c) — ファイル末尾に Acknowledgments section 追加 (License の次)**

Edit `README.md`: 修正 (b) の License section 末尾に続けて以下を append:

```markdown

## Acknowledgments

このプロジェクトは以下の OSS と公開リソースに依存する:

- **NCBI E-utilities** (PubMed / PMC / NLM Catalog) — bibliographic information retrieval
- **Crossref REST API** — DOI 実在確認 (Day15 で導入された 3 分類 audit logic で使用)
- **Anthropic Claude Sonnet 4.6** — LLM-path での reference 構造化
- **PMC Open Access subset** — fixture data (CC BY 4.0 採用 3 系統 = vancouver/apa/cell). 各 fixture の `tests/fixtures/*/README.md` で source paper citation を明示.

開発期間中 (Day1-19) は **Claude Code (Sonnet 4.6)** および **Claude Opus 4.7 (1M context)** が共同作業者として参画した. 全 commit の `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` trailer はその記録.
```

- [ ] **Step 6: 修正結果確認**

```bash
echo "[a-1] tests badge:" && grep -c "actions/workflows/tests.yml/badge.svg" README.md
echo "[a-2] License badge:" && grep -c "License-MIT" README.md
echo "[a-3] Python badge:" && grep -c "python-3.11+" README.md
echo "[a-4] TOC heading:" && grep -c "## Table of Contents" README.md
echo "[c-pre] env setup hint:" && grep -c "cp .env.example .env" README.md
echo "[b] License section:" && grep -c "^## License$" README.md
echo "[c] Acknowledgments section:" && grep -c "^## Acknowledgments$" README.md
echo "" && \
echo "Total README line count:" && wc -l README.md
```

Expected:
- [a-1] `1` (tests badge)
- [a-2] `1` (License badge)
- [a-3] `1` (Python badge)
- [a-4] `1` (TOC)
- [c-pre] `1` (env hint)
- [b] `1` (## License heading)
- [c] `1` (## Acknowledgments heading)
- Total: ~169 行 (134 + 35 = 169 見込)

- [ ] **Step 7: Phase 3 commit**

```bash
git add README.md && \
git commit -m "$(cat <<'EOF'
docs(readme): add badges + TOC + env hint + License + Acknowledgments (Day19 Phase 3)

Public 切替に向けて README.md を 4 箇所拡充 (~35 行追加、134 → 169 行):

(a) 冒頭 badges に 2 個追加 + Table of Contents 挿入
    - tests (既存) + License: MIT + Python 3.11+ の 3 badges 揃う
    - TOC で 8 section に anchor link

(c-pre) インストール section に env setup 手順を 5 行追記
    - cp .env.example .env コマンド + 編集指示 + SETUP_API_KEYS リンク
    - Day19 brainstorming 中の env file 安全性確認を契機に追加
    - Public 公開後の onboarding 時間を短縮

(b) 末尾に ## License section を 5 行追加
    - LICENSE file へのリンク + Copyright (c) 2026 Hideki Katayama

(c) 末尾に ## Acknowledgments section を 11 行追加
    - NCBI E-utilities / Crossref / Anthropic Claude / PMC Open Access
    - Claude Code (Sonnet 4.6) + Claude Opus 4.7 の共同作業記録

主な機能・使用方法・テスト・fixture・プロジェクト構成は Day18 状態
維持 (修正なし).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: gitleaks 公開直前再 scan + SECRET_SCAN_REPORT.md (Phase 4a)

**Files:**
- Create: `docs/sessions/day19/SECRET_SCAN_REPORT.md`

- [ ] **Step 1: gitleaks 再 scan を repo dir で実行**

```bash
cd /Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver && \
gitleaks detect --source . --verbose \
  --report-format json \
  --report-path /tmp/gitleaks_report_day19.json
```

Expected: `INF X commits scanned` (X >= 80) + `INF no leaks found` (`.gitleaksignore` の Day18 既存 suppression が有効、Day19 新規追加 commit も clean).

- [ ] **Step 2: 結果 JSON の finding count を確認**

```bash
jq 'length' /tmp/gitleaks_report_day19.json
```

Expected: `0`

⚠️ leak 検出時: **公開中止**、原因対応 (新規 false positive なら `.gitleaksignore` 更新、真の leak なら `git filter-repo` で history rewrite)、再 scan.

- [ ] **Step 3: 手動 grep 5 patterns 補完**

```bash
echo "=== ANTHROPIC_API_KEY=sk- ===" && git log --all -p -S "ANTHROPIC_API_KEY=sk-" 2>&1 | head -5
echo "=== NCBI_API_KEY= (Day19 含む) ===" && git log --all -p -S "NCBI_API_KEY=" 2>&1 | head -5
echo "=== PRIVATE KEY ===" && git log --all -p -S "PRIVATE KEY" 2>&1 | head -5
echo "=== Bearer ===" && git log --all -p -S "Bearer " 2>&1 | head -5
echo "=== unexpected gmail ===" && git log --all -p -S "@gmail.com" 2>&1 | grep -v "Co-Authored\|hikataya01" | head -5
```

Expected: 全 pattern hit は Day18 PLAN + Day19 SPEC/PLAN ドキュメント自身の self-reference のみ. 実 leak なし.

- [ ] **Step 4: Scan メタデータを収集**

```bash
SCAN_DATE=$(date '+%Y-%m-%d %H:%M:%S %Z')
GITLEAKS_VERSION=$(gitleaks version)
COMMIT_COUNT=$(git log --oneline | wc -l | tr -d ' ')
HEAD_COMMIT=$(git rev-parse --short HEAD)
FIRST_COMMIT=$(git log --oneline | tail -1 | awk '{print $1}')
LEAK_COUNT=$(jq 'length' /tmp/gitleaks_report_day19.json)
echo "SCAN_DATE: $SCAN_DATE"
echo "GITLEAKS_VERSION: $GITLEAKS_VERSION"
echo "COMMIT_COUNT: $COMMIT_COUNT"
echo "HEAD_COMMIT: $HEAD_COMMIT"
echo "FIRST_COMMIT: $FIRST_COMMIT"
echo "LEAK_COUNT: $LEAK_COUNT"
```

これらの値を Step 5 README に転記する.

- [ ] **Step 5: SECRET_SCAN_REPORT.md を作成**

`docs/sessions/day19/SECRET_SCAN_REPORT.md` に以下を書き込む (Step 4 の実測値で `<...>` を置換):

```markdown
# Secret Scan Report (Day19, 公開直前 再 scan)

**Purpose**: Day19 Public 切替**直前**の git history 全体 secret scan の evidence 記録. Day18 SECRET_SCAN_REPORT (Private push 前) の再実行版で、Day18 以降の追加 commit (Day19 SPEC + PLAN + LICENSE + CHANGELOG + README 修正) も含めて clean であることを確認.

**Result**: ✅ **SAFE TO MAKE PUBLIC** (clean、Day18 既存 `.gitleaksignore` suppression が継続有効)

---

## 1. Execution Metadata

- **実行日時**: <SCAN_DATE>
- **gitleaks version**: <GITLEAKS_VERSION>
- **scan 対象 directory**: `.` (repository root)
- **scan 範囲 (commits)**: `<FIRST_COMMIT>` .. `<HEAD_COMMIT>` (合計 **<COMMIT_COUNT> commits**)
- **scan 実施者**: Claude Code (Sonnet 4.6) 経由
- **承認**: 片山英樹 (Hideki Katayama)
- **Day18 SECRET_SCAN_REPORT との関係**: 同 protocol を Day19 commits 追加後に再実行. `.gitleaksignore` で documented suppression された Day8 test fixture (`tests/test_env_loader.py:40`) は引き続き有効.

## 2. gitleaks Detection

### 2.1 実行コマンド
```bash
gitleaks detect --source . --verbose \
  --report-format json \
  --report-path /tmp/gitleaks_report_day19.json
```

### 2.2 結果
- **Finding count**: <LEAK_COUNT> (期待: 0)
- **Report path**: `/tmp/gitleaks_report_day19.json`
- **gitleaks 出力サマリ**: `no leaks found`

### 2.3 Day18 から Day19 への差分

| 観点 | Day18 SECRET_SCAN | Day19 SECRET_SCAN |
|:---|---:|---:|
| Commits scanned | 68 (Day18 SPEC commit `7d6a50e` 時点) | <COMMIT_COUNT> (Day19 docs 追加後) |
| Findings (`.gitleaksignore` 後) | 0 | <LEAK_COUNT> |
| `.gitleaksignore` 有効 fingerprint | 1 (Day8 test fixture) | 1 (Day18 と同じ、追加なし) |

## 3. Manual Grep 補完 (false negative リスク低減)

| Pattern | Command | 結果 |
|:---|:---|:---|
| Anthropic real key | `git log --all -p -S "ANTHROPIC_API_KEY=sk-"` | (Day18-19 SPEC/PLAN ドキュメント内 self-reference のみ、実 key 含まず) |
| NCBI real key | `git log --all -p -S "NCBI_API_KEY="` | (同上 + Day8 test fixture は `.gitleaksignore` で suppression 済) |
| Private key block | `git log --all -p -S "PRIVATE KEY"` | (Day18-19 SPEC/PLAN ドキュメント内 self-reference のみ) |
| Bearer token | `git log --all -p -S "Bearer "` | (同上) |
| Unexpected email | `git log --all -p -S "@gmail.com" \| grep -v "Co-Authored\|hikataya01"` | (同上、想定外メアドなし) |

すべての pattern hit は Day18-19 PLAN/SPEC/LESSONS ドキュメント自身に含まれる「検査 pattern の説明文」であり、実際の secret leak ではない.

## 4. 許容される email 出現

- `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` — Day8+ で全 commit trailer に付与 (Anthropic noreply、公開しても問題なし)
- `hikataya01@gmail.com` — 本人 author email (`git config user.email`、Public commit log で既に既知の情報、GitHub 連携用)

## 5. env file 取扱いの再確認 (Day19 brainstorming 由来)

| 確認項目 | 結果 |
|:---|:---|
| 実 `.env` 所在 | `skill_package/.env` (1 ファイルのみ、`.gitignore` で除外) |
| `.env` git tracked | ✅ No (`git ls-files` で確認) |
| `.env` git history 含有 | ✅ No (`git log --all --full-history -- '*.env'` 空) |
| `.env.example` tracked + placeholder safe | ✅ Tracked、`REPLACE-WITH-YOUR-KEY` placeholder (gitleaks flag せず) |
| Day19 README install hint で `.env.example` 利用明示 | ✅ Phase 3 で追加済 |

## 6. 結論

すべての検査:
- gitleaks 自動 scan (`.gitleaksignore` で 1 件の synthetic test fixture を documented suppression) → **0 findings**
- 手動 grep 5 patterns → **真の leak なし** (Day18-19 PLAN/SPEC ドキュメント内 self-reference のみ)
- env file 取扱いの再確認 → **すべて安全**

→ **SAFE TO MAKE PUBLIC** (Phase 4b で `gh repo edit --visibility public` 実行可)

---

**作成日**: <SCAN_DATE>
**作成者**: Claude Code (Sonnet 4.6)
**承認**: 片山英樹 (Hideki Katayama)
**関連 SPEC**: `docs/sessions/day19/SPEC_github_public_switch.md` §5 (commit `40f5b2d` + `8baa81b`)
**関連 PLAN**: `docs/sessions/day19/PLAN_github_public_switch.md` Task 4
**関連 prior**: `docs/sessions/day18/SECRET_SCAN_REPORT.md` (Private push 前の初回 scan)
```

- [ ] **Step 6: README の `<...>` を Step 4 実測値で埋める**

Step 4 の出力結果を見ながら、README 内の `<SCAN_DATE>`, `<GITLEAKS_VERSION>`, `<COMMIT_COUNT>`, `<HEAD_COMMIT>`, `<FIRST_COMMIT>`, `<LEAK_COUNT>` を実値に置換 (Edit tool で 1 つずつ).

- [ ] **Step 7: Phase 4a commit**

```bash
git add docs/sessions/day19/SECRET_SCAN_REPORT.md && \
git commit -m "$(cat <<'EOF'
docs(security): add Day19 pre-public secret scan report (Phase 4a)

Day19 Public 切替**直前**の git history 全体 secret scan の evidence
記録. Day18 SECRET_SCAN_REPORT (Private push 前) の再実行版.

gitleaks 8.30.1 で repo dir から <COMMIT_COUNT> commits を full scan:
  - Finding count: 0 (Day18 `.gitleaksignore` の Day8 test fixture
    suppression が継続有効、新規 leak なし)
  - 手動 grep 5 patterns: 全て Day18-19 PLAN/SPEC ドキュメント内
    self-reference のみ、実 leak なし

env file 取扱いの再確認 (Day19 brainstorming 由来):
  - 実 .env (skill_package/.env) は gitignored + never committed
  - .env.example は tracked、REPLACE-WITH-YOUR-KEY placeholder で安全
  - Day19 README install hint で .env.example 利用を明示済

結論: SAFE TO MAKE PUBLIC. Phase 4b で gh repo edit --visibility public
実行可.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: GitHub visibility 変更 + topics 追加 (Phase 4b)

**Files:** (外部システム操作中心、commit なし)
- Modify: なし (GitHub 上の repo metadata 変更のみ)

- [ ] **Step 1: docs 全 push 完了確認 (前提)**

```bash
git status                                # working tree clean
git log --oneline origin/main..HEAD       # 空 (全 push 済) 期待
```

Expected: working tree clean + 未 push commit なし.

⚠️ 未 push commit ある場合: `git push origin main` で先に同期してから Step 2 へ.

- [ ] **Step 2: Visibility 変更**

```bash
gh repo edit hikataya01-netizen/pubmed-reference-resolver \
  --visibility public \
  --accept-visibility-change-consequences
```

Expected: silent 成功 (出力なし、exit code 0).

⚠️ エラー時 (権限不足等): `gh auth status` で scope 再確認、必要なら `gh auth refresh -s repo`.

- [ ] **Step 3: Topics 6 個追加**

```bash
gh repo edit hikataya01-netizen/pubmed-reference-resolver \
  --add-topic pubmed \
  --add-topic peer-review \
  --add-topic claude-skill \
  --add-topic medical-references \
  --add-topic bibliographic-audit \
  --add-topic reference-validation
```

Expected: silent 成功 (出力なし).

⚠️ topic 名は GitHub 規約に従う必要 (lowercase 英数 + `-` のみ、35 文字以内). `gh repo edit` が validate.

- [ ] **Step 4: Public 状態確認**

```bash
gh repo view hikataya01-netizen/pubmed-reference-resolver \
  --json visibility,description,homepageUrl,repositoryTopics,licenseInfo | jq
```

Expected:
```json
{
  "visibility": "PUBLIC",
  "description": "PubMed reference resolver / 査読支援スキル (References → PubMed 逆引き + 統合監査レポート)",
  "homepageUrl": "",
  "repositoryTopics": [
    {"name": "pubmed"},
    {"name": "peer-review"},
    {"name": "claude-skill"},
    {"name": "medical-references"},
    {"name": "bibliographic-audit"},
    {"name": "reference-validation"}
  ],
  "licenseInfo": {
    "name": "MIT License",
    "spdxId": "MIT"
  }
}
```

⚠️ `licenseInfo` が null の場合: GitHub の SPDX detection が遅延 (数分) する場合あり. 数分待って再確認.

- [ ] **Step 5: 匿名 (シークレット ブラウザ) で readability 確認**

```bash
gh repo view --web
```

ブラウザで開いたら、別途 **incognito / プライベートブラウズ** ウィンドウで同 URL を開き (`https://github.com/hikataya01-netizen/pubmed-reference-resolver`) 以下を確認:

- 認証なしで repo が見える (Public 化成功)
- README badges 全 3 個 green (tests / License: MIT / Python 3.11+)
- TOC links が anchor 動作
- License sidebar に "MIT License" 表示
- Topics chips が repository 上部に表示
- About section に description 表示

⚠️ 認証ブラウザで Private 表示が継続している場合は browser cache の問題. ハードリロード (Cmd+Shift+R) で更新.

- [ ] **Step 6: 動作 evidence を控える (commit 不要)**

外部操作のため commit なし. Step 4 の `gh repo view --json` 出力と Step 5 の閲覧確認結果は Task 6 (Day19 archive) の LESSONS に転記する.

---

## Task 6: Day19 archive (Phase 5)

**Files:**
- Create: `docs/sessions/day19/README.md`
- Create: `docs/sessions/day19/DAY19_LESSONS_LEARNED.md`

- [ ] **Step 1: Day19 README.md を作成**

Day18 (`docs/sessions/day18/README.md`) を template に、`docs/sessions/day19/README.md` に以下を書き込む:

```markdown
# docs/sessions/day19/

**Day19 セッション (2026-05-18) のアーカイブ**

このディレクトリは、pubmed-reference-resolver プロジェクトの Day19 セッション (Day18 で Private push 済の repo を Public 切替し、副次的に LICENSE + CHANGELOG + README polish を完了した作業) で生成された記録を、永続アーカイブとして保管する.

## 内容

| ファイル | 役割 | 対象 |
|:---|:---|:---|
| `SPEC_github_public_switch.md` | brainstorming 確定設計仕様 (Q1-Q4 + 4 sections、env hint 追加 §4 extension) | Claude Code 向け / プロジェクト閲覧者向け |
| `PLAN_github_public_switch.md` | writing-plans 出力の段階的実装計画 (Task 1-6 + Verification) | 実装エージェント向け |
| `SECRET_SCAN_REPORT.md` | Public 切替**直前**の gitleaks 再 scan 結果 (Day18 後 + Day19 commits 含む) | 公開後の audit trail |
| `DAY19_LESSONS_LEARNED.md` | Day19 全 commits の経緯 + 教訓 D19-1+ | プロジェクト閲覧者向け |
| `README.md` | 本書 | プロジェクト閲覧者向け |

## Day19 の特徴

Day18 で確立された **Phased 戦略 (D18-3)** の Phase 2 (Public 切替) を完了. Day9 で確立された **brainstorming → SPEC → writing-plans → 実行 (Inline Execution / controller 直接)** の 4 段階フローを 6 度目の本格適用. fixture work (Day11/15/16/17) や Private push (Day18) と同様に **code 改修ゼロ**.

## 達成事項 (7 commits)

| 順 | commit | 種別 | 達成 |
|:---:|:---:|:---|:---|
| (前) | `40f5b2d` | docs(spec) | Day19 SPEC archive (404 行、11 章) |
| (前) | `8baa81b` | docs(spec) | SPEC §4 extension (env hint 追加 + §4.4 安全性確認) |
| (前) | `<hash>` | docs(plan) | Day19 PLAN archive |
| 1 | `<hash>` | docs(license) | LICENSE (MIT) 新規追加 (Phase 1) |
| 2 | `<hash>` | docs(changelog) | CHANGELOG.md Day8-18 milestone summary 追加 (Phase 2) |
| 3 | `<hash>` | docs(readme) | README badges + TOC + env hint + License + Acknowledgments (Phase 3) |
| 4 | `<hash>` | docs(security) | SECRET_SCAN_REPORT.md (公開直前再 scan、Phase 4a) |
| Phase 4b | (commit なし) | external | gh repo edit --visibility public + topics 6 個追加 |
| 5 | (本 commit) | docs(sessions) | Day19 archive (README + LESSONS) (Phase 5) |

main branch: 75 → **<N>** + 本 commit で **<N+1> commits** (Day18 末 → Day19 末、+<delta>).
test 健全性: 97 passed / 1 skipped (不変、code 改変なし).
GitHub: ✅ **PUBLIC**、License: MIT、Topics: 6 個.

## Day7 §9.3 残タスクの達成状況 (Day19 末)

| タスク | 状態 (Day19 末) | commit / 備考 |
|:---|:---:|:---:|
| Vancouver golden fixture | ✅ Day11 | `fe38298` |
| Day9 (Z) 未解決 2 件 MEDLINE 調査 | ✅ Day13 | `a2ee5ae` |
| Day13 §6 案 A: 3 分類 audit logic | ✅ Day15 | `132ffab` |
| APA 系 golden fixture | ✅ Day16 | `c35211f` 系列 |
| Cell 系 golden fixture | ✅ Day17 | `94478fe` 系列 |
| GitHub remote + push (Private→Public) | ✅ Day18-19 | Phased 2 段階完了 |
| MCP/hook 経由 Stage 3 配線 | ⏳ Day20+ | |

→ Day7 §9.3 long-term task 7 件中 **6 件完了**. 残 1 件 (MCP 配線) は Day20+.

## GitHub 上の現状 (Day19 末)

| 項目 | 値 |
|:---|:---|
| Owner | hikataya01-netizen |
| Repo name | pubmed-reference-resolver |
| URL | https://github.com/hikataya01-netizen/pubmed-reference-resolver |
| Visibility | **PUBLIC** |
| Default branch | main |
| Pushed commits | <N+1> |
| License | MIT (sidebar 自動表示) |
| Topics | pubmed / peer-review / claude-skill / medical-references / bibliographic-audit / reference-validation |
| README badges | 3 個 (tests + License: MIT + Python 3.11+) |
| Remote URL (local) | https://github.com/hikataya01-netizen/pubmed-reference-resolver.git (HTTPS + gh token) |
| CI workflow | tests.yml (Python 3.11/3.12/3.14) — 各 push 時に自動実行 |

## 関連記録

完全な session 記録は別途以下に保管 (本リポジトリ外):
- `pubmed-reference-resolver-integration-chat-day19.md` (Day19 の完全記録、予定)
- `pubmed-reference-resolver-integration-chat-day{1,...,18}.md` (前日記録)

## 利用方法

### Day20 以降の参照

Day19 で確立された Public 化された repo は、Day20+ の MCP 配線 や Issue/PR template 配置等の外部 collaboration 関連タスクの基盤となる. `DAY19_LESSONS_LEARNED.md` §6 (残存タスク) を参照.

## ディレクトリ命名規約

`docs/sessions/dayN/` 形式 (Day6 で確立、Day7-19 で継続). Day20 セッション完了後は `docs/sessions/day20/` が追加される予定.

---

**作成日**: 2026-05-18 (Day19 クロージング時)
**メンテナ**: 片山英樹 (Hideki Katayama)
```

⚠️ `<hash>`, `<N>`, `<delta>` は Phase 1-4 完了時の実値で置換.

- [ ] **Step 2: Day19 DAY19_LESSONS_LEARNED.md を作成**

`docs/sessions/day19/DAY19_LESSONS_LEARNED.md` に以下を書き込む (Day18 と同型構造):

```markdown
# Day19 LESSONS LEARNED

**Day19 セッション (2026-05-18)**: GitHub Public 切替 (Phased 戦略 Phase 2 完了) + LICENSE + CHANGELOG + README polish

---

## 1. セッション概要

### 1.1 背景

Day18 末時点で Phased 戦略の Phase 1 (Private push) を完了. ユーザーは Day19 task として **(1) Public 切替 (推奨)** を選択 (Day18 LESSONS §7 パターン 1).

### 1.2 brainstorming 段階 (Q1-Q4)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | LICENSE 種別 | MIT License |
| Q2 | CHANGELOG 更新 scope | Day8-18 milestone summary (~60 行) |
| Q3 | README full restructure scope | badges + TOC + License + Acknowledgments (~30 行) |
| Q4 | visibility 変更タイミング | 全 docs 更新 + push 完了後 (安全側) |

ユーザーからの追加質問「env ファイルの扱いはどうなっていますか」を契機に SPEC §4 を extension (env install hint 追加 + §4.4 安全性確認 section 追加).

### 1.3 SPEC (commits `40f5b2d` + `8baa81b`)

`docs/sessions/day19/SPEC_github_public_switch.md` を archive. 11 章構成 (背景・アーキテクチャ・LICENSE+CHANGELOG・README 拡充・public switch protocol・commit 計画・完了条件・Out of Scope・工数・参照).

### 1.4 PLAN (commit `<hash>`)

`docs/sessions/day19/PLAN_github_public_switch.md` を archive. Task 1-6 + Verification で構成. Day18 PLAN を template に Day19 差分中心に再構成.

---

## 2. 実装段階の経緯 (5 commits + 外部操作)

### Phase 1: LICENSE (MIT) 配置 (commit `<hash>`)

- Task 1 (controller 直接実行): `LICENSE` ファイルを repo root に SPDX 標準テキスト (22 行) で配置. Copyright (c) 2026 Hideki Katayama.

### Phase 2: CHANGELOG 更新 (commit `<hash>`)

- Task 2 (controller 直接実行): `CHANGELOG.md` line 9 に新規 `[Unreleased] - 2026-05-18` section を挿入 (~60 行). 既存 Day7-era section はそのまま下に保持. v0.1.0 tag は Day20+.

### Phase 3: README 拡充 (commit `<hash>`)

- Task 3 (controller 直接実行): 4 箇所修正 ((a) badges + TOC / (c-pre) env install hint / (b) License section / (c) Acknowledgments section). 134 → 169 行.

### Phase 4a: gitleaks 公開直前再 scan (commit `<hash>`)

- Task 4 (controller 直接実行): `gitleaks detect` で全 <N> commits を scan、Finding count 0 確認. 手動 grep 5 patterns 全 clean. `docs/sessions/day19/SECRET_SCAN_REPORT.md` を作成 (Day18 と差分対比表 + env file 取扱い再確認 section 含む).

### Phase 4b: Public 切替 + topics 追加 (commit なし)

- Task 5 (controller 直接実行、外部操作):
  - `gh repo edit --visibility public --accept-visibility-change-consequences` で公開化
  - `gh repo edit --add-topic ...` で 6 topics (pubmed / peer-review / claude-skill / medical-references / bibliographic-audit / reference-validation) 追加
  - `gh repo view --json` で公開状態確認 (visibility=PUBLIC、licenseInfo=MIT、topics=6 件)
  - 匿名ブラウザで readability 確認

### Phase 5: Day19 archive (本 commit)

- Task 6 (controller 直接実行): README + LESSONS archive.

---

## 3. 設計判断と検証

### 3.1 MIT License 選定の根拠

医学/アカデミック OSS の主流 (pytest, requests, FastAPI 等). 短い (22 行)、shimple、commercial use 可、modification 可、attribution 要求のみ. Apache 2.0 / GPL v3 / CC BY 4.0 と比較して **学術系 collaboration の摩擦最小**.

### 3.2 Phased 戦略 (Phase 1 → Phase 2) の効果

Day18 で前倒し準備 (Private push + secret scan + .gitignore + README 一次更新) が完了済だったため、Day19 では **公開化に直接 relevant な追加事項のみ** (LICENSE + CHANGELOG + README polish + visibility 変更) で完了可能. もし Day18 を skip して Day19 で全部実施していたら ~5h の大型セッションになっていた見込.

### 3.3 env file 取扱い確認の触発

ユーザー質問「env ファイルの扱いはどうなっていますか」が SPEC §4 extension の触発. 確認結果 (実 .env は gitignored + never committed + Day18 scan で 0 leaks) は安全側で問題なしだったが、README install hint (cp .env.example .env 5 行) 追加で公開後 onboarding 時間を短縮.

---

## 4. 実機検証結果

### 4.1 gitleaks 再 scan (Phase 4a)

| Metric | 値 |
|:---|---:|
| gitleaks version | 8.30.1 |
| Scan commits | <N> (Day18 SECRET_SCAN_REPORT 時 68 から +<N-68>) |
| Bytes scanned | ~3.9 MB |
| Findings | **0** ✅ (`.gitleaksignore` の Day8 test fixture suppression 継続有効) |
| 手動 grep findings | 0 (Day18-19 PLAN/SPEC self-reference + email + grep regex のみ) |

### 4.2 GitHub repo 状態 (Phase 4b 完了後)

| 項目 | 値 |
|:---|:---|
| Owner | hikataya01-netizen |
| Repo name | pubmed-reference-resolver |
| Visibility | **PUBLIC** ✅ (Day18 PRIVATE から切替) |
| URL | https://github.com/hikataya01-netizen/pubmed-reference-resolver |
| License (SPDX detection) | MIT License |
| Topics | 6 個 (pubmed / peer-review / claude-skill / medical-references / bibliographic-audit / reference-validation) |
| README badges | 3 個 green (tests / License: MIT / Python 3.11+) |
| Default branch | main |
| Pushed commits | <N+1> |

### 4.3 CI 動作確認

Day19 中の各 push 時に GitHub Actions が自動 trigger され、Python 3.11/3.12 で 97 tests 全 pass を継続維持.

---

## 5. 教訓 (D19-1, D19-2)

### 5.1 D19-1: Phased 戦略の Phase 分割効果

**事象**: Day18 で Phase 1 (Private push + secret scan + .gitignore + README 一次更新) を前倒し、Day19 で Phase 2 (LICENSE + CHANGELOG + README polish + visibility 変更) のみに集中.

**学び**: 公開化のような不可逆操作は、**事前準備 Phase (Private で問題発見・修正) と公開 Phase (LICENSE 追加 + visibility 変更) を明示的に分割**することで:
- 各 Phase の責務が明確 (事前準備 vs 公開準備)
- 各 Phase で問題発生しても次 Phase に持ち越さない
- 公開 Phase は実質 ~2.5h で完了可能

**適用範囲**: PyPI 公開、Docker Hub 公開、各種パッケージレジストリ公開の workflow にも同型適用可能.

### 5.2 D19-2: ユーザー質問起源の SPEC extension

**事象**: brainstorming Q1-Q4 + design 4 sections 全承認後、ユーザーが「env ファイルの扱いはどうなっていますか」と追加質問. controller が confirm scan 実施 → SPEC §4 に extension commit (8baa81b) で env install hint 追加 + §4.4 安全性確認 section 追加.

**学び**: brainstorming 完了後でも、ユーザーからの質問は SPEC 不足の指摘. **SPEC を amend するのではなく separate commit で extension** する pattern が:
- 元 SPEC の整合性を維持
- extension の経緯が commit log で追跡可能
- ユーザー貢献を可視化

**適用範囲**: 将来の SPEC 作成でも同型 pattern (元 SPEC → ユーザー追加質問 → SPEC extension commit) が有効.

---

## 6. 残存タスク (Day20 以降)

### 6.1 Day7 §9.3 long-term task の達成状況 (Day19 末)

| タスク | 状態 | 残し方 |
|:---|:---:|:---|
| Vancouver golden fixture | ✅ Day11 | — |
| Day9 (Z) 未解決 2 件 MEDLINE 調査 | ✅ Day13 | — |
| Day13 §6 案 A: 3 分類 audit logic | ✅ Day15 | — |
| APA 系 golden fixture | ✅ Day16 | — |
| Cell 系 golden fixture | ✅ Day17 | — |
| GitHub remote + push (Private→Public) | ✅ Day18-19 | — |
| **MCP/hook 経由 Stage 3 配線** | ⏳ Day20+ | 設計議論大、複数セッション |

### 6.2 Day19 が生成した新規候補

- [ ] **v0.1.0 tag 付与** (CHANGELOG `[Unreleased] - 2026-05-18` → `[0.1.0]` 移行 + GitHub Release 作成)
- [ ] **homepageUrl 設定** (PyPI 公開 / Read the Docs 公開時)
- [ ] **Issue / PR template** (collaboration 受入準備)
- [ ] **Branch protection rule** (main への direct push 禁止)
- [ ] **CONTRIBUTING.md / CODE_OF_CONDUCT.md** (Public OSS 規範)
- [ ] **SSH 認証 cleanup** (Day18 D18 起源、SSH passphrase 設定見直し)
- [ ] **AI 工学 book/web refs 三分類改修** (Day17 D17 起源)

### 6.3 Day20+ 推奨着手順

1. **MCP/hook 経由 Stage 3 配線** (Day7 §9.3 残最後の 1 件、最高優先度、複数セッション)
2. **AI 工学 book/web refs 三分類改修** (Day17 起源、実使用品質向上、~2h)
3. **v0.1.0 tag + GitHub Release** (公開化記念、~1h)
4. **CONTRIBUTING.md / Issue PR template** (collaboration 受入準備、~2h)

---

## 7. 次セッション再開時のプロンプトテンプレート

### パターン 1: Day20 として MCP/hook 経由 Stage 3 配線 (推奨)

```
Day20 として、Day7 §9.3 long-term task 残最後の 1 件である Stage 3
(Claude UI 起動の自動配線) を実装します. MCP server / hook 経由で
Claude Code → ローカル command → docx 入力 → audit 出力 → Claude UI
への結果返却パイプラインを設計. 議論大規模のため SPEC 段階まで複数
セッション覚悟. brainstorming で進めてください.
```

### パターン 2: Day20 として AI 工学 book/web refs 三分類改修

```
Day20 として、Day17 cell_45refs で発生した三分類 A 多発 (14/15) の
false positive 問題を改修します. AI 工学領域の book chapter / web page
/ industry report 系 references を「真の捏造 (A)」ではなく「MEDLINE
非収録 (B)」に振り直す logic を crossref_check / three_class_classifier
に追加. brainstorming → SPEC → TDD で進めてください.
```

### パターン 3: Day20 として v0.1.0 tag + GitHub Release

```
Day20 として、Day19 で Public 切替済の pubmed-reference-resolver に
v0.1.0 tag を付与し、GitHub Release を作成します. CHANGELOG.md の
[Unreleased] - 2026-05-18 section を [0.1.0] に移行、git tag v0.1.0 +
push、gh release create で Release notes を生成. ~1h.
```

---

**記録完了日**: 2026-05-18 (Day19)
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day19 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day19.md` (Claude Opus 作成予定)
**ステータス**: Day19 archive 完成、Day20 着手準備完了 (3 パターンプロンプトあり)
```

⚠️ `<N>`, `<hash>` 等の placeholder は Phase 1-4 完了時の実値で置換.

- [ ] **Step 3: Phase 5 commit**

```bash
git add docs/sessions/day19/PLAN_github_public_switch.md \
        docs/sessions/day19/README.md \
        docs/sessions/day19/DAY19_LESSONS_LEARNED.md && \
git commit -m "$(cat <<'EOF'
docs(sessions): archive day19 github public switch session

Day19 セッション完了に伴う archive:
- README.md: day19/ index, Day7 §9.3 残タスク達成状況 6/7 表 (Day18-19
  で Private→Public 完了), GitHub 上の状態 (Public + License: MIT +
  6 topics + 3 badges + <N+1> commits) 記録
- DAY19_LESSONS_LEARNED.md: 全 7 commits 経緯 + 教訓 D19-1, D19-2
  (Phased 戦略の Phase 分割効果 + ユーザー質問起源の SPEC extension)
- PLAN_github_public_switch.md: writing-plans 出力の実装計画

主成果:
- GitHub Public 切替完了 (visibility=PUBLIC、licenseInfo=MIT、
  topics=6 個)
- MIT License を repo root に配置
- CHANGELOG.md に Day8-18 milestone summary を追加 (52→89 tests 推移
  表含む)
- README を 4 箇所拡充 (badges + TOC + env install hint + License +
  Acknowledgments、134→169 行)
- Phase 4a gitleaks 再 scan で公開直前 clean 確認 (Day19 含む全
  commits)

Day7 §9.3 long-term task 7 件中 6 件完了. 残 1 件 (MCP 配線) は Day20+.

副次タスク残 (Day20+ 候補):
- v0.1.0 tag + GitHub Release
- CONTRIBUTING.md / Issue PR template
- AI 工学 book/web refs 三分類改修
- SSH 認証 cleanup

main branch: 75 → <N+1> (+<delta>), test: 97 passed / 1 skipped (不変).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)" && \
echo "---" && \
git push origin main 2>&1 | tail -3
```

---

## Verification (全 Task 完了後の最終確認)

- [ ] **V1: 全 test pass (regression なし)**

```bash
python3 -m pytest tests/ -v 2>&1 | tail -3
```
Expected: **97 passed, 1 skipped** (code 改変なしのため Day18 末と同一).

- [ ] **V2: SPEC §7 12 完了条件すべて満たす**

```bash
echo "[1] LICENSE 存在:" && head -1 LICENSE
echo "[2] CHANGELOG 2026-05-18:" && grep "2026-05-18" CHANGELOG.md | head -1
echo "[3] README badges >=3:" && grep -c "badge.svg\|shields.io" README.md
echo "[4] README TOC:" && grep "Table of Contents" README.md
echo "[5] README License section:" && grep "^## License$" README.md
echo "[6] README Acknowledgments:" && grep "^## Acknowledgments$" README.md
echo "[7] SECRET_SCAN_REPORT:" && ls docs/sessions/day19/SECRET_SCAN_REPORT.md
echo "[8] gitleaks clean:" && jq 'length == 0' /tmp/gitleaks_report_day19.json
echo "[9] GitHub PUBLIC:" && gh repo view hikataya01-netizen/pubmed-reference-resolver --json visibility --jq '.visibility'
echo "[10] License MIT:" && gh repo view hikataya01-netizen/pubmed-reference-resolver --json licenseInfo --jq '.licenseInfo.spdxId'
echo "[11] Topics >=6:" && gh repo view hikataya01-netizen/pubmed-reference-resolver --json repositoryTopics --jq '.repositoryTopics | length'
echo "[12] Day19 archive 5 files:" && ls docs/sessions/day19/ | wc -l
```

Expected: 全 12 条件 OK (具体的に: `MIT License` / `## [Unreleased] - 2026-05-18` / `3` / `## Table of Contents` / `## License` / `## Acknowledgments` / file path / `true` / `PUBLIC` / `MIT` / `6` / `5`).

- [ ] **V3: commit count + GitHub push 同期確認**

```bash
echo "Day19 commits since Day18 末 (c9dce0b):" && git log c9dce0b..HEAD --oneline | wc -l
echo "local HEAD:" && git rev-parse --short HEAD
echo "remote HEAD:" && git ls-remote origin main 2>/dev/null | awk '{print substr($1, 1, 7)}'
```

Expected: Day19 中の commit 数 ~7、local HEAD == remote HEAD.

- [ ] **V4: final git status**

```bash
git status
```
Expected: `On branch main / Your branch is up to date with 'origin/main' / nothing to commit, working tree clean`.

---

## Notes for Implementing Agent

- **Controller-direct 推奨**: Day19 は外部システム操作 (gitleaks 実行、`gh repo edit` 等) と単純 docs 編集が中心. Day18 と同様 controller 直接実行が効率的. subagent dispatch overhead 不要.
- **commit を生成しない Phase**: Phase 4b (visibility 変更 + topics 追加) は外部操作で git commit を生成しない. Day18 と同型 pattern.
- **gitleaks dir 注意 (Day18 D18-1 継承)**: 必ず `cd /Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver && ...` で実行. home dir からの実行は空 scan になる.
- **匿名ブラウザ確認**: Public 切替後の readability 確認は **incognito / プライベートブラウズ** で実施推奨. 認証ブラウザでは cache の影響あり.
- **CHANGELOG 挿入順序**: 新規 `[Unreleased] - 2026-05-18` を **既存 `[Unreleased] - 2026-04-23` の前**に挿入. Keep a Changelog 規約では新しい entry が上に来る.
- **README 修正順序**: (a) → (c-pre) → (b) → (c) の順で Edit すると line shift の影響が最小. (a) で冒頭挿入、(c-pre) で中間 install section 修正、(b)(c) で末尾追加.
- **`.env.example` は既に tracked**: 公開化対象として追加変更不要. Day19 では README install hint で利用方法を明示するのみ.
- **v0.1.0 tag は Day20+**: 本 SPEC scope 外. CHANGELOG は `[Unreleased]` のまま維持し、Day20+ で tag 付与時に `[0.1.0]` に rename.
