"""Low-level Wikimedia Commons download utilities.

This module provides the core HTTP download functionality for fetching
files from Wikimedia Commons. It serves as the foundation for higher-level
download functions used across the application.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from .objects import GetWithRetryData

logger = logging.getLogger(__name__)

# Define API endpoint and parameters
COMMONS_API_ENDPOINT = "https://commons.wikimedia.org/w/api.php"

def create_commons_session(user_agent: str | None = None) -> requests.Session:
    """Create a pre-configured requests Session for Commons API calls.

    Args:
        user_agent: Optional custom User-Agent string. If not provided,
            defaults to a generic bot identifier.

    Returns:
        Configured requests Session ready for use.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": user_agent or "SVGTranslateBot/1.0",
        }
    )
    return session


class CommonsSession:
    def __init__(
        self,
        session: requests.Session | None = None,
        user_agent: str | None = None,
        timeout: int = 60,
    ) -> None:
        self.session = session or create_commons_session(user_agent)
        self.timeout = timeout

    def get(self, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.request("GET", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def post(self, data: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.request("POST", data=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise

    def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        url: str | None = COMMONS_API_ENDPOINT,
    ) -> requests.Response:
        """Perform a request to the Commons API.

        Args:
            params: Parameters to pass to the Commons API.
            session: Pre-configured requests Session with appropriate headers
                (User-Agent, etc.).
        Returns:
            Response from the Commons API.
        """
        if url is None:
            url = COMMONS_API_ENDPOINT

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            timeout=self.timeout,
            allow_redirects=True,
        )
        return response

    def get_with_retry_obj(
        self,
        url: str,
        max_attempts: int = 5,
    ) -> GetWithRetryData:
        """
        Get a URL with retry logic for handling rate limiting and network errors.
        """
        wait_time = 0
        attempts = 0
        while attempts < max_attempts:
            try:
                response = self.request(method="GET", url=url)

                # If successful, return the text content immediately
                if response.status_code == 200:
                    return GetWithRetryData(
                        content=response.content,
                        success=True,
                        status_code=200,
                        attempts=attempts,
                    )

                # If 404, return None
                elif response.status_code == 404:
                    return GetWithRetryData(
                        content=None,
                        success=False,
                        status_code=404,
                        attempts=attempts,
                        msg="Not found",
                    )

                # Handle Rate Limiting (Error 429)
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    try:
                        wait_time = int(retry_after) if retry_after else 5
                    except ValueError:
                        wait_time = 5

                    logger.error(
                        f"Hit 429 (Rate Limit). Attempt {attempts + 1}/{max_attempts}. Waiting {wait_time}s..."
                    )

                    if wait_time > 10:
                        logger.error(f"wait time {wait_time} > 10")
                        return GetWithRetryData(
                            content=None,
                            success=False,
                            status_code=429,
                            wait_time=wait_time,
                            attempts=attempts,
                            msg=f"Hit 429 (Rate Limit). wait time: {wait_time}s",
                        )

                    time.sleep(wait_time)

                # Handle other HTTP errors (e.g., 500, 503)
                else:
                    response.raise_for_status()

            except requests.RequestException as e:
                # Handle network failures, timeouts, etc.
                logger.error(f"Connection error on attempt {attempts + 1}/{max_attempts}: {e}. Retrying in 2s...")
                time.sleep(2)

            attempts += 1

        # raise if all 5 attempts failed
        return GetWithRetryData(
            content=None,
            success=False,
            # status_code=429,
            wait_time=wait_time,
            attempts=attempts,
        )

    def get_with_retry(
        self,
        url: str,
        max_attempts: int = 5,
    ) -> requests.Response | None:
        """
        Get a URL with retry logic for handling rate limiting and network errors.
        """
        result = self.get_with_retry_obj(url, max_attempts)
        return result.content if result.success else None


__all__ = [
    "CommonsSession",
    "create_commons_session",
]
