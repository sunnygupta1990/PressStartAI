
"""Run the new PressStartAI Gameplay Segmentation feature.

This tool is intentionally separate from src/cli.py and the existing highlight pipeline.
"""
from src.gameplay_segmentation.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
