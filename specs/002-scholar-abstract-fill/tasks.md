# Tasks: Scholar API Abstract Retrieval

**Input**: Design documents from `/specs/002-scholar-abstract-fill/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and directory structure

- [x] T001 Update `_scripts/requirements.txt` with new dependencies: `requests>=2.31.0`, `python-dotenv>=1.0.0`, `responses>=0.24.0` (test dependency)
- [x] T002 Create `_scripts/fill_abstracts.py` with CLI argument parsing using `argparse`: `--dry-run` (`-n`), `--publications-dir` (`-p`), `--numbers-file` (`-f`), `--skip-cv-writeback`, `--verbose` (`-v`), `--max-publications` (`-m`) per contracts/cli-contract.md
- [x] T003 Implement input validation in `_scripts/fill_abstracts.py`: verify publications directory exists, CV.numbers file exists (if not --skip-cv-writeback), .env file exists. Exit code 1 with descriptive error messages per cli-contract.md

**Checkpoint**: Script accepts CLI arguments and validates all inputs. Running with invalid paths produces correct error messages.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data loading and API setup functions that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement `load_api_key()` in `_scripts/fill_abstracts.py`: load SCHOLAR_API_KEY from environment using `python-dotenv`, validate non-empty, return masked key for logging (first 4 chars + `****`), exit code 1 if not found per FR-017
- [x] T005 Implement `scan_publications()` in `_scripts/fill_abstracts.py`: scan all `.md` files in `_publications/` using `python-frontmatter`, extract `doi`, `title`, `year`, `author`, `author-tags` from frontmatter, read body content, detect existing abstract via regex `r'\*\*Abstract\*\*:'`, return list of publication dictionaries with `file_path`, `has_abstract`, and frontmatter fields
- [x] T006 Implement `load_cv_numbers()` in `_scripts/fill_abstracts.py`: open CV.numbers file using `numbers-parser`, locate "Publications" sheet, read all rows with DOI, TITLE, YEAR, Abstract columns, return list of row dictionaries. Handle EmptyCell (None) and normalize DOI/title per data-model.md matching rules. Exit code 1 if sheet not found.

**Checkpoint**: All three data sources (environment, publication files, CV.numbers) can be loaded independently. Running with `--verbose` prints counts: "API key found: XXXX****", "Found X publication files, Y missing abstracts", "Found Z CV.numbers rows".

---

## Phase 3: User Story 1 - Fill Missing Abstracts in Website Publications (Priority: P1) MVP

**Goal**: Scan publication files, query Scholar API for missing abstracts using DOI or title+year, update markdown files with retrieved abstracts.

**Independent Test**: Run `python _scripts/fill_abstracts.py` against `_publications/` and verify abstracts are retrieved from Scholar API and inserted into markdown files following the format `**Abstract**: {text}` after the citation blockquote.

**Note**: User Story 1 is the core MVP. This delivers immediate value by enriching existing website content with abstracts.

### Implementation

- [x] T007 [US1] Implement `filter_missing_abstracts()` in `_scripts/fill_abstracts.py`: filter publication list (from T005) to only those where `has_abstract == False`, return list of publications needing abstracts
- [x] T008 [P] [US1] Implement `build_api_request_doi()` in `_scripts/fill_abstracts.py`: construct Scholar API request for DOI-based search per api-contract.md pattern — URL-encode DOI for `keywords` parameter, build natural language `query` string "Find the abstract of the manuscript with this doi: {DOI}", return dict with query parameters (keywords, query, sort=relevance, peer_reviewed_only=true, generative_mode=true)
- [x] T009 [P] [US1] Implement `build_api_request_title_year()` in `_scripts/fill_abstracts.py`: construct Scholar API request for title+year search per api-contract.md pattern — URL-encode title (first 100 chars) for `keywords`, build query string "Find the abstract of the publication titled \"{title}\" published in {year}", return dict with query parameters
- [x] T010 [US1] Implement `query_scholar_api()` in `_scripts/fill_abstracts.py`: make HTTP GET request to Scholar API using `requests` library, include `x-scholarai-api-key` header, implement retry logic (3 attempts with exponential backoff 2s, 4s, 8s) for transient errors (500, 429, timeouts) per FR-012, return JSON response or error. Handle permanent errors (400, 401) without retry.
- [x] T011 [US1] Implement `parse_api_response()` in `_scripts/fill_abstracts.py`: extract abstract text from Scholar API response per api-contract.md — check `total_num_results > 0`, extract `paper_data[0]['answer']`, validate non-empty and > 50 characters per FR-015, return abstract text or None with error message
- [x] T012 [P] [US1] Implement `extract_surnames()` in `_scripts/fill_abstracts.py`: extract author surnames from publication frontmatter `author` and `author-tags` fields — split names, take last word, lowercase, return list of surnames for matching (e.g., "Kelly Caylor" → ["caylor"])
- [x] T013 [US1] Implement `resolve_ambiguous_results()` in `_scripts/fill_abstracts.py`: when Scholar API returns multiple results (total_num_results > 1), select first result matching publication year (`publicationDate`) and containing any publication surname in `creators` array per FR-018, return matched result or None
- [x] T014 [US1] Implement `insert_abstract()` in `_scripts/fill_abstracts.py`: parse markdown body, locate citation blockquote (line starting with `> `), insert new paragraph `\n\n**Abstract**: {abstract_text}\n\n` after blockquote and before article link button per data-model.md format, return updated body content
- [x] T015 [US1] Implement `update_publication_file()` in `_scripts/fill_abstracts.py`: read publication file using `python-frontmatter`, update body content (from T014), preserve all frontmatter fields unchanged per FR-006, write file back with UTF-8 encoding, return success/error status
- [x] T016 [US1] Implement rate limiting in `_scripts/fill_abstracts.py`: call `time.sleep(1.0)` after each API request (successful or failed) before processing next publication per FR-013, not during retries within same publication
- [x] T017 [US1] Implement main processing loop in `_scripts/fill_abstracts.py`: orchestrate full pipeline — load API key (T004), scan publications (T005), filter missing abstracts (T007), for each missing: determine DOI vs title+year query (T008/T009), query API with retries (T010), parse response (T011), resolve ambiguous results if needed (T013), validate abstract, insert into file (T014), update file (T015), apply rate limit (T016). Track success/failure counts and file paths for summary report.
- [x] T018 [US1] Implement `format_summary_report()` in `_scripts/fill_abstracts.py`: generate results summary per cli-contract.md output format — counts for total scanned, skipped (has abstract), API calls made, success, API errors, validation failures. List newly updated file paths and failed files with error messages. Format with aligned padding.
- [x] T019 [US1] Implement exit code logic in `_scripts/fill_abstracts.py`: return exit code 0 for success (all retrieved or none needed), exit code 1 for fatal errors (missing API key, file not found), exit code 2 for partial success (some retrieved but some failed) per cli-contract.md. Wire into `sys.exit()` at end of `main()`.

**Checkpoint**: Running `python _scripts/fill_abstracts.py` scans `_publications/`, queries Scholar API for publications missing abstracts, retrieves and inserts abstract text, prints summary report. Running again skips already-processed publications (idempotent). Abstract text follows format in data-model.md.

---

## Phase 4: User Story 2 - Backfill Abstracts in CV Numbers File (Priority: P2)

**Goal**: Write retrieved abstracts back to the CV.numbers spreadsheet to maintain master data source consistency.

**Independent Test**: Run `python _scripts/fill_abstracts.py` (without `--skip-cv-writeback`), then open CV.numbers and verify the `Abstract` column is populated for publications that had abstracts retrieved.

### Implementation

- [x] T020 [US2] Implement `match_publication_to_cv_row()` in `_scripts/fill_abstracts.py`: match publication file to CV.numbers row using DOI (primary) or title+year (fallback) per FR-007 clarification — normalize DOI (lowercase, strip `https://doi.org/` prefix), normalize title (lowercase, collapse whitespace), compare year as string. Return matched row index or None.
- [x] T021 [US2] Implement `check_cv_abstract_exists()` in `_scripts/fill_abstracts.py`: check if CV.numbers row already has non-empty `Abstract` column value per FR-009, return boolean to skip write-back if abstract exists
- [x] T022 [US2] Implement `write_abstract_to_cv()` in `_scripts/fill_abstracts.py`: update CV.numbers row's `Abstract` column with retrieved abstract text using `numbers-parser`, handle file locking errors gracefully, return success/error status. Skip if `check_cv_abstract_exists()` returns True.
- [x] T023 [US2] Implement `save_cv_numbers()` in `_scripts/fill_abstracts.py`: write updated CV.numbers file back to disk, handle errors if file is locked or being edited in Numbers app, log warning but don't fail entire process
- [x] T024 [US2] Integrate CV.numbers write-back into main processing loop (T017): after successfully updating publication file, call `match_publication_to_cv_row()` (T020), check if abstract exists (T021), write abstract (T022) unless skipped by --skip-cv-writeback flag. Track CV write-back success/failure counts separately in summary report (T018).

**Checkpoint**: Running `python _scripts/fill_abstracts.py` successfully writes abstracts to CV.numbers. Running with `--skip-cv-writeback` only updates markdown files. Summary report shows "CV.numbers write-back: X successful, Y failed".

---

## Phase 5: User Story 3 - Dry Run / Preview Mode (Priority: P3)

**Goal**: Allow preview of what would be updated without making API calls or modifying files.

**Independent Test**: Run `python _scripts/fill_abstracts.py --dry-run` and verify it lists publications that would be queried without making any API calls, file modifications, or CV.numbers updates.

### Implementation

- [x] T025 [US3] Implement dry-run mode in `_scripts/fill_abstracts.py`: modify main processing loop (T017) to check `--dry-run` flag before API calls and file writes. When dry-run is active: skip `query_scholar_api()` calls, skip `update_publication_file()` calls, skip CV.numbers write-back, print "DRY RUN - No API calls will be made, no files will be modified" header, list each publication that would be queried with format "N. {filename} - \"{title}\" ({year}) [DOI: {doi} or 'no DOI']" per cli-contract.md dry-run output spec. Print summary with "Would query: X publications" and "Estimated time: ~Y seconds".
- [x] T026 [US3] Implement "all up-to-date" message in `_scripts/fill_abstracts.py`: when zero missing abstracts found (in either standard or dry-run mode), print "All publications already have abstracts. Nothing to do." per cli-contract.md and exit with code 0.

**Checkpoint**: `--dry-run` accurately lists what would be queried. Running `--dry-run` followed by standard mode produces same publication list (before standard mode processes them). `--dry-run` makes zero API calls and zero file writes.

---

## Phase 6: User Story 4 - Fallback Matching for Publications Without DOI (Priority: P3)

**Goal**: Extend abstract retrieval to publications lacking DOIs using title+year search.

**Independent Test**: Select a publication without a DOI, run abstract retrieval, and verify Scholar API is queried using title+year parameters and ambiguous results are resolved by author surname matching.

**Note**: Much of this functionality is already implemented in Phase 3 (T009, T013). This phase adds explicit routing and logging.

### Implementation

- [x] T027 [US4] Implement `determine_query_type()` in `_scripts/fill_abstracts.py`: inspect publication for DOI field — if present and non-empty, return "DOI"; if absent or empty (`-` or None), return "TITLE_YEAR" per FR-003
- [x] T028 [US4] Integrate query type routing into main loop (T017): call `determine_query_type()` (T027) before building API request, route to `build_api_request_doi()` (T008) or `build_api_request_title_year()` (T009) based on result. Log query type in verbose mode per cli-contract.md verbose output format: "API Query: doi search" or "API Query: title+year search".
- [x] T029 [US4] Enhance verbose logging in main loop: when `--verbose` flag set, print per-publication details including: filename, title (truncated to 60 chars), year, DOI (or "none"), authors, has_abstract status, query type, API response summary (N results, matched result if ambiguous), surname matching details if applicable, abstract validation status, file update status, CV.numbers match/write status per cli-contract.md verbose example

**Checkpoint**: Running script successfully retrieves abstracts for publications without DOIs using title+year search. Verbose mode shows query type and ambiguous result resolution. Summary report doesn't distinguish DOI vs title+year queries (all counted together).

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling, logging, and robustness improvements

- [x] T030 [P] Handle special characters in `_scripts/fill_abstracts.py`: ensure UTF-8 encoding for file writes (already specified in T015), properly handle Unicode characters in abstracts retrieved from API (accents, em-dashes, mathematical symbols), preserve abstract text exactly as returned by API without modification
- [x] T031 [P] Implement `--verbose` logging throughout `_scripts/fill_abstracts.py`: add detailed per-publication output per cli-contract.md when `--verbose` flag is set — API query parameters, response details, validation results, match resolution, file update status, rate limit delays. Ensure verbose mode doesn't break summary report formatting.
- [x] T032 [P] Implement `--max-publications` limit in `_scripts/fill_abstracts.py`: add early termination logic in main loop to stop after processing first N publications when `--max-publications` flag is set, useful for testing without processing entire directory. Print warning "Limiting to first N publications (--max-publications flag)" in output.
- [x] T033 Handle edge case: Scholar API unavailable in `_scripts/fill_abstracts.py`: when API returns 500 errors consistently or connection fails, exhaust retries, log error, continue to next publication rather than crashing. Summary report shows these as API errors.
- [x] T034 Handle edge case: CV.numbers file locked in `_scripts/fill_abstracts.py`: when CV.numbers is open in Numbers app during write-back, catch file locking errors gracefully, log warning "CV.numbers file may be open in Numbers app, write-back failed", continue processing, don't exit. Summary report tracks these as CV write-back failures.
- [x] T035 Validate end-to-end by running `python _scripts/fill_abstracts.py --dry-run --verbose` against actual `_publications/` directory, verify output matches expected format per cli-contract.md, confirm publications are correctly identified as missing/having abstracts, check query parameter construction for DOI and title+year examples

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001-T003) completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 (T004-T006) completion — this is the MVP
- **US2 (Phase 4)**: Depends on US1 (T017) — extends main loop with CV write-back
- **US3 (Phase 5)**: Depends on US1 (T017) — modifies main loop to conditionally skip API calls and writes
- **US4 (Phase 6)**: Depends on US1 (T008, T009, T013) — adds explicit routing and logging for title+year queries
- **Polish (Phase 7)**: Depends on US1 completion; can overlap with US2/US3/US4

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no other story dependencies. This is the MVP.
- **US2 (P2)**: Depends on US1 main loop being built (T017). Adds CV write-back feature.
- **US3 (P3)**: Depends on US1 main loop being built (T017). Adds dry-run mode.
- **US4 (P3)**: Depends on US1 query functions (T008, T009, T013). Adds routing and logging.
- **US2, US3, US4** can proceed in parallel with each other after US1 completes, since they modify different aspects (CV write-back, dry-run mode, query routing).

### Within Phase 3 (US1)

- T007 is sequential (depends on T005 output)
- T008, T009 can run in parallel (different functions, no dependencies)
- T010, T011, T012 can run in parallel (different functions)
- T013 depends on T011, T012 (uses both)
- T014, T015 can run in parallel (different functions)
- T016 is standalone (rate limiting utility)
- T017 depends on all above (orchestration)
- T018, T019 depend on T017 (reporting and exit codes)

### Parallel Opportunities

```text
Phase 2:  T004 ──┐
          T005 ──┼── all parallel (different functions, different data sources)
          T006 ──┘

Phase 3:  T008 ──┐
          T009 ──┘  parallel (different query builders)
                │
          T010 ──┐
          T011 ──┼── parallel (different functions, no shared state)
          T012 ──┘
                │
          T014 ──┐
          T015 ──┘  parallel (different functions)

Phase 7:  T030 ──┐
          T031 ──┼── parallel (different functions, cross-cutting concerns)
          T032 ──┘
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T006)
3. Complete Phase 3: US1 core abstract retrieval (T007-T019)
4. **STOP and VALIDATE**: Run against actual `_publications/`, verify abstracts retrieved and inserted correctly
5. This is a fully functional abstract retrieval tool at this point

### Incremental Delivery

1. Setup + Foundational → Script runs, loads data, validates inputs
2. US1 → Core abstract retrieval works → **MVP deployed**
3. US2 → CV write-back added → Data consistency maintained
4. US3 → Dry-run mode added → Safety net for future runs
5. US4 → Title+year queries explicitly logged → Better observability
6. Polish → Edge cases and robustness → Production-ready

---

## Notes

- All tasks target a single file: `_scripts/fill_abstracts.py`. Tasks marked [P] write independent functions that don't conflict.
- [Story] label maps each task to its user story for traceability.
- The spec does not request tests, so test tasks are omitted. Run the quickstart.md validation (T035) as the end-to-end verification.
- Commit after each phase or logical group of tasks completes.
- Stop at any checkpoint to validate the story independently.
- User has already created `.env` file with `SCHOLAR_API_KEY` and `example_request.txt` — do not recreate these.
