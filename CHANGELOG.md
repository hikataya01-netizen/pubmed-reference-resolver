# Changelog

このプロジェクトの特筆すべき変更はこのファイルに記録されます。

形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠し、
[セマンティックバージョニング](https://semver.org/lang/ja/) を採用する
(v0.1.0 は Day21 = 2026-05-22 でタグ付与済)。

## [Unreleased]

(Day21 以降の変更がここに記録される予定)

## [0.1.0] - 2026-05-22

### Day8-18 統合: Vancouver Veto + 4 fixture + 3 分類 audit + GitHub 公開準備

Day8-18 で実装された主要機能を 6 カテゴリで集約.

### Added (新規追加)

- **Vancouver Veto** (`mdpi_parser.py` regex 強化, Day9 + Day16): `(YYYY)` および `(YYYYa)` を検出して MDPI fast-path から LLM path に強制 routing. APA 7 disambiguation suffix にも対応.
- **golden fixture 3 系統**: vancouver_24refs (Day11, OneDrive 24 件)、apa_45refs (Day16, PMC OA 3 論文計 45 件)、cell_45refs (Day17, iScience 3 論文計 45 件). Day11 で確立された `expected_*` / `baseline_*` ハイブリッド命名規約準拠.
- **3 分類 audit logic** (Day15, 新 3 module): `crossref_check.py` (Crossref DOI 実在確認)、`nlm_catalog_check.py` (NLM Catalog journal indexing 確認)、`three_class_classifier.py` (A=真の捏造 / B=MEDLINE 非収録 / C=収録誌 indexing 漏れ / unknown=fail-soft 分類). `main.py` Phase 4 で sidecar JSON 出力.
- **build script 群** (Day16-17): `tools/build_apa_fixture.py` / `tools/build_cell_fixture.py` (PMC OA JATS XML → APA/Cell plain text → docx 自動組成).
- **session archive 群** (Day8-18): `docs/sessions/day{8,...,18}/` に SPEC / PLAN / LESSONS / 補助 docs を継続蓄積. 全 11 セッション分.
- **API key setup docs** (Day12): `docs/operations/SETUP_API_KEYS.md`.
- **USAGE_QUICKSTART** 1.0 → 1.5 (Day10/14/15/17 各 bump): `skill_package/references/USAGE_QUICKSTART.md` に 3 分類 audit / 4 fixture 情報を追記.
- **GitHub Private push** (Day18): `hikataya01-netizen/pubmed-reference-resolver`、CI 動作確認、gitleaks-based secret scan protocol 確立.

### Changed (変更)

- **env loader** (`main.py:load_env_files`, Day8): 空値環境変数を上書き対応 (harness サブプロセス継承時の空値問題に対処).
- **SKILL.md / USAGE_QUICKSTART** (Day14-17): 「捏造引用 = PubMed 未ヒット」の単純化記述を 3 分類体系に書換.
- **`.gitignore`** (Day16/18): `.cache/`, `.DS_Store` 追加.

### Fixed (修正)

- **MDPI parser `<collab>` 対応** (Day16, `tools/build_apa_fixture.py`): 組織著者 `<collab>` 要素から author を抽出可能に. PMC OA refs 28/37 の空抽出問題を解決.

### Documentation

- README.md を Day17 末状態に更新 (Day18 Phase 2): 97 tests / 4 fixture / Day8-17 構成反映.

### Day20 追加 (2026-05-22)

**Day7 §9.3 long-term task 完全クローズ (7/7)** — Day20 で残最後 1 件 (Stage 3) を達成認証.

### Added (Day20)

- **3 helper 関数 in `three_class_classifier.py`** (Day20): `_detect_book()` / `_detect_conference()` / `_classify_via_nlm_only()`. DOI 欠落 case を 4 rule 順次評価に拡張.
- **`STAGE3_COMPLETION_NOTE.md`** (Day20): Day7 §9.3 残最後の 1 件 (MCP/hook 経由 Stage 3 配線) を SKILL.md 経由達成として認証.
- **3 unit tests** (Day20、`tests/test_three_class_classifier.py`): book / conference / NLM-only 各 rule の動作検証.

### Changed (Day20)

- **`three_class_classifier._classify_single`** (Day20): DOI 欠落 case を「即 A」から 4 rule 順次評価 (book → conference → NLM 検索 → A fallback) に変更. cell_45refs A 分類 14 → 1 (93% 減)、apa_45refs A 分類 4 → 0 (完全消失).
- **`main.py:synthesize_outputs`** (Day20): `unresolved_refs` に `is_book` / `raw_text` / `publisher` 3 fields を追加 (Phase 2 LLM 出力由来、Day20 改修の Rule 1 で利用).
- **`tests/fixtures/{cell,apa}_45refs/baseline_*`** (Day20): 三分類 baseline 再生成、`baseline_report.md` も自動更新.
- **`tests/fixtures/mdpi_149refs/expected_report.md`** (Day20): deterministic golden の三分類 sub-section も Day20 改修反映で再生成 (#4 A→unknown、#9/#19 A→B).

### Test 健全性推移

| Day | passed | 主な追加 |
|:---:|---:|:---|
| Day7 末 | 52 | (baseline) |
| Day8 末 | 56 | env loader test |
| Day11 末 | 60 | vancouver_24refs test |
| Day15 末 | 71 | 3 module test |
| Day16 末 | 81 | apa_45refs test |
| Day17 末 | 89 | cell_45refs test |
| Day19 末 (見込) | 89 | (公開化のみ、test 改変なし) |

詳細な経緯は `docs/sessions/day{8,...,18}/DAY*_LESSONS_LEARNED.md` を参照.

## [Unreleased] - 2026-04-23

### プロジェクト完結の節目

4 日間にわたる MDPI fast-path 統合計画 (Steps 1-7) が完了しました。
本リリースは初回安定版 (v0.1.0 相当) の基盤となります。

### Added (新規追加)

- **MDPI 形式パーサ** (`mdpi_parser.py`): LLM 呼び出しなしで決定論的に MDPI 形式の参照を構造化 (Step 2)
- **journal_audit モジュール** (`journal_audit.py`): ジャーナル名の類似度監査、MAJOR/WARN/INFO の 3 段階 severity 分類 (Step 5)
- **Stage 5 統合監査レポート**: Dashboard / 1.1 MAJOR セクション / 補遺 narrative / sidecar JSON の 4 層構成 (Step 6)
- **manual_overrides.yaml サポート**: 自動パーサで解決困難な特殊ケースを手動補正 (Step 4)
- **149 件 MDPI ゴールドスタンダード**: `tests/fixtures/mdpi_149refs/` に配備、byte 単位の完全一致検証 (Step 3)
- **GitHub Actions CI**: Python 3.11/3.12 必須 + 3.14 実験的併走 (Step 7)
- **requirements.txt**: 再現可能な環境構築のための依存マニフェスト (Step 7)
- **README.md**: プロジェクト概要、使用方法、149 件ゴールドスタンダードの説明 (Step 7)

### Changed (変更)

- **Phase 1 split_references**: DOI 境界判定のバグ修正、Dutch/French の小文字を lookahead で許容 (Step 1)
- **structure_all_references**: MDPI fast-path の統合により、MDPI 形式参照は LLM 呼び出しを bypass (Step 3)

### Fixed (バグ修正)

- Phase 1 で DOI 直後の lowercase 始まりの著者名を誤って split していた問題 (Step 1)

### Infrastructure (基盤整備)

- テスト件数: 11 → 52 (4.7 倍に拡充)
- 単体テスト: test_mdpi_parser.py (4 件), test_journal_audit.py (22 件), test_overrides_contract.py (7 件), test_split_references_doi_boundary.py (2 件)
- 統合テスト: test_integration_149refs.py (6 件 + 1 skipped)
- baseline テスト: test_pre_integration_baseline.py (11 件)

### 開発プロセス記録

- Day1 (2026/04/20): baseline 確立 + Step 1
- Day2 (2026/04/21): Steps 2-5
- Day3 (2026/04/22): Step 6
- Day4 (2026/04/23): Step 7 + merge + 本 CHANGELOG
- 詳細: `pubmed-reference-resolver-integration-chat-day{1,2,3,4}.md`

### Notes (備考)

- 本プロジェクトは現時点でライセンス未定 (TBD)。ライセンス方針決定後に v0.1.0 タグを付与予定
- GitHub remote は未設定、現状ローカルリポジトリのみ
- ANTHROPIC_API_KEY は全テストにおいて不要 (MDPI fast-path が決定論的に動作)

---

## コミット hash 参照表

Step 1-7 の各コミット hash は以下の通り:

| Step | commit hash | 概要 |
|:---:|:---|:---|
| baseline (Day1) | `ea3d604` | snapshot before MDPI fast-path integration |
| baseline (Day1) | `a0bba56` | characterize pre-integration behavior on 149-ref |
| Step 1 | `b8c187c` | fix(phase1): extend lookahead to accept Dutch/French lowercase |
| Step 2 | `531bfe0` | feat(mdpi): add deterministic parser for MDPI-style references |
| Step 2 | `c4b67c5` | docs(mdpi): document parser limitations for Step 4 overrides |
| Step 2 | `941e914` | test(mdpi): capture Ref #141 parser output as pre-override snapshot |
| Step 3 | `10a2a76` | feat(structure): wire MDPI fast-path into structure_all_references |
| Step 4 | `04b15eb` | feat(overrides): load and apply manual corrections from yaml |
| Step 5 | `1dbf9d7` | feat(audit): add journal-name similarity audit module |
| Step 6 | `7b813c2` | feat(report): integrate journal_audit into Stage 5 report synthesis |
| Step 7a | `68509d7` | chore(deps): add requirements.txt for reproducible environment |
| Step 7b | `f6ec966` | chore(ci): add GitHub Actions workflow for 149-ref golden standard |
| Step 7c | `0c41432` | docs(readme): add project README with usage, CI status, and golden standard description |
