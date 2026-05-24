# Day22 Session Archive (2026-05-24)

## 概要

Day22 セッションは 2 段構成:

- **Phase A (security)**: Day21 末セキュリティ監査で検出した 🔴 高優先 2 件を解消
  - A1: `.gitleaksignore` に Day19 報告書 4 fingerprint 追加 (commit `dbbac4a`)
  - A2: GitHub Secret Scanning + Push Protection 有効化 (gh api PATCH)
- **Phase B (main)**: Rule 3 NLM 検索の SSL 問題を解消 (Day20 改修の真価発揮)

## Phase B 成果

| 指標 | Day21 末 | Day22 末 |
|:---|:---:|:---:|
| 全 tests | 100 passed / 1 skipped | 101 passed / 1 skipped |
| cell_45refs 三分類 | A=1, B=6, C=0, unknown=8 | A=1, B=12, C=0, unknown=2 |
| apa_45refs 三分類 | A=0, B=3, C=0, unknown=17 | A=0, B=3, C=0, unknown=17 (※ 数値同一だが reason は SSL→legitimate に変化) |
| requirements.txt deps | 4 | 5 (+certifi>=2024.0,<2027.0) |

apa の数値が変化しない理由: SSL fix は NLM Catalog scope だが、apa 残 17 unknown のうち 16 件は Crossref graceful failure (DOI timeout、非 MEDLINE journal 中心)、1 件は legitimate な「NLM Catalog に該当 journal なし」。NLM SSL fix の真価は cell で発揮 (unknown 8→2、6 件が B に再分類)。Crossref graceful 側は Day23+ の別 task として残置。

## Day22 archive 構成

- `README.md` — 本ファイル (Day22 index)
- `DAY22_LESSONS_LEARNED.md` — Day22 教訓記録
- `../../superpowers/specs/2026-05-24-rule3-nlm-ssl-fix-design.md` — Phase B brainstorming spec
- `../../superpowers/plans/2026-05-24-rule3-nlm-ssl-fix.md` — Phase B implementation plan

## Day22 commits

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `dbbac4a` | chore(security) | Phase A1: Day19 報告書 4 fingerprint suppression |
| 2 | `aaa1eb9` | docs(spec) | Phase B brainstorming spec |
| 3 | `272a34f` | docs(plan) | Phase B implementation plan |
| 4 | `851cf2a` | test(nlm) | TDD RED: certifi context unit test |
| 5 | `81b1b9e` | fix(nlm) | TDD GREEN: certifi SSL context 注入 |
| 6 | `0f0e028` | docs(nlm) | fixup: module docstring (certifi dep) |
| 7 | `4ba48ba` | test(fixtures) | cell + apa baseline 再生成 |
| 8 | `9c299c0` | docs(tests) | fixup: integration test docstring (Day22 fulfillment) |
| 9 | `7af632c` | docs(sessions) | Day22 archive |

Phase B は当初 5 commit 計画だったが、Task 2 と Task 3 のコードレビュー指摘 (#6, #8) を atomic な fix-up commit として分離したため 7 commit に増加。

## 設計判断

実装 approach は **A1: module-level `_SSL_CONTEXT` singleton + `_fetch_json` への注入** を採用 (spec §3.3 参照)。代替案として検討した A2 (`urllib.request.build_opener`)、A3 (`requests`/`httpx` 移行) は、それぞれ test mocking 複雑化と diff/dep 過大化のため不採用。

## Day23+ 候補

- CONTRIBUTING.md / Issue PR template (Day22 handoff パターン 2)
- pre-commit hook gitleaks 自動実行 (Day22 handoff パターン 3 = Phase A B1)
- predatory journal データベース連携 (Beall's list)
- pyproject.toml + uv.lock 移行 (CLAUDE.md § 8 整合)
- SSL fix の corporate proxy 対応文書化 (USAGE_QUICKSTART)
- **NEW**: apa_45refs Crossref graceful failure (16 件) の対応 — Crossref SSL/timeout 側の確認、または NLM 直接検索パスへの fallback 検討
- **NEW**: cell `ref_no=41` で観測された NLM fuzzy-match 誤検出 (Processes journal → Depos Rec) — NLM Catalog 検索の precision 改善検討
