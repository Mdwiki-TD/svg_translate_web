"""
Unit tests for src/main_app/db/services/utils/retry_on_disconnect.py module.

Functions to test: retry_on_db_disconnect
"""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest
from sqlalchemy.exc import OperationalError

import src.main_app.db.services.utils.retry_on_disconnect as decorators_module
from src.main_app.db.services.utils.retry_on_disconnect import retry_on_db_disconnect


def make_operational_error(message="some error", connection_invalidated=False):
    """Build an OperationalError with a controllable message and
    connection_invalidated flag, mirroring what SQLAlchemy raises."""
    err = OperationalError(message, {}, Exception(message))
    err.connection_invalidated = connection_invalidated
    return err


def make_func(side_effect):
    """MagicMock doesn't expose a real __name__ (it's a dunder, so
    __getattr__ raises AttributeError on it), but functools.wraps needs
    one. Give the mock a __name__ so the decorator can wrap it."""
    func = MagicMock(side_effect=side_effect)
    func.__name__ = "fake_job_function"
    return func


@pytest.fixture
def fake_db(monkeypatch):
    """Replace the module-level `db` with a mock so we can assert on
    rollback()/remove() calls without touching a real database."""
    mock_db = MagicMock()
    monkeypatch.setattr(decorators_module, "db", mock_db)
    return mock_db


class TestRetryOnDbDisconnect:
    def test_returns_value_on_success_without_retry(self, fake_db):
        func = MagicMock(return_value="ok", __name__="fake_job_function")
        wrapped = retry_on_db_disconnect()(func)

        result = wrapped(1, 2, foo="bar")

        assert result == "ok"
        func.assert_called_once_with(1, 2, foo="bar")
        fake_db.session.rollback.assert_not_called()
        fake_db.session.remove.assert_not_called()

    def test_retries_on_connection_invalidated_then_succeeds(self, fake_db):
        err = make_operational_error(connection_invalidated=True)
        func = make_func([err, "ok"])
        wrapped = retry_on_db_disconnect()(func)

        result = wrapped()

        assert result == "ok"
        assert func.call_count == 2
        fake_db.session.rollback.assert_called_once()
        fake_db.session.remove.assert_called_once()

    def test_retries_on_mysql_gone_away_message(self, fake_db):
        err = make_operational_error(message="MySQL server has gone away")
        func = make_func([err, "ok"])
        wrapped = retry_on_db_disconnect()(func)

        result = wrapped()

        assert result == "ok"
        assert func.call_count == 2

    def test_non_disconnect_operational_error_raised_immediately(self, fake_db):
        err = make_operational_error(message="some unrelated db error")
        func = make_func(err)
        wrapped = retry_on_db_disconnect()(func)

        with pytest.raises(OperationalError):
            wrapped()

        func.assert_called_once()
        fake_db.session.rollback.assert_not_called()
        fake_db.session.remove.assert_not_called()

    def test_raises_after_exhausting_retries(self, fake_db):
        err = make_operational_error(connection_invalidated=True)
        func = make_func(err)
        wrapped = retry_on_db_disconnect(max_retries=2)(func)

        with pytest.raises(OperationalError):
            wrapped()

        # initial attempt + 2 retries = 3 calls total
        assert func.call_count == 3
        assert fake_db.session.rollback.call_count == 2
        assert fake_db.session.remove.call_count == 2

    def test_custom_max_retries_of_zero_means_no_retry(self, fake_db):
        err = make_operational_error(connection_invalidated=True)
        func = make_func(err)
        wrapped = retry_on_db_disconnect(max_retries=0)(func)

        with pytest.raises(OperationalError):
            wrapped()

        func.assert_called_once()
        fake_db.session.rollback.assert_not_called()
        fake_db.session.remove.assert_not_called()

    def test_rollback_exception_is_swallowed_and_retry_continues(self, fake_db):
        fake_db.session.rollback.side_effect = Exception("connection completely dead")
        err = make_operational_error(connection_invalidated=True)
        func = make_func([err, "ok"])
        wrapped = retry_on_db_disconnect()(func)

        result = wrapped()

        assert result == "ok"
        fake_db.session.rollback.assert_called_once()
        fake_db.session.remove.assert_called_once()

    def test_preserves_wrapped_function_metadata(self, fake_db):
        @retry_on_db_disconnect()
        def my_func(job_id):
            """Docstring."""
            return job_id

        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "Docstring."

    def test_logs_warning_on_each_retry(self, fake_db, caplog):
        err = make_operational_error(connection_invalidated=True)
        func = make_func([err, "ok"])
        wrapped = retry_on_db_disconnect()(func)

        with caplog.at_level("WARNING"):
            wrapped()

        assert "gone away" in caplog.text
        assert "attempt 1/3" in caplog.text.lower() or "1/3" in caplog.text

    def test_logs_error_after_exhausting_retries(self, fake_db, caplog):
        err = make_operational_error(connection_invalidated=True)
        func = make_func(err)
        wrapped = retry_on_db_disconnect(max_retries=1)(func)

        with caplog.at_level("ERROR"):
            with pytest.raises(OperationalError):
                wrapped()

        assert "failed after" in caplog.text

    def test_args_and_kwargs_forwarded_on_every_attempt(self, fake_db):
        err = make_operational_error(connection_invalidated=True)
        func = make_func([err, "ok"])
        wrapped = retry_on_db_disconnect()(func)

        wrapped(42, status="running", job_type="export")

        func.assert_has_calls(
            [
                call(42, status="running", job_type="export"),
                call(42, status="running", job_type="export"),
            ]
        )

    def test_uses_default_max_retries_when_not_specified(self, fake_db):
        err = make_operational_error(connection_invalidated=True)
        func = make_func(err)
        wrapped = retry_on_db_disconnect()(func)  # no max_retries passed

        with pytest.raises(OperationalError):
            wrapped()

        # default is 3 retries -> 1 initial call + 3 retries = 4 calls
        assert func.call_count == 4

    def test_non_operational_errors_propagate_without_handling(self, fake_db):
        func = make_func(ValueError("not a db error"))
        wrapped = retry_on_db_disconnect()(func)

        with pytest.raises(ValueError):
            wrapped()

        func.assert_called_once()
        fake_db.session.rollback.assert_not_called()
