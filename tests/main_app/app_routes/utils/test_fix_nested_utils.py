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


def test_create_task_folder_idempotent(tmp_path):
    """create_task_folder is idempotent - calling it twice does not raise."""
    task_id = "idempotent_task"
    folder1 = create_task_folder(task_id, tmp_path)
    folder2 = create_task_folder(task_id, tmp_path)
    assert folder1 == folder2
    assert folder1.exists()


def test_create_task_folder_with_string_path(tmp_path):
    """create_task_folder accepts a string path as well as a Path object."""
    task_id = "string_path_task"
    folder = create_task_folder(task_id, str(tmp_path))
    assert folder == tmp_path / task_id
    assert folder.exists()


def test_create_task_folder_creates_nested_dirs(tmp_path):
    """create_task_folder creates nested directories if necessary."""
    base = tmp_path / "nested" / "base"
    folder = create_task_folder("task_id", base)
    assert folder.exists()
    assert folder == base / "task_id"


def test_log_to_task_appends_multiple_messages(tmp_path):
    """log_to_task appends each message on a new line."""
    log_to_task(tmp_path, "first message")
    log_to_task(tmp_path, "second message")
    content = (tmp_path / "task_log.txt").read_text()
    assert "first message" in content
    assert "second message" in content
    assert content.count("\n") == 2


def test_log_to_task_includes_timestamp(tmp_path):
    """log_to_task includes an ISO timestamp prefix."""
    log_to_task(tmp_path, "timestamped")
    content = (tmp_path / "task_log.txt").read_text()
    # ISO timestamp starts with a digit for the year and contains 'T'
    assert content.startswith("[2")
    assert "T" in content


def test_save_metadata_with_non_string_values(tmp_path):
    """save_metadata serialises non-string values using default=str."""
    from datetime import datetime

    metadata = {"ts": datetime(2024, 1, 15, 12, 0, 0), "count": 42}
    save_metadata(tmp_path, metadata)
    metadata_file = tmp_path / "metadata.json"
    assert metadata_file.exists()
    content = metadata_file.read_text()
    assert "2024-01-15" in content
    assert "42" in content


def test_save_metadata_overwrites_existing(tmp_path):
    """save_metadata overwrites a pre-existing metadata file."""
    save_metadata(tmp_path, {"version": 1})
    save_metadata(tmp_path, {"version": 2})
    import json

    with open(tmp_path / "metadata.json") as f:
        data = json.load(f)
    assert data["version"] == 2