# SPEC: Day27 — `pyproject.toml` + `uv.lock` 移行 (requirements.txt 廃止)

**作成日**: 2026-05-24 (Day27 brainstorming 完了時)
**著者**: Claude Code (Opus 4.7 / 1M context) / 承認: 片山英樹
**位置付け**: CLAUDE.md §8 (Python 開発環境) 規約と整合させるため、現状 `requirements.txt` ベースの依存管理を **`pyproject.toml` + `uv.lock` を single source of truth とする uv-native 方式** に移行する。PyPI 公開 (Day28+ 候補) の前提条件整備 + uv.lock による依存バージョン完全 lock + CLAUDE.md §8.3 の再現性確保 を同時達成。
**前提**: Day26 末 (HEAD `87062c3`、Day26 archive 含む) で main branch、111 passed / 0 skipped / 0 failed、repo PUBLIC、CI green、v0.1.0 release accessible、gitleaks clean

---

## 1. 背景と目的

### 1.1 CLAUDE.md §8 規約との乖離

CLAUDE.md (ユーザー global instruction) §8 で以下が明記されている:

- §8.1: 「Python プロジェクトでは原則として **uv** を使用する。`pyproject.toml` および `uv.lock` を単一の真実の情報源 (single source of truth) とし、依存関係の追加・削除・同期はすべて uv 経由で行う」
- §8.1: 「`pip install` の直接実行は原則として避ける」
- §8.3: 「臨床データ・研究データを扱う Python パイプラインでは、`uv.lock` を Git にコミットし、依存バージョンの再現性を確保する」

本 repo (pubmed-reference-resolver) は査読支援パイプラインで CLAUDE.md §8.3 該当だが、現状:
- `requirements.txt` ベース (CLAUDE.md §8.1 と乖離)
- `uv.lock` 不在 (再現性なし、§8.3 違反)
- CI も `pip install -r requirements.txt` (§8.1 違反)

Day23 spec §C5 で既に Day24+ 候補入りしていたが、Day23-26 で他の優先事項 (filter-repo / 5 test refactor / split_references fix / DRY refactor) を進めたため後回しになっていた。Day27 で着手。

### 1.2 移行の効用

1. **CLAUDE.md §8 規約準拠**: pyproject.toml + uv.lock を single source of truth、pip install 直接実行を廃止
2. **uv.lock による再現性確保**: §8.3 「臨床/研究データパイプラインで uv.lock コミット」を満たす
3. **PyPI 公開 (Day28+) の前提条件整備**: pyproject.toml の `[project]` metadata は PyPI publish に必須
4. **CI 高速化**: `astral-sh/setup-uv` action で uv の cache + dep cache を action が自動管理、`pip install -r` より高速
5. **PEP 735 dependency groups の活用**: pytest 等の dev-only deps を `[dependency-groups.dev]` に分離、PyPI metadata に混入させない

### 1.3 目的

1. **pyproject.toml 新規作成**: hatchling backend + project metadata + 4 runtime deps + dev group (pytest)
2. **uv.lock 自動生成 + commit**: `uv sync` で確定的に install、依存バージョン完全 lock
3. **.python-version 新規作成**: `3.14` 1 行 (user local + CI experimental matrix と整合)
4. **requirements.txt 削除**: single source of truth 一本化
5. **CI workflow uv 化**: `astral-sh/setup-uv` + `uv sync --frozen --group dev` + `uv run pytest`
6. **flat layout 維持**: 本 repo は CLI application、`[tool.uv] package = false` で package build を skip (PyPI 公開時は Day28+ で改めて package mode 設計)

### 1.4 設計判断の経緯 (brainstorming 質問)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | requirements.txt の扱い | **(α) 完全削除** (CLAUDE.md §8.1 に最も忠実、single source of truth) |
| Q2 | build backend | **(A) hatchling** (modern PEP 517、flat layout 対応、設定最小) |
| Q3 | runtime / dev deps 分離 | **(α) [project.dependencies] + [dependency-groups.dev] (PEP 735)** (uv-native、PyPI metadata 清浄) |
| Q4 | Python version 仕様 | **(α) requires-python = ">=3.11" + .python-version = "3.14"** (CI matrix と整合、user local も 3.14) |
| Q5 | CI 更新範囲 | **(α) astral-sh/setup-uv + uv sync + uv run pytest** (Modern + clean) |

---

## 2. Architecture & ファイル配置

### 2.1 改変対象 (5 file)

| File | 種別 | 改変内容 |
|:---|:---|:---|
| `pyproject.toml` | 新規作成 (~60 行) | hatchling backend + project metadata (name/version/desc/license/authors/keywords/classifiers/urls) + [project.dependencies] 4 件 + [dependency-groups.dev] (pytest) + [tool.uv] package = false |
| `uv.lock` | 新規作成 (自動生成) | `uv sync --group dev` で生成、全依存の transitive deps + hash まで lock |
| `.python-version` | 新規作成 (1 行) | `3.14` (uv local default、CI experimental matrix と整合) |
| `requirements.txt` | 削除 | pyproject.toml + uv.lock を single source of truth とする |
| `.github/workflows/tests.yml` | 修正 | `actions/setup-python` → `astral-sh/setup-uv@v6` 追加 (setup-python は version matrix 用に残す)、`pip install -r requirements.txt` → `uv sync --frozen --group dev`、`python -m pytest` → `uv run pytest tests/ -q` |

### 2.2 改変対象外 (確認のみ)

- `main.py` および全 module (parser ロジック等は不変)
- `tests/` 全 file (test 内容は不変、`uv run pytest` で実行)
- `tests/fixtures/` 全 fixture
- `docs/`, `tools/`, `skill_package/`
- `.gitleaksignore` (filter-repo SHA fingerprint 維持)
- `.gitignore` (既存に `.venv/` 等の uv 関連 ignore が含まれているか要確認、必要なら追記)

### 2.3 新規作成 (Day27 archive)

| File | 用途 |
|:---|:---|
| `docs/superpowers/specs/2026-05-24-day27-pyproject-uv-migration-design.md` | 本 SPEC |
| `docs/superpowers/plans/2026-05-24-day27-pyproject-uv-migration.md` | writing-plans 出力 |
| `docs/sessions/day27/README.md` | Day27 archive index |
| `docs/sessions/day27/DAY27_LESSONS_LEARNED.md` | Day27 教訓記録 |

### 2.4 project metadata 詳細

| Field | Value | 根拠 |
|:---|:---|:---|
| `name` | `"pubmed-reference-resolver"` | repo 名と一致 (PyPI namespace 予約) |
| `version` | `"0.1.0"` | 現 release tag と一致 (Day21 release) |
| `description` | `"Reverse-lookup PubMed validation for peer-review reference sections (PDF/DOCX/TXT input)"` | README §概要から抽出 |
| `readme` | `"README.md"` | PyPI long_description として利用 |
| `requires-python` | `">=3.11"` | Q4 確定、3.11/3.12/3.13/3.14 全 cover |
| `license` | `"MIT"` | Day19 で MIT 採用 (PEP 639 SPDX 形式) |
| `authors` | `[{name = "Hideki Katayama"}]` | email 含めず privacy 配慮 |
| `keywords` | `["pubmed", "reference", "peer-review", "doi", "crossref", "nlm", "bibliography"]` | PyPI 検索性 |
| `classifiers` | Python version × 4, License MIT, Status Beta, Topic Scientific/Information Analysis + Text Processing/Linguistic, OS Independent | PyPI 標準 classifier |
| `urls` | Homepage, Repository, Issues, Release | GitHub URL 群 |

### 2.5 依存関係マッピング

```
現 requirements.txt           → pyproject.toml
─────────────────────────────────────────────────
python-docx>=1.2,<2.0         → [project.dependencies]    "python-docx>=1.2,<2.0"
rapidfuzz>=3.14,<4.0          → [project.dependencies]    "rapidfuzz>=3.14,<4.0"
PyYAML>=6.0,<7.0              → [project.dependencies]    "PyYAML>=6.0,<7.0"
certifi>=2024.0,<2027.0       → [project.dependencies]    "certifi>=2024.0,<2027.0"
pytest>=9.0,<10.0             → [dependency-groups.dev]   "pytest>=9.0,<10.0"
```

---

## 3. 具体 pyproject.toml + CI workflow

### 3.1 pyproject.toml (新規、~60 行)

```toml
# pubmed-reference-resolver — 査読対象論文の Referenceセクション逆引き検証ツール
# Day27 で requirements.txt → pyproject.toml + uv.lock に移行 (CLAUDE.md §8 整合).

[project]
name = "pubmed-reference-resolver"
version = "0.1.0"
description = "Reverse-lookup PubMed validation for peer-review reference sections (PDF/DOCX/TXT input)"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
authors = [
    {name = "Hideki Katayama"},
]
keywords = [
    "pubmed",
    "reference",
    "peer-review",
    "doi",
    "crossref",
    "nlm",
    "bibliography",
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Scientific/Engineering :: Information Analysis",
    "Topic :: Text Processing :: Linguistic",
]
dependencies = [
    "python-docx>=1.2,<2.0",
    "rapidfuzz>=3.14,<4.0",
    "PyYAML>=6.0,<7.0",
    "certifi>=2024.0,<2027.0",
]

[project.urls]
Homepage = "https://github.com/hikataya01-netizen/pubmed-reference-resolver"
Repository = "https://github.com/hikataya01-netizen/pubmed-reference-resolver"
Issues = "https://github.com/hikataya01-netizen/pubmed-reference-resolver/issues"
Release = "https://github.com/hikataya01-netizen/pubmed-reference-resolver/releases/tag/v0.1.0"

# PEP 735 dev dependency group (uv-native、PyPI metadata に含まれない)
[dependency-groups]
dev = [
    "pytest>=9.0,<10.0",
]

# Application mode: 本 repo は CLI application として `python3 main.py` で実行する
# flat layout (main.py + 各 module が repo root 直下) を採用. PyPI publish (Day28+)
# 時は package mode への移行を検討 (src/ layout + entry_points 追加が必要).
[tool.uv]
package = false
```

### 3.2 `.python-version` (新規、1 行)

```
3.14
```

uv が `uv sync` 実行時に **3.14 系の最新 patch** を自動 install (現状 3.14.3 を user local で使用中)。CI matrix は別途 `actions/setup-python` で override する。

### 3.3 CI workflow `.github/workflows/tests.yml` (更新)

**変更前** (現状、両 job の steps が同形):

```yaml
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/ -q
```

**変更後**:

```yaml
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
      - run: uv sync --frozen --group dev
      - run: uv run pytest tests/ -q
```

両 job (test + test-experimental) で同じ steps 更新。Python 3.11/3.12/3.14 各 matrix で:

- `setup-python` が指定 Python を install
- `setup-uv` が uv 0.x.y を install + cache 有効化 (uv の cache + dep cache を action が自動管理)
- `uv sync --frozen --group dev` で `uv.lock` 厳守 install (dev group 含む)
- `uv run pytest tests/ -q` で uv-managed venv 内で pytest 実行

### 3.4 削除する file

- `requirements.txt` — `git rm` で削除、pyproject.toml + uv.lock が source of truth

### 3.5 application mode vs package mode (`[tool.uv] package = false`) の理由

本 repo は CLI application として `python3 main.py <input>` で実行する flat layout (main.py + 各モジュールが repo root 直下、`__init__.py` なし)。tests も `sys.path.insert(0, REPO_ROOT)` で直接 import している (Day8 以来の design)。

`[tool.uv] package = false` で **uv の build/install を skip**、依存管理のみに専念。Day28+ PyPI publish を検討する際は:

1. src/ layout への移行 (modules → `src/pubmed_reference_resolver/*.py`)
2. `__init__.py` 追加
3. `[project.scripts]` で `pubmed-reference-resolver = "pubmed_reference_resolver.main:main"` 等の entry point
4. `package = false` → `true` (デフォルト) + `[build-system]` + hatchling config

これらは Day28+ の別 spec で扱う (本 Day27 では minimum 移行)。

### 3.6 uv.lock 生成手順

```bash
# pyproject.toml 作成後、uv sync で .venv + uv.lock を生成
uv sync --group dev

# uv.lock は git commit、.venv/ は .gitignore (既存) で除外
cat .gitignore | grep -E "venv|env" | head -5  # 確認
```

---

## 4. Commit 計画 (4 commits、atomic migration)

| 順 | Phase | type | scope | 内容 |
|:---:|:---:|:---|:---|:---|
| 1 | Pre | `docs(spec)` | — | 本 SPEC を archive |
| 2 | Pre | `docs(plan)` | — | writing-plans 出力 |
| 3 | Migration | `build(deps)` | Task 1 | 4 file changes atomic: pyproject.toml 新規 + .python-version 新規 + uv.lock 自動生成 + requirements.txt 削除 + CI workflow 更新 + 全 pytest 111 件 PASS 確認 + commit + push |
| 4 | Post | `docs(sessions)` | Task 2 | Day27 archive (README + LESSONS) |

合計 **4 commits**。

**atomic commit の根拠**: pyproject.toml 作成 + requirements.txt 削除 + CI workflow 更新は **相互依存**で、分割すると中間状態で broken (例: CI workflow が requirements.txt を install しようとして失敗、または pyproject.toml だけある状態で uv sync 不可)。

---

## 5. 完了条件 (12 項目)

| # | 条件 | 確認方法 |
|:---:|:---|:---|
| 1 | `pyproject.toml` 新規追加 | `ls pyproject.toml` 存在 + `grep -c '^\[' pyproject.toml` ≥ 5 (sections) |
| 2 | `pyproject.toml` の `name`/`version`/`requires-python`/`dependencies` が spec §1.4 通り | `python3 -c "import tomllib; d = tomllib.load(open('pyproject.toml','rb')); print(d['project']['name'], d['project']['version'])"` |
| 3 | `[dependency-groups.dev]` に pytest 記載 | `grep -A2 '^\[dependency-groups\]' pyproject.toml` で pytest hit |
| 4 | `[tool.uv] package = false` 設定 | `grep -A1 '^\[tool.uv\]' pyproject.toml` で `package = false` hit |
| 5 | `.python-version` 新規追加、`3.14` 1 行 | `cat .python-version` = `3.14` |
| 6 | `uv.lock` 新規追加 + commit 済 | `ls uv.lock` 存在 |
| 7 | `requirements.txt` 削除 | `ls requirements.txt 2>&1` で "No such file" |
| 8 | CI workflow が uv ベース | `grep -c "astral-sh/setup-uv\|uv sync\|uv run pytest" .github/workflows/tests.yml` ≥ 3 |
| 9 | CI workflow に `pip install` が残存しない | `grep "pip install" .github/workflows/tests.yml` で 0 hit |
| 10 | 全 test pass (regression なし) | `uv run pytest tests/ -q` で **111 passed / 0 skipped / 0 failed** |
| 11 | gitleaks 継続 clean | `gitleaks detect --no-banner --redact` で `no leaks found` |
| 12 | CI green for HEAD | `gh run list --limit 1 --jq .[0].conclusion` = `success` |

---

## 6. 工数見積もり

| Phase | 内容 | 見積 |
|:---:|:---|---:|
| Pre | SPEC + PLAN archive | 30 min |
| Task 1 (migration) | pyproject.toml 新規 + .python-version 新規 + uv sync で uv.lock 生成 + requirements.txt 削除 + CI workflow 更新 + 全 pytest + uv run pytest 確認 + atomic commit + push | 60 min |
| Task 2 (archive) | Day27 archive (README + LESSONS) + push + CI verify | 30 min |
| **合計** | | **~2 h** |

LLM cost: **$0** (config migration、parser fix なし)

---

## 7. 想定リスク

| リスク | 確率 | 影響 | 対応 |
|:---|:---:|:---:|:---|
| `uv sync` 初回実行で全依存が install されない / version 解決失敗 | 低-中 | 中 | 既存 requirements.txt の version 範囲をそのまま転載、major version 制約も同じなので解決は確実。失敗時は `--verbose` で原因特定 |
| `uv.lock` の binary 差分が大きく commit が膨大 | 低 | 低 | uv.lock は plain TOML format、binary ではない。size は数 KB 程度 |
| CI の `astral-sh/setup-uv@v6` action が未対応 | 低 | 中 | `@v6` が最新メジャー (2025 リリース)、`@v3` 等の older version でも setup-uv は機能。Fallback として `pip install uv` も可 |
| `uv run pytest` が tests/ の `sys.path.insert(0, REPO_ROOT)` と干渉 | 中 | 中 | uv は cwd を REPO_ROOT に設定、tests は既存 manipulation で動く想定。事前に local `uv run pytest tests/ -q` で実機確認 |
| `[tool.uv] package = false` で hatchling build_system が必要にならない確認 | 低 | 低 | uv docs 確認、`package = false` で build_system 任意。実機で `uv sync` 成功すれば確定 |
| 既存 user (clone 後 pip install) が breaking change を被る | 中 | 低 | README に「uv 必須、pip install -r requirements.txt は Day27 で廃止」を追記。CHANGELOG にも記載 |
| `.python-version` 3.14 で local CI 不一致 (CI matrix は 3.11/3.12 stable) | 低 | 低 | `.python-version` は local default、CI は `actions/setup-python` で matrix 指定 → 別 dimension で衝突なし |
| Day22 で導入した certifi 等の version 範囲が uv.lock で resolve できない | 低 | 中 | Day22-26 で実機 install 済の version 範囲を踏襲、uv の resolver は pip と互換性 high |

---

## 8. Out of Scope (Day28+ 候補)

- **PyPI 公開**: pyproject.toml 整備で前提条件は達成、Day28+ で `[tool.uv] package = true` + src/ layout + entry_points + `uv build` + `uv publish`
- **Latin Extended-A 範囲拡張** (Day26 archive Top priority、`_UPPERCASE_LATIN1` 定数 1 行 update で 8 箇所伝播)
- **pre-commit hook gitleaks 自動実行** (Day22 handoff パターン 3)
- **CONTRIBUTING.md / Issue PR template / dev tool 整備 (ruff, mypy)**
- **Crossref graceful failure 16 件の対応** (Day22 §6.3 NEW)
- **NLM fuzzy-match precision 改善** (Day22 §6.3 NEW)
- **`tools/build_*_fixture.py` の共通 utility refactor** (Day23 code review 指摘)
- **mdpi_173refs 固有の manual_overrides.yaml 構築** (Day24 から継承)
- **deterministic byte-level golden の再構築** (LLM stub 経由、Day29+ 大改修)

---

## 9. 参照

- CLAUDE.md §8 (Python 開発環境): 本 spec の主要根拠
- CLAUDE.md §8.1: pyproject.toml + uv.lock を single source of truth、pip install 直接実行を避ける
- CLAUDE.md §8.3: 臨床/研究データパイプラインで uv.lock コミット
- Day23 spec §C5: 「pyproject.toml + uv.lock 移行 (CLAUDE.md §8 整合)」と明示で Day24+ 候補入り
- Day22 spec: `docs/superpowers/specs/2026-05-24-rule3-nlm-ssl-fix-design.md` (certifi 追加の origin)
- Day26 archive: `docs/sessions/day26/` (_UPPERCASE_LATIN1 定数の前例、本 spec で flat-layout 維持理由として参照)
- 現 `requirements.txt`: 5 deps、Day27 で削除対象
- 現 `.github/workflows/tests.yml`: pip ベース、Day27 で uv ベースに更新
- uv 公式 doc: https://docs.astral.sh/uv/concepts/projects/ (project mode + dependency groups)
- PEP 735 (Dependency Groups): https://peps.python.org/pep-0735/
- PEP 639 (License expression): https://peps.python.org/pep-0639/
- astral-sh/setup-uv: https://github.com/astral-sh/setup-uv

---

**承認**: 片山英樹 (brainstorming Q1-Q5 + design 全 3 sections)
**次工程**: writing-plans skill で bite-sized implementation plan を作成
