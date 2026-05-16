from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from ..sqlalchemy_db.models import OwidChartRecord, TemplateRecord
from ..sqlalchemy_db.services import (
    list_templates,
    list_templates_need_update,
    list_charts,
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


@bp_api.get("/owid-charts")
def owid_charts_list():
    template_filter = request.args.get("template", "").strip()
    all_charts: list[OwidChartRecord] = list_charts()

    if template_filter == "has_template":
        charts = [c for c in all_charts if c.template_title is not None]
    elif template_filter == "no_template":
        charts = [c for c in all_charts if c.template_title is None]
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
            "with": sum(1 for c in all_charts if c.template_title is not None),
            "without": sum(1 for c in all_charts if c.template_title is None),
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
