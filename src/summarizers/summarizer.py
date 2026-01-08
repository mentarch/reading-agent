"""
Summarizer module for generating article summaries
"""

import logging
import random
import re

from src.utils.openai_utils import create_openai_client, generate_summary_with_openai


def generate_random_summary(article: dict) -> str:
    """
    Generate a random summary for an article (fallback when OpenAI fails)

    Args:
        article: The article dictionary

    Returns:
        A generic summary string
    """
    logging.warning(f"Generating random summary for article: {article.get('title')}")
    random_summaries = [
        "This research presents a novel approach to solving problems in the computer vision domain.",
        "The study introduces innovative techniques for image processing with potential applications.",
        "This paper proposes a new framework that outperforms existing methods in benchmark evaluations.",
        "The authors demonstrate improvements in accuracy and efficiency compared to previous approaches.",
        "This work addresses key challenges in the field through an innovative methodology.",
        "The research combines established techniques with new insights to advance the state of the art.",
    ]
    return random.choice(random_summaries)


def summarize_article(article: dict, model: str = "gpt-4o", max_tokens: int = 150) -> str:
    """
    Summarize an article using OpenAI

    Args:
        article: The article dictionary with 'title', 'content', and 'url'
        model: The OpenAI model to use for summarization
        max_tokens: Maximum tokens for the summary (2-3 sentences)

    Returns:
        The summary string
    """
    if not article.get("content"):
        logging.warning(f"No content to summarize for article: {article.get('title')}")
        return "No content available to summarize."

    logging.info(f"Summarizing article: {article.get('title')}")

    try:
        client = create_openai_client()

        if client is None:
            logging.warning("OpenAI client creation failed, falling back to extractive summary")
            return create_fallback_summary(article.get("content", ""))

        content = f"Title: {article.get('title', 'Unknown')}\n\n{article.get('content', '')}"
        summary = generate_summary_with_openai(client, content, model, max_tokens)

        return summary

    except Exception as e:
        logging.error(f"Error summarizing article: {e}")
        return create_fallback_summary(article.get("content", ""))


def create_fallback_summary(content: str, max_words: int = 100) -> str:
    """
    Create a basic extractive summary as fallback

    Args:
        content: The article content
        max_words: Maximum words in the summary

    Returns:
        An extractive summary from the first few sentences
    """
    if not content:
        return "No content available to summarize."

    try:
        # Split into sentences
        sentences = re.split(r"(?<=[.!?])\s+", content.strip())

        if not sentences:
            return content[:500] + "..." if len(content) > 500 else content

        # Take first 3-5 sentences as summary
        summary_sentences = []
        word_count = 0

        for sentence in sentences[:5]:
            words = sentence.split()
            if word_count + len(words) > max_words:
                break
            summary_sentences.append(sentence)
            word_count += len(words)

        if summary_sentences:
            return " ".join(summary_sentences)

        # If first sentence is too long, truncate it
        words = sentences[0].split()
        return " ".join(words[:max_words]) + "..."

    except Exception as e:
        logging.error(f"Error in fallback summarization: {e}")
        return content[:500] + "..." if len(content) > 500 else content
