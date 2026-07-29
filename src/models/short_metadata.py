from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ShortMetadata:
    """AI-generated publishing metadata for one YouTube Short."""

    rank: int
    hook: str
    title: str
    description: str
    hashtags: list[str]
    thumbnail_prompt: str