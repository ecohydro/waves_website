"""Scholar AI PDF fetching service.

This module adapts the Scholar API integration from fill_abstracts.py
for downloading PDF files instead of abstracts.
"""

import os
import time
import requests
import logging
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logger
logger = logging.getLogger(__name__)


class ScholarFetcherError(Exception):
    """Base exception for Scholar fetcher errors."""
    pass


class ScholarAuthError(ScholarFetcherError):
    """Raised when Scholar API authentication fails."""
    pass


class ScholarFetcher:
    """Handles PDF fetching from Scholar AI."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Scholar fetcher.

        Args:
            api_key: Scholar API key (reads from SCHOLAR_API_KEY env if not provided)
        """
        self.api_key = api_key or os.getenv('SCHOLAR_API_KEY')
        if not self.api_key:
            raise ScholarAuthError(
                "Scholar API key not found. Set SCHOLAR_API_KEY environment variable."
            )

        self.base_url = "https://api.scholarai.io/api/v1"
        self.last_request_time = 0
        self.rate_limit_seconds = 1.0  # 1 second between requests

        # Log rate limit configuration (T057)
        logger.debug(f"Scholar API rate limit: {self.rate_limit_seconds} seconds between requests")

    def _rate_limit(self):
        """Enforce rate limiting between requests (T057)."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_seconds:
            wait_time = self.rate_limit_seconds - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
        self.last_request_time = time.time()

    def fetch_pdf_by_doi(
        self,
        doi: str,
        output_path: Path,
        max_retries: int = 3
    ) -> Tuple[bool, str]:
        """Fetch PDF from Scholar AI using DOI.

        Args:
            doi: Digital Object Identifier
            output_path: Path where to save the PDF
            max_retries: Maximum number of retry attempts

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not doi:
            return False, "No DOI provided"

        # Enforce rate limiting
        self._rate_limit()

        # Build request URL - using search endpoint to find paper
        url = f"{self.base_url}/search"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Query for the DOI
        params = {
            'keywords': doi,
            'limit': 1
        }

        retries = 0
        while retries <= max_retries:
            try:
                # Search for paper by DOI
                response = requests.get(url, headers=headers, params=params, timeout=30)

                # Handle rate limiting
                if response.status_code == 429:
                    retries += 1
                    if retries <= max_retries:
                        wait_time = 2 ** retries  # Exponential backoff
                        time.sleep(wait_time)
                        continue
                    return False, "Rate limit exceeded after retries"

                # Handle authentication errors
                if response.status_code in [401, 403]:
                    return False, "Authentication error (invalid API key)"

                # Handle server errors
                if response.status_code >= 500:
                    retries += 1
                    if retries <= max_retries:
                        time.sleep(2)
                        continue
                    return False, f"Server error ({response.status_code})"

                # Success - process response
                if response.status_code == 200:
                    data = response.json()

                    # Check if results found
                    if not data.get('results') or len(data['results']) == 0:
                        return False, "DOI not found in Scholar AI"

                    # Get first result
                    paper = data['results'][0]

                    # Check if PDF URL available
                    pdf_url = paper.get('pdf_url') or paper.get('pdfUrl')
                    if not pdf_url:
                        return False, "PDF not available for this DOI"

                    # Download the PDF
                    return self._download_pdf(pdf_url, output_path)

                # Other error codes
                return False, f"Unexpected status code: {response.status_code}"

            except requests.exceptions.Timeout:
                retries += 1
                if retries <= max_retries:
                    continue
                return False, "Request timeout after retries"

            except requests.exceptions.ConnectionError:
                retries += 1
                if retries <= max_retries:
                    time.sleep(1)
                    continue
                return False, "Network connection error"

            except Exception as e:
                return False, f"Unexpected error: {str(e)}"

        return False, "Max retries exceeded"

    def _download_pdf(self, pdf_url: str, output_path: Path) -> Tuple[bool, str]:
        """Download PDF from URL.

        Args:
            pdf_url: URL to PDF file
            output_path: Path where to save the PDF

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Download PDF
            response = requests.get(pdf_url, timeout=60, stream=True)

            if response.status_code != 200:
                return False, f"Failed to download PDF: HTTP {response.status_code}"

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Verify file was created and has content
            if not output_path.exists() or output_path.stat().st_size == 0:
                return False, "Downloaded file is empty or not created"

            return True, "PDF downloaded successfully"

        except Exception as e:
            return False, f"Download error: {str(e)}"

    @staticmethod
    def create_fetch_result(
        publication_id: str,
        doi: str,
        success: bool,
        message: str,
        pdf_path: Optional[Path] = None
    ):
        """Create a ScholarFetchResult object.

        Args:
            publication_id: Canonical ID of publication
            doi: DOI used for fetch
            success: Whether fetch succeeded
            message: Status or error message
            pdf_path: Path to saved PDF if successful

        Returns:
            ScholarFetchResult object
        """
        from models.scholar_result import ScholarFetchResult

        # Map success and message to status
        if success:
            status = 'success'
        elif 'not found' in message.lower():
            status = 'not_found'
        elif 'auth' in message.lower():
            status = 'auth_error'
        else:
            status = 'network_error'

        return ScholarFetchResult(
            publication_id=publication_id,
            doi=doi,
            status=status,
            fetch_timestamp=datetime.now(),
            error_message=None if success else message,
            pdf_path=pdf_path if success else None
        )
