from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import subprocess

from src.services.video_analysis_proxy import VideoAnalysisProxy
from src.services.voice_activity_detector import VoiceActivityDetector
from src.services.speech_chunk_extractor import SpeechChunkExtractor
from src.services.asr.transcription_pipeline import TranscriptionPipeline
from src.services.scene_detector import SceneDetector
from src.services.scene_transcript_mapper import SceneTranscriptMapper
from src.services.motion_analyzer import MotionAnalyzer
from src.services.audio_analyzer import AudioAnalyzer


FAST_ANALYSIS_SCHEMA_VERSION = "4.1.0"
SHARED_ANALYSIS_ARTIFACT = ".pressstartai_shared_analysis.json"


@dataclass(slots=True)
class FastScene:
    start: float
    end: float
    score: float
    speech: bool
    transcript: str
    motion: float
    audio: float


@dataclass(slots=True)
class FastAnalysisResult:
    scenes: list[FastScene]
    speech: list[tuple[float, float]]
    transcript: list[dict]
    proxy_path: str
    version: str = FAST_ANALYSIS_SCHEMA_VERSION


class _FFmpegAudioExtractor:
    """CLI-only FFmpeg adapter; does not require the Python ffmpeg package."""

    def __init__(self, ffmpeg_bin: str = "ffmpeg") -> None:
        self.ffmpeg_bin = ffmpeg_bin

    def extract(self, input_video: str, output_audio: str) -> str:
        command = [
            self.ffmpeg_bin, "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(input_video), "-vn", "-ac", "1", "-ar", "16000",
            "-c:a", "pcm_s16le", str(output_audio),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Audio extraction failed: {result.stderr.strip()}")
        return output_audio


def shared_analysis_path(output_dir: str) -> Path:
    """Canonical shared-analysis artifact consumed by downstream features."""
    return Path(output_dir) / SHARED_ANALYSIS_ARTIFACT


class FastGameplayPreAnalyzer:
    """
    Single shared analysis artifact for Gameplay Segmentation.

    It deliberately uses the same PressStartAI service layer (proxy, VAD,
    chunking, Qwen ASR, scenes, motion and audio) once and persists the result.
    Downstream stages consume this artifact rather than re-running ASR/audio.
    """

    VERSION = FAST_ANALYSIS_SCHEMA_VERSION

    def __init__(self, cache_dir: Path, cpu_workers: int = 12, shared_analysis_path: str | None = None) -> None:
        self.cache_dir = cache_dir
        self.cpu_workers = max(1, int(cpu_workers))
        self.shared_analysis_path = Path(shared_analysis_path).expanduser().resolve() if shared_analysis_path else None

    def _read(self, name: str):
        path = self.cache_dir / name
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _write(self, name: str, value) -> None:
        path = self.cache_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    @staticmethod
    def _signature(video_file: str, duration: float) -> dict:
        source = Path(video_file).resolve()
        stat = source.stat()
        return {
            "path": str(source),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "duration": round(duration, 3),
        }

    def _discover_external_shared_analysis(self, video_file: str, duration: float) -> dict | None:
        """Optionally consume a sidecar shared artifact emitted by PressStartAI.

        This is additive: existing PressStartAI behavior is untouched. If no
        artifact exists, Gameplay Segmentation builds its own shared artifact.
        """
        source = Path(video_file).resolve()
        candidates = []
        if self.shared_analysis_path is not None:
            candidates.append(self.shared_analysis_path)
        candidates.extend([
            source.parent / SHARED_ANALYSIS_ARTIFACT,
            source.with_suffix(source.suffix + SHARED_ANALYSIS_ARTIFACT),
        ])
        for candidate in candidates:
            if not candidate.is_file():
                continue
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
                if (
                    payload.get("version") == self.VERSION
                    and payload.get("video") == self._signature(video_file, duration)
                    and Path(payload.get("proxy_path", "")).is_file()
                ):
                    return payload
            except Exception:
                continue
        return None

    def run(self, video_file: str, duration: float) -> FastAnalysisResult:
        signature = self._signature(video_file, duration)
        external = self._discover_external_shared_analysis(video_file, duration)
        if external is not None:
            self._write("shared_analysis.json", external)
            return self._decode(external)

        cached = self._read("shared_analysis.json")
        if (
            isinstance(cached, dict)
            and cached.get("version") == self.VERSION
            and cached.get("video") == signature
            and Path(cached.get("proxy_path", "")).is_file()
        ):
            return self._decode(cached)

        work = self.cache_dir / "fast_analysis"
        work.mkdir(parents=True, exist_ok=True)
        proxy_path = work / "analysis_proxy.mp4"
        audio_path = work / "audio.wav"

        print("[SHARED] Creating/reusing PressStartAI analysis proxy...")
        proxy = VideoAnalysisProxy(maximum_width=960, frame_rate=15).create(
            input_video=video_file, output_video=str(proxy_path)
        )

        print("[SHARED] Extracting audio once...")
        audio = _FFmpegAudioExtractor().extract(video_file, str(audio_path))

        print("[SHARED] Detecting speech with VAD...")
        speech_segments = VoiceActivityDetector().detect(audio)

        speech_chunks = SpeechChunkExtractor().extract(
            input_audio=audio,
            speech_segments=speech_segments,
            output_folder=str(work / "speech_chunks"),
            merge_gap_seconds=2.0,
            maximum_chunk_seconds=20.0,
        )

        print(f"[SHARED] Transcribing {len(speech_chunks)} speech chunks with Qwen...")
        transcript_segments = (
            TranscriptionPipeline().transcribe(speech_chunks)
            if speech_chunks else []
        )

        print("[SHARED] Detecting scenes...")
        scenes = SceneDetector().detect(proxy)

        print(f"[SHARED] Measuring motion/audio for {len(scenes)} scenes...")
        scene_analyses = SceneTranscriptMapper().map(scenes, transcript_segments)
        motion = MotionAnalyzer(sample_interval_frames=5).analyze(proxy, scenes)
        audio_features = AudioAnalyzer().analyze(audio, scenes)

        motion_values = [x.maximum_motion_score for x in motion]
        audio_values = [x.maximum_rms for x in audio_features]

        def norm(values, value):
            if not values:
                return 0.0
            lo, hi = min(values), max(values)
            return 0.0 if hi <= lo else max(0.0, min(1.0, (value - lo) / (hi - lo)))

        def intersects(start: float, end: float) -> bool:
            return any(a < end and b > start for a, b in speech_timeline)

        speech_timeline = [
            (float(x[0]) / 16000.0, float(x[1]) / 16000.0)
            for x in speech_segments
            if isinstance(x, (list, tuple)) and len(x) >= 2
        ]

        result = []
        for analysis, m, a in zip(scene_analyses, motion, audio_features, strict=True):
            duration_s = analysis.scene.end_seconds - analysis.scene.start_seconds
            transcript = analysis.transcript_text.strip()
            # VAD, not ASR, determines whether speech exists. ASR enriches it.
            speech = intersects(analysis.scene.start_seconds, analysis.scene.end_seconds)
            score = (
                0.34 * norm(motion_values, m.maximum_motion_score)
                + 0.24 * norm(audio_values, a.maximum_rms)
                + 0.27 * (1.0 if speech else 0.0)
                + 0.15 * min(1.0, max(0.0, duration_s / 12.0))
            )
            if duration_s >= 1.5:
                result.append(FastScene(
                    start=analysis.scene.start_seconds,
                    end=analysis.scene.end_seconds,
                    score=score,
                    speech=speech,
                    transcript=transcript,
                    motion=m.maximum_motion_score,
                    audio=a.maximum_rms,
                ))

        transcript_payload = [
            {
                "start": float(x.start_seconds),
                "end": float(x.end_seconds),
                "text": str(x.text).strip(),
                "language": str(x.language),
            }
            for x in transcript_segments
        ]

        payload = {
            "version": self.VERSION,
            "video": signature,
            "proxy_path": str(Path(proxy).resolve()),
            "speech": [[a, b] for a, b in speech_timeline],
            "transcript": transcript_payload,
            "scenes": [
                {
                    "start": s.start, "end": s.end, "score": s.score,
                    "speech": s.speech, "transcript": s.transcript,
                    "motion": s.motion, "audio": s.audio,
                }
                for s in result
            ],
        }
        self._write("shared_analysis.json", payload)
        # Compatibility artifact for older runs/tools.
        self._write("fast_preanalysis.json", payload)
        print(
            f"[SHARED] Complete: {len(result)} scenes, "
            f"{len(transcript_payload)} transcript segments."
        )
        return self._decode(payload)

    @staticmethod
    def _decode(payload: dict) -> FastAnalysisResult:
        scenes = [
            FastScene(
                float(x["start"]), float(x["end"]), float(x["score"]),
                bool(x["speech"]), str(x.get("transcript", "")),
                float(x.get("motion", 0.0)), float(x.get("audio", 0.0)),
            )
            for x in payload.get("scenes", [])
        ]
        speech = [(float(x[0]), float(x[1])) for x in payload.get("speech", [])]
        transcript = [
            dict(x) for x in payload.get("transcript", [])
            if isinstance(x, dict)
        ]
        return FastAnalysisResult(
            scenes=scenes,
            speech=speech,
            transcript=transcript,
            proxy_path=str(payload.get("proxy_path", "")),
        )
