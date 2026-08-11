
from pathlib import Path

from src.services.run_session_manager import RunSessionManager


def test_same_inputs_have_same_session_key(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"x" * 1024)
    manager = RunSessionManager(tmp_path / "cache")
    first = manager.session_key(str(video), None, None, "portrait")
    second = manager.session_key(str(video), None, None, "portrait")
    assert first == second


def test_resume_registry_survives_before_output_exists(tmp_path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"video")
    manager = RunSessionManager(tmp_path / "cache")
    key = manager.session_key(str(video), None, None, "portrait")
    paths = manager.new_run(key, str(video), output_root=str(tmp_path / "outputs"))
    resumed = manager.previous_run(key)
    assert resumed is not None
    assert resumed.run_id == paths.run_id
    assert resumed.working_folder == paths.working_folder
