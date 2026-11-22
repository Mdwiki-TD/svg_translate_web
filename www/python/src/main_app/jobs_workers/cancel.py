"""Cross-process cancel event that polls the database."""

from __future__ import annotations

import time


class DbCancelEvent:
    """Replacement for ``threading.Event`` that reads cancellation from the database.

    Used when a job runs in a separate process (Toolforge pod) where the
    in-memory ``threading.Event`` set by the web process is not visible.

    The event also responds to ``set()`` (e.g. from a SIGTERM handler) so
    that graceful shutdown works within the process itself.
    """

    def __init__(self, job_id: int, interval: float = 2.0) -> None:
        self.job_id = job_id
        self.interval = interval
        self._set: bool = False
        self._last_check: float = 0.0

    def set(self) -> None:
        self._set = True

    def is_set(self) -> bool:
        if self._set:
            return True
        now = time.monotonic()
        if now - self._last_check >= self.interval:
            self._last_check = now
            from ..database.services import JobsService

            self._set = JobsService().is_job_cancelled(self.job_id)
        return self._set

    def wait(self, timeout: float | None = None) -> bool:
        end = None if timeout is None else time.monotonic() + timeout
        while not self.is_set():
            if end is not None and time.monotonic() >= end:
                break
            time.sleep(0.5)
        return self._set


__all__ = [
    "DbCancelEvent",
]
