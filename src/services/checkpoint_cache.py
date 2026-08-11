
from __future__ import annotations

import hashlib
import json
import os
import pickle
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.config import Config


@dataclass(slots=True, frozen=True)
class CacheLoadResult:
    hit: bool
    value: Any = None


class CheckpointCache:
    """Persistent, checksum-validated stage cache for one input session."""

    SCHEMA_VERSION = 1

    _STAGE_FILES = {
        "Synchronizing recordings": ["src/services/recording_synchronizer.py"],
        "Loading video": ["src/services/video_loader.py"],
        "Creating fast analysis proxy": ["src/services/video_analysis_proxy.py"],
        "Extracting audio": ["src/services/audio_extractor.py"],
        "Detecting speech": ["src/services/voice_activity_detector.py"],
        "Creating speech chunks": ["src/services/speech_chunk_extractor.py"],
        "Transcribing commentary": ["src/services/asr/transcription_pipeline.py"],
        "Detecting scenes": ["src/services/scene_detector.py"],
        "Mapping commentary to scenes": ["src/services/scene_transcript_mapper.py"],
        "Analyzing motion": ["src/services/motion_analyzer.py"],
        "Analyzing audio intensity": ["src/services/audio_analyzer.py"],
        "Extracting highlight features": ["src/services/highlight_feature_extractor.py"],
        "Scoring highlight scenes": ["src/services/highlight_scorer.py"],
        "Selecting highlight candidates": ["src/services/highlight_selector.py"],
        "Resolving highlight overlaps": ["src/services/highlight_overlap_resolver.py"],
        "Generating lightweight analysis clips": ["src/services/highlight_clip_generator.py"],
        "Running commentary AI reasoning": ["src/services/highlight_reasoner.py"],
        "Combining commentary analysis": ["src/services/highlight_analysis_combiner.py"],
        "Warming up visual AI model": ["src/services/visual_highlight_reasoner.py"],
        "Running visual AI reasoning": ["src/services/visual_highlight_reasoner.py"],
        "Fusing multimodal AI decisions": ["src/services/highlight_fusion_reasoner.py"],
        "Selecting final approved highlights": ["src/services/final_highlight_selector.py"],
        "Extracting approved source clips": ["src/services/highlight_clip_generator.py"],
        "Linking approved decisions to source clips": ["src/services/final_highlight_combiner.py"],
    }

    _CONFIG_SECTIONS = {
        "Synchronizing recordings": [],
        "Loading video": [],
        "Creating fast analysis proxy": [],
        "Extracting audio": [],
        "Detecting speech": ["shorts_features"],
        "Creating speech chunks": ["shorts_features"],
        "Transcribing commentary": ["shorts_features", "ai"],
        "Detecting scenes": [],
        "Mapping commentary to scenes": ["shorts_features"],
        "Analyzing motion": [],
        "Analyzing audio intensity": [],
        "Extracting highlight features": [],
        "Scoring highlight scenes": [],
        "Selecting highlight candidates": ["shorts"],
        "Resolving highlight overlaps": ["shorts"],
        "Generating lightweight analysis clips": [],
        "Running commentary AI reasoning": ["shorts_features", "ai"],
        "Combining commentary analysis": ["shorts_features"],
        "Warming up visual AI model": ["shorts_features", "ai"],
        "Running visual AI reasoning": ["shorts_features", "ai"],
        "Fusing multimodal AI decisions": ["shorts_features", "ai"],
        "Selecting final approved highlights": [],
        "Extracting approved source clips": [],
        "Linking approved decisions to source clips": [],
    }

    def __init__(
        self,
        cache_root: str | Path,
        session_key: str,
        enabled: bool = True,
    ) -> None:
        self.cache_root = Path(cache_root)
        self.session_key = session_key
        self.enabled = enabled
        self.session_dir = self.cache_root / "sessions" / session_key
        self.stage_dir = self.session_dir / "stages"
        self.work_dir = self.session_dir / "work"
        self.stage_dir.mkdir(parents=True, exist_ok=True)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self._config = Config().data
        self._ensure_budget_manifest()

    @staticmethod
    def _canonical(stage: str) -> str:
        prefixes = (
            "Extracting representative frames for rank ",
            "Running visual AI reasoning for rank ",
            "Fusing multimodal AI decisions for rank ",
        )
        for prefix in prefixes:
            if stage.startswith(prefix):
                return prefix.rstrip()
        return stage

    @classmethod
    def _files_for_stage(cls, stage: str) -> list[str]:
        canonical = cls._canonical(stage)
        if canonical == "Extracting representative frames for rank":
            return ["src/services/highlight_frame_extractor.py"]
        if canonical == "Running visual AI reasoning for rank":
            return ["src/services/visual_highlight_reasoner.py"]
        if canonical == "Fusing multimodal AI decisions for rank":
            return ["src/services/highlight_fusion_reasoner.py"]
        if stage.startswith("Rendered Short rank="):
            return [
                "src/services/short_package_builder.py",
                "src/services/short_renderer.py",
                "src/services/facecam_short_renderer.py",
                "src/services/caption_renderer.py",
            ]
        return cls._STAGE_FILES.get(stage, [])

    @classmethod
    def _sections_for_stage(cls, stage: str) -> list[str]:
        canonical = cls._canonical(stage)
        if canonical == "Extracting representative frames for rank":
            return ["shorts_features"]
        if canonical == "Running visual AI reasoning for rank":
            return ["shorts_features", "ai"]
        if canonical == "Fusing multimodal AI decisions for rank":
            return ["shorts_features", "ai"]
        if stage.startswith("Rendered Short rank="):
            return ["processing", "video", "layout", "shorts_features", "ai"]
        return cls._CONFIG_SECTIONS.get(stage, [])

    def _stage_fingerprint(self, stage: str) -> str:
        digest = hashlib.sha256()
        digest.update(f"schema:{self.SCHEMA_VERSION}|stage:{stage}".encode())
        for filename in self._files_for_stage(stage):
            path = Path(filename)
            digest.update(filename.encode())
            if path.is_file():
                digest.update(path.read_bytes())
        for section in self._sections_for_stage(stage):
            digest.update(section.encode())
            digest.update(
                json.dumps(
                    self._config.get(section, {}),
                    sort_keys=True,
                    default=str,
                ).encode()
            )
        return digest.hexdigest()

    def _paths(self, stage: str) -> tuple[Path, Path]:
        key = hashlib.sha256(stage.encode()).hexdigest()[:24]
        return self.stage_dir / f"{key}.pkl", self.stage_dir / f"{key}.json"

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _referenced_files(value: Any) -> set[Path]:
        found: set[Path] = set()
        seen: set[int] = set()

        def walk(item: Any) -> None:
            obj_id = id(item)
            if obj_id in seen:
                return
            seen.add(obj_id)
            if isinstance(item, Path):
                if item.exists():
                    found.add(item.resolve())
                return
            if isinstance(item, str):
                p = Path(item)
                if p.exists():
                    found.add(p.resolve())
                return
            if isinstance(item, dict):
                for key, val in item.items():
                    walk(key)
                    walk(val)
                return
            if isinstance(item, (list, tuple, set, frozenset)):
                for child in item:
                    walk(child)
                return
            slots = getattr(type(item), "__slots__", ())
            for name in slots if isinstance(slots, tuple) else (slots,):
                if name and hasattr(item, name):
                    walk(getattr(item, name))
            data = getattr(item, "__dict__", None)
            if isinstance(data, dict):
                walk(data)

        walk(value)
        return found

    def load(self, stage: str) -> CacheLoadResult:
        if not self.enabled:
            return CacheLoadResult(False)

        data_path, manifest_path = self._paths(stage)
        if not data_path.is_file() or not manifest_path.is_file():
            return CacheLoadResult(False)

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("schema") != self.SCHEMA_VERSION:
                return CacheLoadResult(False)
            if manifest.get("stage_fingerprint") != self._stage_fingerprint(stage):
                return CacheLoadResult(False)
            if manifest.get("payload_sha256") != self._sha256(data_path):
                return CacheLoadResult(False)

            for raw in manifest.get("required_files", []):
                if not Path(raw).exists():
                    return CacheLoadResult(False)

            with data_path.open("rb") as handle:
                return CacheLoadResult(True, pickle.load(handle))
        except Exception:
            return CacheLoadResult(False)

    def save(self, stage: str, value: Any) -> None:
        self._ensure_disk_safety()
        data_path, manifest_path = self._paths(stage)
        data_path.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_name = tempfile.mkstemp(
            prefix=data_path.name + ".",
            suffix=".tmp",
            dir=str(data_path.parent),
        )
        os.close(fd)
        temp_data = Path(temp_name)

        try:
            with temp_data.open("wb") as handle:
                pickle.dump(value, handle, protocol=pickle.HIGHEST_PROTOCOL)
                handle.flush()
                os.fsync(handle.fileno())

            payload_hash = self._sha256(temp_data)
            required_files = sorted(
                str(path)
                for path in self._referenced_files(value)
                if path.is_file()
            )
            manifest = {
                "schema": self.SCHEMA_VERSION,
                "stage": stage,
                "stage_fingerprint": self._stage_fingerprint(stage),
                "payload_sha256": payload_hash,
                "required_files": required_files,
            }

            temp_manifest = manifest_path.with_suffix(".json.tmp")
            temp_manifest.write_text(
                json.dumps(manifest, indent=2, sort_keys=True),
                encoding="utf-8",
            )

            os.replace(temp_data, data_path)
            os.replace(temp_manifest, manifest_path)
        finally:
            temp_data.unlink(missing_ok=True)

    def has_any_cache(self) -> bool:
        return any(self.stage_dir.glob("*.json"))


    def _ensure_budget_manifest(self) -> None:
        self.cache_root.mkdir(parents=True, exist_ok=True)
        path = self.cache_root / "cache_budget.json"
        if path.is_file():
            return
        usage = shutil.disk_usage(self.cache_root)
        fraction = float(
            self._config.get("cache", {}).get(
                "maximum_free_space_fraction",
                0.25,
            )
        )
        current_size = self.cache_size_bytes(self.cache_root)
        payload = {
            "schema": 1,
            "initial_free_bytes": usage.free,
            "maximum_cache_bytes": int(
                current_size + usage.free * fraction
            ),
        }
        temp = path.with_suffix(".json.tmp")
        temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(temp, path)

    def _ensure_disk_safety(self) -> None:
        """Protect the SSD from cache growth beyond configured limits."""
        self.cache_root.mkdir(parents=True, exist_ok=True)
        usage = shutil.disk_usage(self.cache_root)
        reserve_fraction = float(
            self._config.get("cache", {}).get(
                "minimum_free_space_reserve_fraction",
                0.15,
            )
        )
        reserve_bytes = int(usage.total * reserve_fraction)
        if usage.free <= reserve_bytes:
            raise RuntimeError(
                "Cache safety reserve reached. Clear cache/checkpoints "
                "from the main menu or free SSD space before continuing."
            )

        budget_path = self.cache_root / "cache_budget.json"
        if budget_path.is_file():
            try:
                budget = json.loads(
                    budget_path.read_text(encoding="utf-8")
                )
                maximum = int(budget["maximum_cache_bytes"])
                current = self.cache_size_bytes(self.cache_root)
                if current > maximum:
                    raise RuntimeError(
                        "Configured cache budget has been reached. "
                        "Clear cache/checkpoints from the main menu "
                        "or choose a different cache drive."
                    )
            except (KeyError, ValueError, json.JSONDecodeError):
                pass

    def check_disk_safety(self) -> None:
        """Public pre/post-stage disk-budget check."""
        self._ensure_disk_safety()

    @classmethod
    def cache_size_bytes(cls, cache_root: str | Path) -> int:
        root = Path(cache_root)
        if not root.exists():
            return 0
        total = 0
        for path in root.rglob("*"):
            try:
                if path.is_file():
                    total += path.stat().st_size
            except OSError:
                continue
        return total

    @classmethod
    def clear_all(cls, cache_root: str | Path) -> None:
        shutil.rmtree(Path(cache_root), ignore_errors=True)
