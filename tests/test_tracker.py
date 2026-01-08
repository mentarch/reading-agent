"""Tests for the SQLite-based ArticleTracker"""

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from src.utils.article_tracker import ArticleTracker


class ArticleTrackerTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.tracker = ArticleTracker(storage_path=self.temp_dir.name)
        self.article1 = {
            "title": "Sample Article 1",
            "source": "Test",
            "url": "https://example.com/article1",
        }
        self.article2 = {
            "title": "Sample Article 2",
            "source": "Test",
            "url": "https://example.com/article2",
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_mark_and_is_processed(self):
        self.assertFalse(self.tracker.is_processed(self.article1))
        success = self.tracker.mark_processed(self.article1, "summary1")
        self.assertTrue(success)
        self.assertTrue(self.tracker.is_processed(self.article1))

    def test_mark_processed_with_summary(self):
        summary = "This is a test summary"
        self.tracker.mark_processed(self.article1, summary)
        articles = self.tracker.get_processed_articles(limit=1)
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["summary"], summary)

    def test_clear_older_than(self):
        self.tracker.mark_processed(self.article1, "summary1")
        self.tracker.mark_processed(self.article2, "summary2")

        # Manually update the date for article1 to be old
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        with self.tracker._get_connection() as conn:
            conn.execute(
                "UPDATE processed_articles SET processed_date = ? WHERE article_id = ?",
                (old_date, self.tracker._get_article_id(self.article1)),
            )
            conn.commit()

        cleared = self.tracker.clear_older_than(5)
        self.assertEqual(cleared, 1)
        self.assertFalse(self.tracker.is_processed(self.article1))
        self.assertTrue(self.tracker.is_processed(self.article2))

    def test_get_processed_articles_with_limit(self):
        for i in range(5):
            article = {"title": f"Article {i}", "source": "Test", "url": f"https://example.com/{i}"}
            self.tracker.mark_processed(article, f"Summary {i}")

        articles = self.tracker.get_processed_articles(limit=3)
        self.assertEqual(len(articles), 3)

    def test_get_processed_articles_by_source(self):
        article_a = {"title": "Article A", "source": "SourceA", "url": "https://a.com/1"}
        article_b = {"title": "Article B", "source": "SourceB", "url": "https://b.com/1"}

        self.tracker.mark_processed(article_a, "summary")
        self.tracker.mark_processed(article_b, "summary")

        articles = self.tracker.get_processed_articles(source="SourceA")
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["source"], "SourceA")

    def test_article_id_generation(self):
        # URL-based ID
        article_with_url = {"url": "https://example.com/test", "title": "Test"}
        self.assertEqual(
            self.tracker._get_article_id(article_with_url), "https://example.com/test"
        )

        # Title + source fallback
        article_no_url = {"title": "Test Title", "source": "TestSource"}
        self.assertEqual(self.tracker._get_article_id(article_no_url), "TestSource:Test Title")

        # Title only fallback
        article_title_only = {"title": "Just Title"}
        self.assertEqual(self.tracker._get_article_id(article_title_only), "Just Title")

    def test_get_stats(self):
        self.tracker.mark_processed(self.article1, "summary1")
        self.tracker.mark_processed(self.article2, "summary2")

        stats = self.tracker.get_stats()
        self.assertEqual(stats["total_articles"], 2)
        self.assertEqual(stats["by_source"]["Test"], 2)

    def test_database_file_created(self):
        db_path = Path(self.temp_dir.name) / "articles.db"
        self.assertTrue(db_path.exists())

    def test_duplicate_processing(self):
        self.tracker.mark_processed(self.article1, "summary1")
        self.tracker.mark_processed(self.article1, "summary2")  # Same article again

        articles = self.tracker.get_processed_articles()
        self.assertEqual(len(articles), 1)
        # Should have updated summary
        self.assertEqual(articles[0]["summary"], "summary2")


if __name__ == "__main__":
    unittest.main()
