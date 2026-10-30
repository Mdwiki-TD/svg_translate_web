"""
Service layer for the error_logs table
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from flask import request
from flask import session as flask_session
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ...extensions import db
from ..models.error_log_models import ErrorLogRecord
from .crud_service import CRUDService  # adjust to where CRUDService lives in your project

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Naive UTC now, matching how created_at is compared in queries."""
    return datetime.now(UTC).replace(tzinfo=None)


def _cut(value: Any, limit: int) -> str | None:
    """Convert to str and truncate so a long value can never break the INSERT."""
    if value is None:
        return None
    return str(value)[:limit]


class ErrorLogService(CRUDService[ErrorLogRecord]):
    model = ErrorLogRecord

    def __init__(self):
        super().__init__(db.session, ErrorLogRecord)

    def log_request(
        self,
        status_code: int,
        error: Exception | str,
        *,
        query: str = "",
        ip: str = "",
    ) -> None:
        """
        Store the current failed request.

        `query` must already be redacted and `ip` already resolved by the caller.
        This method never raises: logging must not break the error page itself.
        """
        try:
            headers = request.headers
            record = ErrorLogRecord(
                status_code=status_code,
                method=_cut(request.method, 10) or "",
                path=_cut(request.path, 500) or "",
                query_str=_cut(query, 2000) or None,
                ip=_cut(ip, 45) or "",
                access_route=_cut(",".join(request.access_route), 255),
                has_cookie="Cookie" in headers,
                # Heuristic only: real browsers always send Sec-Fetch-* headers
                suspected_bot="Sec-Fetch-Mode" not in headers,
                username=_cut(flask_session.get("username"), 120),
                user_agent=_cut(headers.get("User-Agent"), 500),
                accept=_cut(headers.get("Accept"), 500),
                accept_language=_cut(headers.get("Accept-Language"), 255),
                accept_encoding=_cut(headers.get("Accept-Encoding"), 255),
                referer=_cut(headers.get("Referer"), 500),
                sec_fetch_mode=_cut(headers.get("Sec-Fetch-Mode"), 30),
                sec_fetch_dest=_cut(headers.get("Sec-Fetch-Dest"), 30),
                sec_ch_ua=_cut(headers.get("Sec-Ch-Ua"), 255),
                request_id=_cut(headers.get("X-Request-Id"), 64),
                error=_cut(error, 500),
            )

            # Separate session: a failed request transaction must not affect (or be
            # affected by) the log write, e.g. when the original error was a DB error
            with Session(db.engine) as log_session:
                log_session.add(record)
                log_session.commit()
        except Exception:
            logger.warning("Could not write error log to the database", exc_info=True)

    def top_paths(self, days: int = 7, limit: int = 20) -> list[dict[str, Any]]:
        """Most requested failing paths in the last `days` days."""
        since = _utcnow() - timedelta(days=days)
        stmt = (
            select(
                ErrorLogRecord.path,
                ErrorLogRecord.status_code,
                func.count().label("hits"),
                func.sum(ErrorLogRecord.suspected_bot).label("bot_hits"),
                func.max(ErrorLogRecord.created_at).label("last_seen"),
            )
            .where(ErrorLogRecord.created_at >= since)
            .group_by(ErrorLogRecord.path, ErrorLogRecord.status_code)
            .order_by(func.count().desc())
            .limit(limit)
        )
        rows = self.session.execute(stmt).all()
        return [
            {
                "path": r.path,
                "status_code": r.status_code,
                "hits": r.hits,
                "bot_hits": int(r.bot_hits or 0),
                "last_seen": r.last_seen,
            }
            for r in rows
        ]

    def search(
        self,
        *,
        days: int = 7,
        status_code: int | None = None,
        path: str = "",
        ip: str = "",
        suspected_bot: bool | None = None,
        page: int = 1,
        per_page: int = 50,
    ):
        """Return a paginated, newest-first list of rows matching the filters."""
        since = _utcnow() - timedelta(days=days)
        stmt = (
            select(ErrorLogRecord)
            .where(ErrorLogRecord.created_at >= since)
            .order_by(ErrorLogRecord.created_at.desc(), ErrorLogRecord.id.desc())
        )
        if status_code is not None:
            stmt = stmt.where(ErrorLogRecord.status_code == status_code)
        if path:
            # autoescape stops user-typed % and _ from acting as wildcards
            stmt = stmt.where(ErrorLogRecord.path.contains(path, autoescape=True))
        if ip:
            stmt = stmt.where(ErrorLogRecord.ip == ip)
        if suspected_bot is not None:
            stmt = stmt.where(ErrorLogRecord.suspected_bot.is_(suspected_bot))

        return db.paginate(stmt, page=page, per_page=per_page, max_per_page=200, error_out=False)

    def status_summary(self, days: int = 7) -> list[dict[str, Any]]:
        """Hit counts per status code in the last `days` days."""
        since = _utcnow() - timedelta(days=days)
        stmt = (
            select(
                ErrorLogRecord.status_code,
                func.count().label("hits"),
                func.sum(ErrorLogRecord.suspected_bot).label("bot_hits"),
            )
            .where(ErrorLogRecord.created_at >= since)
            .group_by(ErrorLogRecord.status_code)
            .order_by(ErrorLogRecord.status_code)
        )
        return [
            {"status_code": r.status_code, "hits": r.hits, "bot_hits": int(r.bot_hits or 0)}
            for r in self.session.execute(stmt).all()
        ]

    def purge_older_than(self, days: int = 30) -> int:
        """Delete old rows to keep the table small; returns the number of deleted rows."""
        cutoff = _utcnow() - timedelta(days=days)
        result = self.session.execute(delete(ErrorLogRecord).where(ErrorLogRecord.created_at < cutoff))
        # CRUDService.commit() rolls back on failure, so the session stays usable
        self.commit()
        return result.rowcount or 0
