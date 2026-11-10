"""Tests for FilesService.get_file_languages."""

from __future__ import annotations

from unittest.mock import MagicMock

import requests
from src.main_app.api_services.clients.http_client import HttpClient
from src.main_app.api_services.files_service import FilesService


def make_service(json_data=None, side_effect=None):
    """Build a FilesService whose HttpClient session is mocked.

    HttpClient._send calls ``session.request(...)``, so that is what we mock.
    """
    mock_session = MagicMock()
    if side_effect is not None:
        mock_session.request.side_effect = side_effect
    else:
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = json_data
        response.raise_for_status = MagicMock()
        mock_session.request.return_value = response

    http_client = HttpClient(use_session=True, session=mock_session)
    return FilesService(http_client=http_client), mock_session


def page_with_metadata(metadata):
    return {"query": {"pages": [{"title": "File:Test.svg", "imageinfo": [{"metadata": metadata}]}]}}


class TestGetFileLanguages:
    def test_empty_filename(self):
        service, _ = make_service({})
        result = service.get_file_languages("")
        assert result.error == "Empty fileName"
        assert result.langs is None

    def test_none_filename(self):
        service, _ = make_service({})
        result = service.get_file_languages(None)
        assert result.error == "Empty fileName"

    def test_file_colon_prefix_stripped(self):
        service, session = make_service(
            page_with_metadata([{"name": "translations", "value": [{"name": "fr"}, {"name": "de"}]}])
        )
        service.get_file_languages("File:Test.svg")
        params = session.request.call_args.kwargs["params"]
        assert params["titles"] == "File:Test.svg"

    def test_api_error(self):
        service, _ = make_service(side_effect=requests.ConnectionError("Connection failed"))
        result = service.get_file_languages("Test.svg")
        assert "API error" in result.error
        assert result.langs is None

    def test_unexpected_api_response(self):
        service, _ = make_service({"query": {"pages": []}})
        result = service.get_file_languages("Test.svg")
        assert result.error == "Metadata not found for File:Test.svg. Error: Unexpected API response"

    def test_file_missing(self):
        service, _ = make_service({"query": {"pages": [{"title": "File:Missing.svg", "missing": True}]}})
        result = service.get_file_languages("Missing.svg")
        assert "does not exist" in result.error

    def test_no_imageinfo(self):
        service, _ = make_service({"query": {"pages": [{"title": "File:Test.svg", "imageinfo": []}]}})
        result = service.get_file_languages("Test.svg")
        assert "Metadata not found" in result.error

    def test_no_metadata(self):
        service, _ = make_service(page_with_metadata([]))
        result = service.get_file_languages("Test.svg")
        assert "Metadata array empty" in result.error

    def test_with_translations(self):
        service, _ = make_service(
            page_with_metadata([{"name": "translations", "value": [{"name": "fr"}, {"name": "de"}, {"name": "es"}]}])
        )
        result = service.get_file_languages("Test.svg")
        assert result.error is None
        assert result.langs == ["fr", "de", "es", "en"]

    def test_no_translations_defaults_to_en(self):
        service, _ = make_service(page_with_metadata([{"name": "other_key", "value": "some_value"}]))
        result = service.get_file_languages("Test.svg")
        assert result.error is None
        assert result.langs == ["en"]

    def test_empty_translations_defaults_to_en(self):
        service, _ = make_service(page_with_metadata([{"name": "translations", "value": []}]))
        result = service.get_file_languages("Test.svg")
        assert result.error is None
        assert result.langs == ["en"]

    def test_translations_with_invalid_entries(self):
        service, _ = make_service(
            page_with_metadata([{"name": "translations", "value": ["not_a_dict", {"name": "fr"}]}])
        )
        result = service.get_file_languages("Test.svg")
        assert result.error is None
        assert result.langs == ["fr", "en"]

    def test_custom_session_used(self):
        service, session = make_service(page_with_metadata([{"name": "translations", "value": []}]))
        service.get_file_languages("Test.svg")
        session.request.assert_called_once()

    def test_metadata_non_dict_items_filtered(self):
        service, _ = make_service(
            page_with_metadata(["not_a_dict", 123, {"name": "translations", "value": [{"name": "it"}]}])
        )
        result = service.get_file_languages("Test.svg")
        assert result.error is None
        assert result.langs == ["it", "en"]
