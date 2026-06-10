"""
Unit tests for src/main_app/db/services/utils.py module.

Functions to test: db_guard_rollback, db_guard

TODO: write tests
"""

from __future__ import annotations

from unittest.mock import patch

from sqlalchemy.exc import SQLAlchemyError

from src.main_app.db.services.utils import (
    db_guard,
    db_guard_rollback,
)


class TestDbGuard:
    def test_returns_func_result_on_success(self):
        @db_guard(default_return=False)
        def my_func():
            return 42

        assert my_func() == 42

    def test_returns_default_on_exception_with_mock_db(self):
        with patch("src.main_app.db.services.utils.db") as mock_db:

            @db_guard(default_return=None)
            def my_func():
                raise SQLAlchemyError("boom")

            assert my_func() is None
            mock_db.session.rollback.assert_called_once()

    def test_returns_default_on_operational_error(self):
        @db_guard(default_return=False)
        def my_func():
            raise SQLAlchemyError("stmt", "params", Exception("db down"))

        with patch("src.main_app.db.services.utils.db") as mock_db:
            assert my_func() is False
            mock_db.session.rollback.assert_called_once()

    def test_rollback_on_generic_exception(self):
        @db_guard(default_return="fallback")
        def my_func():
            raise SQLAlchemyError("something went wrong")

        with patch("src.main_app.db.services.utils.db") as mock_db:
            result = my_func()
            assert result == "fallback"
            mock_db.session.rollback.assert_called_once()

    def test_preserves_function_name(self):
        @db_guard(default_return=False)
        def my_named_func():
            return True

        assert my_named_func.__name__ == "my_named_func"

    def test_passes_args_and_kwargs(self):
        @db_guard(default_return=False)
        def add(a, b, extra=0):
            return a + b + extra

        assert add(1, 2, extra=10) == 13

    def test_default_return_type_can_be_anything(self):
        with patch("src.main_app.db.services.utils.db"):

            @db_guard(default_return={"error": True})
            def my_func():
                raise SQLAlchemyError("fail")

            assert my_func() == {"error": True}
