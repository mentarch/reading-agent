"""
Test script to check if an article is recognized as processed
"""

import os
import sys

# Ensure the project root is in the Python path for imports
sys.path.insert(0, os.path.abspath('.'))

from src.utils.article_tracker import ArticleTracker

def main():
    """
    Test if an article is recognized as processed
    """
    # Create a tracker instance
    tracker = ArticleTracker(storage_path='./data')

    # Check if sample articles are marked as processed
    samples = [
        {
            'url': 'https://example.com/article1',
            'title': 'Sample Article 1: Deep Learning in Computer Vision',
            'source': 'Test'
        },
        {
            'url': 'https://example.com/new_article',
            'title': 'New Article: Not Yet Processed',
            'source': 'Test'
        }
    ]
    
    for sample in samples:
        is_processed = tracker.is_processed(sample)
        print(f"Article: {sample['title']}")
        print(f"Is processed: {is_processed}")
        print()

if __name__ == "__main__":
    main() 