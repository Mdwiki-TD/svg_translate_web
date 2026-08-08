"""
Worker module for copy_svg_langs.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .forms import CopySvgLangsForm
from .worker import CopySvgLangsWorker

logger = logging.getLogger(__name__)


def setup_svg_langs_form(all_settings: dict[str, Any] | None = None) -> CopySvgLangsForm:
    form = CopySvgLangsForm()
    # set upload default dynamically only on GET (first load)
    upload_disabled_by_default = bool(
        all_settings and all_settings.get("copy_svg_langs_upload_disabled_by_default", False)
    )
    form.upload.data = not upload_disabled_by_default
    return form


from ...objects import JobsRunner


# --- main pipeline --------------------------------------------
def copy_svg_langs_worker_entry(
    data: JobsRunner | None = None,
    *,
    job_id: int | None = None,
    user: dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
    form_data: dict[str, Any] | None = None,
) -> None:
    """Entry point for the background job."""
    if data is not None:
        job_id = data.job_id
        user = data.user
        cancel_event = data.cancel_event
        args = data.args
        form_data = data.form_data

    worker = CopySvgLangsWorker(
        job_id=job_id,  # type: ignore
        user=user,      # type: ignore
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "copy_svg_langs_worker_entry",
]
