#!/usr/bin/env python3
"""Import and rename downloaded PDFs from Downloads folder.

This script helps match PDFs downloaded from publishers to their canonical IDs,
then renames and moves them to the website's PDF directory.

Usage:
    python import_downloaded_pdfs.py [--dry-run] [--downloads-dir ~/Downloads]
"""

import argparse
import frontmatter
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Expected publications needing PDFs (2022+)
EXPECTED_PUBS = {
    'Caylor2026_2244': '10.1016/j.jhydrol.2026.134985',
    'Caylor2025_3067': '10.1016/j.isprsjprs.2025.01.015',
    'Caylor2025_3629': '10.1029/2025AV001726',
    'Caylor2025_4743': '10.1029/2024EF005799',
    'Mayes2025_1367': '10.1029/2024WR038287',
    'Morgan2025_5312': '10.1038/s41559‑025‑02810‑8',
    'Morgan2025_7028': '10.1029/2024GL111403',
    'Boser2024_1590': '10.1038/s41467-024-46031-2',
    'Caylor2024_1816': '10.1016/j.rse.2024.114056',
    'Caylor2024_2494': '10.1145/3674829.3675063',
    'Caylor2024_2958': '10.1038/s44221-024-00221-w',
    'Caylor2024_3604': '10.1002/eco.2729',
    'Caylor2024_7656': '10.1038/s41586-024-07702-8',
    'Caylor2023_4247': '10.1088/2752-664X/acb9a0',
    'Caylor2023_6934': '10.1016/j.agrformet.2023.109560',
    'Caylor2023_8656': '10.1016/j.agsy.2022.103574',
    'Caylor2023_9423': '10.1029/2023JG007451',
    'Estes2023_1099': '10.1088/2634-4505/ad04e4',
    'Krell2023_2456': '10.1016/j.fcr.2023.109014',
    'Morgan2023_6264': '10.1029/2023WR035251',
    'Caylor2022_6128': '10.1002/rra.4076',
    'Estes2022_7895': '10.3389/frai.2021.744863',
    'Good2022_1252': '10.1016/j.agrformet.2021.108790',
    'Krell2022_3948': '10.1016/j.crm.2022.100396',
    'Morgan2026_4660': '10.1016/j.agrformet.2025.110929',
}


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Import and rename downloaded PDFs from Downloads folder',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--downloads-dir',
        default=str(Path.home() / 'Downloads'),
        help='Directory to scan for downloaded PDFs (default: ~/Downloads)'
    )

    parser.add_argument(
        '--pdf-dir',
        default='assets/pdfs/publications',
        help='Target directory for renamed PDFs (default: assets/pdfs/publications)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Prompt for confirmation before each move'
    )

    return parser.parse_args()


def find_pdfs_in_downloads(downloads_dir: Path, max_age_days: int = 7) -> List[Path]:
    """Find recently downloaded PDFs.

    Args:
        downloads_dir: Directory to scan
        max_age_days: Only consider PDFs modified in last N days

    Returns:
        List of PDF file paths
    """
    pdfs = []
    cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

    for pdf_file in downloads_dir.glob('*.pdf'):
        # Check if recently modified
        if pdf_file.stat().st_mtime >= cutoff_time:
            pdfs.append(pdf_file)

    return sorted(pdfs, key=lambda p: p.stat().st_mtime, reverse=True)


def extract_doi_from_filename(filename: str) -> Optional[str]:
    """Try to extract DOI from filename patterns.

    Common patterns:
    - 10.1016-j.rse.2024.114056.pdf
    - s41467-024-46031-2.pdf (Nature format)
    """
    # Direct DOI pattern
    match = re.search(r'10\.\d{4,}[/-][^\s]+', filename)
    if match:
        doi = match.group(0).replace('-', '/')
        # Remove file extension if captured
        doi = re.sub(r'\.pdf$', '', doi, flags=re.IGNORECASE)
        return doi

    # Nature format (s41467-024-46031-2)
    match = re.search(r's\d{5}-\d{3}-\d{5}-\d', filename)
    if match:
        return f"10.1038/{match.group(0)}"

    return None


def match_pdf_to_canonical_id(pdf_path: Path, expected_pubs: Dict[str, str]) -> Optional[str]:
    """Try to match a PDF to a canonical ID.

    Strategies:
    1. Check if filename contains canonical ID
    2. Extract DOI from filename and match
    3. Return None if no match (will require manual matching)
    """
    filename = pdf_path.name

    # Strategy 1: Filename contains canonical ID
    for canonical_id in expected_pubs.keys():
        if canonical_id in filename:
            return canonical_id

    # Strategy 2: Extract DOI from filename
    doi = extract_doi_from_filename(filename)
    if doi:
        # Normalize DOI for comparison
        doi_normalized = doi.lower().replace('/', '.').replace('-', '.')

        for canonical_id, expected_doi in expected_pubs.items():
            expected_normalized = expected_doi.lower().replace('/', '.').replace('-', '.')

            if doi_normalized in expected_normalized or expected_normalized in doi_normalized:
                return canonical_id

    return None


def interactive_match(pdf_path: Path, expected_pubs: Dict[str, str]) -> Optional[str]:
    """Interactively prompt user to match PDF to canonical ID."""
    print(f"\n📄 PDF: {pdf_path.name}")
    print(f"   Size: {pdf_path.stat().st_size / 1024:.1f} KB")
    print(f"   Modified: {datetime.fromtimestamp(pdf_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')}")

    # Show available options
    print("\nAvailable publications:")
    for i, (canonical_id, doi) in enumerate(expected_pubs.items(), 1):
        print(f"  {i:2d}. {canonical_id:20s} - {doi}")

    print(f"\n  0. Skip this file")

    while True:
        try:
            choice = input("\nSelect publication number (or 0 to skip): ").strip()
            choice_num = int(choice)

            if choice_num == 0:
                return None

            if 1 <= choice_num <= len(expected_pubs):
                return list(expected_pubs.keys())[choice_num - 1]

            print("Invalid choice. Please try again.")
        except (ValueError, KeyboardInterrupt):
            print("\nSkipping...")
            return None


def import_and_rename_pdfs(args):
    """Main logic to import and rename PDFs."""
    downloads_dir = Path(args.downloads_dir).expanduser()
    pdf_dir = Path(args.pdf_dir)

    if not downloads_dir.exists():
        print(f"❌ Downloads directory not found: {downloads_dir}")
        return 1

    if not pdf_dir.exists():
        print(f"❌ PDF directory not found: {pdf_dir}")
        return 1

    # Find recent PDFs
    print(f"🔍 Scanning for PDFs in {downloads_dir}")
    recent_pdfs = find_pdfs_in_downloads(downloads_dir)

    if not recent_pdfs:
        print("   No PDFs found from the last 7 days")
        return 0

    print(f"   Found {len(recent_pdfs)} recent PDF(s)")

    # Track what we've already matched
    matched_pubs = EXPECTED_PUBS.copy()
    imported_count = 0
    skipped_count = 0

    for pdf_path in recent_pdfs:
        # Try automatic matching first
        canonical_id = match_pdf_to_canonical_id(pdf_path, matched_pubs)

        if not canonical_id:
            # Fall back to interactive matching if enabled
            if args.interactive:
                canonical_id = interactive_match(pdf_path, matched_pubs)
            else:
                print(f"\n⚠️  Could not auto-match: {pdf_path.name}")
                print(f"   Run with --interactive to manually match")
                skipped_count += 1
                continue

        if not canonical_id:
            skipped_count += 1
            continue

        # Prepare target path
        target_path = pdf_dir / f"{canonical_id}.pdf"

        print(f"\n✓ Matched: {pdf_path.name}")
        print(f"  → {canonical_id}.pdf")

        if args.dry_run:
            print(f"  [DRY RUN] Would copy to: {target_path}")
        else:
            # Copy file
            shutil.copy2(pdf_path, target_path)
            print(f"  ✓ Copied to: {target_path}")
            imported_count += 1

        # Remove from available matches
        del matched_pubs[canonical_id]

    # Summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Imported: {imported_count}")
    print(f"  Skipped:  {skipped_count}")
    print(f"  Remaining: {len(matched_pubs)} publications still need PDFs")

    if matched_pubs and not args.dry_run:
        print(f"\nStill needed:")
        for canonical_id in sorted(matched_pubs.keys()):
            print(f"  - {canonical_id}")

    return 0


def main():
    """Main entry point."""
    args = parse_arguments()
    return import_and_rename_pdfs(args)


if __name__ == '__main__':
    sys.exit(main())
