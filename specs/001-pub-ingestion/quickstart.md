# Quickstart: Publication Ingestion

**Branch**: `001-pub-ingestion` | **Date**: 2026-01-29

## Prerequisites

1. **macOS** with iCloud Drive enabled and synced
2. **Python 3.9+** installed
3. **Homebrew** installed (for native dependency)

## Setup

```bash
# Install native dependency
brew install snappy

# Install Python dependencies
pip install numbers-parser python-frontmatter pyyaml

# Or from requirements file (once created)
pip install -r _scripts/requirements.txt
```

## Usage

### Preview what would be created (recommended first run)

```bash
python _scripts/ingest_publications.py --dry-run
```

### Ingest new publications

```bash
python _scripts/ingest_publications.py
```

### With verbose output

```bash
python _scripts/ingest_publications.py --verbose
```

### Custom file paths

```bash
python _scripts/ingest_publications.py \
  --numbers-file "/path/to/CV.numbers" \
  --output-dir "_publications/" \
  --authors-file "_data/authors.yml"
```

## Typical Workflow

1. Update your CV.numbers file with new publications
2. Run `--dry-run` to preview changes
3. Review the list of new publications that would be created
4. Run without `--dry-run` to create the files
5. Review generated files in `_publications/`
6. Add teaser images to `assets/images/publications/` (optional)
7. Build the Jekyll site to verify: `bundle exec jekyll build`
8. Commit and push

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `numbers-parser` import error | Run `brew install snappy && pip install numbers-parser` |
| File not found error | Ensure iCloud Drive is synced; check file path |
| "Sheet Publications not found" | Open CV.numbers and verify sheet is named exactly "Publications" |
| Missing abstract warnings | Normal for some publications; entries are created without abstract |
| No new publications detected | All spreadsheet entries already have matching files |

## Running Tests

```bash
pytest _scripts/tests/ -v
```
