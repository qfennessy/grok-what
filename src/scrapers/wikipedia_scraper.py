"""
Wikipedia scraper using the Wikipedia API and HTML parsing
"""

import re
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import quote
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper, PageContent


class WikipediaScraper(BaseScraper):
    """
    Scraper for Wikipedia pages using the MediaWiki API and HTML parsing.
    """

    BASE_URL = "https://en.wikipedia.org"
    API_URL = "https://en.wikipedia.org/w/api.php"

    def get_page_url(self, topic: str) -> str:
        """Construct Wikipedia URL for a topic"""
        encoded_topic = quote(topic.replace(" ", "_"))
        return f"{self.BASE_URL}/wiki/{encoded_topic}"

    def _fetch_via_api(self, topic: str) -> Optional[Dict]:
        """
        Fetch page data via Wikipedia API.

        Args:
            topic: Page title

        Returns:
            API response data or None
        """
        params = {
            'action': 'parse',
            'page': topic,
            'format': 'json',
            'prop': 'text|sections|categories|externallinks|displaytitle',
            'disabletoc': '1'
        }

        try:
            self._rate_limit()
            response = self.session.get(self.API_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                print(f"Wikipedia API error for '{topic}': {data['error']['info']}")
                return None

            return data.get('parse', {})
        except Exception as e:
            print(f"Failed to fetch Wikipedia API data for '{topic}': {e}")
            return None

    def parse_page(self, html: str, url: str) -> PageContent:
        """
        Parse Wikipedia HTML into structured PageContent.

        Args:
            html: Raw HTML content
            url: Page URL

        Returns:
            Structured PageContent
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Extract title
        title = self._extract_title(soup)

        # Extract main content
        content_div = soup.find('div', {'id': 'mw-content-text'})
        if not content_div:
            content_div = soup.find('div', {'class': 'mw-parser-output'})

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
            metadata={'source': 'wikipedia'}
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_elem = soup.find('h1', {'id': 'firstHeading'})
        if title_elem:
            return title_elem.get_text().strip()
        # Fallback to title tag
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().replace(' - Wikipedia', '').strip()
        return "Unknown Title"

    def _extract_sections(self, content_div) -> Dict[str, str]:
        """Extract sections with headers and their content"""
        sections = {}
        current_section = "Introduction"
        current_content = []

        for elem in content_div.find_all(['h2', 'h3', 'p', 'ul', 'ol']):
            if elem.name in ['h2', 'h3']:
                # Save previous section
                if current_content:
                    sections[current_section] = ' '.join(current_content)
                    current_content = []

                # Start new section
                headline = elem.find('span', {'class': 'mw-headline'})
                if headline:
                    current_section = headline.get_text().strip()
            else:
                # Add content to current section
                text = elem.get_text().strip()
                if text:
                    current_content.append(text)

        # Save last section
        if current_content:
            sections[current_section] = ' '.join(current_content)

        return sections

    def _extract_citations(self, content_div) -> List[Dict]:
        """Extract citations/references"""
        citations = []
        refs = content_div.find_all('sup', {'class': 'reference'})

        for i, ref in enumerate(refs, 1):
            link = ref.find('a')
            if link:
                citations.append({
                    'number': i,
                    'id': link.get('href', '').replace('#', ''),
                    'text': ref.get_text().strip()
                })

        return citations

    def _extract_infobox(self, soup: BeautifulSoup) -> Optional[Dict]:
        """Extract infobox data"""
        infobox = soup.find('table', {'class': 'infobox'})
        if not infobox:
            return None

        data = {}
        rows = infobox.find_all('tr')

        for row in rows:
            header = row.find('th')
            value = row.find('td')

            if header and value:
                key = header.get_text().strip()
                val = value.get_text().strip()
                data[key] = val

        return data if data else None

    def _extract_images(self, content_div) -> List[str]:
        """Extract image URLs"""
        images = []
        img_tags = content_div.find_all('img')

        for img in img_tags:
            src = img.get('src', '')
            if src and not src.endswith('.svg'):  # Skip SVG icons
                if src.startswith('//'):
                    src = 'https:' + src
                images.append(src)

        return images

    def _extract_categories(self, soup: BeautifulSoup) -> List[str]:
        """Extract page categories"""
        categories = []
        cat_div = soup.find('div', {'id': 'mw-normal-catlinks'})

        if cat_div:
            cat_links = cat_div.find_all('a')
            for link in cat_links:
                if link.get_text() != "Categories":
                    categories.append(link.get_text().strip())

        return categories

    def _extract_external_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract external links from the External Links section"""
        links = []
        ext_links_section = soup.find('span', {'id': 'External_links'})

        if ext_links_section:
            parent = ext_links_section.find_parent(['h2', 'h3'])
            if parent:
                # Find the next ul after the header
                ul = parent.find_next_sibling('ul')
                if ul:
                    for link in ul.find_all('a', {'class': 'external'}):
                        href = link.get('href', '')
                        if href:
                            links.append(href)

        return links

    def _extract_last_modified(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract last modified date"""
        footer = soup.find('li', {'id': 'footer-info-lastmod'})
        if footer:
            text = footer.get_text()
            # Parse date string like "This page was last edited on 31 October 2024, at 10:00"
            match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', text)
            if match:
                try:
                    return datetime.strptime(match.group(1), '%d %B %Y')
                except ValueError:
                    pass

        return None
