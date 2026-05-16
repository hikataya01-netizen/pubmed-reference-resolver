# SPEC_three_class_audit.md

**目的**: Day13 INVESTIGATION で発見した「PubMed 未ヒット 3 分類」を audit_report に実装する (Day13 §6 改修候補 A の完了).

**作成日**: 2026/05/13 (Day15)
**作成者**: Claude Code (Sonnet 4.6)
**承認**: 片山英樹 (Hideki Katayama) — brainstorming Q1-Q4 + 8 section 設計提示で大筋承認取得済
**配置**: `docs/sessions/day15/SPEC_three_class_audit.md`
**配置の理由**: brainstorming skill default は `docs/superpowers/specs/` だが、本プロジェクト慣例 (`docs/sessions/dayN/`) を優先 (Day9 SPEC と同方針). Day15 完了後は SPEC + 実装 + LESSONS_LEARNED が同一ディレクトリに揃う.

---

## 1. 経緯

### 1.1 Day13 で発見された 3 分類

Day9 (Z) で残った未解決 2 件 (#17 Davey, #22 Gallina) を Day13 で実証調査した結果、「PubMed 未ヒット = 捏造」の単純化が誤りで、**3 分類**が必要と判明 (`docs/sessions/day13/INVESTIGATION_unresolved_2refs.md` §3.2):

| 分類 | 判定基準 | 例 | 警告 level |
|:---|:---|:---:|:---:|
| **A. 真の捏造** | DOI 実在せず (Crossref hit なし) | (LLM ハルシネーション) | **重大** |
| **B. MEDLINE 非収録誌の正規論文** | DOI 実在 + journal `currentindexingstatus = N` | #22 Gallina (OMICS) | **軽微** |
| **C. MEDLINE 収録誌の indexing 漏れ論文** | DOI 実在 + journal `currentindexingstatus = Y` + 論文 unindexed | #17 Davey (Fam Syst Health 2003) | **軽微** |

### 1.2 Day13 §6 改修候補 4 案

INVESTIGATION §6 で 4 案を提示、**Day14 で B + C (docs 反映) を完了**、**Day15 で A (audit logic 実装) を完了**するのが本 SPEC の射程.

### 1.3 Day14 までに反映済の docs

- `skill_package/SKILL.md` description: 3 分類化を 1 行サマリーで記載
- `skill_package/SKILL.md` 本文 line 135: 3 sub-bullet で詳細
- `skill_package/references/USAGE_QUICKSTART.md` §V Q4 (1.2): table + curl 補助検証手順 + **「現状制約」section** (本 SPEC 完了で削除予定 → 1.3 bump)

---

## 2. 採用方針 (Q1-Q4 brainstorm 結果)

### Q1: 規模 scope → **案 2 (段階的中規模、独立 2 module、1 session)**

| 案 | 採否 | 理由 |
|:---:|:---:|:---|
| 案 1 (最小実装、1 module 統合) | × | YAGNI 過剰、将来拡張性犠牲 |
| **案 2 (独立 2 module + 統合 logic)** | **○** | clean な設計、Day9 と同規模、1 session 完結可能 |
| 案 3 (複数 SPEC 分割) | × | オーバーヘッド大 |

### Q2: API call timing → **(b) Phase 4 audit 中**

| 案 | 採否 | 理由 |
|:---:|:---:|:---|
| (a) Phase 3 cascade 中 | × | Phase 3 肥大化、phase3_resolved.json schema 拡張で MDPI fixture 再生成必要 |
| **(b) Phase 4 audit 中** | **○** | 既存 journal_audit と同 timing、Phase 3 触らない、Single Responsibility |
| (c) 新 Phase 3.5 | × | YAGNI、phase 数増 |

### Q3: test 戦略 → **(γ) fixture-based**

| 案 | 採否 | 理由 |
|:---:|:---:|:---|
| (α) live API call | × | CI flaky、network 依存 |
| (β) mock-based | × | 手書き JSON で実 API 仕様と乖離リスク |
| **(γ) fixture-based** | **○** | Day13 取得済 API 応答を fixture 化、Day11 規約と整合、deterministic |
| (δ) hybrid | × | Day15 scope 超え (将来検討) |

### Q4: fail-soft 戦略 → **(ii) graceful unknown**

| 案 | 採否 | 理由 |
|:---:|:---:|:---|
| (i) strict (exception raise) | × | 致命的、CI 不能 |
| **(ii) graceful unknown** | **○** | network エラー時は分類 `'unknown'` で継続、user は手動確認可 |
| (iii) fallback to existing | × | 改善効果が隠れる |

**細部**: timeout 10s、retry 1 回、stderr WARN、cache はメモリ内 dict (実行内のみ).

---

## 3. Architecture (ファイル構成)

### 3.1 新規 module 3 ファイル (project root)

```
pubmed-reference-resolver/
├── crossref_check.py          ← 新規: Crossref API client (DOI 実在確認)
├── nlm_catalog_check.py       ← 新規: NLM Catalog API client (currentindexingstatus 取得)
├── three_class_classifier.py  ← 新規: 統合 logic (Day13 §3.4 擬似コード)
├── main.py                    ← 改修: synthesize_outputs() に 3 分類 logic 呼出追加
└── journal_audit.py           ← 不変
```

### 3.2 依存関係

```
synthesize_outputs (main.py)
    ├── journal_audit.audit_journal_mismatch()  ← 既存 (不変)
    └── three_class_classifier.classify_unresolved_refs()  ← 新規
            ├── crossref_check.check_doi_exists()
            └── nlm_catalog_check.get_journal_indexing_status()
```

各 module は **stateless** (cache はメモリ内 dict、関数 scope or module-level)、関数指向設計 (class なし、Day1-9 既存設計と整合).

### 3.3 各 module の責務

#### `crossref_check.py`

```python
def check_doi_exists(doi: str, *, fixture_path: Path | None = None) -> dict:
    """Crossref API で DOI 実在確認.

    Returns:
        {
            "exists": True | False | None,  # None = unknown (graceful)
            "metadata": {...} | None,        # journal/title/authors 等 (実在時)
            "error": str | None,             # network エラーの場合のメッセージ
        }
    """
```

- `fixture_path` 指定時: fixture file から JSON 読出 (test 用)
- 未指定時: `https://api.crossref.org/works/{doi}` に GET (production)
- timeout 10s、retry 1 回、network エラーは graceful (`exists=None`, `error=...`)

#### `nlm_catalog_check.py`

```python
def get_journal_indexing_status(
    journal_name: str | None = None,
    issn: str | None = None,
    *, fixture_path: Path | None = None,
) -> dict:
    """NLM Catalog で journal の currentindexingstatus 取得.

    Returns:
        {
            "status": "Y" | "N" | None,   # None = unknown (graceful or 該当なし)
            "nlm_id": str | None,
            "medlineta": str | None,       # journal 略称
            "error": str | None,
        }
    """
```

- 検索 priority: ISSN (最優先) > journal_name
- esearch + esummary の 2 段 API call
- API key 不要 (rate 3 req/sec で十分、`.env` の NCBI key 設定済なら自動利用)
- network エラーは graceful (`status=None`)

#### `three_class_classifier.py`

```python
def classify_unresolved_refs(
    unresolved_refs: list[dict],
    *,
    crossref_fixture_dir: Path | None = None,
    nlm_fixture_dir: Path | None = None,
) -> list[dict]:
    """未解決 ref に 3 分類 (A/B/C/unknown) を付与.

    Day13 §3.4 擬似コード:
        if not ref.get('doi'):
            return 'A_likely_fabrication'
        if not check_crossref(doi).exists:
            return 'A_likely_fabrication'
        nlm = get_nlm_status(journal/issn)
        if nlm.status == 'N': return 'B_medline_unindexed_journal'
        if nlm.status == 'Y': return 'C_medline_journal_paper_unindexed'
        return 'unknown'

    Returns:
        [
            {
                "ref_no": int,
                "class": "A" | "B" | "C" | "unknown",
                "reason": str,                # 1-2 文の判定根拠
                "doi_resolved": bool | None,
                "journal_indexing": "Y" | "N" | None,
                "details": {...}              # crossref/nlm の raw response 抜粋
            },
            ...
        ]
    """
```

- 入力 `unresolved_refs`: `result["stage4_pubmed_resolutions"]` から `pmid is None` を filter
- 戻り値は list、後段の `synthesize_outputs` で `result["stage5_3class_classification"]` に保存

### 3.4 関連する未変更箇所 (本 SPEC scope 外)

- `journal_audit.py`: 既存 audit logic、本 SPEC で touch しない
- `mdpi_parser.py`: 不変
- `main.py:run_phase1/2/3`: 不変 (改修は `synthesize_outputs` のみ)
- `tests/fixtures/mdpi_149refs/`: 不変 (Phase 3 出力 schema 不変のため)

---

## 4. Data Flow

```
[Phase 4: synthesize_outputs(result, output_dir)]
    │
    ├─ 1. result["stage4_pubmed_resolutions"] から未解決 refs を filter
    │     unresolved_refs = [r for r in resolutions if r.get('pmid') is None]
    │
    ├─ 2. 各未解決 ref に対し three_class_classifier.classify_unresolved_refs() 呼出
    │     classifications = three_class_classifier.classify_unresolved_refs(unresolved_refs)
    │       ├─ DOI なし → A
    │       ├─ DOI あり → crossref_check.check_doi_exists(doi)
    │       │   ├─ exists=False → A
    │       │   ├─ exists=None (graceful) → unknown
    │       │   └─ exists=True → nlm_catalog_check.get_journal_indexing_status(...)
    │       │       ├─ status=N → B
    │       │       ├─ status=Y → C
    │       │       └─ status=None (graceful) → unknown
    │
    ├─ 3. result["stage5_3class_classification"] = classifications で保存
    │
    ├─ 4. 既存 journal_audit.audit_journal_mismatch() 呼出 (不変)
    │     result["stage5_journal_audit"] = filtered_findings
    │
    └─ 5. report.md / sidecar JSON 出力
        ├─ report.md §2 直後に 3 分類 section 追加
        ├─ three_class_classification.json (新 sidecar) 出力
        └─ journal_mismatch_audit.json (既存) 出力
```

---

## 5. Output Structure

### 5.1 report.md (新セクション追加)

`## 2. 未解決参照の詳細` の **直後**に新セクション挿入:

```markdown
### 2.1 [3 分類化] PubMed 未ヒットの分類

(Day13 INVESTIGATION で発見された 3 分類を Day15 で実装)

| ref | 分類 | 理由 | 査読推奨アクション |
|:---:|:---:|:---|:---|
| #17 | C (収録誌 indexing 漏れ) | journal "Fam Syst Health" は MEDLINE 収録 (currentindexingstatus=Y) だが本論文単体は indexing なし | DOI で landing page 確認、他 DB (PsycInfo 等) で検証 |
| #22 | B (MEDLINE 非収録誌) | journal "Clin Mother Child Health" は currentindexingstatus=N (OMICS Publishing Group, predatory 注意) | 引用根拠の信頼性確認、代替論文推奨 |

**集計**: A (真の捏造) 0 件 / B (MEDLINE 非収録誌) 1 件 / C (収録誌 indexing 漏れ) 1 件 / unknown (判定不可) 0 件
```

### 5.2 sidecar JSON 新規 `three_class_classification.json`

`journal_mismatch_audit.json` と並列の独立 file:

```json
[
  {
    "ref_no": 17,
    "class": "C",
    "reason": "journal Fam Syst Health は MEDLINE 収録 (currentindexingstatus=Y) だが論文単体 unindexed",
    "doi_resolved": true,
    "journal_indexing": "Y",
    "details": {
      "doi": "10.1037/1091-7527.21.3.245",
      "crossref_journal": "Families, Systems, & Health",
      "nlm_id": "9610836",
      "nlm_medlineta": "Fam Syst Health"
    }
  },
  {
    "ref_no": 22,
    "class": "B",
    "reason": "journal Clin Mother Child Health は MEDLINE 非収録 (currentindexingstatus=N, OMICS predatory)",
    "doi_resolved": true,
    "journal_indexing": "N",
    "details": {
      "doi": "10.4172/2090-7214.1000217",
      "crossref_journal": "Clinics in Mother and Child Health",
      "crossref_publisher": "OMICS Publishing Group",
      "nlm_id": "101300689",
      "nlm_medlineta": "Clin Mother Child Health"
    }
  }
]
```

### 5.3 既存出力との関係

| ファイル | 変更 |
|:---|:---|
| `report.md` | §2 直後に新セクション追加 |
| `three_class_classification.json` | **新規** sidecar |
| `journal_mismatch_audit.json` | 不変 |
| `phase4_final.json` | `stage5_3class_classification` フィールドが追加される |
| `csv-*.csv` / `abstract-*.txt` | 不変 |

---

## 6. Test Plan

### 6.1 新規 test ファイル `tests/test_three_class_classifier.py` (7 test)

| # | test | 性質 | 期待 |
|:---:|:---|:---|:---|
| 1 | `test_classify_returns_A_when_doi_missing` | A 分類 (DOI なし) | DOI 欠落 ref → class=A |
| 2 | `test_classify_returns_A_when_crossref_404` | A 分類 (Crossref hit なし) | fixture: 空 hit → class=A |
| 3 | `test_classify_returns_B_when_nlm_status_N` | B 分類 (#22 Gallina) | fixture: NLM status=N → class=B |
| 4 | `test_classify_returns_C_when_nlm_status_Y` | C 分類 (#17 Davey) | fixture: NLM status=Y → class=C |
| 5 | `test_classify_returns_unknown_on_network_error` | fail-soft (graceful) | fixture: error response → class=unknown |
| 6 | `test_crossref_check_uses_fixture_correctly` | crossref_check 単体 | fixture path 経由 read |
| 7 | `test_nlm_catalog_check_uses_fixture_correctly` | nlm_catalog_check 単体 | fixture path 経由 read |

### 6.2 既存 `tests/test_integration_vancouver_24refs.py` に test 追加 (1 件)

| # | test | 性質 |
|:---:|:---|:---|
| 8 | `test_baseline_vancouver_3class_classification_documents_classes` | baseline 整合性 (#17→C, #22→B が baseline で成立) |

→ 全 test **79 passed** (Day14 末 71 → +8) を完了条件.

### 6.3 fixture 配置 (Day11 ハイブリッド命名規約)

```
tests/fixtures/three_class_classification/
├── README.md                                          ← 由来 + 命名規約 + refresh 運用
├── expected_crossref_10_1037-1091-7527.json           ← #17 Davey hit
├── expected_crossref_10_4172-2090-7214.json           ← #22 Gallina hit
├── expected_crossref_404.json                         ← 仮想 fabrication (空 hit)
├── expected_nlm_search_1091-7527.json                 ← Fam Syst Health ISSN search
├── expected_nlm_summary_9610836.json                  ← Fam Syst Health (status=Y)
├── expected_nlm_search_clin_mother.json               ← Clin Mother Child Health
└── expected_nlm_summary_101300689.json                ← Clin Mother Child Health (status=N)
```

全ファイル `expected_*` prefix (deterministic、Day13 取得時点 snapshot で固定). `baseline_*` は不要 (本 module は API 応答 fixture を入力に使うのみで、output は分類結果という deterministic なデータ).

---

## 7. Commit 計画

**5 commits に段階分割** (各 TDD cycle):

| # | commit | 種別 | 内容 |
|:---:|:---|:---|:---|
| 1 | `feat(crossref): add crossref_check module with fixture-based test` | feat | crossref_check.py + 単体 test 2 件 (success/404) + fixture 3 個 |
| 2 | `feat(nlm): add nlm_catalog_check module with fixture-based test` | feat | nlm_catalog_check.py + 単体 test 2 件 (status Y/N) + fixture 4 個 |
| 3 | `feat(audit): add three_class_classifier integrating crossref + nlm` | feat | three_class_classifier.py + 統合 test 5 件 (A/B/C/unknown + fail-soft) |
| 4 | `feat(synthesize): integrate three_class into Phase 4 audit_report` | feat | main.py:synthesize_outputs 改修 + report.md / sidecar JSON 出力 + Vancouver fixture test 1 件追加 |
| 5 | `docs(skill): bump USAGE_QUICKSTART to 1.3 (audit logic 実装済反映)` | docs | USAGE_QUICKSTART §V Q4 「現状制約」削除 + 1.3 bump + §X 変更履歴 entry |

**別 commit** (本実装後):
- 6. Day15 archive (README + DAY15_LESSONS_LEARNED) — SPEC は本 SPEC commit で既存

---

## 8. Out of Scope

以下は本 SPEC で扱わない (別タスク):

- **Vancouver fixture (Day11) baseline 再生成**: 現 baseline_phase3_resolved.json は変更不要 (Phase 4 出力のみ拡張)
- **ハルシネーション真実例の fixture**: A 分類実例は擬似 (Crossref 404) のみ. 真の捏造例は将来 user 提供時に追加
- **cache の永続化**: メモリ内のみ、disk persist は YAGNI
- **API key 設定の拡張**: NCBI key は既存 `.env` で十分、Crossref は key 不要
- **MCP/hook 経由 Stage 3 配線**: Day7 §9.3 別タスク
- **`--phase` flag への新 phase 追加**: Phase 4 内追加で済むため不要
- **`(δ) hybrid test` (live API call test の skip-by-default 実装)**: Day16+ 候補

---

## 9. 想定外への対応

| 想定外 | 兆候 | 対処 |
|:---|:---|:---|
| Crossref API 仕様変更 (response schema 変化) | test 5-6 で fixture と diff | fixture 更新 + production code parser 修正 |
| NLM Catalog の `currentindexingstatus` field 廃止 | NLM API 仕様変更 (確率: 低) | esummary v2.0 へ migration 計画、Day15 scope 外 |
| Day11 baseline_phase3_resolved.json と Phase 4 出力 mismatch | test_baseline_vancouver_* で fail | fail-soft fixture 追加で Day11 fixture を変更せず吸収 |
| TDD GREEN 段階で API call の dependency injection 設計問題 | test が production code を変更 | Day9 のように設計修正を commit message で documented、SPEC update commit を別途 |

---

## 10. 工数見積

- brainstorming + SPEC 書き込み: 30-45 分 (現セッション中、本 commit で完結)
- TDD 実装 (5 commits): 60-90 分
- archive 作成: 15-20 分
- **合計: 1.5-2.5 時間** (1 session 内完結可能、Day9 と同規模)

---

## 11. 完了条件

本 SPEC は以下が成立した時点で「実装完了」とする:

- [ ] `crossref_check.py` 新設 (~80 lines)
- [ ] `nlm_catalog_check.py` 新設 (~100 lines)
- [ ] `three_class_classifier.py` 新設 (~80 lines)
- [ ] `main.py:synthesize_outputs()` 改修 (3 分類 logic 呼出 + 出力)
- [ ] `tests/test_three_class_classifier.py` 新設 (7 test)
- [ ] `tests/fixtures/three_class_classification/` 新設 (7 fixture file + README)
- [ ] `tests/test_integration_vancouver_24refs.py` に test 1 件追加
- [ ] `pytest tests/` が **79 passed, 1 skipped** を報告 (Day14 末 71 → +8)
- [ ] `skill_package/references/USAGE_QUICKSTART.md` を 1.2 → 1.3 bump
- [ ] commit が 5 件作成、各 commit message に本 SPEC への参照あり
- [ ] git status が clean (untracked = .DS_Store のみ)

---

## 12. 関連リソース

| リソース | 場所 | 役割 |
|:---|:---|:---|
| Day13 INVESTIGATION | `docs/sessions/day13/INVESTIGATION_unresolved_2refs.md` | §3.4 擬似コード, §4.2 curl 再現手順, §6 改修候補 |
| Day14 docs 反映 | `docs/sessions/day14/DAY14_LESSONS_LEARNED.md` | §2 SKILL.md vs USAGE_QUICKSTART 階層化、本 SPEC 完了で 1.3 bump |
| Day9 SPEC (前例) | `docs/sessions/day9/SPEC_mdpi_fast_path_strict.md` | brainstorming → SPEC → TDD の 4 段階フロー先例 |
| Day11 ハイブリッド命名規約 | `tests/fixtures/vancouver_24refs/README.md` | expected_* / baseline_* の使い分け |
| 既存 audit module | `journal_audit.py` (252 行) | 改修 scope 外、参考実装 |
| 改修対象 | `main.py:synthesize_outputs()` (line 1697-) | Phase 4 出力 logic |

---

**SPEC 作成日**: 2026/05/13
**作成者**: Claude Code (Sonnet 4.6)
**承認**: 片山英樹 (Hideki Katayama) — brainstorming 段階で大筋 approval、本 spec doc の review 後に最終承認予定
**次ステップ**: spec self-review → user reviews → 直接 TDD 実装 (Day9 と同パターン、writing-plans skip)
