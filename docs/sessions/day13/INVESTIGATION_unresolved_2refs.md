# INVESTIGATION_unresolved_2refs.md

**Day9 (Z) 残存未解決 2 件 (Ref #17 Davey 2003, #22 Gallina 2016) の MEDLINE 非収録調査レポート**

**作成日**: 2026/05/13 (Day13)
**作成者**: Claude Code (Sonnet 4.6)
**配置**: `docs/sessions/day13/INVESTIGATION_unresolved_2refs.md`
**起点**: `docs/sessions/day9/DAY9_LESSONS_LEARNED.md` §4.4 (「MEDLINE 非収録の可能性」と推定、本書で実証)
**前提**: Day9 (Z) `tests/fixtures/vancouver_24refs/baseline_phase3_resolved.json` の Ref #17 / #22 データ

---

## 0. 本書の位置づけ

Day9 (Z) production verification で OneDrive `参照.docx` 24 件中 22/24 = 91.7% を PubMed で解決. 残った未解決 2 件 (Ref #17 Davey, #22 Gallina) について、Day9 §4.4 で「MEDLINE 非収録の可能性」と推定したが、**実証は将来タスク** として残されていた.

本書は Day13 で実施した実証調査の結果を記録する. 主な検証経路:

1. **Crossref API** (`api.crossref.org/works/{doi}`) で DOI 実在性確認
2. **PubMed E-utilities** (`eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`) で論文 indexing 確認
3. **NLM Catalog** (同 API、`db=nlmcatalog`) で journal の MEDLINE 収録状況確認

調査により、**両論文とも実在する正規論文**で、PubMed 未ヒットの真因は **journal 側の MEDLINE indexing 状況**にあると判明. 結果として Day7 §8.8 学び 7.7 や USAGE_QUICKSTART で言及された「捏造可能性」judgement に **3 分類化の必要性** (本書 §4) が新たに浮上した.

---

## 1. Ref #17 Davey 2003 の調査

### 1.1 引用情報

```
Davey, M. P., Askew, J., Godette, K. (2003)
Parent and adolescent responses to non-terminal parental cancer:
A retrospective multiple-case pilot study.
Families, Systems, & Health, 21(3), 245–258.
doi: 10.1037/1091-7527.21.3.245
```

(原 raw_text の DOI は `10.103771091-7527.21.3.245` と malformed、Day9 LLM 構造化で `10.1037/1091-7527.21.3.245` に正規化)

### 1.2 検証結果

| 検証項目 | 結果 | 解釈 |
|:---|:---:|:---|
| Crossref DOI 解決 | ✓ ok | DOI 実在、論文 metadata (author/title/journal) も完全一致 |
| PubMed DOI search | **count=0** | この DOI で PubMed には存在しない |
| PubMed title search | **count=0** | この title で PubMed には存在しない |
| NLM Catalog (ISSN 1091-7527) | count=1, ID 9610836 | journal は NLM 登録済 |
| **journal currentindexingstatus** | **`Y`** | **MEDLINE 収録誌** |
| 略称 (medlineta) | `Fam Syst Health` | — |
| journal startyear | 1996 | NLM 登録は 1996 から |
| Fam Syst Health 2003 年 PubMed indexing | **1 件** (PMID 17203136、Davey 論文ではない) | 2003 年は indexing がほぼ未実施 |
| 同 2010 年 indexing | 29 件 | 2010 年頃から本格 indexing |
| Davey M[Author] AND parental cancer | 3 件 (全て 2010 年代) | Davey 2003 自体は PubMed に存在せず |

### 1.3 結論

- **論文は実在する** (DOI 解決可、Crossref で著者/タイトル/誌名一致)
- journal は **MEDLINE 収録誌** (currentindexingstatus=Y)
- ただし **2003 年時点では PubMed indexing がほぼ未実施** (年間 0-1 件、本格化は 2010 頃)
- Davey 2003 論文が PubMed で hit しないのは **journal の selective/historical indexing 開始時期の問題**
- → **捏造ではない**、ただし PubMed 経由では検索不能

### 1.4 査読者向け含意

Davey 2003 論文を引用している原稿を査読する場合、以下を確認推奨:

1. DOI を doi.org で実際に開いて landing page を確認
2. 著者名 (Davey, Askew, Godette) と発表年が APA の Families, Systems, & Health 2003 vol 21(3) と一致するか確認
3. APA PsycInfo 等の他 DB での検証 (PubMed 単独では検索不能)

---

## 2. Ref #22 Gallina 2016 の調査

### 2.1 引用情報

```
Gallina, F., Mazza, U., Tagliabue, L., Sala, F., Ripamonti, C., Jankovic, M.
(2016)
How to explain the parents cancer to their children: a specific intervention
to enhance communication inside the family.
Clinics Mother Child Health, 13:1
doi: 10.4172/2090-7214.1000217
```

### 2.2 検証結果

| 検証項目 | 結果 | 解釈 |
|:---|:---:|:---|
| Crossref DOI 解決 | ✓ ok | DOI 実在、論文 metadata も一致 |
| Crossref publisher | **`OMICS Publishing Group`** | ⚠️ predatory publisher として広く知られる |
| PubMed DOI search | **count=0** | PubMed に存在しない |
| PubMed title search | **count=0** | PubMed に存在しない |
| NLM Catalog (journal name) | count=1, ID 101300689 | journal は NLM 登録あり |
| **journal currentindexingstatus** | **`N`** | **MEDLINE 非収録** |
| 略称 (medlineta) | `Clin Mother Child Health` | — |
| ISSN | 1812-5840 (Print), 2090-7214 (Electronic) | — |
| journal startyear | 2004 | 2004〜現在 (ongoing) |

### 2.3 結論

- **論文は実在する** (DOI 解決可、Crossref で確認)
- publisher は **OMICS Publishing Group** = Beall's List (2016 版含む) 等で predatory publisher 指定されている著名な business
- journal "Clinics in Mother and Child Health" は **MEDLINE 非収録** (currentindexingstatus=N)
- → **捏造ではない**が、MEDLINE 品質基準を満たさない predatory journal

### 2.4 査読者向け含意

Gallina 2016 論文を引用している原稿を査読する場合、以下を確認推奨:

1. predatory publisher (OMICS) の論文であることを認識
2. 引用根拠としての信頼性は低い (peer review の質、editorial board の独立性に疑問)
3. 代替の同テーマ MEDLINE 収録論文での補強引用を著者に推奨

---

## 3. 統合分析: PubMed 未ヒット = 捏造、ではない

### 3.1 Day7-9 skill 設計の仮説

Day7 §8.8 学び 7.7 + USAGE_QUICKSTART §III §V Q4 で:

> AI/LLMによる捏造引用の検出にも有効 (MEDLINE収録誌を名乗りながら PubMed未ヒット + DOI未解決の組合せを "捏造DOIの可能性" として可視化)

→ 「**MEDLINE 収録誌名乗り + PubMed 未ヒット + DOI 未解決**」の AND 3 条件で「捏造疑い」と判定する設計.

### 3.2 Day13 調査が示す refinement

Day13 で #17 / #22 を実証調査した結果、「PubMed 未ヒット」状態は実は **3 つの異なる原因**を持つことが判明:

| 分類 | 判定基準 | 例 | 警告レベル | 査読推奨アクション |
|:---|:---|:---:|:---:|:---|
| **A. 真の捏造** (LLM ハルシネーション) | DOI 実在せず (Crossref hit なし) + title も google で見つからない | 未確認 (Day9-13 では発生せず) | **重大** | 著者に削除/差し替え要求 |
| **B. MEDLINE 非収録誌の正規論文** | DOI 実在 (Crossref hit) + journal currentindexingstatus=N | **#22 Gallina (OMICS)** | **軽微** (predatory 注意) | 引用根拠の信頼性確認、代替論文推奨 |
| **C. MEDLINE 収録誌の indexing 漏れ論文** | DOI 実在 + journal currentindexingstatus=Y + 該当論文単体 unindexed | **#17 Davey (Fam Syst Health 2003)** | **軽微** (人手確認推奨) | DOI で landing page 確認、他 DB (PsycInfo 等) で検証 |

### 3.3 現状 skill の含意

現状の audit ロジックでは、A/B/C の区別が実装されていない. すべて「PubMed 未ヒット」として未解決扱い (severity 区別なし). この設計には以下の含意:

- **false positive リスク**: C 分類 (収録誌の indexing 漏れ、#17 のようなケース) を **「捏造疑い」として誤分類する可能性**
- **false negative リスク**: A 分類 (真の捏造) を B/C と同じ severity で扱うことで重要性が薄まる
- 現状はあくまで **「未解決として human-in-the-loop で確認推奨」**の安全側設計だが、severity 区別があると査読効率が向上

### 3.4 改善方向 (Day14 以降の skill 改修候補)

audit_report ロジックに以下を追加:

```python
def classify_unresolved(ref):
    if not ref.get('doi'):
        return 'A_likely_fabrication'  # DOI なし → 捏造可能性
    crossref_status = check_crossref(ref['doi'])  # Day13 で確認した API
    if not crossref_status:
        return 'A_likely_fabrication'  # DOI 存在せず → 捏造
    nlm_status = check_nlm_catalog(ref['journal'])
    if nlm_status == 'N':
        return 'B_medline_unindexed_journal'  # predatory 等
    if nlm_status == 'Y':
        return 'C_medline_journal_paper_unindexed'  # 収録誌だが論文 unindexed
    return 'unknown'
```

ただし以下のトレードオフ:

- **時間コスト**: NLM Catalog + Crossref への追加 API call (1 件あたり 2 call、24 件で 48 call、~5 秒)
- **API key**: NCBI なしでも動くが rate limit リスク (NCBI 推奨)
- **設計工数**: audit_report の多段分類 + USAGE_QUICKSTART 更新

→ 改修すべきだが、Day13 単独では完結しない. Day14 以降の中-大規模タスクとして残存タスクに追加.

---

## 4. 検証手順 (再現可能性)

本調査を再現する場合の手順:

### 4.1 必要な前提

- インターネット接続 (api.crossref.org, eutils.ncbi.nlm.nih.gov 到達可能)
- Python 3 + curl
- API key 不要 (本調査は全て public API、低 rate)

### 4.2 検証コマンド (#17 Davey 2003 を例に)

```bash
# (A) Crossref で DOI 実在確認
curl -sf "https://api.crossref.org/works/10.1037/1091-7527.21.3.245" \
    -A "research verification" | jq '.message | {journal:."container-title"[0], title:.title[0], authors:[.author[].family]}'

# (B) PubMed で DOI 検索
curl -sf "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=10.1037%2F1091-7527.21.3.245%5Bdoi%5D&retmode=json" \
    | jq '.esearchresult.count'

# (C) PubMed で title 検索
curl -sf "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=%22Parent+and+adolescent+responses+to+non-terminal+parental+cancer%22%5BTitle%5D&retmode=json" \
    | jq '.esearchresult.count'

# (D) NLM Catalog で journal 収録状況
curl -sf "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nlmcatalog&term=1091-7527%5BISSN%5D&retmode=json" \
    | jq '.esearchresult.idlist'
# → ID 取得後 esummary で currentindexingstatus 確認
curl -sf "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=nlmcatalog&id=9610836&retmode=json" \
    | jq '.result."9610836" | {medlineta, currentindexingstatus}'

# (E) journal の年別 indexing 件数
for yr in 2002 2003 2010 2020; do
    count=$(curl -sf "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=%22Fam+Syst+Health%22%5BJournal%5D+AND+${yr}%5BPDAT%5D&retmode=json" | jq -r '.esearchresult.count')
    echo "$yr: $count"; sleep 0.4
done
```

#22 Gallina 2016 も同形で DOI を `10.4172/2090-7214.1000217`、journal を `Clin Mother Child Health` に変えて再現可能.

---

## 5. Day13 で確認できたこと

✅ Day9 (Z) 残存未解決 2 件は **両方とも実在論文** (DOI 解決可)
✅ #17 Davey: journal **MEDLINE 収録 (Y)**、ただし 2003 年時点 indexing 漏れ
✅ #22 Gallina: journal **MEDLINE 非収録 (N)**、OMICS predatory publisher
✅ Day9 (Z) cascade 失敗は **正しい挙動** (両者とも PubMed に存在しないため)
✅ 「**PubMed 未ヒット = 捏造**」という単純化は誤り、**3 分類** (真捏造 / MEDLINE 非収録誌 / 収録誌 indexing 漏れ) が必要

---

## 6. Day14 以降の skill 改修候補 (本調査の派生)

| 改修案 | 工数 | 効果 |
|:---|:---:|:---|
| **A. audit_report に 3 分類追加** (NLM Catalog + Crossref API call) | 大 (新モジュール、test 追加) | false positive 削減、severity の精緻化 |
| **B. USAGE_QUICKSTART §V Q4 (捏造判定) を 3 分類で書き換え** | 中 (docs 更新) | 利用者の判断ガイドライン明確化 |
| **C. SKILL.md description の「捏造引用検出」表記を「捏造 / non-MEDLINE / indexing 漏れの 3 分類検出」に精緻化** | 小 (docs 更新のみ) | 期待値設定の精緻化 |
| **D. 改修なし、本書を運用知識として残す** | 0 | 査読者 (人間) が判断時に本書を参照 |

最小工数で最大効果は **B + C** (docs のみ更新). A は実装大なので別 SPEC + brainstorming セッション必要.

---

## 7. 関連リソース

| リソース | 場所 | 役割 |
|:---|:---|:---|
| Day9 (Z) 残存未解決 2 件のデータソース | `tests/fixtures/vancouver_24refs/baseline_phase3_resolved.json` | 本調査の入力 |
| Day9 §4.4 「未解決 2 件の傾向」 | `docs/sessions/day9/DAY9_LESSONS_LEARNED.md` §4.4 | 「MEDLINE 非収録の可能性」と推定、本書で実証 |
| skill の現状捏造判定設計 | `skill_package/references/USAGE_QUICKSTART.md` §V Q4 | 「MEDLINE収録誌名乗り + PubMed 未ヒット + DOI 未解決」の AND 3 条件 |
| skill description | `skill_package/SKILL.md` | 「**AI/LLMによる捏造引用の検出にも有効**」記述 |
| Vancouver fixture | `tests/fixtures/vancouver_24refs/` | 本調査対象の Day9 (Z) データ凍結保管 (Day11 で fixture 化) |

---

**記録完了日**: 2026/05/13 (Day13)
**記録者**: Claude Code (Sonnet 4.6)
**ステータス**: 調査完結、Day14 以降の改修候補は §6 に記載
