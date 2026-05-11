# SPEC_mdpi_fast_path_strict.md

**目的**: `is_mdpi_style()` の Vancouver 検出を強化し、Stage 2 (Vancouver 系入力) で観測された parser 限界 (24 件中 8 件 = 33% で title/author 境界誤認) を解消する.

**作成日**: 2026/05/09 (Day9)
**作成者**: Claude Code (Sonnet 4.6)
**承認**: 片山英樹 (Hideki Katayama) — 2026/05/09 brainstorm 段階で大筋 approval 取得済
**配置**: `docs/sessions/day9/SPEC_mdpi_fast_path_strict.md`
**配置の理由**: brainstorming skill の default は `docs/superpowers/specs/` だが、本プロジェクトの慣例 (`docs/sessions/dayN/`) と Day9 archive 統合性を優先. Day9 完了後は SPEC + 実装 + LESSONS_LEARNED が同一ディレクトリに揃う.

---

## 1. 経緯

### 1.1 Day7 で発覚した parser 限界

Day7 PHASE_0_VERIFICATION_REPORT §8.6 で、Stage 2 実データ検証 (OneDrive `参照.docx`, 24 件 Vancouver/AMA 系) において以下が判明した:

- 解決率 14/24 = 58.3% (DOI 経由 11、PMID direct 2、title+author+year 1)
- 未解決 10 件のうち過半数で **title フィールドが空または著者名のみ**
- 重大エラー 4 件のうち 3 件は **parser 起因の false positive** (parser が著者リスト末尾を title と誤認)
- **24 件中 8 件 (33%) で MDPI fast-path が title/author 境界を誤処理**

### 1.2 Day8 で発見した補強教訓

Day8 DAY8_LESSONS_LEARNED §5 で:

- **D8-1**: ユニット test だけでは production 環境固有の問題を捉えきれない
- **D8-2**: "同じロジックが 2 箇所" code smell を bug 修正前に必ず grep で検出する
- **D8-3**: 関数 extract で重複排除 + 将来の regression 予防

これらは Day9 の改修にも応用可能 (特に D8-2: 既存 markers と新 marker の重複/補完関係を測定で検証).

### 1.3 Day9 開始

先生から単一プロンプト:

> Day9 として、Vancouver/AMA 系 parser 改善
> (docs/sessions/day7/PHASE_0_VERIFICATION_REPORT.md §8.6 / §9.2)
> を実施します。docs/sessions/day8/DAY8_LESSONS_LEARNED.md と
> PHASE_0_VERIFICATION_REPORT.md を読み込み、現状の MDPI fast-path
> 判定の厳格化を TDD で検討してください。

→ brainstorming skill 起動、Q1-Q3 で方針確定.

---

## 2. 問題分析

### 2.1 MDPI 形式 vs Vancouver 形式の決定的な区別

| 観点 | MDPI (149-ref fixture) | Vancouver (Stage 2 OneDrive) |
|:---|:---|:---|
| **著者区切り** | `;` セミコロン | `,` カンマ |
| **年位置** | `YYYY, Vol` (前置コンマ) | **`(YYYY)` 括弧年** |
| **pages** | `Vol, Pages` | **`Vol(Iss):Pages` 括弧形式** |
| **DOI prefix** | `https://doi.org/` | `doi: ...` (時々混在) |

### 2.2 現状の `is_mdpi_style()` の挙動 (mdpi_parser.py:372-412)

判定基準 (5 段階):

1. **必須**: `_AUTHOR_ITEM_RE` (Surname, I.Y.; 形式) が最低 1 名
2. (a) `\s\d{4}\s*,\s*\d+` (末尾に `YYYY, Vol`)
3. (b) `doi.org/` 含む
4. (c) ISBN または `_BOOK_SIGNS_RE`
5. (d) Vancouver/AMA markers (`Smith J, Lee K,` パターン or `;Vol:Pages`) → False
6. (e) 上記いずれにも該当しない = 不完全 MDPI と仮定して True

### 2.3 既存 Vancouver markers の機能不全 (実測)

Day9 brainstorm で測定:

| Marker | MDPI 149-ref hit | Vancouver 24-ref hit |
|:---|:---:|:---:|
| 既存 marker A (`Smith J, Lee K,`) | 0/149 | **1/24 (#6 のみ)** |
| 既存 marker B (`;Vol:Pages`) | 0/149 | **0/24** |

→ 既存 markers は Vancouver 検出にほぼ無効 (4%). MDPI fixture には影響なし (撤去しても安全).

### 2.4 新 Marker M1 (`(YYYY)` 括弧年) の評価

| Marker | MDPI 149-ref hit | Vancouver 24-ref hit |
|:---|:---:|:---:|
| **M1 (`(YYYY)`)** | **0/149** | **24/24** |

→ M1 は Vancouver 100% 捕捉 + MDPI 0 件影響の **完璧な marker**. 既存 markers の真上位互換.

---

## 3. 採用方針 (Q1-Q3 brainstorm 結果)

### Q1: 改修方針の大筋 → **案 A 採用**

| 案 | 内容 | 採否 |
|:---:|:---|:---:|
| **A** | Vancouver/AMA 検出 regex を追加 (`is_mdpi_style()` の (d) ブロック強化) | **採用** |
| C | MDPI ホワイトリスト方式 (判定ロジック大幅変更、`;` 区切り著者必須化) | 不採用 (規模過大) |
| A+C 組合せ | 全方位的 | 不採用 (Day9 単独完結性低い) |

### Q2: 採用する marker のセット → **案 A (M1 のみ)**

| 案 | marker セット | 採否 |
|:---:|:---|:---:|
| **A** | **M1 のみ** | **採用** (24/24 + 0/149、完璧) |
| B | M1 + M2 | 不採用 (M2 は冗長) |
| C, D | より多 markers | 不採用 (regression リスク) |

### Q3: 既存 Vancouver markers の扱い → **撤去**

| 案 | 内容 | 採否 |
|:---:|:---|:---:|
| **撤去** | line 405-408 の 2 markers を削除し、M1 のみで置換 | **採用** |
| 保持 | 既存 markers + M1 (OR 連鎖) | 不採用 (DRY 違反) |
| 部分保持 | A のみ残す | 不採用 (実用上撤去で問題なし) |

---

## 4. 実装設計

### 4.1 変更箇所

**ファイル**: `mdpi_parser.py` 1 ファイルのみ
**範囲**: `is_mdpi_style()` 関数内、著者チェック直後 (Vancouver Veto = 最優先 early return) + 旧 (d) ブロック (line 401-410) の撤去
**変更性質**: 規則 2 本の撤去 + 規則 1 本 (M1) の追加 + **配置位置の変更** = **net -1 規則**

**重要 (Day9 実装段階で確定)**:
SPEC 初版では M1 を旧 (d) ブロック位置 (line 401-410) に置く設計だったが、TDD verify GREEN 段階で順序問題が発覚:
- (b) `doi.org/` 等 を含む Vancouver ref (例: Stage 2 #1 Huizinga 2011 `doi.org/10.1002/pon.1779`) が、(d) に到達する前に (b) で True を返してしまう
- 解決: M1 を**著者チェック直後**に moved up し、Vancouver Veto = 最優先 early return とした
- 設計の本質 (Vancouver indicator が dominant) は維持、配置位置のみ変更
- 詳細: docs/sessions/day9/DAY9_LESSONS_LEARNED.md (本実装の commit `ab25630`)

### 4.2 Before / After

**Before** (旧設計、line 401-410):

```python
# (d) Vancouver/AMA 系の特徴検出 (これらは LLM にルーティング)
#     例: "Smith J, Lee K. Title. Journal 2024;10:100-5."
#     - "Surname I" (ピリオドなしイニシャル) + "," 連続
#     - ";VOLUME:PAGES" パターン
vancouver_markers = (
    re.search(r"[A-Z][a-z]+ [A-Z]{1,3},\s+[A-Z][a-z]+ [A-Z]{1,3}[,.]", raw)
    or re.search(r";\d+:\d+", raw)
)
if vancouver_markers:
    return False
```

**After (実装版、Day9 commit `ab25630`)**:

```python
# 著者パターン (最低1名必須)
if not _AUTHOR_ITEM_RE.search(raw):
    return False
# Vancouver Veto: "(YYYY)" 括弧年が見つかれば LLM ルーティング (Day9 で導入)
#   このチェックは (a)(b)(c) より前に置く必要がある:
#   さもないと "doi.org/..." 等を含む Vancouver ref が (b) で True を返してしまう
#   (Stage 2 #1 Huizinga 2011 等が該当). SPEC §4.2 から実装段階で順序修正.
if re.search(r"\((?:19|20)\d{2}\)", raw):
    return False
# (a) 標準的 MDPI 末尾パターン
...
# (旧 (d) ブロックは撤去。Vancouver Veto に統合済み)
```

設計の本質 (Vancouver indicator が dominant) は SPEC 初版から不変、配置位置のみ実装段階で修正。

### 4.3 設計判断の根拠

1. **データドリブン**: 4 markers × 2 corpus の hit rate 測定で M1 単独の優位性が証明済
2. **DRY 原則**: 機能重複する規則を撤去
3. **YAGNI**: 投機的な regression 保護より、実測に基づく規則簡素化を優先
4. **Day8 D8-2 の応用**: 重複コード/規則を bug 修正のついでに排除

### 4.4 関連する未変更箇所

以下は本 SPEC の scope 外 (touch しない):

- `_AUTHOR_ITEM_RE` (必須条件): MDPI 著者形式の検出は変えない
- `(a)`-`(c)` ブロック: 標準 MDPI 末尾 / DOI / ISBN 検出は変えない
- `(e)` 不完全 MDPI fallback: 維持 (改修後も M1 hit がなければ True を返す)
- `structure_one_mdpi()`: parser 本体は変えない

---

## 5. TDD test plan

### 5.1 test 配置

`tests/test_mdpi_parser.py` に append (既存 4 test に追加).

### 5.2 追加 test 一覧 (実装版 = 4 件、SPEC 初版 3 件 + 1)

実装段階で test 3 を TDD skill "One behavior" rule に従い **2 件に細分化**:

| # | test 名 | 性質 | 期待 |
|:---:|:---|:---|:---|
| 1 | `test_is_mdpi_style_returns_false_for_paren_year_vancouver` | RED → GREEN | Stage 2 raw_text **3 件** (Ref #1 Huizinga 2011 / Ref #2 Shah 2017 / Ref #11 Lindqvist 2007) → 全 False |
| 2 | `test_is_mdpi_style_still_returns_true_for_pure_mdpi` | regression 保護 | MDPI fixture 代表 ref **3 件** (#1 Bray 2022 / #51 Gustavsson-Lilius / #141 Peterson book) → 全 True 維持 |
| 3a | `test_is_mdpi_style_does_not_match_non_year_parens` | edge case | `(2nd ed.)` のような非年括弧は M1 regex に誤 match しない (4 桁年限定の証明) |
| 3b | `test_is_mdpi_style_paren_year_dominates_over_mdpi_signals` | M1 dominance | `(1995)` を含む MDPI 形式 text でも False を返す (Vancouver Veto = 最優先 early return の確認) |

### 5.3 RED 確認 (実測)

- test 1, 3b が現状 fail (`feature missing`、確認済): `(YYYY)` を検出していないため True を返す → False 期待で AssertionError
- test 2, 3a は現状 pass (regression 保護として既存 markers が機能しない領域)

### 5.4 GREEN 確認 (実測)

- mdpi_parser.py の `is_mdpi_style()` に Vancouver Veto を **著者チェック直後** に early-return で追加 (旧 (d) 位置からの順序修正、§4.1 の備考参照)
- test 1, 2, 3a, 3b 全 pass
- 既存 mdpi_parser test 4 件 pass (regression なし)
- **全体 66 passed (Day8 末 62 → +4) / 1 skipped** (SPEC 初版 65 → +1、test 細分化分)

### 5.5 統合検証

- `tests/test_integration_149refs.py` (149-ref MDPI fixture) が引き続き全 pass であることを確認
- これにより MDPI fast-path への影響なしが byte-identity レベルで保証される

---

## 6. Commit 計画

**1 commit に統合** (TDD 1 cycle、変更が原子的、分離する benefit なし):

```
fix(mdpi-parser): tighten Vancouver detection via (YYYY) marker

is_mdpi_style() の Vancouver 検出を強化:
- 旧 markers (Smith J, Lee K,/;Vol:Pages) を撤去
- 新 marker (YYYY) 括弧年に置換

実測 (Day7 §8.6 / Day9 brainstorm):
- MDPI fixture 149 件: 0 件影響 (regression なし)
- Vancouver 24 件: 24/24 捕捉 (旧 markers は 1/24 のみ)

TDD cycle:
- RED: 3 新 test 追加 (Vancouver→False 1 件、MDPI→True 維持 1 件、edge 1 件)
- GREEN: line 401-410 置換、全 65 test pass

Refs: docs/sessions/day9/SPEC_mdpi_fast_path_strict.md;
      Day7 §8.6 §9.2; Day8 D8-2 (重複 code smell の事前検出)
```

---

## 7. 想定外への対応

| 想定外 | 兆候 | 対処 |
|:---|:---|:---|
| RED test が想定外の理由で失敗 | typo、import error 等 | TDD skill 通り test を fix して再実行 |
| GREEN 後に MDPI regression | `tests/test_mdpi_parser.py` または `test_integration_149refs.py` で fail | line 401-410 の置換が誤っていないか確認、最悪 revert |
| edge case test が fail | MDPI fixture に偶然 `(YYYY)` パターンを含む ref がある | regex を `\s\((?:19|20)\d{2}\)` (前 space 必須) のように context 強化 |
| 全 65 test pass しない | Day8 末 62 から +3 で 65 期待、それ未満なら別問題 | 個別 test の出力を確認、対応 |

---

## 8. 検証 (実装後、本 SPEC scope 外)

実装 commit 後、以下は本 SPEC の対象外だが、Day9 続行 or Day10 で実施推奨:

- **Stage 2 retry** (env 経由) で fast-path 件数の変化観測
  - 旧: 24 件中 21 件 fast-path / 3 件 LLM
  - 新: 期待 0 件 fast-path / 24 件 LLM (M1 で全 24 件が False になるため)
  - LLM コスト試算 (約 $0.10-0.30、Anthropic Sonnet 4.6 想定)
- **解決率の変化**: 現状 14/24 から改善するか測定 (LLM の方が title/author 境界をうまく解析する想定)

---

## 9. 残存リスク

### 9.1 投機的なリスク

- **`(YYYY)` を含まない Vancouver 系 input**: 現状 0 件、将来出現する可能性あり
- **対処**: 本 SPEC scope 外、Day10+ の中期タスク (別ドメイン golden fixture 追加) で monitor

### 9.2 LLM 経路への routing 増加によるコスト

- 現状 MDPI fast-path 21/24 → 新方針 0/24 に減少 → LLM 経由 24/24 に
- 1 件あたり Anthropic Sonnet 4.6 で約 $0.005-0.010 (推定)
- 24 件で $0.12-0.24 程度
- **対処**: 本 SPEC scope 外、Day10+ で実測 + USAGE_QUICKSTART のコスト試算章を更新

---

## 10. 関連リソース

| リソース | 場所 | 役割 |
|:---|:---|:---|
| Day7 PHASE_0_VERIFICATION_REPORT | `docs/sessions/day7/PHASE_0_VERIFICATION_REPORT.md` | §8.6 で問題発見、§9.2 で Day8+ 中期タスクとして提示 |
| Day8 LESSONS_LEARNED | `docs/sessions/day8/DAY8_LESSONS_LEARNED.md` | §5 D8-2 (重複検出) を本 SPEC で応用 |
| 改修対象 | `mdpi_parser.py:372-412` (`is_mdpi_style()`) | line 401-410 のみ変更 |
| 既存 test | `tests/test_mdpi_parser.py` (4 件) | 本 SPEC で +3 追加して 7 件に |
| 統合 test | `tests/test_integration_149refs.py` (10 件) | 本 SPEC で touch しない、regression 保護として継続実行 |

---

## 11. 完了条件 (Day9 完了時点で達成)

本 SPEC は以下が成立した時点で「実装完了」とする:

- [x] mdpi_parser.py の `is_mdpi_style()` に Vancouver Veto を **著者チェック直後** に early-return で追加 (旧 (d) 位置からの順序修正)
- [x] tests/test_mdpi_parser.py に **4 新 test** 追加 (SPEC 初版 3 → +1、TDD One behavior rule 細分化)
- [x] `pytest tests/` が **66 passed, 1 skipped** を報告 (SPEC 初版 65 → +1)
- [x] commit が 1 つ作成 (`ab25630`)、commit message に本 SPEC への参照あり
- [x] git status が clean (untracked = .DS_Store のみ)
- [x] **(Day9 (Z) 実機検証)** Stage 2 OneDrive 24 件で MDPI fast-path 0 件、LLM path 24 件、解決率 14/24 → **22/24 (+33% pt 改善)**

(以下は元の完了条件、項目順保持のため残置)

- [ ] mdpi_parser.py:401-410 が "After" 版に置換済
- [ ] tests/test_mdpi_parser.py に 3 新 test 追加
- [ ] `pytest tests/` が **65 passed, 1 skipped** を報告
- [ ] commit が 1 つ作成され、commit message に本 SPEC への参照あり
- [ ] git status が clean (untracked = .DS_Store のみ)

---

**SPEC 作成日**: 2026/05/09
**作成者**: Claude Code (Sonnet 4.6)
**承認**: 片山英樹 (Hideki Katayama) — brainstorm 段階で大筋 approval、本 spec doc の review 後に最終承認予定
**次ステップ**: spec self-review → user reviews → writing-plans skill (規模次第で直接 TDD 実装も検討)
