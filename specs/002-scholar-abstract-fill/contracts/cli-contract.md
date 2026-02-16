# CLI Contract: fill_abstracts.py

**Branch**: `002-scholar-abstract-fill` | **Date**: 2026-01-29

## Command Interface

```
python _scripts/fill_abstracts.py [OPTIONS]
```

### Options

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--dry-run` | `-n` | bool | false | Preview mode: report what would be updated without making API calls or modifying files |
| `--publications-dir` | `-p` | path | `_publications/` | Directory containing publication markdown files |
| `--numbers-file` | `-f` | path | `~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers` | Path to the CV.numbers file for abstract write-back |
| `--skip-cv-writeback` | | bool | false | Skip writing abstracts back to CV.numbers (only update markdown files) |
| `--verbose` | `-v` | bool | false | Show detailed output for each publication processed |
| `--max-publications` | `-m` | int | None | Limit processing to first N publications (for testing) |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (abstracts retrieved or none needed) |
| 1 | Error (missing API key, file not found, or fatal error) |
| 2 | Partial success (some abstracts retrieved, some failed) |

## Output Contract

### Standard Mode (no flags)

```
Loading API credentials from .env...
API key found: D2zY****7GE3

Scanning _publications/ for files missing abstracts...
Found 173 publication files, 27 missing abstracts

Retrieving abstracts from Scholar API (this may take a few minutes)...
Processing: Caylor2000_5183.md [DOI: none, using title+year]
  ✓ Abstract retrieved (245 characters)
  ✓ File updated
  ✓ CV.numbers updated

Processing: Caylor2004_7319.md [DOI: none, using title+year]
  ✓ Abstract retrieved (312 characters)
  ✓ File updated
  ⚠ CV.numbers match not found (title+year mismatch)

Processing: Caylor2006_3796.md [DOI: 10.1007/1-4020-4260-4_15]
  ✗ API error: No results found

[... 24 more ...]

Results:
  Total scanned:         173 files
  Skipped (has abstract): 146 files
  API calls made:         27

  Success:                24 abstracts retrieved
  API errors:              2 (no results)
  Validation failures:     1 (abstract < 50 chars)

  CV.numbers write-back:  22 successful, 2 failed

New abstracts added to:
  _publications/Caylor2000_5183.md
  _publications/Caylor2004_7319.md
  ... (22 more)

Failed retrievals:
  Caylor2006_3796.md - API returned no results
  Caylor2015_4595.md - Abstract too short (42 characters)
```

### Dry-Run Mode (`--dry-run`)

```
Loading API credentials from .env...
API key found: D2zY****7GE3

Scanning _publications/ for files missing abstracts...
Found 173 publication files, 27 missing abstracts

DRY RUN - No API calls will be made, no files will be modified

Would query Scholar API for:
  1. Caylor2000_5183.md - "Approaches for the estimation..." (2000) [no DOI]
  2. Caylor2004_7319.md - "Coupling ecohydrological patterns..." (2004) [no DOI]
  3. Caylor2006_3796.md - "Pattern and process in savanna..." (2006) [DOI: 10.1007/1-4020-4260-4_15]
  ... (24 more)

Summary:
  Would query:    27 publications
  Estimated time: ~30 seconds (with 1s rate limit + retries)
  Would update:   _publications/ markdown files
  Would update:   CV.numbers Abstract column (matched rows)
```

### All Up-to-Date

```
Loading API credentials from .env...
API key found: D2zY****7GE3

Scanning _publications/ for files missing abstracts...
Found 173 publication files, 0 missing abstracts

All publications already have abstracts. Nothing to do.
```

### Error: Missing API Key

```
Error: SCHOLAR_API_KEY environment variable not found
Please add SCHOLAR_API_KEY to your .env file or set it in your environment
```

### Error: File Not Found

```
Error: Publications directory not found: _publications/
Check that you are running from the repository root
```

## Input Validation

| Input | Validation | On Failure |
|-------|-----------|------------|
| `SCHOLAR_API_KEY` env var | Must be non-empty string | Exit code 1 with error message |
| Publications directory | Directory exists and is readable | Exit code 1: `Publications directory not found: {path}` |
| CV.numbers file path | File exists and is readable (if not `--skip-cv-writeback`) | Exit code 1: `CV.numbers file not found: {path}` |
| Publication markdown file | Valid frontmatter with title, year | Skip file; log warning if verbose |
| API response | `total_num_results > 0` and `paper_data` array non-empty | Log as API_ERROR, continue processing |
| Abstract text | Non-empty and > 50 characters | Log as VALIDATION_FAILED, skip update |

## Verbose Mode (`--verbose`)

When `--verbose` flag is set, print per-publication processing details:

```
Processing: Caylor2000_5183.md
  Title: "Approaches for the estimation of primary productivity..."
  Year: 2000
  DOI: none
  Authors: [Kelly Caylor]
  Has abstract: No

  API Query: title+year search
    keywords: Approaches for the estimation...
    query: Find the abstract of the publication titled...

  API Response: 1 result(s)
    Matched: Dowty, P.R. et al. (2000)
    Surname match: caylor found in creators
    Abstract length: 245 characters
    Validation: PASS

  File Update: SUCCESS
  CV.numbers Match: DOI not available, trying title+year... FOUND
  CV.numbers Write: SUCCESS

Rate limit: sleeping 1.0 seconds...
```

## Compatibility with Feature 001

- Shares `--numbers-file` and `--publications-dir` options with `ingest_publications.py`
- Uses same CV.numbers path default
- Follows same output directory structure
- Compatible `.env` file location (repository root)
- Can be run independently or after feature 001 ingestion
