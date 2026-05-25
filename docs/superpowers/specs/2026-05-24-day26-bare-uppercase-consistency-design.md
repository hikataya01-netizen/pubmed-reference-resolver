# SPEC: Day26 — bare `[A-Z]` 3 箇所の `_UPPERCASE_LATIN1` 定数化 + 統一

**作成日**: 2026-05-24 (Day26 brainstorming 完了時)
**著者**: Claude Code (Opus 4.7 / 1M context) / 承認: 片山英樹
**位置付け**: Day25 Task 2 code quality review で発見された `main.py` 内の 3 箇所の bare `[A-Z]` (`_strip_pre_references` Case 2/Case 3 + `preprocess` ref_blocks_found counter) を `[A-ZÀ-ÖØ-Þ]` に統一しつつ、Day25 で導入した 5 箇所と合わせて計 8 箇所を **module-level 定数 `_UPPERCASE_LATIN1` の参照**に refactor する。DRY 原則準拠 + Day27+ Latin Extended-A 拡張時の保守コスト削減 + 潜在的 inline-header parsing bug の予防。
**前提**: Day25 末 (HEAD `d248d2d`、Day25 archive 含む) で main branch、107 passed / 0 skipped / 0 failed、repo PUBLIC、CI green、v0.1.0 release accessible、gitleaks clean

---

## 1. 背景と目的

### 1.1 Day25 code quality review の発見

Day25 fix(split) (commit `eb1c6f1`) は `main.py split_references()` 関数内の 2 箇所 regex (matcher + standard fallback) の lookahead を `[A-Z]` → `[A-ZÀ-ÖØ-Þ]` に拡張する形で実装。Day25 Task 2 code quality review で reviewer が以下 3 箇所の **bare `[A-Z]` 残存**を発見:

| 行番号 | 関数 | role | 影響 |
|:---:|:---|:---|:---|
| L299 | `_strip_pre_references` Case 2 | "References 1. Author..." inline header detection の lookahead | 著者頭文字が非 ASCII Latin uppercase (Å Ö 等) の corpus で inline header strip 失敗、Case 3 fallback に依存 |
| L303 | `_strip_pre_references` Case 3 | "1. {大文字}" fallback first-ref detection | 同上 + Case 3 も失敗時は pre-references 部分が strip されず本文に流入する潜在 bug |
| L353 | `preprocess` ref_blocks_found counter | `PreprocessTrace.ref_blocks_found` 用診断 counter | 非 ASCII Latin uppercase 著者の ref を undercount、診断 log 信頼性低下 (parser 動作に直接影響なし) |

現 corpus (mdpi_173refs) では Case 1 (独立行 References ヘッダー) が先に match するため test failure は発生していないが、別 corpus で inline header + 非 ASCII 著者の組み合わせが出ると顕在化する latent bug。

### 1.2 DRY 観点での問題

Day25 で 5 箇所、Day26 でさらに 3 箇所、計 **8 箇所**に literal `[A-ZÀ-ÖØ-Þ]` (Day26 後) が散在することになる。Day27+ で Latin Extended-A (Š Č Ł 等) 拡張時は 8 箇所を一斉 update する必要があり、regex 検索ミスのリスクと cognitive cost が high。

### 1.3 目的

1. **bare `[A-Z]` 3 箇所の修正**: L299, L303, L353 を `[A-ZÀ-ÖØ-Þ]` に統一、潜在的 inline-header bug を予防
2. **DRY refactor**: module-level 定数 `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` を導入し、計 8 箇所を `[{_UPPERCASE_LATIN1}]` (f-string 補間) に統一
3. **将来拡張時の保守コスト削減**: Day27+ Latin Extended-A 拡張時は定数 1 行 update で 8 箇所に伝播
4. **TDD discipline**: synthetic input ベースの unit test 4 件を `tests/test_main_split_references.py` (Day25 で作成) に追記、TDD RED commit 先行
5. **Day25 docstring の整理**: Day25 で `split_references` 直前に置いた 5 行の Latin-1 説明 comment を、定数定義 (本 file 上部) に集約し、`split_references` docstring は 3 行の reference に圧縮

### 1.4 設計判断の経緯 (brainstorming 質問)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | 修正 approach | **(B) module-level 定数抽出** (8 箇所統一、Day27+ 拡張で 1 行 update) |
| Q2 | test 範囲 | **(α) 3 箇所全てに unit test 追加** (L299/L303/L353 + ASCII baseline 1 件 = 計 4 件) |
| Q3 | commit 構造 | **(α) Strict TDD 2-commit** (Day25 同 pattern: test(prep) RED + refactor(parse) GREEN) |

---

## 2. Architecture & ファイル配置

### 2.1 改変対象 (2 file)

| File | 種別 | 改変内容 | 影響行数 |
|:---|:---|:---|:---|
| `main.py` | refactor + 修正 | 新規定数 `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` を module-level に追加 (`_strip_pre_references` 直前、Stage 2 セクション開始部) + 既存 Day25 5 箇所 (L423/L441 area) + 新規 3 箇所 (L299, L303, L353) の計 8 箇所を `rf"...[{_UPPERCASE_LATIN1}]..."` f-string 参照に統一 + Day25 既存 docstring (L414-419 area) の 5 行重複説明を 3 行 reference に圧縮 | +定数定義 ~13 行 / -重複 docstring 2 行 / 8 文字列リテラル refactor |
| `tests/test_main_split_references.py` | 追加 | 4 新規 unit test を Day25 既存 test の後ろに追記: `test_strip_pre_references_case2_inline_header_with_aring`, `test_strip_pre_references_case2_inline_header_with_ascii_baseline`, `test_strip_pre_references_case3_fallback_with_oumlaut`, `test_preprocess_counts_aring_refs_correctly` | +60-90 行 |

### 2.2 改変対象外 (確認のみ)

- `tests/test_split_references_doi_boundary.py` (Day25 tripwire、parser 動作不変のため影響なし)
- `tests/fixtures/mdpi_173refs/*` (Phase 1 出力は parser 動作不変なら同一、再生成不要)
- 他 4 fixture (apa_45refs, cell_45refs, vancouver_35refs, three_class_classification)
- 他 module (mdpi_parser, crossref_check, nlm_catalog_check, three_class_classifier, journal_audit)

### 2.3 新規作成 (Day26 archive)

| File | 用途 |
|:---|:---|
| `docs/superpowers/specs/2026-05-24-day26-bare-uppercase-consistency-design.md` | 本 SPEC |
| `docs/superpowers/plans/2026-05-24-day26-bare-uppercase-consistency.md` | writing-plans 出力 |
| `docs/sessions/day26/README.md` | Day26 archive index |
| `docs/sessions/day26/DAY26_LESSONS_LEARNED.md` | Day26 教訓記録 |

### 2.4 `_UPPERCASE_LATIN1` 定数定義位置

`_strip_pre_references` 直前 (Stage 2: Phase 1 preprocessing セクション開始部) に配置:

```python
# =============================================================================
# Stage 2: Phase 1 preprocessing
# =============================================================================

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


def _strip_pre_references(text: str) -> tuple[str, bool]:
    ...
```

理由:
1. `_strip_pre_references` が定数を最初に使用する関数 → 定義位置の自然な場所
2. 「Stage 2 で使用される character class」というセクション意味と整合
3. Day25 で `split_references` 直前に置いた説明 comment は重複削除 → 定数定義に集約

---

## 3. Refactor 実装詳細

### 3.1 main.py 新規定数定義 (Stage 2 セクション開始部、`_strip_pre_references` 直前)

```python
# Character class fragment for non-ASCII Latin uppercase author surnames.
# (上記 §2.4 と同じ comment block + 定数定義)
_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"
```

### 3.2 8 箇所の f-string 参照への統一

#### (a) L299 (`_strip_pre_references` Case 2): bare → 定数参照

```diff
-    m = re.search(r"(?i)\b(references|bibliography)\s+(?=\d+\.\s+[A-Z])", text)
+    m = re.search(rf"(?i)\b(references|bibliography)\s+(?=\d+\.\s+[{_UPPERCASE_LATIN1}])", text)
```

#### (b) L303 (`_strip_pre_references` Case 3): bare → 定数参照

```diff
-    m = re.search(r"(?<![\d.])1\.\s+[A-Z]", text)
+    m = re.search(rf"(?<![\d.])1\.\s+[{_UPPERCASE_LATIN1}]", text)
```

#### (c) L353 (`preprocess` ref_blocks_found counter): bare → 定数参照

```diff
-    blocks = re.findall(r"(?<![\d.])\d+\.\s+[A-Z]", text)
+    blocks = re.findall(rf"(?<![\d.])\d+\.\s+[{_UPPERCASE_LATIN1}]", text)
```

#### (d) Day25 既存 5 箇所も統一 (`split_references` matcher + standard fallback)

```diff
     matcher = re.compile(
-        r"(?<![\d.])(\d+)[\.\s]+"
-        r"(?=[A-ZÀ-ÖØ-Þ]|van\s|de\s+[A-ZÀ-ÖØ-Þ]|du\s+[A-ZÀ-ÖØ-Þ]|den\s+[A-ZÀ-ÖØ-Þ]|von\s+[A-ZÀ-ÖØ-Þ])"
+        rf"(?<![\d.])(\d+)[\.\s]+"
+        rf"(?=[{_UPPERCASE_LATIN1}]|van\s|de\s+[{_UPPERCASE_LATIN1}]|du\s+[{_UPPERCASE_LATIN1}]|den\s+[{_UPPERCASE_LATIN1}]|von\s+[{_UPPERCASE_LATIN1}])"
     )
```

```diff
         standard = re.compile(
-            r"(?<![\d.])(\d+)\.\s+"
-            r"(?=[A-ZÀ-ÖØ-Þ]|van\s|de\s+[A-ZÀ-ÖØ-Þ]|du\s+[A-ZÀ-ÖØ-Þ]|den\s+[A-ZÀ-ÖØ-Þ]|von\s+[A-ZÀ-ÖØ-Þ])"
+            rf"(?<![\d.])(\d+)\.\s+"
+            rf"(?=[{_UPPERCASE_LATIN1}]|van\s|de\s+[{_UPPERCASE_LATIN1}]|du\s+[{_UPPERCASE_LATIN1}]|den\s+[{_UPPERCASE_LATIN1}]|von\s+[{_UPPERCASE_LATIN1}])"
         )
```

#### (e) Day25 既存 docstring (L414-419 area) の重複説明削除

```diff
     # より寛容な候補検出: ピリオド or 空白で数字と著者を区切る
     # NOTE: lookahead allows lowercase prefixes for Dutch/French surnames
     # (van, de, du, den, von) which start with lowercase letters.
     # Without this, refs like "40. van der Biessen" are silently dropped.
-    # Day25: lookahead also accepts Latin-1 Supplement uppercase
-    # ([A-ZÀ-ÖØ-Þ] = ASCII + U+00C0-U+00D6 + U+00D8-U+00DE, excluding × U+00D7)
-    # for Norwegian/German/French/Spanish/Portuguese surnames starting with
-    # Å Ö É Ñ etc. Without [A-ZÀ-ÖØ-Þ], refs like "55. Åkra" or "79. Özcan"
-    # are silently merged into the preceding ref (Day24 Task 1 reconnaissance
-    # discovered this on mdpi_173refs corpus).
+    # Latin-1 Supplement uppercase support は _UPPERCASE_LATIN1 定数 (本 file
+    # 上部、Stage 2 セクション開始部) で定義. Day25 で split_references()、
+    # Day26 で _strip_pre_references() + preprocess() に統一適用.
```

### 3.3 文字列 prefix 重要事項

新規 f-string 利用箇所はすべて `rf"..."` prefix (raw + f-string)。Python regex で `\d` `\s` 等のバックスラッシュエスケープを raw のまま保ちつつ `{_UPPERCASE_LATIN1}` を補間。

複数行 string concatenation (e.g., `rf"..."  rf"..."`) も全行に `rf` を付与しないと一部が f-string、他が raw のみで非対称になる。

---

## 4. TDD flow 詳細 (2-commit cycle、Day25 同 pattern)

### 4.1 Commit N: TDD RED `tests/test_main_split_references.py` に追記

既存 Day25 unit test file の末尾に Day26 用 test 4 件を追記:

```python
# ============================================================================
# Day26: _strip_pre_references + preprocess の Latin-1 uppercase 対応 unit test
# ============================================================================


def test_strip_pre_references_case2_inline_header_with_aring():
    """Case 2 (inline "References 1. Author...") で Å (U+00C5) 先頭著者を
    boundary として認識する.

    Day26: bare [A-Z] → [A-ZÀ-ÖØ-Þ] 統一前は inline header 検出失敗 →
    Case 3 fallback も同じ理由で失敗 → 結果 pre-references 部分が strip
    されず本文が parser に流入する bug.
    現状 (Day25 末) FAIL、Day26 fix で GREEN 化予定.
    """
    text = "Some intro paragraph blah blah References 1. Åberg S. Title. Journal 2020."
    stripped, found = main._strip_pre_references(text)
    assert found is True, "inline header should be detected"
    assert stripped.startswith("1. Åberg"), (
        f"expected stripped text to start with '1. Åberg', got: {stripped[:40]}"
    )


def test_strip_pre_references_case2_inline_header_with_ascii_baseline():
    """Case 2 で ASCII 著者の場合の baseline 動作 (refactor 後も不変)."""
    text = "Some intro References 1. Smith J. Title. Journal 2020."
    stripped, found = main._strip_pre_references(text)
    assert found is True
    assert stripped.startswith("1. Smith")


def test_strip_pre_references_case3_fallback_with_oumlaut():
    """Case 3 fallback で Ö (U+00D6) 先頭著者を boundary として認識する.

    Case 1 (独立行 References ヘッダー) なし、Case 2 (inline) なしの corpus
    で、最初の "1. {大文字}" にジャンプする保守的フォールバック.
    Day25 fix の延長で Case 3 でも Latin-1 を cover.
    """
    text = "Random preamble text with no References heading. 1. Özcan U. Title. Journal 2020."
    stripped, found = main._strip_pre_references(text)
    # Case 3 は found=False で返る (fallback fix なので確実な strip ではない)
    assert found is False
    assert stripped.startswith("1. Özcan"), (
        f"expected stripped text to start with '1. Özcan', got: {stripped[:40]}"
    )


def test_preprocess_counts_aring_refs_correctly():
    """preprocess() の PreprocessTrace.ref_blocks_found counter が
    Latin-1 uppercase 著者の ref も正しくカウントする (Day26 fix).

    旧 bare [A-Z] では counter が undercount、診断 log の信頼性低下.
    """
    # 3 refs: 1 ASCII + 2 Latin-1
    text = "1. Smith J. Title A. Journal 2020.\n2. Åkra S. Title B. Journal 2021.\n3. Özcan U. Title C. Journal 2022."
    _cleaned, trace = main.preprocess(text, main.detect_line_numbers(text))
    assert trace.ref_blocks_found == 3, (
        f"ref_blocks_found counter should detect all 3 refs (1 ASCII + 2 Latin-1), "
        f"got {trace.ref_blocks_found}"
    )
```

**期待される TDD RED 結果**:

| Test | Day25 末 (現状) | Day26 fix 後 |
|:---|:---:|:---:|
| `test_strip_pre_references_case2_inline_header_with_aring` | **FAIL** | PASS |
| `test_strip_pre_references_case2_inline_header_with_ascii_baseline` | PASS | PASS |
| `test_strip_pre_references_case3_fallback_with_oumlaut` | **FAIL** | PASS |
| `test_preprocess_counts_aring_refs_correctly` | **FAIL** (undercount) | PASS (count=3) |

### 4.2 Commit N+1: TDD GREEN/refactor (`main.py`)

§3.1 + §3.2 の全 8 箇所 + 定数定義 + docstring 圧縮を 1 atomic commit に集約。

---

## 5. Commit 計画 (5 commits)

| 順 | Phase | type | scope | 内容 |
|:---:|:---:|:---|:---|:---|
| 1 | Pre | `docs(spec)` | — | 本 SPEC を archive |
| 2 | Pre | `docs(plan)` | — | writing-plans 出力 |
| 3 | TDD RED | `test(prep)` | Task 1 | `tests/test_main_split_references.py` に Day26 unit test 4 件追加 (3 件 FAIL + 1 件 PASS 確認後 commit) |
| 4 | TDD GREEN | `refactor(parse)` | Task 2 | `main.py` の `_UPPERCASE_LATIN1` 定数追加 + 8 箇所 f-string 参照統一 + Day25 docstring 圧縮 (全 111 pytest pass 確認後 commit) |
| 5 | Post | `docs(sessions)` | Task 3 | Day26 archive (README + LESSONS) |

合計 **5 commits** (Day22/Day25 と同型)。

---

## 6. 完了条件 (10 項目)

| # | 条件 | 確認方法 |
|:---:|:---|:---|
| 1 | `main.py` に `_UPPERCASE_LATIN1` 定数定義 + 説明 comment block | `grep -c "_UPPERCASE_LATIN1" main.py` ≥ 9 (定義 1 + 使用 8) |
| 2 | bare `[A-Z]` が main.py 内に残存しない | `grep -E '\[A-Z\]' main.py` で **0 hit** |
| 3 | 新規 unit test 4 件が PASS | 各 test を pytest 個別 verify |
| 4 | 全 test pass (regression なし) | `pytest tests/ -q` で **111 passed / 0 skipped / 0 failed** |
| 5 | gitleaks 継続 clean | `gitleaks detect --no-banner --redact` で `no leaks found` |
| 6 | TDD 2 commit 順序 (test RED → refactor GREEN) | `git log --oneline -5` で `test(prep):` が `refactor(parse):` より先 |
| 7 | CI green for HEAD | `gh run list --limit 1 --jq .[0].conclusion` = `success` |
| 8 | Day26 archive (README + LESSONS) 作成 | `ls docs/sessions/day26/` で 2 file 存在 |
| 9 | Day25 既存 docstring の重複説明削除 | `grep -A2 "Latin-1 Supplement uppercase support は _UPPERCASE_LATIN1 定数" main.py` でヒット |
| 10 | mdpi_173refs Phase 1 出力は不変 (parsed count 173 維持) | `pytest tests/test_split_references_doi_boundary.py -v` で test_ref_count_is_173 PASS |

---

## 7. 工数見積もり

| Phase | 内容 | 見積 |
|:---:|:---|---:|
| Pre | SPEC + PLAN archive | 30 min |
| Commit 1 (TDD RED) | 新 unit test 4 件追加 + pytest で 3 件 FAIL + 1 件 PASS 確認 + commit | 30 min |
| Commit 2 (TDD GREEN/refactor) | `_UPPERCASE_LATIN1` 定数追加 + 8 箇所統一 + Day25 docstring 圧縮 + 全 pytest 確認 + commit + push | 30 min |
| Post | Day26 archive (README + LESSONS) + push + CI 確認 | 30 min |
| **合計** | | **~2 h** |

LLM cost: **$0** (refactor + test addition のみ)

---

## 8. 想定リスク

| リスク | 確率 | 影響 | 対応 |
|:---|:---:|:---:|:---|
| `rf"..."` 文字列で f-string 補間が regex syntax と干渉 (例: `{` が regex の repetition `{1,3}` と衝突) | 低 | 中 | 8 箇所すべて `[{_UPPERCASE_LATIN1}]` 形式で character class 内のみ補間、regex repetition syntax との衝突なし。1 commit pytest で実機検証 |
| 定数定義位置が `_strip_pre_references` より後で `NameError` | 低 | 低 | §2.4 で「Stage 2 セクション開始部、`_strip_pre_references` 直前」と明示 |
| Day25 既存 5 箇所の refactor で regex 挙動が微変化 | 低 | 中 | 文字列リテラル `[A-ZÀ-ÖØ-Þ]` と f-string `[{_UPPERCASE_LATIN1}]` で `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` なら完全に等価。pytest 全 107 件 PASS で実機検証 |
| 新 test の `_strip_pre_references` private 関数呼び出しで import 失敗 | 低 | 低 | Day22 SSL fix で `_load_overrides_yaml` 等を test から import している前例あり、`main._strip_pre_references` でアクセス可 |
| `_preprocess_counts_aring_refs_correctly` の test 設計で `detect_line_numbers` 引数が必要 | 中 | 低 | §4.1 の test 例で `main.detect_line_numbers(text)` を渡す形を示している、preprocess の現 signature と整合 |
| docstring の重複説明削除で履歴情報が失われる | 低 | 低 | Day25 spec/plan に元の情報が残る、git blame で Day25 commit を辿れば履歴可達 |
| 8 箇所の置換漏れ | 中 | 中 | 完了条件 #2 (`grep -E '\[A-Z\]' main.py` 0 hit) で機械的検証 |

---

## 9. Out of Scope (Day27+ 候補)

- **Latin Extended-A 範囲拡張** (Š Č Ž / Ł Ć Ń Ą Ę / Ő Ű / Ș Ț 等) — Day26 では `[A-ZÀ-ÖØ-Þ]` のみ、Extended-A 必要な corpus が出てきたら Day27+ で `_UPPERCASE_LATIN1` 定数を 1 行 update で 8 箇所伝播
- **mdpi_173refs 固有の manual_overrides.yaml 構築** (Day24 から継承)
- **pre-commit hook gitleaks 自動実行** (Day22 handoff パターン 3)
- **CONTRIBUTING.md / Issue PR template / PyPI 公開 / pyproject.toml 移行**
- **Crossref graceful failure 16 件の対応 / NLM fuzzy-match precision 改善**
- **tools/build_*_fixture.py の共通 utility refactor** (Day23 code review 指摘)

---

## 10. 参照

- Day22 brainstorming spec: `docs/superpowers/specs/2026-05-24-rule3-nlm-ssl-fix-design.md` (TDD 2-commit pattern の参考)
- Day25 brainstorming spec: `docs/superpowers/specs/2026-05-24-day25-split-references-non-ascii-fix-design.md` (5 箇所の `[A-Z]→[A-ZÀ-ÖØ-Þ]` 拡張の origin、本 spec で定数化対象)
- Day25 LESSONS: `docs/sessions/day25/DAY25_LESSONS_LEARNED.md` §Day26+ 候補 (本 fix が NEW 項目として明示)
- Day25 Task 2 code quality review (reviewer agent `a0822e10`、bare [A-Z] 3 箇所発見)
- main.py `_strip_pre_references()` (line ~293-308): Case 2 + Case 3 修正対象
- main.py `preprocess()` (line ~310-360): ref_blocks_found counter 修正対象
- main.py `split_references()` (line ~397-451): Day25 既存 5 箇所、定数化対象
- Day24 LESSONS D24-3: tripwire pattern (本 spec の test 設計に influence)
- Unicode reference: Latin-1 Supplement block (U+0080-U+00FF) の uppercase range は U+00C0-U+00DE excluding U+00D7

---

**承認**: 片山英樹 (brainstorming Q1-Q3 + design 全 3 sections)
**次工程**: writing-plans skill で bite-sized implementation plan を作成
