# APA 45-ref Golden Fixture Implementation Plan (Day16)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PMC OA 3 領域 (Psychology / Nursing / Public Health) から計 45 件の APA 7 参考文献を抽出して統合 docx を組成し、Phase 1 deterministic golden + Phase 3/4 baseline + Day15 三分類 audit baseline を凍結することで、Day9 Vancouver Veto の APA 適用 regression 保護と LLM 経由 parsing の document-of-record を実現する.

**Architecture:** Day11 で確立されたハイブリッド命名規約 (`expected_*` deterministic / `baseline_*` document-of-record) を完全踏襲. 新規 `tools/build_apa_fixture.py` で JATS XML → APA 7 plain text 変換 + python-docx で番号付き段落生成 (再現可能スクリプト). production code (`main.py`, `mdpi_parser.py`, `crossref_check.py`, `nlm_catalog_check.py`, `three_class_classifier.py`) は改修しない見込み (Vancouver Veto で APA `(YYYY)` は既に LLM 経由).

**Tech Stack:** Python 3.11+ / uv / pytest / python-docx / urllib (NCBI E-utilities) / Claude Sonnet 4.6 (baseline 生成のみ 1 回) / Crossref + NLM Catalog (Day15 audit logic).

**SPEC**: `docs/sessions/day16/SPEC_apa_45refs_fixture.md` (commit `4f1181d`)

---

## File Structure

### 新規作成

| ファイル | 責務 |
|:---|:---|
| `tools/build_apa_fixture.py` | JATS XML fetch (NCBI E-utilities efetch) + APA 7 plain text 変換 + python-docx 統合 docx 生成 |
| `tests/fixtures/apa_45refs/input_References.docx` | 統合 docx (45 番号付き段落、3 領域混在) |
| `tests/fixtures/apa_45refs/expected_phase1_intermediate.json` | parser-only Phase 1 出力 (byte-strict golden) |
| `tests/fixtures/apa_45refs/baseline_phase3_resolved.json` | LLM + PubMed Phase 3 出力 (document-of-record) |
| `tests/fixtures/apa_45refs/baseline_report.md` | Phase 4 audit report (document-of-record) |
| `tests/fixtures/apa_45refs/baseline_three_class_classification.json` | Day15 三分類 audit sidecar (document-of-record) |
| `tests/fixtures/apa_45refs/README.md` | fixture の由来・規約・選定 3 論文 citation + LICENSE 明記 |
| `tests/test_integration_apa_45refs.py` | 8 tests (base 5 + APA 固有 3) |
| `docs/sessions/day16/README.md` | Day16 セッション index |
| `docs/sessions/day16/DAY16_LESSONS_LEARNED.md` | Day16 末アーカイブ + 教訓 |

### 修正 (optional)

| ファイル | 修正内容 |
|:---|:---|
| `skill_package/references/USAGE_QUICKSTART.md` | バージョン 1.3 → 1.4 bump、APA 系も検証済みであることを §X changelog に追記 |

### 改変なし (確認のみ)

`main.py`, `mdpi_parser.py`, `crossref_check.py`, `nlm_catalog_check.py`, `three_class_classifier.py` — 既存 production code 全般

---

## Task 0: PMC OA 論文 3 本の選定 (ユーザー承認 gate)

**Files:**
- Update: `docs/sessions/day16/SPEC_apa_45refs_fixture.md:94-100` (§3.2 選定確定論文 table)

- [ ] **Step 1: NCBI esearch で 3 領域候補をリストアップ**

3 領域それぞれで以下 query を `curl` または `nlm_catalog_check.py` の esearch helper で実行 (NCBI key 利用、rate limit 配慮):

```bash
# Psychology
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term=(\"Psychooncology\"%5BJournal%5D)+AND+(\"open+access\"%5BFilter%5D)+AND+review%5BPT%5D&retmax=10&api_key=$NCBI_API_KEY"

# Nursing
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term=(\"J+Adv+Nurs\"%5BJournal%5D)+AND+(\"open+access\"%5BFilter%5D)+AND+review%5BPT%5D&retmax=10&api_key=$NCBI_API_KEY"

# Public Health
curl -s "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&term=(\"BMC+Public+Health\"%5BJournal%5D)+AND+(\"open+access\"%5BFilter%5D)+AND+review%5BPT%5D&retmax=10&api_key=$NCBI_API_KEY"
```

- [ ] **Step 2: 各領域から 1 本ずつ候補絞り込み**

絞り込み条件:
- 過去 5 年以内 (2020 以降) 出版
- reference list が 30 件以上 (先頭 15 件抽出のため)
- **APA 第 7 版**採用 (instructions to authors または PMC full-text の `<ref-list>` 構造で確認)
- `<pmc-articleset>` から `<article-id pub-id-type="pmc">` と CC BY ライセンスを確認

候補 3 本を Markdown table 形式で SPEC §3.2 に書き込む案を作成:

```markdown
| 領域 | PMC ID | DOI | Journal | 出版年 | LICENSE |
|:---|:---|:---|:---|:---:|:---|
| Psychology | PMCXXXXXXX | 10.XXXX/... | Psycho-Oncology | 2023 | CC BY 4.0 |
| Nursing | PMCXXXXXXX | 10.XXXX/... | J Adv Nurs | 2024 | CC BY 4.0 |
| Public Health | PMCXXXXXXX | 10.XXXX/... | BMC Public Health | 2024 | CC BY 4.0 |
```

- [ ] **Step 3: 候補をユーザーに提示し承認を取得**

候補 3 本をユーザーに提示し、各 source の Title + Journal + Year + PMC ID + LICENSE + reference 件数を表示. ユーザー承認後に Step 4 へ.

⚠️ **ユーザー却下があれば Step 1 から query を変更して再選定** (例: Journal を BMC Palliat Care、J Pain Symptom Manage 等に変更).

- [ ] **Step 4: SPEC §3.2 を更新 (TBD → 確定値)**

`docs/sessions/day16/SPEC_apa_45refs_fixture.md` の 94-100 行の TBD table を承認確定値で置換し、別 commit ではなく次の Task 1 commit に同梱.

---

## Task 1: build_apa_fixture.py スクリプト作成

**Files:**
- Create: `tools/build_apa_fixture.py`
- Create: `tools/__init__.py` (空、Python パッケージ化)
- Create: `tests/fixtures/apa_45refs/` (ディレクトリのみ、`.gitkeep` 不要)

- [ ] **Step 1: tools/ ディレクトリと __init__.py を作成**

```bash
mkdir -p tools tests/fixtures/apa_45refs
touch tools/__init__.py
```

- [ ] **Step 2: build_apa_fixture.py 本体を作成**

`tools/build_apa_fixture.py` に以下を書き込む:

```python
"""build_apa_fixture.py — PMC OA 3 論文から APA 45-ref fixture を組成する.

Usage:
    uv run python tools/build_apa_fixture.py \\
        --psychology PMCXXXXXXX \\
        --nursing PMCXXXXXXX \\
        --public-health PMCXXXXXXX \\
        --output tests/fixtures/apa_45refs/input_References.docx \\
        --refs-per-paper 15

実行手順:
    1. NCBI E-utilities efetch で 3 論文の PMC XML を取得 (.cache/ にキャッシュ)
    2. 各 XML の <ref-list> から先頭 N 件を抽出
    3. JATS の <element-citation> / <mixed-citation> を APA 7 plain text に変換
    4. python-docx で番号付き段落 (1. ~ 45.) として統合 docx 生成

依存: urllib (標準ライブラリ) / python-docx / xml.etree.ElementTree (標準)

Day16 Phase 0a の中核. 再現性のため tools/ にコミットする.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

CACHE_DIR = REPO_ROOT / ".cache" / "pmc_xml"
NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def fetch_pmc_xml(pmc_id: str, api_key: str | None = None) -> str:
    """PMC ID から full-text XML を取得 (キャッシュ付き).

    Args:
        pmc_id: "PMC12345678" 形式
        api_key: NCBI_API_KEY (rate limit 緩和)

    Returns:
        XML 文字列
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{pmc_id}.xml"
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")

    params = {"db": "pmc", "id": pmc_id, "rettype": "xml"}
    if api_key:
        params["api_key"] = api_key
    url = f"{NCBI_BASE}/efetch.fcgi?{urllib.parse.urlencode(params)}"
    print(f"[fetch] {url[:80]}...")
    with urllib.request.urlopen(url, timeout=30) as resp:
        xml = resp.read().decode("utf-8")
    cache_path.write_text(xml, encoding="utf-8")
    time.sleep(0.34)  # NCBI rate limit: 3 req/sec without key, 10 with key
    return xml


def extract_references(xml: str, limit: int = 15) -> list[dict[str, str]]:
    """PMC XML から先頭 limit 件の reference を抽出.

    Returns:
        [{"label": "1", "raw": "..."}, ...] のリスト
    """
    root = ET.fromstring(xml)
    ns = {"jats": "http://jats.nlm.nih.gov"}
    refs = []
    # ref-list は article 配下 (jats: namespace) または non-namespaced
    ref_elements = root.iter("ref") or []
    for i, ref_el in enumerate(ref_elements):
        if i >= limit:
            break
        # element-citation or mixed-citation
        cit = ref_el.find("element-citation") or ref_el.find("mixed-citation")
        if cit is None:
            continue
        plain_text = format_as_apa7(cit)
        if plain_text:
            refs.append({"label": str(i + 1), "raw": plain_text})
    return refs


def format_as_apa7(cit_el: ET.Element) -> str:
    """JATS <element-citation> / <mixed-citation> を APA 7 plain text に変換.

    APA 7 形式例:
        Smith, J. A., & Brown, K. L. (2023). Title of paper. Journal Name, 12(3), 45-67. https://doi.org/10.1234/xyz

    mixed-citation はそのままテキスト抽出 (元論文の APA 表記を流用).
    element-citation は構造化フィールドから再組成.
    """
    if cit_el.tag.endswith("mixed-citation"):
        # mixed-citation は inline text + element の混在 → text accumulate
        return _collect_text(cit_el).strip()

    # element-citation: structured fields
    authors = _format_authors(cit_el)
    year_el = cit_el.find("year")
    year = year_el.text.strip() if year_el is not None and year_el.text else "n.d."
    title_el = cit_el.find("article-title") or cit_el.find("chapter-title")
    title = (title_el.text or "").strip() if title_el is not None else ""
    journal_el = cit_el.find("source")
    journal = (journal_el.text or "").strip() if journal_el is not None else ""
    vol_el = cit_el.find("volume")
    vol = (vol_el.text or "").strip() if vol_el is not None else ""
    issue_el = cit_el.find("issue")
    issue = (issue_el.text or "").strip() if issue_el is not None else ""
    fpage_el = cit_el.find("fpage")
    fpage = (fpage_el.text or "").strip() if fpage_el is not None else ""
    lpage_el = cit_el.find("lpage")
    lpage = (lpage_el.text or "").strip() if lpage_el is not None else ""
    doi_el = cit_el.find("pub-id[@pub-id-type='doi']")
    doi = (doi_el.text or "").strip() if doi_el is not None else ""

    parts = [f"{authors} ({year}). {title}"]
    if not title.endswith("."):
        parts[-1] += "."
    if journal:
        vol_part = f", {vol}" if vol else ""
        issue_part = f"({issue})" if issue else ""
        page_part = f", {fpage}-{lpage}" if fpage and lpage else (f", {fpage}" if fpage else "")
        parts.append(f" {journal}{vol_part}{issue_part}{page_part}.")
    if doi:
        parts.append(f" https://doi.org/{doi}")
    return "".join(parts)


def _format_authors(cit_el: ET.Element) -> str:
    """JATS person-group から APA 7 著者リストを生成.

    例: "Smith, J. A., & Brown, K. L."
        "Smith, J. A., Brown, K. L., & Jones, M. P."
    """
    persons = cit_el.findall(".//person-group/name") or cit_el.findall(".//name")
    if not persons:
        return ""
    formatted = []
    for name in persons:
        surname = name.findtext("surname", "").strip()
        given = name.findtext("given-names", "").strip()
        if not surname:
            continue
        # given names を initial 化: "John Anthony" → "J. A."
        initials = ". ".join(g[0] for g in given.split() if g) + ("." if given else "")
        formatted.append(f"{surname}, {initials}".strip())
    if len(formatted) == 0:
        return ""
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) == 2:
        return f"{formatted[0]}, & {formatted[1]}"
    return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"


def _collect_text(el: ET.Element) -> str:
    """Element 配下のすべての text を順序通り連結 (mixed-citation 用)."""
    parts = []
    if el.text:
        parts.append(el.text)
    for child in el:
        parts.append(_collect_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def build_docx(refs: list[dict[str, str]], output_path: Path) -> None:
    """45 件 refs を番号付き段落として python-docx で docx 生成."""
    from docx import Document  # type: ignore

    doc = Document()
    doc.add_heading("References", level=1)
    for i, ref in enumerate(refs, start=1):
        p = doc.add_paragraph()
        p.add_run(f"{i}. {ref['raw']}")
    doc.save(output_path)
    print(f"[write] {output_path} ({len(refs)} refs)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build APA 45-ref fixture docx")
    ap.add_argument("--psychology", required=True, help="PMC ID (例: PMC10234567)")
    ap.add_argument("--nursing", required=True, help="PMC ID")
    ap.add_argument("--public-health", required=True, help="PMC ID")
    ap.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "tests/fixtures/apa_45refs/input_References.docx",
        help="出力 docx パス",
    )
    ap.add_argument("--refs-per-paper", type=int, default=15)
    args = ap.parse_args(argv)

    api_key = os.environ.get("NCBI_API_KEY")
    all_refs: list[dict[str, str]] = []
    for label, pmc_id in [
        ("psychology", args.psychology),
        ("nursing", args.nursing),
        ("public_health", args.public_health),
    ]:
        print(f"[{label}] fetching {pmc_id}...")
        xml = fetch_pmc_xml(pmc_id, api_key=api_key)
        refs = extract_references(xml, limit=args.refs_per_paper)
        print(f"[{label}] extracted {len(refs)} refs")
        all_refs.extend(refs)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    build_docx(all_refs, args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: dry-run でヘルプ表示確認**

Run: `uv run python tools/build_apa_fixture.py --help`
Expected: argparse のヘルプメッセージが表示される (`--psychology`, `--nursing`, `--public-health` フラグが見える)

- [ ] **Step 4: python-docx 依存確認**

Run: `uv run python -c "from docx import Document; print('python-docx OK')"`
Expected: `python-docx OK`

依存が無い場合: `uv add python-docx` (pyproject.toml に追加)

---

## Task 2: docx 組成 + Phase 1 expected golden 生成 (Phase 0a)

**Files:**
- Create: `tests/fixtures/apa_45refs/input_References.docx`
- Create: `tests/fixtures/apa_45refs/expected_phase1_intermediate.json`

- [ ] **Step 1: build script を 3 PMC ID で実行**

Task 0 で確定した 3 PMC ID を引数に渡して docx 生成:

```bash
uv run python tools/build_apa_fixture.py \
  --psychology PMCXXXXXXX \
  --nursing PMCXXXXXXX \
  --public-health PMCXXXXXXX \
  --output tests/fixtures/apa_45refs/input_References.docx
```

Expected: stdout に各領域の `extracted 15 refs` が表示され、`[write] .../input_References.docx (45 refs)` で終了.

- [ ] **Step 2: docx sanity check**

```bash
uv run python -c "
from docx import Document
d = Document('tests/fixtures/apa_45refs/input_References.docx')
print(f'Total paragraphs: {len(d.paragraphs)}')
for i, p in enumerate(d.paragraphs):
    if i < 3 or i > len(d.paragraphs) - 3:
        print(f'{i:3d}: {p.text[:80]}')
"
```

Expected:
- Total paragraphs: 46 (heading + 45 refs)
- 段落 1-3 に `1.`, `2.`, `3.` の番号付き ref が表示
- 段落末尾 3 つに `43.`, `44.`, `45.` の番号付き ref が表示
- 各 ref テキストに `(YYYY)` (1900-2099) が含まれる

- [ ] **Step 3: Phase 1 のみ実行して expected_phase1_intermediate.json 生成**

```bash
uv run python main.py \
  tests/fixtures/apa_45refs/input_References.docx \
  --output-dir /tmp/apa_45refs_phase1_gen \
  --phase 1
```

Expected: `/tmp/apa_45refs_phase1_gen/phase1_intermediate.json` が生成される

- [ ] **Step 4: Phase 1 出力を fixture に配置**

```bash
cp /tmp/apa_45refs_phase1_gen/phase1_intermediate.json \
   tests/fixtures/apa_45refs/expected_phase1_intermediate.json
```

- [ ] **Step 5: stage3_reference_blocks 件数確認**

```bash
uv run python -c "
import json
data = json.load(open('tests/fixtures/apa_45refs/expected_phase1_intermediate.json'))
print(f'reference_blocks: {len(data[\"stage3_reference_blocks\"])}')
"
```

Expected: `reference_blocks: 45`

⚠️ もし件数が 45 でない場合は build_apa_fixture.py の段落番号順序や preprocess が誤っている可能性 → script 修正後に Step 1 から再実行.

- [ ] **Step 6: SPEC §3.2 を確定値に更新**

`docs/sessions/day16/SPEC_apa_45refs_fixture.md` の 94-100 行を Task 0 Step 4 で準備した確定 table で置換 (3 PMC ID + DOI + Journal + 出版年 + LICENSE).

- [ ] **Step 7: Phase 0a commit**

```bash
git add tools/__init__.py tools/build_apa_fixture.py \
        tests/fixtures/apa_45refs/input_References.docx \
        tests/fixtures/apa_45refs/expected_phase1_intermediate.json \
        docs/sessions/day16/SPEC_apa_45refs_fixture.md
git commit -m "$(cat <<'EOF'
test(fixtures): add apa_45refs input docx + Phase 1 expected (Day16 Phase 0a)

PMC OA 3 領域 (Psychology / Nursing / Public Health) から 15 件ずつ計 45
件の APA 7 参考文献を JATS XML 経由で抽出し、番号付き段落 docx に統合.
Phase 1 を実行して expected_phase1_intermediate.json (parser-only
deterministic golden) を生成.

選定確定 PMC ID:
  - Psychology: PMCXXXXXXX (...)
  - Nursing: PMCXXXXXXX (...)
  - Public Health: PMCXXXXXXX (...)

tools/build_apa_fixture.py は再現性確保のため commit. NCBI E-utilities
efetch + python-docx で組成する 200 行強のスクリプト.

SPEC §3.2 の TBD table を確定値で更新.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Full pipeline 実行 + Phase 3/4 baseline 生成 (Phase 0b)

**Files:**
- Create: `tests/fixtures/apa_45refs/baseline_phase3_resolved.json`
- Create: `tests/fixtures/apa_45refs/baseline_report.md`
- Create: `tests/fixtures/apa_45refs/baseline_three_class_classification.json`
- Create: `tests/fixtures/apa_45refs/README.md`

- [ ] **Step 1: .env 健全性確認**

```bash
uv run python -c "import os; from main import load_env_files; load_env_files(); print('ANTHROPIC:', bool(os.environ.get('ANTHROPIC_API_KEY'))); print('NCBI:', bool(os.environ.get('NCBI_API_KEY')))"
```

Expected:
```
ANTHROPIC: True
NCBI: True
```

⚠️ いずれかが False の場合: `.env` ファイルの設定確認、または `--api-key` / `--ncbi-api-key` で直接指定.

- [ ] **Step 2: full pipeline (Phase 1-4) 実行**

```bash
uv run python main.py \
  tests/fixtures/apa_45refs/input_References.docx \
  --output-dir /tmp/apa_45refs_baseline_gen \
  --phase 4
```

Expected: 約 5-15 分で完走 (LLM call 45 件 × Sonnet 4.6 + PubMed lookup 45 件 + Crossref/NLM 未解決分). 終了時に以下が `/tmp/apa_45refs_baseline_gen/` に生成:
- `phase1_intermediate.json`
- `phase2_structured.json`
- `phase3_resolved.json`
- `phase4_final.json`
- `report.md`
- `three_class_classification.json`
- `journal_mismatch_audit.json`

⚠️ 途中で失敗した場合 (LLM rate limit / network error): `--reuse-phase2` / `--reuse-phase3` で部分再実行可能.

- [ ] **Step 3: 3 baseline ファイルを fixture に配置**

```bash
cp /tmp/apa_45refs_baseline_gen/phase3_resolved.json \
   tests/fixtures/apa_45refs/baseline_phase3_resolved.json
cp /tmp/apa_45refs_baseline_gen/report.md \
   tests/fixtures/apa_45refs/baseline_report.md
cp /tmp/apa_45refs_baseline_gen/three_class_classification.json \
   tests/fixtures/apa_45refs/baseline_three_class_classification.json
```

- [ ] **Step 4: baseline メタ情報を計測**

```bash
uv run python -c "
import json, re
phase3 = json.load(open('tests/fixtures/apa_45refs/baseline_phase3_resolved.json'))
res = phase3['stage4_pubmed_resolutions']
resolved = sum(1 for r in res if r.get('pmid'))
print(f'Phase 3 resolved: {resolved}/{len(res)}')

three = json.load(open('tests/fixtures/apa_45refs/baseline_three_class_classification.json'))
classes = {}
for c in three:
    cls = c.get('class', 'unknown')
    classes[cls] = classes.get(cls, 0) + 1
print(f'Three-class distribution: {classes}')

report = open('tests/fixtures/apa_45refs/baseline_report.md').read()
m = re.search(r'重大\s*\|\s*(\d+)\s*\|', report)
print(f'Report 重大 count: {m.group(1) if m else \"NOT FOUND\"}')
"
```

Expected (具体値は実機依存): 例として
```
Phase 3 resolved: 40/45
Three-class distribution: {'B': 1, 'C': 3, 'unknown': 1}
Report 重大 count: 0
```

これらの値を Step 5 README に転記する.

- [ ] **Step 5: README.md を作成**

`tests/fixtures/apa_45refs/README.md` に以下を書き込む (Step 4 の実測値で `<...>` を埋める):

```markdown
# tests/fixtures/apa_45refs/

**APA 系 45-ref 統合 baseline (Day16 由来)**

## 由来

このディレクトリは、PMC OA 3 領域 (Psychology / Nursing / Public Health) の論文から 15 件ずつ計 45 件の APA 7 参考文献を JATS XML 経由で抽出し、`tools/build_apa_fixture.py` で番号付き段落 docx に統合した fixture を、Day9 Vancouver Veto の APA 適用 regression 保護と LLM 経由 parsing の document-of-record として固定保管する.

## ソース 3 論文

| 領域 | PMC ID | DOI | Journal | 出版年 | LICENSE |
|:---|:---|:---|:---|:---:|:---|
| Psychology | PMCXXXXXXX | 10.XXXX/... | <Journal> | YYYY | CC BY 4.0 |
| Nursing | PMCXXXXXXX | 10.XXXX/... | <Journal> | YYYY | CC BY 4.0 |
| Public Health | PMCXXXXXXX | 10.XXXX/... | <Journal> | YYYY | CC BY 4.0 |

各論文の先頭 15 件を抽出. 抽出範囲は bibliographic information (factual data) のみで、creative expression (abstract 本文等) は含まない. PMC OA CC BY ライセンスの帰属表示として本 table にて明示.

## ファイル一覧と命名規約 (Day11 ハイブリッド)

| ファイル | 種別 | サイズ |
|:---|:---|---:|
| `input_References.docx` | 入力 (tools/build_apa_fixture.py で生成) | <SIZE> |
| `expected_phase1_intermediate.json` | golden (deterministic, parser-only) | <SIZE> |
| `baseline_phase3_resolved.json` | document-of-record (LLM + PubMed variability) | <SIZE> |
| `baseline_report.md` | document-of-record (Phase 4 audit output) | <SIZE> |
| `baseline_three_class_classification.json` | document-of-record (Day15 三分類 audit sidecar) | <SIZE> |
| `README.md` | 本書 | — |

## baseline 生成時のメタ情報

- 実行日時: 2026-05-17 HH:MM (Day16 Phase 0b)
- LLM model: claude-sonnet-4-6-20260301 (`.env` ANTHROPIC_MODEL)
- PubMed snapshot: 2026-05-17 (NCBI 側 latest)
- main.py version: post-Day15 (commit `f2b497f`)
- pipeline 出力 (Step 4 計測値):
  - **Phase 3 解決件数**: <N>/45
  - **三分類分布**: A=<n>, B=<n>, C=<n>, unknown=<n>
  - **report.md 重大件数**: <N>

## 関連 test (`tests/test_integration_apa_45refs.py`、Day16)

| # | test 名 | 性質 | 検証 |
|:---:|:---|:---|:---|
| 1 | `test_apa_45refs_routes_all_to_llm_path` | regression (deterministic) | 45 件全てが `is_mdpi_style()` で False を返す (Vancouver Veto 適用) |
| 2 | `test_phase1_reference_blocks_match_expected` | byte/structural (deterministic) | Phase 1 抽出が `expected_phase1_intermediate.json` と一致 |
| 3 | `test_phase1_extracts_45_reference_blocks` | 件数 (deterministic) | block 数 = 45 |
| 4 | `test_baseline_phase3_documents_resolution_count` | document-of-record | 解決件数 = `<N>/45` 一致 |
| 5 | `test_baseline_report_documents_audit_summary` | document-of-record | report.md 重大件数 = `<N>` 一致 |
| 6 | `test_apa_paren_year_pattern_detected_in_all_refs` | parser-only | 全 45 件に `(YYYY)` 含む |
| 7 | `test_apa_ampersand_author_separator_present` | structural | ≥20 件が `, & ` を含む |
| 8 | `test_baseline_three_class_classification_distribution` | document-of-record | 三分類分布 = `{A=<n>, B=<n>, C=<n>, unknown=<n>}` 一致 |

**API key 不要**: 全 8 test は parser-only もしくは fixture 直読のため、`ANTHROPIC_API_KEY` / `NCBI_API_KEY` なしで CI 実行可能.

## baseline 更新の運用 (Day11 と同型)

| 変動原因 | 検出 | 対応 |
|:---|:---|:---|
| Anthropic LLM model upgrade | test 4-5, 8 で乖離 | Day16 相当の Phase 0b retry + baseline 更新 + test 期待値更新 (別 commit) |
| PubMed/Crossref/NLM 更新 | 同上 | 同上 |
| parser/main.py 改修 | test 1-3, 6-7 fail | 意図確認、意図的なら expected 更新、意図外なら revert |

## 命名対比 (既存 fixture との関係)

| 観点 | `mdpi_149refs/` | `vancouver_24refs/` | `apa_45refs/` (本ディレクトリ) |
|:---|:---|:---|:---|
| 全件 `expected_*` | ○ (fast-path byte 一致) | × (LLM variability) | × (LLM variability) |
| `baseline_*` 使用 | × | ○ | ○ |
| 件数 | 149 | 24 | 45 |
| ソース | OneDrive (実機) | OneDrive (実機) | PMC OA (合成) |
| 領域多様性 | 低 (1 docx) | 低 (1 docx) | 高 (3 領域混在) |

---

**作成日**: 2026-05-17 (Day16 Phase 0b)
**作成者**: Claude Code (Sonnet 4.6)
**承認**: 片山英樹 (Hideki Katayama)
**関連 SPEC**: `docs/sessions/day16/SPEC_apa_45refs_fixture.md` (commit `4f1181d`)
```

- [ ] **Step 6: README の `<...>` を Step 4 実測値で埋める**

Step 4 の出力結果を見ながら、README 内の `<N>`, `<SIZE>`, `<n>` 等の placeholder を実値に置換 (Edit tool で 1 つずつ).

- [ ] **Step 7: Phase 0b commit**

```bash
git add tests/fixtures/apa_45refs/baseline_phase3_resolved.json \
        tests/fixtures/apa_45refs/baseline_report.md \
        tests/fixtures/apa_45refs/baseline_three_class_classification.json \
        tests/fixtures/apa_45refs/README.md
git commit -m "$(cat <<'EOF'
test(fixtures): freeze apa_45refs Phase 3/4 + three_class baselines (Day16 Phase 0b)

main.py を Phase 4 まで完走させて 3 baseline ファイルを document-of-record
として凍結:
  - baseline_phase3_resolved.json (PubMed 解決 <N>/45)
  - baseline_report.md (重大 <N> 件)
  - baseline_three_class_classification.json (A=<n>, B=<n>, C=<n>, unknown=<n>)

README.md に Day11 ハイブリッド命名規約 + 実測値 + LLM/PubMed snapshot
メタ情報を記録. CC BY 4.0 帰属表示として 3 論文 citation を明示.

LLM cost: ~$<X> (Sonnet 4.6 × 45 calls).
本 fixture は CI 実行で API key 不要 (parser-only + 直読 only).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Test 1 (Vancouver Veto routing regression)

**Files:**
- Create: `tests/test_integration_apa_45refs.py` (新規、共通 helper + test 1)

- [ ] **Step 1: 失敗 test と test file 骨格を作成**

`tests/test_integration_apa_45refs.py` の冒頭部 + test 1 を書く:

```python
"""
Integration test for the APA 45-ref Day16 baseline.

Background:
    Day9 (commit ab25630) introduced the Vancouver Veto in is_mdpi_style()
    so that references with `(YYYY)` paren year are routed to the LLM path
    instead of the MDPI fast-path. Day11 added Vancouver 24-ref fixture
    as the first golden for this regression. Day16 adds APA 45-ref fixture
    as the second golden, extending the regression coverage to APA 7 style.

    PMC OA 3 papers (Psychology / Nursing / Public Health) provide 15 refs
    each, all in APA 7 with `(YYYY)` paren year.

Fixture file naming convention (Day11 hybrid):
    expected_*  : deterministic output (byte/structural match required)
    baseline_*  : variability-bearing output (LLM/PubMed-dependent)

API key requirement: NONE.
    Tests 1-3, 6-7 use parser-only paths (no LLM).
    Tests 4-5, 8 read baseline files directly without re-running Phase 2-4.

Refs: docs/sessions/day16/SPEC_apa_45refs_fixture.md;
      docs/sessions/day16/PLAN_apa_45refs_fixture.md.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

FIXTURES = Path(__file__).parent / "fixtures" / "apa_45refs"
INPUT_DOCX = FIXTURES / "input_References.docx"
EXPECTED_PHASE1 = FIXTURES / "expected_phase1_intermediate.json"
BASELINE_PHASE3 = FIXTURES / "baseline_phase3_resolved.json"
BASELINE_REPORT = FIXTURES / "baseline_report.md"
BASELINE_THREE_CLASS = FIXTURES / "baseline_three_class_classification.json"


# -----------------------------------------------------------------------------
# Helper (pattern borrowed from test_integration_vancouver_24refs.py)
# -----------------------------------------------------------------------------


def _load_phase1_blocks_with_ln_report():
    """Phase 1 を再実行し (blocks, ln_report) を返す.

    Returns ReferenceBlock instances matching the signature expected by
    structure_all_references() and is_mdpi_style().
    """
    from main import (  # noqa: E402
        extract_text,
        preprocess,
        split_references,
        detect_line_numbers,
    )

    raw, _kind = extract_text(INPUT_DOCX)
    ln_report = detect_line_numbers(raw)
    cleaned, _trace = preprocess(raw, ln_report)
    blocks = split_references(cleaned)
    return blocks, ln_report


# -----------------------------------------------------------------------------
# Test 1: Vancouver Veto routing (deterministic)
# -----------------------------------------------------------------------------


def test_apa_45refs_routes_all_to_llm_path():
    """Day9 Vancouver Veto の APA 適用: 45 件すべてが is_mdpi_style() で
    False を返し、LLM path に routing されることを確認.

    Day16 で本 fixture を追加することで、Vancouver Veto の regression 保護を
    APA 7 表記にも拡張する (Day11 vancouver_24refs に続く 2 番目の golden).
    """
    import mdpi_parser  # noqa: E402

    blocks, _ = _load_phase1_blocks_with_ln_report()
    assert len(blocks) == 45, f"Expected 45 blocks, got {len(blocks)}"

    fast_path_blocks = []
    for b in blocks:
        if mdpi_parser.is_mdpi_style(b.raw_text):
            fast_path_blocks.append(b.ref_no)

    assert fast_path_blocks == [], (
        f"Day9 Vancouver Veto regression on APA 7: {len(fast_path_blocks)} "
        f"block(s) routed to MDPI fast-path (should be 0). "
        f"Affected ref_no: {fast_path_blocks[:5]}"
    )
```

- [ ] **Step 2: test 1 が PASS することを確認 (deterministic、fixture 既に在り)**

Run: `uv run pytest tests/test_integration_apa_45refs.py::test_apa_45refs_routes_all_to_llm_path -v`
Expected: **PASS**

⚠️ FAIL の場合: `tools/build_apa_fixture.py` が APA でない ref を含めた可能性 (例: 章/書籍で年が括弧外) → docx 再生成、Task 2 から再実行.

- [ ] **Step 3: 単独 commit せず、Task 5-8 と一緒に Phase 1 で commit**

(後続 test 2-5 を追加した後に統合 commit する.)

---

## Task 5: Test 2 (Phase 1 byte/structural match)

**Files:**
- Modify: `tests/test_integration_apa_45refs.py` (test 2 を append)

- [ ] **Step 1: test 2 を append**

`tests/test_integration_apa_45refs.py` 末尾に追記:

```python


# -----------------------------------------------------------------------------
# Test 2: Phase 1 reference_blocks deterministic
# -----------------------------------------------------------------------------


def test_phase1_reference_blocks_match_expected():
    """Phase 1 (parser-only) の reference_blocks 抽出が expected と一致.

    `input_file` 等の cwd 依存メタフィールドは比較せず、
    stage3_reference_blocks のみを比較 (Day8 _scrub_volatile_lines と同思想、
    Day11 vancouver_24refs と同型).
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()

    expected_doc = json.loads(EXPECTED_PHASE1.read_text(encoding="utf-8"))
    expected_blocks = expected_doc["stage3_reference_blocks"]

    assert len(blocks) == len(expected_blocks), (
        f"Block count mismatch: got {len(blocks)}, expected {len(expected_blocks)}"
    )

    for b, exp in zip(
        sorted(blocks, key=lambda x: x.ref_no),
        sorted(expected_blocks, key=lambda x: x["ref_no"]),
    ):
        assert b.ref_no == exp["ref_no"], (
            f"ref_no mismatch: got {b.ref_no}, expected {exp['ref_no']}"
        )
        assert b.raw_text == exp["raw_text"], (
            f"Ref #{b.ref_no} raw_text mismatch.\n"
            f"  got:      {b.raw_text[:80]!r}\n"
            f"  expected: {exp['raw_text'][:80]!r}"
        )
        assert b.char_length == exp["char_length"], (
            f"Ref #{b.ref_no} char_length mismatch: "
            f"got {b.char_length}, expected {exp['char_length']}"
        )
```

- [ ] **Step 2: test 2 PASS 確認**

Run: `uv run pytest tests/test_integration_apa_45refs.py::test_phase1_reference_blocks_match_expected -v`
Expected: **PASS**

⚠️ FAIL の場合: `expected_phase1_intermediate.json` の生成時と実行環境で `extract_text` / `preprocess` の挙動差異 → 環境再現性問題 → 同じ環境で Phase 1 再実行して expected 再生成.

---

## Task 6: Test 3 (Reference count = 45)

**Files:**
- Modify: `tests/test_integration_apa_45refs.py` (test 3 を append)

- [ ] **Step 1: test 3 を append**

```python


# -----------------------------------------------------------------------------
# Test 3: Reference count = 45
# -----------------------------------------------------------------------------


def test_phase1_extracts_45_reference_blocks():
    """Phase 1 が apa_45refs docx から 45 件の reference を抽出.

    deterministic, helps catch parser regressions that change the count.
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()
    assert len(blocks) == 45, f"Expected 45 blocks, got {len(blocks)}"
```

- [ ] **Step 2: test 3 PASS 確認**

Run: `uv run pytest tests/test_integration_apa_45refs.py::test_phase1_extracts_45_reference_blocks -v`
Expected: **PASS**

---

## Task 7: Test 4 (Baseline Phase 3 resolution count)

**Files:**
- Modify: `tests/test_integration_apa_45refs.py` (test 4 を append)
- Read: `tests/fixtures/apa_45refs/README.md` (実測値確認)

- [ ] **Step 1: README から実測 Phase 3 解決件数を確認**

Run: `grep "Phase 3 解決件数" tests/fixtures/apa_45refs/README.md`
Expected: `- **Phase 3 解決件数**: <N>/45` の行が出力される (N の値をメモ)

- [ ] **Step 2: test 4 を append**

`<N>` は Step 1 で確認した値で置換:

```python


# -----------------------------------------------------------------------------
# Test 4: Baseline Phase 3 resolution count (document-of-record)
# -----------------------------------------------------------------------------

EXPECTED_RESOLVED_COUNT = <N>  # Day16 Phase 0b 実測 (README.md 参照)


def test_baseline_phase3_documents_resolution_count():
    """baseline_phase3_resolved.json (Day16 Phase 0b 実測) に
    解決件数 <N>/45 が記録されていることを確認.

    本 test は LLM/PubMed を再実行せず baseline file の中身を
    document-of-record として assert する.

    将来の LLM/PubMed 変動で baseline 更新が必要になったら、
    Day16 相当の Phase 0b retry を実施し baseline を更新してから
    本 test の EXPECTED_RESOLVED_COUNT 値を更新する.
    """
    data = json.loads(BASELINE_PHASE3.read_text(encoding="utf-8"))
    resolutions = data["stage4_pubmed_resolutions"]

    assert len(resolutions) == 45, (
        f"Expected 45 resolution attempts, got {len(resolutions)}"
    )

    resolved_count = sum(1 for r in resolutions if r.get("pmid"))
    assert resolved_count == EXPECTED_RESOLVED_COUNT, (
        f"Day16 Phase 0b baseline regression: "
        f"resolved {resolved_count}/45, expected {EXPECTED_RESOLVED_COUNT}/45. "
        f"If LLM/PubMed drift is the cause, regenerate baseline and update test."
    )
```

- [ ] **Step 3: test 4 PASS 確認**

Run: `uv run pytest tests/test_integration_apa_45refs.py::test_baseline_phase3_documents_resolution_count -v`
Expected: **PASS**

---

## Task 8: Test 5 (Baseline report 重大 count)

**Files:**
- Modify: `tests/test_integration_apa_45refs.py` (test 5 を append)
- Read: `tests/fixtures/apa_45refs/README.md`

- [ ] **Step 1: README から実測 report.md 重大件数を確認**

Run: `grep "重大件数" tests/fixtures/apa_45refs/README.md`
Expected: `- **report.md 重大件数**: <N>` の行 (N をメモ)

- [ ] **Step 2: test 5 を append**

`<N>` は Step 1 値で置換:

```python


# -----------------------------------------------------------------------------
# Test 5: Baseline report audit summary (document-of-record)
# -----------------------------------------------------------------------------

EXPECTED_REPORT_CRITICAL_COUNT = <N>  # Day16 Phase 0b 実測


def test_baseline_report_documents_audit_summary():
    """baseline_report.md ダッシュボードの「重大」件数が <N> であることを確認.

    Day16 fixture は APA 7 形式 (LLM 経由) なので、Vancouver Veto 適用後の
    LLM parsing 品質を document-of-record として凍結する.
    """
    report = BASELINE_REPORT.read_text(encoding="utf-8")

    # ダッシュボード行: "| 査読コメント: 重大 | N | ..."
    pattern = re.compile(r"重大\s*\|\s*(\d+)\s*\|", re.MULTILINE)
    match = pattern.search(report)

    assert match is not None, (
        f"baseline_report.md ダッシュボードに「重大 | N |」が見つからない. "
        f"report 先頭 500 文字: {report[:500]!r}"
    )
    assert int(match.group(1)) == EXPECTED_REPORT_CRITICAL_COUNT, (
        f"重大 count: got {match.group(1)}, expected {EXPECTED_REPORT_CRITICAL_COUNT}. "
        f"LLM/parser variability の可能性 → Phase 0b retry + baseline 更新 + "
        f"本 test 更新を検討."
    )
```

- [ ] **Step 3: test 5 PASS 確認**

Run: `uv run pytest tests/test_integration_apa_45refs.py::test_baseline_report_documents_audit_summary -v`
Expected: **PASS**

- [ ] **Step 4: Phase 1 commit (test 1-5)**

```bash
git add tests/test_integration_apa_45refs.py
git commit -m "$(cat <<'EOF'
test(integration): add apa_45refs base 5 tests (Day16 Phase 1)

Vancouver 24refs と同型の base 5 tests を新規追加:
  1. test_apa_45refs_routes_all_to_llm_path
       (Vancouver Veto の APA 適用 regression 保護)
  2. test_phase1_reference_blocks_match_expected
       (Phase 1 byte/structural deterministic)
  3. test_phase1_extracts_45_reference_blocks
       (件数 = 45 deterministic)
  4. test_baseline_phase3_documents_resolution_count
       (Phase 3 PubMed 解決件数 <N>/45 document-of-record)
  5. test_baseline_report_documents_audit_summary
       (report.md 重大 <N> 件 document-of-record)

API key 不要 (parser-only / fixture 直読 only).
Day11 vancouver_24refs に続く 2 番目の LLM-path 用 golden fixture test.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Test 6 (APA `(YYYY)` paren year fixture-data health)

**Files:**
- Modify: `tests/test_integration_apa_45refs.py` (test 6 を append)

- [ ] **Step 1: test 6 を append**

```python


# -----------------------------------------------------------------------------
# Test 6: APA paren year pattern detected in all refs (parser-only)
# -----------------------------------------------------------------------------


def test_apa_paren_year_pattern_detected_in_all_refs():
    """全 45 件の raw text に `(YYYY)` (1900-2099) パターンが含まれることを
    確認 (APA 7 表記の中核特徴を fixture data 自体が満たすことの assert、
    test data 健全性保護).

    将来 build_apa_fixture.py 変更で APA でない ref が混入した場合に検知.
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()
    paren_year_pattern = re.compile(r"\((?:19|20)\d{2}\)")
    refs_without_paren_year = [
        b.ref_no for b in blocks
        if not paren_year_pattern.search(b.raw_text)
    ]
    assert refs_without_paren_year == [], (
        f"APA fixture health regression: {len(refs_without_paren_year)} "
        f"ref(s) lack `(YYYY)` pattern. ref_no: {refs_without_paren_year[:5]}"
    )
```

- [ ] **Step 2: test 6 PASS 確認**

Run: `uv run pytest tests/test_integration_apa_45refs.py::test_apa_paren_year_pattern_detected_in_all_refs -v`
Expected: **PASS**

---

## Task 10: Test 7 (APA `, & ` author separator presence)

**Files:**
- Modify: `tests/test_integration_apa_45refs.py` (test 7 を append)

- [ ] **Step 1: test 7 を append**

```python


# -----------------------------------------------------------------------------
# Test 7: APA `, & ` author separator presence (structural)
# -----------------------------------------------------------------------------


def test_apa_ampersand_author_separator_present():
    """45 件中、最低 20 件が `, & ` を含むことを確認.

    APA 7 規約: 著者複数列挙時の最終境界は `, & ` (Vancouver は `; ` または
    `, `). 本 test は fixture が APA 7 規約を満たしていることを保証する
    (build_apa_fixture.py の _format_authors() 出力品質の test data 健全性
    保護).

    20 という閾値は: 単著 ref がある程度含まれることを許容しつつ、共著率が
    APA 領域で過半数を超えるという経験則に基づく.
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()
    refs_with_ampersand = [
        b.ref_no for b in blocks if ", & " in b.raw_text
    ]
    assert len(refs_with_ampersand) >= 20, (
        f"APA 7 structural regression: only {len(refs_with_ampersand)}/45 "
        f"refs contain `, & ` (APA author separator). "
        f"Expected >=20. Refs with separator: {refs_with_ampersand}"
    )
```

- [ ] **Step 2: test 7 PASS 確認**

Run: `uv run pytest tests/test_integration_apa_45refs.py::test_apa_ampersand_author_separator_present -v`
Expected: **PASS**

⚠️ FAIL の場合: build_apa_fixture.py の `_format_authors()` が `, & ` を出力していない可能性 → script 検証.

---

## Task 11: Test 8 (Three-class classification distribution)

**Files:**
- Modify: `tests/test_integration_apa_45refs.py` (test 8 を append)
- Read: `tests/fixtures/apa_45refs/README.md`

- [ ] **Step 1: README から実測三分類分布を確認**

Run: `grep "三分類分布" tests/fixtures/apa_45refs/README.md`
Expected: `- **三分類分布**: A=<n>, B=<n>, C=<n>, unknown=<n>` の行 (各 n をメモ)

- [ ] **Step 2: test 8 を append**

`<n>` は Step 1 値で置換:

```python


# -----------------------------------------------------------------------------
# Test 8: Three-class classification distribution (document-of-record)
# -----------------------------------------------------------------------------

EXPECTED_THREE_CLASS_DISTRIBUTION = {
    "A": <nA>,
    "B": <nB>,
    "C": <nC>,
    "unknown": <nU>,
}  # Day16 Phase 0b 実測 (README.md 参照)


def test_baseline_three_class_classification_distribution():
    """baseline_three_class_classification.json の A/B/C/unknown 分布が
    Day16 Phase 0b 実測値と一致することを確認.

    Day15 で実装した三分類 audit logic (crossref_check + nlm_catalog_check)
    が APA 7 入力に対しても正しく動作する baseline を document-of-record
    として凍結する.

    将来 Crossref/NLM API 応答変動で baseline 更新が必要になったら、
    Phase 0b retry + 本 EXPECTED_THREE_CLASS_DISTRIBUTION 更新.
    """
    classifications = json.loads(BASELINE_THREE_CLASS.read_text(encoding="utf-8"))
    actual = {"A": 0, "B": 0, "C": 0, "unknown": 0}
    for c in classifications:
        cls = c.get("class", "unknown")
        if cls not in actual:
            actual[cls] = 0
        actual[cls] += 1
    assert actual == EXPECTED_THREE_CLASS_DISTRIBUTION, (
        f"Day15 三分類 audit regression on APA fixture: "
        f"got {actual}, expected {EXPECTED_THREE_CLASS_DISTRIBUTION}"
    )
```

- [ ] **Step 3: test 8 PASS 確認**

Run: `uv run pytest tests/test_integration_apa_45refs.py::test_baseline_three_class_classification_distribution -v`
Expected: **PASS**

- [ ] **Step 4: 全 8 tests 一括 PASS 確認**

Run: `uv run pytest tests/test_integration_apa_45refs.py -v`
Expected: **8 passed**

- [ ] **Step 5: 全既存 tests regression なし確認**

Run: `uv run pytest -v`
Expected: **89 passed, 1 skipped** (既存 81 + 新規 8、Day15 末の 81 passed / 1 skipped から regression なし)

⚠️ 既存 test が FAIL した場合: 何らかの interference (e.g., `sys.path.insert` の副作用、conftest.py 影響等) を調査 → 原因解消後再実行.

- [ ] **Step 6: Phase 2 commit (test 6-8)**

```bash
git add tests/test_integration_apa_45refs.py
git commit -m "$(cat <<'EOF'
test(integration): add apa_45refs APA-specific 3 tests (Day16 Phase 2)

APA 7 表記固有の特徴を assert する 3 tests を追加:
  6. test_apa_paren_year_pattern_detected_in_all_refs
       (全 45 件に `(YYYY)` 含む、fixture data health 保護)
  7. test_apa_ampersand_author_separator_present
       (>=20 件に `, & ` 含む、APA 7 structural health 保護)
  8. test_baseline_three_class_classification_distribution
       (Day15 三分類 audit の APA 適用結果 {A=<nA>,B=<nB>,C=<nC>,
       unknown=<nU>} を document-of-record 凍結)

合計 8 tests (base 5 + APA 固有 3) 全 PASS. 既存 81 passed → 89 passed
(regression なし).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 12: USAGE_QUICKSTART version bump (optional, Phase 3)

**Files:**
- Modify: `skill_package/references/USAGE_QUICKSTART.md`

- [ ] **Step 1: 現バージョンを確認**

Run: `grep -n "## バージョン\|## Version" skill_package/references/USAGE_QUICKSTART.md | head -3`
Expected: `## バージョン 1.3` 等の表示 (Day15 で 1.3 にした)

- [ ] **Step 2: バージョン 1.3 → 1.4 に bump**

Edit `skill_package/references/USAGE_QUICKSTART.md`:
- `バージョン 1.3` → `バージョン 1.4` に置換
- `## バージョン履歴` または `## X. 変更履歴` 章に以下行を追記:

```markdown
- **1.4 (2026-05-17, Day16)**: APA 7 表記 (45-ref fixture) の regression 保護を追加. Day9 Vancouver Veto の検証対象を Vancouver/AMA のみから APA 7 にも拡張. 三分類 audit logic の APA 適用 baseline も凍結.
```

- [ ] **Step 3: USAGE_QUICKSTART markdown lint pass 確認**

Run: `uv run python -c "import pathlib; print(pathlib.Path('skill_package/references/USAGE_QUICKSTART.md').read_text(encoding='utf-8').count(chr(10)))"` (行数表示)
Expected: 元の行数 + ~3 行程度

- [ ] **Step 4: Phase 3 commit (optional)**

```bash
git add skill_package/references/USAGE_QUICKSTART.md
git commit -m "$(cat <<'EOF'
docs(skill): bump USAGE_QUICKSTART to 1.4 (Day16 APA fixture)

Day16 で APA 7 表記の 45-ref golden fixture (tests/fixtures/apa_45refs/) を
追加した内容を反映:
  - Day9 Vancouver Veto の regression 保護対象を APA 7 にも拡張
  - Day15 三分類 audit の APA 適用 baseline 凍結
  - 全 8 tests 追加 (81 passed → 89 passed)

変更履歴を 1.3 → 1.4 に bump.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

⚠️ optional: もし `skill_package/references/USAGE_QUICKSTART.md` に APA 言及が不要と判断した場合は本 Task を skip.

---

## Task 13: Day16 session archive (Phase 4)

**Files:**
- Create: `docs/sessions/day16/README.md`
- Create: `docs/sessions/day16/DAY16_LESSONS_LEARNED.md`

- [ ] **Step 1: Day15 README.md を参考に Day16 README.md を作成**

Day15 (`docs/sessions/day15/README.md`) の構造を踏襲. 以下を反映:

```markdown
# docs/sessions/day16/

**Day16 セッション (2026-05-17) のアーカイブ**

このディレクトリは、pubmed-reference-resolver プロジェクトの Day16 セッション (Day7 §9.3 long-term task 残のうち APA / Cell 系 golden fixture の APA 部分を完了した作業) で生成された記録を、永続アーカイブとして保管する.

## 内容

| ファイル | 役割 | 対象 |
|:---|:---|:---|
| `SPEC_apa_45refs_fixture.md` | brainstorming 確定設計仕様 (Q1-Q5 + Approach + 全 6 sections) | Claude Code 向け / プロジェクト閲覧者向け |
| `PLAN_apa_45refs_fixture.md` | writing-plans 出力の段階的実装計画 (Task 0-13) | 実装エージェント向け |
| `DAY16_LESSONS_LEARNED.md` | Day16 全 commits の経緯 + 教訓 | プロジェクト閲覧者向け |
| `README.md` | 本書 | プロジェクト閲覧者向け |

## Day16 の特徴

Day9 で確立された **brainstorming → SPEC → writing-plans → TDD 実装**の 4 段階フローを 3 度目の本格適用 (Day9 / Day15 に続く). 主目的は LLM-path 用の 2 番目の golden fixture 追加 (Day11 vancouver_24refs に続く).

### Day15 (3 分類 audit) との対比

| 観点 | Day15 (3 分類 audit) | Day16 (APA fixture) |
|:---|:---|:---|
| 規模 | 3 新 module + main.py 改修 | 1 新 tool script + fixture 6 files + 1 test file |
| commit 数 | 7 commits | 5-6 commits |
| 新規 production code | あり (3 module + main.py 統合) | なし (production code 改修ゼロ) |
| 主目的 | logic 拡張 | regression 保護 + document-of-record |
| 工数 | ~2h | ~3.5h |

## 達成事項 (5-6 commits)

| 順 | commit | 種別 | 達成 |
|:---:|:---:|:---|:---|
| (前) | `4f1181d` | docs(spec) | Day16 SPEC を archive (334 行、11 章) |
| 1 | `<hash>` | test(fixtures) | apa_45refs Phase 0a (build script + docx + Phase 1 expected) |
| 2 | `<hash>` | test(fixtures) | apa_45refs Phase 0b (Phase 3/4 baseline + 三分類 baseline + README) |
| 3 | `<hash>` | test(integration) | base 5 tests (Phase 1) |
| 4 | `<hash>` | test(integration) | APA 固有 3 tests (Phase 2) |
| 5 | `<hash>` | docs(skill) | USAGE_QUICKSTART 1.3 → 1.4 (Phase 3、optional) |
| 6 | (本 commit) | docs(sessions) | Day16 archive (README + LESSONS + PLAN) (Phase 4) |

main branch: 53 → **59** + 本 commit で **60 commits** (Day15 末 → Day16 末、+7)
test 健全性: 81 passed → **89 passed** (+8) / 1 skipped (条件付き、不変)

## Day7 §9.3 残タスクの達成状況 (Day16 末)

| タスク | 状態 (Day16 末) | commit |
|:---|:---:|:---:|
| Vancouver golden fixture | ✅ Day11 | `fe38298` |
| Day9 (Z) 未解決 2 件 MEDLINE 調査 | ✅ Day13 | `a2ee5ae` |
| Day13 §6 案 A: 3 分類 audit logic | ✅ Day15 | `132ffab` |
| **APA 系 golden fixture** | ✅ **Day16** (本日) | `<hash>` 系列 |
| **Cell 系 golden fixture** | ⏳ Day17+ | |
| MCP/hook 経由 Stage 3 配線 | ⏳ Day17+ | |
| GitHub remote 追加と push | ⏳ Day17+ | |

→ Day7 §9.3 long-term task 5 件中 4 件完了. 残 3 件は Day17+.

## 関連記録

完全な session 記録は別途以下に保管 (本リポジトリ外):
- `pubmed-reference-resolver-integration-chat-day16.md` (Day16 の完全記録、予定)
- `pubmed-reference-resolver-integration-chat-day{1,...,15}.md` (前日記録)

## 利用方法

### Day17 以降の参照

Day16 で追加された APA fixture は、Cell 系 fixture (Day17 候補) の design を準備する際の参照として有用. `tools/build_apa_fixture.py` は同型の `tools/build_cell_fixture.py` のテンプレートとして再利用可能.

詳細な改修候補は `DAY16_LESSONS_LEARNED.md` §6 (残存タスク) を参照.

### audit_report 利用者向け

Day16 以降、APA 7 表記の reference が含まれる docx でも:
- Vancouver Veto の routing 保護が継続
- Day15 三分類 audit が正常動作
- `report.md` §2 (未解決参照詳細) に「[3 分類化]」sub-section が APA 入力でも自動生成

具体例として `tests/fixtures/apa_45refs/baseline_report.md` を参照.

## ディレクトリ命名規約

`docs/sessions/dayN/` 形式 (Day6 で確立、Day7-16 で継続). Day17 セッション完了後は `docs/sessions/day17/` が追加される予定.

---

**作成日**: 2026-05-17 (Day16 クロージング時)
**メンテナ**: 片山英樹 (Hideki Katayama)
```

- [ ] **Step 2: DAY16_LESSONS_LEARNED.md を作成**

Day15 (`docs/sessions/day15/DAY15_LESSONS_LEARNED.md`) と同型の構造で. 以下章立て:

```markdown
# Day16 LESSONS LEARNED

**Day16 セッション (2026-05-17)**: APA 系 45-ref golden fixture 追加 (Day7 §9.3 long-term task 残 4 件目を完了)

---

## 1. セッション概要

(背景・目的・brainstorming の Q1-Q5 + Approach 採択経緯)

## 2. 実装段階の経緯 (Phase 0a → 0b → 1 → 2 → 3 → 4)

(各 Phase の commit hash + 達成内容 + 工数)

## 3. 設計判断と検証

(Q1-Q5 の各選択肢で何が refused されたかと、その判断根拠)

## 4. 実機検証結果

### 4.1 PMC OA 3 論文選定結果
(確定 PMC ID + Journal + Year + LICENSE)

### 4.2 Phase 3 PubMed 解決率
(<N>/45 = <pct>%、Vancouver の 22/24 = 91.7% との対比)

### 4.3 Day15 三分類分布
(A=<n>, B=<n>, C=<n>, unknown=<n>)

## 5. 教訓 (D16-1〜D16-N)

### 5.1 D16-1: <タイトル>
(具体的事象 → 学び → 適用範囲)

### 5.2 D16-2: <タイトル>
(具体的事象 → 学び → 適用範囲)

## 6. 残存タスク (Day17 以降)

### 6.1 Day7 §9.3 long-term task の達成状況
(Day16 末時点での 5 件タスクの状態)

### 6.2 Day16 が生成した新規候補
- [ ] Cell 系 fixture (本 SPEC pattern 適用)
- [ ] APA fixture の領域追加 (現状 3 領域 → 6 領域等)
- [ ] tools/build_apa_fixture.py のテスト追加

## 7. 次セッション再開時のプロンプトテンプレート

### パターン 1: Day17 として Cell 系 fixture

```
Day17 として、Cell 系の golden fixture を新規追加します
(Day16 apa_45refs と同型 pattern). PMC OA Cell Press journal から
15 件 × 3 領域 = 45 件抽出. TDD で進めてください.
```

### パターン 2: 他の Day17+ 残タスク (GitHub push / MCP 配線等)

(Day15 lessons §7 と同型)

---

**記録完了日**: 2026-05-17 (Day16)
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day16 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day16.md` (予定)
**ステータス**: Day16 archive 完成、Day17 着手準備完了
```

⚠️ 章 5 の D16-N 教訓は、実装中に発生した気付き (PMC fetch の rate limit / JATS XML namespace 問題 / LLM/PubMed の APA 解決率の Vancouver との差異等) を実機で集めながら書き込む.

- [ ] **Step 3: Phase 4 commit**

```bash
git add docs/sessions/day16/PLAN_apa_45refs_fixture.md \
        docs/sessions/day16/README.md \
        docs/sessions/day16/DAY16_LESSONS_LEARNED.md
git commit -m "$(cat <<'EOF'
docs(sessions): archive day16 apa_45refs fixture session

Day16 セッション完了に伴う archive:
- README.md: day16/ index, Day7 §9.3 達成状況 4/5 表
- DAY16_LESSONS_LEARNED.md: 全 commits 経緯 + 教訓 D16-1〜D16-N
- PLAN_apa_45refs_fixture.md: writing-plans 出力の実装計画 (Task 0-13)

main branch: 53 → 59 (+6), test: 81 passed → 89 passed (+8) / 1 skipped.
Day7 §9.3 long-term task 5 件中 4 件完了 (Vancouver, MEDLINE 調査,
3 分類 audit, APA fixture). 残 3 件 (Cell fixture, MCP 配線, GitHub push)
は Day17 以降.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Verification (全 Task 完了後の最終確認)

- [ ] **V1: 全 test pass**

Run: `uv run pytest -v`
Expected: **89 passed, 1 skipped** (既存 81 + 新規 8)

- [ ] **V2: SPEC §8 完了条件 12 項目すべて満たす**

`docs/sessions/day16/SPEC_apa_45refs_fixture.md` §8 の 12 項目を 1 つずつ確認:

1. `uv run python tools/build_apa_fixture.py --help` → ヘルプ表示
2. `python -c "from docx import Document; d=Document('tests/fixtures/apa_45refs/input_References.docx'); assert len(d.paragraphs)>=45"`
3. `jq '.stage3_reference_blocks | length' < tests/fixtures/apa_45refs/expected_phase1_intermediate.json` = 45
4. `tests/fixtures/apa_45refs/baseline_phase3_resolved.json` 存在 + JSON parseable
5. `tests/fixtures/apa_45refs/baseline_report.md` 存在 + ダッシュボード行 (`## 1. ダッシュボード` or 同等) 有
6. `tests/fixtures/apa_45refs/baseline_three_class_classification.json` 存在 + JSON parseable
7. `tests/fixtures/apa_45refs/README.md` 存在 + 3 論文 citation + LICENSE 記載
8. `uv run pytest tests/test_integration_apa_45refs.py --collect-only` = 8 items
9. `uv run pytest tests/test_integration_apa_45refs.py -v` = 8 passed
10. `uv run pytest -v` = 89 passed, 1 skipped
11. `docs/sessions/day16/SPEC_apa_45refs_fixture.md` 存在
12. `docs/sessions/day16/{README,DAY16_LESSONS_LEARNED,PLAN}.md` 全部存在

- [ ] **V3: commit count 確認**

Run: `git log --oneline | head -10`
Expected: 最新 commit は `docs(sessions): archive day16 ...`、Day16 中の commit 数は ~6 (SPEC 含めて 7).

- [ ] **V4: 最終 git status**

Run: `git status`
Expected: `nothing to commit, working tree clean` (.DS_Store は untracked のままで OK)

---

## Notes for Implementing Agent

- **TDD 強度**: Phase 1-2 の test 追加段階は厳密 TDD (Step: write test → expect FAIL → implement → expect PASS). ただし本 plan の test は fixture が既に在る前提なので、test 追加時点で即 PASS する想定 ("write a passing assertion against an existing baseline" pattern、Day9-15 で確立).
- **ユーザー gate**: Task 0 Step 3 はユーザー承認が必須. 候補 3 論文の提示後、ユーザーが却下したら Step 1 から再選定.
- **LLM cost**: Task 3 (Phase 0b full pipeline) は 1 回限り、~$0.5-1.0. もし途中で失敗したら `--reuse-phase2` / `--reuse-phase3` で部分再実行可.
- **環境依存**: Task 2 Step 5 / Task 3 Step 4 で出力件数や解決数が SPEC 想定と異なる場合は、その実測値を README に反映 + test 期待値に反映 (SPEC は変更しない; SPEC は意図、README+test は実装記録).
- **PMC fetch のキャッシュ**: `.cache/pmc_xml/` は `.gitignore` 推奨 (XML サイズ大). Task 1 完了後に `.gitignore` に追記.
- **Day11 規約遵守**: `expected_*` / `baseline_*` の区別は絶対遵守. test 4-5, 8 は baseline_ → document-of-record として「予想 != 実測」時には baseline 側を更新 (Day9 (Z) 型 retry).
