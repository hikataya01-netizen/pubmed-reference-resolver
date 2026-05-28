# Day28 Lessons Learned (2026-05-28)

## §1 概要

Day26 で構築した DRY 機構 (`_UPPERCASE_LATIN1` 定数 + 8 箇所 rf-string 参照)
を実際に活用し、Latin Extended-A 大文字を著者姓 boundary regex に追加した。
コード変更は実質 1 行 (定数右辺) + docstring update のみ。

### §1.1 セッション開始時の状態

- 111 passed / 0 skipped (Day27 末)
- `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` (Day26 末から無変更)
- pyproject.toml + uv.lock 体制 (Day27 移行済)

### §1.2 セッション終了時の状態

- 115 passed / 0 skipped / 0 failed (+ 4 unit test)
- `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-ÞĀ-Ž"` (12 chars、Latin Extended-A 追加)
- 8 箇所の rf-string 参照は **無変更** (自動伝播確認)
- LLM cost: $0 (refactor + test 追加、外部 API 呼び出しなし)

---

## §2 設計上の発見

### §2.1 Python `re` の `[]` 文字クラスと Latin Extended-A の構造的制約

最大の発見は **Latin Extended-A の大文字小文字交互配置構造により、Python
`re` の `[]` 文字クラスでは大文字専用レンジを構造的に作れない** こと。

| ブロック | code point 構造 | 大文字専用レンジ可能? |
|:---|:---|:---:|
| Basic Latin | `A-Z` (U+0041-U+005A) 連続後、`a-z` (U+0061-U+007A) 連続 | ✓ |
| Latin-1 Supplement | 大文字 `À-Þ` (U+00C0-U+00DE) と小文字 `ß-ÿ` (U+00DF-U+00FF) が分離 | ✓ (Day25/26) |
| **Latin Extended-A** | Ā (U+0100) ā (U+0101) Ă (U+0102) ă (U+0103) ... 交互配置 | **✕** |
| Latin Extended-B | 同様に交互配置中心 | ✕ |

brainstorm 段階で「strict 3-range (`Ā-ĶĹ-ŇŊ-Ž`) で大文字精密制御可能」と
仮定していたが、実証スクリプトで以下が判明:

```python
import re
strict = '[A-ZÀ-ÖØ-ÞĀ-ĶĹ-ŇŊ-Ž]'  # 大文字 3 連続レンジ「のつもり」
loose  = '[A-ZÀ-ÖØ-ÞĀ-Ž]'        # 1 レンジ

# Latin Extended-A 小文字を 64 文字与えると...
lowercase = 'āăąćĉċč...'  # 64 chars
print(len(re.findall(strict, lowercase)))  # → 59
print(len(re.findall(loose, lowercase)))   # → 63
```

strict 3-range でも 59/64 (92%) の小文字が match する。これは Python `re`
の `[]` が code point 連続レンジを取るためで、`Ā-Ķ` は実際には U+0100-U+0136
の **全** code point を含む (中の小文字 ā ă ą ć ĉ ċ ... も全部)。

つまり Day25 で確立した「Latin-1 Supplement 大文字専用レンジ」のアプローチ
は、Latin Extended-A では構造的に再現不可能。

### §2.2 採用した妥協案: Loose 1-range + boundary 文脈の制約に依存

Option I (loose 1-range `A-ZÀ-ÖØ-ÞĀ-Ž`) を採用した根拠:

1. **Strict 3-range も実質同じ false positive 特性** — 上記実証通り
2. **boundary 文脈は `(?<![\d.])\d+\.\s+` 直後** — reference 番号の後で、
   小文字始まりの著者姓は学術引用で現実的に出現しない
3. **Day26 DRY 機構の最小変更原則と整合** — 1 行 update のみで OK
4. **外部依存追加の回避** — regex ライブラリ + `\p{Lu}` 化は ROI 低

### §2.3 真の精密制御が必要な場合の選択肢 (Day29+)

将来「小文字混入を完全排除する」要件が発生した場合の候補:

| 選択肢 | コスト | 効果 |
|:---|:---:|:---:|
| `regex` ライブラリ + `\p{Lu}` | 中 (外部依存 + 8 箇所書き換え) | 完全精密 |
| `[A-Z]` + `unicodedata.category(ch) == 'Lu'` で post-filter | 大 (regex の単純さ喪失) | 完全精密 |
| code point 個別列挙 | 大 (63 文字を逐一) | 完全精密、可読性悪 |

現時点では boundary 文脈の制約により loose 1-range で十分機能するため、
これらは Day29+ 候補として記録。

---

## §3 Day26 DRY 機構の効果実証

Day26 で構築した「定数 1 個 + 8 箇所 rf-string 参照」機構が、Day28 で文字
通り「1 行 update で全 8 箇所に自動伝播」したことを実証した。

| 観点 | 効果 |
|:---|:---|
| **拡張の所要時間** | 定数 1 行修正 (5 秒) + docstring update (1 分) |
| **影響範囲の確認コスト** | `grep '_UPPERCASE_LATIN1'` で 7 行 (1 定義 + 5 rf-string + 1 comment)、即座 |
| **回帰 risk** | 0 (参照側コード無変更) |
| **TDD GREEN 達成** | test 追加 → 定数 1 行 update のみで 4/4 PASS |

これは Day25 で経験した「同じ修正を 5 箇所に手で配る作業」(forget リスク
3 箇所 + Day26 で発覚) の対極にある。**DRY refactor の長期 ROI は劇的に
高い** ことを実証。

---

## §4 brainstorm/spec/plan の流れと所要時間

| 段階 | 内容 | commit |
|:---:|:---|:---:|
| 1 | brainstorm: 3 つの設計 Question (拡張範囲/test 選定/commit 戦略) を AskUserQuestion で確定 | — |
| 2 | spec 書き出し + self-review (string length 訂正) | `9a46214` |
| 3 | plan 書き出し + Task 1/2/3 を bite-sized step に分解 | `00a00b1` |
| 4 | Task 1 TDD RED (4 test 追加、全 FAIL 確認) | `221adf8` |
| 5 | Task 2 TDD GREEN (定数 1 行 update、4 test PASS 化、115 passed 全体 PASS) | `08a0b90` |
| 6 | Task 3 archive (README + LESSONS) + push + CI 確認 | (本 commit) |

self-review で発見した訂正点 (spec):

- string length を `"14 chars"` → `"12 chars"` (After 値の正確な文字数)
- Before 値に `# 9 chars` 注記追加

self-review で発見した訂正点 (plan):

- spec の test 例が `startswith("1. ...")` だったが、実 API は `.raw_text.
  startswith("著者姓")` (RefBlock dataclass の `.raw_text` 属性)。plan では
  実 API に揃えた。
- grep 期待行数を `9` から `7` に訂正 (1 定義 + 5 rf-string + 1 comment)。

---

## §5 Day29+ 候補

### Top priority (Day28 LESSONS から派生)

1. **`regex` ライブラリ + `\p{Lu}` への移行**
   - 動機: Latin Extended-A の小文字混入を完全排除
   - 規模: 外部依存追加 (`uv add regex`) + 8 箇所書き換え + test 追加
   - ROI: 現時点では低 (boundary 文脈で false positive 影響ゼロ)、ただし
     Latin Extended-B/Additional 拡張時には ROI 上昇

2. **PMC OA fixture を用いた integration test**
   - 動機: Day28 は unit test のみ。Latin Extended-A 著者を含む実 paper の
     end-to-end 検証は未実施
   - 規模: PMC OA から Š/Ł/Č 著者を含む論文を 1 件選定 → fixture 化 →
     既存 test_integration_* パターンで integration test
   - ROI: 中 (Day23 fixture 著作権事案を踏まえ PMC OA の選定が必要)

### Medium priority (既存候補から引き継ぎ)

3. **PyPI 公開化** (Day27 LESSONS から継続)
4. **pre-commit hook gitleaks 自動化**
5. **CONTRIBUTING.md / Issue PR template 整備**
6. **dev tool setup (ruff, mypy)**
7. **CI python-version-file SoT 化**
8. **Node.js 20 deprecation 対応** (Day28 CI annotation で観測。actions/checkout@v5 等への bump)

### Low priority (将来オプション)

9. Latin Extended-B / Extended Additional 拡張 (要件発生時に 1 行 update)
10. Crossref graceful failure (apa_45refs の 16 件)
11. NLM fuzzy-match 精度改善

---

## §6 メトリクス

| 指標 | 値 |
|:---|:---:|
| brainstorm 質問数 | 3 (Q1/Q2/Q3) |
| commit 数 | 5 (spec/plan/RED/GREEN/archive) |
| `main.py` 行数変更 | +14 / -7 (docstring 拡充 + 定数右辺更新) |
| tests/test_main_split_references.py 行数変更 | +58 (4 test + docstring + section header) |
| 新規 unit test 件数 | 4 |
| 全体 tests passed | 111 → 115 |
| skipped | 0 → 0 |
| LLM cost | $0 |
| CI build time | test 3.11: 10s, test 3.12: 10s, test-experimental 3.14: 含 (all 3 jobs green, run 26553898275) |

---

## §7 関連参照

- [Spec](../../superpowers/specs/2026-05-28-day28-latin-extended-a-expansion-design.md)
- [Plan](../../superpowers/plans/2026-05-28-day28-latin-extended-a-expansion.md)
- [Day25 LESSONS](../day25/DAY25_LESSONS_LEARNED.md)
- [Day26 LESSONS](../day26/DAY26_LESSONS_LEARNED.md)
- [Day27 LESSONS](../day27/DAY27_LESSONS_LEARNED.md)
