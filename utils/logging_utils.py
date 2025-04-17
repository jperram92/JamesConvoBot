"""
Logging utilities for AI Meeting Assistant.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

from utils.config import get_config

# Get configuration
config = get_config()


def setup_logger(name: str, log_file: Optional[str] = None, level: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with the specified name, file, and level.
    
    Args:
        name: Name of the logger.
        log_file: Path to the log file. If None, uses the value from config.
        level: Logging level. If None, uses the value from config.
        
    Returns:
        Configured logger instance.
    """
    # Get log level from config if not provided
    if level is None:
        level = config.get('logging.level', 'INFO')
    
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log file is specified
    if log_file is None:
        log_file = config.get('logging.file', 'logs/assistant.log')
    
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Get max size and backup count from config
        max_size_mb = config.get('logging.max_size_mb', 10)
        backup_count = config.get('logging.backup_count', 5)
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Create a default logger
logger = setup_logger('ai_meeting_assistant')
