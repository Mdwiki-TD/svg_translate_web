"""Helpers for loading the current authenticated user."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

FuncType = TypeVar("FuncType", bound=Callable[..., Any])
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CurrentUser:
    """Lightweight representation of the authenticated user."""

    user_id: str
    username: str

class UserService:
    ...

__all__ = [
    "UserService",
    "CurrentUser",
]
