# pubmed-reference-resolver 監査レポート

**入力**: `tests/fixtures/mdpi_173refs/input_References.docx`  |  **実行**: 2026-05-24 17:29:58

---

## ダッシュボード

| 指標 | 件数 | 状態 |
|------|----:|:----:|
| 総参照数 | 171 | — |
| 解決 (PMID取得) | 159 | OK |
| **未解決 (要確認)** | **12** | ATTN |
| **重複引用** | **0** | OK |
| 査読コメント: 重大 | 2 | MAJOR |
| 査読コメント: 要検討 | 6 | WARN |
| 査読コメント: 軽微 | 14 | — |

> **査読者が確認すべき項目: 計 20 件** (重大 2 / 要検討 6 / 未解決 12)

---

## 1. 要確認項目 (優先度順)

### 1.1 [MAJOR] 重大な不整合

**必ず査読コメントとして言及することを推奨します。**

- **Ref #21 タイトル一致度 35% (PMID: 28768654) — 別論文の可能性が高い。**
  - 引用: "Effect of the interaction between diet composition and the PPM1K genetic variant on insulin resistan"
  - PubMed: "Effect of the interaction between diet composition and the "
- **Ref #128 ジャーナル名とDOIが不一致 (PMID: 23318720)** — 引用 `International Journal of Obesity` vs PubMed `Int J Obes (Lond)` (類似度 45%)

### 1.2 [MODERATE] 要検討

文脈に応じて査読コメントを検討してください。

- Ref #14 タイトル一致度 85% (PMID: 40395625)。
  - 引用: "Type 2 diabetes mellitus—Conventional therapies and future perspectives in innov..."
  - PubMed: "Type 2 diabetes mellitus - conventional therapies and future perspectives in inn..."
- Ref #42 タイトル一致度 86% (PMID: 27812911)。
  - 引用: "The obesity paradox: Is it really a paradox?..."
  - PubMed: "The obesity paradox: is it really a paradox? Hypertension...."
- Ref #65 タイトル一致度 83% (PMID: 15561918)。
  - 引用: "β-cell function in obesity: Effects of weight loss..."
  - PubMed: "beta-cell function in obesity: effects of weight loss...."
- Ref #85 タイトル一致度 83% (PMID: 2180315)。
  - 引用: "Impaired Insulin Action But Normal Insulin-Receptor Activity In Diabetic Rat-Liv..."
  - PubMed: "Impaired insulin action but normal insulin receptor activity in diabetic rat liv..."
- Ref #158 引用年 2024 ≠ PubMed年 2023 (PMID: 38665424) — epub/print年の差の可能性。
- Ref #160 引用年 2023 ≠ PubMed年 2024 (PMID: 38325988) — epub/print年の差の可能性。

### 1.3 [MINOR] 軽微な差異

通常は人間査読で無視して問題ありません（参考情報）。

- Ref #4 タイトルに微小な表記差 (一致度 98%、PMID: 41857071)
- Ref #19 タイトルに微小な表記差 (一致度 92%、PMID: 19336687)
- Ref #44 タイトルに微小な表記差 (一致度 99%、PMID: 31130916)
- Ref #51 タイトルに微小な表記差 (一致度 92%、PMID: 16227664)
- Ref #59 タイトルに微小な表記差 (一致度 97%、PMID: 18459586)
- Ref #72 タイトルに微小な表記差 (一致度 99%、PMID: 33561645)
- Ref #76 タイトルに微小な表記差 (一致度 91%、PMID: 20547980)
- Ref #80 タイトルに微小な表記差 (一致度 99%、PMID: 10644884)
- Ref #116 タイトルに微小な表記差 (一致度 98%、PMID: 23782937)
- Ref #118 タイトルに微小な表記差 (一致度 96%、PMID: 6885229)
- Ref #123 タイトルに微小な表記差 (一致度 98%、PMID: 40851148)
- Ref #134 タイトルに微小な表記差 (一致度 98%、PMID: 1728813)
- Ref #153 タイトルに微小な表記差 (一致度 96%、PMID: 36507635)
- Ref #162 タイトルに微小な表記差 (一致度 99%、PMID: 21298579)

---

## 2. 未解決参照の詳細

**計 12 件** が PubMed で解決できませんでした。理由の多くは MEDLINE 非収録誌または書籍です。

### 一覧

| # | タイトル | ジャーナル | 年 | DOI | 言語 | 推定理由 |
|--:|---------|----------|---:|-----|:---:|---------|
| 26 | Molecular Mechanisms of Insulin Resistance in Diabetes | Diabetes: An Old Disease, A N… | 2013 | `10.1007/978-1-4614-5441-0_19` | en | 書籍 (PubMed対象外) |
| 41 | Metabolic Syndrome and Type 2 Diabetes Mellitus in Overweig… | J. Child | 2024 | `10.26650/jchild.2024.1527424` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 50 | Scientific-Based Research and Randomized Controlled Trials,… | Qual. Inq. | 2014 | `10.1177/1077800413508523` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 86 | Overweight effects on metabolic rate, time perception, dise… | Translational Medicine of Agi… | 2025 | `10.1016/j.tma.2024.12.001` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 99 | Illustrated Biochemistry |  | 2003 | `-` | en | 書籍 (PubMed対象外) |
| 103 | Influences of dietary oils and fats, and the accompanied mi… | Trends in Food Science & Tech… | 2021 | `10.1016/j.tifs.2021.05.001` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 104 | Surfactants, Lipids, and Surface Chemistry | Essential Chemistry for Formu… | 2016 | `-` | en | 書籍 (PubMed対象外) |
| 111 | How does the ratio of ATP yield from the complete oxidation… | Biochem. Educ. | 1998 | `10.1016/S0307-4412(97)00046-0` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 122 | Insulin resistance—"The good or the bad and ugly" | Neuroendocrinol. Lett. | 2018 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 126 | Free-living Total Energy Expenditure Assessed using Three A… | Med. Sci. Sports Exerc. | 2017 | `10.1249/01.mss.0000518362.85418.f8` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 136 | Energy Requirement Methodology |  | 2017 | `-` | en | 書籍 (PubMed対象外) |
| 166 | Metabolic rate predicts the lifespan of workers in the bumb… | Apidologie | 2019 | `10.1007/s13592-018-0630-y` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |

### [3 分類化] PubMed 未ヒットの分類

(Day13 INVESTIGATION で発見、Day15 で実装. 詳細は `references/USAGE_QUICKSTART.md` §V Q4 参照)

| ref | 分類 | 理由 |
|:---:|:---:|:---|
| #26 | C | journal 'Advances in Experimental Medicine and Biology' は MEDLINE 収録 (currentindexingstatus=Y) だが本論… |
| #41 | unknown | NLM Catalog status 不明: esearch returned no NLM ID |
| #50 | B | journal 'Qualitative Inquiry' は MEDLINE 非収録 (currentindexingstatus=N, publisher=SAGE Publications) |
| #86 | B | journal 'Translational Medicine of Aging' は MEDLINE 非収録 (currentindexingstatus=N, publisher=Elsevie… |
| #99 | B | book chapter (DOI 欠落だが MEDLINE 対象外) |
| #103 | unknown | NLM Catalog status 不明: unexpected currentindexingstatus='' |
| #104 | B | book chapter (DOI 欠落だが MEDLINE 対象外) |
| #111 | B | journal 'Biochemical Education' は MEDLINE 非収録 (currentindexingstatus=N, publisher=Elsevier BV) |
| #122 | C | DOI 欠落、journal 'Neuroendocrinol. Lett.' は MEDLINE 収録だが 本論文単体は indexing なし |
| #126 | C | journal 'Medicine &amp; Science in Sports &amp; Exercise' は MEDLINE 収録 (currentindexingstatus=Y) だが… |
| #136 | B | book chapter (DOI 欠落だが MEDLINE 対象外) |
| #166 | B | journal 'Apidologie' は MEDLINE 非収録 (currentindexingstatus=N, publisher=Springer Science and Busines… |

**集計**: A (真の捏造) 0 件 / B (MEDLINE 非収録誌) 7 件 / C (収録誌 indexing 漏れ) 3 件 / unknown (判定不可) 2 件

### 参照ごとの試行詳細

#### Ref #26

- **元引用**: `Soumaya K. Molecular Mechanisms of Insulin Resistance in Diabetes. Diabetes: An Old Disease, A New Insight 2013, Volume 771, 240–251. https://doi.org/10.1007/978-1-4614-5441-0_19`
- **構造化結果**: Molecular Mechanisms of Insulin Resistance in Diabetes / Diabetes: An Old Disease, A New Insight / 2013 / DOI=10.1007/978-1-4614-5441-0_19
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #41

- **元引用**: `Demirbuga A; Poyrazoglu S; Bundak R. Metabolic Syndrome and Type 2 Diabetes Mellitus in Overweight and Obese Children: A Single Centre Experience. J. Child 2024, 24, 154–161. https://doi.org/10.26650/jchild.2024.1527424`
- **構造化結果**: Metabolic Syndrome and Type 2 Diabetes Mellitus in Overweight and Obese Children: A Single Centre Experience / J. Child / 2024 / DOI=10.26650/jchild.2024.1527424
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 75 < 90

#### Ref #50

- **元引用**: `Christ TW. Scientific-Based Research and Randomized Controlled Trials, the “Gold” Standard? Alternative Paradigms and Mixed Methodologies. Qual. Inq. 2014, 20, 72–80. https://doi.org/10.1177/1077800413508523`
- **構造化結果**: Scientific-Based Research and Randomized Controlled Trials, the "Gold" Standard? Alternative Paradigms and Mixed Methodologies / Qual. Inq. / 2014 / DOI=10.1177/1077800413508523
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #86

- **元引用**: `Oshakbayev K; Durmanova A; Nabiyev A; Sarria-Santamera A; Idrissov A; Bedelbayeva G; Gaipov A; Mitra A; Gazaliyeva M; Dukenbayeva B. Overweight effects on metabolic rate, time perception, diseases, aging, and lifespan: A systematic review with meta-regression analysis. Transl. Med. Aging 2025, 9, 1…`
- **構造化結果**: Overweight effects on metabolic rate, time perception, diseases, aging, and lifespan: A systematic review with meta-regression analysis / Translational Medicine of Aging / 2025 / DOI=10.1016/j.tma.2024.12.001
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #99

- **元引用**: `Murray RK; Granner DK; Mayes PA; Rodwell VW. Illustrated Biochemistry 2003.`
- **構造化結果**: Illustrated Biochemistry / - / 2003 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #103

- **元引用**: `Ye Z; Xu Y; Liu Y. Influences of dietary oils and fats, and the accompanied minor content of components on the gut microbiota and gut inflammation: A review. Trends Food Sci. Technol. 2021, 113, 255–276. https://doi.org/10.1016/j.tifs.2021.05.001`
- **構造化結果**: Influences of dietary oils and fats, and the accompanied minor content of components on the gut microbiota and gut inflammation: A review / Trends in Food Science & Technology / 2021 / DOI=10.1016/j.tifs.2021.05.001
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 43 < 90

#### Ref #104

- **元引用**: `Kulkarni V; Shaw C. Surfactants, Lipids, and Surface Chemistry. Essential Chemistry for Formulators of Semisolid and Liquid Dosages 2016, 5–19.`
- **構造化結果**: Surfactants, Lipids, and Surface Chemistry / Essential Chemistry for Formulators of Semisolid and Liquid Dosages / 2016 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #111

- **元引用**: `Darvey I. How does the ratio of ATP yield from the complete oxidation of palmitic acid to that of glucose compare with the relative energy contents of fat and carbohydrate? Biochem. Educ. 1998, 26, 22–23. https://doi.org/10.1016/S0307-4412(97)00046-0`
- **構造化結果**: How does the ratio of ATP yield from the complete oxidation of palmitic acid to that of glucose compare with the relative energy contents of fat and carbohydrate? / Biochem. Educ. / 1998 / DOI=10.1016/S0307-4412(97)00046-0
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 45 < 90

#### Ref #122

- **元引用**: `Szosland K; Lewinski A. Insulin resistance—“The good or the bad and ugly”. Neuroendocrinol. Lett. 2018, 39, 355–362.`
- **構造化結果**: Insulin resistance—"The good or the bad and ugly" / Neuroendocrinol. Lett. / 2018 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — fuzzy 87 < 90
  - `[title_fuzzy]` NG — fuzzy 58 < 90

#### Ref #126

- **元引用**: `Kraus W; McCrory M; Bhapkar M; Weiss E; Martin C; DeLany J; Roberts S; Das S; Racette S. Free-living Total Energy Expenditure Assessed using Three Accelerometer Models Validated against Doubly-Labelled Water. Med. Sci. Sports Exerc. 2017, 49, 529. https://doi.org/10.1249/01.mss.0000518362.85418.f8`
- **構造化結果**: Free-living Total Energy Expenditure Assessed using Three Accelerometer Models Validated against Doubly-Labelled Water / Med. Sci. Sports Exerc. / 2017 / DOI=10.1249/01.mss.0000518362.85418.f8
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #136

- **元引用**: `DeLany J. Energy Requirement Methodology 2017, 85–102.`
- **構造化結果**: Energy Requirement Methodology / - / 2017 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #166

- **元引用**: `Kelemen EP; Cao N; Cao T; Davidowitz G; Dornhaus A. Metabolic rate predicts the lifespan of workers in the bumble bee Bombus impatiens. Apidologie 2019, 50, 195–203. https://doi.org/10.1007/s13592-018-0630-y`
- **構造化結果**: Metabolic rate predicts the lifespan of workers in the bumble bee Bombus impatiens / Apidologie / 2019 / DOI=10.1007/s13592-018-0630-y
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

---

## 3. 構造化品質 (parsing_confidence < high)

以下の参照は LLM 構造化時に不確実性が検出されました。必要に応じて目視確認を推奨します。

| # | 確度 | タイトル | 備考 |
|--:|:----:|---------|------|
| 26 | medium | Molecular Mechanisms of Insulin Resistance in Diabetes | This appears to be a book chapter in an edited volume (Advances in Experimental… |
| 42 | medium | The obesity paradox: Is it really a paradox? | The raw citation appears to have 'Hypertension.' as a stray word or misplaced f… |
| 59 | medium | Human visceral fat in different anthropometric patterns and… | No DOI present. MDPI-style citation. All major fields extracted successfully. |
| 99 | low | Illustrated Biochemistry | Book reference (likely Harper's Illustrated Biochemistry). No publisher or ISBN… |
| 104 | medium | Surfactants, Lipids, and Surface Chemistry | This appears to be a book chapter. 'Essential Chemistry for Formulators of Semi… |
| 118 | medium | Nutrition, aging and obesity—A critical review of a complex… | Hyphen in 'critical-review' rescued per preprocessing hint; reconstructed as 'c… |
| 122 | medium | Insulin resistance—"The good or the bad and ugly" | No DOI present. Authors separated by semicolons (MDPI-like style). Title contai… |
| 136 | low | Energy Requirement Methodology | Appears to be a book chapter with pages 85–102, published in 2017. No journal, … |

---

## 4. 透明性トレース

### 4.1 解決経路の内訳

| 経路 | 件数 | 意味 |
|------|----:|------|
| `doi` | 157 | DOI検索成功 |
| `unresolved` | 12 | 全カスケード失敗 |
| `title_author_year` | 2 | タイトル+第一著者+年で検索 |

### 4.2 PDF由来の行番号混入検出

- 行番号混入なし

### 4.3 全参照のスナップショット

| # | PMID | 経路 | ジャーナル | 年 |
|--:|------|:----:|----------|---:|
| 1 | 36949618 | doi | Diabetes Obes Metab | 2023 |
| 2 | 35026882 | doi | J Pediatr Endocrinol Met… | 2022 |
| 3 | 38410415 | doi | J Obes | 2024 |
| 4 | 41857071 | doi | Nat Rev Dis Primers | 2026 |
| 5 | 25935570 | doi | J Acad Nutr Diet | 2015 |
| 6 | 34802979 | doi | Prim Care Diabetes | 2022 |
| 7 | 30938762 | doi | J Clin Endocrinol Metab | 2019 |
| 8 | 36982786 | doi | Int J Mol Sci | 2023 |
| 9 | 25240392 | doi | Obes Surg | 2015 |
| 10 | 35333446 | doi | Obesity (Silver Spring) | 2022 |
| 11 | 36432557 | doi | Nutrients | 2022 |
| 12 | 35315311 | doi | Postgrad Med | 2022 |
| 13 | 41049880 | doi | Health Sci Rep | 2025 |
| 14 | 40395625 | doi | Biochem Biophys Rep | 2025 |
| 15 | 37056675 | doi | Front Endocrinol (Lausan… | 2023 |
| 16 | 38078586 | doi | Diabetes Care | 2024 |
| 17 | 32827435 | doi | J Clin Endocrinol Metab | 2020 |
| 18 | 35163806 | doi | Int J Mol Sci | 2022 |
| 19 | 19336687 | doi | Diabetes | 2009 |
| 20 | 30852132 | doi | Lancet Diabetes Endocrin… | 2019 |
| 21 | 28768654 | doi | Am J Clin Nutr | 2017 |
| 22 | 24559919 | doi | Vitam Horm | 2014 |
| 23 | 11333990 | doi | N Engl J Med | 2001 |
| 24 | 29556093 | doi | Hypertens Res | 2018 |
| 25 | 33477912 | doi | Nutrients | 2021 |
| 26 | — | unresolved | Diabetes: An Old Disease… | 2013 |
| 27 | 40149500 | doi | Genes (Basel) | 2025 |
| 28 | 26451283 | doi | Adipocyte | 2015 |
| 29 | 39415589 | doi | Curr Cardiol Rev | 2025 |
| 30 | 21474268 | doi | Domest Anim Endocrinol | 2011 |
| 31 | 11244467 | doi | Int J Obes Relat Metab D… | 2001 |
| 32 | 24530118 | doi | Diabetes Res Clin Pract | 2014 |
| 33 | 25344447 | doi | Rev Endocr Metab Disord | 2014 |
| 34 | 19228873 | doi | Diabetes Care | 2009 |
| 35 | 38086922 | doi | Nat Rev Mol Cell Biol | 2024 |
| 36 | 24780048 | doi | J Clin Endocrinol Metab | 2014 |
| 37 | 22827962 | doi | Clin Biochem | 2012 |
| 38 | 39086662 | doi | Front Cell Dev Biol | 2024 |
| 39 | 40001516 | doi | Biomolecules | 2025 |
| 40 | 36362108 | doi | Int J Mol Sci | 2022 |
| 41 | — | unresolved | J. Child | 2024 |
| 42 | 27812911 | doi | Eat Weight Disord | 2017 |
| 43 | 31118651 | doi | Vasc Health Risk Manag | 2019 |
| 44 | 31130916 | doi | Front Endocrinol (Lausan… | 2019 |
| 45 | 31857443 | doi | Diabetes Care | 2020 |
| 46 | 26608649 | doi | Nutr J | 2015 |
| 47 | 28163748 | doi | Nutr Metab (Lond) | 2017 |
| 48 | 30431378 | doi | Curr Med Res Opin | 2019 |
| 49 | 33789819 | doi | J Clin Epidemiol | 2021 |
| 50 | — | unresolved | Qual. Inq. | 2014 |
| 51 | 16227664 | doi | Perspect Biol Med | 2005 |
| 52 | 39678229 | doi | Diabetes Metab Syndr Obes | 2024 |
| 53 | 26742056 | doi | Nutrients | 2016 |
| 54 | 31085992 | doi | Int J Mol Sci | 2019 |
| 56 | 34869522 | doi | Front Nutr | 2021 |
| 57 | 31832130 | doi | Ther Adv Endocrinol Metab | 2019 |
| 58 | 26931143 | doi | BMC Public Health | 2016 |
| 59 | 18459586 | title_author_year | Anal Quant Cytol Histol | 2008 |
| 60 | 23666871 | doi | Obesity (Silver Spring) | 2014 |
| 61 | 34100954 | doi | Endocr Rev | 2022 |
| 62 | 30869158 | doi | J Physiol | 2020 |
| 63 | 38706718 | doi | J Pharm Pharm Sci | 2024 |
| 64 | 38397072 | doi | Int J Mol Sci | 2024 |
| 65 | 15561918 | doi | Diabetes | 2004 |
| 66 | 37372966 | doi | Int J Mol Sci | 2023 |
| 67 | 40064750 | doi | Rev Endocr Metab Disord | 2025 |
| 68 | 36718668 | doi | Biosci Rep | 2023 |
| 69 | 32651241 | doi | Diabetes | 2020 |
| 70 | 35269467 | doi | Cells | 2022 |
| 71 | 26997538 | doi | Metabolism | 2016 |
| 72 | 33561645 | doi | Biomed Pharmacother | 2021 |
| 73 | 32752107 | doi | Int J Mol Sci | 2020 |
| 74 | 39109850 | doi | J Clin Endocrinol Metab | 2025 |
| 75 | 31141317 | doi | Mol Nutr Food Res | 2019 |
| 76 | 20547980 | doi | Diabetes | 2010 |
| 77 | 27284940 | doi | J Vis Exp | 2016 |
| 78 | 28065828 | doi | Cell Metab | 2017 |
| 80 | 10644884 | doi | J Biomed Sci | 2000 |
| 81 | 38068912 | doi | Int J Mol Sci | 2023 |
| 82 | 16493415 | doi | Nat Rev Mol Cell Biol | 2006 |
| 83 | 35054822 | doi | Int J Mol Sci | 2022 |
| 84 | 40636148 | doi | Front Physiol | 2025 |
| 85 | 2180315 | doi | Am J Physiol | 1990 |
| 86 | — | unresolved | Translational Medicine o… | 2025 |
| 87 | 41155837 | doi | Medicina (Kaunas) | 2025 |
| 88 | 41405657 | doi | Saudi Pharm J | 2025 |
| 89 | 36148880 | doi | Diabetes Care | 2022 |
| 90 | 28081776 | doi | Metabolism | 2017 |
| 91 | 37892437 | doi | Nutrients | 2023 |
| 92 | 36888890 | doi | Nutr Rev | 2023 |
| 93 | 22449319 | doi | N Engl J Med | 2012 |
| 94 | 15256820 | doi | Horm Res | 2004 |
| 95 | 25632827 | doi | J Physiol Biochem | 2015 |
| 96 | 41598484 | doi | J Clin Med | 2026 |
| 97 | 40737109 | doi | Acta Clin Belg | 2025 |
| 98 | 40626220 | doi | Front Nutr | 2025 |
| 99 | — | unresolved | — | 2003 |
| 100 | 25591987 | doi | Exp Mol Med | 2015 |
| 101 | 30829532 | doi | Nutr Hosp | 2019 |
| 102 | 26086330 | doi | J Clin Endocrinol Metab | 2015 |
| 103 | — | unresolved | Trends in Food Science &… | 2021 |
| 104 | — | unresolved | Essential Chemistry for … | 2016 |
| 105 | 39206417 | doi | Diabetes Metab Syndr Obes | 2024 |
| 106 | 38394525 | doi | Medicine (Baltimore) | 2024 |
| 107 | 30786833 | doi | Circ Res | 2019 |
| 108 | 34047935 | doi | Front Med | 2021 |
| 109 | 28692856 | doi | Curr Opin Plant Biol | 2017 |
| 110 | 28475761 | doi | FEMS Yeast Res | 2017 |
| 111 | — | unresolved | Biochem. Educ. | 1998 |
| 112 | 37163428 | doi | Aging Dis | 2023 |
| 113 | 37039941 | doi | Biol Trace Elem Res | 2023 |
| 114 | 38763181 | doi | Cell Signal | 2024 |
| 115 | 39380265 | doi | Cell Mol Biol (Noisy-le-… | 2024 |
| 116 | 23782937 | doi | Clin Chim Acta | 2013 |
| 117 | 25315502 | doi | BMC Med | 2014 |
| 118 | 6885229 | title_author_year | Int J Obes | 1983 |
| 119 | 11133069 | doi | Endocr Rev | 2000 |
| 120 | 26967715 | doi | Atherosclerosis | 2016 |
| 121 | 25077985 | doi | Cardiovasc Diabetol | 2014 |
| 122 | — | unresolved | Neuroendocrinol. Lett. | 2018 |
| 123 | 40851148 | doi | J Pak Med Assoc | 2025 |
| 124 | 30254244 | doi | Eur J Clin Nutr | 2019 |
| 125 | 30844720 | doi | Front Biosci (Landmark E… | 2019 |
| 126 | — | unresolved | Med. Sci. Sports Exerc. | 2017 |
| 127 | 30998529 | doi | Exerc Sport Sci Rev | 2019 |
| 128 | 23318720 | doi | Int J Obes (Lond) | 2013 |
| 129 | 26187233 | doi | J Gerontol A Biol Sci Me… | 2015 |
| 130 | 35181758 | doi | Int J Obes (Lond) | 2022 |
| 131 | 25016971 | doi | Clin Nutr | 2015 |
| 132 | 35542387 | doi | Curr Dev Nutr | 2022 |
| 133 | 27739007 | doi | Curr Obes Rep | 2016 |
| 134 | 1728813 | doi | Am J Clin Nutr | 1992 |
| 135 | 30496740 | doi | Physiol Behav | 2019 |
| 136 | — | unresolved | — | 2017 |
| 137 | 31322803 | doi | Aging Cell | 2019 |
| 138 | 32201887 | doi | J Gerontol A Biol Sci Me… | 2020 |
| 139 | 30976490 | doi | Acta Pharm Sin B | 2019 |
| 140 | 25559400 | doi | J Clin Endocrinol Metab | 2015 |
| 141 | 15768047 | doi | Nat Rev Mol Cell Biol | 2005 |
| 142 | 28193912 | doi | Oncotarget | 2017 |
| 143 | 30862304 | doi | J Am Coll Nutr | 2019 |
| 144 | 27061677 | doi | Lancet | 2016 |
| 145 | 31912596 | doi | J Intern Med | 2020 |
| 146 | 30535086 | doi | Am J Clin Nutr | 2018 |
| 147 | 20518700 | doi | Antioxid Redox Signal | 2011 |
| 148 | 27901032 | doi | Eur J Clin Nutr | 2017 |
| 149 | 31207126 | doi | Clin Obes | 2019 |
| 150 | 24847411 | doi | Am J Case Rep | 2014 |
| 151 | 32057825 | doi | Exp Gerontol | 2020 |
| 152 | 26808532 | doi | PLoS One | 2016 |
| 153 | 36507635 | doi | Diabetes Care | 2023 |
| 154 | 40081802 | doi | Clin Nutr ESPEN | 2025 |
| 155 | 36876592 | doi | Br J Nutr | 2023 |
| 156 | 38695175 | doi | Circ Heart Fail | 2024 |
| 157 | 32483221 | doi | Eur J Clin Nutr | 2020 |
| 158 | 38665424 | doi | Front Endocrinol (Lausan… | 2023 |
| 159 | 35667273 | doi | Clin Nutr | 2022 |
| 160 | 38325988 | doi | J Am Coll Cardiol | 2024 |
| 161 | 18654066 | doi | Postgrad Med | 2008 |
| 162 | 21298579 | doi | Curr Hypertens Rep | 2011 |
| 163 | 36883605 | doi | Eur J Endocrinol | 2023 |
| 164 | 34940594 | doi | Metabolites | 2021 |
| 165 | 29576535 | doi | Cell Metab | 2018 |
| 166 | — | unresolved | Apidologie | 2019 |
| 167 | 33966355 | doi | Obesity (Silver Spring) | 2021 |
| 168 | 23074240 | doi | Am J Physiol Endocrinol … | 2012 |
| 169 | 35357099 | doi | Asia Pac J Clin Nutr | 2022 |
| 170 | 28066773 | doi | Front Nutr | 2016 |
| 171 | 38068863 | doi | Nutrients | 2023 |
| 172 | 33535876 | doi | Gut Microbes | 2021 |
| 173 | 32259716 | doi | Nutrition | 2020 |

---

## 免責事項

本レポートは PubMed メタデータとの機械的突合による **候補抽出** です。
**最終的な査読判断は必ず人間の査読者が行ってください。**
タイトル fuzzy match が低い場合、必ずしも誤引用とは限らず (例: 原典が多言語、タイトル翻訳等)、
コンテキストを踏まえた判断が必要です。

---

## 補遺: ジャーナル名と PubMed 収載誌の照合監査 (追加)

解決済み 159 件全件について citation journal と PubMed journal_iso の類似度を計算した結果、
類似度 50% 未満のケースは **1件のみ** (Ref #128) でした。
残り 158 件は略称表記の差異を含めて 80% 以上の一致を示し、ジャーナル名記載に
系統的な誤りは認められませんでした。

詳細データ: `journal_mismatch_audit.json` (同ディレクトリ内)
