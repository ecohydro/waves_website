#!/usr/bin/env python3
"""Person and Role data models for people profile management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Role:
    """Represents one affiliation period for a Person."""

    type: str  # One of: Graduate PhD, Graduate MA/MS, Postdoc, Undergrad, Visitor
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    degree: Optional[str] = None  # PhD, MS, MA, BS, BA, etc.
    institution: Optional[str] = None
    research_focus: Optional[str] = None

    def __post_init__(self):
        """Validate role data."""
        # Validate type
        valid_types = [
            "Graduate PhD", "Graduate MA/MS", "Postdoc",
            "Undergrad", "Visitor"
        ]
        if self.type not in valid_types:
            raise ValueError(
                f"Invalid role type: {self.type}. "
                f"Must be one of: {', '.join(valid_types)}"
            )

        # Validate years
        if self.start_year and self.end_year:
            if self.end_year < self.start_year:
                raise ValueError(
                    f"end_year ({self.end_year}) must be >= start_year ({self.start_year})"
                )

        # Validate years are reasonable (not too far in past or future)
        current_year = datetime.now().year
        if self.start_year and (self.start_year < 1990 or self.start_year > current_year + 1):
            raise ValueError(
                f"start_year ({self.start_year}) must be between 1990 and {current_year + 1}"
            )
        if self.end_year and (self.end_year < 1990 or self.end_year > current_year + 5):
            raise ValueError(
                f"end_year ({self.end_year}) must be between 1990 and {current_year + 5}"
            )

    def to_dict(self) -> dict:
        """Convert Role to dictionary for frontmatter."""
        result = {"type": self.type}
        if self.start_year is not None:
            result["start_year"] = self.start_year
        if self.end_year is not None:
            result["end_year"] = self.end_year
        if self.degree:
            result["degree"] = self.degree
        if self.institution:
            result["institution"] = self.institution
        if self.research_focus:
            result["research_focus"] = self.research_focus
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Role":
        """Create Role from dictionary."""
        return cls(
            type=data["type"],
            start_year=data.get("start_year"),
            end_year=data.get("end_year"),
            degree=data.get("degree"),
            institution=data.get("institution"),
            research_focus=data.get("research_focus"),
        )


@dataclass
class Person:
    """Unified representation of an individual affiliated with the research group."""

    name: str
    firstname: str
    lastname: str
    roles: list[Role] = field(default_factory=list)
    current_position: Optional[str] = None
    current_institution: Optional[str] = None
    linkedin_url: Optional[str] = None
    research_interests: list[str] = field(default_factory=list)
    email: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    publications: list[str] = field(default_factory=list)
    alumni_status: bool = False
    profile_file_path: Optional[str] = None
    cv_metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate person data."""
        # Must have at least one role
        if not self.roles:
            raise ValueError("Person must have at least one role")

        # Sort roles chronologically by start_year
        self.roles.sort(key=lambda r: r.start_year or 0)

        # Validate LinkedIn URL format if provided
        if self.linkedin_url and not self.linkedin_url.startswith("https://www.linkedin.com/in/"):
            raise ValueError(
                f"Invalid LinkedIn URL: {self.linkedin_url}. "
                f"Must match pattern: https://www.linkedin.com/in/*"
            )

    @property
    def most_recent_role(self) -> Role:
        """Get the most recent role (last in chronologically sorted list)."""
        return self.roles[-1] if self.roles else None

    @property
    def years_active(self) -> tuple[Optional[int], Optional[int]]:
        """Get range from earliest role start to latest role end."""
        if not self.roles:
            return (None, None)

        start_years = [r.start_year for r in self.roles if r.start_year]
        end_years = [r.end_year for r in self.roles if r.end_year]

        min_start = min(start_years) if start_years else None
        max_end = max(end_years) if end_years else None

        return (min_start, max_end)

    def add_role(self, role: Role):
        """Add a role and re-sort chronologically."""
        self.roles.append(role)
        self.roles.sort(key=lambda r: r.start_year or 0)

    def merge_role(self, new_role: Role):
        """
        Merge a new role into existing roles.

        If role with same type and overlapping years exists, update it.
        Otherwise, add as new role.
        """
        # Check for existing role with same type
        for existing_role in self.roles:
            if existing_role.type == new_role.type:
                # Check for overlapping or adjacent years
                if self._roles_overlap(existing_role, new_role):
                    # Update years to span both roles
                    existing_role.start_year = min(
                        existing_role.start_year or float('inf'),
                        new_role.start_year or float('inf')
                    ) if (existing_role.start_year or new_role.start_year) else None

                    existing_role.end_year = max(
                        existing_role.end_year or 0,
                        new_role.end_year or 0
                    ) if (existing_role.end_year or new_role.end_year) else None

                    # Update other fields if new_role has more info
                    if new_role.degree and not existing_role.degree:
                        existing_role.degree = new_role.degree
                    if new_role.institution and not existing_role.institution:
                        existing_role.institution = new_role.institution
                    if new_role.research_focus and not existing_role.research_focus:
                        existing_role.research_focus = new_role.research_focus

                    return

        # No overlap found, add as new role
        self.add_role(new_role)

    def _roles_overlap(self, role1: Role, role2: Role) -> bool:
        """Check if two roles overlap or are adjacent in time."""
        # If either role has no years, consider them non-overlapping
        if not role1.start_year or not role2.start_year:
            return False

        # Check for overlap or adjacent years (within 1 year)
        end1 = role1.end_year or datetime.now().year + 1
        end2 = role2.end_year or datetime.now().year + 1

        # Roles overlap if start of one is before end of other
        return (
            (role1.start_year <= end2 + 1 and end1 >= role2.start_year - 1) or
            (role2.start_year <= end1 + 1 and end2 >= role1.start_year - 1)
        )
