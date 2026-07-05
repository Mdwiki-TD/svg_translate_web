"""Unit tests for src/main_app/public/main_routes/owid_charts_routes.py."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.main_app.public.main_routes import owid_charts_routes


class TestIndexRoute:
    def test_renders_with_charts(self, monkeypatch):
        mock_chart = MagicMock()
        mock_chart.slug = "test"
        mock_chart.title = "Test"
        monkeypatch.setattr(
            "src.main_app.public.main_routes.owid_charts_routes.list_published_charts",
            lambda: [mock_chart],
        )
        monkeypatch.setattr(
            "src.main_app.public.main_routes.owid_charts_routes.list_charts",
            lambda: [mock_chart],
        )
        monkeypatch.setattr(
            "src.main_app.public.main_routes.owid_charts_routes.render_template",
            lambda t, **c: c,
        )
        result = owid_charts_routes.index()
        assert result["charts"] == [mock_chart]

    def test_with_empty_list(self, monkeypatch):
        monkeypatch.setattr(
            "src.main_app.public.main_routes.owid_charts_routes.list_published_charts",
            list,
        )
        monkeypatch.setattr(
            "src.main_app.public.main_routes.owid_charts_routes.list_charts",
            list,
        )
        monkeypatch.setattr(
            "src.main_app.public.main_routes.owid_charts_routes.render_template",
            lambda t, **c: c,
        )
        result = owid_charts_routes.index()
        assert result["charts"] == []


class TestAllCharts:
    def test_renders_all_charts(self, monkeypatch):
        mock_chart = MagicMock()
        mock_chart.slug = "test"
        mock_chart.title = "Test"
        monkeypatch.setattr(
            "src.main_app.public.main_routes.owid_charts_routes.list_charts",
            lambda: [mock_chart],
        )
        monkeypatch.setattr(
            "src.main_app.public.main_routes.owid_charts_routes.render_template",
            lambda t, **c: c,
        )
        result = owid_charts_routes.all_charts()
        assert result["charts"] == [mock_chart]

    def test_empty_list(self, monkeypatch):
        monkeypatch.setattr(
            "src.main_app.public.main_routes.owid_charts_routes.list_charts",
            list,
        )
        monkeypatch.setattr(
            "src.main_app.public.main_routes.owid_charts_routes.render_template",
            lambda t, **c: c,
        )
        result = owid_charts_routes.all_charts()
        assert result["charts"] == []
