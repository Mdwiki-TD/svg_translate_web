"""Admin routes for exploring scheduler jobs information."""

from __future__ import annotations

import logging
from flask import Blueprint, render_template
from typing import Any

from ....admins.admins_required import admin_required
from ....scheduler import get_jobs_info

logger = logging.getLogger(__name__)


class Schedulers:
    """Admin routes for scheduler jobs management."""

    def __init__(self, bp_admin: Blueprint) -> None:
        @bp_admin.get("/schedulers")
        @admin_required
        def schedulers_dashboard() -> str:
            """Display all scheduler jobs information."""
            jobs = get_jobs_info()
            return render_template("admins/schedulers.html", jobs=jobs)
