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

査読対象論文の References セクション (PDF / DOCX / TXT) の各文献を PubMed で逆引きし、
Word 監査レポート・PubMed 互換 CSV (29 列)・abstract 集の 3 ファイルを生成する。
実在性・書誌正確性・重複・撤回論文を検証し、原著性・エビデンス水準・最新性・
Predatory リスク・主張支持性を評価する査読支援ツール。

## 主な機能

- PDF / DOCX / TXT からの References セクション抽出
- Vancouver / AMA / APA / Harvard / Chicago / Nature / Cell / MDPI など引用スタイル不問
- PDF コピペ由来の行番号 5 パターン (行頭・行末・行中・数字連結・散在) を統計的に検出・除去
- PubMed 未ヒット文献は空行として保持 (通し番号を壊さない)
- 重複引用の複合キー検出 (PMID / DOI / title+author+year)
- 撤回論文検出 (Retraction / Expression of Concern / Erratum を PubMed の `CommentsCorrectionsList` から検出)
- 文献評価 5 基準 (原著性 / エビデンス水準 / 最新性 / Predatory リスク / 主張支持性)
- Word 出力 (`references_audit_report.docx`、`build_docx.js` で生成)
- AI/LLM 捏造引用の検出 (誤マッチ二重ガード: タイトル類似度 + 筆頭著者姓一致)

### 旧版 (main.py)

- MDPI 形式は決定論的 fast-path で処理 (LLM API 呼び出しなし、オフライン完走)
- 引用ジャーナル名と DOI が指すジャーナルの不整合を MAJOR / WARN / INFO の 3 段階で自動分類

## インストール

```bash
git clone git@github.com:hikataya01-netizen/pubmed-reference-resolver.git
cd pubmed-reference-resolver

# 依存同期 (Day27 で uv に移行。pyproject.toml + uv.lock が source of truth)
uv sync --frozen        # テストも実行する場合は --group dev を付ける
npm ci                  # Word レポート生成用 (Node.js 18+)

# API key 設定 (Anthropic + NCBI) — ホーム直下に置けば cwd に関係なく読み込まれる
cp .env.example ~/.pubmed-reference-resolver.env
chmod 600 ~/.pubmed-reference-resolver.env
# REPLACE-WITH-YOUR-KEY を実 key に置換
# 詳細: docs/operations/SETUP_API_KEYS.md

# Claude Code スキルとして登録 (clone した場所はどこでもよい)
mkdir -p ~/.claude/skills
ln -s "$PWD/skill_package" ~/.claude/skills/pubmed-reference-resolver

# 環境診断 (✘ が出たら → の手順で直して再実行)
tools/doctor.sh
```

### 別のパソコンへの展開・動かなくなったとき

API キーと `.venv` は git 管理外のため、パソコンごとに用意する。

1. `git pull` → `uv sync --frozen`
2. `~/.pubmed-reference-resolver.env` を配置 (`chmod 600`)
3. `~/.claude/skills/pubmed-reference-resolver` → `skill_package/` の symlink を確認
4. `tools/doctor.sh` で全項目 ✔ を確認 (外部通信を避けるなら `--offline`)

Python 3.11 以上を推奨。CI では 3.11 / 3.12 を必須、3.14 を実験枠で併走。

## 使用方法

References を PubMed で構造化した `refs.json` を用意する (SKILL.md「実行方法」の手順・
`references/llm_parsing_prompt.md` 参照)。

```bash
uv run python audit.py --structured refs.json -o out/
```

出力は `out/` 配下に固定 3 ファイル (`references_audit_report.docx` / `references_pubmed.csv` /
`references_abstracts.txt`) と補助 JSON (`resolved.json` / `issues.json` / `report_data.json`)。

- `--offline` — 雑誌収載状況照会 (NLM Catalog/DOAJ) をスキップし、Predatory リスク・収載状況を「未評価」にする
- `--reuse-resolved out/resolved.json` — 過去実行の解決結果を再利用し PubMed 照合をスキップ (NCBI 通信ゼロ)
- `--claim-support claim_support.json` — 主張支持性判定 JSON を用いた 2 パス目の実行 (`--reuse-resolved` と併用)

### 出力ファイル

- `references_audit_report.docx` — Word 監査レポート (ダッシュボード + 要確認項目 + 文献評価サマリ等 7 セクション)
- `references_pubmed.csv` — PubMed 互換 CSV (UTF-8 BOM・29 列)
- `references_abstracts.txt` — 番号付き abstract text (78 字幅ラップ)
- `resolved.json` / `issues.json` / `report_data.json` — 各段階の中間結果 (再実行・監査用)

### 旧版 (非推奨)

```bash
uv run python main.py input_References.docx -o out/
uv run python main.py input_References.docx -o out/ --overrides integration/src/manual_overrides.yaml
```

`--overrides` は明示 opt-in。デフォルトパス検索はせず、別コーパスへの誤適用を防ぐ。
Phase 1-2 (抽出・行番号除去) のみ v2 から再利用され、Phase 2-4 (LLM 構造化・`report.md` 出力) は非推奨。

## テスト

```bash
uv run pytest tests/ -q
```

現状 **134 passed + 0 skipped** (2026-09-14)。v2 パイプライン (`pipeline/`, `audit.py`) のテストは
`tests/v2_replay.py` による NCBI/DOAJ 応答の記録再生方式で、ネットワーク・API key 不要。
旧版 main.py のテストは Day23 で旧 mdpi_149refs fixture 削除に伴い module-level skip されていた
5 file を Day24 で新 mdpi_173refs に re-point して skip 解除済み。
全テストは API key・ネットワーク不要でオフライン完走する (外部 API 呼び出しは fixture で DI 注入)。

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
├── audit.py                         # v2 正規エントリポイント
├── pipeline/                        # v2: resolve / enrich / consistency / assess / outputs
├── build_docx.js                    # v2: 出力① Word レポート生成 (docx-js)
├── package.json + package-lock.json # v2 Node.js 依存マニフェスト (npm ci)
├── main.py                          # 旧版パイプライン (Phase 1-5)。v2 は Phase 1-2 (抽出) のみ再利用
├── journal_audit.py                 # 旧版: ジャーナル名類似度監査モジュール
├── mdpi_parser.py                   # 旧版: MDPI 形式 fast-path パーサ
├── crossref_check.py                # 旧版: Crossref DOI 実在確認 (Day15)
├── nlm_catalog_check.py             # 旧版: NLM Catalog journal indexing 確認 (Day15)
├── three_class_classifier.py        # 旧版: PubMed 未ヒット 3 分類 audit (Day15)
├── pyproject.toml + uv.lock         # Python 依存マニフェスト (Day27 で requirements.txt から移行)
├── tools/                           # 開発支援スクリプト群
│   ├── doctor.sh                               # 環境診断 (Python/Node.js/API key/スキル登録/疎通)
│   ├── record_v2_fixture.py                    # v2: NCBI/DOAJ 応答の記録・fixture 再生成 (実通信)
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
│   ├── test_v2_pipeline.py                     # v2: pipeline/ 各段の単体・結合テスト
│   ├── test_v2_env.py                          # v2: audit.py の .env 探索順テスト
│   ├── v2_replay.py                            # v2: NCBI/DOAJ 応答の記録再生ヘルパー (テストではない)
│   ├── test_mdpi_parser.py                     # Day24: mdpi_173refs に re-point して skip 解除
│   ├── test_journal_audit.py                   # Day24: 同上
│   ├── test_pre_integration_baseline.py        # Day24: 同上
│   ├── test_split_references_doi_boundary.py   # Day24: 同上
│   ├── test_overrides_contract.py              # Day24: 同上
│   ├── test_integration_mdpi_173refs.py        # Day23 (新)
│   ├── test_integration_vancouver_35refs.py    # Day23 (新)
│   ├── test_integration_apa_45refs.py          # Day16
│   ├── test_integration_cell_45refs.py         # Day17
│   ├── test_crossref_check.py                  # Day15
│   ├── test_nlm_catalog_check.py               # Day15 (Day22 で certifi SSL fix の regression guard 追加)
│   ├── test_three_class_classifier.py          # Day15
│   ├── test_env_loader.py                      # Day8
│   └── fixtures/
│       ├── v2_synthetic_7refs/                 # v2 回帰テスト用の合成 7 件と記録応答
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
├── skill_package/                   # Claude Code スキル配布パッケージ (repo root への symlink 集)
│   ├── SKILL.md                     # Claude Code スキル定義
│   ├── DEVELOPMENT_NOTES.md
│   ├── audit.py / pipeline / build_docx.js           # repo root への symlink (v2)
│   ├── main.py / mdpi_parser.py / journal_audit.py / manual_overrides.yaml  # repo root への symlink (旧版)
│   ├── examples/ + references/
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
