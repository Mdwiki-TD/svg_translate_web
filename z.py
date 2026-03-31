import ast
from pathlib import Path

from tqdm import tqdm

list_files = """
tests/main_app/admins/test_admin_service.py
tests/main_app/admins/test_admins_required.py
tests/main_app/api_services/test_category.py
tests/main_app/api_services/clients/test_commons_client.py
tests/main_app/api_services/clients/test_wiki_client.py
tests/main_app/api_services/test_download_file_utils.py
tests/main_app/api_services/test_pages_api.py
tests/main_app/api_services/test_text_api.py
tests/main_app/api_services/test_text_bot.py
tests/main_app/api_services/test_upload_bot.py
tests/main_app/app_routes/admin/admin_routes/test_coordinators.py
tests/main_app/app_routes/admin/admin_routes/test_jobs.py
tests/main_app/app_routes/admin/admin_routes/test_recent.py
tests/main_app/app_routes/admin/admin_routes/test_settings.py
tests/main_app/app_routes/admin/admin_routes/test_templates.py
tests/main_app/app_routes/admin/test_routes.py
tests/main_app/app_routes/admin/test_sidebar.py
tests/main_app/app_routes/auth/test_cookie.py
tests/main_app/app_routes/auth/test_oauth.py
tests/main_app/app_routes/auth/test_rate_limit.py
tests/main_app/app_routes/auth/test_routes.py
tests/main_app/app_routes/cancel_restart/test_routes.py
tests/main_app/app_routes/explorer/test_compare.py
tests/main_app/app_routes/explorer/test_routes.py
tests/main_app/app_routes/explorer/test_thumbnail_utils.py
tests/main_app/app_routes/explorer/test_utils.py
tests/main_app/app_routes/extract/test_routes.py
tests/main_app/app_routes/fix_nested/test_explorer_routes.py
tests/main_app/app_routes/fix_nested/test_fix_utils.py
tests/main_app/app_routes/fix_nested/test_routes.py
tests/main_app/app_routes/main/test_routes.py
tests/main_app/app_routes/tasks/test_args_utils.py
tests/main_app/app_routes/tasks/test_routes.py
tests/main_app/app_routes/templates/test_routes.py
tests/main_app/test_config.py
tests/main_app/test_crypto.py
tests/main_app/db/test_db_CoordinatorsDB.py
tests/main_app/db/test_db_CreateUpdate.py
tests/main_app/db/test_db_Jobs.py
tests/main_app/db/test_db_Settings.py
tests/main_app/db/test_db_StageStore.py
tests/main_app/db/test_db_TasksListDB.py
tests/main_app/db/test_db_Templates.py
tests/main_app/db/test_db_class.py
tests/main_app/db/test_fix_nested_task_store.py
tests/main_app/db/test_svg_db.py
tests/main_app/db/test_task_store_pymysql.py
tests/main_app/db/test_utils.py
tests/main_app/jobs_workers/test_base_worker.py
tests/main_app/jobs_workers/test_collect_main_files_worker.py
tests/main_app/jobs_workers/create_owid_pages/test_owid_template_converter.py
tests/main_app/jobs_workers/create_owid_pages/test_worker.py
tests/main_app/jobs_workers/crop_main_files/test_crop_file.py
tests/main_app/jobs_workers/crop_main_files/test_download.py
tests/main_app/jobs_workers/crop_main_files/test_process_new.py
tests/main_app/jobs_workers/crop_main_files/test_upload.py
tests/main_app/jobs_workers/crop_main_files/test_utils.py
tests/main_app/jobs_workers/crop_main_files/test_worker.py
tests/main_app/jobs_workers/test_download_main_files_worker.py
tests/main_app/jobs_workers/test_fix_nested_main_files_worker.py
tests/main_app/jobs_workers/test_jobs_service.py
tests/main_app/jobs_workers/test_jobs_worker.py
tests/main_app/jobs_workers/test_utils.py
tests/main_app/test_routes_utils.py
tests/main_app/tasks/downloads/test_download.py
tests/main_app/tasks/extract/test_extract_task.py
tests/main_app/tasks/fix_nested/test_fix_nested_tasks.py
tests/main_app/tasks/injects/test_inject_tasks.py
tests/main_app/tasks/test_tasks_utils.py
tests/main_app/tasks/texts/test_start_bot.py
tests/main_app/tasks/titles/test_titles_tasks.py
tests/main_app/tasks/uploads/test_up.py
tests/main_app/test_template_service.py
tests/main_app/threads/test_task_threads.py
tests/main_app/threads/test_web_run_task.py
tests/main_app/users/test_current.py
tests/main_app/users/test_store.py
tests/main_app/utils/test_verify.py
tests/main_app/utils/wikitext/test_before_methods.py
tests/main_app/utils/wikitext/test_files_text.py
tests/main_app/utils/wikitext/test_other_versions.py
tests/main_app/utils/wikitext/test_template_page.py
tests/main_app/utils/wikitext/test_temps_bot.py
tests/main_app/utils/wikitext/titles_utils/test_last_world_file.py
tests/main_app/utils/wikitext/titles_utils/test_main_file.py
tests/offline/test_collect_main_files.py
"""

list_files = [x.strip() for x in list_files.splitlines() if x.strip()]

main_dir = Path(__file__).parent

created = 0


def get_file_functions(file_path: Path) -> list[str]:
    """
    Use AST to get all functions in file.

    Args:
        file_path: Path to the Python file to analyze.

    Returns:
        List of function names found in the file.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        functions = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef | ast.ClassDef):
                continue

            if ": Blueprint)" in source or "Blueprint(" in source:
                continue

            if f"    def {node.name}(" in source:
                continue

            if node.name.startswith("_"):
                continue

            functions.append(node.name)

        return functions
    except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
        print(f"Error reading {file_path}: {e}")
        return []


for x in tqdm(list_files):
    file_path = main_dir / x
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        srcpath_str = x.replace("tests/", "src/").replace("test_", "")
        src_path = Path(main_dir / srcpath_str)

        if src_path.exists():
            file_functions = get_file_functions(Path(main_dir / srcpath_str))

            if file_functions:
                file_functions_str = ",\n".join([f"    {x}" for x in file_functions])
                file_text = (
                    '"""\n'
                    f"TODO:write tests for {srcpath_str}\n"
                    '"""\n'
                    "\n\n"
                    f"from {srcpath_str.replace(".py", "").replace("/", ".")} import (\n"
                    f"{file_functions_str}\n"
                    ")\n"
                )
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_text)
                created += 1
                # break

print(f"{created=}")
