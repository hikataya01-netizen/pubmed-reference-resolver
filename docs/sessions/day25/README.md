# Day25 Session Archive (2026-05-24)

## 概要

Day25 セッションは Day24 Task 1 reconnaissance で発見し tripwire pattern で
test に encode していた `split_references()` parser bug を root cause 特定 →
fix する作業. Day24 で立てた仮説「DOI URL 直後の <N>. boundary 検出失敗」が
Day25 brainstorming で実 cleaned text inspect の結果誤りと判明、真因は
「直後の著者姓が非 ASCII Latin uppercase (Å U+00C5, Ö U+00D6) で main.py
regex lookahead `[A-Z]` でマッチしない」と確定. Latin-1 Supplement uppercase
を cover する `[A-ZÀ-ÖØ-Þ]` への regex 拡張で fix.

## 主要成果

| 指標 | Day24 末 | Day25 末 |
|:---|:---:|:---:|
| 全 tests | 100 passed / 0 skipped | **107 passed / 0 skipped / 0 failed** |
| 新規 unit test | — | 5 件 (tests/test_main_split_references.py) |
| 新規 positive integration test | — | 2 件 (#55 Åkra / #79 Özcan) |
| Day24 tripwire test 更新 | — | 3 件 (171→173, gaps→[], KNOWN_MERGE 削除) |
| mdpi_173refs parsed count | 171 | **173 (+2 復活: #55 Åkra, #79 Özcan)** |
| #54 char_length | 569 ch (merged) | ~241 ch (cleaned) |
| #78 char_length | 569 ch (merged) | ~311 ch (cleaned) |
| LLM cost | — | **$0** (parser fix のみ、--phase 1 only baseline) |

## Day25 archive 構成

- `README.md` — 本ファイル (Day25 index)
- `DAY25_LESSONS_LEARNED.md` — Day25 教訓記録 (D25-1, D25-2)
- `../../superpowers/specs/2026-05-24-day25-split-references-non-ascii-fix-design.md` — Day25 spec
- `../../superpowers/plans/2026-05-24-day25-split-references-non-ascii-fix.md` — Day25 plan

## Day25 commits (chain、5 件)

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `8f3bfb3` | docs(spec) | Day25 split_references non-ASCII Latin uppercase fix spec |
| 2 | `491725b` | docs(plan) | Day25 implementation plan |
| 3 | `1a1d899` | test(split) | TDD RED: 5 unit test (Å/Ö/É boundary + ASCII baseline + DOI URL guard) |
| 4 | `eb1c6f1` | fix(split) | TDD GREEN: regex 拡張 [A-Z]→[A-ZÀ-ÖØ-Þ] + tripwire 3 更新 + positive test 2 + json 再生成 + integration test inline fix |
| 5 | (this commit) | docs(sessions) | Day25 archive |

## 設計判断

実装 approach は **Q1 (A) 明示的 character class 拡張 + Q2 (α) Strict TDD 2-commit cycle** を採用 (spec §1.4). 代替案 Q1 (B) Latin Extended-A 拡張 / Q1 (C) 三方 regex library / Q1 (D) Pre-filter 方式 は false positive 増 / 依存追加 / コード複雑化のため不採用. Q2 (β) Integration TDD のみ / Q2 (γ) 両方は corpus 依存度過大化 / commit 数過多のため不採用.

`[A-ZÀ-ÖØ-Þ]` 拡張は Python stdlib re のみ、Latin-1 Supplement uppercase block (À-Ö U+00C0-U+00D6, Ø-Þ U+00D8-U+00DE、× U+00D7 は意図的に excluded) を cover. ノルウェー / スウェーデン / ドイツ / オランダ / フランス / スペイン / ポルトガル等の著者姓に対応.

## Day25 で確認した重要な反省事例

Day24 Task 1 で立てた仮説「DOI URL 直後の <N>. boundary 検出失敗」は **誤り**だった. 実際は「直後の著者姓が非 ASCII Latin uppercase」が真因. Day24 段階で実 cleaned text を inspect していなかったため、外形的な観察 (DOI URL の後で merge 発生) から仮説立て、それを tripwire test の docstring に encode してしまった.

Day25 で reconnaissance を継続 (実 cleaned text の repr() dump) した結果、真因が `Å` U+00C5 の lookahead 不一致だと特定. tripwire test 自体は正しく fail 信号を発しており、Day25 で test 更新時に「真因と一致する docstring」に書き換え.

→ 教訓: 仮説段階の bug 解説は「観察事実」と「推測される原因」を明確に分けるべき (D25-1 として記録).

## Day25 Task 2 code review で発見した Day26+ 候補

Code quality reviewer が `main.py` 内に bare `[A-Z]` が残る 3 箇所を発見:

- **L299, L303** (`_strip_pre_references`): "References 1. Åberg S." 形式の inline header 検出で同様の bug 有
- **L353** (`preprocess` の ref_blocks_found counter): 診断目的のみで分割ロジックに影響なし、ただしログ値 undercount

現 mdpi_173refs corpus では先行 case 1 (独立行 header) で match するため test failure 無し。Day26+ task として記録 (本 Day25 scope 外、本 spec §Day26+ 候補に追加).

## Day26+ 候補

- **Top priority (Day25 D25-2 延長)**: Latin Extended-A 範囲 (チェコ語 Š Č Ž / ポーランド語 Ł Ć Ń Ą Ę / ハンガリー語 Ő Ű / ルーマニア語 Ș Ț) で始まる著者姓が出現する corpus が見つかったら `[A-ZÀ-ÖØ-Þ]` → `[A-ZÀ-ÖØ-ÞĀ-ſ]` 等に拡張
- **NEW (Day25 code review 発見)**: `main.py` `_strip_pre_references` (L299/L303) と `preprocess` (L353) の bare `[A-Z]` を `[A-ZÀ-ÖØ-Þ]` に統一 (consistency + 潜在的 inline-header parsing fix)
- mdpi_173refs 固有の manual_overrides.yaml 構築 (Day24 から継承)
- pre-commit hook gitleaks 自動実行 (Day22 handoff パターン 3)
- CONTRIBUTING.md / Issue PR template (Day22 handoff パターン 2)
- PyPI 公開 (v0.2.0 候補)
- pyproject.toml + uv.lock 移行 (CLAUDE.md §8 整合)
- Crossref graceful failure 16 件の対応 (Day22 §6.3 NEW、apa_45refs)
- NLM fuzzy-match precision 改善 (Day22 §6.3 NEW)
- tools/build_*_fixture.py の共通 utility refactor (Day23 code review 指摘)
- deterministic byte-level golden の再構築 (LLM stub 経由、Day26+ 大改修)
