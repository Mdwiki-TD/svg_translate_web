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
from collections.abc import Iterable

import mwclient
import mwclient.page

from ....api_services import MwClientPage
from ....database.services import TemplateService
from ...base_worker import BaseObjectsJobWorker
from ...objects import JobsRunner
from .objects import RenameInfo, RenameOwidPagesWorkerObject

logger = logging.getLogger(__name__)

# (namespace_id, prefix_after_namespace, full_prefix_label_for_display)
PREFIXES: tuple[tuple[int, str, str], ...] = (
    (10, "OWID/", "Template:OWID/"),  # Template namespace
    (0, "OWID/", "OWID/"),  # Main namespace
)

MOVE_REASON = "Capitalize first letter of OWID subpage name"


class RenameOwidPagesWorker(BaseObjectsJobWorker[RenameOwidPagesWorkerObject]):
    """Background worker that capitalizes OWID subpage names."""

    JOB_TYPE = "rename_owid_pages"

    def __init__(
        self,
        data: JobsRunner,
        template_service: TemplateService | None = None,
        mw_client_cls: MwClientPage | None = None,
    ) -> None:
        super().__init__(data)
        self.template_service = template_service or TemplateService()
        self.mw_client_cls = mw_client_cls or MwClientPage

    def create_result(self) -> RenameOwidPagesWorkerObject:
        """Create and return the specific result object instance."""
        return RenameOwidPagesWorkerObject(
            job_id=self.job_id,
            args=self.args,
        )

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def _get_candidates(self) -> list[RenameInfo]:
        """Return a list of pages that need renaming."""
        # First pass: collect candidates so progress is bounded and we can
        # compute a sane save-progress interval.
        candidates: list[RenameInfo] = []

        for namespace, prefix, full_prefix in PREFIXES:
            logger.info("Job %s: Listing pages with prefix '%s' (ns=%d)", self.job_id, full_prefix, namespace)
            ns_count = 0

            owid_pages = self._iter_owid_pages(namespace, prefix)
            if not owid_pages:
                logger.info("No pages found with prefix %r (namespace %d)", full_prefix, namespace)
                continue

            for page in owid_pages:
                self.result.summary.checked += 1
                ns_count += 1
                title = page.name

                item = RenameInfo(
                    namespace=namespace,
                    full_prefix=full_prefix,
                    old_title=title,
                )
                if item.needs_rename():
                    candidates.append(item)

            logger.info("Job %s: Scanned %d page(s) under '%s'", self.job_id, ns_count, full_prefix)

        return candidates

    def process(self) -> RenameOwidPagesWorkerObject:
        if not self._check_site():
            return self.result

        candidates = self._get_candidates()

        total = len(candidates)
        # Save progress immediately so the UI reflects the discovery phase.
        self.result.summary.total = total

        if not candidates:
            logger.info("Job %s: No pages need renaming", self.job_id)
            self.result.status = "skipped"
            self.result.note = "No pages need renaming"
            return self.result

        if self.is_cancelled():
            return self.result

        logger.info("Job %s: %d page(s) need renaming", self.job_id, total)

        self.save_progress()

        self.rename_candidates(candidates)

        return self.result

    def rename_candidates(self, candidates: list[RenameInfo]) -> None:
        total = len(candidates)

        per_item = self.get_priority(total)

        # Second pass: actually move.
        for n, info in enumerate(candidates, start=1):
            if self.is_cancelled():
                break

            logger.info("Job %s: Renaming %d/%d: %s -> %s", self.job_id, n, total, info.old_title, info.new_title)

            changed = self._process_one_item(info)

            self.update_status(info)

            if changed and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            if n == 1 or n % per_item == 0:
                self.save_progress()

    def update_status(self, info: RenameInfo) -> None:
        self.result.summary.processed += 1

        if info.status == "skipped_target_exists":
            self.result.summary.skipped_target_exists += 1
            self.result.pages_skipped.append(info)

        elif info.status == "redirected":
            self.result.pages_redirected.append(info)

        elif info.status == "renamed":
            self.result.pages_renamed.append(info)

        elif info.status == "failed":
            self.result.pages_failed.append(info)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _iter_owid_pages(self, namespace: int, prefix: str) -> Iterable[mwclient.page.Page]:
        """Yield non-redirect pages with *prefix* in *namespace*.

        ``filterredir='nonredirects'`` means redirects left behind by previous
        runs of this job are not re-processed, keeping the job idempotent.
        """
        if self.site:
            return self.site.allpages(
                prefix=prefix,
                namespace=str(namespace),
                filterredir="nonredirects",
            )
        return []

    def _process_one_item(self, info: RenameInfo) -> bool:
        old_title = info.old_title
        new_title = info.new_title

        # Pre-flight: don't even try to move if the target already exists.
        new_title_page = self.mw_client_cls.load(new_title, self.site)
        old_title_page = self.mw_client_cls.load(old_title, self.site)

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

                self._update_template_title(old_title, new_title)

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
            # Update the title in the database
            self._update_template_title(old_title, new_title)
        else:
            err = res.get("error", "Unknown error")
            details = res.get("details")
            info.status = "failed"
            info.msg = f"{err}: {details}" if details else str(err)

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
            self._update_template_title(old_title, new_title)
        else:
            err = res.get("error", "Unknown error")
            details = res.get("details")
            info.status = "failed"
            info.msg = f"Failed to redirect: {err}: {details}" if details else f"Failed to redirect: {err}"

        return edit_success

    def _update_template_title(self, old_title: str, new_title: str) -> None:
        """Update TemplateRecord.title in the database after a successful move."""
        try:
            record = self.template_service.get_template_by_title(old_title)
            if record:
                self.template_service.update_template_data(record.id, {"title": new_title})
                logger.info("Job %s: Updated DB template title: %s -> %s", self.job_id, old_title, new_title)
            else:
                logger.debug("Job %s: No TemplateRecord found for '%s', skipping DB update", self.job_id, old_title)
        except Exception as exc:
            logger.warning("Job %s: Failed to update DB title for '%s': %s", self.job_id, old_title, exc)


__all__ = [
    "RenameOwidPagesWorker",
]
