import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def create_task_folder(task_id: str, path: Path | str) -> Path:
    """Create folder structure for a fix_nested task."""
    task_dir = Path(path) / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def save_metadata(task_dir: Path, metadata: dict) -> None:
    """Save task metadata to JSON file."""
    metadata_file = task_dir / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)


def log_to_task(task_dir: Path, message: str) -> None:
    """Append log message to task log file."""
    log_file = task_dir / "task_log.txt"
    timestamp = datetime.now().isoformat()
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


__all__ = [
    "create_task_folder",
    "save_metadata",
    "log_to_task",
]
