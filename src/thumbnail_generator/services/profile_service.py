"""Load and validate thumbnail-generator channel profiles."""

from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as error:
    raise RuntimeError(
        "PyYAML is required. Install it with: pip install PyYAML"
    ) from error


DEFAULT_CONFIG_PATH = Path("config/thumbnail_generator/profiles.yaml")


class ProfileServiceError(Exception):
    """Raised when channel profile configuration is invalid."""


def load_profiles(
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict[str, dict[str, Any]]:
    """Load all configured channel profiles."""

    if not config_path.exists():
        raise ProfileServiceError(
            f"Profile configuration file was not found: {config_path}"
        )

    try:
        raw_config = yaml.safe_load(
            config_path.read_text(encoding="utf-8")
        )
    except yaml.YAMLError as error:
        raise ProfileServiceError(
            f"Invalid YAML in profile configuration: {error}"
        ) from error
    except OSError as error:
        raise ProfileServiceError(
            f"Unable to read profile configuration: {error}"
        ) from error

    if not isinstance(raw_config, dict):
        raise ProfileServiceError(
            "Profile configuration must contain a YAML mapping."
        )

    profiles = raw_config.get("profiles")

    if not isinstance(profiles, dict) or not profiles:
        raise ProfileServiceError(
            "Profile configuration must contain at least one profile."
        )

    validated_profiles: dict[str, dict[str, Any]] = {}

    for profile_key, profile_data in profiles.items():
        validated_profiles[profile_key] = _validate_profile(
            profile_key,
            profile_data,
        )

    return validated_profiles


def get_profile(
    profile_key: str,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    """Load one channel profile by its configuration key."""

    profiles = load_profiles(config_path)

    if profile_key not in profiles:
        available_profiles = ", ".join(sorted(profiles))
        raise ProfileServiceError(
            f"Unknown profile '{profile_key}'. "
            f"Available profiles: {available_profiles}"
        )

    return profiles[profile_key]


def list_profile_choices(
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> list[tuple[str, str]]:
    """Return profile keys and display names for CLI menus."""

    profiles = load_profiles(config_path)

    return [
        (profile_key, profile["channel_name"])
        for profile_key, profile in profiles.items()
    ]


def _validate_profile(
    profile_key: str,
    profile_data: Any,
) -> dict[str, Any]:
    """Validate one channel profile."""

    if not isinstance(profile_data, dict):
        raise ProfileServiceError(
            f"Profile '{profile_key}' must contain a YAML mapping."
        )

    required_fields = (
        "channel_name",
        "target_audience",
        "preferred_language",
        "brand_colors",
        "logo",
        "creator_photos_folder",
        "style",
        "ai_face_generation",
    )

    missing_fields = [
        field
        for field in required_fields
        if field not in profile_data
    ]

    if missing_fields:
        missing_text = ", ".join(missing_fields)
        raise ProfileServiceError(
            f"Profile '{profile_key}' is missing: {missing_text}"
        )

    if not isinstance(profile_data["channel_name"], str):
        raise ProfileServiceError(
            f"Profile '{profile_key}' has an invalid channel_name."
        )

    if not isinstance(profile_data["brand_colors"], list):
        raise ProfileServiceError(
            f"Profile '{profile_key}' must define brand_colors as a list."
        )

    creator_photos_folder = Path(
        str(profile_data["creator_photos_folder"])
    )

    validated_profile = dict(profile_data)
    validated_profile["profile_key"] = profile_key
    validated_profile["creator_photos_folder"] = str(
        creator_photos_folder
    )

    return validated_profile