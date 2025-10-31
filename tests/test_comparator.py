"""
Unit tests for PageComparator
"""

import pytest
from src.comparators.page_comparator import PageComparator, ComparisonResult
from src.scrapers.base_scraper import PageContent


def create_sample_page(title: str, content: str, citations: int = 5):
    """Helper to create a sample PageContent for testing"""
    return PageContent(
        title=title,
        url=f"http://example.com/{title}",
        raw_html="<html></html>",
        text_content=content,
        sections={"Introduction": content[:100], "Main": content[100:]},
        citations=[{"number": i, "id": f"ref{i}", "text": f"Citation {i}"} for i in range(citations)],
        infobox={"Key": "Value"},
        images=["image1.jpg"],
        external_links=["http://example.com"],
        categories=["Category1"],
        metadata={'source': 'test'}
    )


def test_comparator_initialization():
    """Test that comparator initializes correctly"""
    comparator = PageComparator()
    assert comparator is not None


def test_compare_identical_pages():
    """Test comparing identical pages"""
    comparator = PageComparator()

    content = "This is a test page with some content. " * 10
    page1 = create_sample_page("Test", content)
    page2 = create_sample_page("Test", content)

    result = comparator.compare(page1, page2)

    assert result.text_similarity == 1.0
    assert result.similarity_category == "high"
    assert result.word_count_diff == 0


def test_compare_different_pages():
    """Test comparing different pages"""
    comparator = PageComparator()

    content1 = "This is the first page with unique content. " * 10
    content2 = "This is the second page with different content. " * 10

    page1 = create_sample_page("Test1", content1)
    page2 = create_sample_page("Test2", content2)

    result = comparator.compare(page1, page2)

    assert result.text_similarity < 1.0
    assert result.text_similarity > 0.0  # Should have some similarity
    assert isinstance(result.similarity_category, str)


def test_text_similarity_calculation():
    """Test text similarity calculation"""
    comparator = PageComparator()

    text1 = "The quick brown fox jumps over the lazy dog"
    text2 = "The quick brown fox jumps over the lazy cat"

    similarity = comparator._calculate_text_similarity(text1, text2)

    assert 0.0 <= similarity <= 1.0
    assert similarity > 0.8  # Very similar texts


def test_section_overlap():
    """Test section overlap calculation"""
    comparator = PageComparator()

    sections1 = {"Intro": "content1", "Main": "content2", "Conclusion": "content3"}
    sections2 = {"Intro": "content1", "Main": "different", "References": "refs"}

    overlap = comparator._calculate_section_overlap(sections1, sections2)

    assert 0.0 <= overlap <= 1.0
    # 2 sections in common (Intro, Main), 4 total unique sections
    assert overlap == 0.5  # 2/4


def test_categorize_similarity():
    """Test similarity categorization"""
    comparator = PageComparator()

    assert comparator._categorize_similarity(0.9) == "high"
    assert comparator._categorize_similarity(0.7) == "medium"
    assert comparator._categorize_similarity(0.3) == "low"


def test_find_unique_sections():
    """Test finding unique sections"""
    comparator = PageComparator()

    sections1 = {"A": "content", "B": "content", "C": "content"}
    sections2 = {"B": "content", "D": "content"}

    unique = comparator._find_unique_sections(sections1, sections2)

    assert "A" in unique
    assert "C" in unique
    assert "B" not in unique
    assert len(unique) == 2


def test_comparison_result_structure():
    """Test that ComparisonResult has all expected fields"""
    comparator = PageComparator()

    content = "Test content " * 20
    page1 = create_sample_page("Test1", content, citations=5)
    page2 = create_sample_page("Test2", content, citations=10)

    result = comparator.compare(page1, page2)

    # Check all expected fields exist
    assert hasattr(result, 'topic')
    assert hasattr(result, 'text_similarity')
    assert hasattr(result, 'similarity_category')
    assert hasattr(result, 'word_count_diff')
    assert hasattr(result, 'citation_diff')
    assert hasattr(result, 'section_overlap')
    assert hasattr(result, 'key_differences')

    # Check citation diff
    assert result.citation_diff == -5  # page1 has 5 fewer citations
