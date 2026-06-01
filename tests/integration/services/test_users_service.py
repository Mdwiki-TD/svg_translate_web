from flask import session

from src.main_app.su_services.users_service import (
    _resolve_user_id,
)


def test_resolve_user_id(app_mock):
    with app_mock.test_request_context():
        session["uid"] = 123
        assert _resolve_user_id() == 123

        session["uid"] = "456"
        assert _resolve_user_id() == 456

        session.pop("uid", None)
        assert _resolve_user_id() is None

        session["uid"] = "invalid"
        assert _resolve_user_id() is None
