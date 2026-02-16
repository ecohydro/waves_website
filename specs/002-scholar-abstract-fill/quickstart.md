# Quickstart: Scholar API Abstract Retrieval

**Branch**: `002-scholar-abstract-fill` | **Date**: 2026-01-29

## Prerequisites

1. **macOS** with iCloud Drive enabled and synced (same as feature 001)
2. **Python 3.9+** installed
3. **Homebrew** installed (for native dependency from feature 001)
4. **Scholar API Key** - Sign up at https://docs.scholarai.io/ and obtain an API key
5. **Feature 001** completed - Publication ingestion system must be functional

## Setup

### 1. Install Dependencies

Feature 001 dependencies are already installed. Add the new dependencies:

```bash
# Install Python dependencies
pip install requests python-dotenv responses

# Or update from requirements file (once updated)
pip install -r _scripts/requirements.txt
```

### 2. Configure API Key

The `.env` file is already created (user has confirmed). Verify it contains:

```bash
# Check .env file exists
cat .env

# Should contain (with your actual API key):
SCHOLAR_API_KEY=your_api_key_here
```

If `.env` doesn't exist, create it:

```bash
echo "SCHOLAR_API_KEY=your_api_key_here" > .env
```

**Important**: The `.env` file is already in `.gitignore`. Never commit API keys to git.

### 3. Verify Setup

```bash
# Test that the API key loads correctly
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key:', os.getenv('SCHOLAR_API_KEY')[:4] + '****' if os.getenv('SCHOLAR_API_KEY') else 'NOT FOUND')"
```

Expected output:
```
API Key: D2zY****
```

## Usage

### Preview what would be updated (recommended first run)

```bash
python _scripts/fill_abstracts.py --dry-run
```

This will:
- Scan all publications in `_publications/`
- Identify which ones lack abstracts
- Show what API queries would be made
- **NOT** make any API calls or modify files

### Retrieve missing abstracts

```bash
python _scripts/fill_abstracts.py
```

This will:
- Scan for publications missing abstracts
- Query Scholar API for each missing abstract (1 req/sec with retries)
- Update markdown files with retrieved abstracts
- Write abstracts back to CV.numbers spreadsheet
- Show progress and summary report

### With verbose output

```bash
python _scripts/fill_abstracts.py --verbose
```

Shows detailed per-publication processing:
- API query parameters
- Response validation
- File update status
- CV.numbers write-back status

### Limit to first N publications (for testing)

```bash
python _scripts/fill_abstracts.py --max-publications 5 --verbose
```

Useful for testing without processing all publications.

### Skip CV.numbers write-back

```bash
python _scripts/fill_abstracts.py --skip-cv-writeback
```

Updates website markdown files only, doesn't modify CV.numbers.

### Custom file paths

```bash
python _scripts/fill_abstracts.py \
  --publications-dir "_publications/" \
  --numbers-file "/path/to/CV.numbers"
```

## Typical Workflow

1. **Run publication ingestion** (feature 001) to identify missing abstracts:
   ```bash
   python _scripts/ingest_publications.py --dry-run
   ```
   Note the count of publications with missing abstracts (shown in warnings).

2. **Preview abstract retrieval**:
   ```bash
   python _scripts/fill_abstracts.py --dry-run
   ```
   Verify the list of publications that would be queried.

3. **Retrieve abstracts**:
   ```bash
   python _scripts/fill_abstracts.py --verbose
   ```
   Monitor progress and check for any failures.

4. **Review updated files**:
   ```bash
   # Check a few updated publications
   grep -A 5 "**Abstract**:" _publications/Caylor2023_4247.md
   ```

5. **Verify CV.numbers** (optional):
   Open `CV.numbers` in Numbers app and check that the `Abstract` column has been populated for updated publications.

6. **Build Jekyll site** to verify:
   ```bash
   bundle exec jekyll build
   ```
   Check that abstracts appear correctly on publication pages.

7. **Commit changes**:
   ```bash
   git add _publications/ ~/Library/Mobile\ Documents/com~apple~Numbers/Documents/CV.numbers
   git commit -m "Add missing abstracts via Scholar API

   - Retrieved abstracts for X publications
   - Updated CV.numbers with abstract text

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   git push
   ```

## Performance Expectations

- **Initial run** (27 missing abstracts): ~30-60 seconds
  - 27 API calls × 1 second rate limit = 27 seconds
  - Plus retry overhead, parsing, file I/O

- **Subsequent runs** (all abstracts present): <2 seconds
  - Scans files but skips API calls entirely

- **Rate limiting**: 1 second between API requests
- **Retries**: Up to 3 attempts with 2s, 4s, 8s delays for transient failures

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `SCHOLAR_API_KEY not found` | Ensure `.env` file exists and contains the key |
| `requests` import error | Run `pip install requests python-dotenv` |
| `Publications directory not found` | Run from repository root, or use `--publications-dir` |
| `CV.numbers file not found` | Ensure iCloud Drive is synced; use `--numbers-file` if moved |
| API returns no results | Some publications may not be indexed by Scholar API; check DOI validity |
| Abstract too short (<50 chars) | Scholar API returned truncated/invalid response; manual review needed |
| Rate limit exceeded (429 error) | Script should retry automatically; if persistent, increase delays |
| CV.numbers write-back failed | Publication may not exist in spreadsheet; use `--skip-cv-writeback` to proceed |

## Integration with Feature 001

This tool is designed to run **after** feature 001 (publication ingestion):

```bash
# Step 1: Ingest new publications from CV.numbers
python _scripts/ingest_publications.py

# Step 2: Fill missing abstracts for all publications (new and existing)
python _scripts/fill_abstracts.py
```

Both tools:
- Use the same CV.numbers file path
- Operate on the same `_publications/` directory
- Share Python dependencies (frontmatter, numbers-parser, PyYAML)
- Are idempotent (safe to run multiple times)

## Example Output

### First Run (27 missing abstracts)

```
Loading API credentials from .env...
API key found: D2zY****7GE3

Scanning _publications/ for files missing abstracts...
Found 173 publication files, 27 missing abstracts

Retrieving abstracts from Scholar API (this may take a few minutes)...
Processing: Caylor2000_5183.md [no DOI, using title+year]
  ✓ Abstract retrieved (245 characters)
  ✓ File updated
  ✓ CV.numbers updated
  Rate limit: sleeping 1.0 seconds...

Processing: Caylor2004_7319.md [no DOI, using title+year]
  ✓ Abstract retrieved (312 characters)
  ✓ File updated
  ⚠ CV.numbers match not found
  Rate limit: sleeping 1.0 seconds...

[... 25 more ...]

Results:
  Total scanned:           173 files
  Skipped (has abstract):  146 files
  API calls made:           27

  Success:                  24 abstracts retrieved
  API errors:                2 (no results)
  Validation failures:       1 (abstract < 50 chars)

  CV.numbers write-back:    22 successful, 2 failed

New abstracts added to:
  _publications/Caylor2000_5183.md
  _publications/Caylor2004_7319.md
  ... (22 more)

Failed retrievals:
  Caylor2006_3796.md - API returned no results
  Caylor2015_4595.md - Abstract too short (42 characters)
```

### Second Run (all up-to-date)

```
Loading API credentials from .env...
API key found: D2zY****7GE3

Scanning _publications/ for files missing abstracts...
Found 173 publication files, 0 missing abstracts

All publications already have abstracts. Nothing to do.
```
