from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.main_app.services.copysvg_wrapper.inject_one_file import (
    inject_step_one_file,
)
from src.main_app.services.copysvg_wrapper.mapping import InjectorData


@dataclass
class Error:
    code: str | None = None
    label: str | None = None


@pytest.fixture
def mock_tree():
    tree = MagicMock()
    tree.write = MagicMock()
    return tree


@pytest.fixture
def mock_write_svg_file(monkeypatch: pytest.MonkeyPatch):
    mock = MagicMock(return_value=True)
    monkeypatch.setattr(
        "src.main_app.services.copysvg_wrapper.inject_one_file.write_svg_file",
        mock,
    )
    return mock


@pytest.fixture
def mock_inject(monkeypatch: pytest.MonkeyPatch):
    mock = MagicMock()
    monkeypatch.setattr(
        "src.main_app.services.copysvg_wrapper.inject_one_file.start_svg_injection",
        mock,
    )
    return mock


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


class TestInjectsWriteSvgFile:
    def test_new_languages(self, mock_inject, mock_tree, svg_file, output_file):
        data = InjectorData(tree=mock_tree)
        data.inject_stats._update(new_languages_count=3, updated_translations=0)

        mock_inject.return_value = data

        result = inject_step_one_file(svg_file, {"new": {"en": "Hello"}}, output_file, overwrite_translations=False)

        assert result.result is True
        assert result.msg == "3 languages injected"
        assert result.new_languages_count == 3
        assert result.updated_translations == 0
        mock_tree.write.assert_called_once_with(
            str(output_file), encoding="utf-8", xml_declaration=True, pretty_print=True
        )

    def test_tree_write_oserror(self, mock_inject, mock_tree, svg_file, output_file):
        mock_tree.write.side_effect = OSError("Permission denied")
        data = InjectorData(tree=mock_tree)
        data.inject_stats._update(
            new_languages_count=2,
            updated_translations=1,
        )

        mock_inject.return_value = data

        result = inject_step_one_file(svg_file, {}, output_file, overwrite_translations=False)

        assert result.result is False
        assert result.msg == "Failed to write file"
        assert result.new_languages_count == 2
        assert result.updated_translations == 1

    def test_tree_write_generic_exception(self, mock_inject, mock_tree, svg_file, output_file):
        mock_tree.write.side_effect = RuntimeError("disk full")
        data = InjectorData(tree=mock_tree)
        data.inject_stats._update(
            new_languages_count=2,
            updated_translations=1,
        )

        mock_inject.return_value = data

        result = inject_step_one_file(svg_file, {}, output_file, overwrite_translations=False)

        assert result.result is False
        assert result.msg == "Failed to write file"


class TestStartInjects:
    def test_updated_translations_only(self, mock_write_svg_file, mock_inject, mock_tree, svg_file, output_file):

        data = InjectorData(tree=mock_tree)
        data.inject_stats._update(new_languages_count=0, updated_translations=5)

        mock_inject.return_value = data

        result = inject_step_one_file(svg_file, {}, output_file, overwrite_translations=False)

        assert result.result is True
        assert result.msg == "5 translations Updated"
        assert result.new_languages_count == 0
        assert result.updated_translations == 5

    def test_no_changes(self, mock_inject, mock_tree, svg_file, output_file):
        data = InjectorData(tree=mock_tree)
        data.inject_stats._update(new_languages_count=0, updated_translations=0)

        mock_inject.return_value = data

        result = inject_step_one_file(svg_file, {}, output_file, overwrite_translations=False)

        assert result.result is None
        assert result.msg == "No changes"
        assert result.new_languages_count is None
        assert result.updated_translations is None

    def test_failed_to_translate(self, mock_inject, mock_tree, svg_file, output_file):
        mock_inject.return_value = InjectorData(tree=None)

        result = inject_step_one_file(svg_file, {}, output_file, overwrite_translations=False)

        assert result.result is False
        assert result.msg == "Failed to translate"

    def test_stats_error(self, mock_inject, mock_tree, svg_file, output_file):
        data = InjectorData(tree=mock_tree)
        data.inject_stats._update(new_languages_count=0, updated_translations=0)
        data.error = Error(label="Some error occurred")  # type: ignore

        mock_inject.return_value = data

        result = inject_step_one_file(svg_file, {}, output_file, overwrite_translations=False)

        assert result.result is False
        assert result.msg == "Some error occurred"

    def test_new_and_updated_both_present(self, mock_write_svg_file, mock_inject, mock_tree, svg_file, output_file):
        data = InjectorData(tree=mock_tree)
        data.inject_stats._update(
            new_languages_count=2,
            updated_translations=3,
        )

        mock_inject.return_value = data

        result = inject_step_one_file(svg_file, {}, output_file, overwrite_translations=False)

        assert result.result is True
        assert result.msg == "2 languages injected"
        assert result.new_languages_count == 2
        assert result.updated_translations == 3


class TestInjectStepOneFileNestedError:
    def test_nested_tspan_error(self, mock_inject, mock_tree, svg_file, output_file):

        data = InjectorData(tree=None)
        data.error.from_error(Error(code="nested_tspan_error"))

        mock_inject.return_value = data

        result = inject_step_one_file(svg_file, {}, output_file, overwrite_translations=False)

        assert result.result is False
        assert result.msg == "Nested tspan error"

    def test_nested_tspan_error_new(self, mock_inject, mock_tree, svg_file, output_file):

        data = InjectorData(tree=None)
        data.error.from_error(Error(code="nested_tspan_error"))

        mock_inject.return_value = data

        result = inject_step_one_file(svg_file, {}, output_file, overwrite_translations=False)

        assert result.result is False
        assert result.msg == "Nested tspan error"
