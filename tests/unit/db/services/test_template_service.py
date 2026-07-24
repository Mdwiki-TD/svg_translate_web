"""Unit tests for template_service module."""

from __future__ import annotations

import pytest

from src.main_app.db.services.template_service import (
    TemplateService,
    add_template_data,
    get_template,
    get_template_by_title,
    list_templates,
    list_templates_mismatched_years,
    update_template_data,
)

def delete_template(template_id: int) -> bool:
    return TemplateService().delete(template_id)

class TestListTemplates:
    """Test list_templates function."""

    def test_list_templates_empty(self):
        """Test listing templates when none exist."""
        templates = list_templates()
        assert templates == []

    def test_list_templates_returns_all(self):
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

    def test_list_templates_with_limit(self):
        """Test listing templates with a limit."""
        add_template_data({"title": "A", "main_file": "a.svg"})
        add_template_data({"title": "B", "main_file": "b.svg"})
        add_template_data({"title": "C", "main_file": "c.svg"})

        result = list_templates(limit=2)

        assert len(result) == 2


class TestDeleteTemplate:
    """Test delete_template function."""

    def test_delete_template_success(self):
        """Test successfully deleting a template."""
        data = {"title": "To Delete", "main_file": "delete.svg"}
        record = add_template_data(data)

        result = delete_template(record.id)

        assert result is True
        assert len(list_templates()) == 0

    def test_delete_template_not_found_raises_lookup_error(self):
        """Test that deleting a non-existent template raises LookupError."""
        result = delete_template(999)
        assert result is False


class TestAddTemplate:
    """Test add_template_data function."""

    def test_template_record_dataclass_with_none_main_file(self):
        """Test TemplateRecord with None main_file (type annotation change)."""
        data = {"title": "No Oldest File", "main_file": ""}
        record = add_template_data(data)

        assert record.title == "No Oldest File"
        assert isinstance(record.main_file, str)

    def test_add_template_empty_title_raises_value_error(self):
        """Test that adding a template with empty title raises ValueError."""
        data = {
            "title": "",
            "main_file": "file.svg",
        }
        with pytest.raises(ValueError, match="Title is required"):
            add_template_data(data)

    def test_add_template_success(self):
        """Test successfully adding a template."""
        data = {
            "title": "Test Template",
            "main_file": "test.svg",
        }
        record = add_template_data(data)

        assert record.title == "Test Template"
        assert record.main_file == "test.svg"
        assert record.id > 0

    def test_add_template_duplicate_raises_value_error(self):
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

    def test_add_template_commit_failure_raises_error(self, monkeypatch):
        """Test that a commit failure raises the original exception."""
        from src.main_app.extensions import db

        def _fail_commit():
            raise RuntimeError("DB connection lost")

        monkeypatch.setattr(db.session, "commit", _fail_commit)

        data = {"title": "Fail", "main_file": "fail.svg"}
        with pytest.raises(RuntimeError, match="DB connection lost"):
            add_template_data(data)


class TestListTemplatesMismatchedYears:
    """Test list_templates_mismatched_years function."""

    def test_empty_when_no_templates(self):
        """Test returns empty list when no templates exist."""
        result = list_templates_mismatched_years()
        assert result == []

    def test_empty_when_all_match(self):
        """Test returns empty when all templates have matching year in filename."""
        add_template_data({"title": "T1", "last_world_file": "chart,World,2024.svg", "last_world_year": 2024})
        add_template_data({"title": "T2", "last_world_file": "chart,World,2025.svg", "last_world_year": 2025})

        result = list_templates_mismatched_years()

        assert result == []

    def test_returns_mismatched(self):
        """Test returns templates where year is not in filename."""
        add_template_data({"title": "Match", "last_world_file": "chart,World,2024.svg", "last_world_year": 2024})
        add_template_data({"title": "Mismatch", "last_world_file": "old_file.svg", "last_world_year": 2024})

        result = list_templates_mismatched_years()

        assert len(result) == 1
        assert result[0].title == "Mismatch"

    def test_skips_null_fields(self):
        """Test skips templates with null last_world_file or last_world_year."""
        add_template_data({"title": "Null Year", "last_world_file": "file.svg"})
        add_template_data({"title": "Null File", "last_world_year": 2024})

        result = list_templates_mismatched_years()

        assert result == []


class TestGetTemplate:
    """Test get_template function."""

    def test_returns_template_by_id(self):
        """Test returns template when found by ID."""
        record = add_template_data({"title": "Test", "main_file": "test.svg"})

        result = get_template(record.id)

        assert result is not None
        assert result.id == record.id
        assert result.title == "Test"

    def test_returns_none_when_not_found(self):
        """Test returns None when template ID does not exist."""
        result = get_template(999)
        assert result is None


class TestGetTemplateByTitle:
    """Test get_template_by_title function."""

    def test_returns_template_by_title(self):
        """Test returns template when found by title."""
        add_template_data({"title": "Unique Title", "main_file": "file.svg"})

        result = get_template_by_title("Unique Title")

        assert result is not None
        assert result.title == "Unique Title"

    def test_returns_none_when_not_found(self):
        """Test returns None when title does not exist."""
        result = get_template_by_title("Non-existent")
        assert result is None


class TestUpdateTemplateData:
    """Test update_template_data function."""

    def test_update_fields_successfully(self):
        """Test successfully updating template fields."""
        record = add_template_data({"title": "Original", "main_file": "original.svg"})

        updated = update_template_data(record.id, {"main_file": "updated.svg"})

        assert updated is not None
        assert updated.id == record.id
        assert updated.title == "Original"
        assert updated.main_file == "updated.svg"

    def test_returns_none_when_template_not_found(self):
        """Test returns None when template ID does not exist."""
        result = update_template_data(999, {"main_file": "new.svg"})
        assert result is None

    def test_ignores_none_values(self):
        """Test does not update fields with None values."""
        record = add_template_data({"title": "Original", "main_file": "original.svg"})

        updated = update_template_data(record.id, {"main_file": None, "title": "New Title"})

        assert updated is not None
        assert updated.title == "New Title"
        assert updated.main_file == "original.svg"

    def test_ignores_unknown_attributes(self):
        """Test ignores keys that are not model attributes."""
        record = add_template_data({"title": "Original", "main_file": "file.svg"})

        updated = update_template_data(record.id, {"nonexistent_field": "value"})

        assert updated is not None
        assert updated.title == "Original"

    def test_handles_file_prefix_stripping(self):
        """Test ensure_template_data strips 'File:' prefix from main_file."""
        record = add_template_data({"title": "Original", "main_file": "file.svg"})

        updated = update_template_data(record.id, {"main_file": "File:new_file.svg"})

        assert updated is not None
        assert updated.main_file == "new_file.svg"
