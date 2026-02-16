#!/usr/bin/env python3
"""Feature Image Extraction Tool - User Story 3.

This tool extracts feature images (specific pages/figures) from publication PDFs.

Usage:
    python extract_feature.py PUBLICATION_ID --page PAGE [OPTIONS]

Examples:
    python extract_feature.py Caylor2022_5678 --page 3
    python extract_feature.py Caylor2022_5678 --page 3 --crop "100,200,800,600"
    python extract_feature.py Caylor2002_1378 --page 5 --force
    python extract_feature.py Caylor2022_5678 --page 3 --dry-run
"""

import argparse
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

from services.pdf_processor import PDFProcessor, PDFProcessorError
from services.image_generator import ImageGenerator, ImageGeneratorError
from services.logger import setup_logger
from models.image_log import ImageGenerationLog


def parse_arguments():
    """Parse command line arguments (T039)."""
    parser = argparse.ArgumentParser(
        description='Extract feature images (specific figures) from publication PDFs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s Caylor2022_5678 --page 3                           # Extract page 3
  %(prog)s Caylor2022_5678 --page 3 --crop "100,200,800,600" # Extract with crop
  %(prog)s Caylor2002_1378 --page 5 --force                  # Force overwrite
  %(prog)s Caylor2022_5678 --page 3 --dry-run                # Preview only

Important:
  PDF files MUST use exact canonical ID naming (case-sensitive):
    ✓ Valid:   Caylor2002_1378.pdf
    ✗ Invalid: Caylor2002_1378_draft.pdf (no suffixes allowed)
        """
    )

    parser.add_argument(
        'publication_id',
        help='Publication canonical ID (e.g., Caylor2022_5678)'
    )

    parser.add_argument(
        '--page',
        type=int,
        required=True,
        help='Page number to extract (1-indexed, required)'
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
        '--crop',
        help='Crop coordinates as "x,y,width,height" in pixels'
    )

    parser.add_argument(
        '--max-dimension',
        type=int,
        default=640,
        help='Maximum dimension (width or height) in pixels (default: 640)'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing feature image without confirmation'
    )

    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompt if feature image exists'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without generating image'
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


def parse_crop_coordinates(crop_str):
    """Parse crop coordinates string (T041).

    Args:
        crop_str: String in format "x,y,width,height"

    Returns:
        Tuple of (x, y, width, height) or None if invalid

    Raises:
        ValueError: If format is invalid
    """
    if not crop_str:
        return None

    try:
        parts = crop_str.split(',')
        if len(parts) != 4:
            raise ValueError("Crop must have exactly 4 values: x,y,width,height")

        x, y, width, height = [int(p.strip()) for p in parts]

        if x < 0 or y < 0 or width <= 0 or height <= 0:
            raise ValueError("Crop coordinates must be non-negative, width and height must be positive")

        return (x, y, width, height)

    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid crop format: {crop_str}. Expected: x,y,width,height")


def validate_inputs(args, logger):
    """Validate input arguments (T040).

    Returns:
        Tuple of (valid: bool, error_message: str or None)
    """
    # Check PDF exists
    pdf_path = Path(args.pdf_dir) / f"{args.publication_id}.pdf"
    if not pdf_path.exists():
        return False, f"Error: PDF not found: {pdf_path}"

    # Validate page number is positive
    if args.page < 1:
        return False, f"Error: Page number must be >= 1 (got {args.page})"

    # Check page number is within PDF bounds
    try:
        page_count = PDFProcessor.get_page_count(pdf_path)
        if args.page > page_count:
            return False, f"Error: Page {args.page} is out of range (PDF has {page_count} pages)"

    except PDFProcessorError as e:
        return False, f"Error: Cannot read PDF: {e}"

    # Validate crop coordinates if provided
    if args.crop:
        try:
            parse_crop_coordinates(args.crop)
        except ValueError as e:
            return False, f"Error: {e}"

    # Check output directory exists and is writable
    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        return False, f"Error: Output directory not found: {args.output_dir}"

    if not os.access(output_dir, os.W_OK):
        return False, f"Error: Output directory not writable: {args.output_dir}"

    return True, None


def check_overwrite_protection(output_path, force, no_confirm):
    """Check if we should proceed with overwrite (T042).

    Returns:
        Tuple of (proceed: bool, cancelled_by_user: bool)
    """
    if not output_path.exists():
        # No existing image, proceed
        return True, False

    # Image exists - check flags
    if force or no_confirm:
        # Skip confirmation, proceed
        return True, False

    # Ask user for confirmation
    print(f"\n⚠️  Feature image already exists:")
    print(f"    {output_path}")
    print()

    response = input("Overwrite existing image? [y/N]: ").strip().lower()

    if response in ['y', 'yes']:
        return True, False
    else:
        return False, True


def calculate_resize_dimensions(original_width, original_height, max_dimension):
    """Calculate new dimensions for max_dimension constraint (T044).

    Returns:
        Tuple of (new_width, new_height)
    """
    return ImageGenerator.calculate_resize_dimensions(
        original_width,
        original_height,
        max_dimension
    )


def extract_feature_image(args, logger):
    """Extract feature image from PDF (T043).

    Returns:
        ImageGenerationLog object
    """
    timestamp = datetime.now()
    pub_id = args.publication_id

    try:
        # Load PDF and render specified page (convert to 0-indexed)
        pdf_path = Path(args.pdf_dir) / f"{pub_id}.pdf"
        page_index = args.page - 1  # Convert from 1-indexed to 0-indexed

        logger.debug(f"Rendering page {args.page} from {pdf_path}")
        print(f"  ⏳ Loading PDF...")
        page_count = PDFProcessor.get_page_count(pdf_path)
        print(f"  ✓ PDF loaded ({page_count} pages)")

        print(f"  ⏳ Rendering page {args.page}...")
        image = PDFProcessor.render_page(pdf_path, page_num=page_index)
        original_size = image.size
        print(f"  ✓ Rendered ({original_size[0]}x{original_size[1]} original)")

        # Apply crop if specified
        if args.crop:
            x, y, width, height = parse_crop_coordinates(args.crop)
            print(f"  ⏳ Cropping to specified region...")

            # Validate crop bounds
            if x + width > image.width or y + height > image.height:
                raise ImageGeneratorError(
                    f"Crop region ({x},{y},{width},{height}) extends beyond "
                    f"image bounds ({image.width}x{image.height})"
                )

            image = ImageGenerator.crop_region(image, x, y, width, height)
            print(f"  ✓ Cropped ({image.width}x{image.height})")

        # Resize to max dimension
        print(f"  ⏳ Resizing to max dimension {args.max_dimension}px...")
        image = ImageGenerator.resize_to_max_dimension(image, args.max_dimension)
        print(f"  ✓ Resized ({image.width}x{image.height})")

        # Save image
        output_path = Path(args.output_dir) / f"{pub_id}_figure.png"
        print(f"  ⏳ Saving feature image...")
        ImageGenerator.save_png(image, output_path)

        file_size = ImageGenerator.get_file_size_kb(output_path)
        print(f"  ✓ Saved ({file_size} KB)")

        logger.info(f"✓ Extracted feature image: {pub_id}_figure.png")

        return ImageGenerationLog(
            timestamp=timestamp,
            operation='feature',
            publication_id=pub_id,
            status='success',
            output_path=output_path
        )

    except PDFProcessorError as e:
        logger.error(f"PDF processing error: {e}")
        return ImageGenerationLog(
            timestamp=timestamp,
            operation='feature',
            publication_id=pub_id,
            status='error',
            message=str(e)
        )

    except ImageGeneratorError as e:
        logger.error(f"Image generation error: {e}")
        return ImageGenerationLog(
            timestamp=timestamp,
            operation='feature',
            publication_id=pub_id,
            status='error',
            message=str(e)
        )

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return ImageGenerationLog(
            timestamp=timestamp,
            operation='feature',
            publication_id=pub_id,
            status='error',
            message=f"Unexpected error: {str(e)}"
        )


def dry_run_preview(args, logger):
    """Show what would be extracted without generating image (T045)."""
    print("\n=== Feature Image Extraction (DRY RUN) ===")
    print("No files will be written\n")

    print(f"Publication: {args.publication_id}")
    print(f"Page: {args.page}")

    pdf_path = Path(args.pdf_dir) / f"{args.publication_id}.pdf"
    output_path = Path(args.output_dir) / f"{args.publication_id}_figure.png"

    print(f"PDF: {pdf_path}")
    print(f"Output: {output_path}")

    if args.crop:
        print(f"Crop: {args.crop}")

    print("\nValidation:")

    # Check PDF exists
    if pdf_path.exists():
        print("  ✓ PDF exists")

        try:
            page_count = PDFProcessor.get_page_count(pdf_path)
            if args.page <= page_count:
                print(f"  ✓ Page {args.page} is valid (PDF has {page_count} pages)")
            else:
                print(f"  ✗ Page {args.page} is out of range (PDF has {page_count} pages)")
        except:
            print("  ⚠ Could not read page count")
    else:
        print("  ✗ PDF not found")

    # Check output directory
    output_dir = Path(args.output_dir)
    if output_dir.exists() and os.access(output_dir, os.W_OK):
        print("  ✓ Output directory is writable")
    else:
        print("  ✗ Output directory not accessible")

    # Check existing image
    if output_path.exists():
        print(f"  ⚠ Feature image already exists (would need confirmation or --force)")
    else:
        print("  ℹ️  Feature image does not exist (would create new)")

    print("\nWould perform:")
    print(f"  1. Load PDF ({args.publication_id}.pdf)")
    print(f"  2. Render page {args.page}")
    if args.crop:
        x, y, w, h = parse_crop_coordinates(args.crop)
        print(f"  3. Crop to region ({x},{y},{w},{h})")
        print(f"  4. Resize to max dimension {args.max_dimension}px")
    else:
        print(f"  3. Resize to max dimension {args.max_dimension}px")
    print(f"  4. Save as PNG")

    print("\nℹ️  No changes made (dry run mode)")


def main():
    """Main orchestration (T046)."""
    args = parse_arguments()

    # Setup logging
    logger = setup_logger(
        'extract_feature',
        verbose=args.verbose,
        log_file=args.log_file
    )

    logger.info("Starting feature image extraction")

    # Log dependency versions (T052)
    if pypdfium2:
        logger.debug(f"pypdfium2 version: {pypdfium2.V_PYPDFIUM2}")
    if PIL:
        logger.debug(f"Pillow version: {PIL.__version__}")

    # Handle dry run
    if args.dry_run:
        dry_run_preview(args, logger)
        return 0

    print("\n=== Feature Image Extraction ===")
    print(f"Publication: {args.publication_id}")
    print(f"Page: {args.page}")

    if args.crop:
        print(f"Crop: {args.crop}")

    output_path = Path(args.output_dir) / f"{args.publication_id}_figure.png"
    print(f"Output: {output_path}")
    print()

    # Validate inputs (T047 - detailed error messages)
    valid, error = validate_inputs(args, logger)
    if not valid:
        logger.error(error)
        print(error)
        return 1

    # Check overwrite protection
    proceed, cancelled = check_overwrite_protection(
        output_path,
        args.force,
        args.no_confirm
    )

    if not proceed:
        if cancelled:
            logger.info("Operation cancelled by user")
            print("\n⚠️  Operation cancelled by user")
            return 2
        else:
            logger.info("Feature image already exists (use --force to overwrite)")
            print("\n⚠️  Feature image already exists (use --force to overwrite)")
            return 0

    # Extract feature image
    log = extract_feature_image(args, logger)

    # Display result
    if log.status == 'success':
        logger.info("Feature image extraction complete")
        print("\n✓ Feature image extracted successfully")
        return 0
    else:
        logger.error(f"Feature image extraction failed: {log.message}")
        print(f"\n✗ Error: {log.message}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
