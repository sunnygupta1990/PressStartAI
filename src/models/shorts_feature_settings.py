# src/models/shorts_feature_settings.py

"""Validated feature switches shared by Normal Mode and Facecam Mode."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.config import Config


@dataclass(frozen=True, slots=True)
class ShortsFeatureSettings:
    """Feature switches for Options 1 and 2."""

    captions_enabled: bool = False
    transcription_enabled: bool = True
    commentary_ai_enabled: bool = True
    visual_ai_enabled: bool = True
    fusion_ai_enabled: bool = True
    metadata_enabled: bool = False
    raw_highlight_export_enabled: bool = False
    keep_intermediate_files: bool = True

    @classmethod
    def load(cls, config: Config | None = None) -> "ShortsFeatureSettings":
        """Load validated switches with quality-preserving defaults."""

        application_config = config or Config()
        raw_section = application_config.data.get(
            "shorts_features",
            {},
        )

        if raw_section is None:
            raw_section = {}

        if not isinstance(raw_section, dict):
            raise ValueError(
                "config.yaml shorts_features must be a mapping."
            )

        settings = cls(
            captions_enabled=cls._read_boolean(
                raw_section,
                "captions_enabled",
                cls.captions_enabled,
            ),
            transcription_enabled=cls._read_boolean(
                raw_section,
                "transcription_enabled",
                cls.transcription_enabled,
            ),
            commentary_ai_enabled=cls._read_boolean(
                raw_section,
                "commentary_ai_enabled",
                cls.commentary_ai_enabled,
            ),
            visual_ai_enabled=cls._read_boolean(
                raw_section,
                "visual_ai_enabled",
                cls.visual_ai_enabled,
            ),
            fusion_ai_enabled=cls._read_boolean(
                raw_section,
                "fusion_ai_enabled",
                cls.fusion_ai_enabled,
            ),
            metadata_enabled=cls._read_boolean(
                raw_section,
                "metadata_enabled",
                cls.metadata_enabled,
            ),
            raw_highlight_export_enabled=cls._read_boolean(
                raw_section,
                "raw_highlight_export_enabled",
                cls.raw_highlight_export_enabled,
            ),
            keep_intermediate_files=cls._read_boolean(
                raw_section,
                "keep_intermediate_files",
                cls.keep_intermediate_files,
            ),
        )

        settings.validate()
        return settings

    def validate(self) -> None:
        """Reject feature combinations that cannot work correctly."""

        if self.commentary_ai_enabled and not self.transcription_enabled:
            raise ValueError(
                "commentary_ai_enabled requires "
                "transcription_enabled=true."
            )

        if self.fusion_ai_enabled and not self.commentary_ai_enabled:
            raise ValueError(
                "fusion_ai_enabled requires "
                "commentary_ai_enabled=true."
            )

        if self.fusion_ai_enabled and not self.visual_ai_enabled:
            raise ValueError(
                "fusion_ai_enabled requires visual_ai_enabled=true."
            )

    @staticmethod
    def _read_boolean(
        section: dict[str, Any],
        key: str,
        default: bool,
    ) -> bool:
        """Read one strict YAML boolean."""

        value = section.get(key, default)

        if not isinstance(value, bool):
            raise ValueError(
                f"shorts_features.{key} must be true or false."
            )

        return value
