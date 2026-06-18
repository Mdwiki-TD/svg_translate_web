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

import pytest
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import DetachedInstanceError

from src.main_app.db.models import SettingRecord
from src.main_app.db.services.utils.retry_on_disconnect import retry_on_db_disconnect
from src.main_app.extensions import db


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
