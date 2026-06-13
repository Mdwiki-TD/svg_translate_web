from ..objects import JobData
from .add_svglanguages_template import add_svglanguages_template_to_templates
from .collect_templates_data.worker import collect_templates_data_entry
from .create_owid_pages import create_owid_pages_for_templates
from .crop_main_files import crop_main_files_worker_entry
from .download_main_files.worker import download_main_files_for_templates
from .fix_nested_main_files.worker import fix_nested_main_files_for_templates
from .rename_owid_pages import rename_owid_pages_for_templates
from .update_owid_charts.worker import update_owid_charts_worker_entry

jobs_data = {
    "collect_templates_data": JobData(
        job_type="collect_templates_data",
        job_name="Collect Templates data",
        job_details_template="jobs_templates/admin/collect_templates_data/details.html",
        job_list_template="jobs_templates/admin/collect_templates_data/list.html",
        job_callable=collect_templates_data_entry,
        job_args=[],
        start_confirm_message="This will start a background job to collect templates data for all templates that don't have one. Continue?",
    ),
    "update_owid_charts": JobData(
        job_type="update_owid_charts",
        job_name="Update OWID Charts",
        job_details_template="jobs_templates/admin/update_owid_charts/details.html",
        job_list_template="jobs_templates/admin/update_owid_charts/list.html",
        job_callable=update_owid_charts_worker_entry,
        job_args=[
            {"key": "owid_charts_limit_items", "as": "limit_items"},
        ],
        start_confirm_message="This will fetch metadata from ourworldindata.org for every chart and update min_time / max_time / len_years where changed. Continue?",
    ),
    "crop_main_files": JobData(
        job_type="crop_main_files",
        job_name="Crop Newest World Files",
        job_details_template="jobs_templates/admin/crop_main_files/details.html",
        job_list_template="jobs_templates/admin/crop_main_files/list.html",
        job_callable=crop_main_files_worker_entry,
        job_args=[
            {"key": "crop_newest_upload_limit", "as": "upload_limit"},
        ],
        start_confirm_message="This will start a background job to crop newest world files and upload them with '(cropped)' suffix. Continue?",
    ),
    "fix_nested_main_files": JobData(
        job_type="fix_nested_main_files",
        job_name="Fix Nested Main Files",
        job_details_template="jobs_templates/admin/fix_nested_main_files/details.html",
        job_list_template="jobs_templates/admin/fix_nested_main_files/list.html",
        job_callable=fix_nested_main_files_for_templates,
        job_args=[],
        start_confirm_message="This will start a background job to fix nested tags in all template main files. This will upload fixed versions to Commons using your credentials. Continue?",
    ),
    "create_owid_pages": JobData(
        job_type="create_owid_pages",
        job_name="Create OWID Pages",
        job_details_template="jobs_templates/admin/create_owid_pages/details.html",
        job_list_template="jobs_templates/admin/create_owid_pages/list.html",
        job_callable=create_owid_pages_for_templates,
        job_args=[
            {"key": "create_owid_pages_limit", "as": "limit_items"},
        ],
        start_confirm_message="This will start a background job to create showcase pages for OWID templates. Continue?",
    ),
    "rename_owid_pages": JobData(
        job_type="rename_owid_pages",
        job_name="Rename OWID Pages",
        job_details_template="jobs_templates/admin/rename_owid_pages/details.html",
        job_list_template="jobs_templates/admin/rename_owid_pages/list.html",
        job_callable=rename_owid_pages_for_templates,
        job_args=[],
        start_confirm_message='This will start a background job that renames every Template:OWID/* and OWID/* page whose first character after "OWID/" is lowercase. Continue?',
    ),
    "add_svglanguages_template": JobData(
        job_type="add_svglanguages_template",
        job_name="Add {{SVGLanguages}}",
        job_details_template="jobs_templates/admin/add_svglanguages_template/details.html",
        job_list_template="jobs_templates/admin/add_svglanguages_template/list.html",
        job_callable=add_svglanguages_template_to_templates,
        job_args=[
            {"key": "add_svglanguages_limit_items", "as": "limit_items"},
        ],
        start_confirm_message="This will start a background job to add Template:SVGLanguages to OWID templates.\nContinue?",
    ),
    "download_main_files": JobData(
        job_type="download_main_files",
        job_name="Download Main Files",
        job_details_template="jobs_templates/admin/download_main_files/details.html",
        job_list_template="jobs_templates/admin/download_main_files/list.html",
        job_callable=download_main_files_for_templates,
        job_args=[
            {"key": "download_main_files_limit_items", "as": "limit_items"},
        ],
        start_confirm_message="This will start a background job to download all main files from the remote source to the local filesystem. Continue?",
    ),
}


# ------------------

__all__ = [
    "jobs_data",
]
