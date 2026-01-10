"""Tests for the rate limiter."""
import time
import pytest
from datetime import timedelta

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


def test_rate_limiter_allow_and_try_after():
    rl = RateLimiter(limit=2, period=timedelta(seconds=0.2))
    key = "client-ip"
    assert rl.allow(key) is True
    assert rl.allow(key) is True
    # Third hit within window should be throttled
    assert rl.allow(key) is False
    wait = rl.try_after(key)
    assert wait.total_seconds() > 0
    # After the period passes, it's allowed again
    time.sleep(0.3)
    assert rl.allow(key) is True
