from ..objects import JobData
from .copy_svg_langs.worker import copy_svg_langs_worker_entry
from .fix_nested_jobs.worker import fix_nested_jobs_worker_entry

jobs_data_public = {
    "copy_svg_langs": JobData(
        job_type="copy_svg_langs",
        job_name="Copy SVG Translation",
        job_details_template="jobs_templates/public/copy_svg_langs/details.html",
        job_list_template="jobs_templates/public/copy_svg_langs/list.html",
        job_callable=copy_svg_langs_worker_entry,
        job_args=["copy_svg_langs_upload_limit"],
        start_confirm_message="",
    ),
    "fix_nested_jobs": JobData(
        job_type="fix_nested_jobs",
        job_name="Fix Nested Tasks",
        job_details_template="jobs_templates/public/fix_nested_jobs/details.html",
        job_list_template="jobs_templates/public/fix_nested_jobs/list.html",
        job_callable=fix_nested_jobs_worker_entry,
        job_args=[],
        start_confirm_message="",
    ),
}

__all__ = [
    "jobs_data_public",
]
