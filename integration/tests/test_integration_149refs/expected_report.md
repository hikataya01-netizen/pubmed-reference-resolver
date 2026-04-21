# pubmed-reference-resolver 監査レポート

**入力**: `References.docx`  |  **実行**: 2026-04-20 06:54:28

---

## ダッシュボード

| 指標 | 件数 | 状態 |
|------|----:|:----:|
| 総参照数 | 149 | — |
| 解決 (PMID取得) | 115 | OK |
| **未解決 (要確認)** | **34** | ATTN |
| **重複引用** | **0** | OK |
| 査読コメント: 重大 | 4 | MAJOR |
| 査読コメント: 要検討 | 32 | WARN |
| 査読コメント: 軽微 | 9 | — |

> **査読者が確認すべき項目: 計 70 件** (重大 4 / 要検討 32 / 未解決 34)

---

## 1. 要確認項目 (優先度順)

### 1.1 [MAJOR] 重大な不整合

**必ず査読コメントとして言及することを推奨します。**

- **Ref #5 タイトル一致度 50% (PMID: 31610923) — 別論文の可能性が高い。**
  - 引用: "Intervention centrée sur les ressources pour réduire les troubles anxieux et dépressifs chez les pat"
  - PubMed: "[Intervention focused on resources to reduce anxiety and depression disorders in cancer patients: A "
- **Ref #18 タイトル一致度 51% (PMID: 31462531) — 別論文の可能性が高い。**
  - 引用: "Savović, J.; Page, M.J.; Elbers, R.G.; Blencowe, N.S.; Boutron, I.; Cates, C.J.; Cheng, H.Y.; Corbet"
  - PubMed: "RoB 2: a revised tool for assessing risk of bias in randomised trials."
- **Ref #106 引用年 2011 ≠ PubMed年 2013 (PMID: 21910162)** — 2年以上の乖離、別論文の可能性も。
- **Ref #13 ジャーナル名とDOIが完全に不一致 (PMID: 28591864)** — 引用では `Ultrasound Med. Biol.` と記載されているが、DOI (`10.1093/jjco/hyx079`) が指す雑誌は `Jpn J Clin Oncol` (類似度 44%)。タイトル・著者・年・巻号は一致しているため、**著者のジャーナル名誤記** と強く推定される。引用元を Jpn. J. Clin. Oncol. に訂正する必要あり。

### 1.2 [MODERATE] 要検討

文脈に応じて査読コメントを検討してください。

- Ref #3 引用年 2022 ≠ PubMed年 2023 (PMID: 36610333) — epub/print年の差の可能性。
- Ref #12 引用年 2024 ≠ PubMed年 2025 (PMID: 39348716) — epub/print年の差の可能性。
- Ref #16 引用年 2011 ≠ PubMed年 2012 (PMID: 22124343) — epub/print年の差の可能性。
- Ref #23 引用年 2020 ≠ PubMed年 2021 (PMID: 32918129) — epub/print年の差の可能性。
- Ref #24 引用年 2020 ≠ PubMed年 2021 (PMID: 32939680) — epub/print年の差の可能性。
- Ref #27 引用年 2016 ≠ PubMed年 2017 (PMID: 27723939) — epub/print年の差の可能性。
- Ref #32 引用年 2016 ≠ PubMed年 2017 (PMID: 27072749) — epub/print年の差の可能性。
- Ref #40 引用年 2017 ≠ PubMed年 2018 (PMID: 28665008) — epub/print年の差の可能性。
- Ref #41 引用年 2017 ≠ PubMed年 2018 (PMID: 28554229) — epub/print年の差の可能性。
- Ref #42 引用年 2018 ≠ PubMed年 2019 (PMID: 30514112) — epub/print年の差の可能性。
- Ref #43 引用年 2019 ≠ PubMed年 2020 (PMID: 31509614) — epub/print年の差の可能性。
- Ref #47 タイトル一致度 82% (PMID: 33610930)。
  - 引用: "d.S.; Paiva, E.M.d.C.; Nogueira, D.A.; Mills, J. Quality of life, selfcompassion..."
  - PubMed: "Quality of life, self-compassion and mindfulness in cancer patients undergoing c..."
- Ref #48 引用年 2017 ≠ PubMed年 2018 (PMID: 28960718) — epub/print年の差の可能性。
- Ref #49 引用年 2021 ≠ PubMed年 2022 (PMID: 34514549) — epub/print年の差の可能性。
- Ref #50 引用年 2015 ≠ PubMed年 2016 (PMID: 26708250) — epub/print年の差の可能性。
- Ref #55 引用年 2014 ≠ PubMed年 2015 (PMID: 25303007) — epub/print年の差の可能性。
- Ref #56 引用年 2015 ≠ PubMed年 2016 (PMID: 26559446) — epub/print年の差の可能性。
- Ref #67 引用年 2016 ≠ PubMed年 2017 (PMID: 27731954) — epub/print年の差の可能性。
- Ref #68 引用年 2017 ≠ PubMed年 2018 (PMID: 28725952) — epub/print年の差の可能性。
- Ref #73 引用年 2016 ≠ PubMed年 2017 (PMID: 27479936) — epub/print年の差の可能性。
- Ref #75 引用年 2015 ≠ PubMed年 2016 (PMID: 25711851) — epub/print年の差の可能性。
- Ref #78 引用年 2021 ≠ PubMed年 2022 (PMID: 34668264) — epub/print年の差の可能性。
- Ref #80 引用年 2021 ≠ PubMed年 2022 (PMID: 34751457) — epub/print年の差の可能性。
- Ref #81 引用年 2022 ≠ PubMed年 2023 (PMID: 35686311) — epub/print年の差の可能性。
- Ref #83 タイトル一致度 81% (PMID: 35535488)。
  - 引用: "; ŞahinBayındır, G.; Kayış, A.; Buzlu, S. The effect of psychosocial distress an..."
  - PubMed: "The effect of psychosocial distress and self-transcendence on resilience in pati..."
- Ref #84 引用年 2020 ≠ PubMed年 2021 (PMID: 33161489) — epub/print年の差の可能性。
- Ref #88 タイトル一致度 84% (PMID: 34029344)。
  - 引用: "Á lvarezFuentes, E.; Iraurgi, I. Resilience and coping strategies in relation to..."
  - PubMed: "Resilience and coping strategies in relation to mental health outcomes in people..."
- Ref #91 引用年 2016 ≠ PubMed年 2017 (PMID: 27167009) — epub/print年の差の可能性。
- Ref #92 引用年 2013 ≠ PubMed年 2014 (PMID: 23526623) — epub/print年の差の可能性。
- Ref #96 引用年 2018 ≠ PubMed年 2019 (PMID: 30324585) — epub/print年の差の可能性。
- Ref #107 引用年 2009 ≠ PubMed年 2010 (PMID: 19353527) — epub/print年の差の可能性。
- Ref #111 引用年 2015 ≠ PubMed年 2016 (PMID: 26215314) — epub/print年の差の可能性。

### 1.3 [MINOR] 軽微な差異

通常は人間査読で無視して問題ありません（参考情報）。

- Ref #2 タイトルに微小な表記差 (一致度 99%、PMID: 36311374)
- Ref #6 タイトルに微小な表記差 (一致度 96%、PMID: 11392865)
- Ref #37 タイトルに微小な表記差 (一致度 94%、PMID: 33413485)
- Ref #69 タイトルに微小な表記差 (一致度 94%、PMID: 20878854)
- Ref #77 タイトルに微小な表記差 (一致度 90%、PMID: 24506500)
- Ref #80 タイトルに微小な表記差 (一致度 99%、PMID: 34751457)
- Ref #100 タイトルに微小な表記差 (一致度 99%、PMID: 21511071)
- Ref #129 タイトルに微小な表記差 (一致度 98%、PMID: 22559117)
- Ref #145 タイトルに微小な表記差 (一致度 99%、PMID: 31078056)

---

## 2. 未解決参照の詳細

**計 34 件** が PubMed で解決できませんでした。理由の多くは MEDLINE 非収録誌または書籍です。

### 一覧

| # | タイトル | ジャーナル | 年 | DOI | 言語 | 推定理由 |
|--:|---------|----------|---:|-----|:---:|---------|
| 4 | Les Ressources Psychologiques Face Aux Maladies Somatiques … | PSN | 2022 | `-` | fr | 非英語 (fr)・MEDLINE非収録の可能性 |
| 7 | Positive Psychology | Theory Psychol | 2008 | `10.1177/0959354308093397` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 8 | Centenary Personality: Are There Psychological Resources th… | J. Happiness Stud | 2023 | `10.1007/s10902-023-00700-z` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 9 | Resource Activation: Using Clients’ Own Strengths in Psycho… | Hogrefe Publishing | 2010 | `-` | en | 書籍 (PubMed対象外) |
| 10 | Social and Psychological Resources and Adaptation | Rev. Gen. Psychol | 2002 | `10.1037/1089-2680.6.4.307` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 11 | POSITIVE PSYCHOLOGICAL CAPITAL: MEASUREMENT AND RELATIONSHI… | Pers. Psychol | 2007 | `10.1111/j.1744-6570.2007.00083.x` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 19 | Psychologie de La Santé-2e Éd: Concepts, Méthodes et Modèles | Dunod | 2021 | `-` | fr | 書籍 (PubMed対象外) |
| 25 | La différence du vécu du cancer chez les personnes créative… | Ann. MedicoPsychologiques | 2021 | `10.1016/j.amp.2020.08.019` | fr | 非英語 (fr)・MEDLINE非収録の可能性 |
| 26 | The Role of Gratitude in Breast Cancer: Its Relationships w… | J. Happiness Stud | 2012 | `10.1007/s10902-012-9330-x` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 45 | Dispositional Mindfulness, Psychological Distress, and Post… | J. Loss Trauma | 2017 | `10.1080/15325024.2017.1384783` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 66 | Posttraumatic growth and predictor variables in Brazilian w… | Psicooncología | 2020 | `10.5209/psic.68243` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 70 | Zięba, M. Basic Trust and Posttraumatic Growth in Oncology … | J. Loss Trauma | 2013 | `10.1080/15325024.2012.687289` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 113 | Benefit-Finding and Benefit-Reminding | Handb. Posit. Psychol | 2002 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 114 | Routledge International Handbook of Positive Health Sciences | Taylor & Francis | 2023 | `-` | en | 書籍 (PubMed対象外) |
| 115 | Defying the Crowd: Cultivating Creativity in a Culture of C… | Free press | 1995 | `-` | en | 書籍 (PubMed対象外) |
| 116 | Les Pouvoirs de La Gratitude | Odile Jacob | 2016 | `-` | fr | 書籍 (PubMed対象外) |
| 117 |  |  | - | `-` | en | 構造化不十分（確認要） |
| 118 | Positive psychology 2.0: Towards a balanced interactive mod… | Can. Psychol. Can | 2011 | `10.1037/a0022511` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 120 | Addressing Fundamental Questions About Mindfulness | Psychol. Inq | 2007 | `10.1080/10478400701703344` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 121 | Mindfulness | In: The Palgrave Encyclopedia… | 2023 | `-` | en | 書籍 (PubMed対象外) |
| 123 |  |  | - | `-` | en | 構造化不十分（確認要） |
| 124 | Posttraumatic Growth: Conceptual Foundations and Empirical … | Psychol. Inq | 2004 | `10.1207/s15327965pli1501_01` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 125 | Les Interventions En Psychologie Positive Auprès de Personn… | PSN | 2019 | `-` | fr | 非英語 (fr)・MEDLINE非収録の可能性 |
| 126 | Resilience in Development | In: Handbook of positive psyc… | 2002 | `-` | en | 書籍 (PubMed対象外) |
| 127 | Resilience: Promoting Well-Being Through Recovery, Sustaina… | Res. Hum. Dev | 2010 | `10.1080/15427609.2010.504431` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 131 | Psychological Well-Being in Adult Life | Curr. Dir. Psychol. Sci | 1995 | `10.1111/1467-8721.ep10772395` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 132 | Self-Compassion and Psychological Well-Being | Seppälä, E.M., Simon-Thomas, … | 2017 | `-` | en | 書籍 (PubMed対象外) |
| 134 | Self-Efficacy Mechanism in Human Agency | Am. Psychol | 1982 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 135 | Self-Efficacy: The Exercise of Control | W H Freeman/Times Books/ Henr… | 1997 | `-` | en | 書籍 (PubMed対象外) |
| 137 | Conceiving the Self | Basic Book: New York | 1986 | `-` | en | 書籍 (PubMed対象外) |
| 140 | I Donaldson, S. The critiques and criticisms of positive ps… | J. Posit. Psychol | 2023 | `10.1080/17439760.2023.2178956` | de | 非英語 (de)・MEDLINE非収録の可能性 |
| 141 | Character Strengths and Virtues: A Handbook and Classificat… | American Psychological Associ… | 2004 | `-` | en | 書籍 (PubMed対象外) |
| 143 | HOW BODY IMAGE AFFECTS CANCER PATIENTS’ COPING WITH THE DIS… | J. Sch. Univ. Med | 2021 | `10.51546/jsum.2021.8304` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 148 | Editors' Introduction to the Special Section on Replicabili… | Perspect. Psychol. Sci. | 2012 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |

### 参照ごとの試行詳細

#### Ref #4

- **元引用**: `Robieux, L.; Bridou, M. Les Ressources Psychologiques Face Aux Maladies Somatiques Chroniques. PSN 2022, 20, 37–56.`
- **構造化結果**: Les Ressources Psychologiques Face Aux Maladies Somatiques Chroniques / PSN / 2022 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #7

- **元引用**: `Becker, D.; Marecek, J. Positive Psychology. Theory Psychol. 2008, 18, 591–604, https://doi.org/10.1177/0959354308093397.`
- **構造化結果**: Positive Psychology / Theory Psychol / 2008 / DOI=10.1177/0959354308093397
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 34 < 90

#### Ref #8

- **元引用**: `Merino, M.D.; Sánchez-Ortega, M.; Elvira-Flores, E.; Mateo-Rodríguez, I. Centenary Personality: Are There Psychological Re-sources that Distinguish Centenarians?. J. Happiness Stud. 2023, 24, 2723–2745, https://doi.org/10.1007/s10902-023-00700-z.`
- **構造化結果**: Centenary Personality: Are There Psychological Resources that Distinguish Centenarians? / J. Happiness Stud / 2023 / DOI=10.1007/s10902-023-00700-z
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #9

- **元引用**: `Flückiger, C.; Wüsten, G.; Zinbarg, R.E.; Wampold, B.E. Resource Activation: Using Clients’ Own Strengths in Psychotherapy and Counseling.; Hogrefe Publishing, 2010; ISBN 0-88937-378-7.`
- **構造化結果**: Resource Activation: Using Clients’ Own Strengths in Psychotherapy and Counseling / Hogrefe Publishing / 2010 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #10

- **元引用**: `Hobfoll, S.E. Social and Psychological Resources and Adaptation. Rev. Gen. Psychol. 2002, 6, 307–324, https://doi.org/10.1037/1089-2680.6.4.307.`
- **構造化結果**: Social and Psychological Resources and Adaptation / Rev. Gen. Psychol / 2002 / DOI=10.1037/1089-2680.6.4.307
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 46 < 90

#### Ref #11

- **元引用**: `Luthans, F.; Avolio, B.J.; Avey, J.B.; Norman, S.M. POSITIVE PSYCHOLOGICAL CAPITAL: MEASUREMENT AND RELA-TIONSHIP WITH PERFORMANCE AND SATISFACTION. Pers. Psychol. 2007, 60, 541–572, https://doi.org/10.1111/j.1744-6570.2007.00083.x.`
- **構造化結果**: POSITIVE PSYCHOLOGICAL CAPITAL: MEASUREMENT AND RELATIONSHIP WITH PERFORMANCE AND SATISFACTION / Pers. Psychol / 2007 / DOI=10.1111/j.1744-6570.2007.00083.x
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 58 < 90

#### Ref #19

- **元引用**: `Bruchon-Schweitzer, M.; Boujut, E. Psychologie de La Santé-2e Éd: Concepts, Méthodes et Modèles; Dunod, 2021; ISBN 2-10-082289-6.`
- **構造化結果**: Psychologie de La Santé-2e Éd: Concepts, Méthodes et Modèles / Dunod / 2021 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #25

- **元引用**: `Delpech, L.; Sordes, F.; Sudres, J.-L. La différence du vécu du cancer chez les personnes créatives. Une étude exploratoire. Ann. Medico-Psychologiques 2021, 179, 438–441, https://doi.org/10.1016/j.amp.2020.08.019.`
- **構造化結果**: La différence du vécu du cancer chez les personnes créatives. Une étude exploratoire / Ann. MedicoPsychologiques / 2021 / DOI=10.1016/j.amp.2020.08.019
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #26

- **元引用**: `Ruini, C.; Vescovelli, F. The Role of Gratitude in Breast Cancer: Its Relationships with Post-traumatic Growth, Psychological Well-Being and Distress. J. Happiness Stud. 2012, 14, 263–274, https://doi.org/10.1007/s10902-012-9330-x.`
- **構造化結果**: The Role of Gratitude in Breast Cancer: Its Relationships with Post-traumatic Growth, Psychological Well-Being and Distress / J. Happiness Stud / 2012 / DOI=10.1007/s10902-012-9330-x
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #45

- **元引用**: `Omid, A.; Mohammadi, A.S.; Jalaeikhoo, H.; Taghva, A. Dispositional Mindfulness, Psychological Distress, and Posttraumatic Growth in Cancer Patients. J. Loss Trauma 2017, 22, 681–688, https://doi.org/10.1080/15325024.2017.1384783.`
- **構造化結果**: Dispositional Mindfulness, Psychological Distress, and Posttraumatic Growth in Cancer Patients / J. Loss Trauma / 2017 / DOI=10.1080/15325024.2017.1384783
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #66

- **元引用**: `Quiroga, C.V.; Dacroce, L.R.B.; Rudnicki, T.; Argimon, I.I.D.L. Posttraumatic growth and predictor variables in Brazilian women with breast cancer. 2020, 17, 91–103, https://doi.org/10.5209/psic.68243.`
- **構造化結果**: Posttraumatic growth and predictor variables in Brazilian women with breast cancer / Psicooncología / 2020 / DOI=10.5209/psic.68243
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #70

- **元引用**: `Trzebiński, J.; Zięba, M. Basic Trust and Posttraumatic Growth in Oncology Patients. J. Loss Trauma 2013, 18, 195–209, https://doi.org/10.1080/15325024.2012.687289.`
- **構造化結果**: Zięba, M. Basic Trust and Posttraumatic Growth in Oncology Patients / J. Loss Trauma / 2013 / DOI=10.1080/15325024.2012.687289
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #113

- **元引用**: `Tennen, H.; Affleck, G. Benefit-Finding and Benefit-Reminding. Handb. Posit. Psychol. 2002, 1, 584–597.`
- **構造化結果**: Benefit-Finding and Benefit-Reminding / Handb. Posit. Psychol / 2002 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 40 < 90

#### Ref #114

- **元引用**: `Burke, J.; Boniwell, I.; Frates, B.; Lianov, L.S.; O’boyle, C.A. Routledge International Handbook of Positive Health Sciences; Taylor & Francis: London, United Kingdom, 2023; ISBN: .`
- **構造化結果**: Routledge International Handbook of Positive Health Sciences / Taylor & Francis / 2023 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #115

- **元引用**: `Sternberg, R.J.; Lubart, T.I. Defying the Crowd: Cultivating Creativity in a Culture of Conformity.; Free press, 1995; ISBN 0-02-931475-5.`
- **構造化結果**: Defying the Crowd: Cultivating Creativity in a Culture of Conformity / Free press / 1995 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #116

- **元引用**: `Shankland, R. Les Pouvoirs de La Gratitude; Odile Jacob, 2016; ISBN 2-7381-5969-9.`
- **構造化結果**: Les Pouvoirs de La Gratitude / Odile Jacob / 2016 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #117

- **元引用**: `Rand, K.L.; Cheavens, J.S.`
- **構造化結果**: - / - / - / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #118

- **元引用**: `Wong, P.T.P. Positive psychology 2.0: Towards a balanced interactive model of the good life.. Can. Psychol. Can. 2011, 52, 69–81, https://doi.org/10.1037/a0022511.`
- **構造化結果**: Positive psychology 2.0: Towards a balanced interactive model of the good life / Can. Psychol. Can / 2011 / DOI=10.1037/a0022511
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #120

- **元引用**: `Brown, K.W.; Ryan, R.M.; Creswell, J.D. Addressing Fundamental Questions About Mindfulness. Psychol. Inq. 2007, 18, 272– 281, https://doi.org/10.1080/10478400701703344.`
- **構造化結果**: Addressing Fundamental Questions About Mindfulness / Psychol. Inq / 2007 / DOI=10.1080/10478400701703344
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 56 < 90

#### Ref #121

- **元引用**: `Trousselard, M. Mindfulness. In The Palgrave Encyclopedia of the Possible; Springer, 2023; pp. 875–883.`
- **構造化結果**: Mindfulness / In: The Palgrave Encyclopedia of the Possible; Springer, 2023; pp. 875–883 / 2023 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #123

- **元引用**: `Watson, D.; Naragon, K.`
- **構造化結果**: - / - / - / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #124

- **元引用**: `Tedeschi, R.G.; Calhoun, L.G. Posttraumatic Growth: Conceptual Foundations and Empirical Evidence. Psychol. Inq. 2004, 15, 1–18, doi:10.1207/s15327965pli1501_01.`
- **構造化結果**: Posttraumatic Growth: Conceptual Foundations and Empirical Evidence / Psychol. Inq / 2004 / DOI=10.1207/s15327965pli1501_01
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 43 < 90

#### Ref #125

- **元引用**: `Bridou, M. Les Interventions En Psychologie Positive Auprès de Personnes Souffrant de Pathologies Somatiques Persistantes. PSN 2019, 17, 39–56.`
- **構造化結果**: Les Interventions En Psychologie Positive Auprès de Personnes Souffrant de Pathologies Somatiques Persistantes / PSN / 2019 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #126

- **元引用**: `Masten, A.S.; Reed, M.-G. Resilience in Development. In Handbook of positive psychology; Snyder, C.R., Lopez, S.J., Eds.; Ox-ford University Press: Oxford, 2002; pp. 74–88.`
- **構造化結果**: Resilience in Development / In: Handbook of positive psychology; Snyder, C.R., Lopez, S.J., Eds.; Oxford University Press: Oxford, 2002; pp. 74–88 / 2002 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #127

- **元引用**: `Zautra, A.J.; Arewasikporn, A.; Davis, M.C. Resilience: Promoting Well-Being Through Recovery, Sustainability, and Growth. Res. Hum. Dev. 2010, 7, 221–238, https://doi.org/10.1080/15427609.2010.504431.`
- **構造化結果**: Resilience: Promoting Well-Being Through Recovery, Sustainability, and Growth / Res. Hum. Dev / 2010 / DOI=10.1080/15427609.2010.504431
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 50 < 90

#### Ref #131

- **元引用**: `Ryff, C.D. Psychological Well-Being in Adult Life. Curr. Dir. Psychol. Sci. 1995, 4, 99–104, https://doi.org/10.1111/1467-8721.ep10772395.`
- **構造化結果**: Psychological Well-Being in Adult Life / Curr. Dir. Psychol. Sci / 1995 / DOI=10.1111/1467-8721.ep10772395
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 48 < 90

#### Ref #132

- **元引用**: `Neff, K.; Germer, C. Self-Compassion and Psychological Well-Being; Seppälä, E.M., Simon-Thomas, E., Brown, S.L., Worline, M.C., Cameron, C.D., Doty, J.R., Eds.; Oxford University Press, 2017; Vol. 1;.`
- **構造化結果**: Self-Compassion and Psychological Well-Being / Seppälä, E.M., Simon-Thomas, E., Brown, S.L., Worline, M.C., Cameron, C.D., Doty, J.R., Eds / 2017 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #134

- **元引用**: `Bandura, A. Self-Efficacy Mechanism in Human Agency. Am. Psychol. 1982, 37, 122–122.`
- **構造化結果**: Self-Efficacy Mechanism in Human Agency / Am. Psychol / 1982 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 46 < 90

#### Ref #135

- **元引用**: `Bandura, A. Self-Efficacy: The Exercise of Control; W H Freeman/Times Books/ Henry Holt & Co, 1997; p. 604;.`
- **構造化結果**: Self-Efficacy: The Exercise of Control / W H Freeman/Times Books/ Henry Holt & Co / 1997 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #137

- **元引用**: `Rosenberg, M. Conceiving the Self; Basic Book: New York, 1986;`
- **構造化結果**: Conceiving the Self / Basic Book: New York / 1986 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #140

- **元引用**: ``
- **構造化結果**: I Donaldson, S. The critiques and criticisms of positive psychology: a systematic review / J. Posit. Psychol / 2023 / DOI=10.1080/17439760.2023.2178956
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 64 < 90

#### Ref #141

- **元引用**: `Peterson, C.; Seligman, M.E.P. Character Strengths and Virtues: A Handbook and Classification; 2004;`
- **構造化結果**: Character Strengths and Virtues: A Handbook and Classification / American Psychological Association / Oxford University Press / 2004 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #143

- **元引用**: `Száva, C.; Dégi, C. HOW BODY IMAGE AFFECTS CANCER PATIENTS’ COPING WITH THE DISEASE: BASED ON WIL-LIAMS LIFESKILLS PROGRAMME EXPERIENCES. J. Sch. Univ. Med. 2021, 08, 43–60, https://doi.org/10.51546/jsum.2021.8304.`
- **構造化結果**: HOW BODY IMAGE AFFECTS CANCER PATIENTS’ COPING WITH THE DISEASE: BASED ON WILLIAMS LIFESKILLS PROGRAMME EXPERIENCES / J. Sch. Univ. Med / 2021 / DOI=10.51546/jsum.2021.8304
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 40 < 90

#### Ref #148

- **元引用**: `Pashler, H.; Wagenmakers, E. Editors’ Introduction to the Special Section on Replicability in Psychological Science: A Crisis of Confidence? Perspect. Psychol. Sci. 2012, 7, 528–530.`
- **構造化結果**: Editors' Introduction to the Special Section on Replicability in Psychological Science: A Crisis of Confidence? / Perspect. Psychol. Sci. / 2012 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

---

## 3. 構造化品質 (parsing_confidence < high)

以下の参照は LLM 構造化時に不確実性が検出されました。必要に応じて目視確認を推奨します。

| # | 確度 | タイトル | 備考 |
|--:|:----:|---------|------|
| 4 | medium | Les Ressources Psychologiques Face Aux Maladies Somatiques … |  |
| 9 | low | Resource Activation: Using Clients’ Own Strengths in Psycho… | is_book=true; 'journal' field holds publisher/container; PubMed likely N/A |
| 12 | medium | Characterizing Psychological Resources and Resilience in Pa… |  |
| 19 | low | Psychologie de La Santé-2e Éd: Concepts, Méthodes et Modèles | is_book=true; 'journal' field holds publisher/container; PubMed likely N/A |
| 113 | medium | Benefit-Finding and Benefit-Reminding |  |
| 114 | low | Routledge International Handbook of Positive Health Sciences | is_book=true; 'journal' field holds publisher/container; PubMed likely N/A; is_… |
| 115 | low | Defying the Crowd: Cultivating Creativity in a Culture of C… | is_book=true; 'journal' field holds publisher/container; PubMed likely N/A |
| 116 | low | Les Pouvoirs de La Gratitude | is_book=true; 'journal' field holds publisher/container; PubMed likely N/A |
| 117 | low |  | incomplete_reference_in_source: authors only, no title/journal/year |
| 121 | low | Mindfulness | is_book=true; 'journal' field holds publisher/container; PubMed likely N/A |
| 123 | low |  | incomplete_reference_in_source: authors only, no title/journal/year |
| 125 | medium | Les Interventions En Psychologie Positive Auprès de Personn… |  |
| 126 | low | Resilience in Development | is_book=true; 'journal' field holds publisher/container; PubMed likely N/A |
| 132 | low | Self-Compassion and Psychological Well-Being | is_book=true; 'journal' field holds publisher/container; PubMed likely N/A |
| 134 | medium | Self-Efficacy Mechanism in Human Agency |  |
| 135 | low | Self-Efficacy: The Exercise of Control | is_book=true; 'journal' field holds publisher/container; PubMed likely N/A |
| 137 | low | Conceiving the Self | is_book=true; 'journal' field holds publisher/container; PubMed likely N/A |
| 141 | low | Character Strengths and Virtues: A Handbook and Classificat… | is_book=true; publisher not specified in source (likely APA/Oxford); PubMed unl… |
| 148 | medium | Editors' Introduction to the Special Section on Replicabili… |  |
| 149 | medium | Perceived Crisis and Reforms: Issues, Explanations, and Rem… |  |

---

## 4. 透明性トレース

### 4.1 解決経路の内訳

| 経路 | 件数 | 意味 |
|------|----:|------|
| `doi` | 112 | DOI検索成功 |
| `unresolved` | 34 | 全カスケード失敗 |
| `title_author_year` | 3 | タイトル+第一著者+年で検索 |

### 4.2 PDF由来の行番号混入検出

- **検出**: 336 件 (範囲: 567-910)
- **判定根拠**: LIS長=336（≥10）、値域 567-910、全体候補337件中 336件が単調増加列
- **前処理除去**: ハイフン橋渡し救済 51 件 / 独立行番号除去 285 件

### 4.3 全参照のスナップショット

| # | PMID | 経路 | ジャーナル | 年 |
|--:|------|:----:|----------|---:|
| 1 | 38572751 | doi | CA Cancer J Clin | 2024 |
| 2 | 36311374 | doi | Gen Psychiatr | 2022 |
| 3 | 36610333 | doi | J Psychosom Res | 2023 |
| 4 | — | unresolved | PSN | 2022 |
| 5 | 31610923 | doi | Encephale | 2020 |
| 6 | 11392865 | doi | Am Psychol | 2000 |
| 7 | — | unresolved | Theory Psychol | 2008 |
| 8 | — | unresolved | J. Happiness Stud | 2023 |
| 9 | — | unresolved | Hogrefe Publishing | 2010 |
| 10 | — | unresolved | Rev. Gen. Psychol | 2002 |
| 11 | — | unresolved | Pers. Psychol | 2007 |
| 12 | 39348716 | title_author_year | J Urol | 2025 |
| 13 | 28591864 | doi | Jpn J Clin Oncol | 2017 |
| 14 | 35783766 | doi | Front Psychol | 2022 |
| 15 | 33781993 | doi | BMJ | 2021 |
| 16 | 22124343 | doi | Spinal Cord | 2012 |
| 17 | 31253092 | doi | BMC Med Res Methodol | 2019 |
| 18 | 31462531 | doi | BMJ | 2019 |
| 19 | — | unresolved | Dunod | 2021 |
| 20 | 36199048 | doi | BMC Psychiatry | 2022 |
| 21 | 30128785 | doi | Qual Life Res | 2018 |
| 22 | 29784133 | doi | Eur J Oncol Nurs | 2018 |
| 23 | 32918129 | doi | Support Care Cancer | 2021 |
| 24 | 32939680 | doi | J Behav Med | 2021 |
| 25 | — | unresolved | Ann. MedicoPsychologiques | 2021 |
| 26 | — | unresolved | J. Happiness Stud | 2012 |
| 27 | 27723939 | doi | Psychooncology | 2017 |
| 28 | 31218773 | doi | Psychooncology | 2019 |
| 29 | 20836603 | doi | Health Psychol | 2010 |
| 30 | 27191964 | doi | PLoS One | 2016 |
| 31 | 24722558 | doi | PLoS One | 2014 |
| 32 | 27072749 | doi | Psychooncology | 2017 |
| 33 | 28818112 | doi | Health Qual Life Outcomes | 2017 |
| 34 | 24315542 | doi | Int J Nurs Stud | 2014 |
| 35 | 20579840 | doi | J Pain Symptom Manage | 2010 |
| 36 | 34122231 | doi | Front Psychol | 2021 |
| 37 | 33413485 | doi | Health Qual Life Outcomes | 2021 |
| 38 | 35585529 | doi | BMC Psychiatry | 2022 |
| 39 | 31046153 | doi | Psychooncology | 2019 |
| 40 | 28665008 | doi | Psychooncology | 2018 |
| 41 | 28554229 | doi | Psychol Health Med | 2018 |
| 42 | 30514112 | doi | Psychol Health Med | 2019 |
| 43 | 31509614 | doi | Psychooncology | 2020 |
| 44 | 28888809 | doi | Child Abuse Negl | 2017 |
| 45 | — | unresolved | J. Loss Trauma | 2017 |
| 46 | 28419640 | doi | Psychooncology | 2017 |
| 47 | 33610930 | doi | Eur J Oncol Nurs | 2021 |
| 48 | 28960718 | doi | Br J Health Psychol | 2018 |
| 49 | 34514549 | doi | J Relig Health | 2022 |
| 50 | 26708250 | doi | Psychol Health Med | 2016 |
| 51 | 21391129 | doi | Psychol Health | 2012 |
| 52 | 34323543 | doi | Health Psychol | 2021 |
| 53 | 28635986 | doi | Oncol Nurs Forum | 2017 |
| 54 | 30487907 | doi | Int J Clin Health Psychol | 2018 |
| 55 | 25303007 | doi | Geriatr Gerontol Int | 2015 |
| 56 | 26559446 | doi | Psychol Health | 2016 |
| 57 | 20397294 | doi | Psychol Health | 2010 |
| 58 | 31957127 | doi | Psychooncology | 2020 |
| 59 | 25612065 | doi | Psychooncology | 2015 |
| 60 | 31343219 | doi | Health Psychol | 2019 |
| 61 | 27124466 | doi | PLoS One | 2016 |
| 62 | 22490001 | doi | Psychol Health | 2012 |
| 63 | 36525411 | doi | PLoS One | 2022 |
| 64 | 28981316 | doi | Psychol Trauma | 2018 |
| 65 | 35290419 | doi | PLoS One | 2022 |
| 66 | — | unresolved | Psicooncología | 2020 |
| 67 | 27731954 | doi | Psychooncology | 2017 |
| 68 | 28725952 | doi | J Relig Health | 2018 |
| 69 | 20878854 | doi | Psychooncology | 2011 |
| 70 | — | unresolved | J. Loss Trauma | 2013 |
| 71 | 23073975 | doi | J Trauma Stress | 2012 |
| 72 | 24136875 | doi | Psychooncology | 2013 |
| 73 | 27479936 | doi | Psychooncology | 2017 |
| 74 | 33609048 | doi | Psychooncology | 2021 |
| 75 | 25711851 | doi | Eur J Cancer Care (Engl) | 2016 |
| 76 | 25967598 | doi | Psychooncology | 2015 |
| 77 | 24506500 | doi | Eur J Cancer Care (Engl) | 2014 |
| 78 | 34668264 | doi | Psychooncology | 2022 |
| 79 | 27128438 | doi | PLoS One | 2016 |
| 80 | 34751457 | doi | Psychooncology | 2022 |
| 81 | 35686311 | doi | Psychol Health Med | 2023 |
| 82 | 31087804 | doi | Psychooncology | 2019 |
| 83 | 35535488 | doi | Perspect Psychiatr Care | 2022 |
| 84 | 33161489 | doi | Arch Womens Ment Health | 2021 |
| 85 | 25521911 | doi | Cancer Nurs | 2015 |
| 86 | 29473117 | doi | Support Care Cancer | 2018 |
| 87 | 32726344 | doi | PLoS One | 2020 |
| 88 | 34029344 | doi | PLoS One | 2021 |
| 89 | 36572859 | doi | BMC Psychiatry | 2022 |
| 90 | 31291695 | doi | Psychooncology | 2019 |
| 91 | 27167009 | doi | Psychooncology | 2017 |
| 92 | 23526623 | doi | Clin Psychol Psychother | 2014 |
| 93 | 19659666 | doi | Eur J Cancer Care (Engl) | 2010 |
| 94 | 25756731 | doi | Scand J Caring Sci | 2015 |
| 95 | 33599393 | doi | Nurs Open | 2021 |
| 96 | 30324585 | doi | Qual Life Res | 2019 |
| 97 | 37143028 | doi | BMC Psychiatry | 2023 |
| 98 | 34507151 | doi | Eur J Oncol Nurs | 2021 |
| 99 | 31920312 | doi | Neuropsychiatr Dis Treat | 2019 |
| 100 | 21511071 | doi | J Psychosom Res | 2011 |
| 101 | 28913686 | doi | Int J Colorectal Dis | 2017 |
| 102 | 26651334 | doi | Health Qual Life Outcomes | 2015 |
| 103 | 34509089 | doi | Eur J Oncol Nurs | 2021 |
| 104 | 31670431 | doi | Psychooncology | 2020 |
| 105 | 32714254 | doi | Front Psychol | 2020 |
| 106 | 21910162 | doi | Psychooncology | 2013 |
| 107 | 19353527 | doi | Psychooncology | 2010 |
| 108 | 25889384 | doi | Health Qual Life Outcomes | 2015 |
| 109 | 23448737 | doi | Oncol Nurs Forum | 2013 |
| 110 | 25545043 | doi | Health Psychol | 2015 |
| 111 | 26215314 | doi | Eur J Cancer Care (Engl) | 2016 |
| 112 | 29857179 | doi | J Pain Symptom Manage | 2018 |
| 113 | — | unresolved | Handb. Posit. Psychol | 2002 |
| 114 | — | unresolved | Taylor & Francis | 2023 |
| 115 | — | unresolved | Free press | 1995 |
| 116 | — | unresolved | Odile Jacob | 2016 |
| 117 | — | unresolved | — | — |
| 118 | — | unresolved | Can. Psychol. Can | 2011 |
| 119 | 12703651 | doi | J Pers Soc Psychol | 2003 |
| 120 | — | unresolved | Psychol. Inq | 2007 |
| 121 | — | unresolved | In: The Palgrave Encyclo… | 2023 |
| 122 | 4029106 | doi | Health Psychol | 1985 |
| 123 | — | unresolved | — | — |
| 124 | — | unresolved | Psychol. Inq | 2004 |
| 125 | — | unresolved | PSN | 2019 |
| 126 | — | unresolved | In: Handbook of positive… | 2002 |
| 127 | — | unresolved | Res. Hum. Dev | 2010 |
| 128 | 10953923 | doi | Child Dev | 2000 |
| 129 | 22559117 | doi | Dev Psychopathol | 2012 |
| 130 | 25395975 | doi | Psychiatry Investig | 2014 |
| 131 | — | unresolved | Curr. Dir. Psychol. Sci | 1995 |
| 132 | — | unresolved | Seppälä, E.M., Simon-Tho… | 2017 |
| 133 | 32100897 | doi | Psychooncology | 2020 |
| 134 | — | unresolved | Am. Psychol | 1982 |
| 135 | — | unresolved | W H Freeman/Times Books/… | 1997 |
| 136 | 9952053 | doi | Health Educ Behav | 1999 |
| 137 | — | unresolved | Basic Book: New York | 1986 |
| 138 | 8480217 | title_author_year | Soc Sci Med | 1993 |
| 139 | 12006231 | doi | J Palliat Med | 2002 |
| 140 | — | unresolved | J. Posit. Psychol | 2023 |
| 141 | — | unresolved | American Psychological A… | 2004 |
| 142 | 21346007 | doi | J Health Psychol | 2011 |
| 143 | — | unresolved | J. Sch. Univ. Med | 2021 |
| 144 | 36570997 | doi | Front Psychol | 2022 |
| 145 | 31078056 | doi | Clin Psychol Rev | 2019 |
| 146 | 20091429 | doi | Ann Behav Med | 2010 |
| 147 | 30525784 | doi | Am Psychol | 2018 |
| 148 | — | unresolved | Perspect. Psychol. Sci. | 2012 |
| 149 | 29771554 | title_author_year | Psychol Bull | 2018 |

---

## 免責事項

本レポートは PubMed メタデータとの機械的突合による **候補抽出** です。
**最終的な査読判断は必ず人間の査読者が行ってください。**
タイトル fuzzy match が低い場合、必ずしも誤引用とは限らず (例: 原典が多言語、タイトル翻訳等)、
コンテキストを踏まえた判断が必要です。

---

## 補遺: ジャーナル名と PubMed 収載誌の照合監査 (追加)

解決済み 115 件全件について citation journal と PubMed journal_iso の類似度を計算した結果、
類似度 50% 未満のケースは **1件のみ** (Ref #13) でした。
残り 114 件は略称表記の差異を含めて 80% 以上の一致を示し、ジャーナル名記載に
系統的な誤りは認められませんでした。

詳細データ: `journal_mismatch_audit.json` (同ディレクトリ内)
