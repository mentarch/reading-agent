"""
Base reader class that defines the interface for all readers
"""

import logging
from abc import ABC, abstractmethod


class BaseReader(ABC):
    """Base class for all article readers"""

    def __init__(self, name: str, url: str):
        """
        Initialize the reader

        Args:
            name: Source name
            url: Source URL
        """
        self.name = name
        self.url = url

    @abstractmethod
    async def fetch_articles(self) -> list[dict]:
        """
        Fetch articles from the source asynchronously

        Returns:
            List of article dictionaries with keys:
                - title (str): Article title
                - authors (list): List of author names
                - published_date (str): Publication date
                - url (str): Article URL
                - content (str): Article content
                - source (str): Source name
        """
        pass

    def filter_by_topics(self, articles: list[dict], topics: list[str]) -> list[dict]:
        """
        Filter articles by topics of interest

        Args:
            articles: List of article dictionaries
            topics: List of topics to filter by

        Returns:
            Filtered list of article dictionaries
        """
        if not topics:
            logging.warning(f"No topics specified for filtering {self.name} articles")
            return articles

        filtered = []
        topics_lower = [topic.lower() for topic in topics]

        for article in articles:
            title = article.get("title", "").lower()
            content = article.get("content", "").lower()

            for topic in topics_lower:
                if topic in title or topic in content:
                    filtered.append(article)
                    break

        return filtered
