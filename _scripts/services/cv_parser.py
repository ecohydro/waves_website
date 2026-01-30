#!/usr/bin/env python3
"""CV.numbers parsing service for extracting people data."""

import os
import sys
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from numbers_parser import Document
from rapidfuzz import fuzz

from models.cv_sheet import CVEntry, CVSheet
from models.person import Person, Role
from services.logger import logger


class CVParserService:
    """Service for parsing CV.numbers file and extracting people data."""

    # Sheet names from contracts/cv-sheet-schema.yml
    SHEET_NAMES = [
        "Graduate PhD",
        "Postdoc",
        "Graduate MA_MS",
        "Undergrad",
        "Visitors",
    ]

    def __init__(self, cv_file_path: str):
        """
        Initialize CVParserService.

        Args:
            cv_file_path: Path to CV.numbers file
        """
        self.cv_file_path = cv_file_path
        self.document: Optional[Document] = None
        self.cv_sheets: dict[str, CVSheet] = {}
        self.all_entries: list[CVEntry] = []

    def load_cv_file(self) -> Document:
        """
        Load CV.numbers file using numbers_parser.Document.

        Returns:
            Document object

        Raises:
            FileNotFoundError: If CV file doesn't exist
            Exception: If file is locked or cannot be read
        """
        if not os.path.exists(self.cv_file_path):
            raise FileNotFoundError(f"CV.numbers file not found: {self.cv_file_path}")

        logger.info(f"Loading CV.numbers file: {self.cv_file_path}")

        try:
            self.document = Document(self.cv_file_path)
            logger.info(f"Successfully loaded CV.numbers file with {len(self.document.sheets)} sheets")
            return self.document

        except Exception as e:
            logger.error(f"Failed to load CV.numbers file: {e}")
            raise Exception(
                f"Failed to load CV.numbers file. "
                f"File may be locked or corrupted: {e}"
            )

    def parse_sheet(self, sheet_name: str) -> CVSheet:
        """
        Create CVSheet, detect columns via fuzzy matching, and extract CVEntry objects.

        Args:
            sheet_name: Name of sheet to parse (e.g., "Graduate PhD")

        Returns:
            CVSheet with parsed entries

        Raises:
            ValueError: If sheet not found in document
        """
        if not self.document:
            raise ValueError("Document not loaded. Call load_cv_file() first.")

        # Find sheet by name
        sheet = None
        for doc_sheet in self.document.sheets:
            if doc_sheet.name == sheet_name:
                sheet = doc_sheet
                break

        if not sheet:
            logger.warning(f"Sheet '{sheet_name}' not found in CV.numbers")
            raise ValueError(f"Sheet '{sheet_name}' not found")

        logger.info(f"Parsing sheet: {sheet_name}")

        # Create CVSheet object
        cv_sheet = CVSheet(name=sheet_name)

        # Get first table from sheet
        if not sheet.tables:
            logger.warning(f"No tables found in sheet '{sheet_name}'")
            return cv_sheet

        table = sheet.tables[0]

        # Extract rows as plain data (numbers-parser returns cell data)
        rows = []
        for row_idx in range(table.num_rows):
            row_data = []
            for col_idx in range(table.num_cols):
                try:
                    cell = table.cell(row_idx, col_idx)
                    value = cell.value if cell else None
                    row_data.append(value)
                except (IndexError, AttributeError):
                    row_data.append(None)
            rows.append(row_data)

        if not rows:
            logger.warning(f"No rows found in sheet '{sheet_name}'")
            return cv_sheet

        # First row is header
        header_row = rows[0] if rows else []

        # Detect columns via fuzzy matching
        column_mapping = cv_sheet.detect_columns(header_row)

        logger.info(f"Detected columns for '{sheet_name}': {column_mapping}")

        # Check if name column was found (required)
        if column_mapping.get("name") is None:
            logger.error(f"Name column not found in sheet '{sheet_name}'")
            raise ValueError(f"Name column not found in sheet '{sheet_name}'. Cannot parse without name column.")

        # Parse entries from remaining rows
        entries = cv_sheet.parse_entries(rows, skip_header=True)

        logger.info(f"Extracted {len(entries)} entries from sheet '{sheet_name}'")

        self.cv_sheets[sheet_name] = cv_sheet
        self.all_entries.extend(entries)

        return cv_sheet

    def parse_all_sheets(self) -> dict[str, CVSheet]:
        """
        Parse all five expected sheets.

        Returns:
            Dictionary mapping sheet names to CVSheet objects
        """
        if not self.document:
            self.load_cv_file()

        for sheet_name in self.SHEET_NAMES:
            try:
                self.parse_sheet(sheet_name)
            except ValueError as e:
                # Sheet not found or no name column - log and continue
                logger.warning(f"Skipping sheet '{sheet_name}': {e}")
                continue

        return self.cv_sheets

    def merge_duplicates(self) -> list[Person]:
        """
        Group CVEntry objects by person name (fuzzy matching) and merge into Person with role history.

        Returns:
            List of Person objects with merged roles
        """
        if not self.all_entries:
            logger.warning("No entries to merge")
            return []

        logger.info(f"Merging {len(self.all_entries)} entries into unique people")

        # Group entries by normalized name
        name_groups: dict[str, list[CVEntry]] = {}

        for entry in self.all_entries:
            # Normalize name for grouping
            normalized_name = self._normalize_name(entry.name)

            # Check for fuzzy matches in existing groups
            matched_group = None
            for existing_name in name_groups.keys():
                if self._names_match(normalized_name, existing_name):
                    matched_group = existing_name
                    break

            if matched_group:
                name_groups[matched_group].append(entry)
            else:
                name_groups[normalized_name] = [entry]

        logger.info(f"Found {len(name_groups)} unique people after merging duplicates")

        # Convert each group to Person object
        people = []
        for normalized_name, entries in name_groups.items():
            person = self._create_person_from_entries(entries)
            people.append(person)

        return people

    def _normalize_name(self, name: str) -> str:
        """Normalize name for matching: lowercase, strip, remove punctuation."""
        import string

        normalized = name.lower().strip()

        # Remove punctuation except hyphens and spaces
        translator = str.maketrans('', '', string.punctuation.replace('-', '').replace(' ', ''))
        normalized = normalized.translate(translator)

        return normalized

    def _names_match(self, name1: str, name2: str, threshold: float = 0.85) -> bool:
        """Check if two names match using fuzzy string matching."""
        ratio = fuzz.ratio(name1, name2) / 100.0
        return ratio >= threshold

    def _create_person_from_entries(self, entries: list[CVEntry]) -> Person:
        """
        Create Person object from list of CVEntry objects (potentially from multiple sheets).

        Args:
            entries: List of CVEntry objects for same person

        Returns:
            Person object with merged roles
        """
        # Use first entry for name extraction
        first_entry = entries[0]

        # Parse name into parts
        name_parts = first_entry.name.strip().split()
        firstname = name_parts[0] if name_parts else ""
        lastname = name_parts[-1] if len(name_parts) > 1 else name_parts[0] if name_parts else ""

        # Convert entries to roles
        roles = [entry.to_role() for entry in entries]

        # Create Person with first role
        person = Person(
            name=first_entry.name.strip(),
            firstname=firstname,
            lastname=lastname,
            roles=[roles[0]],  # Start with first role
        )

        # Merge remaining roles
        for role in roles[1:]:
            person.merge_role(role)

        # Collect research interests from all roles
        research_interests = set()
        for role in person.roles:
            if role.research_focus:
                research_interests.add(role.research_focus)

        if research_interests:
            person.research_interests = list(research_interests)

        # Determine alumni status (if all roles have end_year)
        all_ended = all(role.end_year is not None for role in person.roles)
        if all_ended:
            current_year = 2026  # Use current year from context
            latest_end = max((role.end_year for role in person.roles if role.end_year), default=0)
            person.alumni_status = latest_end < current_year

        logger.debug(f"Created Person: {person.name} with {len(person.roles)} role(s)")

        return person
