""" """

import functools
import os
import uuid

import mwclient
import pytest
from mwclient.client import Site

# ---------------------------------------------------------------------------
# Shared site factory – one connection per domain per session
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=10)
def shared_site_resource(domain: str) -> Site:
    """Return a cached (anonymous) Site for *domain*."""
    return Site(
        domain,
        scheme="https",
        clients_useragent="MwClientPageNetworkTests/1.0",
        force_login=False,
    )


@functools.lru_cache(maxsize=2)
def authenticated_site(domain: str) -> Site | None:
    """Return a cached authenticated site, or None if credentials are absent."""
    username = os.getenv("MW_TEST_USERNAME")
    password = os.getenv("MW_TEST_PASSWORD")
    if not (username and password):
        return None
    site = Site(
        domain,
        scheme="https",
        clients_useragent="MwClientPageNetworkTests/1.0",
    )
    site.login(username, password)
    return site


# ---------------------------------------------------------------------------
# Base mix-in that provides .site and .test_site
# ---------------------------------------------------------------------------


class TestNetwork:
    """Provides .site (commons, read-only) and .test_site (test wiki, writes)."""

    @property
    def site(self) -> Site:
        return shared_site_resource("commons.wikimedia.org")

    @property
    def test_site(self) -> Site | None:
        return shared_site_resource("test.wikipedia.org")

    @property
    def test_auth_site(self) -> Site | None:
        """Authenticated site for test.wikipedia.org, or None if not configured."""
        return authenticated_site("test.wikipedia.org")

    # Helper ------------------------------------------------------------------

    def _require_test_site(self) -> Site:
        """Skip the test if write credentials are unavailable."""
        site = self.test_auth_site
        if site is None:
            pytest.skip(
                "Write tests require MW_TEST_USERNAME and MW_TEST_PASSWORD "
                "environment variables pointing to a test.wikipedia.org bot account."
            )
        return site

    @staticmethod
    def _unique_title(prefix: str = "NetworkTest") -> str:
        """Return a title that is highly unlikely to already exist."""
        uid = uuid.uuid4().hex[:12]
        # return f"User:MwClientPageTest/{prefix}-{uid}"
        return f"MwClientPageTest/{prefix}-{uid}"
