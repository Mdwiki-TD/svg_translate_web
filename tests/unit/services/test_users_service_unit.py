from unittest.mock import MagicMock, patch

import pytest
from flask import g

from src.main_app.services.users_service import (
    CurrentUser,
    context_user,
)


@patch("src.main_app.services.users_service.active_coordinators")
@patch("src.main_app.services.users_service.current_user")
def test_context_user(mock_current_user, mock_active_coordinators):
    user = MagicMock(username="admin")
    mock_current_user.return_value = user
    mock_active_coordinators.return_value = ["admin"]

    ctx = context_user()
    assert ctx["current_user"] == user
    assert ctx["is_authenticated"] is True
    assert ctx["is_admin"] is True
    assert ctx["username"] == "admin"

    mock_active_coordinators.return_value = ["other"]
    ctx = context_user()
    assert ctx["is_admin"] is False

    mock_current_user.return_value = None
    ctx = context_user()
    assert ctx["current_user"] is None
    assert ctx["is_authenticated"] is False
    assert ctx["is_admin"] is False
    assert ctx["username"] is None


def test_CurrentUser():
    u = CurrentUser(user_id="1", username="foo")
    assert u.user_id == "1"
    assert u.username == "foo"
