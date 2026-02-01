"""PDF processing service for rendering pages to images.

This module provides PDF rendering capabilities using pypdfium2
for extracting pages as PIL Image objects.
"""

from pathlib import Path
from typing import Optional
from PIL import Image
import pypdfium2 as pdfium


class PDFProcessorError(Exception):
    """Base exception for PDF processing errors."""
    pass


class PDFNotFoundError(PDFProcessorError):
    """Raised when PDF file is not found."""
    pass


class PDFCorruptedError(PDFProcessorError):
    """Raised when PDF file is corrupted or unreadable."""
    pass


class PDFPasswordProtectedError(PDFProcessorError):
    """Raised when PDF is password-protected."""
    pass


class PDFProcessor:
    """Handles PDF rendering and page extraction using pypdfium2."""

    @staticmethod
    def render_page(
        pdf_path: Path,
        page_num: int = 0,
        target_height: Optional[int] = None,
        target_width: Optional[int] = None
    ) -> Image.Image:
        """Render a single PDF page to PIL Image.

        Args:
            pdf_path: Path to PDF file
            page_num: Page number to render (0-indexed)
            target_height: Target height in pixels (scales proportionally if set)
            target_width: Target width in pixels (scales proportionally if set)

        Returns:
            PIL Image object of the rendered page

        Raises:
            PDFNotFoundError: If PDF file doesn't exist
            PDFCorruptedError: If PDF is corrupted or unreadable
            PDFPasswordProtectedError: If PDF is password-protected
            PDFProcessorError: For other PDF processing errors
        """
        # Validate PDF exists
        if not pdf_path.exists():
            raise PDFNotFoundError(f"PDF not found: {pdf_path}")

        try:
            # Open PDF document (T051: pypdfium2 uses lazy loading - doesn't load all pages into memory)
            doc = pdfium.PdfDocument(str(pdf_path))
        except Exception as e:
            error_msg = str(e).lower()
            if 'password' in error_msg:
                raise PDFPasswordProtectedError(f"PDF is password-protected: {pdf_path}")
            elif 'corrupt' in error_msg or 'invalid' in error_msg:
                raise PDFCorruptedError(f"PDF is corrupted or invalid: {pdf_path}")
            else:
                raise PDFProcessorError(f"Failed to open PDF {pdf_path}: {e}")

        # Validate page number
        if page_num < 0 or page_num >= len(doc):
            doc.close()  # Clean up before raising error
            raise PDFProcessorError(
                f"Page {page_num} out of range (PDF has {len(doc)} pages)"
            )

        try:
            # Get the page (only this page is loaded into memory, not the entire PDF)
            page = doc[page_num]

            # Calculate scale factor if target dimensions specified
            if target_height or target_width:
                # Get original page size
                page_width, page_height = page.get_size()

                if target_height:
                    # Scale to target height
                    scale = target_height / page_height
                elif target_width:
                    # Scale to target width
                    scale = target_width / page_width
                else:
                    scale = 1.0

                # Render with scale
                bitmap = page.render(scale=scale)
            else:
                # Render at default scale
                bitmap = page.render()

            # Convert bitmap to PIL Image
            pil_image = bitmap.to_pil()

            # Close bitmap and document to free resources (T051: explicit cleanup for large PDFs)
            bitmap.close()
            doc.close()

            return pil_image

        except Exception as e:
            # Ensure document is closed on error
            try:
                doc.close()
            except:
                pass
            raise PDFProcessorError(f"Failed to render page {page_num} from {pdf_path}: {e}")

    @staticmethod
    def get_page_count(pdf_path: Path) -> int:
        """Get total number of pages in PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Number of pages in the PDF

        Raises:
            PDFNotFoundError: If PDF file doesn't exist
            PDFProcessorError: If PDF cannot be opened
        """
        if not pdf_path.exists():
            raise PDFNotFoundError(f"PDF not found: {pdf_path}")

        try:
            doc = pdfium.PdfDocument(str(pdf_path))
            page_count = len(doc)
            doc.close()
            return page_count
        except Exception as e:
            raise PDFProcessorError(f"Failed to read page count from {pdf_path}: {e}")

    @staticmethod
    def get_page_size(pdf_path: Path, page_num: int = 0) -> tuple:
        """Get dimensions of a PDF page.

        Args:
            pdf_path: Path to PDF file
            page_num: Page number to check (0-indexed)

        Returns:
            Tuple of (width, height) in pixels

        Raises:
            PDFNotFoundError: If PDF file doesn't exist
            PDFProcessorError: If PDF cannot be opened or page is invalid
        """
        if not pdf_path.exists():
            raise PDFNotFoundError(f"PDF not found: {pdf_path}")

        try:
            doc = pdfium.PdfDocument(str(pdf_path))

            if page_num < 0 or page_num >= len(doc):
                doc.close()
                raise PDFProcessorError(
                    f"Page {page_num} out of range (PDF has {len(doc)} pages)"
                )

            page = doc[page_num]
            size = page.get_size()
            doc.close()

            return size
        except PDFProcessorError:
            raise
        except Exception as e:
            raise PDFProcessorError(f"Failed to get page size from {pdf_path}: {e}")
