#!/usr/bin/env python3
"""
Research Article Reader and Summarizer
Main application entry point with async support
"""

import asyncio
import logging
import os
import sys
import time

import schedule
from dotenv import load_dotenv

# Adjust Python path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import project modules
try:
    from utils.article_tracker import ArticleTracker
    from utils.config_loader import load_config
    from utils.logger import setup_logger
    from readers.reader_factory import create_readers
    from summarizers.summarizer import summarize_article
    from emailer.email_sender import send_email_digest
except ImportError:
    from src.utils.article_tracker import ArticleTracker
    from src.utils.config_loader import load_config
    from src.utils.logger import setup_logger
    from src.readers.reader_factory import create_readers
    from src.summarizers.summarizer import summarize_article
    from src.emailer.email_sender import send_email_digest

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(dotenv_path=dotenv_path)


def setup() -> dict:
    """Initialize application components"""
    config = load_config()
    setup_logger(config.get("app", {}).get("log_level", "info"))

    storage_path = config.get("app", {}).get("storage_path", "./data")
    os.makedirs(storage_path, exist_ok=True)

    logging.info("Application initialized successfully")
    return config


async def fetch_all_articles(readers: list) -> dict[str, list[dict]]:
    """
    Fetch articles from all readers concurrently

    Args:
        readers: List of reader objects

    Returns:
        Dictionary mapping reader names to article lists
    """
    tasks = [reader.fetch_articles() for reader in readers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    articles_by_source = {}
    for reader, result in zip(readers, results):
        if isinstance(result, Exception):
            logging.error(f"Error fetching from {reader.name}: {result}")
            articles_by_source[reader.name] = []
        else:
            articles_by_source[reader.name] = result

    return articles_by_source


async def process_articles(config: dict) -> list[dict]:
    """Main processing function to fetch, filter, summarize and store articles"""
    logging.info("Starting article processing")

    readers = create_readers(config.get("sources", []))
    topics = config.get("topics", [])
    logging.info(f"Filtering for topics: {', '.join(topics)}")

    storage_path = config.get("app", {}).get("storage_path", "./data")
    tracker = ArticleTracker(storage_path)

    # Clear old tracked articles
    retention_days = config.get("app", {}).get("tracking_retention_days", 30)
    num_cleared = tracker.clear_older_than(retention_days)
    if num_cleared > 0:
        logging.info(f"Cleared {num_cleared} articles older than {retention_days} days")

    # Fetch from all sources concurrently
    articles_by_source = await fetch_all_articles(readers)

    new_articles = []
    max_articles = config.get("app", {}).get("max_articles_to_process", 5)
    model = config.get("app", {}).get("openai_model", "gpt-4o")
    max_tokens = config.get("app", {}).get("max_summary_length", 150)

    for reader in readers:
        articles = articles_by_source.get(reader.name, [])
        logging.info(f"Retrieved {len(articles)} articles from {reader.name}")

        # Filter by topic
        filtered = reader.filter_by_topics(articles, topics)
        logging.info(f"Filtered to {len(filtered)} relevant articles from {reader.name}")

        # Filter out already processed
        unprocessed = [a for a in filtered if not tracker.is_processed(a)]
        logging.info(f"Found {len(unprocessed)} new articles from {reader.name}")

        # Limit and process
        to_process = unprocessed[:max_articles]
        if len(unprocessed) > max_articles:
            logging.info(f"Limiting to {max_articles} articles from {reader.name}")

        for article in to_process:
            try:
                summary = summarize_article(article, model=model, max_tokens=max_tokens)
                article["summary"] = summary
                tracker.mark_processed(article, summary)
                new_articles.append(article)
                logging.info(f"Summarized: {article.get('title', 'Unknown')}")
            except Exception as e:
                logging.error(f"Error summarizing {article.get('title', 'Unknown')}: {e}")

    if new_articles:
        logging.info(f"Processed {len(new_articles)} new articles")
    else:
        logging.info("No new articles found")

    return new_articles


def send_digest_if_scheduled(config: dict, articles: list[dict]) -> None:
    """Send email digest if there are articles to send"""
    if not articles:
        logging.info("No articles to send in digest")
        return

    email_config = config.get("email", {})
    logging.info(f"Sending digest with {len(articles)} articles")

    try:
        send_email_digest(
            articles,
            email_config.get("subject_prefix", "[Research Update]"),
            email_config.get("format", "html"),
            email_config.get("include_links", True),
            email_config.get("max_articles_per_email", 5),
        )
        logging.info("Email digest sent successfully")
    except Exception as e:
        logging.error(f"Failed to send email digest: {e}")


def run_scheduled_job() -> None:
    """Run the main processing job"""
    try:
        config = load_config()
        articles = asyncio.run(process_articles(config))
        send_digest_if_scheduled(config, articles)
    except Exception as e:
        logging.error(f"Error in scheduled job: {e}")


def main() -> int:
    """Main application entry point"""
    try:
        config = setup()

        # Run once immediately
        run_scheduled_job()

        # Schedule future runs
        update_freq = config.get("app", {}).get("update_frequency", "6h")

        if update_freq.endswith("h"):
            hours = int(update_freq[:-1])
            schedule.every(hours).hours.do(run_scheduled_job)
        elif update_freq.endswith("m"):
            minutes = int(update_freq[:-1])
            schedule.every(minutes).minutes.do(run_scheduled_job)
        elif update_freq == "daily":
            schedule.every().day.at("08:00").do(run_scheduled_job)
        else:
            logging.warning(f"Unknown update frequency: {update_freq}, defaulting to 6 hours")
            schedule.every(6).hours.do(run_scheduled_job)

        logging.info(f"Application scheduled to run every {update_freq}")

        while True:
            schedule.run_pending()
            time.sleep(60)

    except KeyboardInterrupt:
        logging.info("Application terminated by user")
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
