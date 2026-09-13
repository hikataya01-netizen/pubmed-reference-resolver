---
name: pubmed-reference-resolver
description: 査読対象論文のReferences(PDF/DOCX/TXT、英語)を各文献ごとにPubMedで逆引きし、PubMed互換CSV・番号付きabstract集・統合監査レポート(report.md)を生成する査読支援スキル。重複引用、引用年誤記、タイトル改変、ジャーナル名とDOIの不整合を重大度別に分類し、PubMed未ヒット文献はCrossrefとNLM Catalogで「捏造疑い/MEDLINE非収録誌/indexing漏れ」に3分類する(AI捏造引用の検出)。次のような依頼で使う:「参照文献をPubMedで逆引きして」「Referencesを検証して」「引用文献のPMIDを取得」「abstract集を作って」「重複引用を検出」「捏造引用かチェックして」「ジャーナル名とDOIの整合性をチェック」。和文文献は対象外。新着論文の検索(paper-search)とは逆方向の、既存の引用リストを検証するツール。
---

# pubmed-reference-resolver

論文の参照文献リストを PubMed で逆引きし、**査読実務に直結する3ファイル**(統合監査レポート / PubMed CSV / abstract text)と補助 JSON を生成する。

## 配置と実行環境(最初に確認)

- **本体リポジトリ(`$REPO`)**: `~/.claude/skills/pubmed-reference-resolver` は `$REPO/skill_package/` への symlink。リポジトリの場所はパソコンごとに違ってよく、symlink から次のように求める(bash / zsh 共通):

  ```bash
  REPO="$(cd -P ~/.claude/skills/pubmed-reference-resolver/.. && pwd)"
  ```

  - `main.py` 等も `$REPO` 直下への symlink で、`three_class_classifier.py` / `crossref_check.py` / `nlm_catalog_check.py` は `$REPO` 直下にのみ存在する。**skill_package 単体をコピーして配布すると Phase 4 が動かない。**
- **環境診断**: 初回・別のパソコン・エラー時は、まず `"$REPO/tools/doctor.sh"` を実行する。Python 環境、API キーの読込、スキル登録、サンプル PDF での動作、外部 API 疎通を確認し、問題があれば直し方(→ の行)を表示する。✘ が出たら、その手順をユーザーに示して解消してから本処理に進む(キーの値を表示・入力しない)。
- **Python**: 必ず `$REPO/.venv/bin/python` を使う。システムの `python3` には依存ライブラリが揃っていない。
  - `.venv` が無い/壊れた場合: `cd "$REPO" && uv sync --frozen`
- **API キー**: `~/.pubmed-reference-resolver.env`(chmod 600)に `ANTHROPIC_API_KEY` と `NCBI_API_KEY` を置く。cwd に関係なく自動で読み込まれ、起動時に `[env] loaded from ...` と表示される。キーは git 管理外なので、パソコンごとに配置が必要。
  - 詳細: `$REPO/docs/operations/SETUP_API_KEYS.md`

## 実行手順

```bash
REPO="$(cd -P ~/.claude/skills/pubmed-reference-resolver/.. && pwd)"

# 全工程 (Phase 4)
"$REPO/.venv/bin/python" "$REPO/main.py" path/to/references.pdf -o path/to/out

# 手動補正あり
"$REPO/.venv/bin/python" "$REPO/main.py" path/to/references.docx -o path/to/out --overrides path/to/manual_overrides.yaml
```

1. 入力ファイルと出力先 `-o` を決める。**`-o` の既定は cwd の `./out`**。既存ファイルは確認なく上書きされるため、論文ごとに別フォルダを指定する。
2. 実行する。外部通信と費用:
   - Anthropic API(課金): MDPI 以外の参照の構造化(Phase 2)。24件で約 $0.2。
   - NCBI E-utilities(無料): Phase 3。
   - Crossref / NLM Catalog(無料): Phase 4 の未ヒット文献3分類。
3. `report.md` を読み、ダッシュボードと §1 要確認項目(MAJOR→MODERATE→MINOR)をユーザーに要約する。
4. `parsing_confidence=low/medium` の文献と、3分類 C(indexing 漏れ)は人手確認が必要と明示する。

### 段階実行・部分再実行(デバッグ用)

| コマンド | 内容 | 外部通信 |
|---|---|---|
| `--phase 1` | 抽出 + 前処理 + 行番号統計検出 | なし |
| `--phase 2` | + Stage 3 構造化 | Anthropic(MDPI 以外) |
| `--phase 3` | + Stage 4 PubMed カスケード検索 | NCBI |
| `--phase 4`(既定) | + Stage 5 出力合成・監査 | Crossref / NLM |
| `--reuse-phase2` | 既存 `phase2_structured.json` を再利用(構造化スキップ) | |
| `--reuse-phase3` | 既存 `phase3_resolved.json` を再利用(Phase 4 のみ) | |

## 対応入力

- **ファイル形式**: PDF / DOCX / TXT(PDF が主用途)
- **引用スタイル**: Vancouver / AMA / APA / Harvard / Chicago / Nature / Cell / MDPI など不問(MDPI は決定論的 fast-path で LLM 費用ゼロ)
- **言語**: 英語論文のみ(和文文献・医中誌Web・J-STAGE は非対象)
- **件数**: 30件中心、100件超のレビュー論文にも対応(149件 MDPI ゴールドスタンダードで fixture 一致を検証済)
- **PDF 由来の行番号混入**: 行頭・行末・行中・数字連結・散在の5パターンを統計的に検出・除去

## 出力ファイル(`-o` 配下)

| ファイル | 内容 |
|---|---|
| `report.md` | **統合監査レポート**。ダッシュボード / §1 要確認項目(1.1 MAJOR・1.2 MODERATE・1.3 MINOR、ジャーナル名 vs DOI 不整合を含む)/ §2 未解決参照の詳細(3分類を含む)/ §3 構造化品質 / §4 透明性トレース / 補遺: ジャーナル名監査 / 免責事項 |
| `csv-{first_pmid}-set.csv` | PubMed 純正互換 CSV + `Ref_No`, `Duplicate_of` 列(UTF-8 BOM) |
| `abstract-{first_pmid}-set.txt` | PubMed 標準 abstract text 形式、番号付き、未ヒットは1行保持 |
| `journal_mismatch_audit.json` | ジャーナル名類似度監査の sidecar(全件の生データ) |
| `three_class_classification.json` | PubMed 未ヒット文献の3分類結果 sidecar |
| `phase1_*.txt/json`, `phase2_structured.json`, `phase3_resolved.json` | 各段階の中間結果(監査・再実行用) |

## 処理パイプライン

```
Stage 1   抽出 (pypdf / python-docx / txt)
Stage 2.5 行番号統計検出 (LIS ≥ 10、3桁、年号範囲外)
Stage 2   前処理: ハイフン橋渡し救済 / 独立行番号除去 / 粗い参照境界検出
Stage 3   構造化: MDPI 形式 → mdpi_parser (決定論的)
                  それ以外  → Claude Sonnet 4.6 + プロンプトキャッシュ
          (manual_overrides.yaml の補正を適用)
Stage 4   PubMed カスケード: PMID直接 → DOI (doi → doi_alt) → Title+First Author+Year
                             → Title 単独 fuzzy (rapidfuzz token_sort_ratio ≥ 90)
Stage 5   出力合成 + 重複検出 (PMID || DOI || norm_title+first_author+year)
          + journal_audit: MAJOR (<50%) / WARN (50-79%) / INFO (80-99%) / OK (100%, sidecar のみ)
          + 未ヒット文献3分類 (Crossref + NLM Catalog)
```

## 査読コメント候補の自動検出項目

- **重複引用**: 同一論文の複数引用(複合キー判定)
- **引用年誤記**: 著者引用年 ≠ PubMed 発表年(epub/print 年混同の発見に有効)
- **タイトル差異**: fuzzy 一致 90-99% は軽微、< 90% は重大(要人間確認)
- **雑誌名-DOI 不整合 (MAJOR)**: journal_audit による類似度 50% 未満
- **ソフトハイフン破損の復元**(`RELA-TIONSHIP` → `RELATIONSHIP`)、**DOI 曖昧性の両形式試行**
- **PubMed 未ヒット文献の3分類**(判定の考え方: `references/USAGE_QUICKSTART.md` §V Q4、調査記録: `$REPO/docs/sessions/day13/INVESTIGATION_unresolved_2refs.md`):
  - **A. 捏造疑い**: DOI が Crossref に実在しない — **重大**
  - **B. MEDLINE 非収録誌の正規論文**: DOI 実在 + 誌の `currentindexingstatus = N`(predatory journal を含む)— **軽微(predatory 注意)**
  - **C. MEDLINE 収録誌の indexing 漏れ**: DOI 実在 + 誌は `Y` だが論文単体が未収録 — **軽微(人手確認推奨)**
  - ユーザーへの報告では「PubMed 未ヒット = 捏造」と断定しない。A でも DOI の誤記の可能性があることを添える。

## 手動補正機能(manual_overrides.yaml)

既知のパーサ限界を `ref_no` 単位で明示補正する YAML。

```yaml
overrides:
  - ref_no: 66    # journal boundary issue
    journal: "..."
  - ref_no: 141   # book detection without ISBN
    is_book: true
    publisher: "..."
  - ref_no: 148   # title/journal split with smart quote U+2019
    title: "..."
    journal: "..."
```

149件 MDPI ゴールドスタンダードでは4件の既知限界がこれで解決される(サンプル: `manual_overrides.yaml`)。

## 設計原則

1. **疑わしきは保持**: 行番号除去・重複判定は保守的に(誤削除・誤統合は致命的)
2. **監査可能性**: 全判断を `report.md` と sidecar / 中間 JSON にログ化
3. **人間が最終判断**: `parsing_confidence=low/medium` と3分類 C は目視確認を促す
4. **単一責務**: 「参照 → CSV + abstract + 監査レポート」に徹する(査読レポート本体・翻訳・要約は他スキル)

## 非対応

- 和文文献(医中誌Web、J-STAGE 等)
- Semantic Scholar 等、PubMed / Crossref / NLM Catalog 以外のデータベース
- 他スキルからのサブルーチン呼出(単体ツールとして完結)
- キャッシュ機構(1論文1回の査読用途では不要)

## 既存スキルとの関係

- **`paper-search`**(pull 型、新着検索): 入力と方向が逆。機能衝突なし。
- **`peer-reviewer` / `first-peer-review`**: 査読レポート本体を生成。本スキルはその前段の引用検証材料を提供する。

## 参考資料

- `references/USAGE_QUICKSTART.md` — 利用ガイド・FAQ
- `references/pubmed_csv_schema.md` — CSV 列定義
- `references/citation_style_examples.md` / `references/llm_parsing_prompt.md` — 構造化の仕様
- `examples/` — サンプル入力と期待出力
- `DEVELOPMENT_NOTES.md` と `$REPO/docs/` — 開発経緯・設計判断(実行には不要)
