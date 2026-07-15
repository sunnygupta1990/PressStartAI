import json
import re
import subprocess

from src.models.final_highlight import FinalHighlight
from src.models.short_metadata import ShortMetadata
from src.services.ai_text_cleaner import AITextCleaner


class ShortMetadataGenerator:
    """Generate YouTube Short publishing metadata with local AI."""

    MODEL_NAME = "gemma3:4b"

    OLLAMA_EXECUTABLE = (
        r"C:\Users\SunGupta\AppData\Local\Programs\Ollama\ollama.exe"
    )

    ANSI_ESCAPE_PATTERN = re.compile(
        r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
    )

    DISALLOWED_SCRIPT_PATTERN = re.compile(
        r"[\u0B80-\u0BFF"
        r"\u0C00-\u0C7F"
        r"\u0C80-\u0CFF"
        r"\u0D00-\u0D7F]"
    )

    MAXIMUM_ATTEMPTS = 3

    def __init__(self) -> None:
        self.text_cleaner = AITextCleaner()

    def generate(
        self,
        highlight: FinalHighlight,
    ) -> ShortMetadata:
        for attempt in range(
            1,
            self.MAXIMUM_ATTEMPTS + 1,
        ):
            prompt = self._build_prompt(
                highlight=highlight,
                attempt=attempt,
            )

            process = subprocess.run(
                [
                    self.OLLAMA_EXECUTABLE,
                    "run",
                    self.MODEL_NAME,
                ],
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
            )

            data = self._parse_response(
                process.stdout
            )

            metadata = self._build_metadata(
                highlight=highlight,
                data=data,
            )

            if self._is_valid(
                metadata
            ):
                return metadata

        return self._build_fallback_metadata(
            highlight
        )

    def _build_metadata(
        self,
        highlight: FinalHighlight,
        data: dict[str, object],
    ) -> ShortMetadata:
        hashtags = data.get(
            "hashtags",
            [],
        )

        if not isinstance(
            hashtags,
            list,
        ):
            hashtags = []

        return ShortMetadata(
            rank=highlight.rank,
            hook=self.text_cleaner.clean(
                str(
                    data.get(
                        "hook",
                        "",
                    )
                )
            ),
            title=self.text_cleaner.clean(
                str(
                    data.get(
                        "title",
                        "",
                    )
                )
            ),
            description=self.text_cleaner.clean(
                str(
                    data.get(
                        "description",
                        "",
                    )
                )
            ),
            hashtags=[
                self.text_cleaner.clean(
                    str(hashtag)
                )
                for hashtag in hashtags
                if str(hashtag).strip()
            ],
            thumbnail_prompt=self.text_cleaner.clean(
                str(
                    data.get(
                        "thumbnail_prompt",
                        "",
                    )
                )
            ),
        )

    @classmethod
    def _is_valid(
        cls,
        metadata: ShortMetadata,
    ) -> bool:
        required_text = [
            metadata.hook,
            metadata.title,
            metadata.description,
            metadata.thumbnail_prompt,
        ]

        if any(
            not value.strip()
            for value in required_text
        ):
            return False

        if not metadata.hashtags:
            return False

        if len(metadata.title) > 70:
            return False

        if any(
            not hashtag.startswith("#")
            for hashtag in metadata.hashtags
        ):
            return False

        combined_text = " ".join(
            [
                metadata.hook,
                metadata.title,
                metadata.description,
                metadata.thumbnail_prompt,
            ]
        )

        if cls.DISALLOWED_SCRIPT_PATTERN.search(
            combined_text
        ):
            return False

        return True

    @staticmethod
    def _build_fallback_metadata(
        highlight: FinalHighlight,
    ) -> ShortMetadata:
        category = (
            highlight.category.strip().lower()
            or "gaming"
        )

        if category == "rage":
            hook = "BHAI YE KYA HO RAHA HAI?!"
            title = "Gaming Ne Aaj Dimag Hila Diya 😭"
        elif category == "reaction":
            hook = "BHAI YE KYA THA?!"
            title = "I Was NOT Ready For This 😭"
        elif category == "combat":
            hook = "YE FIGHT ITNI INTENSE KYU HAI?!"
            title = "This Fight Got Intense FAST 😳"
        else:
            hook = "BHAI YE KYA HO GAYA?!"
            title = "This Gaming Moment Was Unexpected 😳"

        return ShortMetadata(
            rank=highlight.rank,
            hook=hook,
            title=title,
            description=(
                "Ek aur crazy gaming moment! "
                "Press Start with Sunny par "
                "real reactions aur gameplay."
            ),
            hashtags=[
                "#Gaming",
                "#HindiGaming",
                "#GamingShorts",
                "#Reaction",
                "#Gameplay",
            ],
            thumbnail_prompt=(
                "Sunny with real facial identity preserved, "
                "wearing a black hoodie, expression matching "
                f"a {category} gaming moment, blue and black "
                "gaming branding, dramatic gameplay background "
                f"based on: {highlight.visual_event}, "
                "high contrast, vertical gaming Short cover, "
                f"suggested cover text: '{hook}'"
            ),
        )

    @staticmethod
    def _build_prompt(
        highlight: FinalHighlight,
        attempt: int,
    ) -> str:
        transcript = (
            highlight.transcript_text.strip()
            or "[NO CLEAR SPEECH]"
        )

        retry_instruction = ""

        if attempt > 1:
            retry_instruction = """
IMPORTANT RETRY:
The previous response was invalid.
Return complete JSON with every field populated.
Do not use Tamil, Telugu, Kannada, or Malayalam text.
Use only Hindi in Devanagari, Hinglish in Latin letters,
or simple English.
"""

        return f"""
You are creating YouTube Shorts metadata for the gaming channel
"Press Start with Sunny".

The channel style is:
- Hindi and Hinglish gaming
- natural reactions
- funny failures
- rage moments
- boss fights
- story gameplay
- genuine reactions
- Indian gaming audience

Highlight category:
{highlight.category}

Event summary:
{highlight.event_summary}

Commentary category:
{highlight.commentary_category}

Visual event:
{highlight.visual_event}

Action level:
{highlight.action_level}

Danger level:
{highlight.danger_level}

Approximate commentary transcript:
{transcript}

The transcript may contain speech recognition errors.
Do not repeat obvious transcription mistakes as factual words.

LANGUAGE RULE:
Use only:
- Hindi written in Devanagari
- Hinglish written with Latin letters
- simple English

Never use Tamil, Telugu, Kannada, Malayalam,
or any other Indian script.

Create publishing metadata for one YouTube Short.

Hook rules:
- very short
- strong first-second text
- Hinglish or simple English
- natural gaming reaction style
- no fake claims

Title rules:
- catchy
- suitable for YouTube Shorts
- maximum 70 characters
- natural, not corporate
- do not invent a game name if it is unknown

Description rules:
- maximum 3 short lines
- Hindi/Hinglish tone
- mention Press Start with Sunny naturally
- do not invent facts

Hashtag rules:
- return 5 to 8 hashtags
- each hashtag must begin with #
- gaming and event relevant
- do not invent a game-specific hashtag if the game is unknown

Thumbnail prompt rules:
- describe Sunny with his real facial identity preserved
- black hoodie
- expression must match the highlight
- blue and black gaming branding
- dramatic gaming background based on the visual event
- high contrast
- suitable for a vertical gaming Short cover
- include a short suggested cover text

{retry_instruction}

Return ONLY valid JSON.

Every field is mandatory and must contain a value.

Use this exact structure:

{{
    "hook": "Short hook",
    "title": "YouTube Short title",
    "description": "Short description",
    "hashtags": [
        "#Gaming",
        "#HindiGaming"
    ],
    "thumbnail_prompt": "Detailed thumbnail prompt"
}}
""".strip()

    @classmethod
    def _parse_response(
        cls,
        response_text: str,
    ) -> dict[str, object]:
        cleaned = cls._remove_ansi_codes(
            response_text.strip()
        )

        json_start = cleaned.find("{")
        json_end = cleaned.rfind("}")

        if (
            json_start == -1
            or json_end == -1
            or json_end < json_start
        ):
            return {}

        json_text = cleaned[
            json_start:json_end + 1
        ]

        repaired_json = cls._repair_json_newlines(
            json_text
        )

        try:
            data = json.loads(
                repaired_json
            )
        except json.JSONDecodeError:
            return {}

        if not isinstance(
            data,
            dict,
        ):
            return {}

        return data

    @classmethod
    def _remove_ansi_codes(
        cls,
        text: str,
    ) -> str:
        return cls.ANSI_ESCAPE_PATTERN.sub(
            "",
            text,
        )

    @staticmethod
    def _repair_json_newlines(
        json_text: str,
    ) -> str:
        repaired: list[str] = []

        inside_string = False
        escaped = False

        for character in json_text:
            if escaped:
                repaired.append(
                    character
                )
                escaped = False
                continue

            if character == "\\":
                repaired.append(
                    character
                )
                escaped = True
                continue

            if character == '"':
                repaired.append(
                    character
                )
                inside_string = not inside_string
                continue

            if (
                inside_string
                and character in ("\r", "\n")
            ):
                if (
                    repaired
                    and repaired[-1] != " "
                ):
                    repaired.append(" ")

                continue

            repaired.append(
                character
            )

        return "".join(
            repaired
        )