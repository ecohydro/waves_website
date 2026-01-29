# Data Model: Scholar API Abstract Retrieval

**Branch**: `002-scholar-abstract-fill` | **Date**: 2026-01-29

## Entities

### PublicationFile (input/output, read/write)

Represents an existing publication markdown file in `_publications/`.

| Field | Source | Type | Required | Notes |
|-------|--------|------|----------|-------|
| `file_path` | Filesystem | str | yes | Absolute path to .md file (e.g., `/path/_publications/Caylor2023_4247.md`) |
| `doi` | Frontmatter `doi` field | str | no | Publication DOI, used for API queries and CV.numbers matching |
| `title` | Frontmatter `title` field | str | yes | Publication title, used for fallback API queries |
| `year` | Frontmatter `year` field | str/int | yes | Publication year, used for API queries and matching |
| `author` | Frontmatter `author` field | str | yes | Primary author name (e.g., "Kelly Caylor"), used for surname extraction |
| `author-tags` | Frontmatter `author-tags` field | list[str] | no | List of group member names, used for surname extraction |
| `body_content` | Markdown body after frontmatter | str | yes | Full body text, checked for existing abstract, updated with retrieved abstract |
| `has_abstract` | Derived from body_content | bool | yes | True if body contains `**Abstract**:` pattern |

### ScholarAPIRequest (outbound, transient)

Represents a query to the Scholar API for a single publication.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `keywords` | str | yes | URL-encoded DOI or title for structured search |
| `query` | str | yes | Natural language query (e.g., "Find the abstract of the manuscript with this doi: 10.xxxx/xxxx") |
| `sort` | str | yes | Fixed value: `"relevance"` |
| `peer_reviewed_only` | bool | yes | Fixed value: `true` |
| `generative_mode` | bool | yes | Fixed value: `true` |
| `api_key` | str | yes | Loaded from `SCHOLAR_API_KEY` environment variable |

### ScholarAPIResponse (inbound, transient)

Represents the JSON response from Scholar API.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `paper_data` | list[dict] | yes | Array of matching publications (may be empty) |
| `paper_data[].answer` | str | yes | Abstract text (generative summary) |
| `paper_data[].doi` | str | no | DOI of matched publication |
| `paper_data[].title` | str | yes | Title of matched publication |
| `paper_data[].creators` | list[str] | yes | Author names in citation format (e.g., ["A Porporato", "KK Caylor"]) |
| `paper_data[].publicationDate` | str | yes | Year as string (e.g., "2003") |
| `total_num_results` | int | yes | Number of results returned |

### CVSpreadsheetRow (input/output, read/write)

Represents a publication entry in the CV.numbers `Publications` sheet.

| Field | Source Column | Type | Required | Notes |
|-------|---------------|------|----------|-------|
| `doi` | `DOI` | str | no | DOI string or `-` if absent, used for matching with PublicationFile |
| `title` | `TITLE` | str | yes | Publication title, used for fallback matching |
| `year` | `YEAR` | int | yes | Publication year, used for matching |
| `abstract` | `Abstract` | str | no | Abstract text, updated if empty and retrieved from API |

### AbstractRetrievalResult (output, transient)

Represents the outcome of processing a single publication.

| Field | Type | Notes |
|-------|------|-------|
| `publication_file` | str | Filename (e.g., "Caylor2023_4247.md") |
| `doi` | str or None | DOI if present |
| `title` | str | Publication title |
| `year` | str/int | Publication year |
| `status` | enum | One of: `SUCCESS`, `API_ERROR`, `NO_RESULTS`, `SKIPPED_HAS_ABSTRACT`, `VALIDATION_FAILED` |
| `abstract_text` | str or None | Retrieved abstract if successful |
| `error_message` | str or None | Error details if status is API_ERROR or VALIDATION_FAILED |
| `cv_writebackSuccess` | bool | Whether CV.numbers write-back succeeded |

## Relationships

```text
PublicationFile (many) --[queries]--> ScholarAPIRequest (many)
  - One API request per publication missing an abstract
  - Request uses DOI (primary) or title+year (fallback)

ScholarAPIRequest (1) --[receives]--> ScholarAPIResponse (1)
  - Each request returns one response with 0-N results in paper_data array

ScholarAPIResponse (1) --[updates]--> PublicationFile (1)
  - Abstract text from response.paper_data[0].answer inserted into body_content

PublicationFile (1) --[matches]--> CVSpreadsheetRow (0..1)
  - Matched by DOI (primary) or title+year (fallback)
  - Match may fail if CV.numbers out of sync

CVSpreadsheetRow (1) <--[updated by]-- ScholarAPIResponse (1)
  - Abstract text written to Abstract column if empty
```

## State Transitions

### PublicationFile Processing States

```text
[File Loaded]
   |
   |--(has abstract)--> [SKIPPED]
   |
   |--(no abstract)--> [Querying API]
                          |
                          |--(3 retries exhausted)--> [API_ERROR]
                          |
                          |--(no results)--> [NO_RESULTS]
                          |
                          |--(results found)--> [Validating Abstract]
                                                   |
                                                   |--(invalid: < 50 chars)--> [VALIDATION_FAILED]
                                                   |
                                                   |--(valid)--> [Updating File]
                                                                   |
                                                                   |--(success)--> [SUCCESS]
                                                                   |
                                                                   |--(file error)--> [WRITE_ERROR]
```

### CV.numbers Write-back States

```text
[Abstract Retrieved]
   |
   |--> [Matching Row in CV.numbers]
           |
           |--(DOI match)--> [Updating Abstract Column] --> [SUCCESS] or [WRITE_ERROR]
           |
           |--(title+year match)--> [Updating Abstract Column] --> [SUCCESS] or [WRITE_ERROR]
           |
           |--(no match)--> [SKIPPED_NO_MATCH]
```

## Validation Rules

| Rule | Field | Enforcement |
|------|-------|-------------|
| Abstract minimum length | ScholarAPIResponse.paper_data[].answer | MUST contain > 50 characters (FR-015) |
| Abstract non-empty | ScholarAPIResponse.paper_data[].answer | MUST be non-empty string (FR-015) |
| DOI normalization | PublicationFile.doi, CVSpreadsheetRow.doi | Lowercase, strip `https://doi.org/` prefix for matching |
| Title normalization | PublicationFile.title, CVSpreadsheetRow.title | Lowercase, collapse whitespace via `\s+` regex |
| Year matching | ScholarAPIResponse.paper_data[].publicationDate | MUST equal PublicationFile.year as string |
| Surname matching | ScholarAPIResponse.paper_data[].creators | At least one surname from PublicationFile author list MUST appear in creators |
| Existing abstract preservation | PublicationFile.body_content | MUST NOT modify if `**Abstract**:` pattern exists (FR-008) |
| CV.numbers preservation | CVSpreadsheetRow.abstract | MUST NOT overwrite if non-empty (FR-009) |

## Query Construction Examples

### DOI-based Query (Primary)

**Input**: PublicationFile with `doi = "10.1029/2002jd002448"`

**API Request**:
```
GET /api/abstracts
?sort=relevance
&peer_reviewed_only=true
&generative_mode=true
&keywords=10.1029%2F2002jd002448
&query=Find%20the%20abstract%20of%20the%20manuscript%20with%20this%20doi%3A%2010.1029%2F2002jd002448
```

### Title+Year Query (Fallback)

**Input**: PublicationFile with `title = "Soil moisture and plant stress dynamics"`, `year = "2003"`, no DOI

**API Request**:
```
GET /api/abstracts
?sort=relevance
&peer_reviewed_only=true
&generative_mode=true
&keywords=Soil%20moisture%20and%20plant%20stress%20dynamics
&query=Find%20the%20abstract%20of%20the%20publication%20titled%20%22Soil%20moisture%20and%20plant%20stress%20dynamics%22%20published%20in%202003
```

## Abstract Insertion Format

**Existing Body Structure** (before insertion):
```markdown
![ first page ]({{ "assets/images/publications/Caylor2023_4247_figure.png" | absolute_url }}){:class="img-responsive" width="50%" .align-right}

> Caylor, K.K., Shugart, H.H., ... (2023). Title. _Journal_, doi:10.xxxx/xxxx.

[Go to the Article](https://www.doi.org/10.xxxx/xxxx){: .btn .btn--success}
```

**After Abstract Insertion**:
```markdown
![ first page ]({{ "assets/images/publications/Caylor2023_4247_figure.png" | absolute_url }}){:class="img-responsive" width="50%" .align-right}

> Caylor, K.K., Shugart, H.H., ... (2023). Title. _Journal_, doi:10.xxxx/xxxx.

**Abstract**: [Retrieved abstract text here, may be multiple sentences or paragraphs.]

[Go to the Article](https://www.doi.org/10.xxxx/xxxx){: .btn .btn--success}
```

**Insertion Logic**:
1. Split body on `\n\n` (paragraph boundaries)
2. Find blockquote paragraph (starts with `> `)
3. Insert new paragraph: `**Abstract**: {text}`
4. Preserve all other paragraphs in original order

## Summary Report Schema

**Printed to console after processing completes.**

| Field | Type | Description |
|-------|------|-------------|
| `total_scanned` | int | Number of publication files scanned |
| `skipped_has_abstract` | int | Files already containing abstracts |
| `api_calls_made` | int | Number of API requests executed (excluding retries) |
| `success_count` | int | Abstracts successfully retrieved and inserted |
| `api_error_count` | int | API failures after retry exhaustion |
| `no_results_count` | int | API returned zero results |
| `validation_failed_count` | int | Retrieved abstracts failed validation |
| `cv_writeback_success` | int | CV.numbers rows successfully updated |
| `cv_writeback_failed` | int | CV.numbers write-back failures (match not found or write error) |
| `success_files` | list[str] | Filenames successfully updated |
| `failed_files` | list[tuple(str, str)] | (filename, error_message) for failures |
