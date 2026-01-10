"""Tests for compare utilities."""

from __future__ import annotations

from pathlib import Path

from src.app.app_routes.explorer import compare


def _write_svg(path: Path, system_languages: list[str]) -> None:
    texts = "".join(f"<text systemLanguage='{lang}'>Sample</text>" for lang in system_languages)
    path.write_text(
        f"""<svg xmlns='http://www.w3.org/2000/svg'>{texts}</svg>""",
        encoding="utf-8",
    )


def test_file_langs_extracts_languages(tmp_path: Path) -> None:
    svg = tmp_path / "file.svg"
    _write_svg(svg, ["fr", "es", "fr"])

    languages = compare.file_langs(svg)

    assert set(languages) == {"en", "fr", "es"}


def test_analyze_file_reports_languages(tmp_path: Path) -> None:
    svg = tmp_path / "doc.svg"
    _write_svg(svg, ["de"])

    result = compare.analyze_file(svg)

    assert set(result["languages"]) == {"en", "de"}


def test_compare_svg_files_returns_both(tmp_path: Path) -> None:
    original = tmp_path / "orig.svg"
    translated = tmp_path / "translated.svg"
    _write_svg(original, ["es"])
    _write_svg(translated, ["fr"])

    first, second = compare.compare_svg_files(original, translated)

    assert set(first["languages"]) == {"en", "es"}
    assert set(second["languages"]) == {"en", "fr"}
