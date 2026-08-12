"""Unit tests for src/main_app/public/api_routes.py module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from flask.testing import FlaskClient

from src.main_app.api_services.files_service.file_langs import FileLanguagesMap
from src.main_app.db.services import (
    OwidChartsService,
    TemplateService,
)


@pytest.fixture
def template_svc() -> TemplateService:
    return TemplateService()


@pytest.fixture
def owid_charts_svc() -> OwidChartsService:
    return OwidChartsService()


class TestTemplatesList:
    """Tests for GET /api/templates."""

    def test_templates_list(self, mock_client: FlaskClient, template_svc: TemplateService) -> None:
        """list returns list of templates; response has data and summary."""
        template_svc.add_template_data({"title": "T1", "main_file": "f1.svg"})
        template_svc.add_template_data({"title": "T2"})

        resp = mock_client.get("/api/templates")
        assert resp.status_code == 200

        body = resp.get_json()
        assert body is not None
        assert len(body["data"]) == 2
        assert body["data"][0]["title"] == "T1"
        assert body["data"][1]["title"] == "T2"
        assert body["summary"]["total"] == 2

    def test_templates_list_summary_counts(self, mock_client: FlaskClient, template_svc: TemplateService) -> None:
        """Summary counts reflect which optional fields are set."""
        template_svc.add_template_data(
            {
                "title": "T1",
                "main_file": "f1.svg",
                "last_world_file": "w1.svg",
                "last_world_year": 2022,
                "source": "src1",
            }
        )
        template_svc.add_template_data(
            {
                "title": "T2",
            }
        )

        resp = mock_client.get("/api/templates")
        body = resp.get_json()

        assert body["summary"]["total"] == 2
        assert body["summary"]["with_main_file"] == 1
        assert body["summary"]["with_last_world_file"] == 1
        assert body["summary"]["with_last_world_year"] == 1
        assert body["summary"]["with_source"] == 1

    def test_templates_list_empty(self, mock_client: FlaskClient) -> None:
        """When no templates exist, data is empty and counts are zero."""
        resp = mock_client.get("/api/templates")
        body = resp.get_json()

        assert body["data"] == []
        assert body["summary"]["total"] == 0
        assert body["summary"]["with_main_file"] == 0
        assert body["summary"]["with_last_world_file"] == 0
        assert body["summary"]["with_last_world_year"] == 0
        assert body["summary"]["with_source"] == 0


class TestTemplatesNeedUpdateList:
    """Tests for GET /api/templates-need-update."""

    def test_templates_need_update_list(
        self, mock_client: FlaskClient, template_svc: TemplateService, owid_charts_svc: OwidChartsService
    ) -> None:
        """list_templates_need_update returns records; JSON has data key."""
        owid_charts_svc.create(
            slug="chart-a",
            title="Chart A",
            max_time=2024,
            owid_variable_id=123,
        )
        template_svc.add_template_data(
            {
                "title": "T1",
                "slug": "chart-a",
                "last_world_year": 2023,
                "source": "owid",
            }
        )

        owid_charts_svc.create(
            slug="chart-b",
            title="Chart B",
            max_time=2025,
            owid_variable_id=456,
        )
        template_svc.add_template_data(
            {
                "title": "T2",
                "slug": "chart-b",
                "last_world_year": 2024,
                "source": "owid",
            }
        )

        resp = mock_client.get("/api/templates-need-update")
        body = resp.get_json()

        assert len(body["data"]) == 2
        titles = {item["template_title"] for item in body["data"]}
        assert titles == {"T1", "T2"}


class TestOwidChartsList:
    """Tests for GET /api/owidcharts/."""

    @pytest.fixture(autouse=True)
    def _setup_data(self, template_svc: TemplateService, owid_charts_svc: OwidChartsService) -> None:
        # chart1: published, has map, has timeline, has matching template
        owid_charts_svc.create(
            slug="s1",
            title="Chart 1",
            is_published=True,
            has_map_tab=True,
            has_timeline=True,
            max_time=2024,
        )
        template_svc.add_template_data({"title": "T1", "slug": "s1", "source": "owid"})

        # chart2: not published, no map, no timeline, no matching template
        owid_charts_svc.create(
            slug="s2",
            title="Chart 2",
            is_published=False,
            has_map_tab=False,
            has_timeline=False,
            max_time=2024,
        )

        # chart3: published, no map, has timeline, has template record but template_id will be set
        owid_charts_svc.create(
            slug="s3",
            title="Chart 3",
            is_published=True,
            has_map_tab=False,
            has_timeline=True,
            max_time=2024,
        )
        template_svc.add_template_data({"title": "T3", "slug": "s3", "source": "owid"})

    def test_owid_charts_list_no_filter(self, mock_client: FlaskClient) -> None:
        """Without a filter, all charts are returned."""
        resp = mock_client.get("/api/owidcharts/")
        body = resp.get_json()

        assert len(body["data"]) == 3
        assert body["selected_template"] == ""

    def test_owid_charts_list_has_template_filter(self, mock_client: FlaskClient) -> None:
        """has_template filter returns only charts having a template."""
        resp = mock_client.get("/api/owidcharts/has_template")
        body = resp.get_json()

        assert len(body["data"]) == 2
        chart_ids = {c["chart_id"] for c in body["data"]}
        assert 1 in chart_ids
        assert 3 in chart_ids

    def test_owid_charts_list_no_template_filter(self, mock_client: FlaskClient) -> None:
        """no_template filter returns only charts without a template."""
        resp = mock_client.get("/api/owidcharts/no_template")
        body = resp.get_json()

        assert len(body["data"]) == 1
        assert body["data"][0]["slug"] == "s2"

    def test_owid_charts_list_summary(self, mock_client: FlaskClient) -> None:
        """Summary counts for published, template, map_tab, timeline are correct."""
        resp = mock_client.get("/api/owidcharts/")
        body = resp.get_json()

        summary = body["summary"]
        assert summary["total"] == 3
        assert summary["published"] == {"with": 2, "without": 1}
        assert summary["template"] == {"with": 2, "without": 1}
        assert summary["map_tab"] == {"with": 1, "without": 2}
        assert summary["timeline"] == {"with": 2, "without": 1}

    def test_owid_charts_list_enriches_with_template_data(self, mock_client: FlaskClient) -> None:
        """Each chart dict has template_id and template_title from the join."""
        resp = mock_client.get("/api/owidcharts/")
        body = resp.get_json()

        chart_by_slug = {c["slug"]: c for c in body["data"]}

        # chart s1 has a template
        assert chart_by_slug["s1"]["template_id"] is not None
        assert chart_by_slug["s1"]["template_title"] == "T1"

        # chart s2 has no matching template record -> None
        assert chart_by_slug["s2"]["template_id"] is None
        assert chart_by_slug["s2"]["template_title"] is None

        # chart s3 has a matching template
        assert chart_by_slug["s3"]["template_id"] is not None
        assert chart_by_slug["s3"]["template_title"] == "T3"


class TestFileLanguages:
    """Tests for GET /api/languages/<file_name>."""

    FILE_NAME = "File:Parkinsons_disease_prevalence_ihme,_Africa,_2021.svg"

    @pytest.fixture(autouse=True)
    def mock_get_file_languages(self, monkeypatch: pytest.MonkeyPatch):
        mock = MagicMock(return_value=FileLanguagesMap(error=None, langs=["en"]))
        monkeypatch.setattr("src.main_app.public.api_routes.get_file_languages", mock)
        return mock

    def test_returns_languages(self, mock_client: FlaskClient, mock_get_file_languages: MagicMock) -> None:
        """Returns language list when file has translations."""
        mock_get_file_languages.return_value = FileLanguagesMap(error=None, langs=["en", "fr", "de"])

        resp = mock_client.get(f"/api/languages/{self.FILE_NAME}")

        assert resp.status_code == 200
        body = resp.get_json()
        assert body == ["en", "fr", "de"]
        mock_get_file_languages.assert_called_once_with(self.FILE_NAME)

    def test_returns_english_only(self, mock_client: FlaskClient) -> None:
        """Returns ['en'] when file has no translations."""
        resp = mock_client.get(f"/api/languages/{self.FILE_NAME}")

        assert resp.status_code == 200
        body = resp.get_json()
        assert body == ["en"]

    def test_returns_404_on_error(self, mock_client: FlaskClient, mock_get_file_languages: MagicMock) -> None:
        """Returns 404 when file metadata cannot be found."""
        mock_get_file_languages.return_value = FileLanguagesMap(
            error="Metadata not found for File:Missing.svg",
            langs=None,
        )

        resp = mock_client.get("/api/languages/File:Missing.svg")

        assert resp.status_code == 404
        body = resp.get_json()
        assert "error" in body

    def test_returns_404_on_empty_filename(self, mock_client: FlaskClient, mock_get_file_languages: MagicMock) -> None:
        """Returns 404 when file_name is empty."""
        mock_get_file_languages.return_value = FileLanguagesMap(error="Empty fileName", langs=None)
        # {"error": "Empty fileName", "langs": None}

        resp = mock_client.get("/api/languages/")

        assert resp.status_code == 404
