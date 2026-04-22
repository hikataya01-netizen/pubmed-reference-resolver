<!--
  NOTE: The CI badge URL below contains a <owner> placeholder.
  When this repository is pushed to GitHub, replace <owner> with the
  actual GitHub account / org name so the badge resolves.
-->

# pubmed-reference-resolver

[![tests](https://github.com/<owner>/pubmed-reference-resolver/actions/workflows/tests.yml/badge.svg)](https://github.com/<owner>/pubmed-reference-resolver/actions/workflows/tests.yml)

査読対象論文の References セクション (PDF / DOCX / TXT) から各文献を PubMed で逆引き検索し、
PubMed 純正互換 CSV + 番号付き abstract text + 統合監査レポートの 3 ファイルを自動生成する
査読支援ツール。

## 主な機能

- PDF / DOCX / TXT からの References セクション抽出
- Vancouver / AMA / APA / Harvard / Chicago / Nature / Cell / MDPI など引用スタイル不問
- PDF コピペ由来の行番号 5 パターン (行頭・行末・行中・数字連結・散在) を統計的に検出・除去
- MDPI 形式は決定論的 fast-path で処理 (LLM API 呼び出しなし、オフライン完走)
- PubMed 未ヒット文献は空行として保持 (通し番号を壊さない)
- 重複引用の複合キー検出 (PMID / DOI / title+author+year)
- 引用ジャーナル名と DOI が指すジャーナルの不整合を MAJOR / WARN / INFO の 3 段階で自動分類
- AI/LLM 捏造引用の検出 (PubMed 未ヒット + DOI 未解決の組合せ)

## インストール

```bash
git clone <repository-url>
cd pubmed-reference-resolver
pip install -r requirements.txt
```

Python 3.11 以上を推奨。CI では 3.11 / 3.12 を必須、3.14 を実験枠で併走。

## 使用方法

### 基本実行

```bash
python main.py input_References.docx
```

### 手動補正を含む実行 (MDPI などの特殊書誌向け)

```bash
python main.py input_References.docx --overrides integration/src/manual_overrides.yaml
```

`--overrides` は明示 opt-in。デフォルトパス検索はせず、別コーパスへの誤適用を防ぐ。

### 出力ファイル

- `report.md` — 統合監査レポート (ダッシュボード + 要確認項目 + 未解決参照詳細 + ジャーナル監査補遺)
- `pubmed_csv-xxx.csv` — PubMed 純正互換 CSV
- `abstract_text-xxx.txt` — 番号付き abstract text
- `journal_mismatch_audit.json` — ジャーナル名監査の機械可読 sidecar

## テスト

```bash
python -m pytest tests/ -q
```

現状 **52 passed + 1 skipped**。skipped 分は LLM path のシナリオで、`ANTHROPIC_API_KEY`
未設定時にスキップされる設計。

## 149 件ゴールドスタンダード

`tests/fixtures/mdpi_149refs/` に MDPI 形式 149 件参照のゴールドスタンダードを配備している。
`tests/test_integration_149refs.py` で以下を byte 単位で検証:

- Phase 2 構造化結果 (`expected_phase2_structured.json`)
- Phase 3 PubMed 解決結果 (`expected_phase3_resolved.json`)
- Phase 5 合成レポート (`expected_report.md`、timestamp 行マスク後)
- ジャーナル監査 sidecar (`expected_journal_audit.json`)
- in-memory 成果物の `stage5_journal_audit` キー存在

GitHub Actions (`.github/workflows/tests.yml`) で Python 3.11 / 3.12 に対して定常検証される。
Python 3.14 は `continue-on-error: true` の実験枠として併走し、将来の Python 移行準備に利用する。

## プロジェクト構成

```
pubmed-reference-resolver/
├── main.py                          # メインパイプライン (Phase 1-5)
├── journal_audit.py                 # ジャーナル名類似度監査モジュール
├── mdpi_parser.py                   # MDPI 形式 fast-path パーサ
├── requirements.txt                 # 依存マニフェスト
├── integration/
│   ├── INTEGRATION_BRIEF.md         # 7 コミット統合計画
│   └── src/
│       ├── manual_overrides.yaml    # 手動補正定義 (149-ref コーパス用)
│       ├── journal_audit.py         # 仕様ベースライン (実装は repo root 側)
│       └── mdpi_parser.py           # 仕様ベースライン (実装は repo root 側)
├── tests/
│   ├── test_mdpi_parser.py
│   ├── test_journal_audit.py
│   ├── test_integration_149refs.py
│   ├── test_overrides_contract.py
│   ├── test_split_references_doi_boundary.py
│   ├── test_pre_integration_baseline.py
│   └── fixtures/
│       └── mdpi_149refs/
├── .github/
│   └── workflows/
│       └── tests.yml
├── SKILL.md                         # Claude Code スキル定義
└── README.md
```
