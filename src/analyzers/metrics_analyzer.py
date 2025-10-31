"""
Metrics analyzer for calculating quality and bias metrics
"""

from typing import Dict, List
from dataclasses import dataclass
import re


@dataclass
class QualityMetrics:
    """Quality metrics for a page"""
    readability_score: float = 0.0
    citation_density: float = 0.0  # Citations per 1000 words
    avg_sentence_length: float = 0.0
    complexity_score: float = 0.0


@dataclass
class BiasMetrics:
    """Bias indicators for a page"""
    sentiment_polarity: float = 0.0  # -1 (negative) to 1 (positive)
    subjectivity_score: float = 0.0  # 0 (objective) to 1 (subjective)
    loaded_language_count: int = 0
    first_person_count: int = 0
    hedge_words_count: int = 0


class MetricsAnalyzer:
    """
    Analyzes pages to calculate quality and bias metrics.
    """

    # Loaded language indicators (words that may indicate bias)
    LOADED_WORDS = [
        'obviously', 'clearly', 'undoubtedly', 'certainly', 'definitely',
        'notorious', 'infamous', 'brilliant', 'terrible', 'amazing',
        'incredible', 'outrageous', 'shocking', 'stunning', 'remarkable'
    ]

    # Hedge words (may indicate uncertainty or weasel words)
    HEDGE_WORDS = [
        'some say', 'many believe', 'it is said', 'allegedly', 'reportedly',
        'supposedly', 'arguably', 'possibly', 'perhaps', 'maybe',
        'some people', 'critics argue', 'supporters claim'
    ]

    # First person pronouns
    FIRST_PERSON = ['i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours']

    def __init__(self):
        pass

    def calculate_quality_metrics(self, text: str, citation_count: int) -> QualityMetrics:
        """
        Calculate quality metrics for text content.

        Args:
            text: Text content to analyze
            citation_count: Number of citations

        Returns:
            QualityMetrics object
        """
        metrics = QualityMetrics()

        if not text:
            return metrics

        # Calculate readability (Flesch Reading Ease approximation)
        metrics.readability_score = self._calculate_readability(text)

        # Calculate citation density
        word_count = len(text.split())
        if word_count > 0:
            metrics.citation_density = (citation_count / word_count) * 1000

        # Calculate average sentence length
        metrics.avg_sentence_length = self._calculate_avg_sentence_length(text)

        # Calculate complexity (based on avg word length and sentence length)
        metrics.complexity_score = self._calculate_complexity(text)

        return metrics

    def calculate_bias_metrics(self, text: str) -> BiasMetrics:
        """
        Calculate bias indicators for text content.

        Args:
            text: Text content to analyze

        Returns:
            BiasMetrics object
        """
        metrics = BiasMetrics()

        if not text:
            return metrics

        text_lower = text.lower()

        # Count loaded language
        metrics.loaded_language_count = sum(
            text_lower.count(word) for word in self.LOADED_WORDS
        )

        # Count first person usage
        words = text_lower.split()
        metrics.first_person_count = sum(
            words.count(pronoun) for pronoun in self.FIRST_PERSON
        )

        # Count hedge words
        metrics.hedge_words_count = sum(
            text_lower.count(phrase) for phrase in self.HEDGE_WORDS
        )

        # Simple sentiment polarity (very basic - count positive/negative words)
        metrics.sentiment_polarity = self._calculate_simple_sentiment(text_lower)

        # Subjectivity score (based on loaded language and first person usage)
        total_words = len(words)
        if total_words > 0:
            subjective_indicators = (
                metrics.loaded_language_count +
                metrics.first_person_count +
                metrics.hedge_words_count
            )
            metrics.subjectivity_score = min(subjective_indicators / total_words * 10, 1.0)

        return metrics

    def _calculate_readability(self, text: str) -> float:
        """
        Calculate Flesch Reading Ease score (approximation).

        Formula: 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)

        Returns:
            Readability score (0-100, higher is easier to read)
        """
        sentences = self._split_sentences(text)
        if not sentences:
            return 0.0

        words = text.split()
        total_words = len(words)
        total_sentences = len(sentences)

        if total_words == 0 or total_sentences == 0:
            return 0.0

        # Approximate syllables (very rough estimate)
        total_syllables = sum(self._count_syllables(word) for word in words)

        # Flesch Reading Ease formula
        score = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)

        return max(0.0, min(100.0, score))

    def _calculate_avg_sentence_length(self, text: str) -> float:
        """Calculate average sentence length in words"""
        sentences = self._split_sentences(text)
        if not sentences:
            return 0.0

        total_words = sum(len(sentence.split()) for sentence in sentences)
        return total_words / len(sentences)

    def _calculate_complexity(self, text: str) -> float:
        """
        Calculate text complexity score (0-1).

        Based on average word length and sentence length.
        """
        words = text.split()
        if not words:
            return 0.0

        avg_word_length = sum(len(word) for word in words) / len(words)
        avg_sentence_length = self._calculate_avg_sentence_length(text)

        # Normalize to 0-1 scale
        word_complexity = min(avg_word_length / 10, 1.0)  # 10+ chars is complex
        sentence_complexity = min(avg_sentence_length / 30, 1.0)  # 30+ words is complex

        return (word_complexity + sentence_complexity) / 2

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _count_syllables(self, word: str) -> int:
        """
        Approximate syllable count for a word.

        Very rough estimate based on vowel groups.
        """
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        previous_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel

        # Adjust for silent 'e'
        if word.endswith('e'):
            syllable_count -= 1

        # Every word has at least one syllable
        return max(1, syllable_count)

    def _calculate_simple_sentiment(self, text: str) -> float:
        """
        Calculate simple sentiment polarity (-1 to 1).

        This is a very basic implementation. For production, use a proper sentiment analysis library.
        """
        positive_words = [
            'good', 'great', 'excellent', 'positive', 'successful', 'beneficial',
            'important', 'significant', 'valuable', 'notable', 'remarkable',
            'innovative', 'leading', 'prominent', 'influential'
        ]

        negative_words = [
            'bad', 'poor', 'negative', 'failed', 'harmful', 'detrimental',
            'insignificant', 'minor', 'controversial', 'criticized', 'disputed',
            'questionable', 'problematic', 'flawed', 'inferior'
        ]

        positive_count = sum(text.count(word) for word in positive_words)
        negative_count = sum(text.count(word) for word in negative_words)

        total = positive_count + negative_count
        if total == 0:
            return 0.0

        return (positive_count - negative_count) / total

    def compare_metrics(self, metrics1: QualityMetrics, metrics2: QualityMetrics) -> Dict[str, float]:
        """
        Compare two quality metrics and return differences.

        Args:
            metrics1: First metrics (e.g., Grokipedia)
            metrics2: Second metrics (e.g., Wikipedia)

        Returns:
            Dictionary of metric differences
        """
        return {
            'readability_diff': metrics1.readability_score - metrics2.readability_score,
            'citation_density_diff': metrics1.citation_density - metrics2.citation_density,
            'complexity_diff': metrics1.complexity_score - metrics2.complexity_score,
            'sentence_length_diff': metrics1.avg_sentence_length - metrics2.avg_sentence_length
        }

    def compare_bias(self, bias1: BiasMetrics, bias2: BiasMetrics) -> Dict[str, float]:
        """
        Compare two bias metrics and return differences.

        Args:
            bias1: First bias metrics (e.g., Grokipedia)
            bias2: Second bias metrics (e.g., Wikipedia)

        Returns:
            Dictionary of bias differences
        """
        return {
            'sentiment_diff': bias1.sentiment_polarity - bias2.sentiment_polarity,
            'subjectivity_diff': bias1.subjectivity_score - bias2.subjectivity_score,
            'loaded_language_diff': bias1.loaded_language_count - bias2.loaded_language_count,
            'first_person_diff': bias1.first_person_count - bias2.first_person_count,
            'hedge_words_diff': bias1.hedge_words_count - bias2.hedge_words_count
        }
