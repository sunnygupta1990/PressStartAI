from src.models.asr_segment import ASRSegment
from src.models.scene import Scene
from src.models.scene_analysis import SceneAnalysis


class SceneTranscriptMapper:
    """Assign each transcript segment to the scene with maximum overlap."""

    def map(
        self,
        scenes: list[Scene],
        transcript_segments: list[ASRSegment],
    ) -> list[SceneAnalysis]:
        scene_segments: list[list[ASRSegment]] = [
            [] for _ in scenes
        ]

        for segment in transcript_segments:
            best_scene_index = self._find_best_scene(
                scenes=scenes,
                segment=segment,
            )

            if best_scene_index is not None:
                scene_segments[best_scene_index].append(segment)

        return [
            SceneAnalysis(
                scene=scene,
                transcript_segments=scene_segments[index],
            )
            for index, scene in enumerate(scenes)
        ]

    @staticmethod
    def _find_best_scene(
        scenes: list[Scene],
        segment: ASRSegment,
    ) -> int | None:
        best_scene_index: int | None = None
        best_overlap = 0.0

        for index, scene in enumerate(scenes):
            overlap_start = max(
                scene.start_seconds,
                segment.start_seconds,
            )

            overlap_end = min(
                scene.end_seconds,
                segment.end_seconds,
            )

            overlap = max(
                0.0,
                overlap_end - overlap_start,
            )

            if overlap > best_overlap:
                best_overlap = overlap
                best_scene_index = index

        return best_scene_index