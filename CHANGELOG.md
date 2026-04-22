# Changelog

このプロジェクトの特筆すべき変更はこのファイルに記録されます。

形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠しており、
このプロジェクトは [セマンティックバージョニング](https://semver.org/lang/ja/) の採用を予定しています
(v0.1.0 タグ付けは別タスクで実施予定)。

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
