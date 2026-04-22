# 統合前 Baseline 診断レポート

**入力**: `input_References.docx`
**計測時刻**: 2026-04-20 21:03:28
**所要時間**: 0.082 秒

---

## Phase 1 (ブロック分割) 結果

| 指標 | 値 |
|:---|---:|
| 入力文字数 (raw) | 36,963 |
| 前処理後文字数 (cleaned) | 35,556 |
| **検出ブロック数** | **147** |
| Ref番号レンジ | [1, 149] |
| 平均ブロック長 | 236.6 文字 |

## ⚠ 欠落参照

現在の本体では以下の Ref が **検出されません**:

- Ref #40
- Ref #140

## ⚠ 異常に大きいブロック

平均の 1.8 倍以上のサイズ → 隣接ブロックが統合された可能性大:

| Ref No | 文字数 |
|:---:|---:|
| #39 | 556 |

---

## ゴールドスタンダードとの比較

**ゴールド (統合後期待値)**: 149 件
**現在の検出数**: 147 件
**差分**: +2 件

**解釈**: ✗ 基準値がゴールドに 2 件不足。欠落 refs: [40, 140]。統合パッチ適用により +2 件の改善が見込まれる

---

## ブロック先頭サンプル (10件)

| # | 文字数 | 先頭120文字 |
|--:|---:|:---|
| 1 | 287 | Bray, F.; Laversanne, M.; Sung, H.; Ferlay, J.; Siegel, R.L.; Soerjomataram, I.; Jemal, A. Global cancer statistics 2022... |
| 2 | 137 | Wang, Y.; Feng, W. Cancer-related psychosocial challenges. Gen. Psychiatry 2022, 35, e100871, https://doi.org/10.1136/gp... |
| 3 | 276 | Murri, M.B.; Caruso, R.; Christensen, A.P.; Folesani, F.; Nanni, M.G.; Grassi, L. The facets of psychopathology in patie... |
| 4 | 115 | Robieux, L.; Bridou, M. Les Ressources Psychologiques Face Aux Maladies Somatiques Chroniques. PSN 2022, 20, 37–56. |
| 5 | 294 | Lantheaume, S.; Montagne, M.; Shankland, R. Intervention centrée sur les ressources pour réduire les troubles anxieux et... |
| 6 | 148 | Seligman, M.E.P.; Csikszentmihalyi, M. Positive psychology: An introduction.. Am. Psychol. 2000, 55, 5–14, https://doi.o... |
| 7 | 121 | Becker, D.; Marecek, J. Positive Psychology. Theory Psychol. 2008, 18, 591–604, https://doi.org/10.1177/0959354308093397... |
| 8 | 246 | Merino, M.D.; Sánchez-Ortega, M.; Elvira-Flores, E.; Mateo-Rodríguez, I. Centenary Personality: Are There Psychological ... |
| 9 | 185 | Flückiger, C.; Wüsten, G.; Zinbarg, R.E.; Wampold, B.E. Resource Activation: Using Clients’ Own Strengths in Psychothera... |
| 10 | 144 | Hobfoll, S.E. Social and Psychological Resources and Adaptation. Rev. Gen. Psychol. 2002, 6, 307–324, https://doi.org/10... |

---

## 次のアクション

1. この基準値ファイル `baseline_phase1.json` を git にコミットしてください
   (将来の回帰検出の起点になります)
2. `integration/patches/01_split_references_fix.patch` を適用後、
   本スクリプトを再実行し、差分を確認してください
3. 期待される改善: 欠落参照 = 0、検出数 = 149
