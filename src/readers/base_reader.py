"""
Base reader class that defines the interface for all readers
"""

import logging
from abc import ABC, abstractmethod

class BaseReader(ABC):
    """Base class for all article readers"""
    
    def __init__(self, name, url):
        """
        Initialize the reader
        
        Args:
            name (str): Source name
            url (str): Source URL
        """
        self.name = name
        self.url = url
        
    @abstractmethod
    def fetch_articles(self):
        """
        Fetch articles from the source
        
        Returns:
            list: List of article dictionaries with keys:
                - title (str): Article title
                - authors (list): List of author names
                - published_date (str): Publication date
                - url (str): Article URL
                - content (str): Article content
                - source (str): Source name
        """
        pass
    
    def filter_by_topics(self, articles, topics):
        """
        Filter articles by topics of interest
        
        Args:
            articles (list): List of article dictionaries
            topics (list): List of topics to filter by
            
        Returns:
            list: Filtered list of article dictionaries
        """
        if not topics:
            logging.warning(f"No topics specified for filtering {self.name} articles")
            return articles
            
        filtered = []
        
        # Convert topics to lowercase for case-insensitive matching
        topics_lower = [topic.lower() for topic in topics]
        
        for article in articles:
            # Check if any topic is mentioned in title or content
            title = article.get('title', '').lower()
            content = article.get('content', '').lower()
            
            for topic in topics_lower:
                if topic in title or topic in content:
                    filtered.append(article)
                    break
                    
        return filtered 