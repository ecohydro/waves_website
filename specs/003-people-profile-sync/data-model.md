# Data Model: People Profile Management and Enrichment

**Feature**: 003-people-profile-sync
**Created**: 2026-01-29
**Status**: Phase 1 - Design

## Overview

This document defines the data entities and their relationships for the people profile synchronization system. The model supports extraction from CV.numbers, matching to Jekyll profile files, multi-role merging, and web enrichment.

## Entity Relationship Diagram

```
┌─────────────┐
│  CVSheet    │
│  (5 sheets) │
└──────┬──────┘
       │ contains
       │ 1..*
       ▼
┌─────────────┐      matches to      ┌──────────────┐
│  CVEntry    │◄────────────────────►│ ProfileFile  │
│ (one person,│     MatchCandidate   │ (markdown)   │
│  one role)  │                      └──────────────┘
└──────┬──────┘                             │
       │                                    │
       │ merges into                        │ represents
       │ 1..*                               │ 1..1
       ▼                                    ▼
┌─────────────┐      enriches       ┌──────────────┐
│   Person    │◄────────────────────│ Enrichment   │
│ (unified    │   EnrichmentSuggestion│  Service   │
│  profile)   │                      └──────────────┘
└─────────────┘
```

## Core Entities

### Person

**Purpose**: Unified representation of an individual affiliated with the research group, combining data from multiple CV.numbers entries (if applicable) and profile file.

**Attributes**:
- `name` (str): Full name (e.g., "Kelly O'Donnell")
- `firstname` (str): First name
- `lastname` (str): Last name (used for filename matching)
- `roles` (list[Role]): Chronologically ordered list of affiliations (see Role sub-entity)
- `current_position` (str | None): Most recent job title (manually added or enriched)
- `current_institution` (str | None): Most recent affiliation (manually added or enriched)
- `linkedin_url` (str | None): LinkedIn profile URL (manually added or enriched)
- `research_interests` (list[str]): Keywords or phrases describing research areas
- `email` (str | None): Contact email
- `avatar` (str | None): Path to profile photo in `assets/images/people/`
- `bio` (str | None): Custom biography text (Markdown)
- `publications` (list[str]): Publication IDs (links to `_publications/`)
- `alumni_status` (bool): True if no longer active in lab
- `profile_file_path` (str | None): Path to corresponding `_people/*.md` file
- `cv_metadata` (dict): Metadata for cv_sourced field tracking (see CVMetadata sub-entity)

**Derived Fields**:
- `most_recent_role`: Last item in `roles` list
- `years_active`: Range from earliest role start to latest role end

**Validation Rules**:
- At least one role must be present
- If `alumni_status` is False, at least one role must have end_year ≥ current year - 1
- `avatar` path must exist in `assets/images/people/` if specified
- `linkedin_url` must match pattern `https://www.linkedin.com/in/*` if specified

### Role

**Purpose**: Represents one affiliation period (e.g., PhD student, Postdoc) for a Person. Sub-entity of Person.

**Attributes**:
- `type` (str): Role category - one of ["Graduate PhD", "Graduate MA/MS", "Postdoc", "Undergrad", "Visitor"]
- `start_year` (int | None): Year affiliation began
- `end_year` (int | None): Year affiliation ended (None if ongoing)
- `degree` (str | None): Degree earned (e.g., "PhD", "MS", None for Postdoc/Visitor)
- `institution` (str | None): Institution where affiliation occurred (defaults to lab's home institution)
- `research_focus` (str | None): Specific research area during this role

**Validation Rules**:
- `end_year` must be ≥ `start_year` if both specified
- If `type` is "Graduate PhD", `degree` should be "PhD"
- If `type` is "Graduate MA/MS", `degree` should be "MS" or "MA"

**Display Format**:
- "Graduate PhD (2015-2020): Climate modeling in East Africa"
- "Postdoc (2020-2022)"

### CVSheet

**Purpose**: Represents one of the five sheets in CV.numbers file with its schema and parsing configuration.

**Attributes**:
- `name` (str): Sheet name - one of ["Graduate PhD", "Postdoc", "Graduate MA_MS", "Undergrad", "Visitors"]
- `table_index` (int): Zero-based index of table within sheet (usually 0)
- `column_mapping` (dict[str, int | None]): Maps standard field names to column indices
  - Standard fields: `name`, `years`, `degree`, `institution`, `research`
- `entries` (list[CVEntry]): Parsed entries from this sheet

**Methods**:
- `detect_columns(header_row: list[str]) -> dict[str, int | None]`: Fuzzy match header row to standard field names (see Decision 1 in research.md)
- `parse_entries() -> list[CVEntry]`: Extract all rows as CVEntry objects

**Validation Rules**:
- `name` field column must be present (required)
- Other columns optional; missing columns logged as warnings

### CVEntry

**Purpose**: Represents one row from a CV.numbers sheet (one person, one role). Intermediate format before merging into Person.

**Attributes**:
- `sheet_name` (str): Source sheet (e.g., "Graduate PhD")
- `name` (str): Person name as appears in CV
- `years` (str | None): Years active (e.g., "2015-2020", "2018-present")
- `degree` (str | None): Degree type (e.g., "PhD", "MS")
- `institution` (str | None): Affiliation
- `research` (str | None): Research focus/area
- `row_index` (int): Row number in original sheet (for logging)

**Methods**:
- `parse_years() -> tuple[int | None, int | None]`: Extract start_year, end_year from years string
- `to_role() -> Role`: Convert to Role object for merging into Person

**Validation Rules**:
- `name` must not be empty
- If `years` contains invalid format, log warning and set to None

### ProfileFile

**Purpose**: Represents a Jekyll markdown file in `_people/` directory.

**Attributes**:
- `file_path` (str): Absolute path to markdown file (e.g., `_people/odonnell.md`)
- `frontmatter` (dict): Parsed YAML frontmatter
- `body` (str): Markdown content below frontmatter
- `last_modified` (datetime): File modification timestamp
- `exists` (bool): True if file exists on disk

**Methods**:
- `load() -> ProfileFile`: Read file from disk, parse frontmatter + body
- `save(dry_run: bool = False)`: Write frontmatter + body back to disk (skip if dry_run)
- `get_cv_sourced_fields() -> list[str]`: Return list of field names marked cv_sourced in `_cv_metadata`
- `is_manually_modified(field: str, new_value: any) -> bool`: Check if cv_sourced field was manually edited since last sync (compare timestamp or value hash)
- `to_person() -> Person`: Convert frontmatter to Person object

**Validation Rules**:
- Frontmatter must be valid YAML
- Required frontmatter fields per constitution: `author`, `avatar`, `excerpt`, `title`, `portfolio-item-category`, `portfolio-item-tag`, `date`
- File must follow naming convention: `{lastname}.md` or `{firstname}-{lastname}.md`

### MatchCandidate

**Purpose**: Represents a potential link between a CVEntry and a ProfileFile, with confidence score.

**Attributes**:
- `cv_entry` (CVEntry): Entry from CV.numbers
- `profile_file` (ProfileFile | None): Matched profile file (None if no match)
- `match_type` (str): How match was made - one of ["exact_filename", "fuzzy_name", "year_degree_disambiguated", "no_match"]
- `confidence` (float): Match confidence 0.0-1.0 (1.0 for exact, < 1.0 for fuzzy)
- `notes` (str): Human-readable explanation of match (e.g., "Fuzzy name match: 'O\'Donnell' vs 'ODonnell', score 0.87")

**Methods**:
- `is_match() -> bool`: Returns True if match_type != "no_match"
- `requires_manual_review() -> bool`: Returns True if confidence < 0.9

**Validation Rules**:
- `confidence` must be in range [0.0, 1.0]
- If `match_type` is "no_match", `profile_file` must be None

### EnrichmentSuggestion

**Purpose**: Proposed update to a Person's profile based on web search results.

**Attributes**:
- `person_name` (str): Name of person being enriched
- `profile_file_path` (str): Path to profile file
- `field` (str): Field to update - one of ["current_position", "current_institution", "linkedin_url"]
- `current_value` (str | None): Existing value in profile (if any)
- `suggested_value` (str): Proposed new value from web search
- `source_url` (str): URL where information was found
- `source_snippet` (str): Relevant text snippet from source
- `confidence` (float): Overall confidence score 0.0-1.0
- `confidence_breakdown` (dict[str, float]): Component scores (see Decision 5 in research.md)
  - `rank_score`: Based on search result position
  - `name_match_score`: Name similarity
  - `institution_match_score`: Institution keyword match
  - `context_score`: Research area / co-author signals
- `timestamp` (datetime): When suggestion was generated
- `query` (str): Search query that produced this result

**Methods**:
- `meets_threshold() -> bool`: Returns True if confidence ≥ 0.6 (FR-013)
- `format_for_review() -> str`: Human-readable summary for manual review
- `apply_to_profile(profile: ProfileFile)`: Update profile with suggested value (marks field as enriched, not cv_sourced)

**Validation Rules**:
- `confidence` must be in range [0.0, 1.0]
- `confidence_breakdown` values must sum to ≤ confidence
- `source_url` must be valid HTTP(S) URL

### EnrichmentCache

**Purpose**: Stores web search results to avoid redundant API calls.

**Attributes**:
- `cache_dir` (str): Path to cache directory (e.g., `.cache/enrichment/`)
- `cache_files` (dict[str, str]): Map of person names to cache file paths

**Methods**:
- `load(person_name: str) -> list[EnrichmentSuggestion] | None`: Load cached suggestions for person
- `save(person_name: str, suggestions: list[EnrichmentSuggestion])`: Write suggestions to cache
- `clear(person_name: str | None)`: Delete cache for specific person or all if None
- `is_cached(person_name: str) -> bool`: Check if person has cached results
- `get_cache_age(person_name: str) -> timedelta`: How long since cache was created

**File Format**: JSON per Decision 6 in research.md
```json
{
  "person_name": "John Doe",
  "person_file": "_people/doe.md",
  "last_updated": "2026-01-29T10:30:00Z",
  "suggestions": [
    {
      "field": "current_position",
      "suggested_value": "Associate Professor",
      "source_url": "https://...",
      "confidence": 0.85,
      "confidence_breakdown": {...}
    }
  ]
}
```

## Supporting Data Structures

### CVMetadata

**Purpose**: Tracks which frontmatter fields are CV-sourced vs manually added. Sub-entity stored in `_cv_metadata` frontmatter field.

**Structure** (dict):
```python
{
  "field_name": {
    "sourced": bool,  # True if CV-sourced, False if manual
    "last_synced": str,  # ISO timestamp of last sync
    "conflict_logged": bool,  # True if manual edit conflict was logged
  }
}
```

**Example**:
```yaml
_cv_metadata:
  title:
    sourced: true
    last_synced: "2026-01-29T10:30:00Z"
    conflict_logged: false
  roles:
    sourced: true
    last_synced: "2026-01-29T10:30:00Z"
    conflict_logged: false
  current_position:
    sourced: false  # manually added
    last_synced: null
    conflict_logged: false
```

## Data Flow

### Extract Flow (CVSheet → CVEntry → Person)

1. Load CV.numbers file using `numbers_parser.Document`
2. For each of 5 sheets:
   - Create `CVSheet` object
   - Detect columns using fuzzy matching
   - Parse all rows into `CVEntry` objects
3. Group `CVEntry` objects by person name (fuzzy matching)
4. For entries with same person name:
   - Merge into single `Person` object
   - Convert each `CVEntry` to `Role` and append to `Person.roles`
   - Sort roles chronologically

### Sync Flow (Person → ProfileFile)

1. For each `Person` from extraction:
   - Create `MatchCandidate` by searching for existing `ProfileFile`
   - If match found:
     - Load existing `ProfileFile`
     - Check `_cv_metadata` for cv_sourced fields
     - For each cv_sourced field, check if manually modified (FR-005a)
     - Update cv_sourced fields that haven't been manually modified
     - Preserve all non-cv_sourced fields
   - If no match:
     - Create new `ProfileFile`
     - Populate frontmatter from `Person` data
     - Mark all fields as cv_sourced
   - Save `ProfileFile` (unless dry-run)

### Enrich Flow (Person → EnrichmentSuggestion → ProfileFile)

1. For each `Person` (or selected person):
   - Check `EnrichmentCache` for existing results
   - If not cached or force-refresh:
     - Query Google Custom Search API with person name + institution
     - Parse search results into candidate updates (position, affiliation, LinkedIn)
     - Calculate confidence scores using hybrid methodology
     - Filter results with confidence < 0.6
     - Create `EnrichmentSuggestion` objects for top 3 matches
     - Save to `EnrichmentCache`
   - Present suggestions to user for manual review
   - On user approval:
     - Load `ProfileFile`
     - Apply suggestion (updates field, marks as NOT cv_sourced in `_cv_metadata`)
     - Save `ProfileFile`

## Schema Contracts

### People Frontmatter Schema (Existing)

**Required fields per constitution**:
- `author`: Person name (string)
- `avatar`: Path to profile photo (string)
- `excerpt`: Short bio for listing pages (string)
- `title`: Full name or title for page (string)
- `portfolio-item-category`: Category tags (list)
- `portfolio-item-tag`: Item tags (list)
- `date`: Profile creation date (string, YYYY-MM-DD)

**Additional fields from this feature**:
- `roles`: List of Role dictionaries (added by this feature)
  ```yaml
  roles:
    - type: "Graduate PhD"
      start_year: 2015
      end_year: 2020
      degree: "PhD"
      institution: "University of California, Santa Barbara"
      research_focus: "Dryland ecohydrology"
  ```
- `current_position`: Current job title (string, optional)
- `current_institution`: Current affiliation (string, optional)
- `linkedin_url`: LinkedIn profile (string, optional)
- `research_interests`: Keywords (list of strings, optional)
- `_cv_metadata`: Source tracking (dict, see CVMetadata above)

### CV.numbers Sheet Schema (Assumptions)

**Common columns** (fuzzy matched):
- Name column (required): "Name", "Full Name", "Student Name", "Person"
- Years column (optional): "Years", "Year", "Dates", "Period"
- Degree column (optional): "Degree", "Degree Type", "Program"
- Institution column (optional): "Institution", "University", "Affiliation"
- Research column (optional): "Research", "Focus", "Area", "Topic"

**Sheet-specific expectations**:
- Graduate PhD: Should have Degree = "PhD"
- Graduate MA_MS: Should have Degree = "MS" or "MA"
- Postdoc: May not have Degree column
- Undergrad: May have Degree = "BS" or "BA"
- Visitors: May have different column structure (visitor type, duration)

## Implementation Notes

### Python Class Hierarchy

```python
# models/person.py
@dataclass
class Role:
    type: str
    start_year: int | None = None
    end_year: int | None = None
    degree: str | None = None
    institution: str | None = None
    research_focus: str | None = None

@dataclass
class Person:
    name: str
    firstname: str
    lastname: str
    roles: list[Role]
    current_position: str | None = None
    current_institution: str | None = None
    linkedin_url: str | None = None
    research_interests: list[str] = field(default_factory=list)
    email: str | None = None
    avatar: str | None = None
    bio: str | None = None
    publications: list[str] = field(default_factory=list)
    alumni_status: bool = False
    profile_file_path: str | None = None
    cv_metadata: dict = field(default_factory=dict)

# models/cv_sheet.py
@dataclass
class CVEntry:
    sheet_name: str
    name: str
    years: str | None
    degree: str | None
    institution: str | None
    research: str | None
    row_index: int

    def parse_years(self) -> tuple[int | None, int | None]: ...
    def to_role(self) -> Role: ...

class CVSheet:
    def __init__(self, name: str, table_index: int = 0): ...
    def detect_columns(self, header_row: list[str]) -> dict[str, int | None]: ...
    def parse_entries(self) -> list[CVEntry]: ...

# models/profile_file.py
class ProfileFile:
    def __init__(self, file_path: str): ...
    def load(self) -> ProfileFile: ...
    def save(self, dry_run: bool = False): ...
    def get_cv_sourced_fields(self) -> list[str]: ...
    def is_manually_modified(self, field: str, new_value: any) -> bool: ...
    def to_person(self) -> Person: ...

# models/enrichment.py
@dataclass
class EnrichmentSuggestion:
    person_name: str
    profile_file_path: str
    field: str
    current_value: str | None
    suggested_value: str
    source_url: str
    source_snippet: str
    confidence: float
    confidence_breakdown: dict[str, float]
    timestamp: datetime
    query: str

    def meets_threshold(self) -> bool: ...
    def format_for_review(self) -> str: ...
    def apply_to_profile(self, profile: ProfileFile): ...

class EnrichmentCache:
    def __init__(self, cache_dir: str = ".cache/enrichment/"): ...
    def load(self, person_name: str) -> list[EnrichmentSuggestion] | None: ...
    def save(self, person_name: str, suggestions: list[EnrichmentSuggestion]): ...
    def clear(self, person_name: str | None): ...
```

## Future Enhancements

- **Role history visualization**: Generate timeline graphic from roles list
- **Publication auto-linking**: Match person to publications in `_publications/` by author name
- **Research keyword extraction**: Use LLM to extract structured keywords from free-text research descriptions
- **Automated cache refresh**: Scheduled enrichment re-run (quarterly/semi-annual) per user clarification Q3
- **Photo enrichment**: Fetch profile photos from LinkedIn or university directories
- **Co-author network**: Build graph of research collaborations from publication data
