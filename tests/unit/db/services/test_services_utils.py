"""
Unit tests for src/main_app/db/services/utils.py module.

Functions to test: db_guard_rollback, db_guard, retry_on_db_disconnect
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError, PendingRollbackError, SQLAlchemyError

from src.main_app.db.services.utils import (
    db_guard,
    db_guard_rollback,
    retry_on_db_disconnect,
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


class TestDbGuardRollback:
    """Tests for db_guard_rollback decorator."""

    def test_returns_func_result_on_success(self):
        @db_guard_rollback
        def my_func():
            return "success"

        assert my_func() == "success"

    def test_rollback_on_integrity_error_and_re_raises(self):
        with patch("src.main_app.db.services.utils.db") as mock_db:

            @db_guard_rollback
            def my_func():
                raise IntegrityError("stmt", "params", Exception("constraint"))

            with pytest.raises(IntegrityError):
                my_func()
            mock_db.session.rollback.assert_called_once()

    def test_rollback_on_generic_exception_and_re_raises(self):
        with patch("src.main_app.db.services.utils.db") as mock_db:

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
        with patch("src.main_app.db.services.utils.db") as mock_db:

            @db_guard(default_return=None)
            def my_func():
                raise PendingRollbackError("stmt", "params", Exception("pending"))

            result = my_func()
            assert result is None
            mock_db.session.rollback.assert_called_once()

    def test_with_msg_param(self):
        with patch("src.main_app.db.services.utils.db") as mock_db:
            with patch("src.main_app.db.services.utils.logger") as mock_logger:

                @db_guard(default_return=None, msg="Custom error message")
                def my_func():
                    raise SQLAlchemyError("fail")

                result = my_func()
                assert result is None
                mock_db.session.rollback.assert_called_once()


class TestRetryOnDbDisconnect:
    """Tests for retry_on_db_disconnect decorator."""

    def test_returns_func_result_on_success(self):
        @retry_on_db_disconnect()
        def my_func():
            return "ok"

        assert my_func() == "ok"

    def test_passes_args_and_kwargs(self):
        @retry_on_db_disconnect()
        def add(a, b, extra=0):
            return a + b + extra

        assert add(1, 2, extra=10) == 13

    def test_preserves_function_name(self):
        @retry_on_db_disconnect()
        def my_named_func():
            return True

        assert my_named_func.__name__ == "my_named_func"

    def test_retries_and_succeeds_on_connection_invalidated(self):
        with patch("src.main_app.db.services.utils.db") as mock_db:

            call_count = 0

            @retry_on_db_disconnect(max_retries=3)
            def my_func():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    exc = OperationalError("stmt", "params", Exception("conn dead"))
                    exc.connection_invalidated = True
                    raise exc
                return "recovered"

            assert my_func() == "recovered"
            assert call_count == 2
            mock_db.session.rollback.assert_called_once()
            mock_db.session.remove.assert_called_once()

    def test_retries_and_succeeds_on_mysql_gone_away(self):
        with patch("src.main_app.db.services.utils.db") as mock_db:

            call_count = 0

            @retry_on_db_disconnect(max_retries=3)
            def my_func():
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise OperationalError("stmt", "params", Exception("MySQL server has gone away"))
                return "recovered"

            assert my_func() == "recovered"
            assert call_count == 3
            assert mock_db.session.rollback.call_count == 2
            assert mock_db.session.remove.call_count == 2

    def test_raises_after_exhausting_retries(self):
        with patch("src.main_app.db.services.utils.db") as mock_db:

            @retry_on_db_disconnect(max_retries=2)
            def my_func():
                exc = OperationalError("stmt", "params", Exception("MySQL server has gone away"))
                exc.connection_invalidated = True
                raise exc

            with pytest.raises(OperationalError):
                my_func()

            assert mock_db.session.rollback.call_count == 2
            assert mock_db.session.remove.call_count == 2

    def test_raises_immediately_on_non_disconnect_operational_error(self):
        with patch("src.main_app.db.services.utils.db") as mock_db:

            @retry_on_db_disconnect()
            def my_func():
                raise OperationalError("stmt", "params", Exception("some other db error"))

            with pytest.raises(OperationalError):
                my_func()

            mock_db.session.rollback.assert_not_called()
            mock_db.session.remove.assert_not_called()

    def test_handles_rollback_failure_gracefully(self):
        with patch("src.main_app.db.services.utils.db") as mock_db:
            mock_db.session.rollback.side_effect = RuntimeError("rollback also fails")

            call_count = 0

            @retry_on_db_disconnect(max_retries=1)
            def my_func():
                nonlocal call_count
                call_count += 1
                exc = OperationalError("stmt", "params", Exception("MySQL server has gone away"))
                exc.connection_invalidated = True
                raise exc

            with pytest.raises(OperationalError):
                my_func()

            assert call_count == 2  # initial + 1 retry
            mock_db.session.remove.assert_called()

    def test_uses_default_max_retries(self):
        with patch("src.main_app.db.services.utils.db") as mock_db:

            call_count = 0

            @retry_on_db_disconnect()
            def my_func():
                nonlocal call_count
                call_count += 1
                exc = OperationalError("stmt", "params", Exception("MySQL server has gone away"))
                exc.connection_invalidated = True
                raise exc

            with pytest.raises(OperationalError):
                my_func()

            # Default is 3: initial attempt + 3 retries = 4 calls
            assert call_count == 4
            assert mock_db.session.rollback.call_count == 3
            assert mock_db.session.remove.call_count == 3
