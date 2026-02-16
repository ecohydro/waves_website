#!/usr/bin/env python3
"""MatchCandidate model for linking CV entries to profile files."""

from dataclasses import dataclass
from typing import Optional

from models.cv_sheet import CVEntry
from models.profile_file import ProfileFile


@dataclass
class MatchCandidate:
    """Represents a potential link between a CVEntry and a ProfileFile."""

    cv_entry: CVEntry
    profile_file: Optional[ProfileFile] = None
    match_type: str = "no_match"  # exact_filename, fuzzy_name, year_degree_disambiguated, no_match
    confidence: float = 0.0  # 0.0-1.0
    notes: str = ""

    def __post_init__(self):
        """Validate match candidate data."""
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError(f"confidence must be in range [0.0, 1.0], got {self.confidence}")

        if self.match_type == "no_match" and self.profile_file is not None:
            raise ValueError("profile_file must be None when match_type is 'no_match'")

    def is_match(self) -> bool:
        """Returns True if match_type != "no_match"."""
        return self.match_type != "no_match"

    def requires_manual_review(self) -> bool:
        """Returns True if confidence < 0.9."""
        return self.confidence < 0.9
