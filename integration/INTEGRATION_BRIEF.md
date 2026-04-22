<!--
Status: Archived (2026-04-23)

本ブリーフが計画した 7 ステップの統合計画は、feature/mdpi-fast-path の main への
merge (commit 5d2d5a9) をもって完了しました。以降は本ドキュメントを仕様の正本として
参照せず、以下のファイルを参照してください。本ドキュメントは歴史的記録として
原地に保持しています (archive 方針: 案 c、物理移動なし)。

- README.md    : 現行の使用方法・機能概要
- CHANGELOG.md : 変更履歴 (Keep a Changelog 1.1.0 準拠、Step 1-7 の commit hash 表を含む)
- 実装エントリポイント: main.py, mdpi_parser.py, journal_audit.py (repo root)
-->

# INTEGRATION BRIEF: MDPI Fast-Path と監査機能強化

**対象スキル**: `pubmed-reference-resolver`
**統合戦略**: B (Fast-path 統合)
**想定ブランチ名**: `feature/mdpi-fast-path`
**作成日**: 2026-04-20
**作成経緯**: 実データ (References.docx, 149 refs, MDPI形式) での実運用中に発見された
Phase 1 バグと、LLM API 呼び出しコスト削減の必要性から派生した統合要件。

---

## 1. 背景と動機

### 1.1 発見された既存バグ

`main.py` の `split_references()` は、LIS (最長単調増加部分列) による誤検出
抑制の副作用として、**先行 Reference が DOI で終わる場合に次の Reference の
ブロック境界を取り逃がす**ことがある。具体的には References.docx で以下が
発生した:

- Ref #39 の末尾 `...https://doi.org/10.1002/pon.4487.` に続く `40. van der Biessen...`
  → #40 が #39 に統合され、全体として #40 が消失
- Ref #139 の末尾 `...https://doi.org/10.1089/109662102753641287.` に続く
  `140. van Zyl...` → #140 が #139 に統合

原因は正規表現の lookbehind `(?<![\d.])` が DOI 末尾の数字/ピリオドを避ける
挙動と、LIS フィルタリングの組合せによるもの。本 brief の **Patch 01** で
修正する。

### 1.2 LLM 呼び出しコスト問題

既存の Stage 3 構造化は全ブロックを逐次 LLM (Claude Sonnet 4.6) に投入する
設計のため、以下の課題がある:

- 149 件の MDPI 形式 References を処理すると概算で **$0.15-0.30 相当の API
  コスト**が発生
- MDPI 形式は極めて定型的 (`Authors; Title. Journal Year, Vol, Pages, DOI.`)
  のため、**決定論的なパーサで十分 high confidence を達成できる**ことが
  本セッションの検証で確認された (149/149 件のうち high=129, medium=7,
  low=13, book=11、DOI ヒット率 86.6%)
- API を使わないことで、オフライン CI、決定論的な回帰テスト、即応性が得られる

### 1.3 検出されない査読重要事象

既存の Stage 5 (report.md 合成) は以下を検出するが、**「著者による引用
ジャーナル名の誤記」は検出していない**:

- 検出済: タイトル類似度低下、引用年乖離、重複引用
- 未検出: citation journal ≠ PubMed journal_iso のケース

実データ Ref #13 でこの事象が発生した。引用では "Ultrasound Med. Biol." と
記載されているが、DOI `10.1093/jjco/hyx079` が指す雑誌は "Jpn J Clin Oncol"
であり、類似度は 44%。**タイトル・著者・年・巻号は一致している**ため、
タイトル類似度ベースの検出では見逃される。

---

## 2. 統合計画 (コミット粒度)

以下の **7 コミット** に分割して段階的に統合することを推奨する。各コミット
は独立してテスト可能で、問題があれば該当コミットのみリバート可能。

| # | コミット | 変更範囲 | テスト |
|:--:|:---|:---|:---|
| 1 | Phase 1 split_references 境界バグ修正 | main.py:291-340 | tests/test_split_references_doi_boundary.py |
| 2 | MDPI parser モジュール新規追加 | mdpi_parser.py (新規) | tests/test_mdpi_parser.py |
| 3 | structure_all_references に fast-path 組込 | main.py:411-436 | tests/test_integration_149refs.py |
| 4 | manual_overrides.yaml サポート追加 | main.py CLI, _apply_overrides | tests/test_manual_overrides.py |
| 5 | journal_audit モジュール新規追加 | journal_audit.py (新規) | tests/test_journal_audit.py |
| 6 | Stage 5 report.md に journal audit 追記 | main.py Stage 5 周辺 | (手動確認) |
| 7 | ゴールドスタンダード 149 refs の CI 組込 | tests/test_integration_149refs/ | .github/workflows |

---

## 3. 各コミットの詳細

### 3.1 Commit 1: split_references boundary fix

**問題**: `(?<![\d.])` の副作用で DOI 末尾 (数字 or `.`) に続く次 reference を
取りこぼす。

**方針**: 既存の LIS ベース検出を残しつつ、**post-pass で改行直後の
`N+1. Surname` パターン**を補充候補として追加する。

適用ファイル: `patches/01_split_references_fix.patch`

```bash
cd /path/to/pubmed-reference-resolver
git apply --check patches/01_split_references_fix.patch  # 事前確認
git apply patches/01_split_references_fix.patch
git commit -m "fix(phase1): recover ref boundaries after DOI-terminated previous ref

Resolve #40/#140 disappearance bug: when a preceding reference ends with
a DOI (digits + period), the standard lookbehind '(?<![\\d.])' masks the
next reference's number, causing LIS filtering to drop it.

Added post-pass candidate recovery: for any '\\nN. Surname' pattern not
already in the candidate list, append it. This safely handles the edge
case without affecting existing behavior.

Verified against References.docx (149 refs, MDPI-style):
 - Before: 147 blocks (refs #40 and #140 lost)
 - After:  149 blocks (complete)
"
```

### 3.2 Commit 2: mdpi_parser.py module

**追加ファイル**: `mdpi_parser.py` (約 400 行、標準ライブラリのみ)

主要関数:
- `fix_hyphens(text)`: 大文字小文字保持ハイフン救済
- `detect_language(text)`: ISO 639-1 コード (en/fr/de/es)
- `strip_doi(doi) / build_doi_alt(doi)`: DOI 処理
- `parse_authors(text)`: 著者-タイトル境界検出
- `parse_title_journal_year_vol_pages(rest)`: タイトル/ジャーナル境界検出
- `is_mdpi_style(raw)`: fast-path 適用可否判定
- `structure_one_mdpi(ref_no, raw)`: 1 件の構造化
- `structure_all_mdpi(blocks)`: 全件の構造化

```bash
cp mdpi_parser.py /path/to/pubmed-reference-resolver/
git add mdpi_parser.py
git commit -m "feat(phase2): add deterministic MDPI parser module

Introduce mdpi_parser.py as a LLM-free alternative for MDPI-style
references. Uses only stdlib (no external deps beyond the existing
rapidfuzz). Parsing strategy:

 - Author boundary: last 'Surname, Initials.' before capitalized word
 - Title/Journal boundary: first '. ' position whose right-hand side
   passes looks_like_journal() validation (all tokens capitalized or in
   connective set, token count <= 8)
 - Year detection: '\\s(\\d{4})\\s*,' pattern
 - Book detection: ISBN OR (book signs AND no DOI)
 - Hyphen rescue: preserves original case via placeholder substitution

Validated on References.docx (149 MDPI-style refs):
 high=129, medium=7, low=13, is_book=11, DOI=129
"
```

### 3.3 Commit 3: structure_all_references fast-path integration

適用ファイル: `patches/02_mdpi_fast_path.patch`

```bash
git apply patches/02_mdpi_fast_path.patch
git commit -m "feat(phase2): route MDPI-style blocks to fast-path parser

structure_all_references() now classifies each block via
is_mdpi_style() and routes MDPI blocks to mdpi_parser, keeping LLM
path for non-MDPI styles (Vancouver/AMA/APA/etc.).

When all 149 blocks in References.docx hit the fast-path, the anthropic
SDK is never imported and API key is not required, allowing fully
offline operation for MDPI-only corpora.

Benchmark (References.docx, 149 refs):
 - Before (pure LLM): ~90s, ~$0.15 API cost
 - After (MDPI fast-path): ~2s, $0 API cost
 - Quality: identical core fields (title/journal/year/doi)
"
```

### 3.4 Commit 4: manual_overrides.yaml support

**追加ファイル**: `manual_overrides.yaml.example` (ユーザーテンプレート)

**変更ファイル**: `main.py` - CLI に `--overrides PATH` を追加、
`_apply_overrides()` で YAML の match/patch ペアを適用。

依存追加: `pyyaml` (optional; 未インストール時は警告して無視)

```bash
# main.py への追加は Patch 02 に含まれる
# あとは CLI 側のみ
# (詳細は Claude Code で実装)
```

### 3.5 Commit 5: journal_audit.py module

**追加ファイル**: `journal_audit.py`

主要関数:
- `audit_journal_mismatch(structured, resolutions) -> findings`
- `format_findings_markdown(findings) -> str`

```bash
cp journal_audit.py /path/to/pubmed-reference-resolver/
git add journal_audit.py
git commit -m "feat(phase5): add citation-journal vs PubMed journal audit

Detects 'author mis-reported journal name' which is invisible to
existing title-similarity checks (since title/author/year/vol may all
match correctly). Severity classification:

 - similarity < 50%: MAJOR (likely different paper or severe typo)
 - 50-69%: WARN (beyond normal abbreviation variance)
 - 70-79%: INFO (minor abbreviation differences)

Validated finding on References.docx Ref #13:
 cited as 'Ultrasound Med. Biol.' but DOI '10.1093/jjco/hyx079'
 points to 'Jpn J Clin Oncol' (similarity 44%, MAJOR)
"
```

### 3.6 Commit 6: report.md integration

main.py の `run_phase4()` の末尾で `journal_audit.audit_journal_mismatch()` を
呼び、`format_findings_markdown()` の結果を report.md に追記する。

### 3.7 Commit 7: CI integration

`tests/test_integration_149refs/` をリポジトリに追加し、pytest CI を設定する。
これにより、将来のパーサ改変で 149 件の出力が退行した場合を即座に検出できる。

---

## 4. 実装上の注意

### 4.1 import 順序

`main.py` で `from . import mdpi_parser` が Stage 3 ブロックの先頭に来るが、
既存の構造では `from dataclasses import ...` など冒頭にまとまっている。
Claude Code 側で適切な位置 (ファイル冒頭の import 群) に移動すること。

### 4.2 `_apply_overrides()` の `raw_contains` マッチャ

現状の patch では `raw_contains` マッチャは TODO (no-op) になっている。
`results` に `raw_text` を含めるか、`structure_all_references()` の内部で
apply するかは設計判断。後者が望ましい (raw を output に露出しないため)。

### 4.3 既存テストへの影響

既存の `examples/expected_output/` にゴールドデータがある場合、
新 MDPI fast-path を通すと出力が微細に変動する可能性あり。特に:

- `parsing_confidence` の判定基準が LLM と決定論で異なる
- `authors[].raw` の文字列表現が若干異なる可能性

Commit 3 の後で既存テストが失敗した場合、**ゴールドデータを更新**する
か、**fast-path を opt-in (デフォルト off)** に変更することを検討。

### 4.4 `claude-sonnet-4-6` モデル指定

本モジュールは `structure_reference()` を変更しないため、LLM モデル指定は
そのまま `claude-sonnet-4-6` を維持する。Phase 2 全体を SKILL.md の
モデル表記も合わせて `claude-opus-4-7` に更新したい場合は別コミットで。

---

## 5. ロールバック手順

各コミットは独立しているため、以下の粒度でリバート可能:

```bash
# Phase 1 修正のみリバート (fast-path は残す)
git revert <commit-1-hash>

# MDPI fast-path を無効化 (コードは残す)
# main.py の enable_mdpi_fast_path default を False に
git cherry-pick -n <commit-3-hash>  # 変更を stage
# 手動編集して default=False
git commit -m "chore: default-disable MDPI fast-path"
```

---

## 6. 成果物一覧

このパッケージに含まれるファイル:

```
integration/
├── INTEGRATION_BRIEF.md                          # 本ドキュメント
├── src/
│   ├── mdpi_parser.py                            # Commit 2 の本体
│   ├── journal_audit.py                          # Commit 5 の本体
│   └── manual_overrides.yaml                     # Commit 4 のテンプレート
├── patches/
│   ├── 01_split_references_fix.patch             # Commit 1
│   └── 02_mdpi_fast_path.patch                   # Commit 3
├── tests/
│   ├── test_mdpi_parser.py                       # MDPI パーサ単体テスト
│   └── test_integration_149refs/
│       ├── input_References.docx                 # 149 refs 入力
│       ├── expected_phase2_structured.json       # ゴールド Phase 2
│       ├── expected_phase3_resolved.json         # ゴールド Phase 3
│       ├── expected_report.md                    # ゴールド report
│       └── expected_journal_audit.json           # ゴールド audit
└── docs/
    └── CLAUDE_CODE_PROMPT.md                     # Claude Code への投げ方
```

---

## 7. 検証チェックリスト

統合完了後、以下を確認:

- [ ] Commit 1 適用後、149 ブロックが Phase 1 で取れること
- [ ] Commit 2-3 適用後、MDPI References.docx が API キー無しで通ること
- [ ] Commit 5-6 適用後、report.md に journal audit セクションが出ること
- [ ] 既存の Vancouver/AMA 形式の References で後退が無いこと
- [ ] `pytest tests/test_mdpi_parser.py` が全緑になること
- [ ] `tests/test_integration_149refs/expected_*` と実行結果が一致すること

---

**以上**。本 brief と同梱ファイル一式を Claude Code 側で参照しながら、
`docs/CLAUDE_CODE_PROMPT.md` のプロンプトテンプレートに従って段階的に
統合を進めることを推奨する。
