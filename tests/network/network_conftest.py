""" """

import functools

import pytest

from src.main_app.api_services.clients import get_cronjob_site


@functools.lru_cache(maxsize=1)
def shared_site_resource():
    # This runs only once when the file starts
    return get_cronjob_site()


class TestNetwork:

    @property
    def site(self):
        return shared_site_resource()
