# Day23 Session Archive (2026-05-24)

## 概要

Day23 セッションは Day22 末セッションで判明した「vancouver_24refs +
mdpi_149refs の 2 fixture が査読由来 (input_References.docx が査読
manuscript 起源) で著作権・査読守秘義務上の懸念がある」事象への
remediation セッション.

Pattern C (Private + filter-repo + force push + new fixtures) を選択し、
GitHub 上の痕跡を完全消去 + test architecture 保持 + 新 PMC OA fixture
追加を 1 セッションで完遂.

## 主要成果

| 指標 | Day22 末 | Day23 末 |
|:---|:---:|:---:|
| 全 tests | 101 passed / 1 skipped | 52 passed / 50 skipped |
| 機密性懸念 fixture | 2 件 (Public で 3 日露出) | 0 件 (history からも消去) |
| Vancouver fixture | vancouver_24refs (OneDrive 由来) | vancouver_35refs (PMC13179246, Supportive Care in Cancer, CC BY 4.0) |
| MDPI fixture | mdpi_149refs (出典不明) | mdpi_173refs (PMC13164670, Nutrients, CC BY 4.0) |
| repo visibility | PUBLIC | PRIVATE 経由 → PUBLIC 復帰 |
| .git size | ~11 MB | ~1.2 MB (約 90% 削減) |
| LLM cost (新 fixture) | — | ~$2-3.5 |

50 skipped の内訳: Day23 Phase 1 で mdpi_149refs を hard-code 参照する
5 test file (test_mdpi_parser.py / test_overrides_contract.py / test_journal_audit.py
/ test_pre_integration_baseline.py / test_split_references_doi_boundary.py)
に module-level pytestmark.skip を付与 (reason="awaiting Day23 Phase 5 new
MDPI fixture"). Day24+ で新 mdpi_173refs fixture に re-point + skip 解除予定.

## Day23 archive 構成

- `README.md` — 本ファイル (Day23 index)
- `DAY23_LESSONS_LEARNED.md` — Day23 教訓記録
- `../../superpowers/specs/2026-05-24-day23-fixture-remediation-design.md` — Day23 spec
- `../../superpowers/plans/2026-05-24-day23-fixture-remediation.md` — Day23 plan

## Day23 commits (chain)

(filter-repo 後の新 SHA で記載。Day22 SHA は Day22 README で Day23 中に更新済)

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `c50e34c` | docs(spec) | Day23 fixture remediation spec |
| 2 | `f986104` | docs(plan) | Day23 implementation plan |
| 3 | `3c676ec` | chore(remove) | vancouver/mdpi fixture + tests 削除 + 5 file skip-mark |
| (Phase 2: filter-repo、no commit、108 commits rewritten) | | | |
| (Phase 3: force push + tag/release 再作成、no commit) | | | |
| 4 | `95118d3` | chore(security) | .gitleaksignore 全 7 fingerprint refresh |
| 5 | `bcb72ce` | docs(sessions) | Day22 archive SHA 表 update |
| 6 | `eee1d67` | feat(fixtures) | Vancouver + MDPI replacement fixtures + 2 build tools |
| 7 | `3d96399` | test(integration) | 新 integration tests 8+8 |
| 8 | (this commit) | docs(sessions) | Day23 archive |

## 設計判断

実装 approach は **Pattern C (Private + filter-repo + force push + new fixtures)** を採用 (spec §1.4 参照)。代替案 Pattern A (soft 削除のみ、history 残存) と Pattern B (Private 切替のみ) では「git history に痕跡残置 + SHA 経由で取得可能」という機密性侵害が残るため、Pattern C で完全消去。

新 fixture は user 専門領域 fit を重視し、Vancouver は Supportive Care in Cancer (CBT 介入)、MDPI は Nutrients review (Adipocyte/Insulin) を選定。両方 CC BY 4.0 で出典明示済 README を fixture ディレクトリに同梱。

## Day24+ 候補

- **Top priority**: skip-mark した 5 test file を新 mdpi_173refs fixture に re-point + skip 解除 (Day23 D23-X として記録)
- pre-commit hook gitleaks 自動実行 (Day22 handoff パターン 3)
- CONTRIBUTING.md / Issue PR template (Day22 handoff パターン 2)
- PyPI 公開 (v0.2.0 候補)
- pyproject.toml + uv.lock 移行 (CLAUDE.md §8 整合)
- Crossref graceful failure 16 件の対応 (Day22 §6.3 NEW、apa)
- NLM fuzzy-match precision 改善 (Day22 §6.3 NEW)
- tools/build_*_fixture.py の共通 utility への refactor (4 tools 出揃ったため、Day23 code review でも指摘)
