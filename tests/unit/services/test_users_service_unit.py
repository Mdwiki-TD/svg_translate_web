from unittest.mock import MagicMock, patch

from src.main_app.su_services.users_service import (
    CurrentUser,
)


def test_CurrentUser():
    # Just simple data class test
    u = CurrentUser(user_id="1", username="foo")
    assert u.user_id == "1"
    assert u.username == "foo"
