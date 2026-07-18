from collections.abc import Callable
from pathlib import Path

from src.models.pipeline_progress import PipelineProgress
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
from src.services.pipeline_progress_reporter import PipelineProgressReporter
from src.services.pipeline_stage_runner import PipelineStageRunner
from src.services.scene_detector import SceneDetector
from src.services.scene_transcript_mapper import SceneTranscriptMapper
from src.services.short_package_batch_builder import ShortPackageBatchBuilder
from src.services.speech_chunk_extractor import SpeechChunkExtractor
from src.services.video_loader import VideoLoader
from src.services.visual_highlight_reasoner import VisualHighlightReasoner
from src.services.voice_activity_detector import VoiceActivityDetector
from src.services.recording_session_loader import RecordingSessionLoader


class HighlightPipeline:
    """Run the complete PressStartAI highlight and Short pipeline."""

    def run(
        self,
        video_file: str,
        working_folder: str,
        output_folder: str,
        layout_type: str,
        progress_callback: Callable[
            [PipelineProgress],
            None,
        ] | None = None,
    ) -> PipelineResult:
        video_path = Path(video_file)

        if not video_path.is_file():
            raise FileNotFoundError(
                f"Video file does not exist: {video_path}"
            )

        progress = PipelineProgressReporter(
            callback=progress_callback,
            total_steps=20,
        )

        stage_runner = PipelineStageRunner()

        working_path = Path(working_folder)
        output_path = Path(output_folder)

        audio_file = working_path / "audio.wav"
        speech_folder = working_path / "speech_chunks"
        highlight_folder = working_path / "highlights"
        frame_folder = working_path / "highlight_frames"
        short_package_folder = output_path / "shorts"

        working_path.mkdir(
            parents=True,
            exist_ok=True,
        )

        progress.report(
            1,
            "Loading video",
        )

        video_loader = VideoLoader()

        video_info = stage_runner.run(
            stage="Loading video",
            action=lambda: video_loader.load(
                str(video_path)
            ),
        )

        progress.report(
            2,
            "Extracting audio",
        )

        audio_extractor = AudioExtractor()

        stage_runner.run(
            stage="Extracting audio",
            action=lambda: audio_extractor.extract(
                input_video=str(video_path),
                output_audio=str(audio_file),
            ),
        )

        progress.report(
            3,
            "Detecting speech",
        )

        vad = VoiceActivityDetector()

        speech_segments = stage_runner.run(
            stage="Detecting speech",
            action=lambda: vad.detect(
                str(audio_file)
            ),
        )

        progress.report(
            4,
            "Creating speech chunks",
        )

        speech_chunk_extractor = SpeechChunkExtractor()

        speech_chunks = stage_runner.run(
            stage="Creating speech chunks",
            action=lambda: speech_chunk_extractor.extract(
                input_audio=str(audio_file),
                speech_segments=speech_segments,
                output_folder=str(speech_folder),
            ),
        )

        progress.report(
            5,
            "Transcribing commentary",
        )

        transcription_pipeline = TranscriptionPipeline()

        transcript_segments = stage_runner.run(
            stage="Transcribing commentary",
            action=lambda: transcription_pipeline.transcribe(
                speech_chunks
            ),
        )

        progress.report(
            6,
            "Detecting scenes",
        )

        scene_detector = SceneDetector()

        scenes = stage_runner.run(
            stage="Detecting scenes",
            action=lambda: scene_detector.detect(
                str(video_path)
            ),
        )

        progress.report(
            7,
            "Mapping commentary to scenes",
        )

        scene_mapper = SceneTranscriptMapper()

        scene_analyses = stage_runner.run(
            stage="Mapping commentary to scenes",
            action=lambda: scene_mapper.map(
                scenes=scenes,
                transcript_segments=transcript_segments,
            ),
        )

        progress.report(
            8,
            "Analyzing motion",
        )

        motion_analyzer = MotionAnalyzer()

        motion_features = stage_runner.run(
            stage="Analyzing motion",
            action=lambda: motion_analyzer.analyze(
                video_file=str(video_path),
                scenes=scenes,
            ),
        )

        progress.report(
            9,
            "Analyzing audio intensity",
        )

        audio_analyzer = AudioAnalyzer()

        audio_features = stage_runner.run(
            stage="Analyzing audio intensity",
            action=lambda: audio_analyzer.analyze(
                audio_file=str(audio_file),
                scenes=scenes,
            ),
        )

        progress.report(
            10,
            "Scoring highlight scenes",
        )

        feature_extractor = HighlightFeatureExtractor()

        highlight_features = stage_runner.run(
            stage="Extracting highlight features",
            action=lambda: feature_extractor.extract(
                scene_analyses=scene_analyses,
                motion_features=motion_features,
                audio_features=audio_features,
            ),
        )

        scorer = HighlightScorer()

        highlight_scores = stage_runner.run(
            stage="Scoring highlight scenes",
            action=lambda: scorer.score(
                highlight_features
            ),
        )

        progress.report(
            11,
            "Selecting highlight candidates",
        )

        selector = HighlightSelector()

        candidates = stage_runner.run(
            stage="Selecting highlight candidates",
            action=lambda: selector.select(
                scores=highlight_scores,
                video_duration_seconds=video_info.duration_seconds,
            ),
        )

        overlap_resolver = HighlightOverlapResolver()

        candidates = stage_runner.run(
            stage="Resolving highlight overlaps",
            action=lambda: overlap_resolver.resolve(
                candidates
            ),
        )

        progress.report(
            12,
            "Generating highlight clips",
        )

        clip_generator = HighlightClipGenerator()

        generated_highlights = stage_runner.run(
            stage="Generating highlight clips",
            action=lambda: clip_generator.generate(
                video_file=str(video_path),
                candidates=candidates,
                output_folder=str(highlight_folder),
            ),
        )

        progress.report(
            13,
            "Running commentary AI reasoning",
        )

        commentary_reasoner = HighlightReasoner()

        commentary_results = stage_runner.run(
            stage="Running commentary AI reasoning",
            action=lambda: commentary_reasoner.reason(
                generated_highlights
            ),
        )

        analysis_combiner = HighlightAnalysisCombiner()

        analyzed_highlights = stage_runner.run(
            stage="Combining commentary analysis",
            action=lambda: analysis_combiner.combine(
                highlights=generated_highlights,
                reasoning_results=commentary_results,
            ),
        )

        progress.report(
            14,
            "Extracting representative frames",
        )

        frame_extractor = HighlightFrameExtractor(
            frame_count=3,
            maximum_frame_width=768,
        )

        highlight_frames: dict[int, list[str]] = {}

        for highlight in generated_highlights:
            current_highlight = highlight

            frame_files = stage_runner.run(
                stage=(
                    "Extracting representative frames "
                    f"for rank {current_highlight.rank}"
                ),
                action=lambda: frame_extractor.extract(
                    highlight=current_highlight,
                    output_folder=str(frame_folder),
                ),
            )

            highlight_frames[
                current_highlight.rank
            ] = frame_files

        progress.report(
            15,
            "Running visual AI reasoning",
        )

        visual_reasoner = VisualHighlightReasoner()

        stage_runner.run(
            stage="Warming up visual AI model",
            action=visual_reasoner.warm_up,
        )

        visual_results = {}

        for highlight in generated_highlights:
            current_highlight = highlight

            current_frame_files = highlight_frames.get(
                current_highlight.rank,
                [],
            )

            visual_result = stage_runner.run(
                stage=(
                    "Running visual AI reasoning "
                    f"for rank {current_highlight.rank}"
                ),
                action=lambda: visual_reasoner.reason(
                    highlight=current_highlight,
                    frame_files=current_frame_files,
                ),
            )

            visual_results[
                current_highlight.rank
            ] = visual_result

        progress.report(
            16,
            "Fusing multimodal AI decisions",
        )

        fusion_reasoner = HighlightFusionReasoner()

        fusion_results = []

        for analyzed_highlight in analyzed_highlights:
            current_analyzed_highlight = analyzed_highlight

            current_visual_result = visual_results.get(
                current_analyzed_highlight.rank
            )

            if current_visual_result is None:
                continue

            fusion_result = stage_runner.run(
                stage=(
                    "Fusing multimodal AI decisions "
                    f"for rank "
                    f"{current_analyzed_highlight.rank}"
                ),
                action=lambda: fusion_reasoner.reason(
                    analyzed_highlight=(
                        current_analyzed_highlight
                    ),
                    visual_reasoning=(
                        current_visual_result
                    ),
                ),
            )

            fusion_results.append(
                fusion_result
            )

        progress.report(
            17,
            "Selecting final approved highlights",
        )

        final_selector = FinalHighlightSelector(
            minimum_confidence=0.70,
        )

        approved_results = stage_runner.run(
            stage="Selecting final approved highlights",
            action=lambda: final_selector.select(
                fusion_results
            ),
        )

        progress.report(
            18,
            "Linking approved decisions to clips",
        )

        final_combiner = FinalHighlightCombiner()

        final_highlights = stage_runner.run(
            stage="Linking approved decisions to clips",
            action=lambda: final_combiner.combine(
                highlights=generated_highlights,
                approved_results=approved_results,
            ),
        )

        progress.report(
            19,
            "Exporting final highlight package",
        )

        exporter = FinalHighlightExporter()

        exported_files = stage_runner.run(
            stage="Exporting final highlight package",
            action=lambda: exporter.export(
                highlights=final_highlights,
                output_folder=str(
                    output_path / "highlights"
                ),
            ),
        )

        progress.report(
            20,
            "Building final YouTube Short packages",
        )

        short_package_builder = ShortPackageBatchBuilder()

        short_packages = stage_runner.run(
    stage="Building final YouTube Short packages",
    action=lambda: short_package_builder.build(
        highlights=final_highlights,
        output_folder=str(short_package_folder),
        layout_type=layout_type,
    ),
)

        return PipelineResult(
            source_video_file=str(video_path),
            video_duration_seconds=video_info.duration_seconds,
            final_highlights=final_highlights,
            exported_files=exported_files,
            short_packages=short_packages,
            stage_timings=list(stage_runner.timings),
        )