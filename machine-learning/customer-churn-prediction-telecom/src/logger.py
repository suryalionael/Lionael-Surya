import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = "telecom_churn", log_file: str = "logs/pipeline.log", level=logging.INFO) -> logging.Logger:
    """Sets up a logger that logs to both console and a rotating log file."""
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger is already configured
    if logger.hasHandlers():
        return logger

    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)

    # File Handler (Rotating, max 5MB, keep 3 backups)
    file_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    # Prevent logs from propagating to root logger
    logger.propagate = False

    return logger

# Create a default logger instance
logger = setup_logger()
