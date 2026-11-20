"""
Unit tests for MediaWikiQueryService.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from src.main_app.api_services.query_api import MediaWikiQueryService


class TestGetPageAssessments:
    """Tests for MediaWikiQueryService class."""

    def test_get_page_assessments_with_list_input(self):
        """Test get_page_assessments accepts list input."""
        mock_site = MagicMock()
        mock_site.api.return_value = {
            "query": {
                "pages": [
                    {
                        "title": "Article 1",
                        "pageassessments": {"Medicine": {"importance": "High"}},
                    },
                    {
                        "title": "Article 2",
                        "pageassessments": {"Medicine": {"importance": "Low"}},
                    },
                ]
            }
        }

        client = MediaWikiQueryService(site=mock_site)
        result = client.get_page_assessments(["Article 1", "Article 2"])

        assert len(result) == 2
        mock_site.api.assert_called()

    def test_get_page_assessments_raises_on_api_error(self):
        """An API failure must propagate so the caller can mark the chunk failed."""
        mock_site = MagicMock()
        mock_site.api.side_effect = Exception("API Error")

        client = MediaWikiQueryService(site=mock_site)

        with pytest.raises(Exception, match="API Error"):
            client.get_page_assessments(["Test Article"])

    def test_get_page_assessments_requests_max_limit(self):
        """palimit is the pageassessments limit; ellimit belongs to another module."""
        mock_site = MagicMock()
        mock_site.api.return_value = {"query": {"pages": []}}

        MediaWikiQueryService(site=mock_site).get_page_assessments(["Article 1"])

        kwargs = mock_site.api.call_args.kwargs
        assert kwargs["palimit"] == "max"
        assert "ellimit" not in kwargs

    def test_get_page_assessments_pagination(self):
        """Test get_page_assessments handles pagination."""
        mock_site = MagicMock()

        # First page (real MediaWiki shape: module token + sentinel). mwclient
        # injects meta=userinfo into every query, hence "-||userinfo".
        first_response = {
            "query": {"pages": [{"title": "Article 1", "pageassessments": {}}]},
            "continue": {"continue": "-||userinfo", "pacontinue": "123"},
        }

        # Second page
        second_response = {"query": {"pages": [{"title": "Article 2", "pageassessments": {}}]}}

        mock_site.api.side_effect = [first_response, second_response]

        client = MediaWikiQueryService(site=mock_site)
        result = client.get_page_assessments(["Article 1", "Article 2"])

        assert len(result) == 2
        assert mock_site.api.call_count == 2

    def test_get_page_assessments_sends_back_module_continue_token(self):
        """The pacontinue token must be echoed back, otherwise the API repeats itself."""
        mock_site = MagicMock()
        mock_site.api.side_effect = [
            {
                "query": {"pages": [{"title": "Article 1"}]},
                "continue": {"continue": "-||userinfo", "pacontinue": "123"},
            },
            {"query": {"pages": [{"title": "Article 2"}]}},
        ]

        client = MediaWikiQueryService(site=mock_site)
        client.get_page_assessments(["Article 1", "Article 2"])

        kwargs = mock_site.api.call_args_list[1].kwargs
        assert kwargs["pacontinue"] == "123"
        assert kwargs["continue"] == "-||userinfo"

    def test_get_page_assessments_does_not_loop_on_stale_continue_token(self):
        """A non-advancing continuation token must terminate the loop, without duplicates."""
        mock_site = MagicMock()
        mock_site.api.return_value = {
            "query": {"pages": [{"title": "Article 1"}]},
            "continue": {"continue": "-||userinfo", "pacontinue": "123"},
        }

        client = MediaWikiQueryService(site=mock_site)
        result = client.get_page_assessments(["Article 1"])

        assert mock_site.api.call_count == 2
        assert len(result) == 1

    def test_get_page_assessments_stops_after_max_rounds(self):
        """Advancing-but-endless tokens are capped by MAX_CONTINUATION_ROUNDS."""
        mock_site = MagicMock()
        round_no = iter(range(1000))
        mock_site.api.side_effect = lambda **_: {
            "query": {"pages": [{"pageid": next(round_no), "title": "Article"}]},
            "continue": {"continue": "-||userinfo", "pacontinue": str(next(round_no))},
        }

        client = MediaWikiQueryService(site=mock_site)
        result = client.get_page_assessments(["Article"])

        assert mock_site.api.call_count == MediaWikiQueryService.MAX_CONTINUATION_ROUNDS
        assert len(result) == MediaWikiQueryService.MAX_CONTINUATION_ROUNDS


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

    def test_follows_continuation(self, mock_site):
        """gtilimit=max still paginates; every token must be sent back."""
        mock_site.get.side_effect = [
            {
                "query": {"pages": [{"pageid": 1, "ns": 0, "title": "Page A"}]},
                "continue": {"continue": "-||-", "gticontinue": "abc"},
            },
            {"query": {"pages": [{"pageid": 2, "ns": 0, "title": "Page B"}]}},
        ]
        service = MediaWikiQueryService(site=mock_site)
        result = service.get_template_pages("Template:Infobox")

        assert result == ["Page A", "Page B"]
        assert mock_site.get.call_args.kwargs["gticontinue"] == "abc"


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

    def test_follows_continuation(self, mock_site):
        """rdlimit=max still paginates per batch of 50 titles."""
        mock_site.get.side_effect = [
            {
                "query": {
                    "normalized": [],
                    "redirects": [{"from": "A", "to": "B"}],
                    "pages": {},
                },
                "continue": {"continue": "-||-", "rdcontinue": "tok"},
            },
            {
                "query": {
                    "normalized": [],
                    "redirects": [{"from": "C", "to": "D"}],
                    "pages": {},
                }
            },
        ]
        service = MediaWikiQueryService(site=mock_site)
        result = service.resolve_redirects(["A", "C"])

        assert result["from_to"] == {"A": "B", "C": "D"}
        assert mock_site.get.call_args.kwargs["rdcontinue"] == "tok"


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

    def test_follows_continuation(self, mock_site):
        """srlimit=max still paginates via sroffset."""
        mock_site.get.side_effect = [
            {
                "query": {"search": [{"title": "Aspirin"}]},
                "continue": {"continue": "-||-", "sroffset": 1},
            },
            {"query": {"search": [{"title": "Aspirin (drug)"}]}},
        ]
        service = MediaWikiQueryService(site=mock_site)
        result = service.search_pages("aspirin")

        assert result == ["Aspirin", "Aspirin (drug)"]
        assert mock_site.get.call_args.kwargs["sroffset"] == 1


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

    def test_follows_continuation(self, mock_site):
        """pllimit=max still paginates on pages with many links."""
        mock_site.get.side_effect = [
            {
                "query": {
                    "pages": {"1": {"links": [{"ns": 0, "title": "LinkA"}]}},
                    "normalized": [],
                    "redirects": [],
                },
                "continue": {"continue": "-||-", "plcontinue": "1|0|LinkB"},
            },
            {
                "query": {
                    "pages": {"1": {"links": [{"ns": 0, "title": "LinkB"}]}},
                    "normalized": [],
                    "redirects": [],
                }
            },
        ]
        service = MediaWikiQueryService(site=mock_site)
        result = service.get_page_links("TestPage")

        assert set(result["links"]) == {"LinkA", "LinkB"}
        assert mock_site.get.call_args.kwargs["plcontinue"] == "1|0|LinkB"


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

    def test_follows_continuation(self, mock_site):
        """gqplimit=max still paginates on large wikis."""
        mock_site.get.side_effect = [
            {
                "query": {"redirects": [{"from": "A", "to": "B"}]},
                "continue": {"continue": "-||-", "gqpoffset": 1},
            },
            {"query": {"redirects": [{"from": "B", "to": "C"}]}},
        ]
        service = MediaWikiQueryService(site=mock_site)
        result = service.get_double_redirects()

        assert [r["from"] for r in result] == ["A", "B"]
        assert mock_site.get.call_args.kwargs["gqpoffset"] == 1
