import logging
import os
from logging.handlers import RotatingFileHandler
from config import config

def setup_logger(name):
    """
    Set up a logger with consistent formatting and handlers.
    Logs will be written to both console and a rotating file.
    """
    logger = logging.getLogger(name)
    
    # Only set up handlers if they haven't been set up already
    if not logger.handlers:
        # Get log level from config, default to INFO
        log_level = getattr(logging, config.get('logging.level', 'INFO'))
        logger.setLevel(log_level)

        # Get log format from config or use defaults
        file_format = config.get('logging.format',
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        console_format = '%(asctime)s - %(levelname)s - %(message)s'

        # Create formatters
        file_formatter = logging.Formatter(file_format)
        console_formatter = logging.Formatter(console_format)

        # File handler (rotating log files, max 5MB each, keep 5 backup files)
        log_file = config.logs_dir / 'transaction_tracker.log'
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=5*1024*1024,
            backupCount=5
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(log_level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(log_level)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
