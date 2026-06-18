"""
Unit tests for src/main_app/db/services/utils/db_guard_model.py module.

Functions to test: db_guard_rollback, db_guard
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError, PendingRollbackError, SQLAlchemyError

from src.main_app.db.services.utils.db_guard_model import (
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
        with patch("src.main_app.db.services.utils.db_guard_model.db") as mock_db:

            @db_guard(default_return=None)
            def my_func():
                raise SQLAlchemyError("boom")

            assert my_func() is None
            mock_db.session.rollback.assert_called_once()

    def test_returns_default_on_operational_error(self):
        @db_guard(default_return=False)
        def my_func():
            raise SQLAlchemyError("stmt", "params", Exception("db down"))

        with patch("src.main_app.db.services.utils.db_guard_model.db") as mock_db:
            assert my_func() is False
            mock_db.session.rollback.assert_called_once()

    def test_rollback_on_generic_exception(self):
        @db_guard(default_return="fallback")
        def my_func():
            raise SQLAlchemyError("something went wrong")

        with patch("src.main_app.db.services.utils.db_guard_model.db") as mock_db:
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
        with patch("src.main_app.db.services.utils.db_guard_model.db"):

            @db_guard(default_return={"error": True})
            def my_func():
                raise SQLAlchemyError("fail")

            assert my_func() == {"error": True}


class TestDbGuardRollback:
    """Tests for db_guard_rollback decorator."""

    def test_returns_func_result_on_success(self):
        @db_guard_rollback
        def my_func():
            return "success"

        assert my_func() == "success"

    def test_rollback_on_integrity_error_and_re_raises(self):
        with patch("src.main_app.db.services.utils.db_guard_model.db") as mock_db:

            @db_guard_rollback
            def my_func():
                raise IntegrityError("stmt", "params", Exception("constraint"))

            with pytest.raises(IntegrityError):
                my_func()
            mock_db.session.rollback.assert_called_once()

    def test_rollback_on_generic_exception_and_re_raises(self):
        with patch("src.main_app.db.services.utils.db_guard_model.db") as mock_db:

            @db_guard_rollback
            def my_func():
                raise ValueError("boom")

            with pytest.raises(ValueError):
                my_func()
            mock_db.session.rollback.assert_called_once()

    def test_preserves_function_name(self):
        @db_guard_rollback
        def my_named_func():
            return True

        assert my_named_func.__name__ == "my_named_func"

    def test_passes_args_and_kwargs(self):
        @db_guard_rollback
        def add(a, b, extra=0):
            return a + b + extra

        assert add(1, 2, extra=10) == 13


class TestDbGuardEdgeCases:
    """Edge-case tests for db_guard decorator."""

    def test_pending_rollback_error_returns_default(self):
        with patch("src.main_app.db.services.utils.db_guard_model.db") as mock_db:

            @db_guard(default_return=None)
            def my_func():
                raise PendingRollbackError("stmt", "params", Exception("pending"))

            result = my_func()
            assert result is None
            mock_db.session.rollback.assert_called_once()

    def test_with_msg_param(self):
        with patch("src.main_app.db.services.utils.db_guard_model.db") as mock_db:
            with patch("src.main_app.db.services.utils.db_guard_model.logger") as mock_logger:

                @db_guard(default_return=None, msg="Custom error message")
                def my_func():
                    raise SQLAlchemyError("fail")

                result = my_func()
                assert result is None
                mock_db.session.rollback.assert_called_once()
