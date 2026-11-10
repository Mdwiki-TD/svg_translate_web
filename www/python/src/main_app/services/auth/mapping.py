""" """

from __future__ import annotations

import logging
from dataclasses import dataclass

from werkzeug.wrappers import Response as WerkzeugResponse

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoginStartResult:
    """Outcome of starting the OAuth login flow."""

    success: bool
    redirect_url: str | None = None
    error_message: str | None = None
    flash_category: str = "danger"


@dataclass(frozen=True)
class CallbackResult:
    """Outcome of completing the OAuth callback."""

    success: bool
    response: WerkzeugResponse | None = None
    error_message: str | None = None
    flash_category: str = "danger"


@dataclass(frozen=True)
class LogoutResult:
    """Outcome of logout."""

    response: WerkzeugResponse
    message: str
    flash_category: str = "info"


__all__ = [
    "CallbackResult",
    "LoginStartResult",
    "LogoutResult",
]
