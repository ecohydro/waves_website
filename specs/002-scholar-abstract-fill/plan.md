# Implementation Plan: Scholar API Abstract Retrieval

**Branch**: `002-scholar-abstract-fill` | **Date**: 2026-01-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-scholar-abstract-fill/spec.md`

## Summary

Build a Python CLI tool that scans existing publication markdown files in `_publications/` to identify those lacking abstracts, queries the Scholar API (https://docs.scholarai.io/) to retrieve missing abstracts using DOI or title+year search, updates the markdown files with retrieved abstracts, and writes abstracts back to the CV.numbers spreadsheet to maintain data consistency. The tool loads API credentials from environment variables, implements rate limiting (1-second delays) and retry logic (3 retries with exponential backoff), supports dry-run preview mode, and reports success/failure statistics. Uses the same libraries as feature 001 (`python-frontmatter`, `numbers-parser`) plus HTTP request handling for the Scholar API.

## Technical Context

**Language/Version**: Python 3.9+ (compatible with existing feature 001)
**Primary Dependencies**: `requests` or `httpx` (HTTP client for Scholar API), `python-frontmatter` (markdown file parsing), `numbers-parser` (CV.numbers read/write), `PyYAML` (YAML handling), `python-dotenv` (environment variable loading from .env)
**Storage**: Filesystem — reads/writes `.md` files in `_publications/`, reads/writes CV.numbers file, loads `.env` for API credentials
**Testing**: `pytest` with `responses` or `httpx-mock` for API mocking, fixtures for publication files
**Target Platform**: macOS (same as feature 001 — iCloud path access required)
**Project Type**: Single CLI script (similar to feature 001)
**Performance Goals**: Complete ~170 publications within 15 minutes (1-second rate limit allows ~170 requests in ~3 minutes plus retry overhead)
**Constraints**: Scholar API rate limits (1-second delay between requests), requires API key in `.env`, macOS only for Numbers file access
**Scale/Scope**: ~170 publication files, ~27 missing abstracts initially, batch processing with incremental updates

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Assessment |
|-----------|--------|------------|
| I. Static-First | PASS | Tool updates existing static markdown files and CV.numbers spreadsheet. No runtime server, no client-side JS, no database. Output remains pre-built static content. |
| II. Content as Data | PASS | Modifies existing `_publications` Jekyll collection entries by adding abstract text to body content. No changes to frontmatter schema, layouts, or includes. Each publication remains a single markdown file. |
| III. Standards Compliance | PASS | Preserves existing markdown format. Abstract insertion follows established pattern (`**Abstract**: {text}`). No HTML generation. No schema changes. |
| IV. Automation & Agentic Refresh | PASS | Tool is idempotent (running twice skips already-processed publications). Follows existing `AuthorYear_ID.md` naming convention. Script lives in `_scripts/` alongside feature 001. Maintains CV.numbers as authoritative source. |
| V. Incremental & Non-Destructive | PASS | Only adds abstract text to existing files; never deletes or modifies other content. Skips publications that already have abstracts. No configuration changes. CV.numbers write-back preserves existing data. |

**Post-Phase 1 re-check**: All gates remain PASS. The design adds a single Python script and test files — no layouts, includes, plugins, or configuration changes. No changes to existing publications beyond abstract text insertion.

## Project Structure

### Documentation (this feature)

```text
specs/002-scholar-abstract-fill/
├── plan.md              # This file
├── research.md          # Phase 0: Scholar API integration patterns, HTTP client choice
├── data-model.md        # Phase 1: API request/response schemas, publication matching logic
├── quickstart.md        # Phase 1: setup (API key), usage examples
├── contracts/           # Phase 1: CLI interface and API interaction contracts
│   ├── cli-contract.md
│   └── api-contract.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
_scripts/
├── fill_abstracts.py         # Main abstract retrieval script (CLI entry point)
├── requirements.txt          # Python dependencies (add requests/httpx, python-dotenv)
├── .env                      # API credentials (already created by user, .gitignored)
├── example_request.txt       # Scholar API example (already created by user, .gitignored)
└── tests/
    ├── test_fill_abstracts.py     # Unit and integration tests with API mocking
    └── fixtures/
        ├── sample_pub_with_abstract.md    # Test fixture
        └── sample_pub_no_abstract.md      # Test fixture
```

**Structure Decision**: Single-script project placed in `_scripts/` at the repository root, following the same pattern as feature 001 (`ingest_publications.py`). This keeps automation scripts co-located without interfering with Jekyll builds. The `.env` file for API credentials is already created by the user and is gitignored. Tests are co-located under `_scripts/tests/`. The script operates on the same `_publications/` directory and CV.numbers file as feature 001, ensuring data consistency.

## Complexity Tracking

No constitution violations. No complexity justifications required.
