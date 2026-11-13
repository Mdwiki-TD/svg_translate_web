"""Base client for the Toolforge API. Flask-free.

Handles the parts shared by every API route (jobs, builds, components,
envvars, logs): internal/external mode, authentication, URL building and
token redaction. Route-specific clients subclass ToolforgeApiService.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote, quote_plus, urlencode

import requests

from .http_client import HttpClient

logger = logging.getLogger(__name__)

API_URL = "https://api.svc.tools.eqiad1.wikimedia.cloud:30003"  # inside toolforge environment

EXTERNAL_API_URL = "https://api.svc.toolforge.org"  # external endpoint

TOKEN_ENV = "TOOLS_DEPLOY_TOKEN"

REQUEST_TIMEOUT = 15  # seconds

API_ROUTES = Literal["builds", "components", "envvars", "jobs", "logs"]

# These routes expose their metrics without the version segment (/<route>/metrics).
_UNVERSIONED_METRICS = {"components", "logs"}


class ToolforgeApiService:
    """Thin client for the Toolforge API.

    Two modes are supported:
    - internal: inside Toolforge, authenticated with the client certificate.
    - external: from anywhere else, authenticated with ``?token=$TOOLS_DEPLOY_TOKEN``.

    Note: in external mode the token is part of the request URL, so do not log
    ``response.url``; use ``redact()`` on any text that may contain it.
    """

    def __init__(
        self,
        api_route: API_ROUTES,
        tool_name: str | None = None,
        home_dir: str | None = None,
        verify: bool | None = None,
        timeout: int | None = None,
        http_client: HttpClient | None = None,
        token: str | None = None,
        internal: bool | None = None,
    ) -> None:
        self.http_client = http_client or HttpClient()
        self.tool_name = tool_name or os.environ.get("TOOL_NAME", "mdw")
        self.home_dir = home_dir or str(Path.home())
        self.token = token or os.environ.get(TOKEN_ENV, "")
        # Without a deploy token we assume we run inside Toolforge.
        self.internal = internal if internal is not None else not self.token
        self.api_url = API_URL if self.internal else EXTERNAL_API_URL
        # The internal cert is self-signed (internal to k8s); the external one is valid.
        self.verify = verify if verify is not None else not self.internal
        self.timeout = timeout or REQUEST_TIMEOUT
        self.api_route: API_ROUTES = api_route

    # ------------------------------------------------------------------
    # URL / auth helpers
    # ------------------------------------------------------------------

    @property
    def client_cert(self) -> tuple[str, str]:
        """Return the (cert, key) paths used for client authentication."""
        base = f"{self.home_dir}/.toolskube"
        return f"{base}/client.crt", f"{base}/client.key"

    def build_url(self, path: str, params: dict[str, Any] | None = None) -> str:
        """Build the full URL, appending the deploy token in external mode."""
        query: dict[str, Any] = {}
        for key, value in (params or {}).items():
            if value is None:
                continue
            query[key] = str(value).lower() if isinstance(value, bool) else value
        if not self.internal:
            query["token"] = self.token
        url = f"{self.api_url}{path}"
        return f"{url}?{urlencode(query)}" if query else url

    def redact(self, text: str) -> str:
        """Hide the deploy token, which requests puts in error messages (it is in the URL)."""
        if not self.token:
            return text
        variants = {self.token, quote(self.token), quote(self.token, safe=""), quote_plus(self.token)}
        for variant in sorted(variants, key=len, reverse=True):
            text = text.replace(variant, "***")
        return text

    # ------------------------------------------------------------------
    # Low-level request
    # ------------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
        check: bool = True,
    ) -> requests.Response:
        """Send a request and return the raw response.

        With ``check=True`` (default) HTTP error statuses raise
        ``requests.HTTPError``; pass ``check=False`` to inspect them yourself.
        """
        if not self.internal and not self.token:
            raise ValueError(f"{TOKEN_ENV} is not set")

        kwargs: dict[str, Any] = {"verify": self.verify, "timeout": self.timeout}

        if self.internal:
            # The client certificate is only used by the internal endpoint.
            kwargs["cert"] = self.client_cert

        if json is not None:
            kwargs["json"] = json

        # Relies on HttpClient exposing get/post/put/patch/delete.
        response = self.http_client.request(
            method=method,
            url=self.build_url(path, params),
            **kwargs,
        )
        if check:
            response.raise_for_status()

        logger.debug("response status: %s", response.status_code)
        return response

    @staticmethod
    def _payload(response: requests.Response) -> Any:
        """Return the JSON body, falling back to text (or {} for an empty body)."""
        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError:
            return response.text

    def _tool_path(self, path: str = "") -> str:
        """Return the path of a tool-scoped endpoint (``path`` starts with '/')."""
        return f"/{self.api_route}/v1/tool/{quote(self.tool_name, safe='')}{path}"

    # ------------------------------------------------------------------
    # Endpoints shared by every route (not tool-scoped)
    # ------------------------------------------------------------------

    def healthcheck(self) -> Any:
        """GET /<route>/v1/healthz: service health check."""
        return self._payload(self.request("GET", f"/{self.api_route}/v1/healthz"))

    def metrics(self) -> str:
        """GET /<route>/v1/metrics: Prometheus metrics as plain text."""
        if self.api_route in _UNVERSIONED_METRICS:
            path = f"/{self.api_route}/metrics"
        else:
            path = f"/{self.api_route}/v1/metrics"
        return self.request("GET", path).text


__all__ = [
    "ToolforgeApiService",
]
