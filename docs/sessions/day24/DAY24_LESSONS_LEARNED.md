# Day24 LESSONS LEARNED

**Day24 セッション (2026-05-24)**: Day23 skip-mark した 5 test file を新 mdpi_173refs fixture に re-point + 構造化 refactor + skip 解除 (52 passed / 50 skipped → 100 passed / 0 skipped)

---

## 1. セッション概要

### 1.1 背景

Day23 末状態: 52 passed / 50 skipped。Day23 Phase 1 (soft delete) の実行中に `tests/fixtures/mdpi_149refs` を hard-code 参照していた 5 test file が発覚し、これらに module-level `pytestmark = pytest.mark.skip(reason="awaiting Day23 Phase 5 new MDPI fixture")` を付与して Day23 作業を完遂した。50 skipped はすべてこの 5 file 由来であり、Day23 session 末のコメントに「Day24 Top priority」と明示して残置した。

Day23 Phase 5 で新 fixture `tests/fixtures/mdpi_173refs/` (PMC13164670, Nutrients, CC BY 4.0, 参照文献 173 件) が構築済であったため、Day24 の目標は以下の通り:

1. 5 test file を `mdpi_149refs` → `mdpi_173refs` に re-point
2. byte-level golden 依存を構造 invariant ベースに refactor
3. skip-mark を解除して全 50 skipped を解消
4. 100 passed / 0 skipped / 0 failed を達成

### 1.2 Day24 末状態

- 全 tests: **100 passed / 0 skipped / 0 failed**
- 改修 test file: 5 file (mdpi_parser / overrides_contract / journal_audit / pre_integration_baseline / split_references_doi_boundary)
- byte-level golden 依存: 4 test → **0** (全て構造 assertion に refactor)
- 新発見 bug: split_references() DOI-boundary miss (Day24 Task 1 recon で発見、tripwire test として encode)
- LLM cost: $0 (API 呼び出し不要の test refactor のみ)
- gitleaks: no leaks found (継続)
- commit chain: 5 件 (docs(spec) + docs(plan) + test(refactor) + style fixup + docs(sessions))

---

## 2. brainstorming 段階

### 2.1 設計方針確定 (Q1, Q2)

| # | 質問 | 選択肢と比較 | 確定 |
|:---:|:---|:---|:---|
| Q1 | refactor 強度: byte-level golden をどう扱うか？ | α 構造 invariant 全置換 / β Phase 1 のみ byte-match / γ test 削除 | **α** (構造 invariant 全置換) |
| Q2 | commit 戦略: 原子性 vs 段階性？ | α 1 atomic commit / β file ごと個別 commit | **α** (1 atomic commit) |

**Q1 判断根拠**: β (byte-match のみ) は新 corpus の baseline JSON が変更された時点で再び壊れる。γ (test 削除) は mdpi 固有の regression coverage が消える。α (構造 invariant) は corpus 置換への耐性が最高で、新 corpus 固有 assertion も保持できる。

**Q2 判断根拠**: file ごとの個別 commit は中間 broken 状態を git history に残す。1 atomic commit はテスト全通過 → commit → push の一貫性を保証する。

### 2.2 SPEC と PLAN

- SPEC (`docs/superpowers/specs/2026-05-24-day24-mdpi-test-restoration-design.md`, commit `8d7df22`): Q1 (α/β/γ) 比較評価表 + §3 per-file detail (各 file の改修戦略・削除予定 assertion・新規 assertion の設計)
- PLAN (`docs/superpowers/plans/2026-05-24-day24-mdpi-test-restoration.md`, commit `b7e5b58`): Task 0-3 の 4 task 構成 (spec doc + plan doc + 実装 + archive)

---

## 3. 実装段階の経緯 (Task 0-3 + fixup)

### 3.1 commit chain (5 件)

| # | SHA | type | 要旨 |
|:---:|:---|:---|:---|
| 1 | `8d7df22` | docs(spec) | Day24 MDPI test restoration spec (per-file refactor 戦略 §3) |
| 2 | `b7e5b58` | docs(plan) | Day24 implementation plan (Task 0-3、4 task 構成) |
| 3 | `357dfe9` | test(refactor) | 5 file 一括 re-point + structural refactor + skip 解除 (212+/281-) |
| 4 | `4e0eb36` | style(tests) | unused json imports cleanup (fixup: 4 file の `import json` 除去) |
| 5 | (this commit) | docs(sessions) | Day24 archive (README + LESSONS) |

### 3.2 Task 1: reconnaissance (/tmp に出力、commit なし)

5 test file の re-point に先立ち、新 corpus `mdpi_173refs` の Phase 1 出力 (`split_references()` の生の分割結果) を `/tmp/mdpi_173refs_phase1.txt` に dump して手動検証した。目的は以下:

1. 新 corpus の参照文献数・構造の把握 (boundary パターン確認)
2. byte-level golden の内容確認 (assertion 再設計の根拠取得)
3. edge case / boundary miss の検出

この reconnaissance で **split_references() DOI-boundary bug** を発見 (詳細は §4.3 参照)。

### 3.3 Task 2: 5 file 一括 refactor (commit `357dfe9`)

diff stats: **212 lines added / 281 lines deleted** (net -69 lines)。削除量が多いのは旧 corpus 固有の assertion を全面刷新したため。

各 file の作業概要:

| file | 改修種別 | 主な変更内容 |
|:---|:---|:---|
| `test_mdpi_parser.py` | 局所改修 | fixture path 変更 + count/sample-ref assertion を新 corpus 値に更新 |
| `test_overrides_contract.py` | 最小改修 (1 test 削除) | byte-level golden に強依存する 1 test を削除、残 tests は path 変更のみ |
| `test_journal_audit.py` | 局所改修 | fixture path 変更 + journal 名 assertion を新 corpus サンプルに更新 |
| `test_pre_integration_baseline.py` | 全面 rewrite | 旧 corpus 固有 assertion を全削除 → 構造 invariant (count/gap/named-ref) ベースに全面書き直し |
| `test_split_references_doi_boundary.py` | 全面 rewrite | 旧 line-range assertion を全削除 → DOI-boundary tripwire + 構造 invariant ベースに全面書き直し |

### 3.4 Task 2 fixup: unused imports cleanup (commit `4e0eb36`)

refactor 後に `import json` が 4 file で不要になっていたため、style fixup commit として個別に除去。main refactor commit とは意図的に分離 (機能変更 vs スタイル修正の分離原則)。

---

## 4. 設計判断と検証

### 4.1 byte-level golden を構造 invariant に置換した方針

**問題**: 旧 corpus (`mdpi_149refs`, 149 ref) の byte-level golden は新 corpus (`mdpi_173refs`, 173 ref) に対して完全に無効。具体的には:
- 参照文献数の変化 (149 → 173 件、parsed count も変化)
- 先頭 ref (旧: Bray 2018 globocan → 新: 別論文) の変化
- 末尾 ref (旧: #149 De Boeck → 新: #173 de Menezes) の変化
- 中間 ref (#40 van der Biessen, #140 van Zyl 等) の変化
- line numbers (旧: 567-910 等) の変化

**解決**: regression coverage を維持しながら corpus 非依存な assertion を設計:

1. **ref count exact match**: `len(refs) == 171` (現在の parse 結果を tripwire として固定)
2. **gap list**: `sorted(missing_indices) == [55, 79]` (DOI-boundary bug を tripwire として encode)
3. **lowercase-prefix specific tests**: `refs[69-1].author.lower().startswith("van vliet")` 等 (corpus 固有だが意味のある assertion)
4. **structural invariant**: `all(isinstance(r, Reference) for r in refs)` 等

この設計により、Day25+ で parser fix を入れた際に `assert len(refs) == 171` および `assert sorted(missing_indices) == [55, 79]` が自動的に失敗し、update を促す仕組みになる。

### 4.2 per-file refactor 強度の差異

同じ「構造 invariant への移行」でも、file によって改修強度を変えた。判断基準は **旧 corpus-specific assertion の比率**:

| file | 旧 corpus 依存度 | 採用戦略 | 理由 |
|:---|:---:|:---|:---|
| `test_mdpi_parser.py` | 低 (path + 数値のみ) | 局所改修 | assertion の論理構造は corpus 非依存のため path と数値の差し替えのみで対応可能 |
| `test_overrides_contract.py` | 中 (byte golden 1 test) | 最小改修 + 1 test 削除 | byte golden 依存の 1 test のみ削除。残は path 変更のみ |
| `test_journal_audit.py` | 低 (journal 名 sample) | 局所改修 | journal 名の論理 (有効な journal 名を持つ) は corpus 非依存。サンプル名のみ更新 |
| `test_pre_integration_baseline.py` | 高 (Bray/De Boeck/van der Biessen/van Zyl 等の固有 ref) | 全面 rewrite | 旧 corpus 固有 assertion が全体の 80%+。保守コストに見合う assertion が残らないため全面刷新 |
| `test_split_references_doi_boundary.py` | 高 (line 567-910 等の旧 corpus line range) | 全面 rewrite | line number assertion はすべて旧 corpus 固有。tripwire + 構造 invariant 中心に設計を刷新 |

### 4.3 Day24 Task 1 reconnaissance による parser bug 発見 (tripwire pattern 適用)

**発見プロセス**: `/tmp` に Phase 1 出力を dump して `split_references()` の分割結果を目視検証したところ、#54 および #78 のコンテンツが 569 characters と異常に長く、#55 と #79 のコンテンツが含まれていることが判明。

**バグの性質**: `split_references()` は `\n<digit(s)>.` パターンで boundary を検出するが、DOI URL (`https://doi.org/10.xxxxx`) の直後に `<N>.` 形式の boundary が連続する場合、DOI の `.` を boundary の `.` と区別できず、次の boundary 検出が skip される。

**具体例**:
```
...doi.org/10.3390/nu12030xxx
55. NextAuthor et al. ...
```

`split_references()` が `\n55.` を boundary として認識できず、ref #55 が #54 の末尾に append される。同様のパターンが #78/#79 でも発生。

**tripwire pattern の適用**: Day24 では parser fix を行わず、test 側で current broken state を assert する:
```python
# tripwire: current parse 結果 (171件、#55/#79 が欠落) を assert
# Day25+ で parser fix → この assert が失敗したら test を 173 に更新する
assert len(refs) == 171  # DOI-boundary bug により 173 → 171
assert sorted(missing_indices) == [55, 79]  # merge された ref の欠落を記録
```

Day20 セッションで確立した「inline-fix を即座に入れる vs tripwire を置いて将来に委ねる」の判断基準 (D20-3 パターン) を適用。今回は parser 修正が Day24 scope を超えるため tripwire 選択。

### 4.4 integration/src/manual_overrides.yaml の 4 entry 残置判断

Day23 Phase 5 で新 fixture 構築時に作成した `integration/src/manual_overrides.yaml` に旧 corpus 由来の 4 entry (ref #66, #137, #141, #148) が含まれていた。これらは新 corpus `mdpi_173refs` には対応していない。

**残置の判断理由**:
1. これらの entry は新 corpus の参照文献番号と必ずしも一致しない → 現時点での override として機能しないが、誤動作もしない (無効な override は無視される仕様)
2. 正しい新 corpus 用 override を構築するには、parser fix (Day25+ top priority) が先に必要
3. Day24 scope は「50 skipped を解消すること」であり、override の正確性は Day25+ scope

**Day25+ での扱い**: split_references() DOI-boundary fix 後に #54/#55/#78/#79 が正しく split されたことを確認してから、`mdpi_173refs` 固有の manual_overrides.yaml を再構築する。

---

## 5. 実機検証結果

### 5.1 test count 推移

| 時点 | passed | skipped | failed |
|:---|:---:|:---:|:---:|
| Day23 末 (task 2 前) | 52 | 50 | 0 |
| task 2 commit 後 (357dfe9) | 100 | 0 | 0 |
| style fixup 後 (4e0eb36) | 100 | 0 | 0 |
| Day24 末 (本 commit 前) | **100** | **0** | **0** |

### 5.2 smoke check 結果

| 検証項目 | 結果 |
|:---|:---|
| `python3 -m pytest tests/ -q` | 100 passed in 0.36s ✅ |
| `gitleaks detect --no-banner --redact` | no leaks found ✅ |
| repo visibility | PUBLIC ✅ |
| local/remote SHA | MATCH ✅ |
| `gh release view v0.1.0` | `{"isDraft":false,"tagName":"v0.1.0"}` ✅ |

### 5.3 Day24 commit chain (5 件)

| # | SHA | type | stats |
|:---:|:---|:---|:---|
| 1 | `8d7df22` | docs(spec) | Day24 spec 新規 |
| 2 | `b7e5b58` | docs(plan) | Day24 plan 新規 |
| 3 | `357dfe9` | test(refactor) | 212+/281- |
| 4 | `4e0eb36` | style(tests) | 4 file, import json 除去 |
| 5 | (this commit) | docs(sessions) | Day24 archive |

---

## 6. 教訓 (D24-1, D24-2, D24-3)

### 6.1 D24-1: 意図的 skip-mark に「次セッション Top priority」を明示すると technical debt が忘れられない

**事象**: Day23 Phase 1 で 5 test file に skip-mark を付与した際、commit message および `pytestmark` の `reason` パラメータに `"awaiting Day23 Phase 5 new MDPI fixture"` と記述し、Day23 archive の §7.1 に「D23-X (Top priority): skip-mark した 5 test file を新 `mdpi_173refs` fixture に re-point + skip 解除」と明示した。Day24 セッション開始時にこの記録を確認し、即座に作業に着手できた。50 skipped という定量指標も「未解消の負債」として視覚的に警告を発し続けた。

**学び**: 意図的に技術的負債を残す場合は、以下を必ず記録する:
1. **なぜ今ではなく後で解消するのか** (reason: corpus 入替待ち、parser fix 待ち等)
2. **次セッション優先度** (Top priority / Day N+1 で対応 等)
3. **定量的な残存指標** (X skipped, Y TODO 等)

この習慣により、負債が「次セッションで自動的に発見される」仕組みができる。特に `pytest --tb=no -q` の最終行に `X skipped` が表示されることで、CI / 次のセッション開始時に常に目に入る。

**適用範囲**: 意図的な一時的破壊 (skip-mark, TODO コメント, FIXME, stub) を残す場面全般。「後で直す」の約束は定量指標と次セッション記録に変換して初めて管理可能になる。

### 6.2 D24-2: byte-level golden は corpus 置換に対して脆弱、構造 invariant 設計が高保守性を実現

**事象**: Day23 の corpus 入替 (mdpi_149refs → mdpi_173refs) により、4 test の byte-level golden (baseline JSON の特定フィールドの exact match) が完全に無効化された。具体的には `test_pre_integration_baseline.py` が Bray globocan #1 / De Boeck #149 / van der Biessen #40 / van Zyl #140 という旧 corpus 固有の著者名・論文タイトルを hard-code しており、新 corpus への移植は「全面書き直し」以外に選択肢がなかった。

**学び**: テストの設計を以下の 2 層に分離する:

| 層 | 説明 | corpus 耐性 | 例 |
|:---|:---|:---:|:---|
| corpus-agnostic invariant | 型・構造・論理的制約 (「N 件以上」「著者名が文字列」等) | 高 | `isinstance(r.author, str)`, `len(refs) > 50` |
| corpus-specific snapshot | 特定 ref の exact content (著者名・タイトル等) | 低 | `refs[0].author == "Bray"`, `refs[-1].title == "De Boeck"` |

corpus-specific snapshot は「現在の実装の出力をそのまま固定する」用途 (regression sentinel) として有効だが、**corpus 入替の際は全削除になることを設計時から理解する**。両層を意図的に分離してファイル・クラス・コメントで区別することで、corpus 入替時のコストを最小化できる。

**適用範囲**: test fixture を参照するすべての integration test、end-to-end test。特に外部データ (PMC, API 等) を原料とするテストは corpus 耐性を意識して設計する。

### 6.3 D24-3: corpus 偵察で発見した parser bug を tripwire pattern で encode すると、将来 fix が「自動的に知らせる」仕組みになる

**事象**: Day24 Task 1 の reconnaissance (新 corpus Phase 1 出力の /tmp dump + 手動検証) で `split_references()` の DOI-boundary miss bug を発見した。Day24 scope では parser fix は対象外であったが、発見した bug を「なかったこと」にせず、test に tripwire として encode した:

```python
# tripwire: DOI-boundary bug により #55 と #79 が欠落 (173 → 171 件)
# Day25+ で parser fix が入った時点でこの assert が失敗する
assert len(parsed) == 171
assert sorted(missing_indices) == [55, 79]
```

この tripwire により、Day25+ で `split_references()` の DOI-boundary 処理を修正した際に:
1. `len(parsed) == 171` が失敗 → 「parser fix が boundary miss を直した」ことを自動検出
2. test の assert を `== 173` に更新し、gap list を `[]` に更新する

**学び**: 「今は直せないが既知の問題」を発見した場合の三択:

| 選択肢 | 使いどころ |
|:---|:---|
| 即時 fix (D20-3 inline-fix) | 修正コストが小さく、今セッション scope 内 |
| tripwire test | 修正コストが大きい / 別の fix が先に必要 / scope 外だが発見した |
| TODO コメントのみ | 問題の所在は明確だが test 化が困難な場合 |

tripwire は「現在の broken state を assert」することで、将来の fix が意図通りに動いたかを自動検証する。単なる TODO コメントより強力であり、fix 後の verification コストを削減する。corpus-specific test (Bray globocan, van der Biessen 等) が corpus 入替で全削除になる問題も、corpus-agnostic invariant + tripwire の組み合わせで代替できる場合がある。

**適用範囲**: reconnaissance 中に発見した known-broken behavior、scope 外の bug、将来の refactor で挙動が変わることが予期される assertion 全般。

---

## 7. 残存タスク (Day25+ 候補)

### 7.1 Day24 で新規追加された課題 (最優先)

- **D24-Top (Top priority)**: split_references() DOI-boundary parser fix
  - 現象: DOI URL 直後の `\n<N>.` boundary が検出されず、#55 と #79 が #54 と #78 に merge
  - 影響: parsed count 173 → 171 (2 件欠落)
  - tripwire test: `test_split_references_doi_boundary.py` に `assert len(refs) == 171` 等
  - 想定作業: `split_references()` の boundary 正規表現改修 + tripwire assertion 更新

- **D24-Sub**: mdpi_173refs 固有の manual_overrides.yaml 構築
  - 前提: DOI-boundary fix 後に #54/#55/#78/#79 が正しく split されることを確認
  - 旧 4 entry (66/137/141/148) は新 corpus 用に刷新または削除

### 7.2 Day22/23 からの継続課題

- **apa_45refs Crossref graceful failure (16 件)** の対応
- **NLM fuzzy-match precision 改善** (Processes journal 誤検出)
- **tools/build_*_fixture.py の共通 utility への refactor** (Day23 code review 指摘)

### 7.3 Day21 §6.1 からの継続課題

- [ ] **pre-commit hook gitleaks 自動実行** (Day22 handoff パターン 3)
- [ ] **CONTRIBUTING.md / Issue PR template** (Day22 handoff パターン 2)
- [ ] **PyPI 公開** (v0.2.0 候補)
- [ ] **pyproject.toml + uv.lock 移行** (CLAUDE.md §8 整合)
- [ ] **predatory journal データベース連携** (Beall's list)
- [ ] **MCP server による batch processing** (Stage 3 拡張)
- [ ] **deterministic byte-level golden の再構築** (LLM stub 経由、Day26+ 大改修)

---

## 8. 次セッション再開時のプロンプトテンプレート

### パターン 1: split_references DOI-boundary parser fix (最優先・推奨)

```
Day25 として、split_references() の DOI-boundary parser bug を修正します。
Day24 Task 1 reconnaissance で発見: DOI URL 直後の \n<N>. boundary が
検出されず、#55 と #79 が #54 と #78 に merge される問題 (parsed count
173 → 171)。tripwire test が test_split_references_doi_boundary.py にあり、
fix 後は assert len(refs) == 171 → 173 に更新予定。TDD で進めてください。
```

### パターン 2: mdpi_173refs 用 manual_overrides.yaml 構築

```
Day25 として、mdpi_173refs corpus に対応した manual_overrides.yaml を
構築します。現状の integration/src/manual_overrides.yaml は旧 corpus
(mdpi_149refs) 由来の 4 entry (66/137/141/148) が残置されており新 corpus
には対応していません。parser 出力 (171 件) を精査して適切な override を
設計してください。注意: DOI-boundary fix が先の場合はその後に実施推奨。
```

### パターン 3: pre-commit hook gitleaks + CONTRIBUTING.md

```
Day25 として、以下の 2 点を追加します:
1. pre-commit hook で gitleaks scan を自動実行 (.pre-commit-config.yaml + 既存
   .gitleaksignore の継承)
2. CONTRIBUTING.md + GitHub Issue/PR template (.github/) 追加 (Public 復帰後の
   外部 collaboration 受入準備)
各 ~1h。まず gitleaks hook → CONTRIBUTING.md の順で進めてください。
```

### パターン 4: Crossref graceful failure 対応

```
Day25 として、apa_45refs の Crossref graceful failure 16 件の根本原因を
調査・解消します。Crossref SSL/timeout の確認または NLM 直接検索パスへの
fallback を検討。TDD で進めてください。~3h。
```

---

**記録完了日**: 2026-05-24 (Day24)
**記録者**: Claude Code (Sonnet 4.6)
**ステータス**: Day24 archive 完成、100 passed / 0 skipped / 0 failed、Day25 着手準備完了 (4 パターンプロンプトあり)
