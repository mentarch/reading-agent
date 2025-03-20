"""
Logging utility for the Research Article Reader and Summarizer
"""

import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def setup_logger(log_level='info', log_file=None):
    """
    Set up the application logger
    
    Args:
        log_level (str): Logging level (debug, info, warning, error, critical)
        log_file (str, optional): Path to log file. If None, logs to stdout.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
        print(f"Invalid log level: {log_level}, defaulting to INFO")
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates when reloading
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    formatter = logging.Formatter(log_format, date_format)
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Setup file handler if specified
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logging.info(f"Logging initialized at {log_level.upper()} level") 