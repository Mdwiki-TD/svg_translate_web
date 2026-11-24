"""Toolforge Jobs API backend: runs jobs as Kubernetes pods."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from requests import HTTPError

from ...api_services.clients.toolforge import ToolforgeJobsService
from ...config import Settings, get_settings
from ...database.models import JobRecord
from ...jobs_workers.objects import JobData
from .base import JobBackend

logger = logging.getLogger(__name__)


def tf_job_name(job_type: str, job_id: int) -> str:
    """Derive a Toolforge-compatible job name from the DB type and id.

    Toolforge names: 1-52 chars, lowercase, digits, '-' and '.' only.
    """
    slug = re.sub(r"[^a-z0-9.\-]+", "-", job_type.lower()).strip("-.")[:40]
    return f"{slug}-{job_id}"


class ToolforgeBackend(JobBackend):
    """Runs jobs as one-off Kubernetes pods via the Toolforge Jobs API."""

    def __init__(
        self,
        svc: ToolforgeJobsService | None = None,
        app_settings: Settings | None = None,
    ) -> None:
        self.app_settings = app_settings or get_settings()
        self.svc = svc or ToolforgeJobsService()

    def start(
        self,
        job: JobRecord,
        job_data: JobData,
        payload: dict[str, Any],
    ) -> str:
        jobs_cfg = self.app_settings.jobs

        name = tf_job_name(job.job_type, job.id)
        image = job_data.image or jobs_cfg.toolforge_job_image
        memory = job_data.memory or jobs_cfg.toolforge_job_default_memory
        cpu = job_data.cpu or jobs_cfg.toolforge_job_default_cpu
        script = jobs_cfg.toolforge_job_script
        cmd = f"bash {script} run-job-id {job.id}"

        home = Path.home()
        body: dict[str, Any] = {
            "name": name,
            "imagename": image,
            "cmd": cmd,
            "job_type": "one-off",
            "mount": "all",
            "memory": memory,
            "cpu": cpu,
            "retry": 0,
            "emails": "none",
            "filelog": True,
            "filelog_stdout": f"{home}/data/logs/tfj_jobs/{name}.out",
            "filelog_stderr": f"{home}/data/logs/tfj_jobs/{name}.err",
        }

        self.svc.create_job(body)
        logger.info("Created Toolforge job '%s' for db job %s", name, job.id)
        return name

    def cancel(self, job: JobRecord) -> bool:
        name = tf_job_name(job.job_type, job.id)
        try:
            self.svc.delete_job(name)
            logger.info("Requested deletion of Toolforge job '%s' for db job %s", name, job.id)
            return True
        except HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                logger.info("Toolforge job '%s' already gone", name)
                return True
            logger.exception("Failed to delete Toolforge job '%s'", name)
            return False

    def status(self, job: JobRecord) -> dict[str, Any] | None:
        name = tf_job_name(job.job_type, job.id)
        try:
            tf_job = self.svc.show_job(name).job
        except HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                return None
            raise

        if not tf_job:
            raise Exception(f"Toolforge job {name} does not exist")

        return tf_job.live_status()

    def logs(self, job: JobRecord, tail: int = 200) -> str:
        name = tf_job_name(job.job_type, job.id)
        try:
            text = self.svc.get_logs(name)
        except HTTPError:
            logger.exception("Failed to get logs for Toolforge job '%s'", name)
            return ""
        lines = text.splitlines()
        return "\n".join(lines[-tail:])


__all__ = [
    "ToolforgeBackend",
    "tf_job_name",
]
