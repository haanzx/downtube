"""Centralized logging."""

import logging
from typing import Any


def get_logger(name: str, **kwargs: Any) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(f"downtube.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
    return logger
