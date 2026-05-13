# USAGE_QUICKSTART.md

**pubmed-reference-resolver スキルの即時使用ガイド**

**作成日**: 2026/05/02 (Day7 = Phase ζ で同梱)
**最終更新**: 2026/05/11 (Day10、§X 変更履歴参照)
**バージョン**: 1.1
**対象**: 本スキルを利用する全ての利用者
**配置**: `skill_package/references/USAGE_QUICKSTART.md` (symlink 経由で `~/.claude/skills/pubmed-reference-resolver/references/USAGE_QUICKSTART.md` でも読み出し可能)

---

## I. このスキルで何ができるか (3 行サマリー)

1. **Reference リストの逆引き検証**: 論文末尾の References を PubMed で逆引き検索し、PMID/DOI 解決と原典との照合を自動化
2. **AI 捏造引用の検出**: ハルシネーション由来の存在しない論文・誤ったジャーナル/年/著者を**3 段階 severity で自動分類**
3. **3 ファイル一括出力**: PubMed 純正互換 CSV + 番号付き abstract text + 統合監査レポート (HTML/Word) を 1 回の実行で生成

LLM 費用: **MDPI 形式は 0 円** (deterministic parser で完結)、**Vancouver/AMA 系は LLM 経路で 24 件 約 $0.20** (Day9 (Z) 実測)。詳細は §III の引用スタイル別ガイド + §VI パフォーマンス特性 を参照。

---

## II. 起動プロンプト (3 シナリオ別の即時利用テンプレート)

### シナリオ A: 1 論文の peer review における Reference 検証

**ユースケース**: 査読対象の論文 PDF があり、Reference の正確性 (PMID 取得 + 引用年誤記検出) を一括確認したい。

**起動プロンプト** (Claude Project または skill 投入時):

```
このPDFの References セクションを pubmed-reference-resolver で検証してください。

入力: <PDFファイル添付>
出力先: ~/Desktop/Claude/査読出力/<論文名>/
出力ファイル:
- references.csv (PubMed CSV)
- abstracts.txt (番号付き abstract 集)
- audit_report.docx (監査レポート、ダッシュボード + 要確認項目)
```

**期待動作**:

1. PDF から References セクションを抽出 (行番号除去、改行ハイフン結合、段落復元)
2. 各文献を split_references で個別化 (典型 30 件)
3. MDPI 形式は fast-path で deterministic 解析、その他は LLM 解析
4. PubMed API (esearch + efetch) で PMID/abstract 取得
5. journal_audit で 3 段階 severity 分類 (重大/要検討/軽微)
6. 出力 3 ファイル生成

**所要時間**: 30 件の References で 約 1-3 分 (PubMed API 待機含む)。

---

### シナリオ B: 系統的レビューでの一括検証 (100 件超)

**ユースケース**: メタアナリシスや系統的レビューで、Included studies 全件の引用情報を一括検証したい。

**起動プロンプト**:

```
以下の References リスト (テキストファイル、各文献を空行で区切り) を
pubmed-reference-resolver で一括検証してください。

入力: <references.txt 添付、120 件想定>
出力先: ~/Desktop/Claude/メタアナ検証/<プロジェクト名>/
オプション:
- 重複引用を検出した場合は audit_report.docx の冒頭に明示
- DOI から PubMed 解決できなかった文献は別シート (excel sheet 2)
```

**期待動作**:

- 重複検出: 複合キー (PMID/DOI/title+author+year) で重複引用を検出
- 未解決文献: 空行として CSV に保持 (削除しない、構造を維持)
- 監査レポートに「未解決 X 件 / 解決 Y 件 / 重大エラー Z 件」のダッシュボードを冒頭表示

**所要時間**: 120 件で 約 5-15 分。

---

### シナリオ C: AI 捏造引用の検出 (ハルシネーション検証)

**ユースケース**: ChatGPT や Claude 等の LLM で生成された原稿の引用が、実在の論文を指しているか検証したい。

**起動プロンプト**:

```
このAI生成原稿の References セクションを pubmed-reference-resolver で
ハルシネーション検証してください。

入力: <原稿.docx または .pdf 添付>
出力先: ~/Desktop/Claude/AI原稿検証/<原稿名>/
重点確認項目:
- MEDLINE 収録誌を名乗りながら PubMed 未ヒット + DOI 未解決の文献
  (= 捏造の可能性が高い)
- 著者名・論文タイトル・発表年の同時不整合 (= 完全捏造の特徴)
- DOI と雑誌名の不整合 (= 部分捏造、コピペ起因)
```

**期待動作**:

- 捏造可能性ランキング: severity = 重大として独立シート/セクションで報告
- 各「重大」フラグに**判定根拠**を 1-2 文で明記 (例: "PubMed search returned 0 hits; DOI 10.1234/... resolves to a different paper title")
- audit_report.docx に「**捏造疑い** N 件」の警告ヘッダー

**所要時間**: 30 件で 約 2-5 分 (PubMed API 通信が主要コスト)。

---

## III. 入力形式の許容範囲

| 形式 | 対応 | 備考 |
|:---|:---:|:---|
| PDF | ◎ | 行番号自動除去 (preprint/MDPI 形式の 5 パターン全対応) |
| DOCX | ◎ | python-docx で抽出 |
| TXT | ◎ | 改行ハイフン自動結合、段落復元 |
| HTML | ○ | text 抽出後 TXT として処理 |
| 和文文献 | × | 英語論文専用 (医中誌は別スキル `paper-search` 等を使用) |

引用スタイル: Vancouver / AMA / APA / Harvard / Chicago / Nature / Cell / MDPI 等、**スタイル不問**で対応。

### 引用スタイル別の処理経路 (Day9 で確立)

is_mdpi_style() の判定により、入力 reference は以下のいずれかに routing される:

| 引用スタイル | 判定 marker | 処理経路 | API key 必須 | 解決率 (実測) |
|:---|:---|:---:|:---:|:---:|
| **MDPI** (`Surname, I.; ... YYYY, Vol`) | 著者 `;` 区切り + 年前置コンマ | deterministic parser (fast-path) | ANTHROPIC: 不要、NCBI: 推奨 | 149/149 = 100% (golden fixture) |
| **Vancouver / AMA** (`(YYYY)` 括弧年) | `(YYYY)` Vancouver Veto (Day9) | LLM (Claude Sonnet 4.6) | **ANTHROPIC: 必須**、NCBI: 推奨 | 22/24 = 91.7% (Day9 (Z) 実測) |
| **APA / Harvard 等 (上記いずれにも該当しない)** | M1 (YYYY) hit なし、不完全 MDPI fallback | deterministic parser (fast-path、graceful 処理) | ANTHROPIC: 不要 | 未測定 (将来 fixture 化候補) |

**Vancouver/AMA 系入力での重要事項**:
- `.env` または `--env-file` で **ANTHROPIC_API_KEY を必ず設定**してください. 未設定の場合 Phase 2 で `RuntimeError: ANTHROPIC_API_KEY not set` が発生します.
- 費用目安: 24 件で 約 $0.15-0.25 (Claude Sonnet 4.6 経由、Day9 (Z) 実測). 100 件超なら $1 前後.
- 解決率は MDPI 同等の高水準 (91.7%) で、parser 起因の false positive 重大エラーが完全消滅します. 詳細は `docs/sessions/day9/DAY9_LESSONS_LEARNED.md` §4.2 参照.
- 所要時間: 24 件で 約 2-3 分 (LLM 構造化が ~110 秒のボトルネック、Day7-8 の 35-61 秒より長い).

---

## IV. 出力 3 ファイルの構造

### IV-1. references.csv (PubMed 純正互換)

PubMed の純正 export と同一フォーマット (タイトル、著者、雑誌、巻号、年、PMID、DOI 等)。Mendeley/Zotero/EndNote へのインポートに直接利用可能。

未解決文献は**空行として保持** (削除しない)。これにより原稿の引用番号と CSV 行番号が一致する。

### IV-2. abstracts.txt (番号付き)

```
[1] Smith et al., 2020. Title of paper.
PMID: 12345678
Abstract: Background...
        Methods...
        Results...
        Conclusions...

[2] (PubMed 未ヒット - manual review required)

[3] Jones et al., 2019. Another paper title.
PMID: 23456789
...
```

査読中の参照に最適化されたフォーマット。

### IV-3. audit_report.docx (統合監査レポート)

| セクション | 内容 |
|:---|:---|
| ダッシュボード | 全文献数、解決数、未解決数、severity 別件数 |
| 重大エラー (要修正) | サイン discrepancy、年誤記、捏造疑い等 |
| 要検討 (review recommended) | 軽微な書式エラー、雑誌名略称揺れ等 |
| 軽微 (informational) | 特に問題なし、参考情報 |
| 未解決参照詳細 | PubMed/DOI 未ヒット文献の生引用テキスト |

---

## V. よくある問題と対処

### Q1. 「PubMed API rate limit に達した」エラーが出る

→ NCBI API Key を取得 (https://www.ncbi.nlm.nih.gov/account/) し、環境変数 `NCBI_API_KEY` に設定。これにより rate limit が **3 req/sec → 10 req/sec** に緩和される。

### Q2. 行番号がうまく除去されない (preprint PDF)

→ preprint PDF は行番号位置が論文ごとに異なる (行頭/行末/独立行/中央/散在の 5 パターン)。**5 パターン全対応**だが、極端なレイアウトでは失敗する場合あり。失敗時は `manual_overrides.yaml` に既知ケースとして登録 (現在 4 件登録済)。

### Q3. MDPI 形式以外で精度が低い

→ **Day9 改修済 (2026/05/11)**. is_mdpi_style() に Vancouver Veto (`(YYYY)` 括弧年検出) を導入し、Vancouver/AMA 系入力は自動的に LLM 経路に routing されるようになりました.

実績 (Day9 (Z) 実測、Stage 2 OneDrive 24 件):
- 解決率: 旧 14/24 (58.3%) → **新 22/24 (91.7%)** (+33% pt)
- 重大エラー: 旧 4 件 (うち 3 件 parser 起因 false positive) → **新 0 件** (完全解消)
- title 抽出品質: parser 誤認 8 件 → LLM 解析で全件正解

詳細: `docs/sessions/day9/DAY9_LESSONS_LEARNED.md` §4.2-4.4.

なお、APA / Harvard 等の `(YYYY)` を含まないスタイルは現在も MDPI fast-path の不完全 ref fallback で処理されます. 将来的に別ドメイン golden fixture (`tests/fixtures/vancouver_*` / `apa_*` 等) を追加して個別最適化する計画です.

### Q4. 捏造判定で false positive が多い

→ 判定基準は "**MEDLINE 収録誌を名乗りながら PubMed 未ヒット + DOI 未解決**" の AND 条件。厳しすぎる場合は、`severity_threshold` パラメータで閾値調整可能。

### Q5. 監査レポートで Word の表示が崩れる

→ Word 2019 以前は一部スタイルが非対応。Word 2021+ または LibreOffice Writer での閲覧を推奨。

---

## VI. パフォーマンス特性

| 文献数 / スタイル | 所要時間 (NCBI key あり) | LLM 呼出回数 | 出典 |
|:---|:---:|:---:|:---|
| 30 件 (MDPI 中心) | 1-3 分 | 0 (全 fast-path) | 推定 |
| 30 件 (混在) | 1-3 分 | 5-15 | 推定 |
| 100 件 (MDPI 中心) | 3-8 分 | 0-5 | 推定 |
| 100 件 (混在) | 3-8 分 | 30-60 | 推定 |
| 200 件 (MDPI 中心) | 8-15 分 | 0-10 | 推定 |
| 200 件 (混在) | 8-15 分 | 60-120 | 推定 |
| **24 件 (Vancouver/AMA)** | **約 2.5 分** (Phase 2: 110s, Phase 3: 38s) | **24 (全件 LLM)** | **Day9 (Z) 実測** |
| 149 件 (MDPI golden) | 3-4 分 | 0 (全 fast-path) | Day7 Stage 1 実測 |

**LLM 費用見積り** (Claude Sonnet 4.6 前提):

- 全 MDPI: **$0** (deterministic parser のみ)
- 混在 30 件: 約 $0.10-0.30
- **Vancouver/AMA 24 件: 約 $0.15-0.25** (Day9 (Z) 実測)
- 混在 200 件: 約 $0.60-1.50
- Vancouver/AMA 100 件 (推定): 約 $0.60-1.00

(価格は変動する可能性があるため、実際の利用前に Anthropic API pricing を確認)

---

## VII. カスタマイズオプション

### VII-1. manual_overrides.yaml による既知限界への対処

特定の引用 (PDF parser 限界に該当する 4 件等) を手動で正解値に置換可能。

```yaml
# skill_package/manual_overrides.yaml (project 本体への symlink)
overrides:
  - reference_number: 66
    pmid: "12345678"
    title: "正解タイトル"
  - reference_number: 137
    pmid: "23456789"
    ...
```

### VII-2. severity 閾値の調整

journal_audit のデフォルト閾値:

- 重大: 雑誌名類似度 < 0.50
- 要検討: 0.50 ≤ 類似度 < 0.80
- 軽微: 類似度 ≥ 0.80

プロジェクト固有のチューニングが必要な場合は `journal_audit.py` を fork して閾値変更。

### VII-3. 出力先のカスタマイズ

デフォルトは起動プロンプトで指定された出力先。指定なしの場合は `~/Downloads/pubmed_resolver_output_<timestamp>/`。

---

## VIII. 関連リソース

| リソース | 場所 |
|:---|:---|
| スキル定義 | `skill_package/SKILL.md` |
| 引用スタイル例 | `skill_package/references/citation_style_examples.md` |
| LLM 解析プロンプト | `skill_package/references/llm_parsing_prompt.md` |
| PubMed CSV スキーマ | `skill_package/references/pubmed_csv_schema.md` |
| サンプル入出力 | `skill_package/examples/` |
| 開発履歴 (Day1-6) | `skill_package/DEVELOPMENT_NOTES.md` |
| 6 日間の協働記録 | `docs/sessions/day6/` (本リポジトリ) + Day1-6 記録 (本リポジトリ外) |

---

## IX. トラブル時の連絡先

本スキルは個人開発のため、Issue tracker は未公開。以下のいずれかで対応:

1. **同一プロジェクト内の他のセッション**: Claude Code に `skill_package/DEVELOPMENT_NOTES.md` を参照させて改修指示
2. **新セッションでの改修**: Day7 記録テンプレート (`docs/templates/TEMPLATE_day_record.md`) を起点に新規開発セッション開始

---

## X. 変更履歴

### バージョン 1.1 (2026/05/11、Day10 更新)

Day9 で発見・実装された Vancouver Veto と (Z) 実機検証データを反映:

- **§I (3 行サマリー)**: LLM 費用記載に Vancouver/AMA 系の具体コスト ($0.20/24refs) を追記.
- **§III (引用スタイル別の処理経路)**: 新サブセクションを追加. is_mdpi_style() の判定 marker、処理経路、API key 必須性、解決率 (実測) を表形式で整理. Vancouver/AMA 系入力での重要事項 (ANTHROPIC_API_KEY 必須、費用、所要時間) を明記.
- **§V Q3 (MDPI 形式以外で精度が低い)**: 「Day7 以降の長期タスク計画中」から「Day9 改修済」に書換. Day9 (Z) 実績 (解決率 14/24 → 22/24, +33% pt; 重大エラー 4 → 0) を記載.
- **§VI (パフォーマンス特性)**: 表に Vancouver/AMA 24 件 (Day9 (Z) 実測) と MDPI 149 件 (Day7 Stage 1 実測) の 2 行を追加. 推定値と実測値を「出典」列で明示区別. LLM 費用見積りに Vancouver/AMA 24 件の項目を追加.

参照: `docs/sessions/day9/SPEC_mdpi_fast_path_strict.md`, `docs/sessions/day9/DAY9_LESSONS_LEARNED.md`.

### バージョン 1.0 (2026/05/02、Day7 = Phase ζ で同梱、初版)

初版作成. Day1-6 統合実装の skill 即時利用ガイドとして 9 章構成 (I-IX) で同梱. シナリオ A (peer review 1 論文) / B (系統的レビュー 100 件超) / C (AI 捏造引用検出) の 3 起動テンプレート、3 出力ファイル仕様、5 つの FAQ、性能特性、カスタマイズオプションを記載.

---

**作成日**: 2026/05/02 (バージョン 1.0)、2026/05/11 (バージョン 1.1 更新)
**作成者**: Claude Opus 4.7 (1.0)、Claude Code Sonnet 4.6 (1.1)
**ファイル名**: `USAGE_QUICKSTART.md`
**配置**: `skill_package/references/USAGE_QUICKSTART.md`
**symlink 経由パス**: `~/.claude/skills/pubmed-reference-resolver/references/USAGE_QUICKSTART.md`
**メンテナ**: 片山英樹 (Hideki Katayama)
**バージョン**: **1.1** (Day10 更新)
