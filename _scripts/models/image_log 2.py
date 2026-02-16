"""Image generation log model for tracking operations.

This module defines the ImageGenerationLog dataclass for tracking
image generation operations and their results.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ImageGenerationLog:
    """Tracks individual image generation operations.

    Attributes:
        timestamp: When the operation occurred
        operation: Type of operation ("preview" or "feature")
        publication_id: Canonical ID of the publication
        status: Operation status ("success", "skipped", or "error")
        message: Optional error message or skip reason
        output_path: Path to generated image if successful
    """

    timestamp: datetime
    operation: str  # "preview" or "feature"
    publication_id: str
    status: str  # "success", "skipped", or "error"
    message: Optional[str] = None
    output_path: Optional[Path] = None

    def __post_init__(self):
        """Validate log entry after initialization."""
        if self.operation not in ['preview', 'feature']:
            raise ValueError(
                f"Invalid operation: {self.operation}. "
                f"Must be 'preview' or 'feature'"
            )

        if self.status not in ['success', 'skipped', 'error']:
            raise ValueError(
                f"Invalid status: {self.status}. "
                f"Must be 'success', 'skipped', or 'error'"
            )

    def to_dict(self) -> dict:
        """Convert log entry to dictionary for JSON serialization.

        Returns:
            Dictionary representation of log entry
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'operation': self.operation,
            'publication_id': self.publication_id,
            'status': self.status,
            'message': self.message,
            'output_path': str(self.output_path) if self.output_path else None
        }

    def __str__(self) -> str:
        """String representation of log entry."""
        status_symbol = {
            'success': '✓',
            'skipped': '⚠',
            'error': '✗'
        }.get(self.status, '?')

        base = f"{status_symbol} {self.operation} {self.publication_id}"
        if self.message:
            base += f": {self.message}"
        return base
