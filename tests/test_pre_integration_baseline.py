"""
test_pre_integration_baseline.py — 統合前本体の挙動を保護する回帰テスト

目的:
    統合パッチ適用の前に、現状の main.py の挙動を pytest assertion として
    固定する。これにより:

    1. 現状のバグも含めた挙動が「既知の現状」として明示される
    2. 意図せず挙動が変わった場合に即座に検出できる
    3. 統合パッチ適用後にこのテストが FAIL したら、それは "期待通りの改善"
       を意味する → baseline 値を更新して新しい正常状態に移行

運用フロー:
    [ 統合前 ]
    pytest tests/test_pre_integration_baseline.py -v
    → 全 PASS (現状の挙動が確認された)

    [ integration/patches/01 適用後 ]
    pytest tests/test_pre_integration_baseline.py -v
    → test_phase1_currently_loses_2_refs が FAIL
       "期待 147 件 != 実際 149 件"
    → これは改善の証。test 側の expected を 149 に更新してコミット

前提:
    tests/fixtures/mdpi_149refs/ に以下のファイルが配置されている:
     - input_References.docx
     - expected_phase2_structured.json
     - expected_phase3_resolved.json
     - expected_report.md
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "mdpi_149refs"


@pytest.fixture(scope="module")
def main_module():
    """main.py を一度だけ import する。"""
    sys.path.insert(0, str(REPO_ROOT))
    import main
    return main


@pytest.fixture(scope="module")
def phase1_blocks(main_module):
    """149 ref docx を Phase 1 に通した結果のブロックリストを共有する。"""
    docx = FIXTURE_DIR / "input_References.docx"
    assert docx.exists(), f"テストデータが見つかりません: {docx}"
    raw, _ = main_module.extract_text(docx)
    ln_report = main_module.detect_line_numbers(raw)
    cleaned, _trace = main_module.preprocess(raw, ln_report)
    return main_module.split_references(cleaned)


# ============================================================================
# 基準値テスト (現状の挙動を固定)
# ============================================================================

# 統合前の期待値 (現状のバグ込み)
BASELINE_BLOCKS_DETECTED = 147   # 本来は 149 だが #40, #140 が欠落
BASELINE_MISSING_REFS = [40, 140]
BASELINE_OVERSIZED_REF = 39       # #39 に #40 が統合されて肥大化


class TestPhase1CurrentBehavior:
    """統合前本体の Phase 1 挙動を特徴付けるテスト。"""

    def test_phase1_runs_without_error(self, phase1_blocks):
        """Phase 1 はクラッシュせずに完走すること。"""
        assert phase1_blocks is not None
        assert isinstance(phase1_blocks, list)

    def test_phase1_detects_baseline_count(self, phase1_blocks):
        """
        現状の検出ブロック数を 147 として固定する。

        統合パッチ適用後はこのテストが FAIL する (= 改善)。
        FAIL を確認したら BASELINE_BLOCKS_DETECTED を 149 に更新すること。
        """
        assert len(phase1_blocks) == BASELINE_BLOCKS_DETECTED, (
            f"Phase 1 検出数 {len(phase1_blocks)} ≠ 既知の基準値 "
            f"{BASELINE_BLOCKS_DETECTED}。本体または Phase 1 の挙動が変化しました。"
            f" もしこれが統合パッチによる改善なら、expected を更新してください。"
        )

    def test_phase1_loses_known_refs(self, phase1_blocks):
        """Ref #40 および #140 が欠落することを確認 (既知のバグ)。"""
        ref_nos = sorted(b.ref_no for b in phase1_blocks)
        missing = [n for n in range(1, 150) if n not in ref_nos]
        assert missing == BASELINE_MISSING_REFS, (
            f"欠落 refs が基準値と異なります: {missing} vs {BASELINE_MISSING_REFS}。"
            f" 統合パッチ適用後の場合、missing=[] を期待値として更新してください。"
        )

    def test_phase1_oversized_block_contains_merged_ref(self, phase1_blocks):
        """Ref #39 が異常に大きく、本来の #40 を含んでいることを確認。"""
        block_39 = next((b for b in phase1_blocks if b.ref_no == 39), None)
        assert block_39 is not None, "Ref #39 が存在しないのは想定外"
        assert block_39.char_length > 400, (
            f"Ref #39 のサイズ {block_39.char_length} が想定より小さい。"
            f" 統合パッチによる改善の可能性"
        )
        assert "van der Biessen" in block_39.raw_text, (
            f"Ref #39 に #40 の著者 'van der Biessen' が含まれない。"
            f" この統合バグが既に解消されている可能性"
        )


# ============================================================================
# 入力データ自体の完全性テスト (golden 側の健全性保証)
# ============================================================================

class TestFixtureIntegrity:
    """tests/fixtures/mdpi_149refs/ の中身自体が破損していないことを確認。"""

    def test_input_docx_exists(self):
        docx = FIXTURE_DIR / "input_References.docx"
        assert docx.exists(), f"入力 .docx が見つかりません: {docx}"
        assert docx.stat().st_size > 30_000, "入力サイズが異常に小さい"

    def test_expected_phase2_exists_and_has_149_refs(self):
        import json
        path = FIXTURE_DIR / "expected_phase2_structured.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        structured = data.get("stage3_structured", data)
        assert len(structured) == 149, (
            f"ゴールド phase2 が 149 件でない: {len(structured)}"
        )

    def test_expected_phase3_exists(self):
        path = FIXTURE_DIR / "expected_phase3_resolved.json"
        assert path.exists()

    def test_expected_report_exists(self):
        path = FIXTURE_DIR / "expected_report.md"
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "ダッシュボード" in content
        assert "149" in content  # 総参照数


# ============================================================================
# スナップショット的な特徴付けテスト (Optional, 詳細な挙動固定用)
# ============================================================================

class TestPhase1DetailedSnapshot:
    """Phase 1 の細部の挙動を固定する (統合後に 1 件ずつ見直す用)。"""

    def test_ref1_is_bray_globocan(self, phase1_blocks):
        b = next((b for b in phase1_blocks if b.ref_no == 1), None)
        assert b is not None
        assert b.raw_text.startswith("Bray, F.")
        assert "Global cancer statistics" in b.raw_text

    def test_ref149_is_de_boeck(self, phase1_blocks):
        b = next((b for b in phase1_blocks if b.ref_no == 149), None)
        assert b is not None
        assert "De Boeck" in b.raw_text or "Boeck" in b.raw_text

    def test_line_numbers_removed(self, main_module):
        """"567-910 の行番号が正しく除去されていること。"""
        docx = FIXTURE_DIR / "input_References.docx"
        raw, _ = main_module.extract_text(docx)
        ln_report = main_module.detect_line_numbers(raw)
        assert ln_report.detected, "行番号が検出されていない"
        assert ln_report.min_val == 567
        assert ln_report.max_val == 910
