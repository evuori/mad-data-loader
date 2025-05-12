"""
Logging configuration for the application.
"""

import logging
import logging.config
import os
from datetime import datetime
from typing import Dict, Any


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    Configure application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
    """
    # Create logs directory if a log file is specified
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    else:
        # Default log file in logs directory
        os.makedirs("logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = f"logs/ingestion_{timestamp}.log"
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure logging
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "level": numeric_level,
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "level": "DEBUG",
                "formatter": "detailed",
                "class": "logging.FileHandler",
                "filename": log_file,
                "mode": "a"
            }
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": True
            }
        }
    }
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Level: {log_level}, File: {log_file}")
    
    # Set library logging levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("chardet").setLevel(logging.WARNING) 