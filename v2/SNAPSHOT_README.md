# v2 スナップショット (MacBook Air 版)

MacBook Air の `~/.claude/skills/pubmed-reference-resolver/` にのみ存在し、git 管理外だった版を
2026-09-14 にそのまま保存したもの。`node_modules/` と `__pycache__/` は除外 (`npm install` で復元)。

- 最終更新: SKILL.md 2026-08-22、audit.py 2026-08-22、main.py 2026-07-25
- エントリポイント: `audit.py` (標準ライブラリのみ、Word 出力は `build_docx.js` + npm `docx`)
- iMac 上で `python3 audit.py --structured examples/expected_output/refs.json -o out --no-docx` を実行し、
  RESOLVED 5 / UNRESOLVED 1 / NON_PUBMED 1、期待出力 CSV の Ref_No・Match_Status・PMID 列と一致を確認

main 版 (v1) との統合方針は別途決定 (v2 を正式版とする)。
