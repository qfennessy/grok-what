"""
Page comparison engine for analyzing differences between Grokipedia and Wikipedia pages
"""

import difflib
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime

from diff_match_patch import diff_match_patch

from ..scrapers.base_scraper import PageContent


@dataclass
class DiffSegment:
    """Represents a segment of text difference"""
    type: str  # 'equal', 'insert', 'delete', 'replace'
    grokipedia_text: str
    wikipedia_text: str
    position: int


@dataclass
class ComparisonResult:
    """Results of comparing two pages"""
    topic: str
    grokipedia_page: PageContent
    wikipedia_page: PageContent

    # Text similarity metrics
    text_similarity: float = 0.0  # 0-1 scale
    levenshtein_distance: int = 0
    diff_segments: List[DiffSegment] = field(default_factory=list)

    # Content metrics
    word_count_diff: int = 0
    word_count_diff_pct: float = 0.0
    section_overlap: float = 0.0  # Jaccard similarity of sections
    unique_to_grokipedia: List[str] = field(default_factory=list)
    unique_to_wikipedia: List[str] = field(default_factory=list)

    # Structural metrics
    citation_count_grokipedia: int = 0
    citation_count_wikipedia: int = 0
    citation_diff: int = 0
    has_infobox_grokipedia: bool = False
    has_infobox_wikipedia: bool = False

    # Quality metrics
    external_links_grokipedia: int = 0
    external_links_wikipedia: int = 0

    # Temporal metrics
    recency_grokipedia: Optional[datetime] = None
    recency_wikipedia: Optional[datetime] = None

    # Summary
    similarity_category: str = ""  # "high", "medium", "low"
    key_differences: List[str] = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.now)


class PageComparator:
    """
    Compares Grokipedia and Wikipedia pages to identify differences and similarities.
    """

    def __init__(self):
        self.dmp = diff_match_patch()

    def compare(self, grokipedia_page: PageContent, wikipedia_page: PageContent) -> ComparisonResult:
        """
        Perform comprehensive comparison between two pages.

        Args:
            grokipedia_page: PageContent from Grokipedia
            wikipedia_page: PageContent from Wikipedia

        Returns:
            ComparisonResult with detailed comparison metrics
        """
        result = ComparisonResult(
            topic=grokipedia_page.title,
            grokipedia_page=grokipedia_page,
            wikipedia_page=wikipedia_page
        )

        # Calculate text similarity
        result.text_similarity = self._calculate_text_similarity(
            grokipedia_page.text_content,
            wikipedia_page.text_content
        )

        # Calculate Levenshtein distance (limited to avoid performance issues)
        result.levenshtein_distance = self._calculate_levenshtein_distance(
            grokipedia_page.text_content[:10000],
            wikipedia_page.text_content[:10000]
        )

        # Generate diff segments
        result.diff_segments = self._generate_diff_segments(
            grokipedia_page.text_content,
            wikipedia_page.text_content
        )

        # Content metrics
        result.word_count_diff = grokipedia_page.word_count - wikipedia_page.word_count
        if wikipedia_page.word_count > 0:
            result.word_count_diff_pct = (result.word_count_diff / wikipedia_page.word_count) * 100

        # Section analysis
        result.section_overlap = self._calculate_section_overlap(
            grokipedia_page.sections,
            wikipedia_page.sections
        )

        result.unique_to_grokipedia = self._find_unique_sections(
            grokipedia_page.sections,
            wikipedia_page.sections
        )

        result.unique_to_wikipedia = self._find_unique_sections(
            wikipedia_page.sections,
            grokipedia_page.sections
        )

        # Structural metrics
        result.citation_count_grokipedia = len(grokipedia_page.citations)
        result.citation_count_wikipedia = len(wikipedia_page.citations)
        result.citation_diff = result.citation_count_grokipedia - result.citation_count_wikipedia

        result.has_infobox_grokipedia = grokipedia_page.infobox is not None
        result.has_infobox_wikipedia = wikipedia_page.infobox is not None

        # External links
        result.external_links_grokipedia = len(grokipedia_page.external_links)
        result.external_links_wikipedia = len(wikipedia_page.external_links)

        # Temporal
        result.recency_grokipedia = grokipedia_page.last_modified
        result.recency_wikipedia = wikipedia_page.last_modified

        # Categorize similarity
        result.similarity_category = self._categorize_similarity(result.text_similarity)

        # Identify key differences
        result.key_differences = self._identify_key_differences(result)

        return result

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity ratio between two texts using SequenceMatcher.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity ratio (0.0 to 1.0)
        """
        if not text1 or not text2:
            return 0.0

        # Use difflib's SequenceMatcher for similarity
        matcher = difflib.SequenceMatcher(None, text1.lower(), text2.lower())
        return matcher.ratio()

    def _calculate_levenshtein_distance(self, text1: str, text2: str) -> int:
        """
        Calculate Levenshtein distance (limited for performance).

        Args:
            text1: First text (truncated to 10000 chars)
            text2: Second text (truncated to 10000 chars)

        Returns:
            Edit distance
        """
        # Simple implementation using difflib
        # For production, consider using python-Levenshtein library
        diffs = self.dmp.diff_main(text1[:10000], text2[:10000])
        return self.dmp.diff_levenshtein(diffs)

    def _generate_diff_segments(self, text1: str, text2: str, max_segments: int = 100) -> List[DiffSegment]:
        """
        Generate diff segments showing where texts differ.

        Args:
            text1: Grokipedia text
            text2: Wikipedia text
            max_segments: Maximum number of segments to return

        Returns:
            List of DiffSegment objects
        """
        diffs = self.dmp.diff_main(text1, text2)
        self.dmp.diff_cleanupSemantic(diffs)

        segments = []
        position = 0

        for diff_type, text in diffs[:max_segments]:
            if diff_type == 0:  # Equal
                segment_type = 'equal'
                grok_text = text
                wiki_text = text
            elif diff_type == -1:  # Deletion (in Wikipedia but not Grokipedia)
                segment_type = 'delete'
                grok_text = ""
                wiki_text = text
            else:  # Insertion (in Grokipedia but not Wikipedia)
                segment_type = 'insert'
                grok_text = text
                wiki_text = ""

            segments.append(DiffSegment(
                type=segment_type,
                grokipedia_text=grok_text[:500],  # Limit length
                wikipedia_text=wiki_text[:500],
                position=position
            ))

            position += len(text)

        return segments

    def _calculate_section_overlap(self, sections1: Dict[str, str], sections2: Dict[str, str]) -> float:
        """
        Calculate Jaccard similarity of section titles.

        Args:
            sections1: Sections from first page
            sections2: Sections from second page

        Returns:
            Jaccard similarity (0.0 to 1.0)
        """
        if not sections1 or not sections2:
            return 0.0

        set1 = set(sections1.keys())
        set2 = set(sections2.keys())

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def _find_unique_sections(self, sections1: Dict[str, str], sections2: Dict[str, str]) -> List[str]:
        """
        Find sections that exist in sections1 but not in sections2.

        Args:
            sections1: Sections to check
            sections2: Sections to compare against

        Returns:
            List of unique section titles
        """
        set1 = set(sections1.keys())
        set2 = set(sections2.keys())
        return sorted(list(set1 - set2))

    def _categorize_similarity(self, similarity: float) -> str:
        """
        Categorize similarity score into high/medium/low.

        Args:
            similarity: Similarity score (0.0 to 1.0)

        Returns:
            Category string
        """
        if similarity >= 0.85:
            return "high"
        elif similarity >= 0.60:
            return "medium"
        else:
            return "low"

    def _identify_key_differences(self, result: ComparisonResult) -> List[str]:
        """
        Identify and summarize key differences between pages.

        Args:
            result: ComparisonResult object

        Returns:
            List of key difference descriptions
        """
        differences = []

        # Length difference
        if abs(result.word_count_diff_pct) > 25:
            if result.word_count_diff > 0:
                differences.append(
                    f"Grokipedia version is {abs(result.word_count_diff_pct):.1f}% longer "
                    f"({result.grokipedia_page.word_count} vs {result.wikipedia_page.word_count} words)"
                )
            else:
                differences.append(
                    f"Wikipedia version is {abs(result.word_count_diff_pct):.1f}% longer "
                    f"({result.wikipedia_page.word_count} vs {result.grokipedia_page.word_count} words)"
                )

        # Citation difference
        if abs(result.citation_diff) > 5:
            if result.citation_diff > 0:
                differences.append(
                    f"Grokipedia has {result.citation_diff} more citations "
                    f"({result.citation_count_grokipedia} vs {result.citation_count_wikipedia})"
                )
            else:
                differences.append(
                    f"Wikipedia has {abs(result.citation_diff)} more citations "
                    f"({result.citation_count_wikipedia} vs {result.citation_count_grokipedia})"
                )

        # Unique sections
        if result.unique_to_grokipedia:
            differences.append(
                f"Grokipedia has unique sections: {', '.join(result.unique_to_grokipedia[:3])}"
            )

        if result.unique_to_wikipedia:
            differences.append(
                f"Wikipedia has unique sections: {', '.join(result.unique_to_wikipedia[:3])}"
            )

        # Infobox difference
        if result.has_infobox_grokipedia != result.has_infobox_wikipedia:
            if result.has_infobox_grokipedia:
                differences.append("Grokipedia has an infobox, Wikipedia does not")
            else:
                differences.append("Wikipedia has an infobox, Grokipedia does not")

        # Overall similarity
        differences.insert(0, f"Text similarity: {result.text_similarity:.2%} ({result.similarity_category})")

        return differences
