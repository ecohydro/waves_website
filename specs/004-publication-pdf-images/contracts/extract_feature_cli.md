# CLI Contract: extract_feature.py

**Purpose**: Extract feature images (specific pages/figures) from publication PDFs

**Location**: `_scripts/extract_feature.py`

---

## Command Signature

```bash
python _scripts/extract_feature.py PUBLICATION_ID --page PAGE_NUMBER [OPTIONS]
```

---

## Arguments

### Required

| Argument | Type | Description |
|----------|------|-------------|
| `PUBLICATION_ID` | str | Canonical ID of publication (e.g., Caylor2022_5678) |
| `--page` | int | Page number to extract (1-indexed, required) |

### Optional

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--pdf-dir` | Path | `assets/pdfs/publications/` | Directory containing PDF files |
| `--output-dir` | Path | `assets/images/publications/` | Directory for generated images |
| `--crop` | str | None | Crop coordinates as "x,y,width,height" in pixels |
| `--max-dimension` | int | 640 | Maximum dimension (width or height) in pixels |
| `--force` | Flag | False | Overwrite existing feature image without confirmation |
| `--no-confirm` | Flag | False | Skip confirmation prompt if feature image exists |
| `--dry-run` | Flag | False | Show what would be done without generating image |
| `--verbose` | Flag | False | Enable verbose logging (DEBUG level) |
| `--log-file` | Path | None | Write logs to file (in addition to console) |

---

## Exit Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 0 | Success | Feature image extracted successfully |
| 1 | Fatal error | PDF not found, page number invalid, output directory not writable |
| 2 | User cancelled | User declined overwrite confirmation |

---

## Output Format

### Console Output (Normal Operation)

```bash
$ python _scripts/extract_feature.py Caylor2022_5678 --page 3
```

```
=== Feature Image Extraction ===
Publication: Caylor2022_5678
Page: 3
Output: assets/images/publications/Caylor2022_5678_figure.png

  ⏳ Loading PDF...
  ✓ PDF loaded (12 pages)
  ⏳ Rendering page 3...
  ✓ Rendered (1800x1200 original)
  ⏳ Resizing to max dimension 640px...
  ✓ Resized (640x427)
  ⏳ Saving feature image...
  ✓ Saved (186 KB)

✓ Feature image extracted successfully
```

### Console Output (With Crop)

```bash
$ python _scripts/extract_feature.py Caylor2022_5678 --page 3 --crop "100,200,800,600"
```

```
=== Feature Image Extraction ===
Publication: Caylor2022_5678
Page: 3
Crop: (100, 200, 800, 600)
Output: assets/images/publications/Caylor2022_5678_figure.png

  ⏳ Loading PDF...
  ✓ PDF loaded (12 pages)
  ⏳ Rendering page 3...
  ✓ Rendered (1800x1200 original)
  ⏳ Cropping to specified region...
  ✓ Cropped (800x600)
  ⏳ Resizing to max dimension 640px...
  ✓ Resized (640x480)
  ⏳ Saving feature image...
  ✓ Saved (124 KB)

✓ Feature image extracted successfully
```

### Console Output (Overwrite Confirmation)

```bash
$ python _scripts/extract_feature.py Caylor2002_1378 --page 5
```

```
=== Feature Image Extraction ===
Publication: Caylor2002_1378
Page: 5

⚠️  Feature image already exists:
    assets/images/publications/Caylor2002_1378_figure.png

Overwrite existing image? [y/N]: y

  ⏳ Loading PDF...
  ✓ PDF loaded (8 pages)
  ⏳ Rendering page 5...
  ✓ Rendered (1200x1600 original)
  ⏳ Resizing to max dimension 640px...
  ✓ Resized (480x640)
  ⏳ Saving feature image...
  ✓ Saved (198 KB)

✓ Feature image extracted successfully
```

### Console Output (User Cancels)

```
Overwrite existing image? [y/N]: n

⚠️  Operation cancelled by user
```

Exit code: 2

### Dry Run Output

```bash
$ python _scripts/extract_feature.py Caylor2022_5678 --page 3 --dry-run
```

```
=== Feature Image Extraction (DRY RUN) ===
No files will be written

Publication: Caylor2022_5678
Page: 3
PDF: assets/pdfs/publications/Caylor2022_5678.pdf
Output: assets/images/publications/Caylor2022_5678_figure.png

Validation:
  ✓ PDF exists
  ✓ Page 3 is valid (PDF has 12 pages)
  ✓ Output directory is writable
  ℹ️  Feature image does not exist (would create new)

Would perform:
  1. Load PDF (Caylor2022_5678.pdf)
  2. Render page 3 (estimated 1800x1200)
  3. Resize to max dimension 640px
  4. Save as PNG (estimated 150-200 KB)

ℹ️  No changes made (dry run mode)
```

---

## Behavior Details

### Page Number Handling

- **1-indexed**: Page 1 is the first page (user-friendly convention)
- **Validation**: Page number must be between 1 and total page count
- **Error if invalid**: Exit 1 with clear error message

```bash
$ python _scripts/extract_feature.py Caylor2022_5678 --page 20
```
```
✗ Error: Page 20 is out of range (PDF has 12 pages)
```

### Crop Coordinates

**Format**: `"x,y,width,height"` in pixels (comma-separated, quoted)

- `x`: Left edge of crop region (0 = left edge of page)
- `y`: Top edge of crop region (0 = top of page)
- `width`: Width of crop region in pixels
- `height`: Height of crop region in pixels

**Example**: `--crop "100,200,800,600"` crops region starting at (100, 200) with size 800x600

**Validation**:
- All values must be non-negative integers
- Crop region must fit within rendered page bounds
- Error if crop extends beyond page: Exit 1 with error message

### Resize Logic

**Max dimension constraint**: Scale image so largest dimension (width or height) is at most `--max-dimension`

**Examples**:
- 1800x1200 image → 640x427 (width is limiting dimension)
- 1200x1600 image → 480x640 (height is limiting dimension)
- 1200x1200 image → 640x640 (square, both dimensions at max)

**Aspect ratio**: Always preserved (no cropping, no letterboxing)

### Overwrite Protection

**Default behavior** (no flags):
- If feature image exists, prompt user: `Overwrite existing image? [y/N]:`
- User enters `y` or `yes` → proceed with extraction
- User enters `n`, `no`, or presses Enter → exit with code 2

**With `--force` flag**:
- Skip confirmation prompt
- Overwrite existing image immediately

**With `--no-confirm` flag**:
- Skip confirmation prompt
- Proceed with extraction (same as `--force`)

**Difference between `--force` and `--no-confirm`**:
- Semantically identical for this tool
- `--force` is more explicit about "overwriting"
- `--no-confirm` is more explicit about "skip prompt"
- Either flag achieves same result

---

## Performance Expectations

- **Single page extraction**: ~0.3-0.5 seconds (render + crop + resize + save)
- **With crop**: ~0.4-0.6 seconds (additional crop operation)
- **Memory usage**: <100 MB (single page buffering)
- **Disk I/O**: Write ~100-250 KB per image (PNG compression)

---

## Dependencies

- PDF rendering: `pypdfium2>=4.0.0`
- Image processing: `Pillow>=10.0.0`
- Logging: `services/logger.py` (existing)

---

## Examples

### Basic Extraction

```bash
python _scripts/extract_feature.py Caylor2022_5678 --page 3
```

### Extract with Crop

```bash
python _scripts/extract_feature.py Caylor2022_5678 --page 3 --crop "100,200,800,600"
```

### Force Overwrite Existing

```bash
python _scripts/extract_feature.py Caylor2002_1378 --page 5 --force
```

### Custom Max Dimension

```bash
python _scripts/extract_feature.py Caylor2022_5678 --page 3 --max-dimension 800
```

### Dry Run to Preview

```bash
python _scripts/extract_feature.py Caylor2022_5678 --page 3 --dry-run
```

### Verbose Logging

```bash
python _scripts/extract_feature.py Caylor2022_5678 --page 3 --verbose
```

---

## File Naming Convention

- **Input PDF**: `assets/pdfs/publications/{canonical_id}.pdf`
- **Output PNG**: `assets/images/publications/{canonical_id}_figure.png`
- **Example**: `Caylor2002_1378.pdf` (page 5) → `Caylor2002_1378_figure.png`

**Note**: Only one feature image per publication (subsequent extractions overwrite)

---

## Error Handling

### Fatal Errors (Exit 1)

| Error | Condition | Message |
|-------|-----------|---------|
| PDF not found | `{pdf_dir}/{canonical_id}.pdf` does not exist | `✗ Error: PDF not found: Caylor2022_5678.pdf` |
| Invalid page number | Page < 1 or page > total pages | `✗ Error: Page 20 is out of range (PDF has 12 pages)` |
| Crop out of bounds | Crop region extends beyond page | `✗ Error: Crop region (100,200,800,600) extends beyond page bounds (600x800)` |
| Output directory not writable | Permission denied or disk full | `✗ Error: Cannot write to output directory: Permission denied` |
| PDF corrupted | pypdfium2 cannot open PDF | `✗ Error: PDF corrupted or unreadable` |
| PDF password-protected | pypdfium2 detects password | `✗ Error: PDF is password-protected` |

### User Cancellation (Exit 2)

- User declines overwrite confirmation
- Message: `⚠️  Operation cancelled by user`

---

## Testing

### Unit Tests

- `test_page_extraction()` - Verify specific page renders correctly
- `test_crop_region()` - Verify crop coordinates applied correctly
- `test_resize_logic()` - Verify max dimension constraint
- `test_aspect_ratio()` - Verify aspect ratio preserved
- `test_overwrite_protection()` - Verify confirmation prompt
- `test_invalid_page_number()` - Verify error on out-of-range page
- `test_crop_out_of_bounds()` - Verify error on invalid crop

### Integration Tests

- `test_full_extraction()` - End-to-end extraction with fixture PDF
- `test_dry_run()` - Verify no filesystem writes
- `test_force_flag()` - Verify --force skips confirmation
- `test_exit_codes()` - Verify correct exit codes

---

## Edge Cases

### Single-Page PDFs

- Valid page number: 1
- Extracting page 2: Error (out of range)

### Very Large PDFs (100+ pages)

- No special handling (only renders requested page)
- Memory footprint same as small PDFs (single page rendering)

### Non-Standard Aspect Ratios

- Very wide (landscape charts): Max dimension limits width, height scales down
- Very tall (portrait figures): Max dimension limits height, width scales down
- Square figures: Both dimensions equal to max dimension

### Crop with Resize

Order of operations:
1. Render full page
2. Crop to specified region
3. Resize cropped region to max dimension

Example: 1800x1200 page → crop to 800x600 → resize to 640x480

---

## Interactive Mode (Future Enhancement)

**Not implemented in Phase 1, marked as optional/future in spec**

Potential future feature:
```bash
python _scripts/extract_feature.py Caylor2022_5678 --interactive
```

Would provide:
- Browse through PDF pages with thumbnails
- Select page visually
- Define crop region with mouse/keyboard
- Preview result before saving

---

## Logging Format

```
2026-01-30 14:45:22 INFO     extract_feature  Starting feature extraction
2026-01-30 14:45:22 INFO     extract_feature  Publication: Caylor2022_5678
2026-01-30 14:45:22 INFO     extract_feature  Page: 3
2026-01-30 14:45:22 DEBUG    pdf_processor    Loading PDF: Caylor2022_5678.pdf
2026-01-30 14:45:22 DEBUG    pdf_processor    PDF has 12 pages
2026-01-30 14:45:22 DEBUG    pdf_processor    Rendering page 3
2026-01-30 14:45:23 DEBUG    pdf_processor    Rendered size: 1800x1200
2026-01-30 14:45:23 DEBUG    image_generator  Resizing to max dimension 640px
2026-01-30 14:45:23 DEBUG    image_generator  Resized to: 640x427
2026-01-30 14:45:23 INFO     extract_feature  Saving to: Caylor2022_5678_figure.png
2026-01-30 14:45:23 INFO     extract_feature  ✓ Saved (186 KB)
```

---

## Configuration

### Environment Variables

None required.

### Config File Support

Future enhancement: Support for per-publication configuration in markdown frontmatter:

```yaml
header:
  teaser: assets/images/publications/Caylor2022_5678.png
  feature_image: assets/images/publications/Caylor2022_5678_figure.png
  feature_page: 3
  feature_crop: [100, 200, 800, 600]
```

Would allow:
```bash
python _scripts/extract_feature.py Caylor2022_5678 --from-frontmatter
```

---

## Comparison with generate_previews.py

| Feature | generate_previews.py | extract_feature.py |
|---------|---------------------|-------------------|
| **Target** | Batch processing (index pages) | Single publication (detail pages) |
| **Page** | Always first page (page 0) | User-specified page number |
| **Sizing** | Fixed height 640px | Max dimension 640px (width or height) |
| **Aspect ratio** | Varies (typically ~480x640) | Varies (depends on source) |
| **Crop support** | No | Yes (optional) |
| **Batch mode** | Yes (all missing) | No (one at a time) |
| **Overwrite protection** | --force flag only | Interactive confirmation + --force |
| **Output naming** | `{id}.png` | `{id}_figure.png` |
| **Use case** | Automated bulk generation | Manual curation |

---

## Future Enhancements

- Interactive mode for page selection and crop definition
- Support for extracting multiple pages/figures per publication
- Auto-detect figures in PDF (ML-based region detection)
- Batch extraction from CSV (publication_id, page, crop per row)
- Support for reading crop coordinates from publication frontmatter
