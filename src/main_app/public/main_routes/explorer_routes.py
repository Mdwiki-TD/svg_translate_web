"""Svg viewer"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from flask import (
    Blueprint,
    render_template,
    send_from_directory,
)
from flask.wrappers import Response

from ...config import settings
from ..utils.compare import analyze_file
from ..utils.explorer_utils import (
    get_files,
    get_informations,
)
from ..utils.thumbnail_utils import save_thumb

logger = logging.getLogger(__name__)


def load_thumb_path() -> Path:
    return Path(settings.paths.svg_data_thumb)


def load_svg_data_path() -> Path:
    return Path(settings.paths.svg_data)


class ExplorerRoutes:
    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.get("/<title_dir>/downloads")
        def by_title_downloaded(title_dir: str) -> str:
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

        @self.bp.get("/<title_dir>/translated")
        def by_title_translated(title_dir: str) -> str:
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

        @self.bp.get("/<title_dir>/not_translated")
        def by_title_not_translated(title_dir: str) -> str:
            downloaded, title_path = get_files(title_dir, "files")
            translated, _ = get_files(title_dir, "translated")

            # title = get_temp_title(title_dir)
            title = title_dir

            not_translated = [x for x in downloaded if x not in set(translated)]

            return render_template(
                "explorer/explore_files.html",
                head_title=f"({title}) Not Translated Files ({len(not_translated):,})",
                path=str(title_path),
                title=title,
                title_dir=title_dir,
                subdir="files",
                files=not_translated,
            )

        @self.bp.get("/<title>")
        def by_title(title: str) -> str:
            infos = get_informations(title)

            return render_template(
                "explorer/folder.html",
                result=infos,
            )
        @self.bp.route("/", methods=["GET"])
        def main() -> str:
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

        @self.bp.route("/media/<title_dir>/<subdir>/<string:filename>")
        def serve_media(title_dir: str, subdir: str, filename: str) -> Response:
            """
            Serve SVG files
            """
            svg_data_path = load_svg_data_path()
            dir_path = svg_data_path / title_dir / subdir
            dir_path = str(dir_path.absolute())

            # dir_path = "I:/SVG_EXPLORER/svg_data/Parkinsons prevalence/translated"
            response = send_from_directory(dir_path, filename)
            response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response

        @self.bp.route("/media_thumb/<title_dir>/<subdir>/<string:filename>")
        def serve_thumb(title_dir: str, subdir: str, filename: str) -> Response:
            # ---
            dir_path = load_svg_data_path() / title_dir / subdir
            thumb_path = load_thumb_path() / title_dir / subdir
            # ---
            file_path = dir_path / filename
            file_thumb_path = thumb_path / filename
            # ---
            if not file_thumb_path.exists():
                save_thumb(file_path, file_thumb_path)

            if file_thumb_path.exists():
                response = send_from_directory(str(thumb_path.absolute()), filename)
            else:
                response = send_from_directory(str(dir_path.absolute()), filename)

            response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response

        @self.bp.route("/compare/<title_dir>/<string:filename>")
        def compare(title_dir: str, filename: str) -> str:
            """Compare SVG files"""
            # ---
            svg_data_path = load_svg_data_path()
            # ---
            file_path = svg_data_path / title_dir / "files" / filename
            translated_path = svg_data_path / title_dir / "translated" / filename
            # ---
            file1_result = analyze_file(file_path)
            file2_result = analyze_file(translated_path)
            # ---
            return render_template(
                "explorer/compare.html",
                file=filename,
                title_dir=title_dir,
                downloaded_result=file1_result,
                translated_result=file2_result,
            )

__all__ = [
    "ExplorerRoutes",
]
