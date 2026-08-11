
from __future__ import annotations

import math
import os
from dataclasses import dataclass

import psutil

from src.core.config import Config


@dataclass(slots=True, frozen=True)
class ResourceSnapshot:
    cpu_percent: float
    ram_percent: float
    available_ram_bytes: int
    logical_cpus: int


class ResourceManager:
    """Choose safe dynamic worker counts from current CPU/RAM pressure."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config if config is not None else Config()
        perf = self.config.data.get("performance", {})
        self.enabled = bool(perf.get("enabled", True))
        self.target_cpu_percent = float(perf.get("target_cpu_percent", 85))
        self.target_ram_percent = float(perf.get("target_ram_percent", 70))
        self.high_ram_percent = float(perf.get("high_ram_percent", 82))
        self.cpu_reserve_cores = int(perf.get("cpu_reserve_cores", 1))
        self.maximum_workers = int(perf.get("maximum_workers", 8))

    def snapshot(self) -> ResourceSnapshot:
        memory = psutil.virtual_memory()
        return ResourceSnapshot(
            cpu_percent=float(psutil.cpu_percent(interval=0.15)),
            ram_percent=float(memory.percent),
            available_ram_bytes=int(memory.available),
            logical_cpus=max(1, int(os.cpu_count() or 1)),
        )

    def workers(
        self,
        *,
        task_name: str,
        item_count: int,
        memory_per_worker_mb: int,
        maximum_workers: int | None = None,
    ) -> int:
        if item_count <= 1 or not self.enabled:
            return 1

        snapshot = self.snapshot()
        usable_cpus = max(1, snapshot.logical_cpus - self.cpu_reserve_cores)

        cpu_budget = max(
            1,
            int(math.ceil(usable_cpus * self.target_cpu_percent / 100.0)),
        )

        total_ram = psutil.virtual_memory().total
        target_ram_bytes = int(total_ram * self.target_ram_percent / 100.0)
        currently_used = total_ram - snapshot.available_ram_bytes
        ram_headroom = max(0, target_ram_bytes - currently_used)
        per_worker = max(1, memory_per_worker_mb) * 1024 * 1024
        ram_budget = max(1, int(ram_headroom // per_worker))

        if snapshot.ram_percent >= self.high_ram_percent:
            ram_budget = 1

        limit = maximum_workers if maximum_workers is not None else self.maximum_workers
        chosen = max(
            1,
            min(
                item_count,
                cpu_budget,
                ram_budget,
                self.maximum_workers,
                max(1, limit),
            ),
        )

        print(
            f"[PERF] {task_name}: workers={chosen} "
            f"| CPU {snapshot.cpu_percent:.0f}% "
            f"| RAM {snapshot.ram_percent:.0f}% "
            f"| target CPU {self.target_cpu_percent:.0f}% "
            f"| target RAM {self.target_ram_percent:.0f}%"
        )
        return chosen
