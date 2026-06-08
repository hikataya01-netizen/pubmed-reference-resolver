# dev-light / dev-strict スキル — 設計仕様 (Design Spec)

**作成日**: 2026-06-08
**対象**: superpowers ワークフローの「重さプロファイル」を 2 つの user-level カスタムスキルに切り出す
**動機**: Day22〜30 で superpowers フルフロー (brainstorming → writing-plans → subagent-driven-development) を実証したが、Day30 で 16 subagent dispatch が重く、処理時間とコンテキスト消費が大きいと判明した

---

## §1 背景と目的

### §1.1 重さの実態 (Day30 実データ)

| 要因 | 実態 |
|:---|:---|
| subagent 数 | 5 Task × (implementer + spec reviewer + code quality reviewer) = 16 dispatch |
| コンテキスト重複 | 各 subagent が 1073 行の plan やコード・git 状態を毎回読み込み直す |
| モデル | subagent を `general-purpose` で dispatch = 親と同じ最上位モデル継承。機械的タスクにも重いモデル |
| adversarial review | reviewer が repo を再走査して網羅検証 (Task 3 implementer は単独で約 16 分) |

二段 adversarial review が実際に効いたのは Day25 (parser バグの根本原因特定) と Day29 (I-1 permissions 指摘) 程度で、大半の Task は spec compliant 一発通過だった。**タスクの性質に重さを合わせるのが本質的な軽量化**である。

### §1.2 目的

superpowers の各サブスキルはそのまま活かしつつ、「どのサブスキルを・どの順序で・どの軽量化パラメータで使うか」を規定する 2 つのオーケストレーション・スキルを作る:

- **dev-light**: 最軽量。inline 実装中心、subagent は微妙な変更のみ
- **dev-strict**: 品質最優先。フル subagent-driven + 二段 adversarial review + モデル階層化

---

## §2 設計上の Question と採用案

### §2.1 Q1: 配置

| Option | 概要 | 採用可否 |
|:---|:---|:---:|
| **(A) user-level 汎用版** ✓ | `~/.claude/skills/` に配置、任意のソフト開発で使える | **採用** |
| (B) project-level 固有版 | pubmed-reference-resolver 専用、Day命名・archive を埋込 | ✕ |
| (C) user-level + 薄い project 層 | 汎用スキル + CLAUDE.md に固有プロファイル | ✕ |

**採用根拠**: dev-light/dev-strict は「コード開発ワークフロー」の汎用手法であり、特定プロジェクトに縛られない。Day命名・archive 等の固有慣習はスキルに埋め込まず、「プロジェクトの慣習があれば従う」と汎用記述する。

### §2.2 Q2: 命名

| Option | 軽量 / 厳格 | 採用可否 |
|:---|:---|:---:|
| **(A) dev-light / dev-strict** ✓ | 簡潔、対比明確、起動しやすい | **採用** |
| (B) lightweight-workflow / rigorous-workflow | 自己説明的だが長い | ✕ |
| (C) solo-dev / review-driven-dev | 手法の本質を表すが対比がやや不明瞭 | ✕ |

**採用根拠**: 簡潔で対比が一目瞭然。「Day31 を dev-light で」と起動しやすい。トリガー語は名前と独立に description で充実させる。

### §2.3 Q3: 実装方式

| Option | 概要 | 採用可否 |
|:---|:---|:---:|
| **(I) superpowers ラッパー型** ✓ | 既存サブスキルを呼ぶ順序とパラメータを規定 | **採用** |
| (II) 自己完結型 | superpowers 非依存、独自にフロー全体を記述 | ✕ |

**採用根拠**: Day22〜30 で実証済みの superpowers フローを土台にし、「重さの匙加減」だけを 2 スキルで分岐させる方が保守コスト最小。superpowers 更新に追従できる。

### §2.4 Q4: モデル階層化マッピング

| Option | 概要 | 採用可否 |
|:---|:---|:---:|
| **(3 段階)** ✓ | 機械的=haiku、統合/judgment/review=sonnet、設計/最終=opus | **採用** |
| (2 段階) | 実装/review=sonnet、設計=opus、haiku 不使用 | ✕ |
| (原則のみ) | 「least-powerful を選ぶ」原則だけ、具体割当は都度判断 | ✕ |

**採用根拠**: subagent-driven-development 公式が推奨する「least powerful model that can handle each role」原則を具体化。コストと品質のバランス。haiku は機械的タスク (config/style/docs/単純 test) に限定し、判断を要するタスクには使わない。

---

## §3 共通アーキテクチャ

両スキルとも superpowers のサブスキル (`brainstorming` / `writing-plans` / `executing-plans` / `subagent-driven-development`) を controller (Claude) が順次 invoke する**オーケストレーション指示書**である。superpowers 本体には手を入れない。

**両スキル共通の不変条件**:
- brainstorming の **HARD-GATE (design 承認まで実装しない) を温存**。軽量化対象にしない
- ユーザーの明示的指示 (CLAUDE.md) が最優先 (superpowers > default の優先順位を維持)
- conventional commits、段階的合意、品質検証は維持

---

## §4 dev-light の設計 (Pattern B 最軽量)

### §4.1 フロー

```
brainstorming (質問は推奨即決で最小化、HARD-GATE は維持)
  → spec + plan を 1 doc に統合 (別々の commit にしない、1 commit)
  → executing-plans で controller が inline 実装 (subagent dispatch なし)
  → review も inline (verification-before-completion でセルフチェック)
  → archive はプロジェクトの慣習があれば作成 (汎用版なのでオプション)
```

### §4.2 subagent 格上げ基準

以下のいずれかを含む Task は、例外的に subagent + 二段 adversarial review に格上げする (dev-strict 相当の扱い):

1. **parser / 正規表現 / 境界ロジック / アルゴリズム**の微妙な変更
2. **複数ファイルに跨り副作用が読みにくい統合**
3. **セキュリティ** (認証・機密・権限) に関わる変更
4. **データ破壊リスク** (一括修正・削除・migration)

それ以外 (config・docs・style・単純な関数追加・test 追加) は inline。

### §4.3 効果

- subagent dispatch のオーバーヘッド (plan 全文の再読み込み) を排除
- controller のコンテキストは実装で消費されるが、dispatch 往復が無くなり全体は高速
- 品質ゲートは「重要な変更だけ格上げ」で担保

---

## §5 dev-strict の設計 (Pattern C 品質最優先)

### §5.1 フロー

```
brainstorming (フル) → writing-plans (フル bite-sized)
  → subagent-driven-development (全 Task で implementer + 二段 adversarial review)
  → archive
```

Day22〜30 の実証フローそのまま。**変更点はモデル階層化のみ** (速度底上げ)。二段 adversarial review は全 Task 温存。

### §5.2 dev-strict が適する場面

- parser / アルゴリズムの中核ロジック変更
- 大規模 migration、破壊的操作を伴う作業
- 複数サブシステムに跨る統合
- 「絶対に壊したくない」高リスク変更

---

## §6 モデル階層化マッピング (両スキル共通)

`Agent` tool の model パラメータでタスク種別に割り当てる:

| タスク種別 | モデル | 例 |
|:---|:---|:---|
| 機械的実装 | **haiku** | config 追加、style 修正、docs 作成、単純な test 追加 |
| 統合・判断を伴う実装 | **sonnet** | parser 修正、複数ファイル統合、デバッグ |
| spec compliance review | **sonnet** | 仕様準拠の照合 |
| code quality review | **sonnet** | 品質・保守性評価 |
| 設計判断・最終 review | **opus** (または親継承) | アーキテクチャ、横断的最終確認 |

**原則**: 「各ロールを処理できる least powerful model を選ぶ」。haiku で不足が判明したら sonnet に格上げ (subagent-driven-development の BLOCKED 対応に準拠)。

---

## §7 SKILL.md 構造

各スキルは `~/.claude/skills/<name>/SKILL.md` として配置:

```markdown
---
name: dev-light
description: <トリガー語を含む説明文。いつ起動すべきか、どう軽量か>
---

# <タイトル>

## いつ使うか / いつ dev-strict に切り替えるか
## フロー (図 or 箇条書き)
## subagent 格上げ基準
## モデル階層化マッピング
## superpowers サブスキルとの関係
```

**description のトリガー設計**:
- dev-light: 「軽量に開発」「素早く実装」「小規模な変更」「inline で」等 + 「小〜中規模・低リスクの開発タスク」
- dev-strict: 「厳格に開発」「フルレビューで」「高リスク変更」「品質最優先」等 + 「parser/アルゴリズム/migration 等の高リスク変更」
- 相互参照: dev-light は「重い変更は dev-strict へ」、dev-strict は「軽い変更は dev-light へ」と記載

---

## §8 配置とファイル

| File | 内容 |
|:---|:---|
| `~/.claude/skills/dev-light/SKILL.md` | dev-light スキル本体 |
| `~/.claude/skills/dev-strict/SKILL.md` | dev-strict スキル本体 |
| `docs/superpowers/specs/2026-06-08-dev-light-dev-strict-skills-design.md` | 本 spec (pubmed-reference-resolver repo 内、設計記録) |

**注**: スキル本体は user-level (`~/.claude/skills/`) に置くため pubmed-reference-resolver の git 管理外。spec/plan は設計記録として本 repo の docs/ に残す (過去の spec と一貫、追跡可能)。

---

## §9 検証方法

スキルは実行可能コードでないため、検証は:

1. **description のトリガー妥当性**: dev-light/dev-strict が意図通り起動・区別されるか (description の語が曖昧でないか)
2. **フロー記述の内部矛盾チェック**: HARD-GATE 温存、格上げ基準の網羅性、モデルマッピングの一貫性
3. **実使用での効果測定**: 次回セッション (Day31 等) で実際に dev-light を使い、subagent 数・処理時間が削減されたか測定

スキル品質の客観評価には `skill-creator` の eval 機能や `superpowers:writing-skills` の検証手順を活用できる。

---

## §10 Out of scope

1. superpowers 本体の改変 (ラッパー型を採用、本体には触れない)
2. project-level への固有プロファイル埋込 (汎用版に集約)
3. dev-light/dev-strict 以外の中間プロファイル (YAGNI、2 つで十分)
4. 自動モデル選択の機械化 (description の原則記述で controller が判断)
5. pubmed-reference-resolver 固有の Day命名・archive 慣習のスキル化 (汎用記述に留める)

---

## §11 LESSONS / 留意点

1. **このスキル作成自体が「軽量化のジレンマ」**: スキルを作る作業自体は docs 中心で軽い。本来 dev-light 相当 (inline) が妥当だが、dev-light がまだ存在しないため初回はフロー規定に従う
2. **superpowers 依存の明示**: ラッパー型のため superpowers プラグインが前提。description に明記
3. **モデル世代変化への耐性**: haiku/sonnet/opus の具体名は将来変わり得る。「tier (機械的/判断/設計)」を主軸に記述し、具体名は補足とする

---

## §12 関連参照

- [Day30 LESSONS](../../sessions/day30/DAY30_LESSONS_LEARNED.md): 16 subagent dispatch の重さが本スキルの動機
- [superpowers:subagent-driven-development]: モデル選択原則 (least powerful model) の出典
- [superpowers:executing-plans]: dev-light の inline 実装の土台
- [superpowers:writing-skills] / skill-creator: スキル実装・検証手段

---

**End of Spec**
