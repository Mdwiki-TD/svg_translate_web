"""Unit tests for views_service module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.main_app.db.services.views_service import ViewsService


class TestListTemplatesNeedUpdate:
    def test_returns_ordered_templates(self):
        mock_records = [MagicMock(template_title="A"), MagicMock(template_title="B")]
        mock_db = MagicMock()
        mock_db.session.query.return_value.order_by.return_value.all.return_value = mock_records
        with patch("src.main_app.db.services.views_service.db", mock_db):
            result = ViewsService().list_templates_need_update()
            assert result == mock_records
            mock_db.session.query.return_value.order_by.assert_called_once()

    def test_returns_empty_list(self):
        mock_db = MagicMock()
        mock_db.session.query.return_value.order_by.return_value.all.return_value = []
        with patch("src.main_app.db.services.views_service.db", mock_db):
            result = ViewsService().list_templates_need_update()
            assert result == []


class TestListOwidChartsTemplates:
    def test_returns_ordered_templates(self):
        mock_records = [MagicMock(template_title="A"), MagicMock(template_title="B")]
        mock_db = MagicMock()
        mock_db.session.query.return_value.order_by.return_value.all.return_value = mock_records
        with patch("src.main_app.db.services.views_service.db", mock_db):
            result = ViewsService().list_owid_charts_templates()
            assert result == mock_records
            mock_db.session.query.return_value.order_by.assert_called_once()

    def test_returns_empty_list(self):
        mock_db = MagicMock()
        mock_db.session.query.return_value.order_by.return_value.all.return_value = []
        with patch("src.main_app.db.services.views_service.db", mock_db):
            result = ViewsService().list_owid_charts_templates()
            assert result == []
