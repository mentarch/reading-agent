"""
RSS reader implementation for fetching articles from RSS feeds asynchronously
"""

import asyncio
import logging
from datetime import datetime

import aiohttp
import feedparser
from bs4 import BeautifulSoup

from .base_reader import BaseReader


class RSSReader(BaseReader):
    """Async reader for RSS feeds like PubMed and arXiv"""

    def __init__(self, name: str, url: str, params: dict | None = None):
        """
        Initialize the RSS reader

        Args:
            name: Source name
            url: RSS feed URL
            params: Additional parameters for the RSS request
        """
        super().__init__(name, url)
        self.params = params or {}

    async def fetch_articles(self) -> list[dict]:
        """
        Fetch articles from RSS feed asynchronously

        Returns:
            List of article dictionaries
        """
        logging.info(f"Fetching articles from {self.name} RSS feed: {self.url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    content = await resp.text()

            # feedparser is synchronous but fast for parsing
            feed = feedparser.parse(content)

            if feed.get("bozo_exception"):
                logging.warning(f"Error parsing feed: {feed.bozo_exception}")

            if not feed.get("entries"):
                logging.warning(f"No entries found in RSS feed: {self.url}")
                return []

            # Fetch article contents concurrently
            articles = await self._process_entries(feed.entries)

            logging.info(f"Fetched {len(articles)} articles from {self.name}")
            return articles

        except asyncio.TimeoutError:
            logging.error(f"Timeout fetching RSS feed {self.url}")
            return []
        except Exception as e:
            logging.error(f"Error fetching RSS feed {self.url}: {e}")
            return []

    async def _process_entries(self, entries: list) -> list[dict]:
        """Process RSS entries and fetch full content concurrently"""
        articles = []
        fetch_tasks = []

        for entry in entries:
            try:
                article = {
                    "title": entry.get("title", "No Title"),
                    "url": entry.get("link", ""),
                    "source": self.name,
                    "content": "",
                    "authors": self._extract_authors(entry),
                    "published_date": self._extract_date(entry),
                }

                # Extract initial content from feed
                if "content" in entry:
                    article["content"] = entry.content[0].value
                elif "summary" in entry:
                    article["content"] = entry.summary

                articles.append(article)

                # Queue content fetch if needed
                if article["url"] and (not article["content"] or len(article["content"]) < 200):
                    fetch_tasks.append((len(articles) - 1, article["url"]))

            except Exception as e:
                logging.error(f"Error processing RSS entry: {e}")

        # Fetch missing content concurrently
        if fetch_tasks:
            async with aiohttp.ClientSession() as session:
                content_results = await asyncio.gather(
                    *[self._fetch_article_content(session, url) for _, url in fetch_tasks],
                    return_exceptions=True,
                )

                for (idx, _), content in zip(fetch_tasks, content_results):
                    if isinstance(content, str) and content:
                        articles[idx]["content"] = content

        # Clean HTML from all content
        for article in articles:
            if article["content"]:
                article["content"] = self._clean_html(article["content"])

        return articles

    def _extract_authors(self, entry) -> list[str]:
        """Extract authors from feed entry"""
        if "authors" in entry:
            return [author.get("name", "") for author in entry.authors]
        elif "author" in entry:
            return [entry.author]
        return []

    def _extract_date(self, entry) -> str:
        """Extract publication date from feed entry"""
        if "published_parsed" in entry and entry.published_parsed:
            return datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
        elif "published" in entry:
            return entry.published
        return "Unknown Date"

    async def _fetch_article_content(self, session: aiohttp.ClientSession, url: str) -> str:
        """
        Fetch article content from URL asynchronously

        Args:
            session: aiohttp client session
            url: URL of the article

        Returns:
            Article content or empty string on error
        """
        if not url:
            return ""

        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return ""
                html = await resp.text()

            soup = BeautifulSoup(html, "lxml")

            # Try common article containers
            article_content = (
                soup.find("article")
                or soup.find("div", class_="article")
                or soup.find("main")
                or soup.find("div", id="content")
                or soup.find("body")
            )

            if article_content:
                # Remove unwanted elements
                for unwanted in article_content.find_all(
                    ["script", "style", "nav", "header", "footer", "aside"]
                ):
                    unwanted.decompose()
                return article_content.get_text(separator="\n")

            return soup.get_text(separator="\n")

        except asyncio.TimeoutError:
            logging.debug(f"Timeout fetching article content from {url}")
            return ""
        except Exception as e:
            logging.debug(f"Error fetching article content from {url}: {e}")
            return ""

    def _clean_html(self, html_content: str) -> str:
        """
        Clean HTML from content

        Args:
            html_content: HTML content

        Returns:
            Cleaned text
        """
        if not html_content:
            return ""

        try:
            soup = BeautifulSoup(html_content, "lxml")
            return soup.get_text(separator="\n")
        except Exception as e:
            logging.error(f"Error cleaning HTML: {e}")
            return BeautifulSoup(html_content, "html.parser").get_text()
