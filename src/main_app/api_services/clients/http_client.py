"""HTTP client service for unified web requests."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)


class HttpClient:
    """HTTP client wrapper providing standardized methods for HTTP requests.

    - ``get`` / ``post`` / ``request`` return a raw ``requests.Response``.
    - ``safe_request`` never raises and returns a result dict with
      ``output``, ``error``, ``error_code`` and ``http_code``.

    When ``use_session=True`` a single ``requests.Session`` is created and
    reused for every request (connection pooling, persistent cookies).
    Call :meth:`close` when done, or use the client as a context manager.
    """

    def __init__(
        self,
        default_timeout: float = 30.0,
        user_agent: str | None = None,
        use_session: bool = False,
        session: requests.Session | None = None,
    ) -> None:
        self.default_timeout = default_timeout
        self.user_agent = user_agent or self._user_agent
        self.use_session = use_session
        self._session: requests.Session | None = session or (requests.Session() if use_session else None)

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------
    @property
    def session(self) -> requests.Session | None:
        """The underlying ``requests.Session`` (``None`` if not used)."""
        return self._session

    def close(self) -> None:
        """Close the session (if any). Safe to call multiple times."""
        if self._session is not None:
            self._session.close()
            self._session = None

    def __enter__(self) -> HttpClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @property
    def _user_agent(self) -> str:
        user_agent = os.getenv(
            "USER_AGENT",
            "Translation Dashboard/1.0 (https://mdwiki.toolforge.org/; tools.mdwiki@toolforge.org)",
        )
        return user_agent

    def _prepare_headers(self, headers: dict[str, str] | None) -> dict[str, str]:
        req_headers = dict(headers) if headers is not None else {}
        if not any(key.lower() == "user-agent" for key in req_headers):
            req_headers["User-Agent"] = self.user_agent
        return req_headers

    def _send(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None,
        timeout: float | None,
        **kwargs: Any,
    ) -> requests.Response:
        """Single place where every request is actually sent."""
        # Reuse the session when enabled, otherwise fall back to one-off requests.
        sender = self._session.request if self._session is not None else requests.request
        return sender(
            method=method.upper(),
            url=url,
            headers=self._prepare_headers(headers),
            timeout=timeout if timeout is not None else self.default_timeout,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Raw-response API
    # ------------------------------------------------------------------
    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: Any = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Perform an HTTP GET request."""
        return self._send(
            "GET",
            url,
            headers,
            timeout,
            params=params,
            auth=auth,
            **kwargs,
        )

    def post(
        self,
        url: str,
        data: Any = None,
        json: Any = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: Any = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Perform an HTTP POST request."""
        return self._send(
            "POST",
            url,
            headers,
            timeout,
            data=data,
            json=json,
            params=params,
            auth=auth,
            **kwargs,
        )

    def request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        auth: Any = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> requests.Response:
        """Perform a generic HTTP request."""
        json_payload = kwargs.pop("json", json_data)
        return self._send(
            method,
            url,
            headers,
            timeout,
            params=params,
            data=data,
            json=json_payload,
            auth=auth,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Safe (dict-result) API
    # ------------------------------------------------------------------
    def safe_request(
        self,
        url: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        """Perform a request without raising; return a result dict.

        Keys: ``output`` (body on HTTP 200), ``error``, ``error_code``, ``http_code``.
        """
        result: dict[str, Any] = {
            "output": "",
            "error": "",
            "error_code": "",
            "http_code": 0,
        }

        try:
            response = self.request(
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json_data=json_data,
                headers=headers,
                timeout=timeout,
            )
        except requests.Timeout:
            result["error"] = "Request timed out"
            result["error_code"] = "TIMEOUT"
            logger.error("Timeout while requesting: %s", url)
            return result
        except Exception as exc:
            result["error"] = str(exc)
            result["error_code"] = "REQUEST_ERROR"
            logger.error("Request failed for %s: %s", url, exc)
            return result

        result["http_code"] = response.status_code

        if response.status_code != 200:
            logger.error("HttpClient: API returned HTTP %s for %s", response.status_code, url)
            result["error"] = "HTTP_ERROR"
            result["error_code"] = str(response.status_code)

            # check Cloudflare protection
            if "Just a moment..." in response.text:
                logger.error("Cloudflare protection detected for %s", url)
                result["error"] = "CLOUDFLARE_PROTECTION"
            else:
                logger.error(repr(response.text))

            return result

        result["output"] = response.text
        return result

    def get_url_json(self, url: str) -> dict | None:
        """Fetch URL content and parse as JSON.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            Parsed JSON as dictionary, None on error
        """
        try:
            response = self.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.debug(f"Request Error: {e}\n{url}")
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"JSON Decode Error: {e}\n{url}")
        return None


__all__ = [
    "HttpClient",
]
