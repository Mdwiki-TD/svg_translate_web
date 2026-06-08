from __future__ import annotations

import functools
import logging
from typing import Any, Callable, ParamSpec, TypeVar, cast

from sqlalchemy.exc import IntegrityError, OperationalError, PendingRollbackError, SQLAlchemyError

from ...extensions import db

logger = logging.getLogger(__name__)


# Define generic types for strict type hinting
FuncType = TypeVar("FuncType", bound=Callable[..., Any])
P = ParamSpec("P")
R = TypeVar("R")


def db_guard_rollback(func: FuncType) -> FuncType:  # noqa: UP047
    """Decorator that requires a full OAuth credential bundle."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        # Check g._current_user which was populated by load_logged_in_user
        try:
            return func(*args, **kwargs)
        except IntegrityError as exc:
            db.session.rollback()
            raise exc
        except Exception as exc:
            db.session.rollback()
            raise exc

    return cast(FuncType, wrapper)


def db_guard(default_return: Any = False, msg: str = "") -> Callable[..., Callable[P, R]]:
    """Decorator factory to wrap a DB service function.

    On success, the original return value is passed through.
    On *any* exception, the session is rolled back, the error is logged,
    and the specified `default_return` value is returned.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except OperationalError as exc:
                logger.error("DB error in %s", func.__qualname__)
                logger.exception(f"{msg}: %s", exc)
                db.session.rollback()
                return default_return
            except PendingRollbackError as exc:
                logger.error("DB pending rollback error in %s", func.__qualname__)
                logger.exception(f"{msg}: %s", exc)
                db.session.rollback()
                return default_return
            except SQLAlchemyError as exc:
                logger.error("DB error in %s", func.__qualname__)
                logger.exception(f"{msg}: %s", exc)
                db.session.rollback()
                return default_return

        return wrapper

    return decorator
