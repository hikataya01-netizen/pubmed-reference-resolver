"""pubmed-reference-resolver: 査読用の References 逆引き検索スキル本体。

Phase 1 (MVP) + Phase 2 (Stage 3 LLM構造化) まで実装済み。
Stage 4 (PubMedカスケード検索) / Stage 5 (出力合成) は後続フェーズで追加。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path


# =============================================================================
# .env ファイル自動読み込み (スキル/CLI どちらでも利用可)
# =============================================================================

def _parse_env_file(path: Path) -> dict[str, str]:
    """`KEY=VALUE` 形式の .env ファイルを解析する。

    対応: コメント行 (# 始まり) / 空行 / `export KEY=VAL` 形式 /
    値のクォート (" or ') / inline comment は非対応 (値の中に # OK)
    """
    out: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return out
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        if k:
            out[k] = v
    return out


def load_env_files(input_path: Path | None = None) -> list[str]:
    """複数の候補パスから .env を探索して os.environ に注入する。

    優先度 (後勝ち = 上書きしないが先頭優先):
      1. {スキル配置ディレクトリ}/.env        (main.py と同じ場所)
      2. $HOME/.pubmed-reference-resolver.env (ユーザー専用、ホーム直下)
      3. {カレントディレクトリ}/.env          (呼び出し元のカレント)
      4. {入力ファイルのディレクトリ}/.env    (入力PDFと同じフォルダ)

    既に os.environ にセット済みのキーは上書きしない (ユーザー指定が最優先)。
    """
    candidates: list[Path] = []
    # 1. skill directory
    try:
        candidates.append(Path(__file__).resolve().parent / ".env")
    except NameError:
        pass
    # 2. home
    candidates.append(Path.home() / ".pubmed-reference-resolver.env")
    # 3. cwd
    candidates.append(Path.cwd() / ".env")
    # 4. input file dir
    if input_path is not None:
        try:
            candidates.append(input_path.resolve().parent / ".env")
        except OSError:
            pass

    loaded_from: list[str] = []
    for p in candidates:
        if not p.is_file():
            continue
        kv = _parse_env_file(p)
        added = 0
        for k, v in kv.items():
            if k not in os.environ and v:
                os.environ[k] = v
                added += 1
        if added:
            loaded_from.append(f"{p} ({added} vars)")
    return loaded_from


# =============================================================================
# Stage 1: 抽出 (PDF / DOCX / TXT)
# =============================================================================

def extract_text(path: Path) -> tuple[str, str]:
    """入力ファイルから生文字列を抽出する。

    Returns: (raw_text, source_type)
    """
    ext = path.suffix.lower()
    if ext == ".pdf":
        return _extract_pdf(path), "pdf"
    if ext == ".docx":
        return _extract_docx(path), "docx"
    if ext in (".txt", ".md"):
        return path.read_text(encoding="utf-8"), "txt"
    raise ValueError(f"Unsupported extension: {ext}")


def _extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError("pypdf is required. Install with: pip install pypdf") from e
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _extract_docx(path: Path) -> str:
    try:
        import docx  # python-docx
    except ImportError as e:
        raise RuntimeError("python-docx is required. Install with: pip install python-docx") from e
    doc = docx.Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


# =============================================================================
# Stage 2.5: 行番号統計検出
# =============================================================================

@dataclass
class LineNumberReport:
    detected: bool
    count: int
    min_val: int | None
    max_val: int | None
    values: list[int]              # LIS構成値（元テキスト出現順）
    spans: list[tuple[int, int]]   # 各値の(start, end)位置
    total_candidates: int          # 3桁孤立整数の全候補数
    rationale: str


def _longest_increasing_subsequence(arr: list[int]) -> list[int]:
    """狭義単調増加のLISを構成するインデックス列を返す（O(n^2)、nは最大でも数百）。"""
    n = len(arr)
    if n == 0:
        return []
    dp = [1] * n
    prev = [-1] * n
    for i in range(n):
        for j in range(i):
            if arr[j] < arr[i] and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                prev[i] = j
    end = max(range(n), key=lambda k: dp[k])
    out: list[int] = []
    cur = end
    while cur != -1:
        out.append(cur)
        cur = prev[cur]
    return out[::-1]


def detect_line_numbers(
    text: str,
    *,
    min_run_length: int = 10,
    year_min: int = 1900,
    year_max: int = 2099,
) -> LineNumberReport:
    """テキストから統計的に行番号列を検出する。

    判定基準 (いずれも満たす場合のみ行番号と認定):
    - 空白で囲まれた 3桁の孤立整数群から LIS を抽出
    - LIS長が min_run_length 以上
    - 年号範囲 (year_min-year_max) 外
    - 値が3桁 (100-999)
    """
    candidates: list[tuple[int, int, int]] = []  # (start, end, value)
    for m in re.finditer(r"(?<!\S)(\d+)(?!\S)", text):
        try:
            v = int(m.group(1))
        except ValueError:
            continue
        if not (100 <= v <= 999):
            continue
        if year_min <= v <= year_max:
            continue
        candidates.append((m.start(), m.end(), v))

    if not candidates:
        return LineNumberReport(
            detected=False, count=0, min_val=None, max_val=None,
            values=[], spans=[], total_candidates=0,
            rationale="3桁の孤立整数候補が存在しない",
        )

    values_in_pos_order = [c[2] for c in candidates]
    lis_idx = _longest_increasing_subsequence(values_in_pos_order)

    if len(lis_idx) < min_run_length:
        return LineNumberReport(
            detected=False, count=0, min_val=None, max_val=None,
            values=[], spans=[], total_candidates=len(candidates),
            rationale=f"LIS長={len(lis_idx)} < 閾値{min_run_length}",
        )

    selected = [candidates[i] for i in lis_idx]
    vals = [c[2] for c in selected]
    spans = [(c[0], c[1]) for c in selected]

    return LineNumberReport(
        detected=True,
        count=len(selected),
        min_val=min(vals),
        max_val=max(vals),
        values=vals,
        spans=spans,
        total_candidates=len(candidates),
        rationale=(
            f"LIS長={len(vals)}（≥{min_run_length}）、"
            f"値域 {min(vals)}-{max(vals)}、"
            f"全体候補{len(candidates)}件中 {len(vals)}件が単調増加列"
        ),
    )


# =============================================================================
# Stage 2: 軽量前処理
# =============================================================================

@dataclass
class PreprocessTrace:
    hyphen_bridged_removed: int     # 「-{空白}行番号{改行}」結合除去の件数
    standalone_removed: int         # 独立行番号除去の件数
    soft_linebreaks_joined: int     # 行連結件数
    ref_blocks_found: int           # 粗い参照境界検出で得たブロック数
    header_stripped: bool           # "References" ヘッダー削除の有無


def _normalize_whitespace_and_chars(text: str) -> str:
    """Unicode正規化 (NFKC) と改行統一、連続空白の軽い整理。"""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\u00A0]+", " ", text)   # タブや全角空白相当を半角空白化
    return text


def _strip_pre_references(text: str) -> tuple[str, bool]:
    """`References` / `REFERENCES` / `Bibliography` ヘッダーより前を除去する。

    pypdfの抽出はページを1行インライン化するため、ヘッダーが独立行にない
    ケースも想定して3段階で検出する。
    """
    # Case 1: 独立行のヘッダー
    m = re.search(r"(?im)^\s*(references|bibliography)\s*$", text)
    if m:
        return text[m.end():].lstrip(), True
    # Case 2: インライン "References 1. Author..." 形式
    m = re.search(r"(?i)\b(references|bibliography)\s+(?=\d+\.\s+[A-Z])", text)
    if m:
        return text[m.end():].lstrip(), True
    # Case 3: 最初の "1. {大文字}" にジャンプ（保守的フォールバック）
    m = re.search(r"(?<![\d.])1\.\s+[A-Z]", text)
    if m:
        return text[m.start():], False
    return text, False


def _build_linenum_alt(values: list[int]) -> str:
    return "(?:" + "|".join(re.escape(str(v)) for v in sorted(set(values), reverse=True)) + r")"


def preprocess(text: str, ln_report: LineNumberReport) -> tuple[str, PreprocessTrace]:
    """行番号除去・ハイフネーション救済・行連結を行う。

    実行順序（重要）:
    ① 「-{空白}<行番号>{改行}{空白}」→「-」  … ハイフネーション優先救済
    ② 「{空白}<行番号>{改行}」→「{改行}」   … 独立行末行番号除去
    ③ 参照境界 (^\\d+\\. ) 以外の改行を空白に … 参照内改行を吸収
    """
    original = text
    text = _normalize_whitespace_and_chars(text)
    text, header_stripped = _strip_pre_references(text)

    hyphen_bridged_removed = 0
    standalone_removed = 0

    if ln_report.detected:
        alt = _build_linenum_alt(ln_report.values)
        # ① ハイフネーション橋渡し（インライン空白 / 改行いずれも対応）
        # 例: "gpsych- 570 2022"   → "gpsych-2022"   (DOI 復元)
        # 例: "RELA- 588 TIONSHIP" → "RELA-TIONSHIP" (ソフトハイフンは保持、LLMが吸収)
        # 例: "- 570\n2022"         → "-2022"         (改行跨ぎ)
        hyphen_pattern = re.compile(rf"-\s+{alt}\b\s+")
        text, n1 = hyphen_pattern.subn("-", text)
        hyphen_bridged_removed = n1

        # ② 独立行番号 (インライン or 行末)
        # 例: "GLOBOCAN 567 estimates" → "GLOBOCAN estimates"
        # 例: "caac.21834. 569 2. Wang" → "caac.21834. 2. Wang"
        standalone_pattern = re.compile(rf"\s+{alt}\b(?=\s|$|\Z)")
        text, n2 = standalone_pattern.subn("", text)
        standalone_removed = n2

    # 後処理: 連続空白を単一空白に、改行周りの空白を整理
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)

    # ③ 参照内ソフト改行の吸収
    text, soft_joined = _join_soft_linebreaks(text)

    # 参照ブロック数を概算（インライン化後は `\d+\. {大文字}` を数える）
    blocks = re.findall(r"(?<![\d.])\d+\.\s+[A-Z]", text)

    trace = PreprocessTrace(
        hyphen_bridged_removed=hyphen_bridged_removed,
        standalone_removed=standalone_removed,
        soft_linebreaks_joined=soft_joined,
        ref_blocks_found=len(blocks),
        header_stripped=header_stripped,
    )
    return text, trace


def _join_soft_linebreaks(text: str) -> tuple[str, int]:
    """参照マーカー (^\\d+\\. ) で始まる行以外の改行を空白に置換する。"""
    lines = text.split("\n")
    out: list[str] = []
    joined = 0
    ref_marker = re.compile(r"^\s*\d+\.\s")
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            continue
        if ref_marker.match(stripped):
            out.append(stripped.lstrip())
        else:
            if out:
                out[-1] = out[-1].rstrip() + " " + stripped.lstrip()
                joined += 1
            else:
                out.append(stripped.lstrip())
    return "\n".join(out), joined


# =============================================================================
# 粗い参照境界検出
# =============================================================================

@dataclass
class ReferenceBlock:
    ref_no: int
    raw_text: str
    char_length: int


def split_references(cleaned: str) -> list[ReferenceBlock]:
    """前処理済みテキストから参照ブロックを切り出す。

    Stage 3 (LLM構造化) の入力になる粒度。

    マッチ条件 (2通り):
      (a) 標準: 数字 + ピリオド + 空白 + 大文字  (例: "1. Smith")
      (b) 無ピリオド型: 数字 + 空白 + 大文字      (例: "1 Smith" MDPI特殊PDF由来)

    誤検出抑制:
    - 直前が数字/ピリオドの場合は除外 (volume/issue "10." 等)
    - 候補値から LIS (最長単調増加部分列) を抽出
    - LISが参照マーカー群、外れ値は本文内の誤マッチ (例: "39 Years") と判定
    """
    # より寛容な候補検出: ピリオド or 空白で数字と著者を区切る
    # NOTE: lookahead allows lowercase prefixes for Dutch/French surnames
    # (van, de, du, den, von) which start with lowercase letters.
    # Without this, refs like "40. van der Biessen" are silently dropped.
    matcher = re.compile(
        r"(?<![\d.])(\d+)[\.\s]+"
        r"(?=[A-Z]|van\s|de\s+[A-Z]|du\s+[A-Z]|den\s+[A-Z]|von\s+[A-Z])"
    )
    candidates = [(m.start(), m.end(), int(m.group(1))) for m in matcher.finditer(cleaned)]
    if not candidates:
        return []

    # 値列から LIS を抽出 (誤マッチ除去)
    values = [c[2] for c in candidates]
    lis_idx = _longest_increasing_subsequence(values)
    if not lis_idx:
        return []
    selected = [candidates[i] for i in lis_idx]

    # 健全性チェック: LIS が1 or 2から始まり、かつ3件以上 (単発誤検出を排除)
    if selected[0][2] > 3 or len(selected) < 2:
        # フォールバック: 標準regex のみで再試行
        standard = re.compile(
            r"(?<![\d.])(\d+)\.\s+"
            r"(?=[A-Z]|van\s|de\s+[A-Z]|du\s+[A-Z]|den\s+[A-Z]|von\s+[A-Z])"
        )
        strict_hits = list(standard.finditer(cleaned))
        if not strict_hits:
            return []
        selected = [(m.start(), m.end(), int(m.group(1))) for m in strict_hits]

    blocks: list[ReferenceBlock] = []
    for i, (start, end, val) in enumerate(selected):
        next_start = selected[i + 1][0] if i + 1 < len(selected) else len(cleaned)
        body = cleaned[end:next_start].strip()
        blocks.append(ReferenceBlock(
            ref_no=val,
            raw_text=body,
            char_length=len(body),
        ))
    return blocks


# =============================================================================
# Stage 3: LLM による構造化
# =============================================================================

LLM_MODEL = "claude-sonnet-4-6"
LLM_PROMPT_PATH = Path(__file__).parent / "references" / "llm_parsing_prompt.md"


def _load_system_prompt() -> str:
    """`references/llm_parsing_prompt.md` から SYSTEM PROMPT セクションを切り出す。"""
    if not LLM_PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt template missing: {LLM_PROMPT_PATH}")
    raw = LLM_PROMPT_PATH.read_text(encoding="utf-8")
    m = re.search(r"## SYSTEM PROMPT.*?\n(.*?)\n---\n", raw, flags=re.DOTALL)
    if not m:
        raise ValueError("Could not locate SYSTEM PROMPT section in prompt template")
    return m.group(1).strip()


def structure_reference(
    client,
    system_prompt: str,
    block: "ReferenceBlock",
    ln_report: LineNumberReport,
    *,
    max_tokens: int = 1500,
) -> dict:
    """1参照ブロックを LLM に投入し構造化JSONを得る。プロンプトキャッシュ利用。"""
    min_val = ln_report.min_val if ln_report.detected else "none"
    max_val = ln_report.max_val if ln_report.detected else "none"
    user_msg = (
        f"REF_NO: {block.ref_no}\n"
        f"RAW: {block.raw_text}\n"
        f"HINTS:\n"
        f"- detected_line_numbers_range: {min_val}-{max_val}\n"
        f"- hyphen_bridge_rescued: true\n"
    )
    resp = client.messages.create(
        model=LLM_MODEL,
        max_tokens=max_tokens,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_msg}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    # JSON ブロック取り出し (```json ... ``` が付くケースに備える)
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.DOTALL).strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        return {
            "ref_no": block.ref_no,
            "_parse_error": f"JSON decode failed: {e}",
            "_raw_response": text,
            "parsing_confidence": "low",
        }
    # 使用量メタ（デバッグ用）
    obj["_usage"] = {
        "input_tokens": getattr(resp.usage, "input_tokens", None),
        "output_tokens": getattr(resp.usage, "output_tokens", None),
        "cache_creation_input_tokens": getattr(resp.usage, "cache_creation_input_tokens", None),
        "cache_read_input_tokens": getattr(resp.usage, "cache_read_input_tokens", None),
    }
    return obj


def structure_all_references(
    blocks: list["ReferenceBlock"],
    ln_report: LineNumberReport,
    *,
    api_key: str | None = None,
    verbose: bool = True,
) -> list[dict]:
    """全参照ブロックを逐次LLM投入して構造化結果のリストを返す。"""
    try:
        import anthropic
    except ImportError as e:
        raise RuntimeError("anthropic SDK is required. Install: pip install anthropic") from e
    if api_key is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set. Pass via env or --api-key.")
    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = _load_system_prompt()

    results: list[dict] = []
    for i, b in enumerate(blocks, 1):
        if verbose:
            print(f"  [{i:>2}/{len(blocks)}] Ref #{b.ref_no} ({b.char_length} chars)...", flush=True)
        obj = structure_reference(client, system_prompt, b, ln_report)
        results.append(obj)
    return results


# =============================================================================
# Stage 4: PubMed カスケード検索
# =============================================================================

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


@dataclass
class SearchAttempt:
    strategy: str          # pmid_direct / doi / doi_alt / title_author_year / title_fuzzy
    query: str
    success: bool
    pmid: str | None = None
    match_score: float | None = None
    error: str | None = None


@dataclass
class PubMedResolution:
    ref_no: int
    pmid: str | None
    final_strategy: str | None
    attempts: list[SearchAttempt] = field(default_factory=list)
    metadata: dict | None = None


class PubMedClient:
    """NCBI E-utilities クライアント。レート制限・リトライ込み。"""

    def __init__(self, api_key: str | None = None, tool: str = "pubmed-reference-resolver"):
        import requests  # local import to avoid hard dep on --phase 1 runs
        self.requests = requests
        self.session = requests.Session()
        self.api_key = api_key
        self.tool = tool
        # NCBI rate limit: 3 req/sec w/o key, 10 req/sec w/ key
        self.min_interval = 0.11 if api_key else 0.34
        self._last_request_at = 0.0

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request_at
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request_at = time.time()

    def _get(self, endpoint: str, params: dict) -> "Response":
        from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
        params = {"tool": self.tool, **params}
        if self.api_key:
            params["api_key"] = self.api_key

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((self.requests.HTTPError, self.requests.ConnectionError, self.requests.Timeout)),
            reraise=True,
        )
        def _do() -> "Response":
            self._throttle()
            url = f"{NCBI_BASE}/{endpoint}"
            r = self.session.get(url, params=params, timeout=30)
            # NCBI returns 429/5xx for rate limit/errors
            if r.status_code >= 500 or r.status_code == 429:
                r.raise_for_status()
            return r

        return _do()

    def esearch(self, term: str, retmax: int = 5) -> list[str]:
        r = self._get("esearch.fcgi", {
            "db": "pubmed",
            "term": term,
            "retmax": str(retmax),
            "retmode": "json",
        })
        r.raise_for_status()
        try:
            data = r.json()
        except ValueError:
            return []
        return list(data.get("esearchresult", {}).get("idlist", []) or [])

    def efetch_metadata(self, pmid: str) -> dict | None:
        r = self._get("efetch.fcgi", {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml",
        })
        r.raise_for_status()
        return _parse_pubmed_xml(r.text, pmid)


def _parse_pubmed_xml(xml_text: str, pmid: str) -> dict | None:
    """efetch のXMLから必要フィールドを抽出する。"""
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None
    art = root.find(".//PubmedArticle")
    if art is None:
        art = root.find(".//PubmedBookArticle")
    if art is None:
        return None

    def _t(el, xp):
        node = el.find(xp)
        return node.text if node is not None and node.text else None

    # Title
    title = _t(art, ".//Article/ArticleTitle") or _t(art, ".//BookTitle")

    # Journal / ISO Abbreviation
    journal_full = _t(art, ".//Journal/Title")
    journal_iso = _t(art, ".//Journal/ISOAbbreviation")

    # Volume / Issue / Pages
    volume = _t(art, ".//Journal/JournalIssue/Volume")
    issue = _t(art, ".//Journal/JournalIssue/Issue")
    pages = _t(art, ".//Pagination/MedlinePgn")

    # PubDate Year/Month/Day
    year = _t(art, ".//Journal/JournalIssue/PubDate/Year")
    month = _t(art, ".//Journal/JournalIssue/PubDate/Month")
    day = _t(art, ".//Journal/JournalIssue/PubDate/Day")
    medline_date = _t(art, ".//Journal/JournalIssue/PubDate/MedlineDate")
    if not year and medline_date:
        m = re.match(r"(\d{4})", medline_date)
        if m:
            year = m.group(1)

    # Create Date (MedlineCitation系)
    create_date = None
    for tag in ("DateCompleted", "DateRevised", "DateCreated"):
        cd = art.find(f".//{tag}")
        if cd is not None:
            y = cd.findtext("Year") or ""
            mo = cd.findtext("Month") or ""
            d = cd.findtext("Day") or ""
            if y:
                create_date = f"{y}/{mo.zfill(2) if mo else '01'}/{d.zfill(2) if d else '01'}"
                break

    # Authors
    authors: list[dict] = []
    for au in art.findall(".//AuthorList/Author"):
        last = au.findtext("LastName") or au.findtext("CollectiveName")
        fore = au.findtext("ForeName")
        init = au.findtext("Initials")
        # Affiliation
        aff_nodes = au.findall("AffiliationInfo/Affiliation")
        affs = [a.text for a in aff_nodes if a.text]
        authors.append({
            "last": last, "fore": fore, "initials": init,
            "affiliations": affs,
        })

    # IDs: DOI / PMCID / NIHMS
    # 注意: CommentsCorrections 内の ArticleIdList を拾わないよう、
    #       PubmedData 直下と Article/ELocationID のみを対象にする。
    doi = None
    pmcid = None
    nihms_id = None
    # PubmedData/ArticleIdList (正規の記事ID)
    for aid in art.findall("./PubmedData/ArticleIdList/ArticleId"):
        idtype = aid.attrib.get("IdType")
        if idtype == "doi" and doi is None:
            doi = aid.text
        elif idtype == "pmc" and pmcid is None:
            pmcid = aid.text
        elif idtype == "mid" and nihms_id is None:
            nihms_id = aid.text
    # Article/ELocationID (一部レコードはこちらにDOIが入る)
    if doi is None:
        for eid in art.findall(".//Article/ELocationID"):
            if eid.attrib.get("EIdType") == "doi" and eid.text:
                doi = eid.text
                break

    # Abstract
    abs_parts: list[str] = []
    for ab in art.findall(".//Abstract/AbstractText"):
        label = ab.attrib.get("Label")
        text = "".join(ab.itertext()) or ""
        abs_parts.append(f"{label}: {text}" if label else text)
    abstract = "\n".join(abs_parts) if abs_parts else None

    # Citation string (PubMed-like: "Journal. Year Mon;Vol(Issue):Pages.")
    cite_head = ""
    if journal_iso:
        cite_head = journal_iso + ". "
    date_part = year or ""
    if year and month:
        date_part += f" {month}"
        if day:
            date_part += f" {day}"
    vol_str = volume or ""
    if issue:
        vol_str += f"({issue})"
    if pages:
        vol_str += f":{pages}" if vol_str else pages
    tail_parts = []
    if date_part:
        tail_parts.append(date_part)
    if vol_str:
        tail_parts.append(vol_str)
    citation = (cite_head + ";".join(tail_parts)).strip() + "."
    if not citation.strip("."):
        citation = ""

    return {
        "pmid": pmid,
        "title": title,
        "journal_full": journal_full,
        "journal_iso": journal_iso,
        "volume": volume,
        "issue": issue,
        "pages": pages,
        "year": year,
        "month": month,
        "day": day,
        "create_date": create_date,
        "authors": authors,
        "doi": doi,
        "pmcid": pmcid,
        "nihms_id": nihms_id,
        "abstract": abstract,
        "citation": citation,
    }


def _is_valid_doi(doi: str | None) -> bool:
    if not doi:
        return False
    return re.match(r"^10\.\d{4,}/\S+", doi) is not None


def resolve_one(
    client: PubMedClient,
    ref: dict,
    *,
    fuzzy_threshold: int = 90,
    verbose: bool = False,
) -> PubMedResolution:
    """段階カスケード検索を1参照に適用。"""
    import rapidfuzz.fuzz as fz

    ref_no = ref.get("ref_no", -1)
    attempts: list[SearchAttempt] = []
    book = bool(ref.get("is_book"))

    def _log(a: SearchAttempt) -> None:
        attempts.append(a)
        if verbose:
            s = "OK" if a.success else "NG"
            print(f"      - [{a.strategy}] {s} {a.query[:80]}"
                  + (f" (score={a.match_score:.0f})" if a.match_score is not None else "")
                  + (f" [{a.error[:80]}]" if a.error else ""))

    # Level 1: PMID 直接
    pmid_in = ref.get("pmid")
    if pmid_in and str(pmid_in).isdigit():
        try:
            meta = client.efetch_metadata(str(pmid_in))
            if meta:
                _log(SearchAttempt("pmid_direct", str(pmid_in), True, pmid=str(pmid_in)))
                return PubMedResolution(ref_no, str(pmid_in), "pmid_direct", attempts, meta)
            _log(SearchAttempt("pmid_direct", str(pmid_in), False, error="efetch returned empty"))
        except Exception as e:
            _log(SearchAttempt("pmid_direct", str(pmid_in), False, error=str(e)[:120]))

    # Level 2: DOI (doi / doi_alt の順で試行)
    if not book:
        for key in ("doi", "doi_alt"):
            doi = ref.get(key)
            if not _is_valid_doi(doi):
                continue
            term = f'"{doi}"[AID] OR "{doi}"[DOI]'
            try:
                ids = client.esearch(term, retmax=2)
                if ids:
                    meta = client.efetch_metadata(ids[0])
                    _log(SearchAttempt(key, term, True, pmid=ids[0]))
                    return PubMedResolution(ref_no, ids[0], key, attempts, meta)
                _log(SearchAttempt(key, term, False, error="no hits"))
            except Exception as e:
                _log(SearchAttempt(key, term, False, error=str(e)[:120]))

    # Level 3: Title + First Author + Year
    title = ref.get("title")
    year = ref.get("year")
    authors = ref.get("authors") or []
    first_author = authors[0].get("surname") if authors else None
    if title and first_author and year and not book:
        clean_title = re.sub(r'["\[\]()]', " ", title)
        # タイトル全文だとヒットしにくいので先頭10単語に削る
        words = clean_title.split()
        short_title = " ".join(words[:10])
        term = f'{short_title}[Title] AND {first_author}[Author] AND {year}[PDAT]'
        try:
            ids = client.esearch(term, retmax=3)
            if ids:
                # 先頭候補をfuzzy一致で確認
                best_pmid, best_score, best_meta = None, 0.0, None
                for pmid in ids[:3]:
                    meta = client.efetch_metadata(pmid)
                    if not meta or not meta.get("title"):
                        continue
                    score = fz.token_sort_ratio(title.lower(), meta["title"].lower())
                    if score > best_score:
                        best_pmid, best_score, best_meta = pmid, score, meta
                if best_pmid and best_score >= fuzzy_threshold:
                    _log(SearchAttempt("title_author_year", term, True,
                                       pmid=best_pmid, match_score=best_score))
                    return PubMedResolution(ref_no, best_pmid, "title_author_year", attempts, best_meta)
                _log(SearchAttempt("title_author_year", term, False,
                                   pmid=best_pmid, match_score=best_score,
                                   error=f"fuzzy {best_score:.0f} < {fuzzy_threshold}"))
            else:
                _log(SearchAttempt("title_author_year", term, False, error="no hits"))
        except Exception as e:
            _log(SearchAttempt("title_author_year", term, False, error=str(e)[:120]))

    # Level 4: Title 単独 fuzzy
    if title and not book:
        clean_title = re.sub(r'["\[\]()]', " ", title)
        words = clean_title.split()
        short_title = " ".join(words[:12])
        try:
            ids = client.esearch(f"{short_title}[Title]", retmax=5)
            if not ids:
                ids = client.esearch(short_title, retmax=5)
            if ids:
                best_pmid, best_score, best_meta = None, 0.0, None
                for pmid in ids[:5]:
                    meta = client.efetch_metadata(pmid)
                    if not meta or not meta.get("title"):
                        continue
                    score = fz.token_sort_ratio(title.lower(), meta["title"].lower())
                    if score > best_score:
                        best_pmid, best_score, best_meta = pmid, score, meta
                if best_pmid and best_score >= fuzzy_threshold:
                    _log(SearchAttempt("title_fuzzy", short_title, True,
                                       pmid=best_pmid, match_score=best_score))
                    return PubMedResolution(ref_no, best_pmid, "title_fuzzy", attempts, best_meta)
                _log(SearchAttempt("title_fuzzy", short_title, False,
                                   pmid=best_pmid, match_score=best_score,
                                   error=f"fuzzy {best_score:.0f} < {fuzzy_threshold}"))
            else:
                _log(SearchAttempt("title_fuzzy", short_title, False, error="no hits"))
        except Exception as e:
            _log(SearchAttempt("title_fuzzy", short_title, False, error=str(e)[:120]))

    return PubMedResolution(ref_no, None, None, attempts, None)


def resolve_all(
    structured: list[dict],
    *,
    ncbi_api_key: str | None = None,
    verbose: bool = True,
) -> list[PubMedResolution]:
    client = PubMedClient(api_key=ncbi_api_key)
    out: list[PubMedResolution] = []
    for i, s in enumerate(structured, 1):
        if "_parse_error" in s:
            out.append(PubMedResolution(s.get("ref_no", -1), None, None, [], None))
            continue
        if verbose:
            tprev = (s.get("title") or "")[:60]
            print(f"  [{i:>2}/{len(structured)}] Ref #{s.get('ref_no')}: {tprev}")
        res = resolve_one(client, s, verbose=verbose)
        out.append(res)
    return out


# =============================================================================
# Stage 5: 出力合成 (CSV / abstract.txt / report.md / unresolved.csv)
# =============================================================================

# PubMed純正CSVスキーマ（UTF-8 BOM付き、全セル ダブルクォート）
CSV_COLUMNS = [
    "Ref_No", "Duplicate_of",
    "PMID", "Title", "Authors", "Citation", "First Author",
    "Journal/Book", "Publication Year", "Create Date",
    "PMCID", "NIHMS ID", "DOI",
]


def _normalize_title_for_dup(t: str) -> str:
    if not t:
        return ""
    t = t.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def detect_duplicates(resolutions: list[dict], structured: dict[int, dict]) -> dict[int, int]:
    """複合キー (PMID || DOI || norm_title+first_author+year) で重複検出。

    戻り値: 重複ref_no → 最初に出現した元のref_no
    """
    seen: dict[tuple, int] = {}
    dup_map: dict[int, int] = {}
    for r in resolutions:
        ref_no = r["ref_no"]
        s = structured.get(ref_no, {})
        keys: list[tuple] = []
        if r.get("pmid"):
            keys.append(("pmid", str(r["pmid"])))
        for k in ("doi", "doi_alt"):
            if s.get(k):
                keys.append(("doi", s[k].lower().strip()))
        title = _normalize_title_for_dup(s.get("title") or "")
        authors = s.get("authors") or []
        first = (authors[0].get("surname") or "").lower().strip() if authors else ""
        year = s.get("year")
        if title and first and year:
            keys.append(("tay", f"{title}|{first}|{year}"))
        matched = None
        for key in keys:
            if key in seen:
                matched = seen[key]
                break
        if matched is not None and matched != ref_no:
            dup_map[ref_no] = matched
        else:
            for key in keys:
                seen.setdefault(key, ref_no)
    return dup_map


def _format_authors_csv(authors: list[dict]) -> str:
    """'Smith J, Lee K, ...' 形式 (PubMed CSV 準拠)。"""
    parts = []
    for a in authors or []:
        last = a.get("last") or ""
        init = a.get("initials") or ""
        if last and init:
            parts.append(f"{last} {init}")
        elif last:
            parts.append(last)
    return ", ".join(parts)


def _first_author_csv(authors: list[dict]) -> str:
    if not authors:
        return ""
    a = authors[0]
    last = a.get("last") or ""
    init = a.get("initials") or ""
    return f"{last} {init}".strip()


def write_pubmed_csv(
    path: Path,
    resolutions: list[dict],
    structured: dict[int, dict],
    duplicates: dict[int, int],
) -> None:
    """PubMed純正形式互換 CSV を書き出す (UTF-8 BOM付き、全セルダブルクォート)。"""
    import csv
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(CSV_COLUMNS)
        for r in resolutions:
            ref_no = r["ref_no"]
            dup_of = duplicates.get(ref_no)
            m = r.get("metadata") or {}
            if r.get("pmid"):
                row = [
                    str(ref_no),
                    str(dup_of) if dup_of else "",
                    r.get("pmid") or "",
                    m.get("title") or "",
                    _format_authors_csv(m.get("authors") or []),
                    m.get("citation") or "",
                    _first_author_csv(m.get("authors") or []),
                    m.get("journal_full") or m.get("journal_iso") or "",
                    m.get("year") or "",
                    m.get("create_date") or "",
                    m.get("pmcid") or "",
                    m.get("nihms_id") or "",
                    m.get("doi") or "",
                ]
            else:
                # 未ヒット: PMID以降は空、行は削除しない
                row = [str(ref_no), str(dup_of) if dup_of else ""] + [""] * (len(CSV_COLUMNS) - 2)
            w.writerow(row)


def _format_authors_abstract(authors: list[dict]) -> str:
    """'Petersen E(1), Holt S(2), ...' 形式 (PubMed abstract text 準拠)。"""
    parts = []
    for i, a in enumerate(authors or [], 1):
        last = a.get("last") or ""
        init = a.get("initials") or ""
        aff_marker = f"({i})" if a.get("affiliations") else ""
        if last and init:
            parts.append(f"{last} {init}{aff_marker}")
        elif last:
            parts.append(f"{last}{aff_marker}")
    return ", ".join(parts)


def _build_abstract_entry(ref_no: int, meta: dict) -> str:
    """PubMed標準 abstract text 形式で1エントリ組み立てる。"""
    lines: list[str] = []
    # ヘッダ行: "Journal. Year Mon Day;Vol(Issue):Pages. doi: ..."
    header = meta.get("citation") or ""
    if meta.get("doi"):
        header = header.rstrip(".") + f". doi: {meta['doi']}."
    lines.append(f"{ref_no}. {header}")
    lines.append("")
    # Title
    if meta.get("title"):
        lines.append(meta["title"].rstrip(".") + ".")
        lines.append("")
    # Authors
    auth_line = _format_authors_abstract(meta.get("authors") or [])
    if auth_line:
        lines.append(auth_line + ".")
        lines.append("")
    # Author information (affiliations)
    affs = []
    for i, a in enumerate(meta.get("authors") or [], 1):
        for aff in (a.get("affiliations") or []):
            affs.append(f"({i}){aff}")
    if affs:
        lines.append("Author information:")
        lines.extend(affs)
        lines.append("")
    # Abstract
    if meta.get("abstract"):
        lines.append(meta["abstract"])
        lines.append("")
    # DOI / PMID footer
    if meta.get("doi"):
        lines.append(f"DOI: {meta['doi']}")
    if meta.get("pmcid"):
        lines.append(f"PMCID: {meta['pmcid']}")
    lines.append(f"PMID: {meta['pmid']}")
    return "\n".join(lines)


def write_abstract_text(
    path: Path,
    resolutions: list[dict],
    structured: dict[int, dict],
) -> None:
    """PubMed標準 abstract text 形式で全件を書き出す。未ヒットは1行保持。"""
    blocks: list[str] = []
    for r in resolutions:
        ref_no = r["ref_no"]
        s = structured.get(ref_no, {})
        if r.get("pmid") and r.get("metadata"):
            blocks.append(_build_abstract_entry(ref_no, r["metadata"]))
        else:
            # 元引用テキストを要約（最大200字）
            raw = (s.get("title") or "") + " / " + (s.get("journal") or "")
            raw = raw[:200]
            blocks.append(f"{ref_no}. [PubMed上に該当文献が見つかりませんでした: {raw}]")
    path.write_text("\n\n\n".join(blocks) + "\n", encoding="utf-8")


def write_unresolved_csv(
    path: Path,
    resolutions: list[dict],
    structured: dict[int, dict],
    reference_blocks: list[dict],
) -> None:
    """未ヒット文献の元引用+試行クエリ+失敗理由を書き出す。"""
    import csv
    blocks_by_ref = {b["ref_no"]: b for b in reference_blocks}
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow([
            "Ref_No", "Original_Citation", "Structured_Title", "Structured_Journal",
            "Structured_Year", "Structured_DOI", "Is_Book", "Language",
            "Attempted_Strategies", "Failure_Reasons",
        ])
        for r in resolutions:
            if r.get("pmid"):
                continue
            ref_no = r["ref_no"]
            s = structured.get(ref_no, {})
            rb = blocks_by_ref.get(ref_no, {})
            strategies = "; ".join(a["strategy"] for a in r.get("attempts", []))
            reasons = "; ".join(
                f"[{a['strategy']}] {a.get('error') or 'no hits'}"
                for a in r.get("attempts", [])
            )
            if not r.get("attempts"):
                reasons = "skipped (book or missing metadata)"
            w.writerow([
                str(ref_no),
                (rb.get("raw_text") or "")[:500],
                s.get("title") or "",
                s.get("journal") or "",
                s.get("year") or "",
                s.get("doi") or s.get("doi_alt") or "",
                "Y" if s.get("is_book") else "",
                s.get("language") or "",
                strategies,
                reasons,
            ])


def _classify_reviewer_issues(
    resolutions: list[dict],
    structured: dict[int, dict],
    duplicates: dict[int, int],
) -> dict[str, list[str]]:
    """査読コメント候補を Major / Moderate / Minor の3段階に分類する。"""
    import rapidfuzz.fuzz as fz
    out: dict[str, list[str]] = {"major": [], "moderate": [], "minor": []}

    # 重複引用 → Major
    for dup_ref, orig_ref in sorted(duplicates.items()):
        out["major"].append(
            f"**Ref #{dup_ref} は Ref #{orig_ref} と同一論文の重複引用です。**"
        )

    for r in resolutions:
        if not r.get("pmid"):
            continue
        ref_no = r["ref_no"]
        s = structured.get(ref_no, {})
        m = r.get("metadata") or {}

        # 年号チェック
        src_y = s.get("year")
        pm_y = m.get("year")
        if src_y and pm_y and str(src_y) != str(pm_y):
            try:
                diff = abs(int(str(src_y)[:4]) - int(str(pm_y)[:4]))
            except ValueError:
                diff = 99
            msg = (
                f"Ref #{ref_no} 引用年 {src_y} ≠ PubMed年 {pm_y} "
                f"(PMID: {r['pmid']})"
            )
            if diff >= 2:
                out["major"].append(f"**{msg}** — 2年以上の乖離、別論文の可能性も。")
            else:
                out["moderate"].append(f"{msg} — epub/print年の差の可能性。")

        # タイトル差異
        src_t = s.get("title") or ""
        pm_t = m.get("title") or ""
        if src_t and pm_t:
            score = fz.token_sort_ratio(src_t.lower(), pm_t.lower())
            if score < 70:
                out["major"].append(
                    f"**Ref #{ref_no} タイトル一致度 {score:.0f}% (PMID: {r['pmid']}) — 別論文の可能性が高い。**\n"
                    f"  - 引用: \"{src_t[:100]}\"\n"
                    f"  - PubMed: \"{pm_t[:100]}\""
                )
            elif score < 90:
                out["moderate"].append(
                    f"Ref #{ref_no} タイトル一致度 {score:.0f}% (PMID: {r['pmid']})。\n"
                    f"  - 引用: \"{src_t[:80]}...\"\n"
                    f"  - PubMed: \"{pm_t[:80]}...\""
                )
            elif score < 99:
                out["minor"].append(
                    f"Ref #{ref_no} タイトルに微小な表記差 (一致度 {score:.0f}%、PMID: {r['pmid']})"
                )

        # DOI-雑誌名の不整合 (LLM検出)
        notes = s.get("notes") or ""
        nlow = notes.lower()
        if "incorrect" in nlow or "appears to be incorrect" in nlow:
            out["major"].append(
                f"**Ref #{ref_no} 引用記述に不整合 (LLM検出)**: {notes[:200]}"
            )

    return out


def _truncate(s: str, n: int) -> str:
    if not s:
        return ""
    s = s.replace("|", "\\|").replace("\n", " ")
    return s if len(s) <= n else s[: n - 1] + "…"


def _unresolved_reason(s: dict, attempts: list[dict]) -> str:
    """未ヒット参照の推定理由を1行にまとめる。"""
    if s.get("is_book"):
        return "書籍 (PubMed対象外)"
    lang = s.get("language") or "en"
    if lang != "en":
        return f"非英語 ({lang})・MEDLINE非収録の可能性"
    has_doi = bool(s.get("doi") or s.get("doi_alt"))
    if has_doi:
        return "DOI有るが PubMed 未ヒット → 非MEDLINE収録誌/捏造DOIの可能性"
    if not attempts:
        return "構造化不十分（確認要）"
    return "DOI無し・タイトル検索失敗 → 非MEDLINE収録誌の可能性"


def write_report(
    path: Path,
    result: dict,
    duplicates: dict[int, int],
) -> None:
    """統合レポート: ダッシュボード + 優先度順要確認項目 + 未解決一覧 + 透明性トレース。"""
    ln = result.get("stage2_5_line_number_detection", {})
    trace = result.get("stage2_preprocess_trace", {})
    structured = {s["ref_no"]: s for s in result.get("stage3_structured", [])}
    resolutions = result.get("stage4_pubmed_resolutions", [])
    ref_blocks_by_id = {b["ref_no"]: b for b in result.get("stage3_reference_blocks", [])}

    resolved = [r for r in resolutions if r.get("pmid")]
    unresolved = [r for r in resolutions if not r.get("pmid")]
    issues = _classify_reviewer_issues(resolutions, structured, duplicates)

    # 解決経路
    strat_counts: dict[str, int] = {}
    for r in resolutions:
        k = r.get("final_strategy") or "unresolved"
        strat_counts[k] = strat_counts.get(k, 0) + 1

    total_action = len(issues["major"]) + len(issues["moderate"]) + len(unresolved)

    lines: list[str] = []

    # =========================================
    # ヘッダー + ダッシュボード
    # =========================================
    lines.append("# pubmed-reference-resolver 監査レポート")
    lines.append("")
    lines.append(f"**入力**: `{result.get('input_file')}`  |  "
                 f"**実行**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## ダッシュボード")
    lines.append("")
    lines.append("| 指標 | 件数 | 状態 |")
    lines.append("|------|----:|:----:|")
    lines.append(f"| 総参照数 | {len(resolutions)} | — |")
    lines.append(f"| 解決 (PMID取得) | {len(resolved)} | OK |")
    lines.append(f"| **未解決 (要確認)** | **{len(unresolved)}** | "
                 f"{'ATTN' if unresolved else 'OK'} |")
    lines.append(f"| **重複引用** | **{len(duplicates)}** | "
                 f"{'MAJOR' if duplicates else 'OK'} |")
    lines.append(f"| 査読コメント: 重大 | {len(issues['major'])} | "
                 f"{'MAJOR' if issues['major'] else 'OK'} |")
    lines.append(f"| 査読コメント: 要検討 | {len(issues['moderate'])} | "
                 f"{'WARN' if issues['moderate'] else 'OK'} |")
    lines.append(f"| 査読コメント: 軽微 | {len(issues['minor'])} | — |")
    lines.append("")
    if total_action == 0:
        lines.append("> **査読者が確認すべき項目はありません** — 全参照が正常に解決しました。")
    else:
        lines.append(f"> **査読者が確認すべき項目: 計 {total_action} 件** "
                     f"(重大 {len(issues['major'])} / 要検討 {len(issues['moderate'])} / 未解決 {len(unresolved)})")
    lines.append("")
    lines.append("---")
    lines.append("")

    # =========================================
    # セクション1: 要確認項目 (優先度順)
    # =========================================
    lines.append("## 1. 要確認項目 (優先度順)")
    lines.append("")

    lines.append("### 1.1 [MAJOR] 重大な不整合")
    lines.append("")
    if issues["major"]:
        lines.append("**必ず査読コメントとして言及することを推奨します。**")
        lines.append("")
        for c in issues["major"]:
            lines.append(f"- {c}")
    else:
        lines.append("_(該当なし)_")
    lines.append("")

    lines.append("### 1.2 [MODERATE] 要検討")
    lines.append("")
    if issues["moderate"]:
        lines.append("文脈に応じて査読コメントを検討してください。")
        lines.append("")
        for c in issues["moderate"]:
            lines.append(f"- {c}")
    else:
        lines.append("_(該当なし)_")
    lines.append("")

    lines.append("### 1.3 [MINOR] 軽微な差異")
    lines.append("")
    if issues["minor"]:
        lines.append("通常は人間査読で無視して問題ありません（参考情報）。")
        lines.append("")
        for c in issues["minor"]:
            lines.append(f"- {c}")
    else:
        lines.append("_(該当なし)_")
    lines.append("")
    lines.append("---")
    lines.append("")

    # =========================================
    # セクション2: 未解決参照の詳細 (旧 unresolved.csv を統合)
    # =========================================
    lines.append("## 2. 未解決参照の詳細")
    lines.append("")
    if unresolved:
        lines.append(f"**計 {len(unresolved)} 件** が PubMed で解決できませんでした。"
                     "理由の多くは MEDLINE 非収録誌または書籍です。")
        lines.append("")
        lines.append("### 一覧")
        lines.append("")
        lines.append("| # | タイトル | ジャーナル | 年 | DOI | 言語 | 推定理由 |")
        lines.append("|--:|---------|----------|---:|-----|:---:|---------|")
        for r in unresolved:
            ref_no = r["ref_no"]
            s = structured.get(ref_no, {})
            title = _truncate(s.get("title") or "", 60)
            journal = _truncate(s.get("journal") or "", 30)
            year = s.get("year") or "-"
            doi = _truncate(s.get("doi") or s.get("doi_alt") or "-", 35)
            lang = s.get("language") or "-"
            reason = _unresolved_reason(s, r.get("attempts") or [])
            lines.append(f"| {ref_no} | {title} | {journal} | {year} | `{doi}` | {lang} | {reason} |")
        lines.append("")

        lines.append("### 参照ごとの試行詳細")
        lines.append("")
        for r in unresolved:
            ref_no = r["ref_no"]
            s = structured.get(ref_no, {})
            rb = ref_blocks_by_id.get(ref_no, {})
            lines.append(f"#### Ref #{ref_no}")
            lines.append("")
            raw_citation = (rb.get("raw_text") or "").replace("\n", " ")
            lines.append(f"- **元引用**: `{_truncate(raw_citation, 300)}`")
            lines.append(f"- **構造化結果**: {s.get('title') or '-'} / "
                         f"{s.get('journal') or '-'} / {s.get('year') or '-'} / "
                         f"DOI={s.get('doi') or s.get('doi_alt') or '-'}")
            attempts = r.get("attempts") or []
            if attempts:
                lines.append("- **試行経路**:")
                for a in attempts:
                    ok = "OK" if a.get("success") else "NG"
                    err = a.get("error") or "no hits"
                    lines.append(f"  - `[{a['strategy']}]` {ok} — {_truncate(err, 100)}")
            else:
                lines.append("- **試行経路**: (スキップ — 書籍またはメタデータ不足)")
            lines.append("")
    else:
        lines.append("_全参照が解決しました。_")
        lines.append("")
    lines.append("---")
    lines.append("")

    # =========================================
    # セクション3: 構造化品質 (目視確認推奨)
    # =========================================
    lowmed = sorted(
        (s for s in structured.values() if s.get("parsing_confidence") in ("low", "medium")),
        key=lambda x: x.get("ref_no", 0),
    )
    lines.append("## 3. 構造化品質 (parsing_confidence < high)")
    lines.append("")
    if lowmed:
        lines.append("以下の参照は LLM 構造化時に不確実性が検出されました。必要に応じて目視確認を推奨します。")
        lines.append("")
        lines.append("| # | 確度 | タイトル | 備考 |")
        lines.append("|--:|:----:|---------|------|")
        for s in lowmed:
            title = _truncate(s.get("title") or "", 60)
            notes = _truncate(s.get("notes") or "", 80)
            lines.append(f"| {s.get('ref_no')} | {s.get('parsing_confidence')} "
                         f"| {title} | {notes} |")
    else:
        lines.append("_全参照が高確度 (high) で構造化されました。_")
    lines.append("")
    lines.append("---")
    lines.append("")

    # =========================================
    # セクション4: 透明性トレース
    # =========================================
    lines.append("## 4. 透明性トレース")
    lines.append("")

    lines.append("### 4.1 解決経路の内訳")
    lines.append("")
    lines.append("| 経路 | 件数 | 意味 |")
    lines.append("|------|----:|------|")
    legend = {
        "pmid_direct": "原典にPMID明記→efetch直叩き",
        "doi": "DOI検索成功",
        "doi_alt": "**ハイフン除去版DOIで救済**",
        "title_author_year": "タイトル+第一著者+年で検索",
        "title_fuzzy": "タイトル単独fuzzy (≥90%一致)",
        "unresolved": "全カスケード失敗",
    }
    for k, v in sorted(strat_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| `{k}` | {v} | {legend.get(k, '-')} |")
    lines.append("")

    lines.append("### 4.2 PDF由来の行番号混入検出")
    lines.append("")
    if ln.get("detected"):
        lines.append(f"- **検出**: {ln['count']} 件 (範囲: {ln['min_val']}-{ln['max_val']})")
        lines.append(f"- **判定根拠**: {ln.get('rationale', '')}")
        lines.append(f"- **前処理除去**: ハイフン橋渡し救済 {trace.get('hyphen_bridged_removed', 0)} 件 / "
                     f"独立行番号除去 {trace.get('standalone_removed', 0)} 件")
    else:
        lines.append("- 行番号混入なし")
    lines.append("")

    lines.append("### 4.3 全参照のスナップショット")
    lines.append("")
    lines.append("| # | PMID | 経路 | ジャーナル | 年 |")
    lines.append("|--:|------|:----:|----------|---:|")
    for r in resolutions:
        ref_no = r["ref_no"]
        s = structured.get(ref_no, {})
        m = r.get("metadata") or {}
        pmid = r.get("pmid") or "—"
        strat = r.get("final_strategy") or "unresolved"
        journal = _truncate(m.get("journal_iso") or s.get("journal") or "—", 25)
        year = m.get("year") or s.get("year") or "—"
        lines.append(f"| {ref_no} | {pmid} | {strat} | {journal} | {year} |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # =========================================
    # 免責
    # =========================================
    lines.append("## 免責事項")
    lines.append("")
    lines.append("本レポートは PubMed メタデータとの機械的突合による **候補抽出** です。")
    lines.append("**最終的な査読判断は必ず人間の査読者が行ってください。**")
    lines.append("タイトル fuzzy match が低い場合、必ずしも誤引用とは限らず (例: 原典が多言語、タイトル翻訳等)、")
    lines.append("コンテキストを踏まえた判断が必要です。")

    path.write_text("\n".join(lines), encoding="utf-8")


def synthesize_outputs(result: dict, output_dir: Path) -> dict:
    """Phase 3 結果から最終3ファイルを合成する。

    report.md は unresolved 一覧を内包し、ダッシュボード + 優先度別
    要確認項目 + 透明性トレース を1ファイルに統合する。
    """
    structured = {s["ref_no"]: s for s in result.get("stage3_structured", [])}
    resolutions = result.get("stage4_pubmed_resolutions", [])

    duplicates = detect_duplicates(resolutions, structured)

    # ファイル名用の first_pmid (解決済みの最初のPMID)
    first_pmid = next((r["pmid"] for r in resolutions if r.get("pmid")), None) or "nopmid"

    csv_path = output_dir / f"csv-{first_pmid}-set.csv"
    abstract_path = output_dir / f"abstract-{first_pmid}-set.txt"
    report_path = output_dir / "report.md"

    write_pubmed_csv(csv_path, resolutions, structured, duplicates)
    write_abstract_text(abstract_path, resolutions, structured)
    write_report(report_path, result, duplicates)

    return {
        "csv": str(csv_path),
        "abstract": str(abstract_path),
        "report": str(report_path),
        "duplicates": duplicates,
    }


# =============================================================================
# CLI
# =============================================================================

def run_phase1(input_path: Path, output_dir: Path) -> dict:
    raw_text, source_type = extract_text(input_path)
    ln_report = detect_line_numbers(raw_text)
    cleaned, trace = preprocess(raw_text, ln_report)
    blocks = split_references(cleaned)

    result = {
        "input_file": str(input_path),
        "source_type": source_type,
        "stage1_raw_length": len(raw_text),
        "stage2_5_line_number_detection": asdict(ln_report),
        "stage2_preprocess_trace": asdict(trace),
        "stage3_reference_blocks": [asdict(b) for b in blocks],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "phase1_intermediate.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "phase1_raw.txt").write_text(raw_text, encoding="utf-8")
    (output_dir / "phase1_cleaned.txt").write_text(cleaned, encoding="utf-8")
    return result


def _print_summary(result: dict) -> None:
    ln = result["stage2_5_line_number_detection"]
    tr = result["stage2_preprocess_trace"]
    blocks = result["stage3_reference_blocks"]
    print("=" * 70)
    print(f"Input: {result['input_file']}  ({result['source_type']})")
    print(f"Raw length: {result['stage1_raw_length']} chars")
    print("-" * 70)
    print("[Stage 2.5] line number detection:")
    print(f"  detected        : {ln['detected']}")
    print(f"  count           : {ln['count']}")
    print(f"  range           : {ln['min_val']} - {ln['max_val']}")
    print(f"  total_candidates: {ln['total_candidates']}")
    print(f"  rationale       : {ln['rationale']}")
    print("-" * 70)
    print("[Stage 2] preprocess trace:")
    print(f"  hyphen_bridged_removed : {tr['hyphen_bridged_removed']}")
    print(f"  standalone_removed     : {tr['standalone_removed']}")
    print(f"  soft_linebreaks_joined : {tr['soft_linebreaks_joined']}")
    print(f"  ref_blocks_found       : {tr['ref_blocks_found']}")
    print(f"  header_stripped        : {tr['header_stripped']}")
    print("-" * 70)
    print(f"[Stage 3-] reference blocks: {len(blocks)}")
    for b in blocks:
        preview = b["raw_text"][:120].replace("\n", " ")
        print(f"  #{b['ref_no']:>3} ({b['char_length']:>4} chars): {preview}...")
    print("=" * 70)


def run_phase2(input_path: Path, output_dir: Path, *, api_key: str | None = None) -> dict:
    """Phase 1 に続けて Stage 3 (LLM構造化) を実行。"""
    result = run_phase1(input_path, output_dir)
    blocks = [ReferenceBlock(**b) for b in result["stage3_reference_blocks"]]
    ln_report = LineNumberReport(**result["stage2_5_line_number_detection"])
    print(f"[Phase 2] LLM structuring {len(blocks)} refs via {LLM_MODEL}...")
    t0 = time.time()
    structured = structure_all_references(blocks, ln_report, api_key=api_key)
    elapsed = time.time() - t0
    result["stage3_structured"] = structured
    result["stage3_elapsed_seconds"] = round(elapsed, 2)
    (output_dir / "phase2_structured.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[Phase 2] done in {elapsed:.1f}s")
    return result


def _print_phase2_summary(result: dict) -> None:
    structured = result.get("stage3_structured", [])
    print("=" * 70)
    print(f"[Phase 2] structured {len(structured)} refs "
          f"in {result.get('stage3_elapsed_seconds')}s")
    conf = {"high": 0, "medium": 0, "low": 0}
    with_doi = 0
    with_pmid = 0
    is_book = 0
    errors = 0
    cache_read = 0
    cache_create = 0
    total_in = 0
    total_out = 0
    for s in structured:
        if "_parse_error" in s:
            errors += 1
        c = s.get("parsing_confidence", "low")
        if c in conf:
            conf[c] += 1
        if s.get("doi"):
            with_doi += 1
        if s.get("pmid"):
            with_pmid += 1
        if s.get("is_book"):
            is_book += 1
        u = s.get("_usage", {}) or {}
        cache_read += u.get("cache_read_input_tokens") or 0
        cache_create += u.get("cache_creation_input_tokens") or 0
        total_in += u.get("input_tokens") or 0
        total_out += u.get("output_tokens") or 0
    print(f"  confidence   : high={conf['high']}  medium={conf['medium']}  low={conf['low']}")
    print(f"  doi present  : {with_doi}/{len(structured)}")
    print(f"  pmid present : {with_pmid}/{len(structured)}")
    print(f"  books        : {is_book}")
    print(f"  parse errors : {errors}")
    print(f"  tokens       : in={total_in}  out={total_out}  "
          f"cache_create={cache_create}  cache_read={cache_read}")
    print("-" * 70)
    print("Per-reference (ref_no | conf | has_doi | has_pmid | title prefix):")
    for s in structured:
        if "_parse_error" in s:
            print(f"  #{s.get('ref_no','?'):>3} | ERROR: {s['_parse_error'][:80]}")
            continue
        title = (s.get("title") or "")[:60].replace("\n", " ")
        doi_flag = "Y" if s.get("doi") else "-"
        pmid_flag = "Y" if s.get("pmid") else "-"
        print(f"  #{s.get('ref_no'):>3} | {s.get('parsing_confidence'):>6} "
              f"| doi={doi_flag} | pmid={pmid_flag} | {title}")
    print("=" * 70)


def run_phase3(
    input_path: Path,
    output_dir: Path,
    *,
    api_key: str | None = None,
    ncbi_api_key: str | None = None,
    reuse_phase2: bool = False,
) -> dict:
    """Phase 2 の構造化結果に Stage 4 (PubMedカスケード) を適用。"""
    phase2_path = output_dir / "phase2_structured.json"
    if reuse_phase2 and phase2_path.exists():
        print(f"[Phase 3] reusing existing {phase2_path}")
        result = json.loads(phase2_path.read_text(encoding="utf-8"))
    else:
        result = run_phase2(input_path, output_dir, api_key=api_key)

    structured = result["stage3_structured"]
    print(f"[Phase 3] PubMed cascade for {len(structured)} refs "
          f"(NCBI key={'yes' if ncbi_api_key else 'no'}, rate="
          f"{'10' if ncbi_api_key else '3'} req/s)...")
    t0 = time.time()
    resolutions = resolve_all(structured, ncbi_api_key=ncbi_api_key)
    elapsed = time.time() - t0

    # dataclass を JSON 化
    def _ser(r: PubMedResolution) -> dict:
        return {
            "ref_no": r.ref_no,
            "pmid": r.pmid,
            "final_strategy": r.final_strategy,
            "attempts": [asdict(a) for a in r.attempts],
            "metadata": r.metadata,
        }

    result["stage4_pubmed_resolutions"] = [_ser(r) for r in resolutions]
    result["stage4_elapsed_seconds"] = round(elapsed, 2)
    (output_dir / "phase3_resolved.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[Phase 3] done in {elapsed:.1f}s")
    return result


def _print_phase3_summary(result: dict) -> None:
    resolutions = result.get("stage4_pubmed_resolutions", [])
    structured = {s["ref_no"]: s for s in result.get("stage3_structured", [])}
    resolved = [r for r in resolutions if r.get("pmid")]
    by_strategy: dict[str, int] = {}
    for r in resolutions:
        by_strategy[r.get("final_strategy") or "unresolved"] = (
            by_strategy.get(r.get("final_strategy") or "unresolved", 0) + 1
        )
    print("=" * 70)
    print(f"[Phase 3] PubMed cascade: resolved {len(resolved)}/{len(resolutions)} "
          f"in {result.get('stage4_elapsed_seconds')}s")
    print(f"  by strategy:")
    for k, v in by_strategy.items():
        print(f"    {k:>24}: {v}")
    print("-" * 70)
    for r in resolutions:
        ref_no = r["ref_no"]
        pmid = r["pmid"] or "-"
        strat = r.get("final_strategy") or "UNRESOLVED"
        s = structured.get(ref_no, {})
        title_prev = (s.get("title") or "")[:55]
        note = ""
        if r["metadata"]:
            pubmed_title = r["metadata"].get("title") or ""
            if pubmed_title and s.get("title"):
                import rapidfuzz.fuzz as fz
                score = fz.token_sort_ratio(s["title"].lower(), pubmed_title.lower())
                note = f"  title-match={score:.0f}%"
        print(f"  #{ref_no:>3} | {strat:>18} | PMID={pmid:>9} | {title_prev}{note}")
    print("=" * 70)


def run_phase4(
    input_path: Path,
    output_dir: Path,
    *,
    api_key: str | None = None,
    ncbi_api_key: str | None = None,
    reuse_phase3: bool = False,
    reuse_phase2: bool = False,
) -> dict:
    """Phase 3 の結果に Stage 5 (出力合成) を適用して最終4ファイル生成。"""
    phase3_path = output_dir / "phase3_resolved.json"
    if reuse_phase3 and phase3_path.exists():
        print(f"[Phase 4] reusing existing {phase3_path}")
        result = json.loads(phase3_path.read_text(encoding="utf-8"))
    else:
        result = run_phase3(
            input_path, output_dir,
            api_key=api_key, ncbi_api_key=ncbi_api_key,
            reuse_phase2=reuse_phase2,
        )
    print("[Phase 4] synthesizing outputs (CSV / abstract.txt / report.md / unresolved.csv)...")
    t0 = time.time()
    paths = synthesize_outputs(result, output_dir)
    elapsed = time.time() - t0
    result["stage5_outputs"] = paths
    result["stage5_elapsed_seconds"] = round(elapsed, 2)
    (output_dir / "phase4_final.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[Phase 4] done in {elapsed:.2f}s")
    return result


def _print_phase4_summary(result: dict) -> None:
    paths = result.get("stage5_outputs", {})
    print("=" * 70)
    print("[Phase 4] Final outputs:")
    for k, v in paths.items():
        if isinstance(v, dict):
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: {v}")
    dup = paths.get("duplicates") or {}
    print(f"  duplicates detected: {len(dup)}")
    print("=" * 70)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="pubmed-reference-resolver")
    ap.add_argument("input", type=Path, help="PDF / DOCX / TXT 入力ファイル")
    ap.add_argument("-o", "--output-dir", type=Path, default=Path("./out"), help="出力先")
    ap.add_argument("--phase", type=int, choices=[1, 2, 3, 4], default=4,
                    help="1: 抽出+前処理 / 2: + LLM構造化 / 3: + PubMedカスケード / 4: + 出力合成 (デフォルト)")
    ap.add_argument("--api-key", type=str, default=None,
                    help="Anthropic API key (env: ANTHROPIC_API_KEY, または .env から)")
    ap.add_argument("--ncbi-api-key", type=str, default=None,
                    help="NCBI API key (env: NCBI_API_KEY, または .env から)")
    ap.add_argument("--env-file", type=Path, default=None,
                    help="明示的な .env ファイルパス (省略時は自動探索)")
    ap.add_argument("--no-env-file", action="store_true",
                    help=".env ファイル自動探索を無効化")
    ap.add_argument("--reuse-phase2", action="store_true",
                    help="既存の phase2_structured.json を再利用")
    ap.add_argument("--reuse-phase3", action="store_true",
                    help="既存の phase3_resolved.json を再利用 (Phase 4のみ実行)")
    ap.add_argument("--quiet", action="store_true", help="サマリ出力を抑制")
    args = ap.parse_args(argv)

    if not args.input.exists():
        print(f"ERROR: input not found: {args.input}", file=sys.stderr)
        return 2

    # .env 読み込み (CLI --api-key / 親プロセスの env より低優先)
    if not args.no_env_file:
        if args.env_file:
            if args.env_file.is_file():
                kv = _parse_env_file(args.env_file)
                for k, v in kv.items():
                    if k not in os.environ and v:
                        os.environ[k] = v
                if not args.quiet:
                    print(f"[env] loaded from {args.env_file}")
            else:
                print(f"WARN: --env-file not found: {args.env_file}", file=sys.stderr)
        else:
            loaded = load_env_files(args.input)
            if loaded and not args.quiet:
                for src in loaded:
                    print(f"[env] loaded from {src}")

    ncbi_key = args.ncbi_api_key or os.environ.get("NCBI_API_KEY")

    if args.phase == 1:
        result = run_phase1(args.input, args.output_dir)
        if not args.quiet:
            _print_summary(result)
    elif args.phase == 2:
        result = run_phase2(args.input, args.output_dir, api_key=args.api_key)
        if not args.quiet:
            _print_summary(result)
            _print_phase2_summary(result)
    elif args.phase == 3:
        result = run_phase3(
            args.input, args.output_dir,
            api_key=args.api_key, ncbi_api_key=ncbi_key,
            reuse_phase2=args.reuse_phase2,
        )
        if not args.quiet:
            _print_phase3_summary(result)
    else:
        result = run_phase4(
            args.input, args.output_dir,
            api_key=args.api_key, ncbi_api_key=ncbi_key,
            reuse_phase3=args.reuse_phase3,
            reuse_phase2=args.reuse_phase2,
        )
        if not args.quiet:
            if "stage4_pubmed_resolutions" in result:
                _print_phase3_summary(result)
            _print_phase4_summary(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
