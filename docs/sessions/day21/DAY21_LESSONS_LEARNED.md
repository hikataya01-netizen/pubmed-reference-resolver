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

### 1.3 SPEC (commit `1a74b47`) + PLAN (commit `8ef78f1`)

`docs/sessions/day21/SPEC_v0_1_0_release.md` (304 行) + `PLAN_v0_1_0_release.md` (716 行) を archive.

---

## 2. 実装段階の経緯 (3 commits + 外部操作 2)

### Phase 1: CHANGELOG.md 改修 (commit `568a17c`)

- Task 1: 3 step (Day20 追加 entry + [Unreleased] → [0.1.0] rename + header コメント更新). 122 → 143 行.

### Phase 2: git tag v0.1.0 + push (外部操作、commit なし)

- Task 2: annotated tag 作成 (commit `568a17c` を tag SHA `c68cad0` で wrap) + GitHub push 成功. Tag 種別が `tag` (annotated) であることを `git cat-file -t v0.1.0` で確認.

### Phase 3: gh release create (外部操作、commit なし)

- Task 3: `/tmp/release_notes_v0.1.0.md` (58 行) を作成 → `gh release create v0.1.0 --notes-file --title` → Release URL `https://github.com/hikataya01-netizen/pubmed-reference-resolver/releases/tag/v0.1.0` 取得 → body に 6 主要ハイライト含むことを `gh release view --json body` で確認 → 一時ファイル削除.

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

実機検証: `git cat-file -t v0.1.0` = `tag` (annotated 確認、`commit` だと lightweight tag になっていて NG).

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
| Release notes ハイライト数 | 6 (確認済) |

### 4.2 test 健全性

不変: 100 passed / 1 skipped (code 改修ゼロ).

### 4.3 CHANGELOG.md 状態

- 122 → 143 行
- `[0.1.0] - 2026-05-22` section: 1
- 新 `[Unreleased]` section (空 placeholder): 1
- Day20 entry (3 helper + STAGE3_COMPLETION_NOTE): 2 keyword 確認
- header コメント (「v0.1.0 は Day21 = 2026-05-22 でタグ付与済」): 1

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