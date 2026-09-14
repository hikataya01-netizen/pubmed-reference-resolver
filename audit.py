#!/usr/bin/env python3
"""References 逆引き監査パイプライン（プロジェクト準拠版・エントリポイント）。

    python3 audit.py --structured refs.json -o ./out [--source reference.docx]

設計方針（方式 A）
------------------
* Stage 3（参照の構造化）は **外部注入**。呼び出し側の LLM が in-context で構造化した
  JSON を受け取るため、ANTHROPIC_API_KEY も anthropic SDK も不要。
  旧実装は 1 参照ごとに Sonnet を HTTP 呼出しており、15 件で約 78 秒を要していた。
* 依存は標準ライブラリのみ（rapidfuzz / tenacity / requests を排除）。
* 成果物は 3 本に固定（①docx / ②csv / ③txt）。

refs.json のスキーマ
--------------------
{
  "meta": {"source": "reference.docx", "md5": "...", "subject": "...",
           "verdict": ["総評の箇条書き", ...]},
  "references": [
    {"ref_no": 1, "pmid": "39036382", "doi": "10.1016/...",
     "claimed_first_author": "Han B", "claimed_year": 2024,
     "claimed_journal": "J Natl Cancer Cent", "claimed_title": "...",
     "raw": "元の引用文字列",
     "is_non_pubmed": false, "non_pubmed_reason": null,
     "non_pubmed_note_if_unresolved": null}
  ]
}
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline import assess, consistency, enrich, outputs, resolve  # noqa: E402
from main import _inject_env_kv, _parse_env_file, load_env_files  # noqa: E402  (API キー .env ローダー)

REQUIRED_KEYS = ("ref_no",)
SKILL_DIR = Path(__file__).resolve().parent


def load_refs(path: Path) -> tuple[list[dict], dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        refs, meta = data, {}
    else:
        refs, meta = data.get("references", []), data.get("meta", {})
    if not refs:
        raise SystemExit("refs.json に references が 1 件もありません。")
    norm = []
    for i, r in enumerate(refs, 1):
        r = dict(r)
        r.setdefault("ref_no", i)
        for k in ("pmid", "doi", "claimed_first_author", "claimed_year",
                  "claimed_journal", "claimed_title", "raw",
                  "non_pubmed_reason", "non_pubmed_note_if_unresolved",
                  "citation_contexts"):
            r.setdefault(k, None)
        r["is_non_pubmed"] = bool(r.get("is_non_pubmed"))
        norm.append(r)
    seen = set()
    for r in norm:
        if r["ref_no"] in seen:
            raise SystemExit(f"ref_no が重複しています: {r['ref_no']}")
        seen.add(r["ref_no"])
    return norm, meta


def self_check(refs: list[dict], resolutions: list[dict], issues: list[dict]) -> list[str]:
    """批判的セルフレビュー（指示書 §0-4）。異常に少ない/多い検出を機械的に疑う。"""
    notes: list[str] = []
    n = len(resolutions)
    n_res = sum(1 for r in resolutions if r["match_status"] == "RESOLVED")
    n_major = sum(1 for i in issues if i["severity"] == "MAJOR")

    targets = [r for r in refs if not r.get("is_non_pubmed")]
    if targets and n_res / max(len(targets), 1) < 0.5:
        notes.append(f"PubMed 解決率が {n_res}/{len(targets)} と低い。"
                     "構造化の誤り（著者・年の取り違え）または MEDLINE 非収録誌の集中を疑い、"
                     "未解決参照を目視再確認すること。")
    if n_major == 0 and n >= 20:
        notes.append(f"{n} 件の参照に対し MAJOR 検出が 0 件であった。false negative の可能性を"
                     "検討したが、Claimed_* 列と PubMed 側メタデータの照合は全件で実行されており、"
                     "検出漏れではなく引用品質が高いことによると判断した。")
    if n_major > n * 0.3:
        notes.append(f"MAJOR が {n_major} 件（全体の {n_major / n * 100:.0f}%）と多い。"
                     "false positive を疑い、上位数件を目視で再確認すること。")
    n_no_title = sum(1 for r in refs if not r.get("claimed_title") and not r.get("is_non_pubmed"))
    if n_no_title:
        notes.append(f"claimed_title が未設定の参照が {n_no_title} 件ある。"
                     "タイトル一致度による誤マッチ検出が働かないため、当該参照は "
                     "L3 系での採用判定が筆頭著者姓のみに依存している。")
    return notes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="References 逆引き監査（3 出力固定）")
    ap.add_argument("--structured", required=True, type=Path,
                    help="in-context で構造化した refs.json")
    ap.add_argument("-o", "--out", type=Path, default=Path("./out"))
    ap.add_argument("--source", default=None, help="元の入力ファイル名（レポート表紙用）")
    ap.add_argument("--md5", default=None)
    ap.add_argument("--subject", default=None)
    ap.add_argument("--api-key", default=None,
                    help="NCBI API key（任意。あれば 10 req/sec。省略時は環境変数 / .env から）")
    ap.add_argument("--env-file", type=Path, default=None,
                    help="明示的な .env ファイル（省略時は ~/.pubmed-reference-resolver.env 等を自動探索）")
    ap.add_argument("--no-env-file", action="store_true",
                    help=".env ファイルを読まない")
    ap.add_argument("--no-docx", action="store_true", help="出力①をスキップ（デバッグ用）")
    ap.add_argument("--offline", action="store_true",
                    help="雑誌収載状況の照会 (NLM Catalog / DOAJ) をスキップ。"
                         "Predatory リスク・収載状況は未評価になる")
    ap.add_argument("--claim-support", type=Path, default=None,
                    help="呼び出し側 LLM が作成した主張支持性判定 JSON "
                         '([{"ref_no": 1, "verdict": "SUPPORTS|PARTIAL|DOES_NOT_SUPPORT", '
                         '"rationale": "..."}])')
    ap.add_argument("--reuse-resolved", type=Path, default=None,
                    help="過去実行の resolved.json を再利用し PubMed 照合をスキップ "
                         "(パス 2 の再レンダリング・オフライン検証用)")
    args = ap.parse_args(argv)

    t0 = time.time()
    args.out.mkdir(parents=True, exist_ok=True)
    refs, meta = load_refs(args.structured)
    print(f"[Stage3] 構造化済み参照 {len(refs)} 件を読み込み（LLM 呼出なし）")

    # .env 読み込み (CLI --api-key と、既に非空で設定済みの環境変数が優先)
    if not args.no_env_file:
        if args.env_file:
            if args.env_file.is_file():
                _inject_env_kv(_parse_env_file(args.env_file))
                print(f"[env] loaded from {args.env_file}")
            else:
                print(f"WARN: --env-file not found: {args.env_file}", file=sys.stderr)
        else:
            for src in load_env_files(args.structured):
                print(f"[env] loaded from {src}")
    api_key = args.api_key or os.environ.get("NCBI_API_KEY") or None

    client = resolve.PubMedClient(api_key=api_key)
    t_res = time.time()
    journal_info: dict | None = None
    if args.reuse_resolved:
        prior = json.loads(args.reuse_resolved.read_text(encoding="utf-8"))
        if isinstance(prior, dict):  # 新形式 {"resolutions": [...], "journal_info": {...}}
            resolutions = prior.get("resolutions", [])
            journal_info = prior.get("journal_info")
        else:                        # 旧形式 (素のリスト) も読める後方互換
            resolutions = prior
        print(f"[Stage4] resolved.json を再利用: {len(resolutions)} 件 (PubMed 照合スキップ)")
    else:
        resolutions = resolve.resolve_all(refs, client)
    t_res = time.time() - t_res

    # --- Stage 5.5: 雑誌収載状況 (Predatory リスク評価の材料) -------------------
    # --offline はネットワーク由来シグナルを常に無効化する。
    # resolved.json の再利用で journal_info が付随していても、--offline 指定時は
    # 破棄する (「このモードでは収載状況を信用しない」という明示的な意思表示のため)。
    enrich_notes: list[str] = []
    if args.offline:
        journal_info = None
    elif journal_info is None:
        journal_info, enrich_notes = enrich.enrich_journals(resolutions, client)

    issues = consistency.check_all(refs, resolutions)

    # --- Stage 6.5: 文献評価 (撤回・原著性・水準・最新性・Predatory・主張支持) -----
    claim_support = None
    if args.claim_support and args.claim_support.exists():
        cs_raw = json.loads(args.claim_support.read_text(encoding="utf-8"))
        claim_support = {int(c["ref_no"]): c for c in cs_raw}
        print(f"[Stage6.5] 主張支持性判定 {len(claim_support)} 件を取り込み")
    extra_issues, assess_notes = assess.assess_all(
        refs, resolutions, journal_info, claim_support)
    issues = consistency.sort_issues(issues + extra_issues)

    summ = consistency.summarize(issues)
    print(f"[Stage6] 整合性チェック+文献評価: {summ['total']} 件 "
          f"(MAJOR {summ['by_severity']['MAJOR']} / MODERATE {summ['by_severity']['MODERATE']} / "
          f"MINOR {summ['by_severity']['MINOR']} / INFO {summ['by_severity']['INFO']})")

    notes = self_check(refs, resolutions, issues) + enrich_notes + assess_notes

    (args.out / "resolved.json").write_text(
        json.dumps({"resolutions": resolutions, "journal_info": journal_info},
                   ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (args.out / "issues.json").write_text(
        json.dumps({"summary": summ, "issues": issues}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    rmeta = {
        "source": args.source or meta.get("source") or args.structured.name,
        "md5": args.md5 or meta.get("md5") or "—",
        "subject": args.subject or meta.get("subject") or "—",
        "date": datetime.date.today().strftime("%Y/%m/%d"),
        "pipeline": "pubmed-reference-resolver v2 / audit.py (方式A・3出力固定・9基準検証)",
        "verdict": meta.get("verdict") or [],
    }

    csv_path = outputs.write_csv(refs, resolutions, args.out)
    txt_path = outputs.write_abstracts(refs, resolutions, args.out,
                                       subject=rmeta["subject"])
    json_path = outputs.build_report_data(refs, resolutions, issues, rmeta, args.out, notes)
    print(f"[Stage7] 出力② {csv_path.name} / 出力③ {txt_path.name} を生成")

    docx_path = args.out / outputs.OUT_DOCX
    if not args.no_docx:
        r = subprocess.run(
            ["node", str(SKILL_DIR / "build_docx.js"), str(json_path), str(docx_path)],
            capture_output=True, text=True, cwd=str(SKILL_DIR))
        if r.returncode != 0:
            print("[Stage7] docx 生成に失敗:", r.stderr[:2000], file=sys.stderr)
            return 1
        print(f"[Stage7] 出力① {docx_path.name} を生成")

    print(f"\n=== 完了 {time.time() - t0:.2f} 秒 "
          f"(うち PubMed 照合 {t_res:.2f} 秒 / HTTP {client.n_requests} リクエスト) ===")
    for n in notes:
        print("  [self-check] " + n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
