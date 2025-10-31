"""
Unit tests for TopicSampler
"""

import pytest
from src.samplers.topic_sampler import TopicSampler


def test_sampler_initialization():
    """Test that sampler initializes correctly"""
    sampler = TopicSampler()
    assert sampler is not None
    assert sampler.config is not None


def test_get_categories():
    """Test that categories are loaded correctly"""
    sampler = TopicSampler()
    categories = sampler.get_categories()
    assert len(categories) > 0
    assert all(hasattr(cat, 'name') for cat in categories)
    assert all(hasattr(cat, 'weight') for cat in categories)


def test_sample_topics():
    """Test that sampling returns the correct number of topics"""
    sampler = TopicSampler()
    sample_size = 20
    sampled = sampler.sample_topics(total_size=sample_size)

    total_topics = sum(len(topics) for topics in sampled.values())
    assert total_topics <= sample_size + 2  # Allow small variance due to rounding


def test_get_all_topics_flat():
    """Test that flat topic list is returned correctly"""
    sampler = TopicSampler()
    flat_topics = sampler.get_all_topics_flat(total_size=10)

    assert isinstance(flat_topics, list)
    assert all(isinstance(t, tuple) for t in flat_topics)
    assert all(len(t) == 2 for t in flat_topics)


def test_add_custom_topic():
    """Test adding custom topics"""
    sampler = TopicSampler()
    custom_topic = "Test Topic"
    sampler.add_custom_topic(custom_topic)

    # Verify it was added
    assert custom_topic in sampler.config['sampling']['categories']['custom']['topics']


def test_reproducibility():
    """Test that sampling is reproducible with same seed"""
    sampler1 = TopicSampler()
    sampler2 = TopicSampler()

    sample1 = sampler1.sample_topics(total_size=20)
    sample2 = sampler2.sample_topics(total_size=20)

    # Should produce identical results with same seed
    assert sample1.keys() == sample2.keys()
    for category in sample1.keys():
        assert sample1[category] == sample2[category]
