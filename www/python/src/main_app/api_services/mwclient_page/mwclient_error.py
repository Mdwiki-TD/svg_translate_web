""" """

from __future__ import annotations

import logging
from typing import Any

import mwclient
import mwclient.errors

logger = logging.getLogger(__name__)


def handle_mwclient_error(exc: Exception) -> dict[str, Any] | None:
    """Map common mwclient exceptions to a failure dict.

    Returns a ``{"success": False, ...}`` dict for known errors, or
    ``None`` if the exception is unrecognised (caller should log and
    handle it themselves).
    """
    code = getattr(exc, "code", None)
    info = getattr(exc, "info", None)

    if isinstance(exc, mwclient.errors.ProtectedPageError):
        return {"success": False, "error": "protectedpageerror", "details": f"code: {code}, info: {info}"}

    if isinstance(exc, mwclient.errors.EditError):
        return {"success": False, "error": "editerror", "details": str(exc)}

    if isinstance(exc, mwclient.errors.AssertUserFailedError):
        return {"success": False, "error": "assertuserfailed"}

    if isinstance(exc, mwclient.errors.UserBlocked):
        return {"success": False, "error": "userblocked"}

    if isinstance(exc, mwclient.errors.APIError):
        if code == "ratelimited":
            return {"success": False, "error": "ratelimited"}
        return {"success": False, "error": code, "details": str(exc)}

    return None  # unrecognised — let the caller log and handle


__all__ = [
    "handle_mwclient_error",
]
