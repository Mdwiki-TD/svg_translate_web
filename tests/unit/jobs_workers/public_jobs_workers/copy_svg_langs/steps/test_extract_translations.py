from pathlib import Path

import pytest

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.extract_translations import (
    extract_translations_step,
)


@pytest.mark.parametrize(
    "extract_return, expected_message",
    [
        ({"existing": {"en": {}}, "new": {}}, "No translations found in main file"),
        ({}, "No translations found in main file"),
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
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.extract_translations.download_one_file",
        fake_download_one_file,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.extract_translations.extract", fake_extract
    )

    result = extract_translations_step("Example.svg", dummy_main_path)

    assert result["success"] is False
    assert result["translations"] == {}
    assert expected_message in result["error"]


def test_extract_translations_download_failure(monkeypatch, tmp_path):
    def fake_download_one_file(title, out_dir, i, overwrite=False, session=None):
        return {"path": ""}

    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.extract_translations.download_one_file",
        fake_download_one_file,
    )

    result = extract_translations_step("Example.svg", tmp_path)

    assert result["success"] is False
    assert result["translations"] == {}
    assert "Error when downloading main file" in result["error"]


def test_extract_translations_extract_exception(monkeypatch, tmp_path):
    fake_svg_path = tmp_path / "Example.svg"
    fake_svg_path.write_text("<svg></svg>")

    def fake_download_one_file(title, out_dir, i, overwrite=False, session=None):
        return {"path": fake_svg_path}

    def fake_extract(path, case_insensitive):
        raise ValueError("SVG parse error")

    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.extract_translations.download_one_file",
        fake_download_one_file,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.extract_translations.extract", fake_extract
    )

    result = extract_translations_step("Example.svg", tmp_path)

    assert result["success"] is False
    assert result["translations"] == {}
    assert result["error"] == "Failed to parse main SVG"


def test_extract_translations_success(monkeypatch, tmp_path):
    fake_svg_path = tmp_path / "Example.svg"
    fake_svg_path.write_text("<svg></svg>")

    def fake_download_one_file(title, out_dir, i, overwrite=False, session=None):
        return {"path": fake_svg_path}

    def fake_extract(path, case_insensitive):
        return {"new": {"en": {"text": "Hello"}, "fr": {"text": "Bonjour"}}, "existing": {}}

    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.extract_translations.download_one_file",
        fake_download_one_file,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.extract_translations.extract", fake_extract
    )

    result = extract_translations_step("Example.svg", tmp_path)

    assert result["success"] is True
    assert result["error"] is None
    assert "Loaded 2 translations" in result["message"]
    assert "new" in result["translations"]
