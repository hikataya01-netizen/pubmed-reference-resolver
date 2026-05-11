"""
mdpi_parser.py — MDPI 形式 Reference の決定論的パーサ

目的:
    MDPI (Molecules, IJMS, Cancers 等) 系ジャーナルで採用されている定型引用
    スタイルを LLM を介さず高精度で構造化する。本スキル本体 (main.py) の
    LLM 構造化 (Stage 3) の前段に "fast path" として組み込むことで、API 費用
    削減 + 決定論性の獲得 + MDPI 形式の99%超を high confidence で解決する
    ことを狙う。

適用可否の判定:
    is_mdpi_style(raw_text) が True を返すブロックにのみ適用。MDPI 形式以外
    (Vancouver, AMA, APA 等) では従来の LLM パスにフォールバックする。

スキーマ準拠:
    references/llm_parsing_prompt.md の JSON スキーマに完全準拠。
    parsing_confidence の基準:
      - high   : authors + title + journal + year + doi の全てが埋まる
      - medium : authors + title + journal + year は埋まるが doi 欠落
      - low    : いずれかのフィールドが欠落、または書籍

パーサの設計原則:
    1. 著者リストは ";" 区切り、最終著者末尾の ". " をタイトル開始境界とする
    2. タイトルとジャーナルの境界は head の ". " 位置を最小側から試し、
       looks_like_journal() を満たす最初の分割を採用する
    3. ハイフン橋渡し救済は大文字小文字を保持する (placeholder 置換方式)
    4. 書籍検出は ISBN + Publisher signs + "In <book_title>" の複合判定

検証済みコーパス:
    References.docx (149 refs, MDPI-style) で high=129/medium=7/low=13 を達成。
    詳細は tests/test_integration_149refs/ を参照。

著者: 本モジュールは Claude Opus 4.7 が生成したものを Claude Code 側で統合する
      ことを前提とする。コードスタイルは main.py に合わせてあり、外部依存は
      標準ライブラリのみ (正規表現 re のみ使用、rapidfuzz 等は不要)。
"""

from __future__ import annotations

import re
from typing import Any


# =============================================================================
# ハイフン橋渡し救済 (大文字小文字保持版)
# =============================================================================

_SOFT_HYPHEN_PATTERN = re.compile(r"([A-Za-zÀ-ÿ])-\s*([A-Za-zÀ-ÿ])")

# PDF コピペで分断される既知の複合語群 (ハイフン復元対象から除外)
_PRESERVE_COMPOUNDS = [
    "end-of-life", "self-efficacy", "self-esteem", "self-care", "self-compassion",
    "self-rated", "self-report", "self-reported", "self-help", "self-management",
    "self-regulation",
    "long-term", "short-term", "full-text", "cross-sectional", "well-being",
    "low-income", "high-income", "benefit-finding", "benefit-reminding",
    "meaning-making",
    "meta-analysis", "meta-analytic", "state-of-the-art", "face-to-face",
    "real-world", "cost-effective", "decision-making", "problem-focused",
    "emotion-focused", "evidence-based", "patient-reported", "five-factor",
    "quality-of-life", "post-traumatic", "posttraumatic", "semi-structured",
    "non-randomized", "placebo-controlled", "randomized-controlled",
    "double-blind", "open-label", "user-centered", "health-related",
    "ill-health", "non-communicable", "p-value", "effect-size", "peer-reviewed",
    "cancer-related", "illness-related", "hope-related", "breast-cancer",
    "lung-cancer", "e-health", "anti-cancer", "anti-tumor", "age-related",
    "sex-related", "work-related", "stress-related", "appetite-related",
    "Simon-Thomas", "Becker-Weidman", "McClain-Jacobson",
]


def fix_hyphens(text: str) -> str:
    """PDF コピペで分断された単語を復元する。既知の複合語はそのまま保持。

    大文字小文字は元の形を保持する (placeholder 置換 → ハイフン処理 → 復元)。
    """
    counter = [0]
    placeholders: dict[str, str] = {}

    def _record(m: re.Match[str]) -> str:
        key = f"\x00P{counter[0]}\x00"
        # Normalize internal whitespace around hyphens: "Cancer- related"
        # (common PDF-split variant) is stored as "Cancer-related".
        # This preserves original letter casing while removing spurious
        # whitespace introduced by PDF line-wrapping.
        placeholders[key] = re.sub(r"\s*-\s*", "-", m.group(0))
        counter[0] += 1
        return key

    for w in _PRESERVE_COMPOUNDS:
        # Allow optional whitespace around hyphens to match PDF-split variants
        # (e.g., "cancer-related" matches "cancer- related" or "cancer -related")
        pattern = re.escape(w).replace(r"\-", r"\s*-\s*")
        text = re.sub(pattern, _record, text, flags=re.IGNORECASE)

    prev: str | None = None
    while prev != text:
        prev = text
        text = _SOFT_HYPHEN_PATTERN.sub(lambda m: m.group(1) + m.group(2), text)

    for key, original in placeholders.items():
        text = text.replace(key, original)
    return text


# =============================================================================
# 言語判定 (ヒューリスティック)
# =============================================================================

_LANG_MARKERS_FR = [
    " de la ", " les ", " une ", " chez ", " psychologie", " maladies",
    " ressources", " santé", " auprès", " thérap", " face aux",
    " pouvoirs de", " souffrant", " atteints", " troubles anxieux",
    " en psychologie positive", " interventions en", " interventions centrée",
]
_LANG_MARKERS_DE = [" der ", " die ", " und ", " für ", " mit ", " bei ", " über "]
_LANG_MARKERS_ES = [" de los ", " de las ", " hacia ", " ensayo "]


def detect_language(text: str) -> str:
    """ISO 639-1 二文字コードを返す。現状は en/fr/de/es のみ対応。"""
    head = text[:500].lower()
    if any(m in head for m in _LANG_MARKERS_FR):
        return "fr"
    if any(m in head for m in _LANG_MARKERS_DE):
        return "de"
    if any(m in head for m in _LANG_MARKERS_ES):
        return "es"
    return "en"


# =============================================================================
# DOI 抽出と alt 候補生成
# =============================================================================

_DOI_RE = re.compile(
    r"(?:https?://(?:dx\.)?doi\.org/|doi:\s*)([^\s,;)]+)", re.IGNORECASE
)


def strip_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = doi.strip().rstrip(".,;:)")
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    return doi or None


def build_doi_alt(doi: str | None) -> str | None:
    """DOI 内の 'word-word' を 'wordword' に圧縮した候補を返す。

    PDF コピペで内部ハイフンが混入した DOI (例 'gpsych-2022-100871' の途中に
    誤って挿入されたハイフン) への救済用。数字間ハイフン (識別子の一部) は
    保持する。
    """
    if not doi or "/" not in doi:
        return None
    prefix, path = doi.split("/", 1)
    alt_path = re.sub(r"(?<=[a-z])-(?=[a-z])", "", path, flags=re.IGNORECASE)
    if alt_path == path:
        return None
    return f"{prefix}/{alt_path}"


# =============================================================================
# 著者リスト抽出
# =============================================================================

_AUTHOR_ITEM_RE = re.compile(
    r"""
    (?P<surname>
        (?:[Vv]an\s+(?:der\s+|de[nr]?\s+)?)?
        (?:[Dd]e\s+la\s+)?(?:[Dd]el?\s+)?
        [A-ZÀ-Ÿ][A-Za-zÀ-ÿ'’‐\-]+
        (?:[\-\s][A-ZÀ-Ÿ][A-Za-zÀ-ÿ'’‐\-]+)?
    )
    ,\s*
    (?P<given>
        [A-ZÀ-Ÿ]\.(?:[\s\-]*[A-ZÀ-Ÿ]\.)*
    )
    """,
    re.VERBOSE,
)


def parse_authors(text: str) -> tuple[list[dict[str, str]], str]:
    """著者リストを抽出し、タイトル以降のテキストを返す。

    Returns:
        (authors_list, title_and_rest_text)
    """
    items: list[dict[str, Any]] = []
    pos = 0
    for m in _AUTHOR_ITEM_RE.finditer(text):
        if pos and m.start() != pos:
            gap = text[pos:m.start()]
            if not re.fullmatch(r"[;\s,]*(?:et\s+al\.)?[;\s,]*", gap):
                break
        items.append({
            "surname": m.group("surname").strip(),
            "given": m.group("given").strip(),
            "raw": m.group(0),
            "end": m.end(),
        })
        pos = m.end()

    if not items:
        return [], text

    last_end = items[-1]["end"]
    rest = text[last_end:]

    m_etal = re.match(r"[;,]?\s*et\s+al\.\s*", rest)
    if m_etal:
        last_end += m_etal.end()
        rest = text[last_end:]

    m_sep = re.match(r"[.\s;,]+(?=[A-ZÀ-ÿ])", rest)
    if m_sep:
        rest = text[last_end + m_sep.end():]

    authors_out = [
        {"surname": a["surname"], "given": a["given"], "raw": a["raw"]}
        for a in items
    ]
    return authors_out, rest


# =============================================================================
# Title/Journal 境界検出
# =============================================================================

# Journal 略称の "接続詞" トークンセット (小文字で含まれることを許可)
_JOURNAL_CONNECTIVES = {
    "of", "and", "in", "for", "the", "a", "an", "&", "de", "la", "et", "du",
    "der", "und", "di", "on", "to", "with", "at", "by", "or", "from", "as",
    "die", "le", "des", "en", "y", "da",
}


def looks_like_journal(candidate: str, max_tokens: int = 8) -> bool:
    """候補文字列が "ジャーナル名らしい" かを判定する。

    全トークンが (a) 大文字始まり、(b) 接続詞、(c) 記号/数字 のいずれかに
    該当し、かつ合計トークン数が max_tokens 以下のときに True。
    """
    tokens = candidate.split()
    if not tokens or len(tokens) > max_tokens:
        return False
    for t in tokens:
        stem = t.rstrip(",.;:!?)").lstrip("(")
        if not stem:
            return False
        if stem[0].isupper():
            continue
        if stem.lower() in _JOURNAL_CONNECTIVES:
            continue
        if not stem[0].isalnum():
            continue
        return False
    return True


def parse_title_journal_year_vol_pages(rest: str) -> dict[str, Any]:
    """rest 文字列から Title / Journal / Year / Volume / Issue / Pages を抽出。

    期待フォーマット: "Title text. Journal Abbr. Year, Vol, Pages"
                      (DOI/ISBN 等の末尾情報は呼び出し側で除去済み)
    """
    d: dict[str, Any] = {
        "title": None, "journal": None, "year": None,
        "volume": None, "issue": None, "pages": None,
    }
    s = rest.strip().rstrip(",.;: ")
    if not s:
        return d

    # Year 検出 (汎用パターン: " YYYY,")
    m_year = re.search(r"\s(\d{4})\s*,", s)
    if not m_year:
        # Nature/Cell 系 "(YYYY)" 末尾パターン
        m_year2 = re.search(r"\((\d{4})\)", s)
        if m_year2:
            d["year"] = int(m_year2.group(1))
            d["title"] = s[:m_year2.start()].rstrip(" .,")
            return d
        d["title"] = s
        return d

    d["year"] = int(m_year.group(1))
    head = s[:m_year.start()].rstrip(" .,")  # Title + Journal
    tail = s[m_year.end():].lstrip(" ,")     # Vol, Pages

    # Title/Journal 境界: head の ". " 位置を最小側から試し、looks_like_journal
    # を満たす最初の分割点を採用する
    dot_positions = [m.start() for m in re.finditer(r"\.\s+", head)]
    chosen: tuple[str, str] | None = None
    for pos in dot_positions:
        j_cand = head[pos + 1:].strip()
        title_cand = head[:pos + 1].strip().rstrip(".,;: ")
        if title_cand and looks_like_journal(j_cand):
            chosen = (title_cand, j_cand)
            break

    if chosen:
        d["title"], d["journal"] = chosen
    else:
        # Fallback: 逆向きトークン取り込み (journal の最後の単語にピリオドが
        # 無いケースに対応, 例 "Gen. Psychiatry 2022, ...")
        tokens = head.split()
        jidx: list[int] = []
        for i in range(len(tokens) - 1, -1, -1):
            t = tokens[i].rstrip(",.;:")
            if not t:
                continue
            if t[0].isupper() or t.lower() in _JOURNAL_CONNECTIVES:
                jidx.insert(0, i)
                if i == 0 or len(jidx) >= 5:
                    break
                prev = tokens[i - 1]
                if prev and prev[0].islower() and prev.lower() not in _JOURNAL_CONNECTIVES:
                    break
            else:
                break
        if jidx and jidx[0] > 0:
            d["title"] = " ".join(tokens[:jidx[0]]).strip().rstrip(" .,;:")
            d["journal"] = " ".join(tokens[jidx[0]:]).strip().rstrip(" ,;:")
        else:
            d["title"] = head

    # Vol, (Issue,) Pages
    m_vp = re.match(
        r"^\s*(\d+)\s*(?:\((\d+)\))?\s*,\s*([A-Za-z]?\d+(?:[–\-][A-Za-z]?\d+)?)",
        tail,
    )
    if m_vp:
        d["volume"] = m_vp.group(1)
        if m_vp.group(2):
            d["issue"] = m_vp.group(2)
        d["pages"] = m_vp.group(3).replace("–", "-")
    else:
        m_v = re.match(r"^\s*(\d+)", tail)
        if m_v:
            d["volume"] = m_v.group(1)
        m_p = re.search(r"[Ee]\d{4,}", tail)
        if m_p:
            d["pages"] = m_p.group(0)
    return d


# =============================================================================
# 書籍検出
# =============================================================================

_ISBN_RE = re.compile(r"ISBN[\s:]+([0-9\-xX]+)", re.IGNORECASE)

# 書籍であることを示す文字列群 (DOI 不在時のみ有効)
_BOOK_SIGNS_RE = re.compile(
    r"\b(pp\.\s*\d|Eds\.|Ed\.\s|Publisher|Press[,:;\s]|"
    r"In\s+[A-Z].+;|University\s+Press|Routledge|Springer,|Wiley,|"
    r"Oxford\s+University|W\s*H\s+Freeman|Basic\s+Books?|Free\s+press|"
    r"Taylor\s+&\s+Francis|Handbook\s+(?:of|on))",
    re.IGNORECASE,
)


# =============================================================================
# MDPI スタイル判定 (fast-path を適用するか)
# =============================================================================

def is_mdpi_style(raw: str) -> bool:
    """ブロックが MDPI 形式 (または MDPI パーサで処理可能) と判定できるとき True。

    判定順序 (early return):
      1. 著者必須: "Surname, I.Y.;" 形式が最低 1 名存在 (なければ False)
      2. **Vancouver Veto**: "(YYYY)" 括弧年が含まれる場合は即 False
         (MDPI は "YYYY, Vol" 前置コンマ形式のため (YYYY) は出現しない)
      3. 以下いずれかが成立すれば MDPI fast-path 採用 (True):
         a) 末尾に "YYYY, Vol" パターン (標準的な MDPI 引用)
         b) DOI URL を含む
         c) ISBN または publisher/book signs を含む
      4. (e) 上記いずれにも該当しない = 不完全 MDPI ref、fast-path で graceful 処理 (True)

    判定 (4) により、著者のみ記載の不完全 ref (#117, #123 等) や
    出版社情報が欠落した書籍 (#141 等) も fast-path で処理でき、LLM 呼び出しを
    完全に回避できる。mdpi_parser 側は不完全 ref を parsing_confidence=low で
    マークするため、後段の判断に影響しない。

    Day9 (2026/05/09) で Vancouver Veto を導入し、(YYYY) 括弧年を含む
    Vancouver/AMA 系 ref が誤って MDPI fast-path に流れる問題を解消した。
    旧 markers (Smith J,/;Vol:Pages) は実 data で Vancouver 24 件中 1 件のみ
    捕捉と判明 (M1 = 24/24 の真サブセット) のため撤去。
    参照: docs/sessions/day9/SPEC_mdpi_fast_path_strict.md
    """
    # 著者パターン (最低1名必須)
    if not _AUTHOR_ITEM_RE.search(raw):
        return False
    # Vancouver Veto: "(YYYY)" 括弧年が見つかれば LLM ルーティング (Day9 で導入)
    #   このチェックは (a)(b)(c) より前に置く必要がある:
    #   さもないと "doi.org/..." 等を含む Vancouver ref が (b) で True を返してしまう
    #   (Stage 2 #1 Huizinga 2011 等が該当). SPEC §4.2 から実装段階で順序修正.
    if re.search(r"\((?:19|20)\d{2}\)", raw):
        return False
    # (a) 標準的 MDPI 末尾パターン
    if re.search(r"\s\d{4}\s*,\s*\d+", raw):
        return True
    # (b) DOI URL
    if "doi.org/" in raw:
        return True
    # (c) ISBN または書籍署名
    if _ISBN_RE.search(raw) or _BOOK_SIGNS_RE.search(raw):
        return True
    # (e) 上記いずれにも該当しない = 不完全 MDPI ref、fast-path で処理
    return True


# =============================================================================
# メイン構造化関数 (LLM 代替)
# =============================================================================

def structure_one_mdpi(ref_no: int, raw_text: str) -> dict[str, Any]:
    """MDPI 形式 1 件を構造化する (LLM 不使用)。

    Returns:
        llm_parsing_prompt.md スキーマに準拠した dict
    """
    raw = fix_hyphens(raw_text).strip()
    result: dict[str, Any] = {
        "ref_no": ref_no,
        "authors": [],
        "title": None,
        "journal": None,
        "year": None,
        "volume": None,
        "issue": None,
        "pages": None,
        "doi": None,
        "doi_alt": None,
        "pmid": None,
        "is_book": False,
        "language": "en",
        "parsing_confidence": "medium",
        "notes": None,
    }
    notes: list[str] = []

    # 言語判定
    result["language"] = detect_language(raw)

    # DOI 抽出
    body = raw
    m_doi = _DOI_RE.search(raw)
    if m_doi:
        doi = strip_doi(m_doi.group(1))
        result["doi"] = doi
        alt = build_doi_alt(doi)
        if alt:
            result["doi_alt"] = alt
        body = raw[:m_doi.start()].rstrip(" ,.;")

    # 書籍判定
    has_isbn = bool(_ISBN_RE.search(raw))
    has_book_signs = bool(_BOOK_SIGNS_RE.search(raw)) and not result["doi"]
    if has_isbn or has_book_signs:
        result["is_book"] = True
        body = re.split(r"\bISBN\b", body, flags=re.IGNORECASE)[0].rstrip(" ,;.")

    # 著者抽出
    authors, rest = parse_authors(body)
    result["authors"] = authors
    if not authors:
        notes.append("author_extraction_failed")
        result["title"] = body
        result["parsing_confidence"] = "low"
        if notes:
            result["notes"] = "; ".join(notes)
        return result

    # 著者のみで本文欠落 (原稿不備)
    if not rest.strip():
        notes.append(
            "incomplete_reference_in_source: "
            "authors only, no title/journal/year"
        )
        result["parsing_confidence"] = "low"
        if notes:
            result["notes"] = "; ".join(notes)
        return result

    if result["is_book"]:
        m_year = re.search(r"(\d{4})", rest)
        if m_year:
            result["year"] = int(m_year.group(1))
        parts = re.split(r"\s*[;]\s*", rest, maxsplit=3)
        first_part = parts[0] if parts else rest

        # "Chapter Title. In BookTitle;" 型
        m_in = re.search(r"\.\s+In\s+", first_part)
        if m_in:
            result["title"] = first_part[:m_in.start()].strip().rstrip(" .,;")
            book_name = first_part[m_in.end():].strip().rstrip(" .,;")
            result["journal"] = "In: " + "; ".join(
                [book_name] + (parts[1:] if len(parts) > 1 else [])
            )
        else:
            result["title"] = first_part.rstrip(" .,;").strip()
            if len(parts) > 1:
                pub_year = parts[1]
                m_pub = re.match(r"^(.+?),\s*(\d{4})", pub_year)
                if m_pub:
                    publisher = m_pub.group(1).strip()
                    # Strip ": City, Country" suffix commonly added by MDPI book refs
                    if ":" in publisher:
                        publisher = publisher.split(":", 1)[0].strip()
                    result["journal"] = publisher
                    if not result["year"]:
                        result["year"] = int(m_pub.group(2))
                else:
                    publisher = pub_year.rstrip(" ,;.")
                    if ":" in publisher:
                        publisher = publisher.split(":", 1)[0].strip()
                    result["journal"] = publisher
        result["parsing_confidence"] = "low"
        notes.append(
            "is_book=true; 'journal' field holds publisher/container; "
            "PubMed likely N/A"
        )
    else:
        d = parse_title_journal_year_vol_pages(rest)
        for k, v in d.items():
            if v is not None:
                result[k] = v

    # 最終 confidence 評価
    if not result["is_book"]:
        has_basics = all([
            result["authors"], result["title"], result["journal"], result["year"]
        ])
        if has_basics and result["doi"]:
            result["parsing_confidence"] = "high"
        elif has_basics:
            result["parsing_confidence"] = "medium"
        else:
            result["parsing_confidence"] = "low"
            miss = [
                k for k in ("authors", "title", "journal", "year")
                if not result.get(k)
            ]
            notes.append(f"missing: {','.join(miss)}")

    if notes:
        result["notes"] = "; ".join(notes)
    return result


def structure_all_mdpi(
    blocks: list[Any],
    *,
    verbose: bool = True,
) -> list[dict[str, Any]]:
    """MDPI パーサを全ブロックに適用する。

    Args:
        blocks: main.py の ReferenceBlock インスタンスのリスト
                (ref_no, raw_text 属性を持つ)
    """
    results: list[dict[str, Any]] = []
    for i, b in enumerate(blocks, 1):
        if verbose:
            print(
                f"  [{i:>3}/{len(blocks)}] Ref #{b.ref_no} (MDPI fast-path)...",
                flush=True,
            )
        results.append(structure_one_mdpi(b.ref_no, b.raw_text))
    return results
