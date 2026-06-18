"""
Unit tests for src/main_app/db/services/utils/retry_on_disconnect.py module.

Functions to test: retry_on_db_disconnect
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import DetachedInstanceError

from src.main_app.db.models import SettingRecord
from src.main_app.db.services.utils import retry_on_db_disconnect
from src.main_app.extensions import db



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


class TestRetryOnDbDisconnectDetachedInstance:
    """Tests demonstrating that retry_on_db_disconnect causes DetachedInstanceError
    for SQLAlchemy objects the caller loaded before calling the decorated function.
    This is because db.session.remove() expires and detaches all ORM-managed objects."""

    def test_detached_instance_error_after_retries_exhausted(self):
        """After retries exhaust, db.session.remove() detaches previously loaded models."""
        record = SettingRecord(key="k", title="T", value="v", value_type="string")
        db.session.add(record)
        db.session.commit()

        loaded = SettingRecord.query.first()
        assert loaded.value == "v"

        @retry_on_db_disconnect(max_retries=1)
        def fail():
            exc = OperationalError("stmt", "params", Exception("MySQL server has gone away"))
            exc.connection_invalidated = True
            raise exc

        with pytest.raises(OperationalError):
            fail()

        with pytest.raises(DetachedInstanceError):
            _ = loaded.value

    def test_detached_instance_error_after_retry_succeeds(self):
        """Even when the retry succeeds, previously loaded objects get detached.
        This is the most insidious case — the decorated function appears to work,
        but the caller's objects are silently broken."""
        record = SettingRecord(key="k", title="T", value="v", value_type="string")
        db.session.add(record)
        db.session.commit()

        loaded = SettingRecord.query.first()
        assert loaded.value == "v"

        call_count = 0

        @retry_on_db_disconnect(max_retries=1)
        def may_fail():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                exc = OperationalError("stmt", "params", Exception("MySQL server has gone away"))
                exc.connection_invalidated = True
                raise exc
            return "recovered"

        assert may_fail() == "recovered"
        assert call_count == 2

        with pytest.raises(DetachedInstanceError):
            _ = loaded.value

    def test_objects_usable_on_first_try_success(self):
        """No retry → session.remove() never called → objects remain usable."""
        record = SettingRecord(key="k", title="T", value="v", value_type="string")
        db.session.add(record)
        db.session.commit()

        loaded = SettingRecord.query.first()
        assert loaded.value == "v"

        @retry_on_db_disconnect()
        def ok():
            return "ok"

        assert ok() == "ok"
        assert loaded.value == "v"

    def test_objects_usable_on_non_disconnect_error(self):
        """Non-disconnect OperationalError is re-raised immediately,
        db.session.remove() is never called → objects remain usable."""
        record = SettingRecord(key="k", title="T", value="v", value_type="string")
        db.session.add(record)
        db.session.commit()

        loaded = SettingRecord.query.first()
        assert loaded.value == "v"

        @retry_on_db_disconnect()
        def fail():
            raise OperationalError("stmt", "params", Exception("other db error"))

        with pytest.raises(OperationalError):
            fail()

        assert loaded.value == "v"
