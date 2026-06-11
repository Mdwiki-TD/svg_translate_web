from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from ...extensions import db

logger = logging.getLogger(__name__)


class OwidChartRecord(db.Model):
    """
    CREATE TABLE `owid_charts` (
        `chart_id` int(11) NOT NULL AUTO_INCREMENT,
        `slug` varchar(255) NOT NULL,
        `title` varchar(500) NOT NULL,
        `has_map_tab` tinyint(1) DEFAULT 0,
        `max_time` int(11) DEFAULT NULL,
        `min_time` int(11) DEFAULT NULL,
        `default_tab` varchar(50) DEFAULT NULL,
        `owid_variable_id` int(11) DEFAULT NULL,
        `is_published` tinyint(1) DEFAULT 0,
        `single_year_data` tinyint(1) DEFAULT 0,
        `len_years` int(11) DEFAULT NULL,
        `has_timeline` tinyint(1) DEFAULT 0,
        `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
        `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
        PRIMARY KEY (`chart_id`),
        UNIQUE KEY `unique_slug` (`slug`),
        KEY `idx_slug` (`slug`),
        KEY `idx_published` (`is_published`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
    """

    __tablename__ = "owid_charts"

    chart_id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String(255), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    has_map_tab = Column(Boolean, server_default="0")
    max_time = Column(Integer, nullable=True)
    min_time = Column(Integer, nullable=True)
    default_tab = Column(String(50), nullable=True)
    owid_variable_id = Column(Integer, nullable=True)
    is_published = Column(Boolean, server_default="0")
    single_year_data = Column(Boolean, server_default="0")
    len_years = Column(Integer, nullable=True)
    has_timeline = Column(Boolean, server_default="0")

    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )

    _template_info = relationship(
        "OwidChartTemplateRecord",
        primaryjoin="OwidChartRecord.chart_id == OwidChartTemplateRecord.chart_id",
        foreign_keys="OwidChartTemplateRecord.chart_id",
        viewonly=True,
        uselist=False,
    )

    @property
    def template_id(self) -> int | None:
        if hasattr(self, "_template_info") and self._template_info:
            return self._template_info.template_id
        return getattr(self, "_template_id_override", None)

    @property
    def template_title(self) -> str | None:
        if hasattr(self, "_template_info") and self._template_info:
            return self._template_info.template_title
        return getattr(self, "_template_title_override", None)

    @template_title.setter
    def template_title(self, value: str | None) -> None:
        self._template_title_override = value

    @template_id.setter
    def template_id(self, value: int | None) -> None:
        self._template_id_override = value

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for column in self.__table__.columns:  # pyright: ignore[reportAttributeAccessIssue]
            value = getattr(self, column.name)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[column.name] = value

        data["template_id"] = self.template_id or None
        data["template_title"] = self.template_title or None

        return data


__all__ = [
    "OwidChartRecord",
]
