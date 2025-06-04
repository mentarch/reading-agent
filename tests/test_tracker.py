import unittest
import tempfile
from datetime import datetime, timedelta

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

    def test_clear_older_than(self):
        self.tracker.mark_processed(self.article1, "summary1")
        self.tracker.mark_processed(self.article2, "summary2")

        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        art1_id = self.tracker._get_article_id(self.article1)
        self.tracker.processed_articles[art1_id]["processed_date"] = old_date
        self.tracker._save_tracker()

        cleared = self.tracker.clear_older_than(5)
        self.assertEqual(cleared, 1)
        self.assertFalse(self.tracker.is_processed(self.article1))
        self.assertTrue(self.tracker.is_processed(self.article2))


if __name__ == "__main__":
    unittest.main()
