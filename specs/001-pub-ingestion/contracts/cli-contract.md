# CLI Contract: ingest_publications.py

**Branch**: `001-pub-ingestion` | **Date**: 2026-01-29

## Command Interface

```
python _scripts/ingest_publications.py [OPTIONS]
```

### Options

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--dry-run` | `-n` | bool | false | Preview mode: report what would be created without writing files |
| `--numbers-file` | `-f` | path | `~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers` | Path to the CV.numbers file |
| `--output-dir` | `-o` | path | `_publications/` | Directory to write new publication files |
| `--authors-file` | `-a` | path | `_data/authors.yml` | Path to the authors registry YAML |
| `--verbose` | `-v` | bool | false | Show detailed output for each publication processed |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (publications created or none needed) |
| 1 | Error (file not found, parse failure, or other fatal error) |
| 2 | Partial success (some publications created, some had warnings) |

## Output Contract

### Standard Mode (no flags)

```
Reading CV.numbers from /Users/.../CV.numbers
Found 159 publications in spreadsheet (142 published)
Scanning _publications/ for existing entries... 137 found

Results:
  Matched (skipped):  132
  Created:              10
  Skipped (non-P):      17
  Warnings:              3

Warnings:
  ⚠ "Paper Title Here" (2024) - missing abstract
  ⚠ "Another Paper" (2023) - missing DOI
  ⚠ "Third Paper" (2025) - missing author list

New files created:
  _publications/Krell2024_3847.md
  _publications/Caylor2025_5192.md
  ... (8 more)
```

### Dry-Run Mode (`--dry-run`)

```
Reading CV.numbers from /Users/.../CV.numbers
Found 159 publications in spreadsheet (142 published)
Scanning _publications/ for existing entries... 137 found

DRY RUN - No files will be written

Would create 10 new publication entries:
  1. Krell, N. et al. (2024) - "Paper Title Here"
  2. Caylor, K. et al. (2025) - "Another Paper Title"
  ... (8 more)

Warnings:
  ⚠ "Paper Title Here" (2024) - missing abstract
  ...

Summary:
  Would match (skip):  132
  Would create:         10
  Would skip (non-P):   17
```

### All Up-to-Date

```
Reading CV.numbers from /Users/.../CV.numbers
Found 159 publications in spreadsheet (142 published)
Scanning _publications/ for existing entries... 142 found

All publications are up to date. No new entries needed.
```

### Error: File Not Found

```
Error: CV.numbers file not found at /Users/.../CV.numbers
Check that iCloud Drive is synced and the file exists.
```

## Input Validation

| Input | Validation | On Failure |
|-------|-----------|------------|
| Numbers file path | File exists and is readable | Exit code 1 with error message |
| Publications sheet | Sheet named "Publications" exists | Exit code 1: `Sheet "Publications" not found in CV.numbers` |
| Output directory | Directory exists | Exit code 1: `Output directory not found: {path}` |
| Authors file | File exists and is valid YAML | Exit code 1: `Authors file not found or invalid: {path}` |
| Spreadsheet row | Has title and year at minimum | Skip row; log warning if verbose |
