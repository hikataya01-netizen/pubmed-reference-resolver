# Three-Class Audit Refinement Implementation Plan (Day20)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Day17 cell_45refs で多発した A 分類 false positive (14/15 → 想定 1+/15) を `three_class_classifier.py` に 3 helper (`_detect_book`, `_detect_conference`, `_classify_via_nlm_only`) と 4 rule 順次評価で改修し、cell + apa baseline を再生成して 100 tests pass を維持しつつ、副次的に Day7 §9.3 残最後 1 件 (Stage 3) を skill 機能経由達成として認証 cleanup する.

**Architecture:** Day15 で確立された `three_class_classifier.py` の `_classify_single` 関数を拡張. DOI 欠落時に「即 A」ではなく「is_book → B / conference → B / journal-only NLM 検索 → B|C|unknown / 全 fail → A」の 4 rule 順次評価. main.py:synthesize_outputs (line 1782-1792) で `unresolved_refs` 構築時に `is_book` flag (Phase 2 LLM output) を追加. cell + apa fixture の baseline を再生成し integration test 8 の期待値を実測値で更新. TDD 厳格 (test 追加 RED → production 実装 GREEN → baseline 再生成 → integration test 期待値更新).

**Tech Stack:** Python 3.11+ / pytest / Claude Sonnet 4.6 (baseline 再生成のみ ~$2) / NCBI E-utilities + Crossref (既存 fail-soft 設計)

**SPEC**: `docs/sessions/day20/SPEC_three_class_book_web_refinement.md` (commit `0b20e89`)

---

## File Structure

### 修正対象 (5 ファイル)

| ファイル | 修正内容 |
|:---|:---|
| `three_class_classifier.py` | 3 helper 追加 (`_detect_book`, `_detect_conference`, `_classify_via_nlm_only`) + `_classify_single` で 4 rule 順次評価 (DOI 欠落 case) |
| `tests/test_three_class_classifier.py` | 3 新 unit test 追加 + 既存 `test_classify_returns_A_when_doi_missing` の reason 文言を改修後仕様に整合 |
| `main.py` | line 1782-1792: `unresolved_refs` に `is_book` を追加 (Phase 2 structured 由来) |
| `tests/test_integration_cell_45refs.py` | line 内の `EXPECTED_THREE_CLASS_DISTRIBUTION` (test 8) を Day20 再生成後の実測値で更新 |
| `tests/test_integration_apa_45refs.py` | 同上 |

### Baseline 再生成 (4 ファイル + 2 README)

| ファイル | 再生成手段 |
|:---|:---|
| `tests/fixtures/cell_45refs/baseline_three_class_classification.json` | `python3 main.py ... --phase 4` Phase 4 再実行 |
| `tests/fixtures/cell_45refs/baseline_report.md` | 同上 |
| `tests/fixtures/cell_45refs/README.md` | 三分類実測値 section を改修後実値で update |
| `tests/fixtures/apa_45refs/baseline_three_class_classification.json` | 同上 |
| `tests/fixtures/apa_45refs/baseline_report.md` | 同上 |
| `tests/fixtures/apa_45refs/README.md` | 同上 |

注: `baseline_phase3_resolved.json` は不変 (Phase 3 結果は本改修と無関係).

### 新規作成 (Day20 archive 5 files)

| ファイル | 用途 |
|:---|:---|
| `docs/sessions/day20/STAGE3_COMPLETION_NOTE.md` | Stage 3 達成認証 |
| `docs/sessions/day20/PLAN_three_class_book_web_refinement.md` | 本 PLAN (既に作成中) |
| `docs/sessions/day20/README.md` | Day20 index |
| `docs/sessions/day20/DAY20_LESSONS_LEARNED.md` | Day20 末アーカイブ |

### 改変なし

- `crossref_check.py` / `nlm_catalog_check.py` (既存 logic 再利用、新規呼出箇所だけ増加)
- 全 fixture (mdpi_149refs / vancouver_24refs) (本 task と無関係)
- `tests/fixtures/cell_45refs/baseline_phase3_resolved.json` (Phase 3 不変)
- `tests/fixtures/apa_45refs/baseline_phase3_resolved.json` (同上)
- `.gitignore` / `.gitleaksignore` / `LICENSE` / `CHANGELOG.md` (Day19 で最終化、本 task で改変なし)

---

## Task 1: STAGE3_COMPLETION_NOTE.md 作成 (Phase 0)

**Files:**
- Create: `docs/sessions/day20/STAGE3_COMPLETION_NOTE.md`

- [ ] **Step 1: ファイル作成**

`docs/sessions/day20/STAGE3_COMPLETION_NOTE.md` に以下を書き込む:

```markdown
# Stage 3 達成認証 (Day20 clean up)

**Purpose**: Day7 PHASE_0_VERIFICATION_REPORT §1.1 で定義され Day8-19 で「未着手」として繰越されていた Stage 3 (Claude UI 経由でのスキル起動配線) について、現状の達成度を認証し long-term task table をクローズする.

## Day7 当時の定義 (2026/05/02)

`docs/sessions/day7/PHASE_0_VERIFICATION_REPORT.md` §1.1:

| 段階 | 入力 | 必要な準備 |
|:---:|:---|:---|
| Stage 3 | Claude UI 経由 | MCP/hook 配線 (Day8 以降) |

当時 Claude Code の skill 機能は未成熟であり、Claude UI から自然言語で skill を起動するには MCP server もしくは hook の手動配線が必要と想定された.

## Day20 時点 (2026-05-21) の現状

Claude Code skill 機能の成熟 (Day8-19 を通じて Anthropic 側で改善) により、以下の構成で Claude UI からの自動起動が既に成立:

1. `skill_package/SKILL.md` を `~/.claude/skills/pubmed-reference-resolver/` に symlink
2. SKILL.md の `description` frontmatter が Claude の skill triggering logic と整合 (Day14 で 3 分類精緻化、Day15 で 3 分類 audit logic 追記)
3. Claude UI から「この論文の参照文献を PubMed で逆引きして」等のプロンプト + DOCX 添付で **自動起動可能**

ユーザー (片山英樹) 自身が Day20 brainstorming Q0 で「(A) Claude Code の SKILL.md 経由で起動している (~/.claude/skills/ 下 symlink)」と確認済.

## 結論

**Stage 3 は実質達成済** (skill 機能経由). Day7 当時に想定された MCP/hook の追加配線は、現状の Claude Code 仕様では不要.

将来追加の高度な体験 (batch processing / progress 表示 / pre-tool-use validation 等) が必要となれば Day21+ で別途 MCP server / hook 設計可能 (本 note では out of scope).

## Day7 §9.3 long-term task table の更新

各 Day8-19 LESSONS.md に記載されていた以下の行を、Day20 archive 以降は「達成 (Day20 認証、Stage 3 = skill 機能で動作確認)」とみなす:

- 旧: `MCP/hook 経由 Stage 3 配線 | ⏳ 未着手`
- 新: `MCP/hook 経由 Stage 3 配線 | ✅ Day20 認証 (skill 機能で達成)`

過去 LESSONS.md の追記改修はしない (履歴尊重) が、Day20 README + LESSONS で本 note への明示参照を持つ.

---

**作成日**: 2026-05-21 (Day20 brainstorming 後)
**作成者**: Claude Code (Sonnet 4.6)
**承認**: 片山英樹 (Hideki Katayama、Q0 で確認)
**関連**: `docs/sessions/day7/PHASE_0_VERIFICATION_REPORT.md` §1.1, `skill_package/SKILL.md`
```

- [ ] **Step 2: 内容確認**

```bash
wc -l docs/sessions/day20/STAGE3_COMPLETION_NOTE.md && \
grep -c "Day7\|skill 機能\|Stage 3" docs/sessions/day20/STAGE3_COMPLETION_NOTE.md
```

Expected: ~40 行 + 5+ keyword hit.

- [ ] **Step 3: Phase 0 commit**

```bash
git add docs/sessions/day20/STAGE3_COMPLETION_NOTE.md && \
git commit -m "$(cat <<'EOF'
docs(sessions): add STAGE3_COMPLETION_NOTE for Day7 §9.3 cleanup (Day20 Phase 0)

Day7 PHASE_0_VERIFICATION_REPORT §1.1 で定義された「Stage 3 = Claude UI
経由スキル起動 (MCP/hook 配線)」が、Day8-19 を通じた Claude Code skill
機能の成熟により実質達成済であることを認証.

Day20 brainstorming Q0 でユーザーが「(A) SKILL.md 経由で起動済」と確認.
追加 MCP server / hook 配線は現状不要 (将来高度な体験が必要なら Day21+).

Day7 §9.3 long-term task table の「⏳ 未着手」を「✅ Day20 認証 (skill
機能で達成)」とみなす. 過去 LESSONS.md は履歴尊重で改修なし、Day20
README + LESSONS で本 note を明示参照.

Day7 §9.3 long-term task 完全クローズに向けた最後の認証 cleanup.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Unit test 3 新追加 + 1 修正 (Phase 2、TDD RED)

**Files:**
- Modify: `tests/test_three_class_classifier.py` (3 新 unit test + 1 既存修正)

注: 本 Task は TDD discipline 上 Phase 1 (production 実装) **前** に書く. test を先に書いて RED にし、Task 3 で production を実装して GREEN にする.

- [ ] **Step 1: 既存 test_classify_returns_A_when_doi_missing を修正 (新 logic に合わせて assertion 強化)**

`tests/test_three_class_classifier.py` 内の `test_classify_returns_A_when_doi_missing` を以下に置換:

```python
def test_classify_returns_A_when_doi_missing():
    """DOI 欠落 + journal も is_book も無い純粋 case → A 分類 (Rule 4 fallback).

    Day20 改修: 旧仕様 (DOI 欠落 = 無条件 A) から、4 rule 順次評価の
    最終 fallback (book/conference/journal 全て失敗時のみ A) に厳格化.
    本 test は Rule 4 fallback が動作することを保証する.
    """
    refs = [{"ref_no": 1, "doi": None, "journal": None, "is_book": False}]

    def fake_crossref(doi):
        raise AssertionError("Crossref should not be called when DOI is missing")
    def fake_nlm(**kwargs):
        raise AssertionError("NLM should not be called when journal is None")

    result = classify_unresolved_refs(refs, crossref_fn=fake_crossref, nlm_fn=fake_nlm)
    assert len(result) == 1
    assert result[0]["class"] == "A"
    assert result[0]["ref_no"] == 1
    assert "journal 不明" in result[0]["reason"] or "ハルシネーション候補" in result[0]["reason"]
```

- [ ] **Step 2: 新 test_classify_returns_B_when_is_book_true 追加**

`tests/test_three_class_classifier.py` 末尾に append:

```python


def test_classify_returns_B_when_is_book_true():
    """is_book=True ref は DOI 欠落でも B 分類される (book は MEDLINE 対象外、Rule 1).

    Day20 改修: 旧仕様だと A 分類になっていたが、book は本質的に MEDLINE
    indexing 対象外であり「真の捏造」ではない. Day17 cell_45refs #31/#32/#37
    が該当.
    """
    refs = [{"ref_no": 31, "doi": None, "journal": "", "is_book": True}]

    def fake_crossref(doi):
        raise AssertionError("Crossref should not be called for book")
    def fake_nlm(**kwargs):
        raise AssertionError("NLM should not be called for book")

    result = classify_unresolved_refs(refs, crossref_fn=fake_crossref, nlm_fn=fake_nlm)
    assert len(result) == 1
    assert result[0]["class"] == "B"
    assert "book" in result[0]["reason"].lower()
    assert result[0]["ref_no"] == 31
```

- [ ] **Step 3: 新 test_classify_returns_B_when_conference_proceedings 追加**

`tests/test_three_class_classifier.py` 末尾に append:

```python


def test_classify_returns_B_when_conference_proceedings():
    """journal 名に 'Conference' / 'Proceedings' / 'Workshop' 等を含む ref は B 分類 (Rule 2).

    Day20 改修: conference proceedings は MEDLINE 非収録が標準的.
    Day17 cell_45refs #34/#42/#43 が該当.
    """
    refs = [
        {"ref_no": 34, "doi": None,
         "journal": "International Conference on Trends in Electronics",
         "is_book": False},
        {"ref_no": 42, "doi": None,
         "journal": "Proceedings of the IEEE Workshop on ML",
         "is_book": False},
    ]

    def fake_crossref(doi):
        raise AssertionError("Crossref should not be called for conference")
    def fake_nlm(**kwargs):
        raise AssertionError("NLM should not be called for conference")

    result = classify_unresolved_refs(refs, crossref_fn=fake_crossref, nlm_fn=fake_nlm)
    assert len(result) == 2
    assert all(r["class"] == "B" for r in result)
    reasons_lower = [r["reason"].lower() for r in result]
    assert any("conference" in r or "proceedings" in r for r in reasons_lower)
```

- [ ] **Step 4: 新 test_classify_calls_nlm_when_doi_missing_with_journal 追加**

`tests/test_three_class_classifier.py` 末尾に append:

```python


def test_classify_calls_nlm_when_doi_missing_with_journal():
    """DOI 欠落 + journal 名あり + 非 book + 非 conference → NLM 直接検索 (Rule 3).

    Day20 改修: 旧仕様だと A 分類になっていたが、journal 名が判明していれば
    NLM Catalog を直接検索して B/C 判定可能. Day17 cell_45refs
    #33/#36/#38/#40/#41/#44/#45 が該当.
    """
    refs = [
        {"ref_no": 33, "doi": None, "journal": "Eng", "is_book": False},
        {"ref_no": 38, "doi": None, "journal": "Journal of Engineered Fibers", "is_book": False},
    ]

    nlm_calls = []
    def fake_crossref(doi):
        raise AssertionError("Crossref should not be called when DOI is missing")
    def fake_nlm(**kwargs):
        nlm_calls.append(kwargs)
        if "Engineered" in (kwargs.get("journal_name") or ""):
            return {"status": "Y", "nlm_id": "12345", "medlineta": "JEF"}
        return {"status": "N", "nlm_id": None, "medlineta": None}

    result = classify_unresolved_refs(refs, crossref_fn=fake_crossref, nlm_fn=fake_nlm)
    assert len(nlm_calls) == 2, f"NLM should be called for each ref, got {len(nlm_calls)} calls"
    assert result[0]["class"] == "B", f"'Eng' (status=N) → B, got {result[0]['class']!r}"
    assert result[1]["class"] == "C", f"'Engineered Fibers' (status=Y) → C, got {result[1]['class']!r}"
```

- [ ] **Step 5: test 全件 RED 確認 (production code が未実装のため fail 期待)**

Run: `python3 -m pytest tests/test_three_class_classifier.py -v 2>&1 | tail -15`

Expected: 既存 4 tests pass + 4 つの新 test (Step 1-4) のうち少なくとも 3 つ (新規追加分) は **FAIL** (production code 未改修).

- Step 1 (修正 test) は 既存 logic でも reason 文言 mismatch で fail する可能性が高い
- Step 2-4 (新規) は確実に fail (3 helper 未実装)

⚠️ もし全 test pass する場合: 既存 production code が既に新 logic を含んでいる可能性. 確認のため Task 3 (production 実装) に進む前に再 grep:

```bash
grep -c "def _detect_book\|def _detect_conference\|def _classify_via_nlm_only" three_class_classifier.py
```

Expected: 0 (未実装).

- [ ] **Step 6: 単独 commit せず、Task 3 完了後に統合 commit** (TDD RED → GREEN を 1 commit でまとめる pattern も可能、本 plan では Task 3 で production 実装後に統合 commit する)

---

## Task 3: three_class_classifier.py 改修 (Phase 1、TDD GREEN)

**Files:**
- Modify: `three_class_classifier.py` (3 helper 追加 + `_classify_single` の DOI 欠落 case を 4 rule 順次評価に変更)

- [ ] **Step 1: import 追加 (re module)**

`three_class_classifier.py` の import section (line 50-55 付近) を以下に変更:

```python
from __future__ import annotations

import re
from typing import Any, Callable

import crossref_check
import nlm_catalog_check
```

(変更点: `import re` を追加)

- [ ] **Step 2: module-level constant `_CONFERENCE_PATTERNS` を追加**

`three_class_classifier.py` の import 直後 (line 56 付近、`def classify_unresolved_refs` の前) に以下を追加:

```python


_CONFERENCE_PATTERNS = re.compile(
    r"\b(?:conference|conf\.|proceedings|proc\.|workshop|symposium|"
    r"symp\.|congress|meeting)\b",
    re.IGNORECASE,
)
```

- [ ] **Step 3: 3 helper 関数を追加 (`_classify_single` の前)**

`three_class_classifier.py` の `def _classify_single(...)` 直前 (line 86 付近) に以下 3 helper を追加:

```python
def _detect_book(ref: dict[str, Any]) -> bool:
    """ref が book chapter か判定.

    Day20 Rule 1: is_book=True なら book と確定.
    フォールバック: raw_text に 'isbn' 含む or publisher field 在り.
    """
    if ref.get("is_book") is True:
        return True
    raw = (ref.get("raw_text") or "").lower()
    if "isbn" in raw:
        return True
    if "publisher" in raw and ref.get("publisher"):
        return True
    return False


def _detect_conference(journal: str | None) -> bool:
    """journal 名に conference/proceedings/workshop 等を含むか判定.

    Day20 Rule 2: \\b 単語境界で false positive 抑制.
    """
    if not journal:
        return False
    return bool(_CONFERENCE_PATTERNS.search(journal))


def _classify_via_nlm_only(
    ref_no: int,
    journal: str,
    nlm_fn: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    """DOI 欠落だが journal 名は判明している case の NLM 直接検索.

    Day20 Rule 3: Crossref skip して NLM Catalog で journal indexing 確認.
    status=N → B / status=Y → C / status=None → unknown.
    """
    nlm = nlm_fn(journal_name=journal)
    status = nlm.get("status")
    base = {
        "ref_no": ref_no,
        "doi_resolved": None,
        "journal_indexing": status,
        "details": {
            "doi": None,
            "crossref_journal": journal,
            "nlm_id": nlm.get("nlm_id"),
            "nlm_medlineta": nlm.get("medlineta"),
        },
    }
    if status == "N":
        return {
            **base,
            "class": "B",
            "reason": (
                f"DOI 欠落だが journal '{journal}' は MEDLINE 非収録 "
                "(NLM 直接検索)"
            ),
        }
    if status == "Y":
        return {
            **base,
            "class": "C",
            "reason": (
                f"DOI 欠落、journal '{journal}' は MEDLINE 収録だが "
                "本論文単体は indexing なし"
            ),
        }
    return {
        **base,
        "class": "unknown",
        "reason": f"DOI 欠落 + NLM 検索でも判定不可: {nlm.get('error')}",
    }
```

- [ ] **Step 4: `_classify_single` の DOI 欠落 case (line 96-105 付近) を 4 rule 順次評価に置換**

`three_class_classifier.py` 内の `_classify_single` 関数のうち、以下旧 code:

```python
    # DOI 欠落 or 不正形式 → A
    if not doi or not str(doi).startswith("10."):
        return {
            "ref_no": ref_no,
            "class": "A",
            "reason": "DOI 欠落 or 不正形式 (LLM ハルシネーション候補)",
            "doi_resolved": None,
            "journal_indexing": None,
            "details": {"doi": doi, "journal": journal},
        }
```

を以下の **4 rule 順次評価** に置換:

```python
    # Day20 改修: DOI 欠落 case を 4 rule 順次評価に拡張
    if not doi or not str(doi).startswith("10."):
        # Rule 1: is_book → B (book は MEDLINE 対象外)
        if _detect_book(ref):
            return {
                "ref_no": ref_no,
                "class": "B",
                "reason": "book chapter (DOI 欠落だが MEDLINE 対象外)",
                "doi_resolved": None,
                "journal_indexing": None,
                "details": {"doi": doi, "journal": journal, "is_book": True},
            }

        # Rule 2: conference proceedings → B (MEDLINE 非収録が標準)
        if _detect_conference(journal):
            return {
                "ref_no": ref_no,
                "class": "B",
                "reason": (
                    f"conference/proceedings '{journal}' "
                    "(MEDLINE 非収録が標準)"
                ),
                "doi_resolved": None,
                "journal_indexing": None,
                "details": {"doi": doi, "journal": journal, "conference": True},
            }

        # Rule 3: journal 名あり → NLM 直接検索 (B/C/unknown)
        if journal:
            return _classify_via_nlm_only(ref_no, journal, nlm_fn)

        # Rule 4: 全て該当せず → A (真の判定不可)
        return {
            "ref_no": ref_no,
            "class": "A",
            "reason": (
                "DOI 欠落 + journal 不明 (真の判定不可、"
                "LLM ハルシネーション候補)"
            ),
            "doi_resolved": None,
            "journal_indexing": None,
            "details": {"doi": doi, "journal": journal},
        }
```

(line 108 以降の Crossref 呼出 logic は不変)

- [ ] **Step 5: 改修確認 (3 helper + 4 rule)**

```bash
grep -c "def _detect_book\|def _detect_conference\|def _classify_via_nlm_only" three_class_classifier.py
```

Expected: `3`

```bash
grep -c "Rule 1: is_book\|Rule 2: conference\|Rule 3: journal\|Rule 4:" three_class_classifier.py
```

Expected: `4`

- [ ] **Step 6: unit test 全件 GREEN 確認**

Run: `python3 -m pytest tests/test_three_class_classifier.py -v 2>&1 | tail -15`

Expected: **8 passed** (既存 5 + 新 3 - 修正 1 で count 維持、いや 5 既存 + 3 新 = 8、修正 1 は assertion 文言だけ調整)

⚠️ FAIL の場合: production code logic に bug. Step 4 の rule 順序や reason 文言を再点検.

- [ ] **Step 7: Phase 1+2 統合 commit**

```bash
git add three_class_classifier.py tests/test_three_class_classifier.py && \
git commit -m "$(cat <<'EOF'
feat(three-class): refine DOI-missing classification with 4-rule sequential eval (Day20 Phase 1+2)

Day17 cell_45refs で多発した A 分類 false positive (14/15、book chapter +
conference proceedings + DOI 無 journal を「LLM ハルシネーション候補」と
誤分類) を解決するため、three_class_classifier.py の _classify_single
を改修. DOI 欠落 case を「即 A」から 4 rule 順次評価に変更:

  Rule 1: is_book=True → B (book は MEDLINE 対象外)
  Rule 2: journal 名に conference/proceedings/workshop 等含む → B
  Rule 3: journal 名あり → NLM 直接検索で B/C/unknown
  Rule 4: 全て該当せず → A (真の判定不可)

3 helper 関数を新規追加:
  - _detect_book(ref): is_book / ISBN / publisher signal
  - _detect_conference(journal): \b 単語境界 regex (false positive 抑制)
  - _classify_via_nlm_only(ref_no, journal, nlm_fn): Crossref skip 版 NLM 検索

tests/test_three_class_classifier.py に 3 新 unit test 追加 + 既存 1
test (test_classify_returns_A_when_doi_missing) の reason 文言を新仕様に
整合:
  - test_classify_returns_B_when_is_book_true (Rule 1)
  - test_classify_returns_B_when_conference_proceedings (Rule 2)
  - test_classify_calls_nlm_when_doi_missing_with_journal (Rule 3)

合計 8 unit tests 全 PASS. TDD strict order (Phase 2 test 先 RED →
Phase 1 production 実装 GREEN).

Day17 D17 教訓 + Day19 §6.2 候補の実装. integration test 期待値更新と
fixture 再生成は Phase 3-4 で別 commit.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: main.py:synthesize_outputs で is_book を unresolved_refs に追加 (Phase 3)

**Files:**
- Modify: `main.py:1782-1792` (unresolved_refs 構築箇所)

- [ ] **Step 1: 現状確認**

```bash
sed -n '1780,1798p' main.py
```

Expected: line 1782-1792 で `unresolved_refs.append({...})` が現状 `ref_no` / `doi` / `journal` のみ追加.

- [ ] **Step 2: is_book + raw_text を追加**

Edit `main.py` line 1788-1792 周辺の `unresolved_refs.append({...})` を以下に置換:

旧:
```python
        unresolved_refs.append({
            "ref_no": ref_no,
            "doi": s.get("doi") or s.get("doi_alt"),
            "journal": s.get("journal"),
        })
```

新:
```python
        unresolved_refs.append({
            "ref_no": ref_no,
            "doi": s.get("doi") or s.get("doi_alt"),
            "journal": s.get("journal"),
            "is_book": s.get("is_book", False),
            "raw_text": s.get("raw_text", ""),
            "publisher": s.get("publisher", ""),
        })
```

(変更点: `is_book` / `raw_text` / `publisher` 3 fields を追加. `_detect_book` の ISBN/publisher fallback で利用)

- [ ] **Step 3: 既存 integration tests に regression がないか確認**

Run: `python3 -m pytest tests/ -v 2>&1 | tail -3`

Expected: **100 passed, 1 skipped** (97 既存 + 3 新 unit = 100、cell/apa integration test の test 8 はまだ古い期待値で fail する可能性あり)

⚠️ test 8 の 2 件 (cell + apa) は **FAIL 想定** (Phase 4a/4b で baseline 再生成 + 期待値更新後に pass する). 一時的 FAIL は許容、ただし他 98 件は pass を確認.

実際の確認 command:
```bash
python3 -m pytest tests/ -v 2>&1 | grep -E "passed|failed" | tail -5
```

Expected like:
```
98 passed, 2 failed, 1 skipped (cell test 8 + apa test 8)
```

これは Phase 4 で解消する想定. FAIL は test 8 のみであることを確認 (他 fail があれば修正前に対処).

- [ ] **Step 4: Phase 3 commit**

```bash
git add main.py && \
git commit -m "$(cat <<'EOF'
chore(synthesize): pass is_book/raw_text/publisher to unresolved_refs (Day20 Phase 3)

main.py:synthesize_outputs の unresolved_refs 構築箇所 (line 1788-1792)
で、three_class_classifier.classify_unresolved_refs() に渡す dict に
以下 3 fields を追加:

  - is_book: Phase 2 LLM 出力の book chapter flag (Rule 1 で利用)
  - raw_text: ref の原文 (ISBN fallback で利用、_detect_book)
  - publisher: Phase 2 出力の出版社名 (publisher fallback、_detect_book)

Day20 改修 (Phase 1) で新規追加された 4 rule 順次評価のうち Rule 1
(_detect_book) が is_book / ISBN / publisher の各 signal を必要とする
ため、本 main.py 微改修が前提.

cell + apa integration test の test_baseline_three_class_classification
は本 commit 直後の test run では一時的に FAIL する想定 (baseline 再生成
+ 期待値更新が Phase 4a/4b で実施されるため). 他 98 tests は継続 pass.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: cell_45refs baseline 再生成 + test 8 期待値更新 (Phase 4a)

**Files:**
- Regenerate: `tests/fixtures/cell_45refs/baseline_three_class_classification.json`
- Regenerate: `tests/fixtures/cell_45refs/baseline_report.md`
- Modify: `tests/fixtures/cell_45refs/README.md` (三分類実測値 section 更新)
- Modify: `tests/test_integration_cell_45refs.py` (`EXPECTED_THREE_CLASS_DISTRIBUTION` 更新)

- [ ] **Step 1: .env 健全性確認**

```bash
uv run python -c "import os; from main import load_env_files; load_env_files(); print('ANTHROPIC:', bool(os.environ.get('ANTHROPIC_API_KEY'))); print('NCBI:', bool(os.environ.get('NCBI_API_KEY')))"
```

Expected: 両方 True.

- [ ] **Step 2: cell_45refs 再生成 (Phase 4 のみ、Phase 2/3 結果再利用)**

```bash
rm -rf /tmp/cell_45refs_day20_rerun && \
python3 main.py tests/fixtures/cell_45refs/input_References.docx \
  --output-dir /tmp/cell_45refs_day20_rerun \
  --phase 4 2>&1 | tail -10
```

Expected: 約 5-15 分で完走. `/tmp/cell_45refs_day20_rerun/` に以下が生成:
- `three_class_classification.json` (改修後分布、A=14 → 想定 1+)
- `report.md` (Phase 4 audit report、三分類 sub-section 更新済)

⚠️ 失敗時: `--reuse-phase2 --reuse-phase3` で部分再実行を試みる (Phase 2/3 結果再利用):
```bash
python3 main.py tests/fixtures/cell_45refs/input_References.docx \
  --output-dir /tmp/cell_45refs_day20_rerun \
  --phase 4 --reuse-phase2 --reuse-phase3
```

- [ ] **Step 3: 改修後分布を確認**

```bash
python3 -c "
import json
data = json.load(open('/tmp/cell_45refs_day20_rerun/three_class_classification.json'))
print(f'Total: {len(data)}')
classes = {}
for c in data:
    cls = c.get('class', 'unknown')
    classes[cls] = classes.get(cls, 0) + 1
print(f'Distribution: {classes}')
print()
print('A 分類詳細 (Day19 は 14 件、Day20 改修後想定 1):')
for c in data:
    if c.get('class') == 'A':
        print(f'  #{c.get(\"ref_no\"):>2} reason={c.get(\"reason\", \"\")[:60]}')
"
```

Expected (実測依存): 例として
```
Total: 15
Distribution: {'B': 6, 'C': 2, 'unknown': 6, 'A': 1}

A 分類詳細 (Day19 は 14 件、Day20 改修後想定 1):
  #17 reason=DOI 欠落 + journal 不明 (真の判定不可、LLM ハルシネーション候補)
```

A=14 → 1 程度に大幅減少が想定. これらの実測値を Step 5 で更新する.

- [ ] **Step 4: baseline 2 ファイルを fixture に配置**

```bash
cp /tmp/cell_45refs_day20_rerun/three_class_classification.json \
   tests/fixtures/cell_45refs/baseline_three_class_classification.json && \
cp /tmp/cell_45refs_day20_rerun/report.md \
   tests/fixtures/cell_45refs/baseline_report.md && \
echo "Updated: cell_45refs baselines"
```

- [ ] **Step 5: README.md の三分類実測値 section を更新**

Read `tests/fixtures/cell_45refs/README.md` (旧値 `{A=14, B=0, C=0, unknown=1}` を Step 3 実測値で置換).

Edit `tests/fixtures/cell_45refs/README.md`:

旧:
```
- **三分類分布**: A=14, B=0, C=0, unknown=1
```

新 (Step 3 の実測値で `<NEW_*>` を置換):
```
- **三分類分布**: A=<NEW_A>, B=<NEW_B>, C=<NEW_C>, unknown=<NEW_UNKNOWN> (Day20 改修後実測)
```

同様に README 内の他の三分類言及箇所 (related test section の `A=14, B=0, C=0, unknown=1` 等) も `<NEW_*>` で更新.

- [ ] **Step 6: test_integration_cell_45refs.py の test 8 期待値を更新**

`tests/test_integration_cell_45refs.py` 内の `EXPECTED_THREE_CLASS_DISTRIBUTION` 定数を Step 3 実測値で更新:

旧:
```python
EXPECTED_THREE_CLASS_DISTRIBUTION = {
    "A": 14,
    "B": 0,
    "C": 0,
    "unknown": 1,
}  # Day17 Phase 0b 実測 (README.md 参照)
```

新 (Step 3 実測値):
```python
EXPECTED_THREE_CLASS_DISTRIBUTION = {
    "A": <NEW_A>,
    "B": <NEW_B>,
    "C": <NEW_C>,
    "unknown": <NEW_UNKNOWN>,
}  # Day20 改修後実測 (cell_45refs/README.md 参照)
```

- [ ] **Step 7: test 8 pass 確認**

```bash
python3 -m pytest tests/test_integration_cell_45refs.py::test_baseline_three_class_classification_distribution -v
```

Expected: **PASS**

⚠️ FAIL の場合: Step 3 実測値と Step 6 期待値が乖離している. Step 3 出力を再確認して Step 6 を補正.

- [ ] **Step 8: Phase 4a commit**

```bash
git add tests/fixtures/cell_45refs/baseline_three_class_classification.json \
        tests/fixtures/cell_45refs/baseline_report.md \
        tests/fixtures/cell_45refs/README.md \
        tests/test_integration_cell_45refs.py && \
git commit -m "$(cat <<'EOF'
test(fixtures): regenerate cell_45refs baselines after Day20 three-class refinement (Phase 4a)

Day20 Phase 1-3 の three_class_classifier 改修 (3 helper + 4 rule 順次
評価 + main.py で is_book/raw_text/publisher 渡し) を反映して
cell_45refs baseline を再生成.

三分類分布の推移:
  Day17 (D19 baseline): A=14, B=0, C=0, unknown=1
  Day20 改修後:         A=<NEW_A>, B=<NEW_B>, C=<NEW_C>, unknown=<NEW_UNKNOWN>

A 分類大幅減少 (14 → <NEW_A>): book chapter / conference proceedings /
DOI 無 journal が正しく B/C/unknown に振り直された. Day17 D17 教訓
(false positive 多発) を解消.

更新ファイル:
  - baseline_three_class_classification.json (再生成)
  - baseline_report.md (再生成、三分類 sub-section 更新)
  - README.md (三分類実測値 section 更新)
  - test_integration_cell_45refs.py:EXPECTED_THREE_CLASS_DISTRIBUTION 更新

baseline_phase3_resolved.json は不変 (Phase 3 結果は本改修と無関係).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: apa_45refs baseline 再生成 + test 8 期待値更新 (Phase 4b)

**Files:**
- Regenerate: `tests/fixtures/apa_45refs/baseline_three_class_classification.json`
- Regenerate: `tests/fixtures/apa_45refs/baseline_report.md`
- Modify: `tests/fixtures/apa_45refs/README.md`
- Modify: `tests/test_integration_apa_45refs.py`

(Task 5 と同型 pattern、apa_45refs 用に置換)

- [ ] **Step 1: apa_45refs 再生成 (Phase 4 のみ)**

```bash
rm -rf /tmp/apa_45refs_day20_rerun && \
python3 main.py tests/fixtures/apa_45refs/input_References.docx \
  --output-dir /tmp/apa_45refs_day20_rerun \
  --phase 4 2>&1 | tail -10
```

⚠️ Phase 2/3 結果が古いケースで再利用したい場合: `--reuse-phase2 --reuse-phase3` 追加.

- [ ] **Step 2: 改修後分布を確認**

```bash
python3 -c "
import json
data = json.load(open('/tmp/apa_45refs_day20_rerun/three_class_classification.json'))
print(f'Total: {len(data)}')
classes = {}
for c in data:
    cls = c.get('class', 'unknown')
    classes[cls] = classes.get(cls, 0) + 1
print(f'Distribution: {classes}')
"
```

Expected (実測依存): 例として
```
Total: 20
Distribution: {'B': 5, 'unknown': 13, 'A': 2}
```

Day16 baseline (A=4, B=0, C=0, unknown=16) からの変動を測定.

- [ ] **Step 3: baseline 2 ファイルを fixture に配置**

```bash
cp /tmp/apa_45refs_day20_rerun/three_class_classification.json \
   tests/fixtures/apa_45refs/baseline_three_class_classification.json && \
cp /tmp/apa_45refs_day20_rerun/report.md \
   tests/fixtures/apa_45refs/baseline_report.md
```

- [ ] **Step 4: README.md の三分類実測値 section を更新**

`tests/fixtures/apa_45refs/README.md` の `**三分類分布**: A=4, B=0, C=0, unknown=16` を Step 2 実測値で置換. 関連 section (test 8 説明等) も更新.

- [ ] **Step 5: test_integration_apa_45refs.py の test 8 期待値を更新**

旧:
```python
EXPECTED_THREE_CLASS_DISTRIBUTION = {
    "A": 4,
    "B": 0,
    "C": 0,
    "unknown": 16,
}  # Day16 Phase 0b 実測 (README.md 参照)
```

新 (Step 2 実測値):
```python
EXPECTED_THREE_CLASS_DISTRIBUTION = {
    "A": <NEW_A>,
    "B": <NEW_B>,
    "C": <NEW_C>,
    "unknown": <NEW_UNKNOWN>,
}  # Day20 改修後実測 (apa_45refs/README.md 参照)
```

- [ ] **Step 6: test 8 pass 確認**

```bash
python3 -m pytest tests/test_integration_apa_45refs.py::test_baseline_three_class_classification_distribution -v
```

Expected: **PASS**

- [ ] **Step 7: 全 tests 再確認 (100 passed 復旧)**

```bash
python3 -m pytest tests/ -v 2>&1 | tail -3
```

Expected: **100 passed, 1 skipped**

⚠️ cell_45refs test 8 + apa_45refs test 8 が両方 pass し、合計 100 で安定することを確認.

- [ ] **Step 8: Phase 4b commit**

```bash
git add tests/fixtures/apa_45refs/baseline_three_class_classification.json \
        tests/fixtures/apa_45refs/baseline_report.md \
        tests/fixtures/apa_45refs/README.md \
        tests/test_integration_apa_45refs.py && \
git commit -m "$(cat <<'EOF'
test(fixtures): regenerate apa_45refs baselines after Day20 three-class refinement (Phase 4b)

Day20 Phase 1-3 の three_class_classifier 改修を apa_45refs にも反映.
cell_45refs (Phase 4a) と同型 baseline 再生成.

三分類分布の推移:
  Day16 (baseline):     A=4, B=0, C=0, unknown=16
  Day20 改修後:         A=<NEW_A>, B=<NEW_B>, C=<NEW_C>, unknown=<NEW_UNKNOWN>

更新ファイル:
  - baseline_three_class_classification.json (再生成)
  - baseline_report.md (再生成)
  - README.md (三分類実測値 section 更新)
  - test_integration_apa_45refs.py:EXPECTED_THREE_CLASS_DISTRIBUTION 更新

Phase 4a + 4b 完了で全 tests 100 passed / 1 skipped 復旧.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Day20 archive (Phase 5)

**Files:**
- Create: `docs/sessions/day20/README.md`
- Create: `docs/sessions/day20/DAY20_LESSONS_LEARNED.md`

- [ ] **Step 1: Day20 README.md を作成**

Day19 (`docs/sessions/day19/README.md`) を template に、`docs/sessions/day20/README.md` に以下を書き込む (`<NEW_*>` 等の placeholder は Phase 4a/4b 実測値で置換):

```markdown
# docs/sessions/day20/

**Day20 セッション (2026-05-21) のアーカイブ**

このディレクトリは、pubmed-reference-resolver プロジェクトの Day20 セッション (三分類 audit の book/proceedings/DOI 欠落 case 改修 + Day7 §9.3 残最後 1 件 Stage 3 の達成認証 cleanup) で生成された記録を、永続アーカイブとして保管する.

## 内容

| ファイル | 役割 |
|:---|:---|
| `SPEC_three_class_book_web_refinement.md` | brainstorming 確定設計仕様 (Q0-Q3 + 4 sections) |
| `PLAN_three_class_book_web_refinement.md` | writing-plans 出力の段階的実装計画 (Task 1-7 + Verification) |
| `STAGE3_COMPLETION_NOTE.md` | Stage 3 達成認証 (Day7 §9.3 long-term task の完全 clean up evidence) |
| `DAY20_LESSONS_LEARNED.md` | Day20 全 commits の経緯 + 教訓 D20-1+ |
| `README.md` | 本書 |

## Day20 の特徴

Day7 §9.3 long-term task 7 件中、**最後の 1 件 (Stage 3) を達成認証として完全クローズ**. 同時に Day17 D17 起源の三分類 false positive 問題を解決し、cell_45refs A 分類を 14 → <NEW_A> 件に大幅減少.

## 達成事項 (Day20 commits)

| 順 | commit | Phase | 達成 |
|:---:|:---:|:---:|:---|
| (前) | `0b20e89` | — | Day20 SPEC archive (490 行) |
| (前) | `<hash>` | — | Day20 PLAN archive |
| 1 | `<hash>` | 0 | STAGE3_COMPLETION_NOTE.md (Stage 3 達成認証) |
| 2-3 | `<hash>` | 1+2 | three_class_classifier.py 改修 + unit test 3 新 + 1 修正 (8 tests) |
| 4 | `<hash>` | 3 | main.py:synthesize_outputs で is_book/raw_text/publisher 渡し |
| 5 | `<hash>` | 4a | cell_45refs baseline 再生成 + test 8 更新 |
| 6 | `<hash>` | 4b | apa_45refs baseline 再生成 + test 8 更新 |
| 7 | (本 commit) | 5 | Day20 archive (README + LESSONS) |

main branch: 83 → **<N>** + 本 commit で **<N+1> commits** (Day19 末 → Day20 末、+<delta>).
test 健全性: 97 passed → **100 passed** (+3 unit tests) / 1 skipped.

## Day7 §9.3 long-term task 完全クローズ

| タスク | 状態 (Day20 末) |
|:---|:---:|
| Vancouver golden fixture | ✅ Day11 |
| Day9 (Z) 未解決 2 件 MEDLINE 調査 | ✅ Day13 |
| Day13 §6 案 A: 3 分類 audit logic | ✅ Day15 |
| APA 系 golden fixture | ✅ Day16 |
| Cell 系 golden fixture | ✅ Day17 |
| GitHub remote + push (Private→Public) | ✅ Day18-19 |
| **MCP/hook 経由 Stage 3 配線** | ✅ **Day20 認証** (skill 機能で達成、STAGE3_COMPLETION_NOTE 参照) |

→ **7/7 達成、Day7 §9.3 long-term task 完全クローズ**.

## 三分類 audit の品質改善 (Day17 D17 解消)

| Fixture | Day19 末 baseline | Day20 改修後 |
|:---|:---:|:---:|
| cell_45refs | A=14, B=0, C=0, unknown=1 | A=<NEW_CELL_A>, B=<NEW_CELL_B>, C=<NEW_CELL_C>, unknown=<NEW_CELL_UNKNOWN> |
| apa_45refs | A=4, B=0, C=0, unknown=16 | A=<NEW_APA_A>, B=<NEW_APA_B>, C=<NEW_APA_C>, unknown=<NEW_APA_UNKNOWN> |

## GitHub 上の現状 (Day20 末)

| 項目 | 値 |
|:---|:---|
| URL | https://github.com/hikataya01-netizen/pubmed-reference-resolver |
| Visibility | PUBLIC (Day19 から継続) |
| License | MIT |
| Topics | 6 個 (pubmed / peer-review / claude-skill / medical-references / bibliographic-audit / reference-validation) |
| Pushed commits | <N+1> |
| Tests | 100 passed, 1 skipped |

---

**作成日**: 2026-05-21 (Day20 クロージング時)
**メンテナ**: 片山英樹 (Hideki Katayama)
```

- [ ] **Step 2: Day20 DAY20_LESSONS_LEARNED.md を作成**

`docs/sessions/day20/DAY20_LESSONS_LEARNED.md` に以下 (Day19 と同型構造、Day20 特化部分は本文で更新):

```markdown
# Day20 LESSONS LEARNED

**Day20 セッション (2026-05-21)**: 三分類 audit の book/proceedings/DOI 欠落 case 改修 (Day17 D17 解消) + Day7 §9.3 残最後 1 件 (Stage 3) 達成認証 cleanup

---

## 1. セッション概要

### 1.1 背景

Day19 末で Day7 §9.3 long-term task 残 1 件 (Stage 3 配線) + 副次タスク残数件. Day20 brainstorming Q0 で Stage 3 が既に SKILL.md 経由で達成済であることをユーザーが確認、Q1 で Day20 メインタスクを **(B1) AI 工学 book/web refs 三分類改修** (Day17 D17 起源) に決定. Stage 3 認証は同梱.

### 1.2 brainstorming 段階 (Q0-Q3)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q0 | Stage 3 の現状達成度 | (A) SKILL.md 経由で起動済 → 認証 cleanup |
| Q1 | Day20 メインタスク | (B1) AI 工学 book/web refs 三分類改修 |
| Q2 | 改修 scope | 全 7-13 件 cover (book + proceedings + DOI 無 journal) |
| Q3 | Test 戦略 | (完全) cell + apa baseline 再生成 + integration test 拡張 |

### 1.3 SPEC (commit `0b20e89`)

`docs/sessions/day20/SPEC_three_class_book_web_refinement.md` を archive (490 行、11 章).

### 1.4 PLAN (commit `<hash>`)

`docs/sessions/day20/PLAN_three_class_book_web_refinement.md` を archive. Task 1-7 + Verification で構成. TDD 厳格 (Phase 2 test 先 RED → Phase 1 production GREEN).

---

## 2. 実装段階の経緯 (7 commits + 2 pre = 9)

### Phase 0: STAGE3_COMPLETION_NOTE 作成 (commit `<hash>`)

- Task 1 (controller 直接実行): Day7 §9.3 残最後 1 件 (Stage 3) を SKILL.md 経由達成として認証. 過去 LESSONS は履歴尊重で改修なし.

### Phase 1+2: three_class_classifier 改修 + unit test (commit `<hash>`)

- Task 2 (TDD RED): test_three_class_classifier.py に 3 新 unit test + 1 既存修正. RED 確認.
- Task 3 (TDD GREEN): three_class_classifier.py に 3 helper (_detect_book / _detect_conference / _classify_via_nlm_only) + 4 rule 順次評価. GREEN 確認 (8 passed).

### Phase 3: main.py:synthesize_outputs 微改修 (commit `<hash>`)

- Task 4 (controller 直接実行): line 1788-1792 で unresolved_refs に is_book/raw_text/publisher 3 fields 追加. _detect_book の signal source 確保.

### Phase 4a: cell_45refs baseline 再生成 (commit `<hash>`)

- Task 5 (controller 直接実行): Phase 4 再実行 (LLM cost ~$1)、baseline_three_class_classification.json + baseline_report.md 再生成、README + test 8 期待値更新.
- 三分類: A=14 → <NEW_CELL_A> に大幅減少.

### Phase 4b: apa_45refs baseline 再生成 (commit `<hash>`)

- Task 6 (controller 直接実行): 同型処理を apa_45refs に適用. LLM cost ~$1.
- 三分類: A=4 → <NEW_APA_A>, unknown=16 → <NEW_APA_UNKNOWN> 変動.

### Phase 5: Day20 archive (本 commit)

- Task 7 (controller 直接実行): README + LESSONS archive.

---

## 3. 設計判断と検証

### 3.1 Stage 3 認証 cleanup の根拠

Day7 PHASE_0_VERIFICATION_REPORT §1.1 当時は Claude Code skill 機能が未成熟で MCP/hook 配線想定. 11 セッション (Day8-19) を経た現状では SKILL.md symlink で起動可能. **「未着手」のまま残置するのは現状と乖離**.

### 3.2 4 rule 順次評価の順序根拠

- Rule 1 (is_book) を最優先: book は MEDLINE 対象外という構造的判定で最も確実
- Rule 2 (conference): regex 1 つで簡潔
- Rule 3 (journal あり → NLM): API call 発生のため後位
- Rule 4 (全 fail → A): 「真の判定不可」として A 残留

### 3.3 TDD 厳格 (Phase 2 → Phase 1) の根拠

3 helper 新規追加 + 既存 logic 変更が混在するため、TDD で「期待される振る舞い」を test で先に固定. これにより:
- helper の interface (引数・戻り値) が test で明示される
- 既存 5 tests のうち 1 件の文言調整漏れを test failure で検出可能
- 実装段階での scope creep 防止

---

## 4. 実機検証結果

### 4.1 三分類 audit の品質改善

| Fixture | Day19 baseline | Day20 改修後 | A 減少 |
|:---|:---|:---|:---:|
| cell_45refs | A=14, B=0, C=0, unknown=1 | A=<NEW_CELL_A>, B=<NEW_CELL_B>, C=<NEW_CELL_C>, unknown=<NEW_CELL_UNKNOWN> | 14 → <NEW_CELL_A> |
| apa_45refs | A=4, B=0, C=0, unknown=16 | A=<NEW_APA_A>, B=<NEW_APA_B>, C=<NEW_APA_C>, unknown=<NEW_APA_UNKNOWN> | 4 → <NEW_APA_A> |

### 4.2 test 健全性

| 段階 | passed | 説明 |
|:---:|---:|:---|
| Day19 末 | 97 | (baseline) |
| Day20 Phase 1+2 後 | 100 | +3 新 unit test |
| Day20 Phase 4a 後 | 99 | cell test 8 期待値更新で復旧、apa test 8 がまだ FAIL |
| Day20 Phase 4b 後 | **100** ✅ | apa test 8 も期待値更新で復旧 |

---

## 5. 教訓 (D20-1, D20-2)

### 5.1 D20-1: long-term task の達成判定基準を時代変化に合わせる

**事象**: Day7 PHASE_0_VERIFICATION_REPORT で「Stage 3 = MCP/hook 配線」と定義された task が、Claude Code skill 機能の成熟により実質達成済だったが、Day8-19 で 11 セッション「未着手」として繰越し.

**学び**: 長期 task の達成判定基準は **当時の前提** に固定されがちだが、ツール・環境が成熟すると **別経路で達成済**になる可能性. 定期的に「当時の課題が現代の方法で解決済か?」を再評価することで dead task を整理.

**適用範囲**: 将来 long-term task table を維持する場合、半期 or 主要マイルストーン毎に「達成判定基準の妥当性」を再評価する慣行を導入.

### 5.2 D20-2: false positive 解消は実 fixture からの逆算で進める

**事象**: Day17 D17 で「A 多発 (14/15)」と問題提起されたが、Day17 当時は具体的に「何が誤分類されているか」が不明. Day20 で実 cell_45refs baseline を分析し、14 件全てが DOI 欠落 case (Crossref 404 ではなく) と判明.

**学び**: 品質改善 task では **実 fixture / 実 baseline から逆算**して原因を特定することが、抽象的議論より圧倒的に効率的. Day20 では 30 分の baseline 分析で **3 つの明確な改修方針** (book / conference / DOI 無 journal) を導出.

**適用範囲**: 将来 false positive / false negative の品質問題を扱う際は、まず実データから逆算する pattern を default に.

---

## 6. 残存タスク (Day21 以降)

### 6.1 Day7 §9.3 long-term task: ✅ 完全クローズ (7/7)

Day20 で最後の 1 件 (Stage 3) を認証 cleanup. Day7 §9.3 で定義された long-term task は全て完了.

### 6.2 Day19+ で生成された Day21+ 候補

- [ ] **v0.1.0 tag 付与** + GitHub Release 作成 (公開化記念、CHANGELOG `[Unreleased] - 2026-05-18` → `[0.1.0]`、~1h)
- [ ] **CONTRIBUTING.md / CODE_OF_CONDUCT.md / Issue PR template** (collaboration 受入準備、~2h)
- [ ] **Branch protection rule** 設定 (main 直接 push 禁止)
- [ ] **SSH 認証 cleanup** (Day18 D18 起源、SSH passphrase 設定見直し)
- [ ] **pre-commit hook gitleaks 自動実行** (Day19 起源、ops 強化)
- [ ] **predatory journal データベース連携** (Beall's list 等、B 細分化)
- [ ] **MCP server による batch processing** (将来高度な体験、Stage 3 を超えた拡張)

### 6.3 Day21+ 推奨着手順

1. **v0.1.0 tag + GitHub Release** (最低コスト、Day7-19 統合の公式 milestone、~1h)
2. **CONTRIBUTING.md / Issue PR template** (公開後の collaboration 受入準備、~2h)
3. **pre-commit hook gitleaks 自動実行** (将来の secret leak 防止、~1h)

---

## 7. 次セッション再開時のプロンプトテンプレート

### パターン 1: Day21 として v0.1.0 tag + GitHub Release (推奨)

```
Day21 として、Day19 で Public 切替済の pubmed-reference-resolver に
v0.1.0 tag を付与し、GitHub Release を作成します. CHANGELOG.md の
[Unreleased] - 2026-05-18 section を [0.1.0] に移行、git tag v0.1.0 +
push、gh release create で Release notes を生成. ~1h.
```

### パターン 2: Day21 として CONTRIBUTING.md / Issue PR template

```
Day21 として、Public 公開済の pubmed-reference-resolver に collaboration
受入準備として CONTRIBUTING.md と Issue/PR template を追加します.
brainstorming → SPEC → 実装で進めてください. ~2h.
```

### パターン 3: Day21 として pre-commit hook gitleaks 自動実行

```
Day21 として、pre-commit hook で gitleaks scan を自動実行する仕組みを
追加します. .pre-commit-config.yaml + Day18 で確立した .gitleaksignore
の継承. 開発者が secret leak を commit 前に検出できる ops 強化. ~1h.
```

---

**記録完了日**: 2026-05-21 (Day20)
**記録者**: Claude Code (Sonnet 4.6)
**ステータス**: Day20 archive 完成、Day7 §9.3 long-term task 完全クローズ、Day21 着手準備完了 (3 パターンプロンプトあり)
```

⚠️ `<hash>`, `<N>`, `<delta>`, `<NEW_*>` 等の placeholder は Phase 0-4 完了時の実値で置換.

- [ ] **Step 3: Phase 5 commit + push**

```bash
git add docs/sessions/day20/PLAN_three_class_book_web_refinement.md \
        docs/sessions/day20/README.md \
        docs/sessions/day20/DAY20_LESSONS_LEARNED.md && \
git commit -m "$(cat <<'EOF'
docs(sessions): archive day20 three-class refinement + Stage 3 cleanup session

Day20 セッション完了に伴う archive:
- README.md: day20/ index, Day7 §9.3 long-term task 完全クローズ (7/7),
  三分類 audit 品質改善の before/after 表
- DAY20_LESSONS_LEARNED.md: 全 commits 経緯 + 教訓 D20-1, D20-2
  (long-term task の達成判定基準を時代変化に合わせる + 実 fixture から
   逆算する品質改善 pattern)
- PLAN_three_class_book_web_refinement.md: writing-plans 出力の実装計画

主成果:
- three_class_classifier に 3 helper (_detect_book / _detect_conference
  / _classify_via_nlm_only) + 4 rule 順次評価
- main.py:synthesize_outputs で is_book/raw_text/publisher を unresolved_refs
  に追加
- cell_45refs 三分類: A=14 → <NEW_CELL_A> 大幅減 (Day17 D17 解消)
- apa_45refs 三分類: A=4 → <NEW_APA_A> 変動
- unit tests: 97 → 100 passed (+3 新 unit test)
- Day7 §9.3 long-term task 完全クローズ (Stage 3 認証で 7/7)

Day21+ 候補:
- v0.1.0 tag + GitHub Release (推奨)
- CONTRIBUTING.md / Issue PR template
- pre-commit hook gitleaks 自動実行

main branch: 83 → <N> (+<delta>), test: 97 passed → 100 passed
(+3) / 1 skipped.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)" && \
echo "---" && \
git push origin main 2>&1 | tail -3
```

---

## Verification (全 Task 完了後の最終確認)

- [ ] **V1: 全 test pass**

```bash
python3 -m pytest tests/ -v 2>&1 | tail -3
```
Expected: **100 passed, 1 skipped** (97 既存 + 3 新 unit test).

- [ ] **V2: SPEC §7 12 完了条件すべて満たす**

```bash
echo "[1] STAGE3_COMPLETION_NOTE:" && ls docs/sessions/day20/STAGE3_COMPLETION_NOTE.md
echo "[2] 3 helpers:" && grep -c "def _detect_book\|def _detect_conference\|def _classify_via_nlm_only" three_class_classifier.py
echo "[3] 4 rule eval:" && grep -c "Rule 1: is_book\|Rule 2: conference\|Rule 3: journal\|Rule 4:" three_class_classifier.py
echo "[4] 8 unit tests:" && python3 -m pytest tests/test_three_class_classifier.py --collect-only -q 2>&1 | tail -2
echo "[5-6] cell+apa baselines updated:" && jq 'length' tests/fixtures/cell_45refs/baseline_three_class_classification.json tests/fixtures/apa_45refs/baseline_three_class_classification.json
echo "[7] cell test 8 PASS:" && python3 -m pytest tests/test_integration_cell_45refs.py::test_baseline_three_class_classification_distribution -v 2>&1 | tail -2
echo "[8] apa test 8 PASS:" && python3 -m pytest tests/test_integration_apa_45refs.py::test_baseline_three_class_classification_distribution -v 2>&1 | tail -2
echo "[9] 100 passed total:" && python3 -m pytest tests/ 2>&1 | tail -1
echo "[10] gitleaks clean (継続):" && jq 'length' /tmp/gitleaks_report_day19.json 2>/dev/null || echo "(Day19 report 残存)"
echo "[11] Day20 archive 5 files:" && ls docs/sessions/day20/ | wc -l && ls docs/sessions/day20/
echo "[12] CI success after push:" && gh run list --limit 1 --json conclusion --jq '.[0].conclusion'
```

Expected: 全 12 条件 OK.

- [ ] **V3: commit count + push 同期確認**

```bash
echo "Day20 commits (after Day19 末 1f2ea82):" && git log 1f2ea82..HEAD --oneline | wc -l && \
echo "local HEAD:" && git rev-parse --short HEAD && \
echo "remote HEAD:" && git ls-remote origin main 2>/dev/null | awk '{print substr($1, 1, 7)}'
```

Expected: Day20 中の commit 数 ~9、local HEAD == remote HEAD.

- [ ] **V4: final git status**

```bash
git status
```
Expected: `nothing to commit, working tree clean` (.DS_Store も Day18 で gitignored 済).

---

## Notes for Implementing Agent

- **TDD 厳格**: Task 2 (test RED) → Task 3 (production GREEN) を統合 commit する. ただし step ごとに `pytest` 実行で RED → GREEN を確認すること.
- **Controller-direct vs subagent**: Day20 は production code 改修 + TDD + baseline 再生成が混在. Task 3 (production 改修) と Task 2 (test 追加) は subagent dispatch で TDD discipline を強化可能. Task 1/4/5/6/7 は controller 直接実行が効率的.
- **commit を生成する Phase 数**: Phase 0/1+2 (統合)/3/4a/4b/5 = 6 commits + 2 pre = 8 commits 想定. SPEC §6 では 9 commits だが Phase 1+2 統合により 8 になる可能性.
- **LLM cost**: Phase 4a + 4b で ~$2. 失敗時は `--reuse-phase2 --reuse-phase3` で部分再実行可能 (Phase 2/3 結果は本改修と無関係なので再利用安全).
- **`<NEW_*>` placeholder**: Phase 4a/4b の実測値で置換. README + test 8 + Day20 archive の README + LESSONS の 4 ファイルで一貫させる.
- **baseline_report.md の三分類 sub-section**: report.md には `## 2.X [3 分類化]` のような sub-section が含まれる. 再生成で自動更新されるため手動編集不要.
- **Stage 3 認証の重要性**: Phase 0 の STAGE3_COMPLETION_NOTE は Day7 §9.3 long-term task 完全クローズの evidence. archive で必ず参照されるため、内容を簡潔かつ完備に.
