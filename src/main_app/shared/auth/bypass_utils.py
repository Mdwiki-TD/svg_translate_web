"""
Utilities for authentication bypasses.
"""

from __future__ import annotations

from flask import current_app


def is_coordinator_bypass_enabled() -> bool:
    """
    Check if the coordinator authorization bypass is enabled.

    This bypass exists only for local development and automated UI/E2E testing.
    It must not be used as a production authorization mechanism.
    """
    return current_app.config.get("ENV") == "development" and current_app.config.get(
        "UI_TEST_BYPASS_COORDINATOR_CHECK",
        False,
    )


__all__ = ["is_coordinator_bypass_enabled"]
