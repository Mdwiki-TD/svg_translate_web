from ..objects import JobData
from .extract_files_translations import extract_files_translations_worker_entry
from .copy_svg_langs.runner import copy_svg_langs_worker_entry, setup_svg_langs_form
from .fix_nested_jobs.runner import fix_nested_jobs_worker_entry

jobs_data_public: dict[str, JobData] = {
    "extract_files_translations": JobData(
        job_type="extract_files_translations",
        job_name="Extract Files Translations",
        job_details_template="jobs_templates/public/extract_files_translations/details.html",
        job_list_template="jobs_templates/public/extract_files_translations/list.html",
        job_callable=extract_files_translations_worker_entry,
        job_args=[
        ],
        start_confirm_message="",
    ),
    "copy_svg_langs": JobData(
        job_type="copy_svg_langs",
        job_name="Copy SVG Translation",
        job_details_template="jobs_templates/public/copy_svg_langs/details.html",
        job_list_template="jobs_templates/public/copy_svg_langs/list.html",
        job_callable=copy_svg_langs_worker_entry,
        job_args=[
            {"key": "copy_svg_langs_upload_limit", "as": "upload_limit"},
            {"key": "copy_svg_langs_pages_limit", "as": "limit_items"},
            {"key": "upload_jobs_files", "as": "upload_files"},
        ],
        start_confirm_message="",
        load_settings=True,
        form_class=setup_svg_langs_form,
    ),
    "fix_nested_jobs": JobData(
        job_type="fix_nested_jobs",
        job_name="Fix Nested Tasks",
        job_details_template="jobs_templates/public/fix_nested_jobs/details.html",
        job_list_template="jobs_templates/public/fix_nested_jobs/list.html",
        job_callable=fix_nested_jobs_worker_entry,
        job_args=[
            {"key": "upload_jobs_files", "as": "upload_files"},
        ],
        start_confirm_message="",
    ),
}

__all__ = [
    "jobs_data_public",
]
