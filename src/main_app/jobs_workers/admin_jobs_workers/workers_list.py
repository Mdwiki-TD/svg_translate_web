from ..objects import JobData
from .add_lang_categories_to_owid_pages import AddLangCategoriesWorker
from .add_svglanguages_template import AddSvgSVGLanguagesTemplate
from .collect_templates_data import CollectMainFilesWorker
from .create_owid_pages import CreateOwidPagesWorker
from .crop_main_files import CropMainFilesWorker
from .download_main_files import DownloadMainFilesWorker
from .fix_nested_main_files import FixNestedMainFilesWorker
from .rename_owid_pages import RenameOwidPagesWorker
from .update_owid_charts import UpdateOwidChartsWorker

jobs_data_admins = {
    # DB Jobs
    "collect_templates_data": JobData(
        job_type="collect_templates_data",
        job_name="Collect Templates data",
        job_details_template="jobs_templates/admin_templates/collect_templates_data/details.html",
        job_list_template="jobs_templates/admin_templates/collect_templates_data/list.html",
        job_class=CollectMainFilesWorker,
        job_args=[],
        start_confirm_message="This will start a background job to collect templates data for all templates that don't have one. Continue?",
    ),
    "update_owid_charts": JobData(
        job_type="update_owid_charts",
        job_name="Update OWID Charts",
        job_details_template="jobs_templates/admin_templates/update_owid_charts/details.html",
        job_list_template="jobs_templates/admin_templates/update_owid_charts/list.html",
        job_class=UpdateOwidChartsWorker,
        job_args=[
            {"key": "owid_charts_limit_items", "as": "limit_items"},
        ],
        start_confirm_message="This will fetch metadata from ourworldindata.org for every chart and update min_time / max_time / len_years where changed. Continue?",
    ),
    # Files Jobs (jobs makes edit or upload in commons)
    "crop_main_files": JobData(
        job_type="crop_main_files",
        job_name="Crop Newest World Files",
        job_details_template="jobs_templates/admin_templates/crop_main_files/details.html",
        job_list_template="jobs_templates/admin_templates/crop_main_files/list.html",
        job_class=CropMainFilesWorker,
        job_args=[
            {"key": "crop_newest_upload_limit", "as": "upload_limit"},
            {"key": "upload_jobs_files", "as": "upload_files"},
        ],
        start_confirm_message="This will start a background job to crop newest world files and upload them with '(cropped)' suffix. Continue?",
    ),
    "fix_nested_main_files": JobData(
        job_type="fix_nested_main_files",
        job_name="Fix Nested Main Files",
        job_details_template="jobs_templates/admin_templates/fix_nested_main_files/details.html",
        job_list_template="jobs_templates/admin_templates/fix_nested_main_files/list.html",
        job_class=FixNestedMainFilesWorker,
        job_args=[
            {"key": "upload_jobs_files", "as": "upload_files"},
        ],
        start_confirm_message="This will start a background job to fix nested tags in all template main files. This will upload fixed versions to Commons using your credentials. Continue?",
    ),
    # OWID Templates/Pages
    "create_owid_pages": JobData(
        job_type="create_owid_pages",
        job_name="Create OWID Pages",
        job_details_template="jobs_templates/admin_templates/create_owid_pages/details.html",
        job_list_template="jobs_templates/admin_templates/create_owid_pages/list.html",
        job_class=CreateOwidPagesWorker,
        job_args=[
            {"key": "create_owid_pages_limit", "as": "limit_items"},
        ],
        start_confirm_message="This will start a background job to create showcase pages for OWID templates. Continue?",
    ),
    "rename_owid_pages": JobData(
        job_type="rename_owid_pages",
        job_name="Rename OWID Pages",
        job_details_template="jobs_templates/admin_templates/rename_owid_pages/details.html",
        job_list_template="jobs_templates/admin_templates/rename_owid_pages/list.html",
        job_class=RenameOwidPagesWorker,
        job_args=[],
        start_confirm_message='This will start a background job that renames every Template:OWID/* and OWID/* page whose first character after "OWID/" is lowercase. Continue?',
    ),
    "add_svglanguages_template": JobData(
        job_type="add_svglanguages_template",
        job_name="Add {{SVGLanguages}}",
        job_details_template="jobs_templates/admin_templates/add_svglanguages_template/details.html",
        job_list_template="jobs_templates/admin_templates/add_svglanguages_template/list.html",
        job_class=AddSvgSVGLanguagesTemplate,
        job_args=[
            {"key": "add_svglanguages_limit_items", "as": "limit_items"},
        ],
        start_confirm_message="This will start a background job to add Template:SVGLanguages to OWID templates.\nContinue?",
    ),
    "add_lang_categories_to_owid_pages": JobData(
        job_type="add_lang_categories_to_owid_pages",
        job_name="Add Language Categories",
        job_details_template="jobs_templates/admin_templates/add_lang_categories_to_owid_pages/details.html",
        job_list_template="jobs_templates/admin_templates/add_lang_categories_to_owid_pages/list.html",
        job_class=AddLangCategoriesWorker,
        job_args=[
            {"key": "add_lang_categories_limit_items", "as": "limit_items"},
        ],
        start_confirm_message="This will add language categories (e.g. [[Category:English-language SVG]]) to OWID pages based on available SVG translations. Continue?",
    ),
    "download_main_files": JobData(
        job_type="download_main_files",
        job_name="Download Main Files",
        job_details_template="jobs_templates/admin_templates/download_main_files/details.html",
        job_list_template="jobs_templates/admin_templates/download_main_files/list.html",
        job_class=DownloadMainFilesWorker,
        job_args=[
            {"key": "download_main_files_limit_items", "as": "limit_items"},
        ],
        start_confirm_message="This will start a background job to download all main files from the remote source to the local filesystem. Continue?",
    ),
}


# ------------------

__all__ = [
    "jobs_data_admins",
]
