# DAY8_LESSONS_LEARNED.md

**Day8 = main.py env loader 改修 + test 正規化拡張 (TDD で対応)**

**作成日**: 2026/05/08
**作成者**: Claude Code (Sonnet 4.6)
**配置**: `docs/sessions/day8/DAY8_LESSONS_LEARNED.md`
**対応 commit 範囲**: `d49dc58` 〜 `b8c0e5b` (3 commits) + 本書の archive commit
**対応する指示書**: なし (先生からの単一プロンプトで開始、Day7 の `PHASE_0_VERIFICATION_REPORT.md §9.1` を起点とする)

---

## 0. 本書の位置づけ

Day8 は Day7 PHASE_0_VERIFICATION_REPORT §9.1 の短期タスク 2 件を **TDD で対応**した。形式的な `PHASE_*_INSTRUCTIONS.md` を持たず、先生からの単一プロンプトで開始したセッションのため、本書が Day8 の archive 主体となる。

本書は以下を記録する:

1. Day8 全 3 commits の TDD cycle 詳細 (RED → GREEN の全段階)
2. **(V) 実機検証**で発見した残存問題と対処の経緯
3. Day8 で抽出された教訓 3 件 (D8-1, D8-2, D8-3)
4. main branch 最終形状と次セッションへの引継ぎ

---

## 1. Day8 のフェーズ構成

3 commits は 3 つの自然な作業フェーズに対応:

| フェーズ | commit | 達成 | 経過時間 |
|:---:|:---:|:---|:---:|
| 1 | `d49dc58` | env loader (load_env_files) 部分 fix | TDD 1st cycle |
| 2 | `7bc009b` | `_inject_env_kv` extract + --env-file 経路完全 fix | TDD 2nd cycle (V 検証起点) |
| 3 | `b8c0e5b` | `_scrub_volatile_lines` 拡張 (test 正規化) | TDD 3rd cycle |

---

## 2. フェーズ 1: env loader 部分 fix (`d49dc58`)

### 2.1 課題

Day7 PHASE_0_VERIFICATION_REPORT §8.8 学び 7.6 で記述された問題:

- 親 shell (Claude Code harness 経由) に `ANTHROPIC_API_KEY=` (空値) が export されている
- main.py:91 の env loader は `if k not in os.environ and v:` という条件
- 「**存在すれば**スキップ」の設計のため、空値の既存値が `.env` の正しい値による上書きを阻害

### 2.2 TDD cycle (1st)

**RED**:
- 新規 `tests/test_env_loader.py` に 3 test 追加:
  - `test_load_env_files_overwrites_empty_existing_env_var` (新挙動、現状 fail)
  - `test_load_env_files_preserves_non_empty_existing_env_var` (既存挙動の保護)
  - `test_load_env_files_skips_empty_value_in_env_file` (`v` truthy check の保護)
- 実行: 1 件 fail (`AssertionError: '' == 'sk-ant-test-12345'`)、2 件 pass
- 失敗理由が「feature missing」であることを確認 (typo / setup ミスではない)

**GREEN**:
- main.py:91 の condition を以下に変更:
  ```python
  # Before
  if k not in os.environ and v:
  # After
  if (not os.environ.get(k)) and v:
  ```
- main.py:65 docstring 更新 (Day7/Phase ζ §8.8 学び 7.6 への参照付き)
- 実行: 3 test 全 pass、全 test 55 passed (Day7 末 52 → +3)

### 2.3 commit `d49dc58` の効果

```
fix(env-loader): overwrite empty existing env var with .env value
1 file changed, 5 insertions(+), 2 deletions(-) (main.py)
1 file created (tests/test_env_loader.py, +132 lines)
```

この時点では「TDD cycle 完璧、修正完了」と判断していた。

---

## 3. フェーズ 2: (V) 実機検証で発覚した残存問題と完全 fix (`7bc009b`)

### 3.1 (V) 実機検証の起動

Day7 で発見された問題は production-like 環境 (Claude Code harness) で発生したため、**修正後も同じ環境で動作するか**を確認する必要があった。

実施内容: Day7 で失敗した Stage 2 と**同じコマンド**から `env -u ANTHROPIC_API_KEY` workaround を**除去**して再実行。

期待: exit 0 + 35 秒で完走 + 14/24 解決。

### 3.2 想定外の失敗

```
Starting at 22:07:22
[env] loaded from /Users/.../skills/pubmed-reference-resolver/.env
RuntimeError: ANTHROPIC_API_KEY not set. Pass via env or --api-key.
Exit code: 1
Finished at 22:07:27
```

`[env] loaded from ...` は出力されているのに `ANTHROPIC_API_KEY not set.` で失敗。5 秒で停止。

### 3.3 真因解析

main.py のコード走査の結果、env loader logic は **2 箇所** に重複していた:

| 経路 | 場所 | フェーズ 1 (`d49dc58`) での修正 |
|:---|:---|:---:|
| 自動探索 (`load_env_files()`) | main.py:91 | ✅ 修正済 |
| **`--env-file` 明示** (`main()` argparse 処理) | **main.py:2031** | ❌ **未修正** |

両方とも同じ条件 `if k not in os.environ and v` を持つ重複コード。私の Day8 fix は 1 箇所のみ修正していた。

`tests/test_env_loader.py` の test も `load_env_files()` 経路だけを検証しており、`--env-file` 明示時の挙動は検証範囲外だった。**TDD だけでは捉えきれず、(V) 実機検証で初めて顕在化した**。

### 3.4 TDD cycle (2nd) — 関数 extract で重複排除

**設計判断**: 単に main.py:2031 を 1 行修正するだけだと、将来 3 箇所目が現れた時に同じ bug を繰り返す。**関数 extract で重複排除**が clean。

**RED**:
- `tests/test_env_loader.py` に 4 test 追加:
  - `test_inject_env_kv_overwrites_empty_existing_env_var`
  - `test_inject_env_kv_preserves_non_empty_existing_env_var`
  - `test_inject_env_kv_skips_empty_value_in_kv`
  - `test_inject_env_kv_handles_multiple_keys`
- 実行: 4 件全 fail (`AttributeError: module 'main' has no attribute '_inject_env_kv'`)
- 失敗理由が「feature missing (関数未存在)」であることを確認

**GREEN (refactor 含む)**:
- `_inject_env_kv(kv: dict[str, str]) -> int` 関数を main.py に追加 (Day7 §8.8 学び 7.6 への参照付き docstring)
- `load_env_files()` の inline loop を `_inject_env_kv(kv)` 呼び出しに置換 (refactor)
- `main()` の `--env-file` 処理 inline loop を `_inject_env_kv(kv)` 呼び出しに置換 (本来の修正)
- 実行: 7 test 全 pass、全 test 59 passed (フェーズ 1 後 55 → +4)

### 3.5 (V) 再実行による実機証拠

`bvmp5zypx` task で Stage 2 を再起動 (env -u なし、main.py 修正済):

| 項目 | 結果 |
|:---|:---|
| Exit code | **0** ✓ |
| 所要 | 61 秒 (Phase 2: 13.7s, Phase 3: 47.4s, Phase 4: 0.01s) |
| `[env] loaded from ...` | あり ✓ |
| `ANTHROPIC_API_KEY not set` | **なし** ✓ |
| 解決率 | 14/24 (Day7 retry と同一) ✓ |
| Day7 retry との byte 比較 | csv / abstract / journal_audit **3/3 完全一致** ✓ |

→ workaround 不要、両 caller で同一挙動、出力 regression なし。

### 3.6 commit `7bc009b` の効果

```
refactor(env-loader): extract _inject_env_kv to fix --env-file path
2 files changed, 127 insertions(+), 8 deletions(-)
- main.py:    +30/-8  (新関数 _inject_env_kv + 2 箇所の inline ロジック置換)
- tests/test_env_loader.py: +97/-0 (4 新 test 追加)
```

---

## 4. フェーズ 3: test 正規化拡張 (`b8c0e5b`)

### 4.1 課題

Day7 PHASE_0_VERIFICATION_REPORT §9.1 の 2 件目: 環境依存フィールドの test 正規化拡張。

具体的には、`tests/test_integration_149refs.py:194` の `_scrub_timestamp` helper は report.md の `**実行**: ...` 行のみ masking、`**入力**: <path>` 行は素通し。Day7 で fixture 再生成時に baked-in した `tests/fixtures/mdpi_149refs/input_References.docx` は cwd / 入力パスに依存する volatile field だった。

### 4.2 TDD cycle (3rd)

**RED**:
- `tests/test_integration_149refs.py` に 3 test 追加:
  - `test__scrub_volatile_lines_normalizes_timestamp` (既存挙動の保護)
  - `test__scrub_volatile_lines_normalizes_input_file_path` (新挙動)
  - `test__scrub_volatile_lines_normalizes_both_in_same_line` (combined ケース、report.md の冒頭行は両者を同一行に持つ)
- 実行: 3 件全 fail (`NameError: name '_scrub_volatile_lines' is not defined`)
- 失敗理由が「feature missing (関数未存在)」であることを確認

**GREEN**:
- `_INPUT_FILE_RE = re.compile(r"\*\*入力\*\*: \`[^\`]+\`")` 追加
- `_scrub_timestamp` を `_scrub_volatile_lines` に **rename + 拡張**:
  ```python
  def _scrub_volatile_lines(s: str) -> str:
      s = _TIMESTAMP_RE.sub("**実行**: <TS>", s)
      s = _INPUT_FILE_RE.sub("**入力**: `<INPUT>`", s)
      return s
  ```
- 既存 caller (`test_synthesize_outputs_report_matches_expected` line 225-226) を新名に更新
- 実行: 3 test 全 pass、全 test 62 passed (フェーズ 2 後 59 → +3)

### 4.3 commit `b8c0e5b` の効果

```
refactor(test): expand _scrub_timestamp to _scrub_volatile_lines
1 file changed, 63 insertions(+), 6 deletions(-) (tests/test_integration_149refs.py)
```

将来の Phase 0 / Stage 2 再実行は cwd / 入力パスを問わず byte-identity test に通る。

---

## 5. Day8 で抽出された教訓 3 件

### 学び D8-1: ユニット test だけでは production 環境固有の問題を捉えきれない

**本質**: TDD で追加した test は仕様の一部を厳密に検証するが、**test の対象範囲外**の問題は検出できない。フェーズ 1 (`d49dc58`) で 3 test 全 pass、CI 上は完璧だったが、`--env-file` 経路は検証範囲外だった。production 検証 (V) が初めて残存問題を顕在化させた。

**応用先**:
- 単一の bug 修正でも、**修正の射程**を test だけで判断せず、production-like 検証を併用する
- harness/runtime 固有の挙動 (環境変数の継承、cwd の差異、permission 等) は unit test でモック化しにくい
- production 検証は "smoke test" として軽量化できる (Day8 では 1 分の Stage 2 retry で十分だった)

**Day7 P12 (副次的成果としてのリアルタイム検証) との関係**:
P12 は「skill 配置直後に skill discovery が新版 description を表示した」ことの記録。D8-1 はその逆方向 — 「test alone is insufficient、production が補完する」点で表裏。

### 学び D8-2: "同じロジックが 2 箇所" code smell の事前検出

**本質**: フェーズ 1 で main.py:91 だけを見て修正したが、main.py:2031 にも同じ buggy 条件があった。Day7 stop-and-report の真因解析時に**両方を検出する義務**があったが、見逃した。

**応用先**:
- bug 修正前に必ず `grep -rn` で類似パターンを探す (条件文、定数、エラーメッセージ等)
- 本セッションでは `grep -nE "k not in os.environ"` で 2 箇所が即座に発見できたはず
- code review チェックリストに「重複コードの検出」を追加

**Day1-7 既存学びとの関係**:
Day1-7 で確立されたプロトコル (12 件) には「停止して報告」「事前合意」など人間-AI 協調の規律はあるが、**コード走査の網羅性**に関するプロトコルは弱かった。D8-2 はその空白を埋める。

### 学び D8-3: 関数 extract で重複排除 + 将来の regression 予防

**本質**: フェーズ 2 で `_inject_env_kv` を関数 extract したことで、(a) 現在の bug が 1 箇所の修正で両 caller に適用された、(b) 将来 3 箇所目の loader が現れた時に同じ条件を共有できる、(c) test も `_inject_env_kv` 単体で軽量に書ける。

**応用先**:
- bug 修正 ≠ 1 行修正、**設計改善のチャンス**として捉える
- TDD と refactor は対立せず、refactor 後の test は extract した関数を直接検証できる
- 関数 extract のタイミング: bug が「重複コードの片方のみ」に対処していた時 (= D8-2 が明らかになった時)

**Day1-7 既存学びとの関係**:
Day3 学び F (原則の対立を仲裁する) の系統。「最小修正の原則」と「重複排除の原則」が対立した場合、後者を選ぶ判断基準を D8-3 が提供する。

---

## 6. main branch の最終形状 (Day8 完了時)

### 6.1 commit history

```
b8c0e5b refactor(test): expand _scrub_timestamp to _scrub_volatile_lines  ← フェーズ 3
7bc009b refactor(env-loader): extract _inject_env_kv to fix --env-file path  ← フェーズ 2
d49dc58 fix(env-loader): overwrite empty existing env var with .env value  ← フェーズ 1
41075e6 docs(sessions): append Stage 2 results and lessons to PHASE_0...    ← Day7 (R+)
f746cc3 docs(sessions): archive day7 instructions and verification report   ← Day7 (U)
1428141 chore(gitignore): exclude editor save backups (*.save)              ← Day7 (Q-β)
4a1c618 test(overrides): align ref #141 assertion with publisher→journal rename  ← Day7 (P) ミス 2
4731b56 fix(fixtures): regenerate expected_phase2 without overrides         ← Day7 (P) ミス 1
92cd582 test(fixtures): regenerate Phase 0 expected outputs                 ← Day7 (β) X3
c4fa044 fix(overrides): map ref #141 publisher to journal field             ← Day7 (β) X1
2500ef6 docs(skill): add USAGE_QUICKSTART for immediate skill utilization
2ddea9d docs(templates): add reusable templates for phase/migration/day-record
91a572d docs(sessions): archive day6 instruction documents
... (Day1-Day6 commits omitted)
```

### 6.2 統計

| 指標 | 値 |
|:---|:---:|
| main commit count (Day8 完了時) | **31** (Day7 末 28 → +3) |
| test 健全性 | **62 passed, 1 skipped** (Day7 末 52 → +10) |
| 新規 test ファイル | `tests/test_env_loader.py` (Day8 で新設) |
| 改修ファイル | `main.py`, `tests/test_integration_149refs.py` |
| identity | 全 commit `Hideki Katayama <hikataya01@gmail.com>` |

---

## 7. 残存タスク (Day9 以降)

Day7 PHASE_0_VERIFICATION_REPORT §9 の更新版:

### 短期 (Day8 で完了)

- [x] main.py env loader の空値上書き対応 (`d49dc58` + `7bc009b`)
- [x] 環境依存フィールドの test 正規化拡張 (`b8c0e5b`)

### 中期 (Day9+ 着手推奨)

- [ ] **Vancouver/AMA 系 parser 改善** (Day7 §8.6 で発覚、24 件中 8 件 = 33% で title/author 境界誤認)
- [ ] **USAGE_QUICKSTART に parser 限界注記** (Day7 §8.8 学び 7.7)
- [ ] **API key セットアップ手順 docs 化** (`docs/operations/SETUP_API_KEYS.md` 等)
- [ ] **`~/.claude/skills/pubmed-reference-resolver.old.20260502/` 最終削除** (Day6 残課題、1-2 週間後の予定)

### 長期 (Day10+ 想定)

- [ ] 別ドメイン golden fixture (Vancouver / APA / Cell 等)
- [ ] MCP/hook 経由 Claude UI 起動配線 (Stage 3)

---

## 8. 次セッション再開時のプロンプトテンプレート

### パターン 1: 中期タスク着手

```
Day9 として、Vancouver/AMA 系 parser 改善
(docs/sessions/day7/PHASE_0_VERIFICATION_REPORT.md §8.6 / §9.2)
を実施します。docs/sessions/day8/DAY8_LESSONS_LEARNED.md と
PHASE_0_VERIFICATION_REPORT.md を読み込み、現状の MDPI fast-path 判定の
厳格化を TDD で検討してください。
```

### パターン 2: USAGE_QUICKSTART 更新

```
Day9 として、skill_package/references/USAGE_QUICKSTART.md に
parser 限界注記 (Day7 §8.8 学び 7.7) を追加します。Vancouver/AMA 系で
title/author 境界誤認が 24 件中 8 件 (33%) で発生したことを警告
セクションとして追加してください。
```

---

**記録完了日**: 2026/05/08
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day8 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day8.md` (Claude Opus 作成予定)
**ステータス**: Day8 archive 完成、Day9 着手準備完了
