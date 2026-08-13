"""Custom exceptions for the database layer."""

from __future__ import annotations

from typing import Any

from sqlalchemy.exc import DatabaseError


class UniqueError(DatabaseError):
    code = "gkpj-unique"
    message = "Unique constraint failed"

    def __init__(self, title) -> None:
        self.title = title
        super().__init__(f"Unique constraint failed for title: {title}", None, None)  # type: ignore


class DatabaseInitError(Exception):
    """Raised when database initialization fails."""


class RecordNotFoundError(LookupError):
    """Raised when a requested record does not exist."""

    def __init__(self, model_name: str, identifier: object | None = None) -> None:
        self.model_name = model_name
        self.identifier = identifier
        super().__init__(f"{model_name} not found: {identifier}")


class MultipleRecordsFoundError(Exception):
    """Raised when get_by() finds more than one result but expected exactly one."""

    def __init__(self, model_name: str, filters: dict[str, Any]) -> None:
        self.model_name = model_name
        self.filters = filters
        super().__init__(f"Multiple {model_name} records found for filters: {filters}")


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


__all__ = [
    "CRUDError",
    "RecordNotFoundError",
    "MultipleRecordsFoundError",
    "UniqueError",
    "DuplicateRecordError",
    "DatabaseInitError",
    "MaxUserConnectionsError",
    "UserNotFoundError",
    "InsufficientDatabaseConfigError",
]
