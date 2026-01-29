# Research: Publication Ingestion from CV Spreadsheet

**Branch**: `001-pub-ingestion` | **Date**: 2026-01-29

## R1: Reading Apple Numbers Files in Python

**Decision**: Use the `numbers-parser` library (v4.16.3, MIT license) to read `.numbers` files natively.

**Rationale**: `numbers-parser` is the only maintained Python library that reads Apple Numbers files directly without export. It supports Python 3.9+, provides sheet-by-name access, typed cell values (str, float, datetime, None), and row iteration. It is read-only for our use case (we only read the CV file). The library requires `snappy` (installed via Homebrew) as a native dependency.

**Alternatives considered**:
- **Export to CSV manually**: Rejected — requires user to open Numbers and export before each run, violating FR-001 (read directly) and SC-004 (single command).
- **AppleScript/osascript export**: Rejected — fragile, requires Numbers app to be running, slow for 159 rows.
- **Openpyxl/xlrd**: Rejected — these read Excel formats (.xlsx/.xls), not .numbers.

**Key implementation notes**:
- Access sheet by name: `doc.sheets["Publications"]`
- Access table: `sheet.tables[0]` (assume single table per sheet)
- First row contains headers; iterate `table.rows(values_only=True)` and use `data[0]` as column names
- Float values for year/ID need `int()` conversion
- `EmptyCell` returns `None`; `MergedCell` returns `None`
- DOI column may contain `-` string for missing DOIs (treat as absent)
- Requires: `pip install numbers-parser` and `brew install snappy`

## R2: Publication ID Generation Strategy

**Decision**: Generate random 4-digit IDs in the range 1000-9999, checking against all existing IDs to avoid collisions.

**Rationale**: Analysis of 137 existing publication files shows IDs are 4-digit integers (range 1016-9991) that are not sequential — they appear randomly assigned, likely from a prior CMS. Only ~1.5% of the 1000-9999 space is used (137 of 9000 slots), so collision risk is negligible. Random generation preserves the existing pattern.

**Alternatives considered**:
- **Sequential from max+1**: Rejected — existing IDs are not sequential; starting from 9992 would be arbitrary and could conflict if new entries are added via CloudCannon or other tools.
- **Hash-based (title+year)**: Rejected — existing IDs don't follow a hash pattern; mixing schemes would be inconsistent.
- **Use the `NUM` column from spreadsheet**: Rejected — `NUM` is a sequential row number (1-159) in the spreadsheet, unrelated to the website ID scheme, and would collide with existing website IDs.

**Key implementation notes**:
- Collect all existing IDs by scanning `_publications/*.md` frontmatter
- Generate random int in 1000-9999 range
- Re-generate if collision detected (loop until unique)
- One known data issue: `Tuholske2021_7248.md` has `id: 1248` (filename/frontmatter mismatch) — ingestion should match on frontmatter `id`, not filename

## R3: Author Matching Strategy

**Decision**: Match publication authors against `authors.yml` YAML keys using exact case-sensitive string comparison, plus "Kelly Caylor" as a special-case site owner.

**Rationale**: Analysis of existing publications confirms that `author` and `author-tags` fields use exact matches to the top-level YAML keys in `_data/authors.yml`. "Kelly Caylor" is defined in `_config.yml` as the site owner, not in `authors.yml`, but appears pervasively in publication entries. Only lab members appear in `author-tags` — external co-authors are never tagged.

**Alternatives considered**:
- **Fuzzy/partial matching**: Rejected — existing data uses exact matches consistently; fuzzy matching would risk false positives (e.g., "Wang" matching wrong person).
- **Match on `name` sub-field**: Rejected — YAML keys and `name` sub-fields are identical in all but one case (`Farai Kaseke` key vs. `Kudzai Farai Kaseke` name). Using keys is consistent with existing entries.

**Key implementation notes**:
- Build a lookup set of author names: all YAML keys from `authors.yml` + "Kelly Caylor"
- For each publication's author columns (A1-A31), check if name exists in lookup set
- Matching is case-sensitive and exact (no initials, no abbreviations)
- Spreadsheet stores full names (e.g., "Natasha Krell") matching the key format
- The `author` frontmatter field is the group member with the earliest author position, determined via the role columns (FR-014)
- The `author-tags` field lists ALL matching group members, not just the primary one

## R4: Frontmatter Field Mapping from Spreadsheet Columns

**Decision**: Map spreadsheet columns to publication frontmatter as follows:

| Frontmatter Field | Source Column(s) | Transformation |
|---|---|---|
| `author` | Role columns + A1-A31 | FR-014 logic: earliest group-member author position |
| `date` | `YEAR` | `{YEAR}-01-01 00:00:00` (day/month unknown; use Jan 1) |
| `id` | Generated | Random 4-digit, collision-checked |
| `year` | `YEAR` | String, quoted (e.g., `'2024'`) |
| `title` | `TITLE` | Direct string |
| `doi` | `DOI` | Direct string; omit if `-` or empty |
| `excerpt` | A1-A31 + `YEAR` + `TITLE` + `PUBLISHER` + `DOI` | Formatted citation: `"LastName, F. et al. (Year). Title. _Journal_, doi:DOI."` |
| `header.teaser` | None | Placeholder: `assets/images/publications/{LastName}{Year}_{id}.png` |
| `portfolio-item-category` | Static | Always `["publications"]` |
| `portfolio-item-tag` | `YEAR` + `PUBLISHER` | `["{year}", "{journal name}"]` |
| `author-tags` | A1-A31 cross-ref authors.yml | List of all group member names found |

**Body content mapping**:

| Body Element | Source Column(s) | Format |
|---|---|---|
| Citation blockquote | A1-A31 + `YEAR` + `TITLE` + `PUBLISHER` + `VOL` + `ISSUE` + `PAGES` + `DOI` | `> Authors (Year). Title. _Journal_, Vol(Issue), Pages, doi:DOI.` |
| Abstract | `Abstract` (col 86) | `**Abstract**: {text}` |
| Article link | `DOI` | `[Go to the Article](https://www.doi.org/{DOI}){: .btn .btn--success}` |

**Rationale**: Mapping derived from analysis of 6+ existing publication files and the full 104-column spreadsheet schema. The `date` field uses Jan 1 as default since the spreadsheet only stores year (no month/day). The teaser image uses a placeholder path since no image data exists in the spreadsheet.

## R5: Duplicate Detection Strategy

**Decision**: Match using DOI as primary key (case-insensitive, normalized), with title+year fallback.

**Rationale**: DOI is the canonical unique identifier for published academic work. The spreadsheet stores DOIs for most entries. For entries without DOI (marked as `-`), title+year matching provides a reasonable fallback. Existing publication files store DOI in frontmatter, making extraction straightforward.

**Key implementation notes**:
- Extract DOIs from all existing `_publications/*.md` frontmatter
- Normalize DOIs: lowercase, strip whitespace, remove `https://doi.org/` prefix if present
- For DOI = `-` or empty: fall back to case-insensitive title comparison + year match
- Title matching should normalize whitespace and ignore minor punctuation differences
