"""Unit tests for src/main_app/api_services/query_api.py module."""

from __future__ import annotations

from src.main_app.api_services.query_api import (
    MediaWikiQueryService,
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
        service = MediaWikiQueryService(site=mock_site)
        result = service.get_template_pages("Template:Infobox")
        assert result == ["Page A", "Page B"]

    def test_empty_pages(self, mock_site):
        mock_site.get.return_value = {"query": {"pages": []}}
        service = MediaWikiQueryService(site=mock_site)
        result = service.get_template_pages("Template:Nonexistent")
        assert result == []

    def test_no_query_key(self, mock_site):
        mock_site.get.return_value = {}
        service = MediaWikiQueryService(site=mock_site)
        result = service.get_template_pages("Template:Empty")
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
        service = MediaWikiQueryService(site=mock_site)
        result = service.is_pages_exists(["aspirin"])
        assert result == {"aspirin": True}

    def test_missing_page(self, mock_site):
        mock_site.get.return_value = {
            "query": {
                "pages": {
                    "0": {"ns": 0, "title": "Nonexistent", "missing": ""},
                },
            }
        }
        service = MediaWikiQueryService(site=mock_site)
        result = service.is_pages_exists(["Nonexistent"])
        assert result == {"Nonexistent": False}

    def test_empty_list(self, mock_site):
        service = MediaWikiQueryService(site=mock_site)
        result = service.is_pages_exists([])
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
        service = MediaWikiQueryService(site=mock_site)
        result = service.is_pages_exists(titles)
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
        service = MediaWikiQueryService(site=mock_site)
        result = service.resolve_redirects(["OldName"])
        assert result["from_to"]["OldName"] == "NewName"

    def test_empty_titles(self, mock_site):
        service = MediaWikiQueryService(site=mock_site)
        result = service.resolve_redirects([])
        assert result == {"normalized": {}, "from_to": {}}

    def test_normalized_entries(self, mock_site):
        mock_site.get.return_value = {
            "query": {
                "normalized": [{"from": "oldpage", "to": "OldPage"}],
                "redirects": [],
                "pages": {},
            }
        }
        service = MediaWikiQueryService(site=mock_site)
        result = service.resolve_redirects(["oldpage"])
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
        service = MediaWikiQueryService(site=mock_site)
        result = service.search_pages("aspirin")
        assert result == ["Aspirin", "Aspirin (drug)"]

    def test_empty_search(self, mock_site):
        mock_site.get.return_value = {"query": {"search": []}}
        service = MediaWikiQueryService(site=mock_site)
        result = service.search_pages("nonexistent")
        assert result == []

    def test_no_query_key(self, mock_site):
        mock_site.get.return_value = {}
        service = MediaWikiQueryService(site=mock_site)
        result = service.search_pages("test")
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
        service = MediaWikiQueryService(site=mock_site)
        result = service.get_page_links("TestPage")
        assert "LinkA" in result["links"]
        assert "LinkB" in result["links"]

    def test_empty_response(self, mock_site):
        mock_site.get.return_value = {}
        service = MediaWikiQueryService(site=mock_site)
        result = service.get_page_links("Empty")
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
        service = MediaWikiQueryService(site=mock_site)
        result = service.get_page_links("test")
        assert len(result["normalized"]) == 1
        assert len(result["redirects"]) == 1


class TestGetDoubleRedirects:
    def test_returns_redirects(self, mock_site):
        mock_site.get.return_value = {
            "query": {
                "redirects": [
                    {"from": "A", "to": "B"},
                    {"from": "B", "to": "C"},
                ]
            }
        }
        service = MediaWikiQueryService(site=mock_site)
        result = service.get_double_redirects()
        assert len(result) == 2
        assert result[0]["from"] == "A"
        assert result[1]["to"] == "C"

    def test_empty_response(self, mock_site):
        mock_site.get.return_value = {}
        service = MediaWikiQueryService(site=mock_site)
        result = service.get_double_redirects()
        assert result == []

    def test_no_query_key(self, mock_site):
        mock_site.get.return_value = {}
        service = MediaWikiQueryService(site=mock_site)
        result = service.get_double_redirects()
        assert result == []
