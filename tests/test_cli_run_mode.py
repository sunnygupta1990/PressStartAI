
from pathlib import Path

def test_cli_contains_resume_fresh_and_clear_cache():
    text = (Path(__file__).parents[1] / "src" / "cli.py").read_text(encoding="utf-8")
    assert "Resume Previous Run" in text
    assert "Fresh Run" in text
    assert "Clear Cache / Checkpoints" in text
    assert "Reusable cache was found for these recordings." in text
