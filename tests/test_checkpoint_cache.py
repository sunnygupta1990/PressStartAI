
from pathlib import Path
import json

from src.services.checkpoint_cache import CheckpointCache
from src.services.pipeline_stage_runner import PipelineStageRunner


def test_cache_round_trip_and_checksum_rejection(tmp_path, monkeypatch):
    monkeypatch.chdir(Path(__file__).parents[1])
    cache = CheckpointCache(tmp_path / "cache", "session", enabled=True)
    cache.save("Loading video", {"value": 42})
    loaded = cache.load("Loading video")
    assert loaded.hit
    assert loaded.value == {"value": 42}

    data_path, _ = cache._paths("Loading video")
    data_path.write_bytes(data_path.read_bytes() + b"corrupt")
    assert not cache.load("Loading video").hit


def test_bypass_read_still_writes_new_checkpoint(tmp_path, monkeypatch):
    monkeypatch.chdir(Path(__file__).parents[1])
    cache = CheckpointCache(tmp_path / "cache", "session", enabled=False)
    cache.save("Loading video", "new")
    assert cache.has_any_cache()
    assert not cache.load("Loading video").hit

    reuse = CheckpointCache(tmp_path / "cache", "session", enabled=True)
    assert reuse.load("Loading video").value == "new"


def test_stage_runner_reuses_cache(tmp_path, monkeypatch):
    monkeypatch.chdir(Path(__file__).parents[1])
    cache = CheckpointCache(tmp_path / "cache", "session", enabled=True)
    calls = {"count": 0}

    def action():
        calls["count"] += 1
        return "result"

    first = PipelineStageRunner(cache)
    assert first.run("Loading video", action) == "result"
    assert calls["count"] == 1

    second = PipelineStageRunner(cache)
    assert second.run("Loading video", action) == "result"
    assert calls["count"] == 1


def test_upstream_rebuild_blocks_downstream_stale_cache(tmp_path, monkeypatch):
    monkeypatch.chdir(Path(__file__).parents[1])
    cache = CheckpointCache(tmp_path / "cache", "session", enabled=True)
    cache.save("Detecting scenes", "old-scenes")

    runner = PipelineStageRunner(cache)
    assert runner.run("Loading video", lambda: "fresh-video") == "fresh-video"
    assert runner.upstream_dirty
    assert runner.run("Detecting scenes", lambda: "fresh-scenes") == "fresh-scenes"
