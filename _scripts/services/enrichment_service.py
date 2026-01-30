#!/usr/bin/env python3
"""Enrichment service orchestrating web search, parsing, scoring, and caching."""

import sys
import os
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.enrichment import EnrichmentSuggestion, EnrichmentCache
from models.person import Person
from services.confidence_scoring import ConfidenceScoringService
from services.logger import logger
from services.result_parser import ResultParserService
from services.web_search import WebSearchService


class EnrichmentService:
    """Service for enriching profiles with web-sourced data."""

    def __init__(self, cache_dir: str = ".cache/enrichment/"):
        """
        Initialize EnrichmentService.

        Args:
            cache_dir: Directory for caching results
        """
        self.web_search = WebSearchService()
        self.result_parser = ResultParserService()
        self.confidence_scorer = ConfidenceScoringService()
        self.cache = EnrichmentCache(cache_dir)

        # Check if web search is available
        if not self.web_search.is_available():
            logger.warning(
                "Web search not available. Enrichment will be skipped. "
                "Set GOOGLE_CUSTOM_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID in .env file."
            )

    def enrich_person(
        self,
        person: Person,
        force_refresh: bool = False
    ) -> list[EnrichmentSuggestion]:
        """
        Enrich person with web-sourced data.

        Implements:
        - Check cache first (unless force_refresh)
        - Query API if not cached
        - Parse results
        - Calculate confidence
        - Create EnrichmentSuggestion objects
        - Filter by ≥0.6 threshold
        - Save to cache

        Args:
            person: Person object to enrich
            force_refresh: If True, bypass cache and re-fetch

        Returns:
            List of EnrichmentSuggestion objects with confidence ≥ 0.6
        """
        logger.info(f"Enriching: {person.name}")

        # Check cache first (unless force_refresh)
        if not force_refresh and self.cache.is_cached(person.name):
            cached_suggestions = self.cache.load(person.name)
            if cached_suggestions:
                logger.info(f"  Using cached results ({len(cached_suggestions)} suggestions)")
                return cached_suggestions

        # Check if web search is available
        if not self.web_search.is_available():
            logger.warning(f"  Skipping {person.name}: Web search not available")
            return []

        # Query API
        suggestions = []

        # Build contextual info
        last_institution = ""
        if person.roles:
            last_role = person.roles[-1]  # Most recent role
            last_institution = last_role.institution or ""

        context = {
            "institution": last_institution,
            "research_keywords": person.research_interests,
            "degree": person.roles[0].degree if person.roles else None
        }

        # Query 1: Position search
        position_suggestions = self._search_position(person, context)
        suggestions.extend(position_suggestions)

        # Query 2: LinkedIn search
        linkedin_suggestions = self._search_linkedin(person)
        suggestions.extend(linkedin_suggestions)

        # Filter by threshold (≥0.6)
        filtered_suggestions = [
            s for s in suggestions if s.meets_threshold()
        ]

        logger.info(f"  Found {len(filtered_suggestions)} suggestions (confidence ≥ 0.6)")

        # Save to cache
        self.cache.save(
            person.name,
            filtered_suggestions,
            person.profile_file_path or ""
        )

        return filtered_suggestions

    def _search_position(self, person: Person, context: dict) -> list[EnrichmentSuggestion]:
        """Search for current position and institution."""
        suggestions = []

        # Build query with contextual disambiguation
        query = self.web_search.build_contextual_query(person.name, context)

        # Execute search
        results = self.web_search.search(query, num_results=5)

        if not results:
            return suggestions

        # Parse each result
        for rank, result in enumerate(results, start=1):
            # Extract position
            position = self.result_parser.extract_position(result)

            if position:
                # Calculate confidence
                confidence, breakdown = self.confidence_scorer.calculate_confidence(
                    result=result,
                    rank=rank,
                    person_name=person.name,
                    institution=context.get('institution', ''),
                    research_keywords=context.get('research_keywords', [])
                )

                # Create suggestion
                suggestion = EnrichmentSuggestion(
                    person_name=person.name,
                    profile_file_path=person.profile_file_path or "",
                    field="current_position",
                    current_value=person.current_position,
                    suggested_value=position,
                    source_url=result.get('link', ''),
                    source_snippet=result.get('snippet', ''),
                    confidence=confidence,
                    confidence_breakdown=breakdown,
                    timestamp=datetime.now(),
                    query=query
                )

                suggestions.append(suggestion)

            # Extract institution
            institution = self.result_parser.extract_institution(result)

            if institution:
                # Calculate confidence
                confidence, breakdown = self.confidence_scorer.calculate_confidence(
                    result=result,
                    rank=rank,
                    person_name=person.name,
                    institution=context.get('institution', ''),
                    research_keywords=context.get('research_keywords', [])
                )

                # Create suggestion
                suggestion = EnrichmentSuggestion(
                    person_name=person.name,
                    profile_file_path=person.profile_file_path or "",
                    field="current_institution",
                    current_value=person.current_institution,
                    suggested_value=institution,
                    source_url=result.get('link', ''),
                    source_snippet=result.get('snippet', ''),
                    confidence=confidence,
                    confidence_breakdown=breakdown,
                    timestamp=datetime.now(),
                    query=query
                )

                suggestions.append(suggestion)

        return suggestions

    def _search_linkedin(self, person: Person) -> list[EnrichmentSuggestion]:
        """Search for LinkedIn profile."""
        suggestions = []

        # Build LinkedIn query
        query = self.web_search.build_linkedin_query(person.name)

        # Execute search
        results = self.web_search.search(query, num_results=3)

        if not results:
            return suggestions

        # Parse each result
        for rank, result in enumerate(results, start=1):
            # Extract LinkedIn URL
            linkedin_url = self.result_parser.extract_linkedin(result)

            if linkedin_url:
                # Calculate confidence
                confidence, breakdown = self.confidence_scorer.calculate_confidence(
                    result=result,
                    rank=rank,
                    person_name=person.name,
                    institution="",
                    research_keywords=[]
                )

                # Boost confidence for LinkedIn results (more reliable)
                confidence = min(confidence + 0.1, 1.0)
                breakdown["linkedin_boost"] = 0.1

                # Create suggestion
                suggestion = EnrichmentSuggestion(
                    person_name=person.name,
                    profile_file_path=person.profile_file_path or "",
                    field="linkedin_url",
                    current_value=person.linkedin_url,
                    suggested_value=linkedin_url,
                    source_url=result.get('link', ''),
                    source_snippet=result.get('snippet', ''),
                    confidence=confidence,
                    confidence_breakdown=breakdown,
                    timestamp=datetime.now(),
                    query=query
                )

                suggestions.append(suggestion)

        return suggestions
