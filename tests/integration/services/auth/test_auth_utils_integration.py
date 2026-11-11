from flask import session
from src.main_app.services.auth.current_user_resolver import (
    CurrentUserResolver,
)


def test_resolve_user_id(mock_app):
    with mock_app.test_request_context():
        session["uid"] = 123
        assert CurrentUserResolver.resolve_user_id(session["uid"]) == 123

        session["uid"] = "456"
        assert CurrentUserResolver.resolve_user_id(session["uid"]) == 456

        session.pop("uid", None)
        assert CurrentUserResolver.resolve_user_id(None) is None

        session["uid"] = "invalid"
        assert CurrentUserResolver.resolve_user_id(session["uid"]) is None
