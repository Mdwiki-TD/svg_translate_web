"""
Background job definitions and registry.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
from pathlib import Path

if _path_ := Path(__file__).parent.parent.parent:
    os.environ["CRON_JOB"] = "true"
    sys.path.append(str(_path_))

from src.logger_config import setup_logging
from src.main_app import create_app
from src.main_app.config import ProductionConfig
from src.main_app.db.services import create_job, update_job_status
from src.main_app.jobs_workers.workers_list import collect_templates_data_entry

logger = logging.getLogger(__name__)


def start() -> None:

    # environment variables in production already in toolforge envvars no need to run load_dotenv()
    setup_logging(logging.DEBUG, "src")
    setup_logging(logging.DEBUG, "main_app")
    setup_logging(logging.DEBUG, "__main__")

    app = create_app(ProductionConfig)

    # Get auth payload for OAuth uploads
    cancel_event = threading.Event()

    with app.app_context():
        try:
            job_record = create_job("collect_templates_data", "Background job")
            job_id = job_record.id
        except Exception as e:
            logger.error(f"Error creating job record: {e}")
            sys.exit(1)

        logger.info(f"Starting collect templates data offline job with job_id={job_id}.")
        try:
            collect_templates_data_entry(
                job_id=job_id,
                user=None,
                cancel_event=cancel_event,
                args={"update_all": "true"},
            )
        except Exception as e:
            logger.error(f"Error running collect templates data offline job: {e}")
            update_job_status(job_id, "failed", result_file=None, job_type="collect_templates_data")
            sys.exit(1)


if __name__ == "__main__":
    start()
