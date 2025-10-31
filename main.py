#!/usr/bin/env python3
"""
Main orchestrator for Grokipedia vs Wikipedia comparison
"""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm

from src.samplers.topic_sampler import TopicSampler
from src.scrapers.wikipedia_scraper import WikipediaScraper
from src.scrapers.grokipedia_scraper import GrokipediaScraper
from src.comparators.page_comparator import PageComparator, ComparisonResult
from src.analyzers.metrics_analyzer import MetricsAnalyzer
from src.visualizers.report_generator import ReportGenerator


class ComparisonOrchestrator:
    """
    Main orchestrator for running comparisons between Grokipedia and Wikipedia.
    """

    def __init__(self, config_path: str = "config/sampling_config.yaml"):
        """
        Initialize the orchestrator.

        Args:
            config_path: Path to configuration file
        """
        self.sampler = TopicSampler(config_path)
        self.wikipedia_scraper = WikipediaScraper()
        self.grokipedia_scraper = GrokipediaScraper()
        self.comparator = PageComparator()
        self.analyzer = MetricsAnalyzer()
        self.report_generator = ReportGenerator()

        self.results: List[ComparisonResult] = []

    def run_comparison(self, sample_size: int = 10, topics: Optional[List[str]] = None):
        """
        Run the comparison process.

        Args:
            sample_size: Number of topics to sample (if topics not provided)
            topics: Optional list of specific topics to compare
        """
        # Get topics to compare
        if topics:
            topic_list = [(None, topic) for topic in topics]
        else:
            print(f"Sampling {sample_size} topics...")
            topic_list = self.sampler.get_all_topics_flat(sample_size)

        print(f"Comparing {len(topic_list)} topics...")

        # Process each topic
        for category, topic in tqdm(topic_list, desc="Processing topics"):
            try:
                result = self._compare_topic(topic, category)
                if result:
                    self.results.append(result)
            except Exception as e:
                print(f"Error processing '{topic}': {e}")
                continue

        print(f"\nSuccessfully compared {len(self.results)} topics.")

    def _compare_topic(self, topic: str, category: Optional[str]) -> Optional[ComparisonResult]:
        """
        Compare a single topic between Grokipedia and Wikipedia.

        Args:
            topic: Topic to compare
            category: Category of the topic

        Returns:
            ComparisonResult or None if failed
        """
        # Fetch from Wikipedia
        wiki_page = self.wikipedia_scraper.fetch_and_parse(topic)
        if not wiki_page:
            print(f"  Failed to fetch Wikipedia page for '{topic}'")
            return None

        # Fetch from Grokipedia
        grok_page = self.grokipedia_scraper.fetch_and_parse(topic)
        if not grok_page:
            print(f"  Failed to fetch Grokipedia page for '{topic}'")
            return None

        # Compare the pages
        result = self.comparator.compare(grok_page, wiki_page)

        # Add category metadata
        if category:
            result.grokipedia_page.metadata['category'] = category
            result.wikipedia_page.metadata['category'] = category

        return result

    def save_results(self, output_path: str = "data/processed/comparison_results.json"):
        """
        Save comparison results to JSON file.

        Args:
            output_path: Path to save results
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = []
        for result in self.results:
            data.append({
                'topic': result.topic,
                'text_similarity': result.text_similarity,
                'similarity_category': result.similarity_category,
                'word_count_diff': result.word_count_diff,
                'citation_diff': result.citation_diff,
                'section_overlap': result.section_overlap,
                'key_differences': result.key_differences,
                'timestamp': result.timestamp.isoformat()
            })

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"Results saved to: {output_file}")

    def generate_reports(self):
        """Generate all reports from comparison results"""
        if not self.results:
            print("No results to generate reports from.")
            return

        print("\nGenerating reports...")

        # Summary report
        self.report_generator.generate_summary_report(self.results)

        # Detailed reports for interesting cases
        # Most similar
        most_similar = max(self.results, key=lambda r: r.text_similarity)
        print(f"Generating detailed report for most similar: {most_similar.topic}")
        self.report_generator.generate_detailed_report(most_similar)

        # Most different
        most_different = min(self.results, key=lambda r: r.text_similarity)
        print(f"Generating detailed report for most different: {most_different.topic}")
        self.report_generator.generate_detailed_report(most_different)

        # JSON export
        self.report_generator.export_json(self.results)

        print("\nAll reports generated successfully!")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Compare Grokipedia and Wikipedia pages"
    )

    parser.add_argument(
        '-n', '--num-samples',
        type=int,
        default=10,
        help='Number of topics to sample (default: 10)'
    )

    parser.add_argument(
        '-t', '--topics',
        nargs='+',
        help='Specific topics to compare (space-separated)'
    )

    parser.add_argument(
        '-c', '--config',
        default='config/sampling_config.yaml',
        help='Path to configuration file'
    )

    parser.add_argument(
        '--no-reports',
        action='store_true',
        help='Skip report generation'
    )

    parser.add_argument(
        '-o', '--output',
        default='data/processed/comparison_results.json',
        help='Output file for results'
    )

    args = parser.parse_args()

    # Create orchestrator
    orchestrator = ComparisonOrchestrator(config_path=args.config)

    try:
        # Run comparison
        orchestrator.run_comparison(
            sample_size=args.num_samples,
            topics=args.topics
        )

        # Save results
        orchestrator.save_results(args.output)

        # Generate reports
        if not args.no_reports:
            orchestrator.generate_reports()

        print("\n✓ Comparison complete!")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
