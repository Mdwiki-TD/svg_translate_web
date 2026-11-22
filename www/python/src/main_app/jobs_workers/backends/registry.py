"""Backend registry: select the right backend from config."""

from __future__ import annotations

import logging

from ...config import get_settings
from .base import JobBackend

logger = logging.getLogger(__name__)

_BACKENDS: dict[str, type[JobBackend]] = {}


def _load_backends() -> dict[str, type[JobBackend]]:
    if _BACKENDS:
        return _BACKENDS

    from .thread_backend import ThreadBackend
    from .toolforge_backend import ToolforgeBackend

    _BACKENDS["thread"] = ThreadBackend
    _BACKENDS["toolforge"] = ToolforgeBackend
    return _BACKENDS


def get_backend_name(job_type: str | None = None) -> str:
    """Return the backend name to use for a given job type.

    Currently reads from the global ``JOBS_BACKEND`` setting.
    Per-job-type overrides can be added later.
    """
    app_settings = get_settings()
    return app_settings.jobs.backend


def get_backend(backend_name: str | None = None) -> JobBackend:
    """Instantiate and return the requested backend."""
    backends = _load_backends()
    name = backend_name or get_backend_name()
    cls = backends.get(name)
    if cls is None:
        raise ValueError(f"Unknown job backend: {name!r}. Available: {list(backends)}")
    return cls()


__all__ = [
    "get_backend",
    "get_backend_name",
]
