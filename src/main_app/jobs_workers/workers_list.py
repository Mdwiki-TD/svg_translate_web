from dataclasses import dataclass
from typing import Callable

from .add_svglanguages_template import add_svglanguages_template_to_templates
from .collect_main_files_worker import collect_main_files_for_templates
from .create_owid_pages import create_owid_pages_for_templates
from .crop_main_files import crop_main_files_for_templates
from .download_main_files_worker import download_main_files_for_templates
from .fix_nested_main_files_worker import fix_nested_main_files_for_templates
from .rename_owid_pages import rename_owid_pages_for_templates
from .update_owid_charts.worker import update_owid_charts_worker_entry


@dataclass
class JobData:
    job_type: str
    job_name: str
    job_details_template: str
    job_list_template: str

    job_callable: Callable
    job_args: list | None = None


jobs_data = {
    "collect_main_files": JobData(
        job_type="collect_main_files",
        job_name="Collect Templates data",
        job_details_template="admins/jobs_templates/collect_main_files/details.html",
        job_list_template="admins/jobs_templates/collect_main_files/list.html",
        job_callable=collect_main_files_for_templates,
        job_args=[],
    ),
    "update_owid_charts": JobData(
        job_type="update_owid_charts",
        job_name="Update OWID Charts",
        job_details_template="admins/jobs_templates/update_owid_charts/details.html",
        job_list_template="admins/jobs_templates/update_owid_charts/list.html",
        job_callable=update_owid_charts_worker_entry,
        job_args=["owid_charts_limit_items"],
    ),
    "crop_main_files": JobData(
        job_type="crop_main_files",
        job_name="Crop Newest World Files",
        job_details_template="admins/jobs_templates/crop_main_files/details.html",
        job_list_template="admins/jobs_templates/crop_main_files/list.html",
        job_callable=crop_main_files_for_templates,
        job_args=["crop_newest_upload_limit"],
    ),
    "fix_nested_main_files": JobData(
        job_type="fix_nested_main_files",
        job_name="Fix Nested Main Files",
        job_details_template="admins/jobs_templates/fix_nested_main_files/details.html",
        job_list_template="admins/jobs_templates/fix_nested_main_files/list.html",
        job_callable=fix_nested_main_files_for_templates,
        job_args=[],
    ),
    "create_owid_pages": JobData(
        job_type="create_owid_pages",
        job_name="Create OWID Pages",
        job_details_template="admins/jobs_templates/create_owid_pages/details.html",
        job_list_template="admins/jobs_templates/create_owid_pages/list.html",
        job_callable=create_owid_pages_for_templates,
        job_args=["create_owid_pages_limit"],
    ),
    "rename_owid_pages": JobData(
        job_type="rename_owid_pages",
        job_name="Rename OWID Pages",
        job_details_template="admins/jobs_templates/rename_owid_pages/details.html",
        job_list_template="admins/jobs_templates/rename_owid_pages/list.html",
        job_callable=rename_owid_pages_for_templates,
        job_args=[],
    ),
    "add_svglanguages_template": JobData(
        job_type="add_svglanguages_template",
        job_name="Add {{SVGLanguages}}",
        job_details_template="admins/jobs_templates/add_svglanguages_template/details.html",
        job_list_template="admins/jobs_templates/add_svglanguages_template/list.html",
        job_callable=add_svglanguages_template_to_templates,
        job_args=["add_svglanguages_limit_items"],
    ),
    "download_main_files": JobData(
        job_type="download_main_files",
        job_name="Download Main Files",
        job_details_template="admins/jobs_templates/download_main_files/details.html",
        job_list_template="admins/jobs_templates/download_main_files/list.html",
        job_callable=download_main_files_for_templates,
        job_args=["download_main_files_limit_items"],
    ),
}


# ------------------

__all__ = [
    "jobs_data",
]
