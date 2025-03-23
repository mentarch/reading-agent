import sys
import os

print("Python path:", sys.path)

try:
    from src.utils.article_tracker import ArticleTracker
    print("Successfully imported ArticleTracker")
    print("ArticleTracker attributes:", dir(ArticleTracker))
except Exception as e:
    print("Error importing ArticleTracker:", str(e))
