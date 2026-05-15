# DAY13_LESSONS_LEARNED.md

**Day13 = Day9 (Z) 残存未解決 2 件の MEDLINE 非収録調査 (データ駆動知識生成セッション)**

**作成日**: 2026/05/13
**作成者**: Claude Code (Sonnet 4.6)
**配置**: `docs/sessions/day13/DAY13_LESSONS_LEARNED.md`
**対応 commit 範囲**: 本書 archive commit (計 1 commit、code 改修なし)
**対応する指示書**: なし (Day12 §7 候補 2 を user 選択)

---

## 0. 本書の位置づけ

Day13 は Day7 §9.3 long-term task の 1 件「Day9 (Z) 残存未解決 2 件 (#17 Davey, #22 Gallina) の MEDLINE 非収録調査」を完了した. Day12 で中期タスク 100% 達成後、最初の長期タスクとして user が選択 (Day12 §7 候補 2).

特徴: **production code 改修なし、test 追加なし、ただし重要な設計知見を生成**. 「データ駆動の調査セッション」型の Day10 (D10-2 数値出典明示) を発展させたもの. 主成果物は `INVESTIGATION_unresolved_2refs.md` (本書とは別 file).

本書は以下を記録する:

1. Day13 のフェーズ構成 (調査のみ、1 archive commit)
2. 調査経路と発見の本質 (詳細は INVESTIGATION_unresolved_2refs.md を参照)
3. Day13 で抽出された教訓 3 件 (D13-1, D13-2, D13-3)
4. main branch 最終形状と Day14 への引継ぎ

---

## 1. Day13 のフェーズ構成

| フェーズ | 内容 | 成果物 |
|:---:|:---|:---|
| 1 | Day9 (Z) baseline_phase3_resolved.json から #17/#22 の詳細抽出 | (作業ログのみ) |
| 2 | Crossref API で DOI 実在性確認 (#17 / #22 共に ok) | (作業ログ) |
| 3 | PubMed E-utilities で論文 indexing 確認 (両 ref 共に count=0) | (作業ログ) |
| 4 | NLM Catalog で journal 収録状況確認 (#17 = Y, #22 = N) | (作業ログ) |
| 5 | 「PubMed 未ヒット 3 分類」の体系化 (真捏造 / MEDLINE 非収録誌 / 収録誌 indexing 漏れ) | INVESTIGATION_unresolved_2refs.md §3 |
| 6 | Day13 archive (本書 + INVESTIGATION + README) | 本 commit |

---

## 2. 調査経路と発見の本質

### 2.1 検証手段

3 つの public API を組合せ (全て API key 不要):

| API | role | endpoint |
|:---|:---|:---|
| **Crossref** | DOI 実在性確認 | `https://api.crossref.org/works/{doi}` |
| **PubMed E-utilities** | 論文 indexing 確認 | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=...` |
| **NLM Catalog** | journal 収録状況 | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=nlmcatalog&term=...` (esummary で `currentindexingstatus` 取得) |

詳細手順は INVESTIGATION_unresolved_2refs.md §4.2 に curl コマンドで例示済.

### 2.2 主要発見

**Ref #17 Davey 2003**:
- DOI 10.1037/1091-7527.21.3.245 = Crossref で実在確認
- journal "Families, Systems, & Health" (略称 Fam Syst Health)
- NLM Catalog: ID 9610836, **currentindexingstatus = Y** (MEDLINE 収録済)
- ただし 2003 年時点の PubMed indexing は 1 件のみ (本格化は 2010 頃)
- → **論文は実在、journal は収録済、ただし historical indexing 漏れ**

**Ref #22 Gallina 2016**:
- DOI 10.4172/2090-7214.1000217 = Crossref で実在確認
- publisher: **OMICS Publishing Group** (Beall's List で predatory 指定)
- journal "Clinics in Mother and Child Health"
- NLM Catalog: ID 101300689, **currentindexingstatus = N** (MEDLINE 非収録)
- → **論文は実在、ただし predatory journal で MEDLINE 品質基準を満たさない**

### 2.3 体系化: 「PubMed 未ヒット」の 3 分類

Day7-9 で skill 設計時に「PubMed 未ヒット = 捏造の可能性」と単純化していたが、Day13 調査で **3 分類**が必要と判明:

| 分類 | 判定基準 | 例 | 警告 level |
|:---|:---|:---:|:---:|
| **A. 真の捏造** | DOI 実在せず、Crossref hit なし | (未確認) | **重大** |
| **B. MEDLINE 非収録誌の正規論文** | DOI 実在 + journal currentindexingstatus=N | **#22 Gallina (OMICS)** | **軽微** (predatory 注意) |
| **C. MEDLINE 収録誌の indexing 漏れ論文** | DOI 実在 + journal currentindexingstatus=Y + 論文 unindexed | **#17 Davey** | **軽微** (人手確認推奨) |

詳細は INVESTIGATION_unresolved_2refs.md §3, §4 を参照.

---

## 3. Day13 で抽出された教訓 3 件

### 学び D13-1: 「PubMed 未ヒット = 捏造」は単純化、3 分類が必要

**本質**: Day7-9 で skill 設計時に採用した「MEDLINE 収録誌名乗り + PubMed 未ヒット + DOI 未解決 → 捏造可能性」の AND 3 条件は、**「DOI 未解決」が真の決め手**であって、「MEDLINE 収録誌名乗り + PubMed 未ヒット」だけでは判定不十分. journal の indexing status (Y/N) と論文単体の indexing 状況を区別する必要がある.

**応用先**:
- 文献検証ツール一般 (PubMed/MEDLINE を使う何でも) で「PubMed 未ヒット = 捏造」の単純化を避ける
- audit logic に Crossref + NLM Catalog による補助検証を組み込む (Day14 以降の skill 改修候補 A)
- 査読指南で「PubMed で見つからない」報告に対し、「他 DB (PsycInfo, Scopus 等) でも検索したか?」「journal が MEDLINE 収録か?」を確認する慣行

**Day1-12 既存学びとの関係**:
Day10 D10-2 (数値の出典明示) の判定 logic 版. 「PubMed 未ヒット」は単一指標、「未ヒット + 補助検証 (Crossref/NLM)」は出典明示版. 設計仮説の精緻化を実データで駆動する pattern (Day9 (Z) で実証 → Day13 で分類化).

### 学び D13-2: code 改修なしの「知識生成型セッション」も valuable

**本質**: Day13 は production code 改修ゼロ、test 追加ゼロ. しかし `INVESTIGATION_unresolved_2refs.md` (本書とは別) という **独立した知見ドキュメント**を生成した. 本知見は Day14 以降の skill 改修 (audit logic 多段分類) のための基礎データとなる.

**応用先**:
- session を「code commit 数」だけで評価せず、「知識資産の蓄積」も指標に
- archive 連鎖 (Day6-13 で 8 連続) には、code 改修型と知識生成型が混在することを許容
- INVESTIGATION_*.md 形式は他プロジェクトでも応用可能 (実証調査結果の独立 file 化)

**Day1-12 既存学びとの関係**:
Day10 (USAGE_QUICKSTART update + cleanup の軽量セッション) の知識集約版. Day10 は既存知識の docs 化、Day13 は **新規知識の生成 + docs 化**.

### 学び D13-3: API key 不要の public API 組合せで深い検証が可能

**本質**: 本調査は Crossref + PubMed E-utilities + NLM Catalog の **3 つの public API** を組合せて実施. いずれも認証不要 (NCBI key も任意)、低 rate (3 req/sec で十分). curl + jq だけで再現可能で、**研究者が自分の引用を検証する hands-on tutorial としても価値がある**.

**応用先**:
- INVESTIGATION_unresolved_2refs.md §4.2 の curl コマンド例は他プロジェクト/利用者にも転用可能
- 「外部 API 検証は API key + 高 rate が必要」という思い込みを排し、まず public API で出来る範囲を確認する慣行
- 査読プロセスのデジタル化指南で「Crossref で DOI 検証、NLM Catalog で journal 状況」を標準手順に

**Day1-12 既存学びとの関係**:
Day12 SETUP_API_KEYS.md §2 (NCBI API key の効果) の補完. NCBI key は rate limit 緩和に有用だが、low-rate な調査タスク (本 Day13 のような ad-hoc verification) では key なしでも十分.

---

## 4. main branch の最終形状 (Day13 完了時)

### 4.1 commit history (Day13 範囲)

```
(本 commit)  docs(sessions): archive day13 MEDLINE non-indexing investigation
ad5f3f7      docs(sessions): archive day12 SETUP_API_KEYS session                  ← Day12 末
... (Day1-Day12 commits omitted)
```

### 4.2 統計

| 指標 | 値 |
|:---|:---:|
| main commit count (Day13 完了時、本 commit 含む) | **43** (Day12 末 42 → +1) |
| test 健全性 | **71 passed, 1 skipped** (Day12 末から不変、code 改修なし) |
| 改修ファイル | (なし、production code 触れず) |
| 新規 docs | `docs/sessions/day13/INVESTIGATION_unresolved_2refs.md` (主成果物) |
| 新規 archive | `docs/sessions/day13/` (3 ファイル: INVESTIGATION + LESSONS + README) |
| identity | 全 commit `Hideki Katayama <hikataya01@gmail.com>` |

### 4.3 Day13 の本質的な達成

1. **Day9 §4.4 「MEDLINE 非収録の可能性」推定の実証完了**
2. **「PubMed 未ヒット 3 分類」の体系化** (Day7-9 設計仮説の refinement)
3. **API key 不要の検証手順の文書化** (INVESTIGATION §4.2、curl 再現コマンド)
4. **archive 連鎖 8 連続達成** (Day6-13)

---

## 5. 残存タスク (Day14 以降)

Day7 §9 の最終更新版 (Day13 反映、+ Day13 自身が生成した改修候補):

### 5.1 Day7 §9.3 long-term (Day11 で 1 件、Day13 で 1 件完了)

- [x] Vancouver golden fixture (Day11)
- [x] **Day9 (Z) 未解決 2 件の MEDLINE 非収録調査 (Day13)**
- [ ] APA / Cell 系 golden fixture
- [ ] MCP/hook 経由 Claude UI 起動配線 (Stage 3)
- [ ] GitHub remote 追加と push

### 5.2 Day13 が生成した新規候補 (skill 改修)

INVESTIGATION_unresolved_2refs.md §6 より:

- [ ] **A. audit_report に「PubMed 未ヒット 3 分類」logic 追加** (NLM Catalog + Crossref API call、新モジュール、test 追加) — 大規模、別 SPEC + brainstorming セッション必要
- [ ] **B. USAGE_QUICKSTART §V Q4 (捏造判定) を 3 分類で書き換え** — 中規模 docs 更新
- [ ] **C. SKILL.md description の「捏造引用検出」表記を 3 分類で精緻化** — 小規模 docs 更新

最小工数で最大効果は **B + C** (docs only). 1 セッション で完結可能.

---

## 6. 次セッション再開時のプロンプトテンプレート

### パターン 1: skill 改修 B + C (docs のみ更新、最小工数)

```
Day14 として、Day13 INVESTIGATION で発見した「PubMed 未ヒット 3 分類」
を skill docs に反映します. 以下の 2 ファイルを更新してください:

1. skill_package/references/USAGE_QUICKSTART.md §V Q4 (捏造判定):
   3 分類 (真捏造 / MEDLINE 非収録誌 / 収録誌 indexing 漏れ) で書き換え.
2. skill_package/SKILL.md description: 「捏造引用検出」表記を
   「捏造 / non-MEDLINE / indexing 漏れの 3 分類検出」に精緻化.

参照: docs/sessions/day13/INVESTIGATION_unresolved_2refs.md §3-§6.
```

### パターン 2: skill 改修 A (audit_report 多段分類、大規模)

```
Day14 として、audit_report に「PubMed 未ヒット 3 分類」logic を実装します.
docs/sessions/day13/INVESTIGATION_unresolved_2refs.md §3.4 の擬似コードを
起点に、brainstorming → SPEC → TDD で進めてください. 新モジュール
(crossref_check.py, nlm_catalog_check.py 等) の追加と既存 audit logic への
統合が必要.
```

### パターン 3: 別の long-term task (APA fixture / GitHub push / Stage 3)

Day12 §7 のテンプレートをそのまま再利用可能.

---

**記録完了日**: 2026/05/13 (Day13)
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day13 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day13.md` (Claude Opus 作成予定)
**ステータス**: Day13 archive 完成、Day14 着手準備完了 (3 候補プロンプトあり)
