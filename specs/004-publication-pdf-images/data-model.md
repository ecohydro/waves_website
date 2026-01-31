# Data Model: Publication PDF Management and Image Generation

**Feature**: 004-publication-pdf-images
**Date**: 2026-01-30

## Entity Overview

This feature introduces two primary data entities and leverages existing publication metadata from CV.numbers.

---

## Entity 1: Publication

Represents a research publication with PDF and image asset references.

### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `canonical_id` | str | Yes | AuthorYear_XXXX pattern identifier | Regex: `^[A-Z][a-z]+\d{4}_\d{4}$` |
| `title` | str | Yes | Publication title | Non-empty string |
| `authors` | List[str] | Yes | List of author names | At least one author |
| `year` | int | Yes | Publication year | 1900 <= year <= current year + 1 |
| `doi` | str | Optional | Digital Object Identifier | DOI format if present |
| `kind` | str | Optional | Publication type | One of: RA, BC, CP, or None |
| `pdf_required` | bool | Computed | Whether PDF is required | Based on year and kind |

### Field Details

**`canonical_id`**: The unique identifier linking all assets
- Example: `Caylor2002_1378`
- Used for: PDF filename (`Caylor2002_1378.pdf`), preview image (`Caylor2002_1378.png`), feature image (`Caylor2002_1378_figure.png`)
- Generated from: First author's last name + year + 4-digit random number
- Purpose: Avoids collisions while maintaining readability

**`kind`**: Publication type code
- `RA` = Research Article (peer-reviewed journal article)
- `BC` = Book Chapter
- `CP` = Conference Proceedings
- `None` or missing = Unknown/legacy publication

**`pdf_required`**: Computed property
- For year >= 2022 AND kind == "RA": Required
- For year >= 2022 AND kind in ["BC", "CP"]: Optional
- For year < 2022: Based on metadata flag (if implemented) or assumed optional

### Relationships

- **Has one** PDF file in `assets/pdfs/publications/`
- **Has zero or one** preview image in `assets/images/publications/`
- **Has zero or one** feature image in `assets/images/publications/`
- **Source**: Single row in CV.numbers "Publications" sheet

### State Transitions

Publications have no lifecycle state (they are immutable records). However, their **asset coverage state** can be tracked:

```
State: Complete
- PDF exists
- Preview image exists
- Feature image exists (or not required)

State: Partial
- PDF exists
- Preview missing OR feature missing

State: Minimal
- PDF missing (required)
- Images missing

State: Legacy
- PDF optional (pre-2022 or kind != RA)
- Images missing
```

### Example

```python
@dataclass
class Publication:
    canonical_id: str
    title: str
    authors: List[str]
    year: int
    doi: Optional[str] = None
    kind: Optional[str] = None

    def __post_init__(self):
        # Validate canonical_id format
        if not re.match(r'^[A-Z][a-z]+\d{4}_\d{4}$', self.canonical_id):
            raise ValueError(f"Invalid canonical_id format: {self.canonical_id}")

        # Validate year
        current_year = datetime.now().year
        if not (1900 <= self.year <= current_year + 1):
            raise ValueError(f"Invalid year: {self.year}")

        # Validate kind
        if self.kind and self.kind not in ['RA', 'BC', 'CP']:
            raise ValueError(f"Invalid kind: {self.kind}")

    @property
    def pdf_required(self) -> bool:
        """Determine if PDF is required based on year and kind"""
        if self.year >= 2022 and self.kind == 'RA':
            return True
        return False

    @property
    def pdf_path(self) -> Path:
        """Expected PDF file path"""
        return Path('assets/pdfs/publications') / f"{self.canonical_id}.pdf"

    @property
    def preview_image_path(self) -> Path:
        """Expected preview image path"""
        return Path('assets/images/publications') / f"{self.canonical_id}.png"

    @property
    def feature_image_path(self) -> Path:
        """Expected feature image path"""
        return Path('assets/images/publications') / f"{self.canonical_id}_figure.png"
```

---

## Entity 2: PDFArchive

Represents the state of the PDF archive and provides matching/validation operations.

### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `base_dir` | Path | Yes | Root directory for PDFs (`assets/pdfs/publications/`) |
| `pdf_files` | Dict[str, Path] | Computed | Map of canonical_id → PDF path |
| `ambiguous_files` | List[Path] | Computed | Files with similar names but not exact matches |

### Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `scan()` | Scan directory and build pdf_files map | None |
| `find_pdf(canonical_id: str)` | Find exact match for publication | Optional[Path] |
| `find_ambiguous(canonical_id: str)` | Find similar but non-matching files | List[Path] |
| `get_coverage_stats()` | Calculate archive statistics | ArchiveStats |
| `validate()` | Check directory exists and is accessible | bool |

### Matching Logic

**Exact Match Required**: Only files matching `{canonical_id}.pdf` exactly are considered valid.

```python
# Valid matches:
Caylor2002_1378.pdf  ✓ matches publication Caylor2002_1378

# Invalid (ambiguous, will warn):
Caylor2002_1378_draft.pdf  ✗ not exact match
Caylor2002_1378_final.pdf  ✗ not exact match
caylor2002_1378.pdf        ✗ wrong case
```

**Ambiguous File Detection**: Files with base name matching but additional suffixes are logged as warnings.

### Coverage Statistics

```python
@dataclass
class ArchiveStats:
    total_publications: int
    pdfs_found: int
    pdfs_missing_required: int
    pdfs_missing_optional: int
    ambiguous_files_detected: int

    @property
    def coverage_percentage(self) -> float:
        return (self.pdfs_found / self.total_publications * 100) if self.total_publications > 0 else 0.0
```

### Example

```python
class PDFArchive:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.pdf_files: Dict[str, Path] = {}
        self.ambiguous_files: List[Path] = []

    def scan(self):
        """Scan directory and build pdf_files map"""
        if not self.base_dir.exists():
            raise FileNotFoundError(f"PDF directory not found: {self.base_dir}")

        for pdf_file in self.base_dir.glob('*.pdf'):
            # Extract canonical_id from filename (stem without extension)
            canonical_id = pdf_file.stem

            # Check if it matches pattern
            if re.match(r'^[A-Z][a-z]+\d{4}_\d{4}$', canonical_id):
                self.pdf_files[canonical_id] = pdf_file
            else:
                # Possible ambiguous file (e.g., Caylor2002_1378_draft.pdf)
                self.ambiguous_files.append(pdf_file)

    def find_pdf(self, canonical_id: str) -> Optional[Path]:
        """Find exact match PDF for publication"""
        return self.pdf_files.get(canonical_id)

    def find_ambiguous(self, canonical_id: str) -> List[Path]:
        """Find files with similar names but not exact matches"""
        matches = []
        for ambiguous_file in self.ambiguous_files:
            if ambiguous_file.stem.startswith(canonical_id):
                matches.append(ambiguous_file)
        return matches

    def get_coverage_stats(self, publications: List[Publication]) -> ArchiveStats:
        """Calculate coverage statistics"""
        pdfs_found = 0
        pdfs_missing_required = 0
        pdfs_missing_optional = 0

        for pub in publications:
            if self.find_pdf(pub.canonical_id):
                pdfs_found += 1
            else:
                if pub.pdf_required:
                    pdfs_missing_required += 1
                else:
                    pdfs_missing_optional += 1

        return ArchiveStats(
            total_publications=len(publications),
            pdfs_found=pdfs_found,
            pdfs_missing_required=pdfs_missing_required,
            pdfs_missing_optional=pdfs_missing_optional,
            ambiguous_files_detected=len(self.ambiguous_files)
        )
```

---

## Entity 3: ImageGenerationLog (Supporting)

Tracks image generation operations for auditing and debugging.

### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | datetime | Yes | Operation timestamp |
| `operation` | str | Yes | Operation type: "preview" or "feature" |
| `publication_id` | str | Yes | Canonical ID of publication |
| `status` | str | Yes | Status: "success", "skipped", "error" |
| `message` | str | Optional | Error message or skip reason |
| `output_path` | Path | Optional | Generated image path if successful |

### Example

```python
@dataclass
class ImageGenerationLog:
    timestamp: datetime
    operation: str  # "preview" or "feature"
    publication_id: str
    status: str  # "success", "skipped", "error"
    message: Optional[str] = None
    output_path: Optional[Path] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'operation': self.operation,
            'publication_id': self.publication_id,
            'status': self.status,
            'message': self.message,
            'output_path': str(self.output_path) if self.output_path else None
        }
```

---

## Entity 4: ScholarFetchResult (Supporting)

Tracks Scholar AI PDF fetch operations.

### Attributes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `publication_id` | str | Yes | Canonical ID of publication |
| `doi` | str | Yes | DOI used for fetch |
| `status` | str | Yes | Status: "success", "not_found", "network_error", "auth_error" |
| `error_message` | str | Optional | Detailed error if failed |
| `pdf_path` | Path | Optional | Saved PDF path if successful |
| `fetch_timestamp` | datetime | Yes | When fetch was attempted |

### Example

```python
@dataclass
class ScholarFetchResult:
    publication_id: str
    doi: str
    status: str  # "success", "not_found", "network_error", "auth_error"
    fetch_timestamp: datetime
    error_message: Optional[str] = None
    pdf_path: Optional[Path] = None

    def to_dict(self) -> dict:
        return {
            'publication_id': self.publication_id,
            'doi': self.doi,
            'status': self.status,
            'fetch_timestamp': self.fetch_timestamp.isoformat(),
            'error_message': self.error_message,
            'pdf_path': str(self.pdf_path) if self.pdf_path else None
        }
```

---

## Data Flow

### 1. PDF Archive Audit

```
CV.numbers Publications sheet
    ↓
[Parse] → List[Publication]
    ↓
[Scan] → PDFArchive
    ↓
[Match] → ArchiveStats
    ↓
[Report] → Console/File
```

### 2. Preview Image Generation

```
List[Publication]
    ↓
[Filter: Missing preview images]
    ↓
PDFArchive.find_pdf(canonical_id)
    ↓
[Render first page] → PIL Image
    ↓
[Resize to 640px height] → PIL Image
    ↓
[Save as PNG] → assets/images/publications/{id}.png
    ↓
[Log] → ImageGenerationLog
```

### 3. Feature Image Extraction

```
Publication (single)
    ↓
PDFArchive.find_pdf(canonical_id)
    ↓
[Render specified page] → PIL Image
    ↓
[Optional: Crop coordinates] → PIL Image
    ↓
[Resize to max 640px] → PIL Image
    ↓
[Save as PNG] → assets/images/publications/{id}_figure.png
    ↓
[Log] → ImageGenerationLog
```

### 4. Scholar AI PDF Fetch

```
Publication (pdf_required=True, PDF missing)
    ↓
[Build Scholar API request with DOI]
    ↓
[Query Scholar API with retry logic]
    ↓
[Download PDF to temp file]
    ↓
[Validate PDF integrity]
    ↓
[Move to assets/pdfs/publications/{id}.pdf]
    ↓
[Log] → ScholarFetchResult
```

---

## Validation Rules

### Publication Validation

- `canonical_id`: Must match `^[A-Z][a-z]+\d{4}_\d{4}$` pattern
- `year`: Must be between 1900 and current_year + 1
- `kind`: Must be one of ["RA", "BC", "CP"] or None
- `authors`: Must contain at least one author

### PDF Matching Validation

- **Exact match only**: `{canonical_id}.pdf` with no additional suffixes
- **Case sensitive**: `Caylor2002_1378.pdf` ≠ `caylor2002_1378.pdf`
- **No partial matches**: `Caylor2002_1378_draft.pdf` is ambiguous, not valid

### Image Generation Validation

- **Preview images**: Fixed height 640px, width varies proportionally
- **Feature images**: Max dimension 640px (usually width for landscape figures)
- **Format**: PNG only (quality preservation)
- **Overwrite protection**: Require explicit --force flag to regenerate existing images

---

## Error Handling

### PDF Processing Errors

| Error Type | Detection | Handling |
|------------|-----------|----------|
| **Password-protected** | pypdfium2 raises exception | Skip, log error, continue batch |
| **Corrupted file** | pypdfium2 raises exception | Skip, log error, continue batch |
| **File not found** | Path.exists() check | Skip, log error, continue batch |
| **Permission denied** | OS error on file open | Skip, log error, continue batch |

### Scholar API Errors

| Error Type | Detection | Handling |
|------------|-----------|----------|
| **Network error** | requests.exceptions.ConnectionError | Log, continue batch, report at end |
| **Authentication error** | HTTP 401/403 | Log, continue batch, report at end |
| **DOI not found** | HTTP 404 or empty result | Log, continue batch, report at end |
| **Rate limiting** | HTTP 429 | Existing retry logic with exponential backoff |

### Image Generation Errors

| Error Type | Detection | Handling |
|------------|-----------|----------|
| **PDF unreadable** | pypdfium2 exception | Skip, log error, continue batch |
| **Disk space** | OS error on write | Fatal error, stop batch, exit 1 |
| **Invalid page number** | Page index out of range | Skip, log error, continue batch |
| **Permission denied** | OS error on write | Skip, log error, continue batch |

---

## Indexing and Performance

### PDF Archive Scanning

- **Strategy**: Single pass directory scan, build in-memory dictionary
- **Complexity**: O(n) where n = number of PDF files
- **Expected n**: ~100-200 files
- **Performance target**: <1 second for 200 files

### Publication Lookup

- **Strategy**: Dictionary lookup by canonical_id
- **Complexity**: O(1)
- **Expected lookups**: 100-200 per batch operation

### Batch Image Generation

- **Strategy**: Sequential processing (no parallelism due to PIL/pypdfium2 thread safety)
- **Expected throughput**: 10+ publications/minute (per success criteria)
- **Bottleneck**: PDF rendering (per research: ~45ms per page for pypdfium2)

---

## Data Persistence

### Transient Data (In-Memory Only)

- `List[Publication]` - Loaded from CV.numbers per operation
- `PDFArchive` state - Scanned per operation
- `ImageGenerationLog` entries - Collected during batch, reported at end

### Persistent Data (Filesystem)

- **PDFs**: `assets/pdfs/publications/{canonical_id}.pdf`
- **Preview images**: `assets/images/publications/{canonical_id}.png`
- **Feature images**: `assets/images/publications/{canonical_id}_figure.png`
- **Placeholder**: `assets/images/publications/placeholder.png`
- **Logs** (optional): Timestamped log files in `_scripts/logs/` (if --log-file flag used)

### No Database

This feature requires no database. All state is derived from:
1. CV.numbers file (source of truth for publications)
2. Filesystem (source of truth for assets)

---

## Schema Version

**Version**: 1.0.0
**Date**: 2026-01-30
**Changes**: Initial data model for Feature 004
