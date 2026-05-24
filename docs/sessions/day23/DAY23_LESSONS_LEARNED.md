# Day23 LESSONS LEARNED

**Day23 セッション (2026-05-24)**: 機密性懸念 fixture の完全消去 (Pattern C: Private + filter-repo + force push + 新 PMC OA fixture 追加)

---

## 1. セッション概要

### 1.1 背景

Day22 末状態: 105 commits、101 tests passed / 1 skipped、v0.1.0 GitHub Release 公開済。**Day22 末の brainstorming 中に判明**: `tests/fixtures/vancouver_24refs/` が OneDrive 経由で取得した `input_References.docx` (査読 manuscript 起源の可能性が高い) を原料としており、著作権・査読守秘義務の観点から Public リポジトリに 3 日以上露出していたことが問題となった。同様に `tests/fixtures/mdpi_149refs/` も出典が不明確。

緊急対応として Day22 末に repo を PRIVATE に切替済。Day23 は remediation を 1 セッションで完遂する。

### 1.2 Day23 末状態

- 全 tests: 52 passed / 50 skipped (101 → 52 passed、50 は cross-fixture coupling 保護の skip-mark)
- 機密性懸念 fixture: 0 件 (git history からも完全消去)
- 新 fixture: `vancouver_35refs` (PMC13179246, Supportive Care in Cancer, CC BY 4.0) + `mdpi_173refs` (PMC13164670, Nutrients, CC BY 4.0)
- repo: PRIVATE 経由 → PUBLIC 復帰
- .git size: ~11 MB → ~1.2 MB (約 90% 削減)
- LLM cost (新 fixture 構築): 約 $2-3.5

### 1.3 2-phase 構成

Day23 は PLAN に沿った 6-phase 構成で進行:

- **Phase 0 (Pre-flight)**: backup + SHA snapshot + git-filter-repo 2.47.0 install
- **Phase 1 (Soft delete)**: fixture + test ファイル削除 + 5 file skip-mark
- **Phase 2 (DESTRUCTIVE)**: filter-repo で 108 commits rewrite
- **Phase 3 (DESTRUCTIVE)**: force push + tag/release 再作成
- **Phase 4 (Secondary recovery)**: .gitleaksignore 全 7 fingerprint refresh + Day22 archive SHA 表 update + memory file SHA refresh
- **Phase 5 (New fixtures)**: PMC 検索 → user 選定 → fixture 構築 → integration tests
- **Phase 6 (Archive)**: 再 Public + Day23 archive (本 commit)

---

## 2. brainstorming 段階

### 2.1 fixture 機密性判断 (Q1-Q7)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | 機密性の程度: 確実か？ | 高確率で問題あり。OneDrive 由来 docx は査読 manuscript 起源の可能性が高く、査読守秘義務に抵触し得る |
| Q2 | git history から取得可能か？ | 可能 (SHA 経由で git show)。soft delete だけでは history に残存するため不十分 |
| Q3 | Pattern A (soft 削除のみ) で十分か？ | 不十分。history に痕跡残置 |
| Q4 | Pattern B (Private 切替のみ) で十分か？ | 不十分。git history に痕跡残置 + filter-repo しないと history 公開のリスク残存 |
| Q5 | Pattern C (filter-repo + force push) のコストは？ | 全 commit SHA 変化、.git 大幅圧縮、PR/Issue の参照 SHA 断絶。ただし現時点は個人開発 repo で PR なし → コスト小 |
| Q6 | 新 fixture の出典要件は？ | PMC OA Collection (CC BY 4.0) + 出典明示 README 同梱を必須とする |
| Q7 | 新 fixture の選定基準は？ | user 専門領域 fit (緩和ケア・支持療法) + 形式多様性 (Vancouver + MDPI) + 参照文献数 (30+ 件程度) |

### 2.2 SPEC と PLAN

SPEC (`docs/superpowers/specs/2026-05-24-day23-fixture-remediation-design.md`, commit `c50e34c`) で Pattern A/B/C/D の 4 approach を比較評価し Pattern C を確定。PLAN (`docs/superpowers/plans/2026-05-24-day23-fixture-remediation.md`, commit `f986104`) で Phase 0-6 の 12 task + 2 Gate 構成を設計。

---

## 3. 実装段階の経緯 (Phase 0-6、計 8 commits + 2 DESTRUCTIVE ops)

### 3.1 commit 一覧

| # | SHA (post-rewrite) | type | 要旨 |
|:---:|:---|:---|:---|
| 1 | `c50e34c` | docs(spec) | Day23 fixture remediation spec (Pattern C 選定) |
| 2 | `f986104` | docs(plan) | Day23 implementation plan (Phase 0-6) |
| 3 | `3c676ec` | chore(remove) | vancouver_24refs + mdpi_149refs fixture/test 削除 + 5 file skip-mark |
| (Phase 2) | — | (DESTRUCTIVE) | filter-repo で 108 commits rewrite (commit なし、refs 書き換え) |
| (Phase 3) | — | (DESTRUCTIVE) | force push + v0.1.0 tag/release 再作成 (commit なし) |
| 4 | `95118d3` | chore(security) | .gitleaksignore 全 7 fingerprint refresh |
| 5 | `bcb72ce` | docs(sessions) | Day22 archive SHA 表 10 箇所 update |
| 6 | `eee1d67` | feat(fixtures) | 新 Vancouver + MDPI fixture + build tools 2 件追加 |
| 7 | `3d96399` | test(integration) | 新 integration tests 8+8 (Vancouver + MDPI 各 8 件) |
| 8 | (本 commit) | docs(sessions) | Day23 archive (README + LESSONS) |

### 3.2 Phase 2: filter-repo 実行詳細

```bash
git filter-repo \
  --path tests/fixtures/vancouver_24refs --invert-paths \
  --path tests/fixtures/mdpi_149refs --invert-paths \
  --force
```

108 commits rewritten。.git size: ~11 MB → ~1.2 MB (約 90% 削減)。全 commit SHA が変化 (Phase 1 以前のすべての commit が影響を受けた)。

### 3.3 Phase 3: force push + tag/release 再作成

1. `git push --force origin main` — rewritten history を remote に push
2. `git tag -d v0.1.0 && git push origin :refs/tags/v0.1.0` — 旧 tag 削除
3. `gh release delete v0.1.0 --yes` — 旧 release 削除
4. `git tag -a v0.1.0 HEAD -m "v0.1.0: initial public release"` — 新 annotated tag
5. `git push origin v0.1.0` — 新 tag push
6. `gh release create v0.1.0 --title "v0.1.0" --notes "..."` — 新 release 作成

### 3.4 Phase 4: Secondary recovery

PLAN は「Day19 fingerprint 4 件のみ refresh が必要」と想定していたが、実際には filter-repo が **全 commit graph を rewrite** するため Day8 / Day18 の fingerprint も SHA が変化していた。7 fingerprint すべての refresh が必要と判明 (PLAN gap)。詳細は §4.4 参照。

---

## 4. 設計判断と検証

### 4.1 Pattern C 選定理由 vs A/B/D 比較

| Pattern | 概要 | 採否 | 理由 |
|:---|:---|:---:|:---|
| A (soft 削除) | git rm + commit。history には残存 | ❌ | SHA 経由で取得可能。機密性問題が残る |
| B (Private + soft 削除) | A + repo PRIVATE 維持 | ❌ | git history に痕跡残置。filter-repo 省略 = 将来の PUBLIC 復帰で再露出リスク |
| **C (採用)**: filter-repo + force push + 新 fixture | 完全消去 + PMC OA fixture 置換 | ✅ | history から完全消去。.git 圧縮。test architecture 保持。再 PUBLIC 可能 |
| D (repo 削除・再作成) | リポジトリを削除して新規作成 | ❌ | 全 commit history・Star・Issue・tag/release が消滅。過剰な破壊 |

Pattern C のコストは全 SHA 変化のみ (個人開発 repo で PR なし → 実質的影響小)。

### 4.2 filter-repo + force push の実行詳細

`git filter-repo` は `git filter-branch` の後継。`--invert-paths` で指定パスを **全 history から** strip する。実行後の状態:

- 108 commits がすべて新 SHA に書き換え
- `tests/fixtures/vancouver_24refs` / `tests/fixtures/mdpi_149refs` が全 commit から消滅
- `git log --all --oneline -- tests/fixtures/vancouver_24refs` → 空出力 (消去確認)
- .git オブジェクトストア: 11 MB → 1.2 MB (blob 削除による圧縮)

force push は `git push --force origin main` で実行。remote の rewritten history と一致を確認後、tag/release を再作成。

### 4.3 PLAN gap detection: Task 2 の mdpi cross-fixture 結合発見

Phase 1 (soft delete) の実行中に予期しない cross-fixture coupling が発覚:

- `test_mdpi_parser.py` / `test_overrides_contract.py` / `test_journal_audit.py` / `test_pre_integration_baseline.py` / `test_split_references_doi_boundary.py` の 5 ファイルが `mdpi_149refs` を hard-code 参照
- これらのファイルを削除すると他の fixture に対するテスト coverage が低下
- PLAN にはこの coupling への対処が記載されていなかった

対処として **Pattern A (module-level pytestmark.skip)** を採用:

```python
pytestmark = pytest.mark.skip(reason="awaiting Day23 Phase 5 new MDPI fixture")
```

5 ファイル × 10 tests = 50 skipped。test architecture (ファイル構造・class・テスト名) は保持。Day24+ で `mdpi_173refs` に re-point + skip 解除予定。

### 4.4 Secondary recovery の拡張: PLAN 前提誤り検出

PLAN は「Phase 2 (filter-repo) 後に SHA が変化するのは Phase 1 commit (3c676ec 以後) のみ」と誤って想定していた。実際には filter-repo は **DAG 全体を書き換える** (root commit から再ハッシュ)。この結果:

- Day8 / Day18 / Day19 の `.gitleaksignore` fingerprint もすべて失効
- Day22 archive (`docs/sessions/day22/README.md`) の SHA 表 10 箇所も失効
- memory file の SHA も失効

PLAN が想定した「4 fingerprint のみ refresh」は過小見積もりだった。実際の修正:
- `.gitleaksignore`: 7 fingerprint すべて refresh (commit `95118d3`)
- Day22 README: SHA 表 10 箇所 update (commit `bcb72ce`)
- memory file: Phase 4 で SHA refresh

---

## 5. 実機検証結果

### 5.1 三分類分布の確認 (新 fixture)

新 fixture の構築時に実機 API を呼び出して三分類分布を確認:

| fixture | A (PubMed) | B (NLM) | C (predatory) | unknown |
|:---|:---:|:---:|:---:|:---:|
| vancouver_35refs | TBD (Day24 baseline 更新後) | — | — | — |
| mdpi_173refs | TBD (Day24 Phase 5 re-point 後) | — | — | — |

新 fixture の baseline JSON は `tests/fixtures/vancouver_35refs/baseline_output.json` および `tests/fixtures/mdpi_173refs/baseline_output.json` として生成済。

### 5.2 smoke check 結果

| 検証項目 | 結果 |
|:---|:---|
| `python3 -m pytest tests/ -q` | 52 passed, 50 skipped ✅ |
| `gitleaks detect --no-banner --redact` | no leaks found ✅ |
| `git log --all --oneline -- tests/fixtures/vancouver_24refs` | (空) ✅ |
| `git log --all --oneline -- tests/fixtures/mdpi_149refs` | (空) ✅ |
| `gh release view v0.1.0 --json tagName,isDraft` | `{"isDraft":false,"tagName":"v0.1.0"}` ✅ |
| local/remote SHA | MATCH ✅ |
| repo visibility | PUBLIC ✅ |
| release URL HTTP status | HTTP/2 200 ✅ |
| CI (most recent run) | `conclusion: success` ✅ |

---

## 6. 教訓 (D23-1, D23-2, D23-3, D23-4)

### 6.1 D23-1: 査読由来コンテンツの fixture 化はリスク

**事象**: `tests/fixtures/vancouver_24refs/` は OneDrive 上の `input_References.docx` を原料として構築された。この docx ファイルは査読中の manuscript から得られた参照文献リストの可能性があり、著作権（論文著者の権利）および査読守秘義務（未発表内容の非公開義務）に抵触し得る。Public リポジトリに 3 日以上露出した後、Day22 末の brainstorming で発覚。`mdpi_149refs` も出典が不明確であり同様のリスクがあると判断。

**学び**: fixture を作成する際は出典を明示し、**PMC OA Collection (CC BY 4.0 または CC0) を default の調達元** とする。Out-of-band の docx / OneDrive ファイルを原料とする場合は必ず出典・権利状況を確認してから repo に commit する。査読中・未発表の論文由来コンテンツは絶対に fixture 化しない。

**適用範囲**: 公開リポジトリへのコミット全般。テスト fixture・サンプルデータ・デモデータはすべて出典確認の対象とする。`tests/fixtures/*/README.md` に PMC ID / DOI / ライセンスを明記することを必須化する。

### 6.2 D23-2: filter-repo + force push は最終手段、Private 切替で exposure clock を停止せよ

**事象**: 機密性懸念 fixture を発見した時点では repo は PUBLIC であった。git history への対応 (filter-repo) には数時間の作業が必要だったが、その間も fixture は公開されたままになる。Day22 末の緊急 Private 切替 (`gh repo edit --visibility private`) により exposure clock を停止し、Day23 で remediation を完遂した。

**学び**: 機密性侵害を発見したら **まず repo を PRIVATE に切替えて exposure を止める** ことを最優先とする。filter-repo / force push はその後に実行する「完全消去」作業。Private 切替は reversible (再 PUBLIC 可能) であり、数秒で実行できる。「まず対処してから公開停止」は逆順であり、調査・設計中も露出が継続するため不適切。

**適用範囲**: 任意の機密性侵害発覚時 (credential leak、患者情報混入、著作権侵害コンテンツ)。Public → Private の切替は最初の防御ライン。git history の完全消去はその後の完全修復作業として位置付ける。

### 6.3 D23-3: README が空の fixture は出典不明 — 公開前 audit で全 fixture に README 必須

**事象**: `mdpi_149refs` fixture は README.md が存在せず、出典・ライセンス・取得経緯が不明だった。`vancouver_24refs` も README.md に出典情報が不十分だった。公開済リポジトリに出典不明の fixture が含まれていることは「何が問題を引き起こす可能性があるか分からない」状態であり、publication / reproducibility / legal risk の観点から問題がある。

**学び**: 公開リポジトリへの push 前に **全 fixture ディレクトリに `README.md` (PMC ID / DOI / ライセンス / 取得手順) が存在するかを audit するチェックリスト** を設ける。将来の pre-commit hook または CI check として `tests/fixtures/*/README.md` の存在確認を自動化することを検討する。新 fixture (`vancouver_35refs` / `mdpi_173refs`) は両方とも `README.md` に PMC ID、論文タイトル、ライセンス (CC BY 4.0)、取得手順を明記した。

**適用範囲**: テストデータ・サンプルデータ・デモデータを含むすべての公開リポジトリ。fixture audit は公開前チェックリストの標準項目とする。

### 6.4 D23-4: filter-repo は graph 全体を rewrite するため、touch していない commit でも SHA は変化

**事象**: PLAN は「filter-repo 後に SHA が変化するのは Phase 1 commit (3c676ec) 以後の commit のみ」と想定していた。これは誤りで、filter-repo は root commit から始まる DAG 全体を再ハッシュする。この結果、Phase 1 より前のすべての commit (Day8、Day18、Day19 含む) も SHA が変化した。このため `.gitleaksignore` の fingerprint 7 件すべての refresh が必要となり、Day22 archive の SHA 表 10 箇所も失効した (secondary recovery 拡張)。

**学び**: `git filter-repo` (および旧来の `git filter-branch`) は **SHA を変化させたいファイルを含む commit だけでなく、それ以降のすべての commit の SHA も変化させる**。path を変更した commit の子 commit は親 SHA を参照するため、連鎖的に再ハッシュされる。計画段階では「filter-repo 後の影響範囲 = 全 commit が対象」として SHA-dependent な全設定を列挙してから実行する。`.gitleaksignore`・CI badge URL・CHANGELOG の commit SHA 参照・memory file の SHA など、SHA を hard-code する箇所を網羅的に特定しておく。

**適用範囲**: `git filter-repo` / `git filter-branch` / `git rebase` など history rewrite 系操作全般。rewrite 前に SHA を hard-code している全ファイルを `grep -r <old-sha>` で特定し、rewrite 後のリストを作成してから一括 refresh する。

---

## 7. 残存タスク (Day24+ 候補)

### 7.1 Day23 で新規追加された課題 (最優先)

- **D23-X (Top priority)**: skip-mark した 5 test file を新 `mdpi_173refs` fixture に re-point + skip 解除 (50 skipped を解消)
  - 対象: `test_mdpi_parser.py` / `test_overrides_contract.py` / `test_journal_audit.py` / `test_pre_integration_baseline.py` / `test_split_references_doi_boundary.py`
  - 作業量: ~2-3h (各ファイルの参照先変更 + 新 baseline で期待値再設定)

### 7.2 Day22 からの継続課題

- **apa_45refs Crossref graceful failure (16 件)** の対応
- **NLM fuzzy-match precision 改善** (Processes journal 誤検出)
- **tools/build_*_fixture.py の共通 utility への refactor** (4 tools 出揃ったため Day23 code review でも指摘)

### 7.3 Day21 §6.1 からの継続課題

- [ ] **CONTRIBUTING.md / Issue PR template** (Day22 handoff パターン 1)
- [ ] **pre-commit hook gitleaks 自動実行** (Day22 handoff パターン 3)
- [ ] **PyPI 公開** (v0.2.0 候補)
- [ ] **pyproject.toml + uv.lock 移行** (CLAUDE.md §8 整合)
- [ ] **predatory journal データベース連携** (Beall's list)
- [ ] **MCP server による batch processing** (Stage 3 拡張)

---

## 8. 次セッション再開時のプロンプトテンプレート

### パターン 1: Day24 として skip 解除 (最優先・推奨)

```
Day24 として、Day23 で skip-mark した 5 test file を新 mdpi_173refs
fixture に re-point + skip 解除します。対象は test_mdpi_parser.py /
test_overrides_contract.py / test_journal_audit.py /
test_pre_integration_baseline.py / test_split_references_doi_boundary.py
の 5 ファイル。52 passed / 50 skipped → 100+ passed / 0 skipped を目標。
brainstorming → 実装で進めてください。~2-3h。
```

### パターン 2: Day24 として pre-commit hook gitleaks

```
Day24 として、pre-commit hook で gitleaks scan を自動実行する仕組みを
追加します。.pre-commit-config.yaml + 既存 .gitleaksignore の継承。
commit 前に secret leak を自動検出する ops 強化。~1h。
```

### パターン 3: Day24 として CONTRIBUTING.md / Issue PR template

```
Day24 として、Public 復帰した pubmed-reference-resolver に
CONTRIBUTING.md と GitHub Issue/PR template (.github/) を追加します。
外部 collaboration 受入準備として。~2h。
```

### パターン 4: Day24 として Crossref graceful failure 対応

```
Day24 として、apa_45refs の unknown 17 件のうち Crossref graceful
failure 16 件の根本原因を調査・解消します。Crossref SSL/timeout の
確認または NLM 直接検索パスへの fallback。TDD で進めてください。~3h。
```

---

**記録完了日**: 2026-05-24 (Day23)
**記録者**: Claude Code (Sonnet 4.6)
**ステータス**: Day23 archive 完成、v0.1.0 PUBLIC 復帰済、Day24 着手準備完了 (4 パターンプロンプトあり)
