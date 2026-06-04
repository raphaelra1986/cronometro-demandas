# logger.py
"""Sistema de logging centralizado da aplicação."""

from __future__ import annotations
import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Tuple, Type
from types import TracebackType

LOG_FILE = "cronometro.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3


def setup_logger(name: str = "cronometro", log_file: str = LOG_FILE) -> logging.Logger:
    """
    Setup and return a logger with file rotation and console output.
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # Console handler for errors
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def setup_exception_handler(logger: logging.Logger):
    """
    Setup global exception handler to log uncaught exceptions.
    """
    def exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_handler


# Global logger instance
logger = setup_logger()
setup_exception_handler(logger)


def log_info(message: str):
    """Log info message."""
    logger.info(message)


def log_warning(message: str):
    """Log warning message."""
    logger.warning(message)


def log_error(message: str, exc_info: bool = False):
    """Log error message."""
    logger.error(message, exc_info=exc_info)


def log_debug(message: str):
    """Log debug message."""
    logger.debug(message)


def log_operation(operation: str, details: str = ""):
    """Log an operation with timestamp."""
    msg = f"OPERATION: {operation}"
    if details:
        msg += f" - {details}"
    logger.info(msg)
