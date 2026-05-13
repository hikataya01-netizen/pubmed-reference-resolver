# DAY12_LESSONS_LEARNED.md

**Day12 = SETUP_API_KEYS.md 新設 (中期タスク 6/6 = 100% 完了の節目)**

**作成日**: 2026/05/13
**作成者**: Claude Code (Sonnet 4.6)
**配置**: `docs/sessions/day12/DAY12_LESSONS_LEARNED.md`
**対応 commit 範囲**: `9969063` + 本書 archive commit (計 2 commits)
**対応する指示書**: なし (Day11 archive §7 パターン 1 に対する単発承認 「1 を進めて下さい」)

---

## 0. 本書の位置づけ

Day12 は Day7 PHASE_0_VERIFICATION_REPORT §9.2 中期タスクの **最後の 1 件**「API key セットアップ手順 docs 化」を完了した. Day8-11 で順次クローズしてきた中期タスク 6 件全てが本日でクローズし、プロジェクトは長期タスク (§9.3) フェーズに移行する.

本書は以下を記録する:

1. Day12 のフェーズ構成 (1 commit + archive)
2. SETUP_API_KEYS.md の構造設計 (8 章、機能分離の理由)
3. `docs/operations/` ディレクトリ新設の意義
4. Day12 で抽出された教訓 3 件 (D12-1, D12-2, D12-3)
5. main branch 最終形状と Day13 への引継ぎ

---

## 1. Day12 のフェーズ構成

| フェーズ | commit | 達成 |
|:---:|:---:|:---|
| 1 | `9969063` | docs/operations/SETUP_API_KEYS.md (281 行、8 章) を新設 |
| 2 | (本 commit) | Day12 archive (README + LESSONS) |

---

## 2. SETUP_API_KEYS.md の構造設計

### 2.1 8 章構成

| § | タイトル | 主内容 |
|:---:|:---|:---|
| 0 | このドキュメントで解決すること | 2 種 API の必須度マトリクス (USAGE_QUICKSTART §III と整合) |
| 1 | ANTHROPIC_API_KEY の取得手順 | console.anthropic.com 手順 + 想定費用表 (Day9 (Z) 実測引用) |
| 2 | NCBI_API_KEY の取得手順 | ncbi.nlm.nih.gov 手順 + 効果 (3→10 req/sec) |
| 3 | .env ファイルの配置 | フォーマット, main.py の 4 候補探索順序, 推奨配置 (Day9 (Z) 実例), .gitignore による保護 |
| 4 | .env 内容の検証 (key 値は表示せず) | 安全確認 3 方法 (`ls -la` / `grep -oE` / `awk length`) |
| 5 | Day8 env loader 改修以降の挙動 | 空値 overwrite, env -u workaround 不要, `_inject_env_kv()` 共有 |
| 6 | トラブルシューティング | Q1-Q4 (`ANTHROPIC_API_KEY not set`, 429 rate limit, env-file not found, .env を git commit してしまった時の緊急対処) |
| 7 | 関連リソース | クロスリファレンス table (USAGE_QUICKSTART, DAY8 LESSONS, DAY9 SPEC, etc.) |
| 8 | API key を絶対に commit しないために | 5 リスク場所 (.env.save, .env.local, shell history, commit message, log file) + 対処 |

### 2.2 USAGE_QUICKSTART との機能分離

| docs | 役割 | 対象読者 | 詳細度 |
|:---|:---|:---|:---|
| `skill_package/references/USAGE_QUICKSTART.md` | スキル即時利用ガイド | エンドユーザー (skill 起動者) | §III で必須度マトリクス、§VI でコスト試算 |
| **`docs/operations/SETUP_API_KEYS.md`** (Day12 新設) | **運用詳細マニュアル** | **API key セットアップ担当者** (= 多くは同一人物だがロール分離) | **取得手順 + 配置 + Day8 改修詳細 + Q&A** |

「**最初の入口は USAGE_QUICKSTART、深掘りは SETUP_API_KEYS**」という階層化. 利用者は USAGE_QUICKSTART §I-III で「Vancouver なら ANTHROPIC 必須」を知り、SETUP_API_KEYS §1 にジャンプして取得手順に進む流れ.

→ 学び D12-2 として教訓化.

### 2.3 key 値を表示しない安全確認方法 (§4)

Day7-9 で実践した「ファイルサイズ + key 名のみ抽出 + 行長計測」の 3 方法を文書化:

```bash
# (a) 存在 + permission のみ
ls -la ~/.claude/skills/pubmed-reference-resolver/.env

# (b) key 名のみ抽出 (値は表示しない)
grep -oE '^[A-Z_][A-Z_0-9]*=' ~/.claude/skills/pubmed-reference-resolver/.env

# (c) 行長計測 (実 key vs placeholder の推測)
awk '{print NR, length($0)}' ~/.claude/skills/pubmed-reference-resolver/.env
```

これは「key は **`.env` の中だけに存在する**」原則を CI/協働環境で保つための実用 know-how. Day12 で初めて文書化された.

---

## 3. `docs/operations/` ディレクトリ新設の意義

### 3.1 既存 docs 構造との並び

| ディレクトリ | 性質 | 内容 |
|:---|:---|:---|
| `docs/sessions/dayN/` | 時系列 archive | 各セッションの README + LESSONS_LEARNED + SPEC (Day9 のみ) |
| `docs/templates/` | 構造設計 | 再利用可能なテンプレート (TEMPLATE_phase_instructions.md, TEMPLATE_day_record.md, etc.) |
| **`docs/operations/`** (Day12 新設) | **横断的 how-to** | **運用知識マニュアル** (本日: SETUP_API_KEYS.md) |

### 3.2 この分類が必要だった理由

Day7-11 で蓄積された運用知識 (env loader 改修詳細, gitignore 戦略, .env 配置 best practice) は、特定セッションの archive に分散保管されていた:

- env loader 詳細 → `docs/sessions/day8/DAY8_LESSONS_LEARNED.md` §3
- gitignore 戦略 → `docs/sessions/day7/`, `docs/sessions/day10/`
- .env 配置 → `docs/sessions/day9/DAY9_LESSONS_LEARNED.md` §8.2 (env loader 問題)

これらを「**API key セットアップを今やる人**」が参照する場合、複数の archive を横断する必要があり、初心者には負担が大きかった. `docs/operations/` 配下に「**運用 how-to をまとめた 1 文書**」を置くことで、archive へのリンク (§7 関連リソース) は保ちつつ、最初の入口を 1 つに統合.

→ 学び D12-1 として教訓化.

---

## 4. Day12 で抽出された教訓 3 件

### 学び D12-1: docs/operations/ 新設 — 運用知識を session archive と分離保管

**本質**: session archive (時系列) は「いつ何が起きたか」の記録、operations docs (横断的) は「今やる人がどう操作するか」のマニュアル. 両者を混同すると、session archive が肥大化したり、運用 docs を session 別に分散探索する負担が発生する.

**応用先**:
- Day13 以降で運用 docs を追加する場合は `docs/operations/` 配下に置く慣行
- 例候補: `docs/operations/CI_SETUP.md`, `docs/operations/BACKUP_RESTORE.md`, `docs/operations/DEPLOYMENT.md`
- session archive (LESSONS) と operations docs はクロスリファレンスで連結 (operations §7、archive §7-8 等)

**Day1-11 既存学びとの関係**:
Day7 で確立された「`docs/templates/` で再利用可能性を担保」(構造設計) の延長で、Day12 で「`docs/operations/` で横断 how-to を担保」(運用設計). docs 構造の **第 3 の柱**を確立.

### 学び D12-2: 利用者向け docs (USAGE_QUICKSTART) と運用詳細 docs (SETUP_API_KEYS) の機能分離

**本質**: 同じ topic (API key) でも、エンドユーザーが「スキル使うのに何が必要?」と聞く時と、運用者が「どう取得して .env に置くか?」と聞く時では、必要な情報粒度が違う. 1 文書に詰めると「ユーザーには重く、運用者には浅い」両端不満になる.

**応用先**:
- 利用者向け docs は「決定マトリクス + 結果」(USAGE_QUICKSTART §III の必須度表 + §VI のコスト) で済ませる
- 運用詳細 docs は「手順 + 検証 + Q&A + リスク」(SETUP_API_KEYS の 8 章) で network depth を担保
- 両者をクロスリファレンスでリンク (USAGE_QUICKSTART で取得手順を聞かれたら → SETUP_API_KEYS §1 へジャンプ)

**Day1-11 既存学びとの関係**:
Day10 D10-2 (数値の出典明示) の docs 設計版. 「読者ロール別の情報粒度設計」を docs 階層化で実現.

### 学び D12-3: 中期タスク 100% 完了の節目 — long-term task に移行できる状態

**本質**: Day7 PHASE_0_VERIFICATION_REPORT §9.2 中期タスク 6 件が Day12 で全クローズ. プロジェクトは「短期 + 中期 = 全 8 件完了」状態となり、残るは §9.3 long-term task のみ. これは「**中期タスクを順次消化する開発フェーズ → 長期タスク選択フェーズ**」への質的移行を意味する.

**応用先**:
- 残存タスクを「短期 / 中期 / 長期」と分類する設計 (Day7 §9 で確立) は、進捗の可視化と移行判断に有用
- 「中期 100% 完了」のような節目は archive で正式に記録 (本書 §0 と §6.2)
- 長期タスクは「やる / やらない」「いつやる」が個別判断 → Day13 以降は **タスク選択型** のセッション運営に移行

**Day1-11 既存学びとの関係**:
Day7 で確立されたタスク分類体系の運用検証. 12 セッション経過時点で、分類体系が機能していることが実証された (短期 2 件 = Day8 で 1 セッション完結 / 中期 4 件 = Day9-12 で 4 セッション分散 / 長期は単発でやる/やらない判断).

---

## 5. main branch の最終形状 (Day12 完了時)

### 5.1 commit history (Day12 範囲)

```
(本 commit)  docs(sessions): archive day12 SETUP_API_KEYS session
9969063      docs(operations): add SETUP_API_KEYS.md (Day7 §9.2 中期最後の 1 件完了)
9c83c53      docs(sessions): archive day11 vancouver fixture session              ← Day11 末
... (Day1-Day11 commits omitted)
```

### 5.2 統計

| 指標 | 値 |
|:---|:---:|
| main commit count (Day12 完了時、本 commit 含む) | **42** (Day11 末 40 → +2) |
| test 健全性 | **71 passed, 1 skipped** (Day11 末から不変、functional change なし) |
| 改修ファイル | (なし、production code 触れず) |
| 新規 docs | `docs/operations/SETUP_API_KEYS.md` (281 lines) |
| 新規 archive | `docs/sessions/day12/` (2 ファイル: README + LESSONS) |
| 新規ディレクトリ | `docs/operations/` (Day12 で新設) |
| identity | 全 commit `Hideki Katayama <hikataya01@gmail.com>` |

### 5.3 Day12 の本質的な達成

1. **Day7 §9.2 中期タスク 100% 完了** (6/6、Day8-12 の 5 セッションで完結)
2. **`docs/operations/` ディレクトリ新設** — docs 構造の第 3 の柱
3. **API key セットアップの一元 docs 化** — 散在していた運用知識を 1 文書に統合 (281 行、8 章、Q&A 4 件)
4. **「key 値を表示しない安全確認」know-how の文書化** (§4)
5. **archive 連鎖 7 連続達成** (Day6-12)

---

## 6. 残存タスク (Day13 以降は long-term のみ)

Day7 PHASE_0_VERIFICATION_REPORT §9 の最終更新版 (Day12 完了反映):

### 6.1 短期 (Day8 で完了、再掲)

- [x] main.py env loader の空値上書き対応
- [x] 環境依存フィールドの test 正規化拡張

### 6.2 中期 (Day9-12 で完了、本日 100% 達成)

- [x] Vancouver/AMA 系 parser 改善 (Day9)
- [x] USAGE_QUICKSTART parser 限界注記 (Day10)
- [x] **API key セットアップ手順 docs 化 (Day12)** ← 中期最後
- [x] 旧スキル削除 (Day10)

### 6.3 長期 (Day11 で 1 件部分完了、残 4 件)

- [x] Vancouver golden fixture (Day11)
- [ ] APA / Cell 系 golden fixture (Vancouver と同じハイブリッド命名規約で)
- [ ] MCP/hook 経由 Claude UI 起動配線 (Stage 3)
- [ ] Day9 (Z) 残存未解決 2 件 (#17 Davey, #22 Gallina) の MEDLINE 非収録調査
- [ ] GitHub remote 追加と push

---

## 7. 次セッション再開時のプロンプトテンプレート

Day13 以降は long-term task からの選択型セッション. user 判断で着手順を決定.

### パターン 1: APA/Cell 系 golden fixture (Vancouver fixture 設計を踏襲)

```
Day13 として、APA 系の golden fixture を新規追加します
(Day11 で確立された expected_*/baseline_* ハイブリッド命名規約を踏襲).
入力 docx をどう用意するかから議論してください
(Day9 (Z) のような既存実機データがない場合は、合成サンプルか、
別の実 docx を準備してもらう). TDD で進めてください.
```

### パターン 2: 未解決 2 件の MEDLINE 非収録調査

```
Day13 として、Day9 (Z) で残った未解決 2 件
(Ref #17 Davey 2003, Ref #22 Gallina 2016) を調査します.
docs/sessions/day9/DAY9_LESSONS_LEARNED.md §4.4 を参照し、
PubMed 検索 + 必要に応じて DOI 解決で MEDLINE 非収録の可能性を
検証してください. 調査結果を docs/sessions/day13/ に記録してください.
```

### パターン 3: GitHub remote 追加と push

```
Day13 として、本プロジェクトを GitHub に push します.
remote 設定 → 既存 42 commits + 全 fixture を含めて push.
公開リポジトリ vs プライベートリポジトリの選択、
README.md の整備 (現状はプロジェクト本体に存在?確認要), .gitignore
最終確認, secret scan を含めて TDD 風に段階確認しながら進めてください.
```

### パターン 4: MCP/hook 経由 Claude UI 起動配線 (Stage 3)

```
Day13 として、Stage 3 = Claude UI 経由でのスキル自動起動を配線します.
USAGE_QUICKSTART §0 で言及した「Stage 3 (Claude UI 経由)」が現状未配線
の状態を解消. MCP server か hook で main.py を呼ぶ実装を検討してください.
brainstorming + TDD で進めてください.
```

---

**記録完了日**: 2026/05/13
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day12 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day12.md` (Claude Opus 作成予定)
**ステータス**: Day12 archive 完成、中期タスク 100% 完了、Day13 (長期 task 選択型) 着手準備完了
