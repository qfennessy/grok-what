# Grok-What: Grokipedia vs Wikipedia Comparison Framework

A comprehensive framework for systematically comparing [Grokipedia](https://grokipedia.com/) (xAI's Wikipedia clone) with Wikipedia to identify similarities, differences, and potential biases.

## Overview

This project implements a multi-faceted approach to analyze and compare content between Grokipedia and Wikipedia across various dimensions:

- **Content Analysis**: Factual accuracy, completeness, recency, and text similarity
- **Structural Analysis**: Citations, sections, organization, and media elements
- **Quality Metrics**: Readability, citation density, and complexity
- **Bias Detection**: Neutrality, sentiment, and loaded language analysis

## Features

### 🎯 Stratified Sampling
- Samples pages across multiple categories (popular, controversial, scientific, recent events, niche topics)
- Configurable sampling weights and strategies
- Support for custom topic lists

### 🔍 Web Scraping
- Robust scrapers for both Wikipedia and Grokipedia
- Rate limiting and retry logic
- Comprehensive content extraction (text, citations, sections, infoboxes, images)

### 📊 Comparison Engine
- Text similarity analysis using multiple algorithms
- Levenshtein distance calculation
- Section-by-section comparison
- Citation and structural analysis

### 📈 Metrics & Analysis
- Quality metrics (readability, citation density, complexity)
- Bias indicators (sentiment, subjectivity, loaded language)
- Temporal analysis (last modified dates)

### 📋 Reporting
- Summary reports with overall statistics
- Detailed page-by-page comparisons
- JSON export for further analysis
- Interactive visualizations

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/grok-what.git
cd grok-what
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Download spaCy language model for advanced NLP:
```bash
python -m spacy download en_core_web_sm
```

## Usage

### Quick Start

Compare 10 randomly sampled topics:
```bash
python main.py
```

### Custom Sample Size

Compare 50 topics:
```bash
python main.py -n 50
```

### Compare Specific Topics

```bash
python main.py -t "Python (programming language)" "Climate change" "Artificial intelligence"
```

### Advanced Usage

```bash
# Use custom configuration
python main.py -c config/my_config.yaml -n 100

# Skip report generation (only save raw results)
python main.py -n 20 --no-reports

# Custom output path
python main.py -n 30 -o results/my_comparison.json
```

## Project Structure

```
grok-what/
├── config/
│   └── sampling_config.yaml      # Sampling strategy configuration
├── src/
│   ├── samplers/                 # Topic sampling strategies
│   │   └── topic_sampler.py
│   ├── scrapers/                 # Web scrapers
│   │   ├── base_scraper.py
│   │   ├── wikipedia_scraper.py
│   │   └── grokipedia_scraper.py
│   ├── comparators/              # Comparison engine
│   │   └── page_comparator.py
│   ├── analyzers/                # Metrics calculation
│   │   └── metrics_analyzer.py
│   └── visualizers/              # Report generation
│       └── report_generator.py
├── tests/                        # Unit tests
├── data/
│   ├── raw/                      # Raw scraped data
│   ├── processed/                # Processed comparison results
│   └── reports/                  # Generated reports
├── main.py                       # Main orchestrator
├── requirements.txt
└── README.md
```

## Configuration

The sampling strategy is configured via `config/sampling_config.yaml`:

### Sampling Categories

- **Popular Pages** (25%): High-traffic general interest topics
- **Controversial** (20%): Political and polarizing subjects
- **Scientific/Technical** (20%): STEM topics
- **Recent Events** (15%): Current affairs and recent developments
- **Niche Topics** (10%): Obscure or specialized subjects
- **Random Sample** (10%): Truly random articles

### Comparison Metrics

Configure which metrics to calculate:
- Content: text similarity, semantic similarity, completeness
- Structural: citations, sections, infoboxes, media
- Quality: readability, citation density, recency
- Bias: sentiment, subjectivity, loaded language

## Output

### Reports

After running a comparison, you'll find several reports in `data/reports/`:

1. **Summary Report** (`summary_report_TIMESTAMP.txt`):
   - Overall statistics across all compared pages
   - Similarity distribution
   - Content analysis
   - Notable differences

2. **Detailed Reports** (`detailed_TOPIC_TIMESTAMP.txt`):
   - In-depth comparison for specific pages
   - Section-by-section analysis
   - Text diff samples
   - Quality and bias metrics

3. **JSON Export** (`comparison_results_TIMESTAMP.json`):
   - Machine-readable format
   - All comparison metrics
   - Suitable for further analysis or visualization

### Sample Output

```
================================================================================
GROKIPEDIA VS WIKIPEDIA COMPARISON REPORT
================================================================================
Generated: 2024-10-31 12:00:00
Total Pages Analyzed: 50
================================================================================

## OVERALL STATISTICS

Average Similarity: 67.45%
High Similarity: 15 pages
Medium Similarity: 25 pages
Low Similarity: 10 pages
Average Word Count Difference: 342 words

## SIMILARITY DISTRIBUTION

Similarity Distribution (0.0 to 1.0):
  0.0-0.1: █ (1)
  0.1-0.2: ██ (2)
  0.2-0.3: ███ (3)
  0.3-0.4: ████ (4)
  0.4-0.5: █████ (5)
  0.5-0.6: ███████ (7)
  0.6-0.7: █████████ (9)
  0.7-0.8: ████████████ (12)
  0.8-0.9: █████ (5)
  0.9-1.0: ██ (2)
```

## Methodology

### Sampling Approach

1. **Stratified Sampling**: Ensures representation across different topic types
2. **Category Weighting**: Balanced coverage of popular, controversial, and niche topics
3. **Reproducibility**: Seeded random sampling for consistent results

### Comparison Dimensions

#### Content Analysis
- **Text Similarity**: SequenceMatcher ratio and diff-match-patch algorithms
- **Levenshtein Distance**: Character-level edit distance
- **Semantic Similarity**: (Optional) Using sentence transformers

#### Structural Analysis
- **Section Comparison**: Jaccard similarity of section titles
- **Citation Analysis**: Count and density of references
- **Media Elements**: Images, tables, infoboxes

#### Quality Metrics
- **Readability**: Flesch Reading Ease score
- **Citation Density**: References per 1000 words
- **Complexity**: Based on word and sentence length

#### Bias Detection
- **Sentiment Polarity**: Positive/negative language
- **Subjectivity Score**: Objective vs subjective content
- **Loaded Language**: Detection of emotionally charged words
- **POV Indicators**: First-person usage, hedge words

## Example Use Cases

### 1. Fact-Check a Controversial Topic

```python
from src.scrapers import WikipediaScraper, GrokipediaScraper
from src.comparators import PageComparator

topic = "Climate change"
wiki_scraper = WikipediaScraper()
grok_scraper = GrokipediaScraper()
comparator = PageComparator()

wiki_page = wiki_scraper.fetch_and_parse(topic)
grok_page = grok_scraper.fetch_and_parse(topic)

result = comparator.compare(grok_page, wiki_page)
print(f"Similarity: {result.text_similarity:.2%}")
print(f"Key differences: {result.key_differences}")
```

### 2. Analyze Citation Patterns

```python
from main import ComparisonOrchestrator

orchestrator = ComparisonOrchestrator()
orchestrator.run_comparison(sample_size=100)

# Analyze citation differences
for result in orchestrator.results:
    if abs(result.citation_diff) > 10:
        print(f"{result.topic}: {result.citation_diff} citation difference")
```

### 3. Custom Sampling Strategy

```python
from src.samplers import TopicSampler

sampler = TopicSampler()

# Add custom topics
custom_topics = [
    "Quantum computing",
    "CRISPR",
    "Large language models"
]

for topic in custom_topics:
    sampler.add_custom_topic(topic)

# Export sampling plan
sampler.export_sample_plan("my_sample_plan.txt", total_size=50)
```

## Ethical Considerations

- **Respect robots.txt**: Rate limiting and respectful scraping
- **Attribution**: Proper source attribution in reports
- **Objectivity**: Presenting findings without cherry-picking
- **Context**: Understanding that AI-generated content may have different editorial standards

## Limitations

1. **Content Understanding**: Text similarity doesn't guarantee factual accuracy
2. **Dynamic Content**: Grokipedia structure may change over time
3. **Language**: Currently supports English Wikipedia only
4. **Scale**: Large-scale comparisons may take considerable time

## Future Enhancements

- [ ] Semantic similarity using transformer models
- [ ] Fact-checking integration with external APIs
- [ ] Interactive web dashboard for visualizations
- [ ] Multi-language support
- [ ] Real-time monitoring of page changes
- [ ] Machine learning-based bias detection
- [ ] Citation quality assessment
- [ ] Image comparison capabilities

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Wikipedia](https://www.wikipedia.org/) - The free encyclopedia
- [Grokipedia](https://grokipedia.com/) - xAI's knowledge platform
- diff-match-patch library
- BeautifulSoup for HTML parsing

## Contact

For questions, issues, or suggestions, please open an issue on GitHub.

---

**Disclaimer**: This is an independent research project. It is not affiliated with or endorsed by Wikipedia, xAI, or Grokipedia.
