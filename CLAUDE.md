# waves Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-29

## Active Technologies
- Python 3.9+ (compatible with existing feature 001) + `requests` or `httpx` (HTTP client for Scholar API), `python-frontmatter` (markdown file parsing), `numbers-parser` (CV.numbers read/write), `PyYAML` (YAML handling), `python-dotenv` (environment variable loading from .env) (002-scholar-abstract-fill)
- Filesystem — reads/writes `.md` files in `_publications/`, reads/writes CV.numbers file, loads `.env` for API credentials (002-scholar-abstract-fill)
- Python 3.9+ (consistent with Features 001 and 002) + numbers-parser (CV.numbers parsing), python-frontmatter (YAML frontmatter manipulation), PyYAML (config), requests (web API calls), python-dotenv (API keys), web search library (TBD in Phase 0) (003-people-profile-sync)
- Filesystem - CV.numbers file at `~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers`, Jekyll markdown files in `_people/` collection, web enrichment cache (format TBD in Phase 0) (003-people-profile-sync)
- Python 3.9+ (consistent with Features 001, 002, 003) + pypdfium2 (PDF rendering, Apache 2.0 license), Pillow (PIL) for image processing, numbers-parser for CV.numbers reading, python-frontmatter for markdown file parsing, PyYAML for configuration, requests for Scholar AI integration, python-dotenv for API credentials (004-publication-pdf-images)
- Filesystem - PDFs in `assets/pdfs/publications/`, images in `assets/images/publications/`, CV.numbers file (existing location) (004-publication-pdf-images)

- Python 3.9+ (compatible with numbers-parser 4.16.3) + `numbers-parser` (Numbers file reading), `python-frontmatter` (YAML frontmatter parsing), `PyYAML` (authors.yml reading) (001-pub-ingestion)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.9+ (compatible with numbers-parser 4.16.3): Follow standard conventions

## Recent Changes
- 004-publication-pdf-images: Implemented PDF management and image generation tools. Uses pypdfium2 (Apache 2.0) for PDF rendering, Pillow for image processing. Three CLI tools: audit_pdfs.py (archive auditing + Scholar AI fetch), generate_previews.py (first page thumbnails), extract_feature.py (specific figure extraction). Jekyll templates updated with three-level fallback (feature→preview→placeholder). Exact-match canonical ID naming enforced (AuthorYear_XXXX.pdf pattern).
- 003-people-profile-sync: Added Python 3.9+ (consistent with Features 001 and 002) + numbers-parser (CV.numbers parsing), python-frontmatter (YAML frontmatter manipulation), PyYAML (config), requests (web API calls), python-dotenv (API keys), web search library (TBD in Phase 0)
- 002-scholar-abstract-fill: Added Python 3.9+ (compatible with existing feature 001) + `requests` or `httpx` (HTTP client for Scholar API), `python-frontmatter` (markdown file parsing), `numbers-parser` (CV.numbers read/write), `PyYAML` (YAML handling), `python-dotenv` (environment variable loading from .env)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
