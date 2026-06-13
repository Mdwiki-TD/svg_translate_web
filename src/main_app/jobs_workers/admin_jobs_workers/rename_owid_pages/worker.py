"""
Worker module for rename_owid_pages.

Lists every page whose title starts with ``Template:OWID/`` or ``OWID/`` on
Wikimedia Commons and renames each one whose first character after ``OWID/``
is a lowercase letter, e.g.::

    Template:OWID/daily_meat_consumption_per_person
        -> Template:OWID/Daily_meat_consumption_per_person
    OWID/daily_meat_consumption_per_person
        -> OWID/Daily_meat_consumption_per_person

Authentication uses the current user's OAuth-bound Site (no env
credentials).
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable

from mwclient.client import Site

from ....api_services import MwClientPage, get_user_site
from ....db.services import get_template_by_title, update_template_data
from ...base_worker_object import BaseObjectsJobWorker
from .objects import RenameOwidPagesWorkerObject

logger = logging.getLogger(__name__)

# (namespace_id, prefix_after_namespace, full_prefix_label_for_display)
PREFIXES: tuple[tuple[int, str, str], ...] = (
    (10, "OWID/", "Template:OWID/"),  # Template namespace
    (0, "OWID/", "OWID/"),  # Main namespace
)

MOVE_REASON = "Capitalize first letter of OWID subpage name"


@dataclass
class RenameInfo:
    """Holds the outcome of attempting to rename a single page."""

    namespace: int
    old_title: str
    new_title: str | None = None
    newrevid: int | None = None
    status: str = "pending"  # renamed | skipped_target_exists | failed
    msg: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "old_title": self.old_title,
            "new_title": self.new_title,
            "status": self.status,
            "msg": self.msg,
            "timestamp": self.timestamp,
        }


def needs_rename(title: str, full_prefix: str) -> tuple[bool, str]:
    """Decide whether *title* needs a rename.

    Only the first character after ``full_prefix`` is changed; everything
    else (including spaces / underscores) is preserved as-is.

    Returns ``(needs_rename, new_title)``.
    """
    if not title.startswith(full_prefix):
        return False, title
    rest = title[len(full_prefix) :]
    if not rest:
        return False, title
    first = rest[0]
    if first.isalpha() and first.islower():
        return True, full_prefix + first.upper() + rest[1:]
    return False, title


class RenameOwidPagesWorker(BaseObjectsJobWorker):
    """Background worker that capitalizes OWID subpage names."""

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.site: Site | None = None

        super().__init__(job_id, user, cancel_event)
        self.result: RenameOwidPagesWorkerObject = RenameOwidPagesWorkerObject()
        self.args = args or {}
        self.result.args = self.args

    # ------------------------------------------------------------------
    # BaseObjectsJobWorker hooks
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        return "rename_owid_pages"

    def process(self) -> RenameOwidPagesWorkerObject:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning("Job %s: No site authentication available", self.job_id)
            self.log_no_site_error()
            return self.result

        # First pass: collect candidates so progress is bounded and we can
        # compute a sane save-progress interval.
        candidates: list[tuple[int, str, str, str]] = []
        for namespace, prefix, full_prefix in PREFIXES:
            if self.is_cancelled():
                return self.result

            logger.info("Job %s: Listing pages with prefix '%s' (ns=%d)", self.job_id, full_prefix, namespace)
            ns_count = 0
            for page in self._iter_owid_pages(namespace, prefix):
                ns_count += 1
                self.result.summary.checked += 1
                title = page.name
                yes, new_title = needs_rename(title, full_prefix)
                if not yes:
                    continue
                candidates.append((namespace, full_prefix, title, new_title))

            logger.info("Job %s: Scanned %d page(s) under '%s'", self.job_id, ns_count, full_prefix)

        total = len(candidates)
        logger.info("Job %s: %d page(s) need renaming", self.job_id, total)

        # Save progress immediately so the UI reflects the discovery phase.
        self.result.summary.total = total

        self._save_progress()

        per_item = self.get_priority(total) if total else 1

        # Second pass: actually move.
        for n, (namespace, _full_prefix, old_title, new_title) in enumerate(candidates, start=1):
            if self.is_cancelled():
                break

            logger.info("Job %s: Renaming %d/%d: %s -> %s", self.job_id, n, total, old_title, new_title)

            changed = self._rename_one(namespace, old_title, new_title)

            if changed and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            if n == 1 or n % per_item == 0:
                self._save_progress()

        if self.result.status in ("pending", "running"):
            self.result.status = "completed"

        return self.result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _iter_owid_pages(self, namespace: int, prefix: str) -> Iterable:
        """Yield non-redirect pages with *prefix* in *namespace*.

        ``filterredir='nonredirects'`` means redirects left behind by previous
        runs of this job are not re-processed, keeping the job idempotent.
        """
        if self.site:
            return self.site.allpages(
                prefix=prefix,
                namespace=namespace,
                filterredir="nonredirects",
            )
        return []

    def _rename_one(self, namespace: int, old_title: str, new_title: str) -> bool:
        self.result.summary.processed += 1

        info = RenameInfo(namespace=namespace, old_title=old_title, new_title=new_title)

        # Pre-flight: don't even try to move if the target already exists.
        new_title_page = MwClientPage(new_title, self.site)
        old_title_page = MwClientPage(old_title, self.site)

        if new_title_page.exists():
            # Both old_title and new_title exist on the wiki.
            # Check redirect relationships to decide what to do:

            if new_title_page.is_redirect():
                # Target is a redirect (e.g. left behind by a previous move),
                # the move API will overwrite it — proceed with the move below.
                pass
            elif old_title_page.is_redirect():
                # The old page is already a redirect to the new one — just
                # update the DB title to match the capitalized version.
                info.status = "skipped_target_exists"
                info.msg = f"Old page redirects to target, updating DB only: {new_title}"
                self.result.summary.skipped_target_exists += 1
                self._update_template_title(old_title, new_title)
                self.result.pages_processed.append(info.to_dict())
                return False  # no changes made
            else:
                # Neither page redirects to the other — both are real pages.
                # Redirect the old (lowercase) page to the new (capitalized) one.
                return self._redirect_old_to_new(info, old_title_page, new_title)

        res = old_title_page.move(
            new_title,
            reason=MOVE_REASON,
            move_talk=True,
            no_redirect=False,
        )
        edit_success = bool(res.get("success"))
        if res.get("success"):
            info.status = "renamed"
            info.newrevid = res.get("newrevid", 0)
            info.msg = f"Moved {old_title} -> {new_title}"
            self.result.summary.renamed += 1
            # Update the title in the database
            self._update_template_title(old_title, new_title)
        else:
            err = res.get("error", "Unknown error")
            details = res.get("details")
            info.status = "failed"
            info.msg = f"{err}: {details}" if details else str(err)
            self.result.summary.failed += 1

        self.result.pages_processed.append(info.to_dict())
        return edit_success

    def _redirect_old_to_new(self, info: RenameInfo, old_title_page: MwClientPage, new_title: str) -> bool:
        """Turn the old (lowercase) page into a redirect to the new (capitalized) page."""
        redirect_text = f"#REDIRECT [[{new_title}]]"
        summary = f"Redirecting to [[{new_title}]] (capitalize first letter of OWID subpage)"
        old_title = old_title_page.title

        res = old_title_page.edit(
            text=redirect_text,
            summary=summary,
        )

        edit_success = bool(res.get("success"))
        if edit_success:
            info.status = "redirected"
            info.newrevid = res.get("newrevid", 0)
            info.msg = f"Redirected {old_title} -> {new_title}"
            self.result.summary.redirected += 1
            self._update_template_title(old_title, new_title)
        else:
            err = res.get("error", "Unknown error")
            details = res.get("details")
            info.status = "failed"
            info.msg = f"Failed to redirect: {err}: {details}" if details else f"Failed to redirect: {err}"
            self.result.summary.failed += 1

        self.result.pages_processed.append(info.to_dict())
        return edit_success

    def _update_template_title(self, old_title: str, new_title: str) -> None:
        """Update TemplateRecord.title in the database after a successful move."""
        try:
            record = get_template_by_title(old_title)
            if record:
                update_template_data(record.id, {"title": new_title})
                logger.info("Job %s: Updated DB template title: %s -> %s", self.job_id, old_title, new_title)
            else:
                logger.debug("Job %s: No TemplateRecord found for '%s', skipping DB update", self.job_id, old_title)
        except Exception as exc:
            logger.warning("Job %s: Failed to update DB title for '%s': %s", self.job_id, old_title, exc)


def rename_owid_pages_for_templates(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point.

    Args:
        job_id: The job ID
        user: User authentication data
        cancel_event: Threading event for cancellation
        args: Optional arguments dict (unused, for unified signature)
    """
    logger.info("Starting job %s: rename OWID pages (capitalize first letter)", job_id)
    worker = RenameOwidPagesWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "RenameOwidPagesWorker",
    "needs_rename",
    "rename_owid_pages_for_templates",
]
