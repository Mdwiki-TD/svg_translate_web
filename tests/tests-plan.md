# project tree

```text
src/
├── __init__.py
├── app.py
├── example.env
├── import_owid_charts.py
├── logger_config.py
├── main_app/
│   ├── __init__.py
│   ├── api_services/
│   │   ├── __init__.py
│   │   ├── category.py
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── commons_client.py
│   │   │   └── wiki_client.py
│   │   ├── mwclient_page.py
│   │   ├── pages_api.py
│   │   ├── text_api.py
│   │   ├── text_bot.py
│   │   ├── upload_bot.py
│   │   ├── upload_bot_new.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── download_file_utils.py
│   ├── app_routes/
│   │   ├── __init__.py
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── admin_routes/
│   │   │   ├── admins_required.py
│   │   │   ├── routes.py
│   │   │   └── sidebar.py
│   │   ├── admin_routes/
│   │   │   ├── __init__.py
│   │   │   ├── coordinators.py
│   │   │   ├── jobs.py
│   │   │   ├── owid_charts.py
│   │   │   ├── settings.py
│   │   │   └── templates.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── cookie.py
│   │   │   ├── oauth.py
│   │   │   ├── rate_limit.py
│   │   │   └── routes.py
│   │   ├── fix_nested/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── worker.py
│   │   ├── main_routes/
│   │   │   ├── __init__.py
│   │   │   ├── explorer_routes.py
│   │   │   ├── extract_routes.py
│   │   │   ├── owid_charts_routes.py
│   │   │   └── routes.py
│   │   ├── public_jobs.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── args_utils.py
│   │       ├── compare.py
│   │       ├── explorer_utils.py
│   │       ├── fix_nested_utils.py
│   │       ├── routes_utils.py
│   │       └── thumbnail_utils.py
│   ├── config.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── cookies.py
│   │   └── crypto.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── owid_charts.csv
│   │   ├── templates_slugs_topics.json
│   │   └── topics_categories.json
│   ├── db/
│   │   ├── __init__.py
│   │   ├── db_class.py
│   │   ├── db_CoordinatorsDB.py
│   │   ├── db_Jobs.py
│   │   ├── db_OwidCharts.py
│   │   ├── db_Settings.py
│   │   ├── db_Templates.py
│   │   ├── exceptions.py
│   │   ├── fix_nested_task_store.py
│   │   ├── sql_schema_tables.py
│   │   ├── svg_db.py
│   │   └── user_tokens.py
│   ├── jobs_workers/
│   │   ├── __init__.py
│   │   ├── add_svglanguages_template/
│   │   │   ├── __init__.py
│   │   │   └── worker.py
│   │   ├── base_worker.py
│   │   ├── collect_main_files_worker.py
│   │   ├── create_owid_pages/
│   │   │   ├── __init__.py
│   │   │   ├── owid_template_converter.py
│   │   │   └── worker.py
│   │   ├── crop_main_files/
│   │   │   ├── __init__.py
│   │   │   ├── crop_file.py
│   │   │   ├── download.py
│   │   │   ├── process_new.py
│   │   │   ├── upload.py
│   │   │   └── worker.py
│   │   ├── download_main_files_worker.py
│   │   ├── fix_nested_main_files_worker.py
│   │   ├── jobs_worker.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── add_svglanguages_template_utils.py
│   │   │   └── crop_main_files_utils.py
│   │   └── workers_list.py
│   ├── public_jobs_workers/
│   │   ├── __init__.py
│   │   └── copy_svg_langs/
│   │       ├── __init__.py
│   │       ├── job.py
│   │       ├── service.py
│   │       ├── steps/
│   │       │   ├── __init__.py
│   │       │   ├── download.py
│   │       │   ├── extract_text.py
│   │       │   ├── extract_titles.py
│   │       │   ├── extract_translations.py
│   │       │   ├── fix_nested.py
│   │       │   ├── inject.py
│   │       │   └── upload.py
│   │       └── worker.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── admin_service.py
│   │   ├── jobs_service.py
│   │   ├── owid_charts_service.py
│   │   ├── template_service.py
│   │   └── users_service.py
│   └── utils/
│       ├── __init__.py
│       ├── jinja_filters.py
│       ├── verify.py
│       └── wikitext/
│           ├── __init__.py
│           ├── before_methods.py
│           ├── categories_utils.py
│           ├── files_text.py
│           ├── other_versions.py
│           ├── temp_source.py
│           ├── template_page.py
│           ├── temps_bot.py
│           └── titles_utils/
│               ├── __init__.py
│               ├── last_world_file_utils.py
│               └── main_file.py
├── static/
├── svg_config.py
└── uwsgi.ini
```

# tests files tree

```text
tests/
├── conftest.py
├── functional/
├── integration/
│   ├── app_routes/
│   │   ├── admin/
│   │   │   ├── admin_routes/
│   │   │   │   ├── test_admin_jobs_routes.py
│   │   │   │   ├── test_owid_charts.py
│   │   │   │   ├── test_templates.py
│   │   │   │   └── test_templates_admin_routes.py
│   │   │   └── test_admin_routes.py
│   │   ├── auth/
│   │   │   └── test_auth_routes.py
│   │   ├── main_routes/
│   │   │   ├── fix_nested/
│   │   │   │   ├── test_fix_nested_routes.py
│   │   │   │   └── test_fix_nested_routes_auth.py
│   │   │   ├── test_admin_templates_routes.py
│   │   │   ├── test_explorer_routes.py
│   │   │   ├── test_extract_routes.py
│   │   │   ├── test_main_routes.py
│   │   │   └── test_owid_charts_routes.py
│   ├── core/
│   │   └── test_cookie_header_client.py
│   ├── db/
│   │   └── test_connection_reuse.py
│   ├── jobs_workers/
│   │   ├── add_svglanguages_template/
│   │   ├── create_owid_pages/
│   │   ├── crop_main_files/
│   │   └── utils/
│   ├── public_jobs_workers/
│   │   └── copy_svg_langs/
│   │       └── steps/
│   └── utils/
│       └── wikitext/
│           └── titles_utils/
├── main_app/
│   ├── admins/
│   │   └── test_admins_required.py
│   ├── api_services/
│   │   ├── clients/
│   │   │   ├── test_commons_client.py
│   │   │   └── test_wiki_client.py
│   │   ├── mwclient_page/
│   │   │   ├── test_mwclient_page.py
│   │   │   └── test_mwclient_page2.py
│   │   ├── test_category.py
│   │   ├── test_pages_api.py
│   │   ├── test_text_api.py
│   │   ├── test_text_bot.py
│   │   ├── test_upload_bot.py
│   │   └── test_upload_bot_new.py
│   ├── app_routes/
│   │   ├── admin/
│   │   │   ├── admin_routes/
│   │   │   │   └── test_coordinators_exception_handling.py
│   │   │   └── test_sidebar.py
│   │   ├── auth/
│   │   │   ├── test_auth_cookie.py
│   │   │   ├── test_auth_oauth_helpers.py
│   │   │   ├── test_cookie.py
│   │   │   ├── test_oauth.py
│   │   │   └── test_rate_limit.py
│   │   ├── fix_nested/
│   │   │   ├── test_explorer_routes_undo.py
│   │   │   ├── test_fix_nested_routes_unit.py
│   │   │   └── test_fix_nested_worker.py
│   │   └── utils/
│   │       ├── test_args_utils.py
│   │       ├── test_compare.py
│   │       ├── test_explorer_utils.py
│   │       ├── test_fix_nested_utils.py
│   │       ├── test_routes_utils_unit.py
│   │       └── test_thumbnail_utils.py
│   ├── core/
│   │   └── test_crypto.py
│   ├── db/
│   │   ├── test_db_class.py
│   │   ├── test_db_CoordinatorsDB.py
│   │   ├── test_db_Jobs.py
│   │   ├── test_db_OwidCharts.py
│   │   ├── test_db_Settings.py
│   │   ├── test_db_Templates.py
│   │   ├── test_exceptions.py
│   │   ├── test_fix_nested_task_store.py
│   │   └── test_svg_db.py
│   ├── jobs_workers/
│   │   ├── add_svglanguages_template/
│   │   │   └── test_add_svglanguages_template_worker.py
│   │   ├── create_owid_pages/
│   │   │   ├── test_create_owid_pages_worker.py
│   │   │   └── test_owid_template_converter.py
│   │   ├── crop_main_files/
│   │   │   ├── test_crop_file.py
│   │   │   ├── test_crop_main_files_worker.py
│   │   │   ├── test_download.py
│   │   │   ├── test_process_new.py
│   │   │   └── test_upload.py
│   │   ├── test_base_worker.py
│   │   ├── test_collect_main_files_worker.py
│   │   ├── test_download_main_files_worker.py
│   │   ├── test_fix_nested_main_files_worker.py
│   │   ├── test_jobs_worker.py
│   │   ├── test_worker_cancellation.py
│   │   └── utils/
│   │       ├── test_add_svglanguages_template_utils.py
│   │       ├── test_crop_main_files_utils.py
│   │       └── test_jobs_workers_utils.py
│   ├── public_jobs_workers/
│   │   ├── copy_svg_langs/
│   │   │   └── test_copy_svg_langs_processor.py
│   │   └── copy_svg_langs_legacy/
│   │       ├── steps/
│   │       │   ├── test_extracts_task.py
│   │       │   ├── test_fix_nested_tasks.py
│   │       │   ├── test_inject_tasks.py
│   │       │   ├── test_start_bot.py
│   │       │   ├── test_titles_bot.py
│   │       │   ├── test_titles_tasks.py
│   │       │   └── test_up.py
│   │       ├── test_legacy_threads.py
│   │       └── test_legacy_worker.py
│   ├── services/
│   │   ├── test_admin_service.py
│   │   ├── test_jobs_service.py
│   │   ├── test_owid_charts_service.py
│   │   └── test_template_service.py
│   ├── test_init.py
│   ├── test_app_factory.py
│   ├── test_config.py
│   ├── test_data.py
│   ├── users/
│   │   ├── test_current_unit.py
│   │   ├── test_store.py
│   │   └── test_users_store.py
│   └── utils/
│       ├── api_services_utils/
│       │   └── test_download_file_utils.py
│       ├── categories_utils/
│       │   ├── test_capitalize_category.py
│       │   ├── test_categories_utils.py
│       │   ├── test_extract_categories.py
│       │   ├── test_find_missing_categories.py
│       │   └── test_merge_categories.py
│       ├── test_jinja_filters.py
│       ├── test_verify.py
│       └── wikitext/
│           ├── temps_bot/
│           │   ├── test_get_files_list.py
│           │   ├── test_get_titles.py
│           │   └── test_temps_bot.py
│           ├── test_appendImageExtractedTemplate.py
│           ├── test_before_methods.py
│           ├── test_files_text.py
│           ├── test_other_versions.py
│           ├── test_temp_source.py
│           ├── test_template_page.py
│           ├── test_text_utils.py
│           ├── test_update_original_file_text.py
│           ├── test_update_template_page_file_reference.py
│           └── titles_utils/
│               ├── last_world_file_utils/
│               │   ├── test_last_world_file.py
│               │   ├── test_last_world_file2.py
│               │   └── test_last_world_file_edge_cases.py
│               ├── test_find_main_title.py
│               ├── test_last_world_file_with_full_date.py
│               ├── test_main_file.py
│               └── test_match_main_title.py
├── test_app.py
├── test_logger_config.py
└── unit/
```

# tests targer dirs

-   ./tests/unit
-   ./tests/integration
-   ./tests/functional
