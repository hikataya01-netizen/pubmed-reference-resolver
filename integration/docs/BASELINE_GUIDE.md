# 基準値取得 (Baseline Characterization) ガイド

本ガイドは、`integration/patches/*` を適用する**前に**、現状の本体スキルが
149 件の References.docx をどう処理するかを計測し、**統合前後の差分を定量
比較できる基準値として固定**する手順を説明します。

---

## なぜ基準値が重要か

統合作業では常に以下の不安が伴います:

> "パッチを当てたら、意図した改善以外に、既存機能が退行していないか?"

基準値があれば、この不安に**定量的に答えられる**ようになります:

- **統合前**: Phase 1 が 147 件検出 (欠落: #40, #140)
- **統合後**: Phase 1 が 149 件検出 (欠落: なし)
- **比較**: +2 件改善、既存の #1-#39, #41-#139, #141-#149 は変化なし

このように「**何が変わり、何が変わっていないか**」を明確にすることで、
統合パッチの効果と安全性を第三者 (レビュアー、将来の自分) に説明できます。

---

## 2 つのアプローチ (併用推奨)

### A. 計測スクリプト (`measure_baseline.py`)

- **用途**: 人間可読な診断レポート (Markdown) の生成
- **出力**: `baseline/baseline_report.md`, `baseline/baseline_phase1.json`
- **利点**: 欠落 refs、異常肥大ブロック、ゴールドとの差分を可視化

### B. pytest (`test_pre_integration_baseline.py`)

- **用途**: 現状の挙動を assertion として固定し、CI で自動チェック
- **出力**: pytest の PASS/FAIL
- **利点**: 統合後に自動的に FAIL することで「改善の証明」になる

---

## 手順

### 前提

- `integration/` パッケージがリポジトリルートに配置済み
- 作業ブランチが `feature/mdpi-fast-path` 等になっている (不要だが推奨)
- パッチは**まだ適用していない**状態

### Step 1: テストデータを配置

```bash
cd ~/claude-skills/pubmed-reference-resolver/

# ゴールドスタンダードを tests/fixtures/ に展開
mkdir -p tests/fixtures
cp -r integration/tests/test_integration_149refs tests/fixtures/mdpi_149refs

# pytest 用の __init__.py
touch tests/__init__.py

# 確認
ls tests/fixtures/mdpi_149refs/
# → input_References.docx
#   expected_phase2_structured.json
#   expected_phase3_resolved.json
#   expected_report.md
#   expected_journal_audit.json
```

### Step 2: 計測スクリプトを配置して実行

```bash
# スクリプトをコピー (名前は自由)
cp integration/tools/measure_baseline.py ./measure_baseline.py

# 実行: テストデータ → 出力先 の順
python3 measure_baseline.py tests/fixtures/mdpi_149refs/ baseline/
```

**期待される出力**:

```
[1/3] Phase 1 を計測中: input_References.docx...
      完了: 147 ブロック検出, 欠落 2 件
[2/3] ゴールドとの比較中...
      ✗ 基準値がゴールドに 2 件不足。欠落 refs: [40, 140]。統合パッチ適用により +2 件の改善が見込まれる
[3/3] レポートを書き出し中...
      JSON: baseline/baseline_phase1.json
      Markdown: baseline/baseline_report.md

✓ 基準値計測完了
```

生成された `baseline/baseline_report.md` を確認してください。
参考形式は `integration/examples/sample_baseline_report.md` を参照。

### Step 3: pytest ベースラインを配置して実行

```bash
cp integration/tests/test_pre_integration_baseline.py tests/

# 実行
python3 -m pytest tests/test_pre_integration_baseline.py -v
```

**期待される出力** (パッチ未適用時):

```
tests/test_pre_integration_baseline.py::TestPhase1CurrentBehavior::test_phase1_runs_without_error PASSED
tests/test_pre_integration_baseline.py::TestPhase1CurrentBehavior::test_phase1_detects_baseline_count PASSED
tests/test_pre_integration_baseline.py::TestPhase1CurrentBehavior::test_phase1_loses_known_refs PASSED
tests/test_pre_integration_baseline.py::TestPhase1CurrentBehavior::test_phase1_oversized_block_contains_merged_ref PASSED
tests/test_pre_integration_baseline.py::TestFixtureIntegrity::test_input_docx_exists PASSED
... (全 11 テスト)
============== 11 passed in 0.59s ==============
```

### Step 4: 基準値をコミット

この時点で、**現状の挙動がテストとレポートで永続化**されました。コミット
しておくことで、将来の差分比較の起点になります:

```bash
git add baseline/ tests/test_pre_integration_baseline.py \
        tests/fixtures/mdpi_149refs/ tests/__init__.py \
        measure_baseline.py
git commit -m "test(baseline): characterize current behavior on 149-ref corpus

Establish a baseline snapshot of main.py's current behavior on the
tests/fixtures/mdpi_149refs/ corpus, prior to MDPI fast-path integration.

Baseline findings (pre-patch):
 - Phase 1 detects 147/149 blocks
 - Refs #40 (van der Biessen) and #140 (van Zyl) are lost
 - Ref #39 is abnormally large (contains merged #40 content)

These characterization tests will fail AFTER the integration patches are
applied, which is the intended signal that improvements have landed.
See docs/BASELINE_GUIDE.md for details.
"
```

---

## 統合後の使い方 (正常フロー)

パッチ適用後に pytest を再実行すると、**意図的に 3 つのテストが FAIL します**:

```bash
# パッチ適用後
python3 -m pytest tests/test_pre_integration_baseline.py -v

# → FAILED: test_phase1_detects_baseline_count
#   (assert 149 == 147)
# → FAILED: test_phase1_loses_known_refs
#   (assert [] == [40, 140])
# → FAILED: test_phase1_oversized_block_contains_merged_ref
#   ("van der Biessen" が #39 に含まれなくなった)
```

この **FAIL は改善の証明**です。失敗した 3 件を確認したら、以下のいずれか:

### オプション 1: 基準値テストを更新 (推奨)

baseline テストファイル内の定数を更新し、新しい期待値に合わせる:

```python
# Before
BASELINE_BLOCKS_DETECTED = 147
BASELINE_MISSING_REFS = [40, 140]

# After
BASELINE_BLOCKS_DETECTED = 149
BASELINE_MISSING_REFS = []
```

また `test_phase1_oversized_block_contains_merged_ref` は、改善後の挙動では
意味を失うため、削除または別の regression 目的のテストに置き換えます。

### オプション 2: `test_post_integration.py` を使う

本パッケージには `integration/tests/test_post_integration.py` として、
統合後の期待値に基づくテストが既に用意されています。これを配置し、
代わりに `test_pre_integration_baseline.py` を削除する運用も可:

```bash
cp integration/tests/test_post_integration.py tests/
rm tests/test_pre_integration_baseline.py
python3 -m pytest tests/test_post_integration.py -v
# → 4 passed (Ref #40 と #140 を含む 149 件が検出される)
```

---

## baseline_report.md の読み方

生成された Markdown レポートには以下の診断が含まれます:

| セクション | 内容 |
|:---|:---|
| **Phase 1 結果** | 検出ブロック数、文字数統計、Ref番号レンジ |
| **⚠ 欠落参照** | 検出されるべきだが見つからない Ref |
| **⚠ 重複検出** | 同じ Ref が複数ブロックに現れる異常 |
| **⚠ 異常に大きいブロック** | 隣接 Ref が統合された疑いのあるブロック |
| **ゴールドとの比較** | 統合後期待値との差分、改善見込み |
| **ブロック先頭サンプル** | 最初の 10 件の実データ |

特に「異常に大きいブロック」は、**#40 が #39 に統合される**ような
サイレントなバグを検出する優れた指標です。本セッションでも:

```
| Ref No | 文字数 |
|:---:|---:|
| #39 | 556 |   ← 平均 237 の 2.3 倍 = #40 が統合されている
```

のように、直ちに異常が見えました。

---

## Phase 2/3 の基準値取得 (応用)

本スクリプトは Phase 1 のみに限定していますが、API キーが利用可能な場合は
Phase 2 (LLM 構造化) の基準値も取れます。拡張したい場合:

```python
# measure_baseline.py に以下を追記
def run_phase2_baseline(blocks, ln_report, main_module, api_key):
    """API キーがあれば LLM 構造化まで走らせる"""
    if not api_key:
        return {"skipped": "no API key"}
    structured = main_module.structure_all_references(
        blocks, ln_report, api_key=api_key, verbose=False
    )
    return {
        "structured_count": len(structured),
        "confidence_breakdown": {
            level: sum(1 for s in structured if s.get("parsing_confidence") == level)
            for level in ("high", "medium", "low")
        },
        "doi_extracted": sum(1 for s in structured if s.get("doi")),
        "is_book_count": sum(1 for s in structured if s.get("is_book")),
    }
```

ただし LLM の出力は非決定的なため、**完全な assertion ではなく範囲チェック**
(例: `high >= 120` のような下限) にするのが現実的です。

---

## チェックリスト

基準値取得が完了したら以下を確認:

- [ ] `measure_baseline.py` が `baseline/baseline_report.md` を生成した
- [ ] レポートに「欠落 Ref #40, #140」が表示されている
- [ ] 「異常に大きいブロック: #39」が表示されている
- [ ] pytest が 11/11 全て PASS する
- [ ] `git add` で基準値ファイル群をコミット済み
- [ ] `git log` で baseline コミットが確認できる

全てクリアしたら、**事前チェック** (PRECHECK_GUIDE.md) と**基準値取得**の
両方が完了した状態です。Claude Code に統合を投げる準備が整いました。

---

## まとめ: 3 段階の安全装置

本統合作業の安全は、以下 3 つの防御線で担保されます:

1. **予行演習** (PRECHECK_GUIDE.md) — パッチが形式的に適用できるかの事前確認
2. **基準値取得** (本ガイド) — 現状の振る舞いを数値と assertion で固定
3. **ゴールドスタンダード** (tests/fixtures/) — 統合後の期待値を具体データで保持

これら 3 つを事前に整えることで、Claude Code への統合依頼が「盲目的な変更」
ではなく、「**定量的に検証可能な改善作業**」になります。

---

**以上**。基準値取得の所要時間は 10-15 分程度です。統合の安全性を大幅に
向上させる投資としてお勧めします。
