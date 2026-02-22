import pytest
from unittest.mock import patch
from src.main_app.tasks.texts.start_bot import text_task

@patch("src.app.tasks.texts.start_bot.get_wikitext")
def test_text_task_success(mock_get):
    mock_get.return_value = "content"
    stages = {}

    text, final_stages = text_task(stages, "Title")

    assert text == "content"
    assert final_stages["status"] == "Completed"

@patch("src.app.tasks.texts.start_bot.get_wikitext")
def test_text_task_fail(mock_get):
    mock_get.return_value = None
    stages = {}

    text, final_stages = text_task(stages, "Title")

    assert text is None
    assert final_stages["status"] == "Failed"
