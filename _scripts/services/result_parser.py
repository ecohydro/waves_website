#!/usr/bin/env python3
"""Result parsing service for extracting data from search results."""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.logger import logger


class ResultParserService:
    """Service for parsing search results to extract structured data."""

    # Position extraction regex patterns from contracts/google-search-api.yml
    POSITION_PATTERNS = [
        r'(?:is a|is an|works as|current position:?)\s+([^,\.]+?)\s+(?:at|in|with)',
        r'^(.+?)\s*[-|]\s*(.+?)\s*[-|]\s*(.+?)$',  # "Name - Position - Institution"
    ]

    # Institution extraction patterns
    INSTITUTION_PATTERNS = [
        r'(?:at|in)\s+((?:University of|MIT|Stanford|Harvard|[A-Z][a-z]+ (?:University|Institute|College))[^,\.]*)',
    ]

    # LinkedIn URL pattern
    LINKEDIN_PATTERN = r'linkedin\.com/in/([a-zA-Z0-9-]+)'

    # Domain to institution mapping
    DOMAIN_MAPPING = {
        'mit.edu': 'Massachusetts Institute of Technology',
        'stanford.edu': 'Stanford University',
        'harvard.edu': 'Harvard University',
        'berkeley.edu': 'University of California, Berkeley',
        'ucsb.edu': 'University of California, Santa Barbara',
        'ucla.edu': 'University of California, Los Angeles',
        'ucsd.edu': 'University of California, San Diego',
        'yale.edu': 'Yale University',
        'princeton.edu': 'Princeton University',
        'columbia.edu': 'Columbia University',
        'cornell.edu': 'Cornell University',
    }

    def extract_position(self, result: dict) -> Optional[str]:
        """
        Extract job title from search result.

        Looks in title and snippet for position indicators.

        Args:
            result: Search result dictionary with 'title' and 'snippet'

        Returns:
            Position title or None
        """
        title = result.get('title', '')
        snippet = result.get('snippet', '')

        # Try title first (often formatted as "Name - Position - Institution")
        title_parts = title.split(' - ')
        if len(title_parts) == 3:
            # Second part is likely the position
            position = title_parts[1].strip()
            if self._looks_like_position(position):
                logger.debug(f"Extracted position from title: {position}")
                return position

        # Try regex patterns in snippet
        for pattern in self.POSITION_PATTERNS:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                if len(match.groups()) == 1:
                    position = match.group(1).strip()
                elif len(match.groups()) >= 2:
                    # Format "Name - Position - Institution", use group 2
                    position = match.group(2).strip()
                else:
                    continue

                if self._looks_like_position(position):
                    logger.debug(f"Extracted position from snippet: {position}")
                    return position

        # No position found
        logger.debug("No position extracted")
        return None

    def extract_institution(self, result: dict) -> Optional[str]:
        """
        Extract institution from search result.

        Looks in displayLink (.edu domains) and snippet.

        Args:
            result: Search result dictionary

        Returns:
            Institution name or None
        """
        display_link = result.get('displayLink', '')
        snippet = result.get('snippet', '')

        # Check domain mapping first
        for domain, institution in self.DOMAIN_MAPPING.items():
            if domain in display_link:
                logger.debug(f"Extracted institution from domain: {institution}")
                return institution

        # Try regex patterns in snippet
        for pattern in self.INSTITUTION_PATTERNS:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                institution = match.group(1).strip()
                logger.debug(f"Extracted institution from snippet: {institution}")
                return institution

        # No institution found
        logger.debug("No institution extracted")
        return None

    def extract_linkedin(self, result: dict) -> Optional[str]:
        """
        Extract LinkedIn profile URL from search result.

        Args:
            result: Search result dictionary with 'link'

        Returns:
            LinkedIn profile URL or None
        """
        link = result.get('link', '')

        # Check if link is a LinkedIn profile
        match = re.search(self.LINKEDIN_PATTERN, link)
        if match:
            slug = match.group(1)
            linkedin_url = f"https://www.linkedin.com/in/{slug}"
            logger.debug(f"Extracted LinkedIn URL: {linkedin_url}")
            return linkedin_url

        # No LinkedIn URL found
        return None

    def _looks_like_position(self, text: str) -> bool:
        """
        Check if text looks like a job position.

        Filters out names, URLs, and other non-position strings.

        Args:
            text: Text to check

        Returns:
            True if looks like a position
        """
        if not text:
            return False

        # Too short or too long
        if len(text) < 5 or len(text) > 100:
            return False

        # Contains URL
        if 'http' in text.lower() or 'www.' in text.lower():
            return False

        # Common position keywords
        position_keywords = [
            'professor', 'associate', 'assistant', 'research', 'scientist',
            'director', 'manager', 'engineer', 'analyst', 'consultant',
            'fellow', 'postdoc', 'student', 'phd', 'lecturer', 'instructor'
        ]

        text_lower = text.lower()
        if any(keyword in text_lower for keyword in position_keywords):
            return True

        # If it has "at" or "in" followed by institution, likely a position
        if re.search(r'\bat\b|\bin\b', text_lower):
            return True

        # Default: not clearly a position
        return False


# Type hint
from typing import Optional
