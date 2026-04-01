from src.main_app.db.db_class import MaxUserConnectionsError


def test_MaxUserConnectionsError():
    """Test MaxUserConnectionsError exception."""
    # Test basic instantiation
    error = MaxUserConnectionsError()
    assert isinstance(error, Exception)
    assert str(error) == ""

    # Test with message
    error_with_msg = MaxUserConnectionsError("Too many connections")
    assert str(error_with_msg) == "Too many connections"
