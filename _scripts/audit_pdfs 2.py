#!/usr/bin/env python3
"""PDF Archive Audit Tool - User Story 1.

This tool audits the PDF archive for completeness and optionally fetches
missing required PDFs from Scholar AI.

Usage:
    python audit_pdfs.py [OPTIONS]

Examples:
    python audit_pdfs.py
    python audit_pdfs.py --fetch-missing
    python audit_pdfs.py --output-report audit.json
    python audit_pdfs.py --dry-run --verbose
"""

import argparse
import frontmatter
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import dependencies for version logging
try:
    import pypdfium2
    import PIL
except ImportError:
    pypdfium2 = None
    PIL = None

from services.cv_parser import CVParserService
from services.scholar_fetcher import ScholarFetcher, ScholarAuthError
from services.logger import setup_logger
from models.pdf_archive import PDFArchive
from models.scholar_result import ScholarFetchResult


def parse_arguments():
    """Parse command line arguments (T015)."""
    parser = argparse.ArgumentParser(
        description='Audit PDF archive for completeness and fetch missing PDFs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Basic audit
  %(prog)s --fetch-missing                    # Audit and fetch missing PDFs
  %(prog)s --output-report audit.json         # Save JSON report
  %(prog)s --dry-run --verbose                # Preview with detailed logs

Important:
  PDF files MUST use exact canonical ID naming (case-sensitive):
    ✓ Valid:   Caylor2002_1378.pdf
    ✗ Invalid: Caylor2002_1378_draft.pdf (no suffixes allowed)
    ✗ Invalid: caylor2002_1378.pdf (wrong case)

  Files not matching exact pattern will be flagged as "ambiguous".
        """
    )

    parser.add_argument(
        '--numbers-file',
        default=os.path.expanduser('~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers'),
        help='Path to CV.numbers file (default: ~/Library/Mobile Documents/.../CV.numbers)'
    )

    parser.add_argument(
        '--pdf-dir',
        default='assets/pdfs/publications',
        help='Directory containing PDF files (default: assets/pdfs/publications)'
    )

    parser.add_argument(
        '--fetch-missing',
        action='store_true',
        help='Attempt to fetch missing required PDFs from Scholar AI'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )

    parser.add_argument(
        '--log-file',
        help='Write logs to file (in addition to console)'
    )

    parser.add_argument(
        '--output-report',
        help='Save detailed report to JSON file'
    )

    return parser.parse_args()


def validate_inputs(args, logger):
    """Validate input arguments (T016).

    Returns:
        Tuple of (valid: bool, error_message: str or None)
    """
    # Check CV.numbers file exists
    if not Path(args.numbers_file).exists():
        return False, f"Error: CV.numbers file not found: {args.numbers_file}"

    # Check PDF directory exists
    pdf_dir = Path(args.pdf_dir)
    if not pdf_dir.exists():
        return False, f"Error: PDF directory not found: {args.pdf_dir}"

    if not pdf_dir.is_dir():
        return False, f"Error: PDF path is not a directory: {args.pdf_dir}"

    # Check Scholar API key if fetch-missing flag set
    if args.fetch_missing and not os.getenv('SCHOLAR_API_KEY'):
        logger.warning(
            "SCHOLAR_API_KEY not found in environment. "
            "PDF fetching will fail. Set in .env file or environment."
        )

    return True, None


def load_publications(args, logger):
    """Load publications from existing markdown files (T017).

    This reads from _publications/ directory instead of CV.numbers since
    publications are already ingested with canonical IDs.

    Returns:
        List of Publication objects or None if error
    """
    try:
        from models.publication import Publication
        publications_dir = Path('_publications')

        if not publications_dir.exists():
            logger.error(f"Publications directory not found: {publications_dir}")
            print(f"Error: Publications directory not found: {publications_dir}")
            return None

        logger.info(f"Loading publications from {publications_dir}")

        publications = []
        for md_file in publications_dir.glob('*.md'):
            try:
                # Load frontmatter
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)

                # Extract canonical_id from filename (e.g., Caylor2002_1378.md)
                canonical_id = md_file.stem

                # Get required fields from frontmatter
                title = post.get('title', '')
                year = post.get('year', None)
                doi = post.get('doi', None)

                # Convert year to int if it's a string
                if year:
                    try:
                        year = int(year)
                    except (ValueError, TypeError):
                        year = None

                # Skip if missing required fields
                if not title or not year:
                    logger.warning(f"Skipping {canonical_id}: missing required fields")
                    continue

                # Create Publication object
                # Extract first author from canonical_id (e.g., "Caylor" from "Caylor2002_1378")
                # This satisfies the validation requirement even though we don't need author names for audit
                import re
                match = re.match(r'^([A-Za-z]+)\d{4}_\d{4}$', canonical_id)
                author_name = match.group(1) if match else "Unknown"

                publication = Publication(
                    canonical_id=canonical_id,
                    title=title,
                    authors=[author_name],  # Extracted from canonical_id
                    year=year,
                    doi=doi,
                    kind=None  # Can add if needed
                )

                publications.append(publication)

            except Exception as e:
                logger.warning(f"Error loading {md_file.name}: {e}")
                continue

        logger.info(f"Found {len(publications)} publications")
        return publications

    except Exception as e:
        logger.error(f"Failed to load publications: {e}")
        print(f"Error: Failed to load publications: {e}")
        return None


def audit_archive(publications, pdf_dir, logger):
    """Audit PDF archive and match to publications (T018).

    Returns:
        Tuple of (archive: PDFArchive, stats: ArchiveStats)
    """
    logger.info(f"Scanning PDF archive: {pdf_dir}")

    archive = PDFArchive(Path(pdf_dir))
    archive.scan()

    logger.info(f"Found {len(archive.pdf_files)} PDFs in archive")

    if archive.ambiguous_files:
        logger.warning(f"Found {len(archive.ambiguous_files)} ambiguous files (non-standard naming)")

    # Calculate statistics
    stats = archive.get_coverage_stats(publications)

    return archive, stats


def generate_audit_report(publications, archive, stats, logger):
    """Generate console audit report (T019).

    Displays:
    - Archive statistics
    - Missing required PDFs list
    - Missing optional PDFs list
    - Ambiguous files warnings
    """
    print("\n=== PDF Archive Audit ===")
    print(f"Total publications:           {stats.total_publications}")
    print(f"PDFs found:                   {stats.pdfs_found} ({stats.coverage_percentage:.1f}%)")
    print(f"PDFs missing (required):      {stats.pdfs_missing_required}")
    print(f"PDFs missing (optional):      {stats.pdfs_missing_optional}")

    if stats.ambiguous_files_detected > 0:
        print(f"Ambiguous files detected:     {stats.ambiguous_files_detected}")

    # List missing required PDFs
    if stats.pdfs_missing_required > 0:
        print("\nRequired PDFs Missing:")
        for pub in publications:
            if pub.pdf_required and not archive.find_pdf(pub.canonical_id):
                doi_str = f" - DOI: {pub.doi}" if pub.doi else ""
                print(f"  - {pub.canonical_id} ({pub.kind}){doi_str}")

    # List ambiguous files if any
    if archive.ambiguous_files:
        print("\nAmbiguous Files (warnings):")
        for ambig_file in archive.ambiguous_files[:10]:  # Show first 10
            print(f"  - {ambig_file.name}")
        if len(archive.ambiguous_files) > 10:
            print(f"  ... and {len(archive.ambiguous_files) - 10} more")


def fetch_missing_pdfs(publications, archive, args, logger):
    """Fetch missing required PDFs from Scholar AI (T020).

    Returns:
        List of ScholarFetchResult objects
    """
    # Find missing required PDFs
    missing_required = [
        pub for pub in publications
        if pub.pdf_required and not archive.find_pdf(pub.canonical_id) and pub.doi
    ]

    if not missing_required:
        logger.info("No missing required PDFs with DOIs to fetch")
        return []

    if args.dry_run:
        print(f"\n[DRY RUN] Would attempt to fetch {len(missing_required)} PDFs from Scholar AI")
        for pub in missing_required:
            print(f"  - {pub.canonical_id} (DOI: {pub.doi})")
        return []

    print(f"\nFetching missing required PDFs from Scholar AI:")

    try:
        fetcher = ScholarFetcher()
    except ScholarAuthError as e:
        logger.error(f"Scholar API authentication error: {e}")
        return []

    results = []

    for i, pub in enumerate(missing_required, 1):
        logger.info(f"Fetching {i}/{len(missing_required)}: {pub.canonical_id}")
        print(f"  ⏳ Fetching {pub.canonical_id} (DOI: {pub.doi})...")

        output_path = Path(args.pdf_dir) / f"{pub.canonical_id}.pdf"
        success, message = fetcher.fetch_pdf_by_doi(pub.doi, output_path)

        if success:
            print(f"  ✓ Successfully fetched {pub.canonical_id}")
            logger.info(f"✓ Fetched: {pub.canonical_id}")
        else:
            print(f"  ✗ Failed: {message}")
            logger.warning(f"✗ Failed {pub.canonical_id}: {message}")

        # Create result
        result = fetcher.create_fetch_result(
            pub.canonical_id,
            pub.doi,
            success,
            message,
            output_path if success else None
        )
        results.append(result)

    return results


def format_fetch_summary(fetch_results):
    """Format fetch summary report (T023)."""
    if not fetch_results:
        return

    success_count = sum(1 for r in fetch_results if r.is_success())
    fail_count = len(fetch_results) - success_count

    print(f"\nFetch Summary:")
    print(f"  Attempted:     {len(fetch_results)}")
    print(f"  Success:       {success_count}")
    print(f"  Failed:        {fail_count}")

    if fail_count > 0:
        print("\nFailed Fetches:")
        for result in fetch_results:
            if not result.is_success():
                print(f"  - {result.publication_id}: {result.error_message or result.status}")


def generate_json_report(publications, archive, stats, fetch_results, args):
    """Generate JSON report file (T021).

    Saves structured report to file specified by --output-report.
    """
    report = {
        'timestamp': datetime.now().isoformat(),
        'cv_numbers_file': args.numbers_file,
        'pdf_directory': args.pdf_dir,
        'statistics': {
            'total_publications': stats.total_publications,
            'pdfs_found': stats.pdfs_found,
            'pdfs_missing_required': stats.pdfs_missing_required,
            'pdfs_missing_optional': stats.pdfs_missing_optional,
            'coverage_percentage': round(stats.coverage_percentage, 1),
            'ambiguous_files': stats.ambiguous_files_detected
        },
        'missing_required': [],
        'missing_optional': [],
        'ambiguous_files': [str(f.name) for f in archive.ambiguous_files],
        'fetch_results': []
    }

    # Add missing publications
    for pub in publications:
        if not archive.find_pdf(pub.canonical_id):
            pub_info = {
                'canonical_id': pub.canonical_id,
                'title': pub.title,
                'year': pub.year,
                'kind': pub.kind,
                'doi': pub.doi
            }

            if pub.pdf_required:
                report['missing_required'].append(pub_info)
            else:
                report['missing_optional'].append(pub_info)

    # Add fetch results
    if fetch_results:
        report['fetch_results'] = [r.to_dict() for r in fetch_results]

    # Write to file
    output_path = Path(args.output_report)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ JSON report saved to: {args.output_report}")


def main():
    """Main orchestration (T022)."""
    args = parse_arguments()

    # Setup logging
    logger = setup_logger(
        'audit_pdfs',
        verbose=args.verbose,
        log_file=args.log_file
    )

    logger.info("Starting PDF archive audit")

    # Log dependency versions (T052)
    if pypdfium2:
        logger.debug(f"pypdfium2 version: {pypdfium2.V_PYPDFIUM2}")
    if PIL:
        logger.debug(f"Pillow version: {PIL.__version__}")

    # Dry run notification
    if args.dry_run:
        print("=== DRY RUN MODE ===")
        print("No files will be written\n")

    # Validate inputs
    valid, error = validate_inputs(args, logger)
    if not valid:
        logger.error(error)
        print(error)
        return 1

    # Load publications
    publications = load_publications(args, logger)
    if publications is None:
        return 1

    # Audit archive
    archive, stats = audit_archive(publications, args.pdf_dir, logger)

    # Generate console report
    generate_audit_report(publications, archive, stats, logger)

    # Fetch missing PDFs if requested
    fetch_results = []
    if args.fetch_missing:
        fetch_results = fetch_missing_pdfs(publications, archive, args, logger)
        format_fetch_summary(fetch_results)

    # Generate JSON report if requested
    if args.output_report and not args.dry_run:
        generate_json_report(publications, archive, stats, fetch_results, args)

    # Determine exit code
    if stats.pdfs_missing_required > 0:
        # Partial success - some required PDFs missing
        if fetch_results:
            # If we fetched, check if any are still missing
            still_missing = stats.pdfs_missing_required - sum(1 for r in fetch_results if r.is_success())
            if still_missing > 0:
                logger.info("Audit complete with missing required PDFs")
                print("\n⚠ Audit complete (partial - some required PDFs still missing)")
                return 2
        else:
            logger.info("Audit complete with missing required PDFs")
            print("\n⚠ Audit complete (partial - some required PDFs missing)")
            return 2

    logger.info("Audit complete - all required PDFs present")
    print("\n✓ Audit complete")
    return 0


if __name__ == '__main__':
    sys.exit(main())
