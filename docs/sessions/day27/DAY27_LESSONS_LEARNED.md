# Day27 Lessons Learned (2026-05-27)

## §1 概要

Day27 は CLAUDE.md §8 (Python 開発環境) 規約との乖離を解消するため、
依存管理を `requirements.txt` + pip ベースから `pyproject.toml` + `uv.lock` +
uv の single source of truth 方式に移行する config migration セッション.

### §1.1 セッション開始時の状態

- **111 passed / 0 skipped** (Day26 末、`python -m pytest`)
- 依存管理: `requirements.txt` + pip (CLAUDE.md §8.1 違反状態)
- Lock file: なし (CLAUDE.md §8.3 違反状態 — 再現性未確保)
- Python version pin: なし
- CI: `pip install -r requirements.txt` (uv 未使用)
- CLAUDE.md §8 は Day23 spec §C5 で "Day24+ 候補" として記録されていたが、
  Day23-26 で他優先事項を先行、Day27 でようやく着手

### §1.2 セッション終了時の状態

- **111 passed / 0 skipped** (`uv run pytest`、parser/test 内容不変)
- 依存管理: `pyproject.toml` + `uv.lock` + uv (single source of truth) ✓
- Lock file: `uv.lock` (358 行、全 transitive deps + hash 完全 lock) ✓
- Python version pin: `.python-version = 3.14` ✓
- CI: `astral-sh/setup-uv@v6` + `uv sync --frozen --group dev` + `uv run pytest` ✓
- `[project]` metadata 整備済み (Day28+ の PyPI publish 前提条件達成) ✓
- **LLM cost: $0** (config migration のみ、parser logic 不変)

---

## §2 brainstorming 段階

Day27 spec §1.4 で 5 つの設計 Question (Q1-Q5) を brainstorm し、各 Option を
評価した上で採用案を確定した.

### §2.1 Q1: requirements.txt の処置

| Option | 概要 | 採用可否 | 不採用理由 |
|:---|:---|:---:|:---|
| **(α) 完全削除** ✓ | requirements.txt を削除、pyproject.toml + uv.lock に一本化 | **採用** | Single source of truth 達成。二重管理の drift リスク除去 |
| **(β) 併存** | requirements.txt を残しつつ pyproject.toml も追加 | ✕ | 二重管理が残存。"Which file is canonical?" 問題が再発 |
| **(γ) 変換のみ** | requirements.txt を pyproject.toml に変換、uv.lock 追加なし | ✕ | Lock file なしでは §8.3 再現性確保を達成できない |

### §2.2 Q2: build backend の選択

| Option | 概要 | 採用可否 | 不採用理由 |
|:---|:---|:---:|:---|
| **(A) hatchling 宣言 (未使用)** ✓ | `[build-system]` section を追加、hatchling 宣言。application mode (`package=false`) で実質未使用 | **採用** | PyPI publish Day28+ で `package=true` に切替時にそのまま活用可能 |
| **(B) 宣言なし** | `[build-system]` なし、純粋な application mode | ✕ | Day28+ の PyPI publish 移行時に追加作業が発生 |
| **(C) flit/setuptools** | 別の build backend | ✕ | hatchling が uv ecosystem と最も親和性高い |

**注意**: Task 1 code review で "Q2 で hatchling を宣言したが実際の `pyproject.toml` に
`[build-system]` section が存在しない" という矛盾が発見された. `[tool.uv] package = false`
(application mode) では build backend は不要で自動省略. Commit body の "hatchling backend"
言及は misleading であった (D27-3 参照).

### §2.3 Q3: dependency-groups vs optional-dependencies

| Option | 概要 | 採用可否 | 不採用理由 |
|:---|:---|:---:|:---|
| **(α) PEP 735 dependency-groups** ✓ | `[dependency-groups.dev]` に pytest 等を配置 | **採用** | PyPI metadata 清浄 (エンドユーザーに dev deps が露出しない)。uv-native |
| **(β) optional-dependencies** | `[project.optional-dependencies.dev]` に配置 | ✕ | PyPI extras として公開され、エンドユーザーが `pip install .[dev]` 可能になる。dev tool は extras にすべきでない |
| **(γ) requirements-dev.txt 継続** | 既存 requirements.txt を dev 用に分割 | ✕ | Lock file なし問題が残存 |

### §2.4 Q4: Python version 指定

| Option | 概要 | 採用可否 | 不採用理由 |
|:---|:---|:---:|:---|
| **(α) >=3.11 + .python-version=3.14** ✓ | requires-python で下限、.python-version で local/CI pin | **採用** | CLAUDE.md §8.1 "3.11 以上を推奨。.python-version で固定" に完全準拠 |
| **(β) ==3.11** | 厳密 pin | ✕ | 将来バージョンへの追随コストが高い |
| **(γ) >=3.8** | 広い互換範囲 | ✕ | modern syntax (match-case 等) を使いたい場合に制約になる |

### §2.5 Q5: CI dep install 方式

| Option | 概要 | 採用可否 | 不採用理由 |
|:---|:---|:---:|:---|
| **(α) astral-sh/setup-uv + uv sync** ✓ | setup-uv@v6 でキャッシュ、`uv sync --frozen --group dev` で完全 lock install | **採用** | `--frozen` で uv.lock の再現性を CI で保証。speed + reliability 最高 |
| **(β) pip install -e .** | setuptools 経由 | ✕ | lock file を活用しない。再現性保証なし |
| **(γ) conda/mamba** | conda 環境 | ✕ | プロジェクト標準と乖離、CI 設定が複雑化 |

---

## §3 実装段階の経緯

### §3.1 Day27 commit chain

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `01366a0` | docs(spec) | Day27 pyproject.toml + uv.lock migration spec |
| 2 | `5c9d9b3` | docs(plan) | Day27 implementation plan |
| 3 | `5a1253c` | build(deps) | 6 file atomic migration |
| 4 | (archive) | docs(sessions) | Day27 archive |

### §3.2 Task 1 sub-step 細分化

Task 1 (build(deps) commit) は以下 7 sub-steps で実行:

| Sub | 内容 | 主要ファイル |
|:---:|:---|:---|
| A | pyproject.toml 新規作成 (`[project]`, `[tool.uv]`, `[dependency-groups]`) | `pyproject.toml` |
| B | .python-version 新規作成 (`3.14`) | `.python-version` |
| C | .gitignore に `.venv/` 追記 | `.gitignore` |
| D | uv sync 実行 → uv.lock 自動生成 (358 行) | `uv.lock` |
| E | requirements.txt 削除 | ~~`requirements.txt`~~ |
| F | CI workflow (.github/workflows/tests.yml) uv 化 | `.github/workflows/tests.yml` |
| G | `uv run pytest` 検証 (111 passed) + atomic commit + push | — |

---

## §4 設計判断と検証

### §4.1 application mode (`package = false`) vs package mode

`[tool.uv] package = false` (application mode) を維持:

- **現状**: `python3 main.py` で実行する flat layout CLI application. `main.py` + 各 module が repo root 直下に配置
- **application mode の利点**: src/ layout 移行不要、import path 変更不要、`[build-system]` 不要
- **package mode への移行 path (Day28+)**:
  1. `[tool.uv] package = true` に変更
  2. `src/pubmed_reference_resolver/` layout に移行
  3. `__init__.py` 追加
  4. `[project.scripts]` で CLI entry point 宣言 (`pubmed-resolver = "pubmed_reference_resolver.main:main"`)
  5. `[build-system] requires = ["hatchling"]` 追加
  6. `uv build` → `uv publish` で TestPyPI → PyPI 公開

### §4.2 PEP 735 `[dependency-groups]` の選択

- **意図**: dev/test 専用 deps (pytest, pytest-mock 等) を PyPI metadata から分離
- **uv コマンド**: `uv sync --group dev` でインストール、`uv add --group dev <pkg>` で追加
- **エンドユーザー向け extras との使い分け**:
  - `[dependency-groups.dev]` → dev tool のみ。PyPI 公開後もエンドユーザーに露出しない
  - `[project.optional-dependencies.extra]` → `pip install pubmed-resolver[extra]` でエンドユーザーが選択可能にしたい場合に使用

### §4.3 `setup-uv@v6` + `setup-python` 併用の理由

- `setup-uv` の role: uv binary のインストール + `.venv` キャッシュ
- `setup-python` の role: matrix Python version (3.11, 3.12, 3.14) の切替
- `--frozen` flag の意義: CI 実行時に `uv.lock` を更新せず、lock された内容を忠実にインストール → **再現性保証**

### §4.4 `.python-version = 3.14` の選択理由

- local 開発環境が 3.14 を使用 (`python3 --version` で確認)
- CI matrix に 3.14 (experimental) を含む構成を維持
- CLAUDE.md §8.1 "Python バージョン: 3.11 以上を推奨。`.python-version` ファイルで固定" に準拠

---

## §5 実機検証

| 検証項目 | 結果 |
|:---|:---|
| test count (Day26 末) | 111 passed / 0 skipped (`python -m pytest`) |
| test count (Day27 末) | 111 passed / 0 skipped (`uv run pytest`) |
| test 内容変更 | なし (config migration のみ) |
| `uv sync` resolve | 13 packages in lockfile, 11 installed (2 already-installed) |
| `uv.lock` size | 358 行 (全 transitive deps + hash 完全 lock) |
| `uv run pytest` 実行時間 | 約 0.39s (test suite 自体は高速) |
| `uv sync --frozen` idempotency | `Checked 11 packages in 0.59ms` (再実行で変更なし) |
| CI status for `5a1253c` | green (build(deps) commit で CI 通過確認) |
| gitleaks | no leaks found (127 commits scanned) |
| repo visibility | PUBLIC |

---

## §6 教訓

### D27-1: Global 規約は関連タスク着手時に同時整合するのが理想

**事象**: CLAUDE.md §8 (uv 使用規約) は Day23 spec §C5 で "Day24+ 候補" として記録され、
4 セッション (Day23-26) にわたって後回しにされた. Day27 でようやく着手.

**学び**: Global 規約 (CLAUDE.md 等) との乖離は「気持ち悪い」状態が累積する.
Python 依存管理を扱う最初の機会 (Day23 filter-repo 導入、Day22 requirements.txt 更新等) に
同時整理する判断が理想であった. 「規約整合は後でまとめて」という先送りパターンは
技術的負債として蓄積する.

**適用範囲**: プロジェクト内の任意の config migration. 特に CLAUDE.md に明示された
標準化ツール (uv, ruff, mypy 等) の採用は "first opportunity" で実施すること.

---

### D27-2: `dependency-groups` と `optional-dependencies` の用途分離

**事象**: pyproject.toml に pytest を追加する際、`[dependency-groups.dev]` (PEP 735) と
`[project.optional-dependencies.dev]` のどちらを使うか判断が必要だった.

**学び**:
- `[dependency-groups]` (PEP 735): **dev-only deps の標準**. PyPI metadata に含まれない.
  uv-native. `uv sync --group dev` でインストール. エンドユーザーには不可視.
- `[project.optional-dependencies]`: **エンドユーザー向け extras の標準**.
  `pip install package[extra]` で選択可能にしたい deps に使用.
  例: `[gpu]`, `[full]`, `[pdf]` 等.

**適用範囲**: pyproject.toml を新規作成・編集する全 Python プロジェクト. dev tool (pytest,
ruff, mypy, pre-commit 等) は必ず `[dependency-groups.dev]` に配置し、
`optional-dependencies` は PyPI エンドユーザー向けの機能拡張にのみ使用する.

---

### D27-3: Application mode vs package mode の設計意図を commit message に明示する

**事象**: Task 1 commit body に "hatchling backend" と記載したが、実際の `pyproject.toml`
に `[build-system]` section は存在しない. `[tool.uv] package = false` (application mode)
では build backend は不要であり、hatchling を宣言していない構成になっていた.
code review で「commit body の言及と実コードの乖離」として発見.

**学び**:
- `[tool.uv] package = false` = application mode: build backend 不要. CLI tool として
  `python3 main.py` で直接実行する flat layout に適切.
- `[tool.uv] package = true` = package mode: `[build-system]` + dist 生成が必要.
  PyPI 公開 (Day28+) 時に移行.
- Commit message で設定の **意図** を正確に記述する: "application mode (no build backend)"
  vs "package mode (hatchling backend)" の区別を明示する.

**適用範囲**: pyproject.toml の `[tool.uv]` 設定変更を含む commit. 特に `package = false/true`
の切替は downstream への影響が大きいため、commit body に意図と影響範囲を明記する.

---

## §7 残存タスク (Day28+ 候補)

| 優先度 | タスク | 備考 |
|:---|:---|:---|
| **Top priority** | PyPI 公開 | Day27 で `[project]` metadata 整備済. `package=true` + src/ layout + entry_points + `uv build` + `uv publish` で v0.2.0 候補 |
| High | Latin Extended-A 範囲拡張 | Day26 archive Top priority. `_UPPERCASE_LATIN1` 定数 1 行 update のみ |
| High | pre-commit hook gitleaks 自動実行 | Day22 handoff パターン 3 |
| Medium | **NEW** dev tool 整備 (ruff, mypy) | CLAUDE.md §8.2 標準ツール. `[dependency-groups.dev]` に追加、CI job 追加 |
| Medium | **NEW** CI で `python-version-file: .python-version` を使用 | `.python-version` を SoT 化. setup-python の matrix 値を廃止 |
| Medium | CONTRIBUTING.md / Issue PR template | OSS 整備 |
| Low | Crossref graceful failure 16 件対応 | Day22 §6.3 NEW、apa_45refs |
| Low | NLM fuzzy-match precision 改善 | Day22 §6.3 NEW |
| Low | `tools/build_*_fixture.py` 共通 utility refactor | Day23 code review 指摘 |
| Low | mdpi_173refs 固有の `manual_overrides.yaml` 構築 | Day24 から継承 |

---

## §8 次セッション再開プロンプトテンプレート

### パターン 1 (推奨): PyPI 公開準備 (package mode 移行)

```
Day27 が終了している状態から再開。
HEAD は docs(sessions) archive commit (Day27 Task 2)。
全 tests: 111 passed / 0 skipped (uv run pytest)。

Day28 タスクとして PyPI 公開準備を実施:
  - [tool.uv] package = true に変更
  - src/pubmed_reference_resolver/ layout 移行
  - __init__.py 追加
  - [project.scripts] で CLI entry point 宣言
  - [build-system] requires = ["hatchling"] 追加
  - uv build → dist/ 生成確認
  - TestPyPI publish (uv publish --index testpypi)
  - (確認後) PyPI publish

TDD で進め、各 step を確認しながら進めること。
```

### パターン 2: Latin Extended-A 範囲拡張

```
Day27 が終了している状態から再開。
HEAD は docs(sessions) archive commit (Day27 Task 2)。
全 tests: 111 passed / 0 skipped (uv run pytest)。

Day28 タスク: Latin Extended-A 範囲拡張 (Day26 archive Top priority)。
main.py の _UPPERCASE_LATIN1 定数 (現在 "A-ZÀ-ÖØ-Þ") を
Latin Extended-A (U+0100-U+017E) まで拡張する。
TDD で進める: まず failing test を追加、次に定数 1 行 update で GREEN にする。
```

### パターン 3: pre-commit hook gitleaks 自動実行

```
Day27 が終了している状態から再開。
HEAD は docs(sessions) archive commit (Day27 Task 2)。
全 tests: 111 passed / 0 skipped (uv run pytest)。

Day28 タスク: pre-commit hook で gitleaks を自動実行 (Day22 handoff パターン 3)。
.pre-commit-config.yaml を新規作成し、gitleaks の pre-commit hook を設定する。
gitleaks は brew でインストール済み。
CI workflow にも pre-commit check job を追加する。
```
