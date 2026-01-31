# Implementation Plan: Publication PDF Management and Image Generation

**Branch**: `004-publication-pdf-images` | **Date**: 2026-01-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-publication-pdf-images/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature implements a PDF management and image generation system for academic publications. The system maintains a local archive of publication PDFs, generates preview images (first page) for index listings, extracts feature images (selected figures) for detail pages, and implements a three-level fallback strategy (feature → preview → placeholder) for missing images. The implementation uses Python CLI tools that integrate with the existing CV.numbers workflow and Jekyll static site, with automated PDF fetching from Scholar AI for missing research articles.

## Technical Context

**Language/Version**: Python 3.9+ (consistent with Features 001, 002, 003)
**Primary Dependencies**: PyMuPDF (fitz) or pdf2image for PDF rendering, Pillow (PIL) for image processing, numbers-parser for CV.numbers reading, python-frontmatter for markdown file parsing, PyYAML for configuration, requests for Scholar AI integration, python-dotenv for API credentials
**Storage**: Filesystem - PDFs in `assets/pdfs/publications/`, images in `assets/images/publications/`, CV.numbers file (existing location)
**Testing**: pytest with fixtures for mock PDFs and CV.numbers files
**Target Platform**: macOS/Linux development environment (CLI tools)
**Project Type**: Single project (Python CLI tools in `_scripts/`)
**Performance Goals**: PDF audit for 100+ publications in <30 seconds, preview generation at 10+ publications/minute, batch processing 50 publications in <10 minutes
**Constraints**: Fixed preview image height of 640px, max feature image dimension 640px, PNG format for quality, must not modify Jekyll layouts (use existing fallback mechanisms)
**Scale/Scope**: ~100 existing publications, growing incrementally

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Static-First ✅ PASS

- Generated images are static PNG assets placed in `assets/images/publications/`
- No server-side rendering or runtime databases
- Jekyll templates use existing fallback logic (no JavaScript required)
- Image generation is a build-time/maintenance operation

### II. Content as Data ✅ PASS

- Publication metadata sourced from CV.numbers (existing structured data)
- Publication markdown files in `_publications/` collection (existing structure)
- No hard-coded content in layouts
- Adding a publication requires only CV.numbers entry + markdown file (existing workflow)

### III. Standards Compliance ✅ PASS

- Generated images are standard PNG format
- Jekyll templates already handle image fallbacks with valid HTML
- No new HTML/CSS generation required
- Images use existing Cloudinary integration via `jekyll-cloudinary`

### IV. Automation & Agentic Refresh ✅ PASS

- Uses canonical AuthorYear_XXXX naming convention for PDFs and images
- CLI tools are idempotent (repeated runs produce same results)
- Batch processing supports automated workflows
- No manual intervention required for standard cases
- Error logging enables monitoring and recovery

### V. Incremental & Non-Destructive ✅ PASS

- Default behavior preserves existing images (force flag required to regenerate)
- PDF archive is additive (never deletes)
- Failure handling skips problematic publications without stopping batch
- No modification of existing Jekyll layouts or front matter required
- Git-friendly outputs (binary images tracked normally)

**Result**: All constitutional checks pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/004-publication-pdf-images/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
_scripts/
├── models/
│   ├── publication.py       # Publication entity from CV.numbers
│   └── pdf_archive.py       # PDF archive state/operations
├── services/
│   ├── pdf_processor.py     # PDF reading and image extraction
│   ├── cv_reader.py         # CV.numbers parsing (may already exist)
│   ├── scholar_fetcher.py   # Scholar AI integration (may already exist from Feature 002)
│   └── image_generator.py   # Image generation coordination
└── cli/
    ├── audit_pdfs.py        # PDF archive audit tool
    ├── generate_previews.py # Preview image generation tool
    └── extract_feature.py   # Feature image extraction tool

tests/
├── fixtures/
│   ├── sample.pdf           # Test PDF files
│   ├── sample_cv.numbers    # Test CV.numbers file
│   └── sample_publications/ # Test markdown files
├── unit/
│   ├── test_pdf_processor.py
│   ├── test_cv_reader.py
│   └── test_image_generator.py
└── integration/
    ├── test_audit_workflow.py
    ├── test_preview_generation.py
    └── test_feature_extraction.py

assets/
├── pdfs/publications/       # PDF archive (AuthorYear_XXXX.pdf)
└── images/publications/     # Generated images (AuthorYear_XXXX.png, AuthorYear_XXXX_figure.png)
```

**Structure Decision**: Single project structure using existing `_scripts/` directory. This aligns with Features 001, 002, and 003 which established the Python tooling pattern for CV.numbers integration. Tests follow pytest conventions with fixtures for reproducible testing.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations to justify. All constitutional principles satisfied.
