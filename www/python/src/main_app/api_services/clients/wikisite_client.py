"""Helpers for creating OAuth-authenticated MediaWiki clients."""

from __future__ import annotations

import logging
import os
from typing import Any

import requests
from mwclient.client import Site

from ...config import get_settings
from ...services.core.crypto import CryptoService

logger = logging.getLogger(__name__)


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


class WikiSiteClient:
    """Helper for creating OAuth-authenticated MediaWiki clients."""

    @staticmethod
    def _get_user_site(wiki_domain: str, user: dict[str, Any] | None) -> Site | None:
        if user is None:
            return None
        app_settings = get_settings()

        if not app_settings.oauth:
            logger.warning("MediaWiki OAuth consumer not configured")
            return None

        access_token = coerce_encrypted(user.get("access_token"))
        access_secret = coerce_encrypted(user.get("access_secret"))

        if not access_token or not access_secret:
            return None

        try:
            _access_key = CryptoService().decrypt(access_token)
            _access_secret = CryptoService().decrypt(access_secret)
            site = Site(
                wiki_domain,
                scheme="https",
                clients_useragent=app_settings.other.user_agent,
                consumer_token=app_settings.oauth.consumer_key,
                consumer_secret=app_settings.oauth.consumer_secret,
                access_token=_access_key,
                access_secret=_access_secret,
            )
        except requests.exceptions.ReadTimeout as exc:  # pragma: no cover - network interaction
            logger.error(f"Failed to build OAuth site, {str(exc)}")
            return None
        except requests.exceptions.ConnectionError:  # pragma: no cover - network interaction
            logger.error("Failed to build OAuth site, connection error")
            return None
        except Exception as exc:  # pragma: no cover - network interaction
            logger.exception("Failed to build OAuth site", exc_info=exc)
            return None
        return site

    @staticmethod
    def get_cronjob_site(domain: str | None = None) -> Site | None:
        app_settings = get_settings()

        if domain is None:
            domain = app_settings.other.wiki_domain

        try:
            site = Site(
                domain,
                scheme="https",
                clients_useragent=app_settings.other.user_agent,
                force_login=False,
            )
        except requests.exceptions.ReadTimeout as exc:  # pragma: no cover - network interaction
            logger.error(f"Failed to build OAuth site, {str(exc)}")
            return None
        except requests.exceptions.ConnectionError:  # pragma: no cover - network interaction
            logger.error("Failed to build OAuth site, connection error")
            return None
        except Exception as exc:  # pragma: no cover - network interaction
            logger.exception("Failed to build OAuth site", exc_info=exc)
            return None
        return site

    @classmethod
    def get_user_site(cls, wiki_domain: str, user: dict[str, Any] | None) -> Site | None:
        is_cron_job = os.getenv("CRON_JOB", "false").lower() == "true"
        if is_cron_job or (user and user.get("username") == "Background job"):
            return cls.get_cronjob_site(wiki_domain)

        return cls._get_user_site(wiki_domain, user)


__all__ = [
    "WikiSiteClient",
]
