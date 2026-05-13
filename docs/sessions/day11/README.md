# docs/sessions/day11/

**Day11 セッション (2026/05/13) のアーカイブ**

このディレクトリは、pubmed-reference-resolver プロジェクトの Day11 セッション (Day7 §9.3 long-term task の 1 件目「Vancouver/AMA 系 golden fixture 追加」を TDD で対応した作業) で生成された記録を、永続アーカイブとして保管する.

## 内容

| ファイル | 役割 | 対象 |
|:---|:---|:---|
| `DAY11_LESSONS_LEARNED.md` | Day11 全 2 commits の TDD cycle + ハイブリッド命名規約 (`expected_*` / `baseline_*`) の設計判断 + 教訓 3 件 (D11-1〜D11-3) の retro レポート | プロジェクト閲覧者向け |
| `README.md` | 本書 | プロジェクト閲覧者向け |

## Day11 の特徴

Day8/Day9/Day10 と同じく **形式的な PHASE_*_INSTRUCTIONS.md を持たない**. 先生からの単一プロンプトで開始:

> Day11 として、Vancouver/AMA 系の golden fixture を新規追加します
> (Day7 §9.3 長期タスク). Day9 (Z) で取得した Stage 2 の出力を
> tests/fixtures/vancouver_24refs/ に baseline として配置し、
> test_integration_vancouver_24refs.py を新設してください.
> TDD で進めてください.

Day11 の特徴は **TDD で「fixture data 配置」を GREEN 工程に位置づけた**こと. 通常 TDD の GREEN は production code を書く段階だが、本セッションでは:

- **RED**: test を先に書き、fixture data 不在で `FileNotFoundError` (5 件全 fail)
- **GREEN**: production code には触れず、**fixture 5 ファイル配置のみ**で test pass

これは Day8 (env loader 改修) や Day9 (Vancouver Veto 実装) のような production code 修正型 TDD とは異なる「**data-driven TDD**」の実例. D11-2 として教訓化.

## 達成事項 (2 commits)

| 順 | commit | 種別 | 達成 |
|:---:|:---:|:---|:---|
| 1 | `fe38298` | test(integration) | Vancouver fixture (5 ファイル) + test (5 件) を新設、TDD 1 cycle で完成 |
| 2 | (本 commit) | docs(sessions) | Day11 archive (README + LESSONS) を追加 |

main branch: 38 → **39** + 本 commit で **40 commits** (Day10 末 → Day11 末、+2)
test 健全性: 66 passed → **71 passed** (+5 件) / 1 skipped

## Day7 §9.3 long-term task の達成状況

| タスク | 状態 |
|:---|:---:|
| **別ドメイン golden fixture (Vancouver / APA / Cell)** | ✅ Vancouver は Day11 完了 (APA / Cell は将来候補) |
| MCP/hook 経由 Claude UI 起動配線 (Stage 3) | ⏳ 未着手 |
| Day9 (Z) 残存未解決 2 件 (#17 Davey, #22 Gallina) の MEDLINE 非収録調査 | ⏳ 未着手 |
| GitHub remote 追加と push | ⏳ 未着手 |

## 関連記録

完全な session 記録は別途以下に保管 (本リポジトリ外):

- `pubmed-reference-resolver-integration-chat-day11.md` (Day11 の完全記録、Claude Opus 作成、予定)
- `pubmed-reference-resolver-integration-chat-day{1,...,10}.md` (前日記録)

## 利用方法

### Day12 以降の参照

Day11 で確立された「ハイブリッド命名規約」(`expected_*` deterministic / `baseline_*` variability-bearing) は、将来 LLM 経由の出力を fixture 化する際に再利用可能. 特に APA/Cell 等の別ドメイン fixture を追加する際の設計指針となる.

### 他プロジェクトへの応用

「**fast-path corpus は厳密 golden、LLM corpus は document-of-record**」設計指針は、LLM ハイブリッド型 pipeline を持つ他のスキル開発でも応用可能. D11-1 として教訓化.

## ディレクトリ命名規約

`docs/sessions/dayN/` 形式 (Day6 で確立、Day7-11 で継続). Day12 セッション完了後は `docs/sessions/day12/` が追加される予定.

---

**作成日**: 2026/05/13 (Day11 クロージング時)
**メンテナ**: 片山英樹 (Hideki Katayama)
