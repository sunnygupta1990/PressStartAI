# src/services/highlight_reasoner.py

import json
import re
import time
import urllib.error
import urllib.request

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_reasoning import HighlightReasoning


class HighlightReasoner:
    """Use a local Ollama model to reason about highlight candidates."""

    MODEL_NAME = "gemma3:4b"
    OLLAMA_API_URL = "http://localhost:11434/api/generate"
    REQUEST_TIMEOUT_SECONDS = 900
    MAXIMUM_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 5
    KEEP_ALIVE = "30m"

    ANSI_ESCAPE_PATTERN = re.compile(
        r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
    )

    def reason(
        self,
        highlights: list[GeneratedHighlight],
    ) -> list[HighlightReasoning]:
        """Analyze every generated highlight."""

        results: list[HighlightReasoning] = []

        for highlight in highlights:
            results.append(
                self._reason_about_highlight(highlight)
            )

        return results

    def _reason_about_highlight(
        self,
        highlight: GeneratedHighlight,
    ) -> HighlightReasoning:
        """Analyze one highlight without starting a new Ollama process."""

        prompt = self._build_prompt(highlight)
        response_text = self._generate(prompt).strip()
        data = self._parse_response(response_text)

        return HighlightReasoning(
            rank=highlight.rank,
            is_interesting=self._normalize_boolean(
                data.get("is_interesting", False)
            ),
            category=str(
                data.get("category", "unknown")
            ),
            reason=str(
                data.get("reason", "")
            ),
            confidence=self._normalize_confidence(
                data.get("confidence", 0.0)
            ),
        )

    def _generate(
        self,
        prompt: str,
    ) -> str:
        """Generate reasoning through Ollama's persistent local API."""

        request_data = {
            "model": self.MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "format": "json",
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
            "Ollama commentary reasoning failed after "
            f"{self.MAXIMUM_ATTEMPTS} attempts: "
            f"{last_error}"
        ) from last_error

    @staticmethod
    def _build_prompt(
        highlight: GeneratedHighlight,
    ) -> str:
        transcript = (
            highlight.transcript_text.strip()
            or "[NO SPEECH]"
        )

        return f"""
You are evaluating a gaming video highlight for a Hindi and Hinglish
YouTube gaming channel called Press Start with Sunny.

The creator makes:
- story-mode gaming videos
- funny and natural gameplay commentary
- boss fight moments
- frustration and rage moments
- unexpected gameplay moments
- exciting action moments

Evaluate this candidate highlight.

Rank: {highlight.rank}
Duration: {highlight.duration_seconds:.2f} seconds
Heuristic score: {highlight.final_score:.4f}
Transcript: {transcript}

The Hindi or Hinglish transcript may contain speech recognition errors.
Do not require perfect grammar.

Decide whether this moment sounds interesting enough to keep as a
gaming highlight.

Choose exactly one category:
funny
rage
reaction
action
story
fail
success
unknown

Return ONLY valid JSON.

Keep the reason short and on one line.

Use this exact structure:

{{
    "is_interesting": true,
    "category": "reaction",
    "reason": "Short explanation",
    "confidence": 0.85
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
            return cls._parse_failure(
                "Unable to locate JSON in AI response."
            )

        json_text = cleaned[
            json_start:json_end + 1
        ]

        repaired_json = cls._repair_json_newlines(
            json_text
        )

        try:
            data = json.loads(repaired_json)
        except json.JSONDecodeError:
            return cls._parse_failure(
                "Unable to parse AI reasoning response."
            )

        if not isinstance(data, dict):
            return cls._parse_failure(
                "AI response was not a JSON object."
            )

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
                repaired.append(character)
                escaped = False
                continue

            if character == "\\":
                repaired.append(character)
                escaped = True
                continue

            if character == '"':
                repaired.append(character)
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

            repaired.append(character)

        return "".join(repaired)

    @staticmethod
    def _parse_failure(
        reason: str,
    ) -> dict[str, object]:
        return {
            "is_interesting": False,
            "category": "unknown",
            "reason": reason,
            "confidence": 0.0,
        }

    @staticmethod
    def _normalize_boolean(
        value: object,
    ) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() == "true"

        return bool(value)

    @staticmethod
    def _normalize_confidence(
        value: object,
    ) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.0

        return max(
            0.0,
            min(1.0, confidence),
        )
