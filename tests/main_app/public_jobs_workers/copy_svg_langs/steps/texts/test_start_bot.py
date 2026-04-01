from unittest.mock import patch

import pytest

from src.main_app.public_jobs_workers.copy_svg_langs.steps.texts.start_bot import extract_text_step


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.texts.start_bot.get_wikitext")
def test_text_task_success(mock_get):
    mock_get.return_value = "content"
    stages = {}

    text, final_stages = extract_text_step(stages, "Title")

    assert text == "content"
    assert final_stages["status"] == "Completed"


@patch("src.main_app.public_jobs_workers.copy_svg_langs.steps.texts.start_bot.get_wikitext")
def test_text_task_fail(mock_get):
    mock_get.return_value = None
    stages = {}

    text, final_stages = extract_text_step(stages, "Title")

    assert text is None
    assert final_stages["status"] == "Failed"
