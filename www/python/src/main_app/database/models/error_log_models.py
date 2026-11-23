"""
SQLAlchemy ORM models

Two tables:
- error_logs:       detailed, one row per failed request (kept ~7 days, purged weekly)
- error_log_daily:  one row per (day, status_code, path), only counters (kept long-term)
"""

from __future__ import annotations

import logging
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

from ..db_base import Model

logger = logging.getLogger(__name__)


class ErrorLogRecord(Model):
    """
    Detailed log: one row per failed request. Old rows are purged periodically
    (see ErrorLogService.purge_older_than); totals live in error_log_daily.

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
        Index("idx_created_at", "created_at"),
        Index("idx_status_path", "status_code", "path", mysql_length={"path": 191}),
        Index("idx_request_id", "request_id"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    # BigInteger on MySQL, plain Integer on SQLite so autoincrement works in tests
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql").with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # What was requested
    status_code: Mapped[int] = mapped_column(SmallInteger)
    method: Mapped[str] = mapped_column(String(10), default="", server_default=text("''"))
    path: Mapped[str] = mapped_column(String(500))
    query_str: Mapped[str | None] = mapped_column(Text)

    # Who asked (the ip is usually the ingress; access_route keeps the proxy chain)
    ip: Mapped[str] = mapped_column(String(45), default="", server_default=text("''"))
    access_route: Mapped[str | None] = mapped_column(String(255))
    has_cookie: Mapped[bool] = mapped_column(default=False, server_default=text("0"))
    suspected_bot: Mapped[bool] = mapped_column(default=False, server_default=text("0"))
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
    request_id: Mapped[str | None] = mapped_column(String(64))

    error: Mapped[str | None] = mapped_column(String(500))

    @classmethod
    def load(cls, **data):
        return cls(**data)


class ErrorLogDaily(Model):
    """
    Long-term counters: one row per (day, status_code, path).

    The path is stored WITHOUT the query string, so /x.php?a=1 and /x.php?a=2
    share one row. `path_hash` (md5 of the path) is what the unique key uses,
    because a unique index over a 500-char utf8mb4 column is too long.

    CREATE TABLE IF NOT EXISTS error_log_daily (
        id bigint unsigned NOT NULL AUTO_INCREMENT,
        day date NOT NULL,
        status_code smallint NOT NULL,
        path varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
        path_hash char(32) COLLATE utf8mb4_unicode_ci NOT NULL,
        hits int NOT NULL DEFAULT 0,
        bot_hits int NOT NULL DEFAULT 0,
        last_seen datetime NOT NULL,
        PRIMARY KEY (id),
        UNIQUE KEY uq_day_status_path (day, status_code, path_hash),
        KEY idx_daily_path_day (path_hash, day)
    ) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """

    __tablename__ = "error_log_daily"
    __table_args__ = (
        UniqueConstraint("day", "status_code", "path_hash", name="uq_day_status_path"),
        Index("idx_daily_path_day", "path_hash", "day"),
        {"mysql_charset": "utf8mb4", "mysql_collate": "utf8mb4_unicode_ci"},
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql").with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    day: Mapped[date]
    status_code: Mapped[int] = mapped_column(SmallInteger)
    path: Mapped[str] = mapped_column(String(500))
    path_hash: Mapped[str] = mapped_column(String(32))
    hits: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    bot_hits: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    last_seen: Mapped[datetime]


__all__ = [
    "ErrorLogDaily",
    "ErrorLogRecord",
]
