""" """

import functools

import mwclient
import pytest

from src.main_app.api_services.clients import get_cronjob_site


@functools.lru_cache(maxsize=10)
def shared_site_resource(domain: str) -> mwclient.Site:
    # This runs only once when the file starts
    return get_cronjob_site(domain=domain)


class TestNetwork:

    @property
    def site(self):
        return shared_site_resource("commons.wikimedia.org")

    @property
    def test_site(self):
        return shared_site_resource("test-commons.wikimedia.org")
