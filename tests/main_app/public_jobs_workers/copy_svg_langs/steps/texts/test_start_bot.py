from unittest.mock import patch

import pytest

from src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_text import extract_text_step


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_text.get_wikitext")
def test_text_task_success(mock_get):
    mock_get.return_value = "content"
    stages = {}

    result = extract_text_step("Title")

    assert result["success"] is True
    assert result["text"] == "content"


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_text.get_wikitext")
def test_text_task_fail(mock_get):
    mock_get.return_value = None
    stages = {}

    result = extract_text_step("Title")

    assert result["success"] is False
    assert result["text"] == ""
