from __future__ import annotations


class DatabaseInitError(Exception):
    """Raised when database initialization fails."""


class MaxUserConnectionsError(Exception):
    pass


class UserNotFoundError(LookupError):
    """Raised when a referenced user does not exist in users."""


class DuplicateJobError(Exception):
    """Raised when attempting to create a job of a type that already has an active (pending/running) instance."""


class DuplicateUserError(Exception):
    """Raised when attempting to create a user or coordinator that already exists."""


class InsufficientDatabaseConfigError(RuntimeError):
    def __init__(self) -> None:
        msg = "DB requires database configuration; no fallback store is available."
        super().__init__(msg)


__all__ = [
    "DatabaseInitError",
    "MaxUserConnectionsError",
    "UserNotFoundError",
    "DuplicateUserError",
    "DuplicateJobError",
    "InsufficientDatabaseConfigError",
]
