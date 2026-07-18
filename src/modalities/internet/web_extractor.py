import logging
from typing import Optional

from bs4 import BeautifulSoup
from src.modalities.internet.http_client import HttpClient, HttpMethod

logger = logging.getLogger(__name__)

class WebExtractionError(Exception):
    """Custom exception for web extraction errors."""
    pass

class WebExtractor:
    """Extracts clean text content from web pages."""

    def __init__(self, http_client: Optional[HttpClient] = None):
        self.http_client = http_client or HttpClient()

    def extract_text(self, url: str) -> str:
        """
        Fetches a URL and extracts its main text content.

        Args:
            url: The URL of the web page to extract content from.

        Returns:
            The extracted clean text content of the page.

        Raises:
            WebExtractionError: If fetching or parsing fails.
        """
        try:
            logger.info(f"Fetching content from: {url}")
            response = self.http_client.request(HttpMethod.GET, url)
            html_content = response["data"]["content"]

            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style elements
            for script_or_style in soup(["script", "style"]):
                script_or_style.extract()

            # Get text and clean it up
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            # Remove blank lines
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            logger.info(f"Successfully extracted text from: {url}")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from {url}: {e}")
            raise WebExtractionError(f"Failed to extract text from {url}: {e}")