# 引用スタイルの代表例 (LLM構造化のリファレンス)

本スキルは正規表現で引用スタイルを判別せず、**LLM (Claude Sonnet 4.6) に意味的に解釈させる**。
このドキュメントは、どのスタイルが入力されても同じ構造化JSONを返すよう LLM プロンプトをチューニングするための参照材料。

## 1. Vancouver (NIH 推奨、医学分野の標準)

```
1. Smith J, Lee K. Title of the article. N Engl J Med. 2020;382(5):123-30.
```

特徴:
- 著者は姓 + イニシャル (カンマ区切り)
- 雑誌は省略形 + ピリオド
- 年とボリュームはセミコロン区切り
- 号は括弧内

## 2. AMA (American Medical Association)

```
Smith J, Lee K. Title of the article. N Engl J Med. 2020;382(5):123-130. doi:10.1056/NEJMoa2001234
```

特徴:
- Vancouver とほぼ同一だが、ページは省略なし (123-130)
- DOI が明示的に付記される

## 3. APA (American Psychological Association, 心理学分野)

```
Smith, J., & Lee, K. (2020). Title of the article. New England Journal of Medicine, 382(5), 123-130. https://doi.org/10.1056/NEJMoa2001234
```

特徴:
- 著者は姓, イニシャル. の形式
- 最終著者の前に `&`
- 年は括弧内
- 雑誌名は**フルタイトル**
- ボリューム(号), ページ (カンマ区切り)
- DOI は URL 形式

## 4. Harvard (英国系社会科学)

```
Smith, J. and Lee, K., 2020. Title of the article. New England Journal of Medicine, 382(5), pp.123-130.
```

特徴:
- 著者は `and` で接続
- 年がピリオド区切り
- ページ は `pp.` プレフィックス

## 5. Chicago (Notes & Bibliography)

```
Smith, John, and Kim Lee. "Title of the Article." New England Journal of Medicine 382, no. 5 (2020): 123-30.
```

特徴:
- 著者はフルネーム
- タイトルは引用符で囲む
- 号は `no. 5` の形式
- 年は括弧内

## 6. Nature (Nature系雑誌)

```
Smith, J. & Lee, K. Title of the article. Nat. Med. 382, 123-130 (2020).
```

特徴:
- 著者は `&` で接続 (最終著者前)
- 雑誌は省略形
- **ボリューム, ページ (年)** の順序
- カンマ区切り

## 7. Cell (Cell Press)

```
Smith, J., and Lee, K. (2020). Title of the article. New England Journal of Medicine 382, 123-130.
```

特徴:
- APA 類似だが、著者は `and` で接続
- 年が括弧内
- 雑誌とボリュームが空白区切り (カンマなし)

## 8. MDPI (本スキル検証サンプルで使用)

```
1. Smith, J.; Lee, K. Title of the article. N. Engl. J. Med. 2020, 382, 123-130, https://doi.org/10.1056/NEJMoa2001234.
```

特徴:
- 著者間はセミコロン `;`
- 雑誌省略形にピリオド
- 年, ボリューム, ページ がカンマ区切り
- DOI は URL 形式で末尾

## 9. IEEE (工学系)

```
[1] J. Smith and K. Lee, "Title of the article," N. Engl. J. Med., vol. 382, no. 5, pp. 123-130, 2020.
```

特徴:
- 参照番号は角括弧 `[1]`
- タイトルは引用符
- `vol.`, `no.`, `pp.` プレフィックス

## 10. BibTeX @article

```
@article{smith2020title,
  author = {Smith, John and Lee, Kim},
  title = {Title of the article},
  journal = {New England Journal of Medicine},
  volume = {382},
  number = {5},
  pages = {123--130},
  year = {2020},
  doi = {10.1056/NEJMoa2001234}
}
```

特徴:
- キー-値形式
- 通常は参照リストに含まれないが、PDF 付録等で見かける可能性あり

## スタイル判別の要点 (LLM用)

- セミコロン区切りの著者 → MDPI / Vancouver の可能性
- 引用符で囲まれたタイトル → Chicago / IEEE
- 括弧付き年号が前置 → APA / Cell / Nature (位置で判別)
- DOI URL 形式 (`https://doi.org/`) → MDPI / APA に多い
- DOI プレフィックス (`doi:`) → AMA に多い

LLM は上記要素を参考に、フィールドの**意味的役割**で抽出すること。スタイル名そのものを識別する必要はない。
