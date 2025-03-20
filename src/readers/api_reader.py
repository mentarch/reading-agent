"""
API reader implementation for fetching articles from API endpoints
"""

import logging
import requests
import json
from datetime import datetime
from .base_reader import BaseReader

class APIReader(BaseReader):
    """Reader for API-based data sources"""
    
    def __init__(self, name, url, headers=None, params=None):
        """
        Initialize the API reader
        
        Args:
            name (str): Source name
            url (str): API endpoint URL
            headers (dict, optional): Headers for API requests
            params (dict, optional): Parameters for API requests
        """
        super().__init__(name, url)
        self.headers = headers or {}
        self.params = params or {}
        
    def fetch_articles(self):
        """
        Fetch articles from API endpoint
        
        Returns:
            list: List of article dictionaries
            
        Raises:
            Exception: If there's an error fetching or parsing API response
        """
        logging.info(f"Fetching articles from {self.name} API: {self.url}")
        
        try:
            # Make API request
            response = requests.get(
                self.url,
                headers=self.headers,
                params=self.params,
                timeout=30
            )
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            # Process data based on expected format
            # This is a generic implementation that needs customization for specific APIs
            articles = self._process_api_response(data)
            
            logging.info(f"Fetched {len(articles)} articles from {self.name} API")
            return articles
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching from API {self.url}: {str(e)}")
            raise
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON from {self.url}: {str(e)}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error with API {self.url}: {str(e)}")
            raise
            
    def _process_api_response(self, data):
        """
        Process API response data into article format
        
        Args:
            data (dict/list): API response data
            
        Returns:
            list: List of processed article dictionaries
        """
        articles = []
        
        # Extract articles based on common API formats
        # This is a simplified implementation that needs customization for specific APIs
        
        try:
            # Case 1: Response is a list of articles
            if isinstance(data, list):
                for item in data:
                    article = self._extract_article_data(item)
                    if article:
                        articles.append(article)
                        
            # Case 2: Response has a 'results', 'items', 'articles', or 'data' field
            elif isinstance(data, dict):
                items = None
                for key in ['results', 'items', 'articles', 'data', 'response']:
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
            logging.error(f"Error processing API response: {str(e)}")
            
        return articles
        
    def _extract_article_data(self, item):
        """
        Extract article data from API response item
        
        Args:
            item (dict): API response item
            
        Returns:
            dict: Article dictionary or None if invalid
        """
        # Skip non-dictionary items
        if not isinstance(item, dict):
            return None
            
        # Try to extract standard fields
        # Field names vary by API, so we try common variations
        
        # Extract title
        title = None
        for key in ['title', 'headline', 'name']:
            if key in item and item[key]:
                title = item[key]
                break
                
        if not title:
            return None
            
        # Initialize article with required fields
        article = {
            'title': title,
            'url': '',
            'content': '',
            'source': self.name,
            'authors': [],
            'published_date': 'Unknown'
        }
        
        # Extract URL
        for key in ['url', 'link', 'href']:
            if key in item and item[key]:
                article['url'] = item[key]
                break
                
        # Extract content
        for key in ['content', 'description', 'abstract', 'summary', 'body', 'text']:
            if key in item and item[key]:
                article['content'] = item[key]
                break
                
        # Extract authors
        for key in ['authors', 'author', 'creator', 'byline']:
            if key in item:
                if isinstance(item[key], list):
                    # Handle list of authors
                    if all(isinstance(a, str) for a in item[key]):
                        article['authors'] = item[key]
                    elif all(isinstance(a, dict) for a in item[key]):
                        # Extract author names from objects
                        article['authors'] = [
                            a.get('name', a.get('fullname', '')) 
                            for a in item[key] if isinstance(a, dict)
                        ]
                elif isinstance(item[key], str):
                    # Handle comma-separated authors
                    article['authors'] = [a.strip() for a in item[key].split(',')]
                break
                
        # Extract publication date
        for key in ['published_date', 'pubDate', 'date', 'created_at', 'publishedAt']:
            if key in item and item[key]:
                try:
                    # Handle different date formats
                    if isinstance(item[key], str):
                        # Try common formats
                        for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%d/%m/%Y']:
                            try:
                                date_obj = datetime.strptime(item[key].split('.')[0], fmt)
                                article['published_date'] = date_obj.strftime('%Y-%m-%d')
                                break
                            except ValueError:
                                continue
                    elif isinstance(item[key], int):
                        # Assume Unix timestamp
                        date_obj = datetime.fromtimestamp(item[key])
                        article['published_date'] = date_obj.strftime('%Y-%m-%d')
                except Exception:
                    # Keep default if parsing fails
                    pass
                break
                
        return article 