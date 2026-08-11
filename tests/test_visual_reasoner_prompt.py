from types import SimpleNamespace

from src.services.visual_highlight_reasoner import VisualHighlightReasoner


def test_build_prompt_accepts_highlight_instance():
    reasoner = VisualHighlightReasoner()
    highlight = SimpleNamespace(
        transcript_text="test transcript",
        rank=1,
        duration_seconds=15.0,
        final_score=0.75,
    )
    prompt = reasoner._build_prompt(highlight)
    assert "test transcript" in prompt
    assert "Highlight rank:" in prompt
