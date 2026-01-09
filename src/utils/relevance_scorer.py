"""
Relevance scoring module for ranking articles by topic relevance

Uses weighted keyword matching with configurable weights for:
- Title matches (high weight)
- Content/summary matches (medium weight)
- Exact phrase vs individual word matches
"""

import logging
import re
from collections import Counter


def calculate_relevance_score(article: dict, topics: list[str]) -> float:
    """
    Calculate relevance score for an article based on topic matches

    Args:
        article: Article dictionary with 'title', 'content', 'summary'
        topics: List of topics to match against

    Returns:
        Relevance score from 0.0 to 1.0
    """
    if not topics:
        return 0.5  # Neutral score when no topics configured

    title = article.get("title", "").lower()
    content = article.get("content", "").lower()
    summary = article.get("summary", "").lower()

    # Combine content and summary for matching
    full_text = f"{content} {summary}"

    # Scoring weights
    TITLE_WEIGHT = 0.5
    CONTENT_WEIGHT = 0.35
    PHRASE_BONUS = 0.15

    title_score = 0.0
    content_score = 0.0
    phrase_score = 0.0

    topics_lower = [topic.lower().strip() for topic in topics]

    for topic in topics_lower:
        # Check for exact phrase match (multi-word topics)
        words_in_topic = topic.split()

        if len(words_in_topic) > 1:
            # Multi-word phrase - check for exact phrase
            if topic in title:
                title_score += 1.0
                phrase_score += 0.5  # Bonus for exact phrase in title
            elif any(word in title for word in words_in_topic):
                title_score += 0.5  # Partial credit for individual words

            if topic in full_text:
                content_score += 1.0
                phrase_score += 0.25  # Bonus for exact phrase in content
            elif any(word in full_text for word in words_in_topic):
                content_score += 0.3  # Partial credit
        else:
            # Single word topic
            if topic in title:
                title_score += 1.0
            if topic in full_text:
                content_score += 0.5

    # Normalize scores
    num_topics = len(topics_lower)
    title_score = min(title_score / num_topics, 1.0)
    content_score = min(content_score / num_topics, 1.0)
    phrase_score = min(phrase_score / num_topics, 1.0)

    # Calculate final weighted score
    final_score = (
        title_score * TITLE_WEIGHT +
        content_score * CONTENT_WEIGHT +
        phrase_score * PHRASE_BONUS
    )

    # Ensure score is in [0, 1] range
    return min(max(final_score, 0.0), 1.0)


def score_and_rank_articles(articles: list[dict], topics: list[str]) -> list[dict]:
    """
    Score and rank articles by relevance

    Args:
        articles: List of article dictionaries
        topics: List of topics to score against

    Returns:
        Articles sorted by relevance_score (highest first), with scores added
    """
    if not articles:
        return []

    for article in articles:
        score = calculate_relevance_score(article, topics)
        article["relevance_score"] = round(score, 3)

    # Sort by relevance score (highest first)
    ranked = sorted(articles, key=lambda x: x.get("relevance_score", 0), reverse=True)

    # Log ranking summary
    if ranked:
        top_score = ranked[0].get("relevance_score", 0)
        avg_score = sum(a.get("relevance_score", 0) for a in ranked) / len(ranked)
        logging.info(f"Article ranking: top score {top_score:.2f}, avg {avg_score:.2f}")

    return ranked


def get_score_tier(score: float) -> str:
    """
    Get human-readable tier for a relevance score

    Args:
        score: Relevance score (0.0 to 1.0)

    Returns:
        Tier label: 'high', 'medium', or 'low'
    """
    if score >= 0.7:
        return "high"
    elif score >= 0.4:
        return "medium"
    else:
        return "low"
