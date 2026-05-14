"""Persistence helpers for storing encrypted OAuth tokens."""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict, Optional

from ..core.crypto import encrypt_value
from ..db import get_db, has_db_config
from ..db.sql_schema_tables import sql_tables
from ..shared.models.users_record import UserTokenRecord
from ..sqlalchemy_db.decode_bytes import coerce_bytes

logger = logging.getLogger(__name__)


def _current_ts() -> str:
    # Store in UTC. MySQL DATETIME has no TZ; keep application-level UTC.
    """
    Return the current UTC timestamp formatted for MySQL DATETIME.

    Returns:
        A string of the current UTC time in the format "YYYY-MM-DD HH:MM:SS".
    """
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")


def mark_token_used(user_id: int) -> None:
    """Update the last-used timestamp for the given user token."""

    db = get_db()
    try:
        db.execute_query(
            "UPDATE user_tokens SET last_used_at = CURRENT_TIMESTAMP WHERE user_id = %s",
            (user_id,),
        )
    except Exception:
        logger.exception("Failed to update last_used_at for user %s", user_id)


def ensure_user_token_table() -> None:
    """Create the user_tokens table if it does not already exist."""

    if not has_db_config():
        logger.debug("Skipping user token table creation; MySQL configuration missing.")
        return

    db = get_db()
    db.execute_query_safe(sql_tables.user_tokens)


def upsert_user_token(*, user_id: int, username: str, access_key: str, access_secret: str) -> None:
    """Insert or update the encrypted OAuth credentials for a user."""

    db = get_db()
    now = _current_ts()
    encrypted_token = encrypt_value(access_key)
    encrypted_secret = encrypt_value(access_secret)
    return db.execute_query_safe(
        """
            INSERT INTO user_tokens (
                user_id,
                username,
                access_token,
                access_secret,
                created_at,
                updated_at,
                last_used_at,
                rotated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, NULL)
            ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                access_token = VALUES(access_token),
                access_secret = VALUES(access_secret),
                updated_at = VALUES(updated_at),
                last_used_at = VALUES(last_used_at),
                rotated_at = CURRENT_TIMESTAMP
            """,
        (
            user_id,
            username,
            encrypted_token,
            encrypted_secret,
            now,
            now,
            now,
        ),
    )


def get_user_token(user_id: str | int) -> Optional[UserTokenRecord]:
    """Fetch the encrypted OAuth credentials for a user."""
    user_id = int(user_id) if isinstance(user_id, str) else user_id

    db = get_db()
    rows: list[Dict[str, Any]] = db.fetch_query_safe(
        """
        SELECT
            user_id,
            username,
            access_token,
            access_secret,
            created_at,
            updated_at,
            last_used_at,
            rotated_at
        FROM user_tokens
        WHERE user_id = %s
        """,
        (user_id,),
    )
    if not rows:
        return None

    row = rows[0]
    return UserTokenRecord(
        user_id=row["user_id"],
        username=row["username"],
        access_token=coerce_bytes(row["access_token"]),
        access_secret=coerce_bytes(row["access_secret"]),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
        last_used_at=row.get("last_used_at"),
        rotated_at=row.get("rotated_at"),
    )


def delete_user_token(user_id: int) -> None:
    """Remove the stored OAuth credentials for the given user id."""

    db = get_db()
    db.execute_query_safe("DELETE FROM user_tokens WHERE user_id = %s", (user_id,))
