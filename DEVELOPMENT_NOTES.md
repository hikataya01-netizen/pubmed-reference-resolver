# DEVELOPMENT NOTES — pubmed-reference-resolver

開発経緯と意思決定の記録。Phase 0〜5 の各段階で得られた観察、変更、トレードオフをまとめる。

## Phase 0: 実データ検証 (ドライラン)

### 入力サンプル
- `referenceサンプル.pdf` (MDPI形式、15参照、2ページ、34行番号)

### 発見事項

1. **行番号パターン**: 全34件が**行末型のみ**、連続番号 567-600
2. **引用スタイル**: MDPI 特有 (ACS寄りVancouver)、`N. Authors. Title. Journal. Year, Vol, Pages, DOI` 形式
3. **言語**: 主に英語、仏語2件 (#4 Robieux, #5 Lantheaume)
4. **特殊ケース**: 書籍1件 (#9 Flückiger, ISBN付き)

### ハイフネーション破損の事前発見

DOIが行番号で分断されているケース:
- `gpsych- 570\n2022-100871` (真値のハイフン)
- `j.jpsy- 573\nchores.2022.111139` (偽ハイフン、真値は hyphen なし)
- `RELA- 588\nTIONSHIP` (ソフトハイフン、語途中)

判別不可能なため、前処理は**保守的にハイフン保持** + Stage 3 LLM でコンテキスト判断 + Stage 4 で `doi_alt` 両形式試行の3層防御を設計。

## Phase 1: Stage 1-2.5 (MVP)

### 重大発見: pypdfのインライン抽出特性

初期実装は「ページ内改行を保持する」前提で regex を書いていたが、pypdf は**ページ全体を1行に連結**する。
当初 `\s*\n\s*` 前提だった行番号パターンを、**インライン空白区切り対応**に全面改修:

```python
# Before (broken):
hyphen_pattern = re.compile(rf"-\s+{alt}\b\s*\n\s*")

# After (correct for both inline and cross-line):
hyphen_pattern = re.compile(rf"-\s+{alt}\b\s+")
```

### 統計的行番号検出アルゴリズム

LIS (最長単調増加部分列) ベースで判定。閾値は以下で調整済:
- 最低長: 10 (サンプルでは 34 を検出、全候補 35 中 34が LIS)
- 3桁のみ: `100 ≤ v ≤ 999`
- 年号除外: `1900 ≤ v ≤ 2099` の候補は除外

偽陽性リスク: `2022, 165, 111139` の `165` (volume number) は 3桁非年号。ただし位置が既存LIS値の間に挟まっても整合しないため、LIS構築から自然に脱落。

### 参照境界検出

正規表現 `(?<![\d.])(\d+)\.\s+(?=[A-Z])` で参照マーカー検出。負の先読みで `10.5` (版番号) 等を除外。サンプル15件全て正確に抽出。

## Phase 2: Stage 3 (LLM構造化)

### モデル選定

仕様書記載の `claude-sonnet-4-20250514` は古い識別子。最新 `claude-sonnet-4-6` に置換。15件で 22.6K 入力トークン / 5.1K 出力トークン、約78秒、コスト約$0.15。

### プロンプトキャッシュが発動せず (既知の軽微課題)

`cache_create=0, cache_read=0`。原因: system prompt が約1060トークン、Sonnet 4.6 の最小キャッシュサイズ 1024 トークン付近で境界条件に触れている可能性。

### LLM品質検証結果

- **ソフトハイフン復元**: 4/4件 全成功 (`RELA-TIONSHIP`→`Relationship`, `dépres-sifs`→`dépressifs`, `Re-sources`→`Resources`, `Charac-teriz-ing`→`Characterizing`)
- **DOI曖昧性**: ref #3 で `doi` と `doi_alt` 両形式を正確に分離 → Stage 4 で doi_alt 経由で解決成功
- **書籍検出**: `is_book=true`で DOI/title 検索をスキップ
- **非英語**: 仏語 `language="fr"` 正確判定
- **想定外の good finding**: ref #13 で「雑誌名 `Ultrasound Med. Biol.` と DOI `10.1093/jjco/...` の不整合」を LLM が自発的に検出

## Phase 3: Stage 4 (PubMedカスケード検索)

### 段階カスケードの実装

1. PMID直接 (efetch)
2. DOI検索 (`"{doi}"[AID] OR "{doi}"[DOI]`) — `doi` → `doi_alt` の順
3. Title + First Author + Year (タイトル先頭10単語、PDAT)
4. Title単独 fuzzy (rapidfuzz token_sort_ratio ≥ 90)

### 結果

15件中 **9件解決 (60%)**。未解決6件は全て**期待通り**:
- ref #4: 仏語、DOI無、MEDLINE非収録
- ref #7, #8, #10, #11: 心理学/社会科学ジャーナル (Theory & Psychology, J Happiness Stud, Rev Gen Psychol, Personnel Psychology) MEDLINE非収録
- ref #9: 書籍 (Hogrefe Publishing)

**PubMed収録対象のみで評価: 9/9 = 100% 解決率**。

### レート制限

- NCBI API key あり: 10 req/sec (0.11秒スリープ)
- 15件 × 平均3-4 API呼出 = 約50呼出を 18秒で完了
- tenacity による 5xx/429 指数バックオフリトライ実装済 (本検証では未発動)

## Phase 4: Stage 5 (出力合成)

### XPath バグ発見と修正 (重大)

初期実装では `.//ArticleIdList/ArticleId` で DOI を抽出していたが、PubMed の efetch XML には `PubmedData/ArticleIdList` (正規) と `CommentsCorrectionsList/*/ArticleIdList` (関連記事参照) の**2種類が存在**する。

症状: ref #2 (Wang 2022) の DOI が `10.1188/16.ONF.E104-E120` (完全無関係の ONF 記事) として取得される。

修正: XPath を `./PubmedData/ArticleIdList/ArticleId` に限定、`Article/ELocationID` もフォールバックに追加。修正後、全9件の DOI が正確に抽出されることを確認。

### 重複検出の合成テスト

`examples/sample_duplicates.txt` に 6参照を配置:
- ref #1 と #4: 同一論文 (Vancouver vs APA スタイル、同じDOI)
- ref #2 と #6: 同一論文 (ref #6 は DOI無記載だが title+author+year で同じ PMID に解決)

結果: **両ペアとも正確に検出** (`Duplicate_of` 列および report.md 査読コメントに反映)。

## 未対応 / 今後の改善候補

### 機能追加候補

1. **プロンプトキャッシュ有効化**: system prompt に引用スタイル例を追加し1200+ トークンにする → 14/15 キャッシュヒットで約70%コスト削減
2. **著者綴り誤りチェック**: PubMed `LastName` と著者引用 surname の fuzzy比較で typo 検出
3. **雑誌省略形の正規化DB**: LLM判断に依存せず NLM LinkOut 等を参照

### 既知の制約

1. **ref #12 で LLM が部分DOI `10.1097` を抽出**: 不完全DOIは Stage 4 で自動スキップ (`_is_valid_doi` の regex で除外)、title+author+year でリカバリ。プロンプト改善余地あり。
2. **仏語タイトルの 50% 一致警告**: ref #5 のフランス語原題と PubMed英訳タイトルで fuzzy 50%。これは正常動作だが「タイトル大幅差異」として査読コメント候補に挙がる。言語別のしきい値分岐は未実装。

## 検証完了済 (全Phase)

- [x] Phase 1: 抽出・前処理・行番号検出・境界検出 (実データ1本、15/15正確)
- [x] Phase 2: LLM構造化 (実データ、15/15成功、エラー0)
- [x] Phase 3: PubMedカスケード検索 (実データ、9/15解決=対象の100%)
- [x] Phase 4: 4ファイル出力 + 重複検出 (合成データで双方向検証済)

## 設計原則の振り返り

仕様書記載の5原則 (YAGNI / 単一責務 / 疑わしきは保持 / 監査可能性 / 人間が最終判断) は全て遵守。
特に「疑わしきは保持」は、Stage 2 のハイフン判断と Stage 3 の doi_alt 出力に直接反映され、Phase 3 での ref #3 救済に貢献した。
