from __future__ import annotations

import functools
import logging
import time

from sqlalchemy.exc import OperationalError

from ....extensions import db

logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 3
# 2006: server has gone away, 2013: lost connection during query
DISCONNECT_CODES = {2006, 2013}


def _is_disconnect(exc: OperationalError) -> bool:
    """Return True if the error looks like a dropped DB connection."""
    orig = getattr(exc, "orig", None)
    args = getattr(orig, "args", None)
    code = args[0] if args else None
    return (
        code in DISCONNECT_CODES or "server has gone away" in str(exc) or getattr(exc, "connection_invalidated", False)
    )


def retry_on_db_disconnect(
    max_retries: int = DEFAULT_MAX_RETRIES,
    remove_session: bool = False,
    backoff: float = 0.2,
):
    """
    Retry a db.session-using function when the connection was dropped.

    Rolls back (and optionally removes) the session between attempts.
    Any other OperationalError, or exhausting retries, is logged and re-raised.

    Warning: only use on idempotent operations. A disconnect during commit
    may have already been applied by the server. With remove_session=True,
    ORM instances loaded before the retry become detached.
    """
    if callable(max_retries):
        raise TypeError("Use @retry_on_db_disconnect(), with parentheses.")

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = getattr(func, "__name__", repr(func))
            attempt = 0
            while True:
                try:
                    result = func(*args, **kwargs)
                except OperationalError as exc:
                    if not _is_disconnect(exc):
                        logger.exception("%s: db operation failed", func_name)
                        raise

                    if attempt >= max_retries:
                        logger.error("%s: failed after %s retries.", func_name, max_retries)
                        raise

                    attempt += 1
                    logger.warning(
                        "%s: DB connection lost. Retrying (attempt %s/%s).",
                        func_name,
                        attempt,
                        max_retries,
                    )

                    try:
                        db.session.rollback()
                    except Exception:
                        pass  # connection may be completely dead

                    # NOTE: this will causes DetachedInstanceError
                    if remove_session:
                        db.session.remove()
                        logger.warning("%s: session removed.", func_name)
                    time.sleep(backoff * attempt)
                else:
                    if attempt:
                        logger.info("%s: succeeded after %s retries.", func_name, attempt)
                    return result

        return wrapper

    return decorator


__all__ = [
    "retry_on_db_disconnect",
]
