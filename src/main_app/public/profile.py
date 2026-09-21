from __future__ import annotations

import logging

from flask import Blueprint, flash, render_template
from flask.views import MethodView

from ..database.services import JobsService, UserJobsStats
from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from ..services.auth.utils import get_current_user

logger = logging.getLogger(__name__)


class ProfileView(MethodView):
    """View to handle rendering user profile dashboard and statistics."""

    def __init__(self) -> None:
        self.jobs_service = JobsService()

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        """Register profile routes on the provided blueprint."""
        view = cls.as_view("dashboard")
        bp.add_url_rule("/", view_func=view, methods=["GET"])
        bp.add_url_rule("/<string:user_name>", view_func=view, methods=["GET"])

    def get(self, user_name: str = "") -> str:
        """Render user profile page with job statistics."""
        user = get_current_user()

        if not user_name:
            if not user:
                flash("You must be logged in to view your profile.", "warning")
                return render_template("profile.html")

            user_name = user.username
            show_all = True
        else:
            show_all = bool(user and getattr(user, "is_active_admin", False))

        try:
            if show_all:
                data = self.jobs_service.get_all_user_jobs_stats(user_name)
            else:
                data = self.jobs_service.get_user_jobs_stats(
                    username=user_name,
                    jobs_types=list(jobs_data_public.keys()),
                )

        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to load user stats.")
            flash("Unable to load user job statistics.", "danger")
            data = UserJobsStats.empty()

        return render_template(
            "profile.html",
            username=user_name,
            stats=data.stats,
            recent_jobs=data.recent_jobs,
            jobs_data_public=list(jobs_data_public.keys()),
        )


__all__ = [
    "ProfileView",
]
