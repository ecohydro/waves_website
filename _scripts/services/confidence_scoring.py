#!/usr/bin/env python3
"""Confidence scoring service for ranking search results."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rapidfuzz import fuzz

from services.logger import logger


class ConfidenceScoringService:
    """Service for calculating confidence scores using hybrid algorithm."""

    # Component weights from Decision 5 in research.md
    WEIGHT_RANK = 0.4
    WEIGHT_NAME_MATCH = 0.3
    WEIGHT_INSTITUTION_MATCH = 0.2
    WEIGHT_CONTEXT = 0.1

    def calculate_confidence(
        self,
        result: dict,
        rank: int,
        person_name: str,
        institution: str = "",
        research_keywords: list[str] = None
    ) -> tuple[float, dict[str, float]]:
        """
        Calculate overall confidence score using weighted components.

        Args:
            result: Search result dictionary
            rank: Result rank (1-based: 1 = top result)
            person_name: Name of person being searched
            institution: Last known institution (optional)
            research_keywords: Research keywords for context (optional)

        Returns:
            Tuple of (confidence_score, breakdown_dict)
        """
        # Calculate component scores
        rank_score = self._rank_score(rank)
        name_match_score = self._name_match_score(result, person_name)
        institution_match_score = self._institution_match_score(result, institution)
        context_score = self._context_score(result, research_keywords or [])

        # Weighted sum
        confidence = (
            self.WEIGHT_RANK * rank_score +
            self.WEIGHT_NAME_MATCH * name_match_score +
            self.WEIGHT_INSTITUTION_MATCH * institution_match_score +
            self.WEIGHT_CONTEXT * context_score
        )

        # Breakdown for transparency
        breakdown = {
            "rank_score": rank_score,
            "name_match_score": name_match_score,
            "institution_match_score": institution_match_score,
            "context_score": context_score,
        }

        logger.debug(
            f"Confidence: {confidence:.2f} "
            f"(rank={rank_score:.2f}, name={name_match_score:.2f}, "
            f"inst={institution_match_score:.2f}, ctx={context_score:.2f})"
        )

        return confidence, breakdown

    def _rank_score(self, rank: int) -> float:
        """
        Calculate rank-based score.

        Top result = 1.0, linear decrease to 0.2 for ranks 2-5, 0.0 for rank 10+

        Args:
            rank: Result rank (1-based)

        Returns:
            Score 0.0-1.0
        """
        if rank == 1:
            return 1.0
        elif rank <= 5:
            # Linear decrease from 1.0 to 0.2
            return 1.0 - (rank - 1) * 0.2
        elif rank < 10:
            # Further decrease
            return max(0.2 - (rank - 5) * 0.04, 0.0)
        else:
            return 0.0

    def _name_match_score(self, result: dict, person_name: str) -> float:
        """
        Calculate name match score using fuzzy string matching.

        Uses rapidfuzz to compare person name with result title.

        Args:
            result: Search result dictionary
            person_name: Name of person

        Returns:
            Score 0.0-1.0
        """
        title = result.get('title', '')

        if not title or not person_name:
            return 0.0

        # Normalize names
        person_name_normalized = self._normalize_name(person_name)
        title_normalized = self._normalize_name(title)

        # Calculate fuzzy match ratio
        ratio = fuzz.ratio(person_name_normalized, title_normalized) / 100.0

        return ratio

    def _institution_match_score(self, result: dict, institution: str) -> float:
        """
        Calculate institution match score.

        Exact match = 1.0, partial substring = 0.5, no match = 0.0

        Args:
            result: Search result dictionary
            institution: Institution name to match

        Returns:
            Score 0.0-1.0
        """
        if not institution:
            # No institution to match against
            return 0.5  # Neutral score

        display_link = result.get('displayLink', '')
        snippet = result.get('snippet', '')

        institution_normalized = institution.lower()
        text = (display_link + ' ' + snippet).lower()

        # Extract key words from institution (e.g., "Stanford" from "Stanford University")
        institution_keywords = [
            word for word in institution_normalized.split()
            if len(word) > 3 and word not in ['university', 'of', 'the', 'and']
        ]

        # Check for exact match
        if institution_normalized in text:
            return 1.0

        # Check for partial match (any keyword found)
        for keyword in institution_keywords:
            if keyword in text:
                return 0.5

        # No match
        return 0.0

    def _context_score(self, result: dict, research_keywords: list[str]) -> float:
        """
        Calculate context score based on research keywords appearing in snippet.

        Args:
            result: Search result dictionary
            research_keywords: List of research keywords

        Returns:
            Score 0.0-1.0
        """
        if not research_keywords:
            return 0.5  # Neutral score

        snippet = result.get('snippet', '').lower()

        # Count how many keywords appear in snippet
        matches = sum(1 for keyword in research_keywords if keyword.lower() in snippet)

        # Score based on proportion of keywords found
        if matches > 0:
            return min(matches / len(research_keywords), 1.0)

        return 0.0

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison."""
        import string

        normalized = name.lower().strip()

        # Remove punctuation
        translator = str.maketrans('', '', string.punctuation)
        normalized = normalized.translate(translator)

        # Collapse multiple spaces
        normalized = ' '.join(normalized.split())

        return normalized
