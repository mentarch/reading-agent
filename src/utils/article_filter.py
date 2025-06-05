import logging
from . import metrics

class ArticleFilter:
    """Filter articles based on citation metrics"""

    def __init__(self, config=None):
        config = config or {}
        self.min_citations = config.get("min_citations", 0)
        self.min_h_index = config.get("min_h_index", 0)

    def score_article(self, article):
        citations = metrics.get_article_citation_count(
            doi=article.get("doi"), title=article.get("title")
        )
        h_index = None
        if self.min_h_index and article.get("journal"):
            h_index = metrics.get_journal_h_index(article.get("journal"))
        article.setdefault("metrics", {})["citations"] = citations
        if h_index is not None:
            article["metrics"]["h_index"] = h_index
        return citations, h_index

    def passes(self, article):
        citations, h_index = self.score_article(article)
        if self.min_citations and citations < self.min_citations:
            logging.info(
                f"Article '{article.get('title')}' filtered due to citations ({citations} < {self.min_citations})"
            )
            return False
        if self.min_h_index and h_index is not None and h_index < self.min_h_index:
            logging.info(
                f"Article '{article.get('title')}' filtered due to journal h-index ({h_index} < {self.min_h_index})"
            )
            return False
        return True

    def filter_articles(self, articles):
        return [a for a in articles if self.passes(a)]
