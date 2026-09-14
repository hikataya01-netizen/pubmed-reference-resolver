# Day31 LESSONS LEARNED

## §1 git 管理外の改修が PC 間で分岐していた

- v2 は MacBook Air の `~/.claude/skills/` に直接置かれ、GitHub にも iMac にも存在しなかった。iMac 側では旧版を修正しており、どちらが最新か誰にも分からない状態だった。
- 「以前は動いた」は PC 固有の状態 (手作業で入れた依存、cwd 依存の .env 読込) に支えられていた。
- **教訓**: スキルは必ず git 管理下の repo に置き、`~/.claude/skills/` からは symlink のみで参照する。新しい PC では `tools/doctor.sh` を通す。

## §2 iCloud 同期フォルダ上の repo

- iMac の repo は iCloud 同期の Desktop 配下にあり、MacBook Air にも同じ実体 (`.git`・`.venv` 含む) が同期されていた。`.venv` のパスはユーザー名に依存し、2 台で `uv sync` すると壊し合う。
- **教訓**: 作業ツリーは同期フォルダの外 (`~/repos/` 等) に置く。iMac 側の移設は未実施 (次回候補)。

## §3 例外を握りつぶすコードに対する記録再生テスト

- `pipeline/enrich.py` は照会失敗を `except Exception` で「未評価」に倒すため、再生クライアントが未記録リクエストで AssertionError を投げても握りつぶされ、テストが空振りし得た (Task 2 レビュー、最終レビューで 2 回検出)。
- **教訓**: 本体を変えずに検証するときは、失敗を例外ではなく「記録」(`unrecorded` / `calls` リスト) で残し、テスト側で空であることを assert する。

## §4 公開 repo の fixture と著作物

- 実 API 応答をそのまま記録すると、出版社の抄録全文が fixture・期待出力に入る。README の「PMC OA CC BY 4.0 由来」方針と衝突した。
- 最新 commit で除去しても履歴には残るため、push 前に全 commit から除去する履歴書き換えが必要になった。
- **教訓**: 記録ツールに sanitize (抄録本文の置換) を最初から組み込む (`tools/record_v2_fixture.py`)。公開前に `git log -p` で本文断片を grep する。

## §5 サブエージェント運用

- 実装担当が API レート制限で中断したが、差分が未コミットで残っていたため再開で完了できた。台帳 (ledger) と git 状態で復旧点を判断した。
- サブエージェント側の環境指示により Co-Authored-By が別名になったため、push 前にメッセージを修正した。

## §6 次回 (Day32) 候補

1. `audit.py extract`: PDF/DOCX から参照ブロックを抽出し、MDPI 形式は自動で refs.json 化
2. 旧 main.py の env ローダーを共有モジュールへ切り出し (v2 が legacy の private 関数に依存している)
3. Crossref による未解決文献 3 分類の v2 統合 (Day33 予定)
4. iMac の repo を iCloud 同期外へ移設
