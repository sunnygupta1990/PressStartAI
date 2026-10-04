from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps


class OllamaGameplayReasoner:
    PROMPT_VERSION = "3.0"
    """Gemma/Ollama vision reasoner optimized for repeated gameplay windows."""

    def __init__(
        self,
        model: str = "gemma3:4b",
        endpoint: str = "http://localhost:11434/api/generate",
        timeout_seconds: int = 300,
        keep_alive: str = "2h",
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.keep_alive = keep_alive

    def analyze_window(
        self,
        frame_files: list[str],
        window_start: float,
        window_end: float,
    ) -> list[dict]:
        if not frame_files:
            return []

        # Send ONE compact contact sheet instead of 4-5 separate 768px images.
        # This substantially reduces vision-token processing while preserving
        # temporal context across the window.
        selected = self._select_frames(frame_files, 2)
        contact_sheet = self._make_contact_sheet(selected)
        try:
            image_b64 = base64.b64encode(contact_sheet).decode("ascii")
        finally:
            # contact_sheet is bytes only; no temporary file is created.
            pass

        prompt = f"""
You are the semantic timeline analyzer for a gaming-video clip extraction system.

The supplied image is a chronological contact sheet covering approximately
{window_start:.3f} to {window_end:.3f} seconds. Read the panels in order:
left-to-right, then top-to-bottom.

Find meaningful reusable gameplay events. Do NOT only find exciting highlights.
Ordinary gameplay can be useful. Repetitive low-information gameplay should be
marked repetitive so the caller can sample it.

Identify distinct events visible across the contact sheet. A continuous action
may be one event. A meaningful camera/cinematic transition is a new event.
Dialogue is meaningful even when the visual scene barely changes.

Return ONLY valid JSON in exactly this shape:
{{
  "events": [
    {{
      "start_offset": 0.0,
      "end_offset": 5.0,
      "category": "Fight",
      "description": "player shoots an enemy",
      "characters": ["Character_01"],
      "location": "Unknown",
      "shot_type": "Gameplay",
      "dialogue_present": false,
      "meaningful": true,
      "repetitive": false,
      "confidence": 0.85
    }}
  ]
}}

Rules:
- Offsets are relative to the supplied window.
- start_offset < end_offset.
- Prefer 3-9 second useful event spans when possible.
- Do not invent names, locations, dialogue, or events.
- Use "Unknown" when unsure.
- Categories: Fight, Running, Exploration, Cinematic, Dialogue, Character,
  Items, Vehicles, Boss, Environment, Puzzle, Cutscene, Other.
- A camera zoom/close-up/cinematic transition should normally be its own event.
- Repetitive means the same action continues without meaningful change.
- meaningful means useful as an editing building block, not necessarily exciting.
- Return no more than 8 events.
- Keep descriptions under 12 words.
- Keep JSON compact; never add commentary outside the JSON object.
""".strip()

        request = {
            "model": self.model,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "format": "json",
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": 0,
                "num_predict": 384,
            },
        }
        response = self._request(request)
        raw = response.get("response", "")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            try:
                data = self._extract_json(raw)
            except Exception:
                # Retry with a larger generation budget while retaining the
                # original image context. This handles truncated JSON.
                retry_request = dict(request)
                retry_request["prompt"] = prompt + """
IMPORTANT: Keep the JSON compact. Use short descriptions and at most 8 events.
Return complete valid JSON before stopping.
""".strip()
                retry_request["options"] = {
                    "temperature": 0,
                    "num_predict": 512,
                }
                retry = self._request(retry_request).get("response", "")
                try:
                    data = json.loads(retry)
                except json.JSONDecodeError:
                    data = self._extract_json(retry)
        events = data.get("events", []) if isinstance(data, dict) else []
        return [e for e in events if isinstance(e, dict)]

    @staticmethod
    def _select_frames(frame_files: list[str], count: int) -> list[str]:
        if len(frame_files) <= count:
            return frame_files
        if count <= 1:
            return [frame_files[len(frame_files) // 2]]
        indices = [
            round(i * (len(frame_files) - 1) / (count - 1))
            for i in range(count)
        ]
        return [frame_files[i] for i in indices]

    @staticmethod
    def _make_contact_sheet(frame_files: list[str]) -> bytes:
        tile_w, tile_h = 448, 252
        canvas = Image.new("RGB", (tile_w * 2, tile_h), "black")

        for index, file_name in enumerate(frame_files[:2]):
            with Image.open(file_name) as image:
                image = ImageOps.fit(image.convert("RGB"), (tile_w, tile_h))
                x = index * tile_w
                y = 0
                canvas.paste(image, (x, y))

        import io
        buffer = io.BytesIO()
        canvas.save(buffer, format="JPEG", quality=72, optimize=True)
        return buffer.getvalue()

    def _request(self, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        last_error = None
        for attempt in range(1, 4):
            req = urllib.request.Request(
                self.endpoint,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8"))
            except (
                urllib.error.URLError,
                TimeoutError,
                ConnectionError,
                json.JSONDecodeError,
            ) as exc:
                last_error = exc
                if attempt < 3:
                    time.sleep(2 ** (attempt - 1))
        raise RuntimeError(f"Ollama gameplay reasoning failed: {last_error}") from last_error

    @staticmethod
    def _extract_json(text: str) -> dict:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise ValueError("Ollama did not return valid JSON.")
