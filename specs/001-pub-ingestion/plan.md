# Implementation Plan: Publication Ingestion from CV Spreadsheet

**Branch**: `001-pub-ingestion` | **Date**: 2026-01-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-pub-ingestion/spec.md`

## Summary

Build a Python CLI tool that reads the Publications sheet from the user's `CV.numbers` file in iCloud, compares entries against existing `_publications/` markdown files, and creates new publication entries for any missing published papers. The tool uses the `numbers-parser` library to read the Numbers file natively, matches publications by DOI (primary) or title+year (fallback), and generates complete Jekyll-compatible markdown files with YAML frontmatter, citation blockquote, abstract, and article link. It supports a dry-run preview mode and reports missing data warnings.

## Technical Context

**Language/Version**: Python 3.9+ (compatible with numbers-parser 4.16.3)
**Primary Dependencies**: `numbers-parser` (Numbers file reading), `python-frontmatter` (YAML frontmatter parsing), `PyYAML` (authors.yml reading)
**Storage**: Filesystem — reads `.numbers` file and `_data/authors.yml`; writes `.md` files to `_publications/`
**Testing**: `pytest` with fixtures for spreadsheet data mocking and file output verification
**Target Platform**: macOS (required for iCloud path access and `snappy` native dependency)
**Project Type**: Single CLI script
**Performance Goals**: N/A — batch tool processing ~160 rows
**Constraints**: Requires Homebrew `snappy` library installed; macOS only; iCloud Drive synced
**Scale/Scope**: ~160 spreadsheet rows, ~137 existing publication files, ~50 known authors

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Assessment |
|-----------|--------|------------|
| I. Static-First | PASS | Tool generates static markdown files only. No runtime server, no client-side JS, no database. Output is pre-built static content. |
| II. Content as Data | PASS | Generated files use the `_publications` Jekyll collection with structured YAML frontmatter. Each publication is a single markdown file — no layouts or includes are modified. |
| III. Standards Compliance | PASS | Generated markdown follows existing kramdown/GFM conventions. No HTML generated. Frontmatter schema matches established entries. |
| IV. Automation & Agentic Refresh | PASS | Tool is idempotent (running twice produces the same result — no duplicates). Follows `AuthorYear_ID.md` naming convention. Script lives alongside existing automation tooling. |
| V. Incremental & Non-Destructive | PASS | Only adds new files; never modifies or deletes existing publication entries. Existing entries are skipped. No configuration changes required. |

**Post-Phase 1 re-check**: All gates remain PASS. The design adds a single Python script and test files — no layouts, includes, plugins, or configuration changes.

## Project Structure

### Documentation (this feature)

```text
specs/001-pub-ingestion/
├── plan.md              # This file
├── research.md          # Phase 0: technology decisions and rationale
├── data-model.md        # Phase 1: entity schemas and field mappings
├── quickstart.md        # Phase 1: setup and usage instructions
├── contracts/           # Phase 1: CLI interface contract
│   └── cli-contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
_scripts/
├── ingest_publications.py    # Main ingestion script (CLI entry point)
├── requirements.txt          # Python dependencies
└── tests/
    ├── test_ingest.py        # Unit and integration tests
    └── fixtures/
        └── sample_pub.md     # Sample publication for test comparison
```

**Structure Decision**: Single-script project placed in `_scripts/` at the repository root, alongside the existing `_publications/parse_publication.py` pattern. This keeps automation scripts co-located with the Jekyll site without interfering with the build. The `_scripts/` prefix signals "not a Jekyll collection" and follows the existing convention of utility scripts living near the content they manage. Tests are co-located under `_scripts/tests/`.

## Complexity Tracking

No constitution violations. No complexity justifications required.
