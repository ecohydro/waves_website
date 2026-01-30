#!/usr/bin/env python3
"""Profile matching service for linking CV entries to existing Jekyll files."""

import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rapidfuzz import fuzz

from models.match_candidate import MatchCandidate
from models.person import Person
from models.profile_file import ProfileFile
from services.logger import logger


class ProfileMatcherService:
    """Service for matching Person objects to existing profile files."""

    def __init__(self, people_dir: str = "_people/"):
        """
        Initialize ProfileMatcherService.

        Args:
            people_dir: Directory containing people markdown files
        """
        self.people_dir = people_dir
        self.existing_profiles: dict[str, ProfileFile] = {}
        self._profile_cache: dict[str, ProfileFile] = {}  # Performance: cache loaded profiles
        self._load_existing_profiles()

    def _load_existing_profiles(self):
        """Load all existing profile files from people_dir."""
        if not os.path.exists(self.people_dir):
            logger.warning(f"People directory does not exist: {self.people_dir}")
            return

        for filename in os.listdir(self.people_dir):
            if filename.endswith('.md'):
                file_path = os.path.join(self.people_dir, filename)
                try:
                    profile = ProfileFile(file_path).load()
                    if profile.exists:
                        self.existing_profiles[filename] = profile
                except Exception as e:
                    logger.warning(f"Failed to load profile {filename}: {e}")

        logger.info(f"Loaded {len(self.existing_profiles)} existing profiles from {self.people_dir}")

    def find_match(self, person: Person) -> MatchCandidate:
        """
        Find matching profile file for person using hybrid matching.

        Implements Decision 2: Try exact filename, then fuzzy frontmatter, then disambiguate.

        Args:
            person: Person object to match

        Returns:
            MatchCandidate with match result
        """
        # Try exact filename match first
        exact_match = self.exact_filename_match(person)
        if exact_match.is_match():
            return exact_match

        # Try fuzzy frontmatter match
        fuzzy_matches = self.fuzzy_frontmatter_match(person)

        if not fuzzy_matches:
            # No match found
            return MatchCandidate(
                cv_entry=None,  # Not using CVEntry here
                profile_file=None,
                match_type="no_match",
                confidence=0.0,
                notes=f"No match found for {person.name}"
            )

        if len(fuzzy_matches) == 1:
            # Single fuzzy match
            return fuzzy_matches[0]

        # Multiple fuzzy matches - disambiguate by year/degree
        best_match = self.disambiguate_by_year_degree(person, fuzzy_matches)
        return best_match

    def exact_filename_match(self, person: Person) -> MatchCandidate:
        """
        Check if {lastname}.md exists in _people/.

        Args:
            person: Person to match

        Returns:
            MatchCandidate with exact match or no match
        """
        # Normalize lastname to filename format
        lastname_normalized = self._normalize_filename(person.lastname)

        # Check for {lastname}.md
        filename = f"{lastname_normalized}.md"
        profile = self.existing_profiles.get(filename)

        if profile:
            logger.debug(f"Exact filename match: {person.name} → {filename}")
            return MatchCandidate(
                cv_entry=None,
                profile_file=profile,
                match_type="exact_filename",
                confidence=1.0,
                notes=f"Exact filename match: {filename}"
            )

        # Check for {firstname}-{lastname}.md
        firstname_normalized = self._normalize_filename(person.firstname)
        filename_alt = f"{firstname_normalized}-{lastname_normalized}.md"
        profile_alt = self.existing_profiles.get(filename_alt)

        if profile_alt:
            logger.debug(f"Exact filename match: {person.name} → {filename_alt}")
            return MatchCandidate(
                cv_entry=None,
                profile_file=profile_alt,
                match_type="exact_filename",
                confidence=1.0,
                notes=f"Exact filename match: {filename_alt}"
            )

        return MatchCandidate(
            cv_entry=None,
            profile_file=None,
            match_type="no_match",
            confidence=0.0,
            notes="No exact filename match"
        )

    def fuzzy_frontmatter_match(self, person: Person, threshold: float = 0.8) -> list[MatchCandidate]:
        """
        Load all _people/*.md files and use rapidfuzz for name matching.

        Args:
            person: Person to match
            threshold: Minimum fuzzy match score (0.0-1.0)

        Returns:
            List of MatchCandidate objects with confidence ≥ threshold
        """
        matches = []

        person_name_normalized = self._normalize_name(person.name)

        for filename, profile in self.existing_profiles.items():
            # Get name from frontmatter (title or author)
            profile_name = profile.frontmatter.get('title') or profile.frontmatter.get('author', '')
            profile_name_normalized = self._normalize_name(profile_name)

            # Calculate fuzzy match score
            score = fuzz.ratio(person_name_normalized, profile_name_normalized) / 100.0

            if score >= threshold:
                logger.debug(f"Fuzzy match: {person.name} → {filename} (score: {score:.2f})")
                matches.append(MatchCandidate(
                    cv_entry=None,
                    profile_file=profile,
                    match_type="fuzzy_name",
                    confidence=score,
                    notes=f"Fuzzy name match: '{person.name}' vs '{profile_name}' (score: {score:.2f})"
                ))

        # Sort by confidence descending
        matches.sort(key=lambda m: m.confidence, reverse=True)

        return matches

    def disambiguate_by_year_degree(self, person: Person, candidates: list[MatchCandidate]) -> MatchCandidate:
        """
        Handle multiple fuzzy matches using year and degree as secondary identifiers.

        Args:
            person: Person to match
            candidates: List of fuzzy match candidates

        Returns:
            Best MatchCandidate after disambiguation
        """
        if not candidates:
            return MatchCandidate(
                cv_entry=None,
                profile_file=None,
                match_type="no_match",
                confidence=0.0,
                notes="No candidates to disambiguate"
            )

        # Try to match by years and degree
        best_match = None
        best_score = 0.0

        person_years = person.years_active
        person_degrees = set(r.degree for r in person.roles if r.degree)

        for candidate in candidates:
            score = candidate.confidence  # Start with name match confidence

            # Extract profile's person data
            profile_person = candidate.profile_file.to_person()
            profile_years = profile_person.years_active
            profile_degrees = set(r.degree for r in profile_person.roles if r.degree)

            # Boost score if years overlap
            if person_years[0] and profile_years[0]:
                # Check for overlapping years
                person_range = range(person_years[0], (person_years[1] or 9999) + 1)
                profile_range = range(profile_years[0], (profile_years[1] or 9999) + 1)

                overlap = set(person_range) & set(profile_range)
                if overlap:
                    score += 0.1  # Boost for year overlap

            # Boost score if degrees match
            if person_degrees & profile_degrees:
                score += 0.1  # Boost for degree match

            if score > best_score:
                best_score = score
                best_match = candidate

        if best_match:
            best_match.match_type = "year_degree_disambiguated"
            best_match.confidence = min(best_score, 1.0)
            best_match.notes += f" (disambiguated by year/degree, final score: {best_score:.2f})"
            logger.debug(f"Disambiguated: {person.name} → {best_match.profile_file.file_path}")

        return best_match or candidates[0]  # Fall back to first candidate if no boost

    def _normalize_filename(self, name: str) -> str:
        """Normalize name for filename: lowercase, hyphens for spaces, no apostrophes."""
        import string

        normalized = name.lower().strip()

        # Remove apostrophes
        normalized = normalized.replace("'", "")

        # Replace spaces with hyphens
        normalized = normalized.replace(" ", "-")

        # Remove other punctuation except hyphens
        translator = str.maketrans('', '', string.punctuation.replace('-', ''))
        normalized = normalized.translate(translator)

        return normalized

    def _normalize_name(self, name: str) -> str:
        """Normalize name for fuzzy matching: lowercase, strip, remove punctuation."""
        import string

        normalized = name.lower().strip()

        # Remove all punctuation
        translator = str.maketrans('', '', string.punctuation)
        normalized = normalized.translate(translator)

        # Collapse multiple spaces
        normalized = ' '.join(normalized.split())

        return normalized
