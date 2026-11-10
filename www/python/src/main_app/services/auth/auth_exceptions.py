from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

IDENTITY_ERROR_MESSAGE = "We couldn't verify your MediaWiki identity. Please try again."


class OAuthCallbackError(Exception):
    """Raised when a step of the OAuth callback fails."""

    def __init__(self, message: str, *, flash_category: str = "danger") -> None:
        super().__init__(message)
        self.flash_category = flash_category


class OAuthIdentityError(Exception):
    """Raised when MediaWiki OAuth identity verification fails."""

    def __init__(
        self,
        message: str,
        *,
        original_exception: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.original_exception = original_exception


__all__ = [
    "OAuthCallbackError",
    "OAuthIdentityError",
]
