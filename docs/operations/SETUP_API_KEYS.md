# SETUP_API_KEYS.md

**pubmed-reference-resolver の API key セットアップ手順**

**作成日**: 2026/05/13 (Day12)
**配置**: `docs/operations/SETUP_API_KEYS.md`
**対象**: 本スキルを利用する全ての利用者 (特に Vancouver/AMA 系入力を扱う場合)
**前提**: Day8 env loader 改修 (commit `d49dc58` + `7bc009b`) 以降の挙動を反映

---

## 0. このドキュメントで解決すること

本スキルは 2 種類の外部 API を利用する:

| API | 必須度 | 用途 |
|:---|:---:|:---|
| **Anthropic API** | **条件付き必須** | LLM 経由の reference 構造化 (Vancouver/AMA 系入力で必須、MDPI 中心入力では不要) |
| **NCBI E-utilities API** | **任意 (推奨)** | PubMed 検索の rate limit 緩和 (3 req/sec → 10 req/sec) |

`USAGE_QUICKSTART.md` §III の「引用スタイル別の処理経路」で両者の必須度マトリクスを整理しているが、本書は**取得手順 + .env 配置 + Day8 env loader 挙動の詳細**に特化する.

---

## 1. ANTHROPIC_API_KEY の取得手順

### 1.1 取得先

1. https://console.anthropic.com/ にアクセス
2. ログイン (アカウントなければ作成)
3. 左メニュー「**API Keys**」→「**Create Key**」
4. Key 名称 (例: `pubmed-reference-resolver`) を入力 → 作成
5. 表示された key (`sk-ant-api03-...` で始まる ~108 文字) を**その場で控える** (再表示不可)

### 1.2 想定費用

Claude Sonnet 4.6 (`claude-sonnet-4-6`) を使用. 2026/05 時点の参考値:

| 入力規模 | 想定 LLM 呼出数 | 概算費用 (Sonnet 4.6) |
|:---|:---:|:---:|
| MDPI 中心 30 件 | 0 (全 fast-path) | **$0** |
| Vancouver/AMA 24 件 | 24 | **$0.15-0.25** (Day9 (Z) 実測) |
| 混在 100 件 | 30-60 | $0.30-0.80 |
| Vancouver/AMA 100 件 (推定) | 100 | $0.60-1.00 |

価格は変動するため、利用前に Anthropic API pricing で最新値を確認推奨.

### 1.3 必須となるシナリオ

- 入力 reference に **`(YYYY)` 括弧年表記**が含まれる (Vancouver/AMA 系) → 全件 LLM 経路 → 必須
- MDPI 中心入力でも、不完全 ref (parser 限界) が混在する場合は **任意** (graceful 処理されるが LLM がない場合は parsing_confidence=low のまま出力)
- `is_mdpi_style()` の判定詳細は `mdpi_parser.py:372-` 参照

→ **「とりあえず設定しておく」のが安全**. 設定済みの key は MDPI 入力では呼ばれない (cost 0).

---

## 2. NCBI_API_KEY の取得手順

### 2.1 取得先

1. https://www.ncbi.nlm.nih.gov/account/ にアクセス
2. ログイン (アカウントなければ作成、メール認証必要)
3. 右上アイコン → **Account Settings**
4. 「**API Key Management**」セクション → **Create an API Key**
5. 表示された key (~36 文字、英数字) を控える

### 2.2 効果

| 設定状態 | PubMed E-utilities rate limit | 24 件処理時間 (Day9 (Z) 実測) |
|:---|:---:|:---:|
| **未設定** | 3 req/sec (NCBI 既定) | Phase 3 約 70-90 秒 (推定) |
| **設定済** | **10 req/sec** | Phase 3 **38 秒** (Day9 (Z) 実測) |

→ 24 件で約 **2-3 倍の高速化**. 100 件超の入力では恩恵が大きい.

### 2.3 必須度

**任意だが推奨**. 未設定でも Phase 3 は完走するが、大量 reference 処理 / 連続実行で 429 (Too Many Requests) エラーが発生しやすい.

---

## 3. .env ファイルの配置

### 3.1 ファイル形式

`KEY=VALUE` 形式. 1 行 1 key. コメント行 (`#` 始まり) と空行は無視.

```bash
# pubmed-reference-resolver API keys
# 取得手順: docs/operations/SETUP_API_KEYS.md

ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
NCBI_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**注意**:
- 値部分に `"..."` や `'...'` で囲んでも OK (内部で除去される)
- 値の中に `#` を含めても OK (inline comment は非対応、`#` 以降も値の一部として扱われる)
- 改行や空白を値に含めない

### 3.2 main.py の探索順序

`main.py:load_env_files()` (lines 56-) は以下の優先順で `.env` を探索:

| # | 候補パス | 用途 |
|:---:|:---|:---|
| 1 | `{スキル配置ディレクトリ}/.env` | main.py と同じ場所 (= project root) |
| 2 | `$HOME/.pubmed-reference-resolver.env` | ユーザー専用、ホーム直下 |
| 3 | `{カレントディレクトリ}/.env` | 呼び出し元の cwd |
| 4 | `{入力ファイルのディレクトリ}/.env` | 入力 PDF/DOCX と同じフォルダ |

複数の候補で見つかった場合、**先勝ち** (#1 が最優先). ただし「既に非空値で os.environ に set 済」の key は上書きしない (Day8 D8-1 で確立、§5 参照).

`--env-file <path>` で明示指定もできる (探索順序を bypass、単一 path のみ参照).

### 3.3 推奨配置 (Day9 (Z) 実例)

**スキル配置ディレクトリ** (`~/.claude/skills/pubmed-reference-resolver/.env`) が推奨. 理由:

- Day6 で確立された symlink 経由構成 (`~/.claude/skills/pubmed-reference-resolver` → project root の `skill_package/`) のため、**スキル管理パスから一元管理可能**
- cwd を変えても自動探索でヒット
- 既存実機検証 (Day7-9) で全て本配置で成功

実例 (heredoc + chmod 600):

```bash
cat > ~/.claude/skills/pubmed-reference-resolver/.env <<'EOF'
ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXXXXXXXXXXXXX
NCBI_API_KEY=XXXXXXXXXXXXXXXXXXXX
EOF
chmod 600 ~/.claude/skills/pubmed-reference-resolver/.env
```

**`chmod 600` を必ず実行**. 機密ファイルとして owner-only read/write に制限.

### 3.4 .gitignore による保護

project の `.gitignore` (line 2-4) で以下が ignored 済み:

```
.env
.env.local
.env.*.local
```

→ `.env` を `git add` しても staging されない (Day7 で確認済). 安心して project root 配下に置ける.

---

## 4. .env 内容の検証 (key 値は表示せず)

key 値の中身を直接 cat するのはセキュリティ上避ける. 以下の安全確認方法を推奨:

```bash
# (a) ファイル存在 + permission 確認 (中身は表示しない)
ls -la ~/.claude/skills/pubmed-reference-resolver/.env
# 期待: -rw-------@ 1 USER staff <SIZE> <DATE> .env

# (b) key 名のみ抽出 (値は表示しない)
grep -oE '^[A-Z_][A-Z_0-9]*=' ~/.claude/skills/pubmed-reference-resolver/.env
# 期待: ANTHROPIC_API_KEY= / NCBI_API_KEY=

# (c) 行ごとの長さ (実 key かサンプル placeholder か推測)
awk '{print NR, length($0)}' ~/.claude/skills/pubmed-reference-resolver/.env
# 実 key の長さ目安:
#   ANTHROPIC_API_KEY=...  → 全 ~126 文字 (key 値は ~108 文字)
#   NCBI_API_KEY=...       → 全 ~49 文字 (key 値は 36 文字)
# placeholder (例: sk-ant-api03-NEW_KEY_HERE) なら全 43 文字程度 → 短い
```

---

## 5. Day8 env loader 改修以降の挙動

Day7-9 で発見・解決された env loader 関連の重要事項を整理.

### 5.1 空値の既存環境変数を上書きする (Day8 D8-1)

**背景**: Claude Code 等の harness は subprocess に `ANTHROPIC_API_KEY=` (空値) を export する場合がある (key 漏洩防止). Day8 改修前の env loader は「key が存在すれば上書きしない」設計のため、空値が `.env` の正しい値による上書きを阻害していた.

**Day8 改修後** (commit `d49dc58` + `7bc009b`):

`main.py:_inject_env_kv()` の条件:
```python
if (not os.environ.get(k)) and v:
    os.environ[k] = v
```

→ 「**未設定** または **空値**」の場合に `.env` から上書き. 「非空値で設定済」の場合のみ保護される (= ユーザー指定が最優先という契約は維持).

### 5.2 `env -u ANTHROPIC_API_KEY` workaround は不要

Day7 (`b9wkuu7w0`) では Claude Code 環境で `RuntimeError: ANTHROPIC_API_KEY not set` が発生し、`env -u ANTHROPIC_API_KEY python3 ...` で workaround していた. Day8 改修以降は **workaround 不要**, 素直に:

```bash
python3 main.py /path/to/input.docx -o /path/to/out/ --env-file ~/.claude/skills/pubmed-reference-resolver/.env
```

で動作 (Day8 (V) 実機検証で確認済、commit `bvmp5zypx`).

### 5.3 共有 injector 関数 `_inject_env_kv()`

Day8 で `load_env_files()` (auto 探索) と `main()` の `--env-file` 処理が同じ injection logic を 2 箇所に重複保持していた問題 (D8-2) が発覚. Day8 commit `7bc009b` で `_inject_env_kv()` 関数を抽出し、両 caller がこれを呼び出す設計に refactor (D8-3).

→ 将来 3 箇所目の env injection が必要になっても、`_inject_env_kv()` 経由なら同じ挙動 (空値 overwrite) が自動継承される.

---

## 6. トラブルシューティング

### Q1. `RuntimeError: ANTHROPIC_API_KEY not set. Pass via env or --api-key.`

**原因と対処順序**:

1. `.env` に `ANTHROPIC_API_KEY=...` が記載されているか確認 (§4 (b)(c) の方法で値を表示せず確認)
2. main.py 起動時に `[env] loaded from <path>` が log に出ているか確認
   - 出ていない場合 → `.env` の path が探索順序のいずれにもヒットしていない. `--env-file <絶対パス>` で明示指定 (§3.2 参照)
3. `[env] loaded from ...` は出ているのにエラー → Day8 改修前の挙動 (空値上書き不可). main.py が **改修前の commit** で実行されている可能性. `git log --oneline | grep -E "(d49dc58|7bc009b)"` で確認、なければ Day8 commit を pull
4. 上記すべて OK でもエラー → key の値が空文字列 ("") で記録されている可能性. `grep -c '^ANTHROPIC_API_KEY=$' .env` で空値 line を検出 (1 以上ヒットすれば key 値が空)

### Q2. `PubMed API rate limit (429 Too Many Requests)`

**原因**: NCBI key 未設定 (3 req/sec 制限) で連続実行している.

**対処**: §2 で NCBI key を取得 → `.env` の `NCBI_API_KEY=...` に追加 → 再起動. 10 req/sec に緩和される.

### Q3. `WARN: --env-file not found: <path>`

**原因**: `--env-file` で指定した path が存在しない or read 権限なし.

**対処**:
- `ls -la <path>` で存在確認
- 相対パス (`./conf/.env` 等) で指定する場合、cwd に依存. **絶対パス** (`/Users/.../...` または `~` を展開した形) を推奨

### Q4. `.env` を git に commit してしまった

**緊急対処**:

1. **即座に key を revoke** (Anthropic / NCBI の管理画面で該当 key を削除/無効化)
2. 新しい key を再発行
3. git history から削除 (例: `git filter-repo --path .env --invert-paths` 等)
4. force push が必要な場合は影響範囲確認後に実施
5. `.gitignore` を確認し、`.env` が含まれていることを確認 (§3.4)

→ **予防が最重要**. 初回セットアップ時に `.gitignore` を必ず確認.

---

## 7. 関連リソース

| リソース | 場所 | 役割 |
|:---|:---|:---|
| 利用者向けスキル即時利用ガイド | `skill_package/references/USAGE_QUICKSTART.md` | §III で引用スタイル別の API key 必須度マトリクス、§VI でコスト試算 |
| 開発履歴 (env loader 改修) | `docs/sessions/day8/DAY8_LESSONS_LEARNED.md` | §3 で `_inject_env_kv` 抽出の経緯、教訓 D8-1〜D8-3 |
| Vancouver Veto 実装 (LLM 必須化の契機) | `docs/sessions/day9/SPEC_mdpi_fast_path_strict.md` | §3-§4 で is_mdpi_style 判定ロジック |
| Day9 (Z) 実機検証データ (本書のコスト/時間値の出典) | `docs/sessions/day9/DAY9_LESSONS_LEARNED.md` §4 | 22:30:15 (Day9 (Z) retry) の Phase 別所要時間 + 解決率 |
| env loader test | `tests/test_env_loader.py` | Day8 で追加された 7 test、空値上書き挙動の regression 保護 |

---

## 8. 補足: API key を絶対に commit しないために

`.env` 以外にも、**意図せず key が記録され得る場所**:

| 場所 | リスク | 対処 |
|:---|:---|:---|
| `.env.save` (nano 編集時の backup) | nano で `.env` 編集中に保存失敗で残る | Day7 (Q-β) で `.gitignore` に `*.save` 追加済 |
| `.env.local`, `.env.*.local` | フレームワーク慣習 | `.gitignore` 既存ルールで除外 |
| shell history (`~/.zsh_history` 等) | `--api-key sk-ant-...` を CLI で直接渡すと履歴に残る | **`--api-key` の使用は避け、`.env` 経由のみ**. やむを得ない場合は `HISTSIZE=0` で一時無効化 |
| commit message / PR description | コピペ事故 | レビュー時に grep `sk-ant-` / `[a-f0-9]{36}` |
| log file / 出力 ファイル | 一部の verbose log で env をダンプする実装あり | 本スキルでは `[env] loaded from <path>` のみ出力 (key 値は表示しない、確認済) |

「**key は `.env` の中だけに存在する**」状態を保つのが最も安全.

---

**作成日**: 2026/05/13 (Day12)
**作成者**: Claude Code (Sonnet 4.6)
**メンテナ**: 片山英樹 (Hideki Katayama)
**バージョン**: 1.0 (初版)
