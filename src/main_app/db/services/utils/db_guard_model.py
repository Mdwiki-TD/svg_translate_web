from __future__ import annotations

import functools
import logging
from typing import Any, Callable, ParamSpec, cast

from sqlalchemy.exc import IntegrityError, OperationalError, PendingRollbackError, SQLAlchemyError

from ....extensions import db

logger = logging.getLogger(__name__)

# Define generic types for strict type hinting
P = ParamSpec("P")


def db_guard_rollback(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that rolls back the DB session on exception and re-raises."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any):
        try:
            return func(*args, **kwargs)
        except IntegrityError as exc:
            db.session.rollback()
            raise exc
        except Exception as exc:
            db.session.rollback()
            raise exc

    return cast(Callable[..., Any], wrapper)


def db_guard(default_return: Any = False, msg: str = "") -> Callable[[Callable[P, Any]], Callable[P, Any]]:
    """Decorator factory to wrap a DB service function.

    On success, the original return value is passed through.
    On *any* exception, the session is rolled back, the error is logged,
    and the specified `default_return` value is returned.
    """

    def decorator(func: Callable[P, Any]) -> Callable[P, Any]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except OperationalError as exc:
                logger.error("DB error in %s", func.__qualname__)
                logger.exception("%s: %s", msg, exc)
                db.session.rollback()
                return default_return
            except PendingRollbackError as exc:
                logger.error("DB pending rollback error in %s", func.__qualname__)
                logger.exception("%s: %s", msg, exc)
                db.session.rollback()
                return default_return
            except SQLAlchemyError as exc:
                logger.error("DB error in %s", func.__qualname__)
                logger.exception("%s: %s", msg, exc)
                db.session.rollback()
                return default_return
            except Exception as exc:
                logger.error("Unexpected error in %s", func.__qualname__)
                logger.exception("%s: %s", msg, exc)
                db.session.rollback()
                return default_return

        return wrapper

    return decorator


__all__ = [
    "db_guard_rollback",
    "db_guard",
]
