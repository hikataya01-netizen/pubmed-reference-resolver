# Day22 LESSONS LEARNED

**Day22 セッション (2026-05-24)**: Rule 3 NLM SSL fix + Phase A security (Day21 末セキュリティ監査対応)

---

## 1. セッション概要

### 1.1 背景

Day21 末状態: 96 commits、100 tests passed / 1 skipped、v0.1.0 GitHub Release 公開済 (annotated tag `c68cad0`)。Day21 §6.1 残存タスク筆頭の「Rule 3 NLM 検索の SSL 問題解消」を Day22 本筋として選択。加えて Day21 セキュリティ監査レポート (`docs/SECRET_SCAN_REPORT.md`) で検出された 🔴 高優先 2 件 (gitleaks false positive suppression + GitHub Secret Scanning 有効化) を Phase A として先行処理。

Day22 末状態: 105 commits (+9)、101 tests passed / 1 skipped (+1 unit test)、v0.1.0 維持。cell_45refs の unknown が 8→2 に減少 (6 件が B に正しく再分類)、apa_45refs の unknown は 17→17 (数値同一だが SSL error → legitimate failure reason に変化)。Phase A + Phase B 2-phase 構成で完結。

### 1.2 2-phase 構成

- **Phase A (security)**: `.gitleaksignore` 拡張 (A1) + GitHub Secret Scanning + Push Protection 有効化 (A2 = gh api PATCH)
- **Phase B (main)**: SPEC → PLAN → TDD RED → TDD GREEN → baseline 再生成 + 2 fix-up commit

---

## 2. brainstorming 段階

### 2.1 Phase B brainstorming (Q1-Q3 + Approach 確定)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | SSL エラーの root cause は何か | Mac Python.org installer の空 cert.pem。certifi で deterministic 化が根本解。OS を横断した fix のため runtime dep として追加 |
| Q2 | 実装 approach の比較 (A1/A2/A3) | A1 (module-level `_SSL_CONTEXT` singleton + `_fetch_json` 注入) を採用。A2 (build_opener) は test mocking が複雑化、A3 (requests/httpx 移行) は diff・dep 過大 |
| Q3 | apa_45refs の unknown は SSL fix で解消するか | 部分解消に留まる。16 件は Crossref graceful failure (DOI timeout、非 MEDLINE)、1 件は legitimate な NLM Catalog 不在。Day23+ 残置 |

### 2.2 SPEC と PLAN

SPEC (`docs/superpowers/specs/2026-05-24-rule3-nlm-ssl-fix-design.md`, commit `aaa1eb9`) で A1/A2/A3 の 3 approach を比較評価し A1 を確定。PLAN (`docs/superpowers/plans/2026-05-24-rule3-nlm-ssl-fix.md`, commit `272a34f`) で Task 0-4 の 5 commit 構成を設計 (実績: fix-up 2 件追加により 7 commit)。

---

## 3. 実装段階の経緯 (Phase A + Phase B、計 9 commits)

### 3.1 commit 一覧

| # | SHA | type | 要旨 |
|:---:|:---|:---|:---|
| 1 | `dbbac4a` | chore(security) | Phase A1: `.gitleaksignore` に Day19 SECRET_SCAN_REPORT 4 fingerprint 追加。gitleaks false positive suppression |
| 2 | `aaa1eb9` | docs(spec) | Phase B: brainstorming spec (approach 比較、A1 確定) |
| 3 | `272a34f` | docs(plan) | Phase B: implementation plan (Task 0-4) |
| 4 | `851cf2a` | test(nlm) | TDD RED: `test_fetch_json_uses_certifi_ssl_context` 追加 (失敗確認) |
| 5 | `81b1b9e` | fix(nlm) | TDD GREEN: `_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())` を module-level に追加、`_fetch_json` に注入 |
| 6 | `0f0e028` | docs(nlm) | fixup: module docstring に certifi dep 注記追加 (Task 2 code review 指摘) |
| 7 | `4ba48ba` | test(fixtures) | cell_45refs + apa_45refs baseline JSON 再生成 (実機 NLM API 呼び出し) |
| 8 | `9c299c0` | docs(tests) | fixup: integration test docstring を Day22 fulfillment 反映に更新 (Task 3 code review 指摘) |
| 9 | (本 commit) | docs(sessions) | Day22 archive (README + LESSONS) |

### 3.2 Phase A 詳細

Phase A1 (commit `dbbac4a`): Day21 末セキュリティ監査で gitleaks が Day19 `SECRET_SCAN_REPORT.md` 内の報告文字列を false positive 検出。4 fingerprint を `.gitleaksignore` に追加して suppress。`gitleaks detect --no-banner --redact` で `no leaks found` を確認。Phase A2: `gh api PATCH /repos/hikataya01-netizen/pubmed-reference-resolver` で Secret Scanning + Push Protection を有効化 (外部操作、commit なし)。

### 3.3 Phase B 詳細

Task 0 (SPEC/PLAN): commit `aaa1eb9` + `272a34f`。Task 1 (TDD RED): commit `851cf2a` で `_fetch_json` の SSL context が certifi を使用することを assert する unit test を追加 → 実行時 FAIL 確認。Task 2 (TDD GREEN): commit `81b1b9e` で `nlm_catalog_check.py` に `import certifi` + module-level `_SSL_CONTEXT` singleton + `_fetch_json` 注入実装 → 全 101 tests pass。Task 3 (baseline 再生成): commit `4ba48ba` で `main.py` を実行し実機 NLM API 呼び出し → JSON 更新 → integration tests pass。fix-up commits (`0f0e028`, `9c299c0`) は subagent code review 指摘を atomic に分離。

---

## 4. 設計判断と検証

### 4.1 module-level singleton vs 代替 approach 比較

| Approach | 概要 | 採否 | 理由 |
|:---|:---|:---:|:---|
| **A1 (採用)**: module-level `_SSL_CONTEXT` singleton | `ssl.create_default_context(cafile=certifi.where())` を module 読み込み時に 1 回生成、`_fetch_json` に注入 | ✅ | diff 最小、test mock が `unittest.mock.patch` で単純、certifi dep 追加のみ |
| A2: `urllib.request.build_opener` | `HTTPSHandler` に custom SSL context を渡す | ❌ | test mocking が複雑化 (opener 全体を mock 必要)、既存 `urllib.request.urlopen` 呼び出しの変更量が大 |
| A3: `requests`/`httpx` 移行 | HTTP client ライブラリを置換 | ❌ | diff 過大 (全 HTTP 呼び出し変更)、dep 追加 2 件、test fixture 全書き換えリスク |

A1 の uniqueness: `_SSL_CONTEXT` を module-level に置くことで、関数呼び出しごとの context 再生成を回避し、かつ `patch('pubmed_reference_resolver.nlm_catalog_check._SSL_CONTEXT', ...)` で test から差し替え可能な構造を実現。

### 4.2 `--reuse-phase3` で LLM cost $0 を実現した手順

baseline 再生成 (Task 3, commit `4ba48ba`) は `main.py --reuse-phase3` オプションを使用。Phase 1/2 (PubMed fetch + Crossref resolution) の出力を cache から再利用し、Phase 3 (NLM Catalog 呼び出し) のみ再実行。NLM Catalog 以外に LLM API 呼び出しは発生せず cost $0。LLM を用いる Phase 4 (三分類判定) も skip され、既存の三分類ロジックで直接 JSON 更新。

### 4.3 apa の unknown 数値が Day21 末と同一である理由

apa_45refs の unknown = 17 は Day22 末でも変化なし。内訳: 16 件は **Crossref graceful failure** (DOI resolution timeout または非 MEDLINE journal)、1 件は **legitimate な NLM Catalog 不在** (NLM Catalog に当該 journal の entry 自体が存在しない)。NLM SSL fix は NLM Catalog への HTTP 接続に作用するため、Crossref 経路の timeout/failure には影響しない。Day22 末の apa unknown は「SSL error」ではなく「Crossref 側の問題 or 正当な NLM 不在」に reason が変化している点が実質的な改善。Crossref graceful 16 件は Day23+ 課題として残置。

---

## 5. 実機検証結果

### 5.1 三分類分布の比較 (cell_45refs)

| 指標 | Day20 末 (SSL 未修正) | Day22 末 (SSL 修正後) | 変化 |
|:---|:---:|:---:|:---:|
| A (PubMed hit) | 1 | 1 | ± 0 |
| B (NLM Catalog hit) | 6 | 12 | +6 ✅ |
| C (predatory / 除外) | 0 | 0 | ± 0 |
| unknown | 8 | 2 | −6 ✅ |
| 合計 | 15 | 15 | — |

### 5.2 三分類分布の比較 (apa_45refs)

| 指標 | Day20 末 | Day22 末 | 変化 |
|:---|:---:|:---:|:---:|
| A (PubMed hit) | 0 | 0 | ± 0 |
| B (NLM Catalog hit) | 3 | 3 | ± 0 |
| C (predatory / 除外) | 0 | 0 | ± 0 |
| unknown | 17 | 17 | ± 0 (reason 変化あり) |
| 合計 | 20 | 20 | — |

### 5.3 smoke check 結果

NLM Catalog ISSN `1091-7527` (Families, Systems & Health (Fam Syst Health)) への直接呼び出しで `status=Y, nlm_id=9610836` を取得。SSL fix 前は `ssl.SSLCertVerificationError` で失敗していたが、certifi 注入後は正常応答を確認。

### 5.4 test suite

`python3 -m pytest tests/ -q` で 101 passed, 1 skipped。新規 unit test `test_fetch_json_uses_certifi_ssl_context` が SSL context の regression guard として機能 (100→101)。

---

## 6. 教訓 (D22-1, D22-2, D22-3)

### 6.1 D22-1: Mac Python.org installer の空 cert.pem 落とし穴

**事象**: Mac に Python.org 公式 installer でインストールした Python 3.x は `/Applications/Python 3.x/Install Certificates.command` を実行しない限り、OS の keychain と切り離された状態で起動する。デフォルトの `ssl.create_default_context()` が参照する cert bundle が空 or 不在となり、HTTPS 接続で `ssl.SSLCertVerificationError: certificate verify failed` が発生する。NLM Catalog の HTTPS エンドポイントに対してこの問題が顕在化し、Day20 で导入した Rule 3 ロジック全体が機能不全に陥っていた。

**解決**: `certifi` パッケージが提供する `certifi.where()` を `ssl.create_default_context(cafile=...)` に渡すことで、OS 環境に依存しない deterministic な cert bundle を使用。Linux (ubuntu-latest CI) でも動作確認済。

**学び**: Mac + Python.org installer の組み合わせは SSL cert 問題が発生しやすい。CI (ubuntu-latest) では問題が出なかったため「CI パスしたから OK」が false safety になる典型例。ローカル Mac で SSL エラーが出たら certifi を runtime dep に追加するのが最短解。

### 6.2 D22-2: logic 層と環境層を分けてデバッグする習慣

**事象**: Day20 で Rule 3 NLM 直接検索の logic を実装し、テストもパスしていた。しかし実際の baseline fixture を生成すると unknown が多発。初見は「logic にバグがある」と疑いたくなるが、実際は「環境 (SSL cert) の問題で logic が呼ばれていなかった」。

**学び**: デバッグ時に「logic 層 (アルゴリズム・データ変換)」と「環境層 (ネットワーク・SSL・ファイルシステム)」を分離して検証する習慣が重要。環境層のエラーは logic の unit test では検出されにくい。integration test や smoke check で環境層まで通すことが「Day20 改修の真価発揮」に必要だった。

**適用範囲**: HTTP 通信・DB 接続・ファイル I/O を伴う任意のモジュールに適用可能。unit test は logic layer の regression guard、integration test + smoke check は environment layer の健全性確認という役割分担を明確にする。

### 6.3 D22-3: code review で検出した Important/Minor を atomic fix-up commit として分離する pattern

**事象**: Task 2 (TDD GREEN) のコードレビューで module docstring に certifi dep 注記が欠落していると指摘 (commit `0f0e028`)。Task 3 (baseline 再生成) のコードレビューで integration test docstring が Day22 fulfillment を反映していないと指摘 (commit `9c299c0`)。どちらも main 実装 commit とは別の atomic commit として追加。

**学び**: code review の fix を main commit に squash しないで atomic な fix-up commit として分離すると、`git log --oneline` で「fix-up がどの review 指摘に対応するか」が一目瞭然になる。history readability が向上し、将来の `git bisect` や `git blame` でも文脈が追いやすい。subagent-driven-development (code review subagent) との連携では、この pattern が標準的なフローとして定着した。

---

## 7. 残存タスク (Day23 以降)

### 7.1 Day22 で新規追加された課題

- **apa_45refs Crossref graceful failure (16 件)**: Crossref SSL/timeout 側の確認、または NLM 直接検索パスへの fallback 検討。DOI が解決できても NLM Catalog に journal がない場合と、Crossref 自体がタイムアウトする場合を切り分ける必要がある。
- **cell `ref_no=41` NLM fuzzy-match 誤検出**: Processes journal のクエリに対し NLM Catalog が Deposition Record (Depos Rec) を返す事象。NLM Catalog 検索の precision 改善 (完全一致優先 or 類似度スコアリング) が必要。

### 7.2 Day21 §6.1 からの継続課題

- [ ] **CONTRIBUTING.md / Issue PR template** (Day23 推奨 パターン 1)
- [ ] **pre-commit hook gitleaks 自動実行** (Day23 推奨 パターン 2)
- [ ] **predatory journal データベース連携** (Beall's list)
- [ ] **pyproject.toml + uv.lock 移行** (CLAUDE.md § 8 整合)
- [ ] **PyPI 公開** (packaging + homepageUrl)
- [ ] **MCP server による batch processing** (Stage 3 拡張)
- [ ] **SSL fix の corporate proxy 対応文書化** (USAGE_QUICKSTART)

### 7.3 Day23+ 推奨着手順

1. **CONTRIBUTING.md / Issue PR template** (公開済リポジトリの collaboration 受入準備、~2h)
2. **pre-commit hook gitleaks 自動実行** (将来の secret leak 防止、~1h)
3. **apa_45refs Crossref graceful failure 対応** (unknown 17 件の残り 16 件解消へ、~3h)

---

## 8. 次セッション再開時のプロンプトテンプレート

### パターン 1: Day23 として CONTRIBUTING.md / Issue PR template

```
Day23 として、Public 公開済の pubmed-reference-resolver に collaboration
受入準備として CONTRIBUTING.md と Issue/PR template (.github/) を追加
します. brainstorming → SPEC → 実装で進めてください. ~2h.
```

### パターン 2: Day23 として pre-commit hook gitleaks 自動実行

```
Day23 として、pre-commit hook で gitleaks scan を自動実行する仕組みを
追加します. .pre-commit-config.yaml + Day18 で確立した .gitleaksignore
の継承. 開発者が secret leak を commit 前に検出できる ops 強化. ~1h.
```

### パターン 3: Day23 として Crossref graceful failure 対応

```
Day23 として、apa_45refs の unknown 17 件のうち Crossref graceful
failure 16 件の根本原因を調査・解消します. Crossref SSL/timeout 側の
確認、または NLM 直接検索パスへの fallback 検討. baseline 再生成で
B/C 判定が増加することを確認. ~3h.
```

### パターン 4: Day23 として NLM fuzzy-match precision 改善

```
Day23 として、cell ref_no=41 (Processes journal) で観測された NLM
fuzzy-match 誤検出 (Processes → Depos Rec) を修正します. NLM Catalog
検索の precision 改善 (完全一致優先 or 類似度スコアリング). TDD で
回帰テストを追加してから実装. ~2h.
```

---

**記録完了日**: 2026-05-24 (Day22)
**記録者**: Claude Code (Sonnet 4.6)
**ステータス**: Day22 archive 完成、v0.1.0 公開維持済、Day23 着手準備完了 (4 パターンプロンプトあり)
