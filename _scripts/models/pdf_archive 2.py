"""PDF Archive model for managing publication PDF files.

This module provides the PDFArchive class for scanning, matching, and
auditing PDF files against publications.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import re


@dataclass
class ArchiveStats:
    """Statistics about PDF archive coverage.

    Attributes:
        total_publications: Total number of publications
        pdfs_found: Number of publications with matching PDFs
        pdfs_missing_required: Number of required PDFs missing
        pdfs_missing_optional: Number of optional PDFs missing
        ambiguous_files_detected: Number of files with ambiguous naming
    """

    total_publications: int
    pdfs_found: int
    pdfs_missing_required: int
    pdfs_missing_optional: int
    ambiguous_files_detected: int

    @property
    def coverage_percentage(self) -> float:
        """Calculate PDF coverage percentage.

        Returns:
            Percentage of publications with PDFs (0-100)
        """
        if self.total_publications == 0:
            return 0.0
        return (self.pdfs_found / self.total_publications) * 100


class PDFArchive:
    """Manages the PDF archive directory and file matching.

    This class scans the PDF directory, matches files to publications using
    exact canonical_id matching, and detects ambiguous files that don't
    follow the naming convention.
    """

    def __init__(self, base_dir: Path):
        """Initialize PDF archive.

        Args:
            base_dir: Root directory containing PDF files
        """
        self.base_dir = Path(base_dir)
        self.pdf_files: Dict[str, Path] = {}
        self.ambiguous_files: List[Path] = []

    def scan(self):
        """Scan directory and build pdf_files map.

        Raises:
            FileNotFoundError: If base_dir does not exist
        """
        if not self.base_dir.exists():
            raise FileNotFoundError(f"PDF directory not found: {self.base_dir}")

        # Clear previous scan results
        self.pdf_files.clear()
        self.ambiguous_files.clear()

        # Scan for PDF files
        for pdf_file in self.base_dir.glob('*.pdf'):
            # Extract canonical_id from filename (stem without extension)
            canonical_id = pdf_file.stem

            # Check if it matches the expected pattern (AuthorYear_XXXX)
            if re.match(r'^[A-Z][a-z]+\d{4}_\d{4}$', canonical_id):
                # Valid canonical ID - add to exact match map
                self.pdf_files[canonical_id] = pdf_file
            else:
                # Invalid pattern - mark as ambiguous
                # This catches files like "Caylor2002_1378_draft.pdf"
                self.ambiguous_files.append(pdf_file)

    def find_pdf(self, canonical_id: str) -> Optional[Path]:
        """Find exact match PDF for publication.

        Args:
            canonical_id: Publication canonical ID to match

        Returns:
            Path to PDF file if found, None otherwise
        """
        return self.pdf_files.get(canonical_id)

    def find_ambiguous(self, canonical_id: str) -> List[Path]:
        """Find files with similar names but not exact matches.

        Args:
            canonical_id: Publication canonical ID to search for

        Returns:
            List of ambiguous file paths that start with canonical_id
        """
        matches = []
        for ambiguous_file in self.ambiguous_files:
            if ambiguous_file.stem.startswith(canonical_id):
                matches.append(ambiguous_file)
        return matches

    def get_coverage_stats(self, publications: List) -> ArchiveStats:
        """Calculate coverage statistics for publications.

        Args:
            publications: List of Publication objects

        Returns:
            ArchiveStats object with coverage metrics
        """
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

    def validate(self) -> bool:
        """Check if directory exists and is accessible.

        Returns:
            True if directory exists and is a directory, False otherwise
        """
        return self.base_dir.exists() and self.base_dir.is_dir()

    def __str__(self) -> str:
        """String representation of archive state."""
        return (
            f"PDFArchive(base_dir={self.base_dir}, "
            f"pdfs={len(self.pdf_files)}, "
            f"ambiguous={len(self.ambiguous_files)})"
        )
