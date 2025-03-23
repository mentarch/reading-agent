#!/usr/bin/env python3
"""
Utility script to display tracked articles
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from src.utils.article_tracker import ArticleTracker
    from src.utils.config_loader import load_config
except ImportError:
    from utils.article_tracker import ArticleTracker
    from utils.config_loader import load_config

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='View tracked articles')
    parser.add_argument('--limit', type=int, default=10, help='Limit number of articles to show')
    parser.add_argument('--source', type=str, help='Filter by source')
    parser.add_argument('--format', choices=['text', 'json'], default='text', help='Output format')
    return parser.parse_args()

def format_date(date_str):
    """Format ISO date string to readable format"""
    try:
        dt = datetime.fromisoformat(date_str)
        return dt.strftime('%Y-%m-%d %H:%M')
    except (ValueError, TypeError):
        return date_str

def main():
    """Main function"""
    args = parse_args()
    
    # Load config to get storage path
    config = load_config()
    storage_path = config.get('app', {}).get('storage_path', './data')
    
    # Initialize tracker
    tracker = ArticleTracker(storage_path)
    
    # Get processed articles
    articles = tracker.get_processed_articles(args.limit, args.source)
    
    if not articles:
        print("No tracked articles found.")
        return 0
    
    if args.format == 'json':
        # Output as JSON
        print(json.dumps(articles, indent=2))
    else:
        # Output as text
        print(f"\nTracked Articles ({len(articles)}):")
        print("=" * 80)
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', 'Unknown')
            source = article.get('source', 'Unknown')
            date = format_date(article.get('processed_date', ''))
            summary = article.get('summary', 'No summary available.')
            url = article.get('url', '')
            
            print(f"{i}. {title}")
            print(f"   Source: {source}")
            print(f"   Processed: {date}")
            
            if url:
                print(f"   URL: {url}")
                
            print(f"   Summary: {summary[:200]}..." if len(summary) > 200 else f"   Summary: {summary}")
            print("-" * 80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 