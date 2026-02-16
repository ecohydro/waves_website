# Quickstart Guide: Publication PDF Management and Image Generation

**Feature**: 004-publication-pdf-images
**Audience**: Website maintainers, developers
**Prerequisites**: Python 3.9+, CV.numbers file, Jekyll site setup

---

## Overview

This feature provides three CLI tools for managing publication PDFs and generating images:

1. **audit_pdfs.py** - Check PDF archive completeness, fetch missing PDFs
2. **generate_previews.py** - Generate preview images (first page) for publication listings
3. **extract_feature.py** - Extract feature images (specific figures) for publication detail pages

---

## Installation

### 1. Install Python Dependencies

```bash
cd /Users/kellycaylor/Documents/website/waves
pip install -r _scripts/requirements.txt
```

New dependencies added for Feature 004:
- `pypdfium2>=4.0.0` - PDF rendering
- `Pillow>=10.0.0` - Image processing

### 2. Set Up Scholar API Credentials (Optional)

Only required if using `--fetch-missing` flag with `audit_pdfs.py`:

```bash
# Create or edit .env file in repository root
echo "SCHOLAR_API_KEY=your_api_key_here" >> .env
```

### 3. Verify Directory Structure

Ensure these directories exist:

```bash
mkdir -p assets/pdfs/publications
mkdir -p assets/images/publications
```

### 4. Create Placeholder Image

Generate or place a generic placeholder image:

```bash
# Location: assets/images/publications/placeholder.png
# Recommended size: 480x640px (standard preview aspect ratio)
# Design: Simple graphic indicating "publication preview unavailable"
```

### 5. Configure Jekyll Fallback

Edit `_config.yml`:

```yaml
# Global fallback for missing publication images
teaser: /assets/images/publications/placeholder.png
```

---

## Common Workflows

### Workflow 1: Complete Setup for New Publication

**Scenario**: Adding a new publication with PDF and generating all images

```bash
# Step 1: Add publication to CV.numbers
# - Add row to "Publications" sheet
# - Include: Title, Authors, Year, DOI, Kind (RA/BC/CP)
# - Note the canonical_id (e.g., Caylor2024_1234)

# Step 2: Add PDF to archive
cp ~/Downloads/my_paper.pdf assets/pdfs/publications/Caylor2024_1234.pdf

# Step 3: Generate preview image (first page)
python _scripts/generate_previews.py Caylor2024_1234

# Step 4: Generate feature image (e.g., from page 5)
python _scripts/extract_feature.py Caylor2024_1234 --page 5

# Step 5: Verify
ls -lh assets/images/publications/Caylor2024_1234*.png
# Should show:
#   Caylor2024_1234.png       (preview)
#   Caylor2024_1234_figure.png (feature)

# Step 6: Build Jekyll site and verify display
bundle exec jekyll serve
# Visit http://localhost:4000/publications/
```

### Workflow 2: Audit Existing Archive

**Scenario**: Check which publications are missing PDFs or images

```bash
# Run comprehensive audit
python _scripts/audit_pdfs.py

# Sample output:
# PDF Archive Status:
#   Total publications:           215
#   PDFs found:                   187 (87.0%)
#   PDFs missing (required):       12
#   PDFs missing (optional):       16

# Review missing required PDFs (these need Scholar AI fetch or manual addition)
# Review missing optional PDFs (legacy publications, manual addition if available)
```

### Workflow 3: Fetch Missing PDFs from Scholar AI

**Scenario**: Automatically fetch missing research article PDFs

```bash
# Prerequisites: SCHOLAR_API_KEY set in .env

# Dry run to preview what would be fetched
python _scripts/audit_pdfs.py --fetch-missing --dry-run

# Perform actual fetch
python _scripts/audit_pdfs.py --fetch-missing

# Sample output:
# Fetching missing required PDFs from Scholar AI:
#   ✓ Successfully fetched Caylor2022_5678
#   ✓ Successfully fetched Smith2023_3456
#   ✗ Failed: Caylor2023_9012 (DOI not found)
#
# Fetch Summary:
#   Attempted:     12
#   Success:        8
#   Failed:         4
```

### Workflow 4: Batch Generate All Missing Preview Images

**Scenario**: Generate preview images for all publications that don't have them

```bash
# Check how many are missing
python _scripts/generate_previews.py --dry-run

# Generate all missing previews
python _scripts/generate_previews.py

# Sample output:
# Generating preview images:
#   ✓ Generated Caylor2022_5678.png (640x480)
#   ✗ Skipped Caylor2023_9012 (PDF not found)
#   ✓ Generated Smith2023_3456.png (640x495)
#   ...
#
# Summary:
#   Total scanned:     215
#   Already existed:   187
#   Generated:          22
#   Skipped (no PDF):    6
```

### Workflow 5: Regenerate Preview for Updated PDF

**Scenario**: PDF was updated and preview needs to be regenerated

```bash
# Regenerate with force flag
python _scripts/generate_previews.py --force Caylor2002_1378

# Or for multiple publications
python _scripts/generate_previews.py --force Caylor2002_1378 Smith2010_5678
```

### Workflow 6: Extract Feature Image with Crop

**Scenario**: Extract a specific figure from page 3, cropping to just the chart region

```bash
# Step 1: Identify crop coordinates (use PDF viewer with pixel coordinates)
# Example: Chart is at x=100, y=200, width=800, height=600

# Step 2: Extract with crop
python _scripts/extract_feature.py Caylor2022_5678 --page 3 --crop "100,200,800,600"

# Step 3: Verify result
open assets/images/publications/Caylor2022_5678_figure.png
```

### Workflow 7: Standardize PDF Naming

**Scenario**: Legacy PDFs with non-standard names need to be renamed

```bash
# Step 1: Audit to identify ambiguous files
python _scripts/audit_pdfs.py

# Sample output:
# Ambiguous Files (warnings):
#   - Caylor2002_1378_draft.pdf (use exact match: Caylor2002_1378.pdf)
#   - 1-s2.0-S0034425712002416-main.pdf (rename to canonical format)

# Step 2: Manually rename PDFs
mv assets/pdfs/publications/Caylor2002_1378_draft.pdf assets/pdfs/publications/Caylor2002_1378.pdf
mv assets/pdfs/publications/1-s2.0-S0034425712002416-main.pdf assets/pdfs/publications/Caylor2012_3456.pdf

# Step 3: Re-audit to verify
python _scripts/audit_pdfs.py
```

### Workflow 8: Generate JSON Report for Tracking

**Scenario**: Create structured report for monitoring or CI/CD

```bash
# Generate audit report with JSON output
python _scripts/audit_pdfs.py --output-report audit_report.json

# Parse with jq or import to monitoring system
cat audit_report.json | jq '.statistics'

# Sample output:
# {
#   "total_publications": 215,
#   "pdfs_found": 187,
#   "pdfs_missing_required": 12,
#   "pdfs_missing_optional": 16,
#   "coverage_percentage": 87.0
# }
```

---

## Tool Reference

### audit_pdfs.py

**Purpose**: Check PDF archive completeness, fetch missing PDFs

**Common Usage**:
```bash
# Basic audit
python _scripts/audit_pdfs.py

# Fetch missing required PDFs
python _scripts/audit_pdfs.py --fetch-missing

# Generate JSON report
python _scripts/audit_pdfs.py --output-report report.json

# Verbose logging
python _scripts/audit_pdfs.py --verbose --log-file audit.log
```

**Key Flags**:
- `--fetch-missing` - Attempt to fetch missing PDFs from Scholar AI
- `--dry-run` - Preview changes without making them
- `--output-report PATH` - Save detailed JSON report

**Exit Codes**:
- `0` - Success (all required PDFs present)
- `1` - Fatal error (CV.numbers not found, etc.)
- `2` - Partial success (some required PDFs missing)

### generate_previews.py

**Purpose**: Generate preview images (first page) from PDFs

**Common Usage**:
```bash
# Generate all missing previews
python _scripts/generate_previews.py

# Generate for specific publication(s)
python _scripts/generate_previews.py Caylor2022_5678

# Force regenerate existing
python _scripts/generate_previews.py --force Caylor2002_1378

# Dry run to preview
python _scripts/generate_previews.py --dry-run
```

**Key Flags**:
- `--force` - Regenerate even if image exists
- `--height INT` - Target height in pixels (default: 640)
- `--dry-run` - Preview changes without generating images

**Exit Codes**:
- `0` - Success (all images generated)
- `1` - Fatal error (output directory not writable)
- `2` - Partial success (some PDFs missing/corrupted)

### extract_feature.py

**Purpose**: Extract feature images (specific figures) from PDFs

**Common Usage**:
```bash
# Extract page 3 as feature image
python _scripts/extract_feature.py Caylor2022_5678 --page 3

# Extract with crop coordinates
python _scripts/extract_feature.py Caylor2022_5678 --page 3 --crop "100,200,800,600"

# Force overwrite without confirmation
python _scripts/extract_feature.py Caylor2002_1378 --page 5 --force

# Dry run to preview
python _scripts/extract_feature.py Caylor2022_5678 --page 3 --dry-run
```

**Key Flags**:
- `--page INT` - **Required** - Page number (1-indexed)
- `--crop "x,y,w,h"` - Crop coordinates in pixels
- `--max-dimension INT` - Max width/height (default: 640)
- `--force` - Skip overwrite confirmation

**Exit Codes**:
- `0` - Success (image extracted)
- `1` - Fatal error (PDF not found, invalid page)
- `2` - User cancelled (declined overwrite)

---

## Troubleshooting

### Issue: "PDF not found" for publication

**Symptom**: Tool reports missing PDF for publication that exists

**Solution**:
1. Check exact filename match: `Caylor2002_1378.pdf` (case-sensitive, no extra suffixes)
2. Run audit to see ambiguous files: `python _scripts/audit_pdfs.py`
3. Rename PDF to exact canonical_id format

### Issue: "Page X is out of range" when extracting feature

**Symptom**: Error extracting page from PDF

**Solution**:
1. Open PDF in viewer and check total page count
2. Use 1-indexed page number (first page is 1, not 0)
3. Ensure page number is within valid range

### Issue: Scholar AI fetch fails with authentication error

**Symptom**: `--fetch-missing` returns HTTP 401/403 errors

**Solution**:
1. Check `.env` file exists in repository root
2. Verify `SCHOLAR_API_KEY` is set correctly
3. Test API key with manual curl:
   ```bash
   curl -H "Authorization: Bearer $SCHOLAR_API_KEY" https://api.scholar.ai/...
   ```

### Issue: Generated images are wrong size

**Symptom**: Preview images not 640px height or feature images not respecting max dimension

**Solution**:
1. Check `--height` flag for generate_previews.py
2. Check `--max-dimension` flag for extract_feature.py
3. Verify PIL/Pillow version: `pip show Pillow` (should be 10.0.0+)

### Issue: Placeholder image not showing on website

**Symptom**: Broken image icon instead of placeholder

**Solution**:
1. Verify placeholder exists: `ls assets/images/publications/placeholder.png`
2. Check `_config.yml` has: `teaser: /assets/images/publications/placeholder.png`
3. Rebuild Jekyll site: `bundle exec jekyll build`
4. Check browser console for 404 errors

### Issue: Permission denied writing images

**Symptom**: Error when saving generated images

**Solution**:
1. Check output directory exists: `mkdir -p assets/images/publications`
2. Verify write permissions: `ls -ld assets/images/publications`
3. Run with sudo if needed (not recommended for production)

---

## Best Practices

### 1. Always Run Audit Before Batch Operations

```bash
# Get current state
python _scripts/audit_pdfs.py

# Then run batch generation
python _scripts/generate_previews.py
```

### 2. Use Dry Run for Large Batches

```bash
# Preview what will happen
python _scripts/generate_previews.py --dry-run

# Confirm, then execute
python _scripts/generate_previews.py
```

### 3. Keep PDFs in Exact Naming Format

- Use canonical_id exactly: `Caylor2002_1378.pdf`
- No suffixes: `_draft`, `_final`, `_v2`
- Case-sensitive: `Caylor` not `caylor`

### 4. Generate Preview Images First, Feature Images Later

Preview images are automated and high priority. Feature images require manual curation:

```bash
# Automated: Generate all missing previews
python _scripts/generate_previews.py

# Manual: Extract feature images one at a time
python _scripts/extract_feature.py Caylor2022_5678 --page 3
```

### 5. Track Audit Reports Over Time

```bash
# Generate timestamped reports
python _scripts/audit_pdfs.py --output-report "audit_$(date +%Y%m%d).json"

# Compare coverage over time
jq '.statistics.coverage_percentage' audit_*.json
```

### 6. Use Version Control for Images

```bash
# Stage generated images
git add assets/images/publications/

# Commit with descriptive message
git commit -m "Add preview images for 2023-2024 publications"

# Push to remote
git push origin 004-publication-pdf-images
```

---

## Integration with Jekyll

### Image Display in Templates

Publications use the three-level fallback chain automatically:

1. **Feature image** (publication detail pages)
   - Frontmatter: `header.feature_image: assets/images/publications/Caylor2022_5678_figure.png`
   - Or inline: `![figure]({{ "assets/images/publications/Caylor2022_5678_figure.png" | absolute_url }})`

2. **Preview image** (publication listings)
   - Frontmatter: `header.teaser: assets/images/publications/Caylor2022_5678.png`
   - Template: `archive-single.html` uses `post.header.teaser`

3. **Placeholder** (global fallback)
   - Config: `teaser: /assets/images/publications/placeholder.png` in `_config.yml`
   - Applied automatically if both feature and preview missing

### Rebuilding Site After Image Generation

```bash
# Generate images
python _scripts/generate_previews.py

# Rebuild Jekyll site
bundle exec jekyll build

# Or serve for local preview
bundle exec jekyll serve

# Visit http://localhost:4000/publications/
```

---

## Maintenance Schedule

### Weekly

- Run audit to check for new publications missing PDFs/images
- Generate preview images for new publications

```bash
python _scripts/audit_pdfs.py
python _scripts/generate_previews.py
```

### Monthly

- Attempt to fetch missing required PDFs from Scholar AI
- Generate JSON report for tracking

```bash
python _scripts/audit_pdfs.py --fetch-missing
python _scripts/audit_pdfs.py --output-report "audit_$(date +%Y%m).json"
```

### As Needed

- Extract feature images for newly curated publications
- Regenerate previews when PDFs are updated
- Standardize legacy PDF naming

---

## Getting Help

### Verbose Logging

Add `--verbose` flag to see detailed operations:

```bash
python _scripts/audit_pdfs.py --verbose
```

### Log Files

Save logs for later review:

```bash
python _scripts/generate_previews.py --log-file preview_gen.log
```

### Dry Run Mode

Always available to preview changes:

```bash
python _scripts/<tool>.py --dry-run
```

### Tool Help

Display usage information:

```bash
python _scripts/audit_pdfs.py --help
python _scripts/generate_previews.py --help
python _scripts/extract_feature.py --help
```

---

## Next Steps

After completing Feature 004 setup:

1. **Generate all missing preview images**
   ```bash
   python _scripts/generate_previews.py
   ```

2. **Audit and fetch missing PDFs**
   ```bash
   python _scripts/audit_pdfs.py --fetch-missing
   ```

3. **Verify Jekyll site displays correctly**
   ```bash
   bundle exec jekyll serve
   ```

4. **Commit and push changes**
   ```bash
   git add assets/images/publications/ assets/pdfs/publications/
   git commit -m "Complete Feature 004: Publication PDF and image management"
   git push origin 004-publication-pdf-images
   ```

5. **Create pull request**
   ```bash
   gh pr create --title "Feature 004: Publication PDF Management and Image Generation"
   ```
