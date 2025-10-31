"""Web scrapers for Grokipedia and Wikipedia"""

from .base_scraper import BaseScraper
from .wikipedia_scraper import WikipediaScraper
from .grokipedia_scraper import GrokipediaScraper

__all__ = ["BaseScraper", "WikipediaScraper", "GrokipediaScraper"]
