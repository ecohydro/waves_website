# Publication PDF Management and Image Generation Tools

This directory contains Python CLI tools for managing publication PDFs and generating images for the WAVES Lab website.

## Tools Overview

### 1. `audit_pdfs.py` - PDF Archive Auditing

Audits the PDF archive for completeness and optionally fetches missing PDFs from Scholar AI.

**Usage:**
```bash
python audit_pdfs.py [OPTIONS]
```

**Key Options:**
- `--fetch-missing` - Attempt to fetch missing required PDFs from Scholar AI
- `--output-report FILE` - Save detailed JSON report
- `--dry-run` - Preview without making changes
- `--verbose` - Enable debug logging

**Examples:**
```bash
# Basic audit
python audit_pdfs.py

# Audit and fetch missing PDFs
python audit_pdfs.py --fetch-missing

# Generate JSON report
python audit_pdfs.py --output-report audit.json

# Preview with verbose output
python audit_pdfs.py --dry-run --verbose
```

**Requirements:**
- CV.numbers file with Publications sheet
- PDFs directory: `assets/pdfs/publications/`
- SCHOLAR_API_KEY environment variable (for --fetch-missing)

### 2. `generate_previews.py` - Preview Image Generation

Generates preview images (first page of PDF) for publication listings.

**Usage:**
```bash
python generate_previews.py [PUBLICATION_IDS...] [OPTIONS]
```

**Key Options:**
- `--force` - Regenerate even if image exists
- `--height N` - Target height in pixels (default: 640)
- `--dry-run` - Preview without generating

**Examples:**
```bash
# Generate all missing preview images
python generate_previews.py

# Generate for specific publication
python generate_previews.py Caylor2022_5678

# Force regenerate existing image
python generate_previews.py --force Caylor2002_1378

# Preview what would be generated
python generate_previews.py --dry-run
```

**Requirements:**
- PDFs directory: `assets/pdfs/publications/`
- Output directory: `assets/images/publications/`

### 3. `extract_feature.py` - Feature Image Extraction

Extracts feature images (specific figures) from publication PDFs.

**Usage:**
```bash
python extract_feature.py PUBLICATION_ID --page PAGE [OPTIONS]
```

**Key Options:**
- `--page N` - Page number to extract (1-indexed, required)
- `--crop "x,y,w,h"` - Crop coordinates in pixels
- `--max-dimension N` - Max width/height (default: 640)
- `--force` - Skip overwrite confirmation

**Examples:**
```bash
# Extract page 3 as feature image
python extract_feature.py Caylor2022_5678 --page 3

# Extract with crop
python extract_feature.py Caylor2022_5678 --page 3 --crop "100,200,800,600"

# Force overwrite without confirmation
python extract_feature.py Caylor2002_1378 --page 5 --force

# Preview extraction
python extract_feature.py Caylor2022_5678 --page 3 --dry-run
```

**Requirements:**
- PDF must exist in `assets/pdfs/publications/`
- Output directory: `assets/images/publications/`

## Installation

### 1. Install Dependencies

```bash
cd _scripts
pip install -r requirements.txt
```

Required packages:
- `pypdfium2>=4.0.0` - PDF rendering
- `Pillow>=10.0.0` - Image processing
- `numbers-parser` - CV.numbers parsing
- `python-frontmatter` - Markdown frontmatter
- `python-dotenv` - Environment variables
- Other existing dependencies

### 2. Configure Environment

Create `.env` file in repository root (optional, only for Scholar AI fetch):

```bash
# For PDF fetching via Scholar AI
SCHOLAR_API_KEY=your_api_key_here
```

### 3. Verify Directories

Ensure these directories exist:

```bash
mkdir -p assets/pdfs/publications
mkdir -p assets/images/publications
```

## File Naming Conventions

**IMPORTANT:** PDF and image files must use exact canonical ID matching.

### Canonical ID Pattern

Format: `AuthorYear_XXXX`
- Example: `Caylor2002_1378`
- Pattern: First author's last name + year + 4-digit number

### File Naming

- **PDF**: `{canonical_id}.pdf` (exact match required)
  - ✓ Valid: `Caylor2002_1378.pdf`
  - ✗ Invalid: `Caylor2002_1378_draft.pdf` (ambiguous)
  - ✗ Invalid: `caylor2002_1378.pdf` (wrong case)

- **Preview Image**: `{canonical_id}.png`
  - Example: `Caylor2002_1378.png`

- **Feature Image**: `{canonical_id}_figure.png`
  - Example: `Caylor2002_1378_figure.png`

## Workflows

### Complete Setup for New Publication

```bash
# 1. Add to CV.numbers Publications sheet
# 2. Add PDF to archive
cp ~/Downloads/paper.pdf assets/pdfs/publications/Caylor2024_1234.pdf

# 3. Generate preview image
python _scripts/generate_previews.py Caylor2024_1234

# 4. Extract feature image
python _scripts/extract_feature.py Caylor2024_1234 --page 5

# 5. Verify images exist
ls -lh assets/images/publications/Caylor2024_1234*
```

### Audit and Fetch Missing PDFs

```bash
# Check what's missing
python _scripts/audit_pdfs.py

# Fetch missing required PDFs from Scholar AI
python _scripts/audit_pdfs.py --fetch-missing

# Generate report
python _scripts/audit_pdfs.py --output-report audit_report.json
```

### Batch Generate All Missing Previews

```bash
# Check what would be generated
python _scripts/generate_previews.py --dry-run

# Generate all missing previews
python _scripts/generate_previews.py

# Regenerate specific images
python _scripts/generate_previews.py --force Caylor2002_1378 Smith2010_5678
```

## Image Specifications

### Preview Images (First Page)

- **Purpose**: Publication listings/index pages
- **Naming**: `{canonical_id}.png`
- **Dimensions**: Fixed height 640px, width varies proportionally
- **Typical Size**: ~480x640px for standard academic PDFs
- **Source**: First page (page 0) of PDF

### Feature Images (Selected Figures)

- **Purpose**: Publication detail pages
- **Naming**: `{canonical_id}_figure.png`
- **Dimensions**: Max dimension 640px (width or height)
- **Source**: Specific page selected by user, optional crop

### Placeholder Image

- **Purpose**: Fallback when images missing
- **Location**: `assets/images/publications/placeholder.png`
- **Fallback Chain**: Feature → Preview → Placeholder

## Troubleshooting

### "PDF not found" Error

**Problem**: Tool reports PDF missing for existing file

**Solution**:
1. Check exact filename: `Caylor2002_1378.pdf` (case-sensitive)
2. Run audit to see ambiguous files: `python audit_pdfs.py`
3. Rename to exact canonical_id format (no suffixes)

### Scholar AI Fetch Fails

**Problem**: `--fetch-missing` returns authentication errors

**Solution**:
1. Check `.env` file exists in repository root
2. Verify `SCHOLAR_API_KEY` is set correctly
3. Test API key with curl

### Page Out of Range Error

**Problem**: "Page X out of range" when extracting feature

**Solution**:
1. Check total pages in PDF viewer
2. Use 1-indexed page numbers (first page is 1, not 0)
3. Verify page number is within valid range

### Permission Denied

**Problem**: Cannot write to output directory

**Solution**:
1. Verify directories exist: `mkdir -p assets/images/publications`
2. Check write permissions: `ls -ld assets/images/publications`
3. Run from repository root (not _scripts/)

## Exit Codes

All tools use consistent exit codes:

- `0` - Success (all operations completed)
- `1` - Fatal error (CV.numbers not found, PDF directory inaccessible)
- `2` - Partial success (some errors occurred, but some operations succeeded)

## Logging

All tools support logging options:

```bash
# Verbose console output
python audit_pdfs.py --verbose

# Write to log file
python audit_pdfs.py --log-file audit.log

# Both verbose and file logging
python audit_pdfs.py --verbose --log-file audit.log
```

Log levels:
- Default: INFO (summary information)
- Verbose: DEBUG (detailed operations)
- Always: ERROR (errors with context)

## Architecture

### Models (`models/`)

- `publication.py` - Publication entity with validation
- `pdf_archive.py` - PDF archive scanning and matching
- `image_log.py` - Image generation operation tracking
- `scholar_result.py` - Scholar AI fetch result tracking

### Services (`services/`)

- `pdf_processor.py` - PDF rendering using pypdfium2
- `image_generator.py` - Image manipulation using Pillow
- `cv_parser.py` - CV.numbers file parsing
- `scholar_fetcher.py` - Scholar AI PDF fetching
- `logger.py` - Logging setup (existing)

### CLI Tools (`_scripts/`)

- `audit_pdfs.py` - PDF archive auditing (User Story 1)
- `generate_previews.py` - Preview image generation (User Story 2)
- `extract_feature.py` - Feature image extraction (User Story 3)

## Version Information

Dependencies:
- Python: 3.9+
- pypdfium2: 4.0.0+
- Pillow: 10.0.0+

Check installed versions:

```bash
python --version
python -c "import pypdfium2; print(f'pypdfium2: {pypdfium2.__version__}')"
python -c "import PIL; print(f'Pillow: {PIL.__version__}')"
```

## Additional Documentation

- Full specification: `specs/004-publication-pdf-images/spec.md`
- Implementation plan: `specs/004-publication-pdf-images/plan.md`
- Quickstart guide: `specs/004-publication-pdf-images/quickstart.md`
- CLI contracts: `specs/004-publication-pdf-images/contracts/`

## Support

For issues or questions:
1. Check quickstart guide for common workflows
2. Review troubleshooting section above
3. Run tools with `--verbose --dry-run` to diagnose
4. Check log files for detailed error messages
