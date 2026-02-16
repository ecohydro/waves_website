# Tasks: Publication Ingestion from CV Spreadsheet

**Input**: Design documents from `/specs/001-pub-ingestion/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and directory structure

- [x] T001 Create `_scripts/` directory and `_scripts/requirements.txt` with dependencies: `numbers-parser`, `python-frontmatter`, `pyyaml`
- [x] T002 Create `_scripts/ingest_publications.py` with CLI argument parsing using `argparse`: `--dry-run` (`-n`), `--numbers-file` (`-f`), `--output-dir` (`-o`), `--authors-file` (`-a`), `--verbose` (`-v`) per contracts/cli-contract.md
- [x] T003 Implement input validation in `_scripts/ingest_publications.py`: verify Numbers file exists, output directory exists, authors file exists and is valid YAML. Exit code 1 with descriptive error messages per cli-contract.md

**Checkpoint**: Script accepts CLI arguments and validates all inputs. Running with invalid paths produces correct error messages.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data loading functions that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement `load_numbers_data()` in `_scripts/ingest_publications.py`: open CV.numbers file using `numbers-parser`, locate the "Publications" sheet by name (FR-012), read all rows via `table.rows(values_only=True)`, use first row as column headers, and return a list of row dictionaries. Handle `EmptyCell` (None) and float-to-int conversion for `YEAR` and `NUM` columns. Exit code 1 if sheet "Publications" not found.
- [x] T005 Implement `load_existing_publications()` in `_scripts/ingest_publications.py`: scan all `.md` files in `_publications/` using `python-frontmatter`, extract `doi`, `title`, `year`, and `id` from each file's YAML frontmatter. Return a set of normalized DOIs (lowercase, stripped), a set of (normalized_title, year) tuples for fallback matching, and a set of all existing integer IDs. Normalize DOIs by lowercasing and stripping `https://doi.org/` prefixes.
- [x] T006 Implement `load_author_registry()` in `_scripts/ingest_publications.py`: read `_data/authors.yml` using `PyYAML`, extract all top-level YAML keys as author names, add "Kelly Caylor" as special-case site owner. Return a set of known group member names for exact case-sensitive matching.

**Checkpoint**: All three data sources (spreadsheet, existing publications, author registry) can be loaded independently. Running with `--verbose` prints counts: "Found X publications in spreadsheet", "Found Y existing entries", "Found Z known authors".

---

## Phase 3: User Story 1 + 2 - Core Ingestion with Correct Frontmatter (Priority: P1) MVP

**Goal**: Read the CV spreadsheet, identify missing published papers, and create complete publication markdown files with all required frontmatter fields and full body content.

**Independent Test**: Run `python _scripts/ingest_publications.py` and verify new `.md` files appear in `_publications/` with correct frontmatter and body matching existing publication format.

**Note**: User Stories 1 and 2 are combined because frontmatter generation (US2) is inseparable from file creation (US1) — you cannot create a publication file without its frontmatter, and frontmatter is only useful when written to a file.

### Implementation

- [x] T007 [US1] Implement `filter_published_rows()` in `_scripts/ingest_publications.py`: filter spreadsheet rows to only those where the `Type` column equals `P`, skipping `R` (in-review) and `D` (draft) entries per FR-002. Return filtered list and count of skipped rows.
- [x] T008 [US1] Implement `find_missing_publications()` in `_scripts/ingest_publications.py`: for each published row, check if its DOI (normalized, case-insensitive) exists in the existing publications set (FR-004). If DOI is `-` or empty, fall back to case-insensitive title + year matching with normalized whitespace. Return list of rows that have no match (missing publications) and list of matched rows (skipped).
- [x] T009 [US1] Implement `generate_publication_id()` in `_scripts/ingest_publications.py`: generate a random 4-digit integer in range 1000-9999, check against the set of all existing IDs, and re-generate on collision (FR-005). Add each newly generated ID to the set to prevent intra-run collisions.
- [x] T010 [P] [US2] Implement `determine_primary_author()` in `_scripts/ingest_publications.py`: inspect group-role columns (`Undergrad Author`, `Visitor Author`, `PhD Committee Member`, `Graduate Advisee`, `Postdoctoral Advisee`, `PI Author`) per FR-014. Parse each non-empty value as an author position (e.g., `A2` → column index 2), find the role with the lowest position number, resolve the author name from the corresponding `A#` column. Cross-reference against the author registry to confirm group membership. Return the primary author name.
- [x] T011 [P] [US2] Implement `find_author_tags()` in `_scripts/ingest_publications.py`: iterate author columns `A1` through `A31` for a given row, check each non-empty name against the author registry set (exact, case-sensitive match per R3). Return a list of all matching group member names in author-position order (FR-013).
- [x] T012 [P] [US2] Implement `format_citation_name()` in `_scripts/ingest_publications.py`: convert a full name (e.g., `Kelly Caylor`) to citation format (`Caylor, K.`). Split name into parts, use last part as surname, generate initials from remaining parts. Handle edge cases: single-name authors, hyphenated surnames, multi-word first names.
- [x] T013 [US2] Implement `build_excerpt()` in `_scripts/ingest_publications.py`: generate the short citation string for the `excerpt` frontmatter field using format `"LastName, F. et al. (Year). Title. _Journal_, doi:DOI."` per data-model.md. Use first author in citation format. Omit `doi:` portion if DOI is absent.
- [x] T014 [US2] Implement `build_full_citation()` in `_scripts/ingest_publications.py`: generate the full blockquote citation listing ALL authors in citation format, plus journal, volume, issue, pages, and DOI per data-model.md. Format: `LastName1, F.M., LastName2, G., ... & LastNameN, H. (Year). Title. _Journal_, Vol(Issue), Pages, doi:DOI.` Use `&` before the last author. Omit volume/issue/pages if absent.
- [x] T015 [US2] Implement `build_frontmatter()` in `_scripts/ingest_publications.py`: assemble the complete YAML frontmatter dictionary for a publication entry per FR-007 and data-model.md field mapping. Fields: `author` (from T010), `date` (`{year}-01-01 00:00:00`), `id` (from T009), `year` (quoted string), `title`, `doi` (omit if absent), `excerpt` (from T013), `header.teaser` (`assets/images/publications/{LastName}{Year}_{id}.png`), `portfolio-item-category` (`["publications"]`), `portfolio-item-tag` (`[year, journal]`), `author-tags` (from T011).
- [x] T016 [US2] Implement `build_body_content()` in `_scripts/ingest_publications.py`: generate the markdown body per data-model.md body format. Include: image placeholder with Liquid absolute_url filter, full citation blockquote (from T014), abstract section with `**Abstract**:` prefix (omit if abstract is empty), and article link button `[Go to the Article](https://www.doi.org/{doi}){: .btn .btn--success}` (omit if no DOI).
- [x] T017 [US1] Implement `write_publication_file()` in `_scripts/ingest_publications.py`: combine frontmatter (from T015) and body (from T016) into a complete markdown file using `python-frontmatter`. Write to `_publications/{LastName}{Year}_{id}.md` per FR-006. Use the primary author's last name for the filename.
- [x] T018 [US1] Implement `check_missing_data()` in `_scripts/ingest_publications.py`: for each publication being created, check if abstract, DOI, or author list (A1) is missing per FR-015. Collect warnings as a list of `(title, year, missing_fields)` tuples. Print warnings using `⚠` format per cli-contract.md output specification.
- [x] T019 [US1] Implement the main ingestion loop in `_scripts/ingest_publications.py`: orchestrate the full pipeline — load data (T004-T006), filter published rows (T007), find missing (T008), then for each missing publication: generate ID (T009), determine author (T010), build frontmatter (T015), build body (T016), check missing data (T018), write file (T017). Track created files list for final output.

**Checkpoint**: Running `python _scripts/ingest_publications.py` reads the CV.numbers file, identifies missing publications, and creates new `.md` files in `_publications/` with complete frontmatter and body content. Running again produces no new files (idempotent). Files match the format of existing entries like `Caylor2023_4247.md`.

---

## Phase 4: User Story 3 - Dry Run / Preview Mode (Priority: P2)

**Goal**: Allow the user to preview what the ingestion would do without creating any files.

**Independent Test**: Run `python _scripts/ingest_publications.py --dry-run` and verify it lists publications that would be created without writing any files to disk.

### Implementation

- [x] T020 [US3] Implement dry-run mode in `_scripts/ingest_publications.py`: modify the main ingestion loop (T019) to check the `--dry-run` flag before writing files. When dry-run is active: skip `write_publication_file()` calls, print "DRY RUN - No files will be written" header, list each publication that would be created with format `N. LastName, F. et al. (Year) - "Title"` per cli-contract.md dry-run output spec. Print warnings and summary counts identically to standard mode but prefixed with "Would".
- [x] T021 [US3] Implement the "all up-to-date" message in `_scripts/ingest_publications.py`: when zero missing publications are found (in either standard or dry-run mode), print "All publications are up to date. No new entries needed." per cli-contract.md and exit with code 0.

**Checkpoint**: `--dry-run` accurately lists what would be created. Running `--dry-run` followed by standard mode produces identical publications. `--dry-run` writes zero files.

---

## Phase 5: User Story 4 - Duplicate Detection Report (Priority: P3)

**Goal**: Provide a summary report showing how publications were matched, created, and skipped.

**Independent Test**: Run the ingestion and verify the summary correctly reports counts and lists for matched, created, skipped, and warning categories.

### Implementation

- [x] T022 [US4] Implement `format_summary_report()` in `_scripts/ingest_publications.py`: generate the results summary per cli-contract.md output format. Include counts for: Matched (skipped), Created, Skipped (non-P), Warnings. List each warning with `⚠` prefix showing title, year, and missing field. List each newly created file path. Format counts with aligned padding.
- [x] T023 [US4] Implement exit code logic in `_scripts/ingest_publications.py`: return exit code 0 for success (all created or none needed), exit code 1 for fatal errors (file not found, parse failure), exit code 2 for partial success (some created but some had warnings) per cli-contract.md. Wire into `sys.exit()` at end of `main()`.
- [x] T024 [US4] Implement `--verbose` output in `_scripts/ingest_publications.py`: when `--verbose` flag is set, print per-row processing details: whether each spreadsheet row was matched/skipped/created, which DOI or title+year match was used, which group members were found in author columns. Print one line per row during processing.

**Checkpoint**: Summary report accurately reflects all processing outcomes. Verbose mode provides per-publication detail. Exit codes match the contract specification.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Edge case handling and robustness improvements

- [x] T025 [P] Handle special characters in `_scripts/ingest_publications.py`: ensure UTF-8 encoding for file writes, properly escape YAML special characters in titles and author names (colons, quotes, ampersands), and preserve accented characters (e.g., diacritics in author names) throughout the pipeline.
- [x] T026 [P] Handle edge case: missing `_publications/` directory in `_scripts/ingest_publications.py`. If `--output-dir` does not exist, exit with code 1 and descriptive error message rather than crashing.
- [x] T027 Validate end-to-end by running `python _scripts/ingest_publications.py --dry-run` against the actual CV.numbers file and comparing output against known existing publications in `_publications/`. Verify zero false positives (existing pubs incorrectly flagged as new) and zero false negatives (missing pubs not detected).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (T001-T003) completion — BLOCKS all user stories
- **US1+US2 (Phase 3)**: Depends on Phase 2 (T004-T006) completion
- **US3 (Phase 4)**: Depends on Phase 3 (T019) — modifies the main loop
- **US4 (Phase 5)**: Depends on Phase 3 (T019) — adds reporting to the main loop
- **Polish (Phase 6)**: Depends on Phase 3 completion; can overlap with Phase 4/5

### User Story Dependencies

- **US1 + US2 (P1)**: Can start after Foundational (Phase 2) — no other story dependencies. These are the MVP.
- **US3 (P2)**: Depends on the main ingestion loop from US1 being built (T019). Modifies that loop to conditionally skip writes.
- **US4 (P3)**: Depends on the main ingestion loop from US1 being built (T019). Adds summary formatting to the output.
- **US3 and US4** can proceed in parallel with each other after US1+US2 completes, since US3 modifies write behavior and US4 modifies output formatting in different code paths.

### Within Phase 3 (US1+US2)

- T007, T008 are sequential (filter → find missing)
- T010, T011, T012 can run in parallel (different functions, no dependencies between them)
- T013, T014 depend on T012 (citation formatting)
- T015 depends on T010, T011, T013 (assembles frontmatter from their outputs)
- T016 depends on T014 (uses full citation)
- T017 depends on T015, T016 (writes combined output)
- T018 is independent (data validation)
- T019 depends on all above (orchestration)

### Parallel Opportunities

```text
Phase 2:  T004 ──┐
          T005 ──┼── all parallel (different functions, different data sources)
          T006 ──┘

Phase 3:  T010 ──┐
          T011 ──┼── parallel (different functions, no shared state)
          T012 ──┘
                 │
          T013 ──┼── parallel (both depend on T012, different outputs)
          T014 ──┘

Phase 4+5: T020 ──┐
           T022 ──┼── parallel (US3 and US4 modify different code paths)
           T024 ──┘
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T006)
3. Complete Phase 3: US1+US2 core ingestion (T007-T019)
4. **STOP and VALIDATE**: Run against actual CV.numbers, verify new files are correct
5. This is a fully functional ingestion tool at this point

### Incremental Delivery

1. Setup + Foundational → Script runs, validates inputs, loads data
2. US1+US2 → Core ingestion works → **MVP deployed**
3. US3 → Dry-run mode added → Safety net for future runs
4. US4 → Summary reporting added → Better visibility into results
5. Polish → Edge cases and robustness → Production-ready

---

## Notes

- All tasks target a single file: `_scripts/ingest_publications.py`. Tasks marked [P] write independent functions that don't conflict.
- [Story] label maps each task to its user story for traceability.
- The spec does not request tests, so test tasks are omitted. Run the quickstart.md validation (T027) as the end-to-end verification.
- Commit after each phase or logical group of tasks completes.
- Stop at any checkpoint to validate the story independently.
