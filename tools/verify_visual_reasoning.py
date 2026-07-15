import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


OLLAMA_API_URL = (
    "http://localhost:11434/api/generate"
)

MODEL_NAME = "gemma3:4b"

FRAME_FOLDER = Path(
    "temp/highlight_frames"
)


def encode_image(
    image_path: Path,
) -> str:
    image_bytes = image_path.read_bytes()

    return base64.b64encode(
        image_bytes
    ).decode("ascii")


def main() -> None:
    frame_files = sorted(
        FRAME_FOLDER.glob(
            "highlight_001_frame_*.jpg"
        )
    )

    if not frame_files:
        raise FileNotFoundError(
            "No highlight frames found."
        )

    images = [
        encode_image(frame_file)
        for frame_file in frame_files
    ]

    prompt = """
You are analyzing representative frames from a gaming highlight.

The frames are in chronological order.

Describe what appears to be happening in the gameplay.

Focus on:
- player action
- enemies or danger
- combat
- movement
- success or failure
- whether the scene looks exciting
- whether it could be a good gaming highlight

Return ONLY valid JSON.

Use this exact structure:

{
    "visual_event": "Short description",
    "action_level": "low",
    "danger_level": "low",
    "looks_interesting": true,
    "reason": "Short explanation",
    "confidence": 0.85
}

Allowed action_level values:
low
medium
high

Allowed danger_level values:
low
medium
high
""".strip()

    request_data = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "images": images,
        "stream": False,
        "format": "json",
    }

    request_body = json.dumps(
        request_data
    ).encode("utf-8")

    request = urllib.request.Request(
        OLLAMA_API_URL,
        data=request_body,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    print("=" * 60)
    print("Visual Reasoning Verification")
    print("=" * 60)

    print(
        f"Frames Sent: {len(frame_files)}"
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
        error_body = (
            error.read().decode(
                "utf-8",
                errors="replace",
            )
        )

        print()
        print("OLLAMA HTTP ERROR")
        print(f"Status: {error.code}")
        print(error_body)

        return

    except urllib.error.URLError as error:
        print()
        print("OLLAMA CONNECTION ERROR")
        print(error)

        return

    response_data = json.loads(
        response_text
    )

    model_response = str(
        response_data.get(
            "response",
            "",
        )
    )

    print()
    print("=" * 60)
    print("VISUAL REASONING RESPONSE")
    print("=" * 60)

    print(model_response)

    print()
    print("=" * 60)
    print("MODEL INFO")
    print("=" * 60)

    print(
        f"Model: "
        f"{response_data.get('model', 'unknown')}"
    )

    print(
        f"Done : "
        f"{response_data.get('done', False)}"
    )


if __name__ == "__main__":
    main()