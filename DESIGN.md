# Design Document: Grokipedia vs Wikipedia Comparison Framework

## Executive Summary

This framework provides a systematic approach to comparing content between Grokipedia (xAI's Wikipedia clone) and Wikipedia. The system employs stratified sampling, multi-dimensional comparison metrics, and comprehensive reporting to identify similarities, differences, and potential biases.

## Architectural Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      Main Orchestrator                          │
│                         (main.py)                               │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─────────────────────────────────────────────────────┐
             │                                                     │
             ▼                                                     ▼
┌────────────────────────┐                        ┌────────────────────────┐
│   Topic Sampler        │                        │   Web Scrapers         │
│   ─────────────        │                        │   ────────────         │
│   - Stratified         │                        │   - Wikipedia          │
│   - Weighted           │                        │   - Grokipedia         │
│   - Reproducible       │                        │   - Rate limiting      │
└────────────────────────┘                        └───────────┬────────────┘
                                                              │
                                                              ▼
                                                  ┌────────────────────────┐
                                                  │   PageContent          │
                                                  │   ────────────         │
                                                  │   - Structured data    │
                                                  └───────────┬────────────┘
                                                              │
                                                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          Comparator Engine                             │
│   ──────────────────────────────────────────────────────────────────   │
│   - Text similarity (SequenceMatcher, diff-match-patch)                │
│   - Structural analysis (sections, citations, media)                   │
│   - Diff generation                                                    │
└───────────────────────────────┬────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌────────────────────────┐        ┌────────────────────────┐
│   Metrics Analyzer     │        │   Report Generator     │
│   ──────────────       │        │   ────────────         │
│   - Quality metrics    │        │   - Summary reports    │
│   - Bias detection     │        │   - Detailed reports   │
│   - Readability        │        │   - JSON export        │
└────────────────────────┘        └────────────────────────┘
```

## Design Principles

### 1. Modularity
Each component (sampler, scraper, comparator, analyzer) is independently testable and reusable. Components communicate through well-defined data structures (PageContent, ComparisonResult).

### 2. Configurability
The sampling strategy, comparison metrics, and thresholds are externalized to YAML configuration files, allowing easy adjustment without code changes.

### 3. Extensibility
New scrapers, metrics, or comparison algorithms can be added by extending base classes without modifying existing code.

### 4. Robustness
- Rate limiting prevents overwhelming target sites
- Retry logic handles transient failures
- Graceful degradation when data is missing
- Comprehensive error handling

### 5. Reproducibility
- Seeded random sampling ensures consistent results
- All configuration and parameters are versioned
- Sampling plans can be exported and re-executed

## Detailed Component Design

### 1. Topic Sampler (src/samplers/topic_sampler.py)

**Purpose**: Select representative topics for comparison using stratified sampling.

**Sampling Strategy**:
```
Total Sample = Σ (Category Weight × Total Sample Size)

Categories:
- Popular Pages (25%): General interest, high traffic
- Controversial (20%): Political, polarizing subjects
- Scientific/Technical (20%): STEM topics
- Recent Events (15%): Current affairs
- Niche Topics (10%): Obscure subjects
- Random (10%): True random selection
```

**Key Features**:
- Weighted stratified sampling
- Reproducible with seed
- Support for custom topics
- Exportable sampling plans

**Configuration**: `config/sampling_config.yaml`

### 2. Web Scrapers (src/scrapers/)

#### Base Scraper (base_scraper.py)

Abstract base class providing common functionality:
- Rate limiting (default: 2 seconds between requests)
- Retry logic with exponential backoff (max 3 retries)
- Request timeout (30 seconds)
- User-Agent headers

#### Wikipedia Scraper (wikipedia_scraper.py)

**Data Sources**:
- MediaWiki API for structured data
- HTML parsing for detailed content

**Extracted Elements**:
```python
PageContent {
    title: str
    url: str
    text_content: str
    sections: Dict[str, str]
    citations: List[Dict]
    infobox: Optional[Dict]
    images: List[str]
    external_links: List[str]
    categories: List[str]
    last_modified: Optional[datetime]
    word_count: int
}
```

#### Grokipedia Scraper (grokipedia_scraper.py)

**Adaptive Parsing**:
- Multiple selector patterns (handles structure variations)
- Graceful fallbacks when elements missing
- Relative URL resolution
- Robust date parsing

### 3. Comparison Engine (src/comparators/page_comparator.py)

#### Comparison Dimensions

**Content Analysis**:
```
Text Similarity = SequenceMatcher.ratio(text1, text2)
Levenshtein Distance = edit_distance(text1[:10k], text2[:10k])
Section Overlap = Jaccard(sections1, sections2)
```

**Structural Metrics**:
- Word count difference (absolute and percentage)
- Citation count difference
- Infobox presence
- External links count
- Section coverage

**Diff Generation**:
Uses Google's diff-match-patch for semantic diffs:
- Equal segments (unchanged)
- Insert segments (Grokipedia only)
- Delete segments (Wikipedia only)

#### Similarity Categorization

```
High:   similarity >= 0.85
Medium: 0.60 <= similarity < 0.85
Low:    similarity < 0.60
```

### 4. Metrics Analyzer (src/analyzers/metrics_analyzer.py)

#### Quality Metrics

**Readability Score** (Flesch Reading Ease):
```
Score = 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)

Interpretation:
90-100: Very Easy
60-70:  Standard
0-30:   Very Difficult
```

**Citation Density**:
```
Density = (citation_count / word_count) * 1000
Target: 5+ citations per 1000 words for quality content
```

**Complexity Score** (0-1):
```
Word Complexity = min(avg_word_length / 10, 1.0)
Sentence Complexity = min(avg_sentence_length / 30, 1.0)
Overall = (Word + Sentence) / 2
```

#### Bias Metrics

**Loaded Language Detection**:
- Maintains lexicon of emotionally charged words
- Counts occurrences in text
- Examples: "obviously", "notorious", "shocking"

**POV Indicators**:
- First-person pronouns (I, we, our)
- Hedge words ("some say", "allegedly")
- Indicates subjective or weasel wording

**Sentiment Polarity** (-1 to +1):
- Basic positive/negative word counting
- Normalized by total sentiment words
- For production: use proper sentiment analysis libraries

**Subjectivity Score** (0-1):
```
Subjectivity = min((loaded_words + first_person + hedges) / total_words * 10, 1.0)
```

### 5. Report Generator (src/visualizers/report_generator.py)

#### Report Types

**1. Summary Report**
- Overall statistics (avg similarity, distributions)
- Content analysis (length, citations)
- Notable differences
- Top 10 most/least similar pages

**2. Detailed Report** (per page)
- Complete comparison metrics
- Section-by-section analysis
- Text diff samples
- Quality and bias metrics

**3. JSON Export**
- Machine-readable format
- All metrics included
- Timestamped
- For further analysis (ML, visualization)

#### Visualization Elements

**Similarity Distribution Histogram**:
```
0.0-0.1: █ (1)
0.1-0.2: ██ (2)
...
0.9-1.0: █████ (5)
```

**Metrics Tables**:
```
Metric              Grokipedia    Wikipedia    Difference
─────────────────────────────────────────────────────────
Word Count          5,432         6,123        -691
Citations           42            38           +4
External Links      15            23           -8
```

## Data Flow

### Complete Comparison Pipeline

```
1. Sampling Phase
   ├─ Load configuration
   ├─ Generate stratified sample
   └─ Export sampling plan (optional)

2. Collection Phase (for each topic)
   ├─ Fetch Wikipedia page
   │  ├─ Rate limit check
   │  ├─ HTTP request
   │  ├─ Parse HTML
   │  └─ Extract PageContent
   │
   └─ Fetch Grokipedia page
      ├─ Rate limit check
      ├─ HTTP request
      ├─ Parse HTML (adaptive)
      └─ Extract PageContent

3. Comparison Phase
   ├─ Calculate text similarity
   ├─ Generate diff segments
   ├─ Analyze structure (sections, citations)
   ├─ Compare metadata
   └─ Produce ComparisonResult

4. Analysis Phase
   ├─ Calculate quality metrics
   ├─ Calculate bias metrics
   └─ Identify key differences

5. Reporting Phase
   ├─ Aggregate results
   ├─ Generate summary report
   ├─ Generate detailed reports (selected pages)
   └─ Export JSON
```

## Comparison Algorithms

### Text Similarity

**Algorithm**: SequenceMatcher (Python difflib)
- Based on longest contiguous matching subsequence
- Efficient for large texts
- Returns ratio: 2 * matches / (len1 + len2)

**Alternative**: Cosine similarity with TF-IDF
- Better for semantic similarity
- Requires preprocessing
- Planned for future enhancement

### Levenshtein Distance

**Purpose**: Character-level edit distance
**Limitation**: Limited to first 10k characters for performance
**Use Case**: Detecting minor textual variations

### Section Overlap (Jaccard Similarity)

```
J(A, B) = |A ∩ B| / |A ∪ B|

Example:
A = {Intro, History, Modern Era}
B = {Intro, History, References}
J(A, B) = 2 / 4 = 0.5
```

## Configuration Management

### Sampling Configuration (config/sampling_config.yaml)

```yaml
sampling:
  total_sample_size: 100
  random_seed: 42

  categories:
    popular_pages:
      weight: 0.25
      topics: [...]

    controversial:
      weight: 0.20
      topics: [...]

metrics:
  content: [text_similarity, semantic_similarity, ...]
  structural: [citations, sections, ...]
  quality: [readability, citation_density, ...]
  bias: [sentiment, subjectivity, ...]

scraping:
  rate_limit_delay: 2
  timeout: 30
  max_retries: 3

thresholds:
  high_similarity: 0.85
  medium_similarity: 0.60
  citation_density_threshold: 5
```

## Performance Considerations

### Scalability

**Current Capacity**:
- 100 pages: ~30-40 minutes (with 2s rate limit)
- Memory: <500MB for 100 pages
- Disk: ~50MB for reports

**Bottlenecks**:
- Network I/O (mitigated by rate limiting)
- HTML parsing (BeautifulSoup)
- Diff calculation (limited to 10k chars)

**Optimization Strategies**:
- Parallel scraping (respecting rate limits)
- Caching of PageContent
- Incremental comparison
- Async I/O

### Error Handling

**Retry Strategy**:
```python
for attempt in range(max_retries):
    try:
        fetch_page()
        break
    except NetworkError:
        wait(2 ** attempt)  # Exponential backoff
```

**Graceful Degradation**:
- Missing sections → empty dict
- No citations → empty list
- Parse failure → skip page, log error

## Security & Ethics

### Rate Limiting
- Default: 2 seconds between requests
- Respects target site load
- Prevents accidental DoS

### User-Agent
```
Mozilla/5.0 (Research Project) GrokipediaComparison/1.0
```
- Transparent identification
- Allows site administrators to contact/block if needed

### robots.txt Compliance
- Currently not implemented (TODO)
- Should check before scraping
- Planned enhancement

### Data Privacy
- No personal data collected
- Only public content
- No authentication required

## Future Enhancements

### Phase 2: Advanced NLP
- [ ] Semantic similarity (sentence-transformers)
- [ ] Named Entity Recognition (spaCy)
- [ ] Fact extraction and verification
- [ ] Topic modeling

### Phase 3: Fact-Checking
- [ ] Integration with fact-check APIs (Google Fact Check)
- [ ] Cross-reference with authoritative sources
- [ ] Confidence scoring for claims

### Phase 4: Visualization Dashboard
- [ ] Interactive web interface (React/Vue)
- [ ] Real-time comparison
- [ ] Heatmaps, charts, graphs
- [ ] Export to PDF

### Phase 5: Monitoring
- [ ] Scheduled comparisons
- [ ] Change detection
- [ ] Email alerts for significant differences
- [ ] Historical trend analysis

## Testing Strategy

### Unit Tests
- Component isolation
- Mock external dependencies
- Cover edge cases

**Example**:
```python
def test_text_similarity_identical():
    comparator = PageComparator()
    assert comparator._calculate_text_similarity("test", "test") == 1.0

def test_section_overlap_empty():
    comparator = PageComparator()
    assert comparator._calculate_section_overlap({}, {}) == 0.0
```

### Integration Tests
- Full pipeline execution
- Real scraping (with mocks for external calls)
- Report generation

### End-to-End Tests
- Small sample comparisons
- Verify report output
- Check JSON validity

## Deployment

### Local Development
```bash
python main.py -n 10
```

### Production Run
```bash
# Large-scale comparison
python main.py -n 500 -o production_results.json

# Specific topics
python main.py -t "Topic 1" "Topic 2" "Topic 3"
```

### Scheduled Execution (cron)
```bash
# Daily at 2 AM
0 2 * * * cd /path/to/grok-what && python main.py -n 100 >> logs/daily.log 2>&1
```

## Limitations & Caveats

1. **Text Similarity ≠ Factual Accuracy**
   - High similarity doesn't mean both are correct
   - Low similarity doesn't mean either is wrong

2. **Grokipedia Structure Unknown**
   - Adaptive parsing may miss elements
   - Future changes may break scraper

3. **Bias Detection is Heuristic**
   - Not definitive proof of bias
   - Requires human interpretation

4. **Single Language**
   - Currently English only
   - Multi-language support requires significant changes

5. **Snapshot Comparison**
   - Pages change over time
   - Comparison valid only at execution time

## Conclusion

This framework provides a systematic, reproducible approach to comparing Grokipedia and Wikipedia. By combining multiple comparison dimensions—content, structure, quality, and bias—it offers comprehensive insights into how these platforms differ. The modular architecture allows for easy extension and customization to suit various research needs.
