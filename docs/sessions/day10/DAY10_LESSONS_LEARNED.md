# DAY10_LESSONS_LEARNED.md

**Day10 = USAGE_QUICKSTART 1.1 update + 旧スキル削除 + Day10 archive (軽量セッション)**

**作成日**: 2026/05/11
**作成者**: Claude Code (Sonnet 4.6)
**配置**: `docs/sessions/day10/DAY10_LESSONS_LEARNED.md`
**対応 commit 範囲**: `359d782` + 本書 archive commit (計 2 commits) + git 外 cleanup 1 件
**対応する指示書**: なし (先生からの単一プロンプトで開始)

---

## 0. 本書の位置づけ

Day10 は Day7-9 のような大型セッションと異なり、**documentation update + cleanup の軽量セッション**. 形式的な PHASE_*_INSTRUCTIONS.md を持たず、Day9 (Z) で発見した実機データを USAGE_QUICKSTART に反映する作業 + Day6 残課題のクリーンアップで完結する.

本書は以下を記録する:

1. Day10 のフェーズ構成 (2 フェーズ + archive)
2. フェーズ 1: USAGE_QUICKSTART 1.1 update (commit `359d782`)
3. フェーズ 2: 旧スキル削除 (git 外 cleanup)
4. Day10 で抽出された教訓 3 件 (D10-1, D10-2, D10-3)
5. main branch 最終形状と Day11 への引継ぎ

---

## 1. Day10 のフェーズ構成

| フェーズ | 種別 | commit / 操作 | 達成 |
|:---:|:---|:---:|:---|
| 1 | docs(skill) | `359d782` | USAGE_QUICKSTART.md を 1.0 → 1.1 に bump (4 update + meta + §X 変更履歴) |
| 2 | cleanup | git 外 (rm -rf) | `~/.claude/skills/pubmed-reference-resolver.old.20260502/` (4.0 MB, Day6 残課題) を削除 |
| 3 | docs(sessions) | (本 commit) | Day10 archive (README + LESSONS) 追加 |

---

## 2. フェーズ 1: USAGE_QUICKSTART 1.1 update (`359d782`)

### 2.1 更新内容 (4 site + meta + 新 §X)

| # | 箇所 | 旧 | 新 |
|:---:|:---|:---|:---|
| 1 | §I 3 行サマリー末尾 | 「LLM 費用: MDPI 形式は 0 円、その他形式は LLM フォールバックでも軽量化済」 | Vancouver/AMA 系の具体コスト ($0.20/24refs, Day9 (Z) 実測) を追記 |
| 2 | §III 引用スタイル直後 | (なし) | 新サブセクション「引用スタイル別の処理経路」追加. is_mdpi_style() の判定 marker, 処理経路, API key 必須性, 解決率を表形式で整理 + 重要事項リスト |
| 3 | §V Q3 「MDPI 以外で精度が低い」 | 「Day7 以降の長期タスク計画中」 | 「Day9 改修済」に書換. 解決率 14/24 → 22/24 (+33% pt), 重大エラー 4 → 0 を記載 |
| 4 | §VI パフォーマンス特性 + LLM 費用見積り | 件数のみの 3 行表 | Vancouver/AMA 24 件 (Day9 (Z) 実測) と MDPI 149 件 (Day7 Stage 1 実測) を追加. 「出典」列で推定/実測を区別. 費用見積りに Vancouver/AMA 行追加 |
| 5 | メタ情報 | バージョン 1.0 のみ | 最終更新日 2026/05/11 追加, バージョン 1.1 bump, 末尾署名を 1.0/1.1 の 2 段表記に |
| 6 | §X (新セクション) | (なし) | 変更履歴を追加. 1.0 (初版) と 1.1 (Day10 更新) の差分を 5 項目で明示 |

### 2.2 トーン選択

3 トーン候補から **A 中立的 informational** を採用:
- ⚠️ 強い警告は不安を煽り、利用者が「コスト vs 品質」のトレードオフを冷静に判断できなくなる
- 後方互換重視 (Day9 知見を末尾付録のみ) は archaeological 価値が弱い
- 中立的 informational は表形式 + 数値根拠で伝える方式 → Day9 で確立した「データドリブン」スタイルと一致

### 2.3 verification

- 全 66 test passed, 1 skipped (functional change なしの確認)
- USAGE_QUICKSTART.md: 266 → **319 行** (+63/-10)
- symlink 経由 `~/.claude/skills/pubmed-reference-resolver/references/USAGE_QUICKSTART.md` でも 319 行で読める (Day6 C-1 切替の継続動作確認)

---

## 3. フェーズ 2: 旧スキル削除 (git 外 cleanup)

### 3.1 背景

Day6 で `~/.claude/skills/pubmed-reference-resolver` を symlink に切替えた際、旧スキル (4.0 MB の実体ディレクトリ) を `pubmed-reference-resolver.old.20260502` にバックアップとして保持. PHASE_DELTA_INSTRUCTIONS.md §残存タスク に「1-2 週間後の最終削除」と明記.

Day10 時点で **9 日経過**, problem 報告なし → 削除タイミング適切.

### 3.2 実行

```bash
# 削除前確認
ls -la ~/.claude/skills/pubmed-reference-resolver*
# → symlink (現スキル) + .old.20260502 (実体ディレクトリ 4.0 MB)

# 削除
rm -rf ~/.claude/skills/pubmed-reference-resolver.old.20260502/

# 削除後確認
ls -la ~/.claude/skills/pubmed-reference-resolver*
# → symlink のみ残存

# 現スキル symlink 経由読出が引き続き動作するか確認
wc -l ~/.claude/skills/pubmed-reference-resolver/SKILL.md
# → 196 行 (Day9 末から不変)
wc -l ~/.claude/skills/pubmed-reference-resolver/references/USAGE_QUICKSTART.md
# → 319 行 (Day10 1.1 update 反映済)
head -1 ~/.claude/skills/pubmed-reference-resolver/main.py
# → """pubmed-reference-resolver: 査読用の References 逆引き検索スキル本体。
#    (二段 symlink resolution = symlink → skill_package → ../main.py が正常動作)
```

### 3.3 影響と確認

- 4.0 MB の disk 解放
- 現スキル symlink (`pubmed-reference-resolver -> .../skill_package`) は無傷
- skill discovery (Claude UI 経由) も影響なし — Claude Code の skill 一覧で `pubmed-reference-resolver.old.20260502` が消滅
- Day6 残課題 100% クリア

### 3.4 git 操作の有無

`~/.claude/skills/` は project ディレクトリ外のため、本作業は **git 管理対象外**. commit 不要. ただし archive 内 (本書 §3) で削除事実を記録することで archaeological accountability を保つ.

---

## 4. Day10 で抽出された教訓 3 件

### 学び D10-1: documentation update では過剰な確認を避ける (user feedback による retro)

**本質**: 本セッション開始時、私は brainstorming skill 風に「4 確認項目 + 3 トーン選択肢 + メタ情報の有無 + 変更履歴セクションの有無」と過剰な確認を user に求めた. user から「**処理が途中で止まっていませんか**」とフィードバックを受け、軽量セッションには軽量な進め方が適切と認識.

**Day1-9 既存学びとの関係**:
Day9 brainstorming skill では「user 承認まで実装しない HARD-GATE」が core rule だったが、これは中-大規模 feature 向け. Day7-8 で確立された「推奨案で即進む、user は結果を見て判断」パターンを軽量タスクでは優先すべき.

**応用先**:
- documentation update / cleanup / 軽量 refactor では、推奨案で即進む方式に倒す
- brainstorming skill は **複数の設計分岐がある場合** に限って起動 (今回は分岐少なく overkill)
- user feedback (今回は「途中で止まっていませんか」) を高感度で察知し、進行スタイルを動的調整

**メタ的な意義**:
本教訓自体が「user 体験のフィードバックループ」を archive に正式記録する初例. 失敗を含む retro が Day10 archive で残ることで、将来の Claude Code が同種の判断ミスを避けやすくなる.

### 学び D10-2: 数値の出典明示 (推定値 vs 実測値) が信頼性を高める

**本質**: USAGE_QUICKSTART §VI のパフォーマンス特性表を 4 列 → 4 列 + **「出典」列**に拡張し、各数値が「推定」「Day9 (Z) 実測」「Day7 Stage 1 実測」のいずれかを明示した. これにより:
- 利用者は「この数値は推測か実測か」を即判断できる
- 実測値を持たない件数 (例: Vancouver 100 件) について「未測定」と honest に記載できる
- 将来 fixture 化されたら出典欄を更新するだけで信頼性管理が継続する

**Day1-9 既存学びとの関係**:
Day9 brainstorming で「データドリブンな合意形成」(4 markers × 2 corpus 実測) を実践したのと同じ系統. 「数値があれば信頼できる」ではなく「数値の出典がわかれば信頼できる」が一段階厚い.

**応用先**:
- パフォーマンス表 / 性能比較表で「出典」列を必ず追加する慣行
- 推定値には根拠を併記する (例: 「Sonnet 4.6 単価から線形外挿、24 件実測 $0.20 を基準」)
- 実測タイミング (Day7 / Day9 等) を明記すると、再測定の必要性も判断できる

### 学び D10-3: archive 連鎖の累積価値 (Day6-10 で 5 連続)

**本質**: Day10 archive 完成により `docs/sessions/day{6,7,8,9,10}/` の 5 連続 archive が揃う. これにより:
- 任意の 1 セッションを参照する際、前後セッションの context が即取得可能
- archive 同士のクロスリファレンス (例: Day10 §3 が PHASE_DELTA_INSTRUCTIONS.md §残存タスク を参照) が成立
- 将来の Claude Code (or 別セッション) が「Day6-10 の累積知識」を読み下しやすい

**Day1-9 既存学びとの関係**:
Day7 (R+) で確立した「ad-hoc verification report」パターン、Day8 で確立した「LESSONS_LEARNED」パターンの連鎖発展. archive 連鎖は単独 archive の価値の単純和ではなく、相互参照による**指数的価値増**.

**応用先**:
- Day11 以降も archive を作る慣行を継続する (たとえ軽量でも)
- archive 末尾に「次セッションプロンプトテンプレート」セクションを必ず含める (Day8 から確立、Day9-10 でも継続)
- archive 内のクロスリファレンスを意識的に増やす (例: Day10 §1 から Day9 LESSONS §4.2 への明示参照)

---

## 5. main branch の最終形状 (Day10 完了時)

### 5.1 commit history (Day10 範囲)

```
(本 commit)  docs(sessions): archive day10 USAGE_QUICKSTART update + cleanup
359d782      docs(skill): bump USAGE_QUICKSTART to 1.1 with Day9 Vancouver Veto data
674a452      docs(sessions): archive day9 SPEC + lessons learned                       ← Day9 末
... (Day1-Day9 commits omitted)
```

### 5.2 統計

| 指標 | 値 |
|:---|:---:|
| main commit count (Day10 完了時、本 commit 含む) | **38** (Day9 末 36 → +2) |
| test 健全性 | **66 passed, 1 skipped** (Day9 末から不変、functional change なし) |
| 改修ファイル | `skill_package/references/USAGE_QUICKSTART.md` のみ |
| 新規 archive | `docs/sessions/day10/` (2 ファイル: README + LESSONS) |
| disk cleanup | `~/.claude/skills/pubmed-reference-resolver.old.20260502/` (4.0 MB) 削除 |
| identity | 全 commit `Hideki Katayama <hikataya01@gmail.com>` |

### 5.3 Day10 の本質的な達成

1. **Day9 改修の利用者向け展開完了** — USAGE_QUICKSTART 1.1 で Vancouver Veto の挙動・コスト・解決率データを公式記載
2. **Day6 残課題の最終クリア** — 旧スキル削除で disk と skill 名空間が綺麗に
3. **archive 連鎖 5 連続達成** (Day6-10) — archaeological review の利便性が一段階向上
4. **軽量セッション運用パターンの確立** (D10-1) — 過剰確認回避の指針

---

## 6. 残存タスク (Day11 以降)

Day7 PHASE_0_VERIFICATION_REPORT §9 の更新版 (Day10 完了反映):

### 6.1 短期 (Day8 で完了)

- [x] main.py env loader の空値上書き対応 (Day8: d49dc58 + 7bc009b)
- [x] 環境依存フィールドの test 正規化拡張 (Day8: b8c0e5b)

### 6.2 中期 (Day9-10 で 2 件完了)

- [x] **Vancouver/AMA 系 parser 改善** (Day9: ab25630, 解決率 +33% pt)
- [x] **USAGE_QUICKSTART に parser 限界注記 + Vancouver Veto 効果の記載** (Day10: 359d782)
- [ ] API key セットアップ手順 docs 化 (`docs/operations/SETUP_API_KEYS.md` 等) ← Day11 候補
- [x] **`~/.claude/skills/pubmed-reference-resolver.old.20260502/` 最終削除** (Day10: git 外 cleanup)

### 6.3 長期 (Day11+ 想定)

- [ ] 別ドメイン golden fixture (Vancouver / APA / Cell 等) — Day9 で Vancouver の挙動が確認できたので fixture 化候補
- [ ] MCP/hook 経由 Claude UI 起動配線 (Stage 3)
- [ ] Day9 (Z) で残った未解決 2 件 (#17 Davey, #22 Gallina) の調査 (MEDLINE 非収録の可能性)
- [ ] GitHub remote 追加と push (Day7 残課題、未着手)

---

## 7. 次セッション再開時のプロンプトテンプレート

### パターン 1: API key セットアップ手順 docs 化

```
Day11 として、Day7 §9.2 中期タスクの最後の 1 件
「API key セットアップ手順 docs 化」を実施します.
docs/operations/SETUP_API_KEYS.md (or 同等パス) を新設し、
ANTHROPIC_API_KEY と NCBI_API_KEY の取得手順、
.env 配置方法、Day8 env loader 改修以降の挙動を docs 化してください.
```

### パターン 2: 別ドメイン golden fixture 追加

```
Day11 として、Vancouver/AMA 系の golden fixture を新規追加します
(Day7 §9.3 長期タスク). Day9 (Z) で取得した Stage 2 の出力を
tests/fixtures/vancouver_24refs/ に baseline として配置し、
test_integration_vancouver_24refs.py を新設してください.
TDD で進めてください.
```

### パターン 3: 未解決 2 件の調査

```
Day11 として、Day9 (Z) で残った未解決 2 件
(Ref #17 Davey 2003, Ref #22 Gallina 2016) を調査します.
docs/sessions/day9/DAY9_LESSONS_LEARNED.md §4.4 を参照し、
MEDLINE 非収録の可能性を検証してください.
```

---

**記録完了日**: 2026/05/11
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day10 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day10.md` (Claude Opus 作成予定)
**ステータス**: Day10 archive 完成、Day11 着手準備完了
