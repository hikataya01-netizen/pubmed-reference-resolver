# PHASE_0_VERIFICATION_REPORT.md

**Day7 = Phase ζ 第 2 相 (指示書外の動的判断作業) の事後記録**

**作成日**: 2026/05/02
**作成者**: Claude Code (Sonnet 4.6)
**配置**: `docs/sessions/day7/PHASE_0_VERIFICATION_REPORT.md`
**対応 commit 範囲**: `c4fa044` 〜 `1428141` (5 commits)
**対応する指示書**: なし (本作業は指示書外の動的判断による)

---

## 0. 本書の位置づけ

Phase ζ (Day7) は当初、`PHASE_ZETA_INSTRUCTIONS.md` に基づく 8 手順 (docs/sessions, docs/templates, USAGE_QUICKSTART の追加 = 3 commits) のみを想定していた。しかし第 1 相完了直後、先生から以下の追加要請があった:

> 実データのphase0検証を行います。どのようにすれば起動できますか。

これを契機として、**指示書のない動的判断による検証作業 = 第 2 相** が開始された。第 2 相は最終的に 5 commits を main branch に追加し、以下の達成事項をもたらした:

1. Day1-7 統合実装の test 健全性証明 (52 passed, 1 skipped)
2. 真の回帰 1 件 (`manual_overrides.yaml` ref #141 publisher → journal) の特定・修正
3. 設計改善 3 件 (#66 / #137 / #148) の golden 化
4. 私の実施ミス 2 件 (X3 fixture 上書き範囲の誤り、X1 後の test 修正漏れ) の解消
5. editor save backup の gitignore 化 (`*.save`)

本書は、これら 5 commits の連続発生の文脈を、後日の archaeological review のために記録する。

---

## 1. 経緯と判断の連鎖

### 1.1 起動方法の整理 (準備フェーズ)

先生の質問に対し、2 経路 × 3 段階で起動方法を整理して提示した:

| 経路 | 起動方法 |
|:---|:---|
| CLI 直接 | `python3 main.py <input> -o <output>` |
| Claude UI (skill 発火) | プロンプト + ファイル添付で自然言語起動 (現状未配線) |

| 段階 | 入力 | 想定時間 | 必要な準備 |
|:---:|:---|:---:|:---|
| Stage 1 | `tests/fixtures/mdpi_149refs/input_References.docx` (149 件 MDPI、smoke test) | 5-15 分 | なし |
| Stage 2 | 先生の手元の実 PDF/DOCX (本番ライク) | 入力次第 | pdfplumber + NCBI/Anthropic API key |
| Stage 3 | Claude UI 経由 | — | MCP/hook 配線 (Day8 以降) |

### 1.2 Stage 2 への直接ジャンプ試行 (失敗)

先生が OneDrive の実 DOCX (`参照.docx`, 29819 bytes) を Stage 2 入力として実行を試みたが、シェルでの path 結合事故で失敗:

```
入力意図: tests/fixtures/...input_/Users/.../参照.docx
実態:    2 つのパスが結合されてエラー (input not found)
```

→ 先生の判断で **Stage 1 (smoke test) を私が代行実行**する方針に転換。

### 1.3 Stage 1 起動と一次結果

```bash
python3 main.py tests/fixtures/mdpi_149refs/input_References.docx \
    -o /tmp/phase0_smoke_<ts>/ \
    --no-env-file \
    --overrides integration/src/manual_overrides.yaml
```

- 開始: 13:50:25 (background task 起動時刻)
- 終了: 17:38:06 (run.log 完了時刻)
- exit code: **0** (完走)

私は当初「実行時間 3 時間 48 分」と判定したが、これは誤り。run.log の `Starting at 17:34:28` / `Finished at 17:38:06` の差から、実際の python 実行は **3 分 38 秒** (内 Phase 3 の PubMed cascade が 214.7 秒)。13:50→17:34 の 3:44 は MacBook Air のシステムスリープによる background task の suspend (実 CPU 時間消費なし) と推定。

---

## 2. 比較分析の 3 分類

完走した 4 出力ファイルを既存 expected fixture と byte 比較:

| 出力 | expected | 結果 |
|:---|:---|:---|
| `journal_mismatch_audit.json` | `expected_journal_audit.json` | ✅ 完全一致 |
| `phase2_structured.json` | `expected_phase2_structured.json` | ⚠️ 微差 (-46 B、80 行) |
| `phase3_resolved.json` | `expected_phase3_resolved.json` | ⚠️ 微差 (+128 B、89 行) |
| `report.md` | `expected_report.md` | ⚠️ 微差 (+314 B、50 行) |

差分を性格別に 3 分類:

- **A. 環境依存** (実害なし): `input_file` path、`report.md` の実行タイムスタンプ、PubMed title 文字列の時間経過更新による fuzzy score 変動
- **B. 改善** (現在実装の方が正しい): split_references が ref #39/#40 と #139/#140 を正しく分離 (旧 fixture では結合状態)
- **C. 回帰候補**: ref #141 の book publisher 情報喪失、ref #74 周辺の override 動作変更、ref #148 の smart quote 処理

---

## 3. 回帰候補 4 件の真因解析

詳細解析の結果、当初 3 件と思われた回帰候補は実際 **4 件**で、うち真の回帰は 1 件のみと判明:

| ケース | ref | 性質 | 真因 | 判定 |
|:---:|:---:|:---|:---|:---|
| C-1 | #66 | 設計改善 | 旧実装の DOI prefix 自動推論を撤廃、manual_overrides.yaml で明示する方針に変更 | 受容 (より監査可能) |
| **C-2** | **#141** | **★真の回帰★** | manual_overrides.yaml の `publisher` キーは `_apply_overrides()` (main.py:619) で field 名そのまま転写されるため `new_entry['publisher']` に格納され、`journal` field には反映されない。旧実装は book 限定で `publisher → journal` 自動転写ロジックがあった疑い | **要対処** |
| C-3 | #148 | 設計改善 | manual_overrides.yaml の title 値が smart quote で記述、現在実装はそのまま採用 (raw 保持原則)。旧実装は post-process で straight quote に正規化していた疑い | 受容 |
| C-4 | #137 | 設計改善 | 新実装は override 適用時に `'override applied for: <fields>'` marker を notes に追記する仕様 (main.py:623) | 受容 (audit 改善) |

特に C-2 は「`manual_overrides.yaml` に publisher を書いても無視される」という実害があり、**修正必要**と判定。先生の判断を仰ぐため対応案を提示:

| 案 | 内容 |
|:---:|:---|
| α | X1 のみ (yaml で `publisher` → `journal` rename) |
| β | X1 + X3 (yaml 修正 + 4 fixture 全更新を 2 commit に分離) |
| γ | X2 (main.py に publisher → journal 転写ロジック追加) |
| δ | 判断保留、Stage 2 に進行 |
| ε | Day7 結果として記録のみ |

→ 先生のご判断: **(β)**

---

## 4. (β) 実施と pytest 発覚問題

### 4.1 計画通りの 2 commit (commit #4-5)

| commit | 種別 | 内容 |
|:---:|:---|:---|
| `c4fa044` | fix(overrides) | yaml の `publisher: "Oxford..."` → `journal: "Oxford..."` rename + コメント更新 |
| `92cd582` | test(fixtures) | smoke test 再実行 (3:52、X1 適用後) → 出力で 4 expected fixture を更新 (ただし `expected_journal_audit.json` は内容無変更で diff 無し) |

### 4.2 (P) pytest による完全性検証で発覚した 2 件のミス

私の判断で「Stage 1 完了 + (β) 完了 = 完結」とせず、**(P) pytest 実行**を提案。先生の判断で実行 → 2 件の test failure が発覚:

**ミス 1**: `test_structure_all_references_with_fast_path_matches_golden` failure
- 真因: 私が (β) X3 で `expected_phase2_structured.json` を smoke test (overrides 適用済) の出力で上書きしたが、当該 test は `structure_all_references()` を `overrides=None` で呼ぶ parser-only 設計
- 結果: `Ref #66 field=journal: got=None expected='Psicooncología'` (override 適用差)
- 修正: `--phase 2 --overrides 指定なし` で再生成 (実行時間 0.22 秒)、`expected_phase2_structured.json` を上書き

**ミス 2**: `test_apply_overrides_ref141_matches_expected` failure
- 真因: X1 で yaml の field 名を rename した際、対応する test の assert (line 86, 94) を更新し忘れた
- 結果: `KeyError: 'publisher'` (`assert post["publisher"] == "Oxford University Press"`)
- 修正: test の `post["publisher"]` → `post["journal"]`、`"publisher" in post["notes"]` → `"journal" in post["notes"]`

### 4.3 ミス対応の 2 commit (commit #6-7)

| commit | 種別 | 内容 |
|:---:|:---|:---|
| `4731b56` | fix(fixtures) | parser-only 出力で `expected_phase2_structured.json` を再生成 |
| `4a1c618` | test(overrides) | `test_overrides_contract.py` の 2 assertion を `journal` field 参照に更新 |

最終的に **52 passed, 1 skipped** (skipped は LLM 必要な条件付きで仕様通り)。

---

## 5. (Q-β) gitignore 強化 (commit #8)

(P) 完了後、(Q) として「skill_package/.env.save」 (Day7 朝 13:28 に発生した nano 経由の編集 backup) の処理判断を求めた。

ファイル素性:
- サイズ 1 byte、内容 `0x0a` (LF のみ、実質空)
- パーミッション 600 (機密ファイル慣習)
- `.gitignore` で除外されておらず、`git add .` で混入リスクあり

→ 先生のご判断: **(Q-β)** = `.gitignore` 強化 + 削除 + commit

| commit | 種別 | 内容 |
|:---:|:---|:---|
| `1428141` | chore(gitignore) | `*.save` パターン追加 + `skill_package/.env.save` 削除 |

---

## 6. 第 2 相 5 commits の最終形状

```
1428141 chore(gitignore): exclude editor save backups (*.save)              ← (Q-β)
4a1c618 test(overrides): align ref #141 assertion with publisher→journal rename  ← (P) ミス 2 修正
4731b56 fix(fixtures): regenerate expected_phase2 without overrides         ← (P) ミス 1 修正
92cd582 test(fixtures): regenerate Phase 0 expected outputs                 ← (β) X3
c4fa044 fix(overrides): map ref #141 publisher to journal field             ← (β) X1
```

第 1 相 3 commits を含めた Day7 計 8 commits、main branch は 18 → 26 commits に到達。

---

## 7. 検証メソッドとして抽出される論点 (Day7 学び候補)

### 7.1 「fixture 再生成」の semantic 整合性

`expected_*.json` には複数の semantic レイヤーがある:
- parser-only 状態 (`expected_phase2_structured.json`)
- parser + overrides 適用後 (`expected_phase3_resolved.json`)
- post-synthesize 出力 (`expected_report.md`, `expected_journal_audit.json`)

smoke test (main.py 全体実行) の出力は overrides 適用後だが、parser-only test との契約を破る。**fixture 再生成時は対応する test の入力契約を明示的に確認する必要がある** (= 私の (β) X3 のミスから抽出される教訓)。

### 7.2 「コード変更」と「対応 test 変更」の同期義務

X1 で yaml の field 名を rename した際、対応する `test_overrides_contract.py` の assert 更新を忘れた。これは「ある変更を加えたら、それを assert している test を全件確認する」原則の不徹底。

→ Day8 以降は yaml 等の field 名変更時に `grep -rn "<old field name>" tests/` を mandatory step に追加する運用が望ましい。

### 7.3 「指示書外の動的判断作業」の文書化義務

Phase ζ 第 2 相 5 commits は元の指示書 (PHASE_ZETA_INSTRUCTIONS.md) には含まれない。後日 commit history のみを見ると「なぜこれらが連続して発生したか」の文脈が失われる。

→ 本書 (`PHASE_0_VERIFICATION_REPORT.md`) のような事後記録を、指示書外作業に対しては必須とする運用が望ましい (Day7 で初めて実践)。

### 7.4 「実行時間判定」のメトリクス整理

私は当初「実行時間 3:48」と誤判定した。原因は以下のメトリクスを混同したため:
- background task 起動時刻 (= mkdir の date stamp、13:50)
- 実 python 実行開始時刻 (= run.log の `Starting at`、17:34)
- 実 python 実行終了時刻 (= run.log の `Finished at`、17:38)

正しい実行時間は run.log の Starting/Finished の差 (= 3:38)。MacBook Air のシステムスリープが background task を suspend していた可能性が高い。

→ 今後の background 起動時は、log file の冒頭に `date` を必ず書き、wall clock 比較時は log file 内のタイムスタンプを正とする。

### 7.5 「副次的成果としてのテスト健全性証明」

(P) pytest 実行は当初 (β) のオプション扱いだったが、結果として 2 件のミスを発見した。Phase 0 検証 (smoke test) と test 健全性検証 (pytest) は**性質の異なる 2 層の verification**であり、両方を実施することで初めて「Day1-7 統合実装の健全性」が証明される (Day6 P12 = 副次的成果としてのリアルタイム検証 の系統)。

---

## 8. 残存タスク

- **Stage 2 (実 OneDrive `参照.docx`) 検証** (Phase 0 の本来目的、別セッションでの実施推奨)
- **環境依存フィールドの test 正規化拡張** (`input_file` path masking 等、現状は timestamp のみ scrubbing)
- **Anthropic API key + NCBI API key の取得・設定手順 docs 化** (Stage 2 前の準備)
- **`~/.claude/skills/pubmed-reference-resolver.old.20260502/` 最終削除** (Day6 残課題、1-2 週間後)

---

**記録完了日**: 2026/05/02
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day7 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day7.md` (Claude Opus 4.7 が別途作成予定)
