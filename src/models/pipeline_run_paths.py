from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PipelineRunPaths:
    """Working and output folders for one PressStartAI pipeline run."""

    run_id: str
    working_folder: str
    output_folder: str