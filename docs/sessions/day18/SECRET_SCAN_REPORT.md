# Secret Scan Report (Day18)

**Purpose**: Day18 Private push 前の git history 全体 secret scan の evidence 記録. 将来 Day19+ で公開切替する際の参考資料.

**Result**: ✅ **SAFE TO PUSH** (clean after 1 documented false-positive suppression)

---

## 1. Execution Metadata

- **実行日時**: 2026-05-18 16:58:11 JST
- **gitleaks version**: 8.30.1
- **scan 対象 directory**: `.` (repository root: `/Users/katayamahideki/Desktop/Claude/査読用/査読reference用/pubmed-reference-resolver`)
- **scan 範囲 (commits)**: `ea3d604` .. `f5a44f1` (合計 **70 commits**)
- **scan 実施者**: Claude Code (Sonnet 4.6) 経由
- **承認**: 片山英樹 (Hideki Katayama)

## 2. gitleaks Detection

### 2.1 実行コマンド
```bash
gitleaks detect --source . --verbose \
  --report-format json \
  --report-path /tmp/gitleaks_report.json
```

### 2.2 結果 (1 回目の scan、`.gitleaksignore` 配置前)

| Metric | 値 |
|:---|---:|
| Commits scanned | 68 (Day18 SPEC commit `7d6a50e` 時点) |
| Bytes scanned | 3.86 MB |
| Findings | **1** |

検出された 1 件:

```
Finding:     "NCBI_API_KEY=ncbi-test-67890\n",
Secret:      ncbi-test-67890
RuleID:      generic-api-key
Entropy:     3.640224
File:        tests/test_env_loader.py
Line:        40
Commit:      d49dc58e0ea89a1d5f0eabbf546824859718e48d
Author:      Hideki Katayama
Email:       hikataya01@gmail.com
Date:        2026-05-08T12:04:57Z
Fingerprint: d49dc58e0ea89a1d5f0eabbf546824859718e48d:tests/test_env_loader.py:generic-api-key:40
```

### 2.3 False positive 判定

該当 file (`tests/test_env_loader.py:40`) の context を確認:

```python
@pytest.fixture
def env_file_in_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a .env file in tmp_path and chdir to it so load_env_files()
    picks it up via the cwd candidate."""
    p = tmp_path / ".env"
    p.write_text(
        "ANTHROPIC_API_KEY=sk-ant-test-12345\n"
        "NCBI_API_KEY=ncbi-test-67890\n",   # ← gitleaks 検出箇所
        encoding="utf-8",
    )
```

**判定**: ✅ **False positive** (synthetic test fixture)

根拠:
- `ncbi-test-67890` は文字列内に `test` を含む synthetic 値
- 同一 fixture 内の `sk-ant-test-12345` も同様の synthetic
- 目的は Day8 env loader regression test (`load_env_files` の空値上書き logic 確認)
- 実 API key とは無関係 (Day8 PHASE_BETA で導入、Day8 PHASE_0_VERIFICATION_REPORT §9.1 で確認済)

### 2.4 Suppression 対応

`.gitleaksignore` を repo root に配置し、該当 fingerprint を suppress:

```
# tests/test_env_loader.py:40 — synthetic NCBI test fixture
d49dc58e0ea89a1d5f0eabbf546824859718e48d:tests/test_env_loader.py:generic-api-key:40
```

### 2.5 結果 (2 回目の scan、`.gitleaksignore` 配置後)

| Metric | 値 |
|:---|---:|
| Commits scanned | 68 |
| Bytes scanned | 3.86 MB |
| Findings | **0** ✅ |

```
INF 68 commits scanned.
INF scanned ~3862797 bytes (3.86 MB) in 898ms
INF no leaks found
```

### 2.6 適用 rules (gitleaks built-in)

gitleaks 8.x は 100+ rule (AWS / GCP / Anthropic / Stripe / private key / DB connection 等) を default で起動. 詳細は <https://github.com/gitleaks/gitleaks/blob/master/config/gitleaks.toml> 参照.

## 3. Manual Grep 補完 (false negative リスク低減)

| Pattern | Command | 結果 |
|:---|:---|:---|
| Anthropic real key | `git log --all -p -S "ANTHROPIC_API_KEY=sk-"` | (Day18 PLAN commit `f5a44f1` 内の documentation 参照のみ、実 key 含まず) |
| NCBI real key | `git log --all -p -S "NCBI_API_KEY="` | (Day18 PLAN commit `f5a44f1` 内の documentation 参照のみ; § 2.3 で扱った test fixture は別途 suppression 済) |
| Private key block | `git log --all -p -S "PRIVATE KEY"` | (Day18 PLAN commit `f5a44f1` 内の documentation 参照のみ) |
| Bearer token | `git log --all -p -S "Bearer "` | (Day18 PLAN commit `f5a44f1` 内の documentation 参照のみ) |
| Unexpected email | `git log --all -p -S "@gmail.com" \| grep -v "Co-Authored\|hikataya01"` | (Day18 PLAN commit `f5a44f1` 内の documentation 参照のみ; 想定外メアドなし) |

すべての pattern hit は Day18 PLAN ドキュメント自身に含まれる「検査 pattern の説明文」であり、実際の secret leak ではない. これは plan が自己記述的に「これらのパターンを scan する」と書いているため発生する想定内現象.

## 4. 許容される email 出現

以下は意図的に commit log / commit body に含まれており、安全とみなす:

- `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` — Day8+ で全 commit trailer に付与、公開しても問題なし (Anthropic noreply)
- `hikataya01@gmail.com` — 本人 author email (`git config user.email`)、公開しても本人 GitHub と紐づく既知情報

## 5. 結論

すべての検査:
- gitleaks 自動 scan (`.gitleaksignore` で 1 件の synthetic test fixture を documented suppression) → **0 findings**
- 手動 grep 5 patterns → **真の leak なし** (PLAN ドキュメント内 self-reference のみ)

→ **SAFE TO PUSH** (Phase 3 で `git push -u origin main` 実行可)

将来 Day19+ で公開切替する際は、本 report を再点検し、間に追加された commit について同一 scan を再実行することが推奨される. `.gitleaksignore` の suppression entry もそのまま有効.

---

**作成日**: 2026-05-18 16:58 JST
**作成者**: Claude Code (Sonnet 4.6)
**承認**: 片山英樹 (Hideki Katayama)
**関連 SPEC**: `docs/sessions/day18/SPEC_github_private_push.md` §3 (commit `7d6a50e`)
**関連 PLAN**: `docs/sessions/day18/PLAN_github_private_push.md` Task 1
**関連 file**: `.gitleaksignore` (suppression list)
