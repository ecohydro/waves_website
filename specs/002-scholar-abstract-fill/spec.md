# Feature Specification: Scholar API Abstract Retrieval

**Feature Branch**: `002-scholar-abstract-fill`
**Created**: 2026-01-29
**Status**: Draft
**Input**: User description: "Use the Scholar API (https://docs.scholarai.io/api-reference/introduction) to fill in missing data (abstracts) for publications on our website and add abstracts to the Numbers CV file as well."

## Clarifications

### Session 2026-01-29

- Q: How should Scholar API credentials be managed and stored? → A: Environment variable `SCHOLAR_API_KEY` loaded from `.env` file at runtime (already configured and .gitignored)
- Q: What delay strategy should be used to respect Scholar API rate limits? → A: Fixed 1-second delay between consecutive API requests
- Q: How should publications be matched between markdown files and CV.numbers rows for abstract write-back? → A: Match by DOI (primary) with title+year fallback (consistent with feature 001 duplicate detection)
- Q: Should transient API failures be retried? → A: Retry up to 3 times with exponential backoff (2s, 4s, 8s delays)
- Q: How should the system resolve ambiguous matches when title+year search returns multiple results? → A: Use first result matching year + any author surname from the publication's author list

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fill Missing Abstracts in Website Publications (Priority: P1)

As the site maintainer, I want to automatically retrieve missing abstracts from the Scholar API for publications on my website and update the publication markdown files with the retrieved abstracts, so that visitors can read publication summaries without visiting external sites.

**Why this priority**: This is the core value proposition. Many existing publications lack abstracts (27 warnings in the last ingestion run), and manually adding them is time-consuming. This story delivers immediate value by enriching existing content.

**Independent Test**: Can be fully tested by running the abstract retrieval tool against publications in `_publications/` that lack abstracts, verifying that the Scholar API is queried using DOI or title+year, and confirming the abstract text is added to the markdown body of each publication file.

**Acceptance Scenarios**:

1. **Given** a publication file in `_publications/` with no abstract text in the body, **When** the abstract retrieval process is run, **Then** the system queries the Scholar API using the publication's DOI, retrieves the abstract, and updates the markdown file to include the abstract in the body content.
2. **Given** a publication file has a DOI that returns an abstract from Scholar API, **When** the abstract is retrieved, **Then** the markdown file is updated with the abstract text inserted after the citation blockquote and before the article link button, following the existing format: `**Abstract**: {text}`.
3. **Given** multiple publications are missing abstracts, **When** the retrieval process is run, **Then** all publications are processed in sequence, and a summary report shows how many abstracts were successfully retrieved, how many failed, and which publications were skipped.

---

### User Story 2 - Backfill Abstracts in CV Numbers File (Priority: P2)

As the site maintainer, I want to write retrieved abstracts back to the CV.numbers spreadsheet, so that the master data source remains synchronized with the website and future ingestion runs include complete abstract data.

**Why this priority**: Keeping the CV.numbers file as the authoritative source ensures data consistency and prevents abstracts from being lost during future ingestion cycles. This is secondary to enriching the website itself but critical for long-term maintainability.

**Independent Test**: Can be tested by running the abstract retrieval tool with write-back enabled, then opening the CV.numbers file in the Numbers app and verifying that the `Abstract` column for each publication has been populated with the retrieved text.

**Acceptance Scenarios**:

1. **Given** a publication in CV.numbers has an empty `Abstract` column and the corresponding abstract was successfully retrieved from Scholar API, **When** the write-back operation is run, **Then** the `Abstract` column for that row is updated with the retrieved text.
2. **Given** a publication already has an abstract in CV.numbers, **When** the retrieval process is run, **Then** the existing abstract is preserved and not overwritten.
3. **Given** the abstract retrieval tool is run with write-back enabled, **When** the process completes, **Then** the CV.numbers file is updated on disk and the changes are reflected when opened in the Numbers app.

---

### User Story 3 - Dry Run / Preview Mode (Priority: P3)

As the site maintainer, I want to preview which abstracts would be retrieved and which publications would be updated before making any changes, so I can verify the results and avoid unintended modifications.

**Why this priority**: Provides a safety net similar to the publication ingestion tool, allowing review before modifying files.

**Independent Test**: Can be tested by running the tool in dry-run mode and verifying it reports which publications would be updated without actually modifying any files or making API calls.

**Acceptance Scenarios**:

1. **Given** the abstract retrieval tool is run in dry-run mode, **When** there are publications missing abstracts, **Then** the system displays a list of publications that would be queried (title, year, DOI) without making any API calls or file modifications.
2. **Given** the tool is run in dry-run mode, **When** there are no missing abstracts, **Then** the system reports that all publications already have abstracts.

---

### User Story 4 - Fallback Matching for Publications Without DOI (Priority: P3)

As the site maintainer, I want the system to attempt abstract retrieval using title and year for publications that lack a DOI, so that older or non-journal publications can also be enriched with abstracts.

**Why this priority**: Some publications (especially book chapters, conference papers, or older papers) lack DOIs. This expands coverage but is lower priority than the DOI-based approach which is more reliable.

**Independent Test**: Can be tested by selecting a publication without a DOI, running the retrieval tool, and verifying that the Scholar API is queried using the publication title and year instead.

**Acceptance Scenarios**:

1. **Given** a publication has no DOI but has a title and year, **When** the abstract retrieval process is run, **Then** the system queries the Scholar API using the title and year as search parameters.
2. **Given** a title+year search returns multiple results from Scholar API, **When** selecting the correct publication, **Then** the system uses the first result that matches the year and includes any author surname from the publication's author list in the result's author metadata.

---

### Edge Cases

- What happens when the Scholar API returns no results for a given DOI or title+year combination?
- What happens when the Scholar API rate limit is exceeded during batch processing?
- What happens when the Scholar API returns multiple results for a title+year query and the correct publication is ambiguous?
- What happens when a publication already has an abstract in the markdown file but not in CV.numbers?
- What happens when the CV.numbers file is locked or being edited in the Numbers app during write-back?
- How does the system handle special characters or encoding issues in abstract text retrieved from the API?
- What happens when the Scholar API is unavailable or returns an error?
- How does the system handle publications with very long abstracts (e.g., >2000 characters)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST scan all publication files in `_publications/` and identify which files lack abstract text in their body content.
- **FR-002**: System MUST query the Scholar API for each publication missing an abstract, using the DOI as the primary search parameter when available.
- **FR-003**: System MUST fall back to title+year search when a publication lacks a DOI, querying the Scholar API using the publication title and year fields from the frontmatter.
- **FR-004**: System MUST parse the Scholar API response and extract the abstract text field.
- **FR-005**: System MUST update the publication markdown file by inserting the retrieved abstract text in the body, following the existing format: `**Abstract**: {text}` positioned after the citation blockquote and before the article link button.
- **FR-006**: System MUST preserve existing markdown file structure and frontmatter when adding abstract text, only modifying the body content.
- **FR-007**: System MUST write retrieved abstracts back to the CV.numbers spreadsheet by updating the `Abstract` column for each corresponding publication row, matching publications by DOI (primary) with title+year fallback when DOI is absent.
- **FR-008**: System MUST skip publications that already have abstracts in their markdown body, avoiding redundant API calls and preserving existing content.
- **FR-009**: System MUST skip abstract write-back for publications that already have abstracts in the CV.numbers `Abstract` column, preserving existing data.
- **FR-010**: System MUST provide a dry-run mode that lists publications that would be updated without making API calls or modifying files.
- **FR-011**: System MUST report a summary after processing: number of abstracts retrieved successfully, number of API failures, number of publications skipped, and which publications were updated.
- **FR-012**: System MUST handle Scholar API errors gracefully by retrying transient failures up to 3 times with exponential backoff (2s, 4s, 8s delays), logging failures after exhausting retries, and continuing to process remaining publications rather than failing completely.
- **FR-013**: System MUST respect Scholar API rate limits by implementing a fixed 1-second delay between consecutive API requests.
- **FR-014**: System MUST log API requests and responses for debugging purposes, including which publications were queried and whether abstracts were found.
- **FR-015**: System MUST validate that retrieved abstract text is non-empty and contains reasonable content (more than 50 characters) before updating files.
- **FR-016**: System MUST use the Scholar API endpoint documented at https://docs.scholarai.io/api-reference/introduction for abstract retrieval.
- **FR-017**: System MUST load the Scholar API key from the `SCHOLAR_API_KEY` environment variable at startup and fail with a clear error message if the variable is not set.
- **FR-018**: System MUST resolve ambiguous title+year search results by selecting the first result that matches the publication year and contains any author surname from the publication's frontmatter author list in the API response author metadata.

### Key Entities

- **Publication**: Represents a research publication on the website, stored as a markdown file in `_publications/` with YAML frontmatter (doi, title, year, author) and body content (citation, abstract, article link).
- **CV Spreadsheet Row**: Represents a publication entry in the CV.numbers file, with columns including: DOI, TITLE, YEAR, Abstract, and author columns A1-A31.
- **Abstract**: Text content describing a publication's research, methodology, and findings. Retrieved from Scholar API and stored both in the website markdown file and the CV.numbers spreadsheet.
- **Scholar API Response**: JSON response from the Scholar API containing publication metadata including abstract text, matched based on DOI or title+year search parameters.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At least 80% of publications currently lacking abstracts (27 publications from the last ingestion run) have abstracts successfully retrieved and added to their markdown files.
- **SC-002**: All retrieved abstracts are accurately written back to the CV.numbers spreadsheet in the correct publication rows.
- **SC-003**: The abstract retrieval process completes for all ~170 publications within 15 minutes, respecting API rate limits.
- **SC-004**: Zero publications with existing abstracts are overwritten or modified during the retrieval process.
- **SC-005**: Users can run the tool multiple times idempotently, with subsequent runs skipping already-processed publications and completing in under 2 minutes.
- **SC-006**: The summary report accurately identifies which publications were successfully enriched, which failed, and specific error messages for failures.

## Assumptions *(mandatory)*

- The Scholar API (https://docs.scholarai.io/) provides abstract data for academic publications and supports both DOI-based and title+year search queries.
- The Scholar API returns JSON responses that include an abstract field or equivalent text content.
- The Scholar API key is stored in the `SCHOLAR_API_KEY` environment variable, loaded from a `.env` file that is excluded from version control.
- The CV.numbers file can be read and written programmatically using the same `numbers-parser` library used in feature 001-pub-ingestion.
- The `Abstract` column in the CV.numbers spreadsheet exists and is the appropriate location for storing abstract text.
- Publication markdown files follow the existing format with citation blockquote followed by abstract section followed by article link button.
- The Scholar API has reasonable rate limits that allow processing ~170 publications without requiring multi-hour batch processing windows.
- Abstract text retrieved from Scholar API is in plain text or minimal HTML that can be directly inserted into markdown files.
- The site maintainer will run this tool manually as a maintenance task, not as part of the automated publication ingestion workflow (feature 001).
- Failed abstract retrievals (API errors, no results) are acceptable and do not block processing of other publications.

## Dependencies *(include if relevant)*

- **Feature 001-pub-ingestion**: This feature assumes the publication ingestion system (001-pub-ingestion) is complete and functional, as it operates on the same `_publications/` directory structure and CV.numbers file.
- **Scholar API**: External dependency on the Scholar API service being available and returning valid responses.
- **numbers-parser library**: Same library used in feature 001 for reading and writing Apple Numbers files.
- **python-frontmatter library**: Same library used in feature 001 for parsing and modifying publication markdown files.

## Out of Scope *(include if relevant)*

- Automatic abstract retrieval during the publication ingestion workflow (feature 001). This is a separate manual maintenance task.
- Abstract quality validation or editing. The tool accepts whatever abstract text is returned by the Scholar API.
- Retrieval of other missing publication metadata (e.g., missing DOIs, author lists, volume/issue numbers).
- Integration with other academic APIs (CrossRef, PubMed, Google Scholar) beyond the specified Scholar API.
- Updating publication metadata on the website beyond abstracts.
- Version control or rollback of abstract changes. The site maintainer is responsible for committing changes via git.
- Automated scheduling or background processing. The tool is run manually by the site maintainer.
