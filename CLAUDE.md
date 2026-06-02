# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A peer-review support tool that takes a paper's **References section** (PDF / DOCX / TXT),
reverse-looks-up each citation in PubMed, and emits three deliverables: a PubMed-compatible
CSV, a numbered abstract-text file, and an integrated audit report (`report.md`). It also
detects duplicate citations, journal-name/DOI mismatches, and likely AI-fabricated references.

The codebase and almost all docs are written in **Japanese**; match that language in
commit messages, session docs, and code comments. Code identifiers are English.

## Commands

This project uses **uv** (migrated from `requirements.txt` at Day27). `pyproject.toml` +
`uv.lock` are the source of truth — do not reintroduce `requirements.txt`.

```bash
# Install / sync deps (dev group includes pytest)
uv sync --frozen --group dev

# Run the full test suite (currently 115 passed, 0 skipped)
uv run pytest tests/ -q

# Run a single test file / single test
uv run pytest tests/test_three_class_classifier.py -q
uv run pytest tests/test_main_split_references.py::test_name -q

# Run the pipeline (CLI app — flat layout, no entry_point installed)
uv run python main.py input_References.docx
uv run python main.py input_References.docx --overrides integration/src/manual_overrides.yaml
```

Tests run fully **offline and without API keys** — fixtures are deterministic and external
API calls are dependency-injected with fixture paths in tests. Never make the test suite
depend on a live `ANTHROPIC_API_KEY` or network access.

CI (`.github/workflows/tests.yml`) runs `uv sync --frozen --group dev` then `uv run pytest`
on Python 3.11/3.12 (required) and 3.14 (`continue-on-error` experimental). Note `.python-version`
pins 3.14 locally but `requires-python` is `>=3.11`.

## Architecture

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

Output files: `pubmed_csv-*.csv` (UTF-8 BOM, quoted), `abstract_text-*.txt`, `report.md`
(dashboard + prioritized issues + unresolved detail + journal-audit appendix + transparency trace),
plus the two JSON sidecars above.

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

**`skill_package/` is a mirror.** `skill_package/{main.py,mdpi_parser.py,journal_audit.py}`
are byte-identical copies of the repo-root modules, packaged for distribution as a Claude
Code skill. When you change a root module, update its `skill_package/` copy in the same change
(verify with `diff main.py skill_package/main.py`). `integration/src/*.py` are spec baselines,
not the live implementation — the root files are authoritative.

**Golden fixtures.** `tests/fixtures/{mdpi_173refs,vancouver_35refs,apa_45refs,cell_45refs}/`
follow the `expected_*` (deterministic, byte-exact) vs `baseline_*` (document-of-record,
regeneratable) naming split. All fixtures derive from PMC Open Access CC BY 4.0 papers with
provenance in each fixture's `README.md`. If you change pipeline output, regenerate the
relevant `baseline_*` files (build scripts live in `tools/`).

**Secrets.** API keys load via `load_env_files()` from a 4-path search (`--env-file` >
cwd `.env` > `$HOME/.pubmed-reference-resolver.env` > skill dir `.env`); CLI `--api-key` /
`--ncbi-api-key` win over env. Never commit real keys — `.gitignore` excludes `.env*`.
Synthetic test secrets that trip gitleaks are documented in `.gitleaksignore` by fingerprint;
add new false positives there with a rationale rather than rewriting fixtures.
