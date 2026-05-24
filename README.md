# pubmed-reference-resolver

[![tests](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml/badge.svg)](https://github.com/hikataya01-netizen/pubmed-reference-resolver/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Table of Contents

- [主な機能](#主な機能)
- [インストール](#インストール)
- [使用方法](#使用方法)
- [テスト](#テスト)
- [ゴールドスタンダード fixture (4 系統)](#ゴールドスタンダード-fixture-4-系統)
- [プロジェクト構成](#プロジェクト構成)
- [License](#license)
- [Acknowledgments](#acknowledgments)

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

# API key 設定 (Anthropic + NCBI)
cp .env.example .env
# .env を編集して REPLACE-WITH-YOUR-KEY を実 key に置換
# 詳細: docs/operations/SETUP_API_KEYS.md
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

現状 **52 passed + 50 skipped** (Day23 末)。
50 skipped の内訳: 5 file (test_mdpi_parser / test_overrides_contract / test_journal_audit / test_pre_integration_baseline / test_split_references_doi_boundary) が module-level pytestmark.skip 付与済 (Day23 で旧 mdpi_149refs fixture を削除した影響、新 mdpi_173refs に re-point + skip 解除は Day24+ 候補)。1 skipped は LLM path シナリオで `ANTHROPIC_API_KEY` 未設定時にスキップされる設計分。

## ゴールドスタンダード fixture (4 系統)

`tests/fixtures/` に 4 系統の golden fixture を配備 (全て PMC OA CC BY 4.0 由来、Day23 で機密性懸念のあった旧 fixture 2 件を全 git history から消去し PMC OA 由来に置換):

| Fixture | 件数 (parsed) | スタイル | 由来 | 解決率 |
|:---|---:|:---|:---|---:|
| `mdpi_173refs/` | 173 (171) | MDPI | [PMC13164670](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13164670/) Nutrients review 2026 (Day23) | 159/171 = 93.0% |
| `vancouver_35refs/` | 35 (31) | Vancouver/AMA | [PMC13179246](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC13179246/) Supportive Care in Cancer 2026 (Day23) | 22/31 = 71.0% |
| `apa_45refs/` | 45 | APA 7 | PMC OA 3 論文 (Day16) | 25/45 = 55.6% |
| `cell_45refs/` | 45 | Cell Press | PMC OA 3 iScience (Day17) | 30/45 = 66.7% |

全 fixture が Day9 で導入された **Vancouver Veto** (`is_mdpi_style()` の `\((?:19|20)\d{2}[a-z]?\)` regex) または同等の判定により LLM path に routing される (新 mdpi_173refs は MDPI publisher 由来だが author 形式が fast-path 条件を満たさず LLM 経由). Day11 で確立された **`expected_*` (deterministic) / `baseline_*` (document-of-record)** ハイブリッド命名規約を踏襲.

各 fixture には `input_References.docx` + `expected_phase1_intermediate.json` + `baseline_phase3_resolved.json` + `baseline_report.md` + `baseline_three_class_classification.json` + `README.md` (出典明示) の 6 file が配置される. 詳細は各 fixture の `README.md` を参照.

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
├── tools/                           # 開発支援スクリプト群 (Day16-23)
│   ├── build_apa_fixture.py                    # APA 7 fixture 生成 (Day16, PMC OA → JATS XML → docx)
│   ├── build_cell_fixture.py                   # Cell-style fixture 生成 (Day17, Day16 template 拡張)
│   ├── build_vancouver_replacement_fixture.py  # Vancouver/AMA fixture 生成 (Day23)
│   └── build_mdpi_replacement_fixture.py       # MDPI fixture 生成 (Day23)
├── integration/
│   ├── INTEGRATION_BRIEF.md         # 7 コミット統合計画 (歴史資料、新 mdpi_173refs と直接連動せず)
│   └── src/
│       ├── manual_overrides.yaml    # 手動補正定義 (旧 149-ref コーパス時代の仕様、Day24+ 再評価対象)
│       ├── journal_audit.py         # 仕様ベースライン (実装は repo root 側)
│       └── mdpi_parser.py           # 仕様ベースライン (実装は repo root 側)
├── tests/
│   ├── test_mdpi_parser.py                     # Day23: pytestmark.skip 付与 (新 mdpi_173refs re-point は Day24+)
│   ├── test_journal_audit.py                   # Day23: 同上 (mdpi_149refs 依存)
│   ├── test_pre_integration_baseline.py        # Day23: 同上
│   ├── test_split_references_doi_boundary.py   # Day23: 同上
│   ├── test_overrides_contract.py              # Day23: 同上
│   ├── test_integration_mdpi_173refs.py        # Day23 (新)
│   ├── test_integration_vancouver_35refs.py    # Day23 (新)
│   ├── test_integration_apa_45refs.py          # Day16
│   ├── test_integration_cell_45refs.py         # Day17
│   ├── test_crossref_check.py                  # Day15
│   ├── test_nlm_catalog_check.py               # Day15 (Day22 で certifi SSL fix の regression guard 追加)
│   ├── test_three_class_classifier.py          # Day15
│   ├── test_env_loader.py                      # Day8
│   └── fixtures/
│       ├── mdpi_173refs/                       # Day23 (新、PMC13164670 Nutrients CC BY 4.0)
│       ├── vancouver_35refs/                   # Day23 (新、PMC13179246 Supportive Care in Cancer CC BY 4.0)
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

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Hideki Katayama

## Acknowledgments

このプロジェクトは以下の OSS と公開リソースに依存する:

- **NCBI E-utilities** (PubMed / PMC / NLM Catalog) — bibliographic information retrieval
- **Crossref REST API** — DOI 実在確認 (Day15 で導入された 3 分類 audit logic で使用)
- **Anthropic Claude Sonnet 4.6** — LLM-path での reference 構造化
- **PMC Open Access subset** — fixture data (CC BY 4.0 採用 3 系統 = vancouver/apa/cell). 各 fixture の `tests/fixtures/*/README.md` で source paper citation を明示.

開発期間中 (Day1-19) は **Claude Code (Sonnet 4.6)** および **Claude Opus 4.7 (1M context)** が共同作業者として参画した. 全 commit の `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` trailer はその記録.
