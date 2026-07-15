import json
import re
import subprocess

from src.models.generated_highlight import GeneratedHighlight
from src.models.highlight_reasoning import HighlightReasoning


class HighlightReasoner:
    """Use a local Ollama model to reason about highlight candidates."""

    MODEL_NAME = "gemma3:4b"

    OLLAMA_EXECUTABLE = (
        r"C:\Users\SunGupta\AppData\Local\Programs\Ollama\ollama.exe"
    )

    ANSI_ESCAPE_PATTERN = re.compile(
        r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
    )

    def reason(
        self,
        highlights: list[GeneratedHighlight],
    ) -> list[HighlightReasoning]:
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
        prompt = self._build_prompt(highlight)

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

        response_text = process.stdout.strip()

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