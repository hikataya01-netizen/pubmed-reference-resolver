# DAY15_LESSONS_LEARNED.md

**Day15 = Day13 §6 改修候補 A (audit_report に 3 分類 logic 追加) の完全実装**

**作成日**: 2026/05/16
**作成者**: Claude Code (Sonnet 4.6)
**配置**: `docs/sessions/day15/DAY15_LESSONS_LEARNED.md`
**対応 commit 範囲**: `aee0ae2` (SPEC) + `f30e8e1` 〜 `6707d0a` + 本書 archive commit (計 8 commits)
**対応する指示書**: なし (Day14 §7 推奨案を user 単発指示「続きを進めて下さい」で開始)

---

## 0. 本書の位置づけ

Day15 は Day13 INVESTIGATION で発見した「PubMed 未ヒット 3 分類」を audit_report に実装した. Day13 §6 改修候補 4 案のうち最後の 1 件 (案 A、大規模) を完了し、Day13 → Day14 (docs 反映) → Day15 (logic 実装) の **3 セッション連鎖**が完結.

本書は以下を記録する:

1. Day15 のフェーズ構成 (Phase 0-6 の 7 commits + SPEC 1 + archive)
2. brainstorming → SPEC → TDD → 実機検証の 4 段階フロー実例
3. Phase 4 で発覚した regression と対処
4. Day15 で抽出された教訓 3 件 (D15-1, D15-2, D15-3)
5. main branch 最終形状と Day16 への引継ぎ

---

## 1. Day15 のフェーズ構成

| フェーズ | commit | 内容 |
|:---:|:---:|:---|
| (前) | `aee0ae2` | brainstorming → SPEC 419 行を archive |
| 0 | `f30e8e1` | fixture 7 件 + README (Day13 curl 出力を凍結) |
| 1 | `ba4de85` | crossref_check module (~110 行) + test 2 (RED→GREEN) |
| 2 | `3d232d2` | nlm_catalog_check module (~150 行) + test 2 (RED→GREEN) |
| 3 | `71a318a` | three_class_classifier module (~150 行) + test 5 (RED→GREEN) |
| 4 | `132ffab` | main.py 改修 (synthesize_outputs + write_report) + Vancouver test 1 + expected_report.md 再生成 |
| 5 | `6707d0a` | USAGE_QUICKSTART 1.2 → 1.3 bump |
| 6 | (本) | Day15 archive (README + LESSONS) |

各 phase は TDD cycle (RED → GREEN) で完結、Phase 0 は test infrastructure として独立 commit (Day9 の SPEC §7 5 commits 計画から +2 件 = 7 commits、軽微 deviation で Phase 0 fixture と Phase 6 archive を追加).

---

## 2. brainstorming → SPEC → TDD → 実機検証の 4 段階フロー実例

### 2.1 brainstorming (Q1-Q4)

| Q | 論点 | 採用 |
|:---:|:---|:---|
| Q1 | 規模 scope | 案 2 (段階的中規模、独立 2 module + 統合 logic、1 session) |
| Q2 | API call timing | (b) Phase 4 audit 中 (Phase 3 触らない、MDPI fixture 再生成不要) |
| Q3 | test 戦略 | (γ) fixture-based (Day13 取得済 API 応答を凍結、Day11 規約準拠) |
| Q4 | fail-soft | (ii) graceful unknown (timeout 10s, retry 1 回, stderr WARN) |

各質問は **2-3 案 + 推奨明示 + 即着手** パターン (Day10 D10-1 過剰確認回避).

### 2.2 SPEC (12 章、419 行)

`docs/sessions/day15/SPEC_three_class_audit.md` に書き込み + commit (`aee0ae2`). brainstorming skill rule の HARD-GATE (設計承認まで実装に入らない) を遵守、user approval 取得後 TDD 開始.

### 2.3 TDD (Phase 0-5)

各 phase で RED → GREEN cycle:
- Phase 0: fixture file 配置 (test infrastructure)
- Phase 1-3: 各 module を test-first で実装 (RED = `ModuleNotFoundError`、GREEN = module 追加で pass)
- Phase 4: synthesize_outputs 統合 + Vancouver test 8 + regression 対応 (詳細 §3)
- Phase 5: USAGE_QUICKSTART 1.3 bump (docs only、test 影響なし)

### 2.4 実機検証は本 SPEC scope 外

本 SPEC では fixture-based test で検証. live API 経由の実機検証 (Day9 (Z) のような Stage 2 retry) は Day16+ 候補. ただし Phase 4 で **MDPI 149-ref expected_report.md 再生成**時に live-like な動作 (stub 経由) が確認された.

---

## 3. Phase 4 で発覚した regression と対処

### 3.1 経緯

Phase 4 で synthesize_outputs に 3 分類 logic を統合した直後、Vancouver test 8 (新) は pass したが、**既存 test_synthesize_outputs_report_matches_expected (MDPI 149-ref) で fail** が発生.

### 3.2 原因解析

- 私の事前認識: 「MDPI 149-ref では全件解決 → unresolved 0 件 → classifications 空 → report.md 不変」
- 実態: MDPI 149-ref fixture には **34 件未解決 ref がある** (Day7 §8.4 で 115/149 解決と判明済を私が失念)
- 結果: synthesize_outputs 内で classify_unresolved_refs が 34 件分の live API call を試行 → SSL 証明書エラー (`CERTIFICATE_VERIFY_FAILED`) で全件 unknown 分類 → report.md に 3 分類 sub-section 追加 → expected_report.md と byte 差分

### 3.3 対処 (2 段階)

1. **synthesize_output fixture 改修**: stub 関数 (`crossref_fn` / `nlm_fn` で always-error 返却) を注入し、live API call を skip.
2. **expected_report.md 再生成**: stub 経由で全 34 件 unknown 分類された状態で report.md を生成、これを新 expected として上書き (Day9 X3 と同パターン).

### 3.4 学びとしての位置づけ

Day9 D9-1 (実装段階で SPEC 想定外発覚) と同系統. SPEC §6.1 で「test 設計」を網羅したつもりが、既存 test の互換性影響を見落とした. → 学び D15-1 として教訓化.

---

## 4. Day15 で抽出された教訓 3 件

### 学び D15-1: SPEC 設計時に「既存 test の互換性影響」を必ず確認する

**本質**: Day15 SPEC §6.1 で「新 test 8 件」「全 79 passed」を計画したが、実装 Phase 4 で「既存 test の前提条件 (MDPI 149-ref では全件解決という思い込み) が誤り」と判明し、regression が発生. SPEC 設計段階で **既存 test を逐一確認する step** が欠落していた.

**応用先**:
- SPEC 作成時に「対象 module を import / 呼出している既存 test の網羅 list」を必須項目に追加
- 各既存 test について「本改修で挙動が変わるか」を評価し、必要なら fixture 更新 / test 改修を SPEC §11 完了条件に明記
- regression 発覚時は Day9 D9-1 と同パターン (commit message で deviation 明示) で対処

**Day1-14 既存学びとの関係**:
Day9 D9-1 (実装段階で順序問題発覚) の「SPEC 設計時の互換性チェック不足」版. D9-1 はロジック設計、D15-1 は test 互換性、両者ともに「SPEC ≠ 実装」のギャップを記録.

### 学び D15-2: 多モジュール改修では fixture を最初に揃える価値

**本質**: Phase 0 で 7 fixture file を一括配置してから Phase 1-3 の TDD に進む構成が機能した. 各 phase で test 書く時点で全 fixture が揃っているため、test failure の真因が「fixture 不在」か「production 不在」か明確に切り分けられる.

**応用先**:
- 多モジュール改修 (3 module 以上) では fixture 配置を独立 commit (Phase 0 相当) として分離
- fixture commit message に「使用される後続 phase の対応関係」を明示
- README.md に各 fixture の出所・用途・refresh 運用を documented (Day11 規約)

**Day1-14 既存学びとの関係**:
Day11 D11-2 (data-driven TDD) + Day11 D11-3 (実機データの永続資産化) の運用パターン版. Day11 は単一 fixture セット、Day15 は 3 module 跨ぎの fixture 統合管理.

### 学び D15-3: 「skip-by-default」default を持たないテスト用 DI が clean

**本質**: synthesize_outputs に `crossref_fn=None, nlm_fn=None` 引数を追加し、None なら production の live API call、test では fixture-bound fake を渡せる設計を採用. これは:
- production interface を汚染しない (default None なので caller は気にしない)
- test 内で明示的に fake を渡すため挙動が予測可能
- 既存 caller (run_phase4 等) は変更不要

**応用先**:
- 外部 API 依存の関数を test する際は **依存性注入 (DI) for testing** パターンを採用
- `default=None` で production と test の dispatch を実現
- 「skip フラグ」(`enable_three_class=False` のような) より「DI で挙動置換」が clean

**Day1-14 既存学びとの関係**:
Day8 D8-3 (関数 extract で重複排除) の「test 容易性」版. D8-3 は production code の DRY、D15-3 は test との境界面設計.

---

## 5. main branch の最終形状 (Day15 完了時)

### 5.1 commit history (Day15 範囲)

```
(本 commit)  docs(sessions): archive day15 three_class audit session
6707d0a      docs(skill): bump USAGE_QUICKSTART to 1.3 (Day15 audit logic 実装完了反映)
132ffab      feat(synthesize): integrate three_class into Phase 4 audit_report (Day15 Phase 4)
71a318a      feat(audit): add three_class_classifier integrating crossref + nlm (Day15 Phase 3)
3d232d2      feat(nlm): add nlm_catalog_check module + 2 fixture-based tests (Day15 Phase 2)
ba4de85      feat(crossref): add crossref_check module + 2 fixture-based tests (Day15 Phase 1)
f30e8e1      test(fixtures): add three_class_classification fixtures from Day13 curl re-runs
aee0ae2      docs(spec): add Day15 SPEC for three_class_audit (Day13 §6 案 A)
b7b2014      docs(sessions): archive day14 3-class docs reflection                ← Day14 末
```

### 5.2 統計

| 指標 | 値 |
|:---|:---:|
| main commit count (Day15 完了時、本 commit 含む) | **53** (Day14 末 45 → +8) |
| test 健全性 | **81 passed, 1 skipped** (Day14 末 71 → +10) |
| 新規 module | 3 (`crossref_check.py`, `nlm_catalog_check.py`, `three_class_classifier.py`) |
| 改修 module | `main.py` (`synthesize_outputs`, `write_report`) |
| 新規 test | 9 (`test_crossref_check.py` 2, `test_nlm_catalog_check.py` 2, `test_three_class_classifier.py` 5, Vancouver test 1, MDPI fixture stub 改修 = 8 新規 + 1 既存改修 = +10 net) |
| 新規 fixture | 7 file + README (`tests/fixtures/three_class_classification/`) |
| 新規 archive | `docs/sessions/day15/` (3 ファイル: SPEC + LESSONS + README) |
| identity | 全 commit `Hideki Katayama <hikataya01@gmail.com>` |

### 5.3 Day15 の本質的な達成

1. **Day13 §6 改修候補 A (大規模) を 1 session で完了** (brainstorming + SPEC + TDD)
2. **Day13 → Day14 → Day15 の 3 セッション連鎖が完結** (調査 → docs 反映 → logic 実装)
3. **3 新 module 追加 + main.py 改修 + 7 fixture + 8 test** を 7 commits に整理
4. **SPEC §11 完了条件 79 → 実装 81 passed** で超過達成
5. **archive 連鎖 10 連続達成** (Day6-15)

---

## 6. 残存タスク (Day16 以降)

### 6.1 Day7 §9.3 long-term task の達成状況

| タスク | 状態 | commit |
|:---|:---:|:---:|
| Vancouver golden fixture | ✅ Day11 | `fe38298` |
| Day9 (Z) 未解決 2 件 MEDLINE 非収録調査 | ✅ Day13 | `a2ee5ae` |
| **Day13 §6 案 A: 3 分類 audit logic** | ✅ **Day15** | `132ffab` (+ 関連 6 commits) |
| APA / Cell 系 golden fixture | ⏳ Day16+ |  |
| MCP/hook 経由 Claude UI 起動配線 (Stage 3) | ⏳ Day16+ |  |
| GitHub remote 追加と push | ⏳ Day16+ |  |

### 6.2 Day15 が生成した新規候補 (3 分類 audit の拡張)

- [ ] **A 分類 (真の捏造) 検証の真実例 fixture 追加** (現状 synthetic 404 のみ. 将来 user 提供時にハルシネーション実例 fixture 化)
- [ ] **B 分類の細分化** (predatory journal vs new journal vs regional journal の区別)
- [ ] **他 DB 補助検証** (Scopus / OpenAlex 等で B/C 判定の精度向上)
- [ ] **(δ) hybrid test** (live API call test の skip-by-default 実装、Day15 SPEC §8 Out of Scope)
- [ ] **report.md sub-section の format 改善** (現状 table 表示、各 ref の details JSON 抜粋を加える等)

### 6.3 Day7 §9 残存タスク (Day16+ 推奨着手順)

- [ ] APA / Cell 系 golden fixture (Day11 ハイブリッド命名規約踏襲、Day9 (Z) のような実機データ要確認)
- [ ] GitHub remote 追加と push (secret scan + README 整備、外部公開判断要)
- [ ] MCP/hook 経由 Claude UI 起動配線 (Stage 3、設計議論大、複数セッション)
- [ ] 上記 §6.2 の拡張 (3 分類 audit の精緻化)

---

## 7. 次セッション再開時のプロンプトテンプレート

### パターン 1: Day7 §9.3 残タスク (APA fixture)

```
Day16 として、APA 系の golden fixture を新規追加します
(Day11 で確立された expected_*/baseline_* ハイブリッド命名規約を踏襲).
入力 docx をどう用意するかから議論してください
(Day9 (Z) のような既存実機データがない場合は、合成サンプルか、
別の実 docx を準備してもらう). TDD で進めてください.
```

### パターン 2: Day15 §6.2 拡張 (3 分類 audit の精緻化)

```
Day16 として、Day15 で実装した 3 分類 audit の拡張を実施します.
docs/sessions/day15/DAY15_LESSONS_LEARNED.md §6.2 から具体的な
拡張候補を選び、brainstorming → SPEC → TDD で進めてください.
(候補: A 分類実例 fixture / B 分類細分化 / 他 DB 検証 / hybrid test
/ report.md format 改善)
```

### パターン 3: GitHub remote + push

```
Day16 として、本プロジェクトを GitHub に push します.
remote 設定 → 既存 53 commits + 全 fixture を含めて push.
公開リポジトリ vs プライベート の選択、README.md の整備、
.gitignore 最終確認、secret scan を含めて段階確認しながら進めて
ください.
```

### パターン 4: 実機検証 (Stage 2 retry with 3 分類 logic)

```
Day16 として、Day15 で実装した 3 分類 logic の実機検証を行います.
Stage 2 (OneDrive 参照.docx) を Day9 (Z) と同コマンドで再実行し、
three_class_classification.json sidecar に #17→C, #22→B が live
API 経由で記録されることを確認してください. 結果を
docs/sessions/day16/ に記録してください.
```

---

**記録完了日**: 2026/05/16 (Day15)
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day15 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day15.md` (Claude Opus 作成予定)
**ステータス**: Day15 archive 完成、Day16 着手準備完了 (4 候補プロンプトあり)
