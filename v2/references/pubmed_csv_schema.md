# references_pubmed.csv 出力スキーマ仕様 (v2, 29列)

> **旧版注記**: 本ファイルは以前、廃止済みの `main.py` 時代の 13 列スキーマ
> (`Ref_No, Duplicate_of, PMID, Title, Authors, Citation, First Author, Journal/Book,
> Publication Year, Create Date, PMCID, NIHMS ID, DOI`) を記載していたが、
> 現行の `audit.py` + `pipeline/outputs.py` パイプラインとは一致していなかった。
> 本改訂 (2026-08-22) で `pipeline/outputs.py::CSV_COLUMNS` の実装に完全準拠させた。

## カラム定義 (29列、`pipeline/outputs.py::CSV_COLUMNS` が単一の情報源)

### ①〜㉑ 基本 21 列 (実在性・書誌情報・重複・照合経路)

| # | カラム名 | 由来 | 説明 |
|---|---------|-----|------|
| 1 | `Ref_No` | refs.json | 参照番号 |
| 2 | `Match_Status` | Stage4 | `RESOLVED` / `UNRESOLVED` / `NON_PUBMED` |
| 3 | `PMID` | PubMed | 解決された PMID |
| 4 | `PMCID` | PubMed | PMC番号 |
| 5 | `Title` | PubMed | `ArticleTitle` |
| 6 | `Authors` | PubMed | `"Bray F; Laversanne M; ..."` (セミコロン区切り) |
| 7 | `First_Author` | PubMed | 筆頭著者 |
| 8 | `Journal` | PubMed | `ISOAbbreviation` 優先 |
| 9 | `Year` | PubMed | 発行年 |
| 10 | `Volume` | PubMed | 巻 |
| 11 | `Issue` | PubMed | 号 |
| 12 | `Pages` | PubMed | ページ |
| 13 | `DOI` | PubMed | canonical DOI |
| 14 | `Publication_Types` | PubMed | `PublicationTypeList` をセミコロン結合 |
| 15 | `Claimed_PMID` | refs.json | 引用元記載の PMID |
| 16 | `Claimed_DOI` | refs.json | 引用元記載の DOI |
| 17 | `Claimed_Year` | refs.json | 引用元記載の年 |
| 18 | `Claimed_First_Author` | refs.json | 引用元記載の筆頭著者 |
| 19 | `Claimed_Journal` | refs.json | 引用元記載の雑誌名 |
| 20 | `Claimed_Title` | refs.json | 引用元記載のタイトル |
| 21 | `Resolution_Path` | Stage4 | `L1`/`L2`/`L3a`〜`L3d`/`NON_PUBMED`/`UNRESOLVED` |

### ㉒〜㉙ 文献評価 8 列 (v2 新規、`pipeline/assess.py` が算出)

`Match_Status = UNRESOLVED` または `NON_PUBMED` の行はこの 8 列すべて空文字列になる
(評価は RESOLVED 参照のみに対して実施する)。

| # | カラム名 | 説明 | 値の例 |
|---|---------|------|--------|
| 22 | `Retraction_Status` | 撤回・懸念表明の状態 | `CLEAN` / `RETRACTED` / `PARTIAL_RETRACTION` / `EXPRESSION_OF_CONCERN` / `CORRECTED` |
| 23 | `Retraction_Notice` | 撤回・懸念表明の通知詳細 (CommentsCorrectionsList 由来) | `RetractionIn: Lancet. 2010...(PMID 20137807)` |
| 24 | `Recency` | 最新性 (発行年からの経過年数による分類) | `最新`(≤5年) / `妥当`(≤10年) / `古い`(>10年) / `判定不能` |
| 25 | `Originality` | 原著性 (PublicationType ベースの決定論的分類) | `原著` / `レビュー` / `メタ解析/SR` / `ガイドライン` / `症例報告` / `レター/社説/コメント` |
| 26 | `Evidence_Level` | エビデンス水準 (同上分類から導出、IF 等の商用指標は不使用) | `1 (メタ解析/SR)` / `2 (RCT)` / `3 (観察研究)` / `4 (症例報告)` |
| 27 | `Indexing_Status` | 収載状況 (NLM Catalog + DOAJ 照会結果) | `MEDLINE` / `DOAJ` / `PubMed収録(要確認)` / `未確認` / `未評価`(`--offline`時) |
| 28 | `Predatory_Risk` | Predatory Journal リスク (複合シグナルによる参考フラグ、断定ではない) | `低` / `要確認` / `未評価` |
| 29 | `Claim_Support` | 主張支持性 (呼び出し側 LLM の読解判定、`--claim-support` 未実施時は常に `NOT_ASSESSED`) | `SUPPORTS` / `PARTIAL` / `DOES_NOT_SUPPORT` / `NOT_ASSESSED` |

## ファイル形式仕様

- **文字コード**: UTF-8 **BOM付き** (`utf-8-sig`)
- **改行コード**: LF
- **引用符**: `csv.DictWriter` 既定 (フィールドにカンマ・引用符・改行を含む場合のみ自動クォート。全セル強制クォートではない)
- **ファイル名**: `references_pubmed.csv` (固定、`OUT_CSV` で一元管理)

## サンプル (基本 21 列のみ抜粋、実際は 29 列)

```csv
Ref_No,Match_Status,PMID,...,Resolution_Path,Retraction_Status,...,Predatory_Risk,Claim_Support
1,RESOLVED,38572751,...,L1,CLEAN,...,低,NOT_ASSESSED
3,RESOLVED,9500320,...,L1,RETRACTED,...,低,NOT_ASSESSED
4,UNRESOLVED,,...,UNRESOLVED,,...,,
```

行3 (Wakefield 1998, PMID 9500320) は `Retraction_Status=RETRACTED` となる実例。
行4 は未解決のため文献評価 8 列すべて空。

## 拡張時の注意

新しい列を追加する場合は `pipeline/outputs.py::CSV_COLUMNS` に列名を追記し、
`write_csv()` の `w.writerow({...})` に対応する key/value を追加するだけでよい。
列の並び順は既存部分を変更しないこと (下流の列位置依存を避けるため、末尾に追加する)。
