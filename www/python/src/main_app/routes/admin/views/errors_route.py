"""
Admin-only routes for checking errors.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from itertools import islice
from pathlib import Path

from flask import Blueprint, flash, render_template, request
from flask.views import MethodView
from markupsafe import Markup, escape

from ....config import get_settings
from ....decorators import admin_required

logger = logging.getLogger(__name__)

DEFAULT_LOG_PATH = Path.home() / "uwsgi.log"
DEFAULT_PER_PAGE = 200
PER_PAGE_CHOICES = (100, 200, 500, 1000)
# Guards the browser against a single enormous line (e.g. a minified payload).
MAX_LINE_CHARS = 5_000
# Stop scanning for matches after this many hits to bound response time.
MAX_SEARCH_MATCHES = 10_000
CHUNK_SIZE = 1024 * 1024

Row = tuple[int, str]


@dataclass(frozen=True)
class LogPage:
    """One rendered page of log rows plus the totals needed for pagination."""

    rows: list[tuple[int, Markup]] = field(default_factory=list)
    total: int = 0
    page: int = 1
    capped: bool = False


def get_log_dir() -> Path:
    """Return configured log directory path."""
    return Path(get_settings().paths.log_dir)


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


def _open_text(path: Path):
    """Open a log file as tolerant UTF-8 text."""
    return path.open("r", encoding="utf-8", errors="replace")


class ErrorDashboardView(MethodView):
    """View to display log files in pages, with server-side search."""

    decorators = [admin_required]

    # ---- file selection -------------------------------------------------

    @staticmethod
    def _available_files(log_dir: Path) -> list[str]:
        """List the .log files in log_dir, plus the default log if it is not already there."""
        names = set()
        if log_dir.is_dir():
            names = {f.name for f in log_dir.iterdir() if f.is_file() and f.suffix == ".log"}
        names.add(DEFAULT_LOG_PATH.name)
        return sorted(names)

    @staticmethod
    def _resolve_log_path(log_dir: Path, available: list[str], requested: str | None) -> Path:
        """Validate the requested name against the whitelist and return its path.

        The whitelist also blocks path traversal. Unknown names flash a message
        and fall back to the default log.
        """
        if not requested:
            return DEFAULT_LOG_PATH
        if requested not in available:
            flash(f"File {requested} not found")
            return DEFAULT_LOG_PATH

        candidate = log_dir / requested
        # The default log normally lives outside log_dir (in the home directory).
        if requested == DEFAULT_LOG_PATH.name and not candidate.is_file():
            return DEFAULT_LOG_PATH
        return candidate

    # ---- reading --------------------------------------------------------

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
    def _read_page(path: Path, page: int, per_page: int) -> list[Row]:
        """Return (line_number, text) rows for one page without loading the whole file."""
        start = (page - 1) * per_page
        with _open_text(path) as fh:
            lines = islice(fh, start, start + per_page)
            return [(start + i + 1, _clip(line)) for i, line in enumerate(lines)]

    @staticmethod
    def _search(
        path: Path,
        pattern: re.Pattern[str],
        page: int,
        per_page: int,
    ) -> tuple[list[Row], int, bool]:
        """Stream the file once; return one page of matches, total matches, and a capped flag."""
        start = (page - 1) * per_page
        end = start + per_page
        rows: list[Row] = []
        total = 0

        with _open_text(path) as fh:
            for lineno, line in enumerate(fh, start=1):
                if not pattern.search(line):
                    continue
                if start <= total < end:
                    rows.append((lineno, _clip(line)))
                total += 1
                if total >= MAX_SEARCH_MATCHES:
                    return rows, total, True
        return rows, total, False

    def _load_page(self, path: Path, query: str, per_page: int) -> LogPage:
        """Load either a search result page or a plain browse page, highlighted for HTML."""
        if query:
            pattern = re.compile(f"({re.escape(query)})", re.IGNORECASE)
            page = _int_arg("page", 1, 1)
            raw_rows, total, capped = self._search(path, pattern, page, per_page)
        else:
            pattern = None
            total = self._count_lines(path)
            # Newest entries are at the bottom, so open on the last page by default.
            last_page = max(1, math.ceil(total / per_page))
            page = _int_arg("page", last_page, 1, last_page)
            raw_rows, capped = self._read_page(path, page, per_page), False

        rows = [(no, _highlight(text, pattern)) for no, text in raw_rows]
        return LogPage(rows=rows, total=total, page=page, capped=capped)

    # ---- request handling -----------------------------------------------

    def get(self, file_name: str | None = None) -> str:
        """Render the log viewer for the selected file, page, and optional search query."""
        query = request.args.get("q", "").strip()
        per_page = _int_arg("per_page", DEFAULT_PER_PAGE, 1, max(PER_PAGE_CHOICES))

        log_dir = get_log_dir()
        files = self._available_files(log_dir)
        log_path = self._resolve_log_path(log_dir, files, file_name or request.args.get("log_file"))
        logger.info("Read file: %s (q=%r)", log_path, query)

        file_exists = log_path.is_file()
        result = LogPage()
        if file_exists:
            try:
                result = self._load_page(log_path, query, per_page)
            except OSError:
                logger.exception("Error reading log file: %s", log_path)
                flash(f"Could not read {log_path.name}")

        return render_template(
            "admins/errors.html",
            files=files,
            selected_file=log_path.name,
            query=query,
            per_page=per_page,
            per_page_choices=PER_PAGE_CHOICES,
            total_pages=max(1, math.ceil(result.total / per_page)),
            max_matches=MAX_SEARCH_MATCHES,
            file_exists=file_exists,
            rows=result.rows,
            page=result.page,
            total=result.total,
            capped=result.capped,
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
