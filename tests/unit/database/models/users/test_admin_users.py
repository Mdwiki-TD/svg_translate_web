# ruff: noqa: F401
"""
Unit tests for src/main_app/database/models/admin_users.py module.

Classes to test: CoordinatorRecord, AdminRecord

TODO: write tests
"""

from src.main_app.database.models import UserRecord
from src.main_app.database.models.admin_users import (
    AdminRecord,
    CoordinatorRecord,
)


class TestAdminRecord:
    """Tests for AdminRecord dataclass."""

    def test_admin_user_record(self, sqlite_db) -> None:

        user = UserRecord(user_id=1, username="model_admin_user")
        sqlite_db.session.add(user)
        sqlite_db.session.commit()

        admin = AdminRecord(username="model_admin_user", is_active=True)
        sqlite_db.session.add(admin)
        sqlite_db.session.commit()

        assert admin.id is not None
        assert admin.username == "model_admin_user"
        assert admin.is_active is True
