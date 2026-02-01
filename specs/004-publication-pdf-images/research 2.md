# Phase 0 Research: Publication PDF Management and Image Generation

**Date**: 2026-01-30
**Feature**: 004-publication-pdf-images

## Research Questions Addressed

1. Best Python library for PDF to image conversion
2. Existing _scripts/ infrastructure and reuse opportunities
3. Jekyll template structure and image fallback mechanisms

---

## Decision 1: PDF Rendering Library

### Decision: **pypdfium2**

### Rationale

pypdfium2 provides the optimal balance of licensing, performance, installation simplicity, and quality for this academic use case:

1. **License Compatibility (CRITICAL)**: Apache 2.0 license - ideal for academic use with no proprietary code restrictions, unlike PyMuPDF's AGPL requirement which would require open-sourcing all related code or purchasing a commercial license

2. **Installation Simplicity**: Single pip install with no external system dependencies. Unlike pdf2image which requires Poppler installation via Homebrew (macOS), apt (Linux), or manual builds (Windows) - a common deployment blocker

3. **Performance**: Near-PyMuPDF speeds (~45ms per page vs 42ms), excellent for batch processing 50+ PDFs. Significantly faster than pdf2image

4. **Image Quality**: Excellent rendering at 640px with configurable scale factors. Produces high-quality PNG output suitable for web display

5. **Edge Case Handling**: Robust password protection detection, corruption handling, and non-standard page size support

6. **No Path Configuration**: Unlike pdf2image's Poppler path issues (common problem in PythonAnywhere, Streamlit, academic cluster environments), pypdfium2 automatically downloads PDFium binaries and works immediately

### Alternatives Considered

**PyMuPDF (fitz)**:
- **Why rejected**: AGPL v3.0 licensing incompatible with proprietary academic infrastructure without commercial license purchase. Fastest performance but license constraints are a blocker
- Would require: Open-sourcing entire codebase OR purchasing Artifex commercial license

**pdf2image (Poppler wrapper)**:
- **Why rejected**: Requires external Poppler installation (brew install poppler on macOS), creating deployment complexity. Slower than alternatives (especially for PNG output). Numerous reported issues in academic/cloud environments
- Would require: System dependency management, PATH configuration, platform-specific installation instructions

**pdfplumber**:
- **Why rejected**: Not designed for full-page rendering - intended for text/table extraction and page visualization only. Cannot reliably reconstruct page rendering

### Implementation Pattern

```python
import pypdfium2 as pdfium
from PIL import Image

def render_pdf_page(pdf_path: str, page_num: int = 0, target_height: int = 640) -> Image:
    """Render a single PDF page to PIL Image at specified height"""
    doc = pdfium.PdfDocument(pdf_path)
    page = doc[page_num]

    # Calculate scale factor for target height
    # pypdfium2 uses 72 DPI base resolution
    scale = target_height / page.get_size()[1]

    # Render page to bitmap
    bitmap = page.render(scale=scale)

    # Convert to PIL Image
    pil_image = bitmap.to_pil()

    return pil_image
```

### Dependencies

- `pypdfium2>=4.0.0` - PDF rendering
- `Pillow>=10.0.0` - Image processing (resize, crop, save)

---

## Decision 2: Code Reuse from Existing Features

### Decision: **Leverage 70-80% of existing _scripts/ infrastructure**

### Rationale

The _scripts/ directory has a mature, well-tested foundation from Features 001 (publication ingestion), 002 (Scholar abstract fill), and 003 (people sync). Reusing proven patterns reduces risk and accelerates implementation.

### Existing Components to Reuse (HIGH CONFIDENCE)

| Component | Location | Reuse Confidence | Usage |
|-----------|----------|------------------|--------|
| CV.numbers parsing | `services/cv_parser.py` | 95% | Read Publications sheet with DOI, kind, year fields |
| Scholar API integration | `fill_abstracts.py` | 85% | Adapt `query_scholar_api()` for PDF downloads |
| CLI argument parsing | All scripts | 95% | Standard argparse with --dry-run, --verbose, --numbers-file |
| Logging setup | `services/logger.py` | 100% | Console and file logging with DEBUG/INFO levels |
| Error handling patterns | All scripts | 95% | Try/except with meaningful error messages |
| Exit codes | All scripts | 100% | 0 (success), 1 (fatal), 2 (partial/warnings) |
| Batch processing patterns | `fill_abstracts.py` | 90% | Iterate, skip on error, continue, summary report |
| Frontmatter reading | `models/profile_file.py` | 90% | python-frontmatter for markdown metadata |
| Input validation | All scripts | 95% | Validate paths, API keys, file existence |

### New Components to Create (20-30%)

| Component | Complexity | Purpose |
|-----------|-----------|---------|
| `services/pdf_processor.py` | High | PDF rendering to PNG using pypdfium2 |
| `services/image_generator.py` | Medium | Coordinate image generation, sizing, cropping |
| `models/pdf_archive.py` | Medium | Track PDF archive state, exact-match logic |
| `models/publication.py` | Low | Publication dataclass (ID, DOI, kind, year) |
| `cli/audit_pdfs.py` | Medium | PDF archive audit CLI tool |
| `cli/generate_previews.py` | Medium | Preview image generation CLI tool |
| `cli/extract_feature.py` | Medium | Feature image extraction CLI tool |

### Existing Patterns to Follow

#### CLI Structure (from `fill_abstracts.py`):
```python
def parse_arguments():
    parser = argparse.ArgumentParser(description='...')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--numbers-file', default='~/Library/Mobile Documents/...')
    return parser.parse_args()

def validate_inputs(args):
    if not Path(args.numbers_file).exists():
        return False, "CV.numbers file not found"
    return True, None

def main():
    args = parse_arguments()

    # Logging setup
    logger = setup_logger(__name__, verbose=args.verbose)

    # Validation
    valid, error = validate_inputs(args)
    if not valid:
        logger.error(error)
        sys.exit(1)

    # Processing
    results = process_batch(args, logger)

    # Summary report
    print(format_summary(results))
    sys.exit(0 if results['success'] else 2)
```

#### Error Handling Pattern:
```python
try:
    result = process_pdf(pdf_path)
    success_count += 1
except PasswordProtectedError as e:
    logger.error(f"PDF password protected: {pdf_path}")
    errors.append({'file': pdf_path, 'error': 'password_protected'})
except CorruptedPDFError as e:
    logger.error(f"PDF corrupted: {pdf_path}")
    errors.append({'file': pdf_path, 'error': 'corrupted'})
except Exception as e:
    logger.error(f"Unexpected error processing {pdf_path}: {e}")
    errors.append({'file': pdf_path, 'error': str(e)})
```

#### Summary Report Pattern:
```python
def format_summary_report(results):
    report = ["\n=== Summary ==="]
    report.append(f"Total scanned: {results['total_scanned']}")
    report.append(f"Success: {results['success']}")
    report.append(f"Skipped: {results['skipped']}")
    report.append(f"Errors: {len(results['errors'])}")

    if results['errors']:
        report.append("\nErrors:")
        for err in results['errors']:
            report.append(f"  - {err['file']}: {err['error']}")

    return '\n'.join(report)
```

### Dependencies Already Installed

From `_scripts/requirements.txt`:
- `numbers-parser` - CV.numbers reading ✅
- `python-frontmatter` - Markdown file parsing ✅
- `pyyaml` - YAML/config handling ✅
- `requests>=2.31.0` - HTTP client (Scholar API) ✅
- `python-dotenv` - Environment variables ✅
- `responses>=0.24.0` - Mock HTTP for testing ✅
- `rapidfuzz>=3.0.0` - Fuzzy string matching ✅

Need to add:
- `pypdfium2>=4.0.0`
- `Pillow>=10.0.0`

---

## Decision 3: Jekyll Template Modifications

### Decision: **Minimal template changes using existing fallback infrastructure**

### Rationale

Jekyll templates already implement a two-level fallback mechanism (`post.header.teaser` → `site.teaser`). Extending to three levels requires minimal changes and leverages existing infrastructure.

### Current State

**Image Reference Pattern** (from `_publications/` markdown):
```yaml
header:
  teaser: assets/images/publications/Caylor2002_1378.png
```

**Existing Fallback Logic** (from `_includes/archive-single.html`):
```liquid
{% if post.header.teaser %}
  {% capture teaser %}{{ post.header.teaser }}{% endcapture %}
{% else %}
  {% assign teaser = site.teaser %}
{% endif %}
```

**Status**:
- Two-level fallback exists: publication-specific → global default
- `site.teaser` is configured but empty (no placeholder image set)
- No JavaScript or CSS-based error handling for missing files
- 187 existing publication images, 87 PDFs (~87% coverage)

### Required Changes

#### 1. Create Placeholder Image Asset
**Action**: Design and place generic placeholder PNG
**Location**: `assets/images/publications/placeholder.png`
**Specifications**: 480x640px (standard preview aspect ratio), simple design indicating "publication preview unavailable"

#### 2. Configure Global Fallback in `_config.yml`
```yaml
# Global fallback for missing publication images
teaser: /assets/images/publications/placeholder.png
```

#### 3. Extend `_includes/archive-single.html` for Three-Level Fallback
```liquid
{% comment %}
  Three-level fallback chain:
  1. Feature image (publication_id_figure.png) if present
  2. Preview image (publication_id.png) if feature missing
  3. Global placeholder if both missing
{% endcomment %}

{% assign pub_id = post.id | split: '/' | last %}
{% assign feature_img = 'assets/images/publications/' | append: pub_id | append: '_figure.png' %}
{% assign preview_img = 'assets/images/publications/' | append: pub_id | append: '.png' %}

{% if post.header.feature_image %}
  {% assign image_to_use = post.header.feature_image %}
{% elsif post.header.teaser %}
  {% assign image_to_use = post.header.teaser %}
{% else %}
  {% assign image_to_use = site.teaser %}
{% endif %}

<div class="archive__item-teaser">
  <img src="{{ image_to_use | absolute_url }}" alt="">
</div>
```

#### 4. Optional: Add JavaScript Error Handling
```html
<img src="{{ image_to_use | absolute_url }}"
     alt=""
     onerror="this.src='{{ site.teaser | absolute_url }}'">
```

**Note**: This is optional - Jekyll's static generation means images should exist at build time. JS fallback only helps if images are deleted post-build.

### Why This Works

- ✅ **No breaking changes**: Existing publications using `header.teaser` continue working
- ✅ **Additive only**: New feature image level is optional
- ✅ **Static-first compliant**: All logic executes at Jekyll build time
- ✅ **Minimal maintenance**: Single placeholder image asset
- ✅ **Git-friendly**: No dynamic content generation
- ✅ **CSS unchanged**: Existing `.archive__item-teaser` styles work as-is

### Cloudinary Integration Note

The site has `jekyll-cloudinary` plugin installed but not currently used in publication templates. This is intentional and remains unchanged:
- Cloudinary provides CDN delivery, responsive sizing, format negotiation
- Not required for Feature 004 core functionality
- Can be added as future enhancement without refactoring

### Asset Organization

Current structure (no changes needed):
```
assets/
├── pdfs/publications/       # AuthorYear_XXXX.pdf (needs standardization)
└── images/publications/     # AuthorYear_XXXX.png, AuthorYear_XXXX_figure.png
    └── placeholder.png      # NEW: Generic fallback
```

---

## Best Practices Identified

### PDF Processing

1. **Memory Management**: Process PDFs one at a time, close document handles immediately
2. **Error Detection**: Check `pdfium.PdfDocument.new()` for success before rendering
3. **Scale Calculation**: Use target height / source height ratio for consistent sizing
4. **Format Selection**: PNG for quality (publications), JPEG for faster generation if needed

### Image Generation

1. **Idempotency**: Check if image exists before generating (unless --force flag)
2. **Atomic Writes**: Write to temp file, then rename to final path
3. **Aspect Ratio**: Let width vary naturally for 640px height (academic PDFs are consistent)
4. **Compression**: PNG compression level 6 (PIL default) balances size vs speed

### Batch Processing

1. **Continue on Error**: Log error, add to report, continue with next publication
2. **Progress Indicators**: Log every N items (e.g., every 10) for long batches
3. **Summary Report**: Total, success, skipped, errors with details
4. **Exit Codes**: 0 (all success), 2 (partial success), 1 (fatal error)

### Testing

1. **Fixtures**: Use small sample PDFs (1-3 pages) for fast tests
2. **Mock API**: Use `responses` library to mock Scholar API calls
3. **Temp Directories**: Use pytest `tmp_path` fixture for output validation
4. **Edge Cases**: Test password-protected, corrupted, zero-byte PDFs

---

## Implementation Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| pypdfium2 rendering quality issues | Low | Medium | Test with diverse PDF samples early |
| Scholar API PDF fetch failures | Medium | Low | Logged in summary report, manual fallback |
| Placeholder image not created | Low | High | Create in Phase 1, validate in tests |
| Template changes break existing pages | Low | High | Test with local Jekyll build, verify all publications render |
| Performance issues with large PDFs | Low | Medium | Lazy page loading, memory profiling |
| PDF naming inconsistencies | Medium | Medium | Exact-match requirement, warn about ambiguous files |

**Overall Risk Level**: LOW - High code reuse, proven patterns, minimal template changes

---

## Gaps Requiring Clarification

None. All research questions resolved with high confidence.

---

## Next Steps

Proceed to Phase 1: Design & Contracts
- Define data models (Publication, PDFArchive)
- Define CLI contracts (arguments, outputs, exit codes)
- Create quickstart guide for tool usage
- Update CLAUDE.md with new technologies
