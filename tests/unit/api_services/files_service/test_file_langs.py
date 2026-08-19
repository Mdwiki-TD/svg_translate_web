"""Tests for src/main_app/utils/file_langs.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import requests

from src.main_app.api_services.files_service.file_langs import FileLanguagesMap  # noqa: F401
from src.main_app.api_services.files_service.file_langs import get_file_languages


class TestGetFileLanguages:
    def test_empty_filename(self):
        result = get_file_languages("")
        assert result.error == "Empty fileName"
        assert result.langs is None

    def test_none_filename(self):
        result = get_file_languages(None)
        assert result.error == "Empty fileName"

    def test_file_colon_prefix_stripped(self):
        mock_session = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "pages": [
                    {
                        "title": "File:Test.svg",
                        "imageinfo": [
                            {
                                "metadata": [
                                    {"name": "translations", "value": [{"name": "fr"}, {"name": "de"}]},
                                ]
                            }
                        ],
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = get_file_languages("File:Test.svg", mock_session)
        call_args = mock_session.get.call_args
        assert "File:Test.svg" in str(call_args)

    def test_api_error(self):
        mock_session = MagicMock()

        mock_session.get.side_effect = requests.ConnectionError("Connection failed")

        result = get_file_languages("Test.svg", mock_session)
        assert "API error" in result.error
        assert result.langs is None

    def test_unexpected_api_response(self):
        mock_session = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"query": {"pages": []}}
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = get_file_languages("Test.svg", mock_session)
        assert result.error == "Metadata not found for File:Test.svg. Error: Unexpected API response"

    def test_file_missing(self):
        mock_session = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"query": {"pages": [{"title": "File:Missing.svg", "missing": True}]}}
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = get_file_languages("Missing.svg", mock_session)
        assert "does not exist" in result.error

    def test_no_imageinfo(self):
        mock_session = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"query": {"pages": [{"title": "File:Test.svg", "imageinfo": []}]}}
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = get_file_languages("Test.svg", mock_session)
        assert "Metadata not found" in result.error

    def test_no_metadata(self):
        mock_session = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "pages": [
                    {
                        "title": "File:Test.svg",
                        "imageinfo": [{"metadata": []}],
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = get_file_languages("Test.svg", mock_session)
        assert "Metadata array empty" in result.error

    def test_with_translations(self):
        mock_session = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "pages": [
                    {
                        "title": "File:Test.svg",
                        "imageinfo": [
                            {
                                "metadata": [
                                    {
                                        "name": "translations",
                                        "value": [
                                            {"name": "fr"},
                                            {"name": "de"},
                                            {"name": "es"},
                                        ],
                                    }
                                ]
                            }
                        ],
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = get_file_languages("Test.svg", mock_session)
        assert result.error is None
        assert result.langs == ["fr", "de", "es", "en"]

    def test_no_translations_defaults_to_en(self):
        mock_session = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "pages": [
                    {
                        "title": "File:Test.svg",
                        "imageinfo": [
                            {
                                "metadata": [
                                    {"name": "other_key", "value": "some_value"},
                                ]
                            }
                        ],
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = get_file_languages("Test.svg", mock_session)
        assert result.error is None
        assert result.langs == ["en"]

    def test_empty_translations_defaults_to_en(self):
        mock_session = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "pages": [
                    {
                        "title": "File:Test.svg",
                        "imageinfo": [
                            {
                                "metadata": [
                                    {"name": "translations", "value": []},
                                ]
                            }
                        ],
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = get_file_languages("Test.svg", mock_session)
        assert result.error is None
        assert result.langs == ["en"]

    def test_translations_with_invalid_entries(self):
        mock_session = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "pages": [
                    {
                        "title": "File:Test.svg",
                        "imageinfo": [
                            {
                                "metadata": [
                                    {
                                        "name": "translations",
                                        "value": [
                                            "not_a_dict",
                                            {"name": "fr"},
                                        ],
                                    }
                                ]
                            }
                        ],
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = get_file_languages("Test.svg", mock_session)
        assert result.error is None
        assert result.langs == ["fr", "en"]

    def test_custom_session_used(self):
        mock_session = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "pages": [
                    {
                        "title": "File:Test.svg",
                        "imageinfo": [{"metadata": [{"name": "translations", "value": []}]}],
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        custom_session = MagicMock()
        result = get_file_languages("Test.svg", session=custom_session)
        custom_session.get.assert_called_once()

    def test_metadata_non_dict_items_filtered(self):
        mock_session = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "query": {
                "pages": [
                    {
                        "title": "File:Test.svg",
                        "imageinfo": [
                            {
                                "metadata": [
                                    "not_a_dict",
                                    123,
                                    {"name": "translations", "value": [{"name": "it"}]},
                                ]
                            }
                        ],
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_response

        result = get_file_languages("Test.svg", mock_session)
        assert result.error is None
        assert result.langs == ["it", "en"]
