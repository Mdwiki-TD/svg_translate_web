"""Tests for category helpers."""

from __future__ import annotations

import pytest

from src.main_app.api_services import category


def test_get_category_members_api_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyResponse:
        def __init__(self, pages):
            self._pages = pages
            self.status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self):
            return self._pages

    class DummySession:
        def __init__(self) -> None:
            self.headers = {}
            self.calls = []

        def get(self, url, params=None, timeout=None):
            self.calls.append((url, params, timeout))
            if "cmcontinue" in params:
                return DummyResponse({"query": {"categorymembers": []}})
            return DummyResponse(
                {
                    "continue": {"cmcontinue": "next"},
                    "query": {"categorymembers": [{"title": "Page"}]},
                }
            )

    monkeypatch.setattr("src.main_app.api_services.category.requests.Session", DummySession)

    pages = category.get_category_members_api("Category:Example", "commons.wikimedia.org")

    assert pages == ["Page"]


def test_get_category_members_api_no_results(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_category_members_api with empty category."""

    class DummyResponse:
        def __init__(self):
            self.status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self):
            return {"query": {"categorymembers": []}}

    class DummySession:
        def __init__(self) -> None:
            self.headers = {}

        def get(self, url, params=None, timeout=None):
            return DummyResponse()

    monkeypatch.setattr("src.main_app.api_services.category.requests.Session", DummySession)

    pages = category.get_category_members_api("Category:Empty", "commons.wikimedia.org")

    assert pages == []


def test_get_category_members_api_request_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_category_members_api handles request exceptions."""

    class DummySession:
        def __init__(self) -> None:
            self.headers = {}

        def get(self, url, params=None, timeout=None):
            import requests

            raise requests.exceptions.RequestException("Network error")

    monkeypatch.setattr("src.main_app.api_services.category.requests.Session", DummySession)

    pages = category.get_category_members_api("Category:Example", "commons.wikimedia.org")

    assert pages == []


def test_get_category_members_api_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_category_members_api handles timeout."""

    class DummySession:
        def __init__(self) -> None:
            self.headers = {}

        def get(self, url, params=None, timeout=None):
            import requests

            raise requests.exceptions.Timeout("Request timed out")

    monkeypatch.setattr("src.main_app.api_services.category.requests.Session", DummySession)

    pages = category.get_category_members_api("Category:Example", "commons.wikimedia.org")

    assert pages == []


def test_get_category_members_api_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_category_members_api handles HTTP errors."""

    class DummyResponse:
        def __init__(self):
            self.status_code = 500

        def raise_for_status(self) -> None:
            import requests

            raise requests.exceptions.HTTPError("500 Server Error")

    class DummySession:
        def __init__(self) -> None:
            self.headers = {}

        def get(self, url, params=None, timeout=None):
            return DummyResponse()

    monkeypatch.setattr("src.main_app.api_services.category.requests.Session", DummySession)

    pages = category.get_category_members_api("Category:Example", "commons.wikimedia.org")

    assert pages == []


def test_get_category_members_api_multiple_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_category_members_api with multiple pages of results."""

    class DummyResponse:
        def __init__(self, pages, has_continue=False):
            self._pages = pages
            self._has_continue = has_continue
            self.status_code = 200

        def raise_for_status(self) -> None:
            return None

        def json(self):
            if self._has_continue:
                return {
                    "continue": {"cmcontinue": "next"},
                    "query": {"categorymembers": self._pages},
                }
            return {"query": {"categorymembers": self._pages}}

    class DummySession:
        def __init__(self) -> None:
            self.headers = {}
            self.call_count = 0

        def get(self, url, params=None, timeout=None):
            self.call_count += 1
            if self.call_count == 1:
                # First call: return pages with continue
                return DummyResponse([{"title": "Page1"}, {"title": "Page2"}], has_continue=True)
            else:
                # Second call: return final page without continue
                return DummyResponse([{"title": "Page3"}])

    monkeypatch.setattr("src.main_app.api_services.category.requests.Session", DummySession)

    pages = category.get_category_members_api("Category:Example", "commons.wikimedia.org")

    assert pages == ["Page1", "Page2", "Page3"]
