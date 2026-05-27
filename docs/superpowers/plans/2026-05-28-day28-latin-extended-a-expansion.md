# Day28 Latin Extended-A 拡張 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `_UPPERCASE_LATIN1` 定数に Latin Extended-A 大文字レンジ (`Ā-Ž` = U+0100-U+017D) を追加し、Šafránek/Łukasiewicz/Čech/Żelazny 等の中欧・東欧著者名で始まる reference の boundary 検出を有効化する。

**Architecture:** Day26 で構築した DRY 機構(module-level 定数 1 個 + 8 箇所の rf-string 参照)に従い、`main.py` L299 の `_UPPERCASE_LATIN1` 1 行を `"A-ZÀ-ÖØ-Þ"` → `"A-ZÀ-ÖØ-ÞĀ-Ž"` に拡張する。8 箇所の参照点はコード変更不要(自動伝播)。TDD 2-commit cycle (Day26 と同じ discipline)。

**Tech Stack:** Python 3.14, `re` (標準), pytest 9.x, uv 0.11.x

**Spec:** `docs/superpowers/specs/2026-05-28-day28-latin-extended-a-expansion-design.md`

**起点 commit:** `9a46214` (Day28 spec commit)

**期待 final state:** 115 passed / 0 skipped / 0 failed (+ 4 unit tests vs Day27)

---

## File Structure

| File | 役割 | Day28 での操作 |
|:---|:---|:---:|
| `main.py` | `_UPPERCASE_LATIN1` 定数 + 8 箇所の rf-string 参照 | modify (L289-299 のみ) |
| `tests/test_main_split_references.py` | split_references の unit test ファイル | modify (4 test 追加) |
| `docs/superpowers/plans/2026-05-28-day28-latin-extended-a-expansion.md` | この plan 自体 | new (Task 0 で commit) |
| `docs/sessions/day28/README.md` | session 末 archive | new (Task 3) |
| `docs/sessions/day28/DAY28_LESSONS_LEARNED.md` | session 末 archive | new (Task 3) |

`main.py` 内の参照点 8 箇所 (L313, L317, L367, L434×4, L452×4) は **コード変更なし**。Day26 機構により定数 update が自動伝播する。

---

## API Notes (実装前に必読)

`main.split_references(cleaned: str) -> list[RefBlock]` の戻り値は dataclass のリストで、各要素は以下の属性を持つ:

- `ref_no: int` — reference 番号 (例: `1`, `2`)
- `raw_text: str` — 番号と "." を除いた著者名以降の本文 (例: `"Smith J. Title A. Journal 2020."`)

unit test では `blocks[i].raw_text.startswith("著者姓")` で assert する (`startswith("1. 著者姓")` は誤り)。

既存 test (`test_split_references_detects_norwegian_aring_boundary` 等) も同パターンを使っている。

---

## Task 0: Plan を commit

**Files:**
- Create: `docs/superpowers/plans/2026-05-28-day28-latin-extended-a-expansion.md` (この file 自体)

- [ ] **Step 1: plan file が存在することを確認**

Run: `ls docs/superpowers/plans/2026-05-28-day28-latin-extended-a-expansion.md`
Expected: ファイルが存在 (この writing-plans skill が作成済)

- [ ] **Step 2: working tree が clean (spec commit 直後) であることを確認**

Run: `git status`
Expected:
```
On branch main
Untracked files:
  docs/superpowers/plans/2026-05-28-day28-latin-extended-a-expansion.md
```

- [ ] **Step 3: stage + commit**

```bash
git add docs/superpowers/plans/2026-05-28-day28-latin-extended-a-expansion.md
git commit -m "$(cat <<'EOF'
docs(plan): add Day28 Latin Extended-A expansion plan

TDD 2-commit cycle (Day26 と同じ discipline) で _UPPERCASE_LATIN1
定数を 1 行 update (A-ZÀ-ÖØ-Þ → A-ZÀ-ÖØ-ÞĀ-Ž) する手順を bite-sized
task に分解。4 unit test 追加で Šafránek/Łukasiewicz/Čech/Żelazny の
boundary 検出を回帰防止。期待 final: 115 passed / 0 skipped。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 4: commit 成功確認**

Run: `git log --oneline -1`
Expected: `<SHA> docs(plan): add Day28 Latin Extended-A expansion plan`

---

## Task 1: TDD RED — Latin Extended-A 用 unit test 4 件追加

**Files:**
- Modify: `tests/test_main_split_references.py` (末尾に 4 test 追加)

**目的:** Latin Extended-A 大文字 (Š/Ł/Č/Ż) で始まる著者名の reference が boundary regex で検出されることを assert する 4 test を追加する。この段階では `_UPPERCASE_LATIN1` は Day26 末の `"A-ZÀ-ÖØ-Þ"` のままなので、全 4 test は FAIL する。

- [ ] **Step 1: 現状確認 — 既存 test が pass することを baseline 確認**

Run: `uv run pytest tests/test_main_split_references.py -v 2>&1 | tail -15`
Expected: 9 passed (Day26 末の状態)

- [ ] **Step 2: test_main_split_references.py の末尾を確認 (insert 位置を決定)**

Run: `tail -5 tests/test_main_split_references.py`
Expected: 末尾は Day26 で追加された preprocess test の終わりであり、空行で終わっている

- [ ] **Step 3: 4 unit test を末尾に追加**

`tests/test_main_split_references.py` の **末尾** に以下の block を追記する:

```python


# ============================================================================
# Day28: Latin Extended-A 大文字対応 unit test
# (Šafránek/Łukasiewicz/Čech/Żelazny で始まる ref boundary の検出)
# ============================================================================


def test_split_references_detects_czech_scaron_boundary():
    """Š (U+0160、チェコ語) で始まる著者の ref boundary が検出される.

    Day28 で Latin Extended-A 拡張するまでは FAIL (boundary loss).
    Day25/26 で対応した Latin-1 Supplement (À-Þ) では Š が範囲外のため
    `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` では recognize できない.
    """
    cleaned = "1. Smith J. Title A. Journal 2020.\n2. Šafránek M. Title B. Journal 2021."
    blocks = main.split_references(cleaned)
    assert len(blocks) == 2, f"expected 2 blocks, got {len(blocks)}"
    assert blocks[1].ref_no == 2
    assert blocks[1].raw_text.startswith("Šafránek")


def test_split_references_detects_polish_lstroke_boundary():
    """Ł (U+0141、ポーランド語) で始まる著者の ref boundary が検出される.

    Day28 で Latin Extended-A 拡張するまでは FAIL.
    """
    cleaned = "1. Smith J. Title A. Journal 2020.\n2. Łukasiewicz J. Title B. Journal 2021."
    blocks = main.split_references(cleaned)
    assert len(blocks) == 2, f"expected 2 blocks, got {len(blocks)}"
    assert blocks[1].ref_no == 2
    assert blocks[1].raw_text.startswith("Łukasiewicz")


def test_split_references_detects_czech_ccaron_boundary():
    """Č (U+010C、チェコ語) で始まる著者の ref boundary が検出される.

    Day28 で Latin Extended-A 拡張するまでは FAIL.
    Latin Extended-A の lower edge (U+0100-U+0136 範囲) をカバー.
    """
    cleaned = "1. Smith J. Title A. Journal 2020.\n2. Čech V. Title B. Journal 2021."
    blocks = main.split_references(cleaned)
    assert len(blocks) == 2, f"expected 2 blocks, got {len(blocks)}"
    assert blocks[1].ref_no == 2
    assert blocks[1].raw_text.startswith("Čech")


def test_split_references_detects_polish_zdot_boundary():
    """Ż (U+017B、ポーランド語) で始まる著者の ref boundary が検出される.

    Day28 で Latin Extended-A 拡張するまでは FAIL.
    Latin Extended-A の upper edge (U+014A-U+017D 範囲) をカバー.
    """
    cleaned = "1. Smith J. Title A. Journal 2020.\n2. Żelazny K. Title B. Journal 2021."
    blocks = main.split_references(cleaned)
    assert len(blocks) == 2, f"expected 2 blocks, got {len(blocks)}"
    assert blocks[1].ref_no == 2
    assert blocks[1].raw_text.startswith("Żelazny")
```

- [ ] **Step 4: 4 新規 test がすべて FAIL することを確認 (TDD RED)**

Run: `uv run pytest tests/test_main_split_references.py -v 2>&1 | tail -25`

Expected output (要点):
```
tests/test_main_split_references.py::test_split_references_detects_czech_scaron_boundary FAILED
tests/test_main_split_references.py::test_split_references_detects_polish_lstroke_boundary FAILED
tests/test_main_split_references.py::test_split_references_detects_czech_ccaron_boundary FAILED
tests/test_main_split_references.py::test_split_references_detects_polish_zdot_boundary FAILED
========================== 4 failed, 9 passed ==========================
```

各 FAIL の root cause は `assert len(blocks) == 2, f"expected 2 blocks, got 1"` (boundary loss で 1 block に merge される) であること。

**もし 4 test のどれかが PASS したら異常**: 既存定数 `"A-ZÀ-ÖØ-Þ"` は Latin Extended-A を含まないため、PASS することはあり得ない。PASS した場合は実装環境を再確認すること(pytest cache 等)。

- [ ] **Step 5: 全体 test も実行して既存 test に影響がないことを確認**

Run: `uv run pytest tests/ -v 2>&1 | tail -5`
Expected: `4 failed, 111 passed` (Day27 末の 111 + 新規 4 FAIL)

- [ ] **Step 6: TDD RED commit**

```bash
git add tests/test_main_split_references.py
git commit -m "$(cat <<'EOF'
test(prep): add failing unit tests for Latin Extended-A boundary (Day28 Task 1 TDD RED)

Šafránek (Š, U+0160) / Łukasiewicz (Ł, U+0141) / Čech (Č, U+010C) /
Żelazny (Ż, U+017B) で始まる ref の boundary 検出を assert する 4 test
を追加。現時点では _UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ" が Latin Extended-A
を含まないため、全 4 test は boundary loss (len == 1) で FAIL する。

Day25 で Latin-1 Supplement (À-Þ) 対応、Day26 で 8 箇所 DRY refactor
した機構を、Day28 で Latin Extended-A まで延伸する TDD cycle の RED 段。
次の commit (fix(parse)) で _UPPERCASE_LATIN1 1 行 update により全 PASS
化する。

Lower edge (U+0100-U+0136: Č) と upper edge (U+014A-U+017D: Ž, Ż) の
両方をカバーする 4 ケースで、Day29+ で範囲を更に拡張する場合の
regression guard としても機能する。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 7: commit 成功確認**

Run: `git log --oneline -2`
Expected:
```
<SHA> test(prep): add failing unit tests for Latin Extended-A boundary (Day28 Task 1 TDD RED)
<SHA> docs(plan): add Day28 Latin Extended-A expansion plan
```

---

## Task 2: TDD GREEN — `_UPPERCASE_LATIN1` を Latin Extended-A に拡張

**Files:**
- Modify: `main.py:288-299` (定数 docstring + 定数値の 1 行 update)

**目的:** `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` を `"A-ZÀ-ÖØ-ÞĀ-Ž"` に拡張し、Task 1 で追加した 4 test を PASS させる。docstring も Day28 時点の記述に update する。8 箇所の参照点はコード変更なし。

- [ ] **Step 1: 変更前の状態確認**

Run: `grep -n "_UPPERCASE_LATIN1" main.py | head -5`
Expected:
```
299:_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"
313:    m = re.search(rf"(?i)\b(references|bibliography)\s+(?=\d+\.\s+[{_UPPERCASE_LATIN1}])", text)
317:    m = re.search(rf"(?<![\d.])1\.\s+[{_UPPERCASE_LATIN1}]", text)
367:    blocks = re.findall(rf"(?<![\d.])\d+\.\s+[{_UPPERCASE_LATIN1}]", text)
429:    # Latin-1 Supplement uppercase support は _UPPERCASE_LATIN1 定数 (本 file
```

- [ ] **Step 2: main.py L288-299 を docstring + 定数値で update**

`main.py` の以下 block (L288-L299) を:

```python
# Character class fragment for non-ASCII Latin uppercase author surnames.
# Used in ref-boundary regex lookaheads across split_references(),
# _strip_pre_references(), and preprocess() to recognize Norwegian/German/
# French/Spanish/Portuguese surnames starting with Å Ö É Ñ Ø Ý Þ etc.
# - A-Z: ASCII uppercase (U+0041-U+005A)
# - À-Ö: Latin-1 Supplement uppercase A-O (U+00C0-U+00D6)
# - Ø-Þ: Latin-1 Supplement uppercase remainder (U+00D8-U+00DE)
# - U+00D7 (× multiplication sign) is intentionally EXCLUDED.
# Day25 (split_references) と Day26 (_strip_pre_references + preprocess
# ref_blocks_found counter) で導入. Day27+ で Latin Extended-A (Š Č Ł 等)
# 拡張時は本定数を 1 行 update で 8 箇所へ伝播.
_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"
```

以下に置き換える:

```python
# Character class fragment for non-ASCII Latin uppercase author surnames.
# Used in ref-boundary regex lookaheads across split_references(),
# _strip_pre_references(), and preprocess() to recognize European surnames.
# - A-Z: ASCII uppercase (U+0041-U+005A)
# - À-Ö: Latin-1 Supplement uppercase A-O (U+00C0-U+00D6)
# - Ø-Þ: Latin-1 Supplement uppercase remainder (U+00D8-U+00DE)
# - Ā-Ž: Latin Extended-A range (U+0100-U+017D) - Day28 で追加。
#   中欧・東欧言語の Š Č Ž Ł Ń Ś Ć Ő Ű Ē Ī Ū Ā 等をカバー。
# - U+00D7 (× multiplication sign) は意図的に EXCLUDE。
# - 注: Latin Extended-A は大文字小文字が交互配置 (U+0100 Ā / U+0101 ā /
#   U+0102 Ă / ...) のため、Python `re` の `[]` 文字クラスでは大文字専用
#   レンジを取れない (loose 1-range)。boundary 文脈 (`\d+\.\s+` 直後) では
#   小文字始まり著者姓は現実的に出現しないため、false positive のリアル
#   ワールド影響はゼロ。精密大文字制御が必要になった場合は regex ライブラリ
#   + \p{Lu} 化を Day29+ で検討。
# Day25 (split_references) で Latin-1 Supplement 導入、Day26 で 8 箇所 DRY
# 統一、Day28 で Latin Extended-A 拡張。将来 Latin Extended-B / Extended
# Additional 拡張時も本定数を 1 行 update で 8 箇所へ伝播。
_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-ÞĀ-Ž"
```

実装には Edit tool を使い、`_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` から始まる block を上記 new block で置換する。docstring 行も含めて 1 つの Edit で置換する。

- [ ] **Step 3: 変更後の定数値確認**

Run: `grep -n '_UPPERCASE_LATIN1 = ' main.py`
Expected: 1 行のみ表示: `<line>:_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-ÞĀ-Ž"`

- [ ] **Step 4: rf-string 参照が無変更 (自動伝播確認)**

Run: `grep -n '_UPPERCASE_LATIN1' main.py | wc -l`
Expected: `7` (定数定義 1 + rf-string 参照 5 行 + comment 1 = 7 行)

```bash
grep -n '_UPPERCASE_LATIN1' main.py
```
Expected output:
```
299:_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-ÞĀ-Ž"
313:    m = re.search(rf"(?i)\b(references|bibliography)\s+(?=\d+\.\s+[{_UPPERCASE_LATIN1}])", text)
317:    m = re.search(rf"(?<![\d.])1\.\s+[{_UPPERCASE_LATIN1}]", text)
367:    blocks = re.findall(rf"(?<![\d.])\d+\.\s+[{_UPPERCASE_LATIN1}]", text)
429:    # Latin-1 Supplement uppercase support は _UPPERCASE_LATIN1 定数 (本 file
434:        rf"(?=[{_UPPERCASE_LATIN1}]|van\s|de\s+[{_UPPERCASE_LATIN1}]|du\s+[{_UPPERCASE_LATIN1}]|den\s+[{_UPPERCASE_LATIN1}]|von\s+[{_UPPERCASE_LATIN1}])"
452:            rf"(?=[{_UPPERCASE_LATIN1}]|van\s|de\s+[{_UPPERCASE_LATIN1}]|den\s+[{_UPPERCASE_LATIN1}]|von\s+[{_UPPERCASE_LATIN1}])"
```

重要な確認点:
- L299 のみ右辺が `"A-ZÀ-ÖØ-ÞĀ-Ž"` に変わっている (1 行 update)
- L313, L317, L367, L434, L452 の rf-string 内容は無変更 (Day26 機構による自動伝播)
- 行番号は docstring 拡充により全体的に下方シフトする可能性あり (行番号は参考値)

注: L429 の "Latin-1 Supplement uppercase support は" comment は Day25 の経緯コメントで、Day28 では更新不要 (LESSONS で「Day28 で Latin Extended-A 拡張済」と記録するため)。

- [ ] **Step 5: 4 新規 test がすべて PASS することを確認 (TDD GREEN)**

Run: `uv run pytest tests/test_main_split_references.py -v 2>&1 | tail -20`

Expected:
```
tests/test_main_split_references.py::test_split_references_detects_ascii_uppercase_boundary PASSED
tests/test_main_split_references.py::test_split_references_detects_norwegian_aring_boundary PASSED
tests/test_main_split_references.py::test_split_references_detects_german_oumlaut_boundary PASSED
tests/test_main_split_references.py::test_split_references_detects_french_acute_boundary PASSED
tests/test_main_split_references.py::test_split_references_does_not_detect_inside_doi_url PASSED
tests/test_main_split_references.py::test_strip_pre_references_case2_inline_header_with_aring PASSED
tests/test_main_split_references.py::test_strip_pre_references_case2_inline_header_with_ascii_baseline PASSED
tests/test_main_split_references.py::test_strip_pre_references_case3_fallback_with_oumlaut PASSED
tests/test_main_split_references.py::test_preprocess_counts_aring_refs_correctly PASSED
tests/test_main_split_references.py::test_split_references_detects_czech_scaron_boundary PASSED
tests/test_main_split_references.py::test_split_references_detects_polish_lstroke_boundary PASSED
tests/test_main_split_references.py::test_split_references_detects_czech_ccaron_boundary PASSED
tests/test_main_split_references.py::test_split_references_detects_polish_zdot_boundary PASSED
========================== 13 passed ==========================
```

- [ ] **Step 6: 全体 test で regression がないことを確認**

Run: `uv run pytest tests/ -v 2>&1 | tail -3`
Expected: `115 passed in <time>s`

`0 failed / 0 skipped / 0 error` であること。Day27 末の 111 + Day28 で +4 = 115。

- [ ] **Step 7: TDD GREEN commit**

```bash
git add main.py
git commit -m "$(cat <<'EOF'
fix(parse): extend _UPPERCASE_LATIN1 to Latin Extended-A (Day28 Task 2 TDD GREEN)

_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ" (9 chars) を "A-ZÀ-ÖØ-ÞĀ-Ž" (12 chars)
に拡張し、Latin Extended-A 大文字 (Ā-Ž = U+0100-U+017D) を著者姓 boundary
regex の認識範囲に追加。Day26 の DRY 機構により定数 1 行 update が 8 箇所
の参照点へ自動伝播し、Task 1 の 4 unit test (Šafránek/Łukasiewicz/Čech/
Żelazny) すべて PASS 化。

カバー範囲:
- 中欧 (チェコ: Š Č Ž / スロバキア: Š Č Ž Ť Ľ)
- 東欧 (ポーランド: Ł Ń Ś Ć Ż Ź / ハンガリー: Ő Ű)
- 北欧拡張 (リトアニア: Ą Ę Į Ų / ラトビア: Ā Ē Ī Ū)

設計上の注記:
- Latin Extended-A は大文字小文字が交互配置のため、Python `re` の `[]` で
  大文字専用レンジを取れない (loose 1-range)。boundary 文脈 (\\d+\\.\\s+
  直後) では小文字始まり著者姓は現実的に出現しないため、false positive
  のリアルワールド影響はゼロ。
- 精密大文字制御が必要になった場合は regex ライブラリ + \\p{Lu} を Day29+
  で検討する選択肢を残す。
- Latin Extended-B / Extended Additional は YAGNI で未対応。要件発生時に
  本定数を再度 1 行 update で対応可能。

Test results: 111 passed (Day27 末) → 115 passed (+ 4 new tests)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 8: commit 成功確認**

Run: `git log --oneline -3`
Expected:
```
<SHA> fix(parse): extend _UPPERCASE_LATIN1 to Latin Extended-A (Day28 Task 2 TDD GREEN)
<SHA> test(prep): add failing unit tests for Latin Extended-A boundary (Day28 Task 1 TDD RED)
<SHA> docs(plan): add Day28 Latin Extended-A expansion plan
```

- [ ] **Step 9: push して CI 確認**

```bash
git push origin main
```

CI ジョブの URL を取得:
```bash
gh run list --limit 1
```

CI が green になるまで待つ (約 1-3 分):
```bash
gh run watch
```

Expected: `✓ <SHA> tests` (success)

---

## Task 3: Day28 archive (README + LESSONS)

**Files:**
- Create: `docs/sessions/day28/README.md`
- Create: `docs/sessions/day28/DAY28_LESSONS_LEARNED.md`

**目的:** Day28 session の成果と学びを永続記録する。Day25/26/27 と同じディレクトリ構造を維持する。

- [ ] **Step 1: docs/sessions/day28 ディレクトリ作成**

```bash
mkdir -p docs/sessions/day28
```

- [ ] **Step 2: README.md 作成**

`docs/sessions/day28/README.md` を以下の内容で作成:

```markdown
# Day28: Latin Extended-A 拡張 (Day26 機構の延伸)

**実施日**: 2026-05-28
**起点 commit**: `9a46214` (Day28 spec commit)
**完了 commit**: <Task 2 Step 9 後の HEAD SHA を記入>

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
| 2 | `<SHA>` | docs(plan) | Day28 Latin Extended-A expansion plan |
| 3 | `<SHA>` | test(prep) | failing unit tests (TDD RED) |
| 4 | `<SHA>` | fix(parse) | _UPPERCASE_LATIN1 拡張 (TDD GREEN) |
| 5 | `<SHA>` | docs(sessions) | archive (this commit) |

## §4 関連ドキュメント

- [Spec](../../superpowers/specs/2026-05-28-day28-latin-extended-a-expansion-design.md)
- [Plan](../../superpowers/plans/2026-05-28-day28-latin-extended-a-expansion.md)
- [LESSONS](DAY28_LESSONS_LEARNED.md)

## §5 関連セッション

- [Day25](../day25/README.md): Latin-1 Supplement 初対応 (boundary regex 5 箇所)
- [Day26](../day26/README.md): `_UPPERCASE_LATIN1` 定数化 + 8 箇所 DRY 統一
- [Day27](../day27/README.md): pyproject.toml + uv.lock 移行
```

**注**: `<SHA>` プレースホルダは Step 4 で実 SHA に置換する。

- [ ] **Step 3: DAY28_LESSONS_LEARNED.md 作成**

`docs/sessions/day28/DAY28_LESSONS_LEARNED.md` を以下の内容で作成:

```markdown
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
| **影響範囲の確認コスト** | `grep '_UPPERCASE_LATIN1'` で 8 行 + 1 行 = 即座 |
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
| 3 | plan 書き出し + Task 1/2/3 を bite-sized step に分解 | (Task 0) |
| 4 | Task 1 TDD RED (4 test 追加、全 FAIL 確認) | (Task 1) |
| 5 | Task 2 TDD GREEN (定数 1 行 update、4 test PASS 化、115 passed 全体 PASS) | (Task 2) |
| 6 | Task 3 archive (README + LESSONS) + push + CI 確認 | (Task 3) |

self-review で発見した訂正点 (spec):

- string length を `"14 chars"` → `"12 chars"` (After 値の正確な文字数)
- Before 値に `# 9 chars` 注記追加

self-review で発見した訂正点 (plan):

- spec の test 例が `startswith("1. ...")` だったが、実 API は `.raw_text.
  startswith("著者姓")` (RefBlock dataclass の `.raw_text` 属性)。plan では
  実 API に揃えた。

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

### Low priority (将来オプション)

8. Latin Extended-B / Extended Additional 拡張 (要件発生時に 1 行 update)
9. Crossref graceful failure (apa_45refs の 16 件)
10. NLM fuzzy-match 精度改善

---

## §6 メトリクス

| 指標 | 値 |
|:---|:---:|
| brainstorm 質問数 | 3 (Q1/Q2/Q3) |
| commit 数 | 5 (spec/plan/RED/GREEN/archive) |
| `main.py` 行数変更 | +14 (docstring 拡充) / -3 (定数右辺更新含む) ≈ net +11 行 |
| tests/test_main_split_references.py 行数変更 | +約 60 (4 test + docstring + section header) |
| 新規 unit test 件数 | 4 |
| 全体 tests passed | 111 → 115 |
| skipped | 0 → 0 |
| LLM cost | $0 |
| CI build time | <Task 2 Step 9 で確認した実値> |

---

## §7 関連参照

- [Spec](../../superpowers/specs/2026-05-28-day28-latin-extended-a-expansion-design.md)
- [Plan](../../superpowers/plans/2026-05-28-day28-latin-extended-a-expansion.md)
- [Day25 LESSONS](../day25/DAY25_LESSONS_LEARNED.md)
- [Day26 LESSONS](../day26/DAY26_LESSONS_LEARNED.md)
- [Day27 LESSONS](../day27/DAY27_LESSONS_LEARNED.md)
```

**注**: `<Task 2 Step 9 で確認した実値>` プレースホルダは Step 4 で実値に置換する。

- [ ] **Step 4: Task 1/2 の SHA と CI build time を実値に置換**

実際の SHA / CI build time を取得して plan template の `<SHA>` 等を埋める。

Run: `git log --oneline -5`
Run: `gh run list --limit 3`

取得した値で README.md と DAY28_LESSONS_LEARNED.md の以下プレースホルダを Edit ツールで置換:

- README.md §1 の `完了 commit: <Task 2 Step 9 後の HEAD SHA>` → 実 SHA
- README.md §3 の Task 2/3/4/5 行の `<SHA>` → 実 SHA
- LESSONS §6 の `<Task 2 Step 9 で確認した実値>` → 実 CI build time

- [ ] **Step 5: archive commit**

```bash
git add docs/sessions/day28/README.md docs/sessions/day28/DAY28_LESSONS_LEARNED.md
git commit -m "$(cat <<'EOF'
docs(sessions): archive day28 Latin Extended-A expansion session

Day26 で構築した `_UPPERCASE_LATIN1` DRY 機構を実際に活用し、Latin
Extended-A 大文字 (Ā-Ž = U+0100-U+017D) を著者姓 boundary regex に
追加した session の成果と学びを永続記録。

主要 finding:
- Python `re` の `[]` は Latin Extended-A の大文字小文字交互配置を
  構造的に分離できない (strict 3-range も loose 1-range も実質同じ
  false positive 特性)
- Day26 DRY 機構の効果実証: 1 行 update で 8 箇所自動伝播、回帰 risk 0
- boundary 文脈 (\\d+\\.\\s+ 直後) の制約により false positive リアル
  ワールド影響はゼロ

成果: 111 passed → 115 passed (+ 4 unit tests)、commit 5、LLM cost $0

Day29+ 候補として regex ライブラリ + \\p{Lu} 化、PMC OA integration
test 等を LESSONS に記録。

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: archive commit を push して CI 確認**

```bash
git push origin main
gh run watch
```

Expected: `✓ <SHA> tests` (success)

- [ ] **Step 7: 最終 state 確認**

Run: `git log --oneline -6`
Expected:
```
<SHA> docs(sessions): archive day28 Latin Extended-A expansion session
<SHA> fix(parse): extend _UPPERCASE_LATIN1 to Latin Extended-A (Day28 Task 2 TDD GREEN)
<SHA> test(prep): add failing unit tests for Latin Extended-A boundary (Day28 Task 1 TDD RED)
<SHA> docs(plan): add Day28 Latin Extended-A expansion plan
9a46214 docs(spec): add Day28 Latin Extended-A expansion spec
d313851 docs(sessions): archive day27 pyproject.toml + uv.lock migration session
```

Run: `uv run pytest tests/ -v 2>&1 | tail -3`
Expected: `115 passed in <time>s`

---

## Self-review notes (writer から実装者へのメモ)

### Spec → Plan の divergence point

- Spec §3.3 の test 例は `assert refs[0].startswith("1. Šafránek")` という形式だったが、`main.split_references` の実 API は `list[RefBlock]` を返し、各 `RefBlock` は `.ref_no: int` と `.raw_text: str` を持つ。`raw_text` は番号と "." を除いた本文 (例: `"Šafránek M. Title B. Journal 2021."`)。本 plan では実 API に揃えた。

### Plan の test 関数命名規則

- 既存 (Day25): `test_split_references_detects_norwegian_aring_boundary` (Å → norwegian aring)
- 新規 (Day28): `test_split_references_detects_czech_scaron_boundary` (Š → czech scaron) 等

### test count の計算 (再掲)

- Day27 末: 111 passed (tests/ 全体)
- Day28 Task 1 後: 4 failed (新規) + 111 passed (既存) = 115 total
- Day28 Task 2 後: 115 passed / 0 failed

### 8 箇所参照点の grep 結果サンプル

```
main.py:299:_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-ÞĀ-Ž"
main.py:313:    m = re.search(rf"(?i)\b(references|bibliography)\s+(?=\d+\.\s+[{_UPPERCASE_LATIN1}])", text)
main.py:317:    m = re.search(rf"(?<![\d.])1\.\s+[{_UPPERCASE_LATIN1}]", text)
main.py:367:    blocks = re.findall(rf"(?<![\d.])\d+\.\s+[{_UPPERCASE_LATIN1}]", text)
main.py:429:    # Latin-1 Supplement uppercase support は _UPPERCASE_LATIN1 定数 (本 file
main.py:434:        rf"(?=[{_UPPERCASE_LATIN1}]|van\s|de\s+[{_UPPERCASE_LATIN1}]|du\s+[{_UPPERCASE_LATIN1}]|den\s+[{_UPPERCASE_LATIN1}]|von\s+[{_UPPERCASE_LATIN1}])"
main.py:452:            rf"(?=[{_UPPERCASE_LATIN1}]|van\s|de\s+[{_UPPERCASE_LATIN1}]|den\s+[{_UPPERCASE_LATIN1}]|von\s+[{_UPPERCASE_LATIN1}])"
```

(L434 は 5 occurrences、L452 は 4 occurrences、合計 12 occurrences across 5 rf-string 行 + 1 comment 行 + 1 定義行 = 7 行)

---

**End of Plan**
