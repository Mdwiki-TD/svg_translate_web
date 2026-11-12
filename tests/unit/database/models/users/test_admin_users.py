"""
Unit tests for src/main_app/database/models/admin_users.py module.

Classes to test: AdminUserRecord

TODO: write tests
"""

from src.main_app.database.models import UserRecord
from src.main_app.database.models.users import (
    AdminUserRecord,
)


class TestAdminUserRecord:
    """Tests for AdminUserRecord dataclass."""

    def test_admin_user_record(self, sqlite_db) -> None:

        user = UserRecord(user_id=1, username="model_admin_user")
        sqlite_db.session.add(user)
        sqlite_db.session.commit()

        admin = AdminUserRecord(username="model_admin_user", is_active=True)
        sqlite_db.session.add(admin)
        sqlite_db.session.commit()

        assert admin.id is not None
        assert admin.username == "model_admin_user"
        assert admin.is_active is True
