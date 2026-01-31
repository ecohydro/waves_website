# Feature Specification: Publication PDF Management and Image Generation

**Feature Branch**: `004-publication-pdf-images`
**Created**: 2026-01-30
**Status**: Draft
**Input**: User description: "When we are creating a new publication entry, we need to be able to grab the first page of a pdf as the preview image for the item and then grab a figure from the pdf as a feature image that appears on the publication page. We need to develop a system that maintains pdfs for all the publications in my CV.numbers file and then a couple of utilities I can use to generate the necesasry images for each publication. Most already have these, so this is mainly about ensuring we have an archive of the pdfs and then developing the tools to make new images and/or fill in any missing images. While we at it, we should have a \"generic\" missing image that auto-loads if either the preview or feature images for a given publication are missing."

## Clarifications

### Session 2026-01-30

- Q: How should the system match PDF filenames to publication entries when the filename doesn't exactly match the publication ID? → A: Publications use "AuthorYear_XXXX" pattern (e.g., "Caylor2002_1378") as the canonical identifier across all files. Pattern is based on author last name (from YAML author field) + year + 4-digit random number (to avoid collisions). All associated files (PDFs, images) follow this naming pattern. These keys can be backported into CV.numbers for clarity. DOI remains the primary key for online lookups.
- Q: How should feature images be named to distinguish them from preview images? → A: Feature images use pattern `{publication_id}_figure.png` (e.g., "Caylor2002_1378_figure.png"). Preview images: 640px height (fixed), typically 480x640 aspect ratio. Feature images: max dimension 640px (usually width).
- Q: How should the system distinguish publications that legitimately have no PDF from those that are simply missing their PDF? → A: Hybrid approach based on publication year: For publications since 2022, use "kind" column from CV.numbers ("RA" = research article requires PDF and should fetch from Scholar AI if missing; "BC" = book chapter and "CP" = conference proceedings are optional, can use fallback images). For older publications (pre-2022), can use metadata flag to mark exceptions.
- Q: When the Scholar AI fetch fails to retrieve a required PDF (network error, authentication issue, or DOI not found), what should the system do? → A: Log the error with publication details, continue processing remaining publications, and generate a summary report of failures at the end
- Q: When a PDF is corrupted, password-protected, or has restricted permissions that prevent image extraction, how should the image generation tools handle this? → A: Skip image generation, log the error in the batch summary report, and rely on Jekyll's existing fallback logic to display placeholders (no frontmatter modification)
- Q: The interactive feature image tool (User Story 3, Scenario 4) mentions browsing through PDF pages. What interface should this use? → A: Mark as optional/future enhancement; defer implementation details to later phase
- Q: What should the fallback strategy be for missing feature images? → A: Use three-level fallback chain: feature image → preview image → generic placeholder. This eliminates need for separate "missing feature" placeholder
- Q: What if multiple PDFs exist in the archive that could match the same publication (e.g., "Caylor2002_1378.pdf" and "Caylor2002_1378_draft.pdf")? → A: Only use exact match (Caylor2002_1378.pdf); warn about other similar files in the report and skip if no exact match exists
- Q: How should the system handle PDFs with non-standard page sizes or orientations when generating fixed-size preview images (640px height)? → A: Scale proportionally to fit 640px height, let width vary naturally. Academic PDFs have minimal aspect ratio variation

## User Scenarios & Testing *(mandatory)*

### User Story 1 - PDF Archive Management (Priority: P1)

As a website maintainer, I need to ensure that all publications listed in my CV.numbers file have corresponding PDFs archived locally, so that I can reliably generate images and provide download links without depending on external sources.

**Why this priority**: This is foundational - without a complete PDF archive, the other features cannot function. This creates the single source of truth for publication materials.

**Independent Test**: Can be fully tested by running the PDF archive audit tool, which checks all publications from CV.numbers against the local PDF directory, reports missing PDFs, and provides a list of what needs to be acquired.

**Acceptance Scenarios**:

1. **Given** I have publications listed in CV.numbers, **When** I run the PDF archive audit, **Then** the system reports which publications have PDFs and which are missing, categorized as "required" or "optional" based on year and kind
2. **Given** I have a PDF file, **When** I add it to the archive with the correct naming convention, **Then** the system recognizes it as linked to the corresponding publication
3. **Given** multiple publications exist in the archive, **When** I request an archive status report, **Then** the system shows total count, missing count (required vs optional), and percentage complete
4. **Given** a post-2022 research article (RA) is missing its PDF, **When** I run the audit with fetch-missing flag, **Then** the system attempts to retrieve the PDF from Scholar AI using the DOI

---

### User Story 2 - Preview Image Generation (Priority: P2)

As a website maintainer, I need to automatically generate preview images (first page of PDF) for publications, so that the publications index page displays visual previews without manual image creation.

**Why this priority**: This provides immediate visual value to the website and automates a repetitive task. It depends on P1 (having PDFs) but can be tested independently once PDFs are available.

**Independent Test**: Can be tested by running the preview image generator on a publication with a PDF, verifying that a PNG image of the first page is created at the expected path, and confirming it displays correctly on the publications index page.

**Acceptance Scenarios**:

1. **Given** a publication has a PDF in the archive, **When** I run the preview image generator for that publication, **Then** a PNG image of the first page is created in the correct location
2. **Given** a publication already has a preview image, **When** I run the preview image generator with default settings, **Then** the existing image is preserved (not overwritten)
3. **Given** a publication already has a preview image, **When** I run the preview image generator with force-regenerate flag, **Then** the image is regenerated from the PDF
4. **Given** I run batch preview image generation, **When** processing multiple publications, **Then** only publications with missing preview images are processed
5. **Given** a publication has no PDF in the archive, **When** I attempt preview image generation, **Then** the system reports the missing PDF and skips that publication

---

### User Story 3 - Feature Image Selection and Extraction (Priority: P3)

As a website maintainer, I need to select and extract a specific figure from a publication PDF as the feature image, so that the publication detail page displays a compelling visual that represents the research content.

**Why this priority**: This enhances the visual appeal of individual publication pages but is lower priority than preview images because it requires human judgment to select the best figure. It can be done manually if needed.

**Independent Test**: Can be tested by running the feature image extractor with a page number parameter, verifying that the specified page is extracted as a PNG, and confirming it displays correctly on the publication detail page.

**Acceptance Scenarios**:

1. **Given** a publication has a PDF with multiple pages, **When** I run the feature image extractor with a specific page number, **Then** that page is extracted as a PNG and saved as the feature image
2. **Given** I want to extract a specific figure region, **When** I run the feature image extractor with crop coordinates, **Then** only the specified region of the page is extracted
3. **Given** a publication has an existing feature image, **When** I run the feature image extractor, **Then** I am prompted to confirm overwriting the existing image
4. **[Optional/Future]** **Given** I want to preview different pages before extraction, **When** I run the interactive feature image tool, **Then** I can browse through PDF pages and select one for extraction

---

### User Story 4 - Fallback Image Handling (Priority: P2)

As a website visitor, I need to see appropriate fallback images when a publication's images are missing, so that the page layout remains intact and professional rather than showing broken image links.

**Why this priority**: This is critical for user experience and website polish. It's ranked P2 because it should be implemented early to prevent broken layouts, but it doesn't depend on the image generation tools.

**Independent Test**: Can be tested by removing a publication's images, loading the pages, and verifying that the fallback chain works correctly (feature → preview → placeholder).

**Acceptance Scenarios**:

1. **Given** a publication has no preview image file, **When** the publications index page loads, **Then** a generic placeholder image displays
2. **Given** a publication has no feature image file but has a preview image, **When** the publication detail page loads, **Then** the preview image displays as the fallback
3. **Given** a publication has neither feature nor preview images, **When** the publication detail page loads, **Then** the generic placeholder image displays
4. **Given** the placeholder image exists in the assets directory, **When** it is referenced, **Then** it uses a path that works correctly with Jekyll's asset pipeline

---

### Edge Cases

- **Corrupted or inaccessible PDFs**: When a PDF is corrupted, password-protected, or has restricted permissions that prevent image extraction, the system skips image generation for that publication, logs the error in the batch summary report, and relies on Jekyll's three-level fallback logic to display images (feature → preview → placeholder)
- **Scholar AI fetch failures**: When Scholar AI cannot retrieve a required PDF (network error, authentication issue, DOI not found), the system logs the error with publication details, continues processing remaining publications, and generates a summary report of all failures at batch completion
- **PDF ambiguity**: When multiple PDFs exist that match the same publication pattern (e.g., "Caylor2002_1378.pdf" and "Caylor2002_1378_draft.pdf"), the system only uses exact matches (Caylor2002_1378.pdf), warns about similar files in the report, and skips publications without exact matches
- **Non-standard page sizes**: PDFs with non-standard page sizes or orientations are scaled proportionally to fit 640px height, with width varying naturally; academic PDFs typically have minimal aspect ratio variation
- **Large PDFs**: How does the system handle very large PDFs (100+ pages) during batch processing to avoid memory issues?
- **CV.numbers access**: What if the CV.numbers file is locked or inaccessible when running the audit tool?
- **Missing metadata**: What if the "kind" column is missing or has unexpected values for post-2022 publications?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read publication entries from the "Publications" sheet in CV.numbers file including canonical ID, title, authors, year, DOI, and kind (publication type)
- **FR-002**: System MUST use the "AuthorYear_XXXX" pattern as the canonical identifier to match PDFs and images to publication entries (e.g., "Caylor2002_1378.pdf" matches publication "Caylor2002_1378"); system MUST require exact filename match and skip publications when only similar files exist (e.g., "Caylor2002_1378_draft.pdf"), warning about ambiguous files in the report
- **FR-003**: System MUST provide a PDF archive audit tool that identifies which publications have corresponding PDFs and which are missing
- **FR-003a**: Audit tool MUST determine PDF requirements based on publication year and kind: for publications since 2022, "RA" (research article) requires PDF, "BC" (book chapter) and "CP" (conference proceedings) are optional; for pre-2022 publications, use metadata flag if present
- **FR-003b**: Audit tool MUST categorize missing PDFs as "required" (RA post-2022 or flagged) vs "optional" (BC/CP post-2022 or unflagged pre-2022) in its report
- **FR-003c**: System MUST provide capability to fetch missing PDFs from Scholar AI for research articles (RA) that are marked as "required" and missing from the archive; when fetch fails (network error, authentication issue, DOI not found), log error with publication details, continue processing remaining publications, and include failure in end-of-batch summary report
- **FR-004**: System MUST provide a preview image generator that extracts the first page of a PDF as a PNG image
- **FR-005**: Preview image generator MUST save images to `assets/images/publications/` using pattern `{publication_id}.png` (e.g., "Caylor2002_1378.png")
- **FR-005a**: Feature image extractor MUST save images to `assets/images/publications/` using pattern `{publication_id}_figure.png` (e.g., "Caylor2002_1378_figure.png")
- **FR-006**: Preview image generator MUST skip publications that already have preview images unless a force-regenerate flag is specified
- **FR-007**: System MUST provide a feature image extractor that extracts a specified page from a PDF as a PNG image
- **FR-008**: Feature image extractor MUST allow specifying which page number to extract
- **FR-009**: Feature image extractor MUST support optional crop coordinates to extract specific regions of a page
- **FR-010**: Feature image extractor MUST prompt for confirmation before overwriting existing feature images
- **FR-011**: System MUST provide batch processing capability to generate preview images for all publications with missing images
- **FR-012**: System MUST handle PDF processing errors gracefully (corrupted files, password protection, inaccessible files) by skipping image generation for that publication, logging errors in the batch summary report, and continuing with remaining publications; Jekyll's fallback logic will display placeholders for skipped publications
- **FR-013**: System MUST create a single generic placeholder image for publications with missing images
- **FR-014**: Jekyll templates MUST implement three-level fallback logic: (1) use feature image if present, (2) fall back to preview image if feature missing, (3) fall back to generic placeholder if both missing. For preview-only contexts (e.g., index pages), use two-level fallback: preview image → generic placeholder
- **FR-015**: System MUST generate preview images at 640px height (fixed) scaled proportionally from source with width varying naturally (typically ~480px for standard academic PDFs), and feature images with max dimension of 640px (usually width)
- **FR-016**: Generated images MUST be in PNG format for quality preservation
- **FR-017**: System MUST maintain a log of image generation operations including timestamps, success/failure status, and file paths
- **FR-017a**: System MUST generate an end-of-batch summary report for PDF fetch operations that includes all failures with publication ID, DOI, and error reason
- **FR-018**: System MUST validate that required directories exist (`assets/pdfs/publications/`, `assets/images/publications/`) before processing

### Key Entities

- **Publication Entry**: Represents a research publication from CV.numbers, with attributes including canonical ID (AuthorYear_XXXX pattern), title, authors, year, DOI, and kind (RA=research article, BC=book chapter, CP=conference proceedings). The canonical ID links to PDF file and generated images. Kind and year determine PDF requirements.
- **PDF Archive**: Collection of PDF files stored in `assets/pdfs/publications/`, each named using the AuthorYear_XXXX pattern (e.g., "Caylor2002_1378.pdf").
- **Preview Image**: PNG image extracted from the first page of a publication PDF, displayed on publications index pages. Stored in `assets/images/publications/` with naming pattern `{publication_id}.png`. Fixed height: 640px, width varies proportionally (typically ~480px for standard academic PDFs).
- **Feature Image**: PNG image extracted from a selected page/region of a publication PDF, displayed on individual publication detail pages. Stored in `assets/images/publications/` with naming pattern `{publication_id}_figure.png`. Max dimension: 640px (usually width).
- **Placeholder Image**: Generic fallback image displayed when publication-specific images are missing. Single image used across all contexts via three-level fallback chain (feature → preview → placeholder).
- **Image Generation Log**: Record of image generation operations including publication ID, operation type (preview/feature), timestamp, success status, and any error messages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: PDF archive audit completes for 100+ publications in under 30 seconds
- **SC-002**: Preview image generation processes at least 10 publications per minute
- **SC-003**: 95% of publications with PDFs successfully generate preview images without manual intervention
- **SC-004**: All publications display either a generated image or appropriate placeholder on website pages (zero broken image links)
- **SC-005**: Users can generate a missing preview image for a single publication in under 2 minutes (including tool invocation and verification)
- **SC-006**: Batch image generation for all missing previews completes for 50 publications in under 10 minutes

## Assumptions

- PDFs are stored in `assets/pdfs/publications/` directory using the AuthorYear_XXXX naming pattern
- Publication entries in CV.numbers can have the AuthorYear_XXXX identifier backported for consistent mapping
- Publication entries in CV.numbers include a "kind" column with values: RA (research article), BC (book chapter), CP (conference proceedings)
- DOI serves as the primary key for online data lookups while AuthorYear_XXXX serves as the file system identifier
- Scholar AI (existing Feature 002 integration) can be used to fetch missing PDFs for research articles using DOI
- Jekyll templates already have fields for preview images (`header.teaser`) and feature images (in page content)
- Generated images follow existing site standards: preview images at 640px height with proportional width (typically ~480px for academic PDFs), feature images at max 640px dimension
- Most publications already have images, so the tools are primarily for filling gaps and handling new publications
- The system will use Python-based tools consistent with the existing `_scripts/` infrastructure
- PDF processing will use standard Python libraries (e.g., PyMuPDF/fitz, pdf2image, Pillow)
