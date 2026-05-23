# SPEC: v0.1.0 tag + GitHub Release (Day21)

**作成日**: 2026/05/22 (Day21 brainstorming 完了時)
**著者**: Claude Code (Sonnet 4.6) / 承認: 片山英樹
**位置付け**: Day20 で **Day7 §9.3 long-term task 完全クローズ (7/7)** した公式 milestone として v0.1.0 semantic version tag + GitHub Release を作成
**前提**: Day20 末 (commit `b432c46`) で main branch 92 commits、4 fixture、100 tests passed / 1 skipped、GitHub PUBLIC 化済、MIT License

---

## 1. 背景と目的

### 1.1 Day20 完全クローズ後の milestone 化

Day20 で Day7 PHASE_0_VERIFICATION_REPORT §9.3 で定義された long-term task 7 件を全てクローズ:

| タスク | 達成 Day |
|:---|:---:|
| Vancouver golden fixture | Day11 |
| Day9 (Z) 未解決 2 件 MEDLINE 調査 | Day13 |
| Day13 §6 案 A: 3 分類 audit logic | Day15 |
| APA 系 golden fixture | Day16 |
| Cell 系 golden fixture | Day17 |
| GitHub remote + push (Private→Public) | Day18-19 |
| MCP/hook 経由 Stage 3 配線 | Day20 (認証) |

→ **Day1-20 の 21 セッションにわたる開発成果を semantic version `v0.1.0` として凍結** し、初の公式 release tag を作成.

### 1.2 目的

1. **公式 milestone 化**: Day7 §9.3 完全クローズという achievement を semantic version + GitHub Release で永続記録
2. **CHANGELOG.md 整備**: 既存 `[Unreleased] - 2026-05-18` (Day8-18) に Day20 改修を追記、`[0.1.0] - 2026-05-22` に rename、新規空 `[Unreleased]` section 挿入 (Keep a Changelog 規約準拠)
3. **GitHub Release 公開**: 見やすい release notes (主要ハイライト 6 件 + CHANGELOG link) で利用者の理解促進
4. **header コメントの更新**: 「v0.1.0 タグ付けは別タスクで実施予定」を「v0.1.0 は Day21 = 2026-05-22 でタグ付与済」に更新 (現状反映)

### 1.3 設計判断の経緯 (brainstorming 質問)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | v0.1.0 に Day20 改修も含めるか | **(含める) Day20 改修を CHANGELOG に追加して v0.1.0 にインクルード** |
| Q2 | GitHub Release notes のスタイル | **(要約 + CHANGELOG リンク)** |

---

## 2. Architecture & ファイル配置

### 修正対象 (1 ファイル)

| ファイル | 修正内容 |
|:---|:---|
| `CHANGELOG.md` | (Step A) 既存 `[Unreleased] - 2026-05-18` section に Day20 追加 entry (~25 行) (Step B) section header を `[0.1.0] - 2026-05-22` に rename + 新規空 `[Unreleased]` section 挿入 (~4 行) (Step C) header コメントの「v0.1.0 タグ付けは別タスクで実施予定」を「v0.1.0 は Day21 = 2026-05-22 でタグ付与済」に更新 |

### 新規作成 (Day21 archive 4 files)

| ファイル | 用途 |
|:---|:---|
| `docs/sessions/day21/SPEC_v0_1_0_release.md` | 本 SPEC |
| `docs/sessions/day21/PLAN_v0_1_0_release.md` | writing-plans 出力 |
| `docs/sessions/day21/README.md` | Day21 index |
| `docs/sessions/day21/DAY21_LESSONS_LEARNED.md` | Day21 末 archive |

### 外部システム変更

| 操作 | コマンド | 結果 |
|:---|:---|:---|
| Git tag 作成 (annotated) | `git tag -a v0.1.0 -m "v0.1.0 - Day1-20 統合スナップショット (Day7 §9.3 long-term task 完全クローズ)"` | ローカルに annotated tag 作成 |
| Tag push | `git push origin v0.1.0` | GitHub に tag 反映 |
| GitHub Release 作成 | `gh release create v0.1.0 --title "..." --notes-file /tmp/release_notes_v0.1.0.md` | Release notes 付き public release を GitHub に公開 |

### 改変なし

- production code 全般 (本 task は release 化のみ、code 変更なし)
- 全 test ファイル / 全 fixture (100 passed 維持)
- `README.md` / `LICENSE` / `SKILL.md` / `.gitignore` / `.gitleaksignore`

---

## 3. CHANGELOG.md 変更詳細

### 3.1 Step A: 既存 `[Unreleased] - 2026-05-18` section に Day20 改修を追記

"Day8-18 統合" section の `### Documentation` の後、`### Test 健全性推移` の前に以下を挿入:

```markdown
### Day20 追加 (2026-05-22)

**Day7 §9.3 long-term task 完全クローズ (7/7)** — Day20 で残最後 1 件 (Stage 3) を達成認証.

### Added (Day20)

- **3 helper 関数 in `three_class_classifier.py`** (Day20): `_detect_book()` / `_detect_conference()` / `_classify_via_nlm_only()`. DOI 欠落 case を 4 rule 順次評価に拡張.
- **`STAGE3_COMPLETION_NOTE.md`** (Day20): Day7 §9.3 残最後の 1 件 (MCP/hook 経由 Stage 3 配線) を SKILL.md 経由達成として認証.
- **3 unit tests** (Day20、`tests/test_three_class_classifier.py`): book / conference / NLM-only 各 rule の動作検証.

### Changed (Day20)

- **`three_class_classifier._classify_single`** (Day20): DOI 欠落 case を「即 A」から 4 rule 順次評価 (book → conference → NLM 検索 → A fallback) に変更. cell_45refs A 分類 14 → 1 (93% 減)、apa_45refs A 分類 4 → 0 (完全消失).
- **`main.py:synthesize_outputs`** (Day20): `unresolved_refs` に `is_book` / `raw_text` / `publisher` 3 fields を追加 (Phase 2 LLM 出力由来、Day20 改修の Rule 1 で利用).
- **`tests/fixtures/{cell,apa}_45refs/baseline_*`** (Day20): 三分類 baseline 再生成、`baseline_report.md` も自動更新.
- **`tests/fixtures/mdpi_149refs/expected_report.md`** (Day20): deterministic golden の三分類 sub-section も Day20 改修反映で再生成 (#4 A→unknown、#9/#19 A→B).
```

→ Test 健全性推移表 (Day19 で記載済) の Day19 末行はそのまま、Day20 末 = 100 passed を追加する形でも良いが、SPEC 範囲外として Day21 では追加しない (将来 v0.1.1 等の release で見直し).

### 3.2 Step B: section header rename + 新 `[Unreleased]` 挿入

```diff
- ## [Unreleased] - 2026-05-18
+ ## [Unreleased]
+
+ (Day21 以降の変更がここに記録される予定)
+
+ ## [0.1.0] - 2026-05-22

  ### Day8-18 統合: Vancouver Veto + 4 fixture + 3 分類 audit + GitHub 公開準備
```

### 3.3 Step C: header コメント更新

旧 (line 5-7):
```
形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠しており、
このプロジェクトは [セマンティックバージョニング](https://semver.org/lang/ja/) の採用を予定しています
(v0.1.0 タグ付けは別タスクで実施予定)。
```

新:
```
形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠し、
[セマンティックバージョニング](https://semver.org/lang/ja/) を採用する
(v0.1.0 は Day21 = 2026-05-22 でタグ付与済)。
```

### 3.4 修正後 line count 想定

| section | 変更 |
|:---|---:|
| 既存 (Day20 末、122 行) | 122 |
| Step A: Day20 追加 entry | +20 |
| Step B: 新 [Unreleased] + 空行 | +4 |
| Step C: header コメント修正 | ±0 |
| **合計** | **~146 行** |

---

## 4. Release notes 内容

GitHub Release notes は **見やすい要約 + CHANGELOG への詳細リンク** style. 一時ファイル `/tmp/release_notes_v0.1.0.md` に書き出して `gh release create --notes-file` で渡す.

### 4.1 Release notes 全体構造 (~70 行)

```markdown
# v0.1.0 — Day1-20 統合スナップショット

**Day7 §9.3 で定義された long-term task 7 件を完全クローズした公式 milestone**.
本リリースは Day1-20 の 21 セッションにわたる開発成果を凍結し、初の semantic version tag として公開する.

## 🎯 主要ハイライト

- **Vancouver Veto + APA 7 disambiguation 対応** (Day9, Day16): `is_mdpi_style()` regex `\((?:19|20)\d{2}[a-z]?\)` で `(YYYY)` / `(YYYYa)` paren year を含む全 ref を LLM path に強制 routing
- **3 分類 audit logic** (Day15-20): PubMed 未ヒット ref を A (真の捏造) / B (MEDLINE 非収録) / C (収録誌 indexing 漏れ) / unknown (graceful fail-soft) に自動分類. Day20 改修で book/conference/DOI 欠落 case の false positive を解消 (cell_45refs A: 14→1、apa_45refs A: 4→0)
- **4 系統 golden fixture**: mdpi_149refs (Day1-7、byte-strict) / vancouver_24refs (Day11) / apa_45refs (Day16) / cell_45refs (Day17) で 4 引用 style の regression 保護
- **100 tests passed + 1 skipped**: deterministic Phase 1 golden + LLM/PubMed variability の document-of-record 二層 hybrid 設計 (Day11 命名規約)
- **GitHub Public + CI 整備** (Day18-19): `hikataya01-netizen/pubmed-reference-resolver`、MIT License、GitHub Actions で Python 3.11/3.12 各 push 自動テスト
- **Day7 §9.3 long-term task 7/7 完全クローズ** (Day20、Stage 3 認証): MCP/hook 配線想定だった最後の 1 件も SKILL.md 経由起動として認証 cleanup

## 📊 統計

| 指標 | 値 |
|:---|---:|
| Commits | 92 (Day1-20、Day21 release commit 除く) |
| Tests passed | 100 |
| Tests skipped | 1 (LLM path シナリオ、API key 未設定時) |
| Production code modules | 6 (`main.py`, `mdpi_parser.py`, `journal_audit.py`, `crossref_check.py`, `nlm_catalog_check.py`, `three_class_classifier.py`) |
| Golden fixture series | 4 (mdpi / vancouver / apa / cell) |
| LICENSE | MIT |

## 📖 詳細

- **全変更履歴**: [CHANGELOG.md `[0.1.0]` section](https://github.com/hikataya01-netizen/pubmed-reference-resolver/blob/v0.1.0/CHANGELOG.md)
- **セッション記録 (Day1-20)**: [docs/sessions/dayN/](https://github.com/hikataya01-netizen/pubmed-reference-resolver/tree/v0.1.0/docs/sessions)
- **使い方ガイド**: [skill_package/references/USAGE_QUICKSTART.md](https://github.com/hikataya01-netizen/pubmed-reference-resolver/blob/v0.1.0/skill_package/references/USAGE_QUICKSTART.md) (バージョン 1.5)
- **README**: [プロジェクト README](https://github.com/hikataya01-netizen/pubmed-reference-resolver/blob/v0.1.0/README.md)

## 🚀 インストール

```bash
git clone git@github.com:hikataya01-netizen/pubmed-reference-resolver.git
cd pubmed-reference-resolver
pip install -r requirements.txt

# API key 設定
cp .env.example .env
# .env を編集して REPLACE-WITH-YOUR-KEY を実 key に置換
```

詳細手順: [docs/operations/SETUP_API_KEYS.md](https://github.com/hikataya01-netizen/pubmed-reference-resolver/blob/v0.1.0/docs/operations/SETUP_API_KEYS.md)

## 🙏 Acknowledgments

- **NCBI E-utilities** (PubMed / PMC / NLM Catalog)
- **Crossref REST API** (DOI 実在確認)
- **Anthropic Claude Sonnet 4.6** (LLM-path での reference 構造化)
- **PMC Open Access subset** (fixture data、各 fixture README で CC BY 4.0 帰属表示)

開発期間中 (Day1-20) は **Claude Code (Sonnet 4.6)** および **Claude Opus 4.7 (1M context)** が共同作業者として参画.

---

**Full tree at this release**: https://github.com/hikataya01-netizen/pubmed-reference-resolver/tree/v0.1.0
```

### 4.2 Tag 命名と annotated tag メッセージ

- **Tag 名**: `v0.1.0` (`v` prefix、semver 慣習に従う、`gh release` も `v` prefix を想定)
- **Annotated tag メッセージ**: `git tag -a v0.1.0 -m "v0.1.0 - Day1-20 統合スナップショット (Day7 §9.3 long-term task 完全クローズ)"`

### 4.3 GitHub Release title

`v0.1.0 — Day1-20 統合スナップショット (Day7 §9.3 完全クローズ)`

---

## 5. Commit 計画 (3 commits + 2 pre = 5 + 外部操作 2)

| 順 | commit 種別 | Phase | 内容 |
|:---:|:---|:---:|:---|
| (前) | `docs(spec)` | — | Day21 SPEC archive (本 commit) |
| (前) | `docs(plan)` | — | Day21 PLAN archive |
| 1 | `docs(changelog)` | 1 | CHANGELOG.md 改修 (Step A + B + C 統合 commit) |
| Phase 2 | (commit なし、外部操作) | 2 | `git tag -a v0.1.0` + `git push origin v0.1.0` |
| Phase 3 | (commit なし、外部操作) | 3 | `gh release create v0.1.0 --notes-file /tmp/release_notes_v0.1.0.md` |
| 2 | `docs(sessions)` | 4 | Day21 archive (README + LESSONS) |

合計 **3 commits + 2 pre = 5 commits + 2 外部操作** (tag + release).

---

## 6. 完了条件 (10 項目)

| # | 条件 | 確認方法 |
|:---:|:---|:---|
| 1 | CHANGELOG.md に `[0.1.0] - 2026-05-22` section | `grep -c "## \[0.1.0\] - 2026-05-22" CHANGELOG.md` = 1 |
| 2 | CHANGELOG.md に Day20 追加 entry | `grep -c "_detect_book\|STAGE3_COMPLETION_NOTE" CHANGELOG.md` ≥ 2 |
| 3 | 新 `[Unreleased]` section 存在 | `grep -c "^## \[Unreleased\]$" CHANGELOG.md` = 1 |
| 4 | git tag v0.1.0 ローカル作成済 (annotated) | `git tag -l v0.1.0` = "v0.1.0" + `git cat-file -t v0.1.0` = "tag" |
| 5 | git tag v0.1.0 が GitHub に push 済 | `git ls-remote --tags origin \| grep v0.1.0` 存在 |
| 6 | GitHub Release v0.1.0 作成済 | `gh release view v0.1.0 --json tagName --jq '.tagName'` = "v0.1.0" |
| 7 | Release notes に 6 主要ハイライト含む | `gh release view v0.1.0 --json body \| jq -r '.body' \| grep -c "Vancouver Veto\|3 分類\|4 系統\|100 tests\|GitHub Public\|Stage 3"` ≥ 6 |
| 8 | 全 test pass (regression なし、code 改変ゼロ) | `pytest tests/ 2>&1 \| tail -1` = "100 passed, 1 skipped" |
| 9 | working tree clean + push 同期 | `git status` clean + local HEAD == remote HEAD |
| 10 | Day21 archive 4 files | `ls docs/sessions/day21/ \| wc -l` = 4 |

---

## 7. 工数見積もり

| Phase | 内容 | 見積 |
|:---:|:---|---:|
| Pre | SPEC + PLAN archive | 20min |
| Phase 1 | CHANGELOG.md 改修 + commit | 20min |
| Phase 2 | git tag + push | 5min |
| Phase 3 | release notes 一時ファイル作成 + gh release create + 確認 | 15min |
| Phase 4 | Day21 archive + push | 20min |
| **合計** | | **~1.5h** |

LLM cost: **$0** (code 改修なし、external API call なし).

---

## 8. 想定リスクと対応

| リスク | 確率 | 対応 |
|:---|:---:|:---|
| `gh release create` で OAuth scope 不足 | 中 | Day18-19 で `repo` + `workflow` scope は設定済、追加で必要なら `gh auth refresh` |
| Release notes 中の compare link が無効 (タグ無の repo に対する比較) | 中 | テンプレ簡略化で「Full Changelog: link」を「Full tree at this release: link」に変更済 (本 SPEC §4.1) |
| tag を間違って付与 | 低 | `git tag -d v0.1.0 && git push origin :v0.1.0` で復旧可能 |
| CI が tag push で workflow 実行され失敗 | 低 | 既存 workflow は push trigger、tag に対する別 workflow は無し |

---

## 9. Out of Scope (Day22+ 候補)

- **v0.2.0 / v1.0.0 のロードマップ** (機能性の semver 判断は別途)
- **release-please 等の自動 release ツール導入**
- **PyPI 公開** (homepageUrl 設定 + setup.py/pyproject.toml 整備が前提)
- **Read the Docs 連携** (sphinx 整備が前提)
- **Rule 3 NLM 検索の SSL 問題解消** (Day20 LESSONS §6.2、Day22+ で対応)
- **CONTRIBUTING.md / Issue PR template** (Day19 LESSONS §6.2、Day22+ で対応)

---

## 10. 参照

- Day19 SPEC: `docs/sessions/day19/SPEC_github_public_switch.md` §10 Out of Scope (v0.1.0 tag 候補として記載)
- Day20 LESSONS: `docs/sessions/day20/DAY20_LESSONS_LEARNED.md` §6.3 (Day21 推奨着手順 1)
- 既存 `CHANGELOG.md` (Day7 era + Day19 `[Unreleased] - 2026-05-18` entry)
- GitHub CLI docs: `gh release create` (https://cli.github.com/manual/gh_release_create)
- Keep a Changelog 1.1.0: https://keepachangelog.com/ja/1.1.0/
- セマンティックバージョニング 2.0.0: https://semver.org/lang/ja/

---

**承認**: 片山英樹 (brainstorming Q1-Q2 + design 全 4 sections)
**次工程**: writing-plans skill で implementation plan を作成
