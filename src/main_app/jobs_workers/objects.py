from dataclasses import dataclass
from typing import Callable


@dataclass
class JobData:
    job_type: str
    job_name: str
    job_details_template: str
    job_list_template: str

    job_callable: Callable
    job_args: list | None = None
    start_confirm_message: str | None = None
