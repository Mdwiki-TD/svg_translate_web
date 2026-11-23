"""
Service layer for the error_logs and error_log_daily tables

- error_logs:       detailed rows, purged weekly (see purge_older_than)
- error_log_daily:  per-day counters per (status_code, path), kept long-term;
                    all statistics (top paths, status summary) are read from here
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any

from flask import request
from flask import session as flask_session
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import Session

from ..db_base import db
from ..models.error_log_models import ErrorLogDaily, ErrorLogRecord
from .crud_service import CRUDService

logger = logging.getLogger(__name__)

# How long detailed rows are kept before the weekly purge removes them
DETAIL_RETENTION_DAYS = 7


class BackfillAlreadyDoneError(RuntimeError):
    """Raised when error_log_daily already contains data built from rows older than `before`."""


def _utcnow() -> datetime:
    """Naive UTC now, matching how created_at is compared in queries."""
    return datetime.now(UTC).replace(tzinfo=None)


def _cut(value: Any, limit: int) -> str | None:
    """Convert to str and truncate so a long value can never break the INSERT."""
    if value is None:
        return None
    return str(value)[:limit]


def _path_hash(path: str) -> str:
    """md5 of the (already truncated) path; same value as MySQL MD5(path) on utf8mb4."""
    return hashlib.md5(path.encode("utf-8")).hexdigest()


def _bump_daily(
    s: Session,
    *,
    status_code: int,
    path: str,
    suspected_bot: bool,
    now: datetime,
) -> None:
    """
    Add one hit to today's counter for (status_code, path).

    Runs inside the caller's transaction so the detailed row and the counter
    are committed (or rolled back) together.
    """
    day = now.date()
    path_hash = _path_hash(path)
    bot = int(suspected_bot)
    table = ErrorLogDaily.__table__

    if s.get_bind().dialect.name == "mysql":
        stmt = mysql_insert(ErrorLogDaily).values(
            day=day,
            status_code=status_code,
            path=path,
            path_hash=path_hash,
            hits=1,
            bot_hits=bot,
            last_seen=now,
        )
        stmt = stmt.on_duplicate_key_update(
            hits=table.c.hits + 1,
            bot_hits=table.c.bot_hits + bot,
            last_seen=now,
        )
        s.execute(stmt)
        return

    # Portable fallback (SQLite in tests): update first, insert if nothing matched
    result = s.execute(
        update(ErrorLogDaily)
        .where(
            ErrorLogDaily.day == day,
            ErrorLogDaily.status_code == status_code,
            ErrorLogDaily.path_hash == path_hash,
        )
        .values(
            hits=ErrorLogDaily.hits + 1,
            bot_hits=ErrorLogDaily.bot_hits + bot,
            last_seen=now,
        )
    )
    if not result.rowcount:  # pyright: ignore[reportAttributeAccessIssue]
        s.add(
            ErrorLogDaily(
                day=day,
                status_code=status_code,
                path=path,
                path_hash=path_hash,
                hits=1,
                bot_hits=bot,
                last_seen=now,
            )
        )


def _since_day(days: int) -> date:
    """First calendar day (exclusive) of a 'last N days' window in error_log_daily."""
    return _utcnow().date() - timedelta(days=days)


class ErrorLogService(CRUDService[ErrorLogRecord]):
    model = ErrorLogRecord

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(session=session or db.session)

    # ------------------------------------------------------------------ write

    def log_request(
        self,
        status_code: int,
        error: Exception | str,
        *,
        query: str = "",
        ip: str = "",
    ) -> None:
        """
        Store the current failed request: one detailed row plus the daily counter.

        `query` must already be redacted and `ip` already resolved by the caller.
        This method never raises: logging must not break the error page itself.
        """
        try:
            headers = request.headers
            record = self.model.load(
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
                _bump_daily(
                    log_session,
                    status_code=record.status_code,
                    path=record.path,
                    suspected_bot=record.suspected_bot,
                    now=_utcnow(),
                )
                log_session.commit()
        except Exception:
            logger.warning("Could not write error log to the database", exc_info=True)

    # ------------------------------------------------- statistics (long-term)

    def top_paths(self, days: int | None = 7, limit: int = 20) -> list[dict[str, Any]]:
        """
        Most requested failing paths, read from the daily counters.

        `days=None` means all time.
        """
        D = ErrorLogDaily
        total = func.sum(D.hits)
        stmt = (
            select(
                D.path,
                D.status_code,
                total.label("hits"),
                func.sum(D.bot_hits).label("bot_hits"),
                func.max(D.last_seen).label("last_seen"),
            )
            .group_by(D.path_hash, D.path, D.status_code)
            .order_by(total.desc())
            .limit(limit)
        )
        if days is not None:
            stmt = stmt.where(D.day > _since_day(days))

        return [
            {
                "path": r.path,
                "status_code": r.status_code,
                "hits": int(r.hits or 0),
                "bot_hits": int(r.bot_hits or 0),
                "last_seen": r.last_seen,
            }
            for r in self.session.execute(stmt).all()
        ]

    def top_paths_for_day(self, day: date, limit: int = 20) -> list[dict[str, Any]]:
        """Top failing paths for one specific day."""
        D = ErrorLogDaily
        stmt = (
            select(D.path, D.status_code, D.hits, D.bot_hits, D.last_seen)
            .where(D.day == day)
            .order_by(D.hits.desc())
            .limit(limit)
        )
        return [
            {
                "path": r.path,
                "status_code": r.status_code,
                "hits": int(r.hits),
                "bot_hits": int(r.bot_hits),
                "last_seen": r.last_seen,
            }
            for r in self.session.execute(stmt).all()
        ]

    def path_history(self, path: str, days: int = 30) -> list[dict[str, Any]]:
        """Per-day hit counts for one path (all status codes summed), oldest first."""
        D = ErrorLogDaily
        stmt = (
            select(D.day, func.sum(D.hits).label("hits"), func.sum(D.bot_hits).label("bot_hits"))
            .where(D.path_hash == _path_hash(path), D.day > _since_day(days))
            .group_by(D.day)
            .order_by(D.day)
        )
        return [
            {"day": r.day, "hits": int(r.hits or 0), "bot_hits": int(r.bot_hits or 0)}
            for r in self.session.execute(stmt).all()
        ]

    def status_summary(self, days: int | None = 7) -> list[dict[str, Any]]:
        """Hit counts per status code, read from the daily counters (`None` = all time)."""
        D = ErrorLogDaily
        stmt = (
            select(
                D.status_code,
                func.sum(D.hits).label("hits"),
                func.sum(D.bot_hits).label("bot_hits"),
            )
            .group_by(D.status_code)
            .order_by(D.status_code)
        )
        if days is not None:
            stmt = stmt.where(D.day > _since_day(days))

        return [
            {"status_code": r.status_code, "hits": int(r.hits or 0), "bot_hits": int(r.bot_hits or 0)}
            for r in self.session.execute(stmt).all()
        ]

    # ------------------------------------------------ detailed rows (short-term)

    def search(
        self,
        *,
        days: int = DETAIL_RETENTION_DAYS,
        status_code: int | None = None,
        path: str = "",
        ip: str = "",
        suspected_bot: bool | None = None,
        page: int = 1,
        per_page: int = 50,
    ):
        """
        Return a paginated, newest-first list of detailed rows matching the filters.

        Only covers the retention window of error_logs (older rows are purged;
        use the daily counters for long-term numbers).
        """
        since = _utcnow() - timedelta(days=days)
        stmt = (
            select(ErrorLogRecord)
            .where(self.model.created_at >= since)
            .order_by(self.model.created_at.desc(), self.model.id.desc())
        )
        if status_code is not None:
            stmt = stmt.where(self.model.status_code == status_code)
        if path:
            # autoescape stops user-typed % and _ from acting as wildcards
            stmt = stmt.where(self.model.path.contains(path, autoescape=True))
        if ip:
            stmt = stmt.where(self.model.ip == ip)
        if suspected_bot is not None:
            stmt = stmt.where(self.model.suspected_bot.is_(suspected_bot))

        return db.paginate(stmt, page=page, per_page=per_page, max_per_page=200, error_out=False)

    # ------------------------------------------------------------ maintenance

    def purge_older_than(self, days: int = DETAIL_RETENTION_DAYS, batch: int = 5000) -> int:
        """
        Delete old detailed rows in small batches (so the table is not locked for long).

        Totals are not affected: they live in error_log_daily. Returns the number
        of deleted rows. Refuses to run while error_log_daily is empty but
        error_logs has rows, i.e. before backfill_daily() was run.
        """
        has_daily = self.session.execute(select(ErrorLogDaily.id).limit(1)).first() is not None
        has_detail = self.session.execute(select(ErrorLogRecord.id).limit(1)).first() is not None
        if has_detail and not has_daily:
            logger.warning("error_log_daily is empty; run backfill_daily() before purging error_logs")
            return 0

        cutoff = _utcnow() - timedelta(days=days)
        total = 0
        while True:
            stmt = delete(ErrorLogRecord).where(ErrorLogRecord.created_at < cutoff)
            if self.dialect_name == "mysql":
                stmt = stmt.with_dialect_options(mysql_limit=batch)

            deleted = self.session.execute(stmt).rowcount or 0  # pyright: ignore[reportAttributeAccessIssue]

            # rolls back on failure, so the session stays usable
            self.commit_or_rollback()
            total += deleted
            if deleted < batch:
                return total

    def backfill_daily(self, before: datetime) -> int:
        """
        One-time migration (MySQL): aggregate existing error_logs rows older than
        `before` into error_log_daily.

        `before` must be the moment the new logging code was deployed. The counts
        are ADDED to existing rows, so this must run exactly once.

        Guard: rows written by the live counter always have last_seen >= the deploy
        time, so any row with last_seen < `before` can only come from an earlier
        backfill. In that case this raises BackfillAlreadyDoneError and changes nothing.

        To redo a backfill on purpose: TRUNCATE TABLE error_log_daily, then run it
        again with `before` = now. Only do this while error_logs still holds all the
        data, i.e. before the first purge.
        """
        already_done = self.session.execute(
            select(ErrorLogDaily.id).where(ErrorLogDaily.last_seen < before).limit(1)
        ).first()
        if already_done is not None:
            raise BackfillAlreadyDoneError(
                f"error_log_daily already contains rows older than {before:%Y-%m-%d %H:%M:%S}; "
                "running the backfill again would double-count them. Nothing was changed."
            )

        result = self.session.execute(
            text("""
                INSERT INTO error_log_daily
                    (day, status_code, path, path_hash, hits, bot_hits, last_seen)
                SELECT DATE(created_at), status_code, path, MD5(path),
                       COUNT(*), SUM(suspected_bot), MAX(created_at)
                FROM error_logs
                WHERE created_at < :before
                GROUP BY DATE(created_at), status_code, path
                ON DUPLICATE KEY UPDATE
                    hits = error_log_daily.hits + VALUES(hits),
                    bot_hits = error_log_daily.bot_hits + VALUES(bot_hits),
                    last_seen = GREATEST(error_log_daily.last_seen, VALUES(last_seen))
                """),
            {"before": before},
        )
        self.commit_or_rollback()
        return result.rowcount or 0  # pyright: ignore[reportAttributeAccessIssue]


__all__ = [
    "DETAIL_RETENTION_DAYS",
    "BackfillAlreadyDoneError",
    "ErrorLogService",
]
