from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, jsonify

from ..db.models import OwidChartRecord, OwidChartTemplateRecord, TemplateRecord
from ..db.services import (
    list_charts,
    list_owid_charts_templates,
    list_templates,
    list_templates_need_update,
)

logger = logging.getLogger(__name__)

bp_api = Blueprint("api", __name__, url_prefix="/api")


@bp_api.get("/templates")
def templates_list():
    templates: list[TemplateRecord] = list_templates()

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
    templates = list_templates_need_update()

    data = [t.to_dict() for t in templates]

    return jsonify({"data": data})


@bp_api.get("/charts_templates")
def charts_templates():
    all_charts_templates: list[OwidChartTemplateRecord] = list_owid_charts_templates()

    data = [c.to_dict() for c in all_charts_templates if c.template_id]
    return jsonify(data)


@bp_api.get("/owidcharts/")
@bp_api.get("/owidcharts/<string:template_filter>")
def owid_charts_list(template_filter: str = ""):
    all_charts: list[OwidChartRecord] = list_charts()
    all_charts_templates: list[OwidChartTemplateRecord] = list_owid_charts_templates()

    charts_temps = {c.chart_id: c for c in all_charts_templates}

    if template_filter == "has_template":
        charts = [c for c in all_charts if charts_temps.get(c.chart_id)]
    elif template_filter == "no_template":
        charts = [c for c in all_charts if not charts_temps.get(c.chart_id)]
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
            "with": sum(1 for c in all_charts if charts_temps.get(c.chart_id)),
            "without": sum(1 for c in all_charts if not charts_temps.get(c.chart_id)),
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

    data: list[dict[str, Any]] = []
    for c in charts:
        c_json = c.to_dict()
        temp = charts_temps.get(c.chart_id)
        c_json["template_id"] = temp.template_id if temp else None
        c_json["template_title"] = temp.template_title if temp else None
        data.append(c_json)

    return jsonify({"data": data, "summary": summary, "selected_template": template_filter})


__all__ = [
    "bp_api",
]
