"""Tests for category helpers."""

from __future__ import annotations

import types

import pytest

from src.main_app.api_services import category


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.main_app.api_services.category.settings",
        types.SimpleNamespace(oauth=types.SimpleNamespace(user_agent="agent")),
    )


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


def test_get_category_members_filters_templates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_category_members filters to Template: namespace and excludes specific templates."""
    def mock_api(category, project, limit):
        return [
            "Template:ValidTemplate1",
            "Template:ValidTemplate2",
            "Template:OWIDslider",  # Should be excluded (case insensitive)
            "Template:OWID",         # Should be excluded (case insensitive)
            "File:NotATemplate.svg",  # Should be excluded (not Template:)
            "Category:NotATemplate",  # Should be excluded (not Template:)
        ]

    monkeypatch.setattr("src.main_app.api_services.category.get_category_members_api", mock_api)

    result = category.get_category_members()

    assert result == ["Template:ValidTemplate1", "Template:ValidTemplate2"]


def test_get_category_members_custom_category(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_category_members with custom category parameter."""
    def mock_api(category, project, limit):
        assert category == "Category:CustomCategory"
        return ["Template:Test"]

    monkeypatch.setattr("src.main_app.api_services.category.get_category_members_api", mock_api)

    result = category.get_category_members(category="Category:CustomCategory")

    assert result == ["Template:Test"]


def test_get_category_members_empty_results(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_category_members with empty API results."""
    def mock_api(category, project, limit):
        return []

    monkeypatch.setattr("src.main_app.api_services.category.get_category_members_api", mock_api)

    result = category.get_category_members()

    assert result == []


def test_get_category_members_no_valid_templates(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_category_members when all templates are excluded."""
    def mock_api(category, project, limit):
        return [
            "Template:OWIDslider",
            "Template:owid",
            "File:Something.svg",
        ]

    monkeypatch.setattr("src.main_app.api_services.category.get_category_members_api", mock_api)

    result = category.get_category_members()

    assert result == []


def test_get_category_members_case_sensitivity(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test get_category_members handles case variations correctly."""
    def mock_api(category, project, limit):
        return [
            "Template:OWIDSLIDER",  # Different case
            "Template:oWiDsLiDeR",  # Mixed case
            "Template:Owid",        # Different case
            "TEMPLATE:owid",        # Different case namespace (but still starts with Template:)
            "template:test",        # Lowercase namespace (but still starts with Template:)
        ]

    monkeypatch.setattr("src.main_app.api_services.category.get_category_members_api", mock_api)

    result = category.get_category_members()

    # All should be excluded because they match excluded templates (case insensitive)
    # or don't start with "Template:" (case sensitive check in source)
    # Actually looking at the source: x.startswith("Template:") is case sensitive
    # and x.lower() not in ["template:owidslider", "template:owid"]
    assert "Template:OWIDSLIDER" not in result
    assert "Template:oWiDsLiDeR" not in result
    assert "Template:Owid" not in result
    assert "TEMPLATE:owid" not in result
    assert "template:test" not in result
