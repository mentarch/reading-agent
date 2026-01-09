"""
Source catalog with pre-configured RSS feeds for popular research sources

Users can reference sources by name in config.yaml instead of manually
entering URLs. Example:
    sources:
      - preset: arxiv-cs-cv
      - preset: arxiv-cs-ai
        enabled: false
"""

# Pre-configured source catalog
# Each entry contains: name, type, url, and optional description
SOURCE_CATALOG = {
    # ===== arXiv Computer Science =====
    "arxiv-cs-cv": {
        "name": "arXiv CS - Computer Vision",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/cs.CV",
        "description": "Computer vision and pattern recognition papers",
    },
    "arxiv-cs-ai": {
        "name": "arXiv CS - Artificial Intelligence",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/cs.AI",
        "description": "General AI research papers",
    },
    "arxiv-cs-lg": {
        "name": "arXiv CS - Machine Learning",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/cs.LG",
        "description": "Machine learning research papers",
    },
    "arxiv-cs-cl": {
        "name": "arXiv CS - Computation & Language",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/cs.CL",
        "description": "NLP and computational linguistics papers",
    },
    "arxiv-cs-ro": {
        "name": "arXiv CS - Robotics",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/cs.RO",
        "description": "Robotics research papers",
    },
    "arxiv-cs-ne": {
        "name": "arXiv CS - Neural & Evolutionary",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/cs.NE",
        "description": "Neural networks and evolutionary computation",
    },
    "arxiv-cs-ir": {
        "name": "arXiv CS - Information Retrieval",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/cs.IR",
        "description": "Search engines and information retrieval",
    },
    "arxiv-cs-hc": {
        "name": "arXiv CS - Human-Computer Interaction",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/cs.HC",
        "description": "HCI and user interface research",
    },
    "arxiv-cs-se": {
        "name": "arXiv CS - Software Engineering",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/cs.SE",
        "description": "Software engineering research",
    },
    "arxiv-cs-cr": {
        "name": "arXiv CS - Cryptography & Security",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/cs.CR",
        "description": "Cryptography and security research",
    },

    # ===== arXiv Other Fields =====
    "arxiv-stat-ml": {
        "name": "arXiv Statistics - Machine Learning",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/stat.ML",
        "description": "Statistical machine learning papers",
    },
    "arxiv-eess-iv": {
        "name": "arXiv EESS - Image & Video Processing",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/eess.IV",
        "description": "Signal processing for images and video",
    },
    "arxiv-quant-ph": {
        "name": "arXiv - Quantum Physics",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/quant-ph",
        "description": "Quantum computing and quantum physics",
    },
    "arxiv-physics": {
        "name": "arXiv - Physics",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/physics",
        "description": "General physics papers",
    },
    "arxiv-math": {
        "name": "arXiv - Mathematics",
        "type": "rss",
        "url": "https://rss.arxiv.org/rss/math",
        "description": "Mathematics research papers",
    },

    # ===== Biomedical =====
    "biorxiv-all": {
        "name": "bioRxiv - All Subjects",
        "type": "rss",
        "url": "http://connect.biorxiv.org/biorxiv_xml.php?subject=all",
        "description": "All bioRxiv preprints",
    },
    "biorxiv-neuroscience": {
        "name": "bioRxiv - Neuroscience",
        "type": "rss",
        "url": "http://connect.biorxiv.org/biorxiv_xml.php?subject=neuroscience",
        "description": "Neuroscience preprints",
    },
    "biorxiv-bioinformatics": {
        "name": "bioRxiv - Bioinformatics",
        "type": "rss",
        "url": "http://connect.biorxiv.org/biorxiv_xml.php?subject=bioinformatics",
        "description": "Bioinformatics preprints",
    },
    "medrxiv-all": {
        "name": "medRxiv - All Subjects",
        "type": "rss",
        "url": "http://connect.medrxiv.org/medrxiv_xml.php?subject=all",
        "description": "All medRxiv preprints",
    },

    # ===== Tech News =====
    "hacker-news": {
        "name": "Hacker News - Best",
        "type": "rss",
        "url": "https://hnrss.org/best",
        "description": "Top stories from Hacker News",
    },
    "lobsters": {
        "name": "Lobsters",
        "type": "rss",
        "url": "https://lobste.rs/rss",
        "description": "Lobsters tech community links",
    },

    # ===== Science & Nature (require institutional access for full text) =====
    "nature-latest": {
        "name": "Nature - Latest Research",
        "type": "rss",
        "url": "https://www.nature.com/nature.rss",
        "description": "Latest research from Nature",
    },
    "science-latest": {
        "name": "Science Magazine - Latest",
        "type": "rss",
        "url": "https://www.science.org/rss/news_current.xml",
        "description": "Latest from Science magazine",
    },
}


def get_source_config(preset_name: str) -> dict | None:
    """
    Get source configuration for a preset name

    Args:
        preset_name: Name of the preset (e.g., 'arxiv-cs-cv')

    Returns:
        Source configuration dict or None if not found
    """
    return SOURCE_CATALOG.get(preset_name)


def list_available_presets() -> list[dict]:
    """
    List all available source presets

    Returns:
        List of preset info dicts with name, description
    """
    return [
        {
            "preset": key,
            "name": config["name"],
            "description": config.get("description", ""),
        }
        for key, config in SOURCE_CATALOG.items()
    ]


def expand_source_config(source: dict) -> dict:
    """
    Expand a source config, resolving presets if present

    Args:
        source: Source configuration dict (may contain 'preset' key)

    Returns:
        Expanded source configuration
    """
    if "preset" in source:
        preset_name = source["preset"]
        preset_config = get_source_config(preset_name)

        if preset_config is None:
            raise ValueError(f"Unknown source preset: {preset_name}")

        # Merge preset with user overrides (user settings take precedence)
        expanded = preset_config.copy()
        for key, value in source.items():
            if key != "preset":
                expanded[key] = value

        return expanded

    return source
