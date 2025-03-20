"""
Configuration loader for the Research Article Reader and Summarizer
"""

import os
import yaml
import logging

DEFAULT_CONFIG_PATH = 'config.yaml'

def load_config(config_path=None):
    """
    Load the application configuration from YAML file
    
    Args:
        config_path (str, optional): Path to the config file. Defaults to 'config.yaml'.
        
    Returns:
        dict: Configuration dictionary
    
    Raises:
        FileNotFoundError: If the config file is not found
        yaml.YAMLError: If the config file is invalid
    """
    if not config_path:
        config_path = os.environ.get('CONFIG_PATH', DEFAULT_CONFIG_PATH)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as config_file:
            config = yaml.safe_load(config_file)
            
        # Validate required sections
        required_sections = ['sources', 'topics', 'email', 'app']
        for section in required_sections:
            if section not in config:
                logging.warning(f"Missing required config section: {section}")
                config[section] = {}
                
        return config
        
    except FileNotFoundError:
        logging.error(f"Config file not found at {config_path}")
        # Return default configuration
        return {
            'sources': [],
            'topics': [],
            'email': {'schedule': 'daily'},
            'app': {'update_frequency': '6h', 'log_level': 'info'}
        }
        
    except yaml.YAMLError as e:
        logging.error(f"Error parsing config file: {str(e)}")
        raise 