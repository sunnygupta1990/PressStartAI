"""
Logging configuration for PressStartAI.
"""

from pathlib import Path
import logging
import logging.config

import yaml


def setup_logger() -> logging.Logger:
    """Configure application logging."""

    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    config_file = Path("config") / "logging.yaml"

    with config_file.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    logging.config.dictConfig(config)

    return logging.getLogger("PressStartAI")