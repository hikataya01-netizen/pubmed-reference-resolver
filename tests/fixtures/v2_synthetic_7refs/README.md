# v2_synthetic_7refs

v2 (MacBook Air 版、2026-08-22) に同梱されていた合成テストセット `refs.json` (7 件)。
実在論文の書誌 (PubMed 公開メタデータ) と、意図的に誤った/存在しない参照から成る。

| ref | 内容 |
|---|---|
| 1 | GLOBOCAN 2022 (PMID 38572751) 正常 |
| 2 | ref 1 と同一 DOI (重複引用) |
| 3 | Wakefield 1998 Lancet (PMID 9500320、撤回論文) |
| 4 | 存在しない論文 (UNRESOLVED) |
| 5 | Temel 2010 NEJM (RCT) |
| 6 | Cochrane レビュー (メタ解析/SR) |
| 7 | 書籍 (NON_PUBMED) |

## ファイル

- `ncbi_responses.json` / `doaj_responses.json`: 2026-09-14 に記録した応答 (テストはこれを再生し、通信しない)
- `expected_*`: 再生 + 実行日 2026-09-14 固定で生成した期待出力
- `resolved.json`: `audit.py --reuse-resolved` 用 (doctor のオフライン確認でも使用)

## 再記録 (実通信あり)

    HOME="$(mktemp -d)" env -u NCBI_API_KEY .venv/bin/python tools/record_v2_fixture.py

PubMed 側の書誌更新でゴールデンテストが意図せず変わる場合のみ実行し、差分をレビューしてコミットする。
