import pytest
from unittest.mock import MagicMock
import pymysql
from src.app.db.db_Templates import TemplatesDB, TemplateRecord

@pytest.fixture
def mock_db_class(mocker):
    return mocker.patch("src.app.db.db_Templates.Database")

@pytest.fixture
def mock_db_instance(mock_db_class):
    instance = MagicMock()
    mock_db_class.return_value = instance
    return instance

@pytest.fixture
def templates_db(mock_db_instance):
    return TemplatesDB({})

def test_TemplateRecord():
    rec = TemplateRecord(id=1, title="t", main_file="f.svg")
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
        {"id": 2, "title": "t2", "main_file": "f2"}
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
        "\n                INSERT INTO templates (title, main_file) VALUES (%s, %s)\n                ",
        ("new", "f.svg")
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
        [{"id": 1, "title": "old", "main_file": "old.svg"}], # _fetch_by_id check
        [{"id": 1, "title": "new", "main_file": "new.svg"}]  # Return updated
    ]
    
    rec = templates_db.update(1, "new", "new.svg")
    
    mock_db_instance.execute_query_safe.assert_called_with(
        "UPDATE templates SET title = %s, main_file = %s WHERE id = %s",
        ("new", "new.svg", 1)
    )
    assert rec.title == "new"

def test_delete_success(templates_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 1, "title": "del", "main_file": "del.svg"}
    ]
    
    rec = templates_db.delete(1)
    
    mock_db_instance.execute_query_safe.assert_called_with(
        "DELETE FROM templates WHERE id = %s",
        (1,)
    )
    assert rec.id == 1

def test_add_or_update(templates_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 1, "title": "upsert", "main_file": "f.svg"}
    ]
    
    rec = templates_db.add_or_update("upsert", "f.svg")
    
    mock_db_instance.execute_query_safe.assert_called()
    assert "INSERT INTO templates" in mock_db_instance.execute_query_safe.call_args[0][0]
    assert "ON DUPLICATE KEY UPDATE" in mock_db_instance.execute_query_safe.call_args[0][0]
    assert rec.title == "upsert"