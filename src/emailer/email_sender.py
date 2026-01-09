"""
Email sender module for sending article digests

Supports:
- Resend API (recommended, default)
- SMTP (legacy fallback)
"""

import logging
import os
import smtplib
import ssl
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


def retry(max_attempts=3, initial_delay=2, backoff_factor=2):
    """
    Decorator for retrying a function with exponential backoff
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


def get_email_service():
    """Determine which email service to use based on environment variables"""
    # Check for Resend first (preferred)
    if os.environ.get('RESEND_API_KEY'):
        return 'resend'
    # Fall back to SMTP if configured
    if os.environ.get('EMAIL_SMTP_SERVER'):
        return 'smtp'
    return None


@retry(max_attempts=3, initial_delay=3)
def send_email_digest(articles, subject_prefix="[Research Update]", email_format="html",
                     include_links=True, max_articles=10):
    """
    Send an email digest of summarized articles
    """
    if not articles:
        logging.warning("No articles to send in digest. Skipping email.")
        return False

    # Limit number of articles
    if len(articles) > max_articles:
        logging.info(f"Limiting digest to {max_articles} articles")
        articles = articles[:max_articles]

    service = get_email_service()

    if service == 'resend':
        return send_via_resend(articles, subject_prefix, include_links)
    elif service == 'smtp':
        return send_via_smtp(articles, subject_prefix, email_format, include_links)
    else:
        raise ValueError("No email service configured. Set RESEND_API_KEY or SMTP configuration.")


def send_via_resend(articles, subject_prefix, include_links):
    """Send email via Resend API"""
    if not HTTPX_AVAILABLE:
        raise ImportError("httpx is required for Resend. Install with: pip install httpx")

    api_key = os.environ.get('RESEND_API_KEY')
    from_email = os.environ.get('EMAIL_FROM', 'Research Digest <digest@resend.dev>')
    to_email = os.environ.get('EMAIL_TO') or os.environ.get('EMAIL_RECIPIENT')

    if not api_key:
        raise ValueError("RESEND_API_KEY not configured")
    if not to_email:
        raise ValueError("EMAIL_TO or EMAIL_RECIPIENT not configured")

    today_date = datetime.now().strftime("%Y-%m-%d")
    subject = f"{subject_prefix} Research Digest - {today_date}"

    html_content = create_simple_html_digest(articles, include_links)
    text_content = create_plain_text_digest(articles, include_links)

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'from': from_email,
                'to': [to_email],
                'subject': subject,
                'html': html_content,
                'text': text_content
            }
        )

        if response.status_code != 200:
            error_detail = response.text
            raise RuntimeError(f"Resend API error {response.status_code}: {error_detail}")

        result = response.json()
        logging.info(f"Email digest sent via Resend to {to_email} (ID: {result.get('id', 'unknown')})")
        return True


def send_via_smtp(articles, subject_prefix, email_format, include_links):
    """Send email via SMTP (legacy method)"""
    sender_email = os.environ.get('EMAIL_SENDER')
    sender_password = os.environ.get('EMAIL_PASSWORD')
    recipient_email = os.environ.get('EMAIL_RECIPIENT')
    smtp_server = os.environ.get('EMAIL_SMTP_SERVER')
    smtp_port = int(os.environ.get('EMAIL_SMTP_PORT', 587))

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
        raise ValueError(f"Missing email configuration: {', '.join(missing_config)}")

    message = MIMEMultipart("alternative")
    today_date = datetime.now().strftime("%Y-%m-%d")
    message["Subject"] = f"{subject_prefix} Research Digest - {today_date}"
    message["From"] = sender_email
    message["To"] = recipient_email

    text_content = create_plain_text_digest(articles, include_links)
    html_content = create_simple_html_digest(articles, include_links) if email_format.lower() == "html" else text_content

    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")

    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, message.as_string())

        logging.info(f"Email digest sent via SMTP to {recipient_email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"Authentication error with SMTP server: {str(e)}")
        raise ValueError("Failed to authenticate with the SMTP server. Please check your email credentials.") from e

    except smtplib.SMTPServerDisconnected as e:
        logging.error(f"SMTP server disconnected: {str(e)}")
        raise ConnectionError("Connection to SMTP server was lost.") from e

    except smtplib.SMTPException as e:
        logging.error(f"SMTP error: {str(e)}")
        raise RuntimeError(f"SMTP error occurred: {str(e)}") from e

    except (ConnectionRefusedError, TimeoutError) as e:
        logging.error(f"Connection error: {str(e)}")
        raise ConnectionError(f"Could not connect to SMTP server at {smtp_server}:{smtp_port}") from e


def create_simple_html_digest(articles, include_links=True):
    """Create a simple HTML digest"""
    html = ["<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<title>Research Article Digest</title>",
            "</head>",
            "<body style='font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;'>",
            "<h1 style='color: #333;'>Research Article Digest</h1>",
            f"<p>Date: {datetime.now().strftime('%Y-%m-%d')} | Number of articles: {len(articles)}</p>"]

    for i, article in enumerate(articles, 1):
        title = article.get('title', 'No Title')
        url = article.get('url', '')
        source = article.get('source', 'Unknown')
        date = article.get('published_date', 'Unknown date')
        authors = article.get('authors', [])
        summary = article.get('summary', 'No summary available.')

        authors_str = ', '.join(authors) if authors else 'Unknown'
        title_html = f"<a href='{url}' style='color: #3498db;'>{title}</a>" if include_links and url else title

        html.append("<div style='margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #eee;'>")
        html.append(f"<h2 style='color: #2980b9; font-size: 18px;'>{title_html}</h2>")
        html.append("<div style='font-size: 13px; color: #666; margin-bottom: 10px;'>")
        html.append(f"<strong>Authors:</strong> {authors_str} | ")
        html.append(f"<strong>Source:</strong> {source} | ")
        html.append(f"<strong>Published:</strong> {date}")
        html.append("</div>")
        html.append("<div>")

        for paragraph in summary.split('\n'):
            if paragraph.strip():
                html.append(f"<p>{paragraph}</p>")

        html.append("</div>")
        html.append("</div>")

    html.append("<div style='margin-top: 30px; font-size: 12px; color: #999; text-align: center;'>")
    html.append("<p>This digest was automatically generated by the Research Article Reader and Summarizer.</p>")
    html.append("</div>")
    html.append("</body>")
    html.append("</html>")

    return "\n".join(html)


def create_plain_text_digest(articles, include_links=True):
    """Create plain text email digest"""
    content = []

    content.append("RESEARCH ARTICLE DIGEST")
    content.append("======================")
    content.append(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    content.append(f"Number of articles: {len(articles)}")
    content.append("\n")

    for i, article in enumerate(articles, 1):
        content.append(f"ARTICLE {i}: {article.get('title', 'No Title')}")
        content.append("-" * 40)

        if article.get('authors'):
            content.append(f"Authors: {', '.join(article.get('authors', []))}")
        content.append(f"Source: {article.get('source', 'Unknown')}")
        content.append(f"Published: {article.get('published_date', 'Unknown date')}")

        if include_links and article.get('url'):
            content.append(f"Link: {article.get('url')}")

        content.append("")
        content.append("SUMMARY:")
        content.append(article.get('summary', 'No summary available.'))
        content.append("\n")
        content.append("=" * 50)
        content.append("\n")

    content.append("\nThis digest was automatically generated by the Research Article Reader and Summarizer.")

    return "\n".join(content)
