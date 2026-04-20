---
name: pubmed-reference-resolver
description: 査読対象論文のReferencesセクション（PDF/DOCX/TXT）から各文献をPubMedで逆引き検索し、PubMed純正互換CSV + 番号付きabstract text + 統合監査レポート(ダッシュボード+要確認項目+未解決参照詳細を1ファイルに統合)の3ファイルを自動生成する査読支援スキル。Vancouver/AMA/APA/Harvard/Chicago/Nature/Cell/MDPI等の引用スタイルに不問で対応し、PDFコピペ由来の行番号問題（行頭・行末・行中・数字連結・散在の5パターン）を統計的に検出・除去する。PubMed未ヒット文献は空行として保持、重複引用は複合キー(PMID/DOI/title+author+year)で検出、引用年誤記・タイトル改変・DOI-雑誌名不整合を重大/要検討/軽微の3段階に自動分類。**AI/LLMによる捏造引用の検出にも有効**（MEDLINE収録誌を名乗りながらPubMed未ヒット＋DOI未解決の組合せを "捏造DOIの可能性" として可視化）。想定参照数30件中心、100件超のレビュー論文にも対応。和文文献・医中誌Web等は非対象（英語論文専用）。既存の `paper-search` スキル（新着pull型検索）とは明確に差別化される**push型の逆引き検証ツール**。以下のようなリクエストで必ず本スキルを使用すること：「この論文の参照文献をPubMedで逆引きして」「Referencesセクションを検証して」「査読対象論文の引用文献をチェック」「論文のReferences全件を一覧化して」「参照文献のPMIDを取得」「引用文献の抄録を全部まとめて」「査読用にabstract集を作成」「Referencesの重複引用を検出して」「引用年誤記をチェックして」「DOIから PubMed 情報を取得」「参照文献のPubMed CSV を作って」「捏造引用かチェックして」「AIが作った論文の引用が怪しいか調べて」。参照文献、References、逆引き、PMID取得、査読支援、引用文献チェック、重複引用検出、引用正確性、abstract text、PubMed CSV、捏造引用検出、ハルシネーション検証等のキーワードが含まれる場合は積極的に本スキルを使用する。
---

# pubmed-reference-resolver

論文の参照文献リストを PubMed で逆引きし、**査読実務に直結する4ファイル**を生成するスキル。

## 使用目的

査読対象となる他者の論文に対し、References セクションから各文献を自動的に PubMed で検索・照合し、引用の正確性を機械的にチェックする。

## 対応入力

- **ファイル形式**: PDF / DOCX / TXT (PDFが主用途)
- **引用スタイル**: Vancouver / AMA / APA / Harvard / Chicago / Nature / Cell / MDPI など不問
- **言語**: 英語論文のみ (和文文献は非対象)
- **件数**: 30件中心、100件超のレビュー論文にも対応
- **PDF由来の行番号混入**: 行頭・行末・行中・数字連結・散在の5パターン全てに対応

## 出力3ファイル (統合設計)

| ファイル | 内容 |
|---------|------|
| `csv-{first_pmid}-set.csv` | PubMed純正互換CSV + `Ref_No`, `Duplicate_of` 列 (UTF-8 BOM) |
| `abstract-{first_pmid}-set.txt` | PubMed標準 abstract text 形式、番号付き、未ヒットは1行保持 |
| `report.md` | **統合監査レポート** (以下を1ファイルに集約): |
| | 1. **ダッシュボード** — 解決/未解決/重複/重大・要検討・軽微の件数を一覧 |
| | 2. **要確認項目 (優先度順)** — MAJOR/MODERATE/MINOR に自動分類 |
| | 3. **未解決参照の詳細** — タイトル・ジャーナル・DOI・試行経路・推定理由の表 |
| | 4. **構造化品質** — `parsing_confidence=low/medium` 一覧 |
| | 5. **透明性トレース** — 行番号検出、解決経路内訳、全参照スナップショット |

## API Key 設定 (重要)

本スキルは **Anthropic API Key** (必須) と **NCBI API Key** (任意・推奨) を必要とします。
Claude Code スキル経由で起動された場合、親シェルの環境変数は**引き継がれません**。以下のいずれかの方法で設定してください。

### 方法 A: `.env` ファイル (推奨、スキル経由で最も確実)

1. スキル配置ディレクトリ (`~/.claude/skills/pubmed-reference-resolver/`) に移動
2. `.env.example` を `.env` にコピー
3. 自分の key に書き換えて保存

```bash
cd ~/.claude/skills/pubmed-reference-resolver
cp .env.example .env
# エディタで .env を開き、ANTHROPIC_API_KEY と NCBI_API_KEY を書き換え
```

main.py 起動時に自動で `.env` を読み込みます。

**探索順** (先にヒットしたものが優先、既存の環境変数は上書きしない):

| 優先度 | 場所 | 用途 |
|-------|------|------|
| 1 | `{スキル配置dir}/.env` | **スキル経由で最も確実** |
| 2 | `$HOME/.pubmed-reference-resolver.env` | ユーザー専用・ホーム直下 |
| 3 | `$PWD/.env` | 呼び出し元カレントディレクトリ |
| 4 | `{入力PDFと同じdir}/.env` | 論文フォルダに配置 |

### 方法 B: シェル設定ファイル (CLI 直接実行時のみ有効)

`~/.zshrc` / `~/.bashrc` に追記:

```bash
export ANTHROPIC_API_KEY='sk-ant-api03-...'
export NCBI_API_KEY='your-ncbi-key'
```

→ 新しいターミナルで `source ~/.zshrc` 後に `python3 main.py ...` で動作。
**ただし Claude Code スキル経由では子プロセスに引き継がれない可能性あり** → 方法A推奨。

### 方法 C: Claude Code の `settings.json` に埋め込む

`~/.claude/settings.json` に `env` セクションを追加:

```json
{
  "env": {
    "ANTHROPIC_API_KEY": "sk-ant-api03-...",
    "NCBI_API_KEY": "your-ncbi-key"
  }
}
```

Claude Code が Bash ツール等を起動する際に自動で渡します。

### 方法 D: CLI 引数で毎回指定 (その場限り)

```bash
python3 main.py input.pdf \
  --api-key sk-ant-... \
  --ncbi-api-key your-ncbi-key \
  --phase 4
```

### 優先順位 (競合時)

1. CLI 引数 `--api-key` / `--ncbi-api-key` (最優先)
2. 親プロセスの環境変数 (`export ANTHROPIC_API_KEY=...`)
3. `.env` ファイル (自動探索)

## 実行方法

### クイックスタート (エンド・ツー・エンド)

```bash
# .env を配置済みなら key の指定不要
python3 main.py path/to/references.pdf -o ./out --phase 4
```

### 段階実行 (デバッグ用)

```bash
# Phase 1: 抽出 + 前処理 + 行番号統計検出 (LLM/PubMed不使用)
python3 main.py input.pdf --phase 1

# Phase 2: + Stage 3 LLM構造化 (Claude Sonnet 4.6)
python3 main.py input.pdf --phase 2

# Phase 3: + Stage 4 PubMedカスケード検索
python3 main.py input.pdf --phase 3

# Phase 4: + Stage 5 出力合成 (デフォルト)
python3 main.py input.pdf --phase 4

# 既存結果を再利用して部分再実行
python3 main.py input.pdf --phase 4 --reuse-phase2  # LLM構造化スキップ
python3 main.py input.pdf --phase 4 --reuse-phase3  # PubMed検索スキップ
```

## 処理パイプライン (5段階)

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
Stage 3: LLM構造化 (Claude Sonnet 4.6 + プロンプトキャッシュ)
         → authors, title, journal, year, volume, pages, doi, doi_alt, pmid, is_book, language, parsing_confidence, notes
         ↓
Stage 4: PubMedカスケード検索
         Level 1: PMID直接 (efetch)
         Level 2: DOI検索 (doi → doi_alt)
         Level 3: Title + First Author + Year
         Level 4: Title単独 fuzzy (rapidfuzz token_sort_ratio ≥ 90)
         ↓
Stage 5: 出力合成 (CSV / abstract / report / unresolved)
         + 重複検出 (複合キー: PMID || DOI || norm_title+first_author+year)
         + 査読コメント候補生成
```

## 査読コメント候補の自動検出項目

- **重複引用**: 同一論文の複数引用 (複合キー判定)
- **引用年誤記**: 著者引用年 ≠ PubMed発表年 (epub/print年混同の発見に有効)
- **タイトル軽微差異**: fuzzy一致 90-99% (句読点・大文字化差異)
- **タイトル重大差異**: fuzzy一致 < 90% (要人間確認)
- **雑誌名-DOI不整合**: LLMが構造化時に検出 (例: `Ultrasound Med. Biol.` と `10.1093/jjco/...` の不一致)
- **ソフトハイフン破損の復元**: `RELA-TIONSHIP` → `RELATIONSHIP` 等
- **DOI曖昧性の両形式保持**: `j.jpsy-chores` と `j.jpsychores` の両方を試行

## 依存ライブラリ

- `pypdf` (PDF抽出)
- `python-docx` (DOCX抽出)
- `requests` (NCBI E-utilities API)
- `rapidfuzz` (タイトルfuzzy match)
- `tenacity` (5xx/429 指数バックオフリトライ)
- `anthropic` (Claude SDK)

## 設計原則

1. **疑わしきは保持**: 行番号除去・重複判定は保守的に (誤削除・誤統合は致命的)
2. **監査可能性**: 全判断 (行番号除去、検索経路、重複判定) を `report.md` / `phase*_*.json` にログ化
3. **人間が最終判断**: `parsing_confidence=low/medium` のものは目視確認を明示的に促す
4. **単一責務**: 「参照→CSV+abstract変換」に徹する (査読レポート生成や翻訳は他スキルに委ねる)

## 非対応

- 和文文献 (医中誌Web、J-STAGE 等)
- CrossRef / Semantic Scholar 等の他データベース
- 他スキルからのサブルーチン呼出 (本スキルは単体ツールとして完結)
- キャッシュ機構 (1論文1回の査読用途では不要)

## 既存スキルとの関係

- **`paper-search`** (pull型、新着検索): 緩和ケア/がん就労/QOL/疫学の最新論文を PubMed から能動的に探す。本スキルとは **入力と方向が逆** (本スキルは既存引用リストを逆引き検証)。機能衝突なし。
- **`peer-reviewer` / `first-peer-review`**: 査読レポート本体を生成。本スキルは **査読のための引用検証材料** を提供し、前段として連携可。
