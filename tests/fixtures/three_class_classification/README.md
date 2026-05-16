# tests/fixtures/three_class_classification/

**Day15 「PubMed 未ヒット 3 分類」module 用 fixture (Day13 INVESTIGATION の API 応答を凍結)**

## 由来

このディレクトリは、Day13 INVESTIGATION (`docs/sessions/day13/INVESTIGATION_unresolved_2refs.md` §4.2 の curl 再現コマンド) で取得した Crossref + NLM Catalog API の実 response を fixture として固定保管する.

Day15 で実装する 3 module (`crossref_check.py`, `nlm_catalog_check.py`, `three_class_classifier.py`) の test 入力として使用される.

- 取得日: 2026/05/16 (Day15 Phase 0 で Day13 §4.2 のコマンドを再実行)
- 対象: Day9 (Z) Vancouver/AMA 24-ref baseline で残存未解決となった #17 Davey 2003 (C 分類) と #22 Gallina 2016 (B 分類) の 2 件 + 仮想 fabrication case (架空 DOI)

## ファイル一覧と命名規約

ファイル名 prefix は **全て `expected_*`** (Day11 ハイブリッド命名規約). 本 fixture は API 応答 input を凍結したものであり、production code の output (deterministic な分類結果) を assert する目的で使用するため、`baseline_*` は不要.

| ファイル | 種別 | 由来 | サイズ |
|:---|:---|:---|---:|
| `expected_crossref_10_1037-1091-7527.json` | Crossref hit response | DOI 10.1037/1091-7527.21.3.245 (Davey 2003) の live response | 4009 |
| `expected_crossref_10_4172-2090-7214.json` | Crossref hit response | DOI 10.4172/2090-7214.1000217 (Gallina 2016) の live response | 3429 |
| `expected_crossref_404.json` | **synthetic** 404 response | 仮想 DOI 10.9999/fake-doi-for-test-fabrication-12345 を Crossref に投げると HTTP 404 + plain text "Resource not found." が返る. これを post-parse 状態の synthetic JSON で表現 (詳細は `_note` field 参照) | ~250 |
| `expected_nlm_search_1091-7527.json` | NLM esearch response | ISSN 1091-7527 (Fam Syst Health) | 534 |
| `expected_nlm_summary_9610836.json` | NLM esummary response | NLM ID 9610836 (Fam Syst Health, **currentindexingstatus = Y**) | 2690 |
| `expected_nlm_search_clin_mother.json` | NLM esearch response | "Clinics in Mother and Child Health"[Journal] | 603 |
| `expected_nlm_summary_101300689.json` | NLM esummary response | NLM ID 101300689 (Clin Mother Child Health, **currentindexingstatus = N**) | 2364 |
| `README.md` | 本書 | — | — |

## 関連 module / test

Day15 SPEC §3-§6 で定義された production module + test:

| ファイル | 役割 | 使用 fixture |
|:---|:---|:---|
| `crossref_check.py` | Crossref API client | `expected_crossref_*.json` (3 件) |
| `nlm_catalog_check.py` | NLM Catalog API client | `expected_nlm_*.json` (4 件) |
| `three_class_classifier.py` | 3 分類統合 logic | (上記両 module 経由で間接的に) |
| `tests/test_crossref_check.py` | crossref_check 単体 test | 同 module の fixture |
| `tests/test_nlm_catalog_check.py` | nlm_catalog_check 単体 test | 同 module の fixture |
| `tests/test_three_class_classifier.py` | 統合 test (A/B/C/unknown) | 全 fixture |

**API key 不要**: 全 test は fixture 直読のため、ANTHROPIC_API_KEY / NCBI_API_KEY なしで CI 実行可能.

## fixture 更新の運用

fixture は API 応答の snapshot. 将来 Crossref / NLM Catalog の response schema が変更されたら以下手順で更新:

1. Day13 INVESTIGATION §4.2 の curl コマンドを再実行 (本 README §由来 と同じ)
2. fixture file を上書き
3. test を実行し、production code の parser が新 schema で動くか確認
4. 必要なら production code (`crossref_check.py` / `nlm_catalog_check.py`) の parse logic を更新
5. 更新を Day-N の archive に記録 (Day11 D11-3 の運用継続)

## Day11 命名規約との関係

Day11 で確立された `expected_*` (deterministic golden) / `baseline_*` (variability-bearing document-of-record) のうち、本 fixture は **全て `expected_*`**:

- 本 fixture は API 応答の input snapshot で、production code 内の logic は deterministic
- 各 test は fixture を input として、deterministic な分類結果 (`A`/`B`/`C`/`unknown`) を assert
- API 応答の variability (Crossref が同 DOI に対して異なる応答を返す等) は extremely rare で、test scope 外

**対比**: Day11 Vancouver fixture (`tests/fixtures/vancouver_24refs/`) は LLM/PubMed variability を含むため `baseline_*` を併用したが、本 fixture は API response 直読で variability なし → `expected_*` 統一.

---

**作成日**: 2026/05/16 (Day15 Phase 0)
**作成者**: Claude Code (Sonnet 4.6)
**メンテナ**: 片山英樹 (Hideki Katayama)
**関連 SPEC/INVESTIGATION**:
- `docs/sessions/day15/SPEC_three_class_audit.md` §6.3 (本 fixture の設計)
- `docs/sessions/day13/INVESTIGATION_unresolved_2refs.md` §4.2 (curl 再現手順 = 本 fixture の出所)
