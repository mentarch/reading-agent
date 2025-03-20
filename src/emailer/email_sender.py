"""
Email sender module for sending article digests
"""

import os
import logging
import smtplib
import ssl
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from functools import wraps

def retry(max_attempts=3, initial_delay=2, backoff_factor=2):
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
                        logging.warning(f"Email sending attempt {attempt} failed: {str(e)}. Retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logging.error(f"All {max_attempts} email sending attempts failed. Last error: {str(e)}")
            
            raise last_exception
        return wrapper
    return decorator

@retry(max_attempts=3, initial_delay=3)
def send_email_digest(articles, subject_prefix="[Research Update]", email_format="html", 
                     include_links=True, max_articles=10):
    """
    Send an email digest of summarized articles
    
    Args:
        articles (list): List of article dictionaries with summaries
        subject_prefix (str): Prefix for the email subject
        email_format (str): Format of the email ('html' or 'plain')
        include_links (bool): Whether to include article links
        max_articles (int): Maximum number of articles to include
        
    Returns:
        bool: True if email was sent successfully, False otherwise
        
    Raises:
        Exception: If the email sending fails after retries
    """
    # Get email configuration from environment
    sender_email = os.environ.get('EMAIL_SENDER')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    recipient_email = os.environ.get('EMAIL_RECIPIENT')
    smtp_server = os.environ.get('EMAIL_SMTP_SERVER')
    smtp_port = int(os.environ.get('EMAIL_SMTP_PORT', 587))
    
    # Validate required configuration
    missing_config = []
    if not sender_email:
        missing_config.append('EMAIL_SENDER')
    if not sender_password:
        missing_config.append('EMAIL_PASSWORD')
    if not recipient_email:
        missing_config.append('EMAIL_RECIPIENT')
    if not smtp_server:
        missing_config.append('EMAIL_SMTP_SERVER')
        
    if missing_config:
        logging.error(f"Missing email configuration: {', '.join(missing_config)}")
        raise ValueError(f"Missing email configuration: {', '.join(missing_config)}")
    
    # Ensure we have articles to send
    if not articles:
        logging.warning("No articles to send in digest. Skipping email.")
        return False
        
    # Limit number of articles
    if len(articles) > max_articles:
        logging.info(f"Limiting digest to {max_articles} articles")
        articles = articles[:max_articles]
    
    # Create email content
    message = MIMEMultipart("alternative")
    today_date = datetime.now().strftime("%Y-%m-%d")
    message["Subject"] = f"{subject_prefix} Research Digest - {today_date}"
    message["From"] = sender_email
    message["To"] = recipient_email
    
    # Create the plain-text and HTML versions of the message
    text_content = create_plain_text_digest(articles, include_links)
    
    # Create HTML content - use a simpler HTML structure to avoid issues
    html_content = create_simple_html_digest(articles, include_links) if email_format.lower() == "html" else text_content
    
    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")
    
    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)
    
    # Create secure connection with server and send email
    context = ssl.create_default_context()
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
            
        logging.info(f"Email digest with {len(articles)} articles sent successfully to {recipient_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"Authentication error with SMTP server: {str(e)}")
        raise ValueError("Failed to authenticate with the SMTP server. Please check your email credentials.") from e
        
    except smtplib.SMTPServerDisconnected as e:
        logging.error(f"SMTP server disconnected: {str(e)}")
        raise ConnectionError("Connection to SMTP server was lost. Please check your network connection.") from e
        
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error: {str(e)}")
        raise RuntimeError(f"SMTP error occurred: {str(e)}") from e
        
    except (ConnectionRefusedError, TimeoutError) as e:
        logging.error(f"Connection error: {str(e)}")
        raise ConnectionError(f"Could not connect to SMTP server at {smtp_server}:{smtp_port}. Please check your configuration.") from e
        
    except Exception as e:
        logging.error(f"Unexpected error sending email: {str(e)}")
        raise

def create_simple_html_digest(articles, include_links=True):
    """
    Create a simple HTML digest to avoid formatting issues
    
    Args:
        articles (list): List of article dictionaries
        include_links (bool): Whether to include article links
        
    Returns:
        str: Simple HTML email content
    """
    # Create a very simple HTML template with minimal styling to avoid issues
    html = ["<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<title>Research Article Digest</title>",
            "</head>",
            "<body style='font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;'>",
            f"<h1 style='color: #333;'>Research Article Digest</h1>",
            f"<p>Date: {datetime.now().strftime('%Y-%m-%d')} | Number of articles: {len(articles)}</p>"]
    
    # Add each article
    for i, article in enumerate(articles, 1):
        title = article.get('title', 'No Title')
        url = article.get('url', '')
        source = article.get('source', 'Unknown')
        date = article.get('published_date', 'Unknown date')
        authors = article.get('authors', [])
        summary = article.get('summary', 'No summary available.')
        
        # Format authors
        authors_str = ', '.join(authors) if authors else 'Unknown'
        
        # Create title with link if URL is available
        title_html = f"<a href='{url}' style='color: #3498db;'>{title}</a>" if include_links and url else title
        
        # Add article HTML
        html.append(f"<div style='margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #eee;'>")
        html.append(f"<h2 style='color: #2980b9; font-size: 18px;'>{title_html}</h2>")
        html.append(f"<div style='font-size: 13px; color: #666; margin-bottom: 10px;'>")
        html.append(f"<strong>Authors:</strong> {authors_str} | ")
        html.append(f"<strong>Source:</strong> {source} | ")
        html.append(f"<strong>Published:</strong> {date}")
        html.append("</div>")
        html.append("<div>")
        
        # Safely handle newlines in summary
        for paragraph in summary.split('\n'):
            if paragraph.strip():
                html.append(f"<p>{paragraph}</p>")
                
        html.append("</div>")
        html.append("</div>")
    
    # Add footer and close tags
    html.append("<div style='margin-top: 30px; font-size: 12px; color: #999; text-align: center;'>")
    html.append("<p>This digest was automatically generated by the Research Article Reader and Summarizer.</p>")
    html.append("</div>")
    html.append("</body>")
    html.append("</html>")
    
    return "\n".join(html)

def create_plain_text_digest(articles, include_links=True):
    """
    Create plain text email digest
    
    Args:
        articles (list): List of article dictionaries
        include_links (bool): Whether to include article links
        
    Returns:
        str: Plain text email content
    """
    content = []
    
    # Add header
    content.append("RESEARCH ARTICLE DIGEST")
    content.append("======================")
    content.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    content.append(f"Number of articles: {len(articles)}")
    content.append("\n")
    
    # Add each article
    for i, article in enumerate(articles, 1):
        content.append(f"ARTICLE {i}: {article.get('title', 'No Title')}")
        content.append("-" * 40)
        
        # Add metadata
        if article.get('authors'):
            content.append(f"Authors: {', '.join(article.get('authors', []))}")
        content.append(f"Source: {article.get('source', 'Unknown')}")
        content.append(f"Published: {article.get('published_date', 'Unknown date')}")
        
        if include_links and article.get('url'):
            content.append(f"Link: {article.get('url')}")
            
        content.append("")
        
        # Add summary
        content.append("SUMMARY:")
        content.append(article.get('summary', 'No summary available.'))
        content.append("\n")
        content.append("=" * 50)
        content.append("\n")
    
    # Add footer
    content.append("\nThis digest was automatically generated by the Research Article Reader and Summarizer.")
    
    return "\n".join(content)

def create_html_digest(articles, include_links=True):
    """
    Create HTML email digest
    
    Args:
        articles (list): List of article dictionaries
        include_links (bool): Whether to include article links
        
    Returns:
        str: HTML email content
    """
    # Create a simple, clean HTML template
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            line-height: 1.5;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .article {
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }
        .article-title {
            font-size: 18px;
            font-weight: bold;
            color: #2980b9;
            margin-bottom: 5px;
        }
        .metadata {
            font-size: 13px;
            color: #7f8c8d;
            margin-bottom: 10px;
        }
        .summary {
            line-height: 1.5;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .footer {
            margin-top: 30px;
            font-size: 12px;
            color: #95a5a6;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>Research Article Digest</h1>
    <p>Date: {date} | Number of articles: {count}</p>
""".format(date=datetime.now().strftime('%Y-%m-%d'), count=len(articles))
    
    # Add each article
    for article in articles:
        title = article.get('title', 'No Title')
        url = article.get('url', '')
        source = article.get('source', 'Unknown')
        date = article.get('published_date', 'Unknown date')
        authors = article.get('authors', [])
        summary = article.get('summary', 'No summary available.')
        
        # Format authors
        authors_str = ', '.join(authors) if authors else 'Unknown'
        
        # Create title with link if URL is available
        title_html = f'<a href="{url}">{title}</a>' if include_links and url else title
        
        # Add article HTML
        html += f"""
    <div class="article">
        <div class="article-title">{title_html}</div>
        <div class="metadata">
            <strong>Authors:</strong> {authors_str} | 
            <strong>Source:</strong> {source} | 
            <strong>Published:</strong> {date}
        </div>
        <div class="summary">
            <p>{summary.replace(chr(10), '<br>')}</p>
        </div>
    </div>
"""
    
    # Add footer and close tags
    html += """
    <div class="footer">
        <p>This digest was automatically generated by the Research Article Reader and Summarizer.</p>
    </div>
</body>
</html>
"""
    return html 