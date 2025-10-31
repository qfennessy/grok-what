"""
Grokipedia scraper for extracting content from grokipedia.com
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import quote
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, PageContent


class GrokipediaScraper(BaseScraper):
    """
    Scraper for Grokipedia pages (grokipedia.com).
    Adapts to the specific structure of xAI's Wikipedia clone.
    """

    BASE_URL = "https://grokipedia.com"

    def get_page_url(self, topic: str) -> str:
        """Construct Grokipedia URL for a topic"""
        # Grokipedia might use a similar URL structure to Wikipedia
        encoded_topic = quote(topic.replace(" ", "_"))
        return f"{self.BASE_URL}/wiki/{encoded_topic}"

    def parse_page(self, html: str, url: str) -> PageContent:
        """
        Parse Grokipedia HTML into structured PageContent.

        Note: This implementation makes assumptions about Grokipedia's structure.
        It may need adjustments based on the actual site structure.

        Args:
            html: Raw HTML content
            url: Page URL

        Returns:
            Structured PageContent
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Extract title (try common patterns)
        title = self._extract_title(soup)

        # Extract main content
        # Try common content container IDs/classes
        content_div = (
            soup.find('div', {'id': 'content'}) or
            soup.find('div', {'class': 'content'}) or
            soup.find('main') or
            soup.find('article') or
            soup.find('div', {'id': 'mw-content-text'})  # If using MediaWiki structure
        )

        # Extract sections
        sections = self._extract_sections(content_div) if content_div else {}

        # Extract text content
        text_content = self.extract_text_from_html(str(content_div)) if content_div else ""

        # Extract citations
        citations = self._extract_citations(content_div) if content_div else []

        # Extract infobox
        infobox = self._extract_infobox(soup)

        # Extract images
        images = self._extract_images(content_div) if content_div else []

        # Extract categories
        categories = self._extract_categories(soup)

        # Extract external links
        external_links = self._extract_external_links(soup)

        # Extract last modified date
        last_modified = self._extract_last_modified(soup)

        return PageContent(
            title=title,
            url=url,
            raw_html=html,
            text_content=text_content,
            sections=sections,
            citations=citations,
            infobox=infobox,
            images=images,
            external_links=external_links,
            categories=categories,
            last_modified=last_modified,
            metadata={'source': 'grokipedia'}
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title from various possible locations"""
        # Try common title locations
        title_candidates = [
            soup.find('h1', {'id': 'firstHeading'}),
            soup.find('h1', {'class': 'title'}),
            soup.find('h1', {'class': 'page-title'}),
            soup.find('h1'),
            soup.find('title')
        ]

        for candidate in title_candidates:
            if candidate:
                text = candidate.get_text().strip()
                # Clean up title (remove " - Grokipedia" suffix if present)
                text = re.sub(r'\s*[-–—]\s*Grokipedia.*$', '', text)
                if text:
                    return text

        return "Unknown Title"

    def _extract_sections(self, content_div) -> Dict[str, str]:
        """Extract sections with headers and their content"""
        sections = {}
        current_section = "Introduction"
        current_content = []

        # Look for various heading patterns
        for elem in content_div.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'div']):
            if elem.name in ['h1', 'h2', 'h3', 'h4']:
                # Save previous section
                if current_content:
                    sections[current_section] = ' '.join(current_content)
                    current_content = []

                # Start new section
                current_section = elem.get_text().strip()

                # Skip empty or navigation headers
                if not current_section or current_section.lower() in ['contents', 'navigation', 'menu']:
                    current_section = "Introduction"

            elif elem.name in ['p', 'ul', 'ol']:
                # Add content to current section
                text = elem.get_text().strip()
                if text and len(text) > 10:  # Ignore very short snippets
                    current_content.append(text)

        # Save last section
        if current_content:
            sections[current_section] = ' '.join(current_content)

        return sections

    def _extract_citations(self, content_div) -> List[Dict]:
        """Extract citations/references"""
        citations = []

        # Try multiple patterns for citations
        ref_patterns = [
            content_div.find_all('sup', {'class': 'reference'}),
            content_div.find_all('a', {'class': 'citation'}),
            content_div.find_all('span', {'class': 'citation'})
        ]

        citation_num = 1
        for pattern in ref_patterns:
            for ref in pattern:
                link = ref.find('a')
                citations.append({
                    'number': citation_num,
                    'id': link.get('href', '').replace('#', '') if link else f'ref-{citation_num}',
                    'text': ref.get_text().strip()
                })
                citation_num += 1

        # Also look for a references/bibliography section
        refs_section = content_div.find(['div', 'section'], {'class': re.compile(r'references|bibliography')})
        if refs_section:
            ref_items = refs_section.find_all(['li', 'p'])
            for i, item in enumerate(ref_items, citation_num):
                text = item.get_text().strip()
                if text:
                    citations.append({
                        'number': i,
                        'id': f'ref-{i}',
                        'text': text[:200]  # Limit length
                    })

        return citations

    def _extract_infobox(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract infobox data"""
        # Try various infobox patterns
        infobox = (
            soup.find('table', {'class': 'infobox'}) or
            soup.find('div', {'class': 'infobox'}) or
            soup.find('aside', {'class': 'infobox'}) or
            soup.find('table', {'class': re.compile(r'info|fact|summary')})
        )

        if not infobox:
            return None

        data = {}

        # Try to extract key-value pairs
        rows = infobox.find_all('tr')
        for row in rows:
            header = row.find(['th', 'dt'])
            value = row.find(['td', 'dd'])

            if header and value:
                key = header.get_text().strip()
                val = value.get_text().strip()
                if key and val:
                    data[key] = val

        return data if data else None

    def _extract_images(self, content_div) -> List[str]:
        """Extract image URLs"""
        images = []
        img_tags = content_div.find_all('img')

        for img in img_tags:
            src = img.get('src', '') or img.get('data-src', '')
            if src:
                # Handle relative URLs
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = self.BASE_URL + src

                # Skip tiny icons and SVGs
                if not src.endswith('.svg') and 'icon' not in src.lower():
                    images.append(src)

        return images

    def _extract_categories(self, soup: BeautifulSoup) -> List[str]:
        """Extract page categories"""
        categories = []

        # Try various category patterns
        cat_containers = [
            soup.find('div', {'id': 'categories'}),
            soup.find('div', {'class': 'categories'}),
            soup.find('div', {'id': 'mw-normal-catlinks'}),
            soup.find('footer')
        ]

        for container in cat_containers:
            if container:
                cat_links = container.find_all('a')
                for link in cat_links:
                    text = link.get_text().strip()
                    if text and text.lower() not in ['category', 'categories']:
                        categories.append(text)

        return list(set(categories))  # Remove duplicates

    def _extract_external_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract external links"""
        links = []

        # Look for external links section
        ext_links_headers = soup.find_all(['h2', 'h3', 'h4'],
                                          string=re.compile(r'External [Ll]inks?|References?|Sources?'))

        for header in ext_links_headers:
            # Find the next list after the header
            next_elem = header.find_next_sibling(['ul', 'ol', 'div'])
            if next_elem:
                for link in next_elem.find_all('a', href=True):
                    href = link.get('href', '')
                    # Only include actual external links
                    if href.startswith('http') and self.BASE_URL not in href:
                        links.append(href)

        return links

    def _extract_last_modified(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract last modified date"""
        # Try various date patterns
        date_patterns = [
            soup.find('time'),
            soup.find('span', {'class': re.compile(r'date|time|modified')}),
            soup.find('div', {'class': re.compile(r'date|time|modified')}),
            soup.find('meta', {'property': 'article:modified_time'}),
            soup.find('li', {'id': 'footer-info-lastmod'})
        ]

        for elem in date_patterns:
            if not elem:
                continue

            # Try to get datetime attribute
            if elem.get('datetime'):
                try:
                    return datetime.fromisoformat(elem['datetime'].replace('Z', '+00:00'))
                except ValueError:
                    pass

            # Try to get content attribute (for meta tags)
            if elem.get('content'):
                try:
                    return datetime.fromisoformat(elem['content'].replace('Z', '+00:00'))
                except ValueError:
                    pass

            # Try to parse text content
            text = elem.get_text()
            date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', text)
            if date_match:
                try:
                    return datetime.strptime(date_match.group(1), '%d %B %Y')
                except ValueError:
                    try:
                        return datetime.strptime(date_match.group(1), '%B %d, %Y')
                    except ValueError:
                        pass

        return None
