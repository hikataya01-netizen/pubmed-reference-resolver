# pubmed-reference-resolver 監査レポート

**入力**: `../サンプル/ref2.pdf`  |  **実行**: 2026-04-20 12:47:02

---

## ダッシュボード

| 指標 | 件数 | 状態 |
|------|----:|:----:|
| 総参照数 | 29 | — |
| 解決 (PMID取得) | 13 | OK |
| **未解決 (要確認)** | **16** | ATTN |
| **重複引用** | **1** | MAJOR |
| 査読コメント: 重大 | 8 | MAJOR |
| 査読コメント: 要検討 | 5 | WARN |
| 査読コメント: 軽微 | 1 | — |

> **査読者が確認すべき項目: 計 29 件** (重大 8 / 要検討 5 / 未解決 16)

---

## 1. 要確認項目 (優先度順)

### 1.1 [MAJOR] 重大な不整合

**必ず査読コメントとして言及することを推奨します。**

- **Ref #13 は Ref #2 と同一論文の重複引用です。**
- **Ref #13 タイトル一致度 68% (PMID: 40594166) — 別論文の可能性が高い。**
  - 引用: "Association of glucocorticoids with outcomes in critically ill patients: A cohort study based on the"
  - PubMed: "Association of glucocorticoids with outcomes in critically ill patients with sepsis-associated acute"
- **Ref #22 タイトル一致度 37% (PMID: 36825895) — 別論文の可能性が高い。**
  - 引用: "Meta-analysis of glucocorticoids in COVID-19: Impacts on mortality in in-hospital settings"
  - PubMed: "Development and External Validation of a Prediction Model for Quality of Life of ICU Survivors: A Su"
- **Ref #23 引用年 2024 ≠ PubMed年 2022 (PMID: 36490303)** — 2年以上の乖離、別論文の可能性も。
- **Ref #23 タイトル一致度 43% (PMID: 36490303) — 別論文の可能性が高い。**
  - 引用: "Impact of early corticosteroids on 60-day mortality in critically ill patients with COVID-19"
  - PubMed: "The influence of race tactics for performance in the heats of an international sprint cross-country "
- **Ref #24 タイトル一致度 50% (PMID: 38490654) — 別論文の可能性が高い。**
  - 引用: "Efficacy and safety of glucocorticoids therapy of severe community-acquired pneumonia: A systematic "
  - PubMed: "Impact of chronic oral glucocorticoid treatment on mortality in patients with COVID-19: analysis of "
- **Ref #27 引用年 2024 ≠ PubMed年 2021 (PMID: 33590875)** — 2年以上の乖離、別論文の可能性も。
- **Ref #27 タイトル一致度 36% (PMID: 33590875) — 別論文の可能性が高い。**
  - 引用: "A contemporary review of glucocorticoids in the management of inflammatory arthritis"
  - PubMed: "IL11 is elevated in systemic sclerosis and IL11-dependent ERK signalling underlies TGFβ-mediated act"

### 1.2 [MODERATE] 要検討

文脈に応じて査読コメントを検討してください。

- Ref #14 引用年 2024 ≠ PubMed年 2025 (PMID: 40597594) — epub/print年の差の可能性。
- Ref #15 タイトル一致度 78% (PMID: 36942789)。
  - 引用: "Hydrocortisone in Severe Community-Acquired Pneumonia: A Randomized Clinical Tri..."
  - PubMed: "Hydrocortisone in Severe Community-Acquired Pneumonia...."
- Ref #17 タイトル一致度 82% (PMID: 38802435)。
  - 引用: "In-hospital survival of critically ill COVID-19 patients treated with glucocorti..."
  - PubMed: "In-hospital survival of critically ill COVID-19 patients treated with glucocorti..."
- Ref #22 引用年 2024 ≠ PubMed年 2023 (PMID: 36825895) — epub/print年の差の可能性。
- Ref #25 タイトル一致度 72% (PMID: 30659379)。
  - 引用: "Effect of preadmission glucocorticoid therapy on 30-day mortality in critically ..."
  - PubMed: "Effect of preadmission glucocorticoid therapy on 30-day mortality in critically ..."

### 1.3 [MINOR] 軽微な差異

通常は人間査読で無視して問題ありません（参考情報）。

- Ref #3 タイトルに微小な表記差 (一致度 98%、PMID: 26216001)

---

## 2. 未解決参照の詳細

**計 16 件** が PubMed で解決できませんでした。理由の多くは MEDLINE 非収録誌または書籍です。

### 一覧

| # | タイトル | ジャーナル | 年 | DOI | 言語 | 推定理由 |
|--:|---------|----------|---:|-----|:---:|---------|
| 1 | Do corticosteroids affect immunotherapy efficacy in cancer … | J Clin Oncol | 2024 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 2 | Association of glucocorticoids with outcomes in critically … | Nature | 2025 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 4 | Corticosteroids in oncology: Use, overuse, indications, and… | ScienceDirect | 2022 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 5 | Evaluating the impact of long-term glucocorticoid use on ca… | J Clin Oncol | 2025 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 7 | Systematic review of glucocorticoids in cancer immunotherapy | J Clin Oncol | 2023 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 8 | The role of glucocorticoids in cancer care: A study of curr… | Support Care Cancer | 2023 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 9 | Use of Glucocorticoids in Critical Care: A Narrative Review | Am J Respir Crit Care Med | 2024 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 10 | Effect of glucocorticoids for the management of immune-rela… | Oncology Letters | 2024 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 12 | Glucocorticoid use and complications following immune check… | Sci Rep | 2020 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 16 | Surviving Sepsis Campaign: Guidelines on the Management of … | Intensive Care Med | 2023 | `10.1007/s00134-023-06729-9` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 18 | Systematic Review on the Efficacy of Glucocorticoids for Cr… | Medicine | 2024 | `10.1097/MD.0000000000020456` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 19 | Glucocorticoids and Risk of Mortality in Critically Ill Pat… | Intensive Care Med | 2024 | `10.1007/s00134-023-07130-7` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 20 | A randomized controlled trial of glucocorticoid discontinua… | Ann Rheum Dis | 2024 | `10.1136/annrheumdis-2024-226620` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 21 | Clinical outcomes in elderly patients treated with glucocor… | Systematic Reviews | 2024 | `10.1186/s13643-022-02006-y` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 28 | The role of corticosteroids in the management of hematologi… | Leukemia | 2024 | `10.1038/s41375-024-00778-z` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 29 | Evaluating corticosteroid protocols in managing severe alle… | Allergy | 2024 | `10.1111/all.15236` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |

### 参照ごとの試行詳細

#### Ref #1

- **元引用**: `Byron Y. Do corticosteroids affect immunotherapy efficacy in cancer patients? J Clin Oncol. 2024.`
- **構造化結果**: Do corticosteroids affect immunotherapy efficacy in cancer patients? / J Clin Oncol / 2024 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 44 < 90

#### Ref #2

- **元引用**: `Zhu X, et al. Association of glucocorticoids with outcomes in critically ill patients: A cohort study based on the MIMIC-III database. Nature. 2025.`
- **構造化結果**: Association of glucocorticoids with outcomes in critically ill patients: A cohort study based on the MIMIC-III database / Nature / 2025 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 63 < 90

#### Ref #4

- **元引用**: `Faggiano A. Corticosteroids in oncology: Use, overuse, indications, and contraindications. ScienceDirect. 2022.`
- **構造化結果**: Corticosteroids in oncology: Use, overuse, indications, and contraindications / ScienceDirect / 2022 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 40 < 90

#### Ref #5

- **元引用**: `Hakem Zadeh F. Evaluating the impact of long-term glucocorticoid use on cancer outcomes. J Clin Oncol. 2025.`
- **構造化結果**: Evaluating the impact of long-term glucocorticoid use on cancer outcomes / J Clin Oncol / 2025 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 47 < 90

#### Ref #7

- **元引用**: `Li B, et al. Systematic review of glucocorticoids in cancer immunotherapy. J Clin Oncol. 2023.`
- **構造化結果**: Systematic review of glucocorticoids in cancer immunotherapy / J Clin Oncol / 2023 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 59 < 90

#### Ref #8

- **元引用**: `Zhao Y, Tan L. The role of glucocorticoids in cancer care: A study of current practices. Support Care Cancer. 2023.`
- **構造化結果**: The role of glucocorticoids in cancer care: A study of current practices / Support Care Cancer / 2023 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #9

- **元引用**: `Chaudhuri D, et al. Use of Glucocorticoids in Critical Care: A Narrative Review. Am J Respir Crit Care Med. 2024.`
- **構造化結果**: Use of Glucocorticoids in Critical Care: A Narrative Review / Am J Respir Crit Care Med / 2024 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 51 < 90

#### Ref #10

- **元引用**: `Svedman FC, et al. Effect of glucocorticoids for the management of immune-related adverse events: A systematic review. Oncology Letters. 2024.`
- **構造化結果**: Effect of glucocorticoids for the management of immune-related adverse events: A systematic review / Oncology Letters / 2024 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 57 < 90

#### Ref #12

- **元引用**: `Agarwal K, et al. Glucocorticoid use and complications following immune checkpoint inhibitor therapy. Sci Rep. 2020.`
- **構造化結果**: Glucocorticoid use and complications following immune checkpoint inhibitor therapy / Sci Rep / 2020 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 63 < 90

#### Ref #16

- **元引用**: `Alhazzani W, et al. Surviving Sepsis Campaign: Guidelines on the Management of Sepsis and Septic Shock. Intensive Care Med. 2023; 49(10): 1342-1355. DOI: 10.1007/s00134-023-06729-9.`
- **構造化結果**: Surviving Sepsis Campaign: Guidelines on the Management of Sepsis and Septic Shock / Intensive Care Med / 2023 / DOI=10.1007/s00134-023-06729-9
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 83 < 90

#### Ref #18

- **元引用**: `Wang G, et al. Systematic Review on the Efficacy of Glucocorticoids for Critically Ill Patients with Acute Respiratory Distress Syndrome. Medicine. 2024; 103(10): e20456. DOI: 10.1097/MD.0000000000020456.`
- **構造化結果**: Systematic Review on the Efficacy of Glucocorticoids for Critically Ill Patients with Acute Respiratory Distress Syndrome / Medicine / 2024 / DOI=10.1097/MD.0000000000020456
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 61 < 90

#### Ref #19

- **元引用**: `Lee J, et al. Glucocorticoids and Risk of Mortality in Critically Ill Patients: A Population-Based Cohort Study. Intensive Care Med. 2024; 50(1): 95-102. DOI: 10.1007/s00134-023-07130-7.`
- **構造化結果**: Glucocorticoids and Risk of Mortality in Critically Ill Patients: A Population-Based Cohort Study / Intensive Care Med / 2024 / DOI=10.1007/s00134-023-07130-7
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 63 < 90

#### Ref #20

- **元引用**: `Ruyssen-Witrand A, et al. A randomized controlled trial of glucocorticoid discontinuation in older adults. Ann Rheum Dis. 2024; 83(1): 95-102. DOI: 10.1136/annrheumdis-2024-226620.`
- **構造化結果**: A randomized controlled trial of glucocorticoid discontinuation in older adults / Ann Rheum Dis / 2024 / DOI=10.1136/annrheumdis-2024-226620
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 41 < 90

#### Ref #21

- **元引用**: `Tanaka Y, et al. Clinical outcomes in elderly patients treated with glucocorticoids: A systematic review. Systematic Rev. 2024. DOI: 10.1186/s13643-022-02006-y.`
- **構造化結果**: Clinical outcomes in elderly patients treated with glucocorticoids: A systematic review / Systematic Reviews / 2024 / DOI=10.1186/s13643-022-02006-y
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 57 < 90

#### Ref #28

- **元引用**: `Vogelzang NJ, et al. (2024). The role of corticosteroids in the management of hematological malignancies: A focus on practical applications. Leukemia. DOI: 10.1038/s41375-024-00778-z.`
- **構造化結果**: The role of corticosteroids in the management of hematological malignancies: A focus on practical applications / Leukemia / 2024 / DOI=10.1038/s41375-024-00778-z
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 44 < 90

#### Ref #29

- **元引用**: `Smith LT, et al. (2024). Evaluating corticosteroid protocols in managing severe allergic reactions: Current evidence and future directions. Allergy. DOI: 10.1111/all.15236.`
- **構造化結果**: Evaluating corticosteroid protocols in managing severe allergic reactions: Current evidence and future directions / Allergy / 2024 / DOI=10.1111/all.15236
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 35 < 90

---

## 3. 構造化品質 (parsing_confidence < high)

以下の参照は LLM 構造化時に不確実性が検出されました。必要に応じて目視確認を推奨します。

| # | 確度 | タイトル | 備考 |
|--:|:----:|---------|------|
| 1 | medium | Do corticosteroids affect immunotherapy efficacy in cancer … | No volume, issue, pages, or DOI provided; article may be ahead of print or earl… |
| 2 | medium | Association of glucocorticoids with outcomes in critically … | et al. used after first author; no volume, issue, pages, or DOI available. Year… |
| 3 | medium | Glucocorticoids and Cancer | PubMed Central is a repository, not a journal; this may be a book chapter or re… |
| 4 | low | Corticosteroids in oncology: Use, overuse, indications, and… | ScienceDirect is a database/platform, not a journal or publisher. The actual jo… |
| 5 | medium | Evaluating the impact of long-term glucocorticoid use on ca… | No volume, issue, pages, or DOI available; likely an ahead-of-print or early on… |
| 6 | medium | Glucocorticoid regulation of cancer development and progres… | No volume, issue, pages, or DOI provided in the raw citation. |
| 7 | medium | Systematic review of glucocorticoids in cancer immunotherapy | Only first author listed with 'et al.'; no volume, issue, pages, or DOI provide… |
| 8 | medium | The role of glucocorticoids in cancer care: A study of curr… | No volume, issue, pages, or DOI present; likely an ahead-of-print or in-press c… |
| 9 | medium | Use of Glucocorticoids in Critical Care: A Narrative Review | Only first author listed with 'et al.' Volume, issue, and pages not yet availab… |
| 10 | medium | Effect of glucocorticoids for the management of immune-rela… | et al. used; only first author extracted. No volume, issue, pages, or DOI provi… |
| 11 | medium | Systematic review of the clinical effect of glucocorticoids… | No volume, issue, or page information provided in the raw citation. 'et al.' us… |
| 12 | medium | Glucocorticoid use and complications following immune check… | Citation uses 'et al.' so only first author captured. No volume, issue, pages, … |
| 21 | medium | Clinical outcomes in elderly patients treated with glucocor… | Only first author listed with 'et al.' Year given as 2024 but DOI path suggests… |
| 27 | medium | A contemporary review of glucocorticoids in the management … | Author list uses 'et al.' so only first author captured. Surname 'Pérez-Ruiz' c… |
| 28 | medium | The role of corticosteroids in the management of hematologi… | Only first author listed with 'et al.'; no volume, issue, or page numbers provi… |
| 29 | medium | Evaluating corticosteroid protocols in managing severe alle… | et al. used in citation; only first author extracted. No volume, issue, or page… |

---

## 4. 透明性トレース

### 4.1 解決経路の内訳

| 経路 | 件数 | 意味 |
|------|----:|------|
| `unresolved` | 16 | 全カスケード失敗 |
| `doi` | 9 | DOI検索成功 |
| `title_author_year` | 3 | タイトル+第一著者+年で検索 |
| `title_fuzzy` | 1 | タイトル単独fuzzy (≥90%一致) |

### 4.2 PDF由来の行番号混入検出

- 行番号混入なし

### 4.3 全参照のスナップショット

| # | PMID | 経路 | ジャーナル | 年 |
|--:|------|:----:|----------|---:|
| 1 | — | unresolved | J Clin Oncol | 2024 |
| 2 | — | unresolved | Nature | 2025 |
| 3 | 26216001 | title_author_year | Adv Exp Med Biol | 2015 |
| 4 | — | unresolved | ScienceDirect | 2022 |
| 5 | — | unresolved | J Clin Oncol | 2025 |
| 6 | 37143725 | title_author_year | Front Endocrinol (Lausan… | 2023 |
| 7 | — | unresolved | J Clin Oncol | 2023 |
| 8 | — | unresolved | Support Care Cancer | 2023 |
| 9 | — | unresolved | Am J Respir Crit Care Med | 2024 |
| 10 | — | unresolved | Oncology Letters | 2024 |
| 11 | 18373855 | title_author_year | BMC Cancer | 2008 |
| 12 | — | unresolved | Sci Rep | 2020 |
| 13 | 40594166 | doi | Sci Rep | 2025 |
| 14 | 40597594 | title_fuzzy | BMC Anesthesiol | 2025 |
| 15 | 36942789 | doi | N Engl J Med | 2023 |
| 16 | — | unresolved | Intensive Care Med | 2023 |
| 17 | 38802435 | doi | Sci Rep | 2024 |
| 18 | — | unresolved | Medicine | 2024 |
| 19 | — | unresolved | Intensive Care Med | 2024 |
| 20 | — | unresolved | Ann Rheum Dis | 2024 |
| 21 | — | unresolved | Systematic Reviews | 2024 |
| 22 | 36825895 | doi | Crit Care Med | 2023 |
| 23 | 36490303 | doi | PLoS One | 2022 |
| 24 | 38490654 | doi | BMJ Open | 2024 |
| 25 | 30659379 | doi | Ann Intensive Care | 2019 |
| 26 | 32876694 | doi | JAMA | 2020 |
| 27 | 33590875 | doi | Rheumatology (Oxford) | 2021 |
| 28 | — | unresolved | Leukemia | 2024 |
| 29 | — | unresolved | Allergy | 2024 |

---

## 免責事項

本レポートは PubMed メタデータとの機械的突合による **候補抽出** です。
**最終的な査読判断は必ず人間の査読者が行ってください。**
タイトル fuzzy match が低い場合、必ずしも誤引用とは限らず (例: 原典が多言語、タイトル翻訳等)、
コンテキストを踏まえた判断が必要です。