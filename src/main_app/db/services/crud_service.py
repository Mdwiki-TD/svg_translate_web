"""
Generic CRUD service/repository for Flask-SQLAlchemy models.

Usage
-----
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()

    class User(db.Model):
        id: Mapped[int] = mapped_column(primary_key=True)
        email: Mapped[str] = mapped_column(unique=True)

    class UserService(CRUDService[User, int]):
        model = User

    user_service = UserService(db.session)

    user = user_service.create(email="a@example.com")
    user = user_service.get_or_404(1)
    users = user_service.list(filters={"email": "a@example.com"}, limit=20)
    user = user_service.update(user, email="b@example.com")
    user_service.delete(user)
"""

from __future__ import annotations

from typing import (
    Any,
    Generic,
    Iterable,
    Sequence,
    Type,
    TypeVar,
)

from sqlalchemy import select, func, Select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from werkzeug.exceptions import NotFound

try:
    # Only used for isinstance checks / typing; not a hard runtime dependency.
    from flask_sqlalchemy.model import Model as _FlaskSQLAlchemyModel
except ImportError:  # pragma: no cover
    _FlaskSQLAlchemyModel = object  # type: ignore[misc, assignment]


ModelT = TypeVar("ModelT", bound=_FlaskSQLAlchemyModel)
PKT = TypeVar("PKT")  # primary key type, e.g. int, str, uuid.UUID


class CRUDError(Exception):
    """Base error for CRUD service failures."""


class CRUDIntegrityError(CRUDError):
    """Raised when a create/update violates a DB constraint (unique, FK, etc.)."""


class CRUDService(Generic[ModelT, PKT]):
    """
    Generic CRUD service wrapping a single SQLAlchemy model.

    Subclass and set `model` to the mapped class. The generic parameters
    let type checkers know exactly what type `get`, `create`, etc. return:

        class UserService(CRUDService[User, int]):
            model = User
    """

    model: Type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    # ------------------------------------------------------------------ #
    # Read
    # ------------------------------------------------------------------ #

    def get(self, pk: PKT) -> ModelT | None:
        """Fetch a single row by primary key, or None if it doesn't exist."""
        return self.session.get(self.model, pk)

    def get_or_404(self, pk: PKT, description: str | None = None) -> ModelT:
        """Fetch a single row by primary key, or raise a 404."""
        instance = self.get(pk)
        if instance is None:
            raise NotFound(
                description or f"{self.model.__name__} with id={pk!r} not found"
            )
        return instance

    def get_by(self, **filters: Any) -> ModelT | None:
        """Fetch a single row matching the given column=value filters."""
        stmt = self._base_select().filter_by(**filters)
        return self.session.execute(stmt).scalars().first()

    def list(
        self,
        *,
        filters: dict[str, Any] | None = None,
        order_by: Iterable[Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[ModelT]:
        """
        Fetch multiple rows.

        `filters` is a simple column=value equality mapping. For anything
        more complex (OR, LIKE, joins, etc.), build your own `Select` and
        pass it to `list_by_statement` instead.
        """
        stmt = self._base_select()
        if filters:
            stmt = stmt.filter_by(**filters)
        if order_by:
            stmt = stmt.order_by(*order_by)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        return self.session.execute(stmt).scalars().all()

    def list_by_statement(self, stmt: Select[tuple[ModelT]]) -> Sequence[ModelT]:
        """Escape hatch: run a caller-built Select and return scalar results."""
        return self.session.execute(stmt).scalars().all()

    def count(self, filters: dict[str, Any] | None = None) -> int:
        stmt = select(func.count()).select_from(self.model)
        if filters:
            stmt = stmt.filter_by(**filters)
        return self.session.execute(stmt).scalar_one()

    def exists(self, **filters: Any) -> bool:
        stmt = select(self._base_select().filter_by(**filters).exists())
        return bool(self.session.execute(stmt).scalar())

    # ------------------------------------------------------------------ #
    # Write
    # ------------------------------------------------------------------ #

    def create(self, *, commit: bool = True, **fields: Any) -> ModelT:
        """Instantiate the model with `fields` and persist it."""
        instance = self.model(**fields)
        self.session.add(instance)
        self._flush_or_commit(commit)
        return instance

    def update(
        self, instance: ModelT, *, commit: bool = True, **fields: Any
    ) -> ModelT:
        """Set attributes on `instance` and persist the change."""
        for key, value in fields.items():
            if not hasattr(instance, key):
                raise CRUDError(
                    f"{self.model.__name__} has no attribute '{key}'"
                )
            setattr(instance, key, value)
        self._flush_or_commit(commit)
        return instance

    def upsert(
        self, pk: PKT, *, commit: bool = True, **fields: Any
    ) -> tuple[ModelT, bool]:
        """
        Update the row with primary key `pk` if it exists, else create it.
        Returns (instance, created).
        """
        instance = self.get(pk)
        if instance is not None:
            return self.update(instance, commit=commit, **fields), False
        return self.create(commit=commit, **fields), True

    def delete(self, instance: ModelT, *, commit: bool = True) -> None:
        self.session.delete(instance)
        self._flush_or_commit(commit)

    def delete_by_pk(self, pk: PKT, *, commit: bool = True) -> bool:
        """Delete by primary key. Returns False if no row was found."""
        instance = self.get(pk)
        if instance is None:
            return False
        self.delete(instance, commit=commit)
        return True

    def bulk_create(
        self, items: Iterable[dict[str, Any]], *, commit: bool = True
    ) -> Sequence[ModelT]:
        instances = [self.model(**fields) for fields in items]
        self.session.add_all(instances)
        self._flush_or_commit(commit)
        return instances

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _base_select(self) -> Select[tuple[ModelT]]:
        return select(self.model)

    def _flush_or_commit(self, commit: bool) -> None:
        """
        Persist pending changes. Commits (and rolls back cleanly on failure)
        when `commit=True`; otherwise just flushes so autogenerated fields
        (e.g. PKs) are available, leaving the transaction open for the caller.
        """
        try:
            if commit:
                self.session.commit()
            else:
                self.session.flush()
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise CRUDIntegrityError(str(exc)) from exc
