---
name: pubmed-reference-resolver
description: 査読対象論文のReferences（PDF/DOCX/TXT、英語）を各文献ごとにPubMedで逆引きし、Word監査レポート・PubMed互換CSV・abstract集の3出力を生成する査読支援スキル。実在性・書誌正確性・重複引用・撤回論文を検証し、原著性・エビデンス水準・最新性・Predatoryリスク・主張支持性を評価する。誤マッチ二重ガードによりAI/LLMの捏造引用も検出する。次のような依頼で必ず使う:「参照文献をPubMedで逆引きして」「Referencesを検証して」「撤回論文が含まれていないかチェックして」「捏造引用かチェックして」「Predatory Journalでないか確認して」「引用の主張を論文が支持しているか確認して」。和文文献は対象外。
---

# pubmed-reference-resolver

論文の参照文献リストを PubMed で逆引きし、**常に同じ 3 ファイル**を生成する。
実在性・書誌正確性・重複・撤回状況を検証し、原著性・エビデンス水準・最新性・
収載状況（Predatory リスク）・（任意で）主張支持性を評価する。

> **本 SKILL.md がパイプライン仕様の正本である。**
> `audit.py` を正規のエントリポイントとする（方式 A・2026/07/25 改修、
> 検証9基準への拡張は 2026/08/22 改修）。
> 旧版 `main.py` の Phase 2〜4 (パイプライン内 Anthropic API 呼出・`report.md` 出力) は非推奨。
> Stage 1-2 (抽出・行番号除去・分割) のみ利用する。

---

## 検証・評価軸（9基準）

**必須4基準**（issue として検出、docx §3 の重要度別表に自動反映）:

| # | 基準 | 実装 |
|---|---|---|
| 1 | 実在性確認 | L1〜L3d のカスケード解決。全戦略で未ヒットなら `unresolved` (MAJOR) |
| 2 | 書誌情報正確性 | PMID/DOI/著者/タイトル/雑誌名/発行年の各不一致カテゴリ |
| 3 | 重複引用検出 | PMID/DOI 複合キーによる `duplicate_citation` (MAJOR) |
| 4 | 撤回論文確認 | PubMed の `PublicationType`（Retracted Publication）と `CommentsCorrectionsList`（RetractionIn/ExpressionOfConcernIn/ErratumIn 等）から検出 |

**評価5基準**（「問題」ではないため issues を汚染せず、docx §5「文献評価サマリ」・CSV新8列に記載。有害所見のみ issue 化）:

| # | 基準 | 実装 | 有害所見の issue 化 |
|---|---|---|---|
| 5 | 主張支持性評価 | 呼び出しClaude式2パス（本文の引用文脈とabstractを突合、`--claim-support`）。**本文なしなら自動スキップ、パイプライン内LLM API呼出は行わない** | `claim_not_supported` (MODERATE) / `claim_partially_supported` (INFO) |
| 6 | 原著性評価 | `PublicationType` から決定論的分類（原著/レビュー/メタ解析/SR/ガイドライン/症例報告/レター等） | 非一次情報源での事実引用は `non_original_source` (INFO) |
| 7 | 文献品質評価 | `PublicationType` ベースのエビデンス階層（SR/MA=1 > RCT=2 > 観察=3 > 症例報告=4）。**Impact Factor等の商用雑誌指標は無料データ源がないため意図的に不使用** | — |
| 8 | 最新性評価 | 発行年からの経過年数（≤5年=最新／≤10年=妥当／>10年=古い） | `outdated_citation` (INFO、>10年時) |
| 9 | Predatory Journal評価 | NLM Catalog（MEDLINE収載）+ DOAJ（無料・認証不要）の複合シグナル。**両シグナル陰性かつL3系解決の場合のみ「要確認」。断定表現は用いない** | `predatory_risk` (MODERATE) |

新規 issue カテゴリを含む全カテゴリ一覧は「整合性チェック 19 カテゴリ」節を参照。

---

## 出力（3 本に固定）

| # | 出力名 | 形式 | ファイル名（固定） |
|:--|:--|:--|:--|
| **①** | 基本レポート | Word (.docx) | `references_audit_report.docx` |
| **②** | 表出力 | CSV (UTF-8 BOM) | `references_pubmed.csv` |
| **③** | abstract 一覧 | テキスト (.txt) | `references_abstracts.txt` |

提示順は **① → ② → ③**（重要度順）。ファイル名は `pipeline/outputs.py` の
`OUT_DOCX` / `OUT_CSV` / `OUT_TXT` で一元管理しており、変更はこの 3 定数のみで完結する。

### 出力① 基本レポート（7 セクション）

1. ダッシュボード（解決状況／整合性チェックサマリ／撤回・懸念表明件数／査読観点の総評）
2. 解決経路の内訳（透明性トレース）
3. 要確認項目（MAJOR → MODERATE → MINOR → INFO の優先度順、**全4段階を描画**）
4. 各文献の詳細（全件／✓ ⊘ ✗）
5. **文献評価サマリ**（v2新設）: 5.1 撤回・懸念表明の警告バナーと一覧表 / 5.2 全件評価表（原著性・エビデンス水準・最新性・収載状況・Predatoryリスク・主張支持性） / 5.3 評価方法の注記（IF不使用等の明記）
6. 特筆事項（非対象判定・未解決の根拠・**内部実装の自己点検記録**）
7. 関連出力ファイル

`build_docx.js`（docx-js）で生成。Yu Mincho。**docx構造の自動バリデーション関数は存在しない**
（`audit.py` は Node サブプロセスの終了コードのみを確認する。SKILL.md旧版の
「バリデーションPASSが必須」は要求仕様であり実装ではない点に注意）。

### 出力② 表出力（29 列）

基本21列（旧仕様のまま）+ 文献評価8列（v2新設）:

```
Ref_No, Match_Status, PMID, PMCID, Title, Authors, First_Author, Journal, Year,
Volume, Issue, Pages, DOI, Publication_Types, Claimed_PMID, Claimed_DOI,
Claimed_Year, Claimed_First_Author, Claimed_Journal, Claimed_Title, Resolution_Path,
Retraction_Status, Retraction_Notice, Recency, Originality, Evidence_Level,
Indexing_Status, Predatory_Risk, Claim_Support
```

詳細は `references/pubmed_csv_schema.md` を参照。
`Match_Status` は `RESOLVED / UNRESOLVED / NON_PUBMED` の 3 値。
`Resolution_Path` は `L1 / L2 / L3a / L3b / L3c / L3d / NON_PUBMED / UNRESOLVED`。
文献評価8列は `Match_Status=RESOLVED` の行のみ値を持つ。

### 出力③ abstract 一覧

78 字幅ラップ（East Asian Width 対応）。RESOLVED は抄録本文＋評価行 `[評価: ...]` を掲載。
**撤回論文は abstract の前に `【警告】` ブロックを表示**。NON_PUBMED / UNRESOLVED は
判定根拠のみを示す。

---

## 配置と実行環境 (最初に確認)

```bash
REPO="$(cd -P ~/.claude/skills/pubmed-reference-resolver/.. && pwd)"
PY="$REPO/.venv/bin/python"
```

- `~/.claude/skills/pubmed-reference-resolver` は `$REPO/skill_package/` への symlink。`audit.py`・`pipeline`・`build_docx.js` は `$REPO` 直下への symlink。
- **初回・別のパソコン・エラー時は `"$REPO/tools/doctor.sh"` を実行**し、✘ を → の手順で解消してから進む (キーの値を表示・入力しない)。
- Python は `$PY` を使う。Word 出力には Node.js と `$REPO/node_modules/docx` が必要 (無ければ `cd "$REPO" && npm ci`)。
- `NCBI_API_KEY` (任意) は次の 4 箇所を先頭から順に自動探索して読み込む (見つかった場所は `[env] loaded from ...` に出る): ① リポジトリ直下 (`main.py` と同じ場所) の `.env` ② `~/.pubmed-reference-resolver.env` **(推奨、chmod 600)** ③ カレントディレクトリの `.env` ④ `refs.json` と同じディレクトリの `.env`。**査読対象の論文フォルダに `.env` を置くと④で読み込まれてしまう点に注意**（意図せぬキー混入を避けるため、論文フォルダに `.env` を置かない）。`--env-file PATH` は上記自動探索の代わりに指定ファイルだけを読む。`--no-env-file` は `.env` を一切読まない。v2 は Anthropic API キーを使わない。

## 実行方法

### 手順

1. **参照文献を読む**: 入力が PDF / DOCX の場合、行番号の混入や改行分断を避けるため、まず抽出する (API 不使用・通信なし)。
   ```bash
   "$PY" "$REPO/main.py" INPUT.pdf --phase 1 --no-env-file -o OUT_DIR/extract
   ```
   `OUT_DIR/extract/phase1_intermediate.json` の参照ブロック (行番号除去・分割済み) を読む。TXT や短いリストは Read で直接読んでよい。
2. **構造化**: `references/llm_parsing_prompt.md` に従い、参照ごとに `refs.json` を書く (本文があれば `citation_contexts` も)。
3. **実行**: 下記コマンドで 3 出力を生成する。`-o` は論文ごとに別フォルダにする (既存ファイルは上書きされる)。
4. **報告**: `references_audit_report.docx` の §1 ダッシュボード・§3 要確認項目・§5 文献評価サマリを要約し、`[self-check]` の注記を必ず伝える。撤回論文・Predatory リスクは断定表現を避ける。

```bash
"$PY" "$REPO/audit.py" --structured refs.json -o ./out \
    --source reference.docx --md5 <md5> --subject "主題"
```

### CLI オプション

| オプション | 説明 |
|---|---|
| `--structured PATH` | 必須。構造化済み `refs.json` |
| `-o, --out DIR` | 出力先ディレクトリ (既定 `./out`) |
| `--source` / `--md5` / `--subject` | レポート表紙用メタデータ |
| `--api-key` | NCBI API key（任意。設定時 10 req/sec、未設定時 3 req/sec） |
| `--env-file PATH` | 明示的な `.env` ファイル（省略時は自動探索。「配置と実行環境」節参照） |
| `--no-env-file` | `.env` ファイルを読まない |
| `--no-docx` | 出力①をスキップ（デバッグ用） |
| `--offline` | 雑誌収載状況照会 (NLM Catalog/DOAJ) をスキップ。Predatory リスク・収載状況は全件「未評価」になる |
| `--claim-support PATH` | 主張支持性判定 JSON（後述の2パスワークフロー） |
| `--reuse-resolved PATH` | 過去実行の `resolved.json` を再利用し PubMed 照合をスキップ（パス2の再レンダリング・オフライン検証用。NCBI通信ゼロ） |

依存は **標準ライブラリのみ**（`rapidfuzz` / `tenacity` / `requests` / `anthropic` は不要）。
出力①の生成にのみ Node.js と `docx`（npm）を用いる。未インストールの環境では
`cd "$REPO" && npm ci`（`package.json` / `package-lock.json` 使用）を実行する。
`NCBI_API_KEY` は任意（設定時 10 req/sec、未設定時 3 req/sec）。DOAJ API は
無料・認証不要（1秒間隔で自主スロットル）。

### 2パス・ワークフロー（主張支持性評価、オプション）

```bash
# パス1: 本文がある場合、refs.json の各参照に citation_contexts を添付して通常実行
"$PY" "$REPO/audit.py" --structured refs.json -o ./out ...

# パス2: 呼び出し側 LLM が resolved.json の abstract と citation_contexts を突合し
#         claim_support.json を作成後、再実行（PubMed再照会なし）
"$PY" "$REPO/audit.py" --structured refs.json -o ./out \
    --reuse-resolved ./out/resolved.json --claim-support ./claim_support.json
```

`refs.json` / `claim_support.json` のスキーマは `references/llm_parsing_prompt.md` を参照。

### `refs.json` スキーマ

```json
{
  "meta": {"source": "reference.docx", "md5": "...", "subject": "...",
           "verdict": ["総評の箇条書き", "..."]},
  "references": [
    {"ref_no": 1, "pmid": "39036382", "doi": "10.1016/j.jncc.2024.01.006",
     "claimed_first_author": "Han B", "claimed_year": 2024,
     "claimed_journal": "J Natl Cancer Cent", "claimed_title": "Cancer incidence...",
     "raw": "1. Han B, Zheng R, ...",
     "is_non_pubmed": false, "non_pubmed_reason": null,
     "non_pubmed_note_if_unresolved": null,
     "citation_contexts": ["本文中の引用箇所の一文 (任意)"]}
  ]
}
```

---

## 処理パイプライン

```
Stage 1-2  抽出・行番号統計検出・前処理・参照分割   … main.py の関数を再利用（任意）
Stage 3    構造化                                 … 呼び出し側 LLM が in-context で実施
                                                    （外部 API 呼出なし＝約110秒/22件を削減）
Stage 4    PubMed カスケード照合                   … pipeline/resolve.py
             L1  PMID 記載分を **一括 efetch**（19件=1リクエスト・0.39秒）
             L2  DOI → esearch → **一括 efetch**
             L3a 著者 + タイトル重要語 + 年
             L3b 著者 + 雑誌 + 年 + タイトル重要語
             L3c 著者 + 雑誌 + 年
             L3d タイトル重要語のみ + 年
Stage 5.5  雑誌収載状況照会 (v2新設)                … pipeline/enrich.py
             NLM Catalog (MEDLINE収載) + DOAJ (無料・認証不要)。--offline でスキップ
Stage 6    整合性チェック（19 カテゴリ / 4 段階）    … pipeline/consistency.py
Stage 6.5  文献評価 (v2新設)                        … pipeline/assess.py
             撤回・原著性・エビデンス水準・最新性・Predatoryリスク・主張支持性
Stage 7    出力生成（3 本固定）                     … pipeline/outputs.py + build_docx.js
Stage 8    自己点検（批判的セルフレビュー）          … audit.py: self_check()
```

## 整合性チェック 19 カテゴリ

| カテゴリ | 判定 | 由来 |
|:--|:--|:--|
| `pmid_mismatch` | 引用元 PMID ≠ 解決 PMID → MAJOR | 必須基準2 |
| `first_author_mismatch` | 姓（正規化後）不一致 → MAJOR | 必須基準2 |
| `title_major_diff` | 類似度 <0.7 MAJOR / 0.7-0.9 MODERATE / 0.9-0.99 MINOR | 必須基準2 |
| `journal_mismatch` | 類似度 <0.6 MAJOR / 0.6-0.8 MODERATE / <1.0 MINOR | 必須基準2 |
| `doi_mismatch` | claimed DOI ≠ PubMed DOI → MAJOR | 必須基準2 |
| `doi_suspicious_in_pubmed` | PubMed 側 DOI が旧式プレースホルダ形式 → MODERATE | 必須基準2 |
| `year_mismatch` | 差 ≥3 年 MAJOR / 2 年 MODERATE / 1 年 MINOR | 必須基準2 |
| `duplicate_citation` | 同一 PMID / DOI が複数参照に出現 → MAJOR | 必須基準3 |
| `unresolved` | 全戦略で未ヒット → MAJOR（MEDLINE 非収録の可能性も併記） | 必須基準1 |
| `missing_pmid` | 引用元に PMID なし、PubMed にあり → INFO | 必須基準2 |
| `missing_doi` | 引用元に DOI なし、PubMed にあり → INFO | 必須基準2 |
| `retracted_publication` | 撤回済み論文の引用 → MAJOR | 必須基準4 (v2新規) |
| `expression_of_concern` | Expression of Concern 付き論文の引用 → MODERATE | 必須基準4 (v2新規) |
| `erratum_notice` | 訂正 (Erratum) が存在 → INFO | 必須基準4 (v2新規) |
| `outdated_citation` | 発行から10年超 → INFO | 評価基準8 (v2新規) |
| `non_original_source` | Letter/Editorial/Comment 等の非一次情報源引用 → INFO | 評価基準6 (v2新規) |
| `predatory_risk` | MEDLINE非収載 かつ DOAJ非収載 かつ L3系解決 → MODERATE（参考フラグ、断定しない） | 評価基準9 (v2新規) |
| `claim_not_supported` | LLM判定 DOES_NOT_SUPPORT → MODERATE | 評価基準5 (v2新規、`--claim-support`時のみ) |
| `claim_partially_supported` | LLM判定 PARTIAL → INFO | 評価基準5 (v2新規、`--claim-support`時のみ) |

## 実装済みの落とし穴対策

1. **XPath 限定** — `./PubmedData/ArticleIdList/ArticleId` と `./MedlineCitation/Article/ELocationID`
   のみを対象とし、`ReferenceList/Reference` 内の ID を拾わない（`resolve.py::_parse_one`）。
   撤回情報抽出 (`CommentsCorrectionsList`) も同様に記事自身に付与された通知のみを対象とする。
2. **タイトル検索に二重引用符を使わない** — Automatic Term Mapping を殺さないため、
   ストップワード除外後の個別単語 AND 検索とする（`resolve.py::title_keywords`）。
3. **誤マッチ二重ガード** — L3 系のヒットは タイトル類似度 ≥0.50 **かつ** 筆頭著者姓一致
   を満たす場合のみ採用（`resolve.py::_accept`）。**L1/L2（PMID/DOI直接一致）はこのガードの対象外**
   （書誌識別子が一致している以上、原則として信頼する）。
4. **雑誌名は ISO 略号を優先**し、比較時に `journal of → j` 等を正規化（`norm_journal`）。
5. **CJK 表示幅** — 出力③のラップは East Asian Width を考慮（`outputs.py::disp_len`）。
6. **Predatory 判定の複合条件** — 単独シグナル（DOAJ非収載など）では判定しない。購読誌は
   DOAJ に載らないため、DOAJ非収載単独は無意味（`assess.py::classify_predatory`）。
7. **--offline の一貫性** — `--reuse-resolved` で過去の収載状況データが読み込まれても、
   `--offline` 指定時は必ず「未評価」に強制降格する（ネットワーク遮断の意思を優先）。

## 非対応

- 和文文献（医中誌 Web、J-STAGE 等）
- CrossRef / Semantic Scholar 等の他データベース（未解決文献の補助検索は別途手動で）
- キャッシュ機構
- 確定的な Predatory Journal リスト（無料の網羅的データ源が存在しないため。参考フラグに留める）
- ジャーナル Impact Factor 等の商用指標（無料データ源が存在しないため意図的に不使用）
- PDF/DOCX から refs.json への自動変換（Day32 予定）
- Crossref による未解決文献の 3 分類（旧版にあり、v2 への統合は Day33 予定）

## 既存スキルとの関係

- **`paper-search`**（pull 型・新着検索）: 入力と方向が逆。機能衝突なし。
- **`peer-reviewer` / `first-peer-review`**: 査読レポート本体を生成。本スキルはその前段。

## ファイル構成 ($REPO)

```
audit.py                 ← 正規エントリポイント
pipeline/                ← resolve / enrich / consistency / assess / outputs
build_docx.js            ← 出力① (docx-js)。package.json / package-lock.json、node_modules は npm ci
main.py                  ← 旧版。Stage 1-2 (抽出) のみ利用、Phase 2-4 は非推奨
tools/doctor.sh          ← 環境診断
tests/fixtures/v2_synthetic_7refs/ ← v2 回帰テスト用の合成 7 件と記録応答
```
