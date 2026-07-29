from __future__ import annotations

from sqlalchemy.exc import DatabaseError


class UniqueError(DatabaseError):
    code = "gkpj-unique"
    message = "Unique constraint failed"

    def __init__(self, title) -> None:
        self.title = title
        super().__init__(f"Unique constraint failed for title: {title}", None, None)  # type: ignore


class DatabaseInitError(Exception):
    """Raised when database initialization fails."""


class MaxUserConnectionsError(Exception):
    pass


class UserNotFoundError(LookupError):
    """Raised when a referenced user does not exist in users."""


class DuplicateRecordError(Exception):
    """Raised when attempting to create duplicate record."""


class InsufficientDatabaseConfigError(RuntimeError):
    def __init__(self) -> None:
        msg = "DB requires database configuration; no fallback store is available."
        super().__init__(msg)


class CRUDError(Exception):
    """Base error for CRUD service failures."""


class RecordNotFoundError(LookupError):
    """Raised when a record not found."""


__all__ = [
    "CRUDError",
    "RecordNotFoundError",
    "UniqueError",
    "DuplicateRecordError",
    "DatabaseInitError",
    "MaxUserConnectionsError",
    "UserNotFoundError",
    "InsufficientDatabaseConfigError",
]
