from unittest.mock import MagicMock, patch

import pytest

from src.main_app.tasks.texts.text_bot import get_wikitext


@patch("src.main_app.tasks.texts.text_bot.requests.Session")
def test_get_wikitext_success(mock_session_cls):
    mock_session = mock_session_cls.return_value
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "query": {"pages": [{"revisions": [{"slots": {"main": {"content": "expected wikitext"}}}]}]}
    }
    mock_session.get.return_value = mock_response

    res = get_wikitext("Title")
    assert res == "expected wikitext"


@patch("src.main_app.tasks.texts.text_bot.requests.Session")
def test_get_wikitext_not_found(mock_session_cls):
    mock_session = mock_session_cls.return_value
    mock_response = MagicMock()
    mock_response.json.return_value = {"query": {"pages": [{"missing": ""}]}}
    mock_session.get.return_value = mock_response

    res = get_wikitext("Title")
    assert res is None


@patch("src.main_app.tasks.texts.text_bot.requests.Session")
def test_get_wikitext_error(mock_session_cls):
    mock_session = mock_session_cls.return_value
    mock_session.get.side_effect = Exception("error")

    res = get_wikitext("Title")
    assert res is None
