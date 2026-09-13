# Day31 設計: v2 (audit.py 系) を正式版スキルとして統合する

**作成日**: 2026-09-14
**ブランチ**: `feature/day31-v2-integration` (起点 `v2-macbookair` = main + v2 スナップショット)
**ワークフロー**: dev-strict

## 1. 背景

- MacBook Air にのみ存在した v2 (2026-07-25〜08-22 改修) を `v2-macbookair` ブランチの `v2/` に保存した (commit `533786d`)。
- v2 は、構造化を呼び出し側 Claude が行い (パイプライン内 LLM API 呼出なし)、標準ライブラリのみで PubMed 照合・整合性チェック 19 カテゴリ・文献評価 (撤回/原著性/エビデンス水準/最新性/Predatory/主張支持性) を行い、Word・CSV・abstract の 3 出力を生成する。
- 一方 v2 には自動テストがなく、`audit.py` は `~/.pubmed-reference-resolver.env` を読まない。
- ユーザー決定 (2026-09-14): v2 を正式版にする / Word 生成は Node.js のまま / 旧版 (main.py Phase 2-4) は当面残して非推奨 / 今回は Day31 のみ。

## 2. ゴール (Day31 完了条件)

1. `~/.claude/skills/pubmed-reference-resolver` 経由のスキルが v2 (`audit.py`) で動く
2. v2 の主要経路が **オフライン・API キー不要** のテストで検証され、CI で回る
3. 既存 117 テストは全件 pass を維持
4. `tools/doctor.sh` が v2 の実行環境 (Node.js・npm `docx`) を診断し、ネットワークなしで v2 の Word 出力まで確認できる
5. iMac・MacBook Air の両方で doctor 全項目 ✔

## 3. 非ゴール (Day32 以降)

- PDF/DOCX から `refs.json` を作る `extract` サブコマンド、MDPI fast-path による自動構造化 (Day32)
- Crossref による未解決文献 3 分類の v2 への統合 (Day33)
- 旧版 main.py Phase 2-4・`report.md` 出力の削除
- v2 のロジック変更 (判定基準・閾値・出力書式は **スナップショットのまま** 移す)

## 4. 配置

| 移動元 (`v2/`) | 移動先 | 備考 |
|---|---|---|
| `audit.py` | `audit.py` (repo root) | env ローダー接続のみ改修 (§5) |
| `pipeline/*.py` | `pipeline/` | 無改修 |
| `build_docx.js`, `package.json`, `package-lock.json` | repo root | 無改修。`node_modules/` は `.gitignore` |
| `SKILL.md` | `skill_package/SKILL.md` | 本 repo 用に書き直し (§7) |
| `references/llm_parsing_prompt.md`, `pubmed_csv_schema.md` | `skill_package/references/` (旧版を置換) | 旧版プロンプトは repo root `references/` に同一内容が既存。旧版 main.py は `$REPO/main.py` から実行すれば root 側を読む |
| `examples/expected_output/refs.json` ほか | `tests/fixtures/v2_synthetic_7refs/` | テスト用 (§6) |
| `main.py` | **取り込まない** | 7 月時点の旧フォーク。repo の main.py が上位互換 |
| `v2/` ディレクトリ | 削除 | 移動完了後。履歴は `533786d` に残る |

`skill_package/` には `audit.py` / `pipeline` / `build_docx.js` への symlink を追加する (既存 `main.py` 等と同じ方式)。
`audit.py` は `Path(__file__).resolve()` で repo root を得るため、Node は repo root の `node_modules/docx` を解決する。

## 5. audit.py の改修 (唯一のロジック変更)

- 起動時に `main.load_env_files(args.structured)` を呼び、`~/.pubmed-reference-resolver.env` 等から `NCBI_API_KEY` を読む。`--api-key` 明示指定・環境変数の非空値が優先 (既存ローダーの契約どおり)。
- `--no-env-file` を追加 (テスト・doctor 用)。
- 読み込んだ場合は `[env] loaded from ...` を表示 (値は表示しない)。
- `--api-key` の default を argparse 定義時 (`os.environ.get`) ではなく、ローダー実行後に解決する。

## 6. テスト (新規、すべてオフライン)

**記録済み応答による再生**: `tests/fixtures/v2_synthetic_7refs/` に以下を置く。

- `refs.json` (v2 同梱の合成 7 件: 正常 2・撤回論文 Wakefield 1998・未解決 1・RCT・メタ解析・非 PubMed)
- `ncbi_responses.json`: NCBI E-utilities (PubMed + NLM Catalog) への各リクエスト (endpoint + tool/api_key を除く params) → 応答本文
- `doaj_responses.json`: ISSN → 収載有無
- `expected_references_pubmed.csv`, `expected_references_abstracts.txt`, `expected_issues.json`: `today_year=2026` 固定で生成した期待出力
- `resolved.json`: doctor の `--reuse-resolved` 用
- `README.md`: 出典 (v2 同梱の合成データ) と再記録手順

記録は新設の `tools/record_v2_fixture.py` で 1 回だけ行う (NCBI・DOAJ への実通信、無料・認証不要)。

**テスト項目** (`tests/test_v2_*.py`):

1. ゴールデン: 再生クライアントで `audit.main([... "--no-docx", "--no-env-file"])` を実行し、CSV・abstract・issues が期待出力とバイト一致 (年は 2026 に固定)
2. `load_refs`: references 空・`ref_no` 重複でエラー、リスト形式も受理
3. 撤回検出: Wakefield (PMID 9500320) が `RETRACTED` かつ `retracted_publication` MAJOR
4. Predatory 複合条件: MEDLINE 非収載 **かつ** DOAJ 非収載 **かつ** L3 系解決のときだけ `predatory_risk`
5. `--offline` + `--reuse-resolved`: 収載状況が全件「未評価」に降格、ネットワーク呼出ゼロ
6. env ローダー接続: `HOME` 隔離下で `.pubmed-reference-resolver.env` の `NCBI_API_KEY` が `PubMedClient` に渡る / `--no-env-file` で渡らない
7. Word 生成スモーク: `node` と `node_modules/docx` があれば docx を生成し ZIP として開けること、無ければ skip

**CI**: `actions/setup-node` + `npm ci` を追加し、7 も CI で実行する。

## 7. SKILL.md (v2 ベースで書き直し)

- v2 の内容 (9 基準・3 出力・19 カテゴリ・2 パス主張支持性・落とし穴対策) を維持
- 置き換える箇所: `$REPO` の求め方、`$REPO/.venv/bin/python "$REPO/audit.py"`、API キー配置、`tools/doctor.sh`、`npm ci`
- **Stage 1-2 の暫定手順** (Day32 まで): 入力ファイルから参照文献を読むには、Read で直接読むか、`"$REPO/.venv/bin/python" "$REPO/main.py" INPUT --phase 1 -o DIR` の `phase1_intermediate.json` (行番号除去・分割済み、API 不使用) を使う
- v2 の「移行元プロジェクト」節 (MacBook Air の Antigravity パス) は削除し、旧版 main.py は「非推奨・Stage 1-2 のみ利用」と明記
- description は 1,000 字未満に短縮 (スキル一覧で表示されるように)

## 8. doctor.sh

- 追加: `node` (≥ 18)、`$REPO/node_modules/docx` (無ければ → `cd "$REPO" && npm ci`)
- 「4. 動作確認」を v2 に変更: `audit.py --structured fixture/refs.json --reuse-resolved fixture/resolved.json --offline --no-env-file -o TMP` で **Word まで生成** (ネットワークなし)。旧 Phase 1 抽出確認も残す
- 本体モジュール確認に `audit` と `pipeline.*` を追加

## 9. ドキュメント

- README: 使用方法を v2 に、旧版を「非推奨」節へ
- CLAUDE.md: Architecture を v2 中心に更新し、既知の誤り (env 探索順・出力ファイル名・skill_package は symlink・テスト件数) を修正
- `docs/sessions/day31/` にセッション記録 (README + LESSONS)

## 10. コミット構成 (repo 規約の 5 コミット + 移設)

1. `docs(spec)`: 本書
2. `docs(plan)`: 実装計画
3. `refactor(v2)`: v2/ → root へ移設 (無改修の移動のみ、`git mv`)
4. `test(prep)`: v2 テスト + fixture (RED: env 接続テスト 6 が失敗)
5. `feat(v2)`: audit.py env 接続・SKILL.md・doctor・CI・docs (GREEN)
6. `docs(sessions)`: archive day31

完了後 PR (`feature/day31-v2-integration` → `main`) を作成し、CI 通過とユーザー確認を経てマージ。

## 11. リスクと対策

| リスク | 対策 |
|---|---|
| 記録応答が PubMed 側の更新で古くなる | テストは記録の再生のみで実通信しない。再記録手順を fixture README に記載 |
| 最新性評価が実行年で変わる | テストでは `today_year=2026` を注入 |
| Node 未導入の環境で Word 出力が失敗 | doctor で検出し `npm ci` を案内。`--no-docx` で CSV/TXT は生成可能 |
| symlink 経由で `pipeline` パッケージが import できない | `audit.py` は resolve 済みパスを `sys.path` に入れる (既存実装)。doctor とテストで symlink 経由起動を確認 |
| iCloud 同期下の iMac 作業ツリー | MacBook Air 側では Desktop のコピーを操作しない (運用で回避、別途 iMac の repo 移設を検討) |
