#!/usr/bin/env python3
"""ProfileFile model for Jekyll markdown files in _people/ directory."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import frontmatter

from models.person import Person, Role


class ProfileFile:
    """Represents a Jekyll markdown file in `_people/` directory."""

    def __init__(self, file_path: str):
        """
        Initialize ProfileFile.

        Args:
            file_path: Absolute or relative path to markdown file
        """
        self.file_path = file_path
        self.frontmatter: dict = {}
        self.body: str = ""
        self.last_modified: Optional[datetime] = None
        self.exists: bool = False

    def load(self) -> "ProfileFile":
        """Read file from disk, parse frontmatter + body."""
        if not os.path.exists(self.file_path):
            self.exists = False
            return self

        self.exists = True

        # Get file modification time
        stat = os.stat(self.file_path)
        self.last_modified = datetime.fromtimestamp(stat.st_mtime)

        # Parse markdown file with frontmatter
        with open(self.file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            self.frontmatter = dict(post.metadata)
            self.body = post.content

        return self

    def save(self, dry_run: bool = False):
        """
        Write frontmatter + body back to disk.

        Args:
            dry_run: If True, skip actual file write
        """
        if dry_run:
            return

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

        # Create Post object with frontmatter and content
        post = frontmatter.Post(self.body, **self.frontmatter)

        # Write to file
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

        self.exists = True

    def get_cv_sourced_fields(self) -> list[str]:
        """Return list of field names marked cv_sourced in `_cv_metadata`."""
        cv_metadata = self.frontmatter.get("_cv_metadata", {})
        return [
            field_name
            for field_name, metadata in cv_metadata.items()
            if metadata.get("sourced", False)
        ]

    def is_manually_modified(self, field: str, new_value) -> bool:
        """
        Check if cv_sourced field was manually edited since last sync.

        Args:
            field: Field name to check
            new_value: New value from CV.numbers

        Returns:
            True if field was manually modified (preserve it)
        """
        cv_metadata = self.frontmatter.get("_cv_metadata", {})
        field_metadata = cv_metadata.get(field, {})

        # If field is not cv_sourced, it's manual
        if not field_metadata.get("sourced", False):
            return True

        # Check if current value differs from what CV would set
        current_value = self.frontmatter.get(field)

        # If values match, no modification
        if current_value == new_value:
            return False

        # If conflict was already logged, preserve manual edit
        if field_metadata.get("conflict_logged", False):
            return True

        # Values differ - check if modification happened after last sync
        last_synced_str = field_metadata.get("last_synced")
        if last_synced_str and self.last_modified:
            try:
                last_synced = datetime.fromisoformat(last_synced_str.replace('Z', '+00:00'))
                # If file was modified after last sync, it's manual
                if self.last_modified > last_synced:
                    return True
            except (ValueError, TypeError):
                pass

        # Default: values differ but no clear manual modification signal
        # Could be first sync or timestamp issue - preserve to be safe
        return True if current_value is not None else False

    def to_person(self) -> Person:
        """Convert frontmatter to Person object."""
        # Extract name parts
        title = self.frontmatter.get("title", "")
        name_parts = title.split()
        firstname = name_parts[0] if name_parts else ""
        lastname = name_parts[-1] if len(name_parts) > 1 else name_parts[0] if name_parts else ""

        # Extract roles
        roles_data = self.frontmatter.get("roles", [])
        roles = [Role.from_dict(r) for r in roles_data] if roles_data else []

        # Create Person object
        person = Person(
            name=self.frontmatter.get("author", title),
            firstname=firstname,
            lastname=lastname,
            roles=roles if roles else [Role(type="Unknown")],  # Must have at least one role
            current_position=self.frontmatter.get("current_position"),
            current_institution=self.frontmatter.get("current_institution"),
            linkedin_url=self.frontmatter.get("linkedin_url"),
            research_interests=self.frontmatter.get("research_interests", []),
            email=self.frontmatter.get("email"),
            avatar=self.frontmatter.get("avatar"),
            bio=self.body.strip() if self.body else None,
            publications=self.frontmatter.get("publications", []),
            alumni_status=self.frontmatter.get("alumni_status", False),
            profile_file_path=self.file_path,
            cv_metadata=self.frontmatter.get("_cv_metadata", {}),
        )

        return person

    @staticmethod
    def from_person(person: Person, file_path: str, existing_frontmatter: Optional[dict] = None) -> "ProfileFile":
        """
        Create ProfileFile from Person object.

        Args:
            person: Person object to convert
            file_path: Path where file will be saved
            existing_frontmatter: Existing frontmatter to preserve manual fields

        Returns:
            ProfileFile with populated frontmatter
        """
        profile = ProfileFile(file_path)

        # Start with existing frontmatter if provided (preserves manual fields)
        if existing_frontmatter:
            profile.frontmatter = existing_frontmatter.copy()
        else:
            # Initialize required fields per contracts/people-frontmatter-schema.yml
            profile.frontmatter = {
                "portfolio-item-category": ["people"],
                "portfolio-item-tag": [],
                "date": datetime.now().strftime("%Y-%m-%d"),
            }

        # Update CV-sourced fields
        profile.frontmatter["author"] = person.name
        profile.frontmatter["title"] = person.name
        profile.frontmatter["roles"] = [r.to_dict() for r in person.roles]

        if person.research_interests:
            profile.frontmatter["research_interests"] = person.research_interests

        if person.alumni_status is not None:
            profile.frontmatter["alumni_status"] = person.alumni_status

        # Set body if person has bio
        if person.bio:
            profile.body = person.bio

        # Initialize _cv_metadata if not present
        if "_cv_metadata" not in profile.frontmatter:
            profile.frontmatter["_cv_metadata"] = {}

        return profile
