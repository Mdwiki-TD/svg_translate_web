from __future__ import annotations

import logging

from flask import Blueprint, jsonify

from ..db import TemplateRecord
from ..services import template_service

logger = logging.getLogger(__name__)

bp_api = Blueprint("api", __name__, url_prefix="/api")


def _build_template_row(template: TemplateRecord) -> dict:
    return {
        "id": template.id,
        "title": template.title,
        "main_file": template.main_file,
        "last_world_file": template.last_world_file,
        "last_world_year": template.last_world_year,
        "source": template.source,
    }


@bp_api.get("/templates")
def templates_list():
    templates: list[TemplateRecord] = template_service.list_templates()

    data = [_build_template_row(t) for t in templates]

    return jsonify({"data": data, })
