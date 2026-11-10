"""Simple in-memory rate limiting for authentication endpoints."""

from __future__ import annotations

import logging
from collections import deque
from datetime import UTC, datetime, timedelta
from threading import Lock

from flask import Request

logger = logging.getLogger(__name__)


class RateLimiter:
    """Track request timestamps per key and enforce a maximum rate."""

    def __init__(self, limit: int, period: timedelta) -> None:
        self._limit = limit
        self._period = period
        self._hits: dict[str, deque[datetime]] = {}
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        """Return True if the key is allowed to proceed, False when throttled."""
        now = datetime.now(UTC)
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] > self._period:
                hits.popleft()
            if len(hits) >= self._limit:
                logger.warning(
                    "Rate limit exceeded for key: %s (limit=%d, period=%s)",
                    key,
                    self._limit,
                    self._period,
                )
                return False
            hits.append(now)
            logger.debug(
                "Rate limit check passed for key: %s (hits=%d/%d)",
                key,
                len(hits),
                self._limit,
            )
            return True

    def try_after(self, key: str) -> timedelta:
        """Return the time until the key is allowed to proceed."""
        now = datetime.now(UTC)
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] > self._period:
                hits.popleft()
            if len(hits) >= self._limit:
                return self._period - (now - hits[0])
            return timedelta(0)

    def get_time_left(self, key: str) -> str:
        time_left = self.try_after(key).total_seconds()
        return str(time_left).split(".")[0]

    @classmethod
    def client_key(cls, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.remote_addr or "anonymous"

    @classmethod
    def login_rate_limiter(cls) -> RateLimiter:
        return RateLimiter(limit=5, period=timedelta(minutes=1))

    @classmethod
    def callback_rate_limiter(cls) -> RateLimiter:
        return RateLimiter(limit=10, period=timedelta(minutes=1))


__all__ = [
    "RateLimiter",
]
