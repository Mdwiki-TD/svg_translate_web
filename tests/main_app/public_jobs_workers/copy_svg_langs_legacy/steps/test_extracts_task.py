from pathlib import Path

import pytest

from src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_translations import extract_translations_step


@pytest.mark.parametrize(
    "extract_return, expected_message",
    [
        # No new translations found
        ({"existing": {"en": {}}, "new": {}}, "No translations found in main file"),
        # extract() returns an empty dict
        ({}, "No translations found in main file"),
        # extract() returns None
        (None, "No translations found in main file"),
    ],
)
def test_translations_task_stops_on_failure(monkeypatch, tmp_path, extract_return, expected_message):
    dummy_main_path = tmp_path / "downloads"
    dummy_main_path.mkdir()

    fake_svg_path = dummy_main_path / "Example.svg"
    fake_svg_path.write_text("<svg></svg>")

    def fake_download_one_file(title, out_dir, i, overwrite=False, session=None):
        return {"path": fake_svg_path}

    def fake_extract(path, case_insensitive):
        assert Path(path) == fake_svg_path
        return extract_return

    monkeypatch.setattr(
        "src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_translations.download_one_file",
        fake_download_one_file,
    )
    monkeypatch.setattr(
        "src.main_app.public_jobs_workers.copy_svg_langs.steps.extract_translations.extract", fake_extract
    )

    result = extract_translations_step("Example.svg", dummy_main_path)

    assert result["success"] is False
    assert result["translations"] == {}
    assert expected_message in result["error"]
