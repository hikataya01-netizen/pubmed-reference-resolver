# Day30 Lessons Learned (2026-05-28)

## §1 概要

Day29 LESSONS §5 Top priority 3 候補 (smoke test 自動化 / 追加 pre-commit
hook / SECURITY.md) を 1 セッションで実装した。Day29 で導入した 3 層防御
(local pre-commit hook + CI gitleaks job + history audit) を土台に、その
回帰 guard と運用面 (style 一貫性・脆弱性報告窓口) を補強する位置づけである。
3 候補は互いに独立しており、subagent-driven-development で Task 単位に
分割実装した。

### §1.1 セッション開始時の状態

- 115 passed / 0 skipped (Day29 末)
- pre-commit hook: gitleaks 1 件のみ
- SECURITY.md 未作成
- 既存 style 違反 (fixture/patch 外): ~10 ファイル
- gitleaks の動作は CI と local hook で確認済だが、その挙動を固定する
  自動テストは存在せず、将来のルール変更・誤設定で防御が無言で外れる
  リスクがあった

### §1.2 セッション終了時の状態

- 117 passed / 0 skipped / 0 failed (+ smoke 2)
- pre-commit hook: 5 件 (gitleaks + end-of-file-fixer + trailing-whitespace
  + check-yaml + check-toml)
- SECURITY.md 作成済 (GitHub Security Advisories 報告窓口)
- 既存 style 違反 (fixture/patch 外): 0
- CI 4 jobs green、smoke test も CI で pass (117 passed)
- LLM cost: $0 (本体ロジック非依存、全工程が決定論的)

---

## §2 設計上の発見

本セッションで得た 8 件の finding を以下に詳述する。いずれも
「pre-commit / gitleaks という外部ツールの実挙動が、ドキュメントから
素朴に期待される挙動と乖離する」点に根がある。spec/plan 段階で仮定した
挙動が実装中に覆る場面が複数あり、plan の contingency 節が機能した。

### §2.1 gitleaks pre-commit hook は --staged + pass_filenames:false

**背景**: smoke test は当初 `gitleaks --files <tmpfile>` 方式で「秘密を
含むファイルを検出する」ことを確認する設計だった。しかし pre-commit の
gitleaks hook entry は `gitleaks git --pre-commit --staged` であり、
`pass_filenames: false` が設定されている。

**対処**: この構成では hook に渡されるファイル名 (`--files`) は無視され、
**staged 内容 (git index) のみ**が scan 対象になる。したがって smoke test
側も「秘密ファイルを git add で staging → hook 相当の scan を起動 →
検出を確認 → staging 解除」という git add staged 方式に切替えた。

**教訓**: pre-commit hook をテストから駆動する場合、その hook が
filename 引数で動くか staged 内容で動くかを `.pre-commit-config.yaml` の
`entry` / `pass_filenames` から確認する必要がある。本件は plan の
contingency 節に「smoke test が --files で動かない場合は staged 方式」と
事前記載していたため、想定内の切替で済んだ。

### §2.2 slack-bot-token rule の entropy 閾値

**背景**: smoke test の「検出される秘密」サンプルとして slack-bot-token
形式 (`xoxb-...`) を採用した。初版では token suffix を `"A"*24` のような
単純反復文字列にしていたが、gitleaks が検出しなかった。

**対処**: gitleaks の多くのルールは正規表現マッチに加えて Shannon entropy
の下限 (slack-bot-token は概ね >=3) を要求する。`"A"*24` は entropy 0 で
閾値を下回り弾かれる。suffix を英数字混在の文字列 (entropy 約 3.77) に
変更したところ安定して検出された。

**教訓**: 秘密検出ツールの positive サンプルは「正規表現を満たす」だけでは
不十分で「entropy 閾値も満たす」必要がある。テスト用 fixture を作る際は
ランダム性のある文字列を使い、entropy 0 の反復文字列を避ける。

### §2.3 smoke test の index 安全性

**背景**: §2.1 の staged 方式は秘密を含むファイルを一時的に git index へ
追加するため、テストが途中で失敗すると index が汚染され、後続の手動 commit
に秘密が紛れ込む二次事故リスクがある。

**対処**: fixture の `finally` 節で `git rm --cached` による index からの
除去と作業ファイルの `shutil.rmtree` を必ず実行する構成とした。テスト
前後で `git status` が空であることを実機で検証し、index 汚染が残らない
ことを確認した。

**教訓**: 「秘密を扱うテスト」自体が漏洩経路になりうる。staging を伴う
テストは finally で必ず原状回復し、前後の git status 空を不変条件として
検証する。Day24 の tripwire test と同じく、防御機構のテストは防御を
破る材料を手元に作るため、後始末の厳密さが本体実装以上に重要になる。

### §2.4 top-level exclude の罠

**背景**: spec 初版では pre-commit の `exclude` を top-level (全 hook 共通)
に置き、fixture/patch ディレクトリを除外する設計だった。

**対処**: top-level exclude は gitleaks hook (別 repo block) にも適用される
ため、gitleaks が fixture 内に意図的に置いた検証用サンプルを scan しなく
なってしまう。これは Day29 の防御意図を損なう。そこで exclude を per-hook
(各 hook の `exclude` キー) に降ろし、gitleaks 以外の整形系 hook にのみ
適用、gitleaks の fixture scan は維持した。この矛盾は spec self-review で
発見・訂正した。

**教訓**: pre-commit の top-level exclude は全 hook に効く強い設定で、
「整形からは外したいが scan からは外したくない」というファイルを誤って
scan からも外す。除外の意図が hook ごとに異なる場合は per-hook exclude を
使う。spec の self-review が実装前にこの矛盾を捕捉した点が効いた。

### §2.5 patch/binary の保護

**背景**: 追加した trailing-whitespace hook は行末空白を機械的に除去する。
しかし `integration/patches/` 配下の `.patch` ファイルは、行末空白が
diff の意味の一部 (context 行の空白) であり、除去すると patch が壊れる。

**対処**: per-hook exclude に `^integration/patches/` を追加し、
trailing-whitespace / end-of-file-fixer が patch を改変しないようにした。
PDF/DOCX 等のバイナリは pre-commit の `identify` がファイル種別を判定して
自動的に skip するため、明示除外は不要だった。

**教訓**: 整形 hook は「空白に意味がある形式」(patch, 一部の固定幅データ,
Makefile の tab 等) を壊しうる。これらは exclude で保護する。バイナリは
pre-commit が自動 skip するため過剰な除外設定は不要。protected file の
変更件数 0 を実測で確認した。

### §2.6 git show --name-only の落とし穴

**背景**: 一括 normalization (Task 2) と各 commit で「保護対象ファイル
(fixture/patch/binary) を誤って変更していないか」を検証する際、当初
`git show --name-only` で変更ファイル一覧を取得しようとした。

**対処**: `git show --name-only` は変更ファイル名に加えて **commit message
本文も出力に含む**ため、message 内の単語がファイル名と誤判定されうる。
protected file 検証には `git diff-tree --no-commit-id --name-only -r <sha>`
を使い、純粋な変更ファイル一覧のみを得る方式に変更した。これは spec review
で発覚した。

**教訓**: commit の変更ファイル一覧をスクリプトで機械処理する場合、
`git show --name-only` ではなく `git diff-tree --no-commit-id --name-only -r`
を使う。前者は message 本文混入で false match を生む。検証ロジックの入力に
ノイズが混じると防御判定が壊れる典型例。

### §2.7 Co-Authored-By trailer の repo 一貫性

**背景**: 本セッションの harness default の Co-Authored-By trailer は
`Claude Opus 4.8 (1M context)` だが、repo 全体の既存 commit は一貫して
`Claude Opus 4.7 (1M context)` を使っている。

**対処**: repo の commit 履歴の一貫性を優先し、本セッションの全 commit でも
`Claude Opus 4.7 (1M context)` を継続使用した。

**教訓**: Co-Authored-By のようなメタデータは、harness の default よりも
当該 repo の既存慣行を優先して一貫性を保つ。履歴の検索性・集計の観点で、
途中でモデル表記が割れると追跡が煩雑になる。

### §2.8 code review NICE-TO-HAVE の取捨選択

**背景**: smoke test (Task 3) に対する code review で、MUST/SHOULD/
NICE-TO-HAVE の指摘が出た。NICE-TO-HAVE まで全て取り込むとスコープが
膨らむため取捨選択が必要だった。

**対処**: smoke test の回帰失敗時に原因を切り分けやすくする診断ヒント
(N2: assertion message に「gitleaks ルール変更の可能性」を示す文言) を
polish として適用し、`f95ed34` に amend した (元 `df823fa` を polish)。
N1/N4 も併せて取り込んだ。一方、README → SECURITY.md / CONTRIBUTING.md
→ SECURITY.md の相互リンク補強は本セッションのスコープ外として Day31+ に
retain した。

**教訓**: code review の NICE-TO-HAVE は「現 Task の本質を強化するもの」
(診断ヒント等) は取り込み、「別 Task / 別ファイル群への波及」(相互リンク
補強等) は次セッションへ送る、という線引きが有効。テストの失敗時診断ヒントは
将来の自分への投資効率が高く、優先的に取り込む価値がある。

---

## §3 実装結果

### §3.1 Task 別サマリ

| Task | 内容 | 結果 |
|:---|:---|:---|
| B-1 (`ab8dacc`) | pre-commit-hooks v6.0.0 から 4 hook 追加 + per-hook exclude | hook 1 → 5 |
| B-2 (`3d31b93`) | 既存 style 違反一括 normalization | 10 file 修正、protected 0 |
| A (`f95ed34`) | gitleaks smoke test 2 件 (+ N2 polish) | 115 → 117 passed |
| C (`e8915e6`) | SECURITY.md (GitHub Security Advisories 窓口) | 報告窓口を明文化 |

### §3.2 一括 normalization 実測

| 指標 | 値 |
|:---|:---:|
| 修正ファイル数 | 10 (.json/.md) |
| 末尾改行追加 (end-of-file-fixer) | 8 files |
| 行末空白除去 (trailing-whitespace) | 2 files |
| protected file (fixture/patch/binary) 変更 | 0 |

### §3.3 smoke test

| 検証 | 結果 |
|:---|:---:|
| detect (slack token) | PASSED |
| clean (false positive guard) | PASSED |
| test ファイル自身の gitleaks scan | Passed |
| 全体 pytest | 117 passed |

### §3.4 CI

| Job | Status | Build time |
|:---|:---:|:---:|
| test (3.11) | success | 38s |
| test (3.12) | success | 37s |
| test-experimental (3.14) | success | 40s |
| gitleaks | success | 6s |

CI run ID: `27093333258` (117 passed、6 commits scanned no leaks)

---

## §4 brainstorm/spec/plan の流れ

| 段階 | 内容 |
|:---|:---|
| brainstorm | 4 質問で 3 候補 (smoke test / 追加 hook / SECURITY.md) の範囲・優先順位・依存を確定 |
| spec | self-review で top-level exclude の矛盾 (§2.4) と git show 誤用 (§2.6) を訂正 |
| plan | pre-commit-hooks を v6.0.0 に固定、exclude に `^integration/patches/` 追加 (§2.5)。smoke test の --files / staged 切替を contingency として事前記載 |
| 実装 | Task 単位で subagent-driven。token entropy (§2.2) と staged 方式 (§2.1) を実装中に確定 |

self-review で発見した訂正点:

- spec: top-level exclude → per-hook exclude (gitleaks fixture scan 保護)
- plan: pre-commit-hooks v5.0.0 → v6.0.0、exclude に `^integration/patches/`
  追加
- 実装: smoke test を `--files` → git add staged 方式 (plan contingency)、
  token entropy 修正

これらはいずれも「実装に入る前 (spec/plan)」または「plan が想定した
contingency 内」で吸収できた。事前の self-review と contingency 設計が
手戻りを抑制した。

---

## §5 Day31+ 候補

### Top priority

- **ruff + mypy 導入** (CLAUDE.md §8.2 準拠、pre-commit hook 化も可能)。
  本セッションで整形系 hook の基盤ができたため、lint/type も hook へ
  載せやすい。
- **README → SECURITY.md / CONTRIBUTING.md → SECURITY.md 相互リンク補強**
  (Task 4 review NICE-TO-HAVE、本セッションで retain)

### Medium priority

- **PyPI 公開化本体** (SECURITY.md / CONTRIBUTING.md / LICENSE 整備済で
  前提条件が揃った)
- **Dependabot 設定** (pre-commit rev / GitHub Actions の自動更新)
- **Node.js 20 deprecation 対応** (actions/checkout@v4 等の CI annotation
  解消)
- **CI branches trigger 整理** (`feature/mdpi-fast-path` 残存の掃除)

### Low priority

- **追加 pre-commit hook 拡張** (check-added-large-files 等)
- **regex + `\p{Lu}` 移行、PMC OA integration test** (Day28 LESSONS 由来)
- **project-overview.html の配置確定** (現在親ディレクトリに存在)

---

## §6 メトリクス

| 指標 | 値 |
|:---|:---:|
| brainstorm 質問数 | 4 |
| commit 数 | 7 |
| 新規 file 数 | 4 (test_gitleaks_smoke.py, SECURITY.md, README.md, LESSONS.md) |
| modify file 数 | 2 + 10 (config/gitignore + style 一括) |
| 新規 dependency | 0 (pre-commit-hooks は pre-commit 管理) |
| 新規 pre-commit hook | 4 |
| 新規 unit test | 2 (smoke) |
| 全体 tests passed | 115 → 117 |
| LLM cost | $0 |

---

## §7 関連参照

- [Spec](../../superpowers/specs/2026-05-28-day30-security-quality-hardening-design.md)
- [Plan](../../superpowers/plans/2026-05-28-day30-security-quality-hardening.md)
- [SECURITY.md](../../../SECURITY.md)
- [CONTRIBUTING.md](../../../CONTRIBUTING.md)
- [Day29 LESSONS](../day29/DAY29_LESSONS_LEARNED.md): pre-commit gitleaks 3 層防御 (本 session の基盤)
- [Day24 LESSONS](../day24/DAY24_LESSONS_LEARNED.md): tripwire test pattern (smoke test の先例)
- [pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks): end-of-file-fixer / trailing-whitespace / check-yaml / check-toml の供給元
- [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories): SECURITY.md の報告窓口
