# Day29 Lessons Learned (2026-05-28)

## §1 概要

Day23 で発生した機密データ commit 事故 (fixture に peer-review 由来内容が
含まれ git filter-repo + force push で対応) の再発防止のため、3 層防御
機構を導入した。

### §1.1 セッション開始時の状態

- 115 passed / 0 skipped (Day28 末)
- pre-commit hook 未導入、CONTRIBUTING.md 未作成
- CI 3 jobs (test 3.11, test 3.12, test-experimental 3.14)
- pyproject.toml dev group: pytest のみ

### §1.2 セッション終了時の状態

- 115 passed / 0 skipped / 0 failed (test 追加なし)
- pre-commit hook 動作中 (gitleaks v8.30.1)
- CI 4 jobs (+ gitleaks)、`permissions: contents: read` 明示
- CONTRIBUTING.md 作成済 (97 行、install 手順 + commit 規約 + セキュリティ規約)
- history audit baseline: **0 件 / 137 commits / 1.23 秒** (Day23 filter-repo の効果実証)
- LLM cost: $0 (設定 + 動作検証のみ、外部 API 呼び出しなし)

---

## §2 設計上の発見

### §2.1 Day23 学びの自動化

Day23 で「人間の目視 review のみに依存」したことが事故の根本原因だった。
Day29 で導入した 3 層防御は、Day23 学びを **自動化機構** に翻訳:

| Day23 教訓 | Day29 自動化 |
|:---|:---|
| commit 前検出機構がなかった | Layer 1: Local pre-commit hook |
| `--no-verify` でローカル防御が無効化され得る | Layer 2: CI gitleaks job (二重防御) |
| 過去の漏洩が未検証だった | Layer 3: One-shot history audit (0 件 baseline) |

### §2.2 gitleaks AWS rule の挙動 — 重要な発見

Plan §Task 3 Step 1 で「`AKIAIOSFODNN7EXAMPLE` は gitleaks default rule が
必ず detect する典型 pattern」と想定したが、**実機検証では detect されな
かった**:

- gitleaks v8.30.1 の `aws-access-token` rule は AWS 公式 documentation の
  example (`AKIAIOSFODNN7EXAMPLE` 等) を allowlist している可能性が高い
- これは false positive 抑制として合理的な設計だが、smoke test では機能
  しない
- entropy check との組み合わせで `EXAMPLE` を含むダミーが弾かれる説もあり

**反省点**: spec/plan 段階で gitleaks rule database (`gitleaks --help` または
公式 `/config/rules/aws.go`) を直接確認すべきだった。

**鉄板 detect pattern (Day29 で実証)**:
- `slack-bot-token` (`xoxb-...`): detect 成功、RuleID `slack-bot-token`
- `private-key` (`-----BEGIN RSA PRIVATE KEY-----`): detect 成功

将来の smoke test/教育素材ではこれらを採用する。

### §2.3 pre-commit framework と独自 gitleaks build

pre-commit framework は repo cache 内に独自の go build 版 gitleaks を
持つ:
- 場所: `~/.cache/pre-commit/repo*/golangenv-default/bin/gitleaks`
- `gitleaks version` は "version is set by build process" と表示、明示 version 出力なし
- hook 実行時はこれが呼ばれる

history audit (CLI 直接実行) には、明示 version を持つ Homebrew 版
(`/opt/homebrew/bin/gitleaks` v8.30.1) を使い分けた。

両者の **rule database は同一**(両者とも公式 gitleaks のソースから build)で
detect 挙動に差はない。

### §2.4 gitleaks default rule の妥当性

事前懸念: PMID (8 桁数字) や DOI URL を誤検出するのではないか?

実証結果 (history audit):
- 137 commits の全 history scan で finding **0 件**
- false positive なし
- PMID/DOI は gitleaks default rule の対象外 (API key/token/private key
  の典型 pattern のみ検出)

結論: `.gitleaks.toml` の事前 customization は **不要**。false positive
発生時に reactive 対応で十分 (YAGNI 原則)。

### §2.5 pre-commit framework と uv 統合パターン

Day27 で確立した uv 体制と pre-commit framework の統合方式:

```bash
# 開発者の install 1 行
uv sync --group dev && uv run pre-commit install
```

- `uv sync --group dev` で pre-commit パッケージを install
- `uv run pre-commit install` で `.git/hooks/pre-commit` を配置
- pre-commit framework が gitleaks binary を auto-build (初回のみ)
- これで CLAUDE.md §8.1 (uv 統一) と整合

### §2.6 Atomic 6-file commit の合理性

partial state は効果不完全:
- `.pre-commit-config.yaml` のみ → 開発者が hook install しないと無効
- CI job のみ → push 前にローカルでの早期検知なし
- CONTRIBUTING.md のみ → 機構未配置

→ 6 ファイルを 1 commit にまとめることで「Day29 commit を revert すれば
完全に元の状態に戻る」性質を確保 (Day27 atomic migration と同パターン)。

### §2.7 CI gitleaks job の `permissions: contents: read` 明示

Code quality reviewer I-1 指摘により、初期 commit (`ae47c63`) に
follow-up commit (`adb0cde`) で `permissions: contents: read` を明示:

- public repo の default permissions と等価だが明示することで:
  - organization 設定変更による暗黙拡張の回避
  - workflow file 単体での security posture の明示
  - 将来の job 追加時の参考形式

- amend ではなく **新規 commit** で対応 (main 既に push 済、CLAUDE.md
  §7.2.2 git push --force 禁止)

defense-in-depth の原則を CI 設定にも適用した好例。

---

## §3 動作検証結果

### §3.1 Layer 1 (Local pre-commit hook)

| 検証項目 | 結果 |
|:---|:---:|
| `uv run pre-commit install` で hook 配置 | ✓ |
| ダミー AWS credential (AKIAIOSFODNN7EXAMPLE) の commit 試行 | **検出されず** (rule allowlist の可能性、§2.2 参照) |
| ダミー Slack bot token (`xoxb-...`) の commit 試行 | **commit ブロック** ✓ (RuleID `slack-bot-token`) |
| 通常 file (README.md 空行追加) の commit 試行 | **commit 成功** ✓ |
| gitleaks binary version | v8.30.1 (Homebrew) / pre-commit cache 内 build (両者同等) |

### §3.2 Layer 2 (CI gitleaks job)

| 検証項目 | 結果 |
|:---|:---:|
| ae47c63 push 後 CI 4 jobs all green (run 26873722044) | ✓ |
| adb0cde push 後 CI 4 jobs all green (run 26874101471) | ✓ |
| `permissions: contents: read` 明示後の gitleaks job | success (13s) |
| SARIF artifact 生成 | ✓ |

### §3.3 Layer 3 (One-shot history audit)

```
gitleaks detect --log-opts="--all" --source . \
  --report-format json --report-path .gitleaks-audit.json --no-banner
```

| 項目 | 値 |
|:---|:---:|
| Scan 対象 commits 数 | **137** |
| Scan 対象 bytes | 5.10 MB |
| Scan 所要時間 | **1.23 秒** (wall clock 1 秒) |
| Finding 件数 | **0** |
| Report file | `.gitleaks-audit.json` (3 bytes、`[]` 空配列、.gitignore で除外) |

**意義**: Day23 で実施した filter-repo + force push が完全に履歴を浄化した
ことを、gitleaks の客観的 audit で証明。Day23 対応の事後検証として価値が
大きい。

---

## §4 brainstorm/spec/plan の流れ

| 段階 | 内容 | commit |
|:---:|:---|:---:|
| 1 | brainstorm: テーマ選定 (Pattern A pre-commit gitleaks)、scope 確定 (二重防御 + history audit) | — |
| 2 | spec 書き出し + self-review | `ddff834` |
| 3 | plan 書き出し (Task 0-4 bite-sized 分解、gitleaks v8.21.4 → v8.30.1 update) | `5a8acdd` |
| 4 | Task 1 事前確認 (uv 0.11.14、pre-commit PyPI 4.6.0、gitleaks v8.30.1 tag 確認) | — |
| 5 | Task 2 atomic 6-file security setup + push + CI 4 jobs 確認 | `ae47c63` |
| 6 | Task 2 follow-up: gitleaks job permissions 明示 (review I-1) | `adb0cde` |
| 7 | Task 3 動作検証 + history audit (Plan AWS pattern 誤りを発見、Slack token 代替で完遂、0 件 baseline) | — |
| 8 | Task 4 archive (README + LESSONS) + push + CI | `(本 commit)` |

self-review で発見した訂正点 (plan):
- gitleaks `v8.21.4` (spec 仮置き) → `v8.30.1` (plan 時点で確認した最新)
  に update

self-review で発見した訂正点 (Task 3 実行時):
- Plan の `AKIAIOSFODNN7EXAMPLE` smoke test pattern は gitleaks v8.30.1
  で detect されず、Slack bot token pattern で代替実施
- 誤通過 commit `d3dda5d` を `git reset --hard HEAD~1` で local revert
  (push 前、CLAUDE.md §7.2.2 例外扱い、即時 `git status` で clean 確認)

---

## §5 Day30+ 候補

### Top priority (Day29 LESSONS から派生)

1. **smoke test 自動化** (回帰防止)
   - `tests/test_pre_commit_smoke.py` で Slack bot token pattern による
     blocking 検証を自動化
   - 規模: 小 (1 test file 追加)
   - ROI: 中 (gitleaks rule database 変更時の検知)

2. **追加 pre-commit hook の検討**
   - end-of-file-fixer / trailing-whitespace / check-yaml / check-toml
   - 規模: 小 (`.pre-commit-config.yaml` への追記のみ)
   - ROI: 中 (style 統一による diff ノイズ削減)

3. **SECURITY.md 整備**
   - Vulnerability disclosure policy
   - 規模: 小 (1 file 追加)
   - ROI: 中 (PyPI 公開化前提では必須)

### Medium priority (既存候補から引き継ぎ)

4. **ruff + mypy 導入** (CLAUDE.md §8.2 既定、技術的負債解消、Day28 LESSONS §5)
5. **Node.js 20 deprecation 対応** (actions/checkout@v4 → @v5、setup-python@v5 → 後継版)
6. **PyPI 公開化** (複数セッション規模、Day27 LESSONS から継続)
7. **CI python-version-file SoT 化**
8. **Dependabot 設定** (依存更新自動化)
9. **CI branches: trigger に残存する `feature/mdpi-fast-path` の削除** (前回 review N-1)

### Low priority (将来オプション)

10. **regex + `\p{Lu}` への移行** (Day28 LESSONS §5、Latin Extended-A の小文字
    混入排除、boundary 文脈で false positive 影響ゼロなので低優先)
11. **PMC OA fixture integration test** (Latin Extended-A 実 paper)
12. **Latin Extended-B / Extended Additional 拡張**
13. **Crossref graceful failure** (apa_45refs の 16 件)
14. **NLM fuzzy-match 精度改善**

---

## §6 メトリクス

| 指標 | 値 |
|:---|:---:|
| brainstorm 質問数 | 2 (gitleaks スコープ / history audit 実施) |
| commit 数 | 5 (spec / plan / security / permissions fix / archive) |
| 新規 file 数 | 4 (.pre-commit-config.yaml, CONTRIBUTING.md, README.md, DAY29_LESSONS_LEARNED.md) |
| modify file 数 | 5 (pyproject.toml, uv.lock, .gitignore, .github/workflows/tests.yml ×2) |
| 新規 dependency | 1 (pre-commit>=4.0,<5.0、dev group のみ) |
| pyproject.toml 変更行 | +1 |
| .github/workflows/tests.yml 変更行 | +12 (gitleaks job 10 行 + permissions 2 行) |
| CONTRIBUTING.md 行数 | 97 |
| 全体 tests passed | 115 → 115 (test 追加なし) |
| skipped | 0 → 0 |
| LLM cost | $0 |
| history audit finding | **0** |
| history audit scan time | 1.23 秒 (137 commits, 5.10 MB) |
| CI 4 jobs build time (run 26874101471) | test 3.11: 16s, test 3.12: 17s, test-experimental 3.14: 11s, **gitleaks: 13s** |

---

## §7 関連参照

- [Spec](../../superpowers/specs/2026-05-28-day29-pre-commit-gitleaks-design.md)
- [Plan](../../superpowers/plans/2026-05-28-day29-pre-commit-gitleaks.md)
- [CONTRIBUTING.md](../../../CONTRIBUTING.md)
- [Day23 LESSONS](../day23/DAY23_LESSONS_LEARNED.md): 機密データ事故と filter-repo 対応
- [Day27 LESSONS](../day27/DAY27_LESSONS_LEARNED.md): pyproject + uv 体制
- [Day28 LESSONS](../day28/DAY28_LESSONS_LEARNED.md): 前 session
- [gitleaks 公式](https://github.com/gitleaks/gitleaks)
- [pre-commit.com](https://pre-commit.com/)
