
from __future__ import annotations

CATEGORY_ALIASES = {
    "combat": "Fight",
    "fight": "Fight",
    "battle": "Fight",
    "action": "Fight",
    "running": "Running",
    "movement": "Running",
    "travel": "Running",
    "exploration": "Exploration",
    "discover": "Exploration",
    "cinematic": "Cinematic",
    "cinematic_shot": "Cinematic",
    "dialogue": "Dialogue",
    "conversation": "Dialogue",
    "speech": "Dialogue",
    "character": "Character",
    "character_closeup": "Character",
    "character_fullbody": "Character",
    "item": "Items",
    "pickup": "Items",
    "loot": "Items",
    "vehicle": "Vehicles",
    "driving": "Vehicles",
    "boss": "Boss",
    "boss_fight": "Boss",
    "environment": "Environment",
    "scenery": "Environment",
    "puzzle": "Puzzle",
    "cutscene": "Cutscene",
    "menu": "Other",
    "loading": "Other",
    "other": "Other",
}

ALLOWED_CATEGORIES = (
    "Fight", "Running", "Exploration", "Cinematic", "Dialogue", "Character",
    "Items", "Vehicles", "Boss", "Environment", "Puzzle", "Cutscene", "Other",
)


def normalize_category(value: str | None) -> str:
    key = (value or "").strip().lower().replace(" ", "_")
    return CATEGORY_ALIASES.get(key, "Other")


def character_subcategory(shot_type: str, description: str) -> str:
    text = f"{shot_type} {description}".lower()
    if "close" in text or "portrait" in text or "face" in text:
        return "Closeup"
    if "full body" in text or "fullbody" in text:
        return "FullBody"
    if "outfit" in text or "appearance" in text or "costume" in text:
        return "DifferentAppearance"
    return "Other"
