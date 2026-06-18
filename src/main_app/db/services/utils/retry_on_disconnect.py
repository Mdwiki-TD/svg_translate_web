from __future__ import annotations

import functools
import logging

from sqlalchemy.exc import OperationalError

from ....extensions import db

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 3


def retry_on_db_disconnect(max_retries: int = DEFAULT_MAX_RETRIES):
    """
    Retry a db.session-using function if the connection was invalidated
    or MySQL reports it has gone away. Rolls back and refreshes the
    session between attempts. Any other OperationalError (or exhausting
    retries) is logged and re-raised.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    is_disconnect = getattr(e, "connection_invalidated", False) or "MySQL server has gone away" in str(
                        e
                    )

                    if not is_disconnect:
                        logger.exception("%s: db operation failed", func.__name__)
                        raise

                    if attempt >= max_retries:
                        logger.error("%s: failed after %s retries.", func.__name__, max_retries)
                        raise

                    attempt += 1
                    logger.warning(
                        "%s: MySQL server has gone away. Rolling back and retrying (attempt %s/%s).",
                        func.__name__,
                        attempt,
                        max_retries,
                    )

                    try:
                        db.session.rollback()
                    except Exception:
                        # connection may be completely dead; ignore
                        pass

                    db.session.remove()

        return wrapper

    return decorator


__all__ = [
    "retry_on_db_disconnect",
]
