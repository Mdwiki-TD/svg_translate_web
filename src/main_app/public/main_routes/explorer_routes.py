"""Svg viewer view definitions using Flask MethodViews."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from flask import (
    Blueprint,
    render_template,
    send_from_directory,
)
from flask.views import MethodView
from flask.wrappers import Response

from ...config import app_settings
from ..utils.compare import analyze_file
from ..utils.explorer_utils import (
    get_files,
    get_informations,
)
from ..utils.thumbnail_utils import save_thumb

logger = logging.getLogger(__name__)


def load_thumb_path() -> Path:
    """Return configured path for thumbnail storage."""
    return Path(app_settings.paths.svg_data_thumb)


def load_svg_data_path() -> Path:
    """Return configured path for SVG data storage."""
    return Path(app_settings.paths.svg_data)


class ExplorerMainView(MethodView):
    """View to handle the main explorer overview dashboard."""

    def get(self) -> str:
        """Render main explorer index showing summary statistics per title directory."""
        svg_data_path = load_svg_data_path()
        titles = [x.name for x in svg_data_path.iterdir() if x.is_dir()]
        data: dict[str, Any] = {}
        for title in titles:
            downloaded, _ = get_files(title, "files")
            translated, _ = get_files(title, "translated")
            data[title] = {
                "downloaded": len(downloaded),
                "translated": len(translated),
                "not_translated": len(set(downloaded).difference(translated)),
            }
        return render_template("explorer/index.html", data=data)


class ExplorerDownloadedView(MethodView):
    """View to list downloaded SVG files for a given title directory."""

    def get(self, title_dir: str) -> str:
        """Render list of downloaded files for a directory."""
        files, title_path = get_files(title_dir, "files")

        # title = get_temp_title(title_dir)
        title = title_dir

        return render_template(
            "explorer/explore_files.html",
            head_title=f"{title} downloaded Files ({len(files):,})",
            path=str(title_path),
            title=title,
            title_dir=title_dir,
            subdir="files",
            files=files,
        )


class ExplorerTranslatedView(MethodView):
    """View to list translated SVG files for a given title directory."""

    def get(self, title_dir: str) -> str:
        """Render list of translated files for a directory."""
        files, title_path = get_files(title_dir, "translated")

        # title = get_temp_title(title_dir)
        title = title_dir

        return render_template(
            "explorer/explore_files.html",
            head_title=f"({title}) Translated Files ({len(files):,})",
            path=str(title_path),
            title=title,
            title_dir=title_dir,
            subdir="translated",
            files=files,
            compare_link=True,
        )


class ExplorerNotTranslatedView(MethodView):
    """View to list files that have not yet been translated."""

    def get(self, title_dir: str) -> str:
        """Render list of non-translated files for a directory."""
        downloaded, title_path = get_files(title_dir, "files")
        translated, _ = get_files(title_dir, "translated")

        # title = get_temp_title(title_dir)
        title = title_dir

        # Instantiating set(translated) outside the list comprehension reduces lookup complexity to O(N + M)
        translated_set = set(translated)
        not_translated = [x for x in downloaded if x not in translated_set]

        return render_template(
            "explorer/explore_files.html",
            head_title=f"({title}) Not Translated Files ({len(not_translated):,})",
            path=str(title_path),
            title=title,
            title_dir=title_dir,
            subdir="files",
            files=not_translated,
        )


class ExplorerByTitleView(MethodView):
    """View to display detailed directory folder information."""

    def get(self, title: str) -> str:
        """Render folder information for a title."""
        infos = get_informations(title)

        return render_template(
            "explorer/folder.html",
            result=infos,
        )


class ExplorerServeMediaView(MethodView):
    """View to securely serve static SVG files."""

    def get(self, title_dir: str, subdir: str, filename: str) -> Response | tuple[str, int]:
        """Serve requested SVG file with security headers applied."""
        svg_data_path = load_svg_data_path().resolve()
        dir_path = (svg_data_path / title_dir / subdir).resolve()

        if not dir_path.is_relative_to(svg_data_path):
            return "Access Denied", 403

        response = send_from_directory(str(dir_path), filename)
        response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


class ExplorerServeThumbView(MethodView):
    """View to generate and serve cached thumbnail images for SVGs."""

    def get(self, title_dir: str, subdir: str, filename: str) -> Response | tuple[str, int]:
        """Generate thumbnail if missing and serve image with security headers."""
        svg_data_path = load_svg_data_path().resolve()
        thumb_base_path = load_thumb_path().resolve()
        dir_path = (svg_data_path / title_dir / subdir).resolve()
        thumb_path = (thumb_base_path / title_dir / subdir).resolve()

        if not dir_path.is_relative_to(svg_data_path) or not thumb_path.is_relative_to(thumb_base_path):
            return "Access Denied", 403

        file_path = dir_path / filename
        file_thumb_path = thumb_path / filename

        if not file_thumb_path.exists():
            save_thumb(file_path, file_thumb_path)

        if file_thumb_path.exists():
            response = send_from_directory(str(thumb_path), filename)
        else:
            response = send_from_directory(str(dir_path), filename)

        response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response


class ExplorerCompareView(MethodView):
    """View to compare downloaded and translated versions of an SVG."""

    def get(self, title_dir: str, filename: str) -> str:
        """Analyze original and translated files and render comparison view."""
        svg_data_path = load_svg_data_path()
        file_path = svg_data_path / title_dir / "files" / filename
        translated_path = svg_data_path / title_dir / "translated" / filename

        file1_result = analyze_file(file_path)
        file2_result = analyze_file(translated_path)

        return render_template(
            "explorer/compare.html",
            file=filename,
            title_dir=title_dir,
            downloaded_result=file1_result,
            translated_result=file2_result,
        )


class ExplorerView:
    """Registrar class to bind explorer MethodViews to a Blueprint."""

    @staticmethod
    def register(bp: Blueprint) -> None:
        """Register all explorer URL rules on the provided blueprint."""
        bp.add_url_rule("/", view_func=ExplorerMainView.as_view("main"))

        bp.add_url_rule("/<title_dir>/downloads", view_func=ExplorerDownloadedView.as_view("by_title_downloaded"))
        bp.add_url_rule("/<title_dir>/translated", view_func=ExplorerTranslatedView.as_view("by_title_translated"))
        bp.add_url_rule(
            "/<title_dir>/not_translated", view_func=ExplorerNotTranslatedView.as_view("by_title_not_translated")
        )

        bp.add_url_rule("/<title>", view_func=ExplorerByTitleView.as_view("by_title"))

        bp.add_url_rule(
            "/media/<title_dir>/<subdir>/<string:filename>",
            view_func=ExplorerServeMediaView.as_view("serve_media"),
        )
        bp.add_url_rule(
            "/media_thumb/<title_dir>/<subdir>/<string:filename>",
            view_func=ExplorerServeThumbView.as_view("serve_thumb"),
        )

        bp.add_url_rule("/compare/<title_dir>/<string:filename>", view_func=ExplorerCompareView.as_view("compare"))


__all__ = [
    "ExplorerView",
]
