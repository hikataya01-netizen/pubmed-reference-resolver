# pubmed-reference-resolver

[![tests](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml/badge.svg)](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml)

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
git clone git@github.com:hikataya01-netizen/pubmed-reference-resolver.git
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

現状 **97 passed + 1 skipped** (Day17 末)。
skipped 分は LLM path のシナリオで、`ANTHROPIC_API_KEY` 未設定時にスキップされる設計。

## ゴールドスタンダード fixture (4 系統)

`tests/fixtures/` に 4 系統の golden fixture を配備:

| Fixture | 件数 | スタイル | 由来 | 解決率 |
|:---|---:|:---|:---|---:|
| `mdpi_149refs/` | 149 | MDPI | OneDrive 実機 (Day1-7) | 全件 fast-path |
| `vancouver_24refs/` | 24 | Vancouver/AMA | OneDrive 実機 (Day9) | 22/24 = 91.7% |
| `apa_45refs/` | 45 | APA 7 | PMC OA 3 論文 (Day16) | 25/45 = 55.6% |
| `cell_45refs/` | 45 | Cell Press | PMC OA 3 iScience (Day17) | 30/45 = 66.7% |

Vancouver/APA/Cell は Day9 で導入された **Vancouver Veto** (`is_mdpi_style()` の `\((?:19|20)\d{2}[a-z]?\)` regex) により LLM path に強制 routing される. Day11 で確立された **`expected_*` (deterministic) / `baseline_*` (document-of-record)** ハイブリッド命名規約を踏襲.

`tests/test_integration_149refs.py` (MDPI) で以下を byte 単位で検証:

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
├── crossref_check.py                # Crossref DOI 実在確認 (Day15)
├── nlm_catalog_check.py             # NLM Catalog journal indexing 確認 (Day15)
├── three_class_classifier.py        # PubMed 未ヒット 3 分類 audit (Day15)
├── requirements.txt                 # 依存マニフェスト
├── tools/                           # 開発支援スクリプト群 (Day16-17)
│   ├── build_apa_fixture.py         # APA 7 fixture 生成 (PMC OA → JATS XML → docx)
│   └── build_cell_fixture.py        # Cell-style fixture 生成 (Day16 template 拡張)
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
│   ├── test_integration_vancouver_24refs.py    # Day11
│   ├── test_integration_apa_45refs.py          # Day16
│   ├── test_integration_cell_45refs.py         # Day17
│   ├── test_crossref_check.py                  # Day15
│   ├── test_nlm_catalog_check.py               # Day15
│   ├── test_three_class_classifier.py          # Day15
│   ├── test_overrides_contract.py
│   ├── test_split_references_doi_boundary.py
│   ├── test_pre_integration_baseline.py
│   └── fixtures/
│       ├── mdpi_149refs/
│       ├── vancouver_24refs/                   # Day11
│       ├── apa_45refs/                         # Day16
│       ├── cell_45refs/                        # Day17
│       └── three_class_classification/         # Day15
├── docs/                            # Session 記録 + SPEC アーカイブ (Day6+)
│   ├── sessions/dayN/               # Day6-18 のセッション archive
│   ├── operations/SETUP_API_KEYS.md # Day12
│   └── templates/
├── .github/
│   └── workflows/
│       └── tests.yml
├── SKILL.md                         # Claude Code スキル定義
└── README.md
```
