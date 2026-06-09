from __future__ import annotations

import logging

from .mwclient_error import handle_mwclient_error
from .mwclient_wraper import MwClientPage

logger = logging.getLogger(__name__)

__all__ = [
    "MwClientPage",
    "handle_mwclient_error",
]
