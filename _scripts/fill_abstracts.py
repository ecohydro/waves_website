#!/usr/bin/env python3
"""
Fill missing abstracts in publication markdown files using Scholar API.

Usage:
    python _scripts/fill_abstracts.py [OPTIONS]

Options:
    --dry-run, -n              Preview mode: report what would be updated without making API calls
    --publications-dir, -p     Directory containing publication markdown files (default: _publications/)
    --numbers-file, -f         Path to CV.numbers file (default: iCloud path)
    --skip-cv-writeback        Skip writing abstracts back to CV.numbers
    --verbose, -v              Show detailed output for each publication
    --max-publications, -m     Limit processing to first N publications (for testing)
"""

import argparse
import os
import random
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import frontmatter
import requests
from dotenv import load_dotenv
from numbers_parser import Document


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fill missing abstracts in publication files using Scholar API",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Preview mode: report what would be updated without making API calls or modifying files'
    )

    parser.add_argument(
        '--publications-dir', '-p',
        type=str,
        default='_publications/',
        help='Directory containing publication markdown files (default: _publications/)'
    )

    parser.add_argument(
        '--numbers-file', '-f',
        type=str,
        default=os.path.expanduser('~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers'),
        help='Path to CV.numbers file'
    )

    parser.add_argument(
        '--skip-cv-writeback',
        action='store_true',
        help='Skip writing abstracts back to CV.numbers (only update markdown files)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output for each publication processed'
    )

    parser.add_argument(
        '--max-publications', '-m',
        type=int,
        default=None,
        help='Limit processing to first N publications (for testing)'
    )

    return parser.parse_args()


def validate_inputs(args):
    """
    Validate input arguments and required files.

    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    # Check publications directory exists
    pub_dir = Path(args.publications_dir)
    if not pub_dir.exists():
        return False, f"Error: Publications directory not found: {args.publications_dir}\nCheck that you are running from the repository root"

    if not pub_dir.is_dir():
        return False, f"Error: Publications path is not a directory: {args.publications_dir}"

    # Check CV.numbers file exists (unless --skip-cv-writeback)
    if not args.skip_cv_writeback:
        cv_file = Path(args.numbers_file)
        if not cv_file.exists():
            return False, f"Error: CV.numbers file not found: {args.numbers_file}\nEnsure iCloud Drive is synced, or use --numbers-file to specify a different path"

    # Check .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        return False, "Error: .env file not found in repository root\nCreate .env file with SCHOLAR_API_KEY=your_api_key_here"

    return True, None


def load_api_key():
    """
    Load Scholar API key from environment.

    Returns:
        tuple: (api_key: str or None, masked_key: str or None, error: str or None)
    """
    # Load environment variables from .env file
    load_dotenv()

    api_key = os.getenv('SCHOLAR_API_KEY')

    if not api_key:
        return None, None, "Error: SCHOLAR_API_KEY environment variable not found\nPlease add SCHOLAR_API_KEY to your .env file or set it in your environment"

    # Create masked version for logging (first 4 chars + ****)
    masked_key = api_key[:4] + '****' if len(api_key) > 4 else '****'

    return api_key, masked_key, None


def scan_publications(publications_dir):
    """
    Scan publication markdown files and extract metadata.

    Args:
        publications_dir: Path to _publications/ directory

    Returns:
        list: List of publication dictionaries with:
            - file_path: absolute path to .md file
            - filename: just the filename
            - doi: DOI string or None
            - title: publication title
            - year: publication year (str or int)
            - author: primary author name
            - author_tags: list of group member names
            - body_content: markdown body after frontmatter
            - has_abstract: True if body contains **Abstract**: pattern
    """
    publications = []
    pub_dir = Path(publications_dir)

    # Scan all .md files
    for md_file in sorted(pub_dir.glob('*.md')):
        try:
            # Parse frontmatter and body
            with open(md_file, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            # Extract required fields
            metadata = post.metadata
            body = post.content

            # Check for existing abstract
            has_abstract = bool(re.search(r'\*\*Abstract\*\*:', body))

            publication = {
                'file_path': str(md_file.absolute()),
                'filename': md_file.name,
                'doi': metadata.get('doi'),
                'title': metadata.get('title', ''),
                'year': metadata.get('year', ''),
                'author': metadata.get('author', ''),
                'author_tags': metadata.get('author-tags', []),
                'body_content': body,
                'has_abstract': has_abstract
            }

            publications.append(publication)

        except Exception as e:
            print(f"Warning: Failed to parse {md_file.name}: {e}", file=sys.stderr)
            continue

    return publications


def load_cv_numbers(numbers_file_path):
    """
    Load CV.numbers spreadsheet and extract publication rows.

    Args:
        numbers_file_path: Path to CV.numbers file

    Returns:
        tuple: (rows: list or None, sheet: Sheet object or None, doc: Document object or None, error: str or None)
            rows: List of row dictionaries with:
                - row_index: 0-based row index in sheet
                - doi: DOI string (normalized) or None
                - title: publication title (normalized)
                - year: publication year as string
                - abstract: existing abstract text or None
    """
    try:
        doc = Document(numbers_file_path)

        # Find Publications sheet
        sheets = doc.sheets
        pub_sheet = None
        for sheet in sheets:
            if sheet.name == 'Publications':
                pub_sheet = sheet
                break

        if not pub_sheet:
            return None, None, None, "Error: 'Publications' sheet not found in CV.numbers file"

        # Find column indices
        table = pub_sheet.tables[0]
        headers = []
        for i in range(table.num_cols):
            cell = table.cell(0, i)
            headers.append(cell.value if cell.value else '')

        try:
            doi_col = headers.index('DOI')
            title_col = headers.index('TITLE')
            year_col = headers.index('YEAR')
            abstract_col = headers.index('Abstract')
        except ValueError as e:
            return None, None, None, f"Error: Required column not found in Publications sheet: {e}"

        # Read all rows
        rows = []
        for row_idx in range(1, table.num_rows):  # Skip header row
            doi_cell = table.cell(row_idx, doi_col)
            title_cell = table.cell(row_idx, title_col)
            year_cell = table.cell(row_idx, year_col)
            abstract_cell = table.cell(row_idx, abstract_col)

            # Extract values (handle EmptyCell as None)
            doi_val = doi_cell.value if doi_cell.value else None
            title_val = title_cell.value if title_cell.value else ''
            year_val = year_cell.value if year_cell.value else ''
            abstract_val = abstract_cell.value if abstract_cell.value else None

            # Normalize DOI (lowercase, strip https://doi.org/ prefix)
            if doi_val and doi_val != '-':
                doi_normalized = doi_val.lower().replace('https://doi.org/', '').strip()
            else:
                doi_normalized = None

            # Normalize title (lowercase, collapse whitespace)
            title_normalized = re.sub(r'\s+', ' ', title_val.lower().strip())

            row = {
                'row_index': row_idx,
                'doi': doi_normalized,
                'title': title_normalized,
                'year': str(year_val),
                'abstract': abstract_val
            }

            rows.append(row)

        return rows, pub_sheet, doc, None

    except Exception as e:
        return None, None, None, f"Error: Failed to load CV.numbers file: {e}"


# ============================================================================
# Phase 3: User Story 1 - Core Abstract Retrieval (T007-T019)
# ============================================================================

def filter_missing_abstracts(publications):
    """
    Filter publications to only those missing abstracts (T007).

    Args:
        publications: List of publication dicts from scan_publications()

    Returns:
        list: Publications where has_abstract == False
    """
    return [p for p in publications if not p['has_abstract']]


def build_api_request_doi(doi):
    """
    Build Scholar API request for DOI-based search (T008).

    Args:
        doi: DOI string (e.g., "10.1029/2002jd002448")

    Returns:
        dict: Query parameters for Scholar API
    """
    # URL-encode DOI for keywords parameter
    keywords = quote(doi)

    # Natural language query
    query = f"Find the abstract of the manuscript with this doi: {doi}"

    return {
        'keywords': keywords,
        'query': query,
        'sort': 'relevance',
        'peer_reviewed_only': 'true',
        'generative_mode': 'true'
    }


def build_api_request_title_year(title, year):
    """
    Build Scholar API request for title+year search (T009).

    Args:
        title: Publication title
        year: Publication year

    Returns:
        dict: Query parameters for Scholar API
    """
    # URL-encode title (first 100 chars to avoid URL length limits)
    title_truncated = title[:100] if len(title) > 100 else title
    keywords = quote(title_truncated)

    # Natural language query
    query = f'Find the abstract of the publication titled "{title}" published in {year}'

    return {
        'keywords': keywords,
        'query': query,
        'sort': 'relevance',
        'peer_reviewed_only': 'true',
        'generative_mode': 'true'
    }


def query_scholar_api(api_key, params, verbose=False):
    """
    Query Scholar API with retry logic (T010).

    Args:
        api_key: Scholar API key
        params: Query parameters dict
        verbose: Print detailed output

    Returns:
        tuple: (response_json: dict or None, error: str or None)
    """
    base_url = "https://api.scholarai.io/api/abstracts"
    headers = {'x-scholarai-api-key': api_key}

    # Retry logic: 3 attempts with exponential backoff
    for attempt in range(1, 4):
        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=30)

            # Check for permanent errors (don't retry)
            if response.status_code in [400, 401, 404]:
                return None, f"API error ({response.status_code}): {response.text}"

            # Check for transient errors (retry)
            if response.status_code in [429, 500]:
                if attempt < 3:
                    delay = 2 ** attempt + random.uniform(-0.5, 0.5)
                    if verbose:
                        print(f"  Transient error ({response.status_code}), retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                else:
                    return None, f"API error ({response.status_code}) after 3 retries"

            # Success
            response.raise_for_status()
            return response.json(), None

        except requests.exceptions.Timeout:
            if attempt < 3:
                delay = 2 ** attempt + random.uniform(-0.5, 0.5)
                if verbose:
                    print(f"  Timeout, retrying in {delay:.1f}s...")
                time.sleep(delay)
                continue
            else:
                return None, "API timeout after 3 retries"

        except requests.exceptions.RequestException as e:
            return None, f"Network error: {e}"

    return None, "Unexpected: retry loop exhausted"


def parse_api_response(response_json, verbose=False):
    """
    Extract and validate abstract from Scholar API response (T011).

    Args:
        response_json: JSON response from Scholar API
        verbose: Print detailed output

    Returns:
        tuple: (abstract: str or None, error: str or None)
    """
    # Check for results
    if response_json.get('total_num_results', 0) == 0:
        return None, "API returned no results"

    paper_data = response_json.get('paper_data', [])
    if not paper_data:
        return None, "Empty results array"

    # Extract abstract from first result
    abstract = paper_data[0].get('answer', '')

    # Validate
    if not abstract or len(abstract) < 50:
        return None, f"Invalid abstract (length: {len(abstract)})"

    return abstract, None


def extract_surnames(author, author_tags=None):
    """
    Extract author surnames from publication metadata (T012).

    Args:
        author: Primary author string (e.g., "Kelly Caylor")
        author_tags: List of group member names (optional)

    Returns:
        list: Lowercase surnames
    """
    surnames = []

    # Extract from primary author
    if author:
        parts = author.split()
        if parts:
            surnames.append(parts[-1].lower())

    # Extract from author tags
    if author_tags:
        for name in author_tags:
            parts = name.split()
            if parts:
                surnames.append(parts[-1].lower())

    return surnames


def resolve_ambiguous_results(response_json, pub_year, pub_surnames, verbose=False):
    """
    Select best match when API returns multiple results (T013).

    Args:
        response_json: Scholar API response with multiple results
        pub_year: Publication year from frontmatter
        pub_surnames: List of surnames from publication authors
        verbose: Print detailed output

    Returns:
        str or None: Abstract text from matched result, or None if no match
    """
    paper_data = response_json.get('paper_data', [])
    pub_year_str = str(pub_year)

    for result in paper_data:
        # Check year match
        if result.get('publicationDate', '') != pub_year_str:
            if verbose:
                print(f"    Skipping result: year mismatch ({result.get('publicationDate')})")
            continue

        # Check surname match
        creators = result.get('creators', [])
        result_surnames = [creator.split()[-1].lower() for creator in creators if creator]

        if any(surname in result_surnames for surname in pub_surnames):
            if verbose:
                print(f"    Matched result: year={pub_year_str}, surname match found")
            return result.get('answer', None)

    return None


def insert_abstract(body_content, abstract_text):
    """
    Insert abstract into markdown body after citation blockquote (T014).

    Args:
        body_content: Original markdown body
        abstract_text: Abstract to insert

    Returns:
        str: Updated body content
    """
    # Split into paragraphs
    paragraphs = body_content.split('\n\n')

    # Find blockquote paragraph (starts with > )
    blockquote_idx = None
    for i, para in enumerate(paragraphs):
        if para.strip().startswith('> '):
            blockquote_idx = i
            break

    # Insert abstract after blockquote
    if blockquote_idx is not None:
        abstract_para = f"**Abstract**: {abstract_text}"
        paragraphs.insert(blockquote_idx + 1, abstract_para)
    else:
        # Fallback: insert at beginning
        abstract_para = f"**Abstract**: {abstract_text}"
        paragraphs.insert(0, abstract_para)

    return '\n\n'.join(paragraphs)


def update_publication_file(file_path, updated_body):
    """
    Write updated body content back to publication file (T015).

    Args:
        file_path: Path to publication markdown file
        updated_body: New body content with abstract

    Returns:
        tuple: (success: bool, error: str or None)
    """
    try:
        # Read original file
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)

        # Update body, preserve frontmatter
        post.content = updated_body

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))

        return True, None

    except Exception as e:
        return False, f"File write error: {e}"


def format_summary_report(results):
    """
    Format summary report for console output (T018).

    Args:
        results: Dict with processing statistics

    Returns:
        str: Formatted report
    """
    report = ["\nResults:"]
    report.append(f"  Total scanned:           {results['total_scanned']} files")
    report.append(f"  Skipped (has abstract):  {results['skipped_has_abstract']} files")
    report.append(f"  API calls made:          {results['api_calls']}")
    report.append("")
    report.append(f"  Success:                 {results['success']} abstracts retrieved")
    report.append(f"  API errors:              {results['api_errors']}")
    report.append(f"  Validation failures:     {results['validation_failures']}")

    if 'cv_writeback_success' in results:
        report.append("")
        report.append(f"  CV.numbers write-back:   {results['cv_writeback_success']} successful, {results['cv_writeback_failed']} failed")

    if results['success_files']:
        report.append("\nNew abstracts added to:")
        for filename in results['success_files'][:10]:  # Show first 10
            report.append(f"  {filename}")
        if len(results['success_files']) > 10:
            report.append(f"  ... ({len(results['success_files']) - 10} more)")

    if results['failed_files']:
        report.append("\nFailed retrievals:")
        for filename, error in results['failed_files']:
            report.append(f"  {filename} - {error}")

    return '\n'.join(report)


# ============================================================================
# Phase 4: User Story 2 - CV.numbers Write-back (T020-T024)
# ============================================================================

def match_publication_to_cv_row(publication, cv_rows):
    """
    Match publication file to CV.numbers row (T020).

    Args:
        publication: Publication dict from scan_publications()
        cv_rows: List of CV.numbers row dicts from load_cv_numbers()

    Returns:
        dict or None: Matched CV row, or None if no match
    """
    pub_doi = publication.get('doi')
    pub_title = publication.get('title', '')
    pub_year = str(publication.get('year', ''))

    # Normalize publication data
    if pub_doi:
        pub_doi_normalized = pub_doi.lower().replace('https://doi.org/', '').strip()
    else:
        pub_doi_normalized = None

    pub_title_normalized = re.sub(r'\s+', ' ', pub_title.lower().strip())

    # Try DOI match first (primary)
    if pub_doi_normalized:
        for row in cv_rows:
            if row['doi'] and row['doi'] == pub_doi_normalized:
                return row

    # Fallback to title+year match
    for row in cv_rows:
        if row['title'] == pub_title_normalized and row['year'] == pub_year:
            return row

    return None


def check_cv_abstract_exists(cv_row):
    """
    Check if CV.numbers row already has an abstract (T021).

    Args:
        cv_row: CV.numbers row dict

    Returns:
        bool: True if abstract exists and non-empty
    """
    abstract = cv_row.get('abstract')
    return abstract is not None and str(abstract).strip() != ''


def write_abstract_to_cv(cv_sheet, cv_row, abstract_text):
    """
    Update CV.numbers row with abstract text (T022).

    Args:
        cv_sheet: numbers-parser Sheet object
        cv_row: Matched CV.numbers row dict with row_index
        abstract_text: Abstract text to write

    Returns:
        tuple: (success: bool, error: str or None)
    """
    try:
        # Find Abstract column index
        table = cv_sheet.tables[0]
        headers = []
        for i in range(table.num_cols):
            cell = table.cell(0, i)
            headers.append(cell.value if cell.value else '')

        abstract_col = headers.index('Abstract')
        row_idx = cv_row['row_index']

        # Write abstract to cell
        table.write(row_idx, abstract_col, abstract_text)

        return True, None

    except Exception as e:
        return False, f"CV write error: {e}"


def save_cv_numbers(doc, numbers_file_path):
    """
    Save updated CV.numbers file to disk (T023).

    Args:
        doc: numbers-parser Document object
        numbers_file_path: Path to CV.numbers file

    Returns:
        tuple: (success: bool, error: str or None)
    """
    try:
        doc.save(numbers_file_path)
        return True, None
    except Exception as e:
        return False, f"Failed to save CV.numbers: {e}"


def main():
    """Main entry point."""
    args = parse_arguments()

    # Validate inputs
    success, error = validate_inputs(args)
    if not success:
        print(error, file=sys.stderr)
        sys.exit(1)

    # Load API key (T004)
    print("Loading API credentials from .env...")
    api_key, masked_key, error = load_api_key()
    if error:
        print(error, file=sys.stderr)
        sys.exit(1)
    print(f"API key found: {masked_key}")

    # Scan publications (T005)
    print(f"\nScanning {args.publications_dir} for files missing abstracts...")
    publications = scan_publications(args.publications_dir)
    missing_abstracts = [p for p in publications if not p['has_abstract']]
    print(f"Found {len(publications)} publication files, {len(missing_abstracts)} missing abstracts")

    # Load CV.numbers (T006) - only if not skipping writeback
    cv_rows = None
    cv_sheet = None
    cv_doc = None
    if not args.skip_cv_writeback:
        cv_rows, cv_sheet, cv_doc, error = load_cv_numbers(args.numbers_file)
        if error:
            print(error, file=sys.stderr)
            sys.exit(1)
        if args.verbose:
            print(f"Found {len(cv_rows)} CV.numbers rows")

    # Check if all publications already have abstracts (T026 from Phase 5)
    if len(missing_abstracts) == 0:
        print("\nAll publications already have abstracts. Nothing to do.")
        sys.exit(0)

    # Dry-run mode (T025 from Phase 5)
    if args.dry_run:
        print("\nDRY RUN - No API calls will be made, no files will be modified")
        print("\nWould query Scholar API for:")

        # Apply --max-publications limit if specified
        publications_to_list = missing_abstracts
        if args.max_publications:
            publications_to_list = missing_abstracts[:args.max_publications]

        for i, pub in enumerate(publications_to_list, 1):
            doi_display = f"DOI: {pub['doi']}" if pub['doi'] else "no DOI"
            title_display = pub['title'][:50] + "..." if len(pub['title']) > 50 else pub['title']
            print(f"  {i}. {pub['filename']} - \"{title_display}\" ({pub['year']}) [{doi_display}]")

        # Calculate estimated time (1 second per publication + retries)
        estimated_time = len(publications_to_list) * 1.5  # 1s rate limit + ~0.5s for API call
        print(f"\nSummary:")
        print(f"  Would query:    {len(publications_to_list)} publications")
        print(f"  Estimated time: ~{int(estimated_time)} seconds (with 1s rate limit + retries)")
        print(f"  Would update:   _publications/ markdown files")
        if not args.skip_cv_writeback:
            print(f"  Would update:   CV.numbers Abstract column (matched rows)")
        sys.exit(0)

    # Main processing loop (T017)
    print(f"\nRetrieving abstracts from Scholar API (this may take a few minutes)...")

    # Track results
    results = {
        'total_scanned': len(publications),
        'skipped_has_abstract': len(publications) - len(missing_abstracts),
        'api_calls': 0,
        'success': 0,
        'api_errors': 0,
        'validation_failures': 0,
        'cv_writeback_success': 0,
        'cv_writeback_failed': 0,
        'success_files': [],
        'failed_files': []
    }

    # Apply --max-publications limit if specified
    publications_to_process = missing_abstracts
    if args.max_publications:
        publications_to_process = missing_abstracts[:args.max_publications]
        print(f"Limiting to first {args.max_publications} publications (--max-publications flag)\n")

    # Process each publication
    for pub in publications_to_process:
        filename = pub['filename']
        doi = pub['doi']
        title = pub['title']
        year = pub['year']

        # Display progress
        doi_display = f"DOI: {doi}" if doi else "no DOI, using title+year"
        print(f"\nProcessing: {filename} [{doi_display}]")

        # Build API request
        if doi:
            params = build_api_request_doi(doi)
        else:
            params = build_api_request_title_year(title, year)

        if args.verbose:
            query_type = "DOI search" if doi else "title+year search"
            print(f"  Title: {title[:60]}...")
            print(f"  Year: {year}")
            print(f"  DOI: {doi if doi else 'none'}")
            print(f"  Author: {pub.get('author', 'unknown')}")
            print(f"  Has abstract: No")
            print(f"  API Query: {query_type}")
            print(f"    keywords: {params['keywords'][:50]}...")

        # Query API (T010)
        results['api_calls'] += 1
        response_json, error = query_scholar_api(api_key, params, args.verbose)

        if error:
            print(f"  ✗ {error}")
            results['api_errors'] += 1
            results['failed_files'].append((filename, error))
            time.sleep(1.0)  # Rate limit (T016)
            continue

        # Parse response (T011)
        abstract, error = parse_api_response(response_json, args.verbose)

        # Handle multiple results - resolve ambiguous match (T013)
        if not abstract and response_json.get('total_num_results', 0) > 1:
            if args.verbose:
                print(f"  Multiple results ({response_json['total_num_results']}), resolving...")
            pub_surnames = extract_surnames(pub['author'], pub.get('author_tags', []))
            abstract = resolve_ambiguous_results(response_json, year, pub_surnames, args.verbose)
            if not abstract:
                error = "No matching result found"

        if error:
            print(f"  ✗ {error}")
            if "no results" in error.lower():
                results['api_errors'] += 1
            else:
                results['validation_failures'] += 1
            results['failed_files'].append((filename, error))
            time.sleep(1.0)  # Rate limit (T016)
            continue

        # Success - abstract retrieved
        print(f"  ✓ Abstract retrieved ({len(abstract)} characters)")
        results['success'] += 1

        # Insert abstract into file (T014)
        updated_body = insert_abstract(pub['body_content'], abstract)

        # Update file (T015)
        success, error = update_publication_file(pub['file_path'], updated_body)
        if not success:
            print(f"  ✗ File update failed: {error}")
            results['failed_files'].append((filename, f"File write error: {error}"))
        else:
            print(f"  ✓ File updated")
            results['success_files'].append(filename)

            # CV.numbers write-back (T024) - only if file update succeeded
            if not args.skip_cv_writeback and cv_rows is not None:
                # Match publication to CV row (T020)
                cv_row = match_publication_to_cv_row(pub, cv_rows)

                if cv_row:
                    # Check if abstract already exists (T021)
                    if check_cv_abstract_exists(cv_row):
                        if args.verbose:
                            print(f"  ⚠ CV.numbers already has abstract, skipping write-back")
                    else:
                        # Write abstract to CV (T022)
                        success, error = write_abstract_to_cv(cv_sheet, cv_row, abstract)
                        if success:
                            print(f"  ✓ CV.numbers updated")
                            results['cv_writeback_success'] += 1
                        else:
                            print(f"  ⚠ CV.numbers write failed: {error}")
                            results['cv_writeback_failed'] += 1
                else:
                    if args.verbose:
                        print(f"  ⚠ CV.numbers match not found")
                    results['cv_writeback_failed'] += 1

        # Rate limiting (T016)
        time.sleep(1.0)

    # Save CV.numbers file if any updates were made (T023)
    if not args.skip_cv_writeback and cv_doc is not None and results['cv_writeback_success'] > 0:
        if args.verbose:
            print("\nSaving CV.numbers file...")
        success, error = save_cv_numbers(cv_doc, args.numbers_file)
        if not success:
            print(f"Warning: {error}", file=sys.stderr)

    # Print summary report (T018)
    print(format_summary_report(results))

    # Exit code logic (T019)
    if results['api_errors'] > 0 or results['validation_failures'] > 0:
        sys.exit(2)  # Partial success
    else:
        sys.exit(0)  # Success


if __name__ == '__main__':
    main()
