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
    job_details_template: str
    job_list_template: str

    job_class: Callable
    job_args: list[dict[str, str]] = field(default_factory=list)
    start_confirm_message: str | None = None
    load_settings: bool = False
    form_class: Callable | None = None
    used_ajax_table: bool = False


__all__ = [
    "JobsRunner",
    "JobData",
]
