from pathlib import Path

import pytest

from src.main_app.services.copysvg_wrapper.extract_translations import extract_from_path
from src.main_app.services.copysvg_wrapper.mapping import TranslationMapping


class TestExtractFromPath:

    @pytest.mark.parametrize(
        "extract_return, expected_message",
        [
            ({"new": {}}, "No translations found in main file"),
            ({}, "No translations found in main file"),
        ],
    )
    def test_translations_task_stops_on_failure(self, monkeypatch, tmp_path, extract_return, expected_message):
        dummy_main_path = tmp_path / "downloads"
        dummy_main_path.mkdir()

        fake_svg_path = dummy_main_path / "Example.svg"
        fake_svg_path.write_text("<svg></svg>")

        def fake_extract(path):
            assert Path(path) == fake_svg_path
            return TranslationMapping.from_any(extract_return)

        monkeypatch.setattr(
            "src.main_app.services.copysvg_wrapper.extract_translations._extract_file_translations",
            fake_extract,
        )

        result = extract_from_path(fake_svg_path)

        assert result.success is False
        assert result.translations == {}
        assert expected_message in result.error

    def test_extract_translations_download_failure(self, tmp_path):

        fake_svg_path = tmp_path / "Example.svg"
        result = extract_from_path(fake_svg_path)

        assert result.success is False
        assert result.translations == {}
        assert "No translations found in main file" == result.message
        assert "io-error" == result.error

    def test_extract_translations_success(self, monkeypatch, tmp_path):
        fake_svg_path = tmp_path / "Example.svg"
        fake_svg_path.write_text("<svg></svg>")

        def fake_extract(path):
            return TranslationMapping(new={"en": {"text": "Hello"}, "fr": {"text": "Bonjour"}})

        monkeypatch.setattr(
            "src.main_app.services.copysvg_wrapper.extract_translations._extract_file_translations",
            fake_extract,
        )

        result = extract_from_path(fake_svg_path)

        assert result.success is True
        assert result.error is None
        assert "Loaded 2 translations" in result.message
        assert "new" in result.translations
