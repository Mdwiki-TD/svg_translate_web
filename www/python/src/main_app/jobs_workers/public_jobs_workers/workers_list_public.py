from __future__ import annotations

from ...jobs.objects import JobData
from .copy_svg_langs import CopySvgLangsForm, CopySvgLangsWorker
from .extract_files_translations import ExtractFilesTranslationsWorker
from .fix_nested_jobs import FixNestedJobsProcessor

jobs_data_public: dict[str, JobData] = {
    "extract_files_translations": JobData(
        job_type=ExtractFilesTranslationsWorker.JOB_TYPE,
        job_name="Extract Files Translations",
        job_details_template="jobs_templates/public/extract_files_translations/details.html",
        job_list_template="jobs_templates/public/extract_files_translations/list.html",
        job_class=ExtractFilesTranslationsWorker,
        job_args=[],
        start_confirm_message="",
        used_ajax_table=True,
        description="",
    ),
    "copy_svg_langs": JobData(
        job_type=CopySvgLangsWorker.JOB_TYPE,
        job_name="Copy SVG Translation",
        job_details_template="jobs_templates/public/copy_svg_langs/details.html",
        job_list_template="jobs_templates/public/copy_svg_langs/list.html",
        job_class=CopySvgLangsWorker,
        job_args=[
            {"key": "copy_svg_langs_upload_limit", "as": "upload_limit"},
            {"key": "copy_svg_langs_pages_limit", "as": "limit_items"},
            {"key": "upload_jobs_files", "as": "upload_files"},
        ],
        start_confirm_message="",
        load_settings=True,
        form_class=CopySvgLangsForm.setup,
        used_ajax_table=True,
        description="",
    ),
    "fix_nested_jobs": JobData(
        job_type=FixNestedJobsProcessor.JOB_TYPE,
        job_name="Fix Nested Tasks",
        job_details_template="jobs_templates/public/fix_nested_jobs/details.html",
        job_list_template="jobs_templates/public/fix_nested_jobs/list.html",
        job_class=FixNestedJobsProcessor,
        job_args=[
            {"key": "upload_jobs_files", "as": "upload_files"},
        ],
        start_confirm_message="",
        description="",
    ),
}

__all__ = [
    "jobs_data_public",
]
