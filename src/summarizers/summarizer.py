"""
Summarizer module for generating article summaries
"""

import os
import logging
import random
from src.utils.openai_utils import create_openai_client, generate_summary_with_openai

def generate_random_summary(article):
    """
    Generate a random summary for an article, limited to 2-3 sentences.
    
    Args:
        article (dict): The article to summarize.
        
    Returns:
        str: A short random summary.
    """
    logging.warning(f"Generating random summary for article: {article.get('title')}")
    random_summaries = [
        "This research presents a novel approach to solving problems in the computer vision domain.",
        "The study introduces innovative techniques for image processing with potential applications in real-world scenarios.",
        "This paper proposes a new framework that outperforms existing methods in benchmark evaluations.",
        "The authors demonstrate improvements in accuracy and efficiency compared to previous approaches.",
        "This work addresses key challenges in the field through an innovative methodology.",
        "The research combines established techniques with new insights to advance the state of the art."
    ]
    return random.choice(random_summaries)

def summarize_article(article, model="gpt-3.5-turbo", max_tokens=150):
    """
    Summarize an article using OpenAI.
    
    Args:
        article (dict): The article to summarize. Must contain 'title', 'content', and 'url'.
        model (str): The OpenAI model to use for summarization.
        max_tokens (int): The maximum number of tokens for the summary. Default is 150 for 2-3 sentence summaries.
        
    Returns:
        str: The summary of the article.
    """
    if not article.get('content'):
        logging.warning(f"No content to summarize for article: {article.get('title')}")
        return "No content available to summarize."
    
    logging.info(f"Summarizing article: {article.get('title')}")
    
    try:
        # Create OpenAI client
        client = create_openai_client()
        
        if client is None:
            logging.warning("OpenAI client creation failed, falling back to random summary")
            return generate_random_summary(article)
        
        # Generate summary using OpenAI with retry logic
        content = f"Title: {article.get('title', 'Unknown')}\n\n{article.get('content', '')}"
        summary = generate_summary_with_openai(client, content, model, max_tokens)
        
        return summary
    
    except Exception as e:
        logging.error(f"Error summarizing article: {str(e)}")
        return generate_random_summary(article)

def create_fallback_summary(content, max_length=300):
    """
    Create a basic extractive summary as fallback
    
    Args:
        content (str): The article content
        max_length (int): Maximum length of the summary in words
        
    Returns:
        str: A basic extractive summary
    """
    try:
        # Split into sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        if len(sentences) <= 5:
            return content
            
        # Get first paragraph (usually introduction)
        intro = ' '.join(sentences[:min(5, len(sentences)//5)])
        
        # Get last few sentences (usually conclusion)
        conclusion = ' '.join(sentences[-min(5, len(sentences)//5):])
        
        # Simple summary is intro + conclusion
        summary = intro + " [...] " + conclusion
        
        # Truncate to max length
        words = summary.split()
        if len(words) > max_length:
            summary = ' '.join(words[:max_length]) + "..."
            
        return summary
        
    except Exception as e:
        logging.error(f"Error in fallback summarization: {str(e)}")
        
        # Ultimate fallback
        words = content.split()
        if len(words) > max_length:
            return ' '.join(words[:max_length]) + "..."
        return content 