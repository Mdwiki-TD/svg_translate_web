"""
SQLAlchemy ORM models
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, SmallInteger, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from ...extensions import db

logger = logging.getLogger(__name__)


class ErrorLogRecord(db.Model):
    """
    CREATE TABLE IF NOT EXISTS error_logs (
        id bigint unsigned NOT NULL AUTO_INCREMENT,
        created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
        status_code smallint NOT NULL,
        method varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
        path varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
        query_str text COLLATE utf8mb4_unicode_ci,
        ip varchar(45) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '',
        access_route varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        has_cookie tinyint(1) NOT NULL DEFAULT '0',
        suspected_bot tinyint(1) NOT NULL DEFAULT '0',
        username varchar(120) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        user_agent varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        accept varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        accept_language varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        accept_encoding varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        referer varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        sec_fetch_mode varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        sec_fetch_dest varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        sec_ch_ua varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        request_id varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        error varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
        PRIMARY KEY (id),
        KEY idx_created_at (created_at),
        KEY idx_status_path (status_code, path(191)),
        KEY idx_request_id (request_id)
    )
    """

    __tablename__ = "error_logs"
    __table_args__ = (
        Index("idx_status_path", "status_code", "path", mysql_length={"path": 191}),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    # BigInteger on MySQL, plain Integer on SQLite so autoincrement works in tests
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )

    # What was requested
    status_code: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False, default="", server_default=text("''"))
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    query_str: Mapped[str | None] = mapped_column(Text)

    # Who asked (the ip is usually the ingress; access_route keeps the proxy chain)
    ip: Mapped[str] = mapped_column(String(45), nullable=False, default="", server_default=text("''"))
    access_route: Mapped[str | None] = mapped_column(String(255))
    has_cookie: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("0"))
    suspected_bot: Mapped[bool] = mapped_column(nullable=False, default=False, server_default=text("0"))
    username: Mapped[str | None] = mapped_column(String(120))

    # Headers that help tell bots from real browsers (never cookies or tokens)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    accept: Mapped[str | None] = mapped_column(String(500))
    accept_language: Mapped[str | None] = mapped_column(String(255))
    accept_encoding: Mapped[str | None] = mapped_column(String(255))
    referer: Mapped[str | None] = mapped_column(String(500))
    sec_fetch_mode: Mapped[str | None] = mapped_column(String(30))
    sec_fetch_dest: Mapped[str | None] = mapped_column(String(30))
    sec_ch_ua: Mapped[str | None] = mapped_column(String(255))
    request_id: Mapped[str | None] = mapped_column(String(64), index=True)

    error: Mapped[str | None] = mapped_column(String(500))
