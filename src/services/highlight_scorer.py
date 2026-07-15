from src.models.highlight_features import HighlightFeatures
from src.models.highlight_score import HighlightScore


class HighlightScorer:
    """Score scenes using speech, motion, and audio intensity."""

    def score(
        self,
        features: list[HighlightFeatures],
    ) -> list[HighlightScore]:
        if not features:
            return []

        maximum_average_motion = max(
            feature.average_motion_score
            for feature in features
        )

        maximum_word_count = max(
            feature.speech_word_count
            for feature in features
        )

        maximum_audio_rms = max(
            feature.average_audio_rms
            for feature in features
        )

        scored: list[HighlightScore] = []

        for feature in features:
            motion_score = self._normalize(
                feature.average_motion_score,
                maximum_average_motion,
            )

            speech_score = self._normalize(
                float(feature.speech_word_count),
                float(maximum_word_count),
            )

            audio_score = self._normalize(
                feature.average_audio_rms,
                maximum_audio_rms,
            )

            final_score = (
                motion_score * 0.45
                + speech_score * 0.30
                + audio_score * 0.25
            )

            scored.append(
                HighlightScore(
                    features=feature,
                    speech_score=speech_score,
                    motion_score=motion_score,
                    audio_score=audio_score,
                    final_score=final_score,
                )
            )

        return sorted(
            scored,
            key=lambda item: item.final_score,
            reverse=True,
        )

    @staticmethod
    def _normalize(
        value: float,
        maximum: float,
    ) -> float:
        if maximum <= 0:
            return 0.0

        return value / maximum