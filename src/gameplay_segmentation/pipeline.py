from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
import re
import shutil
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from src.gameplay_segmentation.event_engine import TemporalEventEngine
from src.gameplay_segmentation.exporter import TransactionalExporter
from src.gameplay_segmentation.models import Event, EventState
import hashlib
from pathlib import Path

from threading import Lock

from src.gameplay_segmentation.audio import SpeechTimeline, extract_audio
from src.gameplay_segmentation.fast_analysis import FastGameplayPreAnalyzer, FastAnalysisResult, FastScene
from src.gameplay_segmentation.categories import character_subcategory, normalize_category
from src.gameplay_segmentation.dedupe import remove_redundant
from src.gameplay_segmentation.models import ClipCandidate, ClipRecord, EventRegion
from src.gameplay_segmentation.video import TimelineScanner, VideoTools
from src.gameplay_segmentation.vision import OllamaGameplayReasoner



class GameplaySegmentationPipeline:
    """Standalone, resumable gameplay semantic clip segmentation."""

    CACHE_VERSION = 8
    STAGE_VERSIONS = {
        "timeline": 4,
        "speech": 2,
        "windows": 5,
        "vision": 5,
        "events": 4,
        "candidates": 5,
        "fast_preanalysis": 4,
        "stage_state": 2,
        "vision_schema": 2,
    }

    def __init__(
        self,
        *,
        output_root: str = "output/gameplay_segments",
        vision_model: str = "gemma3:4b",
        scan_interval_seconds: float = 2.0,
        analysis_window_seconds: float = 10.0,
        analysis_stride_seconds: float = 8.0,
        frame_interval_seconds: float = 2.0,
        min_clip_seconds: float = 3.0,
        max_clip_seconds: float = 9.0,
        max_ai_windows: int = 0,
        ai_workers: int = 2,
        cpu_workers: int = 12,
        shared_analysis_path: str | None = None,
    ) -> None:
        self.output_root = Path(output_root)
        self.scan_interval = scan_interval_seconds
        self.analysis_window = analysis_window_seconds
        self.analysis_stride = analysis_stride_seconds
        self.frame_interval = frame_interval_seconds
        self.min_clip = max(3.0, min_clip_seconds)
        self.max_clip = min(9.0, max_clip_seconds)
        self.max_ai_windows = max(0, int(max_ai_windows))
        self.ai_workers = max(1, min(4, ai_workers))
        self.cpu_workers = max(1, min(int(cpu_workers), 16))
        self.shared_analysis_path = shared_analysis_path
        self.video = VideoTools()
        self.reasoner = OllamaGameplayReasoner(model=vision_model)
        self._frame_lock = Lock()
        self._transcript_lock = Lock()
        self._export_manifest_lock = Lock()

    @staticmethod
    def _safe_name(value: str) -> str:
        return re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_") or "gameplay"

    def frame_cache_dir(self, video_file: str) -> Path:
        path = self.cache_dir(video_file) / "frames"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def cache_dir(self, video_file: str) -> Path:
        source = Path(video_file).expanduser().resolve()
        return self.output_root / self._safe_name(source.stem) / "_cache"

    def clear_cache(self, video_file: str) -> Path:
        path = self.cache_dir(video_file)
        shutil.rmtree(path, ignore_errors=True)
        source = Path(video_file).expanduser().resolve()
        source_root = self.output_root / self._safe_name(source.stem)
        for run_dir in source_root.glob("run_*"):
            if run_dir.is_dir() and (run_dir / ".incomplete").exists():
                shutil.rmtree(run_dir, ignore_errors=True)
        return path

    def _cache_file(self, video_file: str, name: str) -> Path:
        path = self.cache_dir(video_file) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _write_json(self, path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temp.replace(path)

    def _read_json(self, path: Path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return None

    def _cache_valid(self, video_file: str, duration: float, settings: dict) -> bool:
        meta = self._read_json(self._cache_file(video_file, "cache_meta.json"))
        if meta and meta.get("stage_versions") != self.STAGE_VERSIONS:
            for name in (
                "analysis_windows.json", "vision_results.json",
                "events.json", "candidates.json",
            ):
                self._cache_file(video_file, name).unlink(missing_ok=True)
            meta = {}

        if not isinstance(meta, dict):
            return False
        return (
            meta.get("version") == self.CACHE_VERSION
            and meta.get("video") == TimelineScanner.video_signature(video_file, duration)
            and meta.get("settings") == settings
        )

    def _ensure_cache_meta(self, video_file: str, duration: float) -> None:
        settings = {
            "scan_interval": self.scan_interval,
            "analysis_window": self.analysis_window,
            "analysis_stride": self.analysis_stride,
            "frame_interval": self.frame_interval,
            "min_clip": self.min_clip,
            "max_clip": self.max_clip,
            "max_ai_windows": self.max_ai_windows,
            "vision_model": self.reasoner.model,
        }
        meta = {
            "version": self.CACHE_VERSION,
            "stage_versions": self.STAGE_VERSIONS,
            "video": TimelineScanner.video_signature(video_file, duration),
            "settings": settings,
        }
        existing = self._read_json(self._cache_file(video_file, "cache_meta.json"))
        if existing != meta:
            # Settings changed: preserve timeline, speech and completed vision work.
            # Analysis windows/events/candidates are derived from the current settings.
            # vision_results are keyed by their exact time range and can be safely reused.
            cache = self.cache_dir(video_file)
            # Preserve raw timeline, speech, and successful vision results.
            # Derived stages are rebuilt against the new settings.
            old_stages = existing.get("stage_versions", {}) if isinstance(existing, dict) else {}
            old_cache_version = existing.get("version") if isinstance(existing, dict) else None
            names = [
                "analysis_windows.json", "event_regions.json", "events.json",
                "candidates.json", "stage_state.json",
            ]
            if old_cache_version != self.CACHE_VERSION:
                names.extend(["shared_analysis.json", "fast_preanalysis.json", "vision_results.json"])
            if old_stages.get("timeline") != self.STAGE_VERSIONS["timeline"]:
                names.append("timeline.json")
            if old_stages.get("fast_preanalysis") != self.STAGE_VERSIONS["fast_preanalysis"]:
                names.append("shared_analysis.json")
                names.append("fast_preanalysis.json")
            old_settings = existing.get("settings", {}) if isinstance(existing, dict) else {}
            if old_settings.get("vision_model") != settings.get("vision_model"):
                names.append("vision_results.json")
            for name in names:
                (cache / name).unlink(missing_ok=True)
            self._write_json(self._cache_file(video_file, "cache_meta.json"), meta)

    def _timeline(self, source: Path, duration: float) -> list[dict]:
        cache = self._cache_file(str(source), "timeline.json")
        cached = self._read_json(cache)
        if isinstance(cached, list) and cached:
            return cached

        sparse = getattr(self, "_sparse_frames", {})
        if sparse:
            observations = self.video.build_timeline_from_sparse_frames(
                sparse, duration, self.frame_interval
            )
            self._write_json(cache, observations)
            return observations

        scanner = TimelineScanner(self.scan_interval, checkpoint_every=25)
        return scanner.scan(str(source), duration, str(cache))
    @staticmethod
    def _vision_cache_key(
        start: float,
        end: float,
        model: str = "",
        ) -> str:
        """
        Stable cache key for semantic AI windows.
            """
        return (
            f"v2|{OllamaGameplayReasoner.PROMPT_VERSION}"
            f"|{model}|{start:.3f}-{end:.3f}"
        )   

    def _speech(self, source: Path, run_root: Path) -> list[tuple[float, float]]:
        cache = self._cache_file(str(source), "speech_timeline.json")
        cached = self._read_json(cache)
        if isinstance(cached, list):
            return [(float(x[0]), float(x[1])) for x in cached if len(x) == 2]

        audio_file = self.cache_dir(str(source)) / "analysis_audio.wav"
        try:
            extract_audio(str(source), str(audio_file))
            speech = SpeechTimeline(str(audio_file)).detect()
        except Exception as exc:
            (run_root / "speech_errors.log").write_text(
                f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
            )
            speech = []
        self._write_json(cache, speech)
        return speech

    def _segment_timeline_events(
        self, observations: list[dict], speech: list[tuple[float, float]], duration: float
    ) -> list[dict]:
        """Create deterministic coarse event regions before semantic AI analysis."""
        changes = [float(o.get("visual_change_score", 0.0)) for o in observations]
        motions = [float(o.get("motion_score", 0.0)) for o in observations]

        def zscore(values, value):
            mean = sum(values) / max(1, len(values))
            variance = sum((x - mean) ** 2 for x in values) / max(1, len(values))
            return (value - mean) / (math.sqrt(variance) or 1.0)

        regions = []
        for i, obs in enumerate(observations):
            score = (
                max(0.0, zscore(changes, changes[i])) * 0.70
                + max(0.0, zscore(motions, motions[i])) * 0.30
            )
            if score >= 0.75:
                t = float(obs["timestamp"])
                regions.append({
                    "start": max(0.0, t - self.analysis_window * 0.55),
                    "end": min(duration, t + self.analysis_window * 0.55),
                    "score": score,
                    "kind": "visual",
                })

        for start, end in speech:
            regions.append({
                "start": max(0.0, start - 2.0),
                "end": min(duration, end + 2.0),
                "score": 2.0,
                "kind": "speech",
            })

        if not regions:
            return [{"start": 0.0, "end": min(duration, self.analysis_window),
                     "score": 1.0, "kind": "coverage"}]

        regions.sort(key=lambda r: (r["start"], r["end"]))
        merged = []
        for region in regions:
            if not merged or region["start"] > merged[-1]["end"] + 1.5:
                merged.append(dict(region))
            else:
                previous = merged[-1]
                previous["end"] = max(previous["end"], region["end"])
                previous["score"] = max(previous["score"], region["score"])
                if region["kind"] == "speech":
                    previous["kind"] = "speech"
        return merged

    def _select_analysis_windows(
        self, observations: list[dict], duration: float, speech: list[tuple[float, float]]
    ) -> list[dict]:
        cache = self._cache_file(self._current_source, "analysis_windows.json")
        cached = self._read_json(cache)
        if isinstance(cached, list) and cached:
            return cached

        if not observations:
            windows = [{"index": 1, "start": 0.0, "end": min(duration, self.analysis_window), "score": 1.0, "kind": "coverage"}]
            self._write_json(cache, windows)
            return windows

        regions = self._segment_timeline_events(observations, speech, duration)
        self._write_json(
            self._cache_file(self._current_source, "event_regions.json"), regions
        )

        windows = []
        for region in regions:
            midpoint = (region["start"] + region["end"]) / 2.0
            start = max(0.0, min(
                midpoint - self.analysis_window / 2,
                max(0.0, duration - self.analysis_window)
            ))
            windows.append({
                "start": round(start, 3),
                "end": round(min(duration, start + self.analysis_window), 3),
                "score": round(float(region["score"]), 4),
                "kind": region["kind"],
            })

        for t in range(0, int(duration) + 1, 45):
            start = max(0.0, min(
                float(t) - self.analysis_window / 2,
                max(0.0, duration - self.analysis_window)
            ))
            windows.append({
                "start": round(start, 3),
                "end": round(min(duration, start + self.analysis_window), 3),
                "score": 0.05,
                "kind": "coverage",
            })

        unique = []
        # Speech windows are always considered before generic event windows.
        for window in sorted(
            (w for w in windows if w["kind"] == "speech"),
            key=lambda x: x["start"]
        ):
            if len(unique) >= self.max_ai_windows:
                break
            if not any(abs(window["start"] - x["start"]) < self.analysis_stride / 2 for x in unique):
                unique.append(window)

        for window in sorted(windows, key=lambda x: (-x["score"], x["start"])):
            if len(unique) >= self.max_ai_windows:
                break
            if not any(abs(window["start"] - x["start"]) < self.analysis_stride / 2 for x in unique):
                unique.append(window)

        unique.sort(key=lambda x: x["start"])
        result = [{"index": i, **window} for i, window in enumerate(unique, start=1)]
        self._write_json(cache, result)
        return result

    def _fast_scene_events(
        self,
        scenes: list[FastScene],
        selected_starts: set[float],
    ) -> list[EventRegion]:
        """Build cheap baseline events; only selected scenes need Gemma."""
        events: list[EventRegion] = []
        for scene in scenes:
            if any(abs(scene.start - start) < 0.01 for start in selected_starts):
                continue
            category = "Dialogue" if scene.speech else "Exploration"
            description = (
                scene.transcript[:120].strip()
                if scene.speech and scene.transcript
                else ("Gameplay movement and exploration"
                      if scene.score < 0.35
                      else "Gameplay action")
            )
            events.append(EventRegion(
                start_seconds=scene.start,
                end_seconds=min(scene.end, scene.start + self.max_clip),
                category=category,
                description=description,
                characters=(),
                location="Unknown",
                shot_type="Gameplay",
                dialogue_present=scene.speech,
                confidence=max(0.25, min(0.85, scene.score)),
                repetition=1.0 if scene.score < 0.22 else 0.0,
                source_window_start=scene.start,
                source_window_end=scene.end,
            ))
        return events

    def _stage_state_path(self, video_file: str) -> Path:
        return self._cache_file(video_file, "stage_state.json")

    def _set_stage(self, video_file: str, stage: str, status: str, **extra) -> None:
        path = self._stage_state_path(video_file)
        state = self._read_json(path)
        if not isinstance(state, dict):
            state = {}
        state[stage] = {"status": status, "updated": datetime.now().isoformat(timespec="seconds"), **extra}
        self._write_json(path, state)

    def _ai_budget(self, duration: float) -> int:
        # 0 means adaptive: semantic AI scales with video length instead of
        # creating an artificial 240-window ceiling.
        if self.max_ai_windows > 0:
            return self.max_ai_windows
        return max(8, min(16, math.ceil(duration / 480.0)))

    @staticmethod
    def _nearest_frame(frame_map: dict[float, str], timestamp: float) -> str | None:
        if not frame_map:
            return None
        key = min(frame_map, key=lambda t: abs(t - timestamp))
        return frame_map[key]

    def _select_semantic_windows(self, scenes: list[FastScene], duration: float, budget: int) -> list[dict]:
        if not scenes or budget <= 0:
            return []
        # Coverage is deterministic; AI is reserved for information-rich scenes.
        ranked = sorted(scenes, key=lambda x: (-x.score, x.start))
        chosen: list[FastScene] = []
        # Guarantee broad temporal coverage without forcing AI into every bucket.
        bucket_count = min(budget, max(1, math.ceil(duration / 300.0)))
        for i in range(bucket_count):
            a = i * duration / bucket_count
            b = (i + 1) * duration / bucket_count
            bucket = [x for x in scenes if x.start < b and x.end > a]
            if bucket:
                chosen.append(max(bucket, key=lambda x: (x.score, x.speech)))
        for scene in ranked:
            if len(chosen) >= budget:
                break
            if any(abs(scene.start - x.start) < 8.0 for x in chosen):
                continue
            chosen.append(scene)
        return [
            {
                "index": i,
                "start": round(max(0.0, min(scene.start - 1.5, duration)), 3),
                "end": round(min(duration, max(scene.end + 1.5, scene.start + 3.0)), 3),
                "score": round(scene.score, 4),
                "kind": "speech" if scene.speech else "event",
                "scene_start": scene.start,
                "scene_end": scene.end,
            }
            for i, scene in enumerate(sorted(chosen[:budget], key=lambda x: x.start), 1)
        ]

    @staticmethod
    def _baseline_category(scene: FastScene) -> str:
        if scene.speech:
            return "Dialogue"
        if scene.motion >= 0.65 and scene.audio >= 0.65:
            return "Fight"
        if scene.motion >= 0.70:
            return "Running"
        if scene.audio >= 0.75 and scene.motion < 0.35:
            return "Cinematic"
        if scene.motion < 0.18 and scene.audio < 0.25:
            return "Environment"
        return "Exploration"

    @staticmethod
    def _baseline_description(scene: FastScene) -> str:
        if scene.transcript:
            text = re.sub(r"\s+", " ", scene.transcript).strip()
            return text[:120]
        return "Gameplay activity"

    def _baseline_events(self, scenes: list[FastScene], selected_starts: set[float]) -> list[EventRegion]:
        events = []
        for scene in scenes:
            # AI will replace the selected scene; all other scenes retain a cheap
            # representative event so coverage does not depend on the AI budget.
            if any(abs(scene.start - start) < 0.01 for start in selected_starts):
                continue
            start = scene.start
            end = min(scene.end, scene.start + min(6.0, self.max_clip))
            events.append(EventRegion(
                start_seconds=start,
                end_seconds=end,
                category=self._baseline_category(scene),
                description=self._baseline_description(scene),
                characters=(),
                location="Unknown",
                shot_type="Gameplay",
                dialogue_present=scene.speech,
                confidence=max(0.25, min(0.80, scene.score)),
                repetition=1.0 if scene.score < 0.20 else 0.0,
                source_window_start=scene.start,
                source_window_end=scene.end,
            ))
        return events

    def run(self, video_file: str) -> dict:
        source = Path(video_file).expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Gameplay video not found: {source}")

        info = self.video.probe(str(source))
        duration = info["duration_seconds"]
        self._current_source = str(source)
        self._ensure_cache_meta(str(source), duration)

        source_root = self.output_root / self._safe_name(source.stem)
        source_root.mkdir(parents=True, exist_ok=True)
        incomplete_runs = sorted(
            [p for p in source_root.glob("run_*")
             if p.is_dir() and (p / ".incomplete").exists()],
            key=lambda p: p.name, reverse=True,
        )
        run_root = incomplete_runs[0] if incomplete_runs else (
            source_root / datetime.now().strftime("run_%Y%m%d_%H%M%S")
        )
        run_root.mkdir(parents=True, exist_ok=True)
        (run_root / ".incomplete").touch(exist_ok=True)
        metadata_root = run_root / "metadata"
        metadata_root.mkdir(parents=True, exist_ok=True)

        print("PressStartAI Gameplay Segmentation")
        print("=" * 64)
        print(f"Video: {source.name}")
        print(f"Duration: {duration / 60:.1f} min | {info['width']}x{info['height']} | {info['fps']:.2f} FPS")
        print(f"AI budget: {'adaptive' if self.max_ai_windows == 0 else self.max_ai_windows} | CPU workers: {self.cpu_workers}")
        print("=" * 64)

        self._set_stage(str(source), "shared_analysis", "running")
        print("[1/6] Building shared PressStartAI analysis...")
        analysis = FastGameplayPreAnalyzer(
            cache_dir=self.cache_dir(str(source)),
            cpu_workers=self.cpu_workers,
            shared_analysis_path=self.shared_analysis_path,
        ).run(str(source), duration)
        self._timeline_observations = [
            {"timestamp": s.start, "motion_score": s.motion, "visual_change_score": 0.0}
            for s in analysis.scenes
        ]
        self._set_stage(
            str(source), "shared_analysis", "complete",
            scenes=len(analysis.scenes), transcript_segments=len(analysis.transcript),
            speech_segments=len(analysis.speech),
        )

        # The shared artifact is the sole source for transcript/speech in all
        # downstream stages. No candidate-level ASR is permitted.
        self._set_stage(str(source), "semantic_selection", "running")
        budget = self._ai_budget(duration)
        windows = self._select_semantic_windows(analysis.scenes, duration, budget)
        self._write_json(self._cache_file(str(source), "analysis_windows.json"), windows)
        self._write_json(run_root / "analysis_windows.json", windows)
        print(f"[2/6] Semantic selection: {len(analysis.scenes)} scenes -> {len(windows)} AI windows")
        self._set_stage(str(source), "semantic_selection", "complete", windows=len(windows))

        # Extract one sparse timeline from the already-created analysis proxy.
        # This is one FFmpeg pass and prevents per-window MP4 seeking.
        frame_map = self.video.extract_sparse_timeline(
            analysis.proxy_path, duration, 4.0,
            str(self.cache_dir(str(source)) / "vision_sparse"),
        )
        self._set_stage(str(source), "vision_sparse_frames", "complete", frames=len(frame_map))

        vision_cache = self._cache_file(str(source), "vision_results.json")
        vision_results = self._read_json(vision_cache)
        if not isinstance(vision_results, dict):
            vision_results = {}

        pending = []
        for window in windows:
            key = self._vision_cache_key(
                float(window["start"]), float(window["end"]),
                self.reasoner.model,
            )
            if isinstance(vision_results.get(key), dict) and not vision_results[key].get("error"):
                continue
            pending.append(window)

        self._set_stage(str(source), "semantic_ai", "running", total=len(windows), completed=len(windows)-len(pending))
        print(f"[3/6] Semantic AI: {len(pending)} pending / {len(windows)} total")

        import time as _time
        ai_start = _time.perf_counter()
        for completed, window in enumerate(pending, 1):
            start_t = float(window["start"])
            end_t = float(window["end"])
            key = self._vision_cache_key(start_t, end_t, self.reasoner.model)
            frame_files = [
                x for x in (
                    self._nearest_frame(frame_map, start_t + (end_t-start_t)*0.30),
                    self._nearest_frame(frame_map, start_t + (end_t-start_t)*0.70),
                ) if x
            ]
            try:
                events_raw = self.reasoner.analyze_window(frame_files, start_t, end_t)
                vision_results[key] = {
                    "index": window["index"], "start": start_t, "end": end_t,
                    "events": events_raw, "status": "complete",
                }
            except Exception as exc:
                # A failed semantic window never blocks the whole run. The
                # deterministic baseline event remains the fallback.
                vision_results[key] = {
                    "index": window["index"], "start": start_t, "end": end_t,
                    "events": [], "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}",
                }
                with (run_root / "vision_errors.log").open("a", encoding="utf-8") as handle:
                    handle.write(f"{start_t:.3f}-{end_t:.3f}: {type(exc).__name__}: {exc}\n")
            self._write_json(vision_cache, vision_results)
            elapsed = max(0.001, _time.perf_counter() - ai_start)
            rate = completed / elapsed
            remaining = max(0, len(pending) - completed)
            eta = remaining / rate if rate else 0
            print(f"      AI {completed}/{len(pending)} | {rate:.2f}/min | ETA {eta/60:.1f} min")
            self._set_stage(
                str(source), "semantic_ai", "running",
                total=len(windows), completed=(len(windows)-len(pending)+completed),
                failed=sum(1 for v in vision_results.values() if isinstance(v, dict) and v.get("status") == "failed"),
            )
        self._set_stage(str(source), "semantic_ai", "complete", total=len(windows))

        # Build baseline coverage first; AI replaces only selected regions.
        selected_starts = {round(float(w.get("scene_start", w["start"])), 3) for w in windows}
        events = self._baseline_events(analysis.scenes, selected_starts)

        for window in windows:
            key = self._vision_cache_key(float(window["start"]), float(window["end"]), self.reasoner.model)
            result = vision_results.get(key, {})
            for raw in result.get("events", []) if isinstance(result, dict) else []:
                event = self._normalize_event(
                    raw, float(window["start"]), float(window["end"]), analysis.speech
                )
                if event:
                    events.append(event)

        self._set_stage(str(source), "event_build", "running")
        events = self._reconcile_entities(self._merge_events(events))
        events = self._remove_junk_events(events)
        events = self._sample_repetition(events)
        self._write_json(self._cache_file(str(source), "events.json"), [asdict(e) for e in events])
        self._set_stage(str(source), "event_build", "complete", events=len(events))
        print(f"[4/6] Event timeline: {len(events)} usable events")

        self._set_stage(str(source), "candidate_generation", "running")
        candidates = remove_redundant(self._generate_candidates(events, duration))
        candidates_cache = self._cache_file(str(source), "candidates.json")
        self._write_json(candidates_cache, [asdict(c) for c in candidates])
        self._set_stage(str(source), "candidate_generation", "complete", candidates=len(candidates))
        print(f"[5/6] Candidate generation/dedup: {len(candidates)} clips")

        print(f"[6/6] Exporting {len(candidates)} clips...")
        self._set_stage(str(source), "export", "running", total=len(candidates))
        records = self._export_candidates(
            source, run_root, metadata_root, candidates, analysis.transcript,
        )
        self._write_csv(run_root / "PressStartAI_Master.csv", records)

        status = "COMPLETE" if len(records) == len(candidates) else "PARTIAL"
        self._write_json(
            run_root / "run_status.json",
            {"status": status, "candidate_count": len(candidates), "exported_count": len(records)},
        )
        self._set_stage(str(source), "export", "complete", exported=len(records), total=len(candidates))

        if status == "PARTIAL":
            raise RuntimeError(
                f"Export stage incomplete: {len(candidates)-len(records)} candidates failed. "
                "Rerun the same command to resume."
            )

        (run_root / ".incomplete").unlink(missing_ok=True)
        print(f"Complete: {len(records)} clips exported.")
        return {
            "source_video": str(source),
            "output_directory": str(run_root.resolve()),
            "duration_seconds": duration,
            "timeline_observations": len(self._timeline_observations),
            "ai_windows": len(windows),
            "event_count": len(events),
            "clip_count": len(records),
            "csv": str((run_root / "PressStartAI_Master.csv").resolve()),
            "cache_directory": str(self.cache_dir(str(source)).resolve()),
        }

    def _export_candidates(
        self,
        source: Path,
        run_root: Path,
        metadata_root: Path,
        candidates: list[ClipCandidate],
        transcript_segments: list[dict],
    ) -> list[ClipRecord]:
        exporter = TransactionalExporter(run_root)
        records: list[ClipRecord] = []
        total = len(candidates)

        for index, candidate in enumerate(candidates, start=1):
            clip_id = f"PSAI-{index:06d}"
            category = normalize_category(candidate.category)
            subcategory = (
                character_subcategory(candidate.shot_type, candidate.description)
                if category == "Character"
                else ""
            )

            folder = run_root / category / subcategory if subcategory else run_root / category
            folder.mkdir(parents=True, exist_ok=True)

            output_file = folder / self._filename(clip_id, candidate.description)
            exporter.begin(clip_id, clip_id)

            try:
                self.video.export_clip(
                    str(source),
                    candidate.start_seconds,
                    candidate.end_seconds,
                    str(output_file),
                )

                if not output_file.exists():
                    raise RuntimeError("FFmpeg did not create output file.")

                exporter.complete(
                    clip_id,
                    output_file.relative_to(run_root).as_posix(),
                )

                transcript = self._slice_transcript(
                    transcript_segments,
                    candidate.start_seconds,
                    candidate.end_seconds,
                )

                overlap_ids: list[str] = []
                for other_index, other in enumerate(candidates, start=1):
                    if other_index == index:
                        continue

                    overlap = min(candidate.end_seconds, other.end_seconds) - max(
                        candidate.start_seconds, other.start_seconds
                    )

                    if overlap > 0:
                        overlap_ids.append(f"PSAI-{other_index:06d}")

                record = ClipRecord(
                    clip_id=clip_id,
                    event_id=clip_id,
                    file_path=str(output_file.resolve()),
                    relative_file_path=output_file.relative_to(run_root).as_posix(),
                    source_video=str(source),
                    start_seconds=candidate.start_seconds,
                    end_seconds=candidate.end_seconds,
                    duration_seconds=candidate.end_seconds,
                    category=category,
                    subcategory=subcategory,
                    description=candidate.description,
                    characters=candidate.characters,
                    location=candidate.location,
                    shot_type=candidate.shot_type,
                    dialogue_present=candidate.dialogue_present,
                    transcript=transcript,
                    confidence=candidate.confidence,
                    source_event_index=candidate.source_event_index,
                    overlapped_clip_ids=tuple(overlap_ids),
                )

                records.append(record)

                self._write_json(
                    metadata_root / f"{clip_id}.json",
                    record.to_dict(),
                )

            except Exception as exc:
                exporter.failed(
                    clip_id,
                    f"{type(exc).__name__}: {exc}",
                )

                with (run_root / "export_errors.log").open(
                    "a",
                    encoding="utf-8",
                ) as handle:
                    handle.write(f"{clip_id}: {type(exc).__name__}: {exc}\n")

            if (
                index == 1
                or index == total
                or index % max(1, total // 20) == 0
            ):
                completed = len(records)
                print(f"      Export {completed}/{total} ({completed/total*100:.1f}%)")

        return records

    @staticmethod
    def _slice_transcript(segments: list[dict], start: float, end: float) -> str:
        parts = []
        for item in segments or []:
            try:
                a = float(item.get("start", 0.0))
                b = float(item.get("end", a))
                text = str(item.get("text", "")).strip()
            except (AttributeError, TypeError, ValueError):
                continue
            if text and a < end and b > start:
                parts.append(text)
        return " ".join(parts)

    @staticmethod
    def _candidate_key(candidate: ClipCandidate) -> str:
        payload = (
            round(candidate.start_seconds, 3),
            round(candidate.end_seconds, 3),
            candidate.category,
            candidate.description,
            tuple(candidate.characters),
            candidate.location,
            candidate.shot_type,
        )
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _vision_cache_key(start: float, end: float, model: str = "") -> str:
        return f"v2|{OllamaGameplayReasoner.PROMPT_VERSION}|{model}|{start:.3f}-{end:.3f}"

    def _frame_times(self, start: float, end: float) -> list[float]:
        values = []
        current = start
        while current < end:
            values.append(current)
            current += self.frame_interval
        if not values or values[-1] < end - 0.4:
            values.append(max(start, end - 0.25))
        return sorted(set(round(v, 3) for v in values))

    def _normalize_event(
        self, raw: dict, window_start: float, window_end: float,
        speech_segments: list[tuple[float, float]]
    ) -> EventRegion | None:
        try:
            start = window_start + float(raw.get("start_offset", 0))
            end = window_start + float(raw.get("end_offset", 0))
        except (TypeError, ValueError):
            return None
        start = max(window_start, start)
        end = min(window_end, end)
        if end <= start or not bool(raw.get("meaningful", True)):
            return None
        description = str(raw.get("description", "")).strip() or "Gameplay event"
        characters = tuple(str(x).strip() for x in raw.get("characters", []) if str(x).strip())
        dialogue = bool(raw.get("dialogue_present", False)) or self._speech_intersects(
            speech_segments, start, end
        )
        return EventRegion(
            start_seconds=start,
            end_seconds=end,
            category=normalize_category(str(raw.get("category", "Other"))),
            description=description,
            characters=characters,
            location=str(raw.get("location", "Unknown")).strip() or "Unknown",
            shot_type=str(raw.get("shot_type", "Gameplay")).strip() or "Gameplay",
            dialogue_present=dialogue,
            confidence=self._confidence(raw.get("confidence", 0.0)),
            repetition=1.0 if bool(raw.get("repetitive", False)) else 0.0,
            source_window_start=window_start,
            source_window_end=window_end,
        )

    @staticmethod
    def _confidence(value: object) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _speech_intersects(
        segments: list[tuple[float, float]], start: float, end: float
    ) -> bool:
        return any(a < end and b > start for a, b in segments)

    def _reconcile_entities(self, events: list[EventRegion]) -> list[EventRegion]:
        """Conservatively maintain stable character labels without inventing identity."""
        aliases = {
            "player": "Player", "main character": "Player",
            "protagonist": "Player", "hero": "Player",
        }
        result = []
        identity_map: dict[str, str] = {}
        next_id = 1
        last_location = "Unknown"
        last_location_time = -999.0

        for event in sorted(events, key=lambda e: e.start_seconds):
            chars = []
            for raw_name in event.characters:
                key = re.sub(r"\s+", " ", raw_name.strip().lower())
                if not key:
                    continue
                canonical = aliases.get(key)
                if canonical is None:
                    # Preserve an explicit model name; if it is a generic role,
                    # assign a stable internal ID for future clips.
                    generic = key in {"npc", "enemy", "guard", "soldier", "boss", "character", "person"}
                    if generic:
                        canonical = identity_map.setdefault(key, f"Character_{next_id:02d}")
                        if canonical.endswith(f"{next_id:02d}"):
                            next_id += 1
                    else:
                        canonical = identity_map.setdefault(key, raw_name.strip())
                if canonical not in chars:
                    chars.append(canonical)

            if not chars and event.category == "Character":
                generic_key = "unknown_character"
                canonical = identity_map.setdefault(generic_key, f"Character_{next_id:02d}")
                if canonical == f"Character_{next_id:02d}":
                    next_id += 1
                chars = [canonical]

            location = event.location.strip() or "Unknown"
            # Location carry-forward is conservative and short-lived; an
            # explicit Unknown never creates a new location identity.
            if (
                location == "Unknown"
                and last_location != "Unknown"
                and event.start_seconds - last_location_time <= 10.0
            ):
                location = last_location
            elif location != "Unknown":
                last_location = location
                last_location_time = event.start_seconds

            result.append(EventRegion(
                start_seconds=event.start_seconds, end_seconds=event.end_seconds,
                category=event.category, description=event.description,
                characters=tuple(chars), location=location,
                shot_type=event.shot_type, dialogue_present=event.dialogue_present,
                confidence=event.confidence, repetition=event.repetition,
                source_window_start=event.source_window_start,
                source_window_end=event.source_window_end,
            ))
        return result

    def _merge_events(self, events: list[EventRegion]) -> list[EventRegion]:
        merged: list[EventRegion] = []
        for event in sorted(events, key=lambda e: (e.start_seconds, e.end_seconds)):
            if not merged:
                merged.append(event)
                continue
            previous = merged[-1]
            compatible = (
                event.category == previous.category
                and event.location == previous.location
                and event.shot_type == previous.shot_type
                and event.start_seconds <= previous.end_seconds + 0.6
                and not event.dialogue_present
                and not previous.dialogue_present
            )
            if compatible:
                merged[-1] = EventRegion(
                    start_seconds=min(previous.start_seconds, event.start_seconds),
                    end_seconds=max(previous.end_seconds, event.end_seconds),
                    category=previous.category,
                    description=(
                        previous.description
                        if len(previous.description) >= len(event.description)
                        else event.description
                    ),
                    characters=tuple(dict.fromkeys(previous.characters + event.characters)),
                    location=previous.location if previous.location != "Unknown" else event.location,
                    shot_type=previous.shot_type,
                    dialogue_present=False,
                    confidence=max(previous.confidence, event.confidence),
                    repetition=max(previous.repetition, event.repetition),
                    source_window_start=min(previous.source_window_start, event.source_window_start),
                    source_window_end=max(previous.source_window_end, event.source_window_end),
                )
            else:
                merged.append(event)
        return merged

    @staticmethod
    def _remove_junk_events(events: list[EventRegion]) -> list[EventRegion]:
        junk = (
            "loading screen", "main menu", "pause menu", "settings menu",
            "black screen", "splash screen", "no gameplay", "loading",
        )
        result = []
        for event in events:
            text = event.description.lower()
            if any(term in text for term in junk):
                continue
            if event.end_seconds - event.start_seconds < 1.0:
                continue
            result.append(event)
        return result

    @staticmethod
    def _sample_repetition(events: list[EventRegion]) -> list[EventRegion]:
        """Keep representative repetitive events while preserving distinct events."""
        result = []
        last_by_signature: dict[str, float] = {}
        for event in events:
            if event.repetition < 0.5:
                result.append(event)
                continue
            signature = f"{event.category}|{re.sub(r'[^a-z0-9 ]', '', event.description.lower())[:50]}"
            previous = last_by_signature.get(signature)
            if previous is None or event.start_seconds - previous >= 30.0:
                result.append(event)
                last_by_signature[signature] = event.start_seconds
        return result

    def _generate_candidates(
        self, events: list[EventRegion], duration: float
    ) -> list[ClipCandidate]:
        # One primary clip per meaningful event. An optional contextual variant
        # is created only for long, high-confidence events; dedupe is therefore
        # not used as a repair mechanism for a 3x candidate explosion.
        candidates: list[ClipCandidate] = []
        for event_index, event in enumerate(events):
            event_duration = event.end_seconds - event.start_seconds
            if event_duration < self.min_clip:
                length = min(self.max_clip, max(self.min_clip, 5.0))
                start, end = self._fit_clip(event.start_seconds, event.end_seconds, length, duration)
            else:
                length = min(self.max_clip, max(self.min_clip, event_duration))
                start, end = self._fit_clip(event.start_seconds, event.end_seconds, length, duration)
            candidates.append(self._candidate(event, event_index, start, end, "primary event clip"))

            if (
                event_duration > 8.0
                and event.confidence >= 0.75
                and event.category in {"Fight", "Boss", "Cinematic", "Cutscene", "Dialogue"}
            ):
                context_length = min(self.max_clip, 8.5)
                context_start, context_end = self._fit_clip(
                    event.start_seconds, event.end_seconds, context_length, duration
                )
                if abs(context_start-start) > 0.5 or abs(context_end-end) > 0.5:
                    candidates.append(
                        self._candidate(event, event_index, context_start, context_end, "context variant")
                    )
        return candidates

    @staticmethod
    def _fit_clip(start: float, end: float, length: float, duration: float) -> tuple[float, float]:
        length = min(length, duration)
        center = (start + end) / 2.0
        new_start = max(0.0, min(center - length / 2, duration - length))
        return new_start, new_start + length

    @staticmethod
    def _candidate(
        event: EventRegion, index: int, start: float, end: float, reason: str
    ) -> ClipCandidate:
        return ClipCandidate(
            start_seconds=round(max(0.0, start), 3),
            end_seconds=round(max(start, end), 3),
            category=event.category,
            description=event.description,
            characters=event.characters,
            location=event.location,
            shot_type=event.shot_type,
            dialogue_present=event.dialogue_present,
            confidence=event.confidence,
            source_event_index=index,
            reason=reason,
        )

    @staticmethod
    def _filename(clip_id: str, description: str) -> str:
        text = re.sub(r"[^a-zA-Z0-9]+", "_", description.lower()).strip("_")
        return f"{clip_id}_{(text[:70] or 'gameplay_clip')}.mp4"

    @staticmethod
    def _write_csv(path: Path, records: list[ClipRecord]) -> None:
        fields = [
            "clip_id", "relative_file_path", "duration_seconds", "category",
            "subcategory", "description", "action_event", "characters", "location", "shot_type",
            "dialogue_present", "transcript", "start_seconds", "end_seconds",
            "confidence", "source_event_index", "overlapped_clip_ids", "source_video",
        ]
        with path.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for record in records:
                row = record.to_dict()
                row["characters"] = ", ".join(record.characters)
                row["overlapped_clip_ids"] = ", ".join(record.overlapped_clip_ids)
                writer.writerow({field: row.get(field, "") for field in fields})
