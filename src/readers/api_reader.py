"""
API reader implementation for fetching articles from API endpoints asynchronously
"""

import asyncio
import logging
from datetime import datetime

import aiohttp

from .base_reader import BaseReader


class APIReader(BaseReader):
    """Async reader for API-based data sources"""

    def __init__(
        self,
        name: str,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
    ):
        """
        Initialize the API reader

        Args:
            name: Source name
            url: API endpoint URL
            headers: Headers for API requests
            params: Parameters for API requests
        """
        super().__init__(name, url)
        self.headers = headers or {}
        self.params = params or {}

    async def fetch_articles(self) -> list[dict]:
        """
        Fetch articles from API endpoint asynchronously

        Returns:
            List of article dictionaries
        """
        logging.info(f"Fetching articles from {self.name} API: {self.url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.url,
                    headers=self.headers,
                    params=self.params,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        logging.error(f"API returned status {resp.status} for {self.url}")
                        return []
                    data = await resp.json()

            articles = self._process_api_response(data)
            logging.info(f"Fetched {len(articles)} articles from {self.name} API")
            return articles

        except asyncio.TimeoutError:
            logging.error(f"Timeout fetching from API {self.url}")
            return []
        except aiohttp.ContentTypeError as e:
            logging.error(f"Error parsing JSON from {self.url}: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error with API {self.url}: {e}")
            return []

    def _process_api_response(self, data) -> list[dict]:
        """
        Process API response data into article format

        Args:
            data: API response data (dict or list)

        Returns:
            List of processed article dictionaries
        """
        articles = []

        try:
            # Case 1: Response is a list of articles
            if isinstance(data, list):
                for item in data:
                    article = self._extract_article_data(item)
                    if article:
                        articles.append(article)

            # Case 2: Response has a results/items/articles/data field
            elif isinstance(data, dict):
                items = None
                for key in ["results", "items", "articles", "data", "response"]:
                    if key in data and isinstance(data[key], list):
                        items = data[key]
                        break

                if items:
                    for item in items:
                        article = self._extract_article_data(item)
                        if article:
                            articles.append(article)
                else:
                    # Case 3: Response is a single article
                    article = self._extract_article_data(data)
                    if article:
                        articles.append(article)

        except Exception as e:
            logging.error(f"Error processing API response: {e}")

        return articles

    def _extract_article_data(self, item) -> dict | None:
        """
        Extract article data from API response item

        Args:
            item: API response item

        Returns:
            Article dictionary or None if invalid
        """
        if not isinstance(item, dict):
            return None

        # Extract title (required)
        title = None
        for key in ["title", "headline", "name"]:
            if key in item and item[key]:
                title = item[key]
                break

        if not title:
            return None

        article = {
            "title": title,
            "url": "",
            "content": "",
            "source": self.name,
            "authors": [],
            "published_date": "Unknown",
        }

        # Extract URL
        for key in ["url", "link", "href"]:
            if key in item and item[key]:
                article["url"] = item[key]
                break

        # Extract content
        for key in ["content", "description", "abstract", "summary", "body", "text"]:
            if key in item and item[key]:
                article["content"] = item[key]
                break

        # Extract authors
        for key in ["authors", "author", "creator", "byline"]:
            if key in item:
                if isinstance(item[key], list):
                    if all(isinstance(a, str) for a in item[key]):
                        article["authors"] = item[key]
                    elif all(isinstance(a, dict) for a in item[key]):
                        article["authors"] = [
                            a.get("name", a.get("fullname", ""))
                            for a in item[key]
                            if isinstance(a, dict)
                        ]
                elif isinstance(item[key], str):
                    article["authors"] = [a.strip() for a in item[key].split(",")]
                break

        # Extract publication date
        for key in ["published_date", "pubDate", "date", "created_at", "publishedAt"]:
            if key in item and item[key]:
                article["published_date"] = self._parse_date(item[key])
                break

        return article

    def _parse_date(self, date_value) -> str:
        """Parse various date formats into YYYY-MM-DD"""
        try:
            if isinstance(date_value, str):
                for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"]:
                    try:
                        date_obj = datetime.strptime(date_value.split(".")[0], fmt)
                        return date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
            elif isinstance(date_value, int):
                return datetime.fromtimestamp(date_value).strftime("%Y-%m-%d")
        except Exception:
            pass
        return "Unknown"
