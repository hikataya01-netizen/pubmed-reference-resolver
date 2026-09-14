# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A peer-review support tool that takes a paper's **References section** (PDF / DOCX / TXT),
reverse-looks-up each citation in PubMed, and emits three deliverables (v2, `audit.py`):
a Word audit report (`references_audit_report.docx`), a PubMed-compatible CSV
(`references_pubmed.csv`, 29 columns), and a numbered abstract-text file
(`references_abstracts.txt`). It verifies existence, bibliographic accuracy, duplicate
citations, and retracted publications, and assesses originality, evidence level, recency,
predatory-journal risk, and claim support. The legacy `main.py` pipeline's own report
(`report.md`, Markdown, Phase 2-4) is deprecated; only its Phase 1-2 (extraction, line-number
stripping) is still reused by v2.

The codebase and almost all docs are written in **Japanese**; match that language in
commit messages, session docs, and code comments. Code identifiers are English.

## Commands

This project uses **uv** (migrated from `requirements.txt` at Day27). `pyproject.toml` +
`uv.lock` are the source of truth — do not reintroduce `requirements.txt`.

```bash
# Install / sync deps (dev group includes pytest)
uv sync --frozen --group dev
npm ci                  # Node.js deps for Word output (build_docx.js); Node.js 18+

# Run the full test suite (currently 134 passed, 0 skipped)
uv run pytest tests/ -q

# Run a single test file / single test
uv run pytest tests/test_three_class_classifier.py -q
uv run pytest tests/test_main_split_references.py::test_name -q

# Run the v2 pipeline (CLI app — flat layout, no entry_point installed)
uv run python audit.py --structured refs.json -o out/

# Run the legacy pipeline  # legacy
uv run python main.py input_References.docx  # legacy
uv run python main.py input_References.docx --overrides integration/src/manual_overrides.yaml  # legacy
```

Tests run fully **offline and without API keys** — fixtures are deterministic and external
API calls are dependency-injected with fixture paths in tests. Never make the test suite
depend on a live `ANTHROPIC_API_KEY` or network access.

CI (`.github/workflows/tests.yml`) runs `uv sync --frozen --group dev` then `uv run pytest`
on Python 3.11/3.12 (required) and 3.14 (`continue-on-error` experimental). Note `.python-version`
pins 3.14 locally but `requires-python` is `>=3.11`.

## Architecture

### v2 pipeline (`audit.py`)

`audit.py` is the canonical entry point. It takes a pre-structured `refs.json` (the caller's
own LLM structures References in-context — no Anthropic API call inside the pipeline) and
injects it at Stage 3, then runs:

- **Stage 4 — resolve** (`pipeline/resolve.py`): the same PubMed cascade as the legacy
  pipeline, levels **L1 → L2 → L3a → L3b → L3c → L3d** (PMID direct → DOI → author+title
  keywords+year → author+journal+year+title keywords → author+journal+year → title
  keywords+year only). L1/L2 hits are trusted outright; L3 hits require the double guard
  (title similarity ≥0.50 **and** first-author surname match).
- **Stage 5.5 — enrich** (`pipeline/enrich.py`): journal indexing lookups (NLM Catalog
  MEDLINE status + DOAJ), skipped entirely with `--offline`.
- **Stage 6 — consistency** (`pipeline/consistency.py`): 19 issue categories across 4
  severities (MAJOR/MODERATE/MINOR/INFO) — see `skill_package/SKILL.md` for the full table.
- **Stage 6.5 — assess** (`pipeline/assess.py`): the 5 evaluation criteria (retraction status,
  originality, evidence level, recency, predatory-journal risk) plus, when `--claim-support`
  is given, claim-support verdicts.
- **Stage 7 — outputs** (`pipeline/outputs.py` + `build_docx.js`): writes the 3 fixed
  deliverables plus `resolved.json` / `issues.json` / `report_data.json` sidecars.
- **Stage 8 — self_check** (`audit.py`): a critical self-review note appended to the report.

Dependencies are standard-library only for Python (no `anthropic`/`requests`/`rapidfuzz`);
Word generation shells out to Node.js (`build_docx.js`, `package.json`/`package-lock.json`,
installed via `npm ci`).

### Legacy pipeline (`main.py`)

`main.py` (~88KB) is the pipeline. It runs in **phases 1–4** (plus a "Stage 5" report
synthesis inside Phase 4). Each phase is invoked by `run_phaseN()` and writes a
`phaseN_*.json` intermediate so later phases can be re-run with `--reuse-phase2` / `--reuse-phase3`.

- **Phase 1 — extract & clean** (`extract_text` → `detect_line_numbers` → `preprocess` →
  `split_references`). Pulls text from PDF/DOCX/TXT, detects and strips PDF copy-paste line
  numbers via a longest-increasing-subsequence (LIS) heuristic, normalizes Unicode/whitespace,
  and splits into individual reference blocks. The author-surname boundary regex used by
  `split_references` is driven by the `_UPPERCASE_LATIN1` constant (Basic Latin + Latin-1
  Supplement + Latin Extended-A) — extend that single constant rather than scattering ranges.
- **Phase 2 — structure** (`structure_all_references`). Routes each block: MDPI-format
  references go through the **deterministic fast-path** (`mdpi_parser.py`, no API cost); all
  others go to **Claude `claude-sonnet-4-6`** with a prompt-cached system message. Manual
  corrections from `--overrides` YAML are applied here. The **Vancouver Veto** (`is_mdpi_style()`
  detecting `(YYYY)` / `(YYYYa)`) forces ambiguous styles off the fast-path into the LLM path.
- **Phase 3 — resolve** (`resolve_all` → `resolve_one`). A 4-level PubMed cascade via NCBI
  E-utilities: PMID direct → DOI (with hyphen-stripped rescue) → title+author+year fuzzy (≥90%)
  → title-only fuzzy. Rate-limited (3 req/s, or 10 req/s with `NCBI_API_KEY`). Unresolved
  references are kept as blank rows so numbering is never broken.
- **Phase 4 — synthesize** (`synthesize_outputs`). Composite-key duplicate detection
  (PMID / DOI / normalized title+author+year), then two audits, then output writers.

Sibling modules, all called from Phase 4 unless noted:
- `mdpi_parser.py` — MDPI fast-path parser (called in Phase 2).
- `journal_audit.py` — citation-journal vs PubMed `journal_iso` similarity; severities
  MAJOR/WARN/INFO/OK. Emits `journal_mismatch_audit.json` sidecar.
- `three_class_classifier.py` — classifies unresolved refs: **A** = true fabrication
  (no/invalid DOI), **B** = MEDLINE non-indexed journal, **C** = indexed-journal indexing gap,
  **unknown** = fail-soft on network/data error. Emits `three_class_classification.json`.
  Uses dependency injection (`crossref_fn`, `nlm_fn`) so tests pass fixtures instead of hitting the net.
- `crossref_check.py` — Crossref `/works/{doi}` existence check (A vs B/C).
- `nlm_catalog_check.py` — 2-step NLM Catalog lookup for journal MEDLINE indexing status (B vs C).

Output files (legacy): `csv-{first_pmid}-set.csv` (UTF-8 BOM, quoted),
`abstract-{first_pmid}-set.txt`, `report.md` (dashboard + prioritized issues + unresolved
detail + journal-audit appendix + transparency trace), plus the two JSON sidecars above.

## Conventions

**Day-N TDD session workflow.** Development proceeds in numbered "Day" sessions, each a
strict commit chain of exactly five commits:

1. `docs(spec): ...` — design doc in `docs/superpowers/specs/YYYY-MM-DD-dayN-*-design.md`
2. `docs(plan): ...` — plan in `docs/superpowers/plans/YYYY-MM-DD-dayN-*.md`
3. `test(prep): ...` — failing unit test (**TDD RED**)
4. `fix(...)` / `feat(...)`: ... — implementation that makes it pass (**TDD GREEN**)
5. `docs(sessions): archive dayN ...` — session record in `docs/sessions/dayN/`
   (`README.md` summarizing the commit chain + `DAYN_LESSONS_LEARNED.md`)

Follow this pattern for substantive changes. Commit subjects use Conventional Commits
(`type(scope): summary`) with Japanese summaries. Reuse the templates in `docs/templates/`.

**`skill_package/` is a mirror.** `skill_package/{main.py,mdpi_parser.py,journal_audit.py,
audit.py,pipeline,build_docx.js,manual_overrides.yaml}` are symlinks to the repo root,
packaged for distribution as a Claude Code skill — editing the root file is reflected
immediately, no copy step needed. `integration/src/*.py` are spec baselines, not the live
implementation — the root files are authoritative.

**Golden fixtures.** `tests/fixtures/{mdpi_173refs,vancouver_35refs,apa_45refs,cell_45refs}/`
follow the `expected_*` (deterministic, byte-exact) vs `baseline_*` (document-of-record,
regeneratable) naming split. All fixtures derive from PMC Open Access CC BY 4.0 papers with
provenance in each fixture's `README.md`. If you change pipeline output, regenerate the
relevant `baseline_*` files (build scripts live in `tools/`).

**v2 tests.** `test_v2_pipeline.py` / `test_v2_env.py` replay recorded NCBI/DOAJ responses via
`tests/v2_replay.py` against `tests/fixtures/v2_synthetic_7refs/` — no network, no API key.
To re-record (e.g. after a PubMed bibliographic update changes the expected output), run
`tools/record_v2_fixture.py` (real network calls to NCBI E-utilities / NLM Catalog / DOAJ,
no API key required).

**Secrets.** API keys load via `load_env_files()`, which auto-discovers `.env` from 4
candidate paths, in this precedence order: 1) the directory containing `main.py` (repo
root) `.env` 2) `$HOME/.pubmed-reference-resolver.env` (recommended placement) 3) cwd
`.env` 4) the input file's directory `.env` (for `audit.py`/v2 this is the `refs.json`
directory — placing a stray `.env` in a manuscript folder gets picked up here). `--env-file
PATH` **replaces** this auto-discovery entirely (only that one file is read, none of the 4
candidates); `--no-env-file` disables `.env` loading altogether. Regardless of how (or
whether) a `.env` was loaded, an environment variable already set to a **non-empty** value
is never overridden by it, and CLI `--api-key` / `--ncbi-api-key` win over both. Never
commit real keys — `.gitignore` excludes `.env*`.
Synthetic test secrets that trip gitleaks are documented in `.gitleaksignore` by fingerprint;
add new false positives there with a rationale rather than rewriting fixtures.
