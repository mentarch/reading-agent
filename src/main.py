#!/usr/bin/env python3
"""
Research Article Reader and Summarizer
Main application entry point
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime
from dotenv import load_dotenv

# Adjust Python path for imports to work both when run as module and as script
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import project modules
try:
    # Try relative imports first (when run as module)
    from utils.config_loader import load_config
    from utils.logger import setup_logger
    from utils.article_tracker import ArticleTracker
    from utils.article_filter import ArticleFilter
    from readers.reader_factory import create_readers
    from summarizers.summarizer import summarize_article
    from emailer.email_sender import send_email_digest
except ImportError:
    # Fall back to absolute imports (when run from project root)
    from src.utils.config_loader import load_config
    from src.utils.logger import setup_logger
    from src.utils.article_tracker import ArticleTracker
    from src.utils.article_filter import ArticleFilter
    from src.readers.reader_factory import create_readers
    from src.summarizers.summarizer import summarize_article
    from src.emailer.email_sender import send_email_digest

# Load environment variables but ignore proxy settings from .env file
# This prevents conflicts with system proxy configuration
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path=dotenv_path)

# Make sure proxy settings don't cause issues with OpenAI client
if 'HTTP_PROXY' in os.environ and os.environ['HTTP_PROXY'].startswith('#'):
    del os.environ['HTTP_PROXY']
if 'HTTPS_PROXY' in os.environ and os.environ['HTTPS_PROXY'].startswith('#'):
    del os.environ['HTTPS_PROXY']

def setup():
    """Initialize application components"""
    # Load configuration
    config = load_config()
    
    # Set up logging
    setup_logger(config.get('app', {}).get('log_level', 'info'))
    
    # Create data directory if it doesn't exist
    storage_path = config.get('app', {}).get('storage_path', './data')
    os.makedirs(storage_path, exist_ok=True)
    
    logging.info("Application initialized successfully")
    return config

def process_articles(config):
    """Main processing function to fetch, filter, summarize and store articles"""
    logging.info("Starting article processing")
    
    # Create readers for each source
    readers = create_readers(config.get('sources', []))
    
    # Topics to filter by
    topics = config.get('topics', [])
    logging.info(f"Filtering for topics: {', '.join(topics)}")
    
    # Initialize article tracker
    storage_path = config.get('app', {}).get('storage_path', './data')
    tracker = ArticleTracker(storage_path)

    # Initialize quality filter
    q_filter = ArticleFilter(config.get('quality_filter', {}))
    
    # Clear old tracked articles after 30 days (configurable)
    retention_days = config.get('app', {}).get('tracking_retention_days', 30)
    num_cleared = tracker.clear_older_than(retention_days)
    if num_cleared > 0:
        logging.info(f"Cleared {num_cleared} articles older than {retention_days} days")
    
    new_articles = []
    max_articles_to_process = config.get('app', {}).get('max_articles_to_process', 5)
    
    # Process each reader
    for reader in readers:
        try:
            articles = reader.fetch_articles()
            logging.info(f"Retrieved {len(articles)} articles from {reader.name}")
            
            # Filter articles by topic
            filtered_articles = reader.filter_by_topics(articles, topics)
            logging.info(f"Filtered to {len(filtered_articles)} relevant articles from {reader.name}")
            
            # Filter out already processed articles
            unprocessed_articles = []
            for article in filtered_articles:
                if not tracker.is_processed(article):
                    unprocessed_articles.append(article)

            logging.info(f"Found {len(unprocessed_articles)} new articles to process from {reader.name}")

            # Apply quality filter
            quality_articles = q_filter.filter_articles(unprocessed_articles)
            if len(quality_articles) < len(unprocessed_articles):
                logging.info(
                    f"Filtered out {len(unprocessed_articles) - len(quality_articles)} articles below quality threshold"
                )

            # Limit articles to process (take just the first few most relevant)
            articles_to_process = quality_articles[:max_articles_to_process]
            if len(quality_articles) > max_articles_to_process:
                logging.info(f"Limiting to {max_articles_to_process} articles for summarization from {reader.name}")
            
            # Summarize each article
            for article in articles_to_process:
                try:
                    # Pass the entire article object to the new summarize_article function
                    summary = summarize_article(
                        article, 
                        model=config.get('app', {}).get('openai_model', 'gpt-3.5-turbo'),
                        max_tokens=config.get('app', {}).get('max_summary_length', 150)
                    )
                    
                    # Add summary to article
                    article['summary'] = summary
                    
                    # Mark article as processed with its summary
                    tracker.mark_processed(article, summary)
                    
                    # Add to new articles list
                    new_articles.append(article)
                    
                    logging.info(f"Successfully summarized: {article.get('title', 'Unknown article')}")
                except Exception as e:
                    logging.error(f"Error summarizing article {article.get('title', 'Unknown')}: {str(e)}")
        
        except Exception as e:
            logging.error(f"Error processing source {reader.name}: {str(e)}")
    
    # Store and return new articles
    if new_articles:
        logging.info(f"Processed {len(new_articles)} new articles")
    else:
        logging.info("No new articles found")
        
    return new_articles

def send_digest_if_scheduled(config, articles):
    """Check if it's time to send a digest and send if necessary"""
    if not articles:
        logging.info("No articles to send in digest")
        return
        
    email_config = config.get('email', {})
    schedule_setting = email_config.get('schedule', 'daily')
    
    # For demo purposes, we'll just send the email immediately
    # In a real app, you'd implement proper scheduling here
    logging.info(f"Sending digest with {len(articles)} articles")
    
    try:
        send_email_digest(
            articles,
            email_config.get('subject_prefix', '[Research Update]'),
            email_config.get('format', 'html'),
            email_config.get('include_links', True),
            email_config.get('max_articles_per_email', 5)
        )
        logging.info("Email digest sent successfully")
    except Exception as e:
        logging.error(f"Failed to send email digest: {str(e)}")
        # Add more detailed error information to help with debugging
        if hasattr(e, 'smtp_error'):
            logging.error(f"SMTP error: {e.smtp_error}")
        if hasattr(e, 'errno'):
            logging.error(f"Error number: {e.errno}")

def run_scheduled_job():
    """Run the main processing job"""
    try:
        config = load_config()  # Reload config each time to pick up changes
        articles = process_articles(config)
        send_digest_if_scheduled(config, articles)
    except Exception as e:
        logging.error(f"Error in scheduled job: {str(e)}")

def main():
    """Main application entry point"""
    try:
        config = setup()
        
        # Schedule regular updates
        update_freq = config.get('app', {}).get('update_frequency', '6h')
        
        # For demonstration, run once immediately
        run_scheduled_job()
        
        # Then schedule future runs
        if update_freq.endswith('h'):
            hours = int(update_freq[:-1])
            schedule.every(hours).hours.do(run_scheduled_job)
        elif update_freq.endswith('m'):
            minutes = int(update_freq[:-1])
            schedule.every(minutes).minutes.do(run_scheduled_job)
        elif update_freq == 'daily':
            schedule.every().day.at("08:00").do(run_scheduled_job)
        else:
            logging.warning(f"Unknown update frequency: {update_freq}, defaulting to 6 hours")
            schedule.every(6).hours.do(run_scheduled_job)
        
        logging.info(f"Application scheduled to run every {update_freq}")
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    except KeyboardInterrupt:
        logging.info("Application terminated by user")
    except Exception as e:
        logging.error(f"Unhandled exception: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 