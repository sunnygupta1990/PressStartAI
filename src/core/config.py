"""
Configuration management for PressStartAI.
"""

from pathlib import Path
import yaml


class Config:
    """Loads application configuration."""

    def __init__(self) -> None:
        config_path = Path("config/config.yaml")

        with config_path.open("r", encoding="utf-8") as f:
            self.data = yaml.safe_load(f)

    def get(self, *keys):
        value = self.data

        for key in keys:
            value = value[key]

        return value