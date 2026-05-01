# DEVELOPMENT NOTES — pubmed-reference-resolver

開発経緯と意思決定の記録。**Phase 0-4 (初期実装)** と **Day1-Day4 (統合計画)** の 2 段階で構成される。

---

## 第 1 部: Phase 0-4 (初期実装、2026/04 中旬)

### Phase 0: 実データ検証 (ドライラン)

#### 入力サンプル
- `referenceサンプル.pdf` (MDPI形式、15参照、2ページ、34行番号)

#### 発見事項

1. **行番号パターン**: 全34件が**行末型のみ**、連続番号 567-600
2. **引用スタイル**: MDPI 特有 (ACS寄りVancouver)、`N. Authors. Title. Journal. Year, Vol, Pages, DOI` 形式
3. **言語**: 主に英語、仏語2件 (#4 Robieux, #5 Lantheaume)
4. **特殊ケース**: 書籍1件 (#9 Flückiger, ISBN付き)

#### ハイフネーション破損の事前発見

DOIが行番号で分断されているケース:
- `gpsych- 570\n2022-100871` (真値のハイフン)
- `j.jpsy- 573\nchores.2022.111139` (偽ハイフン、真値は hyphen なし)
- `RELA- 588\nTIONSHIP` (ソフトハイフン、語途中)

判別不可能なため、前処理は**保守的にハイフン保持** + Stage 3 LLM でコンテキスト判断 + Stage 4 で `doi_alt` 両形式試行の3層防御を設計。

### Phase 1: Stage 1-2.5 (MVP)

#### 重大発見: pypdfのインライン抽出特性

初期実装は「ページ内改行を保持する」前提で regex を書いていたが、pypdf は**ページ全体を1行に連結**する。
当初 `\s*\n\s*` 前提だった行番号パターンを、**インライン空白区切り対応**に全面改修:

```python
# Before (broken):
hyphen_pattern = re.compile(rf"-\s+{alt}\b\s*\n\s*")

# After (correct for both inline and cross-line):
hyphen_pattern = re.compile(rf"-\s+{alt}\b\s+")
```

#### 統計的行番号検出アルゴリズム

LIS (最長単調増加部分列) ベースで判定。閾値は以下で調整済:
- 最低長: 10 (サンプルでは 34 を検出、全候補 35 中 34が LIS)
- 3桁のみ: `100 ≤ v ≤ 999`
- 年号除外: `1900 ≤ v ≤ 2099` の候補は除外

偽陽性リスク: `2022, 165, 111139` の `165` (volume number) は 3桁非年号。ただし位置が既存LIS値の間に挟まっても整合しないため、LIS構築から自然に脱落。

#### 参照境界検出

正規表現 `(?<![\d.])(\d+)\.\s+(?=[A-Z])` で参照マーカー検出。負の先読みで `10.5` (版番号) 等を除外。サンプル15件全て正確に抽出。

### Phase 2: Stage 3 (LLM構造化)

#### モデル選定

仕様書記載の `claude-sonnet-4-20250514` は古い識別子。最新 `claude-sonnet-4-6` に置換。15件で 22.6K 入力トークン / 5.1K 出力トークン、約78秒、コスト約$0.15。

#### プロンプトキャッシュが発動せず (既知の軽微課題)

`cache_create=0, cache_read=0`。原因: system prompt が約1060トークン、Sonnet 4.6 の最小キャッシュサイズ 1024 トークン付近で境界条件に触れている可能性。

#### LLM品質検証結果

- **ソフトハイフン復元**: 4/4件 全成功 (`RELA-TIONSHIP`→`Relationship`, `dépres-sifs`→`dépressifs`, `Re-sources`→`Resources`, `Charac-teriz-ing`→`Characterizing`)
- **DOI曖昧性**: ref #3 で `doi` と `doi_alt` 両形式を正確に分離 → Stage 4 で doi_alt 経由で解決成功
- **書籍検出**: `is_book=true`で DOI/title 検索をスキップ
- **非英語**: 仏語 `language="fr"` 正確判定
- **想定外の good finding**: ref #13 で「雑誌名 `Ultrasound Med. Biol.` と DOI `10.1093/jjco/...` の不整合」を LLM が自発的に検出 → これが後の Day2 Step 5 (journal_audit モジュール) 開発の動機となる

### Phase 3: Stage 4 (PubMedカスケード検索)

#### 段階カスケードの実装

1. PMID直接 (efetch)
2. DOI検索 (`"{doi}"[AID] OR "{doi}"[DOI]`) — `doi` → `doi_alt` の順
3. Title + First Author + Year (タイトル先頭10単語、PDAT)
4. Title単独 fuzzy (rapidfuzz token_sort_ratio ≥ 90)

#### 結果

15件中 **9件解決 (60%)**。未解決6件は全て**期待通り**:
- ref #4: 仏語、DOI無、MEDLINE非収録
- ref #7, #8, #10, #11: 心理学/社会科学ジャーナル (Theory & Psychology, J Happiness Stud, Rev Gen Psychol, Personnel Psychology) MEDLINE非収録
- ref #9: 書籍 (Hogrefe Publishing)

**PubMed収録対象のみで評価: 9/9 = 100% 解決率**。

#### レート制限

- NCBI API key あり: 10 req/sec (0.11秒スリープ)
- 15件 × 平均3-4 API呼出 = 約50呼出を 18秒で完了
- tenacity による 5xx/429 指数バックオフリトライ実装済 (本検証では未発動)

### Phase 4: Stage 5 (出力合成)

#### XPath バグ発見と修正 (重大)

初期実装では `.//ArticleIdList/ArticleId` で DOI を抽出していたが、PubMed の efetch XML には `PubmedData/ArticleIdList` (正規) と `CommentsCorrectionsList/*/ArticleIdList` (関連記事参照) の**2種類が存在**する。

症状: ref #2 (Wang 2022) の DOI が `10.1188/16.ONF.E104-E120` (完全無関係の ONF 記事) として取得される。

修正: XPath を `./PubmedData/ArticleIdList/ArticleId` に限定、`Article/ELocationID` もフォールバックに追加。修正後、全9件の DOI が正確に抽出されることを確認。

#### 重複検出の合成テスト

`examples/sample_duplicates.txt` に 6参照を配置:
- ref #1 と #4: 同一論文 (Vancouver vs APA スタイル、同じDOI)
- ref #2 と #6: 同一論文 (ref #6 は DOI無記載だが title+author+year で同じ PMID に解決)

結果: **両ペアとも正確に検出** (`Duplicate_of` 列および report.md 査読コメントに反映)。

### Phase 0-4 の検証完了済

- [x] Phase 1: 抽出・前処理・行番号検出・境界検出 (実データ1本、15/15正確)
- [x] Phase 2: LLM構造化 (実データ、15/15成功、エラー0)
- [x] Phase 3: PubMedカスケード検索 (実データ、9/15解決=対象の100%)
- [x] Phase 4: 4ファイル出力 + 重複検出 (合成データで双方向検証済)

---

## 第 2 部: Day1-Day4 統合計画 (2026/04/20-04/23)

Phase 0-4 で MVP は確立されたが、149 件規模の MDPI ゴールドスタンダードに対する byte 単位 fixture 一致と、ジャーナル名監査機能の追加を目的として、4 日間の統合計画 (Steps 1-7) が実施された。

### 計画概要

| Step | 内容 | Day | commit |
|:---:|:---|:---:|:---|
| baseline | 統合前スナップショット | Day1 | `ea3d604`, `a0bba56` |
| 1 | Phase 1 split_references 境界バグ修正 | Day1 | `b8c187c` |
| 2 | MDPI parser モジュール新規追加 | Day2 | `531bfe0`, `c4b67c5`, `941e914` |
| 3 | structure_all_references に fast-path 組込 | Day2 | `10a2a76` |
| 4 | manual_overrides.yaml サポート追加 | Day2 | `04b15eb` |
| 5 | journal_audit モジュール新規追加 | Day2 | `1dbf9d7` |
| 6 | Stage 5 report.md に journal audit 統合 | Day3 | `7b813c2` |
| 7 | CI 基盤整備 (requirements/CI/README) | Day4 | `68509d7`, `f6ec966`, `0c41432` |
| (後処理) | merge + CHANGELOG + archive notice | Day4 | `5d2d5a9`, `1717963`, `c404a05` |

### Day1 (2026/04/20): Step 1 完了

#### 主要成果
- baseline スナップショット 2 commit
- `split_references` の DOI 境界判定バグ修正
- Dutch/French の小文字始まり著者名 (例: van der, de) を許容する lookahead 拡張

#### 学び
- baseline の明示的 commit 化により、以降の変更との純粋な比較が可能に
- 言語多様性 (オランダ語、フランス語の名前) への配慮が学術引用処理では必須

### Day2 (2026/04/21): Steps 2-5 完了 (4 ステップ一気通貫)

#### 主要成果
- **Step 2**: `mdpi_parser.py` 新規追加、決定論的 MDPI 形式パース
- **Step 3**: `structure_all_references` に fast-path 統合、MDPI 形式は LLM bypass
- **Step 4**: `manual_overrides.yaml` ロードと適用ロジック
- **Step 5**: `journal_audit.py` 新規追加、3 段階 severity 分類

#### Day2 で確立された主要原則

1. **ゴールドデータ純化の原則**: fixture を絶対的な正解として扱う
2. **手順の独立化**: 実装前に調査ステップを挟む価値の確認
3. **判断ポイント事前列挙プロトコル**: Claude Opus が推奨を提示してから Claude Code に伝達

#### テスト件数の推移
- Day1 終了時 13 → Day2 終了時 43 + 1 skipped
- test_mdpi_parser.py (4 件)、test_overrides_contract.py (7 件)、test_journal_audit.py (16 件)、test_integration_149refs.py (3 件) を追加

### Day3 (2026/04/22): Step 6 完了

#### 主要成果
- `journal_audit` モジュールを Stage 5 報告書合成に統合
- 4 層統合レポート (Dashboard / 1.1 MAJOR セクション / 補遺 narrative / sidecar JSON) の確立
- `_classify_reviewer_issues` の MAJOR findings 反映機能

#### 想定外の発見と対処

- **fixture が仕様書ではなく手書きサンプルであった**: Ref #13 エントリの 4 行 elaborate paragraph は、プログラム生成を想定しない手書き例示と判明
- **Level 2-3 境界判定**: 完全な byte 一致 (Level 3) ではなく、汎用テンプレで対応可能な Level 2 シナリオ (α) を採用
- **手順 6-3.5 という予定外の調査ステップ**: 実装中に発覚した問題への対応として、調査フェーズを独立挿入

#### Day3 で確立された主要原則

1. **fixture が仕様書として成立しているかを吟味する**: 「fixture を正とする」原則の適用前に、fixture 自体の性格を批判的吟味
2. **Level 2-3 境界判定**: 二択でなく境界的判断の可能性を提示
3. **原則間 tension の調停**: 「fixture を正とする」vs「stop-and-report (スコープ厳守)」の対立を、両原則の本質を抽出した hybrid 解で解決
4. **既存 API の無改修維持**: 新機能は opt-in パラメタで追加、既存テストの投資を守る

#### テスト件数の推移
- Day2 終了時 43 → Day3 終了時 52 + 1 skipped
- test_journal_audit.py に 6 件追加、test_integration_149refs.py に 3 件追加

### Day4 (2026/04/23): Step 7 完了 + プロジェクト完結処理

#### 前半: Step 7 (CI 基盤整備、3 commit)
- **Step 7a**: `requirements.txt` (pinned-minor 戦略、anthropic は lazy import 前提で除外)
- **Step 7b**: `.github/workflows/tests.yml` (Python 3.11/3.12 必須 + 3.14 実験的併走)
- **Step 7c**: `README.md` (プロジェクト概要、CI badge、149 件ゴールドスタンダード説明)

#### 後半: プロジェクト完結処理 (3 commit)
- **merge**: feature/mdpi-fast-path → main の `--no-ff` merge
- **CHANGELOG**: Keep a Changelog 1.1.0 準拠の初版
- **archive notice**: INTEGRATION_BRIEF.md への "Archived" header (物理移動なし)

#### Day4 で顕在化した重要事象: 指示書の前提誤り 3 件

| # | 誤り | 検出手段 |
|:--:|:---|:---|
| 1 | "11 commits" (正: 12) | `git log main..feature/` |
| 2 | INTEGRATION_BRIEF.md が repo root 直下の前提 | `ls INTEGRATION_BRIEF.md` |
| 3 | integration/ パッケージ構造の未把握 | `ls integration/` + 探索 |

3 件全て Claude Code の事前調査フェーズで実行前に検出された。これにより**「指示書を絶対視せず検証対象として扱う」**運用原則が顕在化。

#### Day4 で確立された主要原則

1. **指示書の前提誤りの累積パターン**: 指示書も検証対象である
2. **プロジェクトには未発見の構造が存在しうる**: integration/ パッケージの存在を 4 日間認識していなかった事実
3. **物理移動 vs 意味論的注記のトレードオフ**: 関連ファイルの処遇が未決の場合は注記を優先 (学術界の supersession notice 慣習との整合)
4. **事前協議プロセスの 5 段階モデル**: (1) 事前調査 (2) 推奨提示 (3) 即決 (4) 統合指示書作成 (5) 事前確認 + 実装

#### 所要時間の特徴
- Step 7 本体: 45-70 分 (想定範囲内)
- 後半タスク: 25-35 分
- 合計 70-105 分 (Day3 の 2.5-3 時間より大幅短縮)
- → **事前協議の成熟度が実装時間を決定する**ことが定量的に確認

### 4 日間通じての最上位原則 (定式化)

Day1-Day4 を通じて繰り返し現れた中核的原則を、抽象度の高い形で 3 項目に集約:

1. **「何を守ろうとしているか」を常に言語化する**: 原則を機械的に適用せず、本質を抽出してから別原則との衝突を調停する
2. **自己認識の限界を前提にする**: Claude Opus の context、Claude Code のローカル環境、先生の組織的コンテクスト — どの 1 つも全体を網羅していない、3 者の相補性で埋める
3. **調査と実装を分離する**: 事実確認、複数案比較・推奨提示、純粋実装の 3 フェーズを明確に分離

### 三者協働モデルの確立

Day4 で「指示書の事実検証」が第 4 役割として顕在化:

| 役割 | Claude Opus | Claude Code | 先生 |
|:---|:---|:---|:---|
| 設計判断 | ◎ (主担当) | 補助的提案 | 最終決定 |
| 意思決定 | 推奨提示 | 補助的提案 | ◎ (主担当) |
| 実装 | - | ◎ (主担当) | - |
| **指示書の事実検証** | - | **◎ (Day4 で顕在化)** | - |
| ローカル環境検証 | - | ◎ | - |
| ドメイン知識提供 | 限定的 | - | ◎ |
| 組織的判断 (ライセンス等) | - | - | ◎ |

---

## 第 3 部: 残存課題と将来計画

### 機能追加候補

1. **プロンプトキャッシュ有効化**: system prompt に引用スタイル例を追加し1200+ トークンにする → 14/15 キャッシュヒットで約70%コスト削減
2. **著者綴り誤りチェック**: PubMed `LastName` と著者引用 surname の fuzzy比較で typo 検出
3. **雑誌省略形の正規化DB**: LLM判断に依存せず NLM LinkOut 等を参照
4. **149 件以外のゴールドスタンダード追加**: Vancouver, AMA, Nature 等の他形式

### 既知の制約

1. **ref #12 で LLM が部分DOI `10.1097` を抽出**: 不完全DOIは Stage 4 で自動スキップ (`_is_valid_doi` の regex で除外)、title+author+year でリカバリ。プロンプト改善余地あり。
2. **仏語タイトルの 50% 一致警告**: ref #5 のフランス語原題と PubMed英訳タイトルで fuzzy 50%。これは正常動作だが「タイトル大幅差異」として査読コメント候補に挙がる。言語別のしきい値分岐は未実装。
3. **149 件 MDPI ゴールドスタンダードの 4 件 known limitations**: manual_overrides.yaml で対処 (ref #66 ジャーナル境界、ref #137 出版社情報保持、ref #141 書籍検出、ref #148 タイトル/ジャーナル分割と smart quote)
4. **manual_overrides の運用負担**: 各 PDF/DOCX で個別に override を作成する必要があり、汎用化は将来課題

### スキル外プロジェクト管理

開発実体は以下のローカルプロジェクトに存在する (本スキルとは別管理):
- パス: `/Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver/`
- 構成: 実装本体 + tests/ + .github/workflows/ + integration/ (archived) + Day1-4 記録
- 詳細: ローカルプロジェクトの `README.md`, `CHANGELOG.md`, Day1-4 記録ファイル参照

ライセンス決定、GitHub remote 追加、integration/ 全体再編は本スキルとは独立した管理タスクとして別途検討予定。

---

## 設計原則の振り返り (Phase 0-4 + Day1-4 統合)

仕様書記載の 5 原則 (YAGNI / 単一責務 / 疑わしきは保持 / 監査可能性 / 人間が最終判断) は Phase 0-4 で確立され、Day1-4 統合計画でさらに以下が追加された:

6. **既存 API の無改修維持**: 新機能は opt-in で追加、過去の投資を守る
7. **fixture を仕様書として吟味**: ゴールドデータの絶対視を避ける
8. **指示書も検証対象**: Day4 で顕在化した第 8 原則

これらは将来の他スキル開発 (lecture-architect、script-generator、paper-summarizer 等) にも転用可能な普遍原則。
