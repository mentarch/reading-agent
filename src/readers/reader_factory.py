"""
Reader factory for creating appropriate reader objects based on configuration
"""

import logging
from .rss_reader import RSSReader
from .api_reader import APIReader

def create_readers(sources_config):
    """
    Create reader objects for each configured source
    
    Args:
        sources_config (list): List of source configurations from config.yaml
        
    Returns:
        list: List of reader objects
    """
    readers = []
    
    if not sources_config:
        logging.warning("No sources configured")
        return readers
    
    for source in sources_config:
        # Skip disabled sources
        if not source.get('enabled', True):
            logging.info(f"Skipping disabled source: {source.get('name')}")
            continue
            
        source_type = source.get('type', '').lower()
        source_name = source.get('name', 'Unknown Source')
        
        try:
            if source_type == 'rss':
                readers.append(RSSReader(
                    name=source_name,
                    url=source.get('url'),
                    params=source.get('params', {})
                ))
                logging.info(f"Created RSS reader for {source_name}")
                
            elif source_type == 'api':
                readers.append(APIReader(
                    name=source_name,
                    url=source.get('url'),
                    headers=source.get('headers', {}),
                    params=source.get('params', {})
                ))
                logging.info(f"Created API reader for {source_name}")
                
            else:
                logging.error(f"Unknown source type: {source_type} for {source_name}")
                
        except Exception as e:
            logging.error(f"Failed to create reader for {source_name}: {str(e)}")
    
    logging.info(f"Created {len(readers)} reader(s)")
    return readers 