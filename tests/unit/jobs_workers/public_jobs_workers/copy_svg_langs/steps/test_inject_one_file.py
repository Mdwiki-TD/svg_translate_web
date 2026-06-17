from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.inject_one_file import (
    InjectResult,
    inject_step_one_file,
    start_injects,
)


@pytest.fixture
def mock_inject(monkeypatch: pytest.MonkeyPatch):
    mock = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.inject_one_file.inject",
        mock,
    )
    return mock


@pytest.fixture
def mock_tree():
    tree = MagicMock()
    tree.write = MagicMock()
    return tree


@pytest.fixture
def svg_file(tmp_path: Path) -> Path:
    f = tmp_path / "test.svg"
    f.write_text("<svg></svg>")
    return f


@pytest.fixture
def output_file(tmp_path: Path) -> Path:
    out = tmp_path / "translated" / "test.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


class TestStartInjects:
    def test_new_languages(self, mock_inject, mock_tree, svg_file, output_file):
        mock_inject.return_value = (
            mock_tree,
            {"new_languages": 3, "updated_translations": 0, "error": None, "nested_tspan_error": False},
        )

        result = start_injects(svg_file, {"new": {"en": "Hello"}}, output_file, overwrite=False)

        assert result.result is True
        assert result.msg == "3 languages injected"
        assert result.new_languages == 3
        assert result.updated_translations == 0
        mock_tree.write.assert_called_once_with(
            str(output_file), encoding="utf-8", xml_declaration=True, pretty_print=True
        )

    def test_updated_translations_only(self, mock_inject, mock_tree, svg_file, output_file):
        mock_inject.return_value = (
            mock_tree,
            {"new_languages": 0, "updated_translations": 5, "error": None, "nested_tspan_error": False},
        )

        result = start_injects(svg_file, {}, output_file, overwrite=False)

        assert result.result is True
        assert result.msg == "5 translations Updated"
        assert result.new_languages == 0
        assert result.updated_translations == 5

    def test_no_changes(self, mock_inject, mock_tree, svg_file, output_file):
        mock_inject.return_value = (
            mock_tree,
            {"new_languages": 0, "updated_translations": 0, "error": None, "nested_tspan_error": False},
        )

        result = start_injects(svg_file, {}, output_file, overwrite=False)

        assert result.result is None
        assert result.msg == "No changes"
        assert result.new_languages is None
        assert result.updated_translations is None

    def test_nested_tspan_error(self, mock_inject, mock_tree, svg_file, output_file):
        mock_inject.return_value = (None, {"nested_tspan_error": True})

        result = start_injects(svg_file, {}, output_file, overwrite=False)

        assert result.result is False
        assert result.msg == "Nested tspan error"

    def test_failed_to_translate(self, mock_inject, mock_tree, svg_file, output_file):
        mock_inject.return_value = (None, {"nested_tspan_error": False})

        result = start_injects(svg_file, {}, output_file, overwrite=False)

        assert result.result is False
        assert result.msg == "Failed to translate"

    def test_stats_error(self, mock_inject, mock_tree, svg_file, output_file):
        mock_inject.return_value = (
            mock_tree,
            {"new_languages": 0, "updated_translations": 0, "error": "Some error occurred", "nested_tspan_error": False},
        )

        result = start_injects(svg_file, {}, output_file, overwrite=False)

        assert result.result is False
        assert result.msg == "Some error occurred"

    def test_tree_write_oserror(self, mock_inject, mock_tree, svg_file, output_file):
        mock_tree.write.side_effect = OSError("Permission denied")
        mock_inject.return_value = (
            mock_tree,
            {"new_languages": 2, "updated_translations": 1, "error": None, "nested_tspan_error": False},
        )

        result = start_injects(svg_file, {}, output_file, overwrite=False)

        assert result.result is False
        assert result.msg == "Failed to write file"
        assert result.new_languages == 2
        assert result.updated_translations == 1

    def test_tree_write_generic_exception(self, mock_inject, mock_tree, svg_file, output_file):
        mock_tree.write.side_effect = RuntimeError("disk full")
        mock_inject.return_value = (
            mock_tree,
            {"new_languages": 2, "updated_translations": 1, "error": None, "nested_tspan_error": False},
        )

        result = start_injects(svg_file, {}, output_file, overwrite=False)

        assert result.result is False
        assert result.msg == "Failed to write file"

    def test_new_and_updated_both_present(self, mock_inject, mock_tree, svg_file, output_file):
        mock_inject.return_value = (
            mock_tree,
            {"new_languages": 2, "updated_translations": 3, "error": None, "nested_tspan_error": False},
        )

        result = start_injects(svg_file, {}, output_file, overwrite=False)

        assert result.result is True
        assert result.msg == "2 languages injected"
        assert result.new_languages == 2
        assert result.updated_translations == 3


class TestInjectStepOneFile:
    def test_success(self, mock_inject, mock_tree, svg_file, output_file):
        mock_inject.return_value = (
            mock_tree,
            {"new_languages": 1, "updated_translations": 0, "error": None, "nested_tspan_error": False},
        )

        result = inject_step_one_file(svg_file, {"new": {"en": "Hi"}}, output_file, overwrite=False)

        assert result.result is True
        assert result.msg == "1 languages injected"
        assert result.new_languages == 1

    def test_passthrough_no_changes(self, mock_inject, mock_tree, svg_file, output_file):
        mock_inject.return_value = (
            mock_tree,
            {"new_languages": 0, "updated_translations": 0, "error": None, "nested_tspan_error": False},
        )

        result = inject_step_one_file(svg_file, {}, output_file, overwrite=False)

        assert result.result is None
        assert result.msg == "No changes"

    def test_passthrough_failure(self, mock_inject, mock_tree, svg_file, output_file):
        mock_inject.return_value = (None, {"nested_tspan_error": True})

        result = inject_step_one_file(svg_file, {}, output_file, overwrite=False)

        assert result.result is False
        assert result.msg == "Nested tspan error"

    def test_exception_handling(self, mock_inject, mock_tree, svg_file, output_file):
        mock_inject.side_effect = RuntimeError("Unexpected error")

        result = inject_step_one_file(svg_file, {}, output_file, overwrite=False)

        assert result.result is False
        assert result.msg == "Failed during SVG translation injection"
        assert result.new_languages is None
