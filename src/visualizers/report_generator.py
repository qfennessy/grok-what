"""
Report generator for creating comparison reports
"""

import json
from typing import List, Dict
from pathlib import Path
from datetime import datetime
from collections import Counter

from ..comparators.page_comparator import ComparisonResult
from ..analyzers.metrics_analyzer import MetricsAnalyzer, QualityMetrics, BiasMetrics


class ReportGenerator:
    """
    Generates various types of reports from comparison results.
    """

    def __init__(self, output_dir: str = "data/reports"):
        """
        Initialize the report generator.

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.analyzer = MetricsAnalyzer()

    def generate_summary_report(self, results: List[ComparisonResult], output_file: str = None) -> str:
        """
        Generate a summary report from multiple comparison results.

        Args:
            results: List of ComparisonResult objects
            output_file: Optional output file path

        Returns:
            Report content as string
        """
        if not results:
            return "No comparison results to report."

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report_lines = []

        # Header
        report_lines.append("=" * 80)
        report_lines.append("GROKIPEDIA VS WIKIPEDIA COMPARISON REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {timestamp}")
        report_lines.append(f"Total Pages Analyzed: {len(results)}")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Overall statistics
        report_lines.append("## OVERALL STATISTICS")
        report_lines.append("")
        report_lines.extend(self._generate_overall_stats(results))
        report_lines.append("")

        # Similarity distribution
        report_lines.append("## SIMILARITY DISTRIBUTION")
        report_lines.append("")
        report_lines.extend(self._generate_similarity_distribution(results))
        report_lines.append("")

        # Content analysis
        report_lines.append("## CONTENT ANALYSIS")
        report_lines.append("")
        report_lines.extend(self._generate_content_analysis(results))
        report_lines.append("")

        # Notable differences
        report_lines.append("## NOTABLE DIFFERENCES")
        report_lines.append("")
        report_lines.extend(self._generate_notable_differences(results))
        report_lines.append("")

        # Category breakdown
        report_lines.append("## TOP 10 MOST SIMILAR PAGES")
        report_lines.append("")
        top_similar = sorted(results, key=lambda r: r.text_similarity, reverse=True)[:10]
        for i, result in enumerate(top_similar, 1):
            report_lines.append(f"{i}. {result.topic}: {result.text_similarity:.2%} similarity")
        report_lines.append("")

        report_lines.append("## TOP 10 MOST DIFFERENT PAGES")
        report_lines.append("")
        top_different = sorted(results, key=lambda r: r.text_similarity)[:10]
        for i, result in enumerate(top_different, 1):
            report_lines.append(f"{i}. {result.topic}: {result.text_similarity:.2%} similarity")
        report_lines.append("")

        # Footer
        report_lines.append("=" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("=" * 80)

        report_content = "\n".join(report_lines)

        # Save to file if specified
        if output_file:
            output_path = self.output_dir / output_file
        else:
            output_path = self.output_dir / f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"Report saved to: {output_path}")
        return report_content

    def generate_detailed_report(self, result: ComparisonResult, output_file: str = None) -> str:
        """
        Generate a detailed report for a single page comparison.

        Args:
            result: ComparisonResult object
            output_file: Optional output file path

        Returns:
            Report content as string
        """
        report_lines = []

        # Header
        report_lines.append("=" * 80)
        report_lines.append(f"DETAILED COMPARISON: {result.topic}")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")

        # Overview
        report_lines.append("## OVERVIEW")
        report_lines.append(f"Text Similarity: {result.text_similarity:.2%} ({result.similarity_category})")
        report_lines.append(f"Levenshtein Distance: {result.levenshtein_distance}")
        report_lines.append("")

        # Content metrics
        report_lines.append("## CONTENT METRICS")
        report_lines.append("")
        report_lines.append(f"{'Metric':<30} {'Grokipedia':<15} {'Wikipedia':<15} {'Difference':<15}")
        report_lines.append("-" * 75)
        report_lines.append(
            f"{'Word Count':<30} {result.grokipedia_page.word_count:<15} "
            f"{result.wikipedia_page.word_count:<15} {result.word_count_diff:<15}"
        )
        report_lines.append(
            f"{'Citations':<30} {result.citation_count_grokipedia:<15} "
            f"{result.citation_count_wikipedia:<15} {result.citation_diff:<15}"
        )
        report_lines.append(
            f"{'External Links':<30} {result.external_links_grokipedia:<15} "
            f"{result.external_links_wikipedia:<15} "
            f"{result.external_links_grokipedia - result.external_links_wikipedia:<15}"
        )
        report_lines.append(
            f"{'Has Infobox':<30} {str(result.has_infobox_grokipedia):<15} "
            f"{str(result.has_infobox_wikipedia):<15} {'':<15}"
        )
        report_lines.append("")

        # Section analysis
        report_lines.append("## SECTION ANALYSIS")
        report_lines.append(f"Section Overlap: {result.section_overlap:.2%}")
        report_lines.append("")

        if result.unique_to_grokipedia:
            report_lines.append("Sections unique to Grokipedia:")
            for section in result.unique_to_grokipedia:
                report_lines.append(f"  - {section}")
            report_lines.append("")

        if result.unique_to_wikipedia:
            report_lines.append("Sections unique to Wikipedia:")
            for section in result.unique_to_wikipedia:
                report_lines.append(f"  - {section}")
            report_lines.append("")

        # Key differences
        report_lines.append("## KEY DIFFERENCES")
        report_lines.append("")
        for i, diff in enumerate(result.key_differences, 1):
            report_lines.append(f"{i}. {diff}")
        report_lines.append("")

        # Diff segments (show first 10)
        report_lines.append("## TEXT DIFFERENCES (Sample)")
        report_lines.append("")
        for i, segment in enumerate(result.diff_segments[:10], 1):
            if segment.type != 'equal':
                report_lines.append(f"Diff #{i} ({segment.type}):")
                if segment.grokipedia_text:
                    report_lines.append(f"  Grokipedia: {segment.grokipedia_text[:200]}...")
                if segment.wikipedia_text:
                    report_lines.append(f"  Wikipedia: {segment.wikipedia_text[:200]}...")
                report_lines.append("")

        report_lines.append("=" * 80)

        report_content = "\n".join(report_lines)

        # Save to file if specified
        if output_file:
            output_path = self.output_dir / output_file
        else:
            safe_topic = "".join(c if c.isalnum() else "_" for c in result.topic)[:50]
            output_path = self.output_dir / f"detailed_{safe_topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"Detailed report saved to: {output_path}")
        return report_content

    def export_json(self, results: List[ComparisonResult], output_file: str = None) -> str:
        """
        Export comparison results to JSON format.

        Args:
            results: List of ComparisonResult objects
            output_file: Optional output file path

        Returns:
            Path to exported file
        """
        data = []

        for result in results:
            data.append({
                'topic': result.topic,
                'text_similarity': result.text_similarity,
                'similarity_category': result.similarity_category,
                'word_count_grokipedia': result.grokipedia_page.word_count,
                'word_count_wikipedia': result.wikipedia_page.word_count,
                'word_count_diff': result.word_count_diff,
                'word_count_diff_pct': result.word_count_diff_pct,
                'citation_count_grokipedia': result.citation_count_grokipedia,
                'citation_count_wikipedia': result.citation_count_wikipedia,
                'section_overlap': result.section_overlap,
                'unique_to_grokipedia': result.unique_to_grokipedia,
                'unique_to_wikipedia': result.unique_to_wikipedia,
                'key_differences': result.key_differences,
                'timestamp': result.timestamp.isoformat()
            })

        if output_file:
            output_path = self.output_dir / output_file
        else:
            output_path = self.output_dir / f"comparison_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"JSON export saved to: {output_path}")
        return str(output_path)

    def _generate_overall_stats(self, results: List[ComparisonResult]) -> List[str]:
        """Generate overall statistics"""
        lines = []

        avg_similarity = sum(r.text_similarity for r in results) / len(results)
        lines.append(f"Average Similarity: {avg_similarity:.2%}")

        similarity_categories = Counter(r.similarity_category for r in results)
        lines.append(f"High Similarity: {similarity_categories.get('high', 0)} pages")
        lines.append(f"Medium Similarity: {similarity_categories.get('medium', 0)} pages")
        lines.append(f"Low Similarity: {similarity_categories.get('low', 0)} pages")

        avg_word_diff = sum(abs(r.word_count_diff) for r in results) / len(results)
        lines.append(f"Average Word Count Difference: {avg_word_diff:.0f} words")

        return lines

    def _generate_similarity_distribution(self, results: List[ComparisonResult]) -> List[str]:
        """Generate similarity distribution"""
        lines = []

        # Create histogram buckets
        buckets = [0] * 10
        for result in results:
            bucket = min(int(result.text_similarity * 10), 9)
            buckets[bucket] += 1

        lines.append("Similarity Distribution (0.0 to 1.0):")
        for i, count in enumerate(buckets):
            bar = "█" * count
            lines.append(f"  {i/10:.1f}-{(i+1)/10:.1f}: {bar} ({count})")

        return lines

    def _generate_content_analysis(self, results: List[ComparisonResult]) -> List[str]:
        """Generate content analysis"""
        lines = []

        longer_on_grok = sum(1 for r in results if r.word_count_diff > 0)
        longer_on_wiki = sum(1 for r in results if r.word_count_diff < 0)

        lines.append(f"Pages longer on Grokipedia: {longer_on_grok}")
        lines.append(f"Pages longer on Wikipedia: {longer_on_wiki}")

        more_citations_grok = sum(1 for r in results if r.citation_diff > 0)
        more_citations_wiki = sum(1 for r in results if r.citation_diff < 0)

        lines.append(f"Pages with more citations on Grokipedia: {more_citations_grok}")
        lines.append(f"Pages with more citations on Wikipedia: {more_citations_wiki}")

        return lines

    def _generate_notable_differences(self, results: List[ComparisonResult]) -> List[str]:
        """Generate notable differences"""
        lines = []

        # Find pages with biggest word count differences
        biggest_diff = max(results, key=lambda r: abs(r.word_count_diff_pct))
        lines.append(f"Biggest word count difference: {biggest_diff.topic}")
        lines.append(f"  {abs(biggest_diff.word_count_diff_pct):.1f}% difference")

        # Find pages with most unique sections
        most_unique_grok = max(results, key=lambda r: len(r.unique_to_grokipedia))
        if most_unique_grok.unique_to_grokipedia:
            lines.append(f"Most unique sections on Grokipedia: {most_unique_grok.topic}")
            lines.append(f"  {len(most_unique_grok.unique_to_grokipedia)} unique sections")

        most_unique_wiki = max(results, key=lambda r: len(r.unique_to_wikipedia))
        if most_unique_wiki.unique_to_wikipedia:
            lines.append(f"Most unique sections on Wikipedia: {most_unique_wiki.topic}")
            lines.append(f"  {len(most_unique_wiki.unique_to_wikipedia)} unique sections")

        return lines
