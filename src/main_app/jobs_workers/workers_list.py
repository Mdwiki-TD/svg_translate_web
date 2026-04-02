from ..public_jobs_workers.copy_svg_langs.worker import copy_svg_langs_worker_entry
from .add_svglanguages_template import add_svglanguages_template_to_templates
from .collect_main_files_worker import collect_main_files_for_templates
from .create_owid_pages import create_owid_pages_for_templates
from .crop_main_files import crop_main_files_for_templates
from .download_main_files_worker import download_main_files_for_templates
from .fix_nested_main_files_worker import fix_nested_main_files_for_templates

jobs_targets = {
    "fix_nested_main_files": fix_nested_main_files_for_templates,
    "collect_main_files": collect_main_files_for_templates,
    "crop_main_files": crop_main_files_for_templates,
    "create_owid_pages": create_owid_pages_for_templates,
    "add_svglanguages_template": add_svglanguages_template_to_templates,
    "download_main_files": download_main_files_for_templates,
    "copy_svg_langs": copy_svg_langs_worker_entry,
}


JOB_TYPE_TEMPLATES = {
    "collect_main_files": "admins/jobs_templates/collect_main_files/details.html",
    "crop_main_files": "admins/jobs_templates/crop_main_files/details.html",
    "create_owid_pages": "admins/jobs_templates/create_owid_pages/details.html",
    "fix_nested_main_files": "admins/jobs_templates/fix_nested_main_files/details.html",
    "download_main_files": "admins/jobs_templates/download_main_files/details.html",
    "add_svglanguages_template": "admins/jobs_templates/add_svglanguages_template/details.html",
    "copy_svg_langs": "admins/jobs_templates/copy_svg_langs/details.html",
}


JOB_TYPE_LIST_TEMPLATES = {
    "collect_main_files": "admins/jobs_templates/collect_main_files/list.html",
    "crop_main_files": "admins/jobs_templates/crop_main_files/list.html",
    "create_owid_pages": "admins/jobs_templates/create_owid_pages/list.html",
    "fix_nested_main_files": "admins/jobs_templates/fix_nested_main_files/list.html",
    "download_main_files": "admins/jobs_templates/download_main_files/list.html",
    "add_svglanguages_template": "admins/jobs_templates/add_svglanguages_template/list.html",
    "copy_svg_langs": "admins/jobs_templates/copy_svg_langs/list.html",
}

__all__ = [
    "jobs_targets",
    "JOB_TYPE_TEMPLATES",
    "JOB_TYPE_LIST_TEMPLATES",
]
