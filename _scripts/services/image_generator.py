"""Image generation service for resizing and cropping operations.

This module provides image manipulation capabilities using Pillow (PIL)
for resizing, cropping, and saving publication images.
"""

from pathlib import Path
from typing import Optional, Tuple
from PIL import Image


class ImageGeneratorError(Exception):
    """Base exception for image generation errors."""
    pass


class ImageGenerator:
    """Handles image resizing, cropping, and saving operations."""

    @staticmethod
    def resize_to_height(image: Image.Image, target_height: int) -> Image.Image:
        """Resize image to target height, maintaining aspect ratio.

        Args:
            image: PIL Image to resize
            target_height: Target height in pixels

        Returns:
            Resized PIL Image
        """
        # Get original dimensions
        original_width, original_height = image.size

        # Calculate new width maintaining aspect ratio
        aspect_ratio = original_width / original_height
        new_width = int(target_height * aspect_ratio)

        # Resize using high-quality Lanczos resampling
        resized = image.resize((new_width, target_height), Image.Resampling.LANCZOS)

        return resized

    @staticmethod
    def resize_to_max_dimension(
        image: Image.Image,
        max_dimension: int
    ) -> Image.Image:
        """Resize image so largest dimension equals max_dimension.

        Args:
            image: PIL Image to resize
            max_dimension: Maximum dimension (width or height) in pixels

        Returns:
            Resized PIL Image
        """
        # Get original dimensions
        original_width, original_height = image.size

        # Determine which dimension is larger
        if original_width >= original_height:
            # Width is limiting dimension
            scale = max_dimension / original_width
            new_width = max_dimension
            new_height = int(original_height * scale)
        else:
            # Height is limiting dimension
            scale = max_dimension / original_height
            new_width = int(original_width * scale)
            new_height = max_dimension

        # Resize using high-quality Lanczos resampling
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return resized

    @staticmethod
    def crop_region(
        image: Image.Image,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> Image.Image:
        """Crop a specific region from the image.

        Args:
            image: PIL Image to crop
            x: Left edge of crop region (0 = left edge)
            y: Top edge of crop region (0 = top edge)
            width: Width of crop region in pixels
            height: Height of crop region in pixels

        Returns:
            Cropped PIL Image

        Raises:
            ImageGeneratorError: If crop region is out of bounds
        """
        # Get original dimensions
        img_width, img_height = image.size

        # Validate crop bounds
        if x < 0 or y < 0:
            raise ImageGeneratorError(
                f"Crop coordinates must be non-negative (got x={x}, y={y})"
            )

        if x + width > img_width or y + height > img_height:
            raise ImageGeneratorError(
                f"Crop region ({x},{y},{width},{height}) extends beyond "
                f"image bounds ({img_width}x{img_height})"
            )

        # Crop using PIL box format: (left, upper, right, lower)
        box = (x, y, x + width, y + height)
        cropped = image.crop(box)

        return cropped

    @staticmethod
    def save_png(
        image: Image.Image,
        output_path: Path,
        optimize: bool = True
    ):
        """Save image as PNG file.

        Args:
            image: PIL Image to save
            output_path: Path where to save the PNG file
            optimize: Whether to optimize PNG compression (default: True)

        Raises:
            ImageGeneratorError: If save operation fails
        """
        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save as PNG with optimization
            image.save(
                output_path,
                'PNG',
                optimize=optimize,
                compress_level=6  # Balanced compression (0-9 scale)
            )
        except Exception as e:
            raise ImageGeneratorError(f"Failed to save image to {output_path}: {e}")

    @staticmethod
    def calculate_resize_dimensions(
        original_width: int,
        original_height: int,
        max_dimension: int
    ) -> Tuple[int, int]:
        """Calculate new dimensions for max_dimension constraint.

        Args:
            original_width: Original image width
            original_height: Original image height
            max_dimension: Maximum allowed dimension

        Returns:
            Tuple of (new_width, new_height)
        """
        if original_width >= original_height:
            # Width is limiting dimension
            scale = max_dimension / original_width
            new_width = max_dimension
            new_height = int(original_height * scale)
        else:
            # Height is limiting dimension
            scale = max_dimension / original_height
            new_width = int(original_width * scale)
            new_height = max_dimension

        return (new_width, new_height)

    @staticmethod
    def get_file_size_kb(image_path: Path) -> float:
        """Get file size of saved image in kilobytes.

        Args:
            image_path: Path to image file

        Returns:
            File size in KB
        """
        if not image_path.exists():
            return 0.0

        size_bytes = image_path.stat().st_size
        size_kb = size_bytes / 1024

        return round(size_kb, 1)
