# Day28: Latin Extended-A 拡張 — 設計仕様 (Design Spec)

**作成日**: 2026-05-28
**対象セッション**: Day28
**前提セッション**: Day25 (Latin-1 Supplement 対応) → Day26 (DRY refactor + `_UPPERCASE_LATIN1` 定数化) → Day27 (pyproject/uv 移行)
**起点 commit**: `d313851` (Day27 archive)

---

## §1 背景と目的

### §1.1 Day25/Day26 までの到達点

| Day | 成果 | 残課題 |
|:---|:---|:---|
| Day25 | `split_references` の boundary regex を `[A-Z]` → `[A-ZÀ-ÖØ-Þ]` (Latin-1 Supplement 大文字) に拡張。MDPI 173 refs corpus の Å/Ö 著者で 171/173 → 173/173 解決。 | `[A-ZÀ-ÖØ-Þ]` は 5 箇所のみで適用、残 3 箇所 (`_strip_pre_references`、preprocess counter) は bare `[A-Z]` のまま |
| Day26 | `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` を module-level 定数化、8 箇所すべてを `rf"...[{_UPPERCASE_LATIN1}]..."` に統一。DRY 完了。 | Latin Extended-A (Š Č Ł Ż 等中欧・東欧著者名) は未対応 |
| Day27 | pyproject.toml + uv.lock 移行。CLAUDE.md §8 と整合。 | Day26 の機構を実際に再利用する初回検証はまだない |

### §1.2 Day28 で扱う問題

中欧・東欧言語(チェコ・ポーランド・ハンガリー・スロバキア・スロベニア等)の著者姓は **Latin Extended-A** (U+0100-U+017F) 範囲の大文字を含むケースが多い:

| 著者 | 国 | 含む大文字 | code point |
|:---|:---|:---:|:---|
| **Š**afránek | チェコ | Š | U+0160 |
| **Ł**ukasiewicz | ポーランド | Ł | U+0141 |
| **Č**ech | チェコ | Č | U+010C |
| **Ż**elazny | ポーランド | Ż | U+017B |
| **Ő**ri / K**ő**rösi | ハンガリー | Ő | U+0150 |
| **Ž**ižek | スロベニア | Ž | U+017D |

これらの著者名が reference list の境界(`\d+. ` 直後)に現れた場合、現在の `[A-ZÀ-ÖØ-Þ]` は match に失敗し、Day25 で MDPI 173 corpus に発生したのと同種の boundary loss(split miss)が発生し得る。

### §1.3 Day28 の目的

1. **機能**: `_UPPERCASE_LATIN1` を Latin Extended-A 大文字に拡張する
2. **回帰防止**: Latin Extended-A 著者名を含む reference の boundary 検出に対する unit test を追加する
3. **Day26 機構の実証**: 「定数 1 行 update → 8 箇所に rf-string 経由で伝播」が宣伝通り機能することを実証する

---

## §2 設計上の Question と採用案

### §2.1 Q1: regex 拡張方式の選択

Latin Extended-A は大文字・小文字が **交互配置** (U+0100 Ā / U+0101 ā / U+0102 Ă / U+0103 ă / ...) で、Latin-1 Supplement のような「大文字専用レンジ」を簡潔に取れない。3 つの選択肢を評価した:

| Option | 定数値 | 大文字精度 | 小文字 false positive | 評価 |
|:---|:---|:---:|:---|:---:|
| **(I) Loose 1-range** ✓ | `"A-ZÀ-ÖØ-ÞĀ-Ž"` (12 chars) | 100% (63/63) | 63/64 (理論上) | **採用** |
| (II) Strict 3-range | `"A-ZÀ-ÖØ-ÞĀ-ĶĹ-ŇŊ-Ž"` (18 chars) | 100% (63/63) | 59/64 (実質 Loose と同等) | ✕ |
| (III) regex + `\p{Lu}` | (外部 ライブラリ + 8 箇所書き換え) | 100% | 0% | ✕ |

**採用根拠**:

- Option I と II は実質同じ false positive 特性。Python `re` の `[]` は code point 連続レンジを取るため、Latin Extended-A の交互配置構造により strict 指定でも小文字混入は避けられない
- Option III は唯一の真の精密制御だが、外部依存追加 + 8 箇所書き換えで Day26 機構の最小変更原則と衝突
- boundary 文脈は `(?<![\d.])\d+\.\s+` 直後(reference 番号の後)で、現実的に小文字始まりの著者姓は出現しない。よって false positive のリアルワールド影響はほぼゼロ
- Day26 の「定数 1 行 update で 8 箇所伝播」原則と整合的

### §2.2 Q2: unit test 著者名の選定

| Option | 概要 | 評価 |
|:---|:---|:---:|
| **(α) 典型例 4 名** ✓ | Šafránek / Łukasiewicz / Čech / Żelazny を fixture に直接 embed | **採用** |
| (β) 実 corpus + 典型例 | MDPI/PubMed から実 reference を抽出 + 典型例 | ✕ (fixture 設計コスト + 著作権 review コスト) |
| (γ) Minimal 1-2 名 | Šafránek のみ等 | ✕ (カバレッジ不足) |

**採用根拠**: Day23 で fixture 著作権事案を経験済み。典型例直接 embed は法的 risk 最小、boundary regex の動作実証には十分。中欧 (Č/Ž)・北欧 (Š) ・東欧 (Ł/Ż) を網羅する 4 名は学術引用での典型分布をカバー。

### §2.3 Q3: commit 戦略

| Option | 概要 | 評価 |
|:---|:---|:---:|
| **(α) TDD 2-commit (Day26 と同じ)** ✓ | `test(prep)` RED → `fix(parse)` GREEN | **採用** |
| (β) 1 atomic commit | test + 定数 update を 1 commit | ✕ (RED/GREEN 証跡が history に残らない) |
| (γ) Day20 D20-3 inline | spec/plan 省略、session 内 inline 実装 | ✕ (Day22-27 workflow と不整合) |

**採用根拠**: Day25/26 と同じ TDD discipline を保持。spec + plan + 2-commit + archive の 5 commit chain で history 品質を確保。

---

## §3 Architecture

### §3.1 変更対象

**main.py L293-299**:

```python
# Before
# (Day26 docstring)
# - U+00D7 (× multiplication sign) is intentionally EXCLUDED.
# Day25 (split_references) と Day26 (_strip_pre_references + preprocess
# ref_blocks_found counter) で導入. Day27+ で Latin Extended-A (Š Č Ł 等)
# 拡張時は本定数を 1 行 update で 8 箇所へ伝播.
_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"     # 9 chars

# After
# (Day28 で更新)
# - U+00D7 (× multiplication sign) は意図的に EXCLUDE.
# - Latin Extended-A 大文字 (Ā-Ž = U+0100-U+017D) を Day28 で追加。
#   Latin Extended-A は大文字小文字交互配置のため、Python `re` の `[]` 文字
#   クラスでは大文字専用レンジを取れない (Loose 1-range)。boundary 文脈
#   (`\d+\.\s+` 直後) では小文字始まり著者姓は現実的に出現しないため、
#   false positive のリアルワールド影響はゼロ。
# - 将来 Latin Extended-B / Extended Additional 拡張時も本定数を 1 行 update
#   で 8 箇所へ伝播。精密大文字制御が必要になった場合は regex ライブラリ +
#   \p{Lu} 化を Day29+ で検討。
_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-ÞĀ-Ž"  # 12 chars
```

### §3.2 無変更箇所

`_UPPERCASE_LATIN1` を rf-string 経由で参照する 8 箇所 (L313, L317, L367, L434×4, L452×4) は **コード変更なし**。Day26 機構により自動的に新範囲が伝播する。

### §3.3 新規 unit test (tests/test_main_split_references.py)

Day26 で追加した既存 test の隣に 4 件追加する:

```python
def test_split_references_with_latin_extended_a_safranek() -> None:
    """Latin Extended-A 大文字 Š (U+0160) が boundary regex で recognize されること."""
    text = "1. Šafránek M, Novák J. Title A. J. 2024;1:1.\n2. Smith B. Title B. J. 2024;2:2."
    refs = split_references(text)
    assert len(refs) == 2
    assert refs[0].startswith("1. Šafránek")
    assert refs[1].startswith("2. Smith")


def test_split_references_with_latin_extended_a_lukasiewicz() -> None:
    """Latin Extended-A 大文字 Ł (U+0141) が boundary regex で recognize されること."""
    text = "1. Łukasiewicz J, Kowalski A. Title A. J. 2024;1:1.\n2. Brown C. Title B. J. 2024;2:2."
    refs = split_references(text)
    assert len(refs) == 2
    assert refs[0].startswith("1. Łukasiewicz")
    assert refs[1].startswith("2. Brown")


def test_split_references_with_latin_extended_a_cech() -> None:
    """Latin Extended-A 大文字 Č (U+010C) が boundary regex で recognize されること."""
    text = "1. Čech V, Dvořák P. Title A. J. 2024;1:1.\n2. Jones D. Title B. J. 2024;2:2."
    refs = split_references(text)
    assert len(refs) == 2
    assert refs[0].startswith("1. Čech")
    assert refs[1].startswith("2. Jones")


def test_split_references_with_latin_extended_a_zelazny() -> None:
    """Latin Extended-A 大文字 Ż (U+017B) が boundary regex で recognize されること."""
    text = "1. Żelazny K, Wójcik M. Title A. J. 2024;1:1.\n2. Davis E. Title B. J. 2024;2:2."
    refs = split_references(text)
    assert len(refs) == 2
    assert refs[0].startswith("1. Żelazny")
    assert refs[1].startswith("2. Davis")
```

### §3.4 期待される test count 変化

| 段階 | tests passed | tests added | 検出される FAIL |
|:---|:---:|:---:|:---:|
| 開始時 (Day27 archive) | 111 | 0 | 0 |
| TDD RED commit 直後 | 111 | +4 | 4 FAIL |
| TDD GREEN commit 直後 | 115 | 0 (既存) | 0 |
| Day28 完了時 | **115** | — | **0** |

---

## §4 Error handling

### §4.1 既存 fallback chain は無変更

`split_references` の boundary 検出は 4 段階の fallback chain (number-anchor → period-anchor → semicolon-anchor → newline-anchor) を持つが、`_UPPERCASE_LATIN1` の拡張はすべての段で同じ範囲を共有する。よって既存 fallback chain に semantic 変更はない。

### §4.2 拡張範囲外の文字

- **Latin Extended-B** (U+0180-U+024F): ǎ ǐ ǒ ǔ 等。中越拼音、IPA。学術引用での出現極稀。未対応。
- **Latin Extended Additional** (U+1E00-U+1EFF): Ḥ Ṭ ạ 等。アラビア・ベトナム翻字、サンスクリット。医学誌で稀。未対応。

これらの著者名が含まれる reference は依然 boundary 検出に失敗し得る。`_UPPERCASE_LATIN1` の 1 行 update + unit test 追加で対応可能だが、現時点では YAGNI 原則で見送り。

### §4.3 false positive のリアルワールド影響

- Python `re` の `[]` 文字クラスは Latin Extended-A の小文字 (ā ă ą ć 等) も match 対象に含む
- ただし boundary regex は `(?<![\d.])\d+\.\s+` (reference 番号 + 空白) の **直後** の文字を検査する
- 著者姓が小文字始まりとなる例は学術引用では現実的に存在しない (van/de/du/den/von の prefix は別途 explicit 対応済)
- よって理論上の false positive 0/64 → 64/64 増加は、リアルワールドではゼロ影響

---

## §5 Testing 戦略

### §5.1 TDD 2-commit cycle

**Commit 1: `test(prep): add failing unit tests for Latin Extended-A boundary`**

- `tests/test_main_split_references.py` に 4 test 追加
- `pytest tests/test_main_split_references.py -v` で 4 件すべて FAIL することを確認
- FAIL message が「expected 2 refs, got 1」(boundary 検出失敗) パターンであることを確認

**Commit 2: `fix(parse): extend _UPPERCASE_LATIN1 to Latin Extended-A`**

- `main.py` L293-299 を update (docstring + 定数)
- `pytest tests/ -v` で全 115 test PASS を確認
- 既存 111 test に regression なし

### §5.2 Regression check

- `uv run pytest tests/ -v` 全実行
- 期待: 115 passed / 0 skipped / 0 failed

---

## §6 File structure (session lifecycle)

| File | 状態 | 段階 |
|:---|:---:|:---|
| `docs/superpowers/specs/2026-05-28-day28-latin-extended-a-expansion-design.md` | new | brainstorm 完了時 commit |
| `docs/superpowers/plans/2026-05-28-day28-latin-extended-a-expansion.md` | new | writing-plans 完了時 commit |
| `tests/test_main_split_references.py` | modify | TDD RED commit |
| `main.py` | modify | TDD GREEN commit |
| `docs/sessions/day28/README.md` | new | archive commit |
| `docs/sessions/day28/DAY28_LESSONS_LEARNED.md` | new | archive commit |

合計 commit 数 (期待値): **5**(spec → plan → RED → GREEN → archive)

---

## §7 LESSONS で記録すべき発見事項

Day28 brainstorm 中に発見された設計上の知見を archive 時に LESSONS に記録する:

1. **Python `re` の `[]` は Latin Extended-A の大文字小文字を分離できない**
   - 構造的に交互配置のため、strict 3-range も loose 1-range も実質同じ false positive 特性
   - boundary 文脈では現実的影響ゼロだが、将来要件によっては `regex` ライブラリ + `\p{Lu}` 化が候補

2. **Day26 機構の宣伝通りの効果**
   - `_UPPERCASE_LATIN1` の 1 行 update で 8 箇所へ自動伝播
   - Day28 の実装は事実上「定数 1 行書き換え + test 追加」のみ
   - DRY refactor の長期 ROI を実証

3. **Day29+ 候補**
   - Latin Extended-B / Extended Additional 拡張 (再度 1 行 update、要件発生時)
   - `regex` ライブラリ + `\p{Lu}` 化 (精密大文字制御が必要になった場合)

---

## §8 Out of scope (明示的に Day28 では扱わない事項)

- 著者名以外の Unicode 拡張 (タイトル中の特殊文字、journal name の Unicode 等)
- Latin Extended-B / Extended Additional の拡張
- `regex` ライブラリ導入による `\p{Lu}` 精密化
- PMC OA fixture を用いた integration test (Day28 では unit test のみ)
- 既存 fallback chain (4 段階) の reorganize

これらは LESSONS に Day29+ 候補として記録する。

---

**End of Spec**
