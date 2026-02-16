#!/usr/bin/env python3
"""Enrichment models for web-based profile enhancement."""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from models.profile_file import ProfileFile


@dataclass
class EnrichmentSuggestion:
    """Proposed update to a Person's profile based on web search results."""

    person_name: str
    profile_file_path: str
    field: str  # current_position, current_institution, linkedin_url
    current_value: Optional[str]
    suggested_value: str
    source_url: str
    source_snippet: str
    confidence: float  # 0.0-1.0
    confidence_breakdown: dict[str, float]  # rank_score, name_match_score, etc.
    timestamp: datetime
    query: str

    def __post_init__(self):
        """Validate suggestion data."""
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError(f"confidence must be in range [0.0, 1.0], got {self.confidence}")

        valid_fields = ["current_position", "current_institution", "linkedin_url"]
        if self.field not in valid_fields:
            raise ValueError(
                f"Invalid field: {self.field}. "
                f"Must be one of: {', '.join(valid_fields)}"
            )

    def meets_threshold(self) -> bool:
        """Returns True if confidence ≥ 0.6 (FR-013)."""
        return self.confidence >= 0.6

    def format_for_review(self) -> str:
        """Human-readable summary for manual review."""
        lines = []
        lines.append(f"\n{self.field}: {self.suggested_value} (confidence: {self.confidence:.2f})")
        lines.append(f"  Source: {self.source_url}")
        lines.append(f"  Snippet: {self.source_snippet[:100]}...")

        if self.current_value:
            lines.append(f"  Current: {self.current_value}")

        # Show confidence breakdown
        breakdown_str = ", ".join([
            f"{k}: {v:.2f}" for k, v in self.confidence_breakdown.items()
        ])
        lines.append(f"  Breakdown: {breakdown_str}")

        return "\n".join(lines)

    def apply_to_profile(self, profile: ProfileFile):
        """
        Update profile with suggested value.

        Marks field as NOT cv_sourced (manually reviewed enrichment).
        """
        # Update field value
        profile.frontmatter[self.field] = self.suggested_value

        # Mark field as not CV-sourced (it's from enrichment, manually approved)
        if "_cv_metadata" not in profile.frontmatter:
            profile.frontmatter["_cv_metadata"] = {}

        profile.frontmatter["_cv_metadata"][self.field] = {
            "sourced": False,  # Not from CV, from web enrichment
            "last_synced": None,
            "conflict_logged": False,
        }

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "person_name": self.person_name,
            "profile_file_path": self.profile_file_path,
            "field": self.field,
            "current_value": self.current_value,
            "suggested_value": self.suggested_value,
            "source_url": self.source_url,
            "source_snippet": self.source_snippet,
            "confidence": self.confidence,
            "confidence_breakdown": self.confidence_breakdown,
            "timestamp": self.timestamp.isoformat(),
            "query": self.query,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EnrichmentSuggestion":
        """Create from dictionary."""
        return cls(
            person_name=data["person_name"],
            profile_file_path=data["profile_file_path"],
            field=data["field"],
            current_value=data.get("current_value"),
            suggested_value=data["suggested_value"],
            source_url=data["source_url"],
            source_snippet=data["source_snippet"],
            confidence=data["confidence"],
            confidence_breakdown=data["confidence_breakdown"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            query=data["query"],
        )


class EnrichmentCache:
    """Stores web search results to avoid redundant API calls."""

    def __init__(self, cache_dir: str = ".cache/enrichment/"):
        """
        Initialize EnrichmentCache.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        self.cache_files: dict[str, str] = {}

        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)

        # Build cache file map
        self._scan_cache()

    def _scan_cache(self):
        """Scan cache directory and build file map."""
        if not os.path.exists(self.cache_dir):
            return

        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".json"):
                person_key = filename[:-5]  # Remove .json extension
                self.cache_files[person_key] = os.path.join(self.cache_dir, filename)

    def _get_person_key(self, person_name: str) -> str:
        """Generate cache key from person name."""
        # Convert "John Doe" → "doe_john"
        parts = person_name.lower().strip().split()
        if len(parts) >= 2:
            return f"{parts[-1]}_{parts[0]}"
        else:
            return parts[0] if parts else "unknown"

    def load(self, person_name: str) -> Optional[list[EnrichmentSuggestion]]:
        """
        Load cached suggestions for person.

        Args:
            person_name: Name of person

        Returns:
            List of EnrichmentSuggestion objects, or None if not cached
        """
        person_key = self._get_person_key(person_name)
        cache_file = self.cache_files.get(person_key)

        if not cache_file or not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            suggestions_data = data.get("suggestions", [])
            suggestions = [
                EnrichmentSuggestion.from_dict(s) for s in suggestions_data
            ]

            return suggestions

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Cache file corrupted or invalid format
            print(f"Warning: Failed to load cache for {person_name}: {e}")
            return None

    def save(self, person_name: str, suggestions: list[EnrichmentSuggestion], person_file: str = ""):
        """
        Write suggestions to cache.

        Args:
            person_name: Name of person
            suggestions: List of EnrichmentSuggestion objects
            person_file: Path to person's profile file
        """
        person_key = self._get_person_key(person_name)
        cache_file = os.path.join(self.cache_dir, f"{person_key}.json")

        data = {
            "person_name": person_name,
            "person_file": person_file,
            "last_updated": datetime.now().isoformat(),
            "suggestions": [s.to_dict() for s in suggestions],
        }

        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        self.cache_files[person_key] = cache_file

    def clear(self, person_name: Optional[str] = None):
        """
        Delete cache for specific person or all if None.

        Args:
            person_name: Name of person, or None to clear all cache
        """
        if person_name:
            # Clear specific person's cache
            person_key = self._get_person_key(person_name)
            cache_file = self.cache_files.get(person_key)

            if cache_file and os.path.exists(cache_file):
                os.remove(cache_file)
                del self.cache_files[person_key]

        else:
            # Clear all cache
            for cache_file in self.cache_files.values():
                if os.path.exists(cache_file):
                    os.remove(cache_file)

            self.cache_files.clear()

    def is_cached(self, person_name: str) -> bool:
        """Check if person has cached results."""
        person_key = self._get_person_key(person_name)
        cache_file = self.cache_files.get(person_key)
        return cache_file is not None and os.path.exists(cache_file)

    def get_cache_age(self, person_name: str) -> Optional[timedelta]:
        """
        How long since cache was created.

        Returns:
            timedelta since cache creation, or None if not cached
        """
        person_key = self._get_person_key(person_name)
        cache_file = self.cache_files.get(person_key)

        if not cache_file or not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            last_updated_str = data.get("last_updated")
            if last_updated_str:
                last_updated = datetime.fromisoformat(last_updated_str)
                return datetime.now() - last_updated

        except (json.JSONDecodeError, KeyError, ValueError):
            pass

        return None
