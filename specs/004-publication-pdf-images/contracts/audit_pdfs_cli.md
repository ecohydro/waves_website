# CLI Contract: audit_pdfs.py

**Purpose**: Audit PDF archive for completeness and fetch missing PDFs from Scholar AI

**Location**: `_scripts/audit_pdfs.py`

---

## Command Signature

```bash
python _scripts/audit_pdfs.py [OPTIONS]
```

---

## Arguments

### Required

None - all arguments have defaults

### Optional

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--numbers-file` | Path | `~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers` | Path to CV.numbers file |
| `--pdf-dir` | Path | `assets/pdfs/publications/` | Directory containing PDF files |
| `--fetch-missing` | Flag | False | Attempt to fetch missing required PDFs from Scholar AI |
| `--dry-run` | Flag | False | Show what would be done without making changes |
| `--verbose` | Flag | False | Enable verbose logging (DEBUG level) |
| `--log-file` | Path | None | Write logs to file (in addition to console) |
| `--output-report` | Path | None | Save detailed report to JSON file |

---

## Exit Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 0 | Success | Audit complete, no missing required PDFs (or all fetches succeeded) |
| 1 | Fatal error | CV.numbers not found, PDF directory inaccessible, or Scholar API auth failure |
| 2 | Partial success | Audit complete but some required PDFs missing/unfetchable |

---

## Output Format

### Console Output (Default)

```
=== PDF Archive Audit ===
Scanning CV.numbers: ~/Library/.../CV.numbers
Found 215 publications

PDF Archive Status:
  Total publications:           215
  PDFs found:                   187 (87.0%)
  PDFs missing (required):       12
  PDFs missing (optional):       16
  Ambiguous files detected:       3

Required PDFs Missing:
  - Caylor2022_5678 (RA) - DOI: 10.1234/example1
  - Caylor2023_9012 (RA) - DOI: 10.5678/example2
  ...

Ambiguous Files (warnings):
  - Caylor2002_1378_draft.pdf (use exact match: Caylor2002_1378.pdf)
  - Caylor2010_3456_final.pdf (use exact match: Caylor2010_3456.pdf)

✓ Audit complete
```

### Console Output (With --fetch-missing)

```
=== PDF Archive Audit with Fetch ===
[... same audit output ...]

Fetching missing required PDFs from Scholar AI:
  ⏳ Fetching Caylor2022_5678 (DOI: 10.1234/example1)...
  ✓ Successfully fetched Caylor2022_5678
  ⏳ Fetching Caylor2023_9012 (DOI: 10.5678/example2)...
  ✗ Failed: DOI not found
  ...

Fetch Summary:
  Attempted:     12
  Success:        8
  Failed:         4

Failed Fetches:
  - Caylor2023_9012: DOI not found
  - Caylor2024_3456: Network error (connection timeout)
  ...

✓ Audit complete (partial - 4 PDFs still missing)
```

### JSON Report (--output-report)

```json
{
  "timestamp": "2026-01-30T14:32:10Z",
  "cv_numbers_file": "~/Library/.../CV.numbers",
  "pdf_directory": "assets/pdfs/publications/",
  "statistics": {
    "total_publications": 215,
    "pdfs_found": 187,
    "pdfs_missing_required": 12,
    "pdfs_missing_optional": 16,
    "coverage_percentage": 87.0,
    "ambiguous_files": 3
  },
  "missing_required": [
    {
      "canonical_id": "Caylor2022_5678",
      "title": "Example Publication Title",
      "year": 2022,
      "kind": "RA",
      "doi": "10.1234/example1"
    }
  ],
  "missing_optional": [
    {
      "canonical_id": "Smith2015_1234",
      "title": "Book Chapter Example",
      "year": 2015,
      "kind": "BC",
      "doi": null
    }
  ],
  "ambiguous_files": [
    "Caylor2002_1378_draft.pdf",
    "Caylor2010_3456_final.pdf"
  ],
  "fetch_results": [
    {
      "publication_id": "Caylor2022_5678",
      "doi": "10.1234/example1",
      "status": "success",
      "fetch_timestamp": "2026-01-30T14:32:15Z",
      "pdf_path": "assets/pdfs/publications/Caylor2022_5678.pdf"
    },
    {
      "publication_id": "Caylor2023_9012",
      "doi": "10.5678/example2",
      "status": "not_found",
      "fetch_timestamp": "2026-01-30T14:32:20Z",
      "error_message": "DOI not found in Scholar AI"
    }
  ]
}
```

---

## Behavior Details

### PDF Matching Logic

1. Scan `--pdf-dir` for all `*.pdf` files
2. Extract canonical_id from filename stem
3. **Exact match only**: `Caylor2002_1378.pdf` matches publication `Caylor2002_1378`
4. Files with additional suffixes (`_draft`, `_final`, etc.) are flagged as ambiguous
5. Ambiguous files generate warnings but do not count as matches

### Required vs Optional Logic

For each publication:
- If `year >= 2022` AND `kind == "RA"`: PDF required
- Otherwise: PDF optional

### Scholar AI Fetch Logic (--fetch-missing)

Only executed if `--fetch-missing` flag is set:

1. Identify missing required PDFs (pdf_required=True, PDF not found)
2. For each missing PDF:
   - Check if DOI is available (skip if missing)
   - Query Scholar AI API with DOI
   - Download PDF to temp file
   - Validate PDF is readable (pypdfium2 test)
   - Move to `assets/pdfs/publications/{canonical_id}.pdf`
   - Log result
3. Continue batch on individual failures
4. Generate summary report at end

### Rate Limiting

- Scholar API calls: 1 second between requests (existing pattern from Feature 002)
- No retry on success (only retry on transient errors: 429, 500)

### Dry Run Mode (--dry-run)

- Perform audit and identify missing PDFs
- Print what would be fetched (if --fetch-missing)
- Do not download any files
- Do not write to filesystem
- Exit code 0 (informational only)

---

## Error Handling

### Fatal Errors (Exit 1)

- CV.numbers file not found
- PDF directory does not exist or is not accessible
- Scholar API authentication failure (invalid API key)
- Permission denied writing to PDF directory

### Non-Fatal Errors (Continue Batch, Exit 2)

- Individual PDF fetch failures (DOI not found, network error)
- CV.numbers parsing errors for individual publications
- Ambiguous file warnings

### Logging

- **INFO level** (default): Summary statistics, progress indicators, warnings
- **DEBUG level** (--verbose): Detailed operation logs, API request/response
- **ERROR level**: All error conditions with context

---

## Dependencies

- CV.numbers parsing: `services/cv_parser.py` (existing)
- Scholar API integration: Adapted from `fill_abstracts.py` (existing)
- PDF validation: `pypdfium2`
- Logging: `services/logger.py` (existing)
- Environment: `.env` file with `SCHOLAR_API_KEY`

---

## Examples

### Basic Audit

```bash
python _scripts/audit_pdfs.py
```

### Audit with Scholar Fetch

```bash
python _scripts/audit_pdfs.py --fetch-missing
```

### Verbose Audit with JSON Report

```bash
python _scripts/audit_pdfs.py --verbose --output-report audit_report.json
```

### Dry Run to Preview Fetch

```bash
python _scripts/audit_pdfs.py --fetch-missing --dry-run
```

### Custom Paths

```bash
python _scripts/audit_pdfs.py \
  --numbers-file ~/Documents/CV_backup.numbers \
  --pdf-dir /path/to/pdfs \
  --log-file audit.log
```

---

## Performance Expectations

- **Audit scan**: <1 second for 200 publications
- **Scholar fetch**: ~2 seconds per PDF (1s rate limit + download time)
- **Batch of 10 missing PDFs**: ~20 seconds
- **Memory usage**: <100 MB (no large file buffering)

---

## Testing

### Unit Tests

- `test_exact_match_logic()` - Verify only exact filenames match
- `test_ambiguous_detection()` - Verify suffixed files flagged as ambiguous
- `test_required_optional_logic()` - Verify year/kind determines requirement
- `test_exit_codes()` - Verify correct exit codes for scenarios

### Integration Tests

- `test_audit_workflow()` - End-to-end audit with fixture CV.numbers
- `test_fetch_workflow()` - Mock Scholar API, verify fetch logic
- `test_dry_run()` - Verify no filesystem writes in dry-run mode
- `test_json_report()` - Verify JSON output format

---

## Future Enhancements

- Support for batch PDF imports from directory
- Integration with ORCID for additional PDF sources
- Automatic DOI lookup for publications missing DOI field
- Parallel Scholar API fetching (with rate limit consideration)
