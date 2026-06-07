from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, ParamSpec, TypeVar

from sqlalchemy.exc import IntegrityError, OperationalError, PendingRollbackError, SQLAlchemyError

from ...extensions import db

logger = logging.getLogger(__name__)


# Define generic types for strict type hinting
P = ParamSpec("P")
R = TypeVar("R")


def db_guard_rollback() -> Callable[..., Callable[P, R]]:
    """ """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except IntegrityError as exc:
                db.session.rollback()
                raise exc
            except Exception as exc:
                db.session.rollback()
                raise exc

        return wrapper

    return decorator


def db_guard(default_return: Any = False, msg: str = "") -> Callable[..., Callable[P, R]]:
    """Decorator factory to wrap a DB service function.

    On success, the original return value is passed through.
    On *any* exception, the session is rolled back, the error is logged,
    and the specified ``default_return`` value is returned.
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


def db_retry(
    default_return: Any = False,
    msg: str = "",
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> Callable[..., Callable[P, R]]:
    """Decorator factory to wrap a DB service function with retry logic.

    Behaves like ``db_guard`` but retries on recoverable errors
    (OperationalError, PendingRollbackError) with exponential backoff.

    On success, the original return value is passed through.
    On recoverable DB errors, the session is rolled back and the operation is
    retried up to ``max_retries`` times with ``retry_delay * attempt`` seconds
    between attempts. After all retries are exhausted, ``default_return`` is
    returned. Non-recoverable SQLAlchemyError returns ``default_return``
    immediately without retry.

    Args:
        default_return: Value returned when all retries are exhausted.
        msg: Context message logged on error.
        max_retries: Maximum retry attempts after the first failure.
        retry_delay: Base delay in seconds before first retry (multiplied by
            attempt number for exponential backoff).
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            total_attempts = max_retries + 1
            for attempt in range(1, total_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except OperationalError as exc:
                    logger.error(
                        "DB operational error in %s (attempt %d/%d)",
                        func.__qualname__,
                        attempt,
                        total_attempts,
                    )
                    logger.exception(f"{msg}: %s", exc)
                    db.session.rollback()
                    if attempt >= total_attempts:
                        return default_return
                    time.sleep(retry_delay * attempt)
                except PendingRollbackError as exc:
                    logger.error(
                        "DB pending rollback error in %s (attempt %d/%d)",
                        func.__qualname__,
                        attempt,
                        total_attempts,
                    )
                    logger.exception(f"{msg}: %s", exc)
                    db.session.rollback()
                    if attempt >= total_attempts:
                        return default_return
                    time.sleep(retry_delay * attempt)
                except SQLAlchemyError as exc:
                    logger.error("DB error in %s", func.__qualname__)
                    logger.exception(f"{msg}: %s", exc)
                    db.session.rollback()
                    return default_return

        return wrapper

    return decorator
