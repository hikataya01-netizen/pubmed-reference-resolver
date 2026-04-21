# pubmed-reference-resolver 統合パッケージ (v5: 先生の実環境専用版)

**重要**: 本パッケージは先生が 2026-04-20 にアップロードされた実際の main.py
(70,734 bytes, 1823行) を基に再生成されました。`load_env_files()` 等の先生
独自機能を含む現行バージョンに対して、両パッチとも `git apply --check` で
事前検証済みです。

## 即座に使うには

```bash
cd "/Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver"

# feature/mdpi-fast-path ブランチにいることを確認
git status    # clean であること

# 古い integration/ を削除 (もしあれば)
rm -rf integration/

# v5 を展開
unzip ~/Downloads/pubmed-resolver-integration-v5.zip

# 予行演習 (両方とも 0 になるはず)
git apply --check integration/patches/01_split_references_fix.patch
echo "Patch 01: $?"

git apply --check integration/patches/02_mdpi_fast_path.patch
echo "Patch 02: $?"
```

終了コードが両方 `0` なら本セッションにご報告ください。

## 構成 (v3/v4 と共通)

```
integration/
├── README.md                       ← 本ファイル
├── INTEGRATION_BRIEF.md            ← 統合計画の設計書
├── docs/
│   ├── PRECHECK_GUIDE.md           ← 予行演習ガイド
│   ├── BASELINE_GUIDE.md           ← 基準値取得ガイド
│   └── CLAUDE_CODE_PROMPT.md       ← Claude Code 投入プロンプト集
├── src/
│   ├── mdpi_parser.py              ← MDPI 形式専用パーサ (本体に展開される)
│   ├── journal_audit.py            ← Journal 監査モジュール (未統合, 次回用)
│   └── manual_overrides.yaml       ← 原稿個別補正テンプレート
├── patches/
│   ├── 01_split_references_fix.patch   ← 先生の main.py 専用版
│   └── 02_mdpi_fast_path.patch         ← 先生の main.py 専用版
├── tests/
│   ├── test_mdpi_parser.py
│   ├── test_pre_integration_baseline.py
│   ├── test_post_integration.py
│   └── test_integration_149refs/   ← 149件ゴールドデータ
├── tools/
│   ├── measure_baseline.py
│   └── verify_integration.sh
└── examples/
    ├── sample_baseline_phase1.json
    └── sample_baseline_report.md
```

## v4 → v5 の変更点

- `patches/01_split_references_fix.patch`: 行番号を先生の実 main.py に合わせて再生成
- `patches/02_mdpi_fast_path.patch`: 同上
- 他のファイルは v4 と同一

## 検証済み事項

- 先生の main.py (70,734 bytes, 1823行) + v5 パッチ → `git apply --check` 両方 0
- 適用後の main.py + mdpi_parser.py → Python 構文 OK
- API キーなしで References.docx 149 件 → Phase 1 完全検出 + Phase 2 high=128
