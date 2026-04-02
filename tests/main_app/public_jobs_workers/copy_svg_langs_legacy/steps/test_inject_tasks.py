from pathlib import Path
from unittest.mock import patch

import pytest

from src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.inject import inject_step


@patch("src.main_app.public_jobs_workers.copy_svg_langs_legacy.steps.inject.start_injects")
def test_inject_task_success(mock_start, tmp_path):
    mock_start.return_value = {"success": 2, "failed": 0, "no_changes": 1, "nested_files": 0}
    files = ["f1.svg", "f2.svg"]
    translations = {}

    res = inject_step(files, translations, output_dir=tmp_path)

    assert res["success"] is True
    assert res["summary"]["success"] == 2
    assert (tmp_path / "translated").exists()


def test_inject_task_no_dir():
    # inject_step does not handle None output_dir, so it raises TypeError
    with pytest.raises(TypeError):
        inject_step([], {}, output_dir=None)
