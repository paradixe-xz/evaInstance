"""
Logging configuration for the WhatsApp AI Backend
"""

import logging
import logging.handlers
import os
import sys
from typing import Optional

from .config import get_settings

settings = get_settings()


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True  # Enabled by default for debugging
) -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        enable_console: Whether to enable console logging
    
    Returns:
        Configured logger instance
    """
    # Use settings if not provided
    log_level = log_level or settings.log_level
    log_file = log_file or settings.log_file_path
    
    # Create logger
    logger = logging.getLogger("whatsapp_ai")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler (only if enabled)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler (always enabled)
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=int(settings.log_max_size),
            backupCount=int(settings.log_backup_count)
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Disable SQLAlchemy console logging completely
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
    
    # Enable uvicorn access logs for debugging
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    # Set root logger level
    if not enable_console:
        logging.getLogger().setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str = "whatsapp_ai") -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


# Logger will be initialized when setup_logging() is called