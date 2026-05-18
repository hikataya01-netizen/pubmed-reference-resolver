# Day17 LESSONS LEARNED

**Day17 セッション (2026-05-18)**: Cell 系 45-ref golden fixture 追加 (Day7 §9.3 long-term task 残 5 件目を完了) + 副次成果として **production code 改修ゼロでの fixture 追加** を実証 (Day16 D16-1 教訓の波及効果)

---

## 1. セッション概要

### 1.1 背景

Day16 末時点で Day7 §9.3 long-term task の残 3 件 (Cell fixture、MCP/hook 配線、GitHub push) のうち、ユーザーは Day17 task として **Cell 系 golden fixture** を選択. Day16 LESSONS §7 パターン 1 のテンプレート (Day17 として Cell 系 fixture) を起点として、brainstorming → SPEC → writing-plans → TDD (subagent-driven-development) の 4 段階フローを適用.

### 1.2 brainstorming 段階 (Day16 圧縮版)

Day16 で Q1-Q5 + Approach の 6 質問を経て確立されたパターンを継承するため、Day17 では 2 質問のみに圧縮:

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | Day16 と同じ枠組みで進めるか | (同型) PMC OA + 45 件 + 3 領域 + 8 tests |
| Q2 | PMC OA 論文選定 (Cell-style 採用 + CC BY) | 3 iScience CC BY 4.0 papers (Molecular Biology / Biomedical / AI Engineering) |

### 1.3 SPEC (commit `c4ac9c8`)

427 行の SPEC を `docs/sessions/day17/SPEC_cell_45refs_fixture.md` に archive. Day16 SPEC を template に Cell 差分を反映した 12 章構成.

### 1.4 PLAN (commit `4fcb1a6`)

1549 行の implementation plan を `docs/sessions/day17/PLAN_cell_45refs_fixture.md` に archive. Task 0-8 + Verification で構成. Day16 PLAN を template に同型 task は集約 (Day16 では Task 4-11 で 8 tests を 8 task に分割していたが、Day17 では Task 4-6 で 8 tests を 3 task に統合).

---

## 2. 実装段階の経緯 (7 commits)

### Phase 0a: docx 組成 + Phase 1 expected (commit `94478fe`)

- Task 0 (PMC XML cache 確認): 既に Day17 brainstorming で `/tmp/iscience_check_*.xml` 経由で取得済の 3 PMC 論文を `.cache/pmc_xml/PMC*.xml` にコピー (Day16 と同じ SSL workaround).
- Task 1 (subagent dispatch): `tools/build_apa_fixture.py` を `tools/build_cell_fixture.py` (439 行) に複写、`_normalize_initials(cell_mode)` / `_format_authors(cell_mode)` 拡張、`format_as_cell()` 新規追加. 10/10 unit test (APA 5 + Cell 5) + smoke test 全 PASS. 二段レビュー (spec compliance + code quality) いずれも合格. Code quality reviewer 指摘の 1 件 (misleading journal block comment) を inline で修正.
- Task 2 (controller 直接実行): 45/45 件抽出成功 (Day16 で発生した `<collab>` 欠落事象は Day16 で既に build script 修正済のため再発しない、template 複写で自動継承).

### Phase 0b: full pipeline + 3 baselines (commit `9527fc0`)

- Task 3 (controller 直接実行): `main.py --phase 4` で full pipeline 実行 (LLM cost ~$0.5).
- 実測値:
  - Phase 3 解決 30/45 = 66.7% (Vancouver 91.7% > Cell 66.7% > APA 55.6%)
  - 重大 0 件
  - 三分類分布: A=14, B=0, C=0, unknown=1 (Day16 と対照的!)
- README.md に Vancouver / APA / Cell の 3 fixture 解決率対比表を含む包括的メタ情報を記載.

### Phase 1+2: 8 tests (commit `c9712d9`)

- Task 4-6 (subagent dispatch): `tests/test_integration_apa_45refs.py` を template に複写、9 modifications (fixture paths / 関数名 / docstring / 期待値 / 三分類分布 / test 7 を `, & ` → `, and ` 等) 適用.
- Pre-flight 確認: `, and ` 含む refs = 44/45 (Cell style の高い著者数で予想以上に高い).
- 全 8 tests PASS、89 → 97 passed (regression なし).

### Phase 3: USAGE_QUICKSTART 1.5 bump (commit `b634edc`)

- §X 変更履歴に「1.5 (Day17 更新)」 entry 追加. 履歴メタ情報 (作成日 + 作成者) も更新.

### Phase 4: Day17 archive (本 commit)

- README.md / DAY17_LESSONS_LEARNED.md を archive.

---

## 3. 設計判断と検証

### 3.1 brainstorming 圧縮の根拠

Day16 で 6 質問 (Q1-Q5 + Approach) を経て決定した枠組み (PMC OA + 45 件 + 3 領域 + 8 tests + Day11 ハイブリッド規約) が Day17 でもそのまま適用可能だったため、Q1 で「Day16 同型」確認のみで進行. Q2 で 3 PMC ID 選定のみ. **brainstorming 効率化**は Day9-15-16 で確立したフローの成熟効果.

| 項目 | Day16 | Day17 |
|:---|---:|---:|
| brainstorming 質問数 | 6 | 2 |
| brainstorming 時間 | ~30 min | ~10 min |
| Multi-choice 数 | 6 | 2 |

### 3.2 PMC OA 選定: iScience 一本化の根拠

Day16 では Routledge + T&F + Frontiers の 3 publisher にまたがり license 統一に苦労した. Day17 では iScience 内で 3 領域 (Molecular Biology + Biomedical + AI Engineering) を確保でき、全 CC BY 4.0. publisher 内多様性 vs publisher 多様性のトレードオフがある中、license 一貫性を優先.

### 3.3 build script の cell_mode flag 設計

`format_as_apa7` を完全コピーして `format_as_cell` に変換するのではなく、`_normalize_initials` / `_format_authors` に `cell_mode` flag を追加する設計を採用. 利点:
- ロジック重複を最小化 (initials 抽出 / collab 処理 / 空白対応の 90% は共通)
- 将来 Chicago / Nature style 追加時に flag 拡張 (`style="apa7"|"cell"|"chicago"`) で対応可能
- APA 7 backward 互換性を完全保持 (cell_mode=False default)

### 3.4 build script の独立保持 (依存なし) 設計

`tools/build_apa_fixture.py` と `tools/build_cell_fixture.py` は **完全独立** (import 関係なし). 将来 build_apa_fixture.py が改修されても build_cell_fixture.py には影響しない. DRY 原則よりも fixture 安定性を優先.

---

## 4. 実機検証結果

### 4.1 PMC OA 3 論文 (確定値)

| 領域 | PMC ID | DOI | Journal | LICENSE |
|:---|:---|:---|:---|:---|
| Molecular Biology | PMC13080398 | 10.1016/j.isci.2025.113995 | iScience | CC BY 4.0 |
| Biomedical / Nanomedicine | PMC12918234 | 10.1016/j.isci.2025.114547 | iScience | CC BY 4.0 |
| AI / Agricultural Engineering | PMC12915276 | 10.1016/j.isci.2025.114411 | iScience | CC BY 4.0 |

### 4.2 Phase 3 PubMed 解決率

| Fixture | 解決率 | 主因 (推定) |
|:---|:---:|:---|
| vancouver_24refs (Day11) | 22/24 = 91.7% | 緩和ケア医学、PubMed coverage 高 |
| apa_45refs (Day16) | 25/45 = 55.6% | 社会心理 + 政府文書 + 書籍 |
| **cell_45refs (Day17)** | **30/45 = 66.7%** | 分子生物 (PubMed 高 coverage) + 生医 (中) + AI 工学 (低) の混在 |

Cell 解決率は APA より高いが Vancouver より低い. 分子生物・生医学領域は PubMed 収録率が高い一方、AI 工学領域では book chapter / proceedings / web page refs が大半で PubMed 未収録.

### 4.3 三分類分布

`baseline_three_class_classification.json` (15 entries = unresolved refs):
- **A** (真の捏造、Crossref 404): **14 件**
- **B** (MEDLINE 非収録誌): 0 件
- **C** (収録誌 indexing 漏れ): 0 件
- **unknown** (network error fail-soft): 1 件

Day16 (apa_45refs) が SSL 問題で大半 unknown (16/20) に倒れたのと対照的に、Day17 では Crossref API が正常動作し A=14 と多発. **Day16-17 で同じ環境・同じ Mac Python なのに動作差**があるのは、Day16 の三分類実行時 (2026-05-17) と Day17 (2026-05-18) で SSL chain の状態が変わった可能性、あるいは Crossref API の応答速度・rate limit の差.

A=14 の多くは AI 工学領域 (PMC12915276) の book chapter / web page / industry report 系 references が Crossref で 404 を返した結果と推定. **真の捏造ではなく Crossref 未登録の正当 refs を A 分類している false positive の可能性が高い** → Day18+ で改修候補 (例: `<element-citation publication-type="book">` 等を `<collab>` + book 信号で B 分類に振る).

---

## 5. 教訓 (D17-1, D17-2)

### 5.1 D17-1: brainstorming の template 効果

Day16 で確立されたパターンを Day17 で **質問 6 → 2 に圧縮**できた事例.

**効果**:
- brainstorming 時間: Day16 ~30min → Day17 ~10min (約 1/3)
- ユーザー認知負荷: 6 multi-choice → 2 multi-choice
- 設計品質: 同等 (template が枠を提供するため判断品質を維持)

**学び**: 同型 task 連続実施では、前回 SPEC を「設計言語の参照点」として明示的に template 化することで、brainstorming 段階を大幅短縮可能. ただし「同型と思って実は差分があった」リスクがあるため、最低 1 質問は差分確認に充てる必要あり (Day17 Q2 の論文選定確認がこれに相当).

**適用範囲**: Harvard / Chicago / Nature style 等の追加 fixture 作業で同じ pattern 適用可能.

### 5.2 D17-2: production code 改修ゼロでの fixture 追加 (D16-1 波及効果)

Day16 で Vancouver Veto regex を `\((?:19|20)\d{2}[a-z]?\)` に拡張したことで、Cell-style の `(YYYY)` も自動的に reject される結果となり、Day17 では production code 改修ゼロで Cell fixture 追加を達成. **Day16 D16-1 教訓の波及効果**として記録.

**事象**: Day17 PLAN 設計時点では「production code 改修なし見込み」と明記したが、Day16 では PLAN でも同じ表現をしながら実装段階で regex 拡張が必要になった (refs #32, #34 の APA 7 disambiguation suffix `(2020a)`). Day17 では実際に改修ゼロで完了.

**学び**: regression 保護 fixture を追加する際、**前 fixture で発見・修正した invariant が新 fixture でも有効か**事前検証することで、production code 改修の要否を予測可能. 具体的検証手順:

1. 新 fixture の主要表記 sample (例: `Smith, J.A., and Brown, K.L. (2023). ...`) を python repl で `is_mdpi_style()` に渡して確認
2. False が返る = 改修不要、True が返る = 改修必要

**適用範囲**: Day16-17 で確立された regex 拡張が APA 7 / Cell 共通の `(YYYY[a-z]?)` を完全 cover しているため、Harvard / Chicago / Nature style も同 invariant で reject される見込み.

---

## 6. 残存タスク (Day18 以降)

### 6.1 Day7 §9.3 long-term task の達成状況 (Day17 末)

| タスク | 状態 | 残し方 |
|:---|:---:|:---|
| Vancouver golden fixture | ✅ Day11 | — |
| Day9 (Z) 未解決 2 件 MEDLINE 調査 | ✅ Day13 | — |
| Day13 §6 案 A: 3 分類 audit logic | ✅ Day15 | — |
| APA 系 golden fixture | ✅ Day16 | — |
| Cell 系 golden fixture | ✅ Day17 (本日) | — |
| **MCP/hook 経由 Stage 3 配線** | ⏳ Day18+ | 設計議論大、複数セッション |
| **GitHub remote 追加と push** | ⏳ Day18+ | secret scan + README 整備、外部公開判断要 |

### 6.2 Day17 が生成した新規候補

- [ ] **Harvard / Chicago / Nature style fixture** (Day16-17 と同型 pattern を他 style に適用、`_format_authors(style=...)` 拡張)
- [ ] **AI 工学領域 book/web refs の三分類改修** (Day17 で A 多発、false positive 抑制): `<element-citation publication-type="book">` や `<collab>` + book/proceedings 信号で B 分類に振る改修
- [ ] **三分類 audit の SSL 問題解消後 Day16 baseline 再生成** (Day17 では正常動作したが、Day16 baseline は SSL 問題下で固定. 再現性のため後日再生成検討)
- [ ] **build_cell_fixture.py のテスト追加** (`_normalize_initials(cell_mode=True)` 5 cases を `tests/` 配下に正式昇格)

### 6.3 Day18+ 推奨着手順

1. **GitHub remote + push** (secret scan 要、公開判断要、~2h、最高優先度、外部公開 readiness 向上)
2. **AI 工学 book/web refs 三分類改修** (Day17 で発見した false positive を抑制、~2h、中優先度)
3. **Harvard 系 fixture** (Day17 template 再利用、~2h、中優先度)
4. **MCP/hook 経由 Stage 3 配線** (設計議論大、複数セッション、最後)

---

## 7. 次セッション再開時のプロンプトテンプレート

### パターン 1: Day18 として GitHub remote + push (推奨)

```
Day18 として、本プロジェクトを GitHub に push します.
remote 設定 → 既存 68 commits + 全 fixture (mdpi_149refs,
vancouver_24refs, apa_45refs, cell_45refs, three_class_classification)
を含めて push. 公開リポジトリ vs プライベート の選択、README.md の整備、
.gitignore 最終確認、secret scan を含めて段階確認しながら進めて
ください.
```

### パターン 2: Day18 として AI 工学 book/web refs 三分類改修

```
Day18 として、Day17 cell_45refs で発生した三分類 A 多発 (14/15) の
false positive 問題を改修します. AI 工学領域の book chapter / web page
/ industry report 系 references を「真の捏造 (A)」ではなく「MEDLINE 非
収録 (B)」に振り直す logic を crossref_check / three_class_classifier に
追加. brainstorming → SPEC → TDD で進めてください.
```

### パターン 3: Day18 として Harvard fixture

```
Day18 として、Harvard style の golden fixture を新規追加します
(Day16 apa_45refs / Day17 cell_45refs と同型 pattern). PMC OA Harvard-style
採用論文 3 本選定し、tools/build_harvard_fixture.py を build_cell_fixture.py
から template 化. cell_mode flag を style="harvard" 等に拡張する設計も
検討.
```

### パターン 4: Day18 として MCP/hook 配線 (大型)

```
Day18 として、Stage 3 (Claude UI 起動の自動配線) を実装します.
MCP server / hook 経由で Claude Code → ローカル command → docx 入力 →
audit 出力 → Claude UI への結果返却パイプラインを設計. 議論大規模の
ため SPEC 段階まで複数セッション覚悟.
```

---

**記録完了日**: 2026-05-18 (Day17)
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day17 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day17.md` (Claude Opus 作成予定)
**ステータス**: Day17 archive 完成、Day18 着手準備完了 (4 パターンプロンプトあり)
