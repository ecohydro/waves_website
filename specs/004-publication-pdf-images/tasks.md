# Tasks: Publication PDF Management and Image Generation

**Feature**: 004-publication-pdf-images
**Input**: Design documents from `/specs/004-publication-pdf-images/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are NOT explicitly requested in the specification. Test tasks are omitted per template guidelines.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `_scripts/` for CLI tools, `_scripts/models/` for data models, `_scripts/services/` for services
- Paths follow existing Features 001-003 structure in the repository

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [X] T001 Update _scripts/requirements.txt with new dependencies: pypdfium2>=4.0.0 and Pillow>=10.0.0
- [X] T002 Create directory structure: ensure _scripts/models/, _scripts/services/, _scripts/cli/ exist
- [X] T003 Ensure asset directories exist: assets/pdfs/publications/ and assets/images/publications/
- [X] T004 [P] Create placeholder image at assets/images/publications/placeholder.png (480x640px with "publication preview unavailable" design)
- [X] T005 [P] Configure Jekyll fallback by adding teaser: /assets/images/publications/placeholder.png to _config.yml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Create Publication model in _scripts/models/publication.py with canonical_id, title, authors, year, doi, kind fields and validation
- [X] T007 [P] Create PDFArchive model in _scripts/models/pdf_archive.py with scan(), find_pdf(), find_ambiguous(), get_coverage_stats() methods
- [X] T008 [P] Create ImageGenerationLog dataclass in _scripts/models/image_log.py for tracking operations
- [X] T009 [P] Create ScholarFetchResult dataclass in _scripts/models/scholar_result.py for PDF fetch tracking
- [X] T010 Create PDFProcessor service in _scripts/services/pdf_processor.py with render_page() using pypdfium2
- [X] T011 [P] Create ImageGenerator service in _scripts/services/image_generator.py with resize and crop operations using Pillow
- [X] T012 [P] Extend existing CV parser in _scripts/services/cv_parser.py to read Publications sheet with DOI, kind, year fields
- [X] T013 [P] Adapt Scholar API integration from _scripts/fill_abstracts.py for PDF downloads in _scripts/services/scholar_fetcher.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - PDF Archive Management (Priority: P1) 🎯 MVP

**Goal**: Audit PDF archive completeness and fetch missing required PDFs from Scholar AI

**Independent Test**: Run `python _scripts/audit_pdfs.py` to verify it reports publications with/without PDFs, categorizes by required/optional, and optionally fetches missing PDFs from Scholar AI. Verify JSON report output with `--output-report` flag.

### Implementation for User Story 1

- [X] T014 [US1] Create CLI entry point in _scripts/audit_pdfs.py with argparse setup for --numbers-file, --pdf-dir, --fetch-missing, --dry-run, --verbose, --log-file, --output-report flags
- [X] T015 [US1] Implement parse_arguments() function in _scripts/audit_pdfs.py following existing pattern from fill_abstracts.py
- [X] T016 [US1] Implement validate_inputs() function in _scripts/audit_pdfs.py to check CV.numbers exists and PDF directory accessible
- [X] T017 [US1] Implement load_publications() function in _scripts/audit_pdfs.py using cv_parser.py to read Publications sheet
- [X] T018 [US1] Implement audit_archive() function in _scripts/audit_pdfs.py to scan PDFs, match to publications, detect ambiguous files
- [X] T019 [US1] Implement generate_audit_report() function in _scripts/audit_pdfs.py to format console output with statistics and missing PDFs list
- [X] T020 [US1] Implement fetch_missing_pdfs() function in _scripts/audit_pdfs.py using scholar_fetcher.py with error handling and retry logic
- [X] T021 [US1] Implement generate_json_report() function in _scripts/audit_pdfs.py to output structured report for --output-report flag
- [X] T022 [US1] Implement main() orchestration in _scripts/audit_pdfs.py with logging setup, dry-run handling, and exit codes (0/1/2)
- [X] T023 [US1] Add batch summary report formatting for Scholar fetch failures in _scripts/audit_pdfs.py

**Checkpoint**: At this point, User Story 1 should be fully functional - audit tool works independently with fetch capability

---

## Phase 4: User Story 4 - Fallback Image Handling (Priority: P2)

**Goal**: Implement three-level image fallback (feature → preview → placeholder) in Jekyll templates

**Independent Test**: Remove a publication's images, load Jekyll site locally (`bundle exec jekyll serve`), verify fallback chain works: publications with no feature image show preview, publications with no preview show placeholder, no broken image links appear.

**Why before US2/US3**: This prevents broken layouts immediately and doesn't depend on image generation tools. US2/US3 will generate images that feed into this fallback system.

### Implementation for User Story 4

- [X] T024 [US4] Update _includes/archive-single.html to implement three-level fallback logic: check for feature image (_figure.png suffix), fall back to preview (teaser), fall back to site.teaser (placeholder)
- [X] T025 [US4] Verify _config.yml has teaser: /assets/images/publications/placeholder.png configured (should be done in T005)
- [X] T026 [US4] Test fallback chain by temporarily removing test publication images and building Jekyll site locally
- [X] T027 [US4] Document fallback logic in code comments within _includes/archive-single.html

**Checkpoint**: At this point, User Stories 1 AND 4 work independently - audit tool functions and Jekyll displays placeholders correctly

---

## Phase 5: User Story 2 - Preview Image Generation (Priority: P2)

**Goal**: Generate preview images (first page of PDF) automatically for publications

**Independent Test**: Run `python _scripts/generate_previews.py` on publications with PDFs, verify PNG images created at assets/images/publications/{id}.png with 640px height, existing images preserved unless --force flag used, batch processing skips missing PDFs.

### Implementation for User Story 2

- [X] T028 [US2] Create CLI entry point in _scripts/generate_previews.py with argparse setup for positional PUBLICATION_IDS, --numbers-file, --pdf-dir, --output-dir, --height, --force, --dry-run, --verbose, --log-file flags
- [X] T029 [US2] Implement parse_arguments() function in _scripts/generate_previews.py with support for variadic publication IDs (batch or specific)
- [X] T030 [US2] Implement validate_inputs() function in _scripts/generate_previews.py to check directories exist and are writable
- [X] T031 [US2] Implement check_existing_images() function in _scripts/generate_previews.py to skip publications with existing preview images (unless --force)
- [X] T032 [US2] Implement generate_preview_image() function in _scripts/generate_previews.py using pdf_processor.py to render page 0 and image_generator.py to resize to 640px height
- [X] T033 [US2] Implement batch_generate() function in _scripts/generate_previews.py to process all missing preview images with error handling (skip corrupted/missing PDFs)
- [X] T034 [US2] Implement single_generate() function in _scripts/generate_previews.py to process specific publication IDs with error reporting
- [X] T035 [US2] Implement format_summary_report() function in _scripts/generate_previews.py to show total scanned, generated, skipped, errors
- [X] T036 [US2] Implement main() orchestration in _scripts/generate_previews.py with logging, dry-run mode, and exit codes (0/1/2)
- [X] T037 [US2] Add progress indicators in _scripts/generate_previews.py for batch operations (log every N items)

**Checkpoint**: At this point, User Stories 1, 2, AND 4 work independently - preview images generate and display via fallback logic

---

## Phase 6: User Story 3 - Feature Image Selection and Extraction (Priority: P3)

**Goal**: Extract feature images (specific figures) from publication PDFs with crop support

**Independent Test**: Run `python _scripts/extract_feature.py Caylor2022_5678 --page 3` to verify specific page extracted as {id}_figure.png with max dimension 640px, overwrite confirmation prompts, crop coordinates work, dry-run mode previews without writing.

### Implementation for User Story 3

- [X] T038 [US3] Create CLI entry point in _scripts/extract_feature.py with argparse setup for required PUBLICATION_ID and --page, optional --pdf-dir, --output-dir, --crop, --max-dimension, --force, --no-confirm, --dry-run, --verbose, --log-file flags
- [X] T039 [US3] Implement parse_arguments() function in _scripts/extract_feature.py with required --page argument validation
- [X] T040 [US3] Implement validate_inputs() function in _scripts/extract_feature.py to check PDF exists and page number is valid (1-indexed, within bounds)
- [X] T041 [US3] Implement parse_crop_coordinates() function in _scripts/extract_feature.py to parse "x,y,width,height" string and validate bounds
- [X] T042 [US3] Implement check_overwrite_protection() function in _scripts/extract_feature.py to prompt user if feature image exists (skip if --force or --no-confirm)
- [X] T043 [US3] Implement extract_feature_image() function in _scripts/extract_feature.py using pdf_processor.py to render specified page, image_generator.py to crop (if requested) and resize to max dimension
- [X] T044 [US3] Implement calculate_resize_dimensions() function in _scripts/extract_feature.py to scale so largest dimension equals max-dimension while preserving aspect ratio
- [X] T045 [US3] Implement dry_run_preview() function in _scripts/extract_feature.py to show what would be extracted without generating image
- [X] T046 [US3] Implement main() orchestration in _scripts/extract_feature.py with logging, confirmation handling, and exit codes (0/1/2)
- [X] T047 [US3] Add detailed error messages in _scripts/extract_feature.py for invalid page numbers, crop out of bounds, PDF unreadable

**Checkpoint**: All user stories (1, 2, 3, 4) should now be independently functional - complete PDF management and image generation system

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and documentation

- [X] T048 [P] Create comprehensive README.md in _scripts/ documenting all three CLI tools with usage examples
- [X] T049 [P] Verify quickstart.md examples in specs/004-publication-pdf-images/quickstart.md work end-to-end
- [X] T050 Add detailed error handling for CV.numbers locked/inaccessible in _scripts/audit_pdfs.py
- [X] T051 Add memory-efficient handling for very large PDFs (100+ pages) in _scripts/services/pdf_processor.py by using pypdfium2 lazy page loading
- [X] T052 [P] Add logging of exact pypdfium2 and Pillow versions at tool startup for debugging
- [X] T053 [P] Document exact-match PDF naming requirement in _scripts/audit_pdfs.py help text and error messages
- [X] T054 Update CLAUDE.md recent changes section if not already updated by update-agent-context.sh script
- [X] T055 [P] Create example .env.example file documenting SCHOLAR_API_KEY requirement for --fetch-missing
- [X] T056 Verify all three CLI tools follow consistent error handling patterns from existing _scripts/fill_abstracts.py
- [X] T057 [P] Add rate limiting validation for Scholar API calls (1 second between requests) in _scripts/services/scholar_fetcher.py
- [X] T058 Test complete workflow: audit → fetch missing → generate previews → extract features → verify Jekyll display

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 4 (P2 - fallback): Can start after Foundational - No dependencies on other stories (only needs placeholder from T004)
  - User Story 2 (P2 - preview): Can start after Foundational - No dependencies on other stories (but naturally uses US1 audit to find missing)
  - User Story 3 (P3 - feature): Can start after Foundational - No dependencies on other stories
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Independently testable with audit and fetch
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Independently testable by removing images and checking Jekyll
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independently testable with any publication that has a PDF
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independently testable with any publication PDF and page number

**Note**: While US2 and US3 naturally work better after US1 (audit identifies which PDFs exist), they are technically independent and can be tested with manually added PDFs.

### Within Each User Story

- **User Story 1**: Sequential tasks (T014→T015→...→T023) building up audit_pdfs.py functionality
- **User Story 4**: Sequential template updates (T024→T025→T026→T027) for fallback logic
- **User Story 2**: Sequential tasks (T028→T029→...→T037) building up generate_previews.py functionality
- **User Story 3**: Sequential tasks (T038→T039→...→T047) building up extract_feature.py functionality

### Parallel Opportunities

**Within Setup (Phase 1)**:
- T004 (placeholder image creation) and T005 (Jekyll config) can run in parallel
- T001-T003 (directory/dependency setup) should run sequentially

**Within Foundational (Phase 2)**:
- T006, T007, T008, T009 (all model files) marked [P] can run in parallel - different files
- T011, T012, T013 (service files) marked [P] can run in parallel after T010 - different files
- T010 (pdf_processor.py) should complete first as other services may reference it

**Across User Stories**:
- Once Foundational completes, all four user stories (US1, US2, US3, US4) can start in parallel with different developers
- US1 (T014-T023), US4 (T024-T027), US2 (T028-T037), US3 (T038-T047) are completely independent

**Within Polish (Phase 7)**:
- T048, T049, T052, T053, T055, T056, T057 marked [P] can run in parallel - different files

---

## Parallel Example: Foundational Phase

```bash
# Launch all model creation together (Phase 2):
Task: "Create Publication model in _scripts/models/publication.py"
Task: "Create PDFArchive model in _scripts/models/pdf_archive.py"
Task: "Create ImageGenerationLog dataclass in _scripts/models/image_log.py"
Task: "Create ScholarFetchResult dataclass in _scripts/models/scholar_result.py"

# Then launch service files in parallel (after T010 completes):
Task: "Create ImageGenerator service in _scripts/services/image_generator.py"
Task: "Extend CV parser in _scripts/services/cv_parser.py"
Task: "Adapt Scholar API for PDFs in _scripts/services/scholar_fetcher.py"
```

---

## Parallel Example: All User Stories

```bash
# After Foundational phase completes, launch all user stories in parallel:
Task: "User Story 1 - Implement audit_pdfs.py CLI (T014-T023)"
Task: "User Story 4 - Update Jekyll fallback templates (T024-T027)"
Task: "User Story 2 - Implement generate_previews.py CLI (T028-T037)"
Task: "User Story 3 - Implement extract_feature.py CLI (T038-T047)"

# Each developer works on a different story, all proceed independently
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 4 Only)

**Minimal Viable Product**: Audit PDFs and display placeholders

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T013) - CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 - PDF Archive Management (T014-T023)
4. Complete Phase 4: User Story 4 - Fallback Image Handling (T024-T027)
5. **STOP and VALIDATE**:
   - Test audit tool with real CV.numbers file
   - Verify Scholar AI fetch works (requires .env with SCHOLAR_API_KEY)
   - Test Jekyll site displays placeholders for missing images
6. Deploy/demo if ready

**Why this MVP**: US1 provides immediate value (know what PDFs are missing) and US4 prevents broken layouts on the website. US2 and US3 can be added incrementally as time permits.

### Incremental Delivery

**Complete system built story by story**:

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (audit + fetch) → Test independently → Deploy/Demo (MVP - audit capability)
3. Add User Story 4 (fallback) → Test independently → Deploy/Demo (MVP - no broken images)
4. Add User Story 2 (preview gen) → Test independently → Deploy/Demo (visual value - preview images)
5. Add User Story 3 (feature extract) → Test independently → Deploy/Demo (full feature - curated figures)
6. Polish phase → Final refinements

Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers (all start after Phase 2 completes):

1. **Team completes Setup + Foundational together** (T001-T013)
2. **Once Foundational is done**:
   - Developer A: User Story 1 - Audit tool (T014-T023)
   - Developer B: User Story 4 - Jekyll fallback (T024-T027)
   - Developer C: User Story 2 - Preview generation (T028-T037)
   - Developer D: User Story 3 - Feature extraction (T038-T047)
3. Stories complete and integrate independently
4. Team reconvenes for Polish phase (T048-T058)

---

## Task Count Summary

- **Total Tasks**: 58
- **Setup Phase**: 5 tasks
- **Foundational Phase**: 8 tasks (blocking)
- **User Story 1 (P1)**: 10 tasks
- **User Story 4 (P2)**: 4 tasks
- **User Story 2 (P2)**: 10 tasks
- **User Story 3 (P3)**: 10 tasks
- **Polish Phase**: 11 tasks

**Parallel Opportunities**: 17 tasks marked [P] (29% of total)

**MVP Scope**: Setup + Foundational + US1 + US4 = 27 tasks (47% of total)

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are NOT included (not requested in specification)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Follow existing patterns from _scripts/fill_abstracts.py, _scripts/sync_people.py, _scripts/ingest_publications.py
- All three CLI tools (audit, preview, feature) use consistent argparse structure, logging, error handling, and exit codes
- pypdfium2 selected for PDF rendering (Apache 2.0 license, no external dependencies)
- Pillow for image processing (resize, crop, save PNG)
- Exact-match PDF naming enforced: {canonical_id}.pdf with warnings for ambiguous files
