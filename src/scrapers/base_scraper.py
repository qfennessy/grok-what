"""
Base scraper class for extracting content from wiki-style pages
"""

import time
import requests
from abc import ABC, abstractmethod
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from bs4 import BeautifulSoup


@dataclass
class PageContent:
    """Structured representation of a wiki page"""
    title: str
    url: str
    raw_html: str
    text_content: str
    sections: Dict[str, str] = field(default_factory=dict)
    citations: List[Dict] = field(default_factory=list)
    infobox: Optional[Dict] = None
    images: List[str] = field(default_factory=list)
    external_links: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    last_modified: Optional[datetime] = None
    word_count: int = 0
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Calculate word count after initialization"""
        if self.word_count == 0 and self.text_content:
            self.word_count = len(self.text_content.split())


class BaseScraper(ABC):
    """
    Abstract base class for web scrapers.
    Provides common functionality for rate limiting and error handling.
    """

    def __init__(self, rate_limit_delay: float = 2.0, max_retries: int = 3, timeout: int = 30):
        """
        Initialize the scraper.

        Args:
            rate_limit_delay: Delay in seconds between requests
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Research Project) GrokipediaComparison/1.0'
        })
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page with retry logic and rate limiting.

        Args:
            url: URL to fetch

        Returns:
            HTML content or None if failed
        """
        self._rate_limit()

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1}/{self.max_retries} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"Failed to fetch {url} after {self.max_retries} attempts")
                    return None

    @abstractmethod
    def get_page_url(self, topic: str) -> str:
        """
        Construct the URL for a given topic.

        Args:
            topic: The topic/page title

        Returns:
            Full URL to the page
        """
        pass

    @abstractmethod
    def parse_page(self, html: str, url: str) -> PageContent:
        """
        Parse HTML content into structured PageContent.

        Args:
            html: Raw HTML content
            url: URL of the page

        Returns:
            Structured PageContent object
        """
        pass

    def fetch_and_parse(self, topic: str) -> Optional[PageContent]:
        """
        Fetch and parse a page for a given topic.

        Args:
            topic: The topic/page title

        Returns:
            Parsed PageContent or None if failed
        """
        url = self.get_page_url(topic)
        html = self._fetch_page(url)

        if html is None:
            return None

        return self.parse_page(html, url)

    @staticmethod
    def extract_text_from_html(html: str) -> str:
        """
        Extract clean text from HTML, removing scripts and styles.

        Args:
            html: Raw HTML content

        Returns:
            Clean text content
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text
