from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class JobsRunner:
    job_id: int
    user: dict[str, Any]
    cancel_event: threading.Event | None = None
    args: dict[str, Any] | None = None
    form_data: dict[str, Any] | None = None


@dataclass
class JobData:
    job_type: str
    job_name: str
    job_class: Callable

    job_list_template: str = "jobs_templates/admin_templates/base_list_admin.html"
    job_details_template: str | None = "jobs_templates/_help_templates/shared_details.html"

    job_args: list[dict[str, str]] = field(default_factory=list)
    load_settings: bool = False
    form_class: Callable | None = None
    used_ajax_table: bool = False
    description: str = ""
    start_confirm_message: str = "Run the task?"

    ready: bool = False

    # Toolforge resource overrides (None = use global defaults from config)
    image: str | None = None
    memory: str | None = None
    cpu: str | None = None


__all__ = [
    "JobsRunner",
    "JobData",
]
