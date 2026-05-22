# pubmed-reference-resolver 監査レポート

**入力**: `tests/fixtures/apa_45refs/input_References.docx`  |  **実行**: 2026-05-22 20:20:51

---

## ダッシュボード

| 指標 | 件数 | 状態 |
|------|----:|:----:|
| 総参照数 | 45 | — |
| 解決 (PMID取得) | 25 | OK |
| **未解決 (要確認)** | **20** | ATTN |
| **重複引用** | **0** | OK |
| 査読コメント: 重大 | 0 | OK |
| 査読コメント: 要検討 | 1 | WARN |
| 査読コメント: 軽微 | 2 | — |

> **査読者が確認すべき項目: 計 21 件** (重大 0 / 要検討 1 / 未解決 20)

---

## 1. 要確認項目 (優先度順)

### 1.1 [MAJOR] 重大な不整合

_(該当なし)_

### 1.2 [MODERATE] 要検討

文脈に応じて査読コメントを検討してください。

- Ref #18 引用年 2020 ≠ PubMed年 2021 (PMID: 33340401) — epub/print年の差の可能性。

### 1.3 [MINOR] 軽微な差異

通常は人間査読で無視して問題ありません（参考情報）。

- Ref #23 タイトルに微小な表記差 (一致度 99%、PMID: 23737640)
- Ref #38 タイトルに微小な表記差 (一致度 99%、PMID: 6051769)

---

## 2. 未解決参照の詳細

**計 20 件** が PubMed で解決できませんでした。理由の多くは MEDLINE 非収録誌または書籍です。

### 一覧

| # | タイトル | ジャーナル | 年 | DOI | 言語 | 推定理由 |
|--:|---------|----------|---:|-----|:---:|---------|
| 3 | Service Blueprinting: A Practical Technique for Service Inn… | California Management Review | 2008 | `10.2307/41166446` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 9 | Older adults' experiences and perceptions of digital techno… | Computers in Human Behavior | 2015 | `10.1016/j.chb.2015.01.062` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 10 | The Underlying Structure of Grief: A Taxometric Investigati… | Journal of Psychopathology an… | 2009 | `10.1007/s10862-008-9113-1` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 11 | A conceptual analysis of Ageism | Nordic Psychology | 2009 | `10.1027/1901-2276.61.3.4` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 25 | How professionals deal with clients' explicit objections to… | Discourse Studies | 2022 | `10.1177/14614456221110669` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 26 | Implementing incipient actions: The discourse marker 'so' i… | Journal of Pragmatics | 2009 | `10.1016/j.pragma.2008.10.004` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 28 | Tackling Obesity: Empowering Adults and Children to Live He… | Department of Health and Soci… | 2020 | `-` | en | 書籍 (PubMed対象外) |
| 29 | Clients' resistance to therapists' proposals: Managing epis… | Journal of Pragmatics | 2015 | `10.1016/j.pragma.2015.10.004` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 30 | Laughter in interaction | Cambridge University Press | 2003 | `-` | en | 書籍 (PubMed対象外) |
| 31 | The perceptions of women's roles and progress: a study of M… | Soc. Indic. Res. | 2008 | `10.1007/s11205-008-9242-7` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 32 | Validation of the short forms of the centrality of religios… | Religions | 2020 | `10.3390/rel11020057` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 33 | Short forms of the centrality of religiosity scale: validat… | Religions | 2021 | `10.3390/rel12010009` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 34 | Validation of the short forms of centrality of religiosity … | Religions | 2020 | `10.3390/rel11110577` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 35 | Belief in afterlife and death anxiety: correlates and compa… | OMEGA Journal of Death and Dy… | 1985 | `10.2190/GYPP-VBG3-M3AY-1ML9` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 37 |  | Agency for Integrated Care | 2023 | `-` | en | 構造化不十分（確認要） |
| 40 | Religion and the individual: A social-psychological perspec… |  | 1993 | `-` | en | 書籍 (PubMed対象外) |
| 41 | The multidimensional nature of quest motivation | J. Psychol. Theol. | 2004 | `10.1177/009164710403200401` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 42 | Does religiousness increase with age? Age changes and gener… | Journal for the Scientific St… | 2015 | `10.1111/jssr.12183` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 43 | Defining religion: a practical response | Int. Rev. Sociol. | 2011 | `10.1080/03906701.2011.544190` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 44 | Gender differences in religiosity: a report on Russian data | J. Gend. Stud. | 2023 | `10.1080/09589236.2021.1962702` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |

### [3 分類化] PubMed 未ヒットの分類

(Day13 INVESTIGATION で発見、Day15 で実装. 詳細は `references/USAGE_QUICKSTART.md` §V Q4 参照)

| ref | 分類 | 理由 |
|:---:|:---:|:---|
| #3 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #9 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #10 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #11 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #25 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #26 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #28 | B | book chapter (DOI 欠落だが MEDLINE 対象外) |
| #29 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #30 | B | book chapter (DOI 欠落だが MEDLINE 対象外) |
| #31 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #32 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #33 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #34 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #35 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #37 | unknown | DOI 欠落 + NLM 検索でも判定不可: esearch network failed |
| #40 | B | book chapter (DOI 欠落だが MEDLINE 対象外) |
| #41 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #42 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #43 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #44 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |

**集計**: A (真の捏造) 0 件 / B (MEDLINE 非収録誌) 3 件 / C (収録誌 indexing 漏れ) 0 件 / unknown (判定不可) 17 件

### 参照ごとの試行詳細

#### Ref #3

- **元引用**: `Bitner, M. J., Ostrom, A. L., & Morgan, F. N. (2008). Service Blueprinting: A Practical Technique for Service Innovation. California Management Review, 66-94. https://doi.org/10.2307/41166446`
- **構造化結果**: Service Blueprinting: A Practical Technique for Service Innovation / California Management Review / 2008 / DOI=10.2307/41166446
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 43 < 90

#### Ref #9

- **元引用**: `Hill, R., Betts, L. R., & Gardner, S. E. (2015). Older adults’ experiences and perceptions of digital technology: (Dis)empowerment, wellbeing, and inclusion. Computers in Human Behavior, 415-423. https://doi.org/10.1016/j.chb.2015.01.062`
- **構造化結果**: Older adults' experiences and perceptions of digital technology: (Dis)empowerment, wellbeing, and inclusion / Computers in Human Behavior / 2015 / DOI=10.1016/j.chb.2015.01.062
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #10

- **元引用**: `Holland, J. M., Neimeyer, R. A., Boelen, P. A., & Prigerson, H. G. (2009). The Underlying Structure of Grief: A Taxometric Investigation of Prolonged and Normal Reactions to Loss. Journal of Psychopathology and Behavioral Assessment, 190-201. https://doi.org/10.1007/s10862-008-9113-1`
- **構造化結果**: The Underlying Structure of Grief: A Taxometric Investigation of Prolonged and Normal Reactions to Loss / Journal of Psychopathology and Behavioral Assessment / 2009 / DOI=10.1007/s10862-008-9113-1
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #11

- **元引用**: `Iversen, T. N., Larsen, L., & Solem, P. E. (2009). A conceptual analysis of Ageism. Nordic Psychology, 4-22. https://doi.org/10.1027/1901-2276.61.3.4`
- **構造化結果**: A conceptual analysis of Ageism / Nordic Psychology / 2009 / DOI=10.1027/1901-2276.61.3.4
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 39 < 90

#### Ref #25

- **元引用**: `Bloch, S., & Antaki, C. (2022). How professionals deal with clients’ explicit objections to their advice. Discourse Studies, 24(4), 385-403. https://doi.org/10.1177/14614456221110669`
- **構造化結果**: How professionals deal with clients' explicit objections to their advice / Discourse Studies / 2022 / DOI=10.1177/14614456221110669
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #26

- **元引用**: `Bolden, G. B. (2009). Implementing incipient actions: The discourse marker ‘so’ in English conversation. Journal of Pragmatics, 41(5), 974-998. https://doi.org/10.1016/j.pragma.2008.10.004`
- **構造化結果**: Implementing incipient actions: The discourse marker 'so' in English conversation / Journal of Pragmatics / 2009 / DOI=10.1016/j.pragma.2008.10.004
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #28

- **元引用**: `Department of Health and Social Care (2020). Tackling Obesity: Empowering Adults and Children to Live Healthy Lives.`
- **構造化結果**: Tackling Obesity: Empowering Adults and Children to Live Healthy Lives / Department of Health and Social Care / 2020 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #29

- **元引用**: `Ekberg, K., & LeCouteur, A. (2015). Clients’ resistance to therapists’ proposals: Managing epistemic and deontic status. Journal of Pragmatics, 90, 12-25. https://doi.org/10.1016/j.pragma.2015.10.004`
- **構造化結果**: Clients' resistance to therapists' proposals: Managing epistemic and deontic status / Journal of Pragmatics / 2015 / DOI=10.1016/j.pragma.2015.10.004
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #30

- **元引用**: `Glenn, P. (2003). Laughter in interaction.`
- **構造化結果**: Laughter in interaction / Cambridge University Press / 2003 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #31

- **元引用**: `Abdullah, K., Noor, N. M., & Wok, S. (2008). The perceptions of women’s roles and progress: a study of Malay women. Soc. Indic. Res., 89, 439-455. https://doi.org/10.1007/s11205-008-9242-7`
- **構造化結果**: The perceptions of women's roles and progress: a study of Malay women / Soc. Indic. Res. / 2008 / DOI=10.1007/s11205-008-9242-7
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #32

- **元引用**: `Ackert, M., Maglakelidze, E., Badurashvili, I., & Huber, S. (2020a). Validation of the short forms of the centrality of religiosity scale in Georgia. Religions, 11, 1-22. https://doi.org/10.3390/rel11020057`
- **構造化結果**: Validation of the short forms of the centrality of religiosity scale in Georgia / Religions / 2020 / DOI=10.3390/rel11020057
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #33

- **元引用**: `Ackert, M., & Plopeanu, A.-P. (2021). Short forms of the centrality of religiosity scale: validation and application in the context of religious individualism of orthodox and Pentecostal Christians in Romania. Religions, 12, 1-29. https://doi.org/10.3390/rel12010009`
- **構造化結果**: Short forms of the centrality of religiosity scale: validation and application in the context of religious individualism of orthodox and Pentecostal Christians in Romania / Religions / 2021 / DOI=10.3390/rel12010009
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #34

- **元引用**: `Ackert, M., Prutskova, E., & Zabaev, I. (2020b). Validation of the short forms of centrality of religiosity scale in Russia. Religions, 11, 1-35. https://doi.org/10.3390/rel11110577`
- **構造化結果**: Validation of the short forms of centrality of religiosity scale in Russia / Religions / 2020 / DOI=10.3390/rel11110577
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #35

- **元引用**: `Aday, R. H. (1985). Belief in afterlife and death anxiety: correlates and comparisons. OMEGA J. Death Dying, 15, 67-75. https://doi.org/10.2190/GYPP-VBG3-M3AY-1ML9`
- **構造化結果**: Belief in afterlife and death anxiety: correlates and comparisons / OMEGA Journal of Death and Dying / 1985 / DOI=10.2190/GYPP-VBG3-M3AY-1ML9
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #37

- **元引用**: `Agency for Integrated Care (2023).`
- **構造化結果**: - / Agency for Integrated Care / 2023 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #40

- **元引用**: `Batson, C. D., Schoenrade, P., Ventis, W. L., & Batson, C. D. (1993). Religion and the individual: A social-psychological perspective.`
- **構造化結果**: Religion and the individual: A social-psychological perspective / - / 1993 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #41

- **元引用**: `Beck, R., & Jessup, R. K. (2004). The multidimensional nature of quest motivation. J. Psychol. Theol., 32, 283-294. https://doi.org/10.1177/009164710403200401`
- **構造化結果**: The multidimensional nature of quest motivation / J. Psychol. Theol. / 2004 / DOI=10.1177/009164710403200401
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 34 < 90

#### Ref #42

- **元引用**: `Bengtson, V. L., Silverstein, M., Putney, N. M., & Harris, S. C. (2015). Does religiousness increase with age? Age changes and generational differences over 35 years. J. Sci. Study Relig., 54, 363-379. https://doi.org/10.1111/jssr.12183`
- **構造化結果**: Does religiousness increase with age? Age changes and generational differences over 35 years / Journal for the Scientific Study of Religion / 2015 / DOI=10.1111/jssr.12183
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 47 < 90

#### Ref #43

- **元引用**: `Bruce, S. (2011). Defining religion: a practical response. Int. Rev. Sociol., 21, 107-120. https://doi.org/10.1080/03906701.2011.544190`
- **構造化結果**: Defining religion: a practical response / Int. Rev. Sociol. / 2011 / DOI=10.1080/03906701.2011.544190
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 39 < 90

#### Ref #44

- **元引用**: `Bryukhanov, M., & Fedotenkov, I. (2023). Gender differences in religiosity: a report on Russian data. J. Gend. Stud., 32, 107-123. https://doi.org/10.1080/09589236.2021.1962702`
- **構造化結果**: Gender differences in religiosity: a report on Russian data / J. Gend. Stud. / 2023 / DOI=10.1080/09589236.2021.1962702
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

---

## 3. 構造化品質 (parsing_confidence < high)

以下の参照は LLM 構造化時に不確実性が検出されました。必要に応じて目視確認を推奨します。

| # | 確度 | タイトル | 備考 |
|--:|:----:|---------|------|
| 1 | medium | Multi-stakeholder perspectives on information communication… | Volume and issue not provided in the raw citation. Journal name inferred as 'Di… |
| 2 | medium | Grieving in the digital era: Mapping online support for gri… | Volume and issue not provided in the raw citation; pages extracted directly. DO… |
| 3 | medium | Service Blueprinting: A Practical Technique for Service Inn… | Volume and issue not provided in the raw citation; only page range available. |
| 6 | medium | Evaluation of a guided internet-based self-help interventio… | Volume number is absent from the raw citation; only page range provided. DOI ap… |
| 9 | medium | Older adults' experiences and perceptions of digital techno… | Volume number not present in the raw citation string; only page range provided.… |
| 10 | medium | The Underlying Structure of Grief: A Taxometric Investigati… | Volume and issue not provided in the raw citation. Pages extracted directly. DO… |
| 13 | medium | User profiles and personas in the design and development of… | Volume and issue not provided in the citation. Pages given as e251-e268 (electr… |
| 14 | medium | Prevalence of prolonged grief disorder in adult bereavement… | Volume number is missing from the raw citation; only page range provided. DOI i… |
| 28 | low | Tackling Obesity: Empowering Adults and Children to Live He… | This is a government policy document/report, not a journal article. Author is a… |
| 30 | low | Laughter in interaction | This appears to be a book (monograph) with no journal, volume, or DOI informati… |
| 37 | low |  | Incomplete reference — only the organization name (Agency for Integrated Care) … |
| 40 | low | Religion and the individual: A social-psychological perspec… | This is a book reference with no publisher information present. The duplicate '… |

---

## 4. 透明性トレース

### 4.1 解決経路の内訳

| 経路 | 件数 | 意味 |
|------|----:|------|
| `doi` | 24 | DOI検索成功 |
| `unresolved` | 20 | 全カスケード失敗 |
| `title_author_year` | 1 | タイトル+第一著者+年で検索 |

### 4.2 PDF由来の行番号混入検出

- 行番号混入なし

### 4.3 全参照のスナップショット

| # | PMID | 経路 | ジャーナル | 年 |
|--:|------|:----:|----------|---:|
| 1 | 30044659 | doi | Disabil Rehabil Assist T… | 2019 |
| 2 | 32591255 | doi | Patient Educ Couns | 2020 |
| 3 | — | unresolved | California Management Re… | 2008 |
| 4 | 35462943 | doi | Internet Interv | 2022 |
| 5 | 35522459 | doi | JMIR Ment Health | 2022 |
| 6 | 31003114 | doi | J Affect Disord | 2019 |
| 7 | 34225745 | doi | BMC Health Serv Res | 2021 |
| 8 | 31628789 | doi | JMIR Ment Health | 2019 |
| 9 | — | unresolved | Computers in Human Behav… | 2015 |
| 10 | — | unresolved | Journal of Psychopatholo… | 2009 |
| 11 | — | unresolved | Nordic Psychology | 2009 |
| 12 | 32022693 | doi | J Med Internet Res | 2020 |
| 13 | 21481635 | doi | Int J Med Inform | 2013 |
| 14 | 28167398 | doi | J Affect Disord | 2017 |
| 15 | 29459357 | doi | J Med Internet Res | 2018 |
| 16 | 31376830 | doi | BMC Fam Pract | 2019 |
| 17 | 34489149 | doi | Patient Educ Couns | 2022 |
| 18 | 33340401 | doi | Fam Pract | 2021 |
| 19 | 31793217 | doi | Clin Obes | 2020 |
| 20 | 27789061 | doi | Lancet | 2016 |
| 21 | 27420294 | doi | Health Commun | 2017 |
| 22 | 32371269 | doi | Soc Sci Med | 2020 |
| 23 | 23737640 | doi | J Health Soc Behav | 2013 |
| 24 | 31030008 | doi | Soc Sci Med | 2019 |
| 25 | — | unresolved | Discourse Studies | 2022 |
| 26 | — | unresolved | Journal of Pragmatics | 2009 |
| 27 | 34052990 | doi | Eat Weight Disord | 2022 |
| 28 | — | unresolved | Department of Health and… | 2020 |
| 29 | — | unresolved | Journal of Pragmatics | 2015 |
| 30 | — | unresolved | Cambridge University Pre… | 2003 |
| 31 | — | unresolved | Soc. Indic. Res. | 2008 |
| 32 | — | unresolved | Religions | 2020 |
| 33 | — | unresolved | Religions | 2021 |
| 34 | — | unresolved | Religions | 2020 |
| 35 | — | unresolved | OMEGA Journal of Death a… | 1985 |
| 36 | 33576129 | doi | Psychogeriatrics | 2021 |
| 37 | — | unresolved | Agency for Integrated Ca… | 2023 |
| 38 | 6051769 | title_author_year | J Pers Soc Psychol | 1967 |
| 39 | 26831313 | doi | Singapore Med J | 2016 |
| 40 | — | unresolved | — | 1993 |
| 41 | — | unresolved | J. Psychol. Theol. | 2004 |
| 42 | — | unresolved | Journal for the Scientif… | 2015 |
| 43 | — | unresolved | Int. Rev. Sociol. | 2011 |
| 44 | — | unresolved | J. Gend. Stud. | 2023 |
| 45 | 20097885 | doi | Pers Soc Psychol Rev | 2010 |

---

## 免責事項

本レポートは PubMed メタデータとの機械的突合による **候補抽出** です。
**最終的な査読判断は必ず人間の査読者が行ってください。**
タイトル fuzzy match が低い場合、必ずしも誤引用とは限らず (例: 原典が多言語、タイトル翻訳等)、
コンテキストを踏まえた判断が必要です。

---

## 補遺: ジャーナル名と PubMed 収載誌の照合監査 (追加)

解決済み 25 件全件について citation journal と PubMed journal_iso の類似度を計算した結果、
類似度 50% 未満のケースは検出されませんでした。
全 25 件が略称表記の差異を含めて 80% 以上の一致を示し、ジャーナル名記載に
系統的な誤りは認められませんでした。

詳細データ: `journal_mismatch_audit.json` (同ディレクトリ内)
