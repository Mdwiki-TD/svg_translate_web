""" """

import functools

import mwclient
import pytest


@functools.lru_cache(maxsize=10)
def shared_site_resource(domain: str) -> mwclient.Site:
    # This runs only once when the file starts
    return mwclient.Site(
        domain,
        scheme="https",
        clients_useragent="TestClient/1.0",
        force_login=False,
    )


class TestNetwork:

    @property
    def site(self):
        return shared_site_resource("commons.wikimedia.org")

    @property
    def test_site(self):
        return shared_site_resource("test-commons.wikimedia.org")
