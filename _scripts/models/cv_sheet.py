#!/usr/bin/env python3
"""CV.numbers sheet parsing models."""

import re
from dataclasses import dataclass
from typing import Optional

from models.person import Role


@dataclass
class CVEntry:
    """Represents one row from a CV.numbers sheet (one person, one role)."""

    sheet_name: str
    name: str
    years: Optional[str] = None
    degree: Optional[str] = None
    institution: Optional[str] = None
    research: Optional[str] = None
    row_index: int = 0

    def parse_years(self) -> tuple[Optional[int], Optional[int]]:
        """
        Extract start_year, end_year from years string.

        Supported formats:
        - "2015-2020" → (2015, 2020)
        - "2018-present" → (2018, None)
        - "2019-" → (2019, None)
        - "2020" → (2020, None)
        - "TBD", "N/A", invalid → (None, None)
        """
        if not self.years:
            return (None, None)

        years_str = self.years.strip().lower()

        # Handle "present" or "-" ending (ongoing)
        if "present" in years_str or years_str.endswith("-"):
            years_str = years_str.replace("present", "").replace("-", "-")

        # Extract year patterns (4 digits)
        year_pattern = r'\b(19|20)\d{2}\b'
        matches = re.findall(year_pattern, years_str + years_str[0] if years_str else "")
        year_matches = re.findall(r'\b(19|20)\d{2}\b', years_str if years_str else "")

        if not year_matches:
            # No valid years found
            return (None, None)

        if len(year_matches) == 1:
            # Single year: could be start year or both
            year = int(year_matches[0])
            if "-" in years_str or "present" in self.years.lower():
                # It's a start year (e.g., "2020-" or "2020-present")
                return (year, None)
            else:
                # Ambiguous - treat as start year only
                return (year, None)

        # Multiple years: first is start, last is end
        start_year = int(year_matches[0])
        end_year = int(year_matches[-1])

        # Validate order
        if end_year < start_year:
            # Invalid range, return as-is (will be caught by validation)
            return (start_year, end_year)

        return (start_year, end_year)

    def to_role(self) -> Role:
        """Convert CVEntry to Role object for merging into Person."""
        start_year, end_year = self.parse_years()

        return Role(
            type=self.sheet_name,  # Graduate PhD, Postdoc, etc.
            start_year=start_year,
            end_year=end_year,
            degree=self.degree,
            institution=self.institution,
            research_focus=self.research,
        )


class CVSheet:
    """Represents one of the five sheets in CV.numbers file with parsing logic."""

    # Fuzzy matching patterns from contracts/cv-sheet-schema.yml
    COLUMN_PATTERNS = {
        "name": ["name", "full name", "student name", "person", "postdoc name", "visitor name"],
        "years": ["years", "year", "dates", "period", "visit dates"],
        "degree": ["degree", "degree type", "program", "major"],
        "institution": ["institution", "university", "affiliation", "school", "home institution"],
        "research": ["research", "focus", "area", "topic", "project", "dissertation", "thesis", "purpose"],
    }

    def __init__(self, name: str, table_index: int = 0):
        """
        Initialize CVSheet.

        Args:
            name: Sheet name (e.g., "Graduate PhD")
            table_index: Zero-based index of table within sheet
        """
        self.name = name
        self.table_index = table_index
        self.column_mapping: dict[str, Optional[int]] = {}
        self.entries: list[CVEntry] = []

    def detect_columns(self, header_row: list[str]) -> dict[str, Optional[int]]:
        """
        Fuzzy match header row to standard field names using patterns.

        Args:
            header_row: List of column headers from first row

        Returns:
            Dictionary mapping standard field names to column indices
        """
        mapping = {
            "name": None,
            "years": None,
            "degree": None,
            "institution": None,
            "research": None,
        }

        for field_name, patterns in self.COLUMN_PATTERNS.items():
            for col_idx, header in enumerate(header_row):
                if not header:
                    continue

                header_lower = str(header).strip().lower()

                # Check if any pattern is a substring of the header
                for pattern in patterns:
                    if pattern in header_lower:
                        mapping[field_name] = col_idx
                        break

                if mapping[field_name] is not None:
                    break

        self.column_mapping = mapping
        return mapping

    def parse_entries(self, rows: list[list], skip_header: bool = True) -> list[CVEntry]:
        """
        Extract all rows as CVEntry objects.

        Args:
            rows: List of rows from the sheet
            skip_header: Whether to skip first row (header)

        Returns:
            List of CVEntry objects
        """
        entries = []
        start_idx = 1 if skip_header else 0

        for row_idx, row in enumerate(rows[start_idx:], start=start_idx):
            # Skip empty rows (all cells empty)
            if not any(cell for cell in row):
                continue

            # Extract name (required field)
            name_idx = self.column_mapping.get("name")
            if name_idx is None or name_idx >= len(row):
                continue

            name = str(row[name_idx]).strip() if row[name_idx] else None
            if not name:
                # Skip rows with empty name
                continue

            # Extract optional fields
            years_idx = self.column_mapping.get("years")
            degree_idx = self.column_mapping.get("degree")
            institution_idx = self.column_mapping.get("institution")
            research_idx = self.column_mapping.get("research")

            entry = CVEntry(
                sheet_name=self.name,
                name=name,
                years=str(row[years_idx]).strip() if years_idx is not None and years_idx < len(row) and row[years_idx] else None,
                degree=str(row[degree_idx]).strip() if degree_idx is not None and degree_idx < len(row) and row[degree_idx] else None,
                institution=str(row[institution_idx]).strip() if institution_idx is not None and institution_idx < len(row) and row[institution_idx] else None,
                research=str(row[research_idx]).strip() if research_idx is not None and research_idx < len(row) and row[research_idx] else None,
                row_index=row_idx,
            )

            entries.append(entry)

        self.entries = entries
        return entries
