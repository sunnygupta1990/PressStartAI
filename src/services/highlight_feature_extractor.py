from src.models.audio_features import AudioFeatures
from src.models.highlight_features import HighlightFeatures
from src.models.motion_features import MotionFeatures
from src.models.scene_analysis import SceneAnalysis


class HighlightFeatureExtractor:
    """Combine transcript, motion, and audio features for scenes."""

    def extract(
        self,
        scene_analyses: list[SceneAnalysis],
        motion_features: list[MotionFeatures],
        audio_features: list[AudioFeatures],
    ) -> list[HighlightFeatures]:
        scene_count = len(scene_analyses)

        if len(motion_features) != scene_count:
            raise ValueError(
                "Scene analysis count does not match motion feature count."
            )

        if len(audio_features) != scene_count:
            raise ValueError(
                "Scene analysis count does not match audio feature count."
            )

        features: list[HighlightFeatures] = []

        for analysis, motion, audio in zip(
            scene_analyses,
            motion_features,
            audio_features,
            strict=True,
        ):
            transcript_text = analysis.transcript_text.strip()

            features.append(
                HighlightFeatures(
                    scene_start_seconds=analysis.scene.start_seconds,
                    scene_end_seconds=analysis.scene.end_seconds,
                    scene_duration_seconds=analysis.scene.duration_seconds,
                    transcript_text=transcript_text,
                    has_speech=bool(transcript_text),
                    speech_character_count=len(transcript_text),
                    speech_word_count=len(transcript_text.split()),
                    average_motion_score=motion.average_motion_score,
                    maximum_motion_score=motion.maximum_motion_score,
                    average_audio_rms=audio.average_rms,
                    maximum_audio_rms=audio.maximum_rms,
                )
            )

        return features