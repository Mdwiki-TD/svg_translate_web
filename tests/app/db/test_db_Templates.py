from unittest.mock import MagicMock

import pymysql
import pytest

from src.main_app.db.db_Templates import TemplateRecord, TemplatesDB


@pytest.fixture
def mock_db_class(mocker):
    return mocker.patch("src.main_app.db.db_Templates.Database")


@pytest.fixture
def mock_db_instance(mock_db_class):
    instance = MagicMock()
    mock_db_class.return_value = instance
    return instance


@pytest.fixture
def templates_db(mock_db_instance):
    return TemplatesDB({})


def test_TemplateRecord():
    rec = TemplateRecord(id=1, title="t", main_file="f.svg", last_world_file=None)
    assert rec.id == 1
    assert rec.title == "t"
    assert rec.main_file == "f.svg"


def test_ensure_table(mock_db_instance):
    TemplatesDB({})
    mock_db_instance.execute_query_safe.assert_called()
    assert "CREATE TABLE IF NOT EXISTS templates" in mock_db_instance.execute_query_safe.call_args[0][0]


def test_fetch_by_id_success(templates_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 1, "title": "t", "main_file": "f", "created_at": None, "updated_at": None}
    ]
    rec = templates_db._fetch_by_id(1)
    assert rec.title == "t"


def test_fetch_by_id_not_found(templates_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = []
    with pytest.raises(LookupError):
        templates_db._fetch_by_id(1)


def test_fetch_by_title_success(templates_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 1, "title": "t", "main_file": "f", "created_at": None, "updated_at": None}
    ]
    rec = templates_db._fetch_by_title("t")
    assert rec.id == 1


def test_list(templates_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 1, "title": "t1", "main_file": "f1"},
        {"id": 2, "title": "t2", "main_file": "f2"},
    ]
    res = templates_db.list()
    assert len(res) == 2
    assert res[0].title == "t1"


def test_add_success(templates_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 1, "title": "new", "main_file": "f.svg", "created_at": None, "updated_at": None}
    ]
    rec = templates_db.add("new", "f.svg")

    mock_db_instance.execute_query.assert_called_with(
        "\n                INSERT INTO templates (title, main_file) VALUES (%s, %s)\n                ", ("new", "f.svg")
    )
    assert rec.title == "new"


def test_add_duplicate(templates_db, mock_db_instance):
    mock_db_instance.execute_query.side_effect = pymysql.err.IntegrityError(1062, "Duplicate")
    with pytest.raises(ValueError, match="already exists"):
        templates_db.add("dup", "f.svg")


def test_add_empty_title(templates_db):
    with pytest.raises(ValueError, match="Title is required"):
        templates_db.add("   ", "f.svg")


def test_update_success(templates_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.side_effect = [
        [{"id": 1, "title": "old", "main_file": "old.svg"}],  # _fetch_by_id check
        [{"id": 1, "title": "new", "main_file": "new.svg"}],  # Return updated
    ]

    rec = templates_db.update(1, "new", "new.svg")

    mock_db_instance.execute_query_safe.assert_called_with(
        "UPDATE templates SET title = %s, main_file = %s WHERE id = %s", ("new", "new.svg", 1)
    )
    assert rec.title == "new"


def test_delete_success(templates_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [{"id": 1, "title": "del", "main_file": "del.svg"}]

    rec = templates_db.delete(1)

    mock_db_instance.execute_query_safe.assert_called_with("DELETE FROM templates WHERE id = %s", (1,))
    assert rec.id == 1


def test_add_or_update(templates_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [{"id": 1, "title": "upsert", "main_file": "f.svg"}]

    rec = templates_db.add_or_update("upsert", "f.svg")

    mock_db_instance.execute_query_safe.assert_called()
    assert "INSERT INTO templates" in mock_db_instance.execute_query_safe.call_args[0][0]
    assert "ON DUPLICATE KEY UPDATE" in mock_db_instance.execute_query_safe.call_args[0][0]
    assert rec.title == "upsert"


def test_row_to_record_with_all_fields(templates_db):
    """Test _row_to_record with all fields populated."""
    from datetime import datetime

    now = datetime.now()
    row = {"id": 42, "title": "Test Template", "main_file": "test.svg", "created_at": now, "updated_at": now}

    record = templates_db._row_to_record(row)

    assert record.id == 42
    assert record.title == "Test Template"
    assert record.main_file == "test.svg"
    assert record.created_at == now
    assert record.updated_at == now


def test_row_to_record_with_none_main_file(templates_db):
    """Test _row_to_record with None main_file."""
    row = {"id": 1, "title": "Template Without File", "main_file": None, "created_at": None, "updated_at": None}

    record = templates_db._row_to_record(row)

    assert record.id == 1
    assert record.title == "Template Without File"
    assert record.main_file is None


def test_fetch_by_title_not_found(templates_db, mock_db_instance):
    """Test _fetch_by_title raises LookupError when template not found."""
    mock_db_instance.fetch_query_safe.return_value = []

    with pytest.raises(LookupError, match="was not found"):
        templates_db._fetch_by_title("nonexistent")


def test_add_with_whitespace(templates_db, mock_db_instance):
    """Test add method strips whitespace from title and main_file."""
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 1, "title": "trimmed", "main_file": "file.svg", "created_at": None, "updated_at": None}
    ]

    rec = templates_db.add("  trimmed  ", "  file.svg  ")

    # Verify the execute_query was called with trimmed values
    call_args = mock_db_instance.execute_query.call_args[0][1]
    assert call_args[0] == "trimmed"
    assert call_args[1] == "file.svg"


def test_update_not_found(templates_db, mock_db_instance):
    """Test update raises LookupError when template ID doesn't exist."""
    mock_db_instance.fetch_query_safe.return_value = []

    with pytest.raises(LookupError):
        templates_db.update(999, "new_title", "new_file.svg")


def test_delete_not_found(templates_db, mock_db_instance):
    """Test delete raises LookupError when template ID doesn't exist."""
    mock_db_instance.fetch_query_safe.return_value = []

    with pytest.raises(LookupError):
        templates_db.delete(999)


def test_list_empty(templates_db, mock_db_instance):
    """Test list returns empty list when no templates exist."""
    mock_db_instance.fetch_query_safe.return_value = []

    result = templates_db.list()

    assert result == []
    assert isinstance(result, list)
