# Implementation Plan: People Profile Management and Enrichment

**Branch**: `003-people-profile-sync` | **Date**: 2026-01-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-people-profile-sync/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Extract people data from five CV.numbers sheets (Graduate PhD, Postdoc, Graduate MA_MS, Undergrad, Visitors) to populate and maintain the website's People page. The system will match CV entries to existing profile markdown files, merge multi-role entries into unified profiles, and enrich profiles with current professional information via web search and LinkedIn. All updates preserve manually-added content through frontmatter field tagging and present enrichment suggestions for manual review rather than auto-applying changes. The goal is "directional improvement" (60-80% automation) reducing manual data entry by ~70% while maintaining human oversight.

## Technical Context

**Language/Version**: Python 3.9+ (consistent with Features 001 and 002)
**Primary Dependencies**: numbers-parser (CV.numbers parsing), python-frontmatter (YAML frontmatter manipulation), PyYAML (config), requests (web API calls), python-dotenv (API keys), web search library (TBD in Phase 0)
**Storage**: Filesystem - CV.numbers file at `~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers`, Jekyll markdown files in `_people/` collection, web enrichment cache (format TBD in Phase 0)
**Testing**: pytest (unit tests), responses (HTTP mocking for web enrichment tests), contract tests for CV.numbers schema assumptions
**Target Platform**: macOS (developer workstation with access to CV.numbers via iCloud Drive), command-line tool execution
**Project Type**: Single project - Python CLI tool with multiple subcommands (extract, sync, enrich)
**Performance Goals**: Complete extraction and sync for typical CV file (50-100 entries across 5 sheets) in under 5 minutes; subsequent syncs under 2 minutes by skipping unchanged entries
**Constraints**: Must preserve 100% of manually-added profile content, must handle CV.numbers file locking gracefully, web API rate limits for search/LinkedIn, confidence threshold ≥0.6 for enrichment suggestions
**Scale/Scope**: ~50-100 people across 5 CV sheets, ~30-60 existing `_people/` markdown files, web enrichment for 60% of alumni (estimated 30-40 profiles)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Constitution Version**: 1.0.0 (Ratified 2026-01-29)

### Principle I: Static-First
**Status**: ✅ PASS

The feature generates static markdown files in `_people/` collection. No server-side rendering or runtime databases are introduced. The CLI tool reads CV.numbers, matches/creates/updates markdown files, and optionally enriches via web API calls, but all output is static Jekyll content. Web enrichment results are cached locally and presented for manual review, not dynamically rendered.

### Principle II: Content as Data
**Status**: ✅ PASS

Feature operates on the `_people/` Jekyll collection with structured frontmatter. Each person is a single markdown file following the existing schema. The tool adds cv_sourced tagging to distinguish data sources but maintains collection structure. No content is hard-coded into layouts or includes.

### Principle III: Standards Compliance
**Status**: ✅ PASS

Feature does not modify HTML generation, CSS, or accessibility features. It updates frontmatter fields in existing markdown files that Jekyll already renders according to theme standards. The tool preserves valid YAML frontmatter syntax and does not introduce non-standard markup.

### Principle IV: Automation & Agentic Refresh
**Status**: ✅ PASS

Feature is explicitly designed for automated content updates. CV.numbers is parsed programmatically using established naming conventions (lastname.md for people). Frontmatter schema gains cv_sourced metadata to enable safe automated updates while preserving manual content. The tool is idempotent (running sync twice produces same result if CV.numbers unchanged). Web enrichment suggestions are machine-readable and reviewable.

### Principle V: Incremental & Non-Destructive
**Status**: ✅ PASS

Feature preserves 100% of manually-added content via cv_sourced field tagging (FR-005). When CV.numbers data conflicts with manual edits, manual edits are preserved and conflicts are logged (FR-005a). New profiles are created for people not yet on site; existing profiles are updated only in cv_sourced fields. No destructive operations or forced rebuilds. Git history is preserved through normal commit workflow.

**Overall Assessment**: Feature 003 fully complies with all five constitutional principles. No violations require justification in Complexity Tracking section.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
_scripts/
├── sync_people.py           # Main CLI tool (new for Feature 003)
├── ingest_publications.py   # Feature 001
├── fill_abstracts.py        # Feature 002
└── requirements.txt         # Shared dependencies

_people/                     # Jekyll collection (modified by tool)
├── lastname.md             # One file per person
└── ...

tests/
├── test_sync_people.py     # Unit tests for CV extraction, matching, enrichment
└── fixtures/
    ├── sample_cv.numbers   # Mock CV file for testing
    └── sample_people/      # Sample markdown files
```

**Structure Decision**: Single project structure. This feature adds a new Python CLI tool to the existing `_scripts/` directory, following the pattern established by Features 001 (ingest_publications.py) and 002 (fill_abstracts.py). The tool will be named `sync_people.py` and will share the same dependency stack (numbers-parser, python-frontmatter, PyYAML).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitutional violations. This section is not applicable.

---

## Planning Deliverables

**Status**: ✅ COMPLETE

All Phase 0 and Phase 1 deliverables have been created:

### Phase 0: Outline & Research
- ✅ [research.md](./research.md) - 8 technical decisions documented
  - D1: CV.numbers sheet parsing strategy (fuzzy column matching)
  - D2: Name matching algorithm (hybrid filename + fuzzy frontmatter)
  - D3: Multi-role merging (role history list in frontmatter)
  - D4: Web search API selection (Google Custom Search API)
  - D5: Confidence scoring methodology (hybrid weighted components)
  - D6: Cache storage format (JSON files per person)
  - D7: Frontmatter field tagging mechanism (separate `_cv_metadata` dict)
  - D8: CLI subcommand structure (extract, sync, enrich)

### Phase 1: Design & Contracts
- ✅ [data-model.md](./data-model.md) - Complete entity specifications
  - Core entities: Person, Role, CVSheet, CVEntry, ProfileFile, MatchCandidate, EnrichmentSuggestion, EnrichmentCache
  - Supporting structures: CVMetadata
  - Entity relationship diagram
  - Python class definitions
  - Schema contracts

- ✅ [contracts/](./contracts/) - Schema validation contracts
  - [cv-sheet-schema.yml](./contracts/cv-sheet-schema.yml) - CV.numbers expected columns and fuzzy matching rules
  - [people-frontmatter-schema.yml](./contracts/people-frontmatter-schema.yml) - Jekyll frontmatter requirements
  - [google-search-api.yml](./contracts/google-search-api.yml) - Web enrichment API contract

- ✅ [quickstart.md](./quickstart.md) - User guide with CLI examples
  - Basic workflow (extract → sync → enrich)
  - Common use cases
  - Understanding CV-sourced vs manual fields
  - Troubleshooting guide
  - Integration with git workflow

- ✅ [CLAUDE.md](../../CLAUDE.md) - Agent context updated with Feature 003 technologies

### Phase 2: Task Breakdown
- ⏭️ Not created by `/speckit.plan` - Run `/speckit.tasks` command next

---

## Next Steps

The implementation plan is complete and ready for task breakdown. To proceed:

1. **Review planning deliverables** above and validate technical decisions
2. **Run `/speckit.tasks`** to generate dependency-ordered task breakdown in `tasks.md`
3. **Begin implementation** following the task sequence from Phase 2

**Estimated Implementation Effort** (based on similar Features 001 and 002):
- Core extraction + sync: 2-3 development sessions
- Web enrichment: 1-2 development sessions
- Testing + documentation: 1 development session
- **Total: ~4-6 development sessions**

**Key Success Metrics** (from spec.md SC-001 to SC-006):
- Extract and sync completes in < 5 minutes for typical CV (50-100 entries)
- 90% match rate between CV entries and profile files
- 60% enrichment success rate with ≥0.6 confidence
- 70% reduction in manual data entry
- 100% preservation of manually-added content
