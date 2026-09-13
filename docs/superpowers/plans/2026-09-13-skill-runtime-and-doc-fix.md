# 2026-09-13 スキル実行環境と SKILL.md の修正 (dev-light: spec + plan)

## 背景 (実測で確認した問題)

1. **依存漏れ**: `pyproject.toml` に `pypdf` / `requests` / `tenacity` / `anthropic` が無く、`.venv` では PDF 入力・Phase 3 以降・非 MDPI 構造化が動かなかった。テストはオフラインで完結するため 117 passed のまま検出されなかった。システムの `python3` (Homebrew) にも `python-docx` 等が無く、SKILL.md 記載の `python3 main.py` は失敗した。
2. **`.env` 探索の誤認**: `load_env_files()` の候補 #1 は `Path(__file__).resolve()` = symlink 解決後の project root。`skill_package/.env` は cwd が `skill_package/` のときしか読まれず、`cd ~` から実行するとキー未読込のまま進んだ。
3. **SKILL.md の不整合**: description は Crossref + NLM 補助検証を謳う一方「非対応: CrossRef」と記載、`requirements.txt` 参照 (Day27 で廃止)、出力表に `three_class_classification.json` 欠落、report.md の層構成が実際の見出しと不一致、開発履歴の混入、description が長くスキル一覧で表示されない。

## 決定 (ユーザー承認済み)

- API キーは `~/.pubmed-reference-resolver.env` (chmod 600, 候補 #2) へ移動し `skill_package/.env` を削除
- `anthropic` を必須依存に追加 (lazy import は維持、テストはオフラインのまま)
- 動作確認は PubMed (Phase 3) まで

## 変更

| ファイル | 変更 |
|---|---|
| `pyproject.toml` / `uv.lock` | 依存 4 件追加、`uv lock` |
| `tests/test_env_loader.py` | autouse fixture で `HOME` を隔離 (実機の `~/.pubmed-reference-resolver.env` がテストに漏れて 2 件失敗したため) |
| `skill_package/SKILL.md` | 実行環境節を新設 (`$REPO/.venv/bin/python`、キー配置、symlink 構成の注意)、記述を実装に合わせて修正、description 短縮、開発履歴を削除 |
| `docs/operations/SETUP_API_KEYS.md` | 推奨配置をホーム直下に改訂、候補 #1 の実体を明記 |
| `README.md` | `uv sync`、`.venv/bin/python`、出力ファイル名、テスト件数を更新 |

## 検証

- `uv run pytest tests/ -q` → 117 passed
- `cd ~` から `~/.claude/skills/pubmed-reference-resolver/main.py` で `examples/sample_reference_section.pdf` を `--phase 3` 実行 → `[env] loaded from ~/.pubmed-reference-resolver.env (2 vars)`、15 件中 9 件解決 (期待出力 CSV も 15 行)
- SKILL.md 記載コマンド (`$REPO/.venv/bin/python $REPO/main.py`) で `--phase 1` 実行し env 読込を確認
- SKILL.md の参照パス 8 件の実在を確認

## 未実施

- Phase 4 (Crossref / NLM 通信) の実機実行 — 承認範囲外
