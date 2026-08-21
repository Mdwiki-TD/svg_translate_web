from ..objects import JobData
from .copy_svg_langs import CopySvgLangsWorker, setup_svg_langs_form
from .extract_files_translations import ExtractFilesTranslationsWorker
from .fix_nested_jobs import FixNestedJobsProcessor

jobs_data_public: dict[str, JobData] = {
    "extract_files_translations": JobData(
        job_type="extract_files_translations",
        job_name="Extract Files Translations",
        job_details_template="jobs_templates/public/extract_files_translations/details.html",
        job_list_template="jobs_templates/public/extract_files_translations/list.html",
        job_class=ExtractFilesTranslationsWorker,
        job_args=[],
        start_confirm_message="",
    ),
    "copy_svg_langs": JobData(
        job_type="copy_svg_langs",
        job_name="Copy SVG Translation",
        job_details_template="jobs_templates/public/copy_svg_langs/details_new.html",
        job_list_template="jobs_templates/public/copy_svg_langs/list.html",
        job_class=CopySvgLangsWorker,
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
        job_class=FixNestedJobsProcessor,
        job_args=[
            {"key": "upload_jobs_files", "as": "upload_files"},
        ],
        start_confirm_message="",
    ),
}

__all__ = [
    "jobs_data_public",
]
