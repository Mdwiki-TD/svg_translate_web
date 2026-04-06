from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request

from ..db import TemplateRecord
from ..services import template_service

logger = logging.getLogger(__name__)

bp_api = Blueprint("api", __name__, url_prefix="/api")


def _parse_ssp_params():
    draw = request.args.get("draw", type=int) or request.form.get("draw", type=int) or 0
    start = request.args.get("start", type=int) or request.form.get("start", type=int) or 0
    length = request.args.get("length", type=int) or request.form.get("length", type=int) or 10
    search_value = request.args.get("search[value]") or request.form.get("search[value]") or ""
    order_column = request.args.get("order[0][column]") or request.form.get("order[0][column]") or "0"
    order_dir = request.args.get("order[0][dir]") or request.form.get("order[0][dir]") or "asc"

    return {
        "draw": draw,
        "start": start,
        "length": length,
        "search_value": search_value,
        "order_column": int(order_column),
        "order_dir": order_dir,
    }


COLUMNS_MAP = {
    0: "id",
    1: "title",
    2: "main_file",
    3: "last_world_file",
    4: "last_world_year",
    5: "source",
}


def _build_template_row(template: TemplateRecord, index: int) -> list:
    return [
        index + 1,
        f'<a href="https://commons.wikimedia.org/wiki/{template.title}" target="_blank" rel="noopener noreferrer">{template.title}</a>',
        (
            f'<a href="https://commons.wikimedia.org/wiki/File:{template.main_file}" target="_blank" rel="noopener noreferrer">{template.main_file}</a>'
            if template.main_file
            else ""
        ),
        (
            f'<a href="https://commons.wikimedia.org/wiki/File:{template.last_world_file}" target="_blank" rel="noopener noreferrer">{template.last_world_file}</a>'
            if template.last_world_file
            else ""
        ),
        template.last_world_year or "",
        (
            f'<a href="{template.source}" target="_blank" rel="noopener noreferrer">{template.source[:50]}...</a>'
            if template.source
            else ""
        ),
    ]


@bp_api.get("/templates")
@bp_api.post("/templates")
def templates_list():
    try:
        params = _parse_ssp_params()
        templates: list[TemplateRecord] = template_service.list_templates()

        records_total = len(templates)

        search_value = params["search_value"].lower()
        if search_value:
            templates = [
                t
                for t in templates
                if search_value in (t.title or "").lower()
                or search_value in (t.main_file or "").lower()
                or search_value in (t.last_world_file or "").lower()
                or search_value in (t.source or "").lower()
            ]

        records_filtered = len(templates)

        order_col = COLUMNS_MAP.get(params["order_column"], "id")
        reverse = params["order_dir"] == "desc"
        templates = sorted(templates, key=lambda t: getattr(t, order_col, "") or "", reverse=reverse)

        start = params["start"]
        length = params["length"]
        paginated = templates[start : start + length] if length > 0 else templates

        data = [_build_template_row(t, start + i) for i, t in enumerate(paginated)]

        return jsonify(
            {
                "draw": params["draw"],
                "recordsTotal": records_total,
                "recordsFiltered": records_filtered,
                "data": data,
            }
        )
    except Exception as exc:
        logger.exception("Failed to fetch templates for DataTables")
        return jsonify({"error": str(exc), "draw": 0, "recordsTotal": 0, "recordsFiltered": 0, "data": []}), 500
