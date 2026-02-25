"""Helpers for creating OAuth-authenticated MediaWiki clients."""

from __future__ import annotations
from typing import Dict, Any

import mwclient
import logging
from ..config import settings
from ..crypto import decrypt_value

logger = logging.getLogger(__name__)


def _build_site(access_key: str, access_secret: str) -> mwclient.Site:
    if not settings.oauth:
        raise RuntimeError("MediaWiki OAuth consumer not configured")

    return mwclient.Site(
        settings.oauth.upload_host,
        scheme="https",
        clients_useragent=settings.oauth.user_agent,
        consumer_token=settings.oauth.consumer_key,
        consumer_secret=settings.oauth.consumer_secret,
        access_token=access_key,
        access_secret=access_secret,
    )


def build_upload_site(access_token: bytes, access_secret: bytes) -> mwclient.Site:
    access_key = decrypt_value(access_token)
    access_secret = decrypt_value(access_secret)
    return _build_site(access_key, access_secret)


def coerce_encrypted(value: object) -> bytes | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, memoryview):
        return value.tobytes()
    if isinstance(value, str):
        return value.encode("utf-8")
    return None


def get_user_site(user: Dict[str, Any]) -> mwclient.Site | None:
    access_token = coerce_encrypted(user.get("access_token"))
    access_secret = coerce_encrypted(user.get("access_secret"))

    if not access_token or not access_secret:
        return None
    try:
        site = build_upload_site(access_token, access_secret)
    except Exception as exc:  # pragma: no cover - network interaction
        logger.exception("Failed to build OAuth site", exc_info=exc)
        return None
    return site
