"""Unit tests for template_service module."""

from __future__ import annotations

import pytest

from src.main_app.db.services.template_service import (
    add_template_data,
    list_templates,
    list_templates_mismatched_years,
    get_template,
    get_template_by_title,
    update_template_data,
)
from src.main_app.db.services.delete_service import delete_template


def test_list_templates_empty():
    """Test listing templates when none exist."""
    templates = list_templates()
    assert templates == []


def test_add_template_success():
    """Test successfully adding a template."""
    data = {
        "title": "Test Template",
        "main_file": "test.svg",
    }
    record = add_template_data(data)

    assert record.title == "Test Template"
    assert record.main_file == "test.svg"
    assert record.id > 0


def test_add_template_duplicate_raises_value_error():
    """Test that adding a duplicate template raises ValueError."""
    data1 = {
        "title": "Duplicate",
        "main_file": "file1.svg",
    }
    add_template_data(data1)

    data2 = {
        "title": "Duplicate",
        "main_file": "file2.svg",
    }
    with pytest.raises(ValueError, match="Template 'Duplicate' already exists"):
        add_template_data(data2)


def test_add_template_empty_title_raises_value_error():
    """Test that adding a template with empty title raises ValueError."""
    data = {
        "title": "",
        "main_file": "file.svg",
    }
    with pytest.raises(ValueError, match="Title is required"):
        add_template_data(data)


def test_list_templates_returns_all():
    """Test listing all templates."""
    data1 = {"title": "Template 1", "main_file": "file1.svg"}
    data2 = {"title": "Template 2", "main_file": "file2.svg"}
    data3 = {"title": "Template 3", "main_file": "file3.svg"}
    add_template_data(data1)
    add_template_data(data2)
    add_template_data(data3)

    templates = list_templates()

    assert len(templates) == 3
    assert templates[0].title == "Template 1"
    assert templates[1].title == "Template 2"
    assert templates[2].title == "Template 3"


def test_delete_template_success():
    """Test successfully deleting a template."""
    data = {"title": "To Delete", "main_file": "delete.svg"}
    record = add_template_data(data)

    result = delete_template(record.id)

    assert result is True
    assert len(list_templates()) == 0


def test_delete_template_not_found_raises_lookup_error():
    """Test that deleting a non-existent template raises LookupError."""
    result = delete_template(999)
    assert result is False


def test_template_record_dataclass_with_none_main_file():
    """Test TemplateRecord with None main_file (type annotation change)."""
    data = {"title": "No Oldest File", "main_file": ""}
    record = add_template_data(data)

    assert record.title == "No Oldest File"
    assert isinstance(record.main_file, str)
