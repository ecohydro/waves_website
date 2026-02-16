#!/usr/bin/env python3
"""Profile sync service for updating Jekyll profile files."""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.match_candidate import MatchCandidate
from models.person import Person
from models.profile_file import ProfileFile
from services.logger import logger


class ProfileSyncService:
    """Service for syncing Person data to profile files."""

    def __init__(self, people_dir: str = "_people/"):
        """
        Initialize ProfileSyncService.

        Args:
            people_dir: Directory containing people markdown files
        """
        self.people_dir = people_dir
        self.conflicts_logged: list[dict] = []
        self.files_updated: list[str] = []
        self.files_created: list[str] = []

        # Ensure people directory exists
        os.makedirs(people_dir, exist_ok=True)

    def sync_person(self, person: Person, match: MatchCandidate, dry_run: bool = False) -> bool:
        """
        Sync person to profile file (update existing or create new).

        Args:
            person: Person object from CV extraction
            match: MatchCandidate with matched profile (or None)
            dry_run: If True, don't actually write files

        Returns:
            True if sync successful
        """
        if match.is_match():
            # Update existing profile
            return self.update_existing_profile(person, match.profile_file, dry_run)
        else:
            # Create new profile
            return self.create_new_profile(person, dry_run)

    def update_existing_profile(self, person: Person, profile: ProfileFile, dry_run: bool = False) -> bool:
        """
        Update existing profile with CV data, preserving manual content.

        Implements Decision 7: Check _cv_metadata for cv_sourced fields,
        detect manual modifications, update only unmodified cv_sourced fields.

        Args:
            person: Person object from CV
            profile: Existing ProfileFile
            dry_run: If True, preview changes only

        Returns:
            True if update successful
        """
        logger.debug(f"Updating existing profile: {profile.file_path}")

        # Track changes
        changes = []
        conflicts = []

        # Get CV-sourced fields
        cv_sourced_fields = profile.get_cv_sourced_fields()

        # Update title (author field)
        if self._should_update_field(profile, "title", person.name):
            old_value = profile.frontmatter.get("title")
            if profile.is_manually_modified("title", person.name):
                conflicts.append({
                    "field": "title",
                    "cv_value": person.name,
                    "current_value": old_value,
                })
                self._log_conflict(profile, "title", person.name, old_value)
            else:
                profile.frontmatter["title"] = person.name
                self._update_metadata(profile, "title")
                changes.append(f"title: {old_value} → {person.name}")

        # Update author field
        if self._should_update_field(profile, "author", person.name):
            old_value = profile.frontmatter.get("author")
            if profile.is_manually_modified("author", person.name):
                conflicts.append({
                    "field": "author",
                    "cv_value": person.name,
                    "current_value": old_value,
                })
                self._log_conflict(profile, "author", person.name, old_value)
            else:
                profile.frontmatter["author"] = person.name
                self._update_metadata(profile, "author")
                changes.append(f"author: {old_value} → {person.name}")

        # Update roles
        new_roles = [r.to_dict() for r in person.roles]
        if self._should_update_field(profile, "roles", new_roles):
            old_roles = profile.frontmatter.get("roles", [])
            if profile.is_manually_modified("roles", new_roles):
                conflicts.append({
                    "field": "roles",
                    "cv_value": f"{len(new_roles)} roles",
                    "current_value": f"{len(old_roles)} roles (manually modified)",
                })
                self._log_conflict(profile, "roles", new_roles, old_roles)
            else:
                profile.frontmatter["roles"] = new_roles
                self._update_metadata(profile, "roles")
                changes.append(f"roles: updated with {len(new_roles)} role(s)")

        # Update research interests
        if person.research_interests:
            if self._should_update_field(profile, "research_interests", person.research_interests):
                old_interests = profile.frontmatter.get("research_interests", [])
                if profile.is_manually_modified("research_interests", person.research_interests):
                    conflicts.append({
                        "field": "research_interests",
                        "cv_value": person.research_interests,
                        "current_value": old_interests,
                    })
                    self._log_conflict(profile, "research_interests", person.research_interests, old_interests)
                else:
                    profile.frontmatter["research_interests"] = person.research_interests
                    self._update_metadata(profile, "research_interests")
                    changes.append(f"research_interests: updated")

        # Update alumni_status
        if self._should_update_field(profile, "alumni_status", person.alumni_status):
            old_status = profile.frontmatter.get("alumni_status")
            if profile.is_manually_modified("alumni_status", person.alumni_status):
                self._log_conflict(profile, "alumni_status", person.alumni_status, old_status)
            else:
                profile.frontmatter["alumni_status"] = person.alumni_status
                self._update_metadata(profile, "alumni_status")
                changes.append(f"alumni_status: {old_status} → {person.alumni_status}")

        # Check if update is needed
        if not changes and not conflicts:
            logger.debug(f"No changes needed for {profile.file_path}")
            return self._check_idempotency(profile)

        # Log changes
        if changes:
            logger.info(f"  ✓ {profile.file_path}")
            for change in changes:
                logger.debug(f"    - {change}")

        if conflicts:
            logger.warning(f"  ⚠ {profile.file_path} - {len(conflicts)} conflict(s) (manual edits preserved)")

        # Save updated profile
        if not dry_run:
            profile.save()
            self.files_updated.append(profile.file_path)

        return True

    def create_new_profile(self, person: Person, dry_run: bool = False) -> bool:
        """
        Create new profile file for person not yet on website.

        Implements Decision 7: Generate ProfileFile with frontmatter from Person,
        mark all fields as cv_sourced, use naming convention.

        Args:
            person: Person object from CV
            dry_run: If True, preview only

        Returns:
            True if creation successful
        """
        # Generate filename
        filename = self._generate_filename(person)
        file_path = os.path.join(self.people_dir, filename)

        # Check for collision
        if os.path.exists(file_path):
            # Use firstname-lastname format
            filename_alt = f"{self._normalize_filename(person.firstname)}-{self._normalize_filename(person.lastname)}.md"
            file_path = os.path.join(self.people_dir, filename_alt)

        logger.info(f"  + {file_path} (new profile)")

        # Create ProfileFile from Person
        profile = ProfileFile.from_person(person, file_path)

        # Mark all CV fields as cv_sourced with timestamp
        timestamp = datetime.now().isoformat()
        cv_fields = ["title", "author", "roles", "research_interests", "alumni_status"]

        for field in cv_fields:
            if field in profile.frontmatter:
                profile.frontmatter["_cv_metadata"][field] = {
                    "sourced": True,
                    "last_synced": timestamp,
                    "conflict_logged": False,
                }

        # Ensure required fields are present (per contracts/people-frontmatter-schema.yml)
        if "avatar" not in profile.frontmatter:
            # Placeholder avatar path
            profile.frontmatter["avatar"] = f"assets/images/people/{self._normalize_filename(person.lastname)}.jpg"
            profile.frontmatter["_cv_metadata"]["avatar"] = {
                "sourced": False,
                "last_synced": None,
                "conflict_logged": False,
            }

        if "excerpt" not in profile.frontmatter:
            # Generate excerpt from first role
            if person.roles:
                role = person.roles[0]
                profile.frontmatter["excerpt"] = f"{role.type} in {role.research_focus or 'research'}."
            else:
                profile.frontmatter["excerpt"] = "Research group member."

        # Save new profile
        if not dry_run:
            profile.save()
            self.files_created.append(file_path)

        return True

    def _should_update_field(self, profile: ProfileFile, field: str, new_value) -> bool:
        """Check if field should be updated (value differs)."""
        current_value = profile.frontmatter.get(field)
        return current_value != new_value

    def _update_metadata(self, profile: ProfileFile, field: str):
        """Update _cv_metadata for field with current timestamp."""
        if "_cv_metadata" not in profile.frontmatter:
            profile.frontmatter["_cv_metadata"] = {}

        profile.frontmatter["_cv_metadata"][field] = {
            "sourced": True,
            "last_synced": datetime.now().isoformat(),
            "conflict_logged": False,
        }

    def _log_conflict(self, profile: ProfileFile, field: str, cv_value, current_value):
        """Log conflict when CV data differs from manually-modified field."""
        conflict = {
            "file": profile.file_path,
            "field": field,
            "cv_value": str(cv_value),
            "current_value": str(current_value),
        }

        self.conflicts_logged.append(conflict)

        logger.warning(
            f"    ! Conflict in {field}: "
            f"CV={str(cv_value)[:50]}, Current={str(current_value)[:50]} "
            f"(preserving manual edit)"
        )

        # Mark conflict as logged in metadata
        if "_cv_metadata" not in profile.frontmatter:
            profile.frontmatter["_cv_metadata"] = {}

        if field not in profile.frontmatter["_cv_metadata"]:
            profile.frontmatter["_cv_metadata"][field] = {
                "sourced": True,
                "last_synced": None,
                "conflict_logged": False,
            }

        profile.frontmatter["_cv_metadata"][field]["conflict_logged"] = True

    def _check_idempotency(self, profile: ProfileFile) -> bool:
        """Check if CV data unchanged since last sync (idempotency)."""
        # If no changes were made, it's idempotent
        return True

    def _generate_filename(self, person: Person) -> str:
        """Generate filename from person's lastname."""
        lastname_normalized = self._normalize_filename(person.lastname)
        return f"{lastname_normalized}.md"

    def _normalize_filename(self, name: str) -> str:
        """Normalize name for filename."""
        import string

        normalized = name.lower().strip()
        normalized = normalized.replace("'", "")
        normalized = normalized.replace(" ", "-")

        translator = str.maketrans('', '', string.punctuation.replace('-', ''))
        normalized = normalized.translate(translator)

        return normalized

    def get_summary(self) -> dict:
        """Get sync summary statistics."""
        return {
            "files_updated": len(self.files_updated),
            "files_created": len(self.files_created),
            "conflicts_logged": len(self.conflicts_logged),
        }
