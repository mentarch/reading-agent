"""
Test script for ArticleTracker functionality
"""

import os
import sys
import json
from datetime import datetime

# Ensure the project root is in the Python path for imports
sys.path.insert(0, os.path.abspath('.'))

from src.utils.article_tracker import ArticleTracker

def main():
    """
    Test the ArticleTracker with sample articles
    """
    print("Testing ArticleTracker functionality...")
    
    # Create a tracker instance
    tracker = ArticleTracker(storage_path="./data")
    
    # Create some sample articles
    sample_articles = [
        {
            "title": "Sample Article 1: Deep Learning in Computer Vision",
            "source": "Test",
            "url": "https://example.com/article1",
            "summary": "",
            "published": datetime.now().isoformat()
        },
        {
            "title": "Sample Article 2: Machine Vision Applications",
            "source": "Test",
            "url": "https://example.com/article2",
            "summary": "",
            "published": datetime.now().isoformat()
        },
        {
            "title": "Sample Article 3: Neural Networks for Image Recognition",
            "source": "Test",
            "url": "https://example.com/article3", 
            "summary": "",
            "published": datetime.now().isoformat()
        }
    ]
    
    # Mark the articles as processed
    for article in sample_articles:
        summary = f"Sample summary for {article['title']}"
        if tracker.is_processed(article):
            print(f"Article already processed: {article['title']}")
        else:
            tracker.mark_processed(article, summary)
            print(f"Marked as processed: {article['title']}")
    
    # Display all processed articles
    processed = tracker.get_processed_articles()
    print(f"\nTotal processed articles: {len(processed)}")
    for idx, article in enumerate(processed, 1):
        print(f"{idx}. {article['title']} (from {article['source']})")
        print(f"   Processed on: {article['processed_date']}")
        print(f"   Summary: {article['summary']}")
        print()
    
    # Test the clear older than functionality (but don't actually clear anything)
    print("\nNo articles will be cleared (setting days=1000)")
    cleared = tracker.clear_older_than(1000)
    print(f"Cleared {cleared} article(s)")
    
    print("\nArticleTracker test completed successfully!")

if __name__ == "__main__":
    main() 