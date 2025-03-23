"""
Article tracker module for keeping track of processed articles
"""

import os
import json
import logging
from datetime import datetime

class ArticleTracker:
    """
    Tracks which articles have been processed to avoid duplicate processing
    and summaries.
    """
    
    def __init__(self, storage_path="./data"):
        """
        Initialize the article tracker
        
        Args:
            storage_path (str): Path to the storage directory
        """
        self.storage_path = storage_path
        self.tracker_file = os.path.join(storage_path, "processed_articles.json")
        self.processed_articles = self._load_tracker()
        
    def _load_tracker(self):
        """
        Load the tracker file if it exists
        
        Returns:
            dict: Dictionary of processed articles
        """
        if not os.path.exists(self.tracker_file):
            return {}
            
        try:
            with open(self.tracker_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading article tracker: {str(e)}")
            return {}
            
    def _save_tracker(self):
        """
        Save the tracker file
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.tracker_file), exist_ok=True)
            
            with open(self.tracker_file, 'w') as f:
                json.dump(self.processed_articles, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving article tracker: {str(e)}")
            
    def is_processed(self, article):
        """
        Check if an article has been processed
        
        Args:
            article (dict): Article to check
            
        Returns:
            bool: True if article has been processed, False otherwise
        """
        # Create a unique identifier for the article
        article_id = self._get_article_id(article)
        
        # Check if article is in the tracker
        return article_id in self.processed_articles
        
    def mark_processed(self, article, summary=None):
        """
        Mark an article as processed
        
        Args:
            article (dict): Article to mark as processed
            summary (str): Summary of the article if available
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create a unique identifier for the article
            article_id = self._get_article_id(article)
            
            # Add article to tracker with timestamp
            self.processed_articles[article_id] = {
                "title": article.get("title", "Unknown"),
                "source": article.get("source", "Unknown"),
                "url": article.get("url", ""),
                "processed_date": datetime.now().isoformat(),
                "summary": summary
            }
            
            # Save tracker
            self._save_tracker()
            return True
        except Exception as e:
            logging.error(f"Error marking article as processed: {str(e)}")
            return False
            
    def get_processed_articles(self, limit=None, source=None):
        """
        Get list of processed articles
        
        Args:
            limit (int): Maximum number of articles to return
            source (str): Filter by source
            
        Returns:
            list: List of processed articles
        """
        result = list(self.processed_articles.values())
        
        # Filter by source if specified
        if source:
            result = [a for a in result if a.get("source") == source]
            
        # Sort by processed date (newest first)
        result.sort(key=lambda x: x.get("processed_date", ""), reverse=True)
        
        # Limit results if specified
        if limit and isinstance(limit, int):
            result = result[:limit]
            
        return result
        
    def clear_older_than(self, days):
        """
        Clear articles older than specified days
        
        Args:
            days (int): Number of days
            
        Returns:
            int: Number of articles cleared
        """
        try:
            if not isinstance(days, int) or days <= 0:
                return 0
                
            # Calculate cutoff date
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Find articles older than cutoff date
            to_remove = []
            for article_id, data in self.processed_articles.items():
                processed_date = data.get("processed_date", "")
                if processed_date and processed_date < cutoff_date:
                    to_remove.append(article_id)
                    
            # Remove articles
            for article_id in to_remove:
                del self.processed_articles[article_id]
                
            # Save tracker
            self._save_tracker()
            
            return len(to_remove)
        except Exception as e:
            logging.error(f"Error clearing old articles: {str(e)}")
            return 0
            
    def _get_article_id(self, article):
        """
        Generate a unique identifier for an article
        
        Args:
            article (dict): Article to generate ID for
            
        Returns:
            str: Unique identifier
        """
        # Use URL if available as it should be unique
        if article.get("url"):
            return article.get("url")
            
        # Fall back to title and source if URL is not available
        title = article.get("title", "").strip()
        source = article.get("source", "").strip()
        
        if title and source:
            return f"{source}:{title}"
            
        # Last resort - use the title alone (not ideal)
        if title:
            return title
            
        # Can't generate a reliable ID
        import uuid
        return str(uuid.uuid4()) 