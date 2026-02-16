# Tasks: People Profile Management and Enrichment

**Input**: Design documents from `/specs/003-people-profile-sync/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not requested in feature specification. Test tasks are omitted per spec out-of-scope section.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Per plan.md: Single project structure with `_scripts/` at repository root for Python CLI tools, `_people/` for Jekyll collection.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [X] T001 Add new dependencies to _scripts/requirements.txt: google-api-python-client, rapidfuzz
- [X] T002 Create .env.example file in repository root with GOOGLE_CUSTOM_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID placeholders
- [X] T003 [P] Create .cache/enrichment/ directory and add to .gitignore
- [X] T004 [P] Create tests/fixtures/sample_cv.numbers mock file for testing
- [X] T005 [P] Create tests/fixtures/sample_people/ directory with sample markdown files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create _scripts/models/ directory
- [X] T007 [P] Implement Role dataclass in _scripts/models/person.py with validation rules
- [X] T008 [P] Implement Person dataclass in _scripts/models/person.py with role history management
- [X] T009 [P] Implement CVEntry dataclass in _scripts/models/cv_sheet.py with parse_years() and to_role() methods
- [X] T010 Implement CVSheet class in _scripts/models/cv_sheet.py with detect_columns() using fuzzy matching patterns from contracts/cv-sheet-schema.yml
- [X] T011 [P] Implement ProfileFile class in _scripts/models/profile_file.py with load(), save(), get_cv_sourced_fields(), is_manually_modified(), to_person() methods
- [X] T012 [P] Implement MatchCandidate dataclass in _scripts/models/match_candidate.py with confidence scoring
- [X] T013 [P] Implement EnrichmentSuggestion dataclass in _scripts/models/enrichment.py with meets_threshold(), format_for_review(), apply_to_profile() methods
- [X] T014 [P] Implement EnrichmentCache class in _scripts/models/enrichment.py with load(), save(), clear(), is_cached() methods using JSON file storage per Decision 6
- [X] T015 Create _scripts/services/ directory
- [X] T016 Implement logging configuration in _scripts/services/logger.py with file and console handlers per FR-015

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract People from CV.numbers Sheets (Priority: P1) 🎯 MVP

**Goal**: Extract people data from all five CV.numbers sheets (Graduate PhD, Postdoc, Graduate MA_MS, Undergrad, Visitors) and merge duplicate entries into unified Person objects

**Independent Test**: Run `./sync_people.py extract --dry-run` against CV.numbers and verify that all five sheets are parsed, people are extracted with name/years/degree/institution/research fields, and duplicate entries (same person in multiple sheets) are merged into single profiles with role history

### Implementation for User Story 1

- [X] T017 [P] [US1] Create CVParserService in _scripts/services/cv_parser.py with load_cv_file() method using numbers_parser.Document
- [X] T018 [US1] Implement parse_sheet() method in CVParserService that creates CVSheet, detects columns via fuzzy matching, and extracts CVEntry objects per Decision 1
- [X] T019 [US1] Implement merge_duplicates() method in CVParserService that groups CVEntry objects by person name (fuzzy matching) and merges into Person with role history per Decision 3
- [X] T020 [US1] Handle edge cases in CVParserService: missing columns (FR-007), empty rows, invalid years format, special characters in names
- [X] T021 [US1] Create CLI subcommand 'extract' in _scripts/sync_people.py with argparse setup: --numbers-file, --dry-run, --verbose flags per Decision 8
- [X] T022 [US1] Implement extract command handler that calls CVParserService and outputs summary table of extracted people (count per sheet, merged duplicates, total unique people)
- [X] T023 [US1] Add error handling for CV.numbers file locking (FR-016): wait with retry or clear error message
- [X] T024 [US1] Add logging for all extraction operations: sheets parsed, entries extracted, duplicates merged, errors encountered

**Checkpoint**: At this point, User Story 1 should be fully functional - can extract all people from CV.numbers and see structured output without needing web enrichment or file sync

---

## Phase 4: User Story 2 - Update People Page Profiles (Priority: P2)

**Goal**: Match extracted people to existing `_people/*.md` files, update CV-sourced fields while preserving manual content, create new files for people not yet on website

**Independent Test**: After running extract, run `./sync_people.py sync --dry-run` and verify that: (1) existing profiles are matched by name, (2) CV-sourced fields show proposed updates, (3) manually-added fields (bio, avatar, current_position) are preserved, (4) new profiles are created for unmatched CV entries, (5) conflicts between CV and manual edits are logged

### Implementation for User Story 2

- [X] T025 [P] [US2] Create ProfileMatcherService in _scripts/services/profile_matcher.py with find_match() method implementing hybrid matching per Decision 2
- [X] T026 [US2] Implement exact_filename_match() in ProfileMatcherService: normalize name to lowercase lastname, check if {lastname}.md exists in _people/
- [X] T027 [US2] Implement fuzzy_frontmatter_match() in ProfileMatcherService: load all _people/*.md files, parse frontmatter, use rapidfuzz for name matching with ≥0.8 threshold
- [X] T028 [US2] Implement disambiguate_by_year_degree() in ProfileMatcherService for handling multiple fuzzy matches per FR-004
- [X] T029 [P] [US2] Create ProfileSyncService in _scripts/services/profile_sync.py with sync_person() method
- [X] T030 [US2] Implement update_existing_profile() in ProfileSyncService: load ProfileFile, check _cv_metadata for cv_sourced fields, detect manual modifications per Decision 7, update only cv_sourced fields not manually modified
- [X] T031 [US2] Implement create_new_profile() in ProfileSyncService: generate ProfileFile with frontmatter from Person data, mark all fields as cv_sourced in _cv_metadata, use naming convention {lastname}.md or {firstname}-{lastname}.md if collision
- [X] T032 [US2] Implement conflict logging in ProfileSyncService when CV data differs from manually-modified cv_sourced field per FR-005a: preserve manual edit, log warning with field name, CV value, current value
- [X] T033 [US2] Implement _cv_metadata management in ProfileSyncService: add/update sourced, last_synced, conflict_logged fields per Decision 7
- [X] T034 [US2] Create CLI subcommand 'sync' in _scripts/sync_people.py with argparse setup: --people-dir, --dry-run, --verbose flags
- [X] T035 [US2] Implement sync command handler that: calls ProfileMatcherService for each Person, calls ProfileSyncService to update or create files, outputs summary (files updated, files created, conflicts logged)
- [X] T036 [US2] Add dry-run mode to ProfileSyncService per FR-014: show proposed changes without writing files
- [X] T037 [US2] Add logging for all sync operations: matches found, profiles updated, profiles created, conflicts detected
- [X] T038 [US2] Implement idempotency check in ProfileSyncService: skip update if CV data unchanged since last_synced timestamp

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - can extract from CV, sync to profile files, preserve manual content

---

## Phase 5: User Story 3 - Enrich Profiles via Web Search (Priority: P3)

**Goal**: Search web for current professional information (position, institution, LinkedIn) and present suggestions with ≥0.6 confidence for manual review

**Independent Test**: After running extract and sync, run `./sync_people.py enrich --person "Name" --dry-run` and verify that: (1) Google Custom Search API queries are made, (2) results are parsed for position/institution/LinkedIn, (3) confidence scores are calculated using hybrid algorithm, (4) only suggestions with confidence ≥0.6 are shown, (5) cached results are used if available, (6) suggestions are presented for approval but NOT auto-applied

### Implementation for User Story 3

- [X] T039 [P] [US3] Create WebSearchService in _scripts/services/web_search.py with search() method using google-api-python-client
- [X] T040 [US3] Implement API authentication in WebSearchService: load GOOGLE_CUSTOM_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID from .env using python-dotenv
- [X] T041 [US3] Implement query building in WebSearchService per Decision 4: "{name} {last_known_institution} current position" and "{name} site:linkedin.com/in"
- [X] T042 [US3] Implement error handling in WebSearchService per contracts/google-search-api.yml: quota exceeded (403), invalid key (403), rate limit (429), network timeout - use cached results as fallback
- [X] T043 [P] [US3] Create ResultParserService in _scripts/services/result_parser.py with extract_position(), extract_institution(), extract_linkedin() methods
- [X] T044 [US3] Implement position extraction in ResultParserService using regex patterns from contracts/google-search-api.yml: parse title and snippet for job titles
- [X] T045 [US3] Implement institution extraction in ResultParserService: parse displayLink (.edu domains), snippet phrases like "at [INSTITUTION]"
- [X] T046 [US3] Implement LinkedIn extraction in ResultParserService: filter for linkedin.com/in/ URLs, extract profile slug
- [X] T047 [P] [US3] Create ConfidenceScoringService in _scripts/services/confidence_scoring.py implementing hybrid algorithm per Decision 5
- [X] T048 [US3] Implement rank_score component (weight 0.4) in ConfidenceScoringService: top result = 1.0, linear decrease to 0.2 for ranks 2-5, 0.0 for rank 10+
- [X] T049 [US3] Implement name_match_score component (weight 0.3) in ConfidenceScoringService: use rapidfuzz to compare person name with result title
- [X] T050 [US3] Implement institution_match_score component (weight 0.2) in ConfidenceScoringService: exact match = 1.0, partial substring = 0.5, no match = 0.0
- [X] T051 [US3] Implement context_score component (weight 0.1) in ConfidenceScoringService: check for research keywords, degree type, co-author names in snippet
- [X] T052 [US3] Implement calculate_confidence() in ConfidenceScoringService: weighted sum of components, return score + breakdown dict
- [X] T053 [US3] Create EnrichmentService in _scripts/services/enrichment_service.py orchestrating WebSearchService, ResultParserService, ConfidenceScoringService, EnrichmentCache
- [X] T054 [US3] Implement enrich_person() in EnrichmentService: check cache first, query API if not cached or force-refresh, parse results, calculate confidence, create EnrichmentSuggestion objects, filter by ≥0.6 threshold per FR-013, save to cache
- [X] T055 [US3] Implement contextual disambiguation in EnrichmentService per FR-011: use Person.research_interests, Person.roles institution, degree year as additional context in queries
- [X] T056 [US3] Implement caching logic in EnrichmentService per FR-012: use EnrichmentCache to save results indefinitely, support --force-refresh flag to bypass cache
- [X] T057 [US3] Create CLI subcommand 'enrich' in _scripts/sync_people.py with argparse setup: --person, --force-refresh, --clear-cache, --dry-run flags
- [X] T058 [US3] Implement enrich command handler that: loads extracted people, calls EnrichmentService for each person (or specified --person), presents suggestions in interactive prompt format_for_review(), applies approved suggestions via apply_to_profile(), outputs summary (profiles enriched, suggestions approved/declined, API calls used)
- [X] T059 [US3] Implement interactive approval prompt for each EnrichmentSuggestion: show confidence score + breakdown, source URL, snippet, current value vs suggested value, ask [y/n/skip]
- [X] T060 [US3] Implement apply_to_profile() logic in EnrichmentSuggestion: update ProfileFile with suggested value, mark field as sourced=false in _cv_metadata (manually reviewed, not CV-sourced per FR-009), save file
- [X] T061 [US3] Implement graceful degradation when API unavailable per contracts/google-search-api.yml: missing key → skip enrichment with info message, quota exceeded → use cached results only
- [X] T062 [US3] Add logging for all enrichment operations: cache hits/misses, API queries, results parsed, confidence scores, suggestions approved/declined
- [X] T063 [US3] Implement --clear-cache flag handler: delete .cache/enrichment/ contents (specific person or all)

**Checkpoint**: All user stories should now be independently functional - extract → sync → enrich workflow complete

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T064 [P] Add comprehensive docstrings to all classes and methods in _scripts/models/ and _scripts/services/
- [X] T065 [P] Add input validation to CLI argument parsing in _scripts/sync_people.py: validate file paths exist, --person name is valid
- [X] T066 [P] Implement verbose logging mode that shows detailed output when --verbose flag used: column detection results, fuzzy match scores, confidence breakdowns
- [X] T067 Code cleanup: ensure all services follow single responsibility principle, extract repeated logic into utility functions
- [X] T068 [P] Performance optimization: cache ProfileFile loads in ProfileMatcherService to avoid re-parsing same files multiple times
- [X] T069 [P] Add requirements.txt version pinning for all dependencies: numbers-parser, python-frontmatter, pyyaml, requests, python-dotenv, google-api-python-client, rapidfuzz
- [X] T070 [P] Update quickstart.md with real CLI examples and command outputs from testing
- [X] T071 Security review: ensure .env file is in .gitignore, API keys never logged, web search respects privacy per FR-018
- [X] T072 Run full workflow validation per quickstart.md: extract → sync → enrich on real CV.numbers file, verify all success criteria SC-001 through SC-006

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 (P1) can start after Foundational - No dependencies on other stories
  - User Story 2 (P2) can start after Foundational - Uses Person objects from US1 but can be developed independently
  - User Story 3 (P3) can start after Foundational - Uses Person and ProfileFile from US1/US2 but can be developed independently
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Fully independent, no integration with other stories required
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 output (Person objects) but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrates with US1/US2 output (Person, ProfileFile) but independently testable

### Within Each User Story

- Models before services (T006-T014 before T017+)
- Services follow logical data flow:
  - US1: CVParserService extracts → outputs Person objects
  - US2: ProfileMatcherService matches → ProfileSyncService syncs
  - US3: WebSearchService queries → ResultParserService parses → ConfidenceScoringService scores → EnrichmentService orchestrates
- CLI implementation after services complete
- Logging and error handling added as services are implemented

### Parallel Opportunities

- **Phase 1 (Setup)**: T002, T003, T004, T005 can all run in parallel (different files/directories)
- **Phase 2 (Foundational)**: T007-T014, T016 can all run in parallel (different model/service files)
- **User Story 1**: T017, T021, T024 can run in parallel once dependencies (CVSheet, Person models) are complete
- **User Story 2**: T025, T029 can start in parallel after foundational models complete; T034, T037 can run in parallel after services complete
- **User Story 3**: T039, T043, T047 can all run in parallel (different service files); T057, T062 can run in parallel after services complete
- **Polish**: T064, T065, T066, T068, T069, T070, T071 can all run in parallel (different concerns)

---

## Parallel Example: User Story 1

```bash
# After foundational models are complete, launch in parallel:
Task T017: "Create CVParserService in _scripts/services/cv_parser.py"
Task T021: "Create CLI subcommand 'extract' in _scripts/sync_people.py"
Task T024: "Add logging for all extraction operations"

# These work on different files and have no dependencies on each other
```

## Parallel Example: User Story 3

```bash
# After foundational models are complete, launch in parallel:
Task T039: "Create WebSearchService in _scripts/services/web_search.py"
Task T043: "Create ResultParserService in _scripts/services/result_parser.py"
Task T047: "Create ConfidenceScoringService in _scripts/services/confidence_scoring.py"

# All three services are independent and can be developed simultaneously
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T016) - **CRITICAL - blocks all stories**
3. Complete Phase 3: User Story 1 (T017-T024)
4. **STOP and VALIDATE**: Test extraction independently
   - Run `./sync_people.py extract --verbose` against real CV.numbers
   - Verify all 5 sheets parsed, people extracted, duplicates merged
   - Check SC-001 (< 5 minutes for 50-100 entries)
5. Deploy/demo if ready - **MVP delivers extraction capability**

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → **MVP Demo** (extraction working)
3. Add User Story 2 → Test independently → **Demo** (extraction + sync working, SC-002 90% match rate)
4. Add User Story 3 → Test independently → **Demo** (full workflow, SC-003 60% enrichment success)
5. Complete Polish → Final release with all success criteria met

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T016)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (T017-T024) - CV extraction
   - **Developer B**: User Story 2 (T025-T038) - Profile sync
   - **Developer C**: User Story 3 (T039-T063) - Web enrichment
3. Stories complete and integrate independently
4. Team reconvenes for Polish (T064-T072)

### Success Criteria Validation Points

- **After US1**: Test SC-001 (< 5 minutes extraction)
- **After US2**: Test SC-002 (90% match rate), SC-005 (70% reduction in manual entry), SC-006 (100% manual content preserved)
- **After US3**: Test SC-003 (60% enrichment success)
- **After all stories**: Test SC-004 (< 2 minutes subsequent syncs)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable per spec.md
- Tests are NOT included per feature specification (not explicitly requested)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All file paths are absolute or relative to repository root per plan.md structure
- Focus on "directional improvement" (60-80% automation) not 100% hands-free per spec assumptions
