# Quickstart Guide: People Profile Sync Tool

**Feature**: 003-people-profile-sync
**Created**: 2026-01-29

## Overview

The People Profile Sync Tool (`sync_people.py`) automates the extraction of people data from CV.numbers, synchronization with Jekyll profile files, and enrichment with current professional information from web sources.

**Goal**: "Directional improvement" (60-80% automation) for managing the People page, reducing manual data entry by ~70% while maintaining human oversight.

## Prerequisites

1. **Python 3.9+** installed
2. **CV.numbers file** accessible at default path:
   ```
   ~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers
   ```
3. **Required Python packages** (install via):
   ```bash
   cd _scripts
   pip install -r requirements.txt
   ```

   Dependencies installed:
   - numbers-parser (CV.numbers parsing)
   - python-frontmatter (YAML frontmatter)
   - pyyaml (YAML processing)
   - requests (HTTP requests)
   - python-dotenv (environment variables)
   - google-api-python-client>=2.0.0 (web enrichment)
   - rapidfuzz>=3.0.0 (fuzzy name matching)

4. **Optional: Google Custom Search API** (for web enrichment):
   - Create a Custom Search Engine at https://cse.google.com
   - Get API key from Google Cloud Console
   - Add to `.env` file in project root:
     ```
     GOOGLE_CUSTOM_SEARCH_API_KEY=your_key_here
     GOOGLE_SEARCH_ENGINE_ID=your_cx_here
     ```

## Basic Workflow

The tool has three main subcommands that can be run independently or in sequence:

```bash
# Full workflow
./_scripts/sync_people.py extract    # Extract from CV.numbers
./_scripts/sync_people.py sync       # Update profile files
./_scripts/sync_people.py enrich     # Add web-sourced info (optional)
```

### Step 1: Extract People from CV.numbers

Extract data from all five CV.numbers sheets (Graduate PhD, Postdoc, Graduate MA_MS, Undergrad, Visitors):

```bash
./_scripts/sync_people.py extract
```

**What it does**:
- Parses CV.numbers file using fuzzy column matching
- Extracts name, years, degree, institution, research focus from each sheet
- Merges entries for people who appear in multiple sheets (e.g., PhD → Postdoc)
- Outputs summary table of extracted people

**Options**:
```bash
# Use custom CV.numbers file location
./_scripts/sync_people.py extract --numbers-file ~/Desktop/CV.numbers

# Dry-run mode (preview without changes)
./_scripts/sync_people.py extract --dry-run

# Verbose output (show all entries)
./_scripts/sync_people.py extract --verbose
```

**Example output**:
```
Extracting people from CV.numbers...
✓ Graduate PhD: 12 entries
✓ Postdoc: 8 entries
✓ Graduate MA_MS: 5 entries
✓ Undergrad: 15 entries
✓ Visitors: 6 entries

Merged 3 duplicate entries:
  - John Doe (Postdoc + Visitor)
  - Jane Smith (Graduate MA_MS + Graduate PhD)
  - Kelly O'Donnell (Graduate PhD + Postdoc)

Total: 43 unique people extracted
```

### Step 2: Sync Profiles to Jekyll Files

Match extracted people to existing `_people/*.md` files and update CV-sourced fields:

```bash
./_scripts/sync_people.py sync
```

**What it does**:
- Matches extracted people to existing profile files by name (fuzzy matching)
- Updates CV-sourced fields (`roles`, `research_interests`, etc.) while preserving manual content
- Creates new profile files for people not yet on website
- Logs conflicts when CV data differs from manually-edited fields (preserves manual edits per FR-005a)

**Options**:
```bash
# Use custom people directory
./_scripts/sync_people.py sync --people-dir _team/

# Dry-run mode (preview changes without writing)
./_scripts/sync_people.py sync --dry-run

# Show detailed diff for each file
./_scripts/sync_people.py sync --verbose
```

**Example output**:
```
Syncing 43 people to _people/ directory...

Matched to existing files:
  ✓ John Doe → _people/doe.md (exact filename match)
  ✓ Kelly O'Donnell → _people/odonnell.md (fuzzy name match, confidence: 0.92)
  ⚠ Jane Smith → _people/smith.md (updated roles, preserved manually-edited bio)

Created new files:
  + _people/garcia.md (new Graduate MA_MS entry)
  + _people/patel.md (new Undergrad entry)

Conflicts logged (manual edits preserved):
  ! _people/doe.md: CV shows degree="PhD" but file has "Ph.D." (preserved manual edit)

Summary:
  - 38 files updated
  - 5 files created
  - 3 conflicts logged (manual edits preserved)
  - 0 errors
```

### Step 3: Enrich with Web Sources (Optional)

Search the web for current professional information (position, institution, LinkedIn):

```bash
./_scripts/sync_people.py enrich
```

**What it does**:
- Queries Google Custom Search API for each person (using cached results if available)
- Extracts current position, institution, and LinkedIn URL from search results
- Calculates confidence scores (0.0-1.0) using hybrid algorithm
- Presents suggestions with confidence ≥ 0.6 for manual review
- Does NOT auto-apply suggestions (manual approval required)

**Options**:
```bash
# Enrich specific person only
./_scripts/sync_people.py enrich --person "Kelly O'Donnell"

# Force refresh (ignore cache)
./_scripts/sync_people.py enrich --force-refresh

# Clear all cached results
./_scripts/sync_people.py enrich --clear-cache

# Dry-run mode (show suggestions without applying)
./_scripts/sync_people.py enrich --dry-run
```

**Example output**:
```
Enriching 43 profiles from web sources...

Using cached results: 38 people
Fetching new results: 5 people (API calls: 15)

Enrichment suggestions (confidence ≥ 0.6):

[1] Kelly O'Donnell (_people/odonnell.md)
  Current Position: Associate Professor (confidence: 0.85)
    Source: https://eaps.mit.edu/people/kelly-odonnell
    Snippet: "Kelly O'Donnell is an Associate Professor in the Department of Earth..."

  Current Institution: Massachusetts Institute of Technology (confidence: 0.89)
    Source: https://eaps.mit.edu/people/kelly-odonnell

  LinkedIn: https://www.linkedin.com/in/kellykodonnell (confidence: 0.92)
    Source: Google search rank #3

  Apply suggestions? [y/n/skip]: y
  ✓ Updated _people/odonnell.md

[2] John Doe (_people/doe.md)
  Current Position: Research Scientist (confidence: 0.62)
    Source: https://scholar.google.com/citations?user=...

  Apply suggestions? [y/n/skip]: n
  ⊗ Skipped _people/doe.md

...

Summary:
  - 28 profiles enriched (user approved)
  - 10 profiles skipped (user declined or low confidence)
  - 5 profiles cached (no new suggestions)
  - API calls used: 15 / 100 daily quota
```

## Common Use Cases

### Initial Setup: Populate People Page from CV

```bash
# Extract all people from CV.numbers
./_scripts/sync_people.py extract --verbose

# Review extracted data, then sync to create profile files
./_scripts/sync_people.py sync --dry-run  # Preview first
./_scripts/sync_people.py sync            # Apply changes

# Optional: enrich with web data
./_scripts/sync_people.py enrich
```

### Regular Maintenance: Update Profiles After CV Changes

```bash
# After updating CV.numbers (e.g., new grad student added):
./_scripts/sync_people.py extract
./_scripts/sync_people.py sync

# Review changes in git diff before committing
git diff _people/

# Commit if satisfied
git add _people/
git commit -m "Update people profiles from CV.numbers"
```

### Update Single Person's Profile

```bash
# Extract and sync all (fast if no CV changes)
./_scripts/sync_people.py extract
./_scripts/sync_people.py sync

# Enrich specific person with web data
./_scripts/sync_people.py enrich --person "Kelly O'Donnell" --force-refresh
```

### Refresh All Web Enrichment Data

```bash
# Clear cache and re-fetch all web data
./_scripts/sync_people.py enrich --clear-cache --force-refresh
```

## Understanding CV-Sourced vs Manual Fields

The tool uses frontmatter field tagging (`_cv_metadata`) to distinguish between:
- **CV-sourced fields**: Automatically updated from CV.numbers (e.g., `roles`, `research_interests`)
- **Manual fields**: Preserved during sync (e.g., `bio`, `avatar`, `current_position`)

### Example: Preserving Manual Edits

```yaml
# _people/odonnell.md frontmatter
---
title: Kelly K. O'Donnell           # CV-sourced (auto-updated)
roles:                              # CV-sourced (auto-updated)
  - type: Graduate PhD
    years: 2015-2020
avatar: assets/images/people/odonnell.jpg  # Manual (never auto-updated)
bio: Custom bio text...             # Manual (never auto-updated)
current_position: Associate Professor  # Manual (from web enrichment or manual entry)

_cv_metadata:
  title:
    sourced: true
    last_synced: "2026-01-29T10:30:00Z"
  roles:
    sourced: true
    last_synced: "2026-01-29T10:30:00Z"
  avatar:
    sourced: false      # Manual field - won't be overwritten
  current_position:
    sourced: false      # Manual field - won't be overwritten
---
```

**What happens on sync**:
- `title` and `roles` updated from CV.numbers if changed
- `avatar` and `bio` preserved (never overwritten)
- `current_position` preserved (added manually or via enrichment, not from CV)

### Conflict Handling

If you manually edit a CV-sourced field (e.g., change "PhD" to "Ph.D." in `roles`), the tool will:
1. Detect the manual modification
2. Preserve your edit (NOT overwrite with CV data)
3. Log a warning for manual review

```
⚠ Conflict in _people/odonnell.md:
  Field: roles[0].degree
  CV value: "PhD"
  Current value: "Ph.D." (manually edited)
  Action: Preserved manual edit
```

## Troubleshooting

### "CV.numbers file not found"

```bash
# Specify custom path
./_scripts/sync_people.py extract --numbers-file ~/path/to/CV.numbers
```

### "Google Search API quota exceeded"

The free tier allows 100 queries/day. The tool caches results indefinitely to minimize API usage.

```bash
# Use cached results only (no new API calls)
./_scripts/sync_people.py enrich  # Will use cache where available

# To upgrade quota, visit Google Cloud Console:
# https://console.cloud.google.com
```

### "No enrichment suggestions found"

Low confidence scores (< 0.6) are filtered out. Try:

```bash
# Use more specific queries by ensuring CV has institution data
# Or manually add current_position and current_institution to profile file
```

### "Column 'Name' not found in CV sheet"

The tool uses fuzzy matching but requires at least a Name column. Check that:
- Sheet has a header row with column names
- At least one column contains "name" (case-insensitive)

## File Structure

```
waves/
├── _scripts/
│   ├── sync_people.py         # Main tool
│   └── requirements.txt       # Python dependencies
├── _people/                   # Jekyll collection (output)
│   ├── odonnell.md
│   ├── doe.md
│   └── ...
├── .cache/
│   └── enrichment/            # Web search cache
│       ├── odonnell_kelly.json
│       └── ...
├── .env                       # API keys (gitignored)
└── specs/003-people-profile-sync/
    ├── spec.md                # Feature specification
    ├── plan.md                # Implementation plan
    ├── research.md            # Technical decisions
    ├── data-model.md          # Entity definitions
    ├── quickstart.md          # This file
    └── contracts/             # Schema contracts
        ├── cv-sheet-schema.yml
        ├── people-frontmatter-schema.yml
        └── google-search-api.yml
```

## Advanced Usage

### Custom Workflow: Only Sync New People

```bash
# Extract all people
./_scripts/sync_people.py extract

# Sync only creates new files, skips existing (custom flag - TBD in implementation)
./_scripts/sync_people.py sync --new-only
```

### Batch Enrichment with Manual Review

```bash
# Generate all suggestions without applying
./_scripts/sync_people.py enrich --dry-run > enrichment_suggestions.txt

# Review suggestions offline, then apply selectively
./_scripts/sync_people.py enrich --person "Person Name"
```

### Idempotent Operations

All subcommands are idempotent - running them multiple times produces the same result:

```bash
# These are safe to run repeatedly
./_scripts/sync_people.py extract  # Same output if CV.numbers unchanged
./_scripts/sync_people.py sync     # No changes if profiles already synced
./_scripts/sync_people.py enrich   # Uses cache, no duplicate API calls
```

## Integration with Git Workflow

```bash
# 1. Update CV.numbers file (via Numbers app)

# 2. Run sync workflow
./_scripts/sync_people.py extract
./_scripts/sync_people.py sync

# 3. Review changes
git status
git diff _people/

# 4. Commit if satisfied
git add _people/
git commit -m "Sync people profiles from CV.numbers

- Added 2 new Graduate PhD students
- Updated role years for 5 alumni
- Merged John Doe's Postdoc and Visitor roles"

# 5. Optional: enrich with web data (separate commit)
./_scripts/sync_people.py enrich
git add _people/
git commit -m "Enrich people profiles with current positions"
```

## Performance

**Typical timings** (50-100 people):

| Operation | First Run | Subsequent Runs |
|-----------|-----------|-----------------|
| Extract   | ~5 seconds | ~5 seconds (always reads CV) |
| Sync      | ~30 seconds | ~5 seconds (skips unchanged) |
| Enrich    | ~2 minutes (with API calls) | ~10 seconds (cached) |

**API usage** (free tier: 100 queries/day):
- ~2-3 queries per person (position search + LinkedIn search)
- ~50-100 people = 100-300 queries (requires paid tier or multiple days)
- Caching minimizes repeat queries

## Next Steps

1. **Review** extracted data and matched profiles
2. **Manually add** profile photos (`avatar` field) and custom bios
3. **Set up** Google Custom Search API for web enrichment (optional)
4. **Run periodically** (e.g., after updating CV.numbers) to keep profiles current
5. **Commit changes** to git after review

## Related Documentation

- [Feature Specification](./spec.md) - Full requirements and user stories
- [Implementation Plan](./plan.md) - Technical architecture and design
- [Technical Research](./research.md) - Design decisions and rationale
- [Data Model](./data-model.md) - Entity definitions and relationships
- [Contracts](./contracts/) - Schema validation rules

## Getting Help

- Check troubleshooting section above
- Review error logs in console output
- Inspect `.cache/enrichment/*.json` files for web search debugging
- Open issue at repository with `--verbose` output
