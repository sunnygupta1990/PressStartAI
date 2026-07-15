import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

from src.models.generated_highlight import GeneratedHighlight
from src.models.visual_reasoning import VisualReasoning


class VisualHighlightReasoner:
    """Use local Gemma vision to analyze gaming highlight frames."""

    MODEL_NAME = "gemma3:4b"

    OLLAMA_API_URL = (
        "http://localhost:11434/api/generate"
    )

    def reason(
        self,
        highlight: GeneratedHighlight,
        frame_files: list[str],
    ) -> VisualReasoning:
        images = [
            self._encode_image(
                Path(frame_file)
            )
            for frame_file in frame_files
        ]

        prompt = self._build_prompt(
            highlight
        )

        request_data = {
            "model": self.MODEL_NAME,
            "prompt": prompt,
            "images": images,
            "stream": False,
            "format": "json",
        }

        request_body = json.dumps(
            request_data
        ).encode("utf-8")

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
                timeout=300,
            ) as response:
                response_text = (
                    response.read().decode("utf-8")
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

        except urllib.error.URLError as error:
            raise RuntimeError(
                f"Unable to connect to Ollama: {error}"
            ) from error

        response_data = json.loads(
            response_text
        )

        model_response = str(
            response_data.get(
                "response",
                "",
            )
        )

        data = self._parse_response(
            model_response
        )

        return VisualReasoning(
            rank=highlight.rank,
            visual_event=str(
                data.get(
                    "visual_event",
                    "",
                )
            ),
            action_level=self._normalize_level(
                data.get(
                    "action_level",
                    "low",
                )
            ),
            danger_level=self._normalize_level(
                data.get(
                    "danger_level",
                    "low",
                )
            ),
            looks_interesting=self._normalize_boolean(
                data.get(
                    "looks_interesting",
                    False,
                )
            ),
            reason=str(
                data.get(
                    "reason",
                    "",
                )
            ),
            confidence=self._normalize_confidence(
                data.get(
                    "confidence",
                    0.0,
                )
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
You are analyzing representative frames from a gaming highlight.

The frames are in chronological order.

Channel:
Press Start with Sunny

Content style:
- Hindi and Hinglish gaming
- natural reactions
- funny failures
- rage moments
- intense combat
- boss fights
- unexpected gameplay

Highlight rank:
{highlight.rank}

Highlight duration:
{highlight.duration_seconds:.2f} seconds

Heuristic score:
{highlight.final_score:.4f}

Approximate transcript:
{transcript}

The transcript may contain speech recognition errors.

Analyze the visual gameplay shown in the frames.

Focus on:
- player action
- enemies
- danger
- combat
- movement
- success or failure
- whether the visual event is interesting

Return ONLY valid JSON.

Use this exact structure:

{{
    "visual_event": "Short description",
    "action_level": "medium",
    "danger_level": "high",
    "looks_interesting": true,
    "reason": "Short explanation",
    "confidence": 0.90
}}

Allowed action_level values:
low
medium
high

Allowed danger_level values:
low
medium
high
""".strip()

    @staticmethod
    def _encode_image(
        image_path: Path,
    ) -> str:
        if not image_path.is_file():
            raise FileNotFoundError(
                f"Frame image does not exist: "
                f"{image_path}"
            )

        image_bytes = image_path.read_bytes()

        return base64.b64encode(
            image_bytes
        ).decode("ascii")

    @staticmethod
    def _parse_response(
        response_text: str,
    ) -> dict[str, object]:
        cleaned = response_text.strip()

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

        try:
            data = json.loads(
                json_text
            )
        except json.JSONDecodeError:
            return {}

        if not isinstance(data, dict):
            return {}

        return data

    @staticmethod
    def _normalize_level(
        value: object,
    ) -> str:
        level = str(
            value
        ).strip().lower()

        if level not in {
            "low",
            "medium",
            "high",
        }:
            return "low"

        return level

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