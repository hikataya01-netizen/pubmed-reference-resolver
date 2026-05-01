# PubMed CSV 出力スキーマ仕様

PubMed Web エクスポート (CSV format) と互換のスキーマ + 本スキル固有の補助2列。

## カラム定義 (13列)

| # | カラム名 | 必須 | 由来 | 説明 |
|---|---------|:----:|-----|------|
| 1 | `Ref_No` | 必須 | 本スキル固有 | 参照番号 (References 内の番号と一致) |
| 2 | `Duplicate_of` | オプション | 本スキル固有 | 重複検出時、最初に出現した Ref_No。非重複なら空 |
| 3 | `PMID` | 必須*¹ | PubMed | 8桁の数値 |
| 4 | `Title` | PubMed | PubMed | `ArticleTitle` (末尾ピリオド含む) |
| 5 | `Authors` | PubMed | PubMed | `"Bray F, Laversanne M, Sung H"` 形式 (カンマ区切り、姓+イニシャル) |
| 6 | `Citation` | PubMed | PubMed | `"CA Cancer J Clin. 2024;74(3):229-263."` 形式 |
| 7 | `First Author` | PubMed | PubMed | 筆頭著者のみ `"Bray F"` 形式 |
| 8 | `Journal/Book` | PubMed | PubMed | 雑誌フルタイトル (`Journal/Title`) |
| 9 | `Publication Year` | PubMed | PubMed | 4桁年 |
| 10 | `Create Date` | PubMed | PubMed | `YYYY/MM/DD` 形式 (DateCompleted → DateRevised → DateCreated の順) |
| 11 | `PMCID` | オプション | PubMed | PMC番号 (例: `PMC9540834`) |
| 12 | `NIHMS ID` | オプション | PubMed | NIH Manuscript ID (該当時のみ) |
| 13 | `DOI` | オプション | PubMed | canonical DOI (URL prefix なし) |

*¹ 未ヒット文献は PMID 以降の全カラムが空文字列。行自体は削除せず、`Ref_No` と `Duplicate_of` のみ保持する。

## ファイル形式仕様

- **文字コード**: UTF-8 **BOM付き** (Excel で開いた際の文字化け防止)
- **改行コード**: LF
- **引用符**: **全セルを二重引用符で囲む** (`QUOTE_ALL`)
- **セル内引用符のエスケープ**: `""` (CSV 標準)
- **ファイル名**: `csv-{first_resolved_pmid}-set.csv` (最初に解決された PMID を使用)
  - 解決済みが0件の場合は `csv-nopmid-set.csv`

## サンプル

```csv
"Ref_No","Duplicate_of","PMID","Title","Authors","Citation","First Author","Journal/Book","Publication Year","Create Date","PMCID","NIHMS ID","DOI"
"1","","38572751","Global cancer statistics 2022: GLOBOCAN estimates of incidence and mortality worldwide for 36 cancers in 185 countries.","Bray F, Laversanne M, Sung H, Ferlay J, Siegel RL, Soerjomataram I, Jemal A","CA Cancer J Clin. 2024;74(3):229-263.","Bray F","CA: a cancer journal for clinicians","2024","2024/05/09","","","10.3322/caac.21834"
"2","","36311374","Cancer-related psychosocial challenges.","Wang Y, Feng W","Gen Psychiatr. 2022;35(5):e100871.","Wang Y","General psychiatry","2022","2024/09/05","PMC9540834","","10.1136/gpsych-2022-100871"
"3","","","","","","","","","","","",""
"4","1","38572751","Global cancer statistics 2022: GLOBOCAN estimates of incidence and mortality worldwide for 36 cancers in 185 countries.","Bray F, Laversanne M, Sung H, Ferlay J, Siegel RL, Soerjomataram I, Jemal A","CA Cancer J Clin. 2024;74(3):229-263.","Bray F","CA: a cancer journal for clinicians","2024","2024/05/09","","","10.3322/caac.21834"
```

- 行1: ヘッダー
- 行2: 通常の解決済み参照
- 行3: PMCID付き
- 行4: 未ヒット参照 (全カラム空)
- 行5: 重複 (`Duplicate_of=1`、以降は元と同じメタデータをコピー)

## PubMed 純正エクスポートとの差異

| 項目 | PubMed純正 | 本スキル |
|------|-----------|---------|
| `Ref_No` | ❌ なし | ✅ 追加 |
| `Duplicate_of` | ❌ なし | ✅ 追加 |
| PMID以降の列順 | PubMed準拠 | PubMed準拠 |
| BOM付き UTF-8 | ✅ | ✅ |
| 全セル引用符 | ✅ | ✅ |

参照との対応関係を保持するため、先頭2列のみ拡張。PubMed純正CSVを期待する下流ツールには Python等で先頭2列を削除することで完全互換化可能。
