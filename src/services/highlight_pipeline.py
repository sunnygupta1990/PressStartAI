from pathlib import Path

from src.models.pipeline_result import PipelineResult
from src.services.asr.transcription_pipeline import TranscriptionPipeline
from src.services.audio_analyzer import AudioAnalyzer
from src.services.audio_extractor import AudioExtractor
from src.services.final_highlight_combiner import FinalHighlightCombiner
from src.services.final_highlight_exporter import FinalHighlightExporter
from src.services.final_highlight_selector import FinalHighlightSelector
from src.services.highlight_analysis_combiner import HighlightAnalysisCombiner
from src.services.highlight_clip_generator import HighlightClipGenerator
from src.services.highlight_feature_extractor import HighlightFeatureExtractor
from src.services.highlight_frame_extractor import HighlightFrameExtractor
from src.services.highlight_fusion_reasoner import HighlightFusionReasoner
from src.services.highlight_overlap_resolver import HighlightOverlapResolver
from src.services.highlight_reasoner import HighlightReasoner
from src.services.highlight_scorer import HighlightScorer
from src.services.highlight_selector import HighlightSelector
from src.services.motion_analyzer import MotionAnalyzer
from src.services.scene_detector import SceneDetector
from src.services.scene_transcript_mapper import SceneTranscriptMapper
from src.services.speech_chunk_extractor import SpeechChunkExtractor
from src.services.video_loader import VideoLoader
from src.services.visual_highlight_reasoner import VisualHighlightReasoner
from src.services.voice_activity_detector import VoiceActivityDetector


class HighlightPipeline:
    """Run the complete PressStartAI highlight analysis pipeline."""

    def run(
        self,
        video_file: str,
        working_folder: str,
        output_folder: str,
    ) -> PipelineResult:
        video_path = Path(video_file)

        if not video_path.is_file():
            raise FileNotFoundError(
                f"Video file does not exist: {video_path}"
            )

        working_path = Path(working_folder)

        audio_file = working_path / "audio.wav"
        speech_folder = working_path / "speech_chunks"
        highlight_folder = working_path / "highlights"
        frame_folder = working_path / "highlight_frames"

        working_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        video_loader = VideoLoader()
        video_info = video_loader.load(
            str(video_path)
        )

        audio_extractor = AudioExtractor()
        audio_extractor.extract(
            input_video=str(video_path),
            output_audio=str(audio_file),
        )

        vad = VoiceActivityDetector()
        speech_segments = vad.detect(
            str(audio_file)
        )

        speech_chunk_extractor = SpeechChunkExtractor()
        speech_chunks = speech_chunk_extractor.extract(
            input_audio=str(audio_file),
            speech_segments=speech_segments,
            output_folder=str(speech_folder),
        )

        transcription_pipeline = TranscriptionPipeline()
        transcript_segments = transcription_pipeline.transcribe(
            speech_chunks
        )

        scene_detector = SceneDetector()
        scenes = scene_detector.detect(
            str(video_path)
        )

        scene_mapper = SceneTranscriptMapper()
        scene_analyses = scene_mapper.map(
            scenes=scenes,
            transcript_segments=transcript_segments,
        )

        motion_analyzer = MotionAnalyzer()
        motion_features = motion_analyzer.analyze(
            video_file=str(video_path),
            scenes=scenes,
        )

        audio_analyzer = AudioAnalyzer()
        audio_features = audio_analyzer.analyze(
            audio_file=str(audio_file),
            scenes=scenes,
        )

        feature_extractor = HighlightFeatureExtractor()
        highlight_features = feature_extractor.extract(
            scene_analyses=scene_analyses,
            motion_features=motion_features,
            audio_features=audio_features,
        )

        scorer = HighlightScorer()
        highlight_scores = scorer.score(
            highlight_features
        )

        selector = HighlightSelector()
        candidates = selector.select(
            scores=highlight_scores,
            video_duration_seconds=video_info.duration_seconds,
        )

        overlap_resolver = HighlightOverlapResolver()
        candidates = overlap_resolver.resolve(
            candidates
        )

        clip_generator = HighlightClipGenerator()
        generated_highlights = clip_generator.generate(
            video_file=str(video_path),
            candidates=candidates,
            output_folder=str(highlight_folder),
        )

        commentary_reasoner = HighlightReasoner()
        commentary_results = commentary_reasoner.reason(
            generated_highlights
        )

        analysis_combiner = HighlightAnalysisCombiner()
        analyzed_highlights = analysis_combiner.combine(
            highlights=generated_highlights,
            reasoning_results=commentary_results,
        )

        frame_extractor = HighlightFrameExtractor(
            frame_count=5,
        )

        highlight_frames: dict[int, list[str]] = {}

        for highlight in generated_highlights:
            frame_files = frame_extractor.extract(
                highlight=highlight,
                output_folder=str(frame_folder),
            )

            highlight_frames[
                highlight.rank
            ] = frame_files

        visual_reasoner = VisualHighlightReasoner()

        visual_results = {}

        for highlight in generated_highlights:
            frame_files = highlight_frames.get(
                highlight.rank,
                [],
            )

            visual_result = visual_reasoner.reason(
                highlight=highlight,
                frame_files=frame_files,
            )

            visual_results[
                highlight.rank
            ] = visual_result

        fusion_reasoner = HighlightFusionReasoner()

        fusion_results = []

        for analyzed_highlight in analyzed_highlights:
            visual_result = visual_results.get(
                analyzed_highlight.rank
            )

            if visual_result is None:
                continue

            fusion_result = fusion_reasoner.reason(
                analyzed_highlight=analyzed_highlight,
                visual_reasoning=visual_result,
            )

            fusion_results.append(
                fusion_result
            )

        final_selector = FinalHighlightSelector(
            minimum_confidence=0.70,
        )

        approved_results = final_selector.select(
            fusion_results
        )

        final_combiner = FinalHighlightCombiner()

        final_highlights = final_combiner.combine(
            highlights=generated_highlights,
            approved_results=approved_results,
        )

        exporter = FinalHighlightExporter()

        exported_files = exporter.export(
            highlights=final_highlights,
            output_folder=output_folder,
        )

        return PipelineResult(
            source_video_file=str(video_path),
            video_duration_seconds=video_info.duration_seconds,
            final_highlights=final_highlights,
            exported_files=exported_files,
        )