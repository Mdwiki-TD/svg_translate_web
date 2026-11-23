from __future__ import annotations

import logging

from .http_client import HttpClient
from .objects import RawGrapherMetadataResponse

logger = logging.getLogger(__name__)

METADATA_URL = "https://ourworldindata.org/grapher/{slug}.metadata.json"
INDICATORS_METADATA_URL = "https://api.ourworldindata.org/v1/indicators/{variable_id}.metadata.json"

# Seconds to wait for each HTTP request
REQUEST_TIMEOUT = 15


class OwidClient:
    """Client for fetching metadata from Our World in Data endpoints."""

    def __init__(
        self,
        http_client: HttpClient | None = None,
        timeout: float = REQUEST_TIMEOUT,
    ) -> None:
        # Resolve the HTTP client once so tests and callers can inject a custom client.
        self.timeout = timeout
        self.http_client = http_client or HttpClient(use_session=True, default_timeout=self.timeout)

    def _get_metadata(self, url: str, identifier: str | int) -> RawGrapherMetadataResponse:
        """Fetch JSON metadata from a given URL and normalize errors into a response object."""
        try:
            response = self.http_client.get(url)
            if response.status_code == 200:
                return RawGrapherMetadataResponse(data=response.json(), status_code=response.status_code)
            return RawGrapherMetadataResponse(data=None, status_code=response.status_code)
        except Exception as exc:
            logger.warning("Failed to fetch metadata for %s: %s", identifier, exc)
            return RawGrapherMetadataResponse(data=None, status_code=None)

    def fetch_grapher_metadata_raw(self, slug: str) -> RawGrapherMetadataResponse:
        """Fetch the OWID chart metadata JSON. Returns a dataclass with raw dict and status code."""
        url = METADATA_URL.format(slug=slug)
        return self._get_metadata(url, slug)

    def fetch_indicators_metadata(self, owid_variable_id: int) -> RawGrapherMetadataResponse:
        """Fetch the OWID indicator metadata JSON. Returns a dataclass with raw dict and status code."""
        url = INDICATORS_METADATA_URL.format(variable_id=owid_variable_id)
        return self._get_metadata(url, owid_variable_id)


__all__ = [
    "OwidClient",
]
