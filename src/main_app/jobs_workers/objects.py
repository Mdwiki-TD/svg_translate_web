from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class JobData:
    job_type: str
    job_name: str
    job_details_template: str
    job_list_template: str

    job_callable: Callable
    job_args: list[dict[str, str]] = field(default_factory=list)
    start_confirm_message: str | None = None


__all__ = [
    "JobData",
]
