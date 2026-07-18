import json
import time
import urllib.error
import urllib.request

from src.models.analyzed_highlight import AnalyzedHighlight
from src.models.highlight_fusion import HighlightFusion
from src.models.visual_reasoning import VisualReasoning


class HighlightFusionReasoner:
    """Fuse commentary and visual reasoning into one final decision."""

    MODEL_NAME = "gemma3:4b"

    OLLAMA_API_URL = (
        "http://localhost:11434/api/generate"
    )

    REQUEST_TIMEOUT_SECONDS = 900
    MAXIMUM_ATTEMPTS = 3
    RETRY_DELAY_SECONDS = 5
    KEEP_ALIVE = "30m"

    def reason(
        self,
        analyzed_highlight: AnalyzedHighlight,
        visual_reasoning: VisualReasoning,
    ) -> HighlightFusion:
        prompt = self._build_prompt(
            analyzed_highlight=analyzed_highlight,
            visual_reasoning=visual_reasoning,
        )

        request_data = {
            "model": self.MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "keep_alive": self.KEEP_ALIVE,
        }

        response_text = self._send_request(
            request_data
        )

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

        return HighlightFusion(
            rank=analyzed_highlight.rank,
            keep_highlight=self._normalize_boolean(
                data.get(
                    "keep_highlight",
                    False,
                )
            ),
            category=str(
                data.get(
                    "category",
                    "unknown",
                )
            ),
            event_summary=str(
                data.get(
                    "event_summary",
                    "",
                )
            ),
            commentary_category=(
                analyzed_highlight.category
            ),
            visual_event=(
                visual_reasoning.visual_event
            ),
            action_level=(
                visual_reasoning.action_level
            ),
            danger_level=(
                visual_reasoning.danger_level
            ),
            final_confidence=self._normalize_confidence(
                data.get(
                    "final_confidence",
                    0.0,
                )
            ),
            reason=str(
                data.get(
                    "reason",
                    "",
                )
            ),
        )

    def _send_request(
        self,
        request_data: dict[str, object],
    ) -> str:
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
                    return response.read().decode(
                        "utf-8"
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
            "Ollama fusion reasoning failed after "
            f"{self.MAXIMUM_ATTEMPTS} attempts: "
            f"{last_error}"
        ) from last_error

    @staticmethod
    def _build_prompt(
        analyzed_highlight: AnalyzedHighlight,
        visual_reasoning: VisualReasoning,
    ) -> str:
        return f"""
You are the final highlight decision engine for a Hindi and Hinglish
gaming YouTube channel called Press Start with Sunny.

Combine commentary analysis and visual gameplay analysis.

COMMENTARY ANALYSIS

Interesting:
{analyzed_highlight.is_interesting}

Category:
{analyzed_highlight.category}

Confidence:
{analyzed_highlight.confidence:.4f}

Reason:
{analyzed_highlight.reason}

Approximate transcript:
{analyzed_highlight.transcript_text or "[NO SPEECH]"}

VISUAL ANALYSIS

Visual event:
{visual_reasoning.visual_event}

Action level:
{visual_reasoning.action_level}

Danger level:
{visual_reasoning.danger_level}

Looks interesting:
{visual_reasoning.looks_interesting}

Visual confidence:
{visual_reasoning.confidence:.4f}

Visual reason:
{visual_reasoning.reason}

HEURISTIC SCORE

{analyzed_highlight.final_score:.4f}

Decide whether this should be kept as a gaming highlight.

Choose exactly one final category:

funny
rage
reaction
combat
boss_fight
fail
success
story
unexpected
unknown

Return ONLY valid JSON.

Use this exact structure:

{{
    "keep_highlight": true,
    "category": "combat",
    "event_summary": "Intense combat reaction against a dangerous enemy",
    "final_confidence": 0.93,
    "reason": "Short final explanation"
}}
""".strip()

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