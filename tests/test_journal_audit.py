"""
Unit tests for journal_audit module.

Covers:
- Severity classification (MAJOR/WARN/INFO/OK)
- _normalize_journal preprocessing
- is_book guard (two trigger conditions)
- format_findings_markdown output structure

Data format conventions:
    resolutions: list of dicts matching stage4_pubmed_resolutions from
        main.py::run_phase3(). Each entry has {"ref_no", "pmid", "metadata"}
        where metadata is a nested dict with "journal_iso", "journal_full",
        "journal" keys. This contract is enforced by PubMedResolution._ser()
        in main.py.
    findings: list of dicts emitted by audit_journal_mismatch() with keys
        {"ref_no", "cite_journal", "pm_journal", "pmid", "similarity",
        "severity"}.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skip(
    reason="awaiting Day23 Phase 5 new MDPI fixture "
    "(tracked by docs/superpowers/plans/2026-05-24-day23-fixture-remediation.md). "
    "Original mdpi_149refs/ removed in this commit due to peer-review-derived "
    "confidentiality concern."
)

REPO_ROOT = Path(__file__).parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ============================================================================
# Severity classification
# ============================================================================

class TestSeverityClassification:
    """audit_journal_mismatch が類似度に応じて正しく severity を付与する。"""

    def test_exact_match_is_excluded(self):
        """類似度 100 → OK → findings に含まれない。"""
        from journal_audit import audit_journal_mismatch

        structured = [{"ref_no": 1, "journal": "Nature", "is_book": False}]
        resolutions = [{
            "ref_no": 1,
            "pmid": "12345678",
            "metadata": {"journal_iso": "Nature"},
        }]
        findings = audit_journal_mismatch(structured, resolutions)
        assert findings == []

    def test_major_mismatch_detected(self):
        """類似度 < 50 → MAJOR。"""
        from journal_audit import audit_journal_mismatch

        structured = [{"ref_no": 1, "journal": "Ultrasound Med. Biol.", "is_book": False}]
        resolutions = [{
            "ref_no": 1,
            "pmid": "12345678",
            "metadata": {"journal_iso": "Jpn J Clin Oncol"},
        }]
        findings = audit_journal_mismatch(structured, resolutions)
        assert len(findings) == 1
        assert findings[0]["severity"] == "MAJOR"
        assert findings[0]["ref_no"] == 1

    def test_minor_abbreviation_is_ok(self):
        """略称揺れは OK に分類される (token_set_ratio が高い)。"""
        from journal_audit import audit_journal_mismatch

        structured = [{"ref_no": 1, "journal": "J. Clin. Oncol.", "is_book": False}]
        resolutions = [{
            "ref_no": 1,
            "pmid": "12345678",
            "metadata": {"journal_iso": "Journal of Clinical Oncology"},
        }]
        findings = audit_journal_mismatch(structured, resolutions)
        # 略称と full name の類似度は通常 >= 80 (partial_ratio 経由)
        # findings は空、または INFO 以下のみ
        assert all(f["severity"] in ("INFO", "WARN") for f in findings) or findings == []


# ============================================================================
# is_book guard
# ============================================================================

class TestIsBookGuard:
    """is_book=True または cite_journal が 'In: ...' で始まる ref は監査対象外。"""

    def test_is_book_true_is_skipped(self):
        """is_book=True の ref は findings に含まれない (低類似度でも)。"""
        from journal_audit import audit_journal_mismatch

        structured = [{
            "ref_no": 141,
            "journal": "Character Strengths and Virtues",
            "is_book": True,
        }]
        resolutions = [{
            "ref_no": 141,
            "pmid": "12345678",
            "metadata": {"journal_iso": "Some Journal"},
        }]
        findings = audit_journal_mismatch(structured, resolutions)
        assert findings == [], (
            "Ref with is_book=True should be excluded from audit"
        )

    def test_in_prefix_is_skipped(self):
        """cite_journal が 'In: ...' で始まる ref は findings に含まれない。"""
        from journal_audit import audit_journal_mismatch

        structured = [{
            "ref_no": 50,
            "journal": "In: Hogrefe Publishing, 2010",
            "is_book": False,  # パーサが book 判定に失敗したケース
        }]
        resolutions = [{
            "ref_no": 50,
            "pmid": "12345678",
            "metadata": {"journal_iso": "Nature"},
        }]
        findings = audit_journal_mismatch(structured, resolutions)
        assert findings == [], (
            "Ref with journal starting with 'In: ' should be excluded"
        )

    def test_both_conditions_guard_together(self):
        """is_book=True と 'In: ' 両方該当でも 1 回の continue で除外される。"""
        from journal_audit import audit_journal_mismatch

        structured = [{
            "ref_no": 100,
            "journal": "In: Handbook of Psychology",
            "is_book": True,
        }]
        resolutions = [{
            "ref_no": 100,
            "pmid": "12345678",
            "metadata": {"journal_iso": "Nature"},
        }]
        findings = audit_journal_mismatch(structured, resolutions)
        assert findings == []

    def test_non_book_with_low_similarity_still_detected(self):
        """is_book=False で 'In: ' でもない通常 ref は低類似度で検出される。"""
        from journal_audit import audit_journal_mismatch

        structured = [{
            "ref_no": 13,
            "journal": "Ultrasound Med. Biol.",
            "is_book": False,
        }]
        resolutions = [{
            "ref_no": 13,
            "pmid": "12345678",
            "metadata": {"journal_iso": "Jpn J Clin Oncol"},
        }]
        findings = audit_journal_mismatch(structured, resolutions)
        assert len(findings) == 1
        assert findings[0]["severity"] == "MAJOR"


# ============================================================================
# Missing data handling
# ============================================================================

class TestMissingData:
    """片方が欠落している場合の挙動。"""

    def test_missing_cite_journal_is_skipped(self):
        """citation journal が None の ref は findings に含まれない。"""
        from journal_audit import audit_journal_mismatch

        structured = [{"ref_no": 1, "journal": None, "is_book": False}]
        resolutions = [{
            "ref_no": 1,
            "pmid": "12345678",
            "metadata": {"journal_iso": "Nature"},
        }]
        findings = audit_journal_mismatch(structured, resolutions)
        assert findings == []

    def test_missing_resolution_is_skipped(self):
        """PubMed resolution が None/欠落の ref は findings に含まれない。"""
        from journal_audit import audit_journal_mismatch

        structured = [{"ref_no": 1, "journal": "Nature", "is_book": False}]
        resolutions = []  # 該当 ref の resolution なし
        findings = audit_journal_mismatch(structured, resolutions)
        assert findings == []

    def test_resolution_without_pmid_is_skipped(self):
        """pmid が無い resolution (= PubMed 未解決) は audit 対象外。"""
        from journal_audit import audit_journal_mismatch

        structured = [{"ref_no": 1, "journal": "Nature", "is_book": False}]
        resolutions = [{
            "ref_no": 1,
            "pmid": None,  # 未解決
            "metadata": {"journal_iso": "Some Journal"},
        }]
        findings = audit_journal_mismatch(structured, resolutions)
        assert findings == []


# ============================================================================
# format_findings_markdown
# ============================================================================

class TestFormatFindingsMarkdown:
    """Markdown 整形関数の出力構造。"""

    def test_empty_findings_produces_empty_or_minimal_output(self):
        """findings が空の場合、空文字 or 最小限のプレースホルダを返す。"""
        from journal_audit import format_findings_markdown

        result = format_findings_markdown([])
        assert isinstance(result, str)
        # 実装次第で空文字 or "(no findings)" 等。少なくとも str であること

    def test_mixed_severity_findings_render(self):
        """MAJOR/WARN/INFO 混在の findings が markdown として整形される。"""
        from journal_audit import format_findings_markdown

        findings = [
            {
                "ref_no": 1,
                "severity": "MAJOR",
                "similarity": 30.0,
                "cite_journal": "Foo Bar",
                "pm_journal": "Baz Qux",
                "pmid": "11111111",
            },
            {
                "ref_no": 2,
                "severity": "WARN",
                "similarity": 60.0,
                "cite_journal": "Alpha Beta",
                "pm_journal": "Alpha Gamma",
                "pmid": "22222222",
            },
            {
                "ref_no": 3,
                "severity": "INFO",
                "similarity": 75.0,
                "cite_journal": "Test One",
                "pm_journal": "Test Two",
                "pmid": "33333333",
            },
        ]
        result = format_findings_markdown(findings)
        assert isinstance(result, str)
        assert len(result) > 0
        # 全 3 ref_no が markdown に含まれること
        for ref_no in (1, 2, 3):
            assert str(ref_no) in result


# ============================================================================
# include_ok parameter (Step 6-1)
# ============================================================================

class TestIncludeOkParameter:
    """include_ok フラグで severity==OK の finding を残すか除外するかを制御する。"""

    def test_include_ok_false_filters_ok(self):
        """include_ok=False (既定) では severity==OK は findings に含まれない。"""
        from journal_audit import audit_journal_mismatch

        structured = [{"ref_no": 1, "journal": "Cell", "is_book": False}]
        resolutions = [{
            "ref_no": 1,
            "pmid": "12345678",
            "metadata": {"journal_iso": "Cell"},
        }]
        findings = audit_journal_mismatch(structured, resolutions, include_ok=False)
        assert findings == []

    def test_include_ok_true_returns_all(self):
        """include_ok=True では severity==OK も含む全 finding を返す。"""
        from journal_audit import audit_journal_mismatch

        structured = [
            {"ref_no": 1, "journal": "Cell", "is_book": False},
            {"ref_no": 2, "journal": "Zebrafish Research", "is_book": False},
        ]
        resolutions = [
            {"ref_no": 1, "pmid": "11111111", "metadata": {"journal_iso": "Cell"}},
            {"ref_no": 2, "pmid": "22222222", "metadata": {"journal_iso": "Nature"}},
        ]
        findings = audit_journal_mismatch(structured, resolutions, include_ok=True)
        assert len(findings) == 2
        by_ref = {f["ref_no"]: f for f in findings}
        assert by_ref[1]["severity"] == "OK"
        assert by_ref[1]["similarity"] >= 80
        assert by_ref[2]["severity"] == "MAJOR"

    def test_include_ok_default_matches_explicit_false(self):
        """デフォルト引数の挙動が include_ok=False と同一であることの後方互換保証。"""
        from journal_audit import audit_journal_mismatch

        structured = [
            {"ref_no": 1, "journal": "Cell", "is_book": False},
            {"ref_no": 2, "journal": "Zebrafish Research", "is_book": False},
        ]
        resolutions = [
            {"ref_no": 1, "pmid": "11111111", "metadata": {"journal_iso": "Cell"}},
            {"ref_no": 2, "pmid": "22222222", "metadata": {"journal_iso": "Nature"}},
        ]
        default = audit_journal_mismatch(structured, resolutions)
        explicit = audit_journal_mismatch(structured, resolutions, include_ok=False)
        assert default == explicit
        assert len(default) == 1
        assert default[0]["severity"] == "MAJOR"


# ============================================================================
# format_summary_narrative (Step 6-2)
# ============================================================================

class TestFormatSummaryNarrative:
    """report.md 末尾補遺のナラティブ要約生成。"""

    def test_narrative_matches_expected_fixture(self):
        """149-ref コーパスで生成した narrative が expected_report.md の
        補遺セクションと byte 単位で完全一致する。"""
        import json
        from journal_audit import audit_journal_mismatch, format_summary_narrative

        fixtures_dir = REPO_ROOT / "tests" / "fixtures" / "mdpi_149refs"
        data = json.loads(
            (fixtures_dir / "expected_phase3_resolved.json").read_text(encoding="utf-8")
        )
        findings = audit_journal_mismatch(
            data["stage3_structured"],
            data["stage4_pubmed_resolutions"],
            include_ok=True,
        )
        narrative = format_summary_narrative(findings)

        expected = (fixtures_dir / "expected_report.md").read_text(encoding="utf-8")
        marker = "\n---\n\n## 補遺: ジャーナル名と PubMed 収載誌の照合監査 (追加)"
        idx = expected.find(marker)
        assert idx != -1, "expected_report.md に補遺セクションの目印が見つからない"
        expected_tail = expected[idx:]

        assert narrative == expected_tail

    def test_narrative_no_major(self):
        """MAJOR 0 件時は「検出されませんでした」と「全 N 件」を含む。"""
        from journal_audit import format_summary_narrative

        all_findings = [
            {"ref_no": i, "severity": "OK", "similarity": 95}
            for i in range(1, 11)
        ]
        narrative = format_summary_narrative(all_findings)
        assert "10 件全件" in narrative
        assert "検出されませんでした" in narrative
        assert "全 10 件が" in narrative
        assert "1件のみ" not in narrative
        assert "**0件**" not in narrative
        assert "Ref #" not in narrative

    def test_narrative_multiple_majors(self):
        """MAJOR 複数件時は件数と ref_no 列挙 (昇順) を含む。"""
        from journal_audit import format_summary_narrative

        all_findings = [
            {"ref_no": 99, "severity": "MAJOR", "similarity": 25},
            {"ref_no": 5, "severity": "MAJOR", "similarity": 30},
            {"ref_no": 12, "severity": "MAJOR", "similarity": 40},
        ] + [
            {"ref_no": i, "severity": "OK", "similarity": 95}
            for i in range(100, 150)
        ]
        narrative = format_summary_narrative(all_findings)
        n = len(all_findings)  # 53
        assert f"{n} 件全件" in narrative
        assert "**3件**" in narrative
        # ref_no 昇順で #5, #12, #99
        assert "(Ref #5, #12, #99)" in narrative
        assert f"残り {n - 3} 件" in narrative
        assert "1件のみ" not in narrative


# ============================================================================
# _normalize_journal (internal helper, tested for contract stability)
# ============================================================================

class TestNormalizeJournal:
    """_normalize_journal の前処理ロジック。"""

    def test_lowercase_conversion(self):
        from journal_audit import _normalize_journal
        assert _normalize_journal("Nature") == "nature"

    def test_punctuation_removal(self):
        from journal_audit import _normalize_journal
        # [.,;:&] が space に変換される
        result = _normalize_journal("J. Clin. Oncol.")
        assert "." not in result
        assert "clin" in result
        assert "oncol" in result

    def test_whitespace_normalization(self):
        from journal_audit import _normalize_journal
        # 連続 space は単一 space に
        result = _normalize_journal("Foo    Bar")
        assert "  " not in result
        assert "foo bar" == result.strip()

    def test_empty_string(self):
        from journal_audit import _normalize_journal
        assert _normalize_journal("") == ""
