# Day29: pre-commit gitleaks 導入 — 設計仕様 (Design Spec)

**作成日**: 2026-05-28
**対象セッション**: Day29
**前提セッション**: Day23 (機密データ事故 + filter-repo 浄化) → Day28 (Latin Extended-A 拡張)
**起点 commit**: `4a0adfd` (Day28 archive)

---

## §1 背景と目的

### §1.1 Day23 で発生した事故の振り返り

Day23 で fixture に peer-review 由来の機密データが含まれていることが発覚し、
`git filter-repo` + `git push --force` で履歴浄化を実施した。CLAUDE.md §7.2.2
(破壊的 Git 操作の禁止) を例外的に承認した重大事案。

事故の根本原因:
- **commit 前の機密検出機構が存在しなかった** (人間の目視 review のみに依存)
- review が漏れたら commit → push → 公開リポジトリに到達
- 発見後の対応コストは極めて高い (history rewrite + force push + 共同作業者への影響)

### §1.2 Day29 の目的

「予防は事後対応より遥かに安価」の原則に従い、以下を構築する:

1. **Local pre-commit hook**: 開発者の `git commit` 直前に staged 内容を gitleaks で scan
2. **CI gitleaks job**: GitHub Actions で push/PR 時に再 scan (二重防御、`--no-verify` 対策)
3. **One-shot history audit**: Day29 セッション内で git history 全体を 1 回 scan、漏洩 0 件を証明

これにより、Day23 と同種の事故が将来発生する確率を実質的にゼロに近づける。

### §1.3 CLAUDE.md との整合性

- §7.1 (機密情報・認証情報の保護): pre-commit hook が「commit 前検出」を自動化
- §7.2.2 (Git 履歴の破壊禁止): 予防により filter-repo 等の破壊的操作の必要性自体を減らす
- §8.1 (uv 統一): `pre-commit` パッケージは `[dependency-groups] dev` に追加し uv で管理
- §8.3 (再現性): `uv.lock` を Git 管理することで開発者間の hook バージョン揃えを保証

---

## §2 設計上の Question と採用案

### §2.1 Q1: テーマ選定

| Option | 概要 | 採用可否 |
|:---|:---|:---:|
| **(A) pre-commit gitleaks 導入** ✓ | Day23 再発防止、規模小、ROI 高 | **採用** |
| (B) ruff + mypy 導入 | CLAUDE.md §8.2 既定、技術的負債解消、規模中 | ✕ (Day30+ 候補) |
| (C) Node.js 20 deprecation 対応 | 規模極小、学び薄 | ✕ (Day30+ 候補) |
| (D) PMC OA fixture integration test | Day28 unit test の延長、規模中 | ✕ (Day30+ 候補) |

**採用根拠**: Day23 事故の重大性 + 予防機構の不在 + 規模小 + 1 セッション完結性。

### §2.2 Q2: gitleaks のスコープ

| Option | 概要 | 採用可否 |
|:---|:---|:---:|
| **(α) ローカル pre-commit + CI 二重防御** ✓ | 早期検知 + skip 防止 | **採用** |
| (β) ローカル pre-commit のみ | `--no-verify` で skip 可能、不十分 | ✕ |
| (γ) CI のみ | commit 後検出になり history rewrite が必要に | ✕ |

**採用根拠**: 二重防御により `git commit --no-verify` での skip も CI で捕捉可能。

### §2.3 Q3: history audit を Day29 で実施するか

| Option | 概要 | 採用可否 |
|:---|:---|:---:|
| **(α) Day29 で実施** ✓ | Day23 以前の見落とし漏洩を再検査、0 件を明示的に証明 | **採用** |
| (β) 実施しない | forward looking のみ、過去は Day23 で浄化済と信頼 | ✕ |

**採用根拠**: 「予防機構導入と同時に過去 audit を完結させる」が最も clean な状態。期待値は 0 件だが、万一 finding > 0 ならその時点で対応判断 (Day29 内で stop)。

### §2.4 Q4: pre-commit framework の選択

| Option | 概要 | 採用可否 |
|:---|:---|:---:|
| **(I) pre-commit.com 標準** ✓ | デファクト標準、gitleaks 公式 hook 提供、`.pre-commit-config.yaml` で宣言的 | **採用** |
| (II) 自作 .git/hooks/pre-commit | シンプルだが maintain しにくい、開発者間共有不可 | ✕ |
| (III) lefthook (Go ベース) | 高速だが追加バイナリ install 必要、Python 統一性で劣後 | ✕ |

**採用根拠**: Python project の standard、gitleaks 公式 rev 指定可能、`uv run pre-commit` で実行統一。

### §2.5 Q5: dependency 管理方式

| Option | 概要 | 採用可否 |
|:---|:---|:---:|
| **(a) [dependency-groups] dev に pre-commit 追加** ✓ | CLAUDE.md §8.1 整合、uv sync で install 完結 | **採用** |
| (b) pipx で global install | プロジェクト独立、再現性低 | ✕ |
| (c) CONTRIBUTING.md で手動 install 指示 | 開発者ごとに version drift | ✕ |

**採用根拠**: Day27 で確立した uv ベース single source of truth との整合性。

### §2.6 Q6: rule customization

| Option | 概要 | 採用可否 |
|:---|:---|:---:|
| **(♦) default rule のみで開始** ✓ | gitleaks default は API key/token/private key の典型 pattern を網羅 | **採用** |
| (♥) 最初から .gitleaks.toml で project 固有 allowlist | 過剰最適化、必要性が立証されていない | ✕ |

**採用根拠**: PMID 8 桁数字や DOI URL は gitleaks default rule では誤検出されない。false positive が発生したら追加判断 (現時点で YAGNI)。

---

## §3 Architecture

### §3.1 3 層構造

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Local pre-commit hook (developer machine)         │
│  - .pre-commit-config.yaml で gitleaks hook 定義             │
│  - `uv run pre-commit install` で .git/hooks/pre-commit 配置 │
│  - `git commit` 時に staged file 自動 scan                  │
│  - finding 検出 → commit ブロック                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ (commit 通過、--no-verify でも skip 可)
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: CI gitleaks job (GitHub Actions)                  │
│  - .github/workflows/tests.yml に独立 job 追加               │
│  - gitleaks/gitleaks-action@v2 公式 action                  │
│  - push/PR で history を再 scan                              │
│  - finding 検出 → CI 失敗 → PR merge ブロック                 │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼ (one-shot, Day29 のみ)
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: History audit (one-shot baseline)                 │
│  - `gitleaks detect --log-opts="--all" ...` で全 history scan│
│  - .gitleaks-audit.json に詳細 report 出力 (commit しない)    │
│  - 0 件を確認 → LESSONS に baseline として記録                │
└─────────────────────────────────────────────────────────────┘
```

### §3.2 採用バージョン

| ツール | バージョン | 役割 |
|:---|:---|:---|
| `pre-commit` (PyPI) | `>=4.0,<5.0` | hook framework |
| gitleaks binary | v8.21.x | secret scanner (pre-commit hook が自動 download) |
| `gitleaks/gitleaks-action` | `@v2` | GitHub Actions integration |

注: pre-commit framework は declared hook の binary を自動 install するため、開発者・CI ともに gitleaks の手動 install は不要。

### §3.3 ファイル構成

| File | 種別 | 内容 |
|:---|:---:|:---|
| `.pre-commit-config.yaml` | new | gitleaks hook 定義(最小、5 行) |
| `pyproject.toml` | modify | `[dependency-groups] dev` に `pre-commit>=4.0,<5.0` 追加 |
| `uv.lock` | modify | uv sync 自動 update |
| `.gitignore` | modify | `.gitleaks-audit.json` 追加 |
| `.github/workflows/tests.yml` | modify | gitleaks job 追加 |
| `CONTRIBUTING.md` | new | 開発者向け install 手順(最小) |

### §3.4 `.pre-commit-config.yaml` 構造

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.4
    hooks:
      - id: gitleaks
```

最小構成。`stages` / `args` 等は default のまま (commit 時に staged file を scan)。

### §3.5 `.github/workflows/tests.yml` への追加 job

既存 `test` / `test-experimental` の後に新規 job:

```yaml
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0   # history scan のため shallow clone を解除
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

OSS 利用前提のため `GITLEAKS_LICENSE` (商用 license) は不要。

### §3.6 `CONTRIBUTING.md` 構造

開発フローの最小ガイド (約 30-50 行):

```markdown
# Contributing to pubmed-reference-resolver

## 開発環境セットアップ

1. uv install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. 依存関係 install: `uv sync --group dev`
3. pre-commit hook install: `uv run pre-commit install`

## 開発フロー

- 機能変更 → test 追加 → `uv run pytest tests/` で全 PASS 確認
- `git commit` 時に pre-commit hook が自動実行 (gitleaks scan)
- push 時に CI が再 scan + test 実行

## Pull Request

- main branch から feature branch を切る
- conventional commits 形式 (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`)
- CI green を確認してから PR open

## セキュリティ

- 機密情報 (.env, credentials.json, *.pem 等) は絶対に commit しない
- pre-commit hook で gitleaks が staged 内容を自動 scan
- 万一漏洩した場合は維持者 (@kataya-okayama-u-pall-care) に即座連絡
```

---

## §4 Implementation 詳細

### §4.1 `pyproject.toml` 変更

```toml
[dependency-groups]
dev = [
    "pytest>=9.0,<10.0",
    "pre-commit>=4.0,<5.0",   # ← 追加
]
```

`uv add pre-commit --group dev` で自動追加 + `uv.lock` 更新。

### §4.2 `.gitignore` 追加

```
.gitleaks-audit.json
```

audit report は機密 finding を含み得るため commit しない。

### §4.3 History audit 実行手順

```bash
# Step 1: pre-commit + gitleaks binary を install
uv run pre-commit install

# Step 2: history 全体 scan (詳細 JSON report)
uv run pre-commit run gitleaks --all-files
# あるいは直接 gitleaks CLI (pre-commit が install した binary を使用):
gitleaks detect --log-opts="--all" --source . \
  --report-format json --report-path .gitleaks-audit.json

# Step 3: 結果確認
ls -l .gitleaks-audit.json
jq 'length' .gitleaks-audit.json   # 0 想定
```

**重要**: `.gitleaks-audit.json` は機密 finding を含み得るため commit しない (.gitignore で除外済)。LESSONS には件数のみ記録。

### §4.4 動作確認手順 (Day29 セッション内)

| 検証項目 | 手順 | 期待結果 |
|:---|:---|:---|
| pre-commit hook 動作 | ダミー secret (`sk_test_FAKE_KEY_FOR_TESTING_DO_NOT_USE_aaaaaaaaaaaaaaaaaaaaaaaa`) を含む tmp file を `git add` → `git commit` を試行 | commit がブロックされ gitleaks finding が表示される (tmp file は即座 delete) |
| 通常 commit が pass | この spec 自体の commit | gitleaks scan が pass し commit 成功 |
| CI gitleaks job 動作 | push 後 GitHub Actions で gitleaks job が green | success (4 jobs total) |
| 既存 pytest に regression なし | `uv run pytest tests/` | 115 passed |
| history audit | report 0 件 | LESSONS に baseline 記録 |

---

## §5 Error handling

### §5.1 pre-commit install 失敗時

- uv path 問題: CONTRIBUTING.md の install 手順を参照、`which uv` で確認
- bash/zsh 設定問題: shell rc file の PATH 確認

### §5.2 CI gitleaks finding 検出時

- 設計通り: PR block (intentional behavior)
- 開発者は finding を修正してから再 push

### §5.3 history audit finding 検出時

- Day29 セッション内で作業停止
- ユーザー判断を仰ぐ (filter-repo 等の対応は spec 外で実施)
- finding の詳細は `.gitleaks-audit.json` で確認 (commit しない)

### §5.4 false positive 発生時

- Day29 内: `.gitleaks.toml` に allowlist 追加 + commit
- Day29 後: 個別 commit で追記

---

## §6 Testing 戦略 + Commit 戦略

### §6.1 Testing

既存 pytest suite は変更なし (115 passed 維持)。Day29 で追加するのは:
- pre-commit hook 動作確認 (manual smoke test、tmp file による)
- CI gitleaks job 動作確認 (CI run の green 確認)
- history audit 0 件確認 (`.gitleaks-audit.json` の `jq` 出力)

これらは「Day29 セッション内で 1 回行う動作検証」であり、pytest test として永続化する性質ではない。

### §6.2 Commit 戦略

**4 commit chain**:

| # | type | summary | files |
|:---:|:---|:---|:---|
| 1 | `docs(spec)` | Day29 pre-commit gitleaks spec | `docs/superpowers/specs/...` |
| 2 | `docs(plan)` | Day29 pre-commit gitleaks plan | `docs/superpowers/plans/...` |
| 3 | `chore(security)` | introduce gitleaks pre-commit + CI + CONTRIBUTING.md | `.pre-commit-config.yaml`, `pyproject.toml`, `uv.lock`, `.gitignore`, `.github/workflows/tests.yml`, `CONTRIBUTING.md` (6 files atomic) |
| 4 | `docs(sessions)` | archive day29 session | `docs/sessions/day29/...` |

【意見】3 を分割しないのは、これらの変更が「機密漏洩予防機構の導入」という単一機能であり、partial state では効果不完全だから (Day27 atomic migration と同パターン)。

---

## §7 期待 final state

| 項目 | 値 |
|:---|:---:|
| HEAD | archive commit (Day29 4 commit chain の末尾) |
| 全体 tests passed | 115 (Day28 と同じ、test 追加なし) |
| CI jobs | 4 (test 3.11 / test 3.12 / test-experimental 3.14 / **gitleaks**) |
| pre-commit hook | 動作中 (`uv run pre-commit install` 済) |
| CONTRIBUTING.md | 存在 |
| history audit | **0 件** 確認、LESSONS に baseline 記録 |
| 新規 dependency | `pre-commit>=4.0,<5.0` (dev group のみ、production 依存に影響なし) |

---

## §8 Out of scope

明示的に Day29 では扱わない事項 (Day30+ 候補に retain):

1. **ruff / mypy 導入** (Day28 LESSONS §5 Medium priority)
2. **追加 pre-commit hook** (yamllint, end-of-file-fixer, trailing-whitespace 等)
3. **SECURITY.md** (Vulnerability disclosure policy)
4. **Dependabot** 設定 (依存更新自動化)
5. **Node.js 20 deprecation 対応** (`actions/checkout@v4` → `@v5`、Day28 LESSONS §5 Medium priority)
6. **PMC OA fixture integration test** (Day28 LESSONS §5 Top priority)
7. **PyPI 公開化** (Day27 LESSONS から継続、複数セッション規模)
8. **Crossref graceful failure** (apa_45refs の 16 件、Day28 LESSONS §5 Low priority)
9. **`.gitleaks.toml` custom rule の事前準備** (false positive 発生時の reactive 対応に limit)

これらは Day30+ で順次検討する。

---

## §9 LESSONS で記録すべき事項

Day29 archive 時に LESSONS で永続化する knowledge:

1. **gitleaks default rule の有効性** (PMID/DOI 誤検出なし、API key/token の典型 pattern を網羅)
2. **history audit baseline** (0 件確認の事実、Day23 filter-repo の効果実証)
3. **3 層防御の運用感** (local + CI + audit)
4. **pre-commit framework と uv 統合の実装パターン** (`[dependency-groups] dev` + `uv run pre-commit`)
5. **false positive 0 件の baseline** (今後 finding が発生した場合の比較対象)
6. **Day23 学びとの接続** (予防 vs 事後対応のコスト対比、CLAUDE.md §7.1 自動化)

---

## §10 関連参照

- [Day23 LESSONS](../../sessions/day23/DAY23_LESSONS_LEARNED.md): 機密データ事故と filter-repo 対応
- [Day27 LESSONS](../../sessions/day27/DAY27_LESSONS_LEARNED.md): pyproject + uv 体制(本 spec が依存)
- [Day28 LESSONS](../../sessions/day28/DAY28_LESSONS_LEARNED.md): 本 spec の §5 で Day29 候補として提示
- [gitleaks 公式](https://github.com/gitleaks/gitleaks)
- [pre-commit.com](https://pre-commit.com/)

---

**End of Spec**
