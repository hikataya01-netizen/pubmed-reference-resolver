# Day26 Lessons Learned (2026-05-24)

## §1 概要

Day26 は Day25 Task 2 code quality review で発見された `main.py` 内 3 箇所の bare `[A-Z]`
を修正し、Day25 で導入した 5 箇所と合計 8 箇所を module-level 定数 `_UPPERCASE_LATIN1`
に統一する DRY refactor セッション.

### §1.1 セッション開始時の状態

- **107 passed / 0 skipped** (Day25 末)
- main.py に bare `[A-Z]` が 3 箇所残存 (L299, L303, L353) — Day25 review で発見、
  Top priority として記録
- `[A-ZÀ-ÖØ-Þ]` は Day25 で 5 箇所に導入済だが、3 箇所が literal のまま残存
  → non-ASCII 著者名 corpus での pre-references strip 失敗という潜在的 bug

### §1.2 セッション終了時の状態

- **111 passed / 0 skipped / 0 failed** (+ 4 unit test)
- main.py 内 bare `[A-Z]`: **0 (完全除去)**
- `_UPPERCASE_LATIN1` 参照: **8 箇所**で f-string 参照に統一 (15 occurrences across 7 lines)
- Day25 docstring: 5 行重複説明 → 3 行 reference に圧縮
- **LLM cost: $0** (refactor + test 追加のみ、外部 API 呼び出しなし)

---

## §2 brainstorming 段階

Day26 spec §1.4 で 3 つの設計 Question (Q1/Q2/Q3) を brainstorm し、各 Option を評価した上で採用案を決定した.

### §2.1 Q1: 実装 Approach の選択

| Option | 概要 | 採用可否 | 不採用理由 |
|:---|:---|:---:|:---|
| **(A) Inline fix** | 3 箇所を `[A-ZÀ-ÖØ-Þ]` に直接書き換え、定数化なし | ✕ | DRY 違反継続。Day25 の 5 箇所 literal も残存し、将来拡張コスト変わらず |
| **(B) module-level 定数抽出** ✓ | `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` を追加、全 8 箇所を `rf"...[{_UPPERCASE_LATIN1}]..."` で参照 | **採用** | DRY 完全解消。定数 1 行 update → 8 箇所に伝播。認知コスト最小 |
| **(C) helper function** | `_uppercase_latin1_class() -> str` を定義 | ✕ | 単純な定数に対してオーバーエンジニアリング。呼び出しオーバーヘッドも不要 |

### §2.2 Q2: unit test の範囲

| Option | 概要 | 採用可否 | 不採用理由 |
|:---|:---:|:---:|:---|
| **(α) 全 3 箇所 unit test** ✓ | case 2 (Å入力/ASCII baseline) + case 3 (Ö入力) + preprocess counter | **採用** | 変更箇所を網羅。regression 防止 |
| **(β) 部分 test** | case 2 のみ、または case 3 のみ | ✕ | preprocess counter の変更が uncovered のまま |
| **(γ) test なし** | refactor のみ | ✕ | TDD の意図を損なう。DRY refactor が semantics を保持することを証明できない |

### §2.3 Q3: commit 戦略

| Option | 概要 | 採用可否 | 不採用理由 |
|:---|:---:|:---:|:---|
| **(α) Strict TDD 2-commit** ✓ | test(prep) RED commit → refactor(parse) GREEN commit | **採用** | 「何を fix したか」git log で一目瞭然。history 品質高 |
| **(β) 1 atomic commit** | test + refactor を 1 commit に統合 | ✕ | history で RED/GREEN 分離が失われ、TDD の証跡不明瞭 |

---

## §3 実装段階の経緯

### §3.1 5 commit chain

| # | SHA | type | summary |
|:---:|:---|:---|:---|
| 1 | `36c49e6` | docs(spec) | Day26 bare [A-Z] consistency + DRY refactor spec |
| 2 | `b5ad5cf` | docs(plan) | Day26 implementation plan |
| 3 | `b51bae2` | test(prep) | TDD RED: 4 unit test (case 2 Å + ASCII baseline + case 3 Ö + preprocess counter) |
| 4 | `afb5807` | refactor(parse) | TDD GREEN: _UPPERCASE_LATIN1 定数抽出 + 8 箇所統一 + Day25 docstring 圧縮 |
| 5 | (this commit) | docs(sessions) | Day26 archive |

### §3.2 Task 2 sub-step 細分化

Task 2 (TDD GREEN) は atomic commit に見えるが、内部的に以下の順序で段階実行:

| Sub-step | 内容 | 確認事項 |
|:---|:---|:---|
| A. 定数追加 | `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` を `_strip_pre_references` 直前に追加 | NameError 未発生 |
| B. 新規 3 箇所 | L299/L303/L353 の bare `[A-Z]` を `rf"...[{_UPPERCASE_LATIN1}]..."` に変更 | bare [A-Z] grep 0 hit |
| C. Day25 既存 5 箇所 | `split_references` 内 5 箇所の literal `[A-ZÀ-ÖØ-Þ]` を同様に変換 | 15 occurrences確認 |
| D. docstring 圧縮 | `split_references` docstring の重複 5 行 → 3 行 reference | 可読性向上 |
| E. verify + commit | 111 passed 確認 → refactor(parse) commit | 全 tests green |

---

## §4 設計判断と検証

### §4.1 module-level 定数 vs Inline fix の比較

Day25 末時点で「5 箇所 literal」→ Day26 で「さらに 3 箇所」= 合計 8 箇所が同一パターン.
この時点で module-level 定数化が DRY 原則上の閾値に達したと判断.

**定数化の利点:**
- Latin Extended-A 拡張時 (`Š Č Ł` 等追加) は定数 `_UPPERCASE_LATIN1` の 1 行 update だけで
  8 箇所すべてに自動伝播 → Day27+ の保守コストを推定 5-10 倍削減
- コードを読む際の認知コスト軽減: `[A-ZÀ-ÖØ-Þ]` の意味を 8 箇所ではなく定数定義 1 箇所で把握すれば足りる
- grep 可能性: `grep "_UPPERCASE_LATIN1" main.py` で即座に使用箇所 7 行特定可能

**Inline fix との比較:**
- Inline fix は工数最小だが、Day25 の 5 箇所 literal が残存し DRY 不完全のまま
- 「今回だけ直す」姿勢では次回 review でも同種指摘が発生する

### §4.2 定数定義位置の選択

`_UPPERCASE_LATIN1` を `_strip_pre_references` 関数直前 (Stage 2 セクション冒頭) に配置した理由:

1. **使用箇所との近接性**: `_strip_pre_references` が最初の使用箇所であり、読者が定数を見て
   すぐに使用されているコードに到達できる
2. **NameError 回避**: Python の module-level は上から評価されるため、定義よりも前の参照は
   NameError. `split_references` よりも前に定義する必要がある
3. **慣例的配置**: module-level 定数は関連する関数群の直前または module 冒頭が読みやすい

### §4.3 docstring の重複説明圧縮

Day25 で `split_references` の docstring に `_UPPERCASE_LATIN1` 相当の説明を 5 行で記述.
Day26 で定数定義コメントに集約したため、docstring 側の説明は 3 行の reference に圧縮した.

**圧縮前 (Day25 状態):**
- docstring 内に `[A-ZÀ-ÖØ-Þ]` の適用理由 5 行 (Latin-1 Supplement の説明含む)

**圧縮後 (Day26 状態):**
- docstring は「`_UPPERCASE_LATIN1` を使用、詳細は定数定義コメント参照」3 行
- 定数定義コメント側に Latin-1 Supplement の完全説明を集約

**判断の根拠**: DRY は文書においても適用される。同じ説明が docstring と定数定義コメントの
2 箇所に存在すると、将来の拡張時に両方を更新する必要があり更新漏れリスクが高まる.

### §4.4 `rf"..."` (raw + f-string) prefix の必須性

正規表現パターンを f-string で組み立てる場合、`rf"..."` prefix が必要:

- **`r`**: バックスラッシュを Python 文字列エスケープとして解釈させない (正規表現の `\d`, `\s` 等を保持)
- **`f`**: `{_UPPERCASE_LATIN1}` の変数補間を有効化

`f"[{_UPPERCASE_LATIN1}]"` (r なし) の場合、パターン内にバックスラッシュが含まれると
二重エスケープ問題が発生する可能性がある。今回のパターン `[A-ZÀ-ÖØ-Þ]` はバックスラッシュ
を含まないため実害はないが、`rf"..."` を使用することで将来の安全性を確保した.

---

## §5 実機検証

### §5.1 test count 推移

| タイミング | test 数 | skipped | failed |
|:---|:---:|:---:|:---:|
| Day25 末 | 107 | 0 | 0 |
| Task 1 後 (RED) | 111 | 0 | **4 (期待通り)** |
| Task 2 後 (GREEN) | 111 | 0 | **0** |
| Day26 末 | 111 | 0 | 0 |

RED → GREEN 遷移が 4 test 同時に確認できた。TDD サイクルが意図通り機能.

### §5.2 bare [A-Z] 除去確認

```bash
$ grep -nE '\[A-Z\]' main.py || echo "0 bare [A-Z] (good)"
0 bare [A-Z] (good)
```

### §5.3 `_UPPERCASE_LATIN1` 使用確認

```bash
$ grep -c "_UPPERCASE_LATIN1" main.py
7   # 定数定義 1 行 + 使用 6 行 (grep -c はマッチ行数を返す)
```

実際には f-string 内で複数回参照される行も存在し、15 occurrences across 7 lines.

### §5.4 gitleaks + CI

- `gitleaks detect --no-banner --redact`: **no leaks found** (継続)
- GitHub Actions CI (`afb5807`): **green** (pytest + gitleaks)

### §5.5 semantics-preserving 確認

mdpi_173refs 対象での parsed count: **173 件維持**
refactor 前後で出力変化なし = semantics-preserving refactor として確認.

---

## §6 教訓

### D26-1: code review 発見項目の確実な追跡

**事象:**
Day25 Task 2 code quality review で bare `[A-Z]` 3 箇所が発見された。Day25 LESSONS_LEARNED
§7 で「Day26+ Top priority」として明示記録した結果、Day26 セッション開始時に迷わず取り組めた.

**学び:**
code review で発見された latent bug の扱いには 2 つの正当な選択肢がある:

1. **同 session 内即時 fix** — scope が小さく、session time が許容する場合
2. **次 session top priority として明示記録** — scope が大きい、または session time が不足する場合

どちらを選ぶかより、「暗黙的に先送り」することを避けることが重要.
「後で見る」「TODO」程度の記録では次 session 開始時に忘却するリスクが高い.
今回は Day25 LESSONS §7 に「Day26+ Top priority: Latin Extended-A 統一の継続」と
明示したため、Day26 で確実に対処できた.

**適用範囲:**
- code review / セキュリティ review 後の発見事項の追跡
- 時間切れで完了できなかった実装の継続
- 将来の拡張点の明示的なカタログ化 (LESSONS §7 残存タスクセクション)

### D26-2: DRY refactor の閾値 — 5 箇所以上で定数化

**事象:**
Day25 で `[A-ZÀ-ÖØ-Þ]` を 5 箇所に導入したが、定数化はせず literal のままだった.
Day26 で 3 箇所を追加 = 計 8 箇所になった時点で module-level 定数化を決断した.

**学び:**
同一パターンの繰り返し数と refactor コストの観点から:

| 繰り返し数 | 推奨対応 | 根拠 |
|:---:|:---|:---|
| 1-2 箇所 | inline literal | 定数化のオーバーヘッドが利益を上回る |
| 3-4 箇所 | 状況依存 (将来拡張可能性を考慮) | 拡張予定があれば定数化 |
| **5 箇所以上** | **module-level 定数化** | 機械的 grep+replace で全箇所更新可能。認知コスト削減効果が顕著 |

Day25 の「5 箇所 literal のまま」は閾値ギリギリの判断だったが、Day26 で 3 箇所追加に
なった時点で定数化が明確に正しい選択になった.
重要な副次効果: 8 箇所すべての update を機械的に grep+replace で完了できる設計が
Latin Extended-A 拡張 (Day27+) の工数を 5-10 倍削減する見込み.

**適用範囲:**
- 正規表現パターンの繰り返し
- マジックナンバー / マジック文字列の管理
- 設定値 / 閾値の複数箇所参照

---

## §7 残存タスク (Day27+ 候補)

| 優先度 | タスク | 根拠 |
|:---|:---|:---|
| **Top** | Latin Extended-A 範囲拡張 (Š Č Ž / Ł Ć Ń / Ő Ű / Ș Ț 等) | Day26 で `_UPPERCASE_LATIN1` 定数整備済。定数 1 行 update + test 追加のみ。工数小 |
| High | mdpi_173refs 固有 manual_overrides.yaml 構築 | Day24 から継承。MDPI fast-path 完成に必要 |
| Medium | pre-commit hook gitleaks 自動実行 | Day22 handoff パターン 3。CI で確認済だが pre-commit でも防御 |
| Medium | CONTRIBUTING.md / Issue PR template | Day22 handoff パターン 2。OSS 化準備 |
| Medium | PyPI 公開 (v0.2.0 候補) | v0.1.0 リリース済、機能追加の区切り |
| Low | pyproject.toml + uv.lock 移行 | CLAUDE.md §8 整合。現在 setup.py + requirements.txt |
| Low | Crossref graceful failure 16 件の対応 | Day22 §6.3 NEW、apa_45refs corpus |
| Low | NLM fuzzy-match precision 改善 | Day22 §6.3 NEW |
| Low | tools/build_*_fixture.py の共通 utility refactor | Day23 code review 指摘 |
| Future | deterministic byte-level golden の再構築 | LLM stub 経由、Day28+ 大改修 |

---

## §8 次セッション再開プロンプトテンプレート

### パターン 1 (推奨): Latin Extended-A 拡張

Day26 で `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` 定数を整備済。
定数 1 行の更新 + 関連 unit test 追加のみで完了する見込み (工数小).

```
Day27 を開始します。

## 現状
- HEAD: (git rev-parse HEAD の値)
- 全 tests: 111 passed / 0 skipped / 0 failed
- main.py に `_UPPERCASE_LATIN1 = "A-ZÀ-ÖØ-Þ"` 定数あり (8 箇所で参照)

## Day27 ゴール
`_UPPERCASE_LATIN1` に Latin Extended-A の uppercase 範囲を追加する.
対象: Š Č Ž (U+0160, U+010C, U+017D) / Ł Ć Ń Ą Ę (U+0141, U+0106, etc.)
  / Ő Ű (U+0150, U+0170) / Ș Ț (U+0218, U+021A) 等

現在のカバレッジ: Latin-1 Supplement uppercase のみ (À-Ö, Ø-Þ)
目標カバレッジ: Latin Extended-A (U+0100–U+017E) の uppercase も追加

## Task 0 から始めてください (spec brainstorming)
```

### パターン 2: mdpi_173refs 固有 manual_overrides.yaml 構築

```
Day27 を開始します。

## 現状
- HEAD: (git rev-parse HEAD の値)
- 全 tests: 111 passed / 0 skipped / 0 failed
- mdpi_173refs: 173 件 parse 済、Crossref 失敗 件数は未集計

## Day27 ゴール
mdpi_173refs corpus に対して manual_overrides.yaml を整備する.
Crossref/NLM ともに解決できない参照の fallback として機能させる.

## 手順概要
1. mdpi_173refs で全 resolver を実行し、未解決件数を集計
2. 上位 N 件に対して DOI/PMID を手動検索して yaml に記録
3. resolver に manual_overrides.yaml を参照するロジックを追加
4. tests を追加して CI green を確認

## Task 0 から始めてください (spec brainstorming)
```

### パターン 3: CONTRIBUTING.md / Issue PR template

```
Day27 を開始します。

## 現状
- HEAD: (git rev-parse HEAD の値)
- 全 tests: 111 passed / 0 skipped / 0 failed
- GitHub リポジトリ PUBLIC 公開済、v0.1.0 リリース済

## Day27 ゴール
OSS として外部コントリビューターが参加しやすい環境を整備する.
具体的には:
- CONTRIBUTING.md (セットアップ手順 + PR フロー + code style)
- .github/ISSUE_TEMPLATE/bug_report.md
- .github/ISSUE_TEMPLATE/feature_request.md
- .github/PULL_REQUEST_TEMPLATE.md

## Task 0 から始めてください (spec brainstorming)
```
