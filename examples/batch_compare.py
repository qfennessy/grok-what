#!/usr/bin/env python3
"""
Batch comparison example - Compare multiple topics and generate a summary
"""

import sys
sys.path.insert(0, '..')

from main import ComparisonOrchestrator


def batch_compare(topics: list, generate_reports: bool = True):
    """
    Compare multiple topics and optionally generate reports.

    Args:
        topics: List of topics to compare
        generate_reports: Whether to generate detailed reports
    """
    print(f"Batch Comparison: {len(topics)} topics")
    print("=" * 80)

    # Create orchestrator
    orchestrator = ComparisonOrchestrator()

    # Run comparison
    orchestrator.run_comparison(topics=topics)

    # Display quick summary
    print("\n" + "=" * 80)
    print("QUICK SUMMARY")
    print("=" * 80)

    if orchestrator.results:
        avg_similarity = sum(r.text_similarity for r in orchestrator.results) / len(orchestrator.results)
        print(f"\nAverage Similarity: {avg_similarity:.2%}")

        print("\nResults by topic:")
        for result in sorted(orchestrator.results, key=lambda r: r.text_similarity, reverse=True):
            print(f"  {result.topic:<40} {result.text_similarity:.2%} ({result.similarity_category})")

        # Identify interesting cases
        most_similar = max(orchestrator.results, key=lambda r: r.text_similarity)
        most_different = min(orchestrator.results, key=lambda r: r.text_similarity)

        print(f"\nMost Similar: {most_similar.topic} ({most_similar.text_similarity:.2%})")
        print(f"Most Different: {most_different.topic} ({most_different.text_similarity:.2%})")

        # Generate reports if requested
        if generate_reports:
            print("\nGenerating detailed reports...")
            orchestrator.generate_reports()
    else:
        print("\nNo successful comparisons.")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Default topics
    default_topics = [
        "Python (programming language)",
        "Climate change",
        "Artificial intelligence",
        "Quantum computing",
        "Donald Trump"
    ]

    # Use command line topics if provided
    if len(sys.argv) > 1:
        topics = sys.argv[1:]
    else:
        topics = default_topics
        print("No topics provided. Using defaults:")
        for topic in topics:
            print(f"  - {topic}")
        print()

    batch_compare(topics)
