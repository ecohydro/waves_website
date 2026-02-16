"""Scholar AI fetch result model for tracking PDF downloads.

This module defines the ScholarFetchResult dataclass for tracking
PDF fetch operations from Scholar AI.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ScholarFetchResult:
    """Tracks Scholar AI PDF fetch operations.

    Attributes:
        publication_id: Canonical ID of the publication
        doi: DOI used for the fetch attempt
        status: Fetch status ("success", "not_found", "network_error", "auth_error")
        fetch_timestamp: When the fetch was attempted
        error_message: Detailed error message if failed
        pdf_path: Path to saved PDF if successful
    """

    publication_id: str
    doi: str
    status: str  # "success", "not_found", "network_error", "auth_error"
    fetch_timestamp: datetime
    error_message: Optional[str] = None
    pdf_path: Optional[Path] = None

    def __post_init__(self):
        """Validate fetch result after initialization."""
        valid_statuses = ['success', 'not_found', 'network_error', 'auth_error']
        if self.status not in valid_statuses:
            raise ValueError(
                f"Invalid status: {self.status}. "
                f"Must be one of: {', '.join(valid_statuses)}"
            )

    def to_dict(self) -> dict:
        """Convert fetch result to dictionary for JSON serialization.

        Returns:
            Dictionary representation of fetch result
        """
        return {
            'publication_id': self.publication_id,
            'doi': self.doi,
            'status': self.status,
            'fetch_timestamp': self.fetch_timestamp.isoformat(),
            'error_message': self.error_message,
            'pdf_path': str(self.pdf_path) if self.pdf_path else None
        }

    def is_success(self) -> bool:
        """Check if fetch was successful.

        Returns:
            True if status is "success", False otherwise
        """
        return self.status == 'success'

    def __str__(self) -> str:
        """String representation of fetch result."""
        if self.is_success():
            return f"✓ {self.publication_id}: PDF fetched successfully"
        else:
            error_msg = self.error_message or self.status
            return f"✗ {self.publication_id}: {error_msg}"
