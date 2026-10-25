"""
Admin-only routes for checking errors.
"""

from __future__ import annotations

import logging
import math
import re
from itertools import islice
from pathlib import Path

from flask import Blueprint, flash, render_template, request
from flask.views import MethodView
from markupsafe import Markup, escape

from ...config import app_settings
from ..decorators import admin_required

logger = logging.getLogger(__name__)

DEFAULT_LOG_FILE = "errors.log"
DEFAULT_PER_PAGE = 200
PER_PAGE_CHOICES = (100, 200, 500, 1000)
# Guards the browser against a single enormous line (e.g. a minified payload).
MAX_LINE_CHARS = 5_000
# Stop scanning for matches after this many hits to bound response time.
MAX_SEARCH_MATCHES = 10_000
CHUNK_SIZE = 1024 * 1024


def get_log_dir() -> Path:
    """Return configured log directory path."""
    return Path(app_settings.paths.log_dir)


def _int_arg(name: str, default: int, minimum: int, maximum: int | None = None) -> int:
    """Parse an integer query argument and clamp it to a safe range."""
    try:
        value = int(request.args.get(name, default))
    except (TypeError, ValueError):
        value = default
    value = max(minimum, value)
    return min(value, maximum) if maximum is not None else value


def _clip(line: str) -> str:
    """Strip the line ending and truncate overly long lines."""
    line = line.rstrip("\r\n")
    if len(line) > MAX_LINE_CHARS:
        return line[:MAX_LINE_CHARS] + " … [line truncated]"
    return line


def _highlight(text: str, pattern: re.Pattern[str] | None) -> Markup:
    """Escape text for HTML and wrap search matches in <mark>."""
    if pattern is None:
        return escape(text)
    # The pattern has one capture group, so odd indexes are the matches.
    parts = pattern.split(text)
    return Markup("").join(Markup("<mark>%s</mark>") % part if i % 2 else escape(part) for i, part in enumerate(parts))


class ErrorDashboardView(MethodView):
    """View to display log files in pages, with server-side search."""

    decorators = [admin_required]

    @staticmethod
    def _list_log_files(log_dir: Path) -> list[str]:
        """List all .log files in the specified directory."""
        if not log_dir.is_dir():
            return []
        return sorted(f.name for f in log_dir.iterdir() if f.is_file() and f.suffix == ".log")

    @staticmethod
    def _count_lines(path: Path) -> int:
        """Count lines by streaming binary chunks, so memory stays flat."""
        total = 0
        last_byte = b"\n"
        with path.open("rb") as fh:
            while chunk := fh.read(CHUNK_SIZE):
                total += chunk.count(b"\n")
                last_byte = chunk[-1:]
        # A final line without a trailing newline still counts as a line.
        return total if last_byte == b"\n" else total + 1

    @staticmethod
    def _read_page(path: Path, page: int, per_page: int) -> list[tuple[int, str]]:
        """Return (line_number, text) rows for one page without loading the whole file."""
        start = (page - 1) * per_page
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            lines = islice(fh, start, start + per_page)
            return [(start + i + 1, _clip(line)) for i, line in enumerate(lines)]

    @staticmethod
    def _search(
        path: Path, pattern: re.Pattern[str], page: int, per_page: int
    ) -> tuple[list[tuple[int, str]], int, bool]:
        """Stream the file once; return one page of matches, total matches, and a capped flag."""
        start = (page - 1) * per_page
        end = start + per_page
        rows: list[tuple[int, str]] = []
        total = 0
        capped = False

        with path.open("r", encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, start=1):
                if not pattern.search(line):
                    continue
                if start <= total < end:
                    rows.append((lineno, _clip(line)))
                total += 1
                if total >= MAX_SEARCH_MATCHES:
                    capped = True
                    break
        return rows, total, capped

    def get(self, file_name: str | None = None) -> str:
        """Render the log viewer for the selected file, page, and optional search query."""
        selected_file = file_name or request.args.get("log_file", DEFAULT_LOG_FILE)
        query = request.args.get("q", "").strip()
        per_page = _int_arg("per_page", DEFAULT_PER_PAGE, 1, max(PER_PAGE_CHOICES))

        logger.info("Read file: %s (q=%r)", selected_file, query)

        logs_dir = get_log_dir()
        files = self._list_log_files(logs_dir)

        if selected_file not in files:
            flash(f"File {selected_file} not found")
            selected_file = DEFAULT_LOG_FILE
            logger.info("Changed file to: %s", selected_file)

        log_path = logs_dir / selected_file
        rows: list[tuple[int, Markup]] = []
        total = 0
        capped = False
        page = 1

        if log_path.is_file():
            try:
                pattern = re.compile(f"({re.escape(query)})", re.IGNORECASE) if query else None

                if pattern:
                    page = _int_arg("page", 1, 1)
                    raw_rows, total, capped = self._search(log_path, pattern, page, per_page)
                else:
                    total = self._count_lines(log_path)
                    last_page = max(1, math.ceil(total / per_page))
                    # Newest entries are at the bottom, so open on the last page by default.
                    page = _int_arg("page", last_page, 1, last_page)
                    raw_rows = self._read_page(log_path, page, per_page)

                rows = [(no, _highlight(text, pattern)) for no, text in raw_rows]
            except OSError:
                logger.exception("Error reading log file: %s", log_path)
                flash(f"Could not read {selected_file}")

        total_pages = max(1, math.ceil(total / per_page))
        page = min(page, total_pages) if not query else page

        return render_template(
            "admin/errors.html",
            files=files,
            selected_file=selected_file,
            rows=rows,
            query=query,
            page=page,
            per_page=per_page,
            per_page_choices=PER_PAGE_CHOICES,
            total=total,
            total_pages=total_pages,
            capped=capped,
            max_matches=MAX_SEARCH_MATCHES,
            file_exists=log_path.is_file(),
        )


class CheckErrorsView:
    """Registrar class to bind error checking MethodViews to a Blueprint."""

    @staticmethod
    def register(bp: Blueprint) -> None:
        """Register error checking URL rules on the provided blueprint."""
        view = ErrorDashboardView.as_view("dashboard")

        # Primary route handling optional log filename parameter
        bp.add_url_rule("/", defaults={"file_name": None}, view_func=view)
        bp.add_url_rule("/<string:file_name>", view_func=view)


__all__ = [
    "ErrorDashboardView",
    "CheckErrorsView",
]
