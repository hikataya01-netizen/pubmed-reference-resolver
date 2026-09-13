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

## 追補: パソコン間の可搬性 (同日、ユーザー承認済み)

以前は別のパソコン (または手作業で依存を入れた Python) でのみ動いていた可能性があるため、環境依存を除く。

- **A. パス固定の除去**: SKILL.md の `$REPO` を絶対パスではなく `REPO="$(cd -P ~/.claude/skills/pubmed-reference-resolver/.. && pwd)"` で symlink から求める (bash / zsh で確認)
- **B. `tools/doctor.sh`**: Python 環境・依存 8 件・本体モジュール・uv.lock 整合・API キー (配置/権限/実ローダーでの読込、値は非表示)・スキル symlink・Phase 1 オフライン実行・外部 API 疎通 (`--offline` で省略) を診断し、✘ に直し方を表示。要対処があれば exit 1
- README に展開手順、SKILL.md に「初回・エラー時はまず doctor」を追記

検証:
- 現環境: 全項目 ✔、exit 0
- 空の HOME (新しいパソコン相当): API キー無し・スキル未登録を ✘ 3 件で検出、exit 1
- 空値キー + 権限 644: 権限警告と ANTHROPIC_API_KEY 未設定を検出
- symlink 経由での起動でもリポジトリ位置を正しく解決
- SKILL.md 記載コマンドを zsh・cwd=/tmp で実行し env 読込を確認
