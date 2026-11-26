from __future__ import annotations

import logging

from .mwclient_error import handle_mwclient_error
from .mwclient_wraper import _RETRY_DELAYS, EditPageResult, MovePageResult, MwClientPage

logger = logging.getLogger(__name__)

__all__ = [
    "EditPageResult",
    "MovePageResult",
    "MwClientPage",
    "handle_mwclient_error",
    "_RETRY_DELAYS",
]
