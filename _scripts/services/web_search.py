#!/usr/bin/env python3
"""Web search service using Google Custom Search API."""

import os
import sys
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    build = None
    HttpError = None

from services.logger import logger

# Load environment variables
load_dotenv()


class WebSearchService:
    """Service for web search using Google Custom Search API."""

    def __init__(self):
        """Initialize WebSearchService with API credentials."""
        self.api_key = os.getenv('GOOGLE_CUSTOM_SEARCH_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.service = None

        # Check if API is available
        if build is None:
            logger.warning("google-api-python-client not installed. Web enrichment disabled.")
            return

        # Check if credentials are set
        if not self.api_key or not self.search_engine_id:
            logger.warning(
                "Google Custom Search API credentials not set. "
                "Set GOOGLE_CUSTOM_SEARCH_API_KEY and GOOGLE_SEARCH_ENGINE_ID in .env file. "
                "Web enrichment disabled."
            )
            return

        # Build service
        try:
            self.service = build("customsearch", "v1", developerKey=self.api_key)
            logger.debug("Google Custom Search API initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Custom Search API: {e}")
            self.service = None

    def is_available(self) -> bool:
        """Check if web search is available (API key set and service built)."""
        return self.service is not None

    def search(self, query: str, num_results: int = 10) -> Optional[list[dict]]:
        """
        Search using Google Custom Search API.

        Args:
            query: Search query
            num_results: Number of results to return (max 10)

        Returns:
            List of search result dictionaries, or None on error
        """
        if not self.is_available():
            logger.warning("Web search not available (missing credentials or library)")
            return None

        logger.debug(f"Searching: {query}")

        try:
            result = self.service.cse().list(
                q=query,
                cx=self.search_engine_id,
                num=min(num_results, 10)
            ).execute()

            items = result.get('items', [])
            logger.debug(f"Found {len(items)} results for: {query}")

            return items

        except HttpError as e:
            if e.resp.status == 403:
                # Quota exceeded or invalid API key
                logger.error(
                    "Google Search API quota exceeded or invalid API key. "
                    "Using cached results where available."
                )
            elif e.resp.status == 429:
                # Rate limit exceeded
                logger.warning("Rate limited by Google Search API. Retrying...")
                # Could implement retry logic here
            else:
                logger.error(f"Google Search API error: {e}")

            return None

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return None

    def build_position_query(self, name: str, institution: str = "") -> str:
        """
        Build query for finding current position.

        Format: "{name} {institution} current position"

        Args:
            name: Person's name
            institution: Last known institution (optional)

        Returns:
            Search query string
        """
        query_parts = [name]

        if institution:
            query_parts.append(institution)

        query_parts.append("current position")

        return " ".join(query_parts)

    def build_linkedin_query(self, name: str) -> str:
        """
        Build query for finding LinkedIn profile.

        Format: "{name} site:linkedin.com/in"

        Args:
            name: Person's name

        Returns:
            Search query string
        """
        return f"{name} site:linkedin.com/in"

    def build_contextual_query(self, name: str, context: dict) -> str:
        """
        Build contextual query for disambiguation.

        Uses research keywords, institution, degree from context.

        Args:
            name: Person's name
            context: Dictionary with optional keys: institution, research_keywords, degree

        Returns:
            Search query string
        """
        query_parts = [name]

        if context.get('research_keywords'):
            # Add first research keyword
            keywords = context['research_keywords']
            if keywords:
                query_parts.append(keywords[0])

        if context.get('institution'):
            query_parts.append(context['institution'])

        return " ".join(query_parts)
