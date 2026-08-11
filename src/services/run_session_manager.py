
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from src.models.pipeline_run_paths import PipelineRunPaths
from src.services.pipeline_run_path_builder import PipelineRunPathBuilder


class RunSessionManager:
    """Resolve reusable cache identity and resumable run paths."""

    SCHEMA_VERSION = 1

    def __init__(self, cache_root: str | Path) -> None:
        self.cache_root = Path(cache_root)
        self.registry_dir = self.cache_root / "run_registry"
        self.registry_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sampled_file_identity(raw_path: str | None) -> dict | None:
        if not raw_path:
            return None
        path = Path(raw_path).resolve()
        stat = path.stat()
        digest = hashlib.sha256()
        digest.update(str(path).lower().encode())
        digest.update(str(stat.st_size).encode())
        digest.update(str(stat.st_mtime_ns).encode())
        with path.open("rb") as handle:
            head = handle.read(1024 * 1024)
            digest.update(head)
            if stat.st_size > 1024 * 1024:
                handle.seek(max(0, stat.st_size - 1024 * 1024))
                digest.update(handle.read(1024 * 1024))
        return {
            "path": str(path),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sampled_sha256": digest.hexdigest(),
        }

    def session_key(
        self,
        normal_recording: str,
        gameplay_recording: str | None,
        facecam_recording: str | None,
        layout_type: str,
    ) -> str:
        payload = {
            "schema": self.SCHEMA_VERSION,
            "layout_type": layout_type,
            "normal": self._sampled_file_identity(normal_recording),
            "gameplay": self._sampled_file_identity(gameplay_recording),
            "facecam": self._sampled_file_identity(facecam_recording),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()[:32]

    def _registry_path(self, session_key: str) -> Path:
        return self.registry_dir / f"{session_key}.json"

    def previous_run(self, session_key: str) -> PipelineRunPaths | None:
        path = self._registry_path(session_key)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return PipelineRunPaths(
                run_id=data["run_id"],
                working_folder=data["working_folder"],
                output_folder=data["output_folder"],
            )
        except Exception:
            return None

    def new_run(
        self,
        session_key: str,
        video_file: str,
        output_root: str = "output/runs",
    ) -> PipelineRunPaths:
        built = PipelineRunPathBuilder().build(
            video_file=video_file,
            working_root=str(self.cache_root / "sessions" / session_key),
            output_root=output_root,
        )
        paths = PipelineRunPaths(
            run_id=built.run_id,
            working_folder=built.working_folder,
            output_folder=built.output_folder,
        )
        self._save(session_key, paths)
        return paths

    def _save(self, session_key: str, paths: PipelineRunPaths) -> None:
        target = self._registry_path(session_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": self.SCHEMA_VERSION,
            "run_id": paths.run_id,
            "working_folder": paths.working_folder,
            "output_folder": paths.output_folder,
        }
        temp = target.with_suffix(".json.tmp")
        temp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(temp, target)
