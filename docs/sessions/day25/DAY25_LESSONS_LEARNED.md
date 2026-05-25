# Day25 LESSONS LEARNED

**Day25 セッション (2026-05-24)**: Day24 tripwire test が encode していた `split_references()` parser bug を root cause 特定 → fix する作業. Day24 仮説「DOI URL 直後の <N>. boundary 検出失敗」が誤りと判明し、真因「非 ASCII Latin uppercase (Å/Ö) が `[A-Z]` lookahead でマッチしない」を特定. `[A-ZÀ-ÖØ-Þ]` への regex 拡張で fix. (100 passed / 0 skipped → 107 passed / 0 skipped / 0 failed)

---

## 1. セッション概要

### 1.1 背景

Day24 末状態: 100 passed / 0 skipped。Day24 Task 1 reconnaissance で `split_references()` が mdpi_173refs corpus で #54 と #78 を 569 characters の merged block として誤 parse し、#55 と #79 を欠落させる bug を発見。Day24 では fix を scope 外として tripwire test (`assert len(refs) == 171`, `assert sorted(missing_indices) == [55, 79]`) に encode した上で Day24 を完了させた。

Day24 の tripwire test docstring では「DOI URL 直後の <N>. boundary 検出失敗」と説明し、これが Day25 の出発点となった。

### 1.2 Day25 末状態

- 全 tests: **107 passed / 0 skipped / 0 failed**
- 新規 unit test: 5 件 (tests/test_main_split_references.py)
- 新規 positive integration test: 2 件 (#55 Åkra / #79 Özcan)
- Day24 tripwire test 更新: 3 件 (171→173, gaps→[], KNOWN_MERGE 削除)
- mdpi_173refs parsed count: 171 → **173** (#55 Åkra / #79 Özcan 復活)
- LLM cost: **$0** (parser fix のみ、API 呼び出し不要)
- gitleaks: no leaks found (継続)
- commit chain: 5 件 (docs(spec) + docs(plan) + test(split) + fix(split) + docs(sessions))

---

## 2. brainstorming 段階

### 2.1 設計方針確定 (Q1, Q2)

| # | 質問 | 選択肢と比較 | 確定 |
|:---:|:---|:---|:---|
| Q1 | regex 修正方針: boundary lookahead の character class 拡張方法 | (A) 明示的 Latin-1 class / (B) Latin Extended-A 全込み / (C) regex library 使用 / (D) Pre-filter 方式 | **(A) 明示的 `[A-ZÀ-ÖØ-Þ]`** |
| Q2 | commit 戦略: TDD cycle 粒度 | (α) Strict TDD 2-commit (RED→GREEN) / (β) Integration TDD のみ 1-commit / (γ) Unit + Integration 両方で 3-commit | **(α) Strict TDD 2-commit** |

**Q1 判断根拠**:
- (B) Latin Extended-A 全込み (`[A-ZÀ-ſ]`) は č/š 等の lowercase まで含む危険があり、境界判定が甘くなる。現状の corpus (欧米著者、Latin-1 で十分) に対して over-engineering。
- (C) `regex` / `unicodedata` ライブラリ依存は stdlib の re で解決できる問題に dependency を加える本末転倒。
- (D) Pre-filter 方式 (cleaned text の Unicode 正規化) はコード複雑化を招き、他 boundary 検出ロジックへの波及リスクあり。

**Q2 判断根拠**:
- (β) Integration TDD のみでは unit test が corpus に強依存し、孤立した境界判定ロジックのテストが欠ける。
- (γ) Unit + Integration 両方を 1 RED commit に詰めると commit が肥大化し、history 追跡が困難。(α) の 2-commit (RED: unit only → GREEN: regex fix + integration 更新) が最も履歴が明快。

### 2.2 SPEC と PLAN

- SPEC (`docs/superpowers/specs/2026-05-24-day25-split-references-non-ascii-fix-design.md`, commit `8f3bfb3`): Q1/Q2 比較評価表 + §1.4 採用案の根拠 + Unicode 範囲の詳細設計 (U+00D7 exclusion の意図) + Day26+ 候補
- PLAN (`docs/superpowers/plans/2026-05-24-day25-split-references-non-ascii-fix.md`, commit `491725b`): Task 0-3 の 4 task 構成

---

## 3. 実装段階の経緯 (Task 0-3)

### 3.1 commit chain (5 件)

| # | SHA | type | 要旨 |
|:---:|:---|:---|:---|
| 1 | `8f3bfb3` | docs(spec) | Day25 split_references non-ASCII Latin uppercase fix spec |
| 2 | `491725b` | docs(plan) | Day25 implementation plan |
| 3 | `1a1d899` | test(split) | TDD RED: 5 unit test (Å/Ö/É boundary + ASCII baseline + DOI URL guard) |
| 4 | `eb1c6f1` | fix(split) | TDD GREEN: regex 拡張 [A-Z]→[A-ZÀ-ÖØ-Þ] + tripwire 3 更新 + positive test 2 + json 再生成 + integration test inline fix |
| 5 | (this commit) | docs(sessions) | Day25 archive |

### 3.2 Task 1: TDD RED (commit `1a1d899`)

`tests/test_main_split_references.py` を新規作成。5 unit test:

| test | 検証内容 | RED 時の状態 |
|:---|:---|:---|
| `test_split_at_ascii_uppercase` | 通常の ASCII 境界 (A-Z) | PASS (baseline 確認) |
| `test_split_at_non_ascii_latin_a_ring` | Å (U+00C5) 境界 | **FAIL** |
| `test_split_at_non_ascii_latin_o_umlaut` | Ö (U+00D6) 境界 | **FAIL** |
| `test_split_at_non_ascii_latin_e_acute` | É (U+00C9) 境界 | **FAIL** |
| `test_no_split_inside_doi_url` | DOI URL 内の `.` で分割しない guard | PASS (既存動作確認) |

### 3.3 Task 2: TDD GREEN + tripwire 更新 (commit `eb1c6f1`)

sub-step 構成 (D20-3 pattern を plan-deviation inline fix として適用):

- **A** (regex fix): `main.py` L? `split_references()` の `[A-Z]` → `[A-ZÀ-ÖØ-Þ]` に変更
- **B** (tripwire 更新): `tests/test_split_references_doi_boundary.py` の tripwire 3 件を更新 (171→173、gaps→[]、KNOWN_MERGE block 削除)
- **C** (json 再生成): `tests/fixtures/mdpi_173refs/expected_phase1_intermediate.json` を再生成 (#55 Åkra / #79 Özcan が復活した新 173 件の Phase 1 出力)
- **D** (verify + commit): 107 passed 確認 → atomic commit

**plan-deviation inline fix の発動**: Task 2 実行中に `tests/test_integration_mdpi_173refs.py` 内で `assert len(refs) == 171` を別途 encode した箇所が 2 箇所あり、これらも 173 に更新が必要だと判明。D20-3 パターン (inline fix は即座に sub-step に組み込む) を適用し、commit 分割せずに同一 GREEN commit に含めた。

---

## 4. 設計判断と検証

### 4.1 Day25 で発覚した Day24 仮説誤り

**Day24 の仮説**: `split_references()` は `\n<digit(s)>.` パターンで boundary を検出するが、DOI URL (`https://doi.org/10.xxxxx`) の直後に `<N>.` 形式の boundary が連続する場合、DOI の `.` を boundary の `.` と区別できず次の boundary 検出が skip される。

**Day25 での真因特定**: Day25 で `#54` の実 cleaned text を `repr()` dump したところ、DOI URL の末尾ではなく「著者姓の頭文字が Å (U+00C5)」であることが境界不一致の原因と判明。regex `\n\d+\.\s+[A-Z]` の lookahead `[A-Z]` は ASCII uppercase (U+0041-U+005A) の 26 文字のみを match し、`Å` U+00C5 は範囲外。

**tripwire test の功罪**:
- tripwire test 自体は正しく fail 信号を発していた (設計は正しい)
- ただし docstring 内の説明「DOI URL 直後の <N>. boundary 検出失敗」は外形的観察 (DOI URL の後で merge が発生しているように見えた) から推測された仮説であり、実 data inspect を伴わない誤った原因記述だった
- Day25 で tripwire test 更新時に docstring も「非 ASCII Latin uppercase が [A-Z] lookahead でマッチしない」に書き換えた

### 4.2 `[A-ZÀ-ÖØ-Þ]` 範囲設計の詳細

Unicode Latin-1 Supplement block (U+00C0-U+00FF) の uppercase は:

| 範囲 | 文字 | 代表著者姓の例 |
|:---|:---|:---|
| U+00C0-U+00D6 (À-Ö) | À Á Â Ã Ä Å Æ Ç È É Ê Ë Ì Í Î Ï Ð Ñ Ò Ó Ô Õ Ö | Åkra, Özcan, Ñoguez |
| U+00D7 | × | 乗算記号 (意図的に excluded) |
| U+00D8-U+00DE (Ø-Þ) | Ø Ù Ú Û Ü Ý Þ | Øberg, Ünal |

`[A-ZÀ-ÖØ-Þ]` は U+00D7 (×) を意図的に除外した 2-range 記法。`×` は著者姓頭文字として出現しないため実害はないが、regex の意図を明示するために除外を明記した。

Latin Extended-A (U+0100-U+017F、Ā-ſ) には Š/Č/Ž (チェコ語) / Ł (ポーランド語) / Ő/Ű (ハンガリー語) / Ș/Ț (ルーマニア語) 等が含まれ、Day26+ scope とした理由は現状 corpus で該当ケースがなく、拡張の要件が出た時点で評価する方針に沿っているため。

### 4.3 tripwire test の rename と再利用

Day24 tripwire test の旧名 `test_ref_count_matches_current_parser_state` は「現在の parser state」を encode するという名前であり、parser が修正されると test name 自体が意味を失う。

Day25 で `test_ref_count_is_173` に rename した。「173」は corpus 固定の不変条件であり、parser fix 後も変わらない。この test name の哲学は「現状 (mutable)」ではなく「不変条件 (invariant)」を test name に表現するべき、という考え方に基づく。future regression で parser が誤動作して ref count が変わった場合に即座に検出できる。

### 4.4 strict TDD 2-commit cycle の歴史的価値

RED commit (`1a1d899`) は「Å/Ö/É 境界で FAIL する unit test が存在した瞬間」を git history に刻む。これにより:

1. Day26+ で Latin Extended-A 拡張を行う際、同じ TDD RED→GREEN サイクルの参考になる
2. `[A-Z]` → `[A-ZÀ-ÖØ-Þ]` がどの unit test を GREEN にするために必要だったかが明示される
3. bug が「既知の failing test として encode されてから fix された」ことが証明される (hotfix ではなく TDD で解決されたこと)

---

## 5. 実機検証

### 5.1 test count 推移

| フェーズ | test count |
|:---|:---:|
| Day24 末 | 100 passed / 0 skipped |
| Task 1 RED (1a1d899) | 97 passed / 3 failed |
| Task 2 GREEN (eb1c6f1) | **107 passed / 0 skipped / 0 failed** |

net +7 は内訳: unit test 5 件 + positive integration test 2 件。

### 5.2 #54/#78 char_length 変化

| ref | Day24 末 (merged, 569ch) | Day25 末 (cleaned) |
|:---:|:---:|:---:|
| #54 | 569 ch | ~241 ch |
| #78 | 569 ch | ~311 ch |

#55 Åkra / #79 Özcan が独立 ref として 173 件に復帰。

### 5.3 その他検証

- `python3 -m pytest tests/ -q` → `107 passed in 0.31s`
- `gitleaks detect --no-banner --redact` → `no leaks found`
- `gh repo view --json visibility,isPrivate` → `{"isPrivate":false,"visibility":"PUBLIC"}`
- local HEAD == remote HEAD (`eb1c6f1...`)
- CI (GitHub Actions): fix(split) commit `eb1c6f1` にて green を確認

---

## 6. 教訓

### D25-1: 仮説段階の bug 解説は「観察事実」と「推測される原因」を明確に分けるべき

**事象**:

Day24 Task 1 reconnaissance で「#54 と #78 のコンテンツが 569 文字で、#55 と #79 が欠落している」という観察事実があった。この観察から「DOI URL 直後の <N>. boundary 検出失敗」という仮説を立て、それを tripwire test の docstring にそのまま encode した。

Day25 で実 cleaned text の `repr()` dump を実施したところ、DOI URL の `.` が boundary を block しているのではなく「著者姓の頭文字 `Å` (U+00C5) が `[A-Z]` lookahead でマッチしない」が真因だと判明。

tripwire test 自体は正しく fail 信号を発していたが、docstring の bug 説明は仮説段階の推測原因を記述しており、誤りだった。

**学び**:

bug 発見段階の reconnaissance では以下の 3 階層を明確に分けて記録すべき:

1. **観察事実**: `#54 char_length == 569`、`#55 が refs に存在しない`
2. **実 data inspect 結果**: `repr(cleaned_text[ref54_start:ref54_start+100])` の出力
3. **推測される原因 (仮説)**: inspect 結果から導出した機構説明

docstring に encode するのは (1) と inspect 済の (3) のみ。仮説段階のまま encode する場合は `# HYPOTHESIS:` prefix 等で明示し、inspect 後に update する義務を明記するのが安全。

**適用範囲**:

将来の bug reconnaissance + tripwire test 設計時。特に「観察事実から外形的に仮説を立てやすい」ケース (DOI URL の後で merge が発生している、という見た目の印象) で同型の混同を避けるため、reconnaissance 段階で実 data dump を必須化する。

### D25-2: regex の character class は Unicode 範囲の罠が多い

**事象**:

`[A-Z]` は Python `re` において ASCII uppercase (U+0041-U+005A) の 26 文字のみを cover する。`\w` は Unicode 認識 (全 Unicode の word character を含む) だが意味が広すぎる。Latin-1 Supplement の uppercase (À-Ö Ø-Þ) は `[A-Z]` に含まれず、欧州著者姓 (Åkra, Özcan, Ünal 等) の頭文字でマッチしない。

Day9 で `split_references()` に lowercase prefix (`van/de/du/den/von 等`) の明示的 character class を追加した際と同様に、「明示的 character class で範囲を明示する」ことが重要。

**学び**:

「`[A-Z]` で uppercase を match する」という直感は ASCII 限定の罠。Unicode テキストを扱うすべての regex では:

1. **ASCII 前提** (`[A-Z]`) と **Unicode 前提** (`[A-ZÀ-ÖØ-Þ]` 等) を意図として明示
2. character class を書いたら「どの Unicode codepoint が excluded されているか」を一度確認する
3. `re.UNICODE` flag (Python 3 では default ON) があっても character class の範囲は明示的に指定する必要がある

**適用範囲**:

全 regex での「ASCII 前提」「Unicode 前提」の明示的区別。コメントで `# ASCII uppercase only` または `# Latin-1 Supplement uppercase included` を追加。Day26+ で Latin Extended-A (チェコ / ポーランド / ハンガリー / ルーマニア) の著者姓対応が必要になった場合も同様に範囲を明示する。

---

## 7. 残存タスク (Day26+ 候補)

| 優先度 | タスク | 根拠 |
|:---:|:---|:---|
| **Top** | Latin Extended-A 拡張: Š/Č/Ž/Ł/Ć/Ń/Ő/Ű/Ș/Ț 対応 | D25-2 延長、該当 corpus が見つかったら即対応 |
| **NEW** | `main.py` `_strip_pre_references` (L299/L303) + `preprocess` (L353) の bare `[A-Z]` を `[A-ZÀ-ÖØ-Þ]` に統一 | Day25 code review 発見、consistency + 潜在的 inline-header parsing fix |
| 中 | mdpi_173refs 固有 manual_overrides.yaml 構築 | Day24 から継承、Crossref graceful failure 対応の前提 |
| 中 | pre-commit hook gitleaks 自動実行 | Day22 handoff パターン 3 |
| 低 | CONTRIBUTING.md / Issue PR template | Day22 handoff パターン 2 |
| 低 | PyPI 公開 (v0.2.0 候補) | Day22 から継承 |
| 低 | pyproject.toml + uv.lock 移行 | CLAUDE.md §8 整合 |
| 低 | Crossref graceful failure 16 件の対応 | Day22 §6.3 NEW、apa_45refs corpus |
| 低 | NLM fuzzy-match precision 改善 | Day22 §6.3 NEW |
| 低 | tools/build_*_fixture.py 共通 utility refactor | Day23 code review 指摘 |
| 低 | deterministic byte-level golden 再構築 | LLM stub 経由、Day26+ 大改修 |

---

## 8. 次セッション再開プロンプトテンプレート

### パターン 1 (推奨): Latin Extended-A 拡張 (Day25 D25-2 の延長)

```
Day25 で split_references() の [A-Z] → [A-ZÀ-ÖØ-Þ] (Latin-1 Supplement uppercase) 拡張を完了した。
現在 107 passed / 0 skipped。HEAD は <SHA> (fix(split) eb1c6f1 の後)。

今回は D25-2 の延長として Latin Extended-A 範囲 (U+0100-U+017F) の拡張を行いたい。
対象: Š (U+0160) Č (U+010C) Ž (U+017D) / Ł (U+0141) Ć (U+0106) Ń (U+0143) / Ő (U+0150) Ű (U+0170) / Ș (U+0218) Ț (U+021A) 等。

まず docs/sessions/day25/DAY25_LESSONS_LEARNED.md §7 と §8 を確認し、
D25-2 の教訓 (regex character class は明示的範囲で) に従って TDD RED→GREEN で実装してほしい。
```

### パターン 2: `main.py` 残 bare `[A-Z]` 3 箇所の統一 (Day25 code review 発見)

```
Day25 code review で main.py に bare [A-Z] が 3 箇所残存すると判明した。
- _strip_pre_references (L299, L303): inline header "References 1. Åberg S." 形式の検出で同様の bug 有
- preprocess (L353): ref_blocks_found counter、診断目的のみだが log 値 undercount

現在 107 passed / 0 skipped。HEAD は <SHA>。
docs/sessions/day25/DAY25_LESSONS_LEARNED.md §4.1, §6 (D25-2) を参照し、
3 箇所を [A-ZÀ-ÖØ-Þ] に統一する consistency fix を TDD で実装してほしい。
まず該当行の実コードを確認し、test が必要かどうか評価してから作業開始すること。
```

### パターン 3: mdpi_173refs 固有 manual_overrides.yaml 構築

```
Day25 完了。107 passed / 0 skipped / 0 failed。HEAD は <SHA>。

今回は Day24 から継続の manual_overrides.yaml を mdpi_173refs corpus 向けに構築したい。
Crossref graceful failure が出ている 16 件 (apa_45refs でも確認) の手動補完から始めてほしい。
docs/sessions/day24/DAY24_LESSONS_LEARNED.md §7 の残存タスクと、
docs/sessions/day25/DAY25_LESSONS_LEARNED.md §7 の優先度表を参照して計画を立てること。
```
