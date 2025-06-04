"""
OpenAI utilities for safely creating and using OpenAI clients
"""

import os
import logging
import importlib.util
import sys
import time
from functools import wraps

def retry(max_attempts=3, initial_delay=1, backoff_factor=2):
    """
    Decorator for retrying a function with exponential backoff
    
    Args:
        max_attempts (int): Maximum number of retry attempts
        initial_delay (float): Initial delay between retries in seconds
        backoff_factor (float): Multiplier for delay between retries
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
                        logging.warning(f"Attempt {attempt} failed: {str(e)}. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logging.error(f"All {max_attempts} attempts failed. Last error: {str(e)}")
            
            raise last_exception
        return wrapper
    return decorator

def create_openai_client():
    """
    Create an OpenAI client safely, handling any proxy issues
    
    Returns:
        OpenAI: An initialized OpenAI client instance
        
    Raises:
        ValueError: If the API key is not found
    """
    # Get API key from environment
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logging.error("OpenAI API key not found in environment variables")
        raise ValueError("OpenAI API key not found in environment variables")
    
    # Save original environment
    orig_http_proxy = os.environ.pop('HTTP_PROXY', None)
    orig_https_proxy = os.environ.pop('HTTPS_PROXY', None)
    
    try:
        # Monkey patch the httpx.Client class to handle proxies correctly
        # This is a hack to work around issues with proxies in the OpenAI client
        import httpx
        original_client_init = httpx.Client.__init__

        def patched_client_init(self, *args, **kwargs):
            # Remove the 'proxies' argument if it's present
            if 'proxies' in kwargs:
                del kwargs['proxies']
            original_client_init(self, *args, **kwargs)

        # Apply the monkey patch
        httpx.Client.__init__ = patched_client_init

        # Now import and create the OpenAI client
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        return client
    except Exception as e:
        logging.error(f"Failed to create OpenAI client: {e}")

        # Fall back to a manual summary approach instead
        return None
    finally:
        # Restore patched httpx.Client.__init__ if it was modified
        try:
            if 'httpx' in locals() and original_client_init:
                httpx.Client.__init__ = original_client_init
        except Exception:
            pass
        # Restore environment variables
        if orig_http_proxy:
            os.environ['HTTP_PROXY'] = orig_http_proxy
        if orig_https_proxy:
            os.environ['HTTPS_PROXY'] = orig_https_proxy

@retry(max_attempts=3, initial_delay=2)
def generate_summary_with_openai(client, content, model, max_tokens):
    """
    Generate a summary using OpenAI with retry logic
    
    Args:
        client: OpenAI client
        content (str): Content to summarize
        model (str): Model to use
        max_tokens (int): Maximum tokens for the response
        
    Returns:
        str: Generated summary
    """
    if client is None:
        raise ValueError("OpenAI client is not initialized")
    
    # Create system and user messages
    messages = [
        {"role": "system", "content": "You are a specialized academic assistant that summarizes research papers in just 2-3 concise sentences."},
        {"role": "user", "content": f"""
        Please summarize the following research article in ONLY 2-3 sentences:
        
        {content[:10000]}
        
        Focus ONLY on the most important research contributions and findings.
        Your summary MUST be only 2-3 sentences long, no exceptions.
        """}
    ]
    
    # Call OpenAI API with retry logic already applied via decorator
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.3
    )
    
    return response.choices[0].message.content.strip() 