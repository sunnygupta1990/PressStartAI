from __future__ import annotations

import json
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np


class VideoTools:
    def __init__(self, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe", export_threads: int = 2) -> None:
        self.ffmpeg = ffmpeg
        self.ffprobe = ffprobe
        self.export_threads = max(1, min(int(export_threads), 4))
        self._frame_locks: dict[str, threading.Lock] = {}
        self._frame_locks_guard = threading.Lock()

    def _frame_lock(self, output: Path) -> threading.Lock:
        key = str(output.resolve())
        with self._frame_locks_guard:
            return self._frame_locks.setdefault(key, threading.Lock())

    def probe(self, video_file: str) -> dict:
        path = Path(video_file)
        if not path.is_file():
            raise FileNotFoundError(path)
        if shutil.which(self.ffprobe) is None:
            raise RuntimeError("ffprobe was not found on PATH.")
        command = [
            self.ffprobe, "-v", "error", "-print_format", "json",
            "-show_streams", "-show_format", str(path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")
        data = json.loads(result.stdout)
        video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
        if not video:
            raise RuntimeError("No video stream found.")
        duration = float(data.get("format", {}).get("duration") or video.get("duration") or 0)
        if duration <= 0:
            raise RuntimeError("Unable to determine video duration.")
        return {
            "duration_seconds": duration,
            "width": int(video.get("width") or 0),
            "height": int(video.get("height") or 0),
            "fps": self._fps(video.get("r_frame_rate", "0/1")),
        }

    @staticmethod
    def _fps(value: str) -> float:
        try:
            a, b = value.split("/", 1)
            return float(a) / float(b)
        except (ValueError, ZeroDivisionError):
            return 0.0

    def extract_frames(
        self, video_file: str, timestamps: Iterable[float], output_dir: str, prefix: str
    ) -> list[str]:
        targets = sorted(set(max(0.0, float(t)) for t in timestamps))
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        if not targets:
            return []

        capture = cv2.VideoCapture(str(video_file))
        if not capture.isOpened():
            raise RuntimeError(f"Unable to open video: {video_file}")
        fps = capture.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            capture.release()
            raise RuntimeError("Unable to determine video FPS.")

        generated: list[str] = []
        try:
            for index, target in enumerate(targets, start=1):
                # Seeking is used deliberately: this stage must not decode the whole 60 FPS stream.
                capture.set(cv2.CAP_PROP_POS_MSEC, target * 1000.0)
                ok, frame = capture.read()
                if not ok:
                    continue
                h, w = frame.shape[:2]
                if w > 768:
                    frame = cv2.resize(
                        frame, (768, max(1, round(h * 768 / w))),
                        interpolation=cv2.INTER_AREA,
                    )
                path = output / f"{prefix}_{index:03d}_{target:.3f}.jpg"
                if cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 82]):
                    generated.append(str(path))
        finally:
            capture.release()
        return generated

    def extract_sparse_timeline(
        self, video_file: str, duration: float, interval: float, cache_dir: str
    ) -> dict[float, str]:
        """Build a reusable sparse frame timeline with one FFmpeg process.

        Frames are sampled at a fixed global interval so overlapping AI windows
        reuse exactly the same images instead of opening/seeking the MP4 for
        every requested timestamp.
        """
        source = Path(video_file).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Gameplay video not found: {source}")
        if duration <= 0:
            raise ValueError("Video duration must be positive.")
        if interval <= 0:
            raise ValueError("Sparse-frame interval must be positive.")
        cache = Path(cache_dir)
        cache.mkdir(parents=True, exist_ok=True)
        manifest = cache / "sparse_frames_manifest.json"
        signature = self._video_signature(video_file, duration, interval)
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                if data.get("signature") == signature:
                    frames = {
                        round(float(k), 3): str(v)
                        for k, v in data.get("frames", {}).items()
                        if Path(v).is_file() and Path(v).stat().st_size > 0
                    }
                    if frames:
                        return frames
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                pass

        frame_dir = cache / "sparse_timeline"
        frame_dir.mkdir(parents=True, exist_ok=True)
        for old in frame_dir.glob("frame_*.jpg"):
            old.unlink(missing_ok=True)

        # FFmpeg performs the sparse sampling in one process. This replaces
        # thousands of OpenCV seek/open operations across overlapping windows.
        fps_expr = f"1/{max(0.25, float(interval)):.6f}"
        pattern = frame_dir / "frame_%06d.jpg"
        command = [
            self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(source),
            "-vf", f"fps={fps_expr},scale=768:-2",
            "-q:v", "4",
            "-frames:v", str(max(1, int(duration / interval) + 2)),
            str(pattern),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Sparse frame extraction failed: {result.stderr.strip()}")

        frames: dict[float, str] = {}
        files = sorted(frame_dir.glob("frame_*.jpg"))
        for idx, path in enumerate(files):
            timestamp = round(idx * float(interval), 3)
            if timestamp <= duration + float(interval):
                frames[timestamp] = str(path)

        payload = {"signature": signature, "frames": {str(k): v for k, v in frames.items()}}
        tmp = manifest.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        tmp.replace(manifest)
        return frames

    @staticmethod
    def _video_signature(video_file: str, duration: float, interval: float) -> dict:
        path = Path(video_file)
        stat = path.stat()
        return {
            "path": str(path.resolve()),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "duration": round(float(duration), 3),
            "interval": round(float(interval), 3),
        }

    def extract_cached_frame(self, video_file: str, timestamp: float, cache_dir: str) -> str:
        """Extract one analysis frame once and reuse it across overlapping windows."""
        from pathlib import Path
        cache = Path(cache_dir)
        cache.mkdir(parents=True, exist_ok=True)
        stat = Path(video_file).stat()
        video_key = f"{stat.st_size}_{stat.st_mtime_ns}"
        key = f"{Path(video_file).stem}_{video_key}_{int(round(timestamp * 1000)):012d}"
        output = cache / f"{key}.jpg"
        lock = self._frame_lock(output)
        with lock:
            if output.exists() and output.stat().st_size > 0:
                return str(output)

            frames = self.extract_frames(
                video_file, [timestamp], str(cache), f"frame_{key}"
            )
            if not frames:
                raise RuntimeError(f"Unable to extract frame at {timestamp:.3f}s")
            source = Path(frames[0])
            if source != output:
                source.replace(output)
            return str(output)

    def build_timeline_from_sparse_frames(
        self, frames: dict[float, str], duration: float, interval: float
    ) -> list[dict]:
        """Compute timeline observations from the already extracted sparse frames."""
        observations = []
        previous_histogram = None
        previous_gray = None
        for timestamp, path in sorted(frames.items()):
            image = cv2.imread(path)
            if image is None:
                continue
            small = cv2.resize(image, (160, 90), interpolation=cv2.INTER_AREA)
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            histogram = cv2.calcHist([gray], [0], None, [32], [0, 256])
            cv2.normalize(histogram, histogram)
            change = 0.0 if previous_histogram is None else float(
                cv2.compareHist(previous_histogram, histogram, cv2.HISTCMP_BHATTACHARYYA)
            )
            motion = float(np.abs(gray.astype(np.float32) -
                                  previous_gray.astype(np.float32)).mean()) if previous_gray is not None else float(gray.std())
            observations.append({
                "timestamp": round(float(timestamp), 3),
                "visual_change_score": change,
                "motion_score": motion,
                "brightness": float(gray.mean()),
            })
            previous_histogram = histogram
            previous_gray = gray
        return observations

    def export_clip(self, video_file: str, start: float, end: float, output_file: str) -> str:
        if end <= start:
            raise ValueError("Clip end must be greater than start.")
        output = Path(output_file)
        output.parent.mkdir(parents=True, exist_ok=True)
        duration = end - start
        temporary = output.with_name(output.stem + ".temporary.mp4")
        command = [
            self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{start:.3f}", "-i", str(video_file),
            "-t", f"{duration:.3f}", "-map", "0:v:0", "-map", "0:a?",
            "-threads", str(self.export_threads), "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
            str(temporary),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            temporary.unlink(missing_ok=True)
            raise RuntimeError(f"FFmpeg clip export failed: {result.stderr.strip()}")
        if not temporary.is_file() or temporary.stat().st_size == 0:
            raise RuntimeError("FFmpeg produced an empty clip.")
        temporary.replace(output)
        return str(output)


class TimelineScanner:
    """Fast timestamp-based scan with incremental, resumable checkpoints."""

    CHECKPOINT_VERSION = 2

    def __init__(self, sample_interval_seconds: float = 2.0, checkpoint_every: int = 25) -> None:
        if sample_interval_seconds <= 0:
            raise ValueError("sample_interval_seconds must be positive.")
        self.sample_interval_seconds = sample_interval_seconds
        self.checkpoint_every = max(1, checkpoint_every)

    @staticmethod
    def video_signature(video_file: str, duration: float) -> dict:
        path = Path(video_file)
        stat = path.stat()
        return {
            "path": str(path.resolve()),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "duration_seconds": round(float(duration), 3),
        }

    def _load(self, checkpoint: Path, video_file: str, duration: float):
        if not checkpoint.is_file():
            return None
        try:
            data = json.loads(checkpoint.read_text(encoding="utf-8"))
            if data.get("version") != self.CHECKPOINT_VERSION:
                return None
            if float(data.get("sample_interval_seconds", 0)) != self.sample_interval_seconds:
                return None
            if data.get("video") != self.video_signature(video_file, duration):
                return None
            observations = data.get("observations")
            next_index = int(data.get("next_sample_index", len(observations or [])))
            if not isinstance(observations, list):
                return None
            return observations, max(0, next_index), data.get("previous_histogram")
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return None

    def _save(
        self, checkpoint: Path, video_file: str, duration: float,
        observations: list[dict], next_sample_index: int
    ) -> None:
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": self.CHECKPOINT_VERSION,
            "sample_interval_seconds": self.sample_interval_seconds,
            "video": self.video_signature(video_file, duration),
            "next_sample_index": next_sample_index,
            "observations": [{k: v for k, v in item.items() if k != "_histogram"} for item in observations],
            "previous_histogram": observations[-1].get("_histogram") if observations else None,
        }
        temp = checkpoint.with_suffix(".tmp")
        temp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        temp.replace(checkpoint)

    def scan(
        self, video_file: str, duration: float, checkpoint_file: str | None = None
    ) -> list[dict]:
        checkpoint = Path(checkpoint_file) if checkpoint_file else None
        total = max(1, int(duration / self.sample_interval_seconds) + 1)
        observations: list[dict] = []
        start_index = 0
        previous_histogram = None

        if checkpoint:
            loaded = self._load(checkpoint, video_file, duration)
            if loaded:
                observations, start_index, previous_histogram = loaded
                print(f"Timeline checkpoint found: {len(observations)} observations saved.")
                if start_index >= total:
                    print(f"Timeline scan already complete: {len(observations)} observations.")
                    return observations

        capture = cv2.VideoCapture(str(video_file))
        if not capture.isOpened():
            raise RuntimeError(f"Unable to open video: {video_file}")

        try:
            for sample_index in range(start_index, total):
                timestamp = min(
                    sample_index * self.sample_interval_seconds,
                    max(0.0, duration - 0.05),
                )
                capture.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000.0)
                ok, frame = capture.read()
                if not ok:
                    continue

                small = cv2.resize(frame, (160, 90), interpolation=cv2.INTER_AREA)
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
                histogram = cv2.calcHist([gray], [0], None, [32], [0, 256])
                cv2.normalize(histogram, histogram)

                previous = previous_histogram
                if previous is not None:
                    previous_array = np.asarray(previous, dtype=np.float32)
                    change = float(cv2.compareHist(
                        previous_array, histogram, cv2.HISTCMP_BHATTACHARYYA
                    ))
                else:
                    change = 0.0

                # Histograms are checkpoint-only state; they are removed from public observations below.
                observations.append({
                    "timestamp": round(timestamp, 3),
                    "visual_change_score": change,
                    "motion_score": float(gray.std()),
                    "brightness": float(gray.mean()),
                    "_histogram": histogram.flatten().tolist(),
                })
                previous_histogram = histogram.flatten().tolist()

                progress = min(1.0, (sample_index + 1) / total)
                width = 30
                filled = int(progress * width)
                bar = "█" * filled + "░" * (width - filled)
                print(
                    f"\rScanning video [{bar}] {progress * 100:6.2f}% "
                    f"| {timestamp / 60:6.1f} / {duration / 60:6.1f} min",
                    end="", flush=True,
                )

                if checkpoint and (
                    (sample_index + 1) % self.checkpoint_every == 0
                    or sample_index == total - 1
                ):
                    self._save(checkpoint, video_file, duration, observations, sample_index + 1)

            print()
        finally:
            capture.release()

        # Never expose internal histogram data to later stages.
        clean = [
            {k: v for k, v in item.items() if k != "_histogram"}
            for item in observations
        ]
        if checkpoint:
            self._save(checkpoint, video_file, duration, observations, total)
        print(f"Timeline scan complete: {len(clean)} observations.")
        return clean
