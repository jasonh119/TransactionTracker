import logging
import os
from logging.handlers import RotatingFileHandler
from config import ROOT_DIR

def setup_logger(name):
    """
    Set up a logger with consistent formatting and handlers.
    Logs will be written to both console and a rotating file.
    """
    logger = logging.getLogger(name)
    
    # Only set up handlers if they haven't been set up already
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(ROOT_DIR, 'logs')
        os.makedirs(logs_dir, exist_ok=True)

        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )

        # File handler (rotating log files, max 5MB each, keep 5 backup files)
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'transaction_tracker.log'),
            maxBytes=5*1024*1024,
            backupCount=5
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
