
from dataclasses import dataclass


@dataclass
class BackgroundJob:
    id: str
    hour: int
    minute: int
    func: callable
    upload_host: str
    job_scheduler: None


jobs_data = {}
