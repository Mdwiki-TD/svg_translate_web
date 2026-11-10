"""
Unit tests for src.main_app.services.core.rate_limit.py module.
"""

from __future__ import annotations

import time
from datetime import timedelta
from unittest.mock import Mock

from src.main_app.services.core.rate_limit import (
    RateLimiter,
)

login_rate_limiter = RateLimiter.login_rate_limiter()
callback_rate_limiter = RateLimiter.callback_rate_limiter()


class TestClientKey:
    def test_uses_forwarded_for(self):
        mock_req = Mock()
        mock_req.headers.get.return_value = "1.2.3.4, 5.6.7.8"
        mock_req.remote_addr = "9.10.11.12"

        assert RateLimiter.client_key(mock_req) == "1.2.3.4"

    def test_falls_back_to_remote_addr(self):
        mock_req = Mock()
        mock_req.headers.get.return_value = None
        mock_req.remote_addr = "1.2.3.4"

        assert RateLimiter.client_key(mock_req) == "1.2.3.4"

    def test_falls_back_to_anonymous(self):
        mock_req = Mock()
        mock_req.headers.get.return_value = None
        mock_req.remote_addr = None

        assert RateLimiter.client_key(mock_req) == "anonymous"


class TestRateLimiterInit:
    """Tests for RateLimiter initialization."""

    def test_initializes_with_limit_and_period(self):
        """Test that rate limiter initializes with given limit and period."""
        limiter = RateLimiter(limit=5, period=timedelta(minutes=1))
        assert limiter._limit == 5
        assert limiter._period == timedelta(minutes=1)

    def test_initializes_empty_hits_dict(self):
        """Test that hits dictionary starts empty."""
        limiter = RateLimiter(limit=5, period=timedelta(minutes=1))
        assert limiter._hits == {}

    def test_initializes_with_different_values(self):
        """Test initialization with various values."""
        limiter = RateLimiter(limit=100, period=timedelta(hours=1))
        assert limiter._limit == 100
        assert limiter._period == timedelta(hours=1)


class TestRateLimiterAllow:
    """Tests for RateLimiter.allow method."""

    def test_allows_first_request(self):
        """Test that first request is always allowed."""
        limiter = RateLimiter(limit=5, period=timedelta(minutes=1))
        assert limiter.allow("user1") is True

    def test_allows_requests_up_to_limit(self):
        """Test that requests up to the limit are allowed."""
        limiter = RateLimiter(limit=3, period=timedelta(minutes=1))

        # All requests within limit should be allowed
        assert limiter.allow("user1") is True  # 1/3
        assert limiter.allow("user1") is True  # 2/3
        assert limiter.allow("user1") is True  # 3/3

    def test_blocks_requests_beyond_limit(self):
        """Test that requests beyond the limit are blocked."""
        limiter = RateLimiter(limit=2, period=timedelta(minutes=1))

        # First 2 requests allowed
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is True

        # 3rd request blocked
        assert limiter.allow("user1") is False

    def test_tracks_different_keys_separately(self):
        """Test that different keys are tracked separately."""
        limiter = RateLimiter(limit=2, period=timedelta(minutes=1))

        # User1 makes 2 requests
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is False  # Blocked

        # User2 has their own limit
        assert limiter.allow("user2") is True
        assert limiter.allow("user2") is True
        assert limiter.allow("user2") is False  # Blocked

    def test_old_requests_expire_after_period(self):
        """Test that old requests expire after the period."""
        limiter = RateLimiter(limit=2, period=timedelta(milliseconds=50))

        # Make 2 requests
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is False  # Blocked

        # Wait for period to expire

        time.sleep(0.06)  # Wait slightly more than 50ms

        # Now should be allowed again
        assert limiter.allow("user1") is True

    def test_mixed_allow_and_block(self):
        """Test mixed allowed and blocked requests."""
        limiter = RateLimiter(limit=3, period=timedelta(minutes=1))

        assert limiter.allow("user1") is True  # 1
        assert limiter.allow("user1") is True  # 2
        assert limiter.allow("user1") is True  # 3
        assert limiter.allow("user1") is False  # blocked
        assert limiter.allow("user1") is False  # still blocked
        assert limiter.allow("user1") is False  # still blocked

    def test_allow_updates_hit_count(self):
        """Test that allow method properly tracks hit count."""
        limiter = RateLimiter(limit=5, period=timedelta(minutes=1))

        limiter.allow("user1")
        limiter.allow("user1")

        # Check internal state (through the hits deque length)
        assert len(limiter._hits["user1"]) == 2


class TestRateLimiterTryAfter:
    """Tests for RateLimiter.try_after method."""

    def test_returns_zero_when_allowed(self):
        """Test that try_after returns zero when request would be allowed."""
        limiter = RateLimiter(limit=5, period=timedelta(minutes=1))

        # No requests made yet
        assert limiter.try_after("user1") == timedelta(0)

        # Make a request
        limiter.allow("user1")
        # Still within limit
        assert limiter.try_after("user1") == timedelta(0)

    def test_returns_positive_time_when_blocked(self):
        """Test that try_after returns positive time when blocked."""
        limiter = RateLimiter(limit=1, period=timedelta(milliseconds=100))

        # Make request to hit limit
        limiter.allow("user1")

        # Should return positive time
        wait_time = limiter.try_after("user1")
        assert wait_time > timedelta(0)
        assert wait_time <= timedelta(milliseconds=100)

    def test_returns_zero_for_unknown_key(self):
        """Test that try_after returns zero for unknown key."""
        limiter = RateLimiter(limit=5, period=timedelta(minutes=1))

        assert limiter.try_after("unknown_user") == timedelta(0)

    def test_try_after_updates_expired_hits(self):
        """Test that try_after also cleans up expired hits."""
        limiter = RateLimiter(limit=1, period=timedelta(milliseconds=50))

        # Make request
        limiter.allow("user1")

        # Wait for expiration

        time.sleep(0.06)

        # Should return zero after expiration
        assert limiter.try_after("user1") == timedelta(0)


class TestRateLimiterExpiration:
    """Tests for hit expiration behavior."""

    def test_expired_hits_removed_on_allow(self):
        """Test that expired hits are removed when checking allow."""
        limiter = RateLimiter(limit=2, period=timedelta(milliseconds=50))

        # Make 2 requests
        limiter.allow("user1")
        limiter.allow("user1")

        # Wait for expiration

        time.sleep(0.06)

        # Make another request - should clean up old hits and allow
        assert limiter.allow("user1") is True
        # Should only have 1 hit now (the new one)
        assert len(limiter._hits["user1"]) == 1

    def test_partial_expiration(self):
        """Test partial expiration of hits."""
        limiter = RateLimiter(limit=3, period=timedelta(milliseconds=100))

        # Make 2 requests
        limiter.allow("user1")

        time.sleep(0.05)  # Wait half the period
        limiter.allow("user1")  # 2nd request

        # First request should still be in window, second definitely is
        # Both should count towards limit
        assert limiter.allow("user1") is True  # 3rd request
        assert limiter.allow("user1") is False  # Blocked - at limit


class TestGlobalRateLimiters:
    """Tests for global rate limiter instances."""

    def test_login_rate_limiter_exists(self):
        """Test that login_rate_limiter exists and is a RateLimiter."""
        assert isinstance(login_rate_limiter, RateLimiter)

    def test_login_rate_limiter_config(self):
        """Test login rate limiter configuration."""
        assert login_rate_limiter._limit == 5
        assert login_rate_limiter._period == timedelta(minutes=1)

    def test_callback_rate_limiter_exists(self):
        """Test that callback_rate_limiter exists and is a RateLimiter."""
        assert isinstance(callback_rate_limiter, RateLimiter)

    def test_callback_rate_limiter_config(self):
        """Test callback rate limiter configuration."""
        assert callback_rate_limiter._limit == 10
        assert callback_rate_limiter._period == timedelta(minutes=1)

    def test_global_limiters_are_separate_instances(self):
        """Test that global limiters are separate instances."""
        assert login_rate_limiter is not callback_rate_limiter

    def test_global_limiters_track_separately(self):
        """Test that global limiters track different keys separately."""
        # Use the same key on both limiters
        key = "test_user"

        # Exhaust login limiter
        for _ in range(5):
            assert login_rate_limiter.allow(key) is True
        assert login_rate_limiter.allow(key) is False

        # Callback limiter should still allow (different limit)
        assert callback_rate_limiter.allow(key) is True


class TestRateLimiterThreadSafety:
    """Tests for thread safety of RateLimiter."""

    def test_lock_initialization(self):
        """Test that RateLimiter initializes with a lock."""
        limiter = RateLimiter(limit=5, period=timedelta(minutes=1))
        assert hasattr(limiter, "_lock")
        assert limiter._lock is not None

    def test_concurrent_access(self):
        """Test that concurrent access doesn't corrupt state."""
        import threading

        limiter = RateLimiter(limit=100, period=timedelta(minutes=1))
        results = []

        def make_requests():
            for _ in range(10):
                results.append(limiter.allow("shared_key"))
                time.sleep(0.001)

        threads = [threading.Thread(target=make_requests) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All 50 requests should have succeeded (under limit)
        assert all(results)
        assert len(results) == 50


class TestRateLimiterEdgeCases:
    """Tests for edge cases."""

    def test_limit_of_one(self):
        """Test rate limiter with limit of 1."""
        limiter = RateLimiter(limit=1, period=timedelta(minutes=1))

        assert limiter.allow("user1") is True
        assert limiter.allow("user1") is False

    def test_very_short_period(self):
        """Test rate limiter with very short period."""
        limiter = RateLimiter(limit=2, period=timedelta(microseconds=1))

        assert limiter.allow("user1") is True

        time.sleep(0.001)  # Wait for period to pass
        assert limiter.allow("user1") is True  # Should be allowed after expiration

    def test_empty_key(self):
        """Test rate limiter with empty string key."""
        limiter = RateLimiter(limit=2, period=timedelta(minutes=1))

        assert limiter.allow("") is True
        assert limiter.allow("") is True
        assert limiter.allow("") is False

    def test_special_characters_in_key(self):
        """Test rate limiter with special characters in key."""
        limiter = RateLimiter(limit=2, period=timedelta(minutes=1))

        special_keys = ["user@domain.com", "user:123", "user/key", "user key"]

        for key in special_keys:
            assert limiter.allow(key) is True
            assert limiter.allow(key) is True
            assert limiter.allow(key) is False
