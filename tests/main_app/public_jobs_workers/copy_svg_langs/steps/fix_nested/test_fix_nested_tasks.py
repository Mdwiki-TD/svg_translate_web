from pathlib import Path
from unittest.mock import patch

import pytest

from src.main_app.public_jobs_workers.copy_svg_langs.steps.fix_nested import fix_nested_step


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.fix_nested.match_nested_tags")
@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.fix_nested.fix_nested_file")
def test_fix_nested_task_success(mock_fix, mock_match):
    # Setup mocks
    # First call to match returns 1 tag, second call returns [] (fixed)
    mock_match.side_effect = [["tag1"], []]
    mock_fix.return_value = True

    files = ["file1.svg"]

    result = fix_nested_step(files)

    assert result["success"] is True
    assert result["data"]["status"]["fixed"] == 1
    assert result["data"]["status"]["len_nested_files"] == 1
    assert result["summary"]["total"] == 1


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.fix_nested.match_nested_tags")
def test_fix_nested_task_no_nested(mock_match):
    mock_match.return_value = []

    files = ["file1.svg"]

    result = fix_nested_step(files)

    assert result["success"] is True
    assert result["data"]["status"]["len_nested_files"] == 0
    assert result["data"]["status"]["fixed"] == 0
