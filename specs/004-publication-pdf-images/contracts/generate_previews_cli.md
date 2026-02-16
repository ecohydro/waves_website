# CLI Contract: generate_previews.py

**Purpose**: Generate preview images (first page) from publication PDFs

**Location**: `_scripts/generate_previews.py`

---

## Command Signature

```bash
python _scripts/generate_previews.py [OPTIONS] [PUBLICATION_IDS...]
```

---

## Arguments

### Positional

| Argument | Type | Description |
|----------|------|-------------|
| `PUBLICATION_IDS` | str (variadic) | One or more publication IDs to process. If empty, processes all publications with missing preview images |

### Optional

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--numbers-file` | Path | `~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers` | Path to CV.numbers file |
| `--pdf-dir` | Path | `assets/pdfs/publications/` | Directory containing PDF files |
| `--output-dir` | Path | `assets/images/publications/` | Directory for generated images |
| `--height` | int | 640 | Target height in pixels |
| `--force` | Flag | False | Regenerate images even if they already exist |
| `--dry-run` | Flag | False | Show what would be done without generating images |
| `--verbose` | Flag | False | Enable verbose logging (DEBUG level) |
| `--log-file` | Path | None | Write logs to file (in addition to console) |

---

## Exit Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 0 | Success | All requested images generated successfully |
| 1 | Fatal error | PDF directory inaccessible, output directory not writable, or required dependencies missing |
| 2 | Partial success | Some images generated but some failed (PDF errors, missing PDFs) |

---

## Output Format

### Console Output (Batch Mode - No Publication IDs)

```
=== Preview Image Generation ===
Scanning publications...
Found 215 publications

Checking for missing preview images...
  Missing: 28 publications need preview images
  Existing: 187 publications already have preview images

Generating preview images:
  ⏳ Processing Caylor2022_5678...
  ✓ Generated Caylor2022_5678.png (640x480)
  ⏳ Processing Caylor2023_9012...
  ✗ Skipped (PDF not found)
  ⏳ Processing Smith2023_3456...
  ✓ Generated Smith2023_3456.png (640x495)
  ...

Summary:
  Total scanned:     215
  Already existed:   187
  Generated:          22
  Skipped (no PDF):    6
  Errors:              0

✓ Preview generation complete
```

### Console Output (Single Publication Mode)

```bash
$ python _scripts/generate_previews.py Caylor2022_5678
```

```
=== Preview Image Generation ===
Processing publication: Caylor2022_5678

  ⏳ Rendering first page from PDF...
  ✓ Rendered page (1200x900 original)
  ⏳ Resizing to 640px height...
  ✓ Resized (640x480)
  ⏳ Saving to assets/images/publications/Caylor2022_5678.png...
  ✓ Saved (142 KB)

✓ Successfully generated preview image
```

### Console Output (Force Regenerate)

```bash
$ python _scripts/generate_previews.py --force Caylor2002_1378
```

```
=== Preview Image Generation (Force) ===
Processing publication: Caylor2002_1378

⚠️  Preview image already exists: assets/images/publications/Caylor2002_1378.png
⚠️  Force flag set - regenerating

  ⏳ Rendering first page from PDF...
  ✓ Rendered page (1200x900 original)
  ⏳ Resizing to 640px height...
  ✓ Resized (640x480)
  ⏳ Saving to assets/images/publications/Caylor2002_1378.png...
  ✓ Saved (145 KB)

✓ Successfully regenerated preview image
```

### Dry Run Output

```bash
$ python _scripts/generate_previews.py --dry-run
```

```
=== Preview Image Generation (DRY RUN) ===
No files will be written

Scanning publications...
Found 215 publications

Checking for missing preview images...
  Missing: 28 publications need preview images

Would generate:
  - Caylor2022_5678.png (PDF exists)
  - Smith2023_3456.png (PDF exists)
  - Jones2024_7890.png (PDF exists)
  ...

Would skip:
  - Brown2023_1234 (PDF not found)
  - Davis2024_5678 (PDF not found)
  ...

Summary:
  Would generate:    22 images
  Would skip:         6 publications (no PDF)

ℹ️  No changes made (dry run mode)
```

---

## Behavior Details

### Image Generation Process

For each publication:

1. **Check existing**: If preview image exists and `--force` not set, skip
2. **Find PDF**: Look for exact match `{canonical_id}.pdf`
3. **Render first page**: Use pypdfium2 to render page 0 as bitmap
4. **Calculate scale**: `scale = target_height / source_height`
5. **Resize proportionally**: Width adjusts to maintain aspect ratio
6. **Save as PNG**: Write to `{output_dir}/{canonical_id}.png`
7. **Log result**: Record success or failure with details

### Aspect Ratio Handling

- **Target**: 640px height (fixed)
- **Width**: Varies proportionally based on source aspect ratio
- **Typical result**: ~480px width for standard academic PDFs (letter/A4)
- **No cropping**: Full page rendered, aspect ratio preserved
- **No letterboxing**: No padding added

### Batch vs Single Mode

**Batch mode** (no publication IDs specified):
- Process ALL publications with missing preview images
- Skip publications that already have images (unless --force)
- Continue on errors (individual PDF failures don't stop batch)

**Single/Multi mode** (publication IDs specified):
- Process ONLY the specified publications
- Skip if image exists (unless --force)
- Exit on first fatal error (PDF directory inaccessible, etc.)

### Error Handling

**Non-fatal errors** (log, skip, continue):
- PDF not found for publication
- PDF corrupted or unreadable
- PDF password-protected
- PDF has zero pages
- Permission denied reading PDF

**Fatal errors** (exit 1):
- PDF directory does not exist
- Output directory not writable
- pypdfium2 library not installed
- Disk space exhausted during write

---

## Performance Expectations

- **Single image generation**: ~0.5 seconds (render + resize + save)
- **Batch of 50 images**: ~25-30 seconds (~10-12 images/minute)
- **Memory usage**: <50 MB (single page buffering)
- **Disk I/O**: Write ~100-200 KB per image (PNG compression)

---

## Dependencies

- PDF rendering: `pypdfium2>=4.0.0`
- Image processing: `Pillow>=10.0.0`
- CV.numbers parsing: `services/cv_parser.py` (existing)
- Logging: `services/logger.py` (existing)

---

## Examples

### Generate All Missing Previews

```bash
python _scripts/generate_previews.py
```

### Generate Preview for Single Publication

```bash
python _scripts/generate_previews.py Caylor2022_5678
```

### Generate Previews for Multiple Publications

```bash
python _scripts/generate_previews.py Caylor2022_5678 Smith2023_3456 Jones2024_7890
```

### Force Regenerate Existing Preview

```bash
python _scripts/generate_previews.py --force Caylor2002_1378
```

### Dry Run to Preview Changes

```bash
python _scripts/generate_previews.py --dry-run
```

### Custom Height

```bash
python _scripts/generate_previews.py --height 800
```

### Verbose Logging with Log File

```bash
python _scripts/generate_previews.py --verbose --log-file preview_gen.log
```

---

## File Naming Convention

- **Input PDF**: `assets/pdfs/publications/{canonical_id}.pdf`
- **Output PNG**: `assets/images/publications/{canonical_id}.png`
- **Example**: `Caylor2002_1378.pdf` → `Caylor2002_1378.png`

---

## Testing

### Unit Tests

- `test_image_generation()` - Verify PDF page renders to correct size
- `test_aspect_ratio_preservation()` - Verify width adjusts proportionally
- `test_force_overwrite()` - Verify --force regenerates existing images
- `test_skip_existing()` - Verify existing images skipped by default
- `test_error_handling()` - Verify corrupted/missing PDFs handled gracefully

### Integration Tests

- `test_batch_generation()` - End-to-end batch with fixture PDFs
- `test_single_generation()` - Single publication workflow
- `test_dry_run()` - Verify no filesystem writes
- `test_exit_codes()` - Verify correct exit codes for scenarios

---

## Edge Cases

### Non-Standard Page Sizes

- **Landscape pages**: Width becomes limiting dimension at 640px height
- **Portrait pages**: Standard behavior (~480px width)
- **Square pages**: 640x640 output
- **Very wide pages** (e.g., posters): May exceed 1000px width

### Corrupted PDFs

- Log error with publication ID and error message
- Skip to next publication in batch
- Do not create partial/empty image files

### Password-Protected PDFs

- Detect via pypdfium2 exception
- Log error with publication ID
- Skip to next publication in batch

### Zero-Byte or Empty PDFs

- Detect during rendering (zero pages)
- Log error with publication ID
- Skip to next publication in batch

---

## Configuration

### Environment Variables

None required. All configuration via CLI arguments.

### Config File Support

Future enhancement: Support for `.preview_config.yaml` with:
- Default height
- Output format (PNG/JPEG)
- Compression level
- Default directories

---

## Logging Format

```
2026-01-30 14:32:10 INFO     generate_previews Starting preview generation
2026-01-30 14:32:10 INFO     generate_previews Scanning 215 publications
2026-01-30 14:32:10 INFO     generate_previews Found 28 missing preview images
2026-01-30 14:32:11 INFO     generate_previews Processing Caylor2022_5678
2026-01-30 14:32:11 DEBUG    pdf_processor    Rendering page 0 of Caylor2022_5678.pdf
2026-01-30 14:32:11 DEBUG    pdf_processor    Original size: 1200x900
2026-01-30 14:32:11 DEBUG    image_generator  Resizing to 640x480
2026-01-30 14:32:11 INFO     generate_previews ✓ Generated Caylor2022_5678.png (142 KB)
2026-01-30 14:32:12 INFO     generate_previews Processing Caylor2023_9012
2026-01-30 14:32:12 ERROR    generate_previews ✗ PDF not found: Caylor2023_9012.pdf
2026-01-30 14:32:12 INFO     generate_previews Skipping Caylor2023_9012
```

---

## Future Enhancements

- Parallel image generation (thread pool for I/O-bound operations)
- Support for JPEG output format (faster, smaller files)
- Configurable DPI for higher quality rendering
- Progress bar for batch operations (tqdm integration)
- Automatic retry on transient file system errors
