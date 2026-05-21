# SPEC: GitHub Public 切替 (Day19)

**作成日**: 2026/05/18 (Day19 brainstorming 完了時)
**著者**: Claude Code (Sonnet 4.6) / 承認: 片山英樹
**位置付け**: Day7 §9.3 long-term task 残のうち副次タスクとして発生した「Public 切替」を **Phased 戦略の Phase 2** として完了. Day18 で Private push + secret scan + .gitignore + README 一次更新を完了済 (Phase 1).
**前提**: Day18 末 (commit `c9dce0b`) で main branch 75 commits、4 fixture、97 tests、GitHub `hikataya01-netizen/pubmed-reference-resolver` (PRIVATE) に push 済、CI success 確認済

---

## 1. 背景と目的

### 1.1 Phased 戦略における位置付け

`docs/sessions/day18/DAY18_LESSONS_LEARNED.md` で確立された **Phased 戦略 (D18-3)**:

| Phase | 内容 | 状態 |
|:---:|:---|:---:|
| Phase 1 | Private push + secret scan + .gitignore + README 一次更新 | ✅ Day18 |
| **Phase 2** | **LICENSE + CHANGELOG + README polish + Public 切替** | ⏳ **Day19** (本 SPEC) |

Day7 §9.3 long-term task 7 件中 6 件完了 (Day18 末). Phase 2 は long-term task の本体ではなく副次成果として発生したが、Phase 1 で前倒し準備が完了しているため Day19 で低コストに完了可能.

### 1.2 目的

1. **Public 公開化**: MIT License 適用で外部からの fork / clone / issue 提出を受入可能化
2. **License 明示**: GitHub side-bar の "About" + README の License section で license が一見明確
3. **CHANGELOG 整備**: Day1-7 era のみの記述を Day8-18 milestone summary で補完し、release-readiness を確保
4. **discoverability 向上**: GitHub topics 追加で `pubmed` / `peer-review` 等の関連検索からの到達性向上
5. **再 secret scan**: Day18 以降の追加 commit (Day19 docs 含む) について追加 scan で公開直前の安全性確認

### 1.3 設計判断の経緯 (brainstorming 質問)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | LICENSE 種別 | **MIT License** |
| Q2 | CHANGELOG 更新 scope | **Day8-18 milestone summary (~60 行)** |
| Q3 | README full restructure scope | **badges + TOC + License + Acknowledgments (~30 行)** |
| Q4 | visibility 変更タイミング | **全 docs 更新 + push 完了後に変更 (安全側)** |

---

## 2. Architecture & ファイル配置

### 修正・新規対象 (5 ファイル)

| ファイル | 種別 | 修正内容 |
|:---|:---|:---|
| `LICENSE` | **新規** | MIT License (Copyright (c) 2026 Hideki Katayama) |
| `CHANGELOG.md` | 修正 | Day8-18 milestone summary を新規 `[Unreleased] - 2026-05-18` section に追加 (~60 行、既存 Day7 era section は下に維持) |
| `README.md` | 修正 | License badge + Python version badge + Table of Contents + ## License section + ## Acknowledgments (~30 行) |
| `docs/sessions/day19/SECRET_SCAN_REPORT.md` | 新規 | 公開直前 gitleaks 再 scan 結果 (Day18 以降の追加 commit 含む) |
| `docs/sessions/day19/{SPEC,PLAN,README,DAY19_LESSONS_LEARNED}.md` | 新規 | Day19 archive 4 ファイル |

### 改変なし (確認のみ)

- production code (`main.py`, `mdpi_parser.py`, `crossref_check.py`, `nlm_catalog_check.py`, `three_class_classifier.py`, `journal_audit.py`)
- 全 test ファイル (97 passed 維持)
- 全 fixture ファイル
- `.gitignore` / `.gitleaksignore` (Day18 で最終化済)
- 既存 docs (Day7-18 archive)

### 外部システム変更

- `gh repo edit hikataya01-netizen/pubmed-reference-resolver --visibility public --accept-visibility-change-consequences`
- `gh repo edit ... --add-topic pubmed --add-topic peer-review --add-topic claude-skill --add-topic medical-references --add-topic bibliographic-audit --add-topic reference-validation` (6 topics)
- homepage URL は **未設定** (PyPI / Read the Docs 公開時に追加、Day20+)

---

## 3. LICENSE + CHANGELOG 詳細

### 3.1 LICENSE (新規、MIT)

`LICENSE` file を repo root に配置. 内容は SPDX 標準テキストの逐語コピー:

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

注意点:
- 著作者名: `Hideki Katayama` (英語名、GitHub 公開を想定)
- 著作年: `2026` (CHANGELOG 既存 section `## [Unreleased] - 2026-04-23` と整合)
- fixture (PMC OA 抽出 reference data) は MIT 適用範囲外 (factual data + CC BY 4.0 帰属表示は各 fixture README で個別実施済)

### 3.2 CHANGELOG.md 更新 (Day8-18 milestone summary)

既存 `## [Unreleased] - 2026-04-23` セクション (Day1-7 era) を維持しつつ、その**前**に新規 `## [Unreleased] - 2026-05-18` セクションを挿入. 内容構成:

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
- **USAGE_QUICKSTART** 1.0 → 1.5 (Day10/14/15/17 各 bump): SKILL_PACKAGE/references/USAGE_QUICKSTART.md に 3 分類 audit / 4 fixture 情報を追記.
- **GitHub Private push** (Day18): hikataya01-netizen/pubmed-reference-resolver、CI 動作確認、gitleaks-based secret scan protocol 確立.

### Changed (変更)

- **env loader** (`main.py:load_env_files`, Day8): 空値環境変数を上書き対応 (harness サブプロセス継承時の空値問題に対処).
- **SKILL.md / USAGE_QUICKSTART** (Day14-17): 「捏造引用 = PubMed 未ヒット」の単純化記述を 3 分類体系に書換.
- **`.gitignore`** (Day16/18): `.cache/`, `.DS_Store` 追加.

### Fixed (修正)

- **MDPI parser <collab> 対応** (Day16, `tools/build_apa_fixture.py`): 組織著者 `<collab>` 要素から author を抽出可能に. PMC OA refs 28/37 の空抽出問題を解決.

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

→ `## [Unreleased] - 2026-04-23` (Day1-7) はそのまま下に残る. v0.1.0 tag は本 SPEC scope 外 (Day20+ で別途).

---

## 4. README.md 拡充詳細

### 4.1 修正範囲 (134 → 約 164 行、+30 行)

3 箇所追加 + 1 箇所修正:

#### (a) ファイル冒頭: badges 拡充 + TOC 追加

旧 (Day18 末、line 1-5):
```markdown
# pubmed-reference-resolver

[![tests](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml/badge.svg)](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml)

査読対象論文の References セクション...
```

新:
```markdown
# pubmed-reference-resolver

[![tests](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml/badge.svg)](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

査読対象論文の References セクション...

## Table of Contents

- [主な機能](#主な機能)
- [インストール](#インストール)
- [使用方法](#使用方法)
- [テスト](#テスト)
- [ゴールドスタンダード fixture (4 系統)](#ゴールドスタンダード-fixture-4-系統)
- [プロジェクト構成](#プロジェクト構成)
- [License](#license)
- [Acknowledgments](#acknowledgments)
```

#### (b) ファイル末尾: License section 追加

134 行末に append:
```markdown

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Hideki Katayama
```

#### (c) ファイル末尾: Acknowledgments section 追加 (License の次)

```markdown

## Acknowledgments

このプロジェクトは以下の OSS と公開リソースに依存する:

- **NCBI E-utilities** (PubMed / PMC / NLM Catalog) — bibliographic information retrieval
- **Crossref REST API** — DOI 実在確認 (Day15 で導入された 3 分類 audit logic で使用)
- **Anthropic Claude Sonnet 4.6** — LLM-path での reference 構造化
- **PMC Open Access subset** — fixture data (CC BY 4.0 採用 3 系統 = vancouver/apa/cell). 各 fixture の `tests/fixtures/*/README.md` で source paper citation を明示.

開発期間中 (Day1-19) は **Claude Code (Sonnet 4.6)** および **Claude Opus 4.7 (1M context)** が共同作業者として参画した. 全 commit の `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` trailer はその記録.
```

### 4.2 修正なし (Day18 状態維持)

- 主な機能、インストール、使用方法、テスト、ゴールドスタンダード fixture、プロジェクト構成 — Day18 で既に Day17 末状態に更新済

### 4.3 修正後 line count 想定

| section | 行数 |
|:---|---:|
| 既存 (Day18 末) | 134 |
| (a) badges 2 個 + TOC + 空行 | +14 |
| (b) License section | +5 |
| (c) Acknowledgments section | +11 |
| **合計** | **~164** |

---

## 5. Public switch protocol (Phase 4 で実施)

### 5.1 Step 構成

#### Step 1: 追加 gitleaks scan (公開直前の最終確認)

```bash
gitleaks detect --source . --verbose \
  --report-format json \
  --report-path /tmp/gitleaks_report_day19.json
```

Expected: `INF X commits scanned` (X >= 80、Day19 commits 含む) + `INF no leaks found` + finding count 0.

⚠️ leak 検出時: **公開中止**、`git filter-repo` で history rewrite → 再 scan → 公開.

#### Step 2: SECRET_SCAN_REPORT.md 更新

`docs/sessions/day19/SECRET_SCAN_REPORT.md` に Day18 SECRET_SCAN_REPORT を template として複写、Day19 値で更新:
- scan 範囲: `ea3d604` .. 最新 commit (Day19 docs commit 後)
- commit count: 80+
- 新規追加 commit (LICENSE, CHANGELOG 更新, README badges) も clean であることを確認

#### Step 3: docs 全 commit + push 完了確認

```bash
git status                                # working tree clean
git log --oneline origin/main..HEAD       # 空 (全 push 済)
```

#### Step 4: Visibility 変更

```bash
gh repo edit hikataya01-netizen/pubmed-reference-resolver \
  --visibility public \
  --accept-visibility-change-consequences
```

Expected: silent 成功 (出力なし).

⚠️ `--accept-visibility-change-consequences` flag は GitHub の確認 prompt を bypass. 公開化の不可逆性を SPEC 全体で議論済前提.

#### Step 5: Topics 追加

```bash
gh repo edit hikataya01-netizen/pubmed-reference-resolver \
  --add-topic pubmed \
  --add-topic peer-review \
  --add-topic claude-skill \
  --add-topic medical-references \
  --add-topic bibliographic-audit \
  --add-topic reference-validation
```

Topics 選定根拠:
- `pubmed`: 主機能 (PubMed 逆引き)
- `peer-review`: 用途 (査読支援)
- `claude-skill`: Claude Code との統合 (SKILL.md 配備)
- `medical-references`: domain (医学文献)
- `bibliographic-audit`: 監査機能 (journal_audit, three_class)
- `reference-validation`: 引用検証

GitHub は最大 20 topics 許容、初版は 6 件で polish 余地を残す.

#### Step 6: Public 状態確認

```bash
gh repo view hikataya01-netizen/pubmed-reference-resolver \
  --json visibility,description,homepageUrl,repositoryTopics,licenseInfo | jq
```

Expected:
```json
{
  "visibility": "PUBLIC",
  "description": "PubMed reference resolver / 査読支援スキル...",
  "homepageUrl": "",
  "repositoryTopics": [{"name": "pubmed"}, ...],
  "licenseInfo": {"name": "MIT License", "spdxId": "MIT"}
}
```

licenseInfo は GitHub side-bar の "About" section に License: MIT として表示される (Day19 公開後の visible artifact).

#### Step 7: 匿名ブラウザでの readability 確認

```bash
gh repo view --web
```

ブラウザで以下を確認 (認証ログアウト推奨):
- README badges 全 3 個 green (tests / License: MIT / Python 3.11+)
- TOC links が anchor 動作
- License sidebar に MIT 表示
- Topics chips が repository 上部に表示

---

## 6. Commit 計画 (5 commits + 2 pre = 7)

| 順 | commit 種別 | Phase | 内容 |
|:---:|:---|:---:|:---|
| (前) | `docs(spec)` | — | Day19 SPEC archive (本 commit) |
| (前) | `docs(plan)` | — | Day19 PLAN archive |
| 1 | `docs(license)` | 1 | LICENSE (MIT) 新規追加 |
| 2 | `docs(changelog)` | 2 | CHANGELOG.md に Day8-18 milestone summary 追加 |
| 3 | `docs(readme)` | 3 | README に badges + TOC + License + Acknowledgments 追加 |
| 4 | `docs(security)` | 4a | Day19 SECRET_SCAN_REPORT.md 追加 (公開直前 scan) |
| Phase 4b | (commit なし) | 4b | gh repo edit --visibility public + topics 追加 |
| 5 | `docs(sessions)` | 5 | Day19 archive (README + LESSONS) |

→ 合計 **5 commits + 2 pre = 7 commits** (Day18 と同等規模).

---

## 7. 完了条件 (12 項目)

| # | 条件 | 確認方法 |
|:---:|:---|:---|
| 1 | `LICENSE` ファイル存在 (MIT) | `head -1 LICENSE` = "MIT License" |
| 2 | `CHANGELOG.md` に Day8-18 entry 追加 | `grep "2026-05-18" CHANGELOG.md` 存在 |
| 3 | README badges 3 個揃う | `grep -c "badge.svg\|shields.io" README.md` >= 3 |
| 4 | README TOC 存在 | `grep "Table of Contents" README.md` 存在 |
| 5 | README License section 存在 | `grep "## License" README.md` 存在 |
| 6 | README Acknowledgments section 存在 | `grep "## Acknowledgments" README.md` 存在 |
| 7 | Day19 SECRET_SCAN_REPORT.md 存在 (Day19 commits 含む再 scan) | file 存在 + Finding count 0 記載 |
| 8 | gitleaks 再 scan clean | `jq 'length == 0' /tmp/gitleaks_report_day19.json` |
| 9 | GitHub repo visibility PUBLIC | `gh repo view ... --json visibility --jq '.visibility'` = "PUBLIC" |
| 10 | GitHub repo licenseInfo MIT | `gh repo view ... --json licenseInfo --jq '.licenseInfo.spdxId'` = "MIT" |
| 11 | GitHub repo topics >= 6 | `gh repo view ... --json repositoryTopics --jq '.repositoryTopics \| length'` >= 6 |
| 12 | Day19 archive 5 files (SPEC + PLAN + SECRET_SCAN + README + LESSONS) | `ls docs/sessions/day19/ \| wc -l` = 5 |

---

## 8. 工数見積もり

| Phase | 内容 | 見積 |
|:---:|:---|---:|
| Pre | SPEC + PLAN archive | 25min |
| Phase 1 | LICENSE 配置 + commit | 5min |
| Phase 2 | CHANGELOG 更新 + commit | 30min |
| Phase 3 | README 修正 + commit | 30min |
| Phase 4a | gitleaks 再 scan + SECRET_SCAN_REPORT 更新 + commit | 20min |
| Phase 4b | visibility 変更 + topics 追加 + 公開確認 (外部操作) | 15min |
| Phase 5 | Day19 archive 作成 + push | 25min |
| **合計** | | **~2.5h** |

---

## 9. 想定リスクと対応

| リスク | 確率 | 対応 |
|:---|:---:|:---|
| gitleaks 再 scan で新規 leak 検出 | 低 | 公開中止、原因対応、Day19 中断・延期 |
| visibility 変更後に意図せぬ情報露出 (search engine cache) | 低-中 | 公開直後の手動 url 確認、必要なら緊急 private 戻し (GitHub は visibility toggle 可能) |
| topics 上限超え or 名前不正 | 低 | gh CLI が validate、エラー時に topic 名 review |
| README badge URL 不正 | 低 | Day19 markdown preview で事前確認 |
| LICENSE 不一致 (author name 誤記等) | 低 | LICENSE 配置直後に内容確認、commit 前修正 |

---

## 10. Out of Scope (Day20+ 候補)

- **v0.1.0 tag 付与** + GitHub Release 作成 (CHANGELOG `[Unreleased]` → `[0.1.0]` 移行)
- **homepageUrl 設定** (PyPI 公開 / Read the Docs 公開時)
- **Issue / PR template** (collaboration 受入準備)
- **Branch protection rule** (main への direct push 禁止)
- **CONTRIBUTING.md / CODE_OF_CONDUCT.md**
- **SSH 認証 cleanup** (Day18 D18 から繰越)
- **AI 工学 book/web refs 三分類改修** (Day17 D17 起源)
- **MCP/hook 経由 Stage 3 配線** (Day7 §9.3 残最後の 1 件、Day20+)

---

## 11. 参照

- Day18 SPEC: `docs/sessions/day18/SPEC_github_private_push.md` (Phased 戦略 Phase 1)
- Day18 SECRET_SCAN_REPORT: `docs/sessions/day18/SECRET_SCAN_REPORT.md` (本 Day19 で update + 再 scan)
- Day18 LESSONS: `docs/sessions/day18/DAY18_LESSONS_LEARNED.md` §5.3 (D18-3 Phased 戦略の妥当性)
- 既存 CHANGELOG.md (Day7 era、Step 1-7 record)
- 既存 README.md (Day18 末状態、134 行)

---

**承認**: 片山英樹 (brainstorming Q1-Q4 + design 全 4 sections)
**次工程**: writing-plans skill で implementation plan を作成
