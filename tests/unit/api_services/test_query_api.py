"""Unit tests for src/main_app/api_services/query_api.py module."""

from __future__ import annotations

from src.main_app.api_services.query_api import (
    get_page_links,
    get_template_pages,
    is_pages_exists,
    resolve_redirects,
    search_pages,
)


class TestGetTemplatePages:
    def test_returns_titles(self, mock_site):
        mock_site.get.return_value = {
            "query": {
                "pages": [
                    {"pageid": 1, "ns": 0, "title": "Page A"},
                    {"pageid": 2, "ns": 0, "title": "Page B"},
                ]
            }
        }
        result = get_template_pages("Template:Infobox", site=mock_site)
        assert result == ["Page A", "Page B"]

    def test_empty_pages(self, mock_site):
        mock_site.get.return_value = {"query": {"pages": []}}
        result = get_template_pages("Template:Nonexistent", site=mock_site)
        assert result == []

    def test_no_query_key(self, mock_site):
        mock_site.get.return_value = {}
        result = get_template_pages("Template:Empty", site=mock_site)
        assert result == []


class TestIsPagesExists:
    def test_existing_pages(self, mock_site):
        # API returns pages as a dict keyed by pageid
        mock_site.get.return_value = {
            "query": {
                "normalized": [{"from": "aspirin", "to": "Aspirin"}],
                "pages": {
                    "1": {"pageid": 1, "ns": 0, "title": "Aspirin"},
                },
            }
        }
        result = is_pages_exists(["aspirin"], mock_site)
        assert result == {"aspirin": True}

    def test_missing_page(self, mock_site):
        mock_site.get.return_value = {
            "query": {
                "pages": {
                    "0": {"ns": 0, "title": "Nonexistent", "missing": ""},
                },
            }
        }
        result = is_pages_exists(["Nonexistent"], mock_site)
        assert result == {"Nonexistent": False}

    def test_empty_list(self, mock_site):
        result = is_pages_exists([], mock_site)
        assert result == {}
        mock_site.get.assert_not_called()

    def test_batching_over_50(self, mock_site):
        titles = [f"Page{i}" for i in range(55)]
        # First batch returns dict of 50 pages, second batch returns dict of 5
        pages_batch1 = {str(i): {"pageid": i, "ns": 0, "title": f"Page{i}"} for i in range(50)}
        pages_batch2 = {str(i): {"pageid": i, "ns": 0, "title": f"Page{i}"} for i in range(50, 55)}
        mock_site.get.side_effect = [
            {"query": {"pages": pages_batch1}},
            {"query": {"pages": pages_batch2}},
        ]
        result = is_pages_exists(titles, mock_site)
        assert mock_site.get.call_count == 2
        assert len(result) == 55


class TestResolveRedirects:
    def test_returns_from_to_mapping(self, mock_site):
        mock_site.get.return_value = {
            "query": {
                "normalized": [],
                "redirects": [{"from": "OldName", "to": "NewName"}],
                "pages": {},
            }
        }
        result = resolve_redirects(["OldName"], mock_site)
        assert result["from_to"]["OldName"] == "NewName"

    def test_empty_titles(self, mock_site):
        result = resolve_redirects([], mock_site)
        assert result == {"normalized": {}, "from_to": {}}

    def test_normalized_entries(self, mock_site):
        mock_site.get.return_value = {
            "query": {
                "normalized": [{"from": "oldpage", "to": "OldPage"}],
                "redirects": [],
                "pages": {},
            }
        }
        result = resolve_redirects(["oldpage"], mock_site)
        assert result["normalized"]["OldPage"] == "oldpage"


class TestSearchPages:
    def test_returns_titles(self, mock_site):
        mock_site.get.return_value = {
            "query": {
                "search": [
                    {"title": "Aspirin"},
                    {"title": "Aspirin (drug)"},
                ]
            }
        }
        result = search_pages("aspirin", mock_site)
        assert result == ["Aspirin", "Aspirin (drug)"]

    def test_empty_search(self, mock_site):
        mock_site.get.return_value = {"query": {"search": []}}
        result = search_pages("nonexistent", mock_site)
        assert result == []

    def test_no_query_key(self, mock_site):
        mock_site.get.return_value = {}
        result = search_pages("test", mock_site)
        assert result == []


class TestGetPageLinks:
    def test_returns_links(self, mock_site):
        mock_site.get.return_value = {
            "query": {
                "pages": {
                    "1": {
                        "links": [
                            {"ns": 0, "title": "LinkA"},
                            {"ns": 0, "title": "LinkB"},
                        ]
                    }
                },
                "normalized": [],
                "redirects": [],
            }
        }
        result = get_page_links("TestPage", mock_site)
        assert "LinkA" in result["links"]
        assert "LinkB" in result["links"]

    def test_empty_response(self, mock_site):
        mock_site.get.return_value = {}
        result = get_page_links("Empty", mock_site)
        assert result["links"] == {}
        assert result["normalized"] == []
        assert result["redirects"] == []

    def test_normalized_and_redirects(self, mock_site):
        mock_site.get.return_value = {
            "query": {
                "pages": {"1": {"links": []}},
                "normalized": [{"from": "test", "to": "Test"}],
                "redirects": [{"from": "Old", "to": "Test"}],
            }
        }
        result = get_page_links("test", mock_site)
        assert len(result["normalized"]) == 1
        assert len(result["redirects"]) == 1
