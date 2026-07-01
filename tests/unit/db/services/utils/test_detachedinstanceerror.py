"""
Tests that reproduce the side effect flagged in review: calling
db.session.remove() inside retry_on_db_disconnect's retry loop discards
the scoped session, which detaches *any* other ORM object the caller
was holding in that same thread/request -- not just the one the
decorated function itself was working on.

These use a real in-memory SQLite database and a real scoped_session,
because DetachedInstanceError is a genuine SQLAlchemy object-state error
-- a MagicMock `db` can't reproduce it, it can only record that
.remove() was called.
"""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import DetachedInstanceError

import src.main_app.db.services.utils.retry_on_disconnect as decorators_module
from src.main_app.db.models import SettingRecord
from src.main_app.db.services.utils.retry_on_disconnect import retry_on_db_disconnect
from src.main_app.extensions import db


def make_operational_error(message="some error", connection_invalidated=False):
    """Build an OperationalError with a controllable message and
    connection_invalidated flag, mirroring what SQLAlchemy raises."""
    err = OperationalError(message, {}, Exception(message))
    err.connection_invalidated = connection_invalidated
    return err


class TestRetryOnDbDisconnectRemove:

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        """Replace the module-level `db` with a mock so we can assert on
        rollback()/remove() calls without touching a real database."""
        mock_db = MagicMock()
        monkeypatch.setattr(decorators_module, "db", mock_db)
        self.fake_db = mock_db

    def test_raises_after_exhausting_retries(self):
        err = make_operational_error(connection_invalidated=True)
        func = MagicMock(side_effect=err)
        func.__name__ = "fake_job_function"
        wrapped = retry_on_db_disconnect(max_retries=2, remove_session=True)(func)

        with pytest.raises(OperationalError):
            wrapped()

        # initial attempt + 2 retries = 3 calls total
        assert func.call_count == 3
        assert self.fake_db.session.rollback.call_count == 2
        assert self.fake_db.session.remove.call_count == 2

    def test_rollback_exception_is_swallowed_and_retry_continues(self):
        self.fake_db.session.rollback.side_effect = Exception("connection completely dead")
        err = make_operational_error(connection_invalidated=True)
        func = MagicMock(side_effect=[err, "ok"])
        func.__name__ = "fake_job_function"
        wrapped = retry_on_db_disconnect(remove_session=True)(func)

        result = wrapped()

        assert result == "ok"
        self.fake_db.session.rollback.assert_called_once()
        self.fake_db.session.remove.assert_called_once()

    def test_retries_on_connection_invalidated_then_succeeds(self):
        err = make_operational_error(connection_invalidated=True)
        func = MagicMock(side_effect=[err, "ok"])
        func.__name__ = "fake_job_function"
        wrapped = retry_on_db_disconnect(remove_session=True)(func)

        result = wrapped()

        assert result == "ok"
        assert func.call_count == 2
        self.fake_db.session.rollback.assert_called_once()
        self.fake_db.session.remove.assert_called_once()


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
        assert loaded is not None
        assert loaded.value == "v"

        @retry_on_db_disconnect(max_retries=1, remove_session=True)
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
        assert loaded is not None
        assert loaded.value == "v"

        call_count = 0

        @retry_on_db_disconnect(max_retries=1, remove_session=True)
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
