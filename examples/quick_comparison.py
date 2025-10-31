#!/usr/bin/env python3
"""
Quick comparison example - Compare a single topic between Grokipedia and Wikipedia
"""

import sys
sys.path.insert(0, '..')

from src.scrapers import WikipediaScraper, GrokipediaScraper
from src.comparators import PageComparator
from src.analyzers import MetricsAnalyzer


def quick_compare(topic: str):
    """
    Quickly compare a single topic between Grokipedia and Wikipedia.

    Args:
        topic: The topic/page title to compare
    """
    print(f"Comparing: {topic}")
    print("=" * 80)

    # Initialize scrapers
    wiki_scraper = WikipediaScraper()
    grok_scraper = GrokipediaScraper()
    comparator = PageComparator()
    analyzer = MetricsAnalyzer()

    # Fetch pages
    print("\nFetching Wikipedia page...")
    wiki_page = wiki_scraper.fetch_and_parse(topic)
    if not wiki_page:
        print("Failed to fetch Wikipedia page!")
        return

    print("Fetching Grokipedia page...")
    grok_page = grok_scraper.fetch_and_parse(topic)
    if not grok_page:
        print("Failed to fetch Grokipedia page!")
        return

    # Compare
    print("\nComparing pages...")
    result = comparator.compare(grok_page, wiki_page)

    # Display results
    print("\n" + "=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    print(f"\nText Similarity: {result.text_similarity:.2%} ({result.similarity_category})")
    print(f"Levenshtein Distance: {result.levenshtein_distance}")

    print(f"\nContent Metrics:")
    print(f"  Word Count (Grokipedia): {result.grokipedia_page.word_count}")
    print(f"  Word Count (Wikipedia):  {result.wikipedia_page.word_count}")
    print(f"  Difference: {result.word_count_diff} ({result.word_count_diff_pct:.1f}%)")

    print(f"\nCitations:")
    print(f"  Grokipedia: {result.citation_count_grokipedia}")
    print(f"  Wikipedia:  {result.citation_count_wikipedia}")
    print(f"  Difference: {result.citation_diff}")

    print(f"\nSection Overlap: {result.section_overlap:.2%}")

    if result.unique_to_grokipedia:
        print(f"\nSections unique to Grokipedia ({len(result.unique_to_grokipedia)}):")
        for section in result.unique_to_grokipedia[:5]:
            print(f"  - {section}")

    if result.unique_to_wikipedia:
        print(f"\nSections unique to Wikipedia ({len(result.unique_to_wikipedia)}):")
        for section in result.unique_to_wikipedia[:5]:
            print(f"  - {section}")

    print(f"\nKey Differences:")
    for i, diff in enumerate(result.key_differences, 1):
        print(f"  {i}. {diff}")

    # Calculate quality metrics
    print(f"\nQuality Metrics:")
    grok_quality = analyzer.calculate_quality_metrics(
        grok_page.text_content,
        len(grok_page.citations)
    )
    wiki_quality = analyzer.calculate_quality_metrics(
        wiki_page.text_content,
        len(wiki_page.citations)
    )

    print(f"  Readability (Grokipedia): {grok_quality.readability_score:.1f}")
    print(f"  Readability (Wikipedia):  {wiki_quality.readability_score:.1f}")
    print(f"  Citation Density (Grokipedia): {grok_quality.citation_density:.1f} per 1000 words")
    print(f"  Citation Density (Wikipedia):  {wiki_quality.citation_density:.1f} per 1000 words")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = "Artificial intelligence"
        print(f"No topic provided. Using default: {topic}")

    quick_compare(topic)
