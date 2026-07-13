""" """

from __future__ import annotations

import logging
from typing import Any

from ...extensions import db
from ..models import (
    AdminUserRecord,
    JobRecord,
    OwidChartRecord,
    OwidSlugRedirectRecord,
    SettingRecord,
    TemplateRecord,
    UserRecord,
    UserTokenRecord,
)

logger = logging.getLogger(__name__)


def delete_record_by_pk(model: type[db.Model], pk_value: Any) -> bool:  # type: ignore
    """
    Generic helper to delete a record by its primary key.
    Returns True if deleted, False otherwise.
    """
    if pk_value is None:
        return False

    try:
        # Use session.get() as it is efficient and looks up by primary key
        record = db.session.get(model, pk_value)
        if record:
            db.session.delete(record)
            db.session.commit()
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting {model.__name__} with PK {pk_value}: {e}")
        db.session.rollback()
        return False


def delete_user_token(user_id: int) -> bool:
    return delete_record_by_pk(UserTokenRecord, user_id)


def delete_user(user_id: int) -> bool:
    return delete_record_by_pk(UserRecord, user_id)


def delete_setting_by_key(key: str) -> bool:
    setting = SettingRecord.query.filter_by(key=key).first()
    if setting:
        return delete_record_by_pk(SettingRecord, setting.id)
    return False


def delete_coordinator(coordinator_id: int) -> bool:
    return delete_record_by_pk(AdminUserRecord, coordinator_id)


def delete_job(job_id: int, job_type: str) -> bool:
    """
    Special case since it filters by multiple columns (id and job_type).
    """
    try:
        affected_rows = (
            db.session.query(JobRecord)
            .filter(JobRecord.id == job_id, JobRecord.job_type == job_type)
            .delete(synchronize_session=False)
        )
        db.session.commit()
        return affected_rows > 0
    except Exception as e:
        logger.error(f"Error deleting JobRecord: {e}")
        db.session.rollback()
        return False


def delete_template(template_id: int) -> bool:
    return delete_record_by_pk(TemplateRecord, template_id)


def delete_slug_redirect(redirect_id: int) -> bool:
    return delete_record_by_pk(OwidSlugRedirectRecord, redirect_id)


def delete_chart(chart_id: int) -> bool:
    return delete_record_by_pk(OwidChartRecord, chart_id)


class DeleteService:
    def __init__(self) -> None:
        pass

    def delete_record_by_pk(self, model: type[db.Model], pk_value: Any) -> bool:  # type: ignore
        return delete_record_by_pk(model, pk_value)

    def delete_user_token(self, user_id: int) -> bool:
        return delete_user_token(user_id)

    def delete_user(self, user_id: int) -> bool:
        return delete_user(user_id)

    def delete_setting_by_key(self, key: str) -> bool:
        return delete_setting_by_key(key)

    def delete_coordinator(self, coordinator_id: int) -> bool:
        return delete_coordinator(coordinator_id)

    def delete_job(self, job_id: int, job_type: str) -> bool:
        return delete_job(job_id, job_type)

    def delete_template(self, template_id: int) -> bool:
        return delete_template(template_id)

    def delete_slug_redirect(self, redirect_id: int) -> bool:
        return delete_slug_redirect(redirect_id)

    def delete_chart(self, chart_id: int) -> bool:
        return delete_chart(chart_id)


__all__ = [
    "DeleteService",
    "delete_record_by_pk",
    "delete_user",
    "delete_user_token",
    "delete_coordinator",
    "delete_job",
    "delete_chart",
    "delete_setting_by_key",
    "delete_slug_redirect",
    "delete_template",
]
