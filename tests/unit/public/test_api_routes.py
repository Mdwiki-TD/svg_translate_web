"""Unit tests for src/main_app/public/api_routes.py module."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from flask.testing import FlaskClient


def _make_template_mock(**attrs: Any) -> MagicMock:
    _DEFAULTS_TEMPLATE: dict[str, Any] = {
        "id": 0,
        "title": "",
        "main_file": None,
        "last_world_file": None,
        "last_world_year": None,
        "source": "",
        "slug": "",
        "created_at": None,
        "updated_at": None,
    }
    data = {**_DEFAULTS_TEMPLATE, **attrs}
    mock = MagicMock()
    for key, value in data.items():
        setattr(mock, key, value)
    mock.to_dict.return_value = data
    return mock


def _make_chart_mock(**attrs: Any) -> MagicMock:
    _DEFAULTS_CHART: dict[str, Any] = {
        "chart_id": 0,
        "slug": "",
        "title": "",
        "has_map_tab": False,
        "max_time": None,
        "min_time": None,
        "default_tab": None,
        "owid_variable_id": None,
        "is_published": False,
        "single_year_data": False,
        "len_years": None,
        "has_timeline": False,
        "created_at": None,
        "updated_at": None,
    }
    data = {**_DEFAULTS_CHART, **attrs}
    mock = MagicMock()
    for key, value in data.items():
        setattr(mock, key, value)
    mock.to_dict.return_value = data
    return mock


def _make_chart_template_mock(**attrs: Any) -> MagicMock:
    mock = MagicMock()
    for key, value in attrs.items():
        setattr(mock, key, value)
    mock.to_dict.return_value = dict(attrs)
    return mock


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    mocks = {
        "owidchartsservice": MagicMock(),
        "templateservice": MagicMock(),
        "viewsservice": MagicMock(),
    }
    monkeypatch.setattr(
        "src.main_app.public.api_routes.OwidChartsService",
        mocks["owidchartsservice"],
    )
    monkeypatch.setattr(
        "src.main_app.public.api_routes.TemplateService",
        mocks["templateservice"],
    )
    monkeypatch.setattr(
        "src.main_app.public.api_routes.ViewsService",
        mocks["viewsservice"],
    )
    return mocks


class TestTemplatesList:
    """Tests for GET /api/templates."""

    def test_templates_list(self, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """list_templates returns list of templates; response has data and summary."""
        t1 = _make_template_mock(id=1, title="T1", main_file="f1.svg")
        t2 = _make_template_mock(id=2, title="T2")

        monkeypatch.setattr("src.main_app.public.api_routes.list_templates", lambda: [t1, t2])

        resp = mock_client.get("/api/templates")
        assert resp.status_code == 200

        body = resp.get_json()
        assert body is not None
        assert len(body["data"]) == 2
        assert body["data"][0]["title"] == "T1"
        assert body["data"][1]["title"] == "T2"
        assert body["summary"]["total"] == 2

    def test_templates_list_summary_counts(self, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """Summary counts reflect which optional fields are set."""
        t1 = _make_template_mock(
            id=1,
            title="T1",
            main_file="f1.svg",
            last_world_file="w1.svg",
            last_world_year=2022,
            source="src1",
        )
        t2 = _make_template_mock(
            id=2,
            title="T2",
            main_file=None,
            last_world_file=None,
            last_world_year=None,
            source="",
        )

        monkeypatch.setattr("src.main_app.public.api_routes.list_templates", lambda: [t1, t2])

        resp = mock_client.get("/api/templates")
        body = resp.get_json()

        assert body["summary"]["total"] == 2
        assert body["summary"]["with_main_file"] == 1
        assert body["summary"]["with_last_world_file"] == 1
        assert body["summary"]["with_last_world_year"] == 1
        assert body["summary"]["with_source"] == 1

    def test_templates_list_empty(self, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """When no templates exist, data is empty and counts are zero."""
        monkeypatch.setattr("src.main_app.public.api_routes.list_templates", list)

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

    def test_templates_need_update_list(self, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """list_templates_need_update returns records; JSON has data key."""
        t1 = MagicMock()
        t1.to_dict.return_value = {"template_id": 1, "template_title": "T1", "difference": 2}
        t2 = MagicMock()
        t2.to_dict.return_value = {"template_id": 2, "template_title": "T2", "difference": 0}

        monkeypatch.setattr("src.main_app.public.api_routes.list_templates_need_update", lambda: [t1, t2])

        resp = mock_client.get("/api/templates-need-update")
        body = resp.get_json()

        assert body["data"] == [
            {"template_id": 1, "template_title": "T1", "difference": 2},
            {"template_id": 2, "template_title": "T2", "difference": 0},
        ]


class TestChartsTemplates:
    """Tests for GET /api/charts_templates."""

    def test_charts_templates(self, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """Only records with a template_id are included in the response."""
        ct1 = _make_chart_template_mock(chart_id=1, template_id=10, template_title="T1")
        ct2 = _make_chart_template_mock(chart_id=2, template_id=None, template_title=None)
        ct3 = _make_chart_template_mock(chart_id=3, template_id=30, template_title="T3")

        monkeypatch.setattr(
            "src.main_app.public.api_routes.list_owid_charts_templates",
            lambda: [ct1, ct2, ct3],
        )

        resp = mock_client.get("/api/charts_templates")
        body = resp.get_json()

        assert body is not None
        assert len(body) == 2
        assert body[0]["chart_id"] == 1
        assert body[1]["chart_id"] == 3


class TestOwidChartsList:
    """Tests for GET /api/owidcharts/."""

    @pytest.fixture(autouse=True)
    def _setup_mocks(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chart1 = _make_chart_mock(chart_id=1, slug="s1", is_published=True, has_map_tab=True, has_timeline=True)
        chart2 = _make_chart_mock(chart_id=2, slug="s2", is_published=False, has_map_tab=False, has_timeline=False)
        chart3 = _make_chart_mock(chart_id=3, slug="s3", is_published=True, has_map_tab=False, has_timeline=True)
        self.charts = [chart1, chart2, chart3]

        ct1 = _make_chart_template_mock(chart_id=1, template_id=10, template_title="T1")
        ct3 = _make_chart_template_mock(chart_id=3, template_id=None, template_title=None)
        self.chart_templates = [ct1, ct3]

        monkeypatch.setattr(
            "src.main_app.public.api_routes.list_charts",
            lambda: self.charts,
        )
        monkeypatch.setattr(
            "src.main_app.public.api_routes.list_owid_charts_templates",
            lambda: self.chart_templates,
        )

        chart_temps_dict = {c.chart_id: c for c in self.chart_templates}

        def mock_list_charts_with_templates():
            results = []
            for chart in self.charts:
                ct = chart_temps_dict.get(chart.chart_id)
                results.append((chart, ct.template_id if ct else None, ct.template_title if ct else None))
            return results

        monkeypatch.setattr(
            "src.main_app.public.api_routes.list_charts_with_templates",
            mock_list_charts_with_templates,
        )

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

        assert len(body["data"]) == 1
        assert body["data"][0]["chart_id"] == 1

    def test_owid_charts_list_no_template_filter(self, mock_client: FlaskClient) -> None:
        """no_template filter returns only charts without a template."""
        resp = mock_client.get("/api/owidcharts/no_template")
        body = resp.get_json()

        assert len(body["data"]) == 2
        chart_ids = {c["chart_id"] for c in body["data"]}
        assert chart_ids == {2, 3}

    def test_owid_charts_list_summary(self, mock_client: FlaskClient) -> None:
        """Summary counts for published, template, map_tab, timeline are correct."""
        resp = mock_client.get("/api/owidcharts/")
        body = resp.get_json()

        summary = body["summary"]
        assert summary["total"] == 3
        assert summary["published"] == {"with": 2, "without": 1}
        assert summary["template"] == {"with": 1, "without": 2}
        assert summary["map_tab"] == {"with": 1, "without": 2}
        assert summary["timeline"] == {"with": 2, "without": 1}

    def test_owid_charts_list_enriches_with_template_data(self, mock_client: FlaskClient) -> None:
        """Each chart dict has template_id and template_title from the join."""
        resp = mock_client.get("/api/owidcharts/")
        body = resp.get_json()

        chart_by_id = {c["chart_id"]: c for c in body["data"]}

        # chart 1 has a template
        assert chart_by_id[1]["template_id"] == 10
        assert chart_by_id[1]["template_title"] == "T1"

        # chart 2 has no matching template record -> None
        assert chart_by_id[2]["template_id"] is None
        assert chart_by_id[2]["template_title"] is None

        # chart 3 has a template record but template_id is None -> None
        assert chart_by_id[3]["template_id"] is None
        assert chart_by_id[3]["template_title"] is None


__all__ = []
