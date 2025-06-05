import logging
import requests

CROSSREF_API = "https://api.crossref.org/works"


def get_article_citation_count(doi=None, title=None):
    """Return citation count for an article using Crossref."""
    if not doi and not title:
        return 0
    try:
        if doi:
            url = f"{CROSSREF_API}/{doi}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json().get("message", {})
        else:
            url = f"{CROSSREF_API}?query.bibliographic={requests.utils.quote(title)}&rows=1"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            items = response.json().get("message", {}).get("items", [])
            data = items[0] if items else {}
        return int(data.get("is-referenced-by-count", 0))
    except Exception as e:
        logging.error(f"Error fetching citation count: {e}")
        return 0


def get_journal_h_index(journal, rows=100):
    """Approximate journal h-index using Crossref citation counts."""
    if not journal:
        return 0
    try:
        url = f"{CROSSREF_API}?filter=container-title:{requests.utils.quote(journal)}&rows={rows}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        items = response.json().get("message", {}).get("items", [])
        citations = sorted(
            [int(it.get("is-referenced-by-count", 0)) for it in items], reverse=True
        )
        h = 0
        for i, c in enumerate(citations, 1):
            if c >= i:
                h = i
            else:
                break
        return h
    except Exception as e:
        logging.error(f"Error fetching journal metrics: {e}")
        return 0
