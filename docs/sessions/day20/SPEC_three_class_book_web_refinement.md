# SPEC: 三分類 audit の book/proceedings/DOI 欠落 case 改修 + Stage 3 認証 (Day20)

**作成日**: 2026/05/21 (Day20 brainstorming 完了時)
**著者**: Claude Code (Sonnet 4.6) / 承認: 片山英樹
**位置付け**: Day17 D17 教訓 (cell_45refs で A 多発 14/15) 起源の **品質改善** + Day7 §9.3 残最後 1 件 (Stage 3 配線) の **認証 cleanup**
**前提**: Day19 末 (commit `1f2ea82`) で main branch 83 commits、4 fixture、97 tests passed、GitHub PUBLIC 化済、Day15 三分類 audit logic は `three_class_classifier.py` で稼働中

---

## 1. 背景と目的

### 1.1 Day7 §9.3 残最後 1 件 (Stage 3) の再定義

Day7 PHASE_0_VERIFICATION_REPORT §1.1 で「Stage 3 = Claude UI 経由でのスキル起動配線 (MCP/hook 配線、Day8 以降)」と定義され Day8-19 で「未着手」として繰越されていたが、Day20 brainstorming Q0 で **既に Claude Code skill 機能経由で達成済**であることをユーザー (片山英樹) が確認.

→ Day20 では Stage 3 を「達成認証 cleanup」として処理 (詳細は §6 + `STAGE3_COMPLETION_NOTE.md`).

### 1.2 メインタスク: 三分類 audit の品質改善 (Day17 D17 起源)

Day17 cell_45refs (commit `9527fc0`) で計測された三分類分布は **A=14, B=0, C=0, unknown=1** で、A 多発の false positive 問題が DAY17_LESSONS_LEARNED.md D17 で記録されていた. Day20 brainstorming で全 A=14 件の内訳を分析:

| パターン | 件数 | refs | 改修方針 |
|:---|:---:|:---|:---|
| `is_book=True` (book chapter) | 3 | #31, #32, #37 | → **B 確実** (book は本質的 MEDLINE 非収録) |
| Conference proceedings (journal 名に "Conference" 含む) | 3 | #34, #42, #43 | → **B 確実** (proceedings は MEDLINE 非収録) |
| DOI なし + journal 名あり | 7 | #33, #36, #38, #40, #41, #44, #45 | → NLM Catalog 検索で **B/C 判定可能** |
| Title truncated, journal 空 | 1 | #17 | → A 継続 (真の判定不可) |

**原因**: `three_class_classifier.py:_classify_single` (line 97-105) が「DOI 欠落 → 即 A」と判定しているため、book/proceedings/DOI 無 journal といった正当な MEDLINE 非収録 ref も「LLM ハルシネーション候補」と誤分類. 実 ref の多くは正規論文/書籍であり、false positive.

### 1.3 目的

1. **三分類 audit の精度向上**: cell_45refs A=14 → A=1+ (改修後想定)、book/proceedings/DOI 無 journal を B (or C) に正しく分類
2. **apa_45refs にも同改修の影響を伝播**: 同 fixture の baseline 三分類分布 (A=4, B=0, C=0, unknown=16) も連動更新
3. **Stage 3 達成認証**: Day7 §9.3 long-term task 7 件中、最後の 1 件 (MCP/hook 配線) を skill 機能経由達成として認証
4. **Day7 §9.3 long-term task の完全クローズ**: 7/7 達成、Day21+ は新規 task 群 (v0.1.0 tag / CONTRIBUTING.md 等)

### 1.4 設計判断の経緯 (brainstorming 質問)

| # | 質問 | 確定 |
|:---:|:---|:---|
| Q0 | Stage 3 の現状達成度 | **(A) SKILL.md 経由で Claude UI から起動済** → 達成認証 cleanup |
| Q1 | Day20 メインタスク | **(B1) AI 工学 book/web refs 三分類改修** |
| Q2 | 改修 scope | **全 7-13 件 cover (book + proceedings + DOI 無 journal)** |
| Q3 | Test 戦略 | **(完全) cell + apa 両方 baseline 再生成 + integration test 拡張** |

---

## 2. Architecture & ファイル配置

### 改変対象 (3 ファイル + baseline 2 件再生成)

| ファイル | 種別 | 修正内容 |
|:---|:---|:---|
| `three_class_classifier.py` | 修正 | `_classify_single` 拡張. 3 新 helper (`_detect_book`, `_detect_conference`, `_classify_via_nlm_only`) 抽出. DOI 欠落 case を A 即断ではなく 4 rule 順次評価に変更. |
| `tests/test_three_class_classifier.py` | 修正 | 3 新 unit test 追加 (book / conference / nlm-only). 既存 5 tests のうち 1 件 (test_classify_returns_A_when_doi_missing) の assertion 文言調整. |
| `main.py:synthesize_outputs` | 微改修 (要確認) | `unresolved_refs` に `is_book` flag を含める (現状確認後、不足なら追加) |

### Baseline 再生成 (4 ファイル)

| ファイル | 種別 | 再生成理由 |
|:---|:---|:---|
| `tests/fixtures/cell_45refs/baseline_three_class_classification.json` | **再生成** | A=14 → 改修後分布 (A=1+, B=多, C=可能性, unknown=1-5) |
| `tests/fixtures/cell_45refs/baseline_report.md` | **再生成** | 報告書の三分類 sub-section も連動更新 |
| `tests/fixtures/cell_45refs/README.md` | 更新 | 三分類実測値の section を改修後値に更新 |
| `tests/fixtures/apa_45refs/baseline_three_class_classification.json` | **再生成** | 同改修の影響を受けるため (A=4, unknown=16 → 変動) |
| `tests/fixtures/apa_45refs/baseline_report.md` | **再生成** | 同上 |
| `tests/fixtures/apa_45refs/README.md` | 更新 | 同上 |
| `tests/test_integration_cell_45refs.py` | 修正 | `EXPECTED_THREE_CLASS_DISTRIBUTION` (test 8) を改修後実測値に更新 |
| `tests/test_integration_apa_45refs.py` | 修正 | 同上 |

注: Phase 3 (LLM + PubMed 解決) は不変なので `baseline_phase3_resolved.json` は **再 copy 不要** (Phase 4 のみ再実行で OK).

### 新規作成 (Day20 archive 5 files)

| ファイル | 用途 |
|:---|:---|
| `docs/sessions/day20/SPEC_three_class_book_web_refinement.md` | 本 SPEC |
| `docs/sessions/day20/PLAN_three_class_book_web_refinement.md` | writing-plans 出力 |
| `docs/sessions/day20/STAGE3_COMPLETION_NOTE.md` | Stage 3 達成認証 (Day7 §9.3 long-term task の clean up evidence) |
| `docs/sessions/day20/README.md` | Day20 index |
| `docs/sessions/day20/DAY20_LESSONS_LEARNED.md` | Day20 archive |

### 改変なし (確認のみ)

- `crossref_check.py` (DOI 検索 logic 不変)
- `nlm_catalog_check.py` (journal name 検索 logic 不変、追加呼出が増えるのみ)
- `mdpi_parser.py` / `journal_audit.py` (本 task と無関係)
- 既存 fixture (mdpi_149refs / vancouver_24refs) (本 task と無関係)

### 外部システム変更

- LLM cost: cell + apa fixture 再生成で **~$1 × 2 = ~$2** (Phase 4 のみで Phase 2/3 結果再利用なら半減可能性、要 main.py の `--reuse-phase2 --reuse-phase3` 動作確認)
- Crossref / NLM API call: 既存より多くの NLM call が発生 (DOI 無 journal あり case)、ただし graceful fail-soft 設計

---

## 3. 検出ルール詳細

### 3.1 `_detect_book(ref)` ヘルパー

**Input**: ref dict (with `is_book` flag from Phase 2 LLM output)
**Output**: `bool` (True = book と判定)

**判定 logic**:
```python
def _detect_book(ref: dict) -> bool:
    if ref.get("is_book") is True:
        return True
    # フォールバック: ref text に明示的な book signal
    raw = (ref.get("raw_text") or "").lower()
    if "isbn" in raw:
        return True
    if "publisher" in raw and ref.get("publisher"):
        return True
    return False
```

**該当 refs (cell_45refs 実測)**: #31, #32, #37

### 3.2 `_detect_conference(journal)` ヘルパー

**Input**: journal name (str | None)
**Output**: `bool` (True = conference/proceedings と判定)

**判定 logic**:
```python
import re

_CONFERENCE_PATTERNS = re.compile(
    r"\b(?:conference|conf\.|proceedings|proc\.|workshop|symposium|"
    r"symp\.|congress|meeting)\b",
    re.IGNORECASE,
)

def _detect_conference(journal: str | None) -> bool:
    if not journal:
        return False
    return bool(_CONFERENCE_PATTERNS.search(journal))
```

**該当 refs (cell_45refs 実測)**:
- #34: "International Conference on Trends in El..."
- #42: "International Conference on Advancements..."
- #43: "2022 12th International Conference on El..."

注: `\b` 単語境界で安全 (例: "Annals" の "ann" は誤検出しない).

### 3.3 `_classify_via_nlm_only(ref_no, journal, nlm_fn)` ヘルパー

**Input**: ref_no (int), journal name (str), nlm_fn (DI)
**Output**: classification dict (B/C/unknown)

**Use case**: DOI 欠落だが journal 名は判明 → Crossref をスキップして NLM Catalog 直接検索.

**判定 logic**:
```python
def _classify_via_nlm_only(ref_no, journal, nlm_fn):
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
        return {**base, "class": "B",
                "reason": f"DOI 欠落だが journal '{journal}' は MEDLINE 非収録 (NLM 直接検索)"}
    if status == "Y":
        return {**base, "class": "C",
                "reason": f"DOI 欠落、journal '{journal}' は MEDLINE 収録だが本論文単体は indexing なし"}
    return {**base, "class": "unknown",
            "reason": f"DOI 欠落 + NLM 検索でも判定不可: {nlm.get('error')}"}
```

**該当 refs (cell_45refs 実測)**: #33, #36, #38, #40, #41, #44, #45

### 3.4 改修後 `_classify_single` の評価順序

```python
def _classify_single(ref, crossref_fn, nlm_fn):
    ref_no = ref.get("ref_no")
    doi = ref.get("doi")
    journal = ref.get("journal")

    if not doi or not str(doi).startswith("10."):
        # DOI 欠落 case → 4 rule 順次評価:

        # Rule 1: is_book → B
        if _detect_book(ref):
            return {"ref_no": ref_no, "class": "B",
                    "reason": "book chapter (DOI 欠落だが MEDLINE 対象外)",
                    "doi_resolved": None, "journal_indexing": None,
                    "details": {"doi": None, "journal": journal,
                                "is_book": True}}

        # Rule 2: conference proceedings → B
        if _detect_conference(journal):
            return {"ref_no": ref_no, "class": "B",
                    "reason": f"conference/proceedings '{journal}' (MEDLINE 非収録)",
                    "doi_resolved": None, "journal_indexing": None,
                    "details": {"doi": None, "journal": journal,
                                "conference": True}}

        # Rule 3: journal 名あり → NLM 直接検索
        if journal:
            return _classify_via_nlm_only(ref_no, journal, nlm_fn)

        # Rule 4: 全て該当せず → A (真の判定不可、ハルシネーション候補)
        return {"ref_no": ref_no, "class": "A",
                "reason": "DOI 欠落 + journal 不明 (真の判定不可、ハルシネーション候補)",
                "doi_resolved": None, "journal_indexing": None,
                "details": {"doi": doi, "journal": journal}}

    # DOI あり case は既存 logic 維持 (Crossref → NLM)
    cr = crossref_fn(doi)
    # ... (既存処理続く、line 108- は不変)
```

### 3.5 #17 (title truncated, journal 空) の扱い

raw_text truncated で title も journal も判明せず. Rule 1-3 全 fail. Rule 4 で A 判定継続. reason は「DOI 欠落 + journal 不明」となり、現状の「LLM ハルシネーション候補」より正確.

---

## 4. Test 戦略詳細

### 4.1 Unit test 追加 (tests/test_three_class_classifier.py 拡張)

既存 5 tests に **3 新 unit test** を追加 (DI stub で deterministic):

#### Test 6: `test_classify_returns_B_when_is_book_true`

```python
def test_classify_returns_B_when_is_book_true():
    """is_book=True ref は DOI 欠落でも B 分類される (book は MEDLINE 対象外)."""
    refs = [{"ref_no": 31, "doi": None, "journal": "", "is_book": True}]

    def fake_crossref(doi):
        raise AssertionError("Crossref should not be called for book")
    def fake_nlm(**kwargs):
        raise AssertionError("NLM should not be called for book")

    result = classify_unresolved_refs(refs, crossref_fn=fake_crossref, nlm_fn=fake_nlm)
    assert result[0]["class"] == "B"
    assert "book" in result[0]["reason"].lower()
```

#### Test 7: `test_classify_returns_B_when_conference_proceedings`

```python
def test_classify_returns_B_when_conference_proceedings():
    """journal 名に 'Conference' / 'Proceedings' / 'Workshop' 等を含む ref は B 分類."""
    refs = [
        {"ref_no": 34, "doi": None,
         "journal": "International Conference on Trends in Electronics",
         "is_book": False},
        {"ref_no": 42, "doi": None,
         "journal": "Proceedings of the IEEE Workshop on ML",
         "is_book": False},
    ]

    def fake_crossref(doi):
        raise AssertionError("Crossref should not be called")
    def fake_nlm(**kwargs):
        raise AssertionError("NLM should not be called")

    result = classify_unresolved_refs(refs, crossref_fn=fake_crossref, nlm_fn=fake_nlm)
    assert all(r["class"] == "B" for r in result)
    reasons = [r["reason"].lower() for r in result]
    assert any("conference" in r or "proceedings" in r for r in reasons)
```

#### Test 8: `test_classify_calls_nlm_when_doi_missing_with_journal`

```python
def test_classify_calls_nlm_when_doi_missing_with_journal():
    """DOI 欠落 + journal 名あり + 非 book + 非 conference → NLM 直接検索."""
    refs = [
        {"ref_no": 33, "doi": None, "journal": "Eng", "is_book": False},
        {"ref_no": 38, "doi": None, "journal": "Journal of Engineered Fibers", "is_book": False},
    ]

    nlm_calls = []
    def fake_crossref(doi):
        raise AssertionError("Crossref should not be called")
    def fake_nlm(**kwargs):
        nlm_calls.append(kwargs)
        if "Engineered" in kwargs.get("journal_name", ""):
            return {"status": "Y", "nlm_id": "12345", "medlineta": "JEF"}
        return {"status": "N", "nlm_id": None, "medlineta": None}

    result = classify_unresolved_refs(refs, crossref_fn=fake_crossref, nlm_fn=fake_nlm)
    assert len(nlm_calls) == 2
    assert result[0]["class"] == "B"  # 'Eng' → N
    assert result[1]["class"] == "C"  # 'Engineered Fibers' → Y
```

#### 既存 5 tests の維持

| # | test 名 | 改修後 status |
|:---:|:---|:---:|
| 1 | `test_classify_returns_A_when_doi_missing` | **改修要** (DOI 欠落 + journal 不明 case の reason 文言更新) |
| 2 | `test_classify_returns_A_when_crossref_404` | 不変 (Crossref 404 case) |
| 3 | `test_classify_returns_B_when_nlm_status_N` | 不変 |
| 4 | `test_classify_returns_C_when_nlm_status_Y` | 不変 |
| 5 | `test_classify_returns_unknown_on_network_error` | 不変 |

→ test 1 は「journal も is_book も無い純粋な DOI 欠落のみ A」になるよう assertion 調整、その他 4 件は不変. 合計 5 (既存) + 3 (新) = **8 unit tests** ※元 test 1 修正で count 変動なし.

### 4.2 cell_45refs + apa_45refs baseline 再生成

#### 実行手順

```bash
# cell_45refs 再生成
python3 main.py tests/fixtures/cell_45refs/input_References.docx \
  --output-dir /tmp/cell_45refs_day20_rerun --phase 4
cp /tmp/cell_45refs_day20_rerun/report.md tests/fixtures/cell_45refs/baseline_report.md
cp /tmp/cell_45refs_day20_rerun/three_class_classification.json \
   tests/fixtures/cell_45refs/baseline_three_class_classification.json

# apa_45refs 再生成
python3 main.py tests/fixtures/apa_45refs/input_References.docx \
  --output-dir /tmp/apa_45refs_day20_rerun --phase 4
cp /tmp/apa_45refs_day20_rerun/report.md tests/fixtures/apa_45refs/baseline_report.md
cp /tmp/apa_45refs_day20_rerun/three_class_classification.json \
   tests/fixtures/apa_45refs/baseline_three_class_classification.json
```

⚠️ `synthesize_outputs` が呼ぶ `classify_unresolved_refs` への入力に `is_book` を含める **main.py 微改修**が前提 (現状 unresolved_refs に `is_book` が含まれるか要確認、不足なら Phase 3 で追加).

#### 期待される baseline 分布

| Fixture | Day19 baseline | Day20 改修後 (見込) |
|:---|:---|:---|
| cell_45refs | A=14, B=0, C=0, unknown=1 | A=1, B=6+, C=0-3, unknown=1-5 (NLM 応答次第) |
| apa_45refs | A=4, B=0, C=0, unknown=16 | A=変動, B=変動, C=変動, unknown=変動 |

実測値は再生成後に確定 → README + test 8 期待値を更新.

### 4.3 Integration test 期待値更新

#### tests/test_integration_cell_45refs.py test 8

```python
EXPECTED_THREE_CLASS_DISTRIBUTION = {
    "A": <new_A>,
    "B": <new_B>,
    "C": <new_C>,
    "unknown": <new_unknown>,
}  # Day20 改修後実測 (README 参照)
```

`<new_*>` は Phase 4a 再実行後の baseline_three_class_classification.json から計測.

#### tests/test_integration_apa_45refs.py test 8

同様に更新.

### 4.4 Test 健全性推移想定

| 段階 | passed | 説明 |
|:---:|---:|:---|
| Day19 末 | 97 | (baseline) |
| Day20 Phase 2 (unit test 追加後) | 100 | +3 新 unit test |
| Day20 Phase 4a-4b (baseline 再生成後) | 100 | (regression なし、test 8 期待値更新で pass 継続) |

---

## 5. Stage 3 達成認証 (Day7 §9.3 clean up)

### 5.1 認証 evidence の作成

`docs/sessions/day20/STAGE3_COMPLETION_NOTE.md` (新規) に以下を記録:

- Day7 当時の Stage 3 定義 (MCP/hook 配線想定)
- Day20 時点の達成度 (Claude Code skill 機能で達成済)
- ユーザー Q0 での確認結果
- Day7 §9.3 long-term task table の更新方針 (Day20 認証として処理、過去 LESSONS は履歴尊重で改修なし)

### 5.2 Day7 §9.3 long-term task table の更新

各 Day8-19 LESSONS.md に記載されていた以下の行を、Day20 archive 以降は「達成 (Day20 認証、Stage 3 = skill 機能で動作確認)」とみなす:

- 旧: `MCP/hook 経由 Stage 3 配線 | ⏳ 未着手`
- 新: `MCP/hook 経由 Stage 3 配線 | ✅ Day20 認証 (skill 機能で達成)`

過去 LESSONS.md の追記改修はしない (履歴尊重). Day20 README + LESSONS で本 note への明示参照を持つ.

---

## 6. Commit 計画 (7 commits + 2 pre = 9)

| 順 | commit 種別 | Phase | 内容 |
|:---:|:---|:---:|:---|
| (前) | `docs(spec)` | — | Day20 SPEC archive (本 commit) |
| (前) | `docs(plan)` | — | Day20 PLAN archive |
| 1 | `docs(sessions)` | 0 | STAGE3_COMPLETION_NOTE.md 作成 (達成認証) |
| 2 | `feat(three-class)` | 1 | three_class_classifier.py 改修 (3 helper + 評価順序変更) |
| 3 | `test(three-class)` | 2 | tests/test_three_class_classifier.py に 3 新 unit test + 1 修正 |
| 4 | `chore(synthesize)` | 3 | main.py:synthesize_outputs で `is_book` を unresolved_refs に追加 (必要なら) |
| 5 | `test(fixtures)` | 4a | cell_45refs baseline 2 ファイル再生成 + README 更新 + test 8 期待値更新 |
| 6 | `test(fixtures)` | 4b | apa_45refs baseline 2 ファイル再生成 + README 更新 + test 8 期待値更新 |
| 7 | `docs(sessions)` | 5 | Day20 archive (README + LESSONS) |

合計 **7 commits + 2 pre = 9 commits**. ※ Phase 3 (main.py 微改修) は不要と判明すれば 8 commits.

---

## 7. 完了条件 (12 項目)

| # | 条件 | 確認方法 |
|:---:|:---|:---|
| 1 | `STAGE3_COMPLETION_NOTE.md` 作成 + commit | file 存在 + git log 確認 |
| 2 | `three_class_classifier.py` に 3 helper 関数追加 | `grep -c "def _detect_book\|def _detect_conference\|def _classify_via_nlm_only" three_class_classifier.py` = 3 |
| 3 | `_classify_single` で 4 rule 順次評価 | code review で目視確認 |
| 4 | 既存 5 unit tests + 3 新 unit tests pass | `pytest tests/test_three_class_classifier.py -v` = 8 passed |
| 5 | cell_45refs baseline 再生成 (Phase 4 only) | `tests/fixtures/cell_45refs/baseline_three_class_classification.json` の git diff で A 件数が <14 に減 |
| 6 | apa_45refs baseline 再生成 | 同上 |
| 7 | test_integration_cell_45refs test 8 期待値更新 + pass | `pytest tests/test_integration_cell_45refs.py::test_baseline_three_class_classification_distribution -v` PASS |
| 8 | test_integration_apa_45refs test 8 期待値更新 + pass | 同上 |
| 9 | 全 test pass (regression なし) | `pytest tests/ -v 2>&1 \| tail -3` = **100 passed, 1 skipped** |
| 10 | gitleaks scan clean (継続) | `.gitleaksignore` の Day19 4 fingerprint 継続有効 |
| 11 | Day20 archive 5 files (SPEC + PLAN + STAGE3 + README + LESSONS) | `ls docs/sessions/day20/ \| wc -l` = 5 |
| 12 | GitHub push 完了 (CI success) | `gh run list --limit 1 --json conclusion --jq '.[0].conclusion'` = "success" |

---

## 8. 工数見積もり

| Phase | 内容 | 見積 |
|:---:|:---|---:|
| Pre | SPEC + PLAN archive | 30min |
| Phase 0 | STAGE3_COMPLETION_NOTE 作成 + commit | 15min |
| Phase 1 | three_class_classifier.py 改修 (3 helper + 評価順序) + commit | 30min |
| Phase 2 | unit test 3 新追加 + 1 修正 (TDD) + commit | 30min |
| Phase 3 | main.py 微改修 (is_book 渡し、必要なら) + commit | 10min |
| Phase 4a | cell_45refs baseline 再生成 (LLM cost ~$1) + README + test 8 + commit | 40min |
| Phase 4b | apa_45refs baseline 再生成 (LLM cost ~$1) + README + test 8 + commit | 40min |
| Phase 5 | Day20 archive (README + LESSONS) + push | 30min |
| **合計** | | **~3.5h** |

LLM cost: **~$2** (cell + apa fixture 再生成).

---

## 9. 想定リスクと対応

| リスク | 確率 | 対応 |
|:---|:---:|:---|
| NLM API 応答遅延/SSL エラーで baseline 再生成が unstable | 中 | retry + graceful unknown (Day15 設計通り)、不安定なら Day21+ で再 scan |
| `is_book` flag が `synthesize_outputs` で渡されていない | 高 | Phase 3 で main.py 微改修必要 (10min) |
| baseline 再生成で予想と異なる分布 (A=0 等) | 中 | 期待値ではなく実測値で test 8 を更新 (Day11 規約通り) |
| conference regex が false positive | 低 | `\b` 単語境界で安全、test で確認 |
| Phase 4a-4b の LLM call で network failure | 中 | `--reuse-phase2 --reuse-phase3` で部分再実行可能なら活用 |

---

## 10. Out of Scope (Day21+ 候補)

- **MCP server による batch processing** (Stage 3 認証で skill 機能経由を確認したが、より高度な体験は別 task)
- **predatory journal データベース連携** (Beall's list 等で B 細分化)
- **v0.1.0 tag 付与** + GitHub Release (公開化記念、~1h)
- **CONTRIBUTING.md / Issue PR template** (collaboration 受入準備)
- **SSH 認証 cleanup** (Day18 D18 起源)
- **pre-commit hook gitleaks 自動実行** (Day19 起源)

---

## 11. 参照

- Day15 SPEC: `docs/sessions/day15/SPEC_three_class_audit.md` (三分類 audit logic の origin)
- Day15 LESSONS: `docs/sessions/day15/DAY15_LESSONS_LEARNED.md` (3 module 設計)
- Day17 SPEC: `docs/sessions/day17/SPEC_cell_45refs_fixture.md` (cell_45refs fixture)
- Day17 LESSONS: `docs/sessions/day17/DAY17_LESSONS_LEARNED.md` D17 (A 多発の指摘)
- Day19 LESSONS: `docs/sessions/day19/DAY19_LESSONS_LEARNED.md` §6.2 (Day20+ 候補一覧)
- 既存 `three_class_classifier.py` (Day15 commit `71a318a`、本 SPEC で拡張対象)
- Day7 PHASE_0_VERIFICATION_REPORT: `docs/sessions/day7/PHASE_0_VERIFICATION_REPORT.md` §1.1 (Stage 3 origin)

---

**承認**: 片山英樹 (brainstorming Q0-Q3 + design 全 4 sections)
**次工程**: writing-plans skill で implementation plan を作成
