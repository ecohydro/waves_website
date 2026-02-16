#!/usr/bin/env python3
"""Ingest publications from CV.numbers spreadsheet into Jekyll _publications/ collection."""

import argparse
import os
import random
import re
import sys
from datetime import datetime
from pathlib import Path

import frontmatter
import yaml
from numbers_parser import Document


# ---------------------------------------------------------------------------
# T002 / T003: CLI argument parsing and input validation
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Ingest publications from CV.numbers into Jekyll _publications/",
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Preview mode: report what would be created without writing files",
    )
    parser.add_argument(
        "-f", "--numbers-file",
        default=os.path.expanduser(
            "~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers"
        ),
        help="Path to the CV.numbers file",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="_publications/",
        help="Directory to write new publication files",
    )
    parser.add_argument(
        "-a", "--authors-file",
        default="_data/authors.yml",
        help="Path to the authors registry YAML",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show detailed output for each publication processed",
    )
    return parser.parse_args()


def validate_inputs(args):
    """Validate that all required input files and directories exist."""
    if not os.path.isfile(args.numbers_file):
        print(f"Error: CV.numbers file not found at {args.numbers_file}")
        print("Check that iCloud Drive is synced and the file exists.")
        sys.exit(1)

    if not os.path.isdir(args.output_dir):
        print(f"Error: Output directory not found: {args.output_dir}")
        sys.exit(1)

    if not os.path.isfile(args.authors_file):
        print(f"Error: Authors file not found or invalid: {args.authors_file}")
        sys.exit(1)

    try:
        with open(args.authors_file, "r", encoding="utf-8") as f:
            yaml.safe_load(f)
    except yaml.YAMLError:
        print(f"Error: Authors file not found or invalid: {args.authors_file}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# T004: Load Numbers spreadsheet data
# ---------------------------------------------------------------------------

def load_numbers_data(numbers_file):
    """Open CV.numbers, find the Publications sheet, and return rows as dicts."""
    doc = Document(numbers_file)

    # Find sheet by name
    try:
        sheet = doc.sheets["Publications"]
    except KeyError:
        print('Error: Sheet "Publications" not found in CV.numbers')
        sys.exit(1)

    table = sheet.tables[0]
    data = table.rows(values_only=True)

    if not data:
        return []

    headers = data[0]
    rows = []
    for row_values in data[1:]:
        # Skip completely empty rows
        if all(v is None for v in row_values):
            continue
        row = {}
        for i, header in enumerate(headers):
            if header is None:
                continue
            val = row_values[i] if i < len(row_values) else None
            # Convert float to int for numeric columns
            if header in ("YEAR", "NUM") and isinstance(val, float):
                val = int(val)
            row[header] = val
        rows.append(row)

    return rows


# ---------------------------------------------------------------------------
# T005: Load existing publications from _publications/ directory
# ---------------------------------------------------------------------------

def normalize_doi(doi):
    """Normalize a DOI for comparison: lowercase, strip prefixes and whitespace."""
    if not doi or doi == "-":
        return None
    doi = str(doi).strip().lower()
    # Strip common URL prefixes
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/",
                    "http://dx.doi.org/"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
    return doi


def normalize_title(title):
    """Normalize a title for comparison: lowercase, collapse whitespace."""
    if not title:
        return None
    return re.sub(r"\s+", " ", str(title).strip().lower())


def load_existing_publications(output_dir):
    """Scan _publications/*.md and extract DOIs, titles+years, and IDs."""
    existing_dois = set()
    existing_title_years = set()
    existing_ids = set()

    pub_dir = Path(output_dir)
    if not pub_dir.is_dir():
        return existing_dois, existing_title_years, existing_ids

    for md_file in pub_dir.glob("*.md"):
        try:
            post = frontmatter.load(str(md_file))
        except Exception:
            continue

        meta = post.metadata

        # Collect ID
        pub_id = meta.get("id")
        if pub_id is not None:
            existing_ids.add(int(pub_id))

        # Collect normalized DOI
        doi = normalize_doi(meta.get("doi"))
        if doi:
            existing_dois.add(doi)

        # Collect normalized title + year
        title = normalize_title(meta.get("title"))
        year = meta.get("year")
        if title and year:
            existing_title_years.add((title, str(year)))

    return existing_dois, existing_title_years, existing_ids


# ---------------------------------------------------------------------------
# T006: Load author registry from _data/authors.yml
# ---------------------------------------------------------------------------

def load_author_registry(authors_file):
    """Read authors.yml and return known group member names and a surname lookup.

    Returns:
        known_authors: set of full names (e.g., "Kelly Caylor")
        surname_to_full: dict mapping lowercase surname → full name
            Used to match citation-format names from the spreadsheet.
    """
    with open(authors_file, "r", encoding="utf-8") as f:
        authors_data = yaml.safe_load(f)

    known_authors = set()
    surname_to_full = {}
    if authors_data:
        for key in authors_data:
            full_name = str(key)
            known_authors.add(full_name)
            # Extract surname (last word of the full name)
            surname = full_name.split()[-1].lower()
            surname_to_full[surname] = full_name

    # Special case: site owner defined in _config.yml, not authors.yml
    known_authors.add("Kelly Caylor")
    surname_to_full["caylor"] = "Kelly Caylor"

    return known_authors, surname_to_full


# ---------------------------------------------------------------------------
# T007: Filter to published rows only
# ---------------------------------------------------------------------------

def filter_published_rows(rows):
    """Filter rows to Type == 'P' only. Return (published_rows, skipped_count)."""
    published = []
    skipped = 0
    for row in rows:
        pub_type = row.get("Type")
        if pub_type == "P":
            published.append(row)
        else:
            skipped += 1
    return published, skipped


# ---------------------------------------------------------------------------
# T008: Find missing publications (not yet on website)
# ---------------------------------------------------------------------------

def find_missing_publications(published_rows, existing_dois, existing_title_years,
                              verbose=False):
    """Compare published rows against existing entries. Return (missing, matched)."""
    missing = []
    matched = []

    for row in published_rows:
        title = row.get("TITLE", "")
        year = row.get("YEAR")
        doi_raw = row.get("DOI")
        doi = normalize_doi(doi_raw)

        # Primary match: DOI
        if doi and doi in existing_dois:
            matched.append(row)
            if verbose:
                print(f"  Matched (DOI): {title[:60]}... → doi:{doi}")
            continue

        # Fallback match: title + year
        norm_title = normalize_title(title)
        if norm_title and year and (norm_title, str(int(year) if isinstance(year, float) else year)) in existing_title_years:
            matched.append(row)
            if verbose:
                print(f"  Matched (title+year): {title[:60]}...")
            continue

        # No match → missing
        missing.append(row)
        if verbose:
            print(f"  Missing: {title[:60]}... ({year})")

    return missing, matched


# ---------------------------------------------------------------------------
# T009: Generate unique publication ID
# ---------------------------------------------------------------------------

def generate_publication_id(existing_ids):
    """Generate a random 4-digit ID not in existing_ids. Add it to the set."""
    while True:
        pub_id = random.randint(1000, 9999)
        if pub_id not in existing_ids:
            existing_ids.add(pub_id)
            return pub_id


# ---------------------------------------------------------------------------
# T010: Determine primary author from group-role columns
# ---------------------------------------------------------------------------

ROLE_COLUMNS = [
    "Undergrad Author",
    "Visitor Author",
    "PhD Committee Member",
    "Graduate Advisee",
    "Postdoctoral Advisee",
    "PI Author",
]


def parse_author_position(value):
    """Parse 'A2' → 2, 'A14' → 14. Return None if invalid."""
    if not value or not isinstance(value, str):
        return None
    m = re.match(r"^A(\d+)$", value.strip())
    if m:
        return int(m.group(1))
    return None


def citation_name_to_surname(cite_name):
    """Extract surname from citation-format name: 'Caylor, K.K.' → 'caylor'."""
    if not cite_name:
        return None
    name = str(cite_name).strip()
    if "," in name:
        return name.split(",")[0].strip().lower()
    # No comma — might be a single name or full name
    parts = name.split()
    return parts[-1].strip().lower() if parts else None


def match_citation_author(cite_name, surname_to_full):
    """Match a citation-format name against the author registry via surname lookup.

    Returns the full name (e.g., 'Kelly Caylor') if matched, else None.
    """
    surname = citation_name_to_surname(cite_name)
    if surname:
        return surname_to_full.get(surname)
    return None


def determine_primary_author(row, known_authors, surname_to_full):
    """Find the group member with the earliest author position via role columns."""
    best_position = None
    best_name = None

    for role_col in ROLE_COLUMNS:
        pos_str = row.get(role_col)
        pos = parse_author_position(pos_str)
        if pos is None:
            continue

        # Resolve author name from the A# column
        author_col = f"A{pos}"
        author_name = row.get(author_col)
        if not author_name:
            continue

        cite_name = str(author_name).strip()

        # Check group membership via surname matching
        full_name = match_citation_author(cite_name, surname_to_full)
        if full_name is None:
            continue

        if best_position is None or pos < best_position:
            best_position = pos
            best_name = full_name

    # Fallback: if no role columns matched, use first group author found
    if best_name is None:
        for i in range(1, 32):
            author_name = row.get(f"A{i}")
            if author_name:
                full_name = match_citation_author(
                    str(author_name).strip(), surname_to_full
                )
                if full_name:
                    best_name = full_name
                    break

    # Final fallback: Kelly Caylor (PI is always involved)
    if best_name is None:
        best_name = "Kelly Caylor"

    return best_name


# ---------------------------------------------------------------------------
# T011: Find all group member author tags
# ---------------------------------------------------------------------------

def find_author_tags(row, surname_to_full):
    """Return list of group member full names found in A1-A31, in position order."""
    tags = []
    seen = set()
    for i in range(1, 32):
        author_name = row.get(f"A{i}")
        if author_name:
            cite_name = str(author_name).strip()
            full_name = match_citation_author(cite_name, surname_to_full)
            if full_name and full_name not in seen:
                tags.append(full_name)
                seen.add(full_name)
    return tags


# ---------------------------------------------------------------------------
# T012: Format a full name into citation format
# ---------------------------------------------------------------------------

def format_citation_name(full_name):
    """Convert 'Kelly Caylor' → 'Caylor, K.' or 'Kelly K. Caylor' → 'Caylor, K.K.'"""
    if not full_name:
        return ""
    parts = str(full_name).strip().split()
    if len(parts) == 1:
        return parts[0]

    surname = parts[-1]
    initials = "".join(p[0] + "." for p in parts[:-1])
    return f"{surname}, {initials}"


# ---------------------------------------------------------------------------
# T013: Build the excerpt (short citation for frontmatter)
# ---------------------------------------------------------------------------

def get_authors_list(row):
    """Extract non-empty author names from A1-A31."""
    authors = []
    for i in range(1, 32):
        name = row.get(f"A{i}")
        if name:
            authors.append(str(name).strip())
    return authors


def clean_citation_name(name):
    """Clean a citation-format name: strip trailing commas/spaces."""
    if not name:
        return ""
    name = str(name).strip()
    # Remove trailing commas or periods that look wrong
    name = name.rstrip(",").strip()
    # Ensure trailing period on initials
    if re.search(r"[A-Z]$", name):
        name += "."
    return name


def build_excerpt(row):
    """Build the excerpt citation string for frontmatter.

    Names in the spreadsheet are already in citation format (e.g., 'Caylor, K.K.').
    """
    authors = get_authors_list(row)
    year = row.get("YEAR", "")
    if isinstance(year, float):
        year = int(year)
    title = row.get("TITLE", "")
    journal = row.get("PUBLISHER", "")
    doi_raw = row.get("DOI", "")
    doi = normalize_doi(doi_raw)

    if not authors:
        first_author_cite = "Unknown"
    else:
        first_author_cite = clean_citation_name(authors[0])

    et_al = " et al." if len(authors) > 1 else ""

    doi_part = f", doi:{doi_raw}" if doi else ""

    excerpt = (
        f'{first_author_cite}{et_al} ({year}). '
        f'{title}. _{journal}_{doi_part}.'
    )
    return excerpt


# ---------------------------------------------------------------------------
# T014: Build the full citation blockquote
# ---------------------------------------------------------------------------

def build_full_citation(row):
    """Build the complete citation with all authors for the body blockquote.

    Names in the spreadsheet are already in citation format (e.g., 'Caylor, K.K.').
    """
    authors = get_authors_list(row)
    year = row.get("YEAR", "")
    if isinstance(year, float):
        year = int(year)
    title = row.get("TITLE", "")
    journal = row.get("PUBLISHER", "")
    volume = row.get("VOL", "")
    pages = row.get("PAGES", "")
    doi_raw = row.get("DOI", "")
    doi = normalize_doi(doi_raw)

    # Authors are already in citation format — just clean them
    if not authors:
        authors_str = "Unknown"
    elif len(authors) == 1:
        authors_str = clean_citation_name(authors[0])
    else:
        cleaned = [clean_citation_name(a) for a in authors]
        authors_str = ", ".join(cleaned[:-1]) + ", & " + cleaned[-1]

    # Build volume/pages portion
    vol_part = ""
    if volume:
        vol_str = str(volume)
        vol_part = f", {vol_str}"
    if pages:
        vol_part += f", {pages}"

    doi_part = f", doi:{doi_raw}" if doi else ""

    citation = (
        f"{authors_str} ({year}). "
        f"{title}. "
        f"_{journal}_{vol_part}{doi_part}."
    )
    return citation


# ---------------------------------------------------------------------------
# T015: Build complete frontmatter dictionary
# ---------------------------------------------------------------------------

def build_frontmatter(row, pub_id, primary_author, author_tags):
    """Assemble the YAML frontmatter dict for a publication entry."""
    year = row.get("YEAR", "")
    if isinstance(year, float):
        year = int(year)
    title = row.get("TITLE", "")
    journal = row.get("PUBLISHER", "")
    doi_raw = row.get("DOI", "")
    doi = normalize_doi(doi_raw)

    # Determine last name for paths
    last_name = str(primary_author).strip().split()[-1]

    meta = {
        "author": primary_author,
        "date": datetime(int(year), 1, 1),
        "id": pub_id,
        "year": str(year),
        "title": title,
    }

    if doi:
        meta["doi"] = doi_raw

    meta["excerpt"] = build_excerpt(row)
    meta["header"] = {
        "teaser": f"assets/images/publications/{last_name}{year}_{pub_id}.png",
    }
    meta["portfolio-item-category"] = ["publications"]
    meta["portfolio-item-tag"] = [str(year), journal]
    meta["author-tags"] = author_tags if author_tags else [primary_author]

    return meta


# ---------------------------------------------------------------------------
# T016: Build markdown body content
# ---------------------------------------------------------------------------

def build_body_content(row, pub_id, primary_author):
    """Generate the markdown body for a publication entry."""
    year = row.get("YEAR", "")
    if isinstance(year, float):
        year = int(year)
    doi_raw = row.get("DOI", "")
    doi = normalize_doi(doi_raw)
    abstract = row.get("Abstract", "")

    last_name = str(primary_author).strip().split()[-1]

    # Image placeholder
    image_path = f"assets/images/publications/{last_name}{year}_{pub_id}_figure.png"
    body_parts = [
        f'![ first page ]({{{{ "{image_path}" | absolute_url }}}})'
        '{:class="img-responsive" width="50%" .align-right}',
        "",
    ]

    # Full citation blockquote
    full_citation = build_full_citation(row)
    body_parts.append(f"> {full_citation}")
    body_parts.append("")

    # Abstract
    if abstract and str(abstract).strip():
        body_parts.append(f"**Abstract**: {str(abstract).strip()}")
        body_parts.append("")

    # Article link
    if doi:
        body_parts.append(
            f"[Go to the Article](https://www.doi.org/{doi_raw})"
            "{: .btn .btn--success}"
        )
        body_parts.append("")

    return "\n".join(body_parts)


# ---------------------------------------------------------------------------
# T017: Write publication file to disk
# ---------------------------------------------------------------------------

def write_publication_file(output_dir, meta, body, primary_author):
    """Write a complete publication markdown file."""
    year = meta["year"]
    pub_id = meta["id"]
    last_name = str(primary_author).strip().split()[-1]
    filename = f"{last_name}{year}_{pub_id}.md"
    filepath = os.path.join(output_dir, filename)

    post = frontmatter.Post(body)
    post.metadata = meta

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))
        f.write("\n")

    return filepath


# ---------------------------------------------------------------------------
# T018: Check for missing critical data and generate warnings
# ---------------------------------------------------------------------------

def check_missing_data(row):
    """Check if critical data is missing. Return list of missing field names."""
    missing = []
    doi_raw = row.get("DOI", "")
    doi = normalize_doi(doi_raw)
    if not doi:
        missing.append("DOI")

    abstract = row.get("Abstract")
    if not abstract or not str(abstract).strip():
        missing.append("abstract")

    a1 = row.get("A1")
    if not a1 or not str(a1).strip():
        missing.append("author list")

    return missing


# ---------------------------------------------------------------------------
# T022: Format summary report
# ---------------------------------------------------------------------------

def format_summary_report(matched_count, created_count, skipped_nonp_count,
                          warnings, created_files, dry_run=False):
    """Generate the results summary."""
    lines = []

    if dry_run:
        prefix = "Would "
    else:
        prefix = ""

    lines.append("")
    lines.append("Results:" if not dry_run else "Summary:")
    lines.append(f"  {prefix}Matched (skipped):  {matched_count}")
    lines.append(f"  {prefix}Created:            {created_count}")
    lines.append(f"  Skipped (non-P):      {skipped_nonp_count}")
    lines.append(f"  Warnings:             {len(warnings)}")

    if warnings:
        lines.append("")
        lines.append("Warnings:")
        for title, year, missing_fields in warnings:
            fields = ", ".join(missing_fields)
            lines.append(f'  \u26a0 "{title}" ({year}) - missing {fields}')

    if created_files and not dry_run:
        lines.append("")
        lines.append("New files created:")
        for fpath in created_files:
            lines.append(f"  {fpath}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# T019 / T020 / T021 / T023 / T024: Main ingestion loop
# ---------------------------------------------------------------------------

def main():
    args = parse_args()
    validate_inputs(args)

    # --- Load data sources ---
    print(f"Reading CV.numbers from {args.numbers_file}")
    rows = load_numbers_data(args.numbers_file)
    print(f"Found {len(rows)} publications in spreadsheet", end="")

    # Filter to published
    published_rows, skipped_nonp = filter_published_rows(rows)
    print(f" ({len(published_rows)} published)")

    # Load existing publications
    print(f"Scanning {args.output_dir} for existing entries...", end=" ")
    existing_dois, existing_title_years, existing_ids = load_existing_publications(
        args.output_dir
    )
    print(f"{len(existing_ids)} found")

    # Load author registry
    known_authors, surname_to_full = load_author_registry(args.authors_file)
    if args.verbose:
        print(f"Loaded {len(known_authors)} known authors from {args.authors_file}")

    # --- Find missing publications ---
    if args.verbose:
        print("\nMatching publications:")
    missing, matched = find_missing_publications(
        published_rows, existing_dois, existing_title_years, verbose=args.verbose,
    )

    # --- Handle all-up-to-date case ---
    if not missing:
        print("\nAll publications are up to date. No new entries needed.")
        sys.exit(0)

    # --- Dry run header ---
    if args.dry_run:
        print(f"\nDRY RUN - No files will be written")
        print(f"\nWould create {len(missing)} new publication entries:")

    # --- Process each missing publication ---
    warnings = []
    created_files = []

    for idx, row in enumerate(missing, 1):
        title = row.get("TITLE", "Unknown")
        year = row.get("YEAR", "")
        if isinstance(year, float):
            year = int(year)

        # Check for missing critical data
        missing_fields = check_missing_data(row)
        if missing_fields:
            warnings.append((title, year, missing_fields))

        # Skip rows with no title (can't create entry)
        if not title or not str(title).strip():
            if args.verbose:
                print(f"  Skipping row with no title")
            continue

        # Generate ID
        pub_id = generate_publication_id(existing_ids)

        # Determine primary author
        primary_author = determine_primary_author(row, known_authors, surname_to_full)

        # Find author tags
        author_tags = find_author_tags(row, surname_to_full)

        if args.dry_run:
            # Preview only — use raw citation names from spreadsheet
            authors = get_authors_list(row)
            if authors:
                first_author_cite = clean_citation_name(authors[0])
            else:
                first_author_cite = primary_author
            et_al = " et al." if len(authors) > 1 else ""
            print(f'  {idx}. {first_author_cite}{et_al} ({year}) - "{title}"')
            created_files.append(f"(would create)")
        else:
            # Build and write
            meta = build_frontmatter(row, pub_id, primary_author, author_tags)
            body = build_body_content(row, pub_id, primary_author)
            filepath = write_publication_file(
                args.output_dir, meta, body, primary_author
            )
            created_files.append(filepath)

            if args.verbose:
                print(
                    f"  Created: {filepath} "
                    f"(author={primary_author}, tags={author_tags})"
                )

    # --- Summary report ---
    report = format_summary_report(
        matched_count=len(matched),
        created_count=len(missing),
        skipped_nonp_count=skipped_nonp,
        warnings=warnings,
        created_files=created_files,
        dry_run=args.dry_run,
    )
    print(report)

    # --- Exit code ---
    if warnings and not args.dry_run:
        sys.exit(2)  # Partial success with warnings
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
