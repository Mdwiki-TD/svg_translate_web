from __future__ import annotations


class DatabaseInitError(Exception):
    """Raised when database initialization fails."""


class MaxUserConnectionsError(Exception):
    pass


class UserNotFoundError(LookupError):
    """Raised when a referenced user does not exist in users."""


class JobAlreadyRunningError(Exception):
    """Raised when a job of the same type is already running."""


class InsufficientDatabaseConfigError(RuntimeError):
    def __init__(self):
        msg = "DB requires database configuration; no fallback store is available."
        super().__init__(msg)
