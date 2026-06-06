"""
Background job definitions and registry.

TODO:
The MainFilesWorker class in this file is nearly identical to CollectMainFilesWorker in src/main_app/jobs_workers/collect_templates_data_worker.py. This significant code duplication makes maintenance difficult and error-prone.
Please consider refactoring so both could use a shared base class or utility functions for the common logic.

"""

from __future__ import annotations

import os
import sys
import logging
import threading
from pathlib import Path

if _path_ := Path(__file__).parent.parent.parent:
    os.environ["CRON_JOB"] = "true"
    sys.path.append(str(_path_))

from src.main_app.db.services import create_job
from src.main_app import create_app
from src.main_app.jobs_workers.workers_list import collect_templates_data_entry
from src.main_app.config import ProductionConfig
from src.logger_config import setup_logging

logger = logging.getLogger(__name__)

def start() -> None:
    user = None

    # environment variables in production already in toolforge envvars no need to run load_dotenv()
    setup_logging(logging.DEBUG, "main_app")
    setup_logging(logging.DEBUG, "__main__")

    app = create_app(ProductionConfig)

    # Get auth payload for OAuth uploads
    cancel_event = threading.Event()

    with app.app_context():
        job_record = create_job("collect_templates_data", "Background job")
        job_id = job_record.id
        logger.info(f"Starting collect templates data offline job with job_id={job_id}.")

        collect_templates_data_entry(
            job_id=job_id,
            user=user,
            cancel_event=cancel_event,
        )


if __name__ == "__main__":
    start()
