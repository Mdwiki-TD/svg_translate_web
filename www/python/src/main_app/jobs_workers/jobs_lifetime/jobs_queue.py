"""Database backed FIFO queue for background jobs.

The ``jobs`` table is the durable source of truth. A job is accepted with
``status='pending'`` and ``is_running=NULL`` (queued, no active slot) and is
atomically claimed (``status='running'``, ``is_running=1``) only when no other
job of the same ``job_type`` holds the unique active slot
``idx_unique_active_job``.

Layering:

- ``JobStarter`` validates and submits jobs.
- ``JobsQueue`` orders, claims, and dispatches jobs (this module).
- ``JobBackend`` executes a claimed job.
- ``JobsService`` persists and updates job state.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

from ...database.models import JobRecord
from ...database.services import JobsService, QueueJobsService
from ...io.jobs_files_service import JobFilesService
from ..objects import JobData

logger = logging.getLogger(__name__)

# Username used by CLI/cron submissions; it authenticates with the bot
# password of the tool instead of a stored user OAuth token.
BACKGROUND_JOB_USERNAME = "Background job"

# Fields that must never be persisted with a queued payload.
SENSITIVE_PAYLOAD_KEYS = frozenset(
    {
        "csrf_token",
        "access_token",
        "access_secret",
        "access_secret_token",
        "password",
        "secret",
        "token",
    }
)


class JobCredentialsError(RuntimeError):
    """Raised when the identity of a queued job cannot be rebuilt."""


@dataclass(frozen=True)
class EnqueueResult:
    """Outcome of a queue submission."""

    job_id: int
    queued: bool
    position: int = 0

    @property
    def started(self) -> bool:
        """True when the job was dispatched immediately."""
        return not self.queued


def sanitize_payload(data: dict[str, Any] | None) -> dict[str, Any]:
    """Remove CSRF tokens and credential-like keys from a payload mapping.

    Args:
        data: Raw args or form data.

    Returns:
        A shallow copy without sensitive or non-persistent keys.
    """
    if not data:
        return {}

    return {key: value for key, value in dict(data).items() if key not in SENSITIVE_PAYLOAD_KEYS}


class JobIdentityResolver:
    """Rebuilds the execution identity of a queued job from its username.

    Queued jobs can wait for a long time, so no request context, Flask ``g``
    or in-memory object may be used. Only the username is persisted; the
    encrypted OAuth token is loaded again at dispatch time through the
    existing token services. Tokens are never written to the queue payload.
    """

    def __init__(self, token_manager: Any | None = None) -> None:
        self._token_manager = token_manager

    @property
    def token_manager(self) -> Any:
        if self._token_manager is None:
            # Lazy import avoids a circular dependency at module import time.
            from ...services.auth import TokenManager

            self._token_manager = TokenManager()
        return self._token_manager

    def resolve(self, username: str) -> dict[str, Any]:
        """Return the auth payload used to execute a job for ``username``.

        Args:
            username: Owner of the queued job.

        Returns:
            A mapping compatible with ``WikiSiteClient.get_user_site``.

        Raises:
            JobCredentialsError: When no usable credential exists.
        """
        if not username:
            raise JobCredentialsError("Job has no username; credentials are unavailable")

        if username == BACKGROUND_JOB_USERNAME:
            # Cron/CLI submissions authenticate with the tool bot password.
            return {"username": username}

        try:
            payload = self.token_manager.get_auth_payload_by_username(username)
        except Exception:
            logger.exception("Failed to load credentials for job owner %s", username)
            raise JobCredentialsError("User credentials could not be loaded") from None

        if not payload or not payload.get("access_token") or not payload.get("access_secret"):
            logger.warning("No stored credentials for job owner %s", username)
            raise JobCredentialsError("User credentials are no longer available; please log in again")

        return payload


class JobsQueue:
    """Orders, claims, and dispatches queued jobs."""

    # Maximum number of claim attempts per dispatch call.
    MAX_CLAIM_ATTEMPTS = 5

    def __init__(
        self,
        jobs_service: JobsService | None = None,
        files_service: JobFilesService | None = None,
        backend: Any | None = None,
        identity_resolver: JobIdentityResolver | None = None,
        queue_jobs_service: QueueJobsService | None = None,
    ) -> None:
        """Initialize with optional dependencies.

        Args:
            jobs_service: Job persistence service.
            files_service: Durable payload storage.
            backend: Execution backend; defaults to ``ThreadBackend``.
            identity_resolver: Rebuilds the job owner identity at dispatch.
        """
        self.jobs_service = jobs_service or JobsService()
        self.queue_jobs_service = queue_jobs_service or QueueJobsService()
        self.files_service = files_service or JobFilesService()
        self._backend = backend
        self.identity_resolver = identity_resolver or JobIdentityResolver()
        self._recover_lock = threading.Lock()
        self._last_recover_at: float = 0.0

    # ------------------------------------------------------------------
    # Dependencies resolved lazily to avoid circular imports
    # ------------------------------------------------------------------

    @property
    def backend(self) -> Any:
        if self._backend is None:
            from ..backends.thread_backend import ThreadBackend

            self._backend = ThreadBackend()
        return self._backend

    @staticmethod
    def load_job_data(job_type: str) -> JobData | None:
        """Resolve the ``JobData`` descriptor registered for ``job_type``."""
        from .jobs_starter import load_job_data

        return load_job_data(job_type)

    # ------------------------------------------------------------------
    # Queue operations
    # ------------------------------------------------------------------

    def enqueue(
        self,
        job_type: str,
        username: str,
        args: dict[str, Any] | None = None,
        form_data: dict[str, Any] | None = None,
    ) -> EnqueueResult:
        """Persist a new pending job with its execution payload.

        Args:
            job_type: Registered job type.
            username: Owner of the job; used to rebuild credentials later.
            args: Resolved job arguments (sanitized before persisting).
            form_data: Submitted form data (sanitized before persisting).

        Returns:
            An :class:`EnqueueResult` telling whether the job started at once
            or waits in the queue, and its position when queued.

        Raises:
            ValueError: When the job type is unknown or no username is given.
            RuntimeError: When the payload could not be persisted.
        """
        job_data = self.load_job_data(job_type)
        if job_data is None or job_data.job_class is None:
            raise ValueError(f"Unknown job type: {job_type}")

        if not username:
            raise ValueError("User authentication data is required")

        job = self.queue_jobs_service.enqueue_job(job_type, username)

        payload = {
            "args": sanitize_payload(args),
            "form_data": sanitize_payload(form_data),
            "username": username,
        }

        try:
            self.files_service.save_payload(job.id, job.job_type, payload)
        except Exception:
            logger.exception("Failed to persist payload for job %s", job.id)
            self.queue_jobs_service.fail_job(job.id, job.job_type, "Failed to store the job payload")
            raise RuntimeError(f"Failed to store the payload of job {job.id}") from None

        started_id = self.dispatch_next(job.job_type)
        if started_id == job.id:
            return EnqueueResult(job_id=job.id, queued=False)

        position = self.queue_jobs_service.get_queue_position(job.id)
        return EnqueueResult(job_id=job.id, queued=True, position=position)

    def get_next_pending(self, job_type: str) -> JobRecord | None:
        """Return the oldest queued job of ``job_type`` (FIFO)."""
        pending = self.queue_jobs_service.list_pending_jobs(job_type, limit=1)
        return pending[0] if pending else None

    def claim_job(self, job: JobRecord) -> bool:
        """Atomically reserve the active slot for ``job``.

        Args:
            job: A pending job record.

        Returns:
            True when this caller now owns the active slot for the job type.
        """
        return self.queue_jobs_service.claim_pending_job(job.id)

    def dispatch_next(self, job_type: str) -> int | None:
        """Claim and submit the next eligible job of ``job_type``.

        Args:
            job_type: The job type whose queue should advance.

        Returns:
            The id of the dispatched job, or None when nothing could start.
        """
        if not job_type:
            return None

        try:
            if self.queue_jobs_service.has_running_job(job_type):
                return None
        except Exception:
            logger.exception("Unable to check the active slot of %s", job_type)
            return None

        for _ in range(self.MAX_CLAIM_ATTEMPTS):
            job = self.get_next_pending(job_type)
            if job is None:
                return None

            if not self.claim_job(job):
                # Lost race, or the slot got taken: stop or try the next row.
                if self.queue_jobs_service.has_running_job(job_type):
                    return None
                continue

            try:
                self._start_claimed(job)
            except JobCredentialsError as exc:
                logger.error("Job %s cannot start: %s", job.id, exc)
                self.queue_jobs_service.fail_job(job.id, job.job_type, str(exc))
                continue
            except Exception as exc:
                logger.exception("Backend submission failed for job %s", job.id)
                self.queue_jobs_service.fail_job(job.id, job.job_type, self._failure_message(exc))
                continue

            logger.info("Dispatched queued job %s (type=%s)", job.id, job.job_type)
            return job.id

        return None

    def dispatch_pending(self) -> list[int]:
        """Scan every job type with queued work and attempt one dispatch each.

        Returns:
            Ids of the jobs that were dispatched.
        """
        dispatched: list[int] = []
        for job_type in self.queue_jobs_service.list_pending_job_types():
            try:
                job_id = self.dispatch_next(job_type)
            except Exception:
                logger.exception("Failed to dispatch pending jobs of type %s", job_type)
                continue
            if job_id:
                dispatched.append(job_id)

        if dispatched:
            logger.info("Dispatched %d pending job(s): %s", len(dispatched), dispatched)
        return dispatched

    def cancel_pending(self, job_id: int, job_type: str | None = None) -> bool:
        """Cancel a job that has not started; the backend is never invoked.

        Args:
            job_id: The queued job.
            job_type: Optional extra filter.

        Returns:
            True when the pending job was cancelled.
        """
        return self.queue_jobs_service.cancel_pending_job(job_id, job_type)

    def queue_position(self, job_id: int) -> int:
        """Return the 1-based position of a queued job, 0 when not queued."""
        return self.queue_jobs_service.get_queue_position(job_id)

    def queue_positions(self, job_type: str) -> dict[int, int]:
        """Map pending job ids of ``job_type`` to their queue position."""
        return self.queue_jobs_service.get_queue_positions(job_type)

    def on_job_finished(self, job_id: int, job_type: str) -> int | None:
        """Advance the queue after a job reached a terminal state.

        Args:
            job_id: The finished job.
            job_type: Its job type.

        Returns:
            The id of the next dispatched job, if any.
        """
        try:
            return self.dispatch_next(job_type)
        except Exception:
            logger.exception("Failed to advance the queue after job %s", job_id)
            return None

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------

    def recover(self, *, force: bool = False, min_interval: float = 60.0) -> list[int]:
        """Release stale active slots and dispatch eligible pending jobs.

        Safe to call repeatedly: the claim is atomic and idempotent. Calls
        happening less than ``min_interval`` seconds apart are throttled so
        the recovery can be triggered from cheap places (startup, CLI cron,
        dispatch attempts) without hammering the database.

        Args:
            force: Ignore the throttle.
            min_interval: Minimum seconds between two recovery runs.

        Returns:
            Ids of the jobs dispatched by this run.
        """
        with self._recover_lock:
            now = time.monotonic()
            if not force and (now - self._last_recover_at) < min_interval:
                return []
            self._last_recover_at = now

        try:
            self.queue_jobs_service.release_stale_active_slots()
        except Exception:
            logger.exception("Stale active slot recovery failed")

        try:
            return self.dispatch_pending()
        except Exception:
            logger.exception("Pending job recovery failed")
            return []

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _failure_message(exc: Exception) -> str:
        """Build a non-sensitive failure reason for a job that could not start."""
        if isinstance(exc, (RuntimeError, ValueError)):
            return f"Failed to start the job: {exc}"
        return f"Failed to start the job: {type(exc).__name__}"

    def _start_claimed(self, job: JobRecord) -> None:
        """Hand an already claimed job to the execution backend.

        Args:
            job: A job that now holds the active slot for its type.

        Raises:
            JobCredentialsError: When the owner identity cannot be rebuilt.
            RuntimeError: When the job type or its payload is unavailable.
        """
        job_data = self.load_job_data(job.job_type)
        if job_data is None or job_data.job_class is None:
            raise RuntimeError(f"Unknown job type: {job.job_type}")

        stored = self.files_service.load_payload(job.id, job.job_type)
        if stored is None:
            raise RuntimeError(f"Missing payload for job {job.id}")

        user = self.identity_resolver.resolve(job.username)

        payload: dict[str, Any] = {
            "args": stored.get("args") or {},
            "form_data": stored.get("form_data"),
            "user": user,
        }

        self.backend.start(job, job_data, payload)


__all__ = [
    "BACKGROUND_JOB_USERNAME",
    "EnqueueResult",
    "JobCredentialsError",
    "JobIdentityResolver",
    "JobsQueue",
    "sanitize_payload",
]
