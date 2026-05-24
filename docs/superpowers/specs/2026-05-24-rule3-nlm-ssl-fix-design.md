# SPEC: Rule 3 NLM 検索の SSL 問題解消 (Day22)

**作成日**: 2026-05-24 (Day22 brainstorming 完了時)
**著者**: Claude Code (Opus 4.7 / 1M context) / 承認: 片山英樹
**位置付け**: Day20 改修で導入した Rule 3 (NLM Catalog 直接検索) の SSL 問題を解消し、Day20 改修の真価 (三分類 audit の精度向上) を発揮する
**前提**: Day21 末 (commit `c0993f0`、Day22 Phase A1 セキュリティ修正後) で main branch 96 commits、101 tests passed / 1 skipped、GitHub PUBLIC、`v0.1.0` release 公開済

---

## 1. 背景と目的

### 1.1 Day20 改修の積み残し

Day20 で `three_class_classifier.py` に 3 helper を追加 (Day20 SPEC §3) し、DOI 欠落 case の三分類精度を改善した。Day20 baseline 再生成の結果:

| Fixture | Day19 baseline | Day20 改修後 |
|:---|:---|:---|
| cell_45refs | A=14, B=0, C=0, unknown=1 | A=1, B=6, C=0, **unknown=8** |
| apa_45refs | A=4, B=0, C=0, unknown=16 | A=0, B=3, C=0, **unknown=17** |

Rule 1 (book) と Rule 2 (conference) は期待通り B 判定できているが、**Rule 3 (DOI 欠落 + journal 名あり → NLM Catalog 直接検索)** の大半が unknown に倒れる現象が残っていた。Day20 §3.3 / §9 risk table および Day21 LESSONS §6.1 で「Day22+ で SSL 問題解消」と申し送り。

### 1.2 SSL 問題の根本原因 (Day22 brainstorming で確定)

ローカル環境 (Mac, Python.org Python 3.14 installer) での再現:

```
URLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED]
certificate verify failed: self-signed certificate in certificate chain
(_ssl.c:1081)'))
```

原因:
- Python.org installer の `/Library/Frameworks/Python.framework/Versions/3.14/etc/openssl/cert.pem` が **空ディレクトリ** (cert.pem が seed されていない)
- `urllib.request.urlopen()` の default SSL context が CA bundle を持たず、`https://eutils.ncbi.nlm.nih.gov/` への検証で失敗
- `nlm_catalog_check.py:_fetch_json` (line 175-190) は graceful fail-soft で stderr WARN + return None → `_classify_via_nlm_only` が `status=unknown` を返却
- 全 25 件 (cell_45refs 8 件 + apa_45refs 17 件) が unknown に倒れる

検証: `ssl.create_default_context(cafile=certifi.where())` を `urlopen` の `context` kwarg に渡すと、NCBI eUtils へ HTTP 200 取得成功 (NLM ID 9610836 = Fam Syst Health を確認)。

### 1.3 目的

1. **Rule 3 NLM 検索を全 OS で deterministic に成功させる** (certifi の Mozilla CA bundle を明示注入)
2. **三分類 audit の品質改善 (Day20 改修の真価発揮)**: cell_45refs unknown 8 → <8 (B/C 識別)、apa_45refs unknown 17 → <17
3. **将来 regression を防ぐ unit test の追加** (certifi singleton が urlopen に注入されることを検証)
4. **既存 graceful fail-soft の維持**: SSL fix は primary path を通すだけで、network/HTTP/timeout error の unknown fallback は不変

### 1.4 設計判断の経緯 (brainstorming 質問)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | certifi の依存追加方針 | **(a) certifi を requirements.txt に runtime dep として追加** |
| Q2 | baseline 再生成 scope | **(a) cell + apa 両方 (Phase 4 only で LLM cost 0)** |
| Q3 | test 追加方針 | **(a) unit test 1 件追加 (mock で urlopen の context 引数を捕捉)** |
| Approach | 実装スタイル | **A1: module-level `_SSL_CONTEXT` 定数 + `_fetch_json` への注入 (最小 diff)** |

---

## 2. Architecture & ファイル配置

### 2.1 改変対象 (3 ファイル + baseline 4 件再生成)

| ファイル | 種別 | 修正内容 |
|:---|:---|:---|
| `requirements.txt` | 修正 | `certifi>=2024.0,<2027.0` を runtime dep として追加 |
| `nlm_catalog_check.py` | 修正 | module 直下に `_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())` (singleton)、`_fetch_json` の `urlopen(...)` に `context=_SSL_CONTEXT` を渡す |
| `tests/test_nlm_catalog_check.py` | 修正 | unit test 1 件追加 (`test_fetch_json_uses_certifi_ssl_context`) |

### 2.2 Baseline 再生成 (8 ファイル)

| ファイル | 種別 | 再生成理由 |
|:---|:---|:---|
| `tests/fixtures/cell_45refs/baseline_three_class_classification.json` | 再生成 | unknown 8/15 → B/C 識別を確認 |
| `tests/fixtures/cell_45refs/baseline_report.md` | 再生成 | 三分類 section が連動 |
| `tests/fixtures/cell_45refs/README.md` | 更新 | 改修後実測の三分類値 |
| `tests/fixtures/apa_45refs/baseline_three_class_classification.json` | 再生成 | unknown 17/20 → B/C 識別を確認 |
| `tests/fixtures/apa_45refs/baseline_report.md` | 再生成 | 同上 |
| `tests/fixtures/apa_45refs/README.md` | 更新 | 同上 |
| `tests/test_integration_cell_45refs.py` | 修正 | `EXPECTED_THREE_CLASS_DISTRIBUTION` (test 8) を実測値に更新 |
| `tests/test_integration_apa_45refs.py` | 修正 | 同上 |
| `tests/fixtures/mdpi_149refs/expected_report.md` | 必要に応じ再生成 | stub fixture で SSL fix が出力に影響する場合のみ (Day20 §3.4 PLAN gap 同型対応) |

### 2.3 改変なし (確認のみ)

- `three_class_classifier.py` / `main.py` / `crossref_check.py` / `journal_audit.py` / `mdpi_parser.py` (logic 不変)
- 既存 fixture (vancouver_24refs / mdpi_149refs の input + phase1-3 baseline) (本 task と無関係)

### 2.4 新規作成 (Day22 archive)

| ファイル | 用途 |
|:---|:---|
| `docs/superpowers/specs/2026-05-24-rule3-nlm-ssl-fix-design.md` | brainstorming spec (本ファイル) |
| `docs/sessions/day22/PLAN_rule3_nlm_ssl_fix.md` | writing-plans 出力 |
| `docs/sessions/day22/DAY22_LESSONS_LEARNED.md` | Day22 archive |
| `docs/sessions/day22/README.md` | Day22 index |

### 2.5 外部システム変更

- LLM cost: 原則 **$0** (Phase 4 reuse 成功時)。Phase 4 reuse 不可なら ~$2 (Phase 1-4 全実行 × 2 fixture)
- NLM API call: cell_45refs 8 件 + apa_45refs 17 件 = 25 件追加 (rate limit 3 req/s で ~10 秒、API key あれば 10 req/s で ~3 秒)
- 認証情報: `NCBI_API_KEY` (既存 `skill_package/.env` のもの、commit せず)

---

## 3. 実装詳細 (Approach A1)

### 3.1 `requirements.txt` 追加

```diff
 python-docx>=1.2,<2.0   # extract_text() — DOCX ingestion
 rapidfuzz>=3.14,<4.0    # journal/title similarity in structure_all_references & synthesize_outputs
 PyYAML>=6.0,<7.0        # _load_overrides_yaml() — --overrides CLI flag
+certifi>=2024.0,<2027.0 # Mac Python.org installer の空 cert.pem 対策。nlm_catalog_check
+                        # の SSL context (Mozilla CA bundle) を deterministic に供給.
+                        # Day22 Rule 3 NLM SSL fix で導入.
 pytest>=9.0,<10.0       # test runner
```

### 3.2 `nlm_catalog_check.py` 改修 (3 箇所、~7 行追加)

**(a) imports + module-level singleton**:

```diff
 from __future__ import annotations

 import json
 import os
+import ssl
 import sys
 import urllib.error
 import urllib.parse
 import urllib.request
 from pathlib import Path
 from typing import Any

+import certifi
+
 NLM_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
 TIMEOUT_SECONDS = 10
+
+# Module-level SSL context with certifi-provided Mozilla CA bundle.
+# Day22 fix: Python.org installer (Mac) ships an empty cert.pem at
+# /Library/Frameworks/Python.framework/Versions/3.X/etc/openssl/,
+# causing urllib default verification to fail with SSLCertVerificationError
+# against https://eutils.ncbi.nlm.nih.gov/. Using certifi.where() works on
+# all OSes (Linux/Mac/Windows) deterministically.
+_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
```

**(b) `_fetch_json` への context 注入** (line 175-190):

```diff
 def _fetch_json(url: str, *, label: str = "") -> dict | None:
     """Generic JSON fetch with 1 retry (graceful on network error)."""
     for attempt in (1, 2):
         try:
-            with urllib.request.urlopen(url, timeout=TIMEOUT_SECONDS) as resp:
+            with urllib.request.urlopen(
+                url, timeout=TIMEOUT_SECONDS, context=_SSL_CONTEXT,
+            ) as resp:
                 return json.loads(resp.read().decode("utf-8"))
         except (urllib.error.HTTPError, urllib.error.URLError,
                 TimeoutError, OSError) as e:
             if attempt == 2:
                 print(
                     f"WARN: nlm_catalog_check {label} failed: {e}",
                     file=sys.stderr,
                 )
                 return None
             continue  # retry
     return None
```

`get_journal_indexing_status` / `_esearch_live` / `_esummary_live` / `_build_query_params` は触らない。既存 graceful fail-soft (network/HTTP/timeout error は依然として `_result(None, error=...)` 経由で unknown を返す) は不変。

### 3.3 設計判断: なぜ module-level singleton か

| 案 | 評価 |
|:---|:---|
| **(採用) module-level `_SSL_CONTEXT` (singleton)** | certifi cert bundle のロードは数 ms かかるが起動時 1 回。test で `monkeypatch.setattr(nlm_catalog_check, "_SSL_CONTEXT", ...)` で容易に差し替え可能 |
| per-call で `ssl.create_default_context(...)` | 毎 NLM call で数 ms オーバーヘッド、25 件で ~100 ms 損失。test mocking は同程度の難易度 |
| `urllib.request.build_opener(HTTPSHandler(context=...))` | opener が module 状態として残る、test mock chain が複雑化、urllib idiomatic でもない |
| `requests` / `httpx` 移行 | dep 1 件追加 + ~50 行書き直し + test 構造変更、Day22 scope 大幅拡大、minimum-dep 哲学から乖離 |

---

## 4. Test 戦略詳細

### 4.1 unit test 追加 (`tests/test_nlm_catalog_check.py`)

```python
def test_fetch_json_uses_certifi_ssl_context(monkeypatch):
    """_fetch_json は certifi 由来の SSL context を urlopen に渡すこと.

    Day22 Rule 3 NLM SSL fix の regression guard. certifi.where() の
    cafile を持つ ssl.SSLContext が urlopen の context kwarg に渡る
    ことを mock で検証.
    """
    import io
    import ssl
    import nlm_catalog_check  # noqa: E402

    captured = {}

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False

    def fake_urlopen(url, timeout=None, context=None):
        captured["url"] = url
        captured["timeout"] = timeout
        captured["context"] = context
        return FakeResp(b'{"esearchresult": {"idlist": ["12345"]}}')

    monkeypatch.setattr(nlm_catalog_check.urllib.request, "urlopen", fake_urlopen)

    result = nlm_catalog_check._fetch_json(
        "https://eutils.ncbi.nlm.nih.gov/test", label="test"
    )

    assert result == {"esearchresult": {"idlist": ["12345"]}}
    assert isinstance(captured["context"], ssl.SSLContext), (
        f"Expected SSLContext, got {type(captured['context']).__name__}"
    )
    assert captured["context"] is nlm_catalog_check._SSL_CONTEXT, (
        "Expected the module-level _SSL_CONTEXT singleton (certifi-based)"
    )
    assert captured["timeout"] == nlm_catalog_check.TIMEOUT_SECONDS
```

ポイント:
- `monkeypatch` で `urllib.request.urlopen` を差し替え、本物のネットワーク call をせず、`context` 引数を捕捉して検証
- `_SSL_CONTEXT is captured["context"]` で「singleton として渡している」ことを担保 (per-call 生成への regression を防ぐ)
- `cafile` の中身が certifi 経由かは `_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())` という事実で担保

### 4.2 既存 2 unit test の維持

| # | test 名 | 改修後 status |
|:---:|:---|:---:|
| 1 | `test_get_journal_indexing_status_returns_Y_for_indexed_journal` | 不変 (fixture 経由) |
| 2 | `test_get_journal_indexing_status_returns_N_for_unindexed_journal` | 不変 (fixture 経由) |

注: 既存 test は `fixture_search_path` / `fixture_summary_path` 経由で `_fetch_json` を bypass するため、SSL context 変更の影響なし。Phase 3 GREEN 後の test_nlm_catalog_check.py は 既存 2 + 新 1 = **3 件**。

### 4.3 baseline 再生成手順 (Day20 SPEC §4.2 と同型)

```bash
# 環境変数 (.env から事前 source)
set -a; source skill_package/.env; set +a

# (a) cell_45refs 再生成 — Phase 4 only
python3 main.py tests/fixtures/cell_45refs/input_References.docx \
  --output-dir /tmp/cell_45refs_day22_rerun --phase 4
cp /tmp/cell_45refs_day22_rerun/report.md \
   tests/fixtures/cell_45refs/baseline_report.md
cp /tmp/cell_45refs_day22_rerun/three_class_classification.json \
   tests/fixtures/cell_45refs/baseline_three_class_classification.json

# (b) apa_45refs 再生成
python3 main.py tests/fixtures/apa_45refs/input_References.docx \
  --output-dir /tmp/apa_45refs_day22_rerun --phase 4
cp /tmp/apa_45refs_day22_rerun/report.md \
   tests/fixtures/apa_45refs/baseline_report.md
cp /tmp/apa_45refs_day22_rerun/three_class_classification.json \
   tests/fixtures/apa_45refs/baseline_three_class_classification.json
```

⚠️ Phase 4 only で Phase 2/3 結果再利用するため、main.py の `--phase` flag 仕様を Phase 1 直前に `main.py --help` で確認。reuse 不可なら Phase 1-4 全実行 (LLM cost ~$2 追加)。

### 4.4 想定される三分類分布変化

| Fixture | Day20 baseline | Day22 SSL fix 後 (見込) |
|:---|:---|:---|
| cell_45refs | A=1, B=6, C=0, **unknown=8** | A=1, B=6+α, C=β, **unknown ≈ 0-3** (NLM 応答次第) |
| apa_45refs | A=0, B=3, C=0, **unknown=17** | A=0, B=3+α, C=β, **unknown 大幅減** |

α + β は NLM 応答次第で確定。期待値ではなく **実測値** で test 8 (`EXPECTED_THREE_CLASS_DISTRIBUTION`) を更新する (Day20 D20-2 教訓: 「実 fixture から逆算」)。

### 4.5 test 健全性推移想定

| 段階 | passed | 説明 |
|:---:|---:|:---|
| Day21 末 | 100 / 1 skipped | (baseline) |
| Phase 1 (requirements.txt 追加のみ) | 100 / 1 skipped | code 変更なし、不変 |
| Phase 2 (TDD RED): unit test 1 件追加 | 100 / 1 skipped (新 test FAIL) | production code 未改修 → 新 test だけ RED |
| Phase 3 (TDD GREEN): nlm_catalog_check.py 改修 | **101** / 1 skipped | 新 test GREEN、既存 6 unit + 全 integration test 不変 |
| Phase 4a (cell_45refs baseline 再生成 + test 8 更新) | 101 / 1 skipped | EXPECTED_THREE_CLASS_DISTRIBUTION の値変更で pass |
| Phase 4b (apa_45refs baseline 再生成 + test 8 更新) | 101 / 1 skipped | 同上 |
| Phase 5 (mdpi_149refs golden 再生成、必要時) | 101 / 1 skipped | stub fixture が影響を受けた場合のみ |

---

## 5. Commit 計画 (6 commits)

| 順 | type | Phase | 内容 |
|:---:|:---|:---:|:---|
| 1 | `docs(spec)` | Pre | brainstorming spec を `docs/superpowers/specs/2026-05-24-rule3-nlm-ssl-fix-design.md` に commit |
| 2 | `docs(plan)` | Pre | writing-plans 出力を `docs/sessions/day22/PLAN_*.md` に commit |
| 3 | `test(nlm)` | 2 | unit test 1 件追加 (TDD RED 確認) |
| 4 | `fix(nlm)` | 1+3 | requirements.txt に certifi + nlm_catalog_check.py に SSL context 注入 (TDD GREEN) |
| 5 | `test(fixtures)` | 4 | cell_45refs + apa_45refs baseline 再生成 + README + test 8 期待値更新 (必要なら mdpi 含む) |
| 6 | `docs(sessions)` | 5 | Day22 archive (README + LESSONS) |

合計 **6 commits**。Phase A1 commit (`c0993f0`) は既に push 済のため別カウント。

---

## 6. 完了条件 (10 項目)

| # | 条件 | 確認方法 |
|:---:|:---|:---|
| 1 | requirements.txt に `certifi` 追加 + commit | `grep certifi requirements.txt` |
| 2 | nlm_catalog_check.py に `_SSL_CONTEXT` module-level 定数 | `grep "_SSL_CONTEXT = ssl.create_default_context" nlm_catalog_check.py` |
| 3 | `_fetch_json` が `context=_SSL_CONTEXT` を urlopen に渡す | code review + 新 unit test pass |
| 4 | 新 unit test 1 件 (`test_fetch_json_uses_certifi_ssl_context`) pass | `pytest tests/test_nlm_catalog_check.py -v` |
| 5 | 全 unit test pass (regression なし) | `pytest tests/ -q` = 101 passed, 1 skipped |
| 6 | cell_45refs baseline 再生成、unknown が <8 に減少 | `git diff tests/fixtures/cell_45refs/baseline_three_class_classification.json` で unknown 件数 |
| 7 | apa_45refs baseline 再生成、unknown が <17 に減少 | 同上 |
| 8 | test_integration_cell/apa の EXPECTED_THREE_CLASS_DISTRIBUTION 更新 | `pytest tests/test_integration_cell_45refs.py tests/test_integration_apa_45refs.py -v` |
| 9 | gitleaks scan clean (継続) | `gitleaks detect --no-banner --redact` で `no leaks found` |
| 10 | Day22 archive 完成 + push + CI success | `gh run list --limit 1 --json conclusion` |

---

## 7. 工数見積もり

| Phase | 内容 | 見積 |
|:---:|:---|---:|
| Pre | SPEC + PLAN archive | 30 min |
| Phase 1 | requirements.txt + nlm_catalog_check.py 改修 | 15 min |
| Phase 2 | unit test 1 件追加 (TDD) | 15 min |
| Phase 3 | 全 test pass 確認 + 統合 commit | 10 min |
| Phase 4a | cell_45refs baseline 再生成 + test 8 + commit | 30 min |
| Phase 4b | apa_45refs baseline 再生成 + test 8 + commit | 30 min |
| Phase 5 | Day22 archive + push + CI 確認 | 30 min |
| **合計** | | **~2.5h** |

LLM cost: 原則 **$0** (Phase 4 reuse 成功時)。Phase 4 reuse 不可なら ~$2。

---

## 8. 想定リスクと対応

| リスク | 確率 | 対応 |
|:---|:---:|:---|
| NLM API が rate-limit / 一時 503 で再生成不安定 | 中 | 既存 retry 1 回 + graceful unknown で個別 ref が unknown 化、後日再生成で改善。完了条件 6/7 は「unknown 減少」(<完全 0 ではなく) なので許容 |
| mdpi_149refs/expected_report.md が SSL fix で影響 | 低-中 | Day20 §3.4 同様、Phase 3 で全 tests 実行時に検出 → inline fix で同 commit に含める |
| `--phase 4` reuse mode が未実装 | 中 | Phase 1 直前に `main.py --help` で確認、未実装なら Phase 1-4 全実行 (LLM cost ~$2 追加) |
| CI Linux で certifi が冗長 | 低 | Linux は system CA bundle で問題ないが、certifi を経由しても害なし。code は OS 不問で deterministic |
| certifi 2027 までの version pin が狭すぎる | 低 | `<2027.0` は 1 年以上余裕、必要なら patch release で bump |
| corporate proxy 環境で certifi だけでは不十分 | 低 | 本環境では再現せず (ローカル Mac は素のネットワーク)。proxy 環境ユーザーは `SSL_CERT_FILE` env var で proxy CA を override 可能 (将来 USAGE_QUICKSTART で文書化検討) |

---

## 9. Out of Scope (Day23+ 候補)

- **CONTRIBUTING.md / Issue PR template** (Day19 §6.2、collaboration 受入準備、Day22 handoff パターン 2)
- **pre-commit hook gitleaks 自動実行** (Day19 起源、Day22 handoff パターン 3)
- **predatory journal データベース連携** (Beall's list 等で B 細分化)
- **MCP server による batch processing** (Stage 3 を超えた拡張)
- **PyPI 公開** (Day20 §10、homepageUrl 設定 + packaging)
- **pyproject.toml + uv.lock 移行** (Day22 handoff A3 §C5、CLAUDE.md § 8 整合)
- **SSL fix の corporate proxy 対応 文書化** (本 SPEC §8 リスク参照、`SSL_CERT_FILE` env var の使い方を USAGE_QUICKSTART に追記)

---

## 10. 参照

- Day15 SPEC: `docs/sessions/day15/SPEC_three_class_audit.md` (三分類 audit logic の origin、nlm_catalog_check 設計)
- Day15 LESSONS: `docs/sessions/day15/DAY15_LESSONS_LEARNED.md` (graceful fail-soft 設計)
- Day20 SPEC: `docs/sessions/day20/SPEC_three_class_book_web_refinement.md` (Rule 3 origin、baseline 再生成手順)
- Day20 LESSONS: `docs/sessions/day20/DAY20_LESSONS_LEARNED.md` (D20-2: 実 fixture から逆算)
- Day21 LESSONS: `docs/sessions/day21/DAY21_LESSONS_LEARNED.md` §6.1 / §7 パターン 1 (Day22 候補)
- Day22 handoff: `~/Downloads/pubmed-reference-resolver_day22_handoff_20260524.md` Phase B パターン 1
- 既存 `nlm_catalog_check.py` (Day15 commit `71a318a`、本 SPEC で SSL context 注入対象)

---

**承認**: 片山英樹 (brainstorming Q1-Q3 + Approach A1 + design 全 3 sections)
**次工程**: writing-plans skill で implementation plan を作成
