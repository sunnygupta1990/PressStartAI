# src/services/short_metadata_generator.py

import json
import re
import time
import urllib.error
import urllib.request

from src.models.final_highlight import FinalHighlight
from src.models.short_metadata import ShortMetadata
from src.services.ai_text_cleaner import AITextCleaner


class ShortMetadataGenerator:
    """Generate lightweight metadata for one YouTube Short."""

    MODEL_NAME = "gemma3:4b"

    OLLAMA_API_URL = "http://localhost:11434/api/generate"
    REQUEST_TIMEOUT_SECONDS = 900
    RETRY_DELAY_SECONDS = 5
    KEEP_ALIVE = "30m"

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
        """Generate hook, title, and hashtags only."""

        for attempt in range(
            1,
            self.MAXIMUM_ATTEMPTS + 1,
        ):
            prompt = self._build_prompt(
                highlight=highlight,
                attempt=attempt,
            )

            response_text = self._generate(
                prompt
            )

            data = self._parse_response(
                response_text
            )

            metadata = self._build_metadata(
                highlight=highlight,
                data=data,
            )

            if self._is_valid(metadata):
                return metadata

        return self._build_fallback_metadata(
            highlight
        )

    def _generate(
        self,
        prompt: str,
    ) -> str:
        """Generate metadata through Ollama's persistent local API."""

        request_data = {
            "model": self.MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.KEEP_ALIVE,
        }

        request_body = json.dumps(
            request_data
        ).encode("utf-8")

        last_error: Exception | None = None

        for attempt in range(
            1,
            self.MAXIMUM_ATTEMPTS + 1,
        ):
            request = urllib.request.Request(
                self.OLLAMA_API_URL,
                data=request_body,
                headers={
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self.REQUEST_TIMEOUT_SECONDS,
                ) as response:
                    response_data = json.loads(
                        response.read().decode("utf-8")
                    )

                return str(
                    response_data.get(
                        "response",
                        "",
                    )
                )

            except urllib.error.HTTPError as error:
                error_body = error.read().decode(
                    "utf-8",
                    errors="replace",
                )

                raise RuntimeError(
                    f"Ollama HTTP error "
                    f"{error.code}: {error_body}"
                ) from error

            except (
                TimeoutError,
                urllib.error.URLError,
            ) as error:
                last_error = error

                if attempt < self.MAXIMUM_ATTEMPTS:
                    time.sleep(
                        self.RETRY_DELAY_SECONDS
                    )

        raise RuntimeError(
            "Ollama metadata generation failed after "
            f"{self.MAXIMUM_ATTEMPTS} attempts: "
            f"{last_error}"
        ) from last_error

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
            description="",
            hashtags=[
                self.text_cleaner.clean(
                    str(hashtag)
                )
                for hashtag in hashtags
                if str(hashtag).strip()
            ],
            thumbnail_prompt="",
        )

    @classmethod
    def _is_valid(
        cls,
        metadata: ShortMetadata,
    ) -> bool:
        if not metadata.hook.strip():
            return False

        if not metadata.title.strip():
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
                *metadata.hashtags,
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
            description="",
            hashtags=[
                "#Gaming",
                "#HindiGaming",
                "#GamingShorts",
                "#Reaction",
                "#Gameplay",
            ],
            thumbnail_prompt="",
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
You are creating lightweight YouTube Shorts metadata for the gaming
channel "Press Start with Sunny".

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

Create only:
- one short hook
- one YouTube Short title
- five to eight hashtags

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

Hashtag rules:
- return 5 to 8 hashtags
- each hashtag must begin with #
- gaming and event relevant
- do not invent a game-specific hashtag if the game is unknown

{retry_instruction}

Return ONLY valid JSON using this exact structure:

{{
    "hook": "Short hook",
    "title": "YouTube Short title",
    "hashtags": [
        "#Gaming",
        "#HindiGaming"
    ]
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

        return "".join(repaired)
