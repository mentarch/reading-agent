"""
OpenAI utilities for safely creating and using OpenAI clients
"""

import logging
import os
import time
from functools import wraps


def retry(max_attempts=3, initial_delay=1, backoff_factor=2):
    """
    Decorator for retrying a function with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay between retries
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = initial_delay
            last_exception = None

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    last_exception = e

                    if attempt < max_attempts:
                        logging.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logging.error(f"All {max_attempts} attempts failed. Last error: {e}")

            raise last_exception

        return wrapper

    return decorator


def create_openai_client():
    """
    Create an OpenAI client safely

    Returns:
        OpenAI: An initialized OpenAI client instance, or None if creation fails

    Raises:
        ValueError: If the API key is not found
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logging.error("OpenAI API key not found in environment variables")
        raise ValueError("OpenAI API key not found in environment variables")

    try:
        import httpx
        from openai import OpenAI

        # Create a custom httpx client without proxy configuration
        # This avoids conflicts with system proxy environment variables
        http_client = httpx.Client(
            timeout=httpx.Timeout(60.0, connect=10.0),
        )

        client = OpenAI(
            api_key=api_key,
            http_client=http_client,
        )
        return client

    except Exception as e:
        logging.error(f"Failed to create OpenAI client: {e}")
        return None


@retry(max_attempts=3, initial_delay=2)
def generate_summary_with_openai(client, content: str, model: str, max_tokens: int) -> str:
    """
    Generate a summary using OpenAI with retry logic

    Args:
        client: OpenAI client
        content: Content to summarize
        model: Model to use
        max_tokens: Maximum tokens for the response

    Returns:
        Generated summary
    """
    if client is None:
        raise ValueError("OpenAI client is not initialized")

    messages = [
        {
            "role": "system",
            "content": (
                "You are a specialized academic assistant that summarizes "
                "research papers in just 2-3 concise sentences."
            ),
        },
        {
            "role": "user",
            "content": f"""Please summarize the following research article in ONLY 2-3 sentences:

{content[:10000]}

Focus ONLY on the most important research contributions and findings.
Your summary MUST be only 2-3 sentences long, no exceptions.""",
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()
