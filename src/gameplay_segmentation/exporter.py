from __future__ import annotations

import json
from pathlib import Path
from threading import Lock


class TransactionalExporter:
    """
    Thread-safe transactional export journal.

    Every clip is written atomically:
        PENDING -> EXPORTING -> DONE / FAILED
    """

    def __init__(self, run_root: Path):
        self.run_root = Path(run_root)
        self.manifest = self.run_root / "export_manifest.json"
        self._lock = Lock()

        if not self.manifest.exists():
            self._write({})

    def _read(self):
        if not self.manifest.exists():
            return {}
        try:
            return json.loads(self.manifest.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write(self, data):
        temp = self.manifest.parent / (self.manifest.name + ".tmp")

        with temp.open("w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False,
            )

        import os
        os.replace(temp, self.manifest)

    def begin(self, clip_id, event_id):
        with self._lock:
            data = self._read()
            data[clip_id] = {
                "event_id": event_id,
                "status": "EXPORTING",
            }
            self._write(data)

    def complete(self, clip_id, relative_path):
        with self._lock:
            data = self._read()
            entry = data.setdefault(clip_id, {})
            entry["status"] = "DONE"
            entry["relative_file_path"] = relative_path
            self._write(data)

    def failed(self, clip_id, reason):
        with self._lock:
            data = self._read()
            entry = data.setdefault(clip_id, {})
            entry["status"] = "FAILED"
            entry["reason"] = reason
            self._write(data)

    def completed(self):
        data = self._read()
        return sum(
            1 for x in data.values()
            if isinstance(x, dict) and x.get("status") == "DONE"
        )