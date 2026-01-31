"""Publication model for PDF and image management.

This module defines the Publication entity representing research publications
from CV.numbers with validation and computed properties for file paths.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import re


@dataclass
class Publication:
    """Represents a research publication with PDF and image asset references.

    Attributes:
        canonical_id: AuthorYear_XXXX pattern identifier (e.g., "Caylor2002_1378")
        title: Publication title
        authors: List of author names
        year: Publication year
        doi: Digital Object Identifier (optional)
        kind: Publication type - one of RA (research article), BC (book chapter),
              CP (conference proceedings), or None
    """

    canonical_id: str
    title: str
    authors: List[str]
    year: int
    doi: Optional[str] = None
    kind: Optional[str] = None

    def __post_init__(self):
        """Validate publication data after initialization."""
        # Validate canonical_id format
        if not re.match(r'^[A-Z][a-z]+\d{4}_\d{4}$', self.canonical_id):
            raise ValueError(
                f"Invalid canonical_id format: {self.canonical_id}. "
                f"Expected pattern: AuthorYear_XXXX (e.g., Caylor2002_1378)"
            )

        # Validate year
        current_year = datetime.now().year
        if not (1900 <= self.year <= current_year + 1):
            raise ValueError(
                f"Invalid year: {self.year}. Must be between 1900 and {current_year + 1}"
            )

        # Validate kind
        if self.kind and self.kind not in ['RA', 'BC', 'CP']:
            raise ValueError(
                f"Invalid kind: {self.kind}. Must be one of: RA, BC, CP"
            )

        # Validate authors
        if not self.authors or len(self.authors) == 0:
            raise ValueError("Publication must have at least one author")

    @property
    def pdf_required(self) -> bool:
        """Determine if PDF is required based on year and kind.

        Returns:
            True if PDF is required (post-2022 research article), False otherwise
        """
        return self.year >= 2022 and self.kind == 'RA'

    @property
    def pdf_path(self) -> Path:
        """Expected PDF file path.

        Returns:
            Path object for {canonical_id}.pdf in publications PDF directory
        """
        return Path('assets/pdfs/publications') / f"{self.canonical_id}.pdf"

    @property
    def preview_image_path(self) -> Path:
        """Expected preview image path (first page of PDF).

        Returns:
            Path object for {canonical_id}.png in publications images directory
        """
        return Path('assets/images/publications') / f"{self.canonical_id}.png"

    @property
    def feature_image_path(self) -> Path:
        """Expected feature image path (selected figure from PDF).

        Returns:
            Path object for {canonical_id}_figure.png in publications images directory
        """
        return Path('assets/images/publications') / f"{self.canonical_id}_figure.png"

    def __str__(self) -> str:
        """String representation of publication."""
        return f"Publication({self.canonical_id}, {self.year}, {self.title[:50]}...)"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"Publication(canonical_id='{self.canonical_id}', "
            f"year={self.year}, kind={self.kind}, "
            f"pdf_required={self.pdf_required})"
        )
