"""
Topic Sampler for selecting representative pages from Grokipedia and Wikipedia
"""

import random
import yaml
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class SamplingCategory:
    """Represents a category of topics for sampling"""
    name: str
    weight: float
    topics: List[str]


class TopicSampler:
    """
    Implements stratified sampling strategy to select representative topics
    for comparison between Grokipedia and Wikipedia.
    """

    def __init__(self, config_path: str = "config/sampling_config.yaml"):
        """
        Initialize the topic sampler with configuration.

        Args:
            config_path: Path to the sampling configuration YAML file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.random_seed = self.config['sampling'].get('random_seed', 42)
        random.seed(self.random_seed)

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def get_categories(self) -> List[SamplingCategory]:
        """Extract sampling categories from configuration"""
        categories = []
        for name, data in self.config['sampling']['categories'].items():
            categories.append(SamplingCategory(
                name=name,
                weight=data['weight'],
                topics=data.get('topics', [])
            ))
        return categories

    def sample_topics(self, total_size: int = None) -> Dict[str, List[str]]:
        """
        Generate a stratified sample of topics across all categories.

        Args:
            total_size: Total number of topics to sample (default from config)

        Returns:
            Dictionary mapping category names to lists of sampled topics
        """
        if total_size is None:
            total_size = self.config['sampling']['total_sample_size']

        categories = self.get_categories()
        sampled_topics = {}

        for category in categories:
            # Calculate sample size for this category based on weight
            category_sample_size = int(total_size * category.weight)

            # Skip categories with no topics defined
            if not category.topics:
                continue

            # Sample topics (with replacement if needed)
            if len(category.topics) >= category_sample_size:
                sampled = random.sample(category.topics, category_sample_size)
            else:
                # If we need more samples than available, use all + random repeats
                sampled = category.topics + random.choices(
                    category.topics,
                    k=category_sample_size - len(category.topics)
                )

            sampled_topics[category.name] = sampled

        return sampled_topics

    def get_all_topics_flat(self, total_size: int = None) -> List[Tuple[str, str]]:
        """
        Get a flat list of all sampled topics with their categories.

        Args:
            total_size: Total number of topics to sample

        Returns:
            List of (category, topic) tuples
        """
        sampled = self.sample_topics(total_size)
        flat_list = []

        for category, topics in sampled.items():
            for topic in topics:
                flat_list.append((category, topic))

        return flat_list

    def get_topic_by_category(self, category_name: str) -> List[str]:
        """Get all topics for a specific category"""
        categories = self.config['sampling']['categories']
        return categories.get(category_name, {}).get('topics', [])

    def add_custom_topic(self, topic: str, category: str = "custom"):
        """
        Add a custom topic for comparison.

        Args:
            topic: The topic/page title to add
            category: Category to assign the topic to
        """
        if 'custom' not in self.config['sampling']['categories']:
            self.config['sampling']['categories']['custom'] = {
                'weight': 0.0,
                'topics': []
            }

        if topic not in self.config['sampling']['categories']['custom']['topics']:
            self.config['sampling']['categories']['custom']['topics'].append(topic)

    def export_sample_plan(self, output_path: str, total_size: int = None):
        """
        Export the sampling plan to a file for reproducibility.

        Args:
            output_path: Path to save the sampling plan
            total_size: Total sample size
        """
        sampled_topics = self.sample_topics(total_size)

        with open(output_path, 'w') as f:
            f.write("# Grokipedia vs Wikipedia Sampling Plan\n\n")
            f.write(f"Random Seed: {self.random_seed}\n")
            f.write(f"Total Sample Size: {sum(len(topics) for topics in sampled_topics.values())}\n\n")

            for category, topics in sampled_topics.items():
                f.write(f"\n## {category.replace('_', ' ').title()}\n")
                f.write(f"Count: {len(topics)}\n\n")
                for i, topic in enumerate(topics, 1):
                    f.write(f"{i}. {topic}\n")


if __name__ == "__main__":
    # Example usage
    sampler = TopicSampler()
    topics = sampler.sample_topics(total_size=50)

    print("Sampling Plan:")
    for category, topic_list in topics.items():
        print(f"\n{category}: {len(topic_list)} topics")
        for topic in topic_list[:3]:  # Show first 3
            print(f"  - {topic}")
