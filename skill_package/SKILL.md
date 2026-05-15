---
name: pubmed-reference-resolver
description: 査読対象論文のReferencesセクション(PDF/DOCX/TXT)から各文献をPubMedで逆引き検索し、PubMed純正互換CSV + 番号付きabstract text + 統合監査レポート(ダッシュボード+要確認項目+未解決参照詳細を1ファイルに統合)の3ファイルを自動生成する査読支援スキル。**MDPI形式の参照は決定論的fast-pathで処理し、LLM呼び出し費用ゼロで解決する**(Vancouver/AMA/APA/Harvard/Chicago/Nature/Cell/MDPI等の引用スタイルに不問で対応、MDPI以外はLLM経由)。PDFコピペ由来の行番号問題(行頭・行末・行中・数字連結・散在の5パターン)を統計的に検出・除去する。PubMed未ヒット文献は空行として保持、重複引用は複合キー(PMID/DOI/title+author+year)で検出、引用年誤記・タイトル改変・DOI-雑誌名不整合を重大/要検討/軽微の3段階に自動分類。**ジャーナル名類似度監査**により、引用ジャーナル名とPubMed側ジャーナル名の不一致をMAJOR/WARN/INFOの3段階severityで自動分類し、4層統合レポート(Dashboard/MAJOR詳細セクション/補遺narrative/sidecar JSON)として出力。**AI/LLMによる捏造引用の検出にも有効**(PubMed未ヒット文献を「真の捏造(DOI実在せず)/MEDLINE非収録誌の正規論文(predatory含む)/MEDLINE収録誌のindexing漏れ論文」の3分類で扱い、Crossref+NLM Catalog補助検証でfalse positiveを抑制可能。詳細はreferences/USAGE_QUICKSTART.md §V Q4参照)。手動補正機能(manual_overrides.yaml)により、特殊ケース(書籍検出、出版社情報保持、smart quote処理等)を明示的に補正可能。想定参照数30件中心、100件超のレビュー論文にも対応(149件MDPIゴールドスタンダードでbyte単位fixture一致を検証済み)。和文文献・医中誌Web等は非対象(英語論文専用)。既存の `paper-search` スキル(新着pull型検索)とは明確に差別化される**push型の逆引き検証ツール**。以下のようなリクエストで必ず本スキルを使用すること:「この論文の参照文献をPubMedで逆引きして」「Referencesセクションを検証して」「査読対象論文の引用文献をチェック」「論文のReferences全件を一覧化して」「参照文献のPMIDを取得」「引用文献の抄録を全部まとめて」「査読用にabstract集を作成」「Referencesの重複引用を検出して」「引用年誤記をチェックして」「DOIから PubMed 情報を取得」「参照文献のPubMed CSV を作って」「捏造引用かチェックして」「AIが作った論文の引用が怪しいか調べて」「ジャーナル名とDOIの整合性をチェック」「MDPIの参照を検証して」。参照文献、References、逆引き、PMID取得、査読支援、引用文献チェック、重複引用検出、引用正確性、abstract text、PubMed CSV、捏造引用検出、ハルシネーション検証、ジャーナル名監査、MDPI fast-path等のキーワードが含まれる場合は積極的に本スキルを使用する。
---

# pubmed-reference-resolver

論文の参照文献リストを PubMed で逆引きし、**査読実務に直結する3ファイル**(統合監査レポート / PubMed CSV / abstract text)を生成するスキル。

## 使用目的

査読対象となる他者の論文に対し、References セクションから各文献を自動的に PubMed で検索・照合し、引用の正確性を機械的にチェックする。LLM 捏造引用 (ハルシネーション) の検証にも有効。

## 統合計画完了 (2026/04/23)

本スキルは 4 日間にわたる 7 ステップ統合計画 (Day1-Day4) を経て、以下の機能を実装済み:

- **Step 1**: Phase 1 split_references の境界バグ修正 (Dutch/French 小文字 lookahead 許容)
- **Step 2**: MDPI 形式 fast-path パーサ (LLM 費用ゼロで決定論的解決)
- **Step 3**: structure_all_references への fast-path 統合
- **Step 4**: manual_overrides.yaml サポート (特殊ケースの手動補正)
- **Step 5**: journal_audit モジュール (3 段階 severity 分類)
- **Step 6**: Stage 5 報告書への 4 層統合 (Dashboard/MAJOR/narrative/sidecar)
- **Step 7**: CI 基盤と再現可能環境 (requirements, GitHub Actions, README)

149 件 MDPI ゴールドスタンダードで byte 単位 fixture 一致を検証済み。

## 対応入力

- **ファイル形式**: PDF / DOCX / TXT (PDFが主用途)
- **引用スタイル**: Vancouver / AMA / APA / Harvard / Chicago / Nature / Cell / MDPI など不問
- **言語**: 英語論文のみ (和文文献は非対象)
- **件数**: 30件中心、100件超のレビュー論文にも対応 (149件で fixture 一致検証済)
- **PDF由来の行番号混入**: 行頭・行末・行中・数字連結・散在の5パターン全てに対応

## 出力3ファイル (4層統合設計)

| ファイル | 内容 |
|---------|------|
| `csv-{first_pmid}-set.csv` | PubMed純正互換CSV + `Ref_No`, `Duplicate_of` 列 (UTF-8 BOM) |
| `abstract-{first_pmid}-set.txt` | PubMed標準 abstract text 形式、番号付き、未ヒットは1行保持 |
| `report.md` | **統合監査レポート** (4 層構成): |
| | **層 1. Dashboard** — 解決/未解決/重複/重大・要検討・軽微の件数を一覧 |
| | **層 2. 要確認項目 (MAJOR/MODERATE/MINOR)** — 1.1 [MAJOR] にジャーナル名 vs DOI 不整合を含む |
| | **層 3. 構造化品質と未解決詳細** — `parsing_confidence=low/medium` 一覧と未解決理由 |
| | **層 4. 補遺: ジャーナル名監査** — 全件類似度評価、50% 未満の具体的 ref_no を列挙 |
| (補助) `journal_mismatch_audit.json` | sidecar JSON (機械可読、115 件全件の生データ) |

## 実行方法

### クイックスタート (エンド・ツー・エンド)

```bash
# Anthropic API Key と NCBI API Key を環境変数に設定
export ANTHROPIC_API_KEY='sk-ant-...'    # MDPI 以外で必要 (lazy import)
export NCBI_API_KEY='...'                 # optional, あれば10 req/sec

# Phase 4 (全工程) を実行
python3 main.py path/to/references.pdf -o ./out --phase 4
```

### MDPI 形式の参照 (推奨)

```bash
# 手動補正を含む実行 (MDPI 149 件等の特殊ケース対応)
python3 main.py path/to/references.docx --overrides path/to/manual_overrides.yaml
```

MDPI 形式の参照は fast-path により決定論的に解決されるため、ANTHROPIC_API_KEY なしでも動作可能 (`anthropic` SDK は lazy import、MDPI 以外でのみロードされる)。

### 段階実行 (デバッグ用)

```bash
# Phase 1: 抽出 + 前処理 + 行番号統計検出 (LLM/PubMed不使用)
python3 main.py input.pdf --phase 1

# Phase 2: + Stage 3 構造化 (MDPI fast-path 優先、それ以外は Claude Sonnet 4.6)
python3 main.py input.pdf --phase 2

# Phase 3: + Stage 4 PubMedカスケード検索
python3 main.py input.pdf --phase 3

# Phase 4: + Stage 5 出力合成 (デフォルト、journal_audit 統合済)
python3 main.py input.pdf --phase 4

# 既存結果を再利用して部分再実行
python3 main.py input.pdf --phase 4 --reuse-phase2  # 構造化スキップ
python3 main.py input.pdf --phase 4 --reuse-phase3  # PubMed検索スキップ
```

## 処理パイプライン (5段階 + fast-path)

```
Stage 1: 抽出 (pypdf / python-docx / txt)
         ↓
Stage 2.5: 行番号統計検出 (LIS ≥ 10、3桁、年号範囲外)
         ↓
Stage 2: 前処理
         ① ハイフン橋渡し救済: "gpsych- 570 2022" → "gpsych-2022"
         ② 独立行番号除去: "GLOBOCAN 567 estimates" → "GLOBOCAN estimates"
         ③ 粗い参照境界検出 (^\d+\.\s+[A-Z])
         ↓
Stage 3: 構造化 [MDPI fast-path 優先 + LLM フォールバック]
         ┌─ MDPI 形式判定 → mdpi_parser で決定論的解決 (LLM 費用ゼロ)
         └─ それ以外    → Claude Sonnet 4.6 + プロンプトキャッシュ
         (manual_overrides.yaml の補正を適用)
         → authors, title, journal, year, volume, pages, doi, doi_alt, pmid,
           is_book, language, parsing_confidence, notes
         ↓
Stage 4: PubMedカスケード検索
         Level 1: PMID直接 (efetch)
         Level 2: DOI検索 (doi → doi_alt)
         Level 3: Title + First Author + Year
         Level 4: Title単独 fuzzy (rapidfuzz token_sort_ratio ≥ 90)
         ↓
Stage 5: 出力合成 (CSV / abstract / report / sidecar JSON)
         + 重複検出 (複合キー: PMID || DOI || norm_title+first_author+year)
         + 査読コメント候補生成
         + journal_audit (引用ジャーナル名 vs PubMed 名の類似度監査)
           - MAJOR (類似度 < 50%): 1.1 セクションに自動追記
           - WARN  (50-79%): 補遺セクションで集計
           - INFO  (80-99%): 補遺セクションで集計
           - OK    (100%): sidecar JSON のみ
```

## 査読コメント候補の自動検出項目

- **重複引用**: 同一論文の複数引用 (複合キー判定)
- **引用年誤記**: 著者引用年 ≠ PubMed発表年 (epub/print年混同の発見に有効)
- **タイトル軽微差異**: fuzzy一致 90-99% (句読点・大文字化差異)
- **タイトル重大差異**: fuzzy一致 < 90% (要人間確認)
- **雑誌名-DOI不整合 (MAJOR)**: journal_audit による類似度 50% 未満の自動検出
- **ソフトハイフン破損の復元**: `RELA-TIONSHIP` → `RELATIONSHIP` 等
- **DOI曖昧性の両形式保持**: `j.jpsy-chores` と `j.jpsychores` の両方を試行
- **AI/LLM 捏造引用候補 (3 分類化、Day14 で精緻化)**: PubMed 未ヒット文献は以下の 3 分類で扱う (詳細: `references/USAGE_QUICKSTART.md` §V Q4 + `docs/sessions/day13/INVESTIGATION_unresolved_2refs.md`):
  - **A. 真の捏造**: DOI 実在せず (Crossref hit なし) — **重大**
  - **B. MEDLINE 非収録誌の正規論文**: DOI 実在 + journal `currentindexingstatus = N` (predatory journal 含む) — **軽微 (predatory 注意)**
  - **C. MEDLINE 収録誌の indexing 漏れ論文**: DOI 実在 + journal `currentindexingstatus = Y` + 該当論文単体 unindexed — **軽微 (人手確認推奨)**

## 手動補正機能 (manual_overrides.yaml)

既知のパーサ限界事例を明示的に補正するための YAML 形式の override ファイル。サンプル構成:

```yaml
overrides:
  - ref_no: 66    # journal boundary issue
    journal: "..."
  - ref_no: 137   # publisher city retention
    publisher_location: "..."
  - ref_no: 141   # book detection without ISBN
    is_book: true
    publisher: "..."
  - ref_no: 148   # title/journal split with smart quote U+2019
    title: "..."
    journal: "..."
```

149 件 MDPI ゴールドスタンダードでは 4 件の既知限界が override で解決される。

## 依存ライブラリ

- `python-docx` (DOCX抽出)
- `rapidfuzz` (タイトルfuzzy match、journal_audit 類似度計算)
- `pyyaml` (manual_overrides.yaml ロード)
- `pypdf` (PDF抽出、PDF入力時のみ)
- `requests` (NCBI E-utilities API)
- `tenacity` (5xx/429 指数バックオフリトライ)
- `anthropic` (Claude SDK、**lazy import**: MDPI 以外でのみロード)

## 設計原則

1. **疑わしきは保持**: 行番号除去・重複判定は保守的に (誤削除・誤統合は致命的)
2. **監査可能性**: 全判断 (行番号除去、検索経路、重複判定、journal_audit) を `report.md` / `journal_mismatch_audit.json` / `phase*_*.json` にログ化
3. **人間が最終判断**: `parsing_confidence=low/medium` のものは目視確認を明示的に促す
4. **単一責務**: 「参照→CSV+abstract+監査レポート変換」に徹する (査読レポート本体生成や翻訳は他スキルに委ねる)
5. **既存 API の無改修維持**: journal_audit のような新機能は opt-in パラメタで追加し、既存テストを温存
6. **fixture を仕様書として吟味**: ゴールドスタンダードを正とするが、手書きサンプル要素が混入する場合は批判的吟味を行う

## 非対応

- 和文文献 (医中誌Web、J-STAGE 等)
- CrossRef / Semantic Scholar 等の他データベース
- 他スキルからのサブルーチン呼出 (本スキルは単体ツールとして完結)
- キャッシュ機構 (1論文1回の査読用途では不要)

## 既存スキルとの関係

- **`paper-search`** (pull型、新着検索): 緩和ケア/がん就労/QOL/疫学の最新論文を PubMed から能動的に探す。本スキルとは **入力と方向が逆** (本スキルは既存引用リストを逆引き検証)。機能衝突なし。
- **`peer-reviewer` / `first-peer-review`**: 査読レポート本体を生成。本スキルは **査読のための引用検証材料** を提供し、前段として連携可。
- **`paper-summarizer`** (開発中): 検索結果や個別論文の要約。本スキルは reference 全件処理に特化、要約は提供しない。

## 開発履歴と方法論的資産

開発経緯と意思決定の詳細は `DEVELOPMENT_NOTES.md` を参照。本スキルは:

- Phase 0-4 (初期実装、2026/04/14-04/19 頃): MVP からゴールドスタンダード基盤確立まで
- Day1-Day4 (統合計画、2026/04/20-04/23): MDPI fast-path 統合と CI 基盤整備

の 2 段階で開発された。Day1-Day4 で確立された方法論 (事前協議プロセス、stop-and-report、調査フェーズ独立化、原則 tension の hybrid 解、三者協働モデル) は他スキル開発にも応用可能。
