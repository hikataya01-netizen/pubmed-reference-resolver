# pubmed-reference-resolver 監査レポート

**入力**: `tests/fixtures/cell_45refs/input_References.docx`  |  **実行**: 2026-05-24 11:33:23

---

## ダッシュボード

| 指標 | 件数 | 状態 |
|------|----:|:----:|
| 総参照数 | 45 | — |
| 解決 (PMID取得) | 30 | OK |
| **未解決 (要確認)** | **15** | ATTN |
| **重複引用** | **0** | OK |
| 査読コメント: 重大 | 0 | OK |
| 査読コメント: 要検討 | 2 | WARN |
| 査読コメント: 軽微 | 3 | — |

> **査読者が確認すべき項目: 計 17 件** (重大 0 / 要検討 2 / 未解決 15)

---

## 1. 要確認項目 (優先度順)

### 1.1 [MAJOR] 重大な不整合

_(該当なし)_

### 1.2 [MODERATE] 要検討

文脈に応じて査読コメントを検討してください。

- Ref #15 タイトル一致度 85% (PMID: 10228155)。
  - 引用: "An F-box protein, FWD1, mediates ubiquitin-dependent proteolysis of β-catenin..."
  - PubMed: "An F-box protein, FWD1, mediates ubiquitin-dependent proteolysis of beta-catenin..."
- Ref #29 タイトル一致度 87% (PMID: 30684552)。
  - 引用: "Elevated Local Senescence in Diabetic Wound Healing Is Linked to Pathological Re..."
  - PubMed: "Elevated Local Senescence in Diabetic Wound Healing Is Linked to Pathological Re..."

### 1.3 [MINOR] 軽微な差異

通常は人間査読で無視して問題ありません（参考情報）。

- Ref #14 タイトルに微小な表記差 (一致度 90%、PMID: 15021890)
- Ref #18 タイトルに微小な表記差 (一致度 99%、PMID: 18264518)
- Ref #19 タイトルに微小な表記差 (一致度 98%、PMID: 16722862)

---

## 2. 未解決参照の詳細

**計 15 件** が PubMed で解決できませんでした。理由の多くは MEDLINE 非収録誌または書籍です。

### 一覧

| # | タイトル | ジャーナル | 年 | DOI | 言語 | 推定理由 |
|--:|---------|----------|---:|-----|:---:|---------|
| 16 | Impaired wound healing after radiation therapy: A systemati… | JPRAS Open | 2017 | `10.1016/J.JPRA.2017.04.001` | en | DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性 |
| 17 |  |  | 1997 | `-` | en | 構造化不十分（確認要） |
| 31 | Cotton Sector Development in Ethiopia: Challenges and Oppor… |  | 2024 | `-` | en | 書籍 (PubMed対象外) |
| 32 | Sustainable fibres for fashion and textile manufacturing |  | 2023 | `-` | en | 書籍 (PubMed対象外) |
| 33 | Economic, societal, and environmental impacts of available … | Eng | 2024 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 34 |  | International Conference on T… | 2023 | `-` | en | 構造化不十分（確認要） |
| 36 | Gio-nigeria economic relations on the development of the ni… | J. Int. Coop. Dev. | 2024 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 37 | Knitting Food: Food and Eco-textiles: New Perspectives for … |  | 2024 | `-` | en | 書籍 (PubMed対象外) |
| 38 | Development of a standardized data collection and intellige… | Journal of Engineered Fibers … | 2025 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 40 | A survey on using deep learning techniques for plant diseas… | Smart Agricultural Technology | 2023 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 41 | A smart manufacturing process for textile industry automati… | Processes | 2024 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 42 |  | International Conference on A… | 2022 | `-` | en | 構造化不十分（確認要） |
| 43 |  | 2022 12th International Confe… | 2022 | `-` | en | 構造化不十分（確認要） |
| 44 | Classification of diseased cotton leaves and plants using i… | Multimed. Tools Appl. | 2023 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |
| 45 | Meta deep learn leaf disease identification model for cotto… | Computers | 2022 | `-` | en | DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性 |

### [3 分類化] PubMed 未ヒットの分類

(Day13 INVESTIGATION で発見、Day15 で実装. 詳細は `references/USAGE_QUICKSTART.md` §V Q4 参照)

| ref | 分類 | 理由 |
|:---:|:---:|:---|
| #16 | unknown | Crossref network error (graceful unknown): network failed (after 1 retry) |
| #17 | A | DOI 欠落 + journal 不明 (真の判定不可、LLM ハルシネーション候補) |
| #31 | B | book chapter (DOI 欠落だが MEDLINE 対象外) |
| #32 | B | book chapter (DOI 欠落だが MEDLINE 対象外) |
| #33 | B | DOI 欠落だが journal 'Eng' は MEDLINE 非収録 (NLM 直接検索) |
| #34 | B | conference/proceedings 'International Conference on Trends in Electronics and Health Informatics' (… |
| #36 | unknown | DOI 欠落 + NLM 検索でも判定不可: esearch returned no NLM ID |
| #37 | B | book chapter (DOI 欠落だが MEDLINE 対象外) |
| #38 | B | DOI 欠落だが journal 'Journal of Engineered Fibers and Fabrics' は MEDLINE 非収録 (NLM 直接検索) |
| #40 | B | DOI 欠落だが journal 'Smart Agricultural Technology' は MEDLINE 非収録 (NLM 直接検索) |
| #41 | B | DOI 欠落だが journal 'Processes' は MEDLINE 非収録 (NLM 直接検索) |
| #42 | B | conference/proceedings 'International Conference on Advancements in Smart Computing and Information… |
| #43 | B | conference/proceedings '2022 12th International Conference on Electrical and Computer Engineering (… |
| #44 | B | DOI 欠落だが journal 'Multimed. Tools Appl.' は MEDLINE 非収録 (NLM 直接検索) |
| #45 | B | DOI 欠落だが journal 'Computers' は MEDLINE 非収録 (NLM 直接検索) |

**集計**: A (真の捏造) 1 件 / B (MEDLINE 非収録誌) 12 件 / C (収録誌 indexing 漏れ) 0 件 / unknown (判定不可) 2 件

### 参照ごとの試行詳細

#### Ref #16

- **元引用**: `Jacobson, L.K., Johnson, M.B., Dedhia, R.D., Niknam-Bienia, S., and Wong, A.K. (2017). Impaired wound healing after radiation therapy: A systematic review of pathogenesis and treatment. JPRAS Open 13, 92-105. https://doi.org/10.1016/J.JPRA.2017.04.001`
- **構造化結果**: Impaired wound healing after radiation therapy: A systematic review of pathogenesis and treatment / JPRAS Open / 2017 / DOI=10.1016/J.JPRA.2017.04.001
- **試行経路**:
  - `[doi]` NG — no hits
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 61 < 90

#### Ref #17

- **元引用**: `Hassey Dow, K., Bucholtz, J.D., Iwamoto, R.R., Fieler, V., and Hilderley, L.J. (1997).`
- **構造化結果**: - / - / 1997 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #31

- **元引用**: `Kabish, A.K., Degefu, D.T., Gebregiorgis, Z.D., Babu, K.M., Kabish, A.K., Tesema, G.B., and Semahagn, B.K. (2024). Cotton Sector Development in Ethiopia: Challenges and Opportunities, 441-463.`
- **構造化結果**: Cotton Sector Development in Ethiopia: Challenges and Opportunities / - / 2024 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #32

- **元引用**: `Goyal, A., Parashar, M., and Nayak, R. (2023). Sustainable fibres for fashion and textile manufacturing, 51-74.`
- **構造化結果**: Sustainable fibres for fashion and textile manufacturing / - / 2023 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #33

- **元引用**: `Al Mubarak, F., Rezaee, R., and Wood, D.A. (2024). Economic, societal, and environmental impacts of available energy sources: a review. Eng 5, 1232-1265.`
- **構造化結果**: Economic, societal, and environmental impacts of available energy sources: a review / Eng / 2024 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 49 < 90

#### Ref #34

- **元引用**: `Bappi, M.B.R., Swapno, S.M.R., and Rabbi, M.F. (2023). International Conference on Trends in Electronics and Health Informatics, 485-498.`
- **構造化結果**: - / International Conference on Trends in Electronics and Health Informatics / 2023 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #36

- **元引用**: `Owa, O.E., Chukwudi, C.E., Okongor, J.N., and Ezebuilo, P.C. (2024). Gio-nigeria economic relations on the development of the nigerian textile sector, 2006–2017. J. Int. Coop. Dev. 7, 79-116.`
- **構造化結果**: Gio-nigeria economic relations on the development of the nigerian textile sector, 2006–2017 / J. Int. Coop. Dev. / 2024 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #37

- **元引用**: `Gausa, M., and Tucci, G. (2024). Knitting Food: Food and Eco-textiles: New Perspectives for Sustainable Urban Production Systems, 259-270.`
- **構造化結果**: Knitting Food: Food and Eco-textiles: New Perspectives for Sustainable Urban Production Systems / - / 2024 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #38

- **元引用**: `Dai, N., Li, L., Xu, K., Lu, Z., Hu, X., and Yuan, Y. (2025). Development of a standardized data collection and intelligent fabric quality prediction system for the weaving department. J. Eng. Fiber. Fabr. 20.`
- **構造化結果**: Development of a standardized data collection and intelligent fabric quality prediction system for the weaving department / Journal of Engineered Fibers and Fabrics / 2025 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #40

- **元引用**: `Ahmad, A., Saraswat, D., and El Gamal, A. (2023). A survey on using deep learning techniques for plant disease diagnosis and recommendations for development of appropriate tools. Smart Agric. Technol. 3.`
- **構造化結果**: A survey on using deep learning techniques for plant disease diagnosis and recommendations for development of appropriate tools / Smart Agricultural Technology / 2023 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 48 < 90

#### Ref #41

- **元引用**: `Kaur, G., Dey, B.K., Pandey, P., Majumder, A., and Gupta, S. (2024). A smart manufacturing process for textile industry automation under uncertainties. Processes 12, 778.`
- **構造化結果**: A smart manufacturing process for textile industry automation under uncertainties / Processes / 2024 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

#### Ref #42

- **元引用**: `Kukadiya, H., and Meva, D. (2022). International Conference on Advancements in Smart Computing and Information Security, 247-266.`
- **構造化結果**: - / International Conference on Advancements in Smart Computing and Information Security / 2022 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #43

- **元引用**: `Peyal, H.I., Pramanik, M.A.H., Nahiduzzaman, M., Goswami, P., Mahapatra, U., and Atusi, J.J. (2022). 2022 12th International Conference on Electrical and Computer Engineering (ICECE), 413-416.`
- **構造化結果**: - / 2022 12th International Conference on Electrical and Computer Engineering (ICECE) / 2022 / DOI=-
- **試行経路**: (スキップ — 書籍またはメタデータ不足)

#### Ref #44

- **元引用**: `Rai, C.K., and Pahuja, R. (2023). Classification of diseased cotton leaves and plants using improved deep convolutional neural network. Multimed. Tools Appl. 82, 25307-25325.`
- **構造化結果**: Classification of diseased cotton leaves and plants using improved deep convolutional neural network / Multimed. Tools Appl. / 2023 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — fuzzy 42 < 90

#### Ref #45

- **元引用**: `Memon, M.S., Kumar, P., and Iqbal, R. (2022). Meta deep learn leaf disease identification model for cotton crop. Computers 11, 102.`
- **構造化結果**: Meta deep learn leaf disease identification model for cotton crop / Computers / 2022 / DOI=-
- **試行経路**:
  - `[title_author_year]` NG — no hits
  - `[title_fuzzy]` NG — no hits

---

## 3. 構造化品質 (parsing_confidence < high)

以下の参照は LLM 構造化時に不確実性が検出されました。必要に応じて目視確認を推奨します。

| # | 確度 | タイトル | 備考 |
|--:|:----:|---------|------|
| 17 | low |  | Raw citation appears to be truncated — only author names and year are present. … |
| 18 | medium | Wound healing in patients with cancer | No page numbers, issue, or DOI provided. Volume 8 inferred from the number foll… |
| 31 | low | Cotton Sector Development in Ethiopia: Challenges and Oppor… | No journal or publisher information present. Pages 441-463 suggest a book chapt… |
| 32 | low | Sustainable fibres for fashion and textile manufacturing | Appears to be a book chapter (pages 51-74) with no journal, publisher, or ISBN … |
| 33 | medium | Economic, societal, and environmental impacts of available … | No DOI present. Journal abbreviated as 'Eng', likely MDPI journal 'Eng' (ISSN 2… |
| 34 | low |  | Title is missing from the raw citation; only conference name and page range are… |
| 36 | medium | Gio-nigeria economic relations on the development of the ni… | No DOI present. Title contains 'Gio-nigeria' — the hyphen may be a line-break a… |
| 37 | low | Knitting Food: Food and Eco-textiles: New Perspectives for … | Appears to be a book chapter (pages 259-270) but no publisher, editor, or book … |
| 38 | medium | Development of a standardized data collection and intellige… | No DOI or page numbers provided. Volume 20 noted. Journal abbreviated as 'J. En… |
| 40 | medium | A survey on using deep learning techniques for plant diseas… | No DOI or page numbers provided in the raw citation. Volume 3 extracted. Journa… |
| 41 | medium | A smart manufacturing process for textile industry automati… | No DOI provided in the raw citation. Page field appears to be an article number… |
| 42 | low |  | Title is missing from the raw citation; only authors, conference name, year, an… |
| 43 | low |  | No article title found in the raw citation; the publication appears to be confe… |
| 44 | medium | Classification of diseased cotton leaves and plants using i… | No DOI present in the raw citation. All other major fields cleanly extracted. |
| 45 | medium | Meta deep learn leaf disease identification model for cotto… | No DOI present in raw citation. Page number '102' likely an article number rath… |

---

## 4. 透明性トレース

### 4.1 解決経路の内訳

| 経路 | 件数 | 意味 |
|------|----:|------|
| `doi` | 29 | DOI検索成功 |
| `unresolved` | 15 | 全カスケード失敗 |
| `title_author_year` | 1 | タイトル+第一著者+年で検索 |

### 4.2 PDF由来の行番号混入検出

- 行番号混入なし

### 4.3 全参照のスナップショット

| # | PMID | 経路 | ジャーナル | 年 |
|--:|------|:----:|----------|---:|
| 1 | 11683914 | doi | Genes Cells | 2001 |
| 2 | 14585973 | doi | Mol Cell Biol | 2003 |
| 3 | 25937177 | doi | Free Radic Biol Med | 2015 |
| 4 | 21245377 | doi | Mol Cell Biol | 2011 |
| 5 | 31362447 | doi | Cancers (Basel) | 2019 |
| 6 | 30125702 | doi | Fish Shellfish Immunol | 2018 |
| 7 | 16944320 | doi | Neurochem Res | 2007 |
| 8 | 26551701 | doi | Biochem Soc Trans | 2015 |
| 9 | 28159764 | doi | J Biol Chem | 2017 |
| 10 | 31406304 | doi | Cell Death Differ | 2020 |
| 11 | 10648623 | doi | Mol Cell Biol | 2000 |
| 12 | 12820959 | doi | Mol Cell | 2003 |
| 13 | 9461217 | doi | Nature | 1998 |
| 14 | 15021890 | doi | Oncogene | 2004 |
| 15 | 10228155 | doi | EMBO J | 1999 |
| 16 | — | unresolved | JPRAS Open | 2017 |
| 17 | — | unresolved | — | 1997 |
| 18 | 18264518 | title_author_year | Eplasty | 2008 |
| 19 | 16722862 | doi | Int Wound J | 2005 |
| 20 | 31513068 | doi | Ann Plast Surg | 2019 |
| 21 | 39061166 | doi | Cancers (Basel) | 2024 |
| 22 | 33513872 | doi | Cancers (Basel) | 2021 |
| 23 | 32752135 | doi | Cancers (Basel) | 2020 |
| 24 | 25499914 | doi | Dev Cell | 2014 |
| 25 | 20526329 | doi | Nat Cell Biol | 2010 |
| 26 | 29872395 | doi | Front Pharmacol | 2018 |
| 27 | 32482536 | doi | Trends Cancer | 2020 |
| 28 | 32117790 | doi | Front Oncol | 2019 |
| 29 | 30684552 | doi | J Invest Dermatol | 2019 |
| 30 | 27979832 | doi | Cancer Discov | 2017 |
| 31 | — | unresolved | — | 2024 |
| 32 | — | unresolved | — | 2023 |
| 33 | — | unresolved | Eng | 2024 |
| 34 | — | unresolved | International Conference… | 2023 |
| 35 | 37764510 | doi | Molecules | 2023 |
| 36 | — | unresolved | J. Int. Coop. Dev. | 2024 |
| 37 | — | unresolved | — | 2024 |
| 38 | — | unresolved | Journal of Engineered Fi… | 2025 |
| 39 | 39841622 | doi | Mol Plant Pathol | 2025 |
| 40 | — | unresolved | Smart Agricultural Techn… | 2023 |
| 41 | — | unresolved | Processes | 2024 |
| 42 | — | unresolved | International Conference… | 2022 |
| 43 | — | unresolved | 2022 12th International … | 2022 |
| 44 | — | unresolved | Multimed. Tools Appl. | 2023 |
| 45 | — | unresolved | Computers | 2022 |

---

## 免責事項

本レポートは PubMed メタデータとの機械的突合による **候補抽出** です。
**最終的な査読判断は必ず人間の査読者が行ってください。**
タイトル fuzzy match が低い場合、必ずしも誤引用とは限らず (例: 原典が多言語、タイトル翻訳等)、
コンテキストを踏まえた判断が必要です。

---

## 補遺: ジャーナル名と PubMed 収載誌の照合監査 (追加)

解決済み 30 件全件について citation journal と PubMed journal_iso の類似度を計算した結果、
類似度 50% 未満のケースは検出されませんでした。
全 30 件が略称表記の差異を含めて 80% 以上の一致を示し、ジャーナル名記載に
系統的な誤りは認められませんでした。

詳細データ: `journal_mismatch_audit.json` (同ディレクトリ内)
