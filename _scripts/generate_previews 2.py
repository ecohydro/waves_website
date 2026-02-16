#!/usr/bin/env python3
"""Preview Image Generation Tool - User Story 2.

This tool generates preview images (first page of PDF) for publications.

Usage:
    python generate_previews.py [PUBLICATION_IDS...] [OPTIONS]

Examples:
    python generate_previews.py                        # Generate all missing
    python generate_previews.py Caylor2022_5678       # Generate for specific ID
    python generate_previews.py --force Caylor2002_1378  # Force regenerate
    python generate_previews.py --dry-run --verbose    # Preview changes
"""

import argparse
import frontmatter
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
from services.pdf_processor import PDFProcessor, PDFProcessorError
from services.image_generator import ImageGenerator, ImageGeneratorError
from services.logger import setup_logger
from models.pdf_archive import PDFArchive
from models.image_log import ImageGenerationLog


def parse_arguments():
    """Parse command line arguments (T029)."""
    parser = argparse.ArgumentParser(
        description='Generate preview images (first page) from publication PDFs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                               # Generate all missing preview images
  %(prog)s Caylor2022_5678               # Generate for specific publication
  %(prog)s --force Caylor2002_1378      # Force regenerate existing image
  %(prog)s --dry-run                     # Preview without generating

Important:
  PDF files MUST use exact canonical ID naming (case-sensitive):
    ✓ Valid:   Caylor2002_1378.pdf
    ✗ Invalid: Caylor2002_1378_draft.pdf (no suffixes allowed)
        """
    )

    parser.add_argument(
        'publication_ids',
        nargs='*',
        help='Publication IDs to process (if empty, processes all missing)'
    )

    parser.add_argument(
        '--numbers-file',
        default=os.path.expanduser('~/Library/Mobile Documents/com~apple~Numbers/Documents/CV.numbers'),
        help='Path to CV.numbers file'
    )

    parser.add_argument(
        '--pdf-dir',
        default='assets/pdfs/publications',
        help='Directory containing PDF files'
    )

    parser.add_argument(
        '--output-dir',
        default='assets/images/publications',
        help='Directory for generated images'
    )

    parser.add_argument(
        '--height',
        type=int,
        default=640,
        help='Target height in pixels (default: 640)'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Regenerate images even if they already exist'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without generating images'
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

    return parser.parse_args()


def validate_inputs(args, logger):
    """Validate input arguments (T030).

    Returns:
        Tuple of (valid: bool, error_message: str or None)
    """
    # Check directories exist
    pdf_dir = Path(args.pdf_dir)
    if not pdf_dir.exists():
        return False, f"Error: PDF directory not found: {args.pdf_dir}"

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        return False, f"Error: Output directory not found: {args.output_dir}"

    # Check output directory is writable
    if not os.access(output_dir, os.W_OK):
        return False, f"Error: Output directory not writable: {args.output_dir}"

    return True, None


def check_existing_images(publications, output_dir, force=False):
    """Check which publications already have preview images (T031).

    Returns:
        List of publications needing image generation
    """
    needs_generation = []

    for pub in publications:
        image_path = Path(output_dir) / f"{pub.canonical_id}.png"

        if not image_path.exists() or force:
            needs_generation.append(pub)

    return needs_generation


def generate_preview_image(pub, pdf_dir, output_dir, target_height, logger):
    """Generate preview image for a single publication (T032).

    Returns:
        ImageGenerationLog object
    """
    timestamp = datetime.now()

    try:
        # Find PDF
        pdf_path = Path(pdf_dir) / f"{pub.canonical_id}.pdf"

        if not pdf_path.exists():
            logger.warning(f"PDF not found: {pub.canonical_id}")
            return ImageGenerationLog(
                timestamp=timestamp,
                operation='preview',
                publication_id=pub.canonical_id,
                status='skipped',
                message='PDF not found'
            )

        # Render first page
        logger.debug(f"Rendering first page: {pub.canonical_id}")
        image = PDFProcessor.render_page(pdf_path, page_num=0, target_height=target_height)

        # Save as PNG
        output_path = Path(output_dir) / f"{pub.canonical_id}.png"
        logger.debug(f"Saving preview image: {output_path}")
        ImageGenerator.save_png(image, output_path)

        # Get file size
        file_size = ImageGenerator.get_file_size_kb(output_path)

        logger.info(f"✓ Generated {pub.canonical_id}.png ({image.width}x{image.height}, {file_size} KB)")

        return ImageGenerationLog(
            timestamp=timestamp,
            operation='preview',
            publication_id=pub.canonical_id,
            status='success',
            output_path=output_path
        )

    except PDFProcessorError as e:
        logger.error(f"PDF processing error for {pub.canonical_id}: {e}")
        return ImageGenerationLog(
            timestamp=timestamp,
            operation='preview',
            publication_id=pub.canonical_id,
            status='error',
            message=str(e)
        )

    except ImageGeneratorError as e:
        logger.error(f"Image generation error for {pub.canonical_id}: {e}")
        return ImageGenerationLog(
            timestamp=timestamp,
            operation='preview',
            publication_id=pub.canonical_id,
            status='error',
            message=str(e)
        )

    except Exception as e:
        logger.error(f"Unexpected error for {pub.canonical_id}: {e}")
        return ImageGenerationLog(
            timestamp=timestamp,
            operation='preview',
            publication_id=pub.canonical_id,
            status='error',
            message=f"Unexpected error: {str(e)}"
        )


def batch_generate(publications, args, logger):
    """Process all publications needing preview images (T033).

    Returns:
        List of ImageGenerationLog objects
    """
    logs = []
    total = len(publications)

    for i, pub in enumerate(publications, 1):
        # Progress indicator every 10 items (T037)
        if i % 10 == 0 or i == total:
            logger.info(f"Progress: {i}/{total} publications processed")

        print(f"  ⏳ Processing {pub.canonical_id}...")

        if args.dry_run:
            print(f"  [DRY RUN] Would generate preview for {pub.canonical_id}")
            continue

        log = generate_preview_image(pub, args.pdf_dir, args.output_dir, args.height, logger)
        logs.append(log)

        # Display result
        if log.status == 'success':
            print(f"  ✓ Generated {pub.canonical_id}.png")
        elif log.status == 'skipped':
            print(f"  ⚠ Skipped: {log.message}")
        else:
            print(f"  ✗ Error: {log.message}")

    return logs


def single_generate(publication_ids, all_publications, args, logger):
    """Process specific publication IDs (T034).

    Returns:
        List of ImageGenerationLog objects
    """
    logs = []

    # Find publications by ID
    pub_map = {pub.canonical_id: pub for pub in all_publications}

    for pub_id in publication_ids:
        if pub_id not in pub_map:
            logger.warning(f"Publication not found: {pub_id}")
            print(f"  ✗ Publication not found: {pub_id}")
            continue

        pub = pub_map[pub_id]

        # Check if image already exists (unless force)
        image_path = Path(args.output_dir) / f"{pub.canonical_id}.png"
        if image_path.exists() and not args.force:
            logger.info(f"Image already exists: {pub_id} (use --force to regenerate)")
            print(f"  ⚠ Image already exists: {pub_id} (use --force to regenerate)")
            continue

        print(f"  ⏳ Processing {pub.canonical_id}...")

        if args.dry_run:
            print(f"  [DRY RUN] Would generate preview for {pub.canonical_id}")
            continue

        log = generate_preview_image(pub, args.pdf_dir, args.output_dir, args.height, logger)
        logs.append(log)

        # Display result
        if log.status == 'success':
            print(f"  ✓ Generated {pub.canonical_id}.png")
        elif log.status == 'skipped':
            print(f"  ⚠ Skipped: {log.message}")
        else:
            print(f"  ✗ Error: {log.message}")

    return logs


def format_summary_report(logs, total_scanned, already_existed):
    """Format summary report (T035)."""
    if not logs:
        return

    success_count = sum(1 for log in logs if log.status == 'success')
    skipped_count = sum(1 for log in logs if log.status == 'skipped')
    error_count = sum(1 for log in logs if log.status == 'error')

    print(f"\nSummary:")
    print(f"  Total scanned:     {total_scanned}")
    print(f"  Already existed:   {already_existed}")
    print(f"  Generated:         {success_count}")
    print(f"  Skipped (no PDF):  {skipped_count}")
    print(f"  Errors:            {error_count}")


def main():
    """Main orchestration (T036)."""
    args = parse_arguments()

    # Setup logging
    logger = setup_logger(
        'generate_previews',
        verbose=args.verbose,
        log_file=args.log_file
    )

    logger.info("Starting preview image generation")

    # Log dependency versions (T052)
    if pypdfium2:
        logger.debug(f"pypdfium2 version: {pypdfium2.V_PYPDFIUM2}")
    if PIL:
        logger.debug(f"Pillow version: {PIL.__version__}")

    # Dry run notification
    if args.dry_run:
        print("=== DRY RUN MODE ===")
        print("No images will be generated\n")

    # Validate inputs
    valid, error = validate_inputs(args, logger)
    if not valid:
        logger.error(error)
        print(error)
        return 1

    # Load publications from existing markdown files
    try:
        publications_dir = Path('_publications')

        if not publications_dir.exists():
            logger.error(f"Publications directory not found: {publications_dir}")
            print(f"Error: Publications directory not found: {publications_dir}")
            return 1

        logger.info(f"Loading publications from {publications_dir}")

        all_publications = []
        for md_file in publications_dir.glob('*.md'):
            try:
                # Load frontmatter
                with open(md_file, 'r', encoding='utf-8') as f:
                    post = frontmatter.load(f)

                # Extract canonical_id from filename
                canonical_id = md_file.stem

                # Get fields from frontmatter
                title = post.get('title', '')
                year = post.get('year', None)
                doi = post.get('doi', None)

                # Convert year to int if needed
                if year:
                    try:
                        year = int(year)
                    except (ValueError, TypeError):
                        year = None

                # Skip if missing required fields
                if not title or not year:
                    continue

                # Create Publication object
                # Extract first author from canonical_id
                import re
                from models.publication import Publication
                match = re.match(r'^([A-Za-z]+)\d{4}_\d{4}$', canonical_id)
                author_name = match.group(1) if match else "Unknown"

                publication = Publication(
                    canonical_id=canonical_id,
                    title=title,
                    authors=[author_name],
                    year=year,
                    doi=doi,
                    kind=None
                )

                all_publications.append(publication)

            except Exception as e:
                logger.warning(f"Error loading {md_file.name}: {e}")
                continue

        logger.info(f"Found {len(all_publications)} publications")

    except Exception as e:
        logger.error(f"Failed to load publications: {e}")
        print(f"Error: Failed to load publications: {e}")
        return 1

    print("\n=== Preview Image Generation ===")

    # Determine mode: batch or specific publications
    if args.publication_ids:
        # Single/multi mode - process specific IDs
        print(f"Processing {len(args.publication_ids)} specific publication(s)\n")
        logs = single_generate(args.publication_ids, all_publications, args, logger)
        total_scanned = len(all_publications)
        already_existed = 0  # Not tracked in single mode

    else:
        # Batch mode - process all missing
        print(f"Scanning {len(all_publications)} publications\n")

        # Check which need generation
        needs_generation = check_existing_images(
            all_publications,
            args.output_dir,
            force=args.force
        )

        already_existed = len(all_publications) - len(needs_generation)

        if needs_generation:
            print(f"  Missing: {len(needs_generation)} publications need preview images")
            if already_existed > 0:
                print(f"  Existing: {already_existed} publications already have preview images")
            print("\nGenerating preview images:")

            logs = batch_generate(needs_generation, args, logger)
        else:
            print("  ✓ All publications already have preview images")
            print("\n✓ Preview generation complete (nothing to do)")
            return 0

        total_scanned = len(all_publications)

    # Display summary
    if not args.dry_run:
        format_summary_report(logs, total_scanned, already_existed)

    # Determine exit code
    if logs:
        error_count = sum(1 for log in logs if log.status == 'error')
        if error_count > 0:
            logger.info("Preview generation complete with errors")
            print("\n⚠ Preview generation complete (partial - some errors occurred)")
            return 2

    logger.info("Preview generation complete")
    print("\n✓ Preview generation complete")
    return 0


if __name__ == '__main__':
    sys.exit(main())
