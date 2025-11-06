"""
Tests for the RateLimiter class.
"""
from datetime import timedelta
import time

from src.app.app_routes.auth.rate_limit import RateLimiter


def test_ratelimiter_allow():
    """
    Tests that the rate limiter allows requests within the limit.
    """
    limiter = RateLimiter(limit=3, period=timedelta(seconds=1))
    assert limiter.allow("key1")
    assert limiter.allow("key1")
    assert limiter.allow("key1")


def test_ratelimiter_deny():
    """
    Tests that the rate limiter denies requests exceeding the limit.
    """
    limiter = RateLimiter(limit=2, period=timedelta(seconds=1))
    assert limiter.allow("key1")
    assert limiter.allow("key1")
    assert not limiter.allow("key1")


def test_ratelimiter_reset():
    """
    Tests that the rate limit resets after the period.
    """
    limiter = RateLimiter(limit=1, period=timedelta(seconds=1))
    assert limiter.allow("key1")
    assert not limiter.allow("key1")
    time.sleep(1.1)
    assert limiter.allow("key1")


def test_ratelimiter_try_after():
    """
    Tests that try_after returns the correct time delta.
    """
    limiter = RateLimiter(limit=1, period=timedelta(seconds=2))
    assert limiter.allow("key1")
    time_left = limiter.try_after("key1")
    assert time_left.total_seconds() > 0
    assert time_left.total_seconds() <= 2


def test_ratelimiter_multiple_keys():
    """
    Tests that the rate limiter handles multiple keys independently.
    """
    limiter = RateLimiter(limit=1, period=timedelta(seconds=1))
    assert limiter.allow("key1")
    assert not limiter.allow("key1")
    assert limiter.allow("key2")
    assert not limiter.allow("key2")
