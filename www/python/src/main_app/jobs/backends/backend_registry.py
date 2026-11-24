"""Backend registry: select the right backend from config."""

from __future__ import annotations

import logging

from ...config import get_settings
from .base import JobBackend

logger = logging.getLogger(__name__)


class BackendRegistry:
    """Registry for resolving and instantiating job backends."""

    def __init__(self) -> None:
        self._backends: dict[str, type[JobBackend]] = {}

    def register(self, name: str, backend_cls: type[JobBackend]) -> None:
        """Register a backend class under the given name."""
        self._backends[name] = backend_cls

    def _ensure_defaults_loaded(self) -> None:
        if self._backends:
            return

        from .thread_backend import ThreadBackend
        from .toolforge_backend import ToolforgeBackend

        self.register("thread", ThreadBackend)
        self.register("toolforge", ToolforgeBackend)

    def available_backends(self) -> list[str]:
        """Return the list of registered backend names."""
        self._ensure_defaults_loaded()
        return list(self._backends)

    def get_backend_name(self, job_type: str | None = None) -> str:
        """Return the backend name to use for a given job type."""
        return get_settings().jobs.backend

    def get_backend(self, backend_name: str | None = None) -> JobBackend:
        """Instantiate and return the requested backend."""
        self._ensure_defaults_loaded()
        name = backend_name or self.get_backend_name()
        cls = self._backends.get(name)
        if cls is None:
            raise ValueError(f"Unknown job backend: {name!r}. Available: {list(self._backends)}")
        return cls()


__all__ = [
    "BackendRegistry",
]
