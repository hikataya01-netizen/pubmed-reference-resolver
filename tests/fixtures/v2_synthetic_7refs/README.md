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

## 抄録本文について (プレースホルダ置換済み)

本リポジトリは公開であり、`ncbi_responses.json` (efetch 応答) に含まれる書誌メタデータ
(タイトル・著者・雑誌名・DOI 等) は問題ないが、非 OA 出版社 (Lancet / NEJM /
Cochrane 等) の **抄録本文** をそのまま収録するのは著作権上望ましくない。そのため
`<AbstractText>` 要素の本文はすべて `[abstract omitted from fixture: publisher text]`
に置換してある (属性は保持、`tools/record_v2_fixture.py:sanitize_efetch_xml`)。
`expected_references_abstracts.txt` / `resolved.json` もこの置換後の内容から再生成
されている。書誌メタデータ・撤回検出等の回帰テストの有効性には影響しない。

## 再記録 (実通信あり)

    HOME="$(mktemp -d)" env -u NCBI_API_KEY .venv/bin/python tools/record_v2_fixture.py

PubMed 側の書誌更新でゴールデンテストが意図せず変わる場合のみ実行し、差分をレビューしてコミットする。
デフォルト実行 (フラグなし) は記録時に自動で抄録本文をサニタイズする。

既存の記録済み応答を取り直さずサニタイズだけやり直したい場合 (実通信なし):

    HOME="$(mktemp -d)" env -u NCBI_API_KEY .venv/bin/python tools/record_v2_fixture.py --sanitize-only
