# Cell 45-ref Golden Fixture Implementation Plan (Day17)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** PMC OA 3 iScience (Cell Press) 論文 (Molecular Biology / Biomedical / AI Engineering) から計 45 件の Cell-style 参考文献を抽出して統合 docx を組成し、Day9 Vancouver Veto + Day16 拡張 regex が Cell 表記も確実に reject することの regression 保護と LLM 経由 parsing の document-of-record を確立する.

**Architecture:** Day11 確立ハイブリッド命名規約 (`expected_*` deterministic / `baseline_*` document-of-record) + Day16 確立 PMC fetch / JATS XML 解析 pattern を Cell 化. `tools/build_apa_fixture.py` を template に複写し、`_normalize_initials(cell_mode)` / `_format_authors(cell_mode)` 拡張 + `format_as_cell()` 新規追加で Cell-style (compressed initials `J.A.` + `, and ` connector + no issue number) 出力. production code 改修なし (Day16 で Vancouver Veto regex を `\((?:19|20)\d{2}[a-z]?\)` に拡張済、Cell の `(YYYY)` も既に reject).

**Tech Stack:** Python 3.11+ / pytest / python-docx / urllib (NCBI E-utilities) / Claude Sonnet 4.6 (baseline 生成のみ 1 回) / Crossref + NLM Catalog (Day15 audit logic)

**SPEC**: `docs/sessions/day17/SPEC_cell_45refs_fixture.md` (commit `c4ac9c8`)
**直接 template**: `docs/sessions/day16/PLAN_apa_45refs_fixture.md` (commit `0f0ed39`), `tools/build_apa_fixture.py` (commit `c35211f` + `d6e31c3` での `<collab>` 拡張), `tests/test_integration_apa_45refs.py` (commit `f7d5cb2` + `07eb100`)

---

## File Structure

### 新規作成

| ファイル | 責務 |
|:---|:---|
| `tools/build_cell_fixture.py` | `tools/build_apa_fixture.py` を template に複写、`_normalize_initials(cell_mode)` / `_format_authors(cell_mode)` 拡張 + `format_as_cell` 新規 + CLI 引数を Cell 領域名に変更 |
| `tests/fixtures/cell_45refs/input_References.docx` | 統合 docx (45 番号付き段落、3 領域混在) |
| `tests/fixtures/cell_45refs/expected_phase1_intermediate.json` | parser-only Phase 1 出力 (byte-strict golden) |
| `tests/fixtures/cell_45refs/baseline_phase3_resolved.json` | LLM + PubMed Phase 3 出力 (document-of-record) |
| `tests/fixtures/cell_45refs/baseline_report.md` | Phase 4 audit report (document-of-record) |
| `tests/fixtures/cell_45refs/baseline_three_class_classification.json` | Day15 三分類 audit sidecar (document-of-record) |
| `tests/fixtures/cell_45refs/README.md` | fixture の由来・規約・選定 3 論文 citation + LICENSE 明記 |
| `tests/test_integration_cell_45refs.py` | 8 tests (base 5 + test 6 + Cell 固有 2: test 7 `, and ` + test 8 三分類) |
| `docs/sessions/day17/README.md` | Day17 セッション index |
| `docs/sessions/day17/DAY17_LESSONS_LEARNED.md` | Day17 末アーカイブ + 教訓 |

### 修正

| ファイル | 修正内容 |
|:---|:---|
| `skill_package/references/USAGE_QUICKSTART.md` | バージョン 1.4 → 1.5 bump、Cell 系も検証済みであることを §X changelog に追記 |

### 改変なし (確認のみ)

`main.py`, `mdpi_parser.py`, `crossref_check.py`, `nlm_catalog_check.py`, `three_class_classifier.py`, `tools/build_apa_fixture.py` — 既存 production code / tool 全般

---

## Task 0: PMC OA 論文 3 本の最終確認 (Day17 brainstorming で確定済)

SPEC §3.1 で確定:

| 領域 | PMC ID | DOI | Journal | 出版年 | LICENSE | Refs |
|:---|:---|:---|:---|:---:|:---|---:|
| Molecular Biology | PMC13080398 | 10.1016/j.isci.2025.113995 | iScience | 2026 | CC BY 4.0 | 64 |
| Biomedical / Nanomedicine | PMC12918234 | 10.1016/j.isci.2025.114547 | iScience | 2026 | CC BY 4.0 | 114 |
| AI / Agricultural Engineering | PMC12915276 | 10.1016/j.isci.2025.114411 | iScience | 2026 | CC BY 4.0 | 55 |

XML キャッシュは既に Day17 brainstorming で取得済:
- `.cache/pmc_xml/PMC13080398.xml`
- `.cache/pmc_xml/PMC12918234.xml`
- `.cache/pmc_xml/PMC12915276.xml`

(SSL 証明書問題で live fetch 失敗時の Day16 同型 workaround として `/tmp/iscience_check_*.xml` から `.cache/pmc_xml/PMC*.xml` にコピー必要)

- [ ] **Step 1: PMC XML cache が `.cache/pmc_xml/` に揃っているか確認**

Run:
```bash
ls -la .cache/pmc_xml/PMC13080398.xml .cache/pmc_xml/PMC12918234.xml .cache/pmc_xml/PMC12915276.xml
```

Expected: 3 ファイル全て存在 (各 30KB-200KB 程度).

⚠️ 存在しない場合:
```bash
mkdir -p .cache/pmc_xml
cp /tmp/iscience_check_13080398.xml .cache/pmc_xml/PMC13080398.xml
cp /tmp/iscience_check_12918234.xml .cache/pmc_xml/PMC12918234.xml
cp /tmp/iscience_check_12915276.xml .cache/pmc_xml/PMC12915276.xml
```

⚠️ `/tmp/iscience_check_*.xml` も無い場合: SSL 証明書修復 (certifi) 後に再 fetch、もしくは Day16 で取得した Task 0 protocol に準ずる手動取得.

---

## Task 1: build_cell_fixture.py 実装

**Files:**
- Create: `tools/build_cell_fixture.py` (~420 行、build_apa_fixture.py を複写 + Cell 化)

- [ ] **Step 1: build_apa_fixture.py を template として複写**

```bash
cp tools/build_apa_fixture.py tools/build_cell_fixture.py
```

- [ ] **Step 2: モジュール docstring を Cell 版に書き換え**

`tools/build_cell_fixture.py` の冒頭 (line 1-21) を以下に置換:

```python
"""build_cell_fixture.py — PMC OA 3 論文から Cell-style 45-ref fixture を組成する.

Usage:
    python3 tools/build_cell_fixture.py \\
        --molecular-biology PMC13080398 \\
        --biomedical PMC12918234 \\
        --ai-engineering PMC12915276 \\
        --output tests/fixtures/cell_45refs/input_References.docx \\
        --refs-per-paper 15

実行手順:
    1. NCBI E-utilities efetch で 3 論文の PMC XML を取得 (.cache/pmc_xml/ にキャッシュ、
       Day16 build_apa_fixture.py と共有)
    2. 各 XML の <ref-list> から先頭 N 件を抽出
    3. JATS の <element-citation> / <mixed-citation> を Cell-style plain text に
       structured-field 経路で常に再組成 (Day16 build_apa_fixture.py の format_as_apa7
       を template に、Cell 用の compressed initials + ", and " connector + 
       no issue number + journal-volume no comma 形式に変換)
    4. python-docx で番号付き段落 (1. ~ 45.) として統合 docx 生成

依存: urllib (標準) / python-docx / xml.etree.ElementTree (標準)

Day17 Phase 0a (Task 1 implementation). Day16 build_apa_fixture.py の template を
複写・改変. 共通コード (fetch_pmc_xml / extract_references / build_docx) は再利用、
format/normalize 関数は Cell mode で改変.
"""
```

- [ ] **Step 3: `_normalize_initials` 関数を cell_mode 対応に拡張**

`_normalize_initials(given: str) -> str:` 関数 (line 280-300 付近) を以下に置換:

```python
def _normalize_initials(given: str, cell_mode: bool = False) -> str:
    """Convert given names to initials per APA 7 or Cell style.

    APA 7 (default, cell_mode=False):
        'John Anthony' -> 'J. A.'
        'JE'           -> 'J. E.'
        'K. G.'        -> 'K. G.'
    Cell mode (cell_mode=True, compressed without spaces):
        'John Anthony' -> 'J.A.'
        'JE'           -> 'J.E.'
        'K. G.'        -> 'K.G.'
    """
    given = given.strip()
    if not given:
        return ""
    # If contains dots, preserve as-is (already formatted)
    if "." in given:
        result = given.rstrip(".") + "."
        if cell_mode:
            result = result.replace(". ", ".")
        return result
    # Split by whitespace first
    tokens = given.split()
    if len(tokens) > 1:
        # 'John Anthony' style
        sep = "." if cell_mode else ". "
        return sep.join(t[0].upper() for t in tokens if t) + "."
    # Single token: could be 'J' or 'JE' (compressed)
    tok = tokens[0]
    if tok.isupper() and len(tok) >= 2:
        # 'JE' -> 'J. E.' (APA) or 'J.E.' (Cell)
        caps = re.findall(r"[A-Z]", tok)
        sep = "." if cell_mode else ". "
        return sep.join(caps) + "."
    # Single char or lowercase
    return tok[0].upper() + "."
```

- [ ] **Step 4: `_format_authors` を cell_mode 対応に拡張**

`_format_authors(cit_el: ET.Element) -> str:` 関数 (line 216-277 付近) を以下に置換:

```python
def _format_authors(cit_el: ET.Element, cell_mode: bool = False) -> str:
    """Format authors per APA 7 or Cell from <name>, <string-name>, <collab> nodes.

    Walks ``cit_el`` in document order, picking up <name>, <string-name> and
    <collab> (organizational author) children. Handles three given-name forms
    via _normalize_initials.

    APA 7 (default, cell_mode=False) combiners:
        0          -> ''
        1          -> 'Smith, J. A.'
        2          -> 'Smith, J. A., & Brown, K. L.'
        3+         -> 'Smith, A., Brown, K., & Jones, M.'

    Cell mode (cell_mode=True) combiners:
        0          -> ''
        1          -> 'Smith, J.A.'
        2          -> 'Smith, J.A., and Brown, K.L.'
        3+         -> 'Smith, A., Brown, K., and Jones, M.'

    Organizational authors (<collab>) appear as-is in both modes.
    """
    # Document-order walk: collect <name>, <string-name>, and <collab> nodes.
    name_nodes: list[ET.Element] = []
    for el in cit_el.iter():
        if el is cit_el:
            continue
        if el.tag in ("name", "string-name", "collab"):
            name_nodes.append(el)

    formatted: list[str] = []
    for n in name_nodes:
        if n.tag == "collab":
            collab_text = "".join(n.itertext()).strip()
            if collab_text:
                formatted.append(collab_text)
            continue
        surname_el = n.find("surname")
        given_el = n.find("given-names")
        surname = (surname_el.text or "").strip() if surname_el is not None else ""
        given = (given_el.text or "").strip() if given_el is not None else ""
        if not surname and not given:
            txt = (n.text or "").strip()
            if not txt:
                continue
            formatted.append(txt)
            continue
        initials = _normalize_initials(given, cell_mode=cell_mode)
        if surname and initials:
            formatted.append(f"{surname}, {initials}")
        elif surname:
            formatted.append(surname)
        elif initials:
            formatted.append(initials)

    if not formatted:
        return ""
    if len(formatted) == 1:
        return formatted[0]
    connector = ", and " if cell_mode else ", & "
    if len(formatted) == 2:
        return f"{formatted[0]}{connector}{formatted[1]}"
    return ", ".join(formatted[:-1]) + f"{connector}{formatted[-1]}"
```

- [ ] **Step 5: `format_as_apa7` を `format_as_cell` に置換 (新規関数追加)**

`format_as_apa7(cit_el: ET.Element) -> str:` 関数 (line 130-210 付近) を **削除** し、以下の `format_as_cell` で置換:

```python
def format_as_cell(cit_el: ET.Element) -> str:
    """Convert a JATS citation element to Cell-style plain text.

    CRITICAL: Always uses structured-field extraction regardless of element
    type (``element-citation`` vs ``mixed-citation``). This ensures clean
    Cell-style output even from journals whose XML lacks tail-commas between
    ``<name>`` children (e.g., iScience).

    Returns empty string when both authors AND year are missing.

    Cell style differs from APA 7:
        - Compressed initials: 'J.A.' not 'J. A.'
        - 'and' connector: 'Smith, J.A., and Brown, K.L.' not 'Smith, J. A., & Brown, K. L.'
        - No issue number: 'Cell 12, 100-110' not 'Cell, 12(3), 100-110'
        - No comma between journal and volume: 'Cell 12,' not 'Cell, 12,'
    """
    authors = _format_authors(cit_el, cell_mode=True)
    year_el = cit_el.find("year")
    year = (year_el.text or "").strip() if year_el is not None else ""

    title_el = cit_el.find("article-title")
    if title_el is None:
        title_el = cit_el.find("chapter-title")
    title = _full_text(title_el).strip() if title_el is not None else ""

    source_el = cit_el.find("source")
    journal = _full_text(source_el).strip() if source_el is not None else ""

    def _t(tag: str) -> str:
        el = cit_el.find(tag)
        return (el.text or "").strip() if el is not None and el.text else ""

    volume = _t("volume")
    # Cell style: issue number is intentionally omitted
    fpage = _t("fpage")
    lpage = _t("lpage")

    doi = ""
    for pub_id in cit_el.findall("pub-id"):
        if pub_id.get("pub-id-type") == "doi" and pub_id.text:
            doi = pub_id.text.strip()
            break

    if not authors and not year:
        return ""

    # Build: "{authors} ({year}). {title}."
    parts: list[str] = []
    head = ""
    if authors:
        head = authors
    if year:
        head = (head + " " if head else "") + f"({year})."
    elif head:
        head = head + "."
    parts.append(head.strip())

    if title:
        t = title.rstrip()
        if not t.endswith((".", "?", "!")):
            t = t + "."
        parts.append(t)

    # Cell journal block: "{journal} {volume}, {fpage}-{lpage}."
    # NOTE: Cell style uses NO comma between journal and volume (APA uses comma).
    if journal:
        jbits = journal
        if not jbits.endswith("."):
            jbits_after_journal = " "
        else:
            jbits_after_journal = " "
        if volume:
            jbits += f"{jbits_after_journal}{volume}"
        if fpage:
            pages = fpage if not lpage else f"{fpage}-{lpage}"
            jbits += f", {pages}"
        if not jbits.endswith("."):
            jbits += "."
        parts.append(jbits)

    body = " ".join(p for p in parts if p)

    if doi:
        body = body + f" https://doi.org/{doi}"

    return _collapse_whitespace(body)
```

- [ ] **Step 6: `extract_references` 内の `format_as_apa7` 呼び出しを `format_as_cell` に書き換え**

`extract_references` 関数内の以下行を変更:

```python
# 旧 (build_apa_fixture.py から複写したまま):
apa_text = format_as_apa7(cit)

# 新:
cell_text = format_as_cell(cit)
```

変数名も `apa_text` → `cell_text` に統一. その後の `if not apa_text: continue` も `if not cell_text: continue` に. `refs.append({"label": ..., "raw": apa_text})` も `"raw": cell_text` に.

- [ ] **Step 7: CLI 引数を Cell 領域名に変更**

`_parse_args` または `main` 関数の argparse セットアップで、`--psychology` / `--public-health` / `--psychology-religion` を以下に置換:

```python
ap.add_argument("--molecular-biology", required=True,
                help="PMC ID for molecular biology paper (e.g., PMC13080398)")
ap.add_argument("--biomedical", required=True,
                help="PMC ID for biomedical paper (e.g., PMC12918234)")
ap.add_argument("--ai-engineering", required=True,
                help="PMC ID for AI/engineering paper (e.g., PMC12915276)")
```

`main` 関数のループも同様に変更:
```python
for label, pmc_id in [
    ("molecular_biology", args.molecular_biology),
    ("biomedical", args.biomedical),
    ("ai_engineering", args.ai_engineering),
]:
```

- [ ] **Step 8: デフォルト出力 path を Cell 用に変更**

`_parse_args` の `--output` デフォルトを変更:
```python
ap.add_argument("--output",
                default="tests/fixtures/cell_45refs/input_References.docx",
                ...)
```

- [ ] **Step 9: 拡張版 `_normalize_initials` の unit test を実行**

```bash
python3 -c "
import sys; sys.path.insert(0, 'tools')
from build_cell_fixture import _normalize_initials

# APA 7 default (cell_mode=False) - same as Day16 tests
assert _normalize_initials('K. G.') == 'K. G.', repr(_normalize_initials('K. G.'))
assert _normalize_initials('JE') == 'J. E.', repr(_normalize_initials('JE'))
assert _normalize_initials('John Anthony') == 'J. A.', repr(_normalize_initials('John Anthony'))
assert _normalize_initials('K') == 'K.', repr(_normalize_initials('K'))
assert _normalize_initials('') == '', repr(_normalize_initials(''))

# Cell mode (cell_mode=True) - new behavior
assert _normalize_initials('K. G.', cell_mode=True) == 'K.G.', repr(_normalize_initials('K. G.', cell_mode=True))
assert _normalize_initials('JE', cell_mode=True) == 'J.E.', repr(_normalize_initials('JE', cell_mode=True))
assert _normalize_initials('John Anthony', cell_mode=True) == 'J.A.', repr(_normalize_initials('John Anthony', cell_mode=True))
assert _normalize_initials('K', cell_mode=True) == 'K.', repr(_normalize_initials('K', cell_mode=True))
assert _normalize_initials('', cell_mode=True) == '', repr(_normalize_initials('', cell_mode=True))

print('PASS: _normalize_initials 10/10 (APA 5 + Cell 5)')
"
```

Expected: `PASS: _normalize_initials 10/10 (APA 5 + Cell 5)`

⚠️ FAIL 時: Step 3 の `_normalize_initials` 実装を見直し.

- [ ] **Step 10: `--help` 実行確認**

```bash
python3 tools/build_cell_fixture.py --help
```

Expected: argparse のヘルプメッセージが表示され、`--molecular-biology`, `--biomedical`, `--ai-engineering` の 3 つの required 引数が見える.

- [ ] **Step 11: 単独 commit せず、Task 2 と一緒に Phase 0a で commit**

(Task 2 完了後に統合 commit する.)

---

## Task 2: docx 組成 + Phase 1 expected golden 生成 (Phase 0a)

**Files:**
- Create: `tests/fixtures/cell_45refs/input_References.docx`
- Create: `tests/fixtures/cell_45refs/expected_phase1_intermediate.json`

- [ ] **Step 1: 出力ディレクトリ作成 + build script 実行**

```bash
mkdir -p tests/fixtures/cell_45refs && \
python3 tools/build_cell_fixture.py \
  --molecular-biology PMC13080398 \
  --biomedical PMC12918234 \
  --ai-engineering PMC12915276 \
  --output tests/fixtures/cell_45refs/input_References.docx \
  --refs-per-paper 15
```

Expected: stdout に各領域の `extracted 15 refs` が表示され、`wrote 45 refs to tests/fixtures/cell_45refs/input_References.docx` で終了.

- [ ] **Step 2: docx sanity check**

```bash
python3 -c "
from docx import Document
d = Document('tests/fixtures/cell_45refs/input_References.docx')
print(f'Total paragraphs: {len(d.paragraphs)}')
for i, p in enumerate(d.paragraphs):
    if i < 3 or i in (15, 30) or i > len(d.paragraphs) - 3:
        print(f'{i:3d}: {p.text[:120]}')
"
```

Expected:
- Total paragraphs: 46 (heading + 45 refs)
- 段落 1-3 に `1.`, `2.`, `3.` の番号付き ref
- 段落 15 (= ref 15) / 段落 30 (= ref 30) 領域境界
- 段落末尾 3 つに `43.`, `44.`, `45.` の番号付き ref
- 各 ref テキストに `(YYYY)` (1900-2099) 含む
- 多くの ref に `, and ` (Cell connector) 含む (3+ 著者の場合)

- [ ] **Step 3: Phase 1 のみ実行**

```bash
set -a && source skill_package/.env && set +a && \
rm -rf /tmp/cell_45refs_phase1_gen && \
python3 main.py \
  tests/fixtures/cell_45refs/input_References.docx \
  --output-dir /tmp/cell_45refs_phase1_gen \
  --phase 1 2>&1 | tail -20
```

Expected: `[Stage 3-] reference blocks: 45` が表示される.

- [ ] **Step 4: Phase 1 出力件数確認**

```bash
python3 -c "
import json
data = json.load(open('/tmp/cell_45refs_phase1_gen/phase1_intermediate.json'))
blocks = data['stage3_reference_blocks']
present = {b['ref_no'] for b in blocks}
missing = set(range(1, 46)) - present
print(f'stage3_reference_blocks count: {len(blocks)}')
print(f'Missing ref_no: {sorted(missing) if missing else \"none\"}')
"
```

Expected: `stage3_reference_blocks count: 45`, `Missing ref_no: none`

⚠️ 件数が 45 でない場合 (Day16 で refs 28, 37 が `<collab>` で欠落した類似事象):
- どの ref が欠落しているか確認 → source XML の該当 ref 構造を `python3 -c "import xml.etree.ElementTree as ET; ..."` で調査
- build script の `format_as_cell` または `_format_authors` を inline fix → Step 1 から再実行

- [ ] **Step 5: Phase 1 出力を fixture に配置**

```bash
cp /tmp/cell_45refs_phase1_gen/phase1_intermediate.json \
   tests/fixtures/cell_45refs/expected_phase1_intermediate.json && \
ls -la tests/fixtures/cell_45refs/
```

Expected: `input_References.docx` + `expected_phase1_intermediate.json` 2 ファイル.

- [ ] **Step 6: Phase 0a commit (build script + docx + Phase 1 expected)**

```bash
git add tools/build_cell_fixture.py \
        tests/fixtures/cell_45refs/input_References.docx \
        tests/fixtures/cell_45refs/expected_phase1_intermediate.json && \
git commit -m "$(cat <<'EOF'
test(fixtures): add cell_45refs input docx + Phase 1 expected (Day17 Phase 0a)

PMC OA 3 iScience (Cell Press) 論文から 15 件ずつ計 45 件の Cell-style
参考文献を JATS XML から抽出し、番号付き段落 docx に統合. Phase 1 を実行
して expected_phase1_intermediate.json (parser-only deterministic golden)
を生成.

選定 PMC ID (Day17 SPEC §3.1):
  - Molecular Biology: PMC13080398 (Nrf2 / CBP)
  - Biomedical: PMC12918234 (wound healing / connexin-43)
  - AI Engineering: PMC12915276 (cotton leaf transformer)
全て iScience (Cell Press) CC BY 4.0.

tools/build_cell_fixture.py (~420 行):
  - Day16 tools/build_apa_fixture.py を template に複写
  - _normalize_initials(cell_mode=True): 'J.A.' (compressed initials)
  - _format_authors(cell_mode=True): ', and ' connector
  - format_as_cell(): 新規、issue number 省略 + journal-volume no comma
  - extract_references / build_docx / fetch_pmc_xml は共通利用 (複写)
  - CLI: --molecular-biology / --biomedical / --ai-engineering

_normalize_initials 10/10 unit test (APA 5 + Cell 5) pass.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Full pipeline 実行 + Phase 3/4 baseline 生成 (Phase 0b)

**Files:**
- Create: `tests/fixtures/cell_45refs/baseline_phase3_resolved.json`
- Create: `tests/fixtures/cell_45refs/baseline_report.md`
- Create: `tests/fixtures/cell_45refs/baseline_three_class_classification.json`
- Create: `tests/fixtures/cell_45refs/README.md`

- [ ] **Step 1: .env 健全性確認**

```bash
set -a && source skill_package/.env && set +a && \
python3 -c "import os; from main import load_env_files; load_env_files(); print('ANTHROPIC:', bool(os.environ.get('ANTHROPIC_API_KEY'))); print('NCBI:', bool(os.environ.get('NCBI_API_KEY')))"
```

Expected:
```
ANTHROPIC: True
NCBI: True
```

- [ ] **Step 2: full pipeline 実行**

```bash
set -a && source skill_package/.env && set +a && \
rm -rf /tmp/cell_45refs_baseline_gen && \
python3 main.py \
  tests/fixtures/cell_45refs/input_References.docx \
  --output-dir /tmp/cell_45refs_baseline_gen \
  --phase 4 2>&1 | tail -30
```

Expected: 約 5-15 分で完走. `/tmp/cell_45refs_baseline_gen/` に以下が生成:
- `phase1_intermediate.json`
- `phase2_structured.json`
- `phase3_resolved.json`
- `phase4_final.json`
- `report.md`
- `three_class_classification.json`
- `journal_mismatch_audit.json`

⚠️ 失敗時 (LLM rate limit / network): `--reuse-phase2` / `--reuse-phase3` で部分再実行可能.

- [ ] **Step 3: 3 baseline ファイルを fixture に配置**

```bash
cp /tmp/cell_45refs_baseline_gen/phase3_resolved.json \
   tests/fixtures/cell_45refs/baseline_phase3_resolved.json && \
cp /tmp/cell_45refs_baseline_gen/report.md \
   tests/fixtures/cell_45refs/baseline_report.md && \
cp /tmp/cell_45refs_baseline_gen/three_class_classification.json \
   tests/fixtures/cell_45refs/baseline_three_class_classification.json
```

- [ ] **Step 4: baseline メタ情報を計測**

```bash
python3 -c "
import json, re
phase3 = json.load(open('tests/fixtures/cell_45refs/baseline_phase3_resolved.json'))
res = phase3['stage4_pubmed_resolutions']
resolved = sum(1 for r in res if r.get('pmid'))
print(f'Phase 3 resolved: {resolved}/{len(res)} ({100*resolved/len(res):.1f}%)')

three = json.load(open('tests/fixtures/cell_45refs/baseline_three_class_classification.json'))
print(f'Three-class total entries: {len(three)}')
classes = {}
for c in three:
    cls = c.get('class', 'unknown')
    classes[cls] = classes.get(cls, 0) + 1
print(f'Three-class distribution: {classes}')

report = open('tests/fixtures/cell_45refs/baseline_report.md').read()
m = re.search(r'重大\s*\|\s*(\d+)\s*\|', report)
print(f'Report 重大 count: {m.group(1) if m else \"NOT FOUND\"}')
"
```

Expected (具体値は実機依存): 例として
```
Phase 3 resolved: 38/45 (84.4%)
Three-class total entries: 7
Three-class distribution: {'unknown': 6, 'A': 1}
Report 重大 count: 0
```

これらの値を Step 5 README に転記する.

- [ ] **Step 5: README.md を作成**

`tests/fixtures/cell_45refs/README.md` に以下を書き込む (Step 4 実測値で `<...>` を置換):

```markdown
# tests/fixtures/cell_45refs/

**Cell-style 45-ref 統合 baseline (Day17 由来)**

## 由来

このディレクトリは、PMC OA 3 iScience (Cell Press) 論文から 15 件ずつ計 45 件の Cell-style 参考文献を JATS XML 経由で抽出し、`tools/build_cell_fixture.py` で番号付き段落 docx に統合した fixture を、Day9 Vancouver Veto + Day16 拡張 regex の Cell 適用 regression 保護と LLM 経由 parsing の document-of-record として固定保管する.

## ソース 3 論文 (Day17 Task 0 でユーザー承認)

| 領域 | PMC ID | DOI | Journal | 出版年 | LICENSE |
|:---|:---|:---|:---|:---:|:---|
| Molecular Biology | PMC13080398 | 10.1016/j.isci.2025.113995 | iScience (Cell Press) | 2026 | CC BY 4.0 |
| Biomedical / Nanomedicine | PMC12918234 | 10.1016/j.isci.2025.114547 | iScience (Cell Press) | 2026 | CC BY 4.0 |
| AI / Agricultural Engineering | PMC12915276 | 10.1016/j.isci.2025.114411 | iScience (Cell Press) | 2026 | CC BY 4.0 |

各論文の先頭 15 件を抽出. 抽出範囲は引用論文の bibliographic information (factual data) のみで、creative expression (abstract 本文等) は含まない. PMC OA CC BY 4.0 ライセンスの帰属表示として本 table にて明示.

選定タイトル:
- PMC13080398: "Two domains of Nrf2 cooperatively bind CBP, a CREB binding protein, and synergistically activate transcription"
- PMC12918234: "Nanoencapsulated senotherapeutic compounds targeting connexin-43 for enhanced wound healing"
- PMC12915276: "Explainable transformer framework for fast cotton leaf diagnostics and fabric defect detection"

## ファイル一覧と命名規約 (Day11 ハイブリッド)

| ファイル | 種別 | サイズ |
|:---|:---|---:|
| `input_References.docx` | 入力 (tools/build_cell_fixture.py で生成) | <SIZE> |
| `expected_phase1_intermediate.json` | golden (deterministic, parser-only) | <SIZE> |
| `baseline_phase3_resolved.json` | document-of-record (LLM + PubMed variability) | <SIZE> |
| `baseline_report.md` | document-of-record (Phase 4 audit output) | <SIZE> |
| `baseline_three_class_classification.json` | document-of-record (Day15 三分類 audit sidecar) | <SIZE> |
| `README.md` | 本書 | — |

## baseline 生成時のメタ情報

- 実行日時: 2026-05-17 HH:MM (Day17 Phase 0b)
- LLM model: claude-sonnet-4-6-20260301 (`.env` の `ANTHROPIC_MODEL`)
- PubMed snapshot: 2026-05-17 (NCBI 側 latest)
- main.py version: post-Day16 (commit `705b141`)
- pipeline 実測値:
  - **Phase 3 解決件数**: <N>/45
  - **三分類分布**: A=<n>, B=<n>, C=<n>, unknown=<n>
  - **report.md 重大件数**: <N>

### Vancouver / APA fixture との対比

| 指標 | cell_45refs (Day17) | apa_45refs (Day16) | vancouver_24refs (Day11) |
|:---|:---:|:---:|:---:|
| 解決率 | <N>/45 | 25/45 = 55.6% | 22/24 = 91.7% |
| 重大件数 | <N> | 0 | 0 |
| 領域 | 分子生物 + 生医 + AI 工学 | Psychology + Public Health | 緩和ケア |
| ソース | PMC OA 合成 (Cell Press) | PMC OA 合成 (Routledge/Frontiers) | OneDrive 実機 |

## 関連 test (`tests/test_integration_cell_45refs.py`、Day17)

| # | test 名 | 性質 | 検証 |
|:---:|:---|:---|:---|
| 1 | `test_cell_45refs_routes_all_to_llm_path` | regression (deterministic) | 45 件全てが `is_mdpi_style()` で False を返す (Vancouver Veto + Day16 拡張 regex 適用) |
| 2 | `test_phase1_reference_blocks_match_expected` | byte/structural (deterministic) | Phase 1 抽出が `expected_phase1_intermediate.json` と一致 |
| 3 | `test_phase1_extracts_45_reference_blocks` | 件数 (deterministic) | block 数 = 45 |
| 4 | `test_baseline_phase3_documents_resolution_count` | document-of-record | 解決件数 = `<N>/45` 一致 |
| 5 | `test_baseline_report_documents_audit_summary` | document-of-record | report.md 重大件数 = `<N>` 一致 |
| 6 | `test_cell_paren_year_pattern_detected_in_all_refs` | parser-only | 全 45 件に `(YYYY[a-z]?)` 含む |
| 7 | `test_cell_and_author_separator_present` | structural | ≥20 件が `, and ` を含む |
| 8 | `test_baseline_three_class_classification_distribution` | document-of-record | 三分類分布 = `{A=<n>, B=<n>, C=<n>, unknown=<n>}` 一致 |

**API key 不要**: 全 8 test は parser-only もしくは fixture 直読のため、`ANTHROPIC_API_KEY` / `NCBI_API_KEY` なしで CI 実行可能.

## baseline 更新の運用 (Day11 と同型)

| 変動原因 | 検出 | 対応 |
|:---|:---|:---|
| Anthropic LLM model upgrade | test 4-5, 8 で乖離 | Day17 相当の Phase 0b retry + baseline 更新 + test 期待値更新 (別 commit) |
| PubMed/Crossref/NLM 更新 | 同上 | 同上 |
| parser/main.py 改修 | test 1-3, 6-7 fail | 意図確認、意図的なら expected 更新、意図外なら revert |

---

**作成日**: 2026-05-17 (Day17 Phase 0b)
**作成者**: Claude Code (Sonnet 4.6)
**承認**: 片山英樹 (Hideki Katayama)
**関連 SPEC**: `docs/sessions/day17/SPEC_cell_45refs_fixture.md` (commit `c4ac9c8`)
**関連 PLAN**: `docs/sessions/day17/PLAN_cell_45refs_fixture.md`
```

- [ ] **Step 6: README の `<...>` を Step 4 実測値で埋める**

Step 4 出力結果を見ながら、README 内の `<N>`, `<SIZE>`, `<n>` placeholder を実値に置換 (Edit tool で 1 つずつ).

- [ ] **Step 7: Phase 0b commit**

```bash
git add tests/fixtures/cell_45refs/baseline_phase3_resolved.json \
        tests/fixtures/cell_45refs/baseline_report.md \
        tests/fixtures/cell_45refs/baseline_three_class_classification.json \
        tests/fixtures/cell_45refs/README.md && \
git commit -m "$(cat <<'EOF'
test(fixtures): freeze cell_45refs Phase 3/4 + three_class baselines (Day17 Phase 0b)

main.py を Phase 4 まで完走させて 3 baseline ファイルを document-of-record
として凍結:
  - baseline_phase3_resolved.json (PubMed 解決 <N>/45 = <pct>%)
  - baseline_report.md (重大 <N> 件)
  - baseline_three_class_classification.json (A=<nA>, B=<nB>, C=<nC>, unknown=<nU>)

README.md に Day11 ハイブリッド命名規約 + 実測値 + LLM/PubMed snapshot
メタ情報を記録. CC BY 4.0 帰属表示として 3 iScience 論文 citation を明示.

Vancouver (91.7%) / APA (55.6%) との解決率比較を README に記載.

LLM cost: ~$<X> (Sonnet 4.6 × 45 calls).
本 fixture は CI 実行で API key 不要 (parser-only + fixture 直読 only).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Test 1-6 を Day16 から複写 + Cell 化 (Phase 1)

**Files:**
- Create: `tests/test_integration_cell_45refs.py`

- [ ] **Step 1: Day16 test ファイルを template として複写**

```bash
cp tests/test_integration_apa_45refs.py tests/test_integration_cell_45refs.py
```

- [ ] **Step 2: モジュール docstring を Cell 版に書き換え**

`tests/test_integration_cell_45refs.py` の冒頭 docstring (line 1-30 付近) を以下に置換:

```python
"""
Integration test for the Cell-style 45-ref Day17 baseline.

Background:
    Day9 (commit ab25630) introduced the Vancouver Veto in is_mdpi_style()
    so that references with `(YYYY)` paren year are routed to the LLM path
    instead of the MDPI fast-path. Day16 extended the Veto regex to
    `\\((?:19|20)\\d{2}[a-z]?\\)` to handle APA 7 disambiguation suffixes
    like `(2020a)`. Day17 adds Cell-style 45-ref fixture as the third golden
    for this regression, extending coverage to Cell Press citation style
    (compressed initials `J.A.` + `, and ` connector + no issue number).

    PMC OA 3 iScience (Cell Press) papers (Molecular Biology / Biomedical /
    AI Engineering) provide 15 refs each, all in Cell style with `(YYYY)`
    paren year. All 3 papers under CC BY 4.0.

Fixture file naming convention (Day11 hybrid):
    expected_*  : deterministic output (byte/structural match required)
    baseline_*  : variability-bearing output (LLM/PubMed-dependent)

API key requirement: NONE.
    Tests 1-3, 6-7 use parser-only paths (no LLM).
    Tests 4-5, 8 read baseline files directly without re-running Phase 2-4.

Refs: docs/sessions/day17/SPEC_cell_45refs_fixture.md (commit c4ac9c8);
      docs/sessions/day17/PLAN_cell_45refs_fixture.md;
      tests/fixtures/cell_45refs/README.md.
"""
```

- [ ] **Step 3: Fixture path 定数を Cell 用に変更**

`tests/test_integration_cell_45refs.py` 内の `FIXTURES` 周りを変更:

```python
FIXTURES = Path(__file__).parent / "fixtures" / "cell_45refs"
INPUT_DOCX = FIXTURES / "input_References.docx"
EXPECTED_PHASE1 = FIXTURES / "expected_phase1_intermediate.json"
BASELINE_PHASE3 = FIXTURES / "baseline_phase3_resolved.json"
BASELINE_REPORT = FIXTURES / "baseline_report.md"
BASELINE_THREE_CLASS = FIXTURES / "baseline_three_class_classification.json"
```

`apa_45refs` → `cell_45refs` のみ.

- [ ] **Step 4: Test 関数名 1, 3, 6 を Cell 用に変更**

| 旧 (Day16) | 新 (Day17) |
|:---|:---|
| `test_apa_45refs_routes_all_to_llm_path` | `test_cell_45refs_routes_all_to_llm_path` |
| `test_apa_paren_year_pattern_detected_in_all_refs` | `test_cell_paren_year_pattern_detected_in_all_refs` |

Tests 2, 3, 4, 5, 8 は関数名そのまま (Day16 で既に generic な名前: `test_phase1_reference_blocks_match_expected` 等).

Test 2 内の `f"Day9 Vancouver Veto regression on APA 7"` を `f"Day9 + Day16 拡張 Vancouver Veto regression on Cell-style"` に変更.

Test 6 (paren year) の説明 docstring を APA → Cell に変更:

```python
def test_cell_paren_year_pattern_detected_in_all_refs():
    """全 45 件の raw text に `(YYYY)` または `(YYYYa)` 等の paren year
    パターンが含まれることを確認 (Cell style の中核特徴を fixture data
    自体が満たすことの assert).

    Day9 + Day16 拡張 Vancouver Veto regex (`\\((?:19|20)\\d{2}[a-z]?\\)`)
    と同じ regex で検証. Cell style は通常 disambiguation suffix を
    使わないが、念のため Day16 拡張 pattern も対応する形で assert.
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()
    paren_year_pattern = re.compile(r"\((?:19|20)\d{2}[a-z]?\)")
    refs_without_paren_year = [
        b.ref_no for b in blocks
        if not paren_year_pattern.search(b.raw_text)
    ]
    assert refs_without_paren_year == [], (
        f"Cell fixture health regression: {len(refs_without_paren_year)} "
        f"ref(s) lack `(YYYY)` pattern. ref_no: {refs_without_paren_year[:5]}"
    )
```

- [ ] **Step 5: Test 4 の `EXPECTED_RESOLVED_COUNT` を Day17 実測値に更新**

`tests/fixtures/cell_45refs/README.md` から実測解決件数を取得:
```bash
grep "Phase 3 解決件数" tests/fixtures/cell_45refs/README.md
```

その値 (例: 38) を test 4 直前の module-level 定数で置換:

```python
EXPECTED_RESOLVED_COUNT = <N>  # Day17 Phase 0b 実測 (README.md 参照)
```

- [ ] **Step 6: Test 5 の `EXPECTED_REPORT_CRITICAL_COUNT` を Day17 実測値に更新**

同様に:
```bash
grep "重大件数" tests/fixtures/cell_45refs/README.md
```

その値 (例: 0) を test 5 直前で置換:

```python
EXPECTED_REPORT_CRITICAL_COUNT = <N>  # Day17 Phase 0b 実測
```

- [ ] **Step 7: 単独 commit せず、Task 5 完了後に Phase 1 で commit**

---

## Task 5: Test 7 (`, and ` separator) を Cell 化

**Files:**
- Modify: `tests/test_integration_cell_45refs.py` (test 7 を Cell 化)

- [ ] **Step 1: Test 7 関数を Cell 版に置換**

`test_apa_ampersand_author_separator_present` 関数 (Task 4 で複写された Day16 版) を以下に置換:

```python
# -----------------------------------------------------------------------------
# Test 7: Cell `, and ` author separator presence (structural)
# -----------------------------------------------------------------------------


def test_cell_and_author_separator_present():
    """45 件中、最低 20 件が `, and ` を含むことを確認.

    Cell style 規約: 3+ 著者列挙時の最終境界は `, and ` (APA 7 の
    `, & ` に相当). 本 test は fixture が Cell 規約を満たしている
    ことを保証する (build_cell_fixture.py の _format_authors(cell_mode=True)
    出力品質の test data 健全性保護).

    20 という閾値は: 単著 ref / 2 著者 ref / 組織著者 ref がある程度
    含まれることを許容しつつ、3+ 著者 ref が過半数を超えるという経験則
    に基づく.
    """
    blocks, _ = _load_phase1_blocks_with_ln_report()
    refs_with_and = [
        b.ref_no for b in blocks if ", and " in b.raw_text
    ]
    assert len(refs_with_and) >= 20, (
        f"Cell style structural regression: only {len(refs_with_and)}/45 "
        f"refs contain `, and ` (Cell author separator). "
        f"Expected >=20. Refs with separator: {refs_with_and}"
    )
```

- [ ] **Step 2: Pre-flight: 実際の `, and ` 件数を確認**

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from pathlib import Path
from main import extract_text, preprocess, split_references, detect_line_numbers
INPUT_DOCX = Path('tests/fixtures/cell_45refs/input_References.docx')
raw, _ = extract_text(INPUT_DOCX)
ln = detect_line_numbers(raw)
cleaned, _ = preprocess(raw, ln)
blocks = split_references(cleaned)
count = sum(1 for b in blocks if ', and ' in b.raw_text)
print(f'refs with \", and \": {count}/{len(blocks)}')
"
```

Expected: count ≥ 20.

⚠️ count が 20 未満の場合: build_cell_fixture.py の `_format_authors(cell_mode=True)` の connector logic を見直し. もしくは多くの ref が単著・2 著者・組織著者で構成されている可能性 → 閾値見直しを検討 (要ユーザー判断).

- [ ] **Step 3: test 7 PASS 確認**

```bash
python3 -m pytest tests/test_integration_cell_45refs.py::test_cell_and_author_separator_present -v
```

Expected: **PASS**

---

## Task 6: Test 8 (三分類分布) を Day17 実測値に更新

**Files:**
- Modify: `tests/test_integration_cell_45refs.py` (test 8 の `EXPECTED_THREE_CLASS_DISTRIBUTION` 更新)

- [ ] **Step 1: README から実測三分類分布を確認**

```bash
grep "三分類分布" tests/fixtures/cell_45refs/README.md
```

Expected: `- **三分類分布**: A=<nA>, B=<nB>, C=<nC>, unknown=<nU>` の行.

- [ ] **Step 2: `EXPECTED_THREE_CLASS_DISTRIBUTION` を実測値で置換**

`tests/test_integration_cell_45refs.py` 内の `EXPECTED_THREE_CLASS_DISTRIBUTION` 定数 (Task 4 で複写された Day16 値) を Day17 実測値に置換:

```python
EXPECTED_THREE_CLASS_DISTRIBUTION = {
    "A": <nA>,
    "B": <nB>,
    "C": <nC>,
    "unknown": <nU>,
}  # Day17 Phase 0b 実測 (README.md 参照)
```

- [ ] **Step 3: test 8 PASS 確認**

```bash
python3 -m pytest tests/test_integration_cell_45refs.py::test_baseline_three_class_classification_distribution -v
```

Expected: **PASS**

- [ ] **Step 4: 全 8 tests 一括 PASS 確認**

```bash
python3 -m pytest tests/test_integration_cell_45refs.py -v
```

Expected: **8 passed**

- [ ] **Step 5: 全既存 tests regression なし確認**

```bash
python3 -m pytest tests/ -v 2>&1 | tail -5
```

Expected: **97 passed, 1 skipped** (Day16 末 89 + 新規 8 = 97).

⚠️ 既存 test FAIL の場合: 何らかの interference (sys.path、conftest.py 等) を調査 → 原因解消後再実行.

- [ ] **Step 6: Phase 1 + 2 統合 commit (Task 4-6 すべて)**

```bash
git add tests/test_integration_cell_45refs.py && \
git commit -m "$(cat <<'EOF'
test(integration): add cell_45refs 8 tests (Day17 Phase 1+2)

Day16 test_integration_apa_45refs.py を template に複写し、Cell-style 用に
6 同型 tests + 2 Cell 固有 tests を追加:

Base 6 tests (Day16 と同型、関数名/path のみ Cell 化):
  1. test_cell_45refs_routes_all_to_llm_path
       (Day9 + Day16 拡張 Vancouver Veto regex の Cell 適用 regression 保護)
  2. test_phase1_reference_blocks_match_expected
       (Phase 1 byte/structural deterministic)
  3. test_phase1_extracts_45_reference_blocks
       (件数 = 45 deterministic)
  4. test_baseline_phase3_documents_resolution_count
       (Phase 3 PubMed 解決件数 <N>/45 document-of-record)
  5. test_baseline_report_documents_audit_summary
       (report.md 重大 <N> 件 document-of-record)
  6. test_cell_paren_year_pattern_detected_in_all_refs
       (全 45 件に `(YYYY[a-z]?)` 含む、fixture data health 保護)

Cell 固有 2 tests:
  7. test_cell_and_author_separator_present
       (>=20 件に `, and ` 含む、Cell style structural health 保護、
       APA 7 の `, & ` から Cell の `, and ` に変更)
  8. test_baseline_three_class_classification_distribution
       (Day15 三分類 audit の Cell 適用結果 {A=<nA>,B=<nB>,C=<nC>,
       unknown=<nU>} を document-of-record 凍結)

合計 8 tests 全 PASS. 既存 89 passed → 97 passed (regression なし).

API key 不要 (parser-only / fixture 直読 only).
Day11 vancouver_24refs / Day16 apa_45refs に続く 3 番目の LLM-path
用 golden fixture test.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: USAGE_QUICKSTART version bump (Phase 3)

**Files:**
- Modify: `skill_package/references/USAGE_QUICKSTART.md`

- [ ] **Step 1: 現バージョンを確認**

```bash
grep -n "^\*\*バージョン" skill_package/references/USAGE_QUICKSTART.md | head -3
```

Expected: line 7 と末尾近くに `**バージョン**: 1.4` (Day16 で bump 済).

- [ ] **Step 2: 冒頭バージョンを 1.4 → 1.5 に bump**

Edit `skill_package/references/USAGE_QUICKSTART.md`:

旧:
```
**バージョン**: 1.4
```
新:
```
**バージョン**: 1.5
```

(line 7 付近、1 箇所)

- [ ] **Step 3: 末尾の version line も 1.4 → 1.5 に bump**

旧:
```
**バージョン**: **1.4** (Day16 更新、APA 7 regression 保護 + Vancouver Veto regex 拡張)
```
新:
```
**バージョン**: **1.5** (Day17 更新、Cell 系 regression 保護を追加)
```

- [ ] **Step 4: §X 変更履歴に 1.5 entry を追記**

`### バージョン 1.4 (2026/05/17、Day16 更新)` の **直前**に以下を追記:

```markdown
### バージョン 1.5 (2026/05/17、Day17 更新)

Day17 で Day7 §9.3 long-term task の 5 件目 (Cell 系 golden fixture) を完了:

- **regression 保護対象の拡張**: Day9 Vancouver Veto + Day16 拡張 regex の検証対象を Cell-style (iScience Cell Press × 3 論文計 45 件) にも拡張. `tests/fixtures/cell_45refs/` 新設、`tests/test_integration_cell_45refs.py` に 8 tests 追加. 既存 89 passed → 97 passed.
- **Day15 三分類 audit baseline の Cell 適用記録**: `baseline_three_class_classification.json` で {A=<nA>, B=<nB>, C=<nC>, unknown=<nU>} を凍結. Crossref/NLM の SSL 問題 (Day16 と同) により大半 unknown に倒れる挙動も graceful fail-soft 設計通り.
- **新規 tool 追加**: `tools/build_cell_fixture.py` (~420 行) で PMC OA から JATS XML 経由で Cell-style docx を再現生成可能. `tools/build_apa_fixture.py` を template に複写 + `_normalize_initials(cell_mode)` / `_format_authors(cell_mode)` 拡張 + `format_as_cell` 新規追加.
- **production code 改修なし**: Day16 で Vancouver Veto regex を `\\((?:19|20)\\d{2}[a-z]?\\)` に拡張済のため、Cell の `(YYYY)` も既に reject. production code 変更ゼロで Cell 系 regression 保護を達成.

参照: `docs/sessions/day17/SPEC_cell_45refs_fixture.md`, `docs/sessions/day17/PLAN_cell_45refs_fixture.md`, `docs/sessions/day17/DAY17_LESSONS_LEARNED.md`.

```

- [ ] **Step 5: 履歴メタ情報も更新**

旧:
```
**作成日**: 2026/05/02 (バージョン 1.0)、2026/05/11 (1.1 更新)、2026/05/13 (1.2 更新)、2026/05/16 (1.3 更新)、2026/05/17 (1.4 更新)
**作成者**: Claude Opus 4.7 (1.0)、Claude Code Sonnet 4.6 (1.1, 1.2, 1.3, 1.4)
```
新:
```
**作成日**: 2026/05/02 (バージョン 1.0)、2026/05/11 (1.1 更新)、2026/05/13 (1.2 更新)、2026/05/16 (1.3 更新)、2026/05/17 (1.4 更新)、2026/05/17 (1.5 更新)
**作成者**: Claude Opus 4.7 (1.0)、Claude Code Sonnet 4.6 (1.1, 1.2, 1.3, 1.4, 1.5)
```

- [ ] **Step 6: Phase 3 commit**

```bash
git add skill_package/references/USAGE_QUICKSTART.md && \
git commit -m "$(cat <<'EOF'
docs(skill): bump USAGE_QUICKSTART to 1.5 (Day17 Cell fixture)

Day17 で実施した内容を反映:
- Day9 + Day16 拡張 Vancouver Veto regex の regression 保護対象を
  Cell-style (iScience Cell Press × 3 論文計 45 件) にも拡張.
  既存 89 passed → 97 passed.
- Day15 三分類 audit baseline の Cell 適用結果を凍結.
- tools/build_cell_fixture.py 新設 (build_apa_fixture.py を template に
  複写 + cell_mode flag 拡張).
- production code 改修ゼロで Cell 系 regression 保護達成 (Day16 で既に
  Vancouver Veto regex を APA 7 disambiguation suffix まで拡張済).

§X 変更履歴に「1.5 (Day17 更新)」 entry 追加. 履歴メタ情報も更新.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Day17 session archive (Phase 4)

**Files:**
- Create: `docs/sessions/day17/README.md`
- Create: `docs/sessions/day17/DAY17_LESSONS_LEARNED.md`

- [ ] **Step 1: Day17 README.md を作成**

Day16 (`docs/sessions/day16/README.md`) を template に、`docs/sessions/day17/README.md` に以下を書き込む:

```markdown
# docs/sessions/day17/

**Day17 セッション (2026-05-17) のアーカイブ**

このディレクトリは、pubmed-reference-resolver プロジェクトの Day17 セッション (Day7 §9.3 long-term task 残のうち APA / Cell 系 golden fixture の Cell 部分を完了した作業) で生成された記録を、永続アーカイブとして保管する.

## 内容

| ファイル | 役割 | 対象 |
|:---|:---|:---|
| `SPEC_cell_45refs_fixture.md` | brainstorming 確定設計仕様 (Day16 圧縮 Q1-Q2 + 4 sections、Task 0 で §3.1 確定値) | Claude Code 向け / プロジェクト閲覧者向け |
| `PLAN_cell_45refs_fixture.md` | writing-plans 出力の段階的実装計画 (Task 0-8 + Verification) | 実装エージェント向け |
| `DAY17_LESSONS_LEARNED.md` | Day17 全 commits の経緯 + 教訓 | プロジェクト閲覧者向け |
| `README.md` | 本書 | プロジェクト閲覧者向け |

## Day17 の特徴

Day9 で確立された **brainstorming → SPEC → writing-plans → TDD (subagent-driven) 実装** の 4 段階フローを 4 度目の本格適用 (Day9 / Day15 / Day16 に続く). Day16 で確立された pattern を直接 template として再利用 (build script / test 構造 / SPEC 章立て). production code 改修なし.

### Day16 (APA fixture) との対比

| 観点 | Day16 (APA fixture) | Day17 (Cell fixture) |
|:---|:---|:---|
| brainstorming 質問 | Q1-Q5 (5 問) + Approach (6 問) | Q1-Q2 (2 問、圧縮) |
| Task 数 | Task 0-13 + Verification | Task 0-8 + Verification (Task 4-6 で 8 tests を 3 task に統合) |
| commit 数 | 8 commits (SPEC + PLAN + Phase 0a/0b/1/2/3/4) | 8 commits (同型) |
| production code 改修 | 1 行 (Vancouver Veto regex 拡張) | なし (Day16 で既に対応済) |
| 新規 tool | build_apa_fixture.py (新規 ~410 行) | build_cell_fixture.py (build_apa_fixture.py から複写 ~420 行) |
| Phase 3 解決率 | 25/45 = 55.6% | <N>/45 = <pct>% |
| 工数 | ~3h | ~3h (Day16 template 利用で同等) |

## 達成事項 (8 commits)

| 順 | commit | 種別 | 達成 |
|:---:|:---:|:---|:---|
| (前) | `c4ac9c8` | docs(spec) | Day17 SPEC archive (427 行、12 章) |
| (前) | `<hash>` | docs(plan) | Day17 PLAN archive |
| 1 | `<hash>` | test(fixtures) | cell_45refs Phase 0a (build script + docx + Phase 1 expected) |
| 2 | `<hash>` | test(fixtures) | cell_45refs Phase 0b (Phase 3/4 baseline + 三分類 baseline + README) |
| 3 | `<hash>` | test(integration) | 8 tests (base 6 + Cell 固有 2) (Phase 1+2 統合) |
| 4 | `<hash>` | docs(skill) | USAGE_QUICKSTART 1.4 → 1.5 bump (Phase 3) |
| 5 | (本 commit) | docs(sessions) | Day17 archive (README + LESSONS) (Phase 4) |

main branch: 61 → **<N> commits** (Day16 末 → Day17 末、+<delta>).
test 健全性: 89 passed → **97 passed** (+8) / 1 skipped (条件付き、不変).

## Day7 §9.3 残タスクの達成状況 (Day17 末)

| タスク | 状態 (Day17 末) | commit |
|:---|:---:|:---:|
| Vancouver golden fixture | ✅ Day11 | `fe38298` |
| Day9 (Z) 未解決 2 件 MEDLINE 調査 | ✅ Day13 | `a2ee5ae` |
| Day13 §6 案 A: 3 分類 audit logic | ✅ Day15 | `132ffab` |
| APA 系 golden fixture | ✅ Day16 | `c35211f` 系列 |
| **Cell 系 golden fixture** | ✅ **Day17** (本日) | `<hash>` 系列 |
| MCP/hook 経由 Stage 3 配線 | ⏳ Day18+ | |
| GitHub remote 追加と push | ⏳ Day18+ | |

→ Day7 §9.3 long-term task 7 件中 **5 件完了**. 残 2 件は Day18+.

## 関連記録

完全な session 記録は別途以下に保管 (本リポジトリ外):
- `pubmed-reference-resolver-integration-chat-day17.md` (Day17 の完全記録、予定)
- `pubmed-reference-resolver-integration-chat-day{1,...,16}.md` (前日記録)

## 利用方法

### Day18 以降の参照

Day17 で確立された `tools/build_cell_fixture.py` は、追加 style fixture (Harvard / Chicago / Nature 等、Day18+ 候補) を作る際の同型テンプレートとして再利用可能 (差し替えポイント: `cell_mode` フラグ → 新 style mode フラグの追加).

詳細な改修候補は `DAY17_LESSONS_LEARNED.md` §6 (残存タスク) を参照.

### audit_report 利用者向け

Day17 以降、Cell-style reference が含まれる docx でも:
- Vancouver Veto + Day16 拡張 regex の routing 保護が継続
- Day15 三分類 audit が正常動作
- `report.md` §2 に「[3 分類化]」sub-section が Cell 入力でも自動生成

具体例として `tests/fixtures/cell_45refs/baseline_report.md` を参照.

## ディレクトリ命名規約

`docs/sessions/dayN/` 形式 (Day6 で確立、Day7-17 で継続). Day18 セッション完了後は `docs/sessions/day18/` が追加される予定.

---

**作成日**: 2026-05-17 (Day17 クロージング時)
**メンテナ**: 片山英樹 (Hideki Katayama)
```

⚠️ `<hash>`, `<N>`, `<pct>`, `<nA>`, `<nB>`, `<nC>`, `<nU>`, `<delta>` は実際の値で置換 (Phase 0b / commit ハッシュから).

- [ ] **Step 2: Day17 DAY17_LESSONS_LEARNED.md を作成**

`docs/sessions/day17/DAY17_LESSONS_LEARNED.md` に以下を書き込む (Day16 と同型構造):

```markdown
# Day17 LESSONS LEARNED

**Day17 セッション (2026-05-17)**: Cell 系 45-ref golden fixture 追加 (Day7 §9.3 long-term task 残 5 件目を完了)

---

## 1. セッション概要

### 1.1 背景

Day16 末時点で Day7 §9.3 long-term task の残 3 件 (Cell fixture、MCP/hook 配線、GitHub push) のうち、ユーザーは Day17 task として **Cell 系 golden fixture** を選択. Day16 LESSONS §7 パターン 1 のテンプレート (Day17 として Cell 系 fixture) を起点として、brainstorming → SPEC → writing-plans → TDD (subagent-driven-development) の 4 段階フローを適用.

### 1.2 brainstorming 段階 (Day16 圧縮版)

Day16 で Q1-Q5 + Approach の 6 質問を経て確立されたパターンを継承するため、Day17 では 2 質問のみに圧縮:

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q1 | Day16 と同じ枠組みで進めるか | (同型) PMC OA + 45 件 + 3 領域 + 8 tests |
| Q2 | PMC OA 論文選定 (Cell-style 採用 + CC BY) | 3 iScience CC BY 4.0 papers |

### 1.3 SPEC (commit `c4ac9c8`)

427 行の SPEC を `docs/sessions/day17/SPEC_cell_45refs_fixture.md` に archive. Day16 SPEC を template に Cell 差分を反映した 12 章構成.

### 1.4 PLAN (commit `<hash>`)

`docs/sessions/day17/PLAN_cell_45refs_fixture.md` に archive. Task 0-8 + Verification で構成. Day16 PLAN を template に同型 task は集約 (Day16 では Task 4-11 で 8 tests を 8 task に分割していたが、Day17 では Task 4-6 で 8 tests を 3 task に統合).

---

## 2. 実装段階の経緯 (<N> commits)

### Phase 0a: docx 組成 + Phase 1 expected (commit `<hash>`)

- Task 0 (PMC XML cache 確認): 既に Day17 brainstorming で `/tmp/iscience_check_*.xml` 経由で取得済の 3 PMC 論文を `.cache/pmc_xml/PMC*.xml` にコピー.
- Task 1 (build script 実装): `tools/build_apa_fixture.py` を `tools/build_cell_fixture.py` に複写、`_normalize_initials(cell_mode)` / `_format_authors(cell_mode)` 拡張、`format_as_cell()` 新規追加. 10/10 unit test (APA 5 + Cell 5) 全 PASS.
- Task 2 (docx 組成 + Phase 1 expected): 45/45 件抽出成功 (Day16 で発生した `<collab>` 欠落事象は Day16 で既に build script 修正済のため再発しない).

### Phase 0b: full pipeline + 3 baselines (commit `<hash>`)

- Task 3: `main.py --phase 4` で full pipeline 実行 (LLM cost ~$<X>).
- 実測値:
  - Phase 3 解決 <N>/45 = <pct>%
  - 重大 <N> 件
  - 三分類分布: A=<nA>, B=<nB>, C=<nC>, unknown=<nU>
- README.md に Vancouver / APA との対比表を含む包括的メタ情報を記載.

### Phase 1+2: 8 tests (commit `<hash>`)

- Task 4-6: `tests/test_integration_apa_45refs.py` を template に複写、6 tests の関数名/path/期待値を Cell 化、test 7 を `, & ` → `, and ` に変更、test 8 の三分類期待値を Day17 実測値に更新.
- 全 8 tests PASS、89 → 97 passed (regression なし).

### Phase 3: USAGE_QUICKSTART 1.5 bump (commit `<hash>`)

- §X 変更履歴に「1.5 (Day17 更新)」 entry 追加.

### Phase 4: Day17 archive (本 commit)

- README.md / DAY17_LESSONS_LEARNED.md を archive.

---

## 3. 設計判断と検証

### 3.1 brainstorming 圧縮の根拠

Day16 で 6 質問 (Q1-Q5 + Approach) を経て決定した枠組み (PMC OA + 45 件 + 3 領域 + 8 tests + Day11 ハイブリッド規約) が Day17 でもそのまま適用可能だったため、Q1 で「Day16 同型」確認のみで進行. Q2 で 3 PMC ID 選定のみ. **brainstorming 効率化**は Day9-15-16 で確立したフローの成熟効果.

### 3.2 PMC OA 選定: iScience 一本化の根拠

Day16 では Routledge + T&F + Frontiers の 3 publisher にまたがり license 統一に苦労した. Day17 では iScience 内で 3 領域 (Molecular Biology + Biomedical + AI Engineering) を確保でき、全 CC BY 4.0. publisher 内多様性 vs publisher 多様性のトレードオフがある中、license 一貫性を優先.

### 3.3 build script の cell_mode flag 設計

`format_as_apa7` を完全コピーして `format_as_cell` に変換するのではなく、`_normalize_initials` / `_format_authors` に `cell_mode` flag を追加する設計を採用. 利点:
- ロジック重複を最小化 (initials 抽出 / collab 処理 / 空白対応の 90% は共通)
- 将来 Chicago / Nature style 追加時に flag 拡張 (`style="apa7"|"cell"|"chicago"`) で対応可能

## 4. 実機検証結果

### 4.1 PMC OA 3 論文 (確定値)

| 領域 | PMC ID | DOI | Journal | LICENSE |
|:---|:---|:---|:---|:---|
| Molecular Biology | PMC13080398 | 10.1016/j.isci.2025.113995 | iScience | CC BY 4.0 |
| Biomedical / Nanomedicine | PMC12918234 | 10.1016/j.isci.2025.114547 | iScience | CC BY 4.0 |
| AI / Agricultural Engineering | PMC12915276 | 10.1016/j.isci.2025.114411 | iScience | CC BY 4.0 |

### 4.2 Phase 3 PubMed 解決率

| Fixture | 解決率 | 主因 (推定) |
|:---|:---:|:---|
| vancouver_24refs (Day11) | 22/24 = 91.7% | 緩和ケア医学、PubMed coverage 高 |
| apa_45refs (Day16) | 25/45 = 55.6% | 社会心理 + 政府文書 + 書籍 |
| **cell_45refs (Day17)** | **<N>/45 = <pct>%** | 分子生物 + 生医 + 工学 |

### 4.3 三分類分布

`baseline_three_class_classification.json`:
- **A** (真の捏造): <nA> 件
- **B** (MEDLINE 非収録誌): <nB> 件
- **C** (収録誌 indexing 漏れ): <nC> 件
- **unknown** (network error fail-soft): <nU> 件

Day16 同様、SSL 問題により大半 unknown に倒れる. Day18+ で SSL 解消後再生成すれば B/C 分布が出現する見込み.

---

## 5. 教訓 (D17-N)

### 5.1 D17-1: brainstorming の template 効果

Day16 で確立されたパターンを Day17 で **質問 6 → 2 に圧縮**できた事例. 効果:
- brainstorming 時間: Day16 ~30min → Day17 ~10min
- ユーザー認知負荷: 6 multi-choice → 2 multi-choice
- 設計品質: 同等 (template が枠を提供するため判断品質を維持)

**学び**: 同型 task 連続実施では、前回 SPEC を「設計言語の参照点」として明示的に template 化することで、brainstorming 段階を大幅短縮可能. ただし「同型と思って実は差分があった」リスクがあるため、最低 1 質問は差分確認に充てる必要あり (Day17 Q2 の論文選定確認がこれに相当).

### 5.2 D17-2: production code 改修ゼロでの fixture 追加

Day16 で Vancouver Veto regex を `\((?:19|20)\d{2}[a-z]?\)` に拡張したことで、Cell-style の `(YYYY)` も自動的に reject される結果となり、Day17 では production code 改修ゼロで Cell fixture 追加を達成. **Day16 D16-1 教訓の波及効果**として記録.

**学び**: regression 保護 fixture を追加する際、前 fixture で発見・修正した invariant が新 fixture でも有効か事前検証することで、production code 改修の要否を予測可能.

---

## 6. 残存タスク (Day18 以降)

### 6.1 Day7 §9.3 long-term task の達成状況 (Day17 末)

| タスク | 状態 | 残し方 |
|:---|:---:|:---|
| Vancouver golden fixture | ✅ Day11 | — |
| Day9 (Z) 未解決 2 件 MEDLINE 調査 | ✅ Day13 | — |
| Day13 §6 案 A: 3 分類 audit logic | ✅ Day15 | — |
| APA 系 golden fixture | ✅ Day16 | — |
| Cell 系 golden fixture | ✅ Day17 (本日) | — |
| **MCP/hook 経由 Stage 3 配線** | ⏳ Day18+ | 設計議論大、複数セッション |
| **GitHub remote 追加と push** | ⏳ Day18+ | secret scan + README 整備、外部公開判断要 |

### 6.2 Day17 が生成した新規候補

- [ ] **Harvard / Chicago / Nature style fixture** (Day16-17 と同型 pattern を他 style に適用、`_format_authors(style=...)` 拡張)
- [ ] **iScience の領域追加** (現状 3 領域 → 5 領域、Climate / Materials Science 等追加)
- [ ] **三分類 audit の SSL 問題解消後 baseline 再生成** (Day16-17 とも未解消、共通課題)
- [ ] **build_cell_fixture.py のテスト追加** (`_normalize_initials(cell_mode=True)` 5 cases を `tests/` 配下に正式昇格)

### 6.3 Day18+ 推奨着手順

1. GitHub remote + push (secret scan 要、公開判断要、~2h、最高優先度)
2. 三分類 audit の SSL 問題解消後 baseline 再生成 (中優先度、~1-2h)
3. Harvard 系 fixture (中優先度、~3h、Day17 template 再利用)
4. MCP/hook 経由 Stage 3 配線 (設計議論大、複数セッション、最後)

---

## 7. 次セッション再開時のプロンプトテンプレート

### パターン 1: Day18 として GitHub remote + push

```
Day18 として、本プロジェクトを GitHub に push します.
remote 設定 → 既存 <N> commits + 全 fixture (mdpi_149refs,
vancouver_24refs, apa_45refs, cell_45refs, three_class_classification)
を含めて push. 公開リポジトリ vs プライベート の選択、README.md の整備、
.gitignore 最終確認、secret scan を含めて段階確認しながら進めて
ください.
```

### パターン 2: Day18 として三分類 baseline 再生成

```
Day18 として、Day16-17 で凍結した apa_45refs / cell_45refs 三分類
baseline の SSL 問題解消後再生成を実施します. Mac Python の SSL 証明書
を修復 (certifi 等)、Crossref + NLM 経由で B/C 分類が確実に出現する
よう確認してから両 baseline を更新. test 8 期待値も更新.
```

### パターン 3: Day18 として Harvard fixture

```
Day18 として、Harvard style の golden fixture を新規追加します
(Day16 apa_45refs / Day17 cell_45refs と同型 pattern). PMC OA Harvard-style
採用論文 3 本選定し、tools/build_harvard_fixture.py を build_cell_fixture.py
から template 化. cell_mode flag を style="harvard" 等に拡張する設計も
検討.
```

### パターン 4: Day18 として MCP/hook 配線 (大型)

```
Day18 として、Stage 3 (Claude UI 起動の自動配線) を実装します.
MCP server / hook 経由で Claude Code → ローカル command → docx 入力 →
audit 出力 → Claude UI への結果返却パイプラインを設計. 議論大規模の
ため SPEC 段階まで複数セッション覚悟.
```

---

**記録完了日**: 2026-05-17 (Day17)
**記録者**: Claude Code (Sonnet 4.6)
**対応 Day17 完全記録 (リポジトリ外)**: `pubmed-reference-resolver-integration-chat-day17.md` (Claude Opus 作成予定)
**ステータス**: Day17 archive 完成、Day18 着手準備完了 (4 パターンプロンプトあり)
```

⚠️ `<N>`, `<hash>`, `<X>`, `<pct>`, `<nA>` 等の placeholder は実際の値で置換.

- [ ] **Step 3: Phase 4 commit**

```bash
git add docs/sessions/day17/PLAN_cell_45refs_fixture.md \
        docs/sessions/day17/README.md \
        docs/sessions/day17/DAY17_LESSONS_LEARNED.md && \
git commit -m "$(cat <<'EOF'
docs(sessions): archive day17 cell_45refs fixture session

Day17 セッション完了に伴う archive:
- README.md: day17/ index, Day7 §9.3 残タスク達成状況 5/7 表
- DAY17_LESSONS_LEARNED.md: 全 commits 経緯 + 教訓 D17-1, D17-2
  (brainstorming template 効果 + production code 改修ゼロ事例)
- PLAN_cell_45refs_fixture.md: writing-plans 出力の実装計画

主成果:
- cell_45refs fixture (PMC OA 3 iScience CC BY 4.0 × 15 件 = 45 件)
- 8 tests 追加 (89 → 97 passed)
- production code 改修ゼロ (Day16 拡張 regex の波及効果)
- tools/build_cell_fixture.py 新設 (build_apa_fixture.py から template 複写)

Day7 §9.3 long-term task 7 件中 5 件完了 (Vancouver, MEDLINE 調査,
3 分類 audit, APA fixture, Cell fixture). 残 2 件 (MCP 配線, GitHub
push) は Day18 以降.

main branch: 61 → <N> (+<delta>), test: 89 passed → 97 passed (+8) / 1 skipped.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Verification (全 Task 完了後の最終確認)

- [ ] **V1: 全 test pass**

```bash
python3 -m pytest tests/ -v 2>&1 | tail -5
```
Expected: **97 passed, 1 skipped** (Day16 末 89 + 新規 8).

- [ ] **V2: SPEC §8 12 完了条件すべて満たす**

`docs/sessions/day17/SPEC_cell_45refs_fixture.md` §8 の 12 項目を確認:

```bash
echo "[1]" && python3 tools/build_cell_fixture.py --help 2>&1 | head -3 && \
echo "[2]" && python3 -c "from docx import Document; d=Document('tests/fixtures/cell_45refs/input_References.docx'); print(f'paragraphs={len(d.paragraphs)}')" && \
echo "[3]" && python3 -c "import json; d=json.load(open('tests/fixtures/cell_45refs/expected_phase1_intermediate.json')); print(f'stage3={len(d[\"stage3_reference_blocks\"])}')" && \
echo "[4-7]" && ls -la tests/fixtures/cell_45refs/baseline_*.json tests/fixtures/cell_45refs/baseline_*.md tests/fixtures/cell_45refs/README.md && \
echo "[8]" && python3 -m pytest tests/test_integration_cell_45refs.py --collect-only -q 2>&1 | tail -2 && \
echo "[9]" && python3 -m pytest tests/test_integration_cell_45refs.py -v 2>&1 | tail -3 && \
echo "[10]" && python3 -m pytest tests/ -v 2>&1 | tail -2 && \
echo "[11]" && ls docs/sessions/day17/SPEC_cell_45refs_fixture.md && \
echo "[12]" && ls docs/sessions/day17/{README,DAY17_LESSONS_LEARNED,PLAN}.md
```

Expected: 全 12 条件 OK.

- [ ] **V3: commit count 確認**

```bash
git log --oneline | head -10
```
Expected: 最新 commit は `docs(sessions): archive day17 ...`、Day17 中の commit 数は 8.

- [ ] **V4: 最終 git status**

```bash
git status
```
Expected: `nothing to commit, working tree clean` (.DS_Store は untracked のまま OK).

---

## Notes for Implementing Agent

- **TDD 強度**: Phase 1+2 (Task 4-6) は厳密 TDD ではなく fixture-driven testing pattern (Day9-16 で確立). fixture が既に在る前提で test を書き、即 PASS する想定.
- **LLM cost**: Task 3 (Phase 0b full pipeline) は 1 回限り、~$0.5-1.0. 途中失敗時は `--reuse-phase2` / `--reuse-phase3` で部分再実行可.
- **環境依存**: Task 2 Step 4 / Task 3 Step 4 で出力件数や解決数が SPEC 想定と異なる場合、README に実測値を反映 + test 期待値に反映 (SPEC は変更しない; SPEC は意図、README+test は実装記録).
- **PMC fetch のキャッシュ**: `.cache/pmc_xml/` は `.gitignore` 済 (Day16 で追加). Day17 で新 PMC ID 取得時もここに保存される.
- **Day11 規約遵守**: `expected_*` / `baseline_*` の区別は絶対遵守. test 4-5, 8 は baseline_ → document-of-record として「予想 != 実測」時には baseline 側を更新.
- **Day16 PLAN との task 分割差**: Day16 では tests を 8 task (Task 4-11) に分割していたが、Day17 では 3 task (Task 4-6) に統合. Day16 で確立された structure を理解した上での効率化.
- **共通コード再利用方針**: build_apa_fixture.py と build_cell_fixture.py は **複写 (独立保持)**. インポート依存は将来の片方改修時にもう片方が壊れるリスクのため避ける.
- **`<collab>` 対応の必要性**: Day16 で `_format_authors` に `<collab>` 対応を追加済 (commit `c35211f` 内). Day17 は build_apa_fixture.py を template に複写するため自動継承される.
