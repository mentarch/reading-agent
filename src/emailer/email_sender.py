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
    """Decorator for retrying a function with exponential backoff"""
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
    if os.environ.get('RESEND_API_KEY'):
        return 'resend'
    if os.environ.get('EMAIL_SMTP_SERVER'):
        return 'smtp'
    return None


@retry(max_attempts=3, initial_delay=3)
def send_email_digest(articles, subject_prefix="[Research Update]", email_format="html",
                     include_links=True, max_articles=10):
    """Send an email digest of summarized articles"""
    if not articles:
        logging.warning("No articles to send in digest. Skipping email.")
        return False

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

    today_date = datetime.now().strftime("%B %d, %Y")
    subject = f"{subject_prefix} {len(articles)} New Articles - {today_date}"

    html_content = create_html_digest(articles, include_links)
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
    today_date = datetime.now().strftime("%B %d, %Y")
    message["Subject"] = f"{subject_prefix} {len(articles)} New Articles - {today_date}"
    message["From"] = sender_email
    message["To"] = recipient_email

    text_content = create_plain_text_digest(articles, include_links)
    html_content = create_html_digest(articles, include_links) if email_format.lower() == "html" else text_content

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
        raise ValueError("Failed to authenticate with SMTP server.") from e
    except smtplib.SMTPServerDisconnected as e:
        logging.error(f"SMTP server disconnected: {str(e)}")
        raise ConnectionError("Connection to SMTP server was lost.") from e
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error: {str(e)}")
        raise RuntimeError(f"SMTP error occurred: {str(e)}") from e
    except (ConnectionRefusedError, TimeoutError) as e:
        logging.error(f"Connection error: {str(e)}")
        raise ConnectionError(f"Could not connect to SMTP server at {smtp_server}:{smtp_port}") from e


# Color scheme for sources
SOURCE_COLORS = {
    'arxiv': {'bg': '#b31b1b', 'text': '#ffffff'},
    'pubmed': {'bg': '#326599', 'text': '#ffffff'},
    'biorxiv': {'bg': '#782624', 'text': '#ffffff'},
    'medrxiv': {'bg': '#0047AB', 'text': '#ffffff'},
    'default': {'bg': '#6c757d', 'text': '#ffffff'},
}


def get_source_color(source):
    """Get color scheme for a source"""
    source_lower = source.lower()
    for key in SOURCE_COLORS:
        if key in source_lower:
            return SOURCE_COLORS[key]
    return SOURCE_COLORS['default']


def create_html_digest(articles, include_links=True):
    """Create a modern, mobile-friendly HTML email digest"""
    today = datetime.now()
    date_str = today.strftime("%B %d, %Y")

    # Group articles by source for the summary
    sources = {}
    for article in articles:
        src = article.get('source', 'Unknown')
        sources[src] = sources.get(src, 0) + 1

    source_summary = " · ".join([f"{count} from {src}" for src, count in sources.items()])

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Digest</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f7; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f4f4f7;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width: 600px; width: 100%;">

                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; border-radius: 12px 12px 0 0;">
                            <h1 style="margin: 0 0 10px 0; color: #ffffff; font-size: 28px; font-weight: 700;">
                                📚 Research Digest
                            </h1>
                            <p style="margin: 0; color: rgba(255,255,255,0.9); font-size: 16px;">
                                {date_str} · {len(articles)} new articles
                            </p>
                            <p style="margin: 10px 0 0 0; color: rgba(255,255,255,0.7); font-size: 14px;">
                                {source_summary}
                            </p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="background-color: #ffffff; padding: 30px;">
'''

    # Add each article
    for i, article in enumerate(articles):
        title = article.get('title', 'No Title')
        url = article.get('url', '')
        source = article.get('source', 'Unknown')
        pub_date = article.get('published_date', '')
        authors = article.get('authors', [])
        summary = article.get('summary', 'No summary available.')
        score = article.get('relevance_score', None)

        # Get source colors
        colors = get_source_color(source)

        # Format authors (truncate if too many)
        if authors:
            if len(authors) > 3:
                authors_str = f"{authors[0]} et al."
            else:
                authors_str = ", ".join(authors)
        else:
            authors_str = ""

        # Title with optional link
        if include_links and url:
            title_html = f'<a href="{url}" style="color: #1a1a2e; text-decoration: none;">{title}</a>'
        else:
            title_html = title

        # Score badge if available
        score_badge = ""
        if score is not None:
            score_color = "#10b981" if score >= 0.7 else "#f59e0b" if score >= 0.4 else "#6b7280"
            score_badge = f'''
                <span style="display: inline-block; background-color: {score_color}; color: white; font-size: 11px; padding: 2px 8px; border-radius: 10px; margin-left: 8px;">
                    {int(score * 100)}% match
                </span>
            '''

        # Add spacing between articles (not before first)
        margin_top = "30px" if i > 0 else "0"

        html += f'''
                            <!-- Article {i + 1} -->
                            <div style="margin-top: {margin_top}; padding-bottom: 25px; border-bottom: 1px solid #e5e7eb;">
                                <!-- Source badge -->
                                <div style="margin-bottom: 12px;">
                                    <span style="display: inline-block; background-color: {colors['bg']}; color: {colors['text']}; font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.5px;">
                                        {source}
                                    </span>
                                    {score_badge}
                                </div>

                                <!-- Title -->
                                <h2 style="margin: 0 0 10px 0; font-size: 18px; font-weight: 600; line-height: 1.4;">
                                    {title_html}
                                </h2>

                                <!-- Meta info -->
                                <p style="margin: 0 0 15px 0; font-size: 13px; color: #6b7280;">
                                    {f'<span style="color: #374151;">{authors_str}</span> · ' if authors_str else ''}{pub_date if pub_date else ''}
                                </p>

                                <!-- Summary -->
                                <p style="margin: 0; font-size: 15px; line-height: 1.6; color: #374151;">
                                    {summary}
                                </p>

                                <!-- Read more link -->
                                {f'<p style="margin: 15px 0 0 0;"><a href="{url}" style="color: #667eea; font-size: 14px; font-weight: 500; text-decoration: none;">Read full paper →</a></p>' if include_links and url else ''}
                            </div>
'''

    # Footer
    html += f'''
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 25px 30px; border-radius: 0 0 12px 12px; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 10px 0; font-size: 13px; color: #6b7280; text-align: center;">
                                This digest was automatically generated by your Research Agent.
                            </p>
                            <p style="margin: 0; font-size: 12px; color: #9ca3af; text-align: center;">
                                Tracking {len(sources)} sources · Next digest in 6 hours
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>'''

    return html


def create_plain_text_digest(articles, include_links=True):
    """Create plain text email digest"""
    today = datetime.now()
    date_str = today.strftime("%B %d, %Y")

    lines = []
    lines.append("=" * 50)
    lines.append(f"RESEARCH DIGEST - {date_str}")
    lines.append(f"{len(articles)} New Articles")
    lines.append("=" * 50)
    lines.append("")

    for i, article in enumerate(articles, 1):
        title = article.get('title', 'No Title')
        url = article.get('url', '')
        source = article.get('source', 'Unknown')
        pub_date = article.get('published_date', '')
        authors = article.get('authors', [])
        summary = article.get('summary', 'No summary available.')
        score = article.get('relevance_score', None)

        lines.append(f"[{i}] {title}")
        lines.append("-" * 40)
        lines.append(f"Source: {source}")
        if authors:
            lines.append(f"Authors: {', '.join(authors[:3])}{'...' if len(authors) > 3 else ''}")
        if pub_date:
            lines.append(f"Published: {pub_date}")
        if score is not None:
            lines.append(f"Relevance: {int(score * 100)}%")
        if include_links and url:
            lines.append(f"Link: {url}")
        lines.append("")
        lines.append(summary)
        lines.append("")
        lines.append("=" * 50)
        lines.append("")

    lines.append("This digest was automatically generated by your Research Agent.")

    return "\n".join(lines)
