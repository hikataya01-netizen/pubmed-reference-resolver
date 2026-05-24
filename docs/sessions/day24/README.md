# Day24 Session Archive (2026-05-24)

## 概要

Day24 セッションは Day23 Phase 1 で意図的に skip-mark した 5 test file を
新 mdpi_173refs fixture に re-point + 構造化 refactor + skip 解除する作業.
Day23 で意図的に残した「Day24 Top priority」を片付けた technical debt 解消
セッション + Day24 Task 1 reconnaissance で新 corpus に parser DOI-boundary
bug を発見し Day25+ task として記録.

## 主要成果

| 指標 | Day23 末 | Day24 末 |
|:---|:---:|:---:|
| 全 tests | 52 passed / 50 skipped | **100 passed / 0 skipped** |
| skipped test 削減 | 50 | **-50 (skip 完全解消)** |
| 改修 test file | — | 5 file (mdpi_parser / overrides_contract / journal_audit / pre_integration_baseline / split_references_doi_boundary) |
| byte-level golden 依存 | 4 test | 0 (全て構造 assertion に refactor) |
| corpus-specific assertion | 多数 (149-ref Bray globocan #1 / De Boeck #149 / van der Biessen #40 / van Zyl #140 / line numbers 567-910 等) | 新 corpus 固有のみ (171 count / gap [55,79] / #69 van Vliet / #92 van den Burg / #173 de Menezes 等) |
| 新発見 Day25+ bug | — | **split_references DOI-boundary bug** (Day24 Task 1 recon、#55/#79 が #54/#78 に merge) |

## Day24 archive 構成

- `README.md` — 本ファイル (Day24 index)
- `DAY24_LESSONS_LEARNED.md` — Day24 教訓記録 (D24-1, D24-2, D24-3)
- `../../superpowers/specs/2026-05-24-day24-mdpi-test-restoration-design.md` — Day24 spec
- `../../superpowers/plans/2026-05-24-day24-mdpi-test-restoration.md` — Day24 plan

## Day24 commits (chain、5 件)

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `8d7df22` | docs(spec) | Day24 MDPI test restoration spec |
| 2 | `b7e5b58` | docs(plan) | Day24 implementation plan |
| 3 | `357dfe9` | test(refactor) | 5 file 一括 re-point + structural refactor + skip 解除 (212+/281-) |
| 4 | `4e0eb36` | style(tests) | unused json imports cleanup (fixup) |
| 5 | (this commit) | docs(sessions) | Day24 archive |

## 設計判断

実装 approach は **Q1 (α) 構造 test refactor + Q2 (α) 1 atomic commit** を採用
(spec §1.4). 代替案 Q1 (β) Phase 1 のみ byte-match / Q1 (γ) test 削除 (B/C 級)
は regression coverage の保ち方が中途半端のため不採用.

各 file の改修戦略は spec §3 per-file detail に従い、byte-level golden 依存度
の濃淡に応じて refactor 強度を調整 (mdpi_parser/journal_audit は局所改修、
pre_integration_baseline/doi_boundary は全面 rewrite、overrides_contract は 1
test のみ削除).

## Day24 Task 1 reconnaissance による新発見 (Day25+ task)

新 mdpi_173refs corpus に対する Phase 1 出力を /tmp に dump して boundary
edge case を分析した結果、**split_references() が DOI URL 直後の `<N>.` boundary
を検出できず、#55 と #79 がそれぞれ #54 と #78 に merge されている** ことが判明.

- 該当 ref: #54 (569ch, includes #55 content), #78 (569ch, includes #79 content)
- 結果: parsed count = 171 (本来の 173 から 2 件減)
- Day24 では test 側で current state を assert (tripwire pattern)、Day25+ で
  parser fix を入れた時点で関連 assertion を更新する想定

## Day25+ 候補

- **Top priority**: split_references DOI-boundary parser fix (Day24 Task 1 で発見)
- mdpi_173refs 固有の manual_overrides.yaml 構築 (Day25+ で parser 出力に
  応じた override 追加、本 Day24 で残置した 4 entry (66/137/141/148) の刷新)
- pre-commit hook gitleaks 自動実行 (Day22 handoff パターン 3)
- CONTRIBUTING.md / Issue PR template (Day22 handoff パターン 2)
- PyPI 公開 (v0.2.0 候補)
- pyproject.toml + uv.lock 移行 (CLAUDE.md §8 整合)
- Crossref graceful failure 16 件の対応 (Day22 §6.3 NEW、apa_45refs)
- NLM fuzzy-match precision 改善 (Day22 §6.3 NEW)
- tools/build_*_fixture.py の共通 utility refactor (Day23 code review 指摘)
- deterministic byte-level golden の再構築 (LLM stub 経由、Day26+ 大改修)
