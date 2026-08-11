# src/services/highlight_pipeline.py

"""Configurable highlight and Short generation pipeline."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import shutil

from src.core.config import Config
from src.models.pipeline_progress import PipelineProgress
from src.models.pipeline_result import PipelineResult
from src.models.shorts_feature_settings import ShortsFeatureSettings
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
from src.services.checkpoint_cache import CheckpointCache
from src.services.recording_session_loader import RecordingSessionLoader
from src.services.recording_synchronizer import RecordingSynchronizer
from src.services.scene_detector import SceneDetector
from src.services.scene_transcript_mapper import SceneTranscriptMapper
from src.services.short_package_batch_builder import ShortPackageBatchBuilder
from src.services.shorts_feature_fallbacks import ShortsFeatureFallbacks
from src.services.speech_chunk_extractor import SpeechChunkExtractor
from src.services.video_analysis_proxy import VideoAnalysisProxy
from src.services.video_loader import VideoLoader
from src.services.visual_highlight_reasoner import VisualHighlightReasoner
from src.services.voice_activity_detector import VoiceActivityDetector


class HighlightPipeline:
    """Run the complete configurable PressStartAI pipeline."""

    def run(
        self,
        video_file: str,
        working_folder: str,
        output_folder: str,
        layout_type: str,
        gameplay_video: str | None = None,
        facecam_video: str | None = None,
        progress_callback: Callable[[PipelineProgress], None] | None = None,
        checkpoint_cache: CheckpointCache | None = None,
    ) -> PipelineResult:
        config = Config()
        feature_settings = ShortsFeatureSettings.load(config)

        recording_session = RecordingSessionLoader().load(
            video_file=video_file,
            layout_type=layout_type,
            gameplay_video=gameplay_video,
            facecam_video=facecam_video,
        )

        video_path = Path(recording_session.recording_video)
        working_path = Path(working_folder)
        output_path = Path(output_folder)

        audio_file = working_path / "audio.wav"
        analysis_proxy_file = working_path / "analysis_proxy.mp4"
        analysis_highlight_folder = working_path / "analysis_highlights"
        speech_folder = working_path / "speech_chunks"
        highlight_folder = working_path / "highlights"
        frame_folder = working_path / "highlight_frames"
        short_package_folder = output_path / "shorts"

        working_path.mkdir(parents=True, exist_ok=True)

        progress = PipelineProgressReporter(
            callback=progress_callback,
            total_steps=21,
        )
        stage_runner = PipelineStageRunner(checkpoint_cache=checkpoint_cache)

        self._print_feature_summary(feature_settings)

        if recording_session.has_facecam_layout:
            synchronization = stage_runner.run(
                stage="Synchronizing recordings",
                action=lambda: RecordingSynchronizer().synchronize(
                    recording_session=recording_session,
                    working_folder=str(working_path),
                ),
            )
            recording_session.synchronization = synchronization

        progress.report(1, "Loading video")
        video_info = stage_runner.run(
            stage="Loading video",
            action=lambda: VideoLoader().load(str(video_path)),
        )

        progress.report(2, "Creating fast analysis proxy")
        analysis_video_file = stage_runner.run(
            stage="Creating fast analysis proxy",
            action=lambda: VideoAnalysisProxy(
                maximum_width=960,
                frame_rate=15,
            ).create(
                input_video=str(video_path),
                output_video=str(analysis_proxy_file),
            ),
        )

        progress.report(3, "Extracting audio")
        audio_file = Path(
            stage_runner.run(
                stage="Extracting audio",
                action=lambda: AudioExtractor().extract(
                    input_video=str(video_path),
                    output_audio=str(audio_file),
                ),
            )
        )

        transcript_segments = []

        if feature_settings.transcription_enabled:
            progress.report(4, "Detecting speech")
            speech_segments = stage_runner.run(
                stage="Detecting speech",
                action=lambda: VoiceActivityDetector().detect(
                    str(audio_file)
                ),
            )

            progress.report(5, "Creating speech chunks")
            speech_chunks = stage_runner.run(
                stage="Creating speech chunks",
                action=lambda: SpeechChunkExtractor().extract(
                    input_audio=str(audio_file),
                    speech_segments=speech_segments,
                    output_folder=str(speech_folder),
                ),
            )

            progress.report(6, "Transcribing commentary")
            transcript_segments = stage_runner.run(
                stage="Transcribing commentary",
                action=lambda: TranscriptionPipeline().transcribe(
                    speech_chunks
                ),
            )
        else:
            progress.report(4, "Skipping speech detection")
            progress.report(5, "Skipping speech chunk creation")
            progress.report(6, "Skipping commentary transcription")

        progress.report(7, "Detecting scenes")
        scenes = stage_runner.run(
            stage="Detecting scenes",
            action=lambda: SceneDetector().detect(
                analysis_video_file
            ),
        )

        progress.report(8, "Mapping commentary to scenes")
        scene_analyses = stage_runner.run(
            stage="Mapping commentary to scenes",
            action=lambda: SceneTranscriptMapper().map(
                scenes=scenes,
                transcript_segments=transcript_segments,
            ),
        )

        progress.report(9, "Analyzing motion")
        motion_features = stage_runner.run(
            stage="Analyzing motion",
            action=lambda: MotionAnalyzer().analyze(
                video_file=analysis_video_file,
                scenes=scenes,
            ),
        )

        progress.report(10, "Analyzing audio intensity")
        audio_features = stage_runner.run(
            stage="Analyzing audio intensity",
            action=lambda: AudioAnalyzer().analyze(
                audio_file=str(audio_file),
                scenes=scenes,
            ),
        )

        progress.report(11, "Scoring highlight scenes")
        highlight_features = stage_runner.run(
            stage="Extracting highlight features",
            action=lambda: HighlightFeatureExtractor().extract(
                scene_analyses=scene_analyses,
                motion_features=motion_features,
                audio_features=audio_features,
            ),
        )
        highlight_scores = stage_runner.run(
            stage="Scoring highlight scenes",
            action=lambda: HighlightScorer().score(highlight_features),
        )

        progress.report(12, "Selecting highlight candidates")
        selector = self._create_selector(
            config=config,
            is_facecam_mode=recording_session.has_facecam_layout,
        )
        candidates = stage_runner.run(
            stage="Selecting highlight candidates",
            action=lambda: selector.select(
                scores=highlight_scores,
                video_duration_seconds=video_info.duration_seconds,
            ),
        )
        candidates = stage_runner.run(
            stage="Resolving highlight overlaps",
            action=lambda: HighlightOverlapResolver().resolve(candidates),
        )

        candidates = candidates[:25]
        print(
            "Fast Analysis Mode: deeply analyzing "
            f"{len(candidates)} highest-scoring candidates."
        )

        progress.report(13, "Generating lightweight analysis clips")
        clip_generator = HighlightClipGenerator()
        generated_highlights = stage_runner.run(
            stage="Generating lightweight analysis clips",
            action=lambda: clip_generator.generate(
                video_file=analysis_video_file,
                candidates=candidates,
                output_folder=str(analysis_highlight_folder),
                analysis_mode=True,
            ),
        )

        progress.report(14, "Running commentary AI reasoning")
        if feature_settings.commentary_ai_enabled:
            commentary_results = stage_runner.run(
                stage="Running commentary AI reasoning",
                action=lambda: HighlightReasoner().reason(
                    generated_highlights
                ),
            )
        else:
            commentary_results = ShortsFeatureFallbacks.commentary(
                generated_highlights
            )

        analyzed_highlights = stage_runner.run(
            stage="Combining commentary analysis",
            action=lambda: HighlightAnalysisCombiner().combine(
                highlights=generated_highlights,
                reasoning_results=commentary_results,
            ),
        )

        progress.report(15, "Extracting representative frames")
        highlight_frames: dict[int, list[str]] = {}

        if feature_settings.visual_ai_enabled:
            frame_extractor = HighlightFrameExtractor(
                frame_count=1,
                maximum_frame_width=512,
            )

            for highlight in generated_highlights:
                frame_files = stage_runner.run(
                    stage=(
                        "Extracting representative frames "
                        f"for rank {highlight.rank}"
                    ),
                    action=lambda current=highlight: frame_extractor.extract(
                        highlight=current,
                        output_folder=str(frame_folder),
                    ),
                )
                highlight_frames[highlight.rank] = frame_files

        progress.report(16, "Running visual AI reasoning")
        if feature_settings.visual_ai_enabled:
            visual_reasoner = VisualHighlightReasoner()
            stage_runner.run(
                stage="Warming up visual AI model",
                action=visual_reasoner.warm_up,
                cacheable=False,
            )
            visual_results = {}

            for highlight in generated_highlights:
                result = stage_runner.run(
                    stage=(
                        "Running visual AI reasoning "
                        f"for rank {highlight.rank}"
                    ),
                    action=lambda current=highlight: visual_reasoner.reason(
                        highlight=current,
                        frame_files=highlight_frames.get(
                            current.rank,
                            [],
                        ),
                    ),
                )
                visual_results[highlight.rank] = result
        else:
            visual_results = ShortsFeatureFallbacks.visual(
                generated_highlights
            )

        progress.report(17, "Fusing multimodal AI decisions")
        if feature_settings.fusion_ai_enabled:
            fusion_reasoner = HighlightFusionReasoner()
            fusion_results = []

            for analyzed_highlight in analyzed_highlights:
                visual_result = visual_results.get(
                    analyzed_highlight.rank
                )
                if visual_result is None:
                    continue

                fusion_results.append(
                    stage_runner.run(
                        stage=(
                            "Fusing multimodal AI decisions "
                            f"for rank {analyzed_highlight.rank}"
                        ),
                        action=lambda current=analyzed_highlight, visual=visual_result: (
                            fusion_reasoner.reason(
                                analyzed_highlight=current,
                                visual_reasoning=visual,
                            )
                        ),
                    )
                )
        else:
            fusion_results = ShortsFeatureFallbacks.fusion(
                analyzed_highlights=analyzed_highlights,
                visual_results=visual_results,
            )

        progress.report(18, "Selecting final approved highlights")
        approved_results = stage_runner.run(
            stage="Selecting final approved highlights",
            action=lambda: FinalHighlightSelector(
                minimum_confidence=0.70,
            ).select(fusion_results),
        )

        progress.report(19, "Extracting approved source clips")
        approved_ranks = {result.rank for result in approved_results}
        approved_candidates = [
            candidate
            for candidate in candidates
            if candidate.rank in approved_ranks
        ]
        source_highlights = stage_runner.run(
            stage="Extracting approved source clips",
            action=lambda: clip_generator.generate(
                video_file=str(video_path),
                candidates=approved_candidates,
                output_folder=str(highlight_folder),
                analysis_mode=False,
            ),
        )
        final_highlights = stage_runner.run(
            stage="Linking approved decisions to source clips",
            action=lambda: FinalHighlightCombiner().combine(
                highlights=source_highlights,
                approved_results=approved_results,
            ),
        )

        progress.report(20, "Exporting final highlight package")
        if feature_settings.raw_highlight_export_enabled:
            exported_files = stage_runner.run(
                stage="Exporting final highlight package",
                action=lambda: FinalHighlightExporter().export(
                    highlights=final_highlights,
                    output_folder=str(output_path / "highlights"),
                ),
            )
        else:
            exported_files = []

        progress.report(21, "Building final YouTube Short packages")
        short_packages = stage_runner.run(
            stage="Building final YouTube Short packages",
            action=lambda: ShortPackageBatchBuilder(
                feature_settings=feature_settings,
                checkpoint_cache=checkpoint_cache,
            ).build(
                highlights=final_highlights,
                output_folder=str(short_package_folder),
                recording_session=recording_session,
                layout_type=layout_type,
            ),
            cacheable=False,
        )

        result = PipelineResult(
            source_video_file=str(video_path),
            video_duration_seconds=video_info.duration_seconds,
            final_highlights=final_highlights,
            exported_files=exported_files,
            short_packages=short_packages,
            stage_timings=list(stage_runner.timings),
        )

        if not feature_settings.keep_intermediate_files:
            self._remove_intermediate_files(
                paths=[
                    analysis_proxy_file,
                    audio_file,
                    analysis_highlight_folder,
                    speech_folder,
                    frame_folder,
                ]
            )

        return result

    @staticmethod
    def _create_selector(
        config: Config,
        is_facecam_mode: bool,
    ) -> HighlightSelector:
        """Create the configured duration selector."""

        if not is_facecam_mode:
            return HighlightSelector()

        shorts_config = config.get("shorts")

        selector = HighlightSelector(
            minimum_score=0.0,
            minimum_highlight_duration_seconds=float(
                shorts_config["minimum_duration"]
            ),
            preferred_highlight_duration_seconds=float(
                shorts_config["preferred_duration"]
            ),
            maximum_highlight_duration_seconds=float(
                shorts_config["maximum_duration"]
            ),
        )

        print(
            "Facecam Short durations: "
            f"{shorts_config['minimum_duration']}-"
            f"{shorts_config['maximum_duration']} seconds "
            f"(preferred {shorts_config['preferred_duration']} seconds)."
        )
        return selector

    @staticmethod
    def _remove_intermediate_files(paths: list[Path]) -> None:
        """Remove only regeneratable working artifacts."""

        for path in paths:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)

    @staticmethod
    def _print_feature_summary(
        settings: ShortsFeatureSettings,
    ) -> None:
        """Print the shared Option 1 and Option 2 feature profile."""

        print()
        print("Short feature profile")
        print(f"  Captions            : {settings.captions_enabled}")
        print(f"  Transcription       : {settings.transcription_enabled}")
        print(f"  Commentary AI       : {settings.commentary_ai_enabled}")
        print(f"  Visual AI           : {settings.visual_ai_enabled}")
        print(f"  Fusion AI           : {settings.fusion_ai_enabled}")
        print(f"  Metadata            : {settings.metadata_enabled}")
        print(
            "  Raw highlight export: "
            f"{settings.raw_highlight_export_enabled}"
        )
        print(
            "  Keep intermediates  : "
            f"{settings.keep_intermediate_files}"
        )
        print()
