from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from ..db import OwidChartRecord, TemplateRecord
from ..db import fetch_query_safe
from ..services import owid_charts_service, template_service

logger = logging.getLogger(__name__)

bp_api = Blueprint("api", __name__, url_prefix="/api")


@bp_api.get("/templates")
def templates_list():
    templates: list[TemplateRecord] = template_service.list_templates()

    data = [t.to_dict() for t in templates]

    total = len(templates)
    summary = {
        "total": total,
        "with_main_file": sum(1 for t in templates if t.main_file),
        "with_last_world_file": sum(1 for t in templates if t.last_world_file),
        "with_last_world_year": sum(1 for t in templates if t.last_world_year),
        "with_source": sum(1 for t in templates if t.source),
    }

    return jsonify({"data": data, "summary": summary})


@bp_api.get("/templates-need-update")
def templates_need_update_list():
    sql = """
        SELECT
            template_id,
            template_title,
            slug,
            max_time as chart_year,
            last_world_year as template_year
        FROM templates_need_update
        ORDER BY max_time ASC
    """
    templates = fetch_query_safe(sql, ())

    data = [
        {
            "template_id": row["template_id"],
            "template_title": row["template_title"],
            "slug": row["slug"],
            "chart_year": row["chart_year"],
            "template_year": row["template_year"],
            "difference": (
                (row["chart_year"] or 0) - (row["template_year"] or 0)
                if row["template_year"] and row["chart_year"]
                else None
            ),
        }
        for row in templates
    ]

    return jsonify(
        {
            "data": data,
        }
    )


@bp_api.get("/owid-charts")
def owid_charts_list():
    template_filter = request.args.get("template", "").strip()
    all_charts: list[OwidChartRecord] = owid_charts_service.list_charts()

    if template_filter == "has_template":
        charts = [c for c in all_charts if c.template_title]
    elif template_filter == "no_template":
        charts = [c for c in all_charts if not c.template_title]
    else:
        charts = all_charts

    total = len(all_charts)
    summary = {
        "total": total,
        "published": {
            "with": sum(1 for c in all_charts if c.is_published),
            "without": sum(1 for c in all_charts if not c.is_published),
        },
        "template": {
            "with": sum(1 for c in all_charts if c.template_id),
            "without": sum(1 for c in all_charts if not c.template_id),
        },
        "map_tab": {
            "with": sum(1 for c in all_charts if c.has_map_tab),
            "without": sum(1 for c in all_charts if not c.has_map_tab),
        },
        "timeline": {
            "with": sum(1 for c in all_charts if c.has_timeline),
            "without": sum(1 for c in all_charts if not c.has_timeline),
        },
    }

    data = [c.to_dict() for c in charts]

    return jsonify({"data": data, "summary": summary, "selected_template": template_filter})
