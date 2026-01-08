"""
Article tracker module using SQLite for persistent storage
"""

import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path


class ArticleTracker:
    """
    Tracks which articles have been processed to avoid duplicate processing.
    Uses SQLite for reliable concurrent access and querying.
    """

    def __init__(self, storage_path: str = "./data"):
        """
        Initialize the article tracker

        Args:
            storage_path: Path to the storage directory
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_path / "articles.db"
        self._init_db()
        self._migrate_from_json()

    def _init_db(self) -> None:
        """Initialize the SQLite database schema"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_articles (
                    article_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    url TEXT,
                    summary TEXT,
                    processed_date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_date
                ON processed_articles(processed_date)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_source
                ON processed_articles(source)
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections with WAL mode"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _migrate_from_json(self) -> None:
        """Migrate existing JSON data to SQLite (one-time migration)"""
        json_path = self.storage_path / "processed_articles.json"
        if not json_path.exists():
            return

        try:
            with open(json_path) as f:
                old_data = json.load(f)

            if not old_data:
                return

            migrated = 0
            with self._get_connection() as conn:
                for article_id, data in old_data.items():
                    # Check if already migrated
                    existing = conn.execute(
                        "SELECT 1 FROM processed_articles WHERE article_id = ?", (article_id,)
                    ).fetchone()

                    if existing:
                        continue

                    conn.execute(
                        """
                        INSERT INTO processed_articles
                        (article_id, title, source, url, summary, processed_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            article_id,
                            data.get("title", "Unknown"),
                            data.get("source", "Unknown"),
                            data.get("url", ""),
                            data.get("summary"),
                            data.get("processed_date", datetime.now().isoformat()),
                        ),
                    )
                    migrated += 1

                conn.commit()

            if migrated > 0:
                logging.info(f"Migrated {migrated} articles from JSON to SQLite")
                # Rename old file to prevent re-migration
                backup_path = json_path.with_suffix(".json.bak")
                json_path.rename(backup_path)
                logging.info(f"Backed up old JSON file to {backup_path}")

        except Exception as e:
            logging.error(f"Error migrating from JSON: {e}")

    def is_processed(self, article: dict) -> bool:
        """
        Check if an article has been processed

        Args:
            article: Article dictionary

        Returns:
            True if article has been processed
        """
        article_id = self._get_article_id(article)
        with self._get_connection() as conn:
            result = conn.execute(
                "SELECT 1 FROM processed_articles WHERE article_id = ?", (article_id,)
            ).fetchone()
            return result is not None

    def mark_processed(self, article: dict, summary: str | None = None) -> bool:
        """
        Mark an article as processed

        Args:
            article: Article dictionary
            summary: Summary of the article if available

        Returns:
            True if successful
        """
        try:
            article_id = self._get_article_id(article)
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO processed_articles
                    (article_id, title, source, url, summary, processed_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        article_id,
                        article.get("title", "Unknown"),
                        article.get("source", "Unknown"),
                        article.get("url", ""),
                        summary,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error marking article as processed: {e}")
            return False

    def get_processed_articles(
        self, limit: int | None = None, source: str | None = None
    ) -> list[dict]:
        """
        Get list of processed articles

        Args:
            limit: Maximum number of articles to return
            source: Filter by source

        Returns:
            List of processed article dictionaries
        """
        query = "SELECT * FROM processed_articles"
        params = []

        if source:
            query += " WHERE source = ?"
            params.append(source)

        query += " ORDER BY processed_date DESC"

        if limit and isinstance(limit, int):
            query += " LIMIT ?"
            params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def clear_older_than(self, days: int) -> int:
        """
        Clear articles older than specified days

        Args:
            days: Number of days

        Returns:
            Number of articles cleared
        """
        if not isinstance(days, int) or days <= 0:
            return 0

        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "DELETE FROM processed_articles WHERE processed_date < ?", (cutoff_date,)
                )
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logging.error(f"Error clearing old articles: {e}")
            return 0

    def _get_article_id(self, article: dict) -> str:
        """
        Generate a unique identifier for an article

        Args:
            article: Article dictionary

        Returns:
            Unique identifier string
        """
        # Use URL if available as it should be unique
        if article.get("url"):
            return article["url"]

        # Fall back to title and source
        title = article.get("title", "").strip()
        source = article.get("source", "").strip()

        if title and source:
            return f"{source}:{title}"

        if title:
            return title

        # Last resort - generate a hash from available data
        import hashlib

        content = f"{article.get('title', '')}{article.get('source', '')}{article.get('content', '')}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_stats(self) -> dict:
        """
        Get statistics about tracked articles

        Returns:
            Dictionary with statistics
        """
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM processed_articles").fetchone()[0]

            sources = conn.execute("""
                SELECT source, COUNT(*) as count
                FROM processed_articles
                GROUP BY source
                ORDER BY count DESC
            """).fetchall()

            oldest = conn.execute(
                "SELECT MIN(processed_date) FROM processed_articles"
            ).fetchone()[0]

            newest = conn.execute(
                "SELECT MAX(processed_date) FROM processed_articles"
            ).fetchone()[0]

            return {
                "total_articles": total,
                "by_source": {row["source"]: row["count"] for row in sources},
                "oldest_article": oldest,
                "newest_article": newest,
            }
