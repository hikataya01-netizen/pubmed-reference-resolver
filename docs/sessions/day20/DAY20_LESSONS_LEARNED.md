# Day20 LESSONS LEARNED

**Day20 セッション (2026-05-22)**: 三分類 audit の book/proceedings/DOI 欠落 case 改修 (Day17 D17 解消) + Day7 §9.3 残最後 1 件 (Stage 3) 達成認証 cleanup

---

## 1. セッション概要

### 1.1 背景

Day19 末で Day7 §9.3 long-term task 残 1 件 (Stage 3 配線) + 副次タスク残数件. Day20 brainstorming Q0 で Stage 3 が既に SKILL.md 経由で達成済であることをユーザーが確認、Q1 で Day20 メインタスクを **(B1) AI 工学 book/web refs 三分類改修** (Day17 D17 起源) に決定. Stage 3 認証は同梱.

### 1.2 brainstorming 段階 (Q0-Q3)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q0 | Stage 3 の現状達成度 | (A) SKILL.md 経由で起動済 → 認証 cleanup |
| Q1 | Day20 メインタスク | (B1) AI 工学 book/web refs 三分類改修 |
| Q2 | 改修 scope | 全 7-13 件 cover (book + proceedings + DOI 無 journal) |
| Q3 | Test 戦略 | (完全) cell + apa baseline 再生成 + integration test 拡張 |

### 1.3 SPEC (commit `0b20e89`)

`docs/sessions/day20/SPEC_three_class_book_web_refinement.md` を archive (490 行、11 章).

### 1.4 PLAN (commit `a5f75ea`)

`docs/sessions/day20/PLAN_three_class_book_web_refinement.md` を archive (1304 行). Task 1-7 + Verification で構成. TDD 厳格 (Phase 2 test 先 RED → Phase 1 production GREEN).

---

## 2. 実装段階の経緯 (8 commits)

### Phase 0: STAGE3_COMPLETION_NOTE 作成 (commit `f3708da`)

- Task 1: Day7 §9.3 残最後 1 件 (Stage 3) を SKILL.md 経由達成として認証. 過去 LESSONS は履歴尊重で改修なし.

### Phase 1+2: three_class_classifier 改修 + unit test (commit `0351d35`)

- Task 2 (TDD RED): test_three_class_classifier.py に 3 新 unit test + 1 既存修正. 3 新 test が確かに FAIL することを確認.
- Task 3 (TDD GREEN): three_class_classifier.py に 3 helper (_detect_book / _detect_conference / _classify_via_nlm_only) + 4 rule 順次評価. 8/8 unit tests pass.

### Phase 3: main.py 微改修 + PLAN gap fix (commit `6a7c837`)

- Task 4: line 1788-1792 で unresolved_refs に is_book/raw_text/publisher 3 fields 追加.
- **PLAN gap fix**: 全 tests 実行で `test_synthesize_outputs_report_matches_expected` (mdpi_149refs integration) が FAIL を検出. Day20 改修により stub 環境での report.md 出力が変わったため (#4 A→unknown, #9/#19 A→B). mdpi_149refs/expected_report.md も再生成して同 commit に含めた.

### Phase 4a: cell_45refs baseline 再生成 (commit `faa920d`)

- Task 5: Phase 4 再実行 (LLM cost ~$1)、baseline 2 ファイル再生成、README + test 8 期待値更新.
- 三分類: A=14 → A=1 (#17 のみ、93% 減). B=6 (book 3 + conference 3).

### Phase 4b: apa_45refs baseline 再生成 (commit `1df22ac`)

- Task 6: 同型処理を apa_45refs に適用. LLM cost ~$1.
- 三分類: A=4 → A=0 (完全消失). B=3 (book chapter).

### Phase 5: Day20 archive (本 commit)

- Task 7: README + LESSONS archive.

---

## 3. 設計判断と検証

### 3.1 Stage 3 認証 cleanup の根拠

Day7 PHASE_0_VERIFICATION_REPORT §1.1 当時は Claude Code skill 機能が未成熟で MCP/hook 配線想定. 11 セッション (Day8-19) を経た現状では SKILL.md symlink で起動可能. **「未着手」のまま残置するのは現状と乖離**.

### 3.2 4 rule 順次評価の順序根拠

- Rule 1 (is_book) を最優先: book は MEDLINE 対象外という構造的判定で最も確実
- Rule 2 (conference): regex 1 つで簡潔、API call 不要
- Rule 3 (journal あり → NLM): API call 発生のため後位、SSL 問題に強い fail-soft
- Rule 4 (全 fail → A): 「真の判定不可」として A 残留

### 3.3 TDD 厳格 (Phase 2 → Phase 1) の根拠

3 helper 新規追加 + 既存 logic 変更が混在するため、TDD で「期待される振る舞い」を test で先に固定. これにより:
- helper の interface (引数・戻り値) が test で明示される
- 既存 5 tests のうち 1 件 (test_classify_returns_A_when_doi_missing) の input 調整漏れを test failure で検出可能
- 実装段階での scope creep 防止

実機検証: 3 新 test を実装前に書いた直後 → 3 FAIL (production code 未改修) → production 実装後 → 8 PASS. TDD cycle が完全に機能.

### 3.4 PLAN gap への対応 (mdpi_149refs golden 再生成)

PLAN では cell + apa の baseline 再生成のみ想定していたが、Phase 3 で全 tests 実行時に mdpi_149refs の `test_synthesize_outputs_report_matches_expected` も影響を受けることを発見. 同 test の stub crossref/nlm 環境では、Day20 改修により:
- #4 (DOI 欠落 + journal あり): A → unknown (Rule 3 で NLM stub が graceful unknown)
- #9, #19 (is_book=True): A → B (Rule 1 で book 判定)

mdpi_149refs/expected_report.md を再生成して Phase 3 commit に同梱. **PLAN gap を執行段階で発見・解消** (executing-plans skill「Don't force through blockers」を遵守し inline fix).

---

## 4. 実機検証結果

### 4.1 三分類 audit の品質改善

| Fixture | Day19 baseline | Day20 改修後 | A 削減率 |
|:---|:---|:---|:---:|
| cell_45refs | A=14, B=0, C=0, unknown=1 | A=1, B=6, C=0, unknown=8 | **-93%** |
| apa_45refs | A=4, B=0, C=0, unknown=16 | A=0, B=3, C=0, unknown=17 | **-100%** (完全消失) |

### 4.2 cell_45refs の Rule 別分類詳細

| Rule | refs | 件数 |
|:---:|:---|:---:|
| Rule 1 (is_book → B) | #31, #32, #37 | 3 |
| Rule 2 (conference → B) | #34, #42, #43 | 3 |
| Rule 3 (NLM 検索 → unknown) | #16, #33, #36, #38, #40, #41, #44, #45 | 8 |
| Rule 4 (真の A) | #17 (title truncated, journal 空) | 1 |
| **合計** | | **15** |

### 4.3 apa_45refs の Rule 別分類詳細

| Rule | refs | 件数 |
|:---:|:---|:---:|
| Rule 1 (is_book → B) | #28 (UK DHSC), #30 (Glenn book), #40 (Allport) | 3 |
| Rule 3 (NLM 検索 → unknown) | 17 件 (元 A=4 + unknown=13 が再分類) | 17 |
| **合計** | | **20** |

### 4.4 test 健全性

| 段階 | passed | 説明 |
|:---:|---:|:---|
| Day19 末 | 97 | (baseline) |
| Day20 Phase 1+2 後 | 100 | +3 新 unit test |
| Day20 Phase 3 後 | 100 | mdpi_149refs golden 再生成で復旧 |
| Day20 Phase 4a+4b 後 | **100** ✅ | cell/apa test 8 期待値更新で全 pass 維持 |

---

## 5. 教訓 (D20-1, D20-2, D20-3)

### 5.1 D20-1: long-term task の達成判定基準を時代変化に合わせる

**事象**: Day7 PHASE_0_VERIFICATION_REPORT で「Stage 3 = MCP/hook 配線」と定義された task が、Claude Code skill 機能の成熟により実質達成済だったが、Day8-19 で 11 セッション「未着手」として繰越し.

**学び**: 長期 task の達成判定基準は **当時の前提** に固定されがちだが、ツール・環境が成熟すると **別経路で達成済**になる可能性. 定期的に「当時の課題が現代の方法で解決済か?」を再評価することで dead task を整理.

**適用範囲**: 将来 long-term task table を維持する場合、半期 or 主要マイルストーン毎に「達成判定基準の妥当性」を再評価する慣行を導入.

### 5.2 D20-2: 品質改善は実 fixture からの逆算で進める

**事象**: Day17 D17 で「A 多発 (14/15)」と問題提起されたが、Day17 当時は具体的に「何が誤分類されているか」が不明. Day20 で実 cell_45refs baseline を分析し、14 件全てが DOI 欠落 case (Crossref 404 ではなく) と判明.

**学び**: 品質改善 task では **実 fixture / 実 baseline から逆算**して原因を特定することが、抽象的議論より圧倒的に効率的. Day20 では 30 分の baseline 分析で **3 つの明確な改修方針** (book / conference / DOI 無 journal) を導出、それぞれが Rule 1/2/3 に対応する綺麗な設計に直結.

**適用範囲**: 将来 false positive / false negative の品質問題を扱う際は、まず実データから逆算する pattern を default に.

### 5.3 D20-3: PLAN gap は executing 段階での inline fix で対処

**事象**: Day20 PLAN は cell + apa fixture の baseline 再生成のみ想定. 執行 Phase 3 で `test_synthesize_outputs_report_matches_expected` (mdpi_149refs deterministic golden) も影響を受けることを発見. PLAN にない作業だったが inline fix で mdpi_149refs/expected_report.md も再生成、Phase 3 commit に同梱.

**学び**: 設計段階で全 baseline の影響を予測するのは現実的でない. 執行段階で test failure として発見された PLAN gap は、**stop して clarification を求めるか fix を当てるか** の判断が必要. 本件は:
- gap 内容が明確 (mdpi_149refs の expected_report.md regeneration)
- 修正手順も明確 (stub fixture で再生成)
- スコープ拡大ではなく PLAN の補完
だったため inline fix が適切. もし gap 内容が不明確なら stop して人間判断を仰ぐべき.

**適用範囲**: 将来の plan execution で test failure を発見した場合、まず「PLAN の意図と整合する補完か否か」を判断. 整合するなら inline fix、整合しないなら stop.

---

## 6. 残存タスク (Day21 以降)

### 6.1 Day7 §9.3 long-term task: ✅ 完全クローズ (7/7)

Day20 で最後の 1 件 (Stage 3) を認証 cleanup. Day7 §9.3 で定義された long-term task は全て完了.

### 6.2 Day19+ で生成された Day21+ 候補

- [ ] **v0.1.0 tag 付与** + GitHub Release 作成 (公開化記念、CHANGELOG `[Unreleased] - 2026-05-18` → `[0.1.0]`、~1h)
- [ ] **CONTRIBUTING.md / CODE_OF_CONDUCT.md / Issue PR template** (collaboration 受入準備、~2h)
- [ ] **Branch protection rule** 設定 (main 直接 push 禁止)
- [ ] **SSH 認証 cleanup** (Day18 D18 起源、SSH passphrase 設定見直し)
- [ ] **pre-commit hook gitleaks 自動実行** (Day19 起源、ops 強化)
- [ ] **predatory journal データベース連携** (Beall's list 等、B 細分化)
- [ ] **MCP server による batch processing** (将来高度な体験、Stage 3 を超えた拡張)
- [ ] **Rule 3 NLM 検索の SSL 問題解消** (現状大半 unknown に倒れる、SSL chain 修復で B/C 判定率向上)

### 6.3 Day21+ 推奨着手順

1. **v0.1.0 tag + GitHub Release** (Day7 §9.3 完全クローズの公式 milestone、~1h、最高優先度)
2. **Rule 3 NLM 検索の SSL 問題解消** (Day20 改修の真価発揮、~2h)
3. **CONTRIBUTING.md / Issue PR template** (公開後の collaboration 受入準備、~2h)

---

## 7. 次セッション再開時のプロンプトテンプレート

### パターン 1: Day21 として v0.1.0 tag + GitHub Release (推奨)

```
Day21 として、Day19 で Public 切替済 + Day20 で long-term task 完全
クローズした pubmed-reference-resolver に v0.1.0 tag を付与し、GitHub
Release を作成します. CHANGELOG.md の [Unreleased] - 2026-05-18 section
を [0.1.0] に移行、git tag v0.1.0 + push、gh release create で Release
notes を生成. Day7 §9.3 long-term task 完全クローズの公式 milestone. ~1h.
```

### パターン 2: Day21 として Rule 3 NLM 検索の SSL 問題解消

```
Day21 として、Day20 で導入した Rule 3 (NLM 直接検索) の SSL 問題を
解消します. 現状 cell_45refs では 8/15、apa_45refs では 17/20 が
unknown に倒れている. nlm_catalog_check.py の HTTP 実装を certifi
ベースに変更、もしくは requests/httpx 移行で SSL chain 修復. baseline
再生成で B/C 判定が実際に出るよう確認.
```

### パターン 3: Day21 として CONTRIBUTING.md / Issue PR template

```
Day21 として、Public 公開済の pubmed-reference-resolver に collaboration
受入準備として CONTRIBUTING.md と Issue/PR template (.github/) を追加
します. brainstorming → SPEC → 実装で進めてください. ~2h.
```

---

**記録完了日**: 2026-05-22 (Day20)
**記録者**: Claude Code (Sonnet 4.6)
**ステータス**: Day20 archive 完成、**Day7 §9.3 long-term task 完全クローズ**、Day21 着手準備完了 (3 パターンプロンプトあり)
