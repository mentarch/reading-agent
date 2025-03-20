"""
RSS reader implementation for fetching articles from RSS feeds
"""

import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from .base_reader import BaseReader

class RSSReader(BaseReader):
    """Reader for RSS feeds like PubMed and arXiv"""
    
    def __init__(self, name, url, params=None):
        """
        Initialize the RSS reader
        
        Args:
            name (str): Source name
            url (str): RSS feed URL
            params (dict, optional): Additional parameters for the RSS request
        """
        super().__init__(name, url)
        self.params = params or {}
        
    def fetch_articles(self):
        """
        Fetch articles from RSS feed
        
        Returns:
            list: List of article dictionaries
            
        Raises:
            Exception: If there's an error fetching or parsing the feed
        """
        logging.info(f"Fetching articles from {self.name} RSS feed: {self.url}")
        
        try:
            # Parse the feed
            feed = feedparser.parse(self.url)
            
            if feed.get('bozo_exception'):
                logging.warning(f"Error parsing feed: {feed.bozo_exception}")
                
            # Check if feed has entries
            if not feed.get('entries'):
                logging.warning(f"No entries found in RSS feed: {self.url}")
                return []
                
            articles = []
            
            for entry in feed.entries:
                try:
                    # Extract article details
                    article = {
                        'title': entry.get('title', 'No Title'),
                        'url': entry.get('link', ''),
                        'source': self.name,
                        'content': '',  # Will fetch content separately
                    }
                    
                    # Extract authors if available
                    if 'authors' in entry:
                        article['authors'] = [author.get('name', '') for author in entry.authors]
                    elif 'author' in entry:
                        article['authors'] = [entry.author]
                    else:
                        article['authors'] = []
                    
                    # Extract publication date
                    if 'published_parsed' in entry:
                        pub_date = entry.published_parsed
                        article['published_date'] = datetime(*pub_date[:6]).strftime('%Y-%m-%d')
                    elif 'published' in entry:
                        article['published_date'] = entry.published
                    else:
                        article['published_date'] = 'Unknown Date'
                        
                    # Extract content/summary
                    if 'content' in entry:
                        article['content'] = entry.content[0].value
                    elif 'summary' in entry:
                        article['content'] = entry.summary
                    else:
                        article['content'] = ''
                    
                    # Fetch full article content if needed
                    if article['url'] and (not article['content'] or len(article['content']) < 200):
                        article['content'] = self._fetch_article_content(article['url'])
                    
                    # Clean HTML from content
                    if article['content']:
                        article['content'] = self._clean_html(article['content'])
                    
                    articles.append(article)
                    
                except Exception as e:
                    logging.error(f"Error processing RSS entry: {str(e)}")
            
            logging.info(f"Fetched {len(articles)} articles from {self.name}")
            return articles
            
        except Exception as e:
            logging.error(f"Error fetching RSS feed {self.url}: {str(e)}")
            raise
        
    def _fetch_article_content(self, url):
        """
        Fetch the actual article content from the URL
        
        Args:
            url (str): URL of the article
            
        Returns:
            str: Article content or empty string on error
        """
        if not url:
            return ""
            
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Try to extract article content
            # This is a simplified approach - might need customization for specific sites
            
            # First try common article containers
            article_content = soup.find('article') or soup.find('div', class_='article')
            
            if not article_content:
                # Look for main content area
                article_content = soup.find('main') or soup.find('div', id='content')
            
            if not article_content:
                # Just use the body if no better container found
                article_content = soup.find('body')
            
            if article_content:
                # Remove unwanted elements
                for unwanted in article_content.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    unwanted.decompose()
                    
                return article_content.get_text(separator='\n')
            else:
                return soup.get_text(separator='\n')
                
        except Exception as e:
            logging.error(f"Error fetching article content from {url}: {str(e)}")
            return ""
    
    def _clean_html(self, html_content):
        """
        Clean HTML from content
        
        Args:
            html_content (str): HTML content
            
        Returns:
            str: Cleaned text
        """
        if not html_content:
            return ""
            
        try:
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'lxml')
            
            # Extract text
            return soup.get_text(separator='\n')
            
        except Exception as e:
            logging.error(f"Error cleaning HTML: {str(e)}")
            # Return original but strip basic HTML tags
            return BeautifulSoup(html_content, 'html.parser').get_text() 