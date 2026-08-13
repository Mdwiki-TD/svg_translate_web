"""
Generic CRUD service/repository for Flask-SQLAlchemy models.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from typing import Any, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..exceptions import RecordNotFoundError

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT")  # , bound=db.Model
PKT = TypeVar("PKT")  # primary key type, e.g. int, str, uuid.UUID


# class CRUDService[ModelT, PKT]:
class CRUDService[ModelT]:
    """
    Generic CRUD service wrapping a single SQLAlchemy model.
    """

    model: type[ModelT]

    def __init__(self, session: Session | Any, model: type[ModelT]) -> None:
        self.session = session
        self.model = model
        self.model_name = getattr(self.model, "__name__", None)

    # ------------------------------------------------------------------ #
    # Read
    # ------------------------------------------------------------------ #

    def get_record_by_id(self, pk: PKT) -> ModelT | None:  # pyright: ignore[reportInvalidTypeVarUse]
        """Fetch a single row by primary key, or None if it doesn't exist."""
        try:
            return self.session.get(self.model, pk)
        except Exception as exc:
            logger.error("Error getting %s id=%s: %s", self.model_name, pk, exc)
            return None

    def get(self, pk: PKT) -> ModelT | None:  # pyright: ignore[reportInvalidTypeVarUse]
        return self.get_record_by_id(pk)

    def get_by(self, **filters: Any) -> ModelT | None:
        """Fetch a single row matching the given column=value filters."""
        try:
            stmt = self._base_select().filter_by(**filters)
            return self.session.execute(stmt).scalars().first()
        except Exception as exc:
            logger.error("Error getting %s by filters: %s", self.model_name, exc)
            return None

    def list_all(
        self,
        order_by: Iterable[Any] | None = None,
    ) -> list[ModelT]:
        try:
            stmt = self.session.query(self.model)

            if order_by:
                stmt = stmt.order_by(*order_by)

            return list(stmt.all())
        except Exception as exc:
            logger.error("Error listing %s records: %s", self.model_name, exc)
            return []

    def list(
        self,
        *,
        filters: dict[str, Any] | None = None,
        order_by: Iterable[Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ModelT]:
        """
        Fetch multiple rows.

        `filters` is a simple column=value equality mapping. For anything
        more complex (OR, LIKE, joins, etc.), build your own `Select` and
        pass it to `list_by_statement` instead.
        """
        try:
            stmt = self._base_select()
            if filters:
                stmt = stmt.filter_by(**filters)
            if order_by:
                stmt = stmt.order_by(*order_by)
            if limit is not None:
                stmt = stmt.limit(limit)
            if offset is not None:
                stmt = stmt.offset(offset)
            result = self.session.execute(stmt).scalars().all()
            return list(result)
        except Exception as exc:
            logger.error("Error listing %s records: %s", self.model_name, exc)
            return []

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

    def add_record(self, instance: ModelT) -> ModelT:
        """Instantiate the model with `fields` and persist it."""
        try:
            self.session.add(instance)
        except Exception:
            logger.error("Error adding %s", self.model_name)
            raise

        try:
            self.commit()
            self.session.refresh(instance)
            return instance
        except Exception:
            logger.error("Error adding %s", self.model_name)
            raise

    def create(self, **fields: Any) -> ModelT:
        """Instantiate the model with `fields` and persist it."""
        try:
            instance = self.model(**fields)
            self.session.add(instance)
        except Exception:
            logger.error("Error adding %s", self.model_name)
            raise

        try:
            self.commit()
            self.session.refresh(instance)
            return instance
        except Exception:
            logger.error("Error adding %s", self.model_name)
            raise

    def update(self, instance: ModelT, **fields: Any) -> ModelT:
        """Set attributes on `instance` and persist the change."""
        for key, value in fields.items():
            if not hasattr(instance, key):
                logger.warning("%s has no attribute %r; ignoring", self.model_name, key)
                # raise CRUDError(f"{self.model_name} has no attribute '{key}'")
                continue
            if value is not None:
                setattr(instance, key, value)

        self.commit()
        self.session.refresh(instance)

        return instance

    def update_by_id(
        self,
        pk: PKT,  # pyright: ignore[reportInvalidTypeVarUse]
        data: dict[str, Any],
        validate: bool = False,
    ) -> ModelT | None:
        """Set attributes on `instance` and persist the change."""
        record = self.get_record_by_id(pk)
        if record is None:
            logger.error("Error updating %s id=%s: record not found", self.model_name, pk)
            return None

        try:
            # if validate and hasattr(record, "validate"): record.validate()
            self.update(record, **data)
            return record
        except Exception as exc:
            logger.error("Error updating %s id=%s: %s", self.model_name, pk, exc)
            return None

    def upsert(self, pk: PKT, **fields: Any) -> tuple[ModelT, bool]:  # pyright: ignore[reportInvalidTypeVarUse]
        """
        Update the row with primary key `pk` if it exists, else create it.
        Returns (instance, created).
        """
        instance = self.get_record_by_id(pk)
        if instance is not None:
            return self.update(instance, **fields), False
        return self.create(**fields), True

    def upsert_by(self, keys: dict[str, Any], **fields: Any) -> tuple[ModelT, bool]:
        """
        Update the row matching `keys` if it exists, else create it.

        `keys` defines the *lookup identity* — the columns used to determine whether a matching row already exists
        (e.g. email or external_id). `fields` are the remaining values to update/create with.

        Important notes:
        - `keys` must not be empty. An empty dict would make get_by() run with no filters at all, potentially
          returning an arbitrary first row from the table.
        - `keys` and `fields` must not overlap on column names. This guarantees the "lookup identity" and "created
          identity" are always the same. Without this check, the lookup could search using one value (e.g. an old
          email) while the newly created row ends up with a different value (e.g. a new email) for that same column.
        - There is a potential race condition between the lookup step (get_by) and the insert step (create): two
          concurrent calls could both see "no row exists" and both attempt to create one, causing one of them to
          fail with a unique-constraint IntegrityError. We catch that and retry as an update instead of failing
          outright.
        - This approach relies on an actual unique constraint in the database on the `keys` columns. Without one,
          IntegrityError will never be raised, and nothing will actually prevent duplicate concurrent inserts.

        Args:
            keys: Lookup identity columns; must not be empty.
            **fields: Remaining fields to update on an existing row, or to add (merged with keys) when creating a
                new one.

        Returns:
            tuple: (instance, created) where created=True if a new row was created, or False if an existing row was
            updated.

        Raises:
            ValueError: If `keys` is empty, or if `keys` and `fields` overlap.
            IntegrityError: If creation fails for a reason other than the expected key race (e.g. a different
                unique constraint), and the retry lookup also fails to find the row.
        """
        # 1) Reject empty keys: without this, get_by() would search with no filters at all, potentially returning
        #    an arbitrary first row from the table instead of a real match.
        if not keys:
            raise ValueError("upsert_by requires at least one non-empty key")

        # 2) Reject overlapping column names between keys and fields, to prevent the lookup identity from
        #    diverging from the created identity (see the "Important notes" section in the docstring above).
        overlap = set(keys) & set(fields)
        if overlap:
            raise ValueError(f"upsert_by: keys and fields overlap: {overlap}")

        # 3) Try to find an existing row using keys only. `fields` is intentionally excluded from the lookup so
        #    that the search identity can never be influenced by the values we intend to write.
        instance = self.get_by(**keys)
        if instance is not None:
            # Row exists -> update fields only (keys are left untouched, since they define identity).
            return self.update(instance, **fields), False

        # 4) No matching row found (as far as we could see) -> attempt to create one. `keys` is merged with
        #    `fields` so the new row's identity columns are populated alongside the rest of its data.
        data = {**keys, **fields}
        try:
            return self.create(**data), True
        except IntegrityError:
            # Most likely a race: a concurrent request created the same row between our get_by() call above and
            # this create() call. Roll back the failed transaction, then re-fetch and update instead of creating.
            self.session.rollback()
            instance = self.get_by(**keys)
            if instance is not None:
                return self.update(instance, **fields), False
            # The row still doesn't exist, so the error came from something else (e.g. a different unique
            # constraint on `fields`) -> re-raise the original error rather than masking it.
            raise

    def bulk_create(self, items: Iterable[dict[str, Any]]) -> Sequence[ModelT]:
        instances = [self.model(**fields) for fields in items]
        self.session.add_all(instances)
        try:
            self.commit()
        except Exception as exc:
            logger.error("Error bulk creating %s: %s", self.model_name, exc)
        return instances

    def delete(self, pk: PKT) -> bool:  # pyright: ignore[reportInvalidTypeVarUse]
        """Delete a record by primary key.

        Args:
            pk: Primary key value for the configured model.

        Returns:
            True when a row was deleted, otherwise False.
        """
        if pk is None:
            return False

        record = self.get_record_by_id(pk)
        if record:
            return self.delete_record(record)
        return False

    def delete_record(self, record: ModelT) -> bool:
        try:
            self.session.delete(record)
            self.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting {self.model_name} {e}")
            return False

    # ------------------------------------------------------------------ #
    # or 404
    # ------------------------------------------------------------------ #

    def get_or_404(self, pk: PKT, description: str | None = None) -> ModelT:  # pyright: ignore[reportInvalidTypeVarUse]
        """Fetch a single row by primary key, or raise a 404."""
        instance = self.get_record_by_id(pk)
        if instance is None:
            raise RecordNotFoundError(description or f"{self.model_name} with id={pk!r} not found")

        return instance

    def update_or_404(self, pk: PKT, **kwargs) -> ModelT:  # pyright: ignore[reportInvalidTypeVarUse]
        """Update an assessment record."""
        orm_obj = self.get_record_by_id(pk)
        if not orm_obj:
            raise RecordNotFoundError(f"Record with ID {pk} not found")

        if not kwargs:
            return orm_obj

        return self.update(orm_obj, **kwargs)

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def commit(self) -> None:
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def _base_select(self) -> Select[tuple[ModelT]]:
        return select(self.model)

    def expire_all(self) -> None:
        self.session.expire_all()


__all__ = [
    "CRUDService",
]
