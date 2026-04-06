```
tests/
├── conftest.py                              # Fixtures عامة (csrf_token, mock_site, sample_wikitext, ...)
├── pytest.ini                               # إعدادات pytest
│
# =========================================================================
# 1. اختبارات الوحدة (Unit Tests)
# منطق برمجي بحت — بدون DB، بدون شبكة، بدون Flask App
# =========================================================================
├── unit/
│   ├── test_crypto.py                       # دوال التشفير/فك التشفير
│   ├── test_logger_config.py                # إعدادات Logger
│   ├── test_svg_config.py                   # ثوابت وإعدادات SVG
│   ├── test_config.py                       # DbConfig, Paths, CookieConfig, OAuthConfig, Settings
│   ├── test_data.py                         # get_slug_categories()
│   │
│   ├── main_app/
│   │   ├── utils/
│   │   │   ├── test_jinja_filters.py        # format_stage_timestamp, short_url
│   │   │   ├── test_verify.py               # verify_required_fields
│   │   │   ├── wikitext/
│   │   │   │   ├── test_before_methods.py
│   │   │   │   ├── test_categories_utils.py # CategoryLink + دوال التصنيفات
│   │   │   │   ├── test_files_text.py
│   │   │   │   ├── test_other_versions.py
│   │   │   │   ├── test_temp_source.py
│   │   │   │   ├── test_template_page.py
│   │   │   │   ├── test_temps_bot.py
│   │   │   │   ├── test_text_utils.py
│   │   │   │   ├── test_update_original_file_text.py
│   │   │   │   ├── test_update_template_page_file_reference.py
│   │   │   │   ├── test_append_image_extracted_template.py
│   │   │   │   └── titles_utils/
│   │   │   │       ├── test_main_file.py
│   │   │   │       ├── test_find_main_title.py
│   │   │   │       ├── test_match_main_title.py
│   │   │   │       ├── test_last_world_file_with_full_date.py
│   │   │   │       └── last_world_file_utils/
│   │   │   │           ├── test_last_world_file.py
│   │   │   │           ├── test_last_world_file2.py
│   │   │   │           └── test_last_world_file_edge_cases.py
│   │   │   └── download_file_utils/
│   │   │       └── test_download_file_utils.py
│   │   │
│   │   ├── app_routes/utils/
│   │   │   ├── test_args_utils.py           # Args, parse_args
│   │   │   ├── test_explorer_utils.py
│   │   │   ├── test_fix_nested_utils.py
│   │   │   ├── test_routes_utils.py
│   │   │   └── test_thumbnail_utils.py
│   │   │
│   │   ├── jobs_workers/utils/
│   │   │   ├── test_jobs_workers_utils.py
│   │   │   ├── test_crop_main_files_utils.py
│   │   │   └── test_add_svglanguages_template_utils.py
│   │   │
│   │   ├── tasks/utils/
│   │   │   └── test_tasks_utils.py          # json_save, commons_link, ...
│   │   │
│   │   └── jobs_workers/create_owid_pages/
│   │       └── test_owid_template_converter.py
│
# =========================================================================
# 2. اختبارات التكامل (Integration Tests)
# تفاعل مع DB، خدمات خارجية (Mocked)، Workers، Services، Tasks
# =========================================================================
├── integration/
│   ├── test_app.py                          # تهيئة Flask + بدء التطبيق
│   ├── test_app_factory.py                  # create_app() مع إعدادات مختلفة
│   │
│   ├── main_app/
│   │   ├── admins/
│   │   │   └── test_admins_required.py      # Decorator صلاحيات الأدمن
│   │   │
│   │   ├── api_services/
│   │   │   ├── test_category.py
│   │   │   ├── test_pages_api.py
│   │   │   ├── test_text_api.py
│   │   │   ├── test_text_bot.py
│   │   │   ├── test_upload_bot.py
│   │   │   ├── test_mwclient_page.py        # MwClientPage (مع Mock)
│   │   │   └── clients/
│   │   │       ├── test_commons_client.py
│   │   │       └── test_wiki_client.py
│   │   │
│   │   ├── db/
│   │   │   ├── test_db_class.py             # Database, MaxUserConnectionsError
│   │   │   ├── test_db_utils.py                # DbUtils mixin
│   │   │   ├── test_db_create_update.py     # CreateUpdateTask, TaskAlreadyExistsError
│   │   │   ├── test_db_stage_store.py       # StageStore
│   │   │   ├── test_db_tasks_list_db.py     # TasksListDB
│   │   │   ├── test_task_store_pymysql.py   # TaskStorePyMysql
│   │   │   ├── test_fix_nested_task_store.py # FixNestedTaskStore
│   │   │   ├── test_db_coordinators_db.py   # CoordinatorsDB, CoordinatorRecord
│   │   │   ├── test_db_jobs.py              # JobsDB, JobRecord
│   │   │   ├── test_db_owid_charts.py       # OwidChartsDB, OwidChartRecord
│   │   │   ├── test_db_settings.py          # SettingsDB
│   │   │   ├── test_db_templates.py         # TemplatesDB, TemplateRecord
│   │   │   ├── test_svg_db.py
│   │   │   ├── test_sql_schema_tables.py    # TablesCreatesSql
│   │   │   └── test_connection_reuse.py
│   │   │
│   │   ├── cookies/
│   │   │   └── test_cookie_header_client.py # CookieHeaderClient
│   │   │
│   │   ├── jobs_workers/
│   │   │   ├── test_base_worker.py          # BaseJobWorker (ABC)
│   │   │   ├── test_jobs_worker.py
│   │   │   ├── test_worker_cancellation.py
│   │   │   ├── test_collect_main_files_worker.py  # CollectMainFilesWorker
│   │   │   ├── test_download_main_files_worker.py # DownloadMainFilesWorker
│   │   │   ├── test_fix_nested_main_files_worker.py # FixNestedMainFilesWorker
│   │   │   ├── crop_main_files/
│   │   │   │   ├── test_crop_main_files_worker.py           # CropMainFilesWorker
│   │   │   │   ├── test_process_new.py      # CropMainFilesProcessor, FileProcessingInfo
│   │   │   │   ├── test_crop_file.py
│   │   │   │   ├── test_download.py
│   │   │   │   └── test_upload.py
│   │   │   ├── create_owid_pages/
│   │   │   │   ├── test_create_owid_pages_worker.py           # CreateOwidPagesWorker, TemplateProcessingInfo
│   │   │   │   └── test_owid_template_converter.py
│   │   │   └── add_svglanguages_template/
│   │   │       ├── test_add_svglanguages_template_worker.py           # AddSvgSVGLanguagesTemplate, TemplateInfo
│   │   │       └── test_utils.py
│   │   │
│   │   ├── services/
│   │   │   ├── test_admin_service.py
│   │   │   ├── test_jobs_service.py
│   │   │   ├── test_owid_charts_service.py
│   │   │   ├── test_tasks_service.py
│   │   │   └── test_template_service.py
│   │   │
│   │   ├── tasks/
│   │   │   ├── downloads/
│   │   │   │   └── test_download.py
│   │   │   ├── extract/
│   │   │   │   └── test_extract_task.py
│   │   │   ├── fix_nested/
│   │   │   │   └── test_fix_nested_tasks.py
│   │   │   ├── injects/
│   │   │   │   └── test_inject_tasks.py
│   │   │   ├── texts/
│   │   │   │   └── test_start_bot.py
│   │   │   ├── titles/
│   │   │   │   ├── test_titles_tasks.py
│   │   │   │   └── test_titles_bot.py
│   │   │   └── uploads/
│   │   │       └── test_up.py
│   │   │
│   │   ├── threads/
│   │   │   ├── test_task_threads.py
│   │   │   └── test_web_run_task.py
│   │   │
│   │   └── users/
│   │       ├── test_current.py              # CurrentUser, current_user(), oauth_required()
│   │       ├── test_store.py                # UserTokenRecord
│   │       └── test_users_store.py
│
# =========================================================================
# 3. اختبارات المسارات (Functional / E2E API Tests)
# إرسال طلبات HTTP عبر test_client — استجابات 200, 404, 403, 401
# =========================================================================
└── functional/
    └── main_app/
        └── app_routes/
            ├── admin/
            │   ├── test_routes.py                   # /admin (الصفحة الرئيسية)
            │   ├── test_sidebar.py                  # SidebarItem + بناء القائمة
            │   └── admin_routes/
            │       ├── test_coordinators.py         # /admin/coordinators
            │       ├── test_jobs.py                 # /admin/jobs
            │       ├── test_owid_charts.py          # /admin/owid_charts
            │       ├── test_recent.py               # /admin/recent
            │       ├── test_settings.py             # /admin/settings
            │       └── test_templates.py            # /admin/templates
            ├── auth/
            │   ├── test_cookie.py                   # إنشاء/حذف الكوكيز
            │   ├── test_oauth.py                    # دورة OAuth (Mocked)
            │   ├── test_rate_limit.py               # RateLimiter عبر HTTP
            │   └── test_auth_routes.py                   # /auth/login, /auth/logout
            ├── cancel_restart/
            │   └── test_cancel_restart_routes.py                   # /tasks/cancel, /tasks/restart
            ├── explorer/
            │   ├── test_compare.py
            │   ├── test_compare_routes.py                   # /explorer
            │   └── test_utils.py
            ├── extract/
            │   └── test_extract_routes.py                   # /extract
            ├── fix_nested/
            │   ├── test_explorer_routes.py
            │   ├── test_fix_nested_routes.py                   # /fix_nested
            │   └── test_fix_nested_worker.py
            ├── main/
            │   └── test_main_routes.py                   # / (الصفحة الرئيسية)
            ├── tasks/
            │   ├── test_task_routes.py                   # /tasks
            │   └── test_args_utils.py
            ├── templates/
            │   └── test_templates_routes.py                   # /templates
            └── test_owid_charts_routes.py           # /owid_charts (خارج admin)
```
