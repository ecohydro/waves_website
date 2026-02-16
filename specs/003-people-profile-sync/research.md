# Technical Research: People Profile Management and Enrichment

**Feature**: 003-people-profile-sync
**Created**: 2026-01-29
**Status**: Phase 0 - Technical Decisions

## Overview

This document captures technical decisions for extracting people data from CV.numbers sheets, matching to Jekyll profile files, and enriching with web-sourced information. The goal is "directional improvement" (60-80% automation) while preserving human oversight.

## Decision 1: CV.numbers Sheet Parsing Strategy

**Context**: CV.numbers file contains 5 sheets (Graduate PhD, Postdoc, Graduate MA_MS, Undergrad, Visitors) with varying column structures but common fields like name, years, affiliation.

**Options Considered**:
1. **Strict schema enforcement** - Require exact column names and order
2. **Fuzzy column matching** - Match columns by similarity (e.g., "Name" vs "Full Name")
3. **Manual column mapping** - User provides column mapping config per sheet

**Decision**: **Option 2 - Fuzzy column matching with fallback**

**Rationale**:
- Feature 001 (ingest_publications.py) successfully uses numbers-parser with hardcoded column access
- CV.numbers sheets may have slight variations (e.g., "Degree" vs "Degree Type")
- Fuzzy matching balances robustness (handles minor schema changes) with simplicity (no config files)
- Fallback to known patterns (e.g., first column usually name) for missing columns
- FR-007 requires graceful handling of incomplete data

**Implementation Notes**:
- Use `numbers_parser.Document` to load CV.numbers
- For each sheet, scan header row for column name patterns:
  - Name: `["name", "full name", "student name", "person"]`
  - Years: `["years", "year", "dates", "period"]`
  - Degree: `["degree", "degree type", "program"]`
  - Institution: `["institution", "university", "affiliation"]`
  - Research: `["research", "focus", "area", "topic"]`
- Use case-insensitive substring matching
- Log warnings when columns are missing or ambiguous

## Decision 2: Name Matching Algorithm for Profile Files

**Context**: Must match CV.numbers entries (name + optional year/degree) to existing `_people/lastname.md` files. FR-004 specifies name as primary key; FR-003 requires merging duplicate entries across sheets.

**Options Considered**:
1. **Exact filename match** - "John Doe" → johndoe.md (fails if filename convention differs)
2. **Frontmatter name match** - Parse all profile files, compare frontmatter `title` or `author` field
3. **Hybrid: filename + fuzzy frontmatter** - Try filename first, fall back to fuzzy name match in frontmatter

**Decision**: **Option 3 - Hybrid matching with fuzzy fallback**

**Rationale**:
- Existing people files use naming convention like `odonnell.md`, `bhattachan.md` (lowercase lastname)
- Some files may use full names in frontmatter (e.g., `title: "Kelly O'Donnell"`)
- Hybrid approach handles both conventions
- Fuzzy matching accounts for middle initials, hyphens, apostrophes (O'Donnell vs ODonnell)
- FR-004 allows year + degree as secondary identifiers for disambiguation

**Implementation Notes**:
- Normalize CV name: lowercase, strip punctuation, extract lastname
- First pass: check if `{lastname}.md` exists in `_people/`
- Second pass: load all `_people/*.md`, parse frontmatter, compare `title` or `author` fields using fuzzy string matching (e.g., Levenshtein distance ≥ 0.8 threshold)
- If multiple matches, use year + degree from CV entry to disambiguate
- Log ambiguous matches for manual review
- For entries with no match, generate new filename: `{lastname}.md` (or `{firstname}-{lastname}.md` if collision)

## Decision 3: Multi-Role Merging for Duplicate Entries

**Context**: FR-003 requires merging entries when same person appears in multiple CV sheets (e.g., Postdoc → Visitor). Clarification Q1 answer: "Merge into single profile with all roles."

**Options Considered**:
1. **Last role wins** - Only keep most recent sheet entry
2. **Role history list** - Store all roles with years in frontmatter array
3. **Separate profiles** - Create one profile per role (conflicts with FR-003)

**Decision**: **Option 2 - Role history list in frontmatter**

**Rationale**:
- Preserves full career trajectory (aligns with research group history goals)
- Frontmatter array is machine-readable and supports chronological sorting
- Allows future enhancements (e.g., display timeline on profile page)
- Clarification Q1 explicitly chose this approach

**Implementation Notes**:
- Add frontmatter field: `roles: [{type: "Graduate PhD", years: "2015-2020", degree: "PhD"}, {type: "Postdoc", years: "2020-2022"}]`
- When matching CV entry to existing profile, check if role already exists (same type + overlapping years)
- If role exists, update years/degree; if new role, append to list
- Sort roles chronologically by end year (most recent last)
- Mark field as `cv_sourced: true` in metadata

## Decision 4: Web Search API Selection

**Context**: FR-008 requires web search for current professional information (position, affiliation). FR-010 specifies LinkedIn profile search. FR-018 requires public information only.

**Options Considered**:
1. **Google Custom Search API** - Paid, 10k queries/day free tier, structured results
2. **SerpAPI** - Paid ($50/mo for 5k searches), supports Google + LinkedIn scraping
3. **Direct web scraping** - Free but fragile (breaks with site changes)
4. **LLM-powered search** - Use Claude API with web search tool (available in Claude API)
5. **Manual links only** - No automated web search (user provides LinkedIn URLs)

**Decision**: **Option 1 - Google Custom Search API with fallback to manual**

**Rationale**:
- 10k queries/day free tier sufficient for ~50-100 alumni (avg 2-3 queries per person)
- Structured JSON results easier to parse than scraping
- Respects robots.txt and rate limits (FR-018 compliance)
- LinkedIn official API requires OAuth and is restrictive; Custom Search can find public LinkedIn profiles via Google
- Option 4 (Claude API web search) is viable but adds dependency on external LLM service (future enhancement)
- Option 5 (manual only) viable fallback if API limits exceeded

**Implementation Notes**:
- Require `GOOGLE_CUSTOM_SEARCH_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID` in `.env` file
- Query format: `"{name} {last_known_institution} current position"`
- For LinkedIn: `"{name} site:linkedin.com/in"`
- Parse results for position titles, institution names, LinkedIn URLs
- Cache results in JSON format (see Decision 5)
- If API key missing or quota exceeded, log warning and skip enrichment (graceful degradation)

## Decision 5: Confidence Scoring Methodology

**Context**: FR-013 requires confidence scores (0.0-1.0) for web enrichment suggestions with ≥0.6 threshold. FR-009 requires manual review of suggestions.

**Options Considered**:
1. **Search rank only** - Top result = 1.0, second = 0.8, etc.
2. **Keyword match count** - Score based on how many CV fields (name, institution, degree) appear in search result
3. **Hybrid: rank + keyword + context** - Combine search position, keyword matches, and contextual signals (co-authors, research area)

**Decision**: **Option 3 - Hybrid scoring with weighted components**

**Rationale**:
- Search rank alone insufficient (person with common name may not be top result)
- Keyword matching aligns with FR-011 (contextual disambiguation)
- Weighted approach allows tuning to meet 60% enrichment success rate (SC-003)
- Transparency: show score breakdown to user during manual review

**Implementation Notes**:
- Score components:
  - **Search rank**: 0.4 weight (top result = 1.0, positions 2-5 linearly decrease to 0.2)
  - **Name match**: 0.3 weight (exact full name = 1.0, fuzzy match ≥ 0.7)
  - **Institution match**: 0.2 weight (exact = 1.0, partial substring = 0.5)
  - **Contextual signals**: 0.1 weight (research keywords, co-author names in result snippet)
- Final score = weighted sum
- Filter results with score < 0.6 per FR-013
- Store score + breakdown in `EnrichmentSuggestion` entity
- Present top 3 matches per person (FR-013)

## Decision 6: Cache Storage Format and Location

**Context**: FR-012 requires indefinite caching of web search results with manual clear option. Must support force-refresh per person or entire cache.

**Options Considered**:
1. **JSON files** - One file per person in `.cache/enrichment/{lastname}.json`
2. **SQLite database** - Single `.cache/enrichment.db` with tables for people, queries, results
3. **YAML files** - Similar to JSON but more readable

**Decision**: **Option 1 - JSON files with directory structure**

**Rationale**:
- Simple, human-readable, easy to inspect/debug
- Per-person files support selective cache clearing (delete one file vs database query)
- No additional dependencies (SQLite is stdlib but adds complexity)
- Consistent with project's "Content as Data" principle (structured files over databases)
- Easy to gitignore entire cache directory

**Implementation Notes**:
- Cache directory: `.cache/enrichment/` (add to .gitignore)
- Filename format: `{lastname}_{firstname}.json` (matches person file naming)
- JSON structure:
  ```json
  {
    "person_name": "John Doe",
    "person_file": "_people/doe.md",
    "last_updated": "2026-01-29T10:30:00Z",
    "queries": [
      {
        "query": "John Doe Stanford current position",
        "results": [
          {
            "title": "John Doe - Associate Professor - MIT",
            "url": "https://...",
            "snippet": "...",
            "confidence": 0.85,
            "confidence_breakdown": {"rank": 0.4, "name": 0.3, ...}
          }
        ]
      }
    ]
  }
  ```
- Force refresh: `--force-refresh` CLI flag deletes cache file before running enrichment
- Clear all cache: `--clear-cache` flag or manual `rm -rf .cache/enrichment/`

## Decision 7: Frontmatter Field Tagging Mechanism

**Context**: FR-005 requires tagging frontmatter fields with `cv_sourced` metadata to distinguish CV data from manual additions. FR-005a requires preserving manual edits when conflicts occur.

**Options Considered**:
1. **Inline comments** - Add YAML comments like `# cv_sourced: true` above each field
2. **Separate metadata field** - Add `_cv_metadata: {field1: {sourced: true, last_synced: "2026-01-29"}}` to frontmatter
3. **Field name suffix** - Rename fields like `position_cv_sourced` (breaks existing schema)

**Decision**: **Option 2 - Separate metadata dictionary**

**Rationale**:
- YAML comments are not preserved by python-frontmatter (lost on re-write)
- Separate `_cv_metadata` field is machine-readable and preserves all data
- Doesn't break existing frontmatter schema (no field renaming)
- Supports additional metadata (last_synced timestamp, conflict flags)
- Easy to query: check if field name exists in `_cv_metadata` keys

**Implementation Notes**:
- Add to frontmatter:
  ```yaml
  _cv_metadata:
    title:
      sourced: true
      last_synced: "2026-01-29T10:30:00Z"
    roles:
      sourced: true
      last_synced: "2026-01-29T10:30:00Z"
    position:
      sourced: false  # manually added, never overwrite
  ```
- When syncing:
  - If field not in `_cv_metadata` or `sourced: false`, skip update (preserve manual content)
  - If `sourced: true` and CV value differs from current value, check if current value was manually modified (compare timestamps or hash)
  - If manual modification detected, log warning and skip update per FR-005a
- Initialize `_cv_metadata` for new profiles with all CV fields marked `sourced: true`

## Decision 8: CLI Subcommand Structure

**Context**: Tool performs multiple operations (extract, sync, enrich). Should support dry-run, selective operations, force-refresh.

**Options Considered**:
1. **Single script with flags** - `sync_people.py --extract --sync --enrich --dry-run`
2. **Subcommands** - `sync_people.py extract|sync|enrich --dry-run`
3. **Separate scripts** - `extract_people.py`, `sync_people.py`, `enrich_people.py`

**Decision**: **Option 2 - Subcommands with shared options**

**Rationale**:
- Matches user story priorities (P1: extract, P2: sync, P3: enrich) - each can run independently
- Allows incremental workflow: extract → review → sync → review → enrich
- Shared `--dry-run` flag across all subcommands (FR-014)
- Follows git-style CLI pattern (familiar to users)
- Easier to test individual operations in isolation

**Implementation Notes**:
- Use argparse with subparsers:
  ```python
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(dest='command')

  # Extract subcommand
  extract_parser = subparsers.add_parser('extract')
  extract_parser.add_argument('--numbers-file', default='~/Library/Mobile Documents/...')
  extract_parser.add_argument('--dry-run', action='store_true')

  # Sync subcommand
  sync_parser = subparsers.add_parser('sync')
  sync_parser.add_argument('--people-dir', default='_people/')
  sync_parser.add_argument('--dry-run', action='store_true')

  # Enrich subcommand
  enrich_parser = subparsers.add_parser('enrich')
  enrich_parser.add_argument('--force-refresh', action='store_true')
  enrich_parser.add_argument('--clear-cache', action='store_true')
  enrich_parser.add_argument('--person', help='Enrich specific person only')
  ```
- Full workflow: `./sync_people.py extract && ./sync_people.py sync && ./sync_people.py enrich`
- Each subcommand returns structured output (JSON or summary table) for review

## Dependencies

### Python Libraries (to add to requirements.txt)
- `numbers-parser` - Already present (Feature 001)
- `python-frontmatter` - Already present (Feature 001)
- `pyyaml` - Already present (Feature 001)
- `requests` - Already present (Feature 002)
- `python-dotenv` - Already present (Feature 002)
- `google-api-python-client` - NEW - For Google Custom Search API
- `rapidfuzz` - NEW - For fuzzy string matching (name comparison)

### External Services
- **Google Custom Search API** - Free tier 10k queries/day (requires API key in `.env`)
- **CV.numbers file** - Must be accessible at `~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers` via iCloud sync

### Feature Dependencies
- Feature 001 (ingest_publications.py) - Shares numbers-parser usage patterns, CV.numbers file access
- Constitution Principle IV (Automation & Agentic Refresh) - Requires idempotent scripts, machine-readable content

## Testing Strategy

### Unit Tests
- CV.numbers parsing with mock spreadsheet data (fixture: `tests/fixtures/sample_cv.numbers`)
- Name matching algorithm with various formats (O'Donnell, van der Berg, hyphenated names)
- Fuzzy column matching with schema variations
- Multi-role merging logic
- Confidence scoring calculations with known inputs
- Frontmatter metadata tagging and conflict detection

### Integration Tests
- Extract → Sync → Enrich full workflow with sample data
- Idempotency: run sync twice, verify no changes on second run
- Conflict handling: manually modify cv_sourced field, verify preservation
- Cache behavior: run enrichment, delete cache, verify re-fetch
- Force refresh: modify cached result, run with --force-refresh, verify update

### Contract Tests
- CV.numbers schema assumptions (expected columns in each sheet)
- People frontmatter schema (required fields: author, avatar, title, etc.)
- Google Custom Search API response structure

### Manual Testing Checklist
- Extract from real CV.numbers file with 50-100 entries
- Sync to real `_people/` directory (dry-run first)
- Enrich 5-10 alumni profiles, review confidence scores
- Verify manual content preservation (photos, bios, research interests)
- Test with missing API key (graceful degradation)
- Test with rate-limited API (cache usage)

## Open Questions

1. **LinkedIn profile verification**: Should we verify LinkedIn URLs are valid/public before suggesting? (Could add HTTP HEAD request check, but increases API calls)
   - **Recommendation**: Accept as-is for now; user reviews suggestions manually anyway

2. **Duplicate detection across name variations**: What if same person appears as "John Doe" in one sheet and "J. Doe" in another?
   - **Recommendation**: Fuzzy matching with ≥0.8 threshold should catch most; log low-confidence duplicates for manual review

3. **Historical role data**: Should we preserve old roles that no longer appear in CV.numbers?
   - **Recommendation**: Yes - once a role is in the profile, only update years/degree if CV data changes; never remove roles (incremental & non-destructive)

4. **Research area extraction**: CV sheets may have free-text "Research" column - how to structure this in profile?
   - **Recommendation**: Store as-is in frontmatter `research_interests` field (list); future enhancement could extract keywords

## Next Steps (Phase 1)

1. Create detailed data model with Python class definitions (data-model.md)
2. Define contracts for CV.numbers sheets and people frontmatter schema (contracts/)
3. Write quickstart guide with example commands (quickstart.md)
4. Update agent context file with new technologies and patterns (CLAUDE.md)
