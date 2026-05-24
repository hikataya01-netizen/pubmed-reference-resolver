# pubmed-reference-resolver 監査レポート

**入力**: `tests/fixtures/vancouver_35refs/input_References.docx`  |  **実行**: 2026-05-24 16:54:55

---

## ダッシュボード

| 指標 | 件数 | 状態 |
|------|----:|:----:|
| 総参照数 | 31 | — |
| 解決 (PMID取得) | 22 | OK |
| **未解決 (要確認)** | **9** | ATTN |
| **重複引用** | **0** | OK |
| 査読コメント: 重大 | 2 | MAJOR |
| 査読コメント: 要検討 | 2 | WARN |
| 査読コメント: 軽微 | 1 | — |

> **査読者が確認すべき項目: 計 13 件** (重大 2 / 要検討 2 / 未解決 9)

---

## 1. 要確認項目 (優先度順)

### 1.1 [MAJOR] 重大な不整合

**必ず査読コメントとして言及することを推奨します。**

- **Ref #4 引用年 2014 ≠ PubMed年 2010 (PMID: 20479397)** — 2年以上の乖離、別論文の可能性も。
- **Ref #28 タイトル一致度 43% (PMID: 15280923) — 別論文の可能性が高い。**
  - 引用: "Psychosocial interventions for patients with advanced cancer: a systematic review of the literature"
  - PubMed: "Dual blockade of EGFR and ERK1/2 phosphorylation potentiates growth inhibition of breast cancer cell"

### 1.2 [MODERATE] 要検討

文脈に応じて査読コメントを検討してください。

- Ref #2 タイトル一致度 73% (PMID: 29846122)。
  - 引用: "Recommendations for human epidermal growth factor receptor 2 testing in breast c..."
  - PubMed: "Human Epidermal Growth Factor Receptor 2 Testing in Breast Cancer: American Soci..."
- Ref #18 タイトル一致度 75% (PMID: 34864639)。
  - 引用: "Shame mediates the relationship between stigma and quality of life among patient..."
  - PubMed: "[Shame mediates the relationship between stigma and quality of life among patien..."

### 1.3 [MINOR] 軽微な差異

通常は人間査読で無視して問題ありません（参考情報）。

- Ref #15 タイトルに微小な表記差 (一致度 95%、PMID: 30284181)

---

## 2. 未解決参照の詳細

**計 9 件** が PubMed で解決できませんでした。理由の多くは MEDLINE 非収録誌または書籍です。

### 一覧

| # | タイトル | ジャーナル | 年 | DOI | 言語 | 推定理由 |
|--:|---------|----------|---:|-----|:---:|---------|
| 3 | Psychological impact of metastasized cancer: a systematic r… | BMJ Open | 2021 | `10.1136/bmjopen-2020-040298` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 8 | Tailoring psychosocial interventions to the needs of advanc… | J Psychosoc Oncol | 2010 | `10.1080/07347331003676105` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 12 | The role of psychosocial support in enhancing quality of li… | J Neonatal Surg | 2025 | `10.52783/jns.v14.1552` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 13 | A kognitív viselkedésterápia lehetőségei az onkológiai ellá… | Magy Onkol | 2020 | `-` | other | 非英語 (other)・MEDLINE非収録の可能性 |
| 14 | Nem vagy egyedül! |  | 2023 | `-` | other | 書籍 (PubMed対象外) |
| 24 | Exploratory structural equation modeling analysis of the Se… | Mindfulness | 2017 | `10.1007/s12671-016-0662-1` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 25 | Statistical power analysis for the behavioral sciences |  | 1988 | `-` | en | 書籍 (PubMed対象外) |
| 26 | Statistical methods for meta-analysis |  | 2014 | `-` | en | 書籍 (PubMed対象外) |
| 27 | Cognitive therapy | Psycho-oncology | 2010 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |

### [3 分類化] PubMed 未ヒットの分類

(Day13 INVESTIGATION で発見、Day15 で実装. 詳細は `references/USAGE_QUICKSTART.md` §V Q4 参照)

| ref | 分類 | 理由 |
|:---:|:---:|:---|
| #3 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #8 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #12 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #13 | C | DOI 欠落、journal 'Magy Onkol' は MEDLINE 収録だが 本論文単体は indexing なし |
| #14 | B | book chapter (DOI 欠落だが MEDLINE 対象外) |
| #24 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #25 | B | book chapter (DOI 欠落だが MEDLINE 対象外) |
| #26 | B | book chapter (DOI 欠落だが MEDLINE 対象外) |
| #27 | C | DOI 欠落、journal 'Psycho-oncology' は MEDLINE 収録だが 本論文単体は indexing なし |

**集計**: A (真の捏造) 0 件 / B (MEDLINE 非収録誌) 3 件 / C (収録誌 indexing 漏れ) 2 件 / unknown (判定不可) 4 件

### 参照ごとの試行詳細

#### Ref #3

- **元引用**: `Snoek HM, Dijkstra A, van der Sluis F. Psychological impact of metastasized cancer: a systematic review of qualitative studies. BMJ Open. 2021;11:e040298. doi:10.1136/bmjopen-2020-040298`
- **構造化結果**: Psychological impact of metastasized cancer: a systematic review of qualitative studies / BMJ Open / 2021 / DOI=10.1136/bmjopen-2020-040298
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #8

- **元引用**: `Greer JA, Park ER, Prigerson HG, Safren SA. Tailoring psychosocial interventions to the needs of advanced cancer patients. J Psychosoc Oncol. 2010;28:276-295. doi:10.1080/07347331003676105`
- **構造化結果**: Tailoring psychosocial interventions to the needs of advanced cancer patients / J Psychosoc Oncol / 2010 / DOI=10.1080/07347331003676105
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #12

- **元引用**: `Harish J, Syed A. The role of psychosocial support in enhancing quality of life for cancer patients: challenges and solutions. J Neonatal Surg. 2025;14:384-387. doi:10.52783/jns.v14.1552`
- **構造化結果**: The role of psychosocial support in enhancing quality of life for cancer patients: challenges and solutions / J Neonatal Surg / 2025 / DOI=10.52783/jns.v14.1552
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 51 < 90

#### Ref #13

- **元引用**: `Vizin G, Farkas K. A kognitív viselkedésterápia lehetőségei az onkológiai ellátásban. Magy Onkol. 2020;64:62-69.`
- **構造化結果**: A kognitív viselkedésterápia lehetőségei az onkológiai ellátásban / Magy Onkol / 2020 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 41 < 90

#### Ref #14

- **元引用**: `Vizin G. Nem vagy egyedül!. 2023.`
- **構造化結果**: Nem vagy egyedül! / - / 2023 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #24

- **元引用**: `Tóth-Király I, Bőthe B, Orosz G. Exploratory structural equation modeling analysis of the Self-Compassion Scale. Mindfulness. 2017;8:881-892. doi:10.1007/s12671-016-0662-1`
- **構造化結果**: Exploratory structural equation modeling analysis of the Self-Compassion Scale / Mindfulness / 2017 / DOI=10.1007/s12671-016-0662-1
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 69 < 90

#### Ref #25

- **元引用**: `Cohen J. Statistical power analysis for the behavioral sciences. 1988.`
- **構造化結果**: Statistical power analysis for the behavioral sciences / - / 1988 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #26

- **元引用**: `Hedges LV, Olkin I. Statistical methods for meta-analysis. 2014.`
- **構造化結果**: Statistical methods for meta-analysis / - / 2014 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #27

- **元引用**: `Moorey S, Holland J, Breitbart W, Jacobsen P. Cognitive therapy. Psycho-oncology. 2010:402-407.`
- **構造化結果**: Cognitive therapy / Psycho-oncology / 2010 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 26 < 90

---

## 3. 構造化品質 (parsing_confidence < high)

以下の参照は LLM 構造化時に不確実性が検出されました。必要に応じて目視確認を推奨します。

| # | 確度 | タイトル | 備考 |
|--:|:----:|---------|------|
| 13 | medium | A kognitív viselkedésterápia lehetőségei az onkológiai ellá… | Hungarian language article. Title translates roughly to 'Possibilities of cogni… |
| 14 | low | Nem vagy egyedül! | Hungarian-language reference. No journal or publisher information provided; lik… |
| 25 | low | Statistical power analysis for the behavioral sciences | Book reference; no publisher information provided. No DOI or PMID available. Pu… |
| 26 | low | Statistical methods for meta-analysis | Book reference with no publisher information. Year 2014 may refer to a reprint/… |
| 27 | medium | Cognitive therapy | Hyphen in 'Psycho-oncology' preserved as it is a compound journal name. No volu… |

---

## 4. 透明性トレース

### 4.1 解決経路の内訳

| 経路 | 件数 | 意味 |
|------|----:|------|
| `doi` | 20 | DOI検索成功 |
| `unresolved` | 9 | 全カスケード失敗 |
| `title_fuzzy` | 1 | タイトル単独fuzzy (≥90%一致) |
| `title_author_year` | 1 | タイトル+第一著者+年で検索 |

### 4.2 PDF由来の行番号混入検出

- 行番号混入なし

### 4.3 全参照のスナップショット

| # | PMID | 経路 | ジャーナル | 年 |
|--:|------|:----:|----------|---:|
| 1 | 34642313 | doi | NPJ Breast Cancer | 2021 |
| 2 | 29846122 | doi | J Clin Oncol | 2018 |
| 3 | — | unresolved | BMJ Open | 2021 |
| 4 | 20479397 | title_fuzzy | J Clin Oncol | 2010 |
| 5 | 36602400 | doi | Cancer Med | 2023 |
| 6 | 19807473 | doi | Expert Rev Pharmacoecon … | 2002 |
| 7 | 23319686 | doi | J Clin Oncol | 2013 |
| 8 | — | unresolved | J Psychosoc Oncol | 2010 |
| 9 | 33478252 | title_author_year | J Health Psychol | 2022 |
| 10 | 28525559 | doi | Ann Oncol | 2017 |
| 11 | 37405330 | doi | Front Health Serv | 2023 |
| 12 | — | unresolved | J Neonatal Surg | 2025 |
| 13 | — | unresolved | Magy Onkol | 2020 |
| 14 | — | unresolved | — | 2023 |
| 15 | 30284181 | doi | Qual Life Res | 2019 |
| 16 | 19996233 | doi | Psychosomatics | 2009 |
| 17 | 22639392 | doi | Int J Behav Med | 2013 |
| 18 | 34864639 | doi | Orv Hetil | 2021 |
| 19 | 32102523 | doi | Asian Pac J Cancer Prev | 2020 |
| 20 | 689890 | doi | Health Educ Monogr | 1978 |
| 21 | 7844739 | doi | J Pers Assess | 1994 |
| 22 | 25202967 | doi | PLoS One | 2014 |
| 23 | 23070875 | doi | J Clin Psychol | 2013 |
| 24 | — | unresolved | Mindfulness | 2017 |
| 25 | — | unresolved | — | 1988 |
| 26 | — | unresolved | — | 2014 |
| 27 | — | unresolved | Psycho-oncology | 2010 |
| 28 | 15280923 | doi | Br J Cancer | 2004 |
| 29 | 20205038 | doi | Psychol Health | 2009 |
| 30 | 19604706 | doi | Crit Rev Oncol Hematol | 2010 |
| 31 | 25787828 | doi | Psychooncology | 2016 |

---

## 免責事項

本レポートは PubMed メタデータとの機械的突合による **候補抽出** です。
**最終的な査読判断は必ず人間の査読者が行ってください。**
タイトル fuzzy match が低い場合、必ずしも誤引用とは限らず (例: 原典が多言語、タイトル翻訳等)、
コンテキストを踏まえた判断が必要です。

---

## 補遺: ジャーナル名と PubMed 収載誌の照合監査 (追加)

解決済み 22 件全件について citation journal と PubMed journal_iso の類似度を計算した結果、
類似度 50% 未満のケースは検出されませんでした。
全 22 件が略称表記の差異を含めて 80% 以上の一致を示し、ジャーナル名記載に
系統的な誤りは認められませんでした。

詳細データ: `journal_mismatch_audit.json` (同ディレクトリ内)
