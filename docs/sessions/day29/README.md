# Day29: pre-commit gitleaks 導入 (Day23 再発防止)

**実施日**: 2026-05-28
**起点 commit**: `ddff834` (Day29 spec commit)
**完了 commit**: `adb0cde` (Day29 Task 2 follow-up: gitleaks permissions 明示)

## §1 概要

Day23 で発生した機密データ commit 事故 (fixture に peer-review 由来内容が
含まれ filter-repo + force push で対応) の再発防止を目的として、3 層防御
機構 (Local pre-commit hook + CI gitleaks job + one-shot history audit)
を導入した。

## §2 成果

| 項目 | Day28 末 | Day29 末 | 差分 |
|:---|:---:|:---:|:---:|
| pre-commit hook | 未導入 | gitleaks v8.30.1 動作中 | + Layer 1 |
| CI gitleaks job | なし | gitleaks-action@v2 + `permissions: contents: read` | + Layer 2 |
| CONTRIBUTING.md | 未作成 | 作成済 (97 行) | + 開発者ガイド |
| history audit baseline | 未確認 | **0 件**確認 (137 commits, 1.23s) | + Layer 3 (one-shot) |
| dev dependency | pytest のみ | + pre-commit>=4.0,<5.0 | + 1 件 |
| CI jobs | 3 | 4 | + gitleaks |
| tests passed | 115 | 115 | 0 (test 追加なし) |
| commit 数 | — | 5 | spec + plan + security + permissions fix + archive |

## §3 commit chain

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `ddff834` | docs(spec) | Day29 pre-commit gitleaks introduction spec |
| 2 | `5a8acdd` | docs(plan) | Day29 pre-commit gitleaks introduction plan |
| 3 | `ae47c63` | chore(security) | atomic 6-file security setup |
| 4 | `adb0cde` | ci(security) | explicit `permissions: contents: read` on gitleaks job (review I-1 fix) |
| 5 | `(本 commit)` | docs(sessions) | archive day29 session |

## §4 関連ドキュメント

- [Spec](../../superpowers/specs/2026-05-28-day29-pre-commit-gitleaks-design.md)
- [Plan](../../superpowers/plans/2026-05-28-day29-pre-commit-gitleaks.md)
- [LESSONS](DAY29_LESSONS_LEARNED.md)
- [CONTRIBUTING.md](../../../CONTRIBUTING.md)

## §5 関連セッション

- [Day23](../day23/README.md): 機密データ事故 + filter-repo 浄化 (本 session の動機)
- [Day27](../day27/README.md): pyproject.toml + uv.lock 体制 (本 session が依存)
- [Day28](../day28/README.md): Latin Extended-A 拡張 (前 session)
