# Day28: Latin Extended-A 拡張 (Day26 機構の延伸)

**実施日**: 2026-05-28
**起点 commit**: `9a46214` (Day28 spec commit)
**完了 commit**: `08a0b90` (Day28 Task 2 TDD GREEN)

## §1 概要

Day26 で完成した `_UPPERCASE_LATIN1` DRY 機構 (定数 1 個 + 8 箇所 rf-string
参照) を実際に活用し、Latin Extended-A 大文字 (Ā-Ž = U+0100-U+017D) を著者
姓 boundary regex の認識範囲に追加した。

## §2 成果

| 項目 | Day27 末 | Day28 末 | 差分 |
|:---|:---:|:---:|:---:|
| `_UPPERCASE_LATIN1` 文字数 | 9 | 12 | +3 (`Ā-Ž`) |
| 対応 Unicode 範囲 | Basic Latin + Latin-1 Supplement | + Latin Extended-A | + U+0100-U+017D |
| `main.py` 内コード変更箇所 | — | 1 行 (定数値) | + docstring update |
| tests passed | 111 | 115 | +4 |
| commit 数 | — | 5 | spec + plan + RED + GREEN + archive |

## §3 commit chain

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `9a46214` | docs(spec) | Day28 Latin Extended-A expansion spec |
| 2 | `00a00b1` | docs(plan) | Day28 Latin Extended-A expansion plan |
| 3 | `221adf8` | test(prep) | failing unit tests (TDD RED) |
| 4 | `08a0b90` | fix(parse) | _UPPERCASE_LATIN1 拡張 (TDD GREEN) |
| 5 | (本 commit) | docs(sessions) | archive (this commit) |

## §4 関連ドキュメント

- [Spec](../../superpowers/specs/2026-05-28-day28-latin-extended-a-expansion-design.md)
- [Plan](../../superpowers/plans/2026-05-28-day28-latin-extended-a-expansion.md)
- [LESSONS](DAY28_LESSONS_LEARNED.md)

## §5 関連セッション

- [Day25](../day25/README.md): Latin-1 Supplement 初対応 (boundary regex 5 箇所)
- [Day26](../day26/README.md): `_UPPERCASE_LATIN1` 定数化 + 8 箇所 DRY 統一
- [Day27](../day27/README.md): pyproject.toml + uv.lock 移行
