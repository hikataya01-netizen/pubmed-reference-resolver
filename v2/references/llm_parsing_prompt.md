# Stage 3: 参照構造化 (呼び出し側 LLM が in-context で実施)

Version: 2.0 (2026-08-22)
Purpose: References セクションの生テキストを、`audit.py --structured` が読み込む
`refs.json` へ変換する。**外部 API 呼び出しは行わない** — この作業は本スキルを
実行しているセッションの Claude 自身が in-context で行う。

> **旧版注記**: 本ファイルは以前、`main.py` 時代の Stage 3 (1 参照ごとに
> Sonnet を HTTP 呼出しして構造化する設計) 向けの出力スキーマ
> (`{ref_no, authors:[...], doi_alt, is_book, ...}`) を記載していたが、
> これは現行 `audit.py::load_refs()` が実際に読み込むスキーマと一致していなかった。
> 本改訂で `refs.json` の実スキーマに合わせて全面的に書き直した。
> 以下の「既知の前処理アーティファクトへの耐性」の節は旧版から価値が高いため
> そのまま引き継いでいる。

---

## 出力スキーマ: `refs.json`

```json
{
  "meta": {
    "source": "reference.docx",
    "md5": "<入力ファイルの MD5>",
    "subject": "<論文の主題、1行>",
    "verdict": ["査読観点の総評を箇条書きで", "..."]
  },
  "references": [
    {
      "ref_no": 1,
      "pmid": "39036382",
      "doi": "10.1016/j.jncc.2024.01.006",
      "claimed_first_author": "Han B",
      "claimed_year": 2024,
      "claimed_journal": "J Natl Cancer Cent",
      "claimed_title": "Cancer incidence and mortality in China, 2022",
      "raw": "1. Han B, Zheng R, Zeng H, et al. Cancer incidence and mortality in China, 2022. J Natl Cancer Cent. 2024;4(1):47-53.",
      "is_non_pubmed": false,
      "non_pubmed_reason": null,
      "non_pubmed_note_if_unresolved": null,
      "citation_contexts": ["本文中でこの文献が引用されている箇所の一文 (任意、複数可)"]
    }
  ]
}
```

### フィールド説明

| フィールド | 必須 | 説明 |
|---|:--:|---|
| `ref_no` | 必須 | References 内の通し番号。重複不可 |
| `pmid` | 任意 | 引用元に明記された PMID (`null` 可) |
| `doi` | 任意 | 引用元に明記された DOI (`null` 可、URL prefix なし) |
| `claimed_first_author` | 任意 | 引用元の筆頭著者姓 (Stage4 の L3 系検索と `_accept()` ガードに使う。省略すると誤マッチ検出の精度が下がる) |
| `claimed_year` | 任意 | 引用元記載の発行年 |
| `claimed_journal` | 任意 | 引用元記載の雑誌名 |
| `claimed_title` | 任意 | 引用元記載のタイトル (L3 系検索の主要な手がかり。省略すると `_accept()` の類似度ガードが機能しない) |
| `raw` | 推奨 | 元の引用文字列そのまま (レポート上での参照用) |
| `is_non_pubmed` | 任意 | 書籍・ガイドライン等 PubMed 対象外なら `true` |
| `non_pubmed_reason` | `is_non_pubmed=true` 時に推奨 | 対象外と判定した理由 |
| `non_pubmed_note_if_unresolved` | 任意 | 未解決時に表示する補足 (省略時は既定文言) |
| `citation_contexts` | 任意 (v2 新規) | この文献が本文中で引用されている箇所の一文または要約。**主張支持性評価 (`claim_not_supported`/`claim_partially_supported` カテゴリ) にのみ使う。省略した場合、その参照の主張支持性評価は自動的にスキップされる (パイプライン内 LLM 呼出は行わない)** |

`ref_no` 以外の欠落フィールドは `audit.py::load_refs()` が `null`/`false` で
自動補完するため、生成側で全フィールドを埋める必要はない。ただし
`claimed_title` を省略すると L3 系解決の誤マッチガード (タイトル類似度 ≥0.50)
が効かなくなるため、可能な限り埋めること。

---

## 既知の前処理アーティファクトへの耐性 (旧版より継承)

References セクションが PDF からのコピー&ペーストである場合、以下のノイズが
混入していることがある。`raw` への転記時に気づいたら妥当な範囲で補正してよいが、
不確実な場合は補正せず `raw` に原文のまま残すこと (捏造を避けるため)。

1. **単語中のソフトハイフン** — PDF の行折り返しでハイフンが単語中に残る:
   `RELA-TIONSHIP` → `RELATIONSHIP`、`Charac-teriz-ing` → `Characterizing`。
   ハイフンを除去して意味の通る語になる場合のみ除去する。`state-of-the-art` の
   ような複合語のハイフンは保持する。
2. **DOI 中のハイフンの曖昧性** — `10.1016/j.jpsy-chores.2022.111139` の
   `jpsy-chores` は行折り返しアーティファクトの可能性が高い
   (`jpsychores` が正しい可能性)。判断がつかない場合は `doi` に見たままの形を
   入れ、`raw` に元の文字列を残す。Stage4 の DOI 検索は完全一致を要求しないため、
   誤りがあっても L3 系カスケードでの再解決を試みる。
3. **散在する数字の残骸** — 行番号統計検出 (Stage 1-2、`main.py::detect_line_numbers`)
   で大半は除去済みだが、1〜2 個の残骸が残ることがある。巻号・ページ・年の
   抽出時は無視する。
4. **英語以外の文献** — フランス語・ドイツ語・スペイン語・イタリア語等の参照も
   有効な入力である。ダイアクリティカルマーク (é, è, ü, ñ, á) は保持する。
5. **書籍と雑誌論文の区別** — 書籍は ISBN・出版社の記載があり雑誌・巻・号がない。
   `is_non_pubmed=true`、`non_pubmed_reason="書籍"` とする。PubMed でヒットしない
   ことが正常であり、`unresolved` カテゴリで MAJOR 扱いにはしない。

## 主張支持性評価のための `citation_contexts` 抽出指針 (v2 新規)

`citation_contexts` は「本文が、この参照によって何を主張させているか」を示す
最小限の手がかりである。以下の方針で抽出する。

- 引用番号 `[n]` や上付き数字が本文中に現れる箇所を検索し、その文が含む
  **事実主張・数値・結論**を短く抜き出す (原文の一文、または要約)。
- 1 参照に複数の引用箇所がある場合は配列に複数格納してよい。
- 本文が提供されていない (References セクションのみの検証依頼) 場合、
  `citation_contexts` は省略してよい。省略時、当該参照の主張支持性評価は
  自動スキップされ、CSV の `Claim_Support` 列は `NOT_ASSESSED` になる
  (エラーにはならない)。
- **捏造しないこと**: 本文中に該当する引用箇所が見当たらない場合は、
  無理に主張を作らず省略する。

## 主張支持性の判定 (2 パス目、`--claim-support`)

Stage4 の PubMed 解決が完了した後、呼び出し側 LLM は解決済み参照の abstract
(`resolved.json` または `references_abstracts.txt` から取得可能) と
`citation_contexts` を突合し、以下の形式で `claim_support.json` を作成する。

```json
[
  {"ref_no": 5, "verdict": "DOES_NOT_SUPPORT",
   "rationale": "本文は『生存期間を2倍に延長』と主張するが、当該研究の主要評価項目は QOL であり、生存期間中央値に有意差はなかった。"}
]
```

`verdict` は `SUPPORTS` / `PARTIAL` / `DOES_NOT_SUPPORT` のいずれか。
`DOES_NOT_SUPPORT` は `claim_not_supported` (MODERATE)、`PARTIAL` は
`claim_partially_supported` (INFO) として issues に計上される。`SUPPORTS` は
issue化しない (問題ではないため)。

再実行コマンド:

```bash
python3 audit.py --structured refs.json -o ./out \
    --reuse-resolved ./out/resolved.json \
    --claim-support ./claim_support.json
```

`--reuse-resolved` により PubMed への再照会は発生しない (NCBI へのリクエスト 0 件)。
