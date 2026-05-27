# Day27 Session Archive (2026-05-24)

## 概要

Day27 セッションは CLAUDE.md §8 (Python 開発環境) 規約整合のため、
依存管理を `requirements.txt` + pip ベースから `pyproject.toml` +
`uv.lock` + uv の single source of truth 方式に移行する config
migration セッション. PyPI 公開 (Day28+ 候補) の前提条件整備 + uv.lock
による依存バージョン完全 lock + CLAUDE.md §8.3 再現性確保 を同時達成.

## 主要成果

| 指標 | Day26 末 | Day27 末 |
|:---|:---:|:---:|
| 全 tests | 111 passed / 0 skipped (`python -m pytest`) | **111 passed / 0 skipped (`uv run pytest`)** |
| 依存管理 | requirements.txt + pip | **pyproject.toml + uv.lock + uv (single source of truth)** |
| Lock file | なし | **uv.lock (358 行、全 transitive deps + hash 完全 lock)** |
| Python version pin | なし | **`.python-version = 3.14`** |
| CI dep install | `pip install -r requirements.txt` | **`uv sync --frozen --group dev` (setup-uv@v6 cache)** |
| PyPI publish 前提 | 未整備 | **`pyproject.toml [project]` metadata 整備済 (Day28+ で package mode 移行)** |
| LLM cost | — | **$0** (config migration のみ) |

## Day27 archive 構成

- `README.md` — 本ファイル (Day27 index)
- `DAY27_LESSONS_LEARNED.md` — Day27 教訓記録 (D27-1, D27-2, D27-3)
- `../../superpowers/specs/2026-05-24-day27-pyproject-uv-migration-design.md` — Day27 spec
- `../../superpowers/plans/2026-05-24-day27-pyproject-uv-migration.md` — Day27 plan

## Day27 commits (chain、4 件)

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `01366a0` | docs(spec) | Day27 pyproject.toml + uv.lock migration spec |
| 2 | `5c9d9b3` | docs(plan) | Day27 implementation plan |
| 3 | `5a1253c` | build(deps) | 6 file atomic migration (pyproject + uv.lock + .python-version + .gitignore + CI workflow + requirements.txt 削除) |
| 4 | (this commit) | docs(sessions) | Day27 archive |

## 設計判断

実装 approach は **Q1 (α) requirements.txt 完全削除 + Q2 (A) hatchling backend (宣言のみ、application mode で未使用) + Q3 (α) PEP 735 [dependency-groups] + Q4 (α) requires-python ">=3.11" + .python-version "3.14" + Q5 (α) astral-sh/setup-uv + uv sync + uv run pytest** を採用 (spec §1.4).

`[tool.uv] package = false` で application mode 維持: 本 repo は CLI application として `python3 main.py` で実行する flat layout (main.py + 各 module が repo root 直下). PyPI publish (Day28+) 時は src/ layout + entry_points 追加で package mode 移行を検討.

## CLAUDE.md §8 規約整合確認

- §8.1: pyproject.toml + uv.lock を single source of truth ✓ (requirements.txt 削除)
- §8.1: pip install 直接実行を avoid ✓ (CI で uv sync --frozen)
- §8.3: 臨床/研究データパイプラインで uv.lock コミット ✓ (uv.lock 追加 + commit)
- §8.2: 標準ツール (ruff, mypy, pytest, Google docstring) — pytest のみ整備、ruff/mypy は Day28+

## Day27 Task 1 code review で発見された Minor 3 件

1. **build(deps) commit body の数え誤り**: "5 file atomic changes" と記載するが実際は **6 ファイル** (`.gitignore` の 1 件が undercount). 機能影響なし、LESSONS で記録.
2. **hatchling 言及だが `[build-system]` 不在**: pyproject.toml に `[build-system]` section なし (application mode、`package = false` で build backend 不要). Commit body の "hatchling backend" 言及は misleading.
3. **`.python-version` 単一情報源化未活用**: CI が matrix 値で Python version 指定、`python-version-file: .python-version` を使えば SoT 化が進む (Day28+ 候補).

## Day28+ 候補

- **Top priority (Day27 で前提条件整備済)**: PyPI 公開 — `[tool.uv] package = true` + src/ layout (`src/pubmed_reference_resolver/`) + `__init__.py` 追加 + `[project.scripts]` で CLI entry point + `[build-system] requires = ["hatchling"]` + `uv build` + `uv publish` で TestPyPI → PyPI 公開
- Latin Extended-A 範囲拡張 (Day26 archive Top priority、`_UPPERCASE_LATIN1` 定数 1 行 update)
- pre-commit hook gitleaks 自動実行 (Day22 handoff パターン 3)
- CONTRIBUTING.md / Issue PR template
- **NEW (Day27 review 発見)**: dev tool 整備 (ruff, mypy in `[dependency-groups.dev]`) — CLAUDE.md §8.2 で標準ツール指定済
- **NEW (Day27 review 発見)**: CI workflow で `python-version-file: .python-version` を使い `.python-version` を SoT 化
- Crossref graceful failure 16 件の対応 (Day22 §6.3 NEW、apa_45refs)
- NLM fuzzy-match precision 改善 (Day22 §6.3 NEW)
- `tools/build_*_fixture.py` の共通 utility refactor (Day23 code review 指摘)
- mdpi_173refs 固有の `manual_overrides.yaml` 構築 (Day24 から継承)
