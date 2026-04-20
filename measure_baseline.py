#!/usr/bin/env python3
"""
measure_baseline.py — 統合前の本体スキルの挙動を基準値として計測する

目的:
    `integration/patches/*` を適用する前に、現状の main.py が 149 件の
    References.docx をどう処理するかを測定し、診断レポート (JSON + Markdown) を
    生成する。

    統合後に同スクリプトを再実行することで、改善点・退行点を定量的に比較
    できる。

使い方:
    cd pubmed-reference-resolver/
    python3 measure_baseline.py tests/fixtures/mdpi_149refs/ baseline/

    出力:
      baseline/baseline_phase1.json     ← Phase 1 の detect 結果
      baseline/baseline_report.md       ← 診断レポート (人間向け)

LLM (Anthropic API) が利用可能な場合は Phase 2 も実行される。
未設定の場合は Phase 1 のみで終了 (エラーにはしない)。

Phase 3/4 (PubMed カスケード + 最終合成) は敢えてスキップする。
これらは network 依存で非決定的なため、基準値としては不適。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


def run_phase1_baseline(
    input_docx: Path, main_module: Any
) -> dict[str, Any]:
    """Phase 1 (ブロック分割) のみを走らせて現状の挙動を記録する。"""
    t0 = time.time()
    raw, source_type = main_module.extract_text(input_docx)
    ln_report = main_module.detect_line_numbers(raw)
    cleaned, trace = main_module.preprocess(raw, ln_report)
    blocks = main_module.split_references(cleaned)
    elapsed = time.time() - t0

    ref_nos = sorted([b.ref_no for b in blocks])
    missing = [n for n in range(1, max(ref_nos) + 1) if n not in ref_nos]
    duplicate = [n for n in ref_nos if ref_nos.count(n) > 1]

    # 統合されてしまったブロック (char_length が異常に大きいもの) を検出
    lengths = [b.char_length for b in blocks]
    avg_len = sum(lengths) / len(lengths) if lengths else 0
    suspicious = [
        {"ref_no": b.ref_no, "char_length": b.char_length}
        for b in blocks
        if b.char_length > avg_len * 1.8
    ]

    return {
        "input_file": str(input_docx.name),
        "source_type": source_type,
        "stage1_raw_length": len(raw),
        "stage2_cleaned_length": len(cleaned),
        "line_number_detection": {
            "detected": ln_report.detected,
            "min_val": ln_report.min_val,
            "max_val": ln_report.max_val,
            "count_removed": getattr(ln_report, "count_removed", None),
        },
        "preprocess_trace": {
            "hyphen_bridge_rescued": getattr(trace, "hyphen_bridge_rescued", None),
            "soft_linebreaks_joined": getattr(trace, "soft_linebreaks_joined", None),
            "standalone_line_numbers_removed": getattr(
                trace, "standalone_line_numbers_removed", None
            ),
        },
        "phase1_results": {
            "blocks_detected": len(blocks),
            "ref_nos_range": [min(ref_nos), max(ref_nos)] if ref_nos else None,
            "missing_ref_nos": missing,
            "duplicate_ref_nos": duplicate,
            "avg_block_char_length": round(avg_len, 1),
            "suspicious_oversized_blocks": suspicious,
        },
        "blocks_preview": [
            {
                "ref_no": b.ref_no,
                "char_length": b.char_length,
                "raw_text_head": b.raw_text[:120] + ("..." if len(b.raw_text) > 120 else ""),
            }
            for b in blocks[:10]
        ],
        "elapsed_seconds": round(elapsed, 3),
    }


def compare_with_gold(
    baseline: dict[str, Any], gold_phase2_path: Path
) -> dict[str, Any]:
    """ゴールドスタンダード (統合後の期待値) との差分サマリを生成する。"""
    if not gold_phase2_path.exists():
        return {"comparison_skipped": "gold file not found"}

    gold = json.loads(gold_phase2_path.read_text(encoding="utf-8"))
    gold_structured = gold.get("stage3_structured", gold)
    gold_ref_nos = sorted([s["ref_no"] for s in gold_structured])

    baseline_blocks_detected = baseline["phase1_results"]["blocks_detected"]
    gold_blocks_expected = len(gold_ref_nos)
    delta = gold_blocks_expected - baseline_blocks_detected

    missing_in_baseline = baseline["phase1_results"]["missing_ref_nos"]

    return {
        "gold_ref_count": gold_blocks_expected,
        "baseline_detected": baseline_blocks_detected,
        "delta": delta,
        "refs_missing_in_baseline": missing_in_baseline,
        "interpretation": _interpret_delta(delta, missing_in_baseline),
    }


def _interpret_delta(delta: int, missing: list[int]) -> str:
    if delta == 0 and not missing:
        return "✓ 基準値 = ゴールド (統合による検出数改善なし、既にクリーン)"
    elif delta > 0:
        return (
            f"✗ 基準値がゴールドに {delta} 件不足。"
            f"欠落 refs: {missing}。"
            f"統合パッチ適用により +{delta} 件の改善が見込まれる"
        )
    elif delta < 0:
        return (
            f"! 基準値がゴールドより {abs(delta)} 件多い。"
            f"ゴールドデータの検証または本体の退行を要確認"
        )
    return "?"


def generate_markdown_report(
    baseline: dict[str, Any], comparison: dict[str, Any]
) -> str:
    """人間可読な診断レポートを生成する。"""
    p1 = baseline["phase1_results"]
    lines = [
        "# 統合前 Baseline 診断レポート",
        "",
        f"**入力**: `{baseline['input_file']}`",
        f"**計測時刻**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**所要時間**: {baseline['elapsed_seconds']} 秒",
        "",
        "---",
        "",
        "## Phase 1 (ブロック分割) 結果",
        "",
        "| 指標 | 値 |",
        "|:---|---:|",
        f"| 入力文字数 (raw) | {baseline['stage1_raw_length']:,} |",
        f"| 前処理後文字数 (cleaned) | {baseline['stage2_cleaned_length']:,} |",
        f"| **検出ブロック数** | **{p1['blocks_detected']}** |",
        f"| Ref番号レンジ | {p1['ref_nos_range']} |",
        f"| 平均ブロック長 | {p1['avg_block_char_length']} 文字 |",
        "",
    ]

    if p1["missing_ref_nos"]:
        lines.extend([
            "## ⚠ 欠落参照",
            "",
            f"現在の本体では以下の Ref が **検出されません**:",
            "",
        ])
        for n in p1["missing_ref_nos"]:
            lines.append(f"- Ref #{n}")
        lines.append("")

    if p1["duplicate_ref_nos"]:
        lines.extend([
            "## ⚠ 重複検出",
            "",
            f"同じ Ref 番号が複数回検出されました: {p1['duplicate_ref_nos']}",
            "",
        ])

    if p1["suspicious_oversized_blocks"]:
        lines.extend([
            "## ⚠ 異常に大きいブロック",
            "",
            "平均の 1.8 倍以上のサイズ → 隣接ブロックが統合された可能性大:",
            "",
            "| Ref No | 文字数 |",
            "|:---:|---:|",
        ])
        for s in p1["suspicious_oversized_blocks"]:
            lines.append(f"| #{s['ref_no']} | {s['char_length']:,} |")
        lines.append("")

    if "gold_ref_count" in comparison:
        lines.extend([
            "---",
            "",
            "## ゴールドスタンダードとの比較",
            "",
            f"**ゴールド (統合後期待値)**: {comparison['gold_ref_count']} 件",
            f"**現在の検出数**: {comparison['baseline_detected']} 件",
            f"**差分**: {comparison['delta']:+d} 件",
            "",
            f"**解釈**: {comparison['interpretation']}",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## ブロック先頭サンプル (10件)",
        "",
        "| # | 文字数 | 先頭120文字 |",
        "|--:|---:|:---|",
    ])
    for b in baseline["blocks_preview"]:
        head = b["raw_text_head"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {b['ref_no']} | {b['char_length']} | {head} |")
    lines.append("")

    lines.extend([
        "---",
        "",
        "## 次のアクション",
        "",
        "1. この基準値ファイル `baseline_phase1.json` を git にコミットしてください",
        "   (将来の回帰検出の起点になります)",
        "2. `integration/patches/01_split_references_fix.patch` を適用後、",
        "   本スクリプトを再実行し、差分を確認してください",
        "3. 期待される改善: 欠落参照 = 0、検出数 = 149",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="統合前の本体スキルの挙動を計測する"
    )
    parser.add_argument(
        "fixture_dir", type=Path,
        help="tests/fixtures/mdpi_149refs/ ディレクトリのパス",
    )
    parser.add_argument(
        "output_dir", type=Path,
        help="baseline/ などの出力先ディレクトリ",
    )
    args = parser.parse_args()

    input_docx = args.fixture_dir / "input_References.docx"
    gold_phase2 = args.fixture_dir / "expected_phase2_structured.json"
    if not input_docx.exists():
        print(f"ERROR: 入力が見つかりません: {input_docx}", file=sys.stderr)
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # main.py を動的 import (カレントディレクトリが repo root の想定)
    sys.path.insert(0, str(Path.cwd()))
    try:
        import main as main_module
    except ImportError as e:
        print(f"ERROR: main.py を import できません: {e}", file=sys.stderr)
        return 1

    print(f"[1/3] Phase 1 を計測中: {input_docx.name}...")
    baseline = run_phase1_baseline(input_docx, main_module)
    print(
        f"      完了: {baseline['phase1_results']['blocks_detected']} ブロック検出, "
        f"欠落 {len(baseline['phase1_results']['missing_ref_nos'])} 件"
    )

    print(f"[2/3] ゴールドとの比較中...")
    comparison = compare_with_gold(baseline, gold_phase2)
    if "interpretation" in comparison:
        print(f"      {comparison['interpretation']}")

    print(f"[3/3] レポートを書き出し中...")
    baseline["comparison"] = comparison

    json_out = args.output_dir / "baseline_phase1.json"
    json_out.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"      JSON: {json_out}")

    md_out = args.output_dir / "baseline_report.md"
    md_out.write_text(
        generate_markdown_report(baseline, comparison), encoding="utf-8"
    )
    print(f"      Markdown: {md_out}")

    print("\n✓ 基準値計測完了")
    return 0


if __name__ == "__main__":
    sys.exit(main())
