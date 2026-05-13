# DAY11_LESSONS_LEARNED.md

**Day11 = Vancouver/AMA 系 golden fixture + 5 test の TDD 新設**

**作成日**: 2026/05/13
**作成者**: Claude Code (Sonnet 4.6)
**配置**: `docs/sessions/day11/DAY11_LESSONS_LEARNED.md`
**対応 commit 範囲**: `fe38298` + 本書 archive commit (計 2 commits)
**対応する指示書**: なし (先生からの単一プロンプトで開始、Day7 §9.3 long-term task 1 件目)

---

## 0. 本書の位置づけ

Day11 は Day7 PHASE_0_VERIFICATION_REPORT §9.3 long-term task の 1 件目 (「別ドメイン golden fixture」のうち Vancouver) を **TDD で完了**した. Day10 のような documentation update + cleanup と異なり、test infrastructure を 1 つ拡張する性質.

本書は以下を記録する:

1. Day11 のフェーズ構成 (1 commit + archive)
2. fixture 設計判断 — ハイブリッド命名規約 (`expected_*` / `baseline_*`) の理由
3. data-driven TDD の実例 (production code 修正なしで GREEN)
4. Day11 で抽出された教訓 3 件 (D11-1, D11-2, D11-3)
5. main branch 最終形状と Day12 への引継ぎ

---

## 1. Day11 のフェーズ構成

| フェーズ | commit | 達成 |
|:---:|:---:|:---|
| 1 | `fe38298` | Vancouver fixture (5 ファイル) + test (5 件) を TDD で新設 |
| 2 | (本 commit) | Day11 archive (README + LESSONS) |

---

## 2. fixture 設計判断 — ハイブリッド命名規約

### 2.1 出発点: MDPI fixture (149-ref) の構造

既存 `tests/fixtures/mdpi_149refs/` は全ファイル `expected_*` prefix:
- `expected_phase2_structured.json`
- `expected_phase3_resolved.json`
- `expected_journal_audit.json`
- `expected_report.md`

これは「fast-path で全件 deterministic、byte 一致が成立する」前提で成立する設計.

### 2.2 Vancouver fixture の課題

Day9 Vancouver Veto 採用により、Vancouver/AMA 系入力は **24 件全件が LLM 経路に routing** される. LLM (Claude Sonnet 4.6) の出力は決定論的でない (temperature, model update 等で変動). PubMed cascade も DB 状態に依存. → MDPI fixture 同様の「全 expected_* で byte 一致」型は **成立不能**.

### 2.3 採用した設計: ハイブリッド命名規約

`expected_*` と `baseline_*` を意味的に分離:

| prefix | 意味 | byte 一致要求 | 例 |
|:---|:---|:---:|:---|
| `expected_*` | deterministic な output (parser-only, no LLM) | ○ (golden) | `expected_phase1_intermediate.json` |
| `baseline_*` | variability-bearing な output (LLM/PubMed-dependent) | × (document-of-record) | `baseline_phase3_resolved.json`, `baseline_report.md` |

### 2.4 設計の本質

「**fast-path corpus は厳密 golden、LLM corpus は document-of-record**」という Day11 で確立された設計指針. これは Day9 Vancouver Veto 採用に伴う必然的な帰結であり、LLM 時代の test infrastructure 設計の汎用パターンとして他プロジェクトでも応用可能.

→ 学び D11-1 として教訓化.

---

## 3. data-driven TDD の実例

### 3.1 通常の TDD vs Day11 の TDD

| 項目 | 通常の TDD (Day8/Day9) | Day11 の TDD |
|:---|:---|:---|
| GREEN で何を書くか | production code | **fixture data file** (production code には触れない) |
| RED の失敗パターン | `feature missing` (関数未存在 / assertion 不一致) | **`FileNotFoundError`** (fixture 不在) |
| 修正の本質 | アルゴリズム改善 | データ凍結 |

### 3.2 Day11 のサイクル

**RED**: 5 test を tests/test_integration_vancouver_24refs.py に作成
- test 1-3: parser-only test (fixture の input docx を Phase 1 で再実行)
- test 4-5: baseline file の中身を assert
- 実行: 5 件全 fail (`FileNotFoundError`、fixture 5 ファイル不在のため)

**GREEN**: production code に触れず、fixture 5 ファイルを配置
- `input_References.docx` (OneDrive 参照.docx を cp + rename)
- `expected_phase1_intermediate.json` (Day9 (Z) 出力 cp)
- `baseline_phase3_resolved.json` (Day9 (Z) 出力 cp)
- `baseline_report.md` (Day9 (Z) 出力 cp)
- `README.md` (新規作成、由来 + 命名規約 + 更新運用)
- 実行: 5 件全 pass、全体 71 passed (Day10 末 66 → +5)

→ 学び D11-2 として教訓化.

---

## 4. Day11 で抽出された教訓 3 件

### 学び D11-1: ハイブリッド命名規約 (`expected_*` / `baseline_*`) は LLM 時代の golden test 設計パターン

**本質**: 全件 deterministic な fixture (MDPI 149-ref) に対しては従来の `expected_*` prefix で「byte 一致 golden」が成立するが、LLM/外部 API 経由の output を含む fixture では同じ設計は成立しない. `expected_*` (deterministic) と `baseline_*` (variability-bearing, document-of-record) を意味的に分離することで、両者を 1 つの fixture ディレクトリ内で共存させることができる.

**応用先**:
- 他プロジェクトの LLM ハイブリッド型 pipeline (例: 翻訳, 要約, 分類) でも同パターンが適用可能
- baseline 更新の運用方針を README に明記する慣行 (本 fixture では §5「baseline 更新の運用」table)
- variability の原因を 3 分類 (LLM update / 外部 DB drift / production code 改修) して、それぞれの対応を文書化

**Day1-10 既存学びとの関係**:
Day8 D8-1 (TDD だけでは捕捉できない問題) の test 設計版. 「全部 deterministic test で固める」アプローチは LLM 時代には限界があり、document-of-record という別カテゴリが必要.

### 学び D11-2: data-driven TDD (fixture data 配置で GREEN を達成する)

**本質**: TDD の Red-Green-Refactor サイクルにおいて、GREEN は通常 production code を書く段階だが、Day11 では **fixture data file の配置**で GREEN を達成した. これは「test を書く → data を凍結する」という data-as-code 的な workflow を TDD のフレームに収めた実例.

**応用先**:
- 既存実機データを fixture 化するときに TDD 順序が活きる (test 先行で「何を凍結すべきか」が明確化)
- production code 修正なしで test 数が増える運用 (regression coverage の拡張)
- 「fixture を最初に作る」のではなく「test を作って fail させる → fixture を後追いで配置」の順序が、不要な fixture data の配置を防ぐ

**Day1-10 既存学びとの関係**:
Day10 D10-2 (数値の出典明示) の運用版. 「baseline file は document-of-record として固定保管、必要な時だけ更新」という運用は、出典明示の責務を fixture 自身が担う.

### 学び D11-3: 「過去の検証成果を fixture 化する」 = 実機データの永続資産化

**本質**: Day9 (Z) production verification は「Day9 Vancouver Veto の動作確認」という単発目的だったが、その出力を Day11 で fixture 化することで「**未来の任意のセッションで過去の検証成果を再現可能 / 比較可能**」になった. 一過性の検証データが永続資産に転換される.

**応用先**:
- production verification は単発で終わらせず、**fixture 化を最初から想定した OUTDIR 設計**にする (例: 出力ディレクトリ命名に `_for_fixture` suffix を加える等)
- 重要な production data はリポジトリに取り込む (本 fixture では 117KB の `baseline_phase3_resolved.json` を git 管理対象に)
- archive (Day7-11) の DAY*_LESSONS_LEARNED.md でデータ出典 (background task ID, タイムスタンプ) を明記する慣行が、後日の fixture 化を容易にする

**Day1-10 既存学びとの関係**:
Day8 D8-1 (production 検証で TDD だけでは捕捉できない問題を発見) の発展. 「production 検証 → 実機データ → fixture」という連鎖が、検証努力の long-term ROI を最大化する.

---

## 5. main branch の最終形状 (Day11 完了時)

### 5.1 commit history (Day11 範囲)

```
(本 commit)  docs(sessions): archive day11 vancouver fixture session
fe38298      test(integration): add vancouver_24refs golden fixture + 5 tests
1dc8068      docs(sessions): archive day10 USAGE_QUICKSTART update + cleanup       ← Day10 末
... (Day1-Day10 commits omitted)
```

### 5.2 統計

| 指標 | 値 |
|:---|:---:|
| main commit count (Day11 完了時、本 commit 含む) | **40** (Day10 末 38 → +2) |
| test 健全性 | **71 passed, 1 skipped** (Day10 末 66 → +5) |
| 改修ファイル | (なし、production code 触れず) |
| 新規 fixture | `tests/fixtures/vancouver_24refs/` (5 ファイル、3300 lines insertions のうち 大半) |
| 新規 test | `tests/test_integration_vancouver_24refs.py` (5 test, 218 lines) |
| 新規 archive | `docs/sessions/day11/` (2 ファイル: README + LESSONS) |
| identity | 全 commit `Hideki Katayama <hikataya01@gmail.com>` |

### 5.3 Day11 の本質的な達成

1. **Day7 §9.3 long-term task の 1 件目完了** (Vancouver fixture 追加)
2. **ハイブリッド命名規約の確立** (`expected_*` / `baseline_*`)
3. **data-driven TDD パターンの実証** (production code 修正なしで GREEN)
4. **Day9 (Z) 実機検証成果の永続資産化** (一過性データ → 永続 fixture)

---

## 6. 残存タスク (Day12 以降)

Day7 PHASE_0_VERIFICATION_REPORT §9 の更新版 (Day11 完了反映):

### 6.1 短期 (Day8 で完了)

- [x] main.py env loader の空値上書き対応
- [x] 環境依存フィールドの test 正規化拡張

### 6.2 中期 (Day9-10 で 3 件完了、1 件残)

- [x] Vancouver/AMA 系 parser 改善 (Day9)
- [x] USAGE_QUICKSTART parser 限界注記 (Day10)
- [ ] **API key セットアップ手順 docs 化** (`docs/operations/SETUP_API_KEYS.md` 等) ← Day12 候補
- [x] 旧スキル削除 (Day10)

### 6.3 長期 (Day11 で 1 件部分完了)

- [x] **別ドメイン golden fixture (Vancouver)** ← Day11 完了 (APA / Cell は将来)
- [ ] APA / Cell 系 golden fixture (Vancouver と同じハイブリッド命名規約で) ← Day12+ 候補
- [ ] MCP/hook 経由 Claude UI 起動配線 (Stage 3)
- [ ] Day9 (Z) 残存未解決 2 件 (#17 Davey, #22 Gallina) の MEDLINE 非収録調査
- [ ] GitHub remote 追加と push

---

## 7. 次セッション再開時のプロンプトテンプレート

### パターン 1: API key セットアップ手順 docs 化

```
Day12 として、Day7 §9.2 中期タスクの最後の 1 件
「API key セットアップ手順 docs 化」を実施します.
docs/operations/SETUP_API_KEYS.md (or 同等パス) を新設し、
ANTHROPIC_API_KEY と NCBI_API_KEY の取得手順、
.env 配置方法、Day8 env loader 改修以降の挙動を docs 化してください.
```

### パターン 2: 別ドメイン (APA) golden fixture 追加

```
Day12 として、APA 系の golden fixture を新規追加します
(Day11 で確立された expected_*/baseline_* ハイブリッド命名規約を踏襲).
入力 docx をどう用意するかから議論してください
(Day9 (Z) のような既存実機データがない場合は、合成サンプルか、
別の実 docx を準備してもらう). TDD で進めてください.
```

### パターン 3: 未解決 2 件の MEDLINE 非収録調査

```
Day12 として、Day9 (Z) で残った未解決 2 件
(Ref #17 Davey 2003, Ref #22 Gallina 2016) を調査します.
docs/sessions/day9/DAY9_LESSONS_LEARNED.md §4.4 を参照し、
PubMed 検索 + 必要に応じて DOI 解決で MEDLINE 非収録の可能性を
検証してください.
```

---

**記録完了日**: 2026/05/13
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day11 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day11.md` (Claude Opus 作成予定)
**ステータス**: Day11 archive 完成、Day12 着手準備完了
