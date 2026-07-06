""" """

from __future__ import annotations

import logging
import threading
from typing import Any

import requests

from ...config import settings

logger = logging.getLogger(__name__)

METADATA_URL = "https://ourworldindata.org/grapher/{slug}.metadata.json"
INDICATORS_METADATA_URL = "https://api.ourworldindata.org/v1/indicators/{variable_id}.metadata.json"

# Seconds to wait for each HTTP request
REQUEST_TIMEOUT = 15


_thread_local = threading.local()


def _build_session() -> requests.Session:
    if not hasattr(_thread_local, "session"):
        session = requests.Session()
        session.headers.update({"User-Agent": settings.other.user_agent})
        _thread_local.session = session
    return _thread_local.session


def _fetch_grapher_metadata(slug: str) -> Any:
    """Fetch the OWID chart metadata JSON. Returns the parsed dict or None."""
    session = _build_session()
    url = METADATA_URL.format(slug=slug)
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        return response.json(), response.status_code

    except Exception as exc:
        logger.warning(f"Failed to fetch metadata for '{slug}': {exc}")
        return None, None


def fetch_grapher_metadata(slug: str) -> dict | None:
    """Fetch the OWID chart metadata JSON. Returns the parsed dict or None."""
    session = _build_session()
    url = METADATA_URL.format(slug=slug)
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        # If successful, return the text content immediately
        if response.status_code == 200:
            return response.json()

        response.raise_for_status()
        return response.json()

    except Exception as exc:
        logger.warning(f"Failed to fetch metadata for '{slug}': {exc}")
        return None


def fetch_indicators_metadata(owid_variable_id: int) -> dict | None:
    """Fetch the OWID indicator metadata JSON. Returns the parsed dict or None."""
    session = _build_session()
    url = INDICATORS_METADATA_URL.format(variable_id=owid_variable_id)
    try:
        resp = session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning(f"Failed to fetch metadata for '{owid_variable_id}': {exc}")
        return None


__all__ = [
    "fetch_grapher_metadata",
    "_fetch_grapher_metadata",
    "fetch_indicators_metadata",
]
