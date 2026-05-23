# v0.1.0 Release Implementation Plan (Day21)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Day20 で Day7 §9.3 long-term task 完全クローズした milestone を CHANGELOG 整備 + git tag v0.1.0 + GitHub Release で公式 record 化する.

**Architecture:** code 改変ゼロ. CHANGELOG.md に Day20 追加 entry + `[Unreleased] - 2026-05-18` → `[0.1.0] - 2026-05-22` rename + 新 `[Unreleased]` 挿入 + header コメント更新. `git tag -a v0.1.0` + `git push origin v0.1.0`. `gh release create v0.1.0 --notes-file` で 6 ハイライト要約 + CHANGELOG link の release notes 公開.

**Tech Stack:** git tag (annotated) / GitHub CLI (`gh release create --notes-file`) / 既存 main.py / 既存 100 tests

**SPEC**: `docs/sessions/day21/SPEC_v0_1_0_release.md` (commit `1a74b47`)

---

## File Structure

### 修正対象 (1 ファイル)

| ファイル | 修正内容 |
|:---|:---|
| `CHANGELOG.md` | Step A (Day20 追加 entry ~25 行) + Step B (section rename + 新 [Unreleased] ~4 行) + Step C (header コメント更新) |

### 新規作成 (Day21 archive 4 files + 1 temp)

| ファイル | 用途 |
|:---|:---|
| `docs/sessions/day21/PLAN_v0_1_0_release.md` | 本 PLAN (既に作成中) |
| `docs/sessions/day21/README.md` | Day21 index |
| `docs/sessions/day21/DAY21_LESSONS_LEARNED.md` | Day21 末 archive |
| `/tmp/release_notes_v0.1.0.md` | gh release create に渡す release notes (一時ファイル、commit せず) |

### 外部システム変更

- `git tag -a v0.1.0 -m "..."` (ローカル annotated tag)
- `git push origin v0.1.0` (GitHub に tag 反映)
- `gh release create v0.1.0 --title "..." --notes-file /tmp/release_notes_v0.1.0.md`

### 改変なし

- production code 全般 / 全 test ファイル / 全 fixture / README / LICENSE / SKILL.md / `.gitignore` / `.gitleaksignore`

---

## Task 1: CHANGELOG.md 改修 (Phase 1)

**Files:**
- Modify: `CHANGELOG.md` (Step A + B + C 統合)

- [ ] **Step 1: 現状確認 (line 1-9)**

Run: `head -9 CHANGELOG.md`

Expected:
```
# Changelog

このプロジェクトの特筆すべき変更はこのファイルに記録されます。

形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠しており、
このプロジェクトは [セマンティックバージョニング](https://semver.org/lang/ja/) の採用を予定しています
(v0.1.0 タグ付けは別タスクで実施予定)。

## [Unreleased] - 2026-05-18
```

- [ ] **Step 2: Step C — header コメント更新 (line 5-7)**

Edit `CHANGELOG.md` 旧:
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

- [ ] **Step 3: Step B — section header rename + 新 [Unreleased] 挿入 (line 9)**

Edit `CHANGELOG.md`:

旧:
```
## [Unreleased] - 2026-05-18

### Day8-18 統合: Vancouver Veto + 4 fixture + 3 分類 audit + GitHub 公開準備
```

新:
```
## [Unreleased]

(Day21 以降の変更がここに記録される予定)

## [0.1.0] - 2026-05-22

### Day8-18 統合: Vancouver Veto + 4 fixture + 3 分類 audit + GitHub 公開準備
```

- [ ] **Step 4: Step A — Day20 追加 entry を挿入**

`CHANGELOG.md` 内で `### Documentation` セクション (Day19 で記載済) の **直後**、`### Test 健全性推移` セクション (Day19 で記載済) の **直前**に、以下を挿入:

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

- [ ] **Step 5: 修正結果確認**

Run:
```bash
echo "[1] [0.1.0] section:" && grep -c "## \[0.1.0\] - 2026-05-22" CHANGELOG.md
echo "[2] 新 [Unreleased] section:" && grep -c "^## \[Unreleased\]$" CHANGELOG.md
echo "[3] Day20 entry:" && grep -c "_detect_book\|STAGE3_COMPLETION_NOTE" CHANGELOG.md
echo "[4] header コメント:" && grep -c "v0.1.0 は Day21 = 2026-05-22 でタグ付与済" CHANGELOG.md
echo "[5] line count:" && wc -l CHANGELOG.md
```

Expected:
```
[1] [0.1.0] section: 1
[2] 新 [Unreleased] section: 1
[3] Day20 entry: 2 (or more)
[4] header コメント: 1
[5] line count: ~146
```

- [ ] **Step 6: Phase 1 commit**

```bash
git add CHANGELOG.md && \
git commit -m "$(cat <<'EOF'
docs(changelog): add Day20 entry + rename [Unreleased] → [0.1.0] (Day21 Phase 1)

Day20 で Day7 §9.3 long-term task 完全クローズ (7/7) を達成した milestone
に向けて、CHANGELOG.md を v0.1.0 release 準備状態に整備:

Step A: 既存 [Unreleased] - 2026-05-18 section に Day20 追加 entry を
挿入 (~20 行):
  - Added: 3 helper (_detect_book / _detect_conference / _classify_via_nlm_only)
    + STAGE3_COMPLETION_NOTE + 3 unit tests
  - Changed: three_class_classifier._classify_single (4 rule 順次評価)
    + main.py:synthesize_outputs (is_book/raw_text/publisher 渡し)
    + cell/apa baseline 再生成 + mdpi_149refs expected_report 再生成

Step B: section header を [Unreleased] - 2026-05-18 → [0.1.0] - 2026-05-22
に rename + 新 [Unreleased] section を line 9 に挿入 (Day22+ 用 placeholder).

Step C: header コメント line 5-7 を「v0.1.0 タグ付けは別タスクで実施予定」
から「v0.1.0 は Day21 = 2026-05-22 でタグ付与済」に更新.

122 → ~146 行. 100 tests passed / 1 skipped 不変 (code 改変なし).
git tag + gh release create は Phase 2-3 で外部操作.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: git tag v0.1.0 作成 + push (Phase 2)

**Files:** (外部操作、commit なし)
- Modify: なし (git refs/tags/v0.1.0 が local に作成され、GitHub に push される)

- [ ] **Step 1: tag が未作成であること確認**

Run: `git tag -l`

Expected: (空) — Day20 末まで tag なし.

⚠️ 既に v0.1.0 tag が存在する場合: `git tag -d v0.1.0` (local) + `git push origin :v0.1.0` (remote) で削除してから再作成.

- [ ] **Step 2: annotated tag を Task 1 commit に作成**

Run:
```bash
git tag -a v0.1.0 -m "v0.1.0 - Day1-20 統合スナップショット (Day7 §9.3 long-term task 完全クローズ)"
```

Expected: silent 成功 (出力なし).

- [ ] **Step 3: tag 種別と message 確認 (annotated)**

Run:
```bash
git cat-file -t v0.1.0 && \
git tag -l v0.1.0 -n5
```

Expected:
```
tag
v0.1.0          v0.1.0 - Day1-20 統合スナップショット (Day7 §9.3 long-term task 完全クローズ)
```

(`tag` 種別 = annotated tag 確認、`commit` だと lightweight tag になっていて NG)

- [ ] **Step 4: tag を GitHub に push**

```bash
git push origin v0.1.0
```

Expected:
```
To https://github.com/hikataya01-netizen/pubmed-reference-resolver.git
 * [new tag]         v0.1.0 -> v0.1.0
```

- [ ] **Step 5: GitHub 側 tag 確認**

```bash
git ls-remote --tags origin | grep v0.1.0
```

Expected: tag SHA が表示される (e.g., `<hash>\trefs/tags/v0.1.0`).

---

## Task 3: Release notes 一時ファイル作成 + gh release create (Phase 3)

**Files:**
- Create (一時): `/tmp/release_notes_v0.1.0.md` (commit せず、`gh release create --notes-file` 用)

- [ ] **Step 1: release notes 一時ファイル作成**

Write `/tmp/release_notes_v0.1.0.md`:

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

- [ ] **Step 2: 一時ファイル sanity check**

```bash
wc -l /tmp/release_notes_v0.1.0.md && \
grep -c "Vancouver Veto\|3 分類\|4 系統\|100 tests\|GitHub Public\|Stage 3" /tmp/release_notes_v0.1.0.md
```

Expected:
```
~75 /tmp/release_notes_v0.1.0.md
6 (or more)
```

- [ ] **Step 3: gh release create 実行**

```bash
gh release create v0.1.0 \
  --title "v0.1.0 — Day1-20 統合スナップショット (Day7 §9.3 完全クローズ)" \
  --notes-file /tmp/release_notes_v0.1.0.md
```

Expected: silent 成功 + release URL 出力 (`https://github.com/hikataya01-netizen/pubmed-reference-resolver/releases/tag/v0.1.0`).

⚠️ OAuth scope エラー時: `gh auth refresh -h github.com -s repo` (interactive、ユーザー操作必要).

- [ ] **Step 4: GitHub Release 状態確認**

```bash
gh release view v0.1.0 --json tagName,name,isDraft,isPrerelease,url | jq
```

Expected:
```json
{
  "tagName": "v0.1.0",
  "name": "v0.1.0 — Day1-20 統合スナップショット (Day7 §9.3 完全クローズ)",
  "isDraft": false,
  "isPrerelease": false,
  "url": "https://github.com/hikataya01-netizen/pubmed-reference-resolver/releases/tag/v0.1.0"
}
```

- [ ] **Step 5: Release notes body 内容確認**

```bash
gh release view v0.1.0 --json body --jq '.body' | grep -c "Vancouver Veto\|3 分類\|4 系統\|100 tests\|GitHub Public\|Stage 3"
```

Expected: `6` 以上.

- [ ] **Step 6: 一時ファイル削除 (cleanup)**

```bash
rm -f /tmp/release_notes_v0.1.0.md
```

- [ ] **Step 7: Phase 2-3 は commit を生成しない (外部操作のため)**

git status 確認:
```bash
git status
```

Expected: `nothing to commit, working tree clean` (Task 1 の CHANGELOG commit のみが新規、tag/release は外部状態の変更).

---

## Task 4: Day21 archive (Phase 4) + push

**Files:**
- Create: `docs/sessions/day21/README.md`
- Create: `docs/sessions/day21/DAY21_LESSONS_LEARNED.md`

- [ ] **Step 1: Day21 README.md を作成**

Write `docs/sessions/day21/README.md`:

```markdown
# docs/sessions/day21/

**Day21 セッション (2026-05-22) のアーカイブ**

このディレクトリは、pubmed-reference-resolver プロジェクトの Day21 セッション (Day20 で Day7 §9.3 long-term task 完全クローズ後の公式 milestone として v0.1.0 tag + GitHub Release を作成した作業) で生成された記録を、永続アーカイブとして保管する.

## 内容

| ファイル | 役割 |
|:---|:---|
| `SPEC_v0_1_0_release.md` | brainstorming 確定設計仕様 (Q1-Q2 + 4 sections) |
| `PLAN_v0_1_0_release.md` | writing-plans 出力の段階的実装計画 (Task 1-4 + Verification) |
| `DAY21_LESSONS_LEARNED.md` | Day21 全 commits の経緯 + 教訓 D21-1+ |
| `README.md` | 本書 |

## Day21 の特徴

Day1-20 の 21 セッションを semantic version `v0.1.0` として凍結. Day7 §9.3 で定義された long-term task 7 件が Day20 で完全クローズしたことを GitHub Release で公式 record 化. code 改修ゼロ、CHANGELOG + tag + release のみの軽量セッション.

## 達成事項 (3 commits + 2 pre = 5 + 外部操作 2)

| 順 | commit / 操作 | Phase | 達成 |
|:---:|:---:|:---:|:---|
| (前) | `1a74b47` | — | Day21 SPEC archive (304 行) |
| (前) | `<plan_hash>` | — | Day21 PLAN archive |
| 1 | `<changelog_hash>` | 1 | CHANGELOG.md 改修 (Day20 追加 + [Unreleased] → [0.1.0] + 新 [Unreleased] + header コメント) |
| Phase 2 | (外部操作) | 2 | `git tag -a v0.1.0` + `git push origin v0.1.0` |
| Phase 3 | (外部操作) | 3 | `gh release create v0.1.0 --notes-file /tmp/release_notes_v0.1.0.md` |
| 2 | (本 commit) | 4 | Day21 archive (README + LESSONS) |

main branch: 92 → **94** + 本 commit で **95 commits** (Day20 末 → Day21 末、+3).
test 健全性: 100 passed / 1 skipped (不変、code 改変なし).
GitHub Release: ✅ **v0.1.0** 公開、Annotated tag、Release notes 6 ハイライト.

## GitHub 上の現状 (Day21 末)

| 項目 | 値 |
|:---|:---|
| URL | https://github.com/hikataya01-netizen/pubmed-reference-resolver |
| Release URL | https://github.com/hikataya01-netizen/pubmed-reference-resolver/releases/tag/v0.1.0 |
| Visibility | PUBLIC (Day19 から継続) |
| License | MIT |
| Topics | 6 個 |
| Pushed commits | 95 |
| **Latest tag** | **v0.1.0** (Day1-20 統合スナップショット) |
| Tests | 100 passed / 1 skipped |

## 関連記録

完全な session 記録は別途以下に保管 (本リポジトリ外):
- `pubmed-reference-resolver-integration-chat-day21.md` (Day21 の完全記録、予定)

---

**作成日**: 2026-05-22 (Day21 クロージング時)
**メンテナ**: 片山英樹 (Hideki Katayama)
```

⚠️ `<plan_hash>` / `<changelog_hash>` は Task 1 + writing-plans commit の実値で置換.

- [ ] **Step 2: Day21 DAY21_LESSONS_LEARNED.md を作成**

Write `docs/sessions/day21/DAY21_LESSONS_LEARNED.md`:

```markdown
# Day21 LESSONS LEARNED

**Day21 セッション (2026-05-22)**: v0.1.0 tag + GitHub Release (Day1-20 統合 milestone)

---

## 1. セッション概要

### 1.1 背景

Day20 で Day7 §9.3 long-term task 7 件を完全クローズ. ユーザーは Day21 task として **(1) v0.1.0 tag + GitHub Release** を選択 (Day20 LESSONS §7 パターン 1).

### 1.2 brainstorming 段階 (Q1-Q2)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | v0.1.0 に Day20 改修も含めるか | (含める) Day20 改修を CHANGELOG に追加 |
| Q2 | Release notes のスタイル | (要約 + CHANGELOG リンク) |

### 1.3 SPEC (commit `1a74b47`) + PLAN

`docs/sessions/day21/SPEC_v0_1_0_release.md` (304 行) + `PLAN_v0_1_0_release.md` を archive.

---

## 2. 実装段階の経緯 (3 commits + 外部操作 2)

### Phase 1: CHANGELOG.md 改修 (commit `<changelog_hash>`)

- Task 1: 3 step (Day20 追加 entry + [Unreleased] → [0.1.0] rename + header コメント更新). 122 → ~146 行.

### Phase 2: git tag v0.1.0 + push (外部操作、commit なし)

- Task 2: annotated tag 作成 + GitHub push. Tag 種別が `tag` (annotated) であることを `git cat-file -t v0.1.0` で確認.

### Phase 3: gh release create (外部操作、commit なし)

- Task 3: `/tmp/release_notes_v0.1.0.md` (~75 行) を作成 → `gh release create v0.1.0 --notes-file` → Release URL 取得 → body 6 ハイライト確認 → 一時ファイル削除.

### Phase 4: Day21 archive (本 commit)

- Task 4: README + LESSONS archive + push.

---

## 3. 設計判断と検証

### 3.1 Day20 改修を含める根拠

Day20 改修は Day7 §9.3 完全クローズ (Stage 3 認証) を含むため、これを除外して v0.1.0 を打つと「6/7 達成版」になってしまう. Day21 が「完全クローズ後」の milestone であるため Day20 改修込みが筋.

### 3.2 Annotated tag vs lightweight tag

`git tag -a v0.1.0 -m "..."` で annotated tag を採用. lightweight tag (`git tag v0.1.0`) と異なり:
- tag 自体が commit object として履歴に残る
- author / date / message を持つ
- `git describe` 等で参照可能
- semver release では annotated が標準

### 3.3 Release notes の compare link を回避

GitHub の typical pattern `**Full Changelog**: https://github.com/.../compare/<prev>...v0.1.0` は **previous tag** が必要. v0.1.0 は初 release なので previous tag 無し → compare link 無効. 代わりに `Full tree at this release` link で同等情報を提供.

---

## 4. 実機検証結果

### 4.1 GitHub Release 状態

| 項目 | 値 |
|:---|:---|
| Tag name | v0.1.0 |
| Release title | v0.1.0 — Day1-20 統合スナップショット (Day7 §9.3 完全クローズ) |
| Is draft | false (Public Release) |
| Is prerelease | false (Stable Release) |
| Tag type | annotated |
| URL | https://github.com/hikataya01-netizen/pubmed-reference-resolver/releases/tag/v0.1.0 |

### 4.2 test 健全性

不変: 100 passed / 1 skipped (code 改修ゼロ).

---

## 5. 教訓 (D21-1, D21-2)

### 5.1 D21-1: milestone release は long-term task 完全クローズと同期させる

**事象**: Day20 で Day7 §9.3 完全クローズ (7/7) を達成 → Day21 で即 v0.1.0 release. 「未完了 task の残置」と「release」が両立しないため、release 化は long-term task の完全クローズ後にすると整理しやすい.

**学び**: semver release は **achievement gate** として機能する. 「v0.1.0 = 初期 milestone セット完了」「v0.2.0 = 次の milestone セット完了」のように、release 番号と長期 task の chunk を同期させる pattern が project 全体の見通しを向上.

**適用範囲**: Day22+ の long-term task (v0.2.0 で完了させる task chunk) を Day21 中に予測しなくて良いが、Day22 以降に新 task が積まれた段階で「次 release はいつ」を意識する.

### 5.2 D21-2: 初 release で compare link は使えない

**事象**: GitHub の慣習に従って release notes 末尾に `**Full Changelog**: .../compare/<prev>...v0.1.0` を入れようとしたが、初 release では previous tag が存在せず無効. 代替として `Full tree at this release` link を採用.

**学び**: 初 release は GitHub typical pattern の一部が機能しない. 「Full Changelog」概念は v0.2.0 以降で有効. 初 release は **tree link** で代用するか、`compare/ROOT...v0.1.0` という magic ref を使う方法もあるが、可読性は tree link が上.

**適用範囲**: 将来 v0.2.0 release 時には `compare/v0.1.0...v0.2.0` が使えるため、本 D21-2 は v0.1.0 限定の 1 回事象.

---

## 6. 残存タスク (Day22 以降)

### 6.1 Day19+ で生成された Day22+ 候補

- [ ] **Rule 3 NLM 検索の SSL 問題解消** (Day20 D20 起源、改修の真価発揮)
- [ ] **CONTRIBUTING.md / CODE_OF_CONDUCT.md / Issue PR template** (Day19 §6.2、collaboration 受入準備)
- [ ] **Branch protection rule** 設定
- [ ] **SSH 認証 cleanup** (Day18 D18 起源)
- [ ] **pre-commit hook gitleaks 自動実行** (Day19 起源)
- [ ] **predatory journal データベース連携** (Day20 §10、B 細分化)
- [ ] **MCP server による batch processing** (Day20 §10、Stage 3 を超えた拡張)
- [ ] **PyPI 公開** (Day20 §10、homepageUrl 設定 + packaging)

### 6.2 Day22+ 推奨着手順

1. **Rule 3 NLM 検索の SSL 問題解消** (Day20 改修の真価発揮、~2h)
2. **CONTRIBUTING.md / Issue PR template** (公開後の collaboration 受入準備、~2h)
3. **pre-commit hook gitleaks 自動実行** (将来の secret leak 防止、~1h)

---

## 7. 次セッション再開時のプロンプトテンプレート

### パターン 1: Day22 として Rule 3 NLM 検索の SSL 問題解消 (推奨)

```
Day22 として、Day20 で導入した Rule 3 (NLM 直接検索) の SSL 問題を
解消します. 現状 cell_45refs では 8/15、apa_45refs では 17/20 が
unknown に倒れている. nlm_catalog_check.py の HTTP 実装を certifi
ベースに変更、もしくは requests/httpx 移行で SSL chain 修復. baseline
再生成で B/C 判定が実際に出るよう確認.
```

### パターン 2: Day22 として CONTRIBUTING.md / Issue PR template

```
Day22 として、Public 公開済の pubmed-reference-resolver に collaboration
受入準備として CONTRIBUTING.md と Issue/PR template (.github/) を追加
します. brainstorming → SPEC → 実装で進めてください. ~2h.
```

### パターン 3: Day22 として pre-commit hook gitleaks 自動実行

```
Day22 として、pre-commit hook で gitleaks scan を自動実行する仕組みを
追加します. .pre-commit-config.yaml + Day18 で確立した .gitleaksignore
の継承. 開発者が secret leak を commit 前に検出できる ops 強化. ~1h.
```

---

**記録完了日**: 2026-05-22 (Day21)
**記録者**: Claude Code (Sonnet 4.6)
**ステータス**: Day21 archive 完成、v0.1.0 公開済、Day22 着手準備完了 (3 パターンプロンプトあり)
```

⚠️ `<changelog_hash>` は Task 1 commit の実値で置換.

- [ ] **Step 3: Phase 4 commit + push**

```bash
git add docs/sessions/day21/PLAN_v0_1_0_release.md \
        docs/sessions/day21/README.md \
        docs/sessions/day21/DAY21_LESSONS_LEARNED.md && \
git commit -m "$(cat <<'EOF'
docs(sessions): archive day21 v0.1.0 release session

Day21 セッション完了に伴う archive:
- README.md: day21/ index, v0.1.0 release 達成 (Day7 §9.3 完全クローズ
  milestone)、GitHub Release URL + 統計
- DAY21_LESSONS_LEARNED.md: 全 commits 経緯 + 教訓 D21-1, D21-2
  (milestone release を long-term task クローズと同期 + 初 release で
   compare link は使えない)
- PLAN_v0_1_0_release.md: writing-plans 出力の実装計画

主成果:
- v0.1.0 annotated tag 作成 + GitHub push
- GitHub Release v0.1.0 公開 (release notes 6 ハイライト + CHANGELOG link)
- CHANGELOG.md 改修 (Day20 追加 entry + [Unreleased] → [0.1.0] rename
  + 新 [Unreleased] + header コメント更新、122 → 146 行)

Day7 §9.3 long-term task 完全クローズ (7/7) を公式 milestone として
record. Day1-20 の 21 セッションにわたる開発成果を semantic version
v0.1.0 で凍結.

Day22+ 候補:
- Rule 3 NLM 検索の SSL 問題解消 (Day20 改修の真価発揮)
- CONTRIBUTING.md / Issue PR template
- pre-commit hook gitleaks 自動実行

main branch: 92 → 94 (+2) + 本 commit で 95, test: 100 passed / 1 skipped
(code 改修ゼロで不変). Release: https://github.com/hikataya01-netizen/pubmed-reference-resolver/releases/tag/v0.1.0

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
python3 -m pytest tests/ 2>&1 | tail -1
```
Expected: **100 passed, 1 skipped** (code 改修ゼロのため不変).

- [ ] **V2: SPEC §6 10 完了条件すべて満たす**

```bash
echo "[1] [0.1.0] section:" && grep -c "## \[0.1.0\] - 2026-05-22" CHANGELOG.md
echo "[2] Day20 entry:" && grep -c "_detect_book\|STAGE3_COMPLETION_NOTE" CHANGELOG.md
echo "[3] 新 [Unreleased]:" && grep -c "^## \[Unreleased\]$" CHANGELOG.md
echo "[4] tag annotated:" && git cat-file -t v0.1.0
echo "[5] tag pushed:" && git ls-remote --tags origin | grep v0.1.0 | wc -l
echo "[6] Release exists:" && gh release view v0.1.0 --json tagName --jq '.tagName'
echo "[7] Release 6 highlights:" && gh release view v0.1.0 --json body --jq '.body' | grep -c "Vancouver Veto\|3 分類\|4 系統\|100 tests\|GitHub Public\|Stage 3"
echo "[8] tests:" && python3 -m pytest tests/ 2>&1 | tail -1
echo "[9] working tree clean:" && git status --short && echo "local HEAD:" && git rev-parse --short HEAD && echo "remote HEAD:" && git ls-remote origin main 2>/dev/null | awk '{print substr($1, 1, 7)}'
echo "[10] Day21 archive 4 files:" && ls docs/sessions/day21/ | wc -l && ls docs/sessions/day21/
```

Expected:
- [1] `1`
- [2] `2` (or more)
- [3] `1`
- [4] `tag` (annotated 確認)
- [5] `1` (GitHub tag 存在)
- [6] `v0.1.0`
- [7] `6` (or more)
- [8] `100 passed, 1 skipped`
- [9] clean + local HEAD == remote HEAD
- [10] `4` (SPEC + PLAN + README + LESSONS)

- [ ] **V3: GitHub Release URL ブラウザ確認 (manual)**

ブラウザで `https://github.com/hikataya01-netizen/pubmed-reference-resolver/releases/tag/v0.1.0` を開いて以下を視認確認:

- Release title: "v0.1.0 — Day1-20 統合スナップショット (Day7 §9.3 完全クローズ)"
- Source code zip / tar.gz が自動生成されている
- Release notes body が正しく markdown render されている (絵文字 🎯 📊 📖 🚀 🙏 含む)
- "Latest" バッジが付与されている

---

## Notes for Implementing Agent

- **Controller-direct 推奨**: Day21 は CHANGELOG 編集 + git tag + gh release create + docs 作成のみ. subagent dispatch の利点なし、controller 直接実行が効率的.
- **commit を生成しない Phase**: Phase 2 (tag + push) と Phase 3 (gh release) は外部操作、git commit を生成しない. PLAN の commit 計画でも skip 表記.
- **`<changelog_hash>` placeholder**: Task 4 archive 内で参照される. Task 1 完了後の commit hash で置換.
- **Annotated tag 確認**: Task 2 Step 3 で必ず `git cat-file -t v0.1.0` = `tag` を確認 (lightweight だと `commit` になる). Annotated が semver release の標準.
- **Release notes 一時ファイル**: Phase 3 Step 6 で削除. Task 4 archive 完了後は不要.
- **compare link 不使用**: 初 release のため previous tag なし、`compare/<prev>...v0.1.0` は無効. 代わりに `tree/v0.1.0` link で代用済 (PLAN Task 3 Step 1 内テンプレ).
- **gh auth scope**: `repo` (Day18 で設定済) で release 作成可. 不足したら `gh auth refresh -h github.com -s repo`.
