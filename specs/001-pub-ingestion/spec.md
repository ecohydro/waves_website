# Feature Specification: Publication Ingestion from CV Spreadsheet

**Feature Branch**: `001-pub-ingestion`
**Created**: 2026-01-29
**Status**: Draft
**Input**: User description: "Develop an ingestion system that reads data from the Publications sheet in my CV.numbers file (in iCloud) and then creates new publication entries for missing publications."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ingest New Publications from CV (Priority: P1)

As the site maintainer, I want to run an ingestion process that reads the Publications sheet from my CV.numbers file stored in iCloud, compares those entries against the existing publication files on the website, and automatically creates new publication entries for any publications that are missing from the site.

**Why this priority**: This is the core feature. Without the ability to read the spreadsheet and generate new entries, no other functionality matters. This directly eliminates the manual effort of creating publication markdown files by hand.

**Independent Test**: Can be fully tested by running the ingestion tool against the CV.numbers file and verifying that new markdown files appear in the `_publications/` directory with correct frontmatter and content structure matching the existing publication format.

**Acceptance Scenarios**:

1. **Given** the CV.numbers file contains publications not present in `_publications/`, **When** the ingestion process is run, **Then** new publication markdown files are created in `_publications/` for each missing publication, following the existing naming convention (`{LastName}{Year}_{id}.md`).
2. **Given** the CV.numbers file contains publications that already exist in `_publications/`, **When** the ingestion process is run, **Then** those existing publications are skipped and not duplicated or overwritten.
3. **Given** the CV.numbers file is accessible at its iCloud path, **When** the ingestion process is run, **Then** the system reads the Publications sheet without requiring the user to manually export or convert the file.

---

### User Story 2 - Correct Frontmatter Generation (Priority: P1)

As the site maintainer, I want each newly created publication entry to contain all required frontmatter fields (author, date, id, year, title, doi, excerpt, header teaser, portfolio-item-category, portfolio-item-tag, author-tags) so that the publication renders correctly on the Jekyll site without manual editing.

**Why this priority**: Publication entries without correct frontmatter will not display properly on the site, making the ingestion useless without this capability.

**Independent Test**: Can be tested by inspecting generated markdown files and verifying all frontmatter fields are present and correctly formatted, then building the Jekyll site to confirm publications render.

**Acceptance Scenarios**:

1. **Given** a new publication is ingested from the spreadsheet, **When** the markdown file is created, **Then** it contains all required frontmatter fields: `author`, `date`, `id`, `year`, `title`, `doi`, `excerpt`, `header.teaser`, `portfolio-item-category`, `portfolio-item-tag`, and `author-tags`.
2. **Given** a publication has a DOI in the spreadsheet, **When** the entry is created, **Then** the body content includes a link to the article using the DOI.
3. **Given** a publication entry is created, **When** the excerpt field is generated, **Then** it follows the existing citation format: `"LastName, F. et al. (Year). Title. _Journal_, doi:DOI."`.

---

### User Story 3 - Dry Run / Preview Mode (Priority: P2)

As the site maintainer, I want to preview what the ingestion would do before it creates any files, so I can verify the results and catch any issues before committing changes.

**Why this priority**: Provides a safety net that prevents unintended file creation and lets the user review output before modifying the site.

**Independent Test**: Can be tested by running the ingestion in preview mode and verifying that it reports what would be created without actually writing any files to disk.

**Acceptance Scenarios**:

1. **Given** the ingestion tool is run in preview mode, **When** there are missing publications, **Then** the system displays a summary of publications that would be created (title, authors, year) without writing any files.
2. **Given** the ingestion tool is run in preview mode, **When** there are no missing publications, **Then** the system reports that all publications are already up to date.

---

### User Story 4 - Duplicate Detection Report (Priority: P3)

As the site maintainer, I want to see a summary of how publications were matched between the spreadsheet and existing files, so I can identify any matching errors or data discrepancies.

**Why this priority**: Useful for ongoing maintenance and data hygiene, but the core ingestion works without it.

**Independent Test**: Can be tested by running the ingestion and verifying the summary report accurately lists matched, skipped, and newly created publications.

**Acceptance Scenarios**:

1. **Given** the ingestion process completes, **When** the summary is displayed, **Then** it shows counts and lists of: publications matched to existing entries, publications newly created, and any publications that could not be processed (with reasons).

---

### Edge Cases

- What happens when the CV.numbers file is not found at the expected iCloud path (e.g., not synced, renamed, or moved)?
- What happens when a publication row in the spreadsheet is missing required fields (e.g., no title, no DOI, no author)?
- What happens when the spreadsheet contains a publication with the same title and year as an existing entry but different metadata (e.g., updated DOI)?
- What happens when the `_publications/` directory does not exist?
- How does the system handle special characters in publication titles or author names (e.g., accented characters, em-dashes)?
- What happens when the spreadsheet contains multiple sheets and the Publications sheet must be identified among them?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read the Publications sheet from the Apple Numbers file located at `~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers`.
- **FR-002**: System MUST extract publication data from the spreadsheet rows, including at minimum: title, authors, year, journal name, and DOI. System MUST only ingest rows where the `Type` column is `P` (Published), skipping in-review (`R`) and draft (`D`) entries.
- **FR-003**: System MUST compare extracted publications against existing files in the `_publications/` directory to identify which publications are missing from the site.
- **FR-004**: System MUST match publications using DOI as the primary identifier when available, falling back to title-and-year matching when DOI is absent.
- **FR-005**: System MUST generate a unique numeric ID for each new publication entry that does not conflict with existing publication IDs.
- **FR-006**: System MUST create new markdown files following the existing naming convention: `{FirstAuthorLastName}{Year}_{id}.md`.
- **FR-007**: System MUST generate complete YAML frontmatter for each new publication, including all fields used by the existing Jekyll collection: `author`, `date`, `id`, `year`, `title`, `doi`, `excerpt`, `header.teaser`, `portfolio-item-category`, `portfolio-item-tag`, and `author-tags`.
- **FR-008**: System MUST generate the full markdown body content following the existing publication format: a citation blockquote listing all authors, journal name, volume, issue, pages, and DOI; the abstract text; and a link to the article via DOI.
- **FR-009**: System MUST support a preview/dry-run mode that reports what would be created without writing files.
- **FR-010**: System MUST report a summary of results after ingestion, showing counts of matched, created, and skipped publications.
- **FR-011**: System MUST handle publications with missing optional fields gracefully, creating entries with available data and leaving optional fields empty rather than failing.
- **FR-015**: System MUST alert the user when critical data is missing (abstract, DOI, or author list) for a publication being added, clearly identifying which publication and which fields are absent.
- **FR-012**: System MUST identify the correct sheet within the Numbers file by sheet name ("Publications") rather than assuming sheet position.
- **FR-013**: System MUST recognize group member authors by cross-referencing against the existing `_data/authors.yml` file to populate the `author-tags` field.
- **FR-014**: System MUST determine the primary `author` frontmatter field by inspecting the group-role columns (`Undergrad Author`, `Visitor Author`, `PhD Committee Member`, `Graduate Advisee`, `Postdoctoral Advisee`, `PI Author`), selecting the role with the lowest (earliest) author position number (e.g., `A1` before `A7`), and resolving the name from the corresponding author column.

### Key Entities

- **CV Spreadsheet**: The Apple Numbers file containing the Publications sheet. Columns include publication metadata such as title, authors, year, journal, and DOI. Located in iCloud at a known file path.
- **Publication Entry**: A Jekyll collection markdown file in `_publications/` with YAML frontmatter and body content. Each entry represents one academic publication and is identified by a unique numeric ID.
- **Author Registry**: The `_data/authors.yml` file containing known group members. Used to determine which authors to tag in the `author-tags` frontmatter field.
- **Publication ID**: A unique numeric identifier assigned to each publication, used in the filename and frontmatter. Must not conflict with any existing publication IDs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All publications present in the CV spreadsheet but absent from the website are successfully ingested and added as properly formatted publication entries.
- **SC-002**: Zero duplicate publication entries are created when the ingestion is run multiple times against the same spreadsheet.
- **SC-003**: 100% of generated publication entries contain all required frontmatter fields and render correctly when the Jekyll site is built.
- **SC-004**: The ingestion process can be completed by running a single command, with no manual file editing required for standard publications.
- **SC-005**: The preview mode accurately reports all publications that would be created, with zero discrepancies between preview output and actual ingestion results.
- **SC-006**: Group member authors are correctly identified and tagged in at least 95% of new publication entries.

## Clarifications

### Session 2026-01-29

- Q: Which publication types from the spreadsheet should be ingested? → A: Only published (`P`) entries. In-review (`R`) and draft (`D`) entries are skipped.
- Q: How should the primary `author` frontmatter field be determined? → A: Check all group-role columns (`Undergrad Author`, `Visitor Author`, `PhD Committee Member`, `Graduate Advisee`, `Postdoctoral Advisee`, `PI Author`), each containing an author position (e.g., `A1`, `A7`). Select the role with the lowest (earliest) author position number, then resolve the author name from the corresponding `A#` column. That person becomes the `author` field. If only the PI appears (e.g., `PI Author` = `A7`), the PI is the author.
- Q: Should ingestion populate full body content from spreadsheet data? → A: Yes. Generate the complete body: citation blockquote (all authors, journal, volume, pages, DOI) + abstract + article link. Alert the user when critical data (abstract, DOI, or author list) is missing for a publication being added.

## Assumptions

- The CV.numbers file is stored at `~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers` and is accessible from the local filesystem (iCloud Drive is enabled and synced).
- The Publications sheet within the Numbers file has a consistent tabular structure with column headers for publication metadata.
- Each publication in the spreadsheet has at least a title and year; DOI is present for most but may be absent for some entries.
- The existing `_data/authors.yml` file contains current group members and is the source of truth for author matching.
- Teaser images for new publications will use a placeholder or default image path, as the spreadsheet does not contain image data.
- The ingestion tool will be run locally on the same machine where the iCloud-synced Numbers file resides.
- The existing publication file naming convention (`{LastName}{Year}_{id}.md`) and frontmatter schema will remain stable.
