"""
Logging configuration for Kalshi NBA Paper Trading Application.

Provides structured logging with JSON formatting for production environments.
Uses standard Python logging with configurable levels.
"""

import logging
import sys
from typing import Optional
from datetime import datetime

from backend.config.settings import settings


# ============================================================================
# Custom JSON Formatter
# ============================================================================

class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format.

    Useful for log aggregation tools like Datadog, Elasticsearch, etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON-formatted log string.
        """
        import json

        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add custom fields if present
        if hasattr(record, "custom_fields"):
            log_data.update(record.custom_fields)

        return json.dumps(log_data)


# ============================================================================
# Standard Formatter
# ============================================================================

class StandardFormatter(logging.Formatter):
    """Standard formatter for development environments."""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


# ============================================================================
# Logger Setup
# ============================================================================

def setup_logging(
    log_level: Optional[str] = None,
    use_json: bool = False
) -> None:
    """
    Configure application logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, uses settings.log_level.
        use_json: Whether to use JSON formatting (default: False).
    """
    if log_level is None:
        log_level = settings.log_level

    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Set formatter based on environment
    if use_json or settings.environment.lower() == "production":
        formatter = JSONFormatter()
    else:
        formatter = StandardFormatter()

    console_handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Log setup completion
    root_logger.info(
        f"Logging configured: level={log_level}, json={use_json}, env={settings.environment}"
    )


# ============================================================================
# Helper Functions
# ============================================================================

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Name of the logger (typically __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **context
) -> None:
    """
    Log a message with additional context fields.

    Args:
        logger: Logger instance to use.
        level: Log level (debug, info, warning, error, critical).
        message: Log message.
        **context: Additional context fields to include in log.
    """
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "(unknown file)",
        0,
        message,
        (),
        None
    )
    record.custom_fields = context
    logger.handle(record)


# ============================================================================
# Initialize Logging on Module Import
# ============================================================================

# Setup logging when module is imported
setup_logging()
