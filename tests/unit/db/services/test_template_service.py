"""Unit tests for template_service module."""

from __future__ import annotations

import pytest

from src.main_app.db.services.template_service import TemplateService


class TestListTemplates:
    """Test list_templates function."""

    def test_list_templates_empty(self):
        templates = TemplateService().list_templates()
        assert templates == []

    def test_list_templates_returns_all(self):
        data1 = {"title": "Template 1", "main_file": "file1.svg"}
        data2 = {"title": "Template 2", "main_file": "file2.svg"}
        data3 = {"title": "Template 3", "main_file": "file3.svg"}
        TemplateService().add_template_data(data1)
        TemplateService().add_template_data(data2)
        TemplateService().add_template_data(data3)

        templates = TemplateService().list_templates()

        assert len(templates) == 3
        assert templates[0].title == "Template 1"
        assert templates[1].title == "Template 2"
        assert templates[2].title == "Template 3"

    def test_list_templates_with_limit(self):
        TemplateService().add_template_data({"title": "A", "main_file": "a.svg"})
        TemplateService().add_template_data({"title": "B", "main_file": "b.svg"})
        TemplateService().add_template_data({"title": "C", "main_file": "c.svg"})

        result = TemplateService().list_templates(limit=2)

        assert len(result) == 2


class TestDeleteTemplate:
    """Test TemplateService().delete function."""

    def test_delete_template_success(self):
        data = {"title": "To Delete", "main_file": "delete.svg"}
        record = TemplateService().add_template_data(data)

        result = TemplateService().delete(record.id)

        assert result is True
        assert len(TemplateService().list_templates()) == 0

    def test_delete_template_not_found_raises_lookup_error(self):
        result = TemplateService().delete(999)
        assert result is False


class TestAddTemplate:
    """Test add_template_data function."""

    def test_template_record_dataclass_with_none_main_file(self):
        data = {"title": "No Oldest File", "main_file": ""}
        record = TemplateService().add_template_data(data)

        assert record.title == "No Oldest File"
        assert isinstance(record.main_file, str)

    def test_add_template_empty_title_raises_value_error(self):
        data = {
            "title": "",
            "main_file": "file.svg",
        }
        with pytest.raises(ValueError, match="Title is required"):
            TemplateService().add_template_data(data)

    def test_add_template_success(self):
        data = {
            "title": "Test Template",
            "main_file": "test.svg",
        }
        record = TemplateService().add_template_data(data)

        assert record.title == "Test Template"
        assert record.main_file == "test.svg"
        assert record.id > 0

    def test_add_template_duplicate_raises_value_error(self):
        data1 = {
            "title": "Duplicate",
            "main_file": "file1.svg",
        }
        TemplateService().add_template_data(data1)

        data2 = {
            "title": "Duplicate",
            "main_file": "file2.svg",
        }
        with pytest.raises(ValueError, match="Template 'Duplicate' already exists"):
            TemplateService().add_template_data(data2)

    def test_add_template_commit_failure_raises_error(self, monkeypatch):
        from src.main_app.extensions import db

        def _fail_commit():
            raise RuntimeError("DB connection lost")

        monkeypatch.setattr(db.session, "commit", _fail_commit)

        data = {"title": "Fail", "main_file": "fail.svg"}
        with pytest.raises(RuntimeError, match="DB connection lost"):
            TemplateService().add_template_data(data)


class TestListTemplatesMismatchedYears:
    """Test list_templates_mismatched_years function."""

    def test_empty_when_no_templates(self):
        result = TemplateService().list_templates_mismatched_years()
        assert result == []

    def test_empty_when_all_match(self):
        TemplateService().add_template_data({"title": "T1", "last_world_file": "chart,World,2024.svg", "last_world_year": 2024})
        TemplateService().add_template_data({"title": "T2", "last_world_file": "chart,World,2025.svg", "last_world_year": 2025})

        result = TemplateService().list_templates_mismatched_years()

        assert result == []

    def test_returns_mismatched(self):
        TemplateService().add_template_data({"title": "Match", "last_world_file": "chart,World,2024.svg", "last_world_year": 2024})
        TemplateService().add_template_data({"title": "Mismatch", "last_world_file": "old_file.svg", "last_world_year": 2024})

        result = TemplateService().list_templates_mismatched_years()

        assert len(result) == 1
        assert result[0].title == "Mismatch"

    def test_skips_null_fields(self):
        TemplateService().add_template_data({"title": "Null Year", "last_world_file": "file.svg"})
        TemplateService().add_template_data({"title": "Null File", "last_world_year": 2024})

        result = TemplateService().list_templates_mismatched_years()

        assert result == []


class TestGetTemplate:
    """Test get_template function."""

    def test_returns_template_by_id(self):
        record = TemplateService().add_template_data({"title": "Test", "main_file": "test.svg"})

        result = TemplateService().get_template(record.id)

        assert result is not None
        assert result.id == record.id
        assert result.title == "Test"

    def test_returns_none_when_not_found(self):
        result = TemplateService().get_template(999)
        assert result is None


class TestGetTemplateByTitle:
    """Test get_template_by_title function."""

    def test_returns_template_by_title(self):
        TemplateService().add_template_data({"title": "Unique Title", "main_file": "file.svg"})

        result = TemplateService().get_template_by_title("Unique Title")

        assert result is not None
        assert result.title == "Unique Title"

    def test_returns_none_when_not_found(self):
        result = TemplateService().get_template_by_title("Non-existent")
        assert result is None


class TestUpdateTemplateData:
    """Test update_template_data function."""

    def test_update_fields_successfully(self):
        record = TemplateService().add_template_data({"title": "Original", "main_file": "original.svg"})

        updated = TemplateService().update_template_data(record.id, {"main_file": "updated.svg"})

        assert updated is not None
        assert updated.id == record.id
        assert updated.title == "Original"
        assert updated.main_file == "updated.svg"

    def test_returns_none_when_template_not_found(self):
        result = TemplateService().update_template_data(999, {"main_file": "new.svg"})
        assert result is None

    def test_ignores_none_values(self):
        record = TemplateService().add_template_data({"title": "Original", "main_file": "original.svg"})

        updated = TemplateService().update_template_data(record.id, {"main_file": None, "title": "New Title"})

        assert updated is not None
        assert updated.title == "New Title"
        assert updated.main_file == "original.svg"

    def test_ignores_unknown_attributes(self):
        record = TemplateService().add_template_data({"title": "Original", "main_file": "file.svg"})

        updated = TemplateService().update_template_data(record.id, {"nonexistent_field": "value"})

        assert updated is not None
        assert updated.title == "Original"

    def test_handles_file_prefix_stripping(self):
        record = TemplateService().add_template_data({"title": "Original", "main_file": "file.svg"})

        updated = TemplateService().update_template_data(record.id, {"main_file": "File:new_file.svg"})

        assert updated is not None
        assert updated.main_file == "new_file.svg"