"""Integration tests for templates admin routes improvements."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.main_app.admin.routes import templates
from src.main_app.db.services import TemplateService


@pytest.fixture
def flash_redirect_mocks(monkeypatch: pytest.MonkeyPatch):
    """Mock only Flask utility dependencies (flash, redirect, url_for)."""
    mocks = {
        "flash": Mock(),
        "redirect": Mock(),
        "url_for": Mock(),
    }
    monkeypatch.setattr("src.main_app.admin.routes.templates.flash", mocks["flash"])
    monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", mocks["redirect"])
    monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", mocks["url_for"])
    return mocks


def test_update_template_uses_request_form_type_parameter(mock_app, flash_redirect_mocks):
    """Test that _update_template parses id as int (type=int parameter)."""
    svc = TemplateService()
    created = svc.add_template_data({"title": "Test Title", "main_file": "test.svg"})

    templates.TemplatesRoutesFuncs()._update_template(
        {"id": str(created.id), "title": "Test Title", "main_file": "test.svg"}
    )

    updated = svc.get_template(created.id)
    assert updated is not None
    assert updated.main_file == "test.svg"


def test_update_template_correct_error_message_for_missing_title(mock_app, flash_redirect_mocks):
    """Test that _update_template shows correct error message for update (not 'add')."""
    svc = TemplateService()
    created = svc.add_template_data({"title": "Existing", "main_file": "test.svg"})

    templates.TemplatesRoutesFuncs()._update_template({"id": created.id, "title": "", "main_file": "test.svg"})

    flash_redirect_mocks["flash"].assert_called_once()
    flash_message = flash_redirect_mocks["flash"].call_args[0][0]
    assert "update" in flash_message.lower()
    assert "Title is required to update a template" in flash_message


def test_update_template_missing_id_shows_error(mock_app, flash_redirect_mocks):
    """Test that _update_template shows error when template ID is missing."""
    templates.TemplatesRoutesFuncs()._update_template({"id": "0", "title": "Test", "main_file": "test.svg"})

    flash_redirect_mocks["flash"].assert_called_once_with("Template ID is required to update a template.", "danger")
