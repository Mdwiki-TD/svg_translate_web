import json

from src.main_app.app_routes.utils.fix_nested_utils import (
    create_task_folder,
    log_to_task,
    save_metadata,
)


def test_create_task_folder(tmp_path):
    task_id = "t1"
    folder = create_task_folder(task_id, tmp_path)
    assert folder == tmp_path / task_id
    assert folder.exists()


def test_save_metadata(tmp_path):
    metadata = {"key": "value"}
    save_metadata(tmp_path, metadata)
    metadata_file = tmp_path / "metadata.json"
    assert metadata_file.exists()
    with open(metadata_file, "r") as f:
        assert json.load(f) == metadata


def test_log_to_task(tmp_path):
    log_to_task(tmp_path, "test message")
    log_file = tmp_path / "task_log.txt"
    assert log_file.exists()
    assert "test message" in log_file.read_text()
