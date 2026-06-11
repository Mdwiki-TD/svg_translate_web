from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, func, Index
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped, mapped_column

from .views import OwidChartTemplateRecord
from ...extensions import db

logger = logging.getLogger(__name__)


class OwidChartRecord(db.Model): # type: ignore
    """
    Represents the main owid_charts table.
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

    # Core Columns
    chart_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    has_map_tab: Mapped[bool] = mapped_column(Boolean, server_default="0", default=False)
    max_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    default_tab: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    owid_variable_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, server_default="0", default=False)
    single_year_data: Mapped[bool] = mapped_column(Boolean, server_default="0", default=False)
    len_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    has_timeline: Mapped[bool] = mapped_column(Boolean, server_default="0", default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        server_onupdate=func.current_timestamp(),
    )

    # Table-level indexes as requested by the original CREATE TABLE DDL
    __table_args__ = (
        Index("idx_slug", "slug"),
        Index("idx_published", "is_published"),
    )

    # Private internal storage for overrides using Type-Hinting
    _template_id_override: Mapped[Optional[int]] = mapped_column(init=False, repr=False, default=None)
    _template_title_override: Mapped[Optional[str]] = mapped_column(init=False, repr=False, default=None)

    # Optimized relationship mapping
    _template_info: Mapped[Optional[OwidChartTemplateRecord]] = relationship(
        "OwidChartTemplateRecord",
        primaryjoin="OwidChartRecord.chart_id == OwidChartTemplateRecord.chart_id",
        foreign_keys="[OwidChartTemplateRecord.chart_id]",
        viewonly=True,
        uselist=False,
    )

    @property
    def template_id(self) -> Optional[int]:
        """Returns the template ID from the view or the local override."""
        if self._template_info is not None:
            return self._template_info.template_id
        return self._template_id_override

    @template_id.setter
    def template_id(self, value: Optional[int]) -> None:
        self._template_id_override = value

    @property
    def template_title(self) -> Optional[str]:
        """Returns the template title from the view or the local override."""
        if self._template_info is not None:
            return self._template_info.template_title
        return self._template_title_override

    @template_title.setter
    def template_title(self, value: Optional[str]) -> None:
        self._template_title_override = value

    def to_dict(self) -> dict[str, Any]:
        """Serializes the model instance into a dictionary."""
        data: dict[str, Any] = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[column.name] = value

        # Explicitly remove internal override attributes from the root data dictionary
        data.pop("_template_id_override", None)
        data.pop("_template_title_override", None)

        # Inject clean property fields
        data["template_id"] = self.template_id
        data["template_title"] = self.template_title

        return data


__all__ = [
    "OwidChartRecord",
]
