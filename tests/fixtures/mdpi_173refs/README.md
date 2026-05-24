# tests/fixtures/mdpi_173refs/

**MDPI-style 173-ref baseline (Day23 由来、Nutrients review)**

## 由来

このディレクトリは、PMC OA Nutrients (MDPI) review 論文から全 173 件の MDPI-style
参考文献を JATS XML 経由で抽出し、`tools/build_mdpi_replacement_fixture.py` で
番号付き段落 docx に統合した fixture を、旧 mdpi_149refs (commit a0bba56 由来、
Day23 で confidentiality concern により削除) の test architecture 後継として固定保管する.

## ソース論文 (Day23 user 選定)

| 項目 | 値 |
|:---|:---|
| PMC ID | PMC13164670 |
| DOI | 10.3390/nu18091382 |
| Journal | Nutrients (MDPI) |
| 出版年 | 2026 |
| LICENSE | CC BY 4.0 (MDPI default) |
| Article type | review-article |
| 抽出 ref 数 | 173 |
| Title | Adipocyte Size, Overweight, and Insulin Resistance in Type 2 Diabetes Mellitus and the Impact of Weight Loss: A Systematic Review |

抽出範囲は引用論文の bibliographic information (factual data) のみで、creative
expression (abstract 本文等) は含まない. PMC OA CC BY 4.0 ライセンスの帰属表示として
本 table にて明示.

## ファイル一覧

| ファイル | 種別 | 用途 |
|:---|:---|:---|
| `input_References.docx` | 入力 (tools/build_mdpi_replacement_fixture.py 生成) | parser/test 入力 |
| `expected_phase1_intermediate.json` | golden (deterministic, parser-only) | byte-level regression |
| `baseline_phase3_resolved.json` | document-of-record (LLM + PubMed variability) | 構造確認 |
| `baseline_report.md` | document-of-record | 出力 narrative |
| `baseline_three_class_classification.json` | document-of-record | 三分類 audit baseline |
| `README.md` | 本書 | — |

## Baseline 生成結果 (Day23 実測値)

| 指標 | 値 |
|:---|:---|
| Phase 1 パース参照数 | 171 (173 ref 中 2 件は結合等) |
| PubMed 解決済 (PMID 取得) | 159 |
| 未解決 | 12 |

## 三分類分布 (Day23 baseline 生成時、未解決 12 件のみ対象)

| クラス | 件数 |
|:---:|:---:|
| A | 0 |
| B | 7 |
| C | 3 |
| unknown | 2 |
| **三分類合計** | **12** |

> 注: 三分類 (three_class_classification) は未解決参照のみを対象とする.
> PMID 取得済みの 159 件は本ファイルには含まれない.

## 関連 test

`tests/test_integration_mdpi_173refs.py` (Day23 Task 10 で追加、apa/cell 8-test
template 流用、EXPECTED_THREE_CLASS_DISTRIBUTION は上記実測値で固定).

## Day23 origin

旧 mdpi_149refs は commit a0bba56 で導入されたが、README 未作成で出典記述なく、
input_References.docx の出自確認の過程で査読由来である可能性が示唆され、
著作権・査読守秘義務上の懸念から Day23 で削除 + git filter-repo で全 history からも消去.
本 fixture は PMC OA CC BY 4.0 由来の代替として Day23 Phase 5 で新規構築.

spec: docs/superpowers/specs/2026-05-24-day23-fixture-remediation-design.md
plan: docs/superpowers/plans/2026-05-24-day23-fixture-remediation.md
