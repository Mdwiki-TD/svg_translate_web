"""Tests for the rate limiter."""

from datetime import timedelta

import pytest

from src.app.app_routes.auth.rate_limit import RateLimiter


def test_ratelimiter_enforces_limit() -> None:
    limiter = RateLimiter(limit=2, period=timedelta(seconds=60))

    assert limiter.allow("key") is True
    assert limiter.allow("key") is True
    assert limiter.allow("key") is False

    remaining = limiter.try_after("key")
    assert remaining > timedelta(0)
    assert remaining <= timedelta(seconds=60)


@pytest.mark.parametrize("key", ["a", "b"])
def test_ratelimiter_tracks_keys_independently(key: str) -> None:
    limiter = RateLimiter(limit=1, period=timedelta(seconds=10))

    assert limiter.allow(key) is True
    assert limiter.allow(key) is False
    assert limiter.allow("other") is True
