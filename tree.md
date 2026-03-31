```
PS I:\SVG\svg_repo\src> python -m directory_tree --ignore-list __pycache__
src/
├── __init__.py
├── app.py
├── example.env
├── import_owid_charts.py
├── logger_config.py
├── main_app/
│   ├── __init__.py
│   ├── admins/
│   │   └── __init__.py
│   ├── admins_required.py
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
│   │   │   │   ├── __init__.py
│   │   │   │   ├── coordinators.py
│   │   │   │   ├── jobs.py
│   │   │   │   ├── owid_charts.py
│   │   │   │   ├── recent.py
│   │   │   │   ├── settings.py
│   │   │   │   └── templates.py
│   │   │   ├── routes.py
│   │   │   └── sidebar.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── cookie.py
│   │   │   ├── oauth.py
│   │   │   ├── rate_limit.py
│   │   │   └── routes.py
│   │   ├── copy_svg_langs_job/
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── fix_nested/
│   │   │   ├── __init__.py
│   │   │   ├── explorer_routes.py
│   │   │   ├── routes.py
│   │   │   └── worker.py
│   │   ├── main_routes/
│   │   │   ├── __init__.py
│   │   │   ├── explorer_routes.py
│   │   │   ├── extract_routes.py
│   │   │   ├── owid_charts_routes.py
│   │   │   └── routes.py
│   │   ├── templates/
│   │   │   ├── __init__.py
│   │   │   └── routes.py
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
│   │   ├── db_CreateUpdate.py
│   │   ├── db_Jobs.py
│   │   ├── db_OwidCharts.py
│   │   ├── db_Settings.py
│   │   ├── db_StageStore.py
│   │   ├── db_TasksListDB.py
│   │   ├── db_Templates.py
│   │   ├── fix_nested_task_store.py
│   │   ├── sql_schema_tables.py
│   │   ├── svg_db.py
│   │   ├── task_store_pymysql.py
│   │   ├── user_tokens.py
│   │   └── utils.py
│   ├── jobs_workers/
│   │   ├── __init__.py
│   │   ├── add_svglanguages_template/
│   │   │   ├── __init__.py
│   │   │   └── worker.py
│   │   ├── base_worker.py
│   │   ├── collect_main_files_worker.py
│   │   ├── copy_svg_langs/
│   │   │   ├── __init__.py
│   │   │   ├── steps/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── downloads/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── download.py
│   │   │   │   ├── extract/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── extract_task.py
│   │   │   │   ├── fix_nested/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── fix_nested_tasks.py
│   │   │   │   ├── injects/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── inject_tasks.py
│   │   │   │   ├── texts/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── start_bot.py
│   │   │   │   ├── titles/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── titles_tasks.py
│   │   │   │   ├── uploads/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── up.py
│   │   │   │   └── utils/
│   │   │   │       ├── __init__.py
│   │   │   │       └── tasks_utils.py
│   │   │   ├── task_threads.py
│   │   │   └── web_run_task.py
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
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── add_svglanguages_template_utils.py
│   │       └── crop_main_files_utils.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── admin_service.py
│   │   ├── jobs_service.py
│   │   ├── owid_charts_service.py
│   │   ├── tasks_service.py
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
├── offline/
│   ├── __init__.py
│   └── collect_main_files.py
├── static/
│   ├── css/
│   │   ├── navbar.css
│   │   ├── sidebar-desktop.css
│   │   ├── sidebar-mobile.css
│   │   └── style.css
│   ├── images/
│   ├── js/
│   │   ├── autocomplete.js
│   │   ├── card-tools.js
│   │   ├── dark-mode.js
│   │   ├── sidebar.js
│   │   └── SVGLanguages.js
│   └── translate.svg
├── svg_config.py
├── templates/
│   ├── _navbar.html
│   ├── admins/
│   │   ├── _sidebar.html
│   │   ├── admin.html
│   │   ├── base.html
│   │   ├── compare_crop_files.html
│   │   ├── coordinators.html
│   │   ├── jobs_templates/
│   │   │   ├── add_svglanguages_template/
│   │   │   │   ├── details.html
│   │   │   │   └── list.html
│   │   │   ├── base_details.html
│   │   │   ├── base_list.html
│   │   │   ├── collect_main_files/
│   │   │   │   ├── details.html
│   │   │   │   └── list.html
│   │   │   ├── create_owid_pages/
│   │   │   │   ├── details.html
│   │   │   │   └── list.html
│   │   │   ├── crop_main_files/
│   │   │   │   ├── details.html
│   │   │   │   └── list.html
│   │   │   ├── download_main_files/
│   │   │   │   ├── details.html
│   │   │   │   └── list.html
│   │   │   └── fix_nested_main_files/
│   │   │       ├── details.html
│   │   │       └── list.html
│   │   ├── owid_charts/
│   │   │   ├── add.html
│   │   │   ├── edit.html
│   │   │   └── list.html
│   │   ├── popup_action.html
│   │   ├── settings.html
│   │   ├── template_edit.html
│   │   └── templates.html
│   ├── admins.html
│   ├── base.html
│   ├── explorer/
│   │   ├── compare.html
│   │   ├── explore_files.html
│   │   ├── folder.html
│   │   └── index.html
│   ├── extract/
│   │   ├── form.html
│   │   └── result.html
│   ├── fix_nested/
│   │   ├── compare.html
│   │   ├── form.html
│   │   ├── task_detail.html
│   │   ├── tasks_list.html
│   │   └── upload_form.html
│   ├── index.html
│   ├── owid_charts/
│   │   ├── all_charts.html
│   │   └── index.html
│   ├── task.html
│   ├── tasks.html
│   └── templates/
│       └── index.html
└── uwsgi.ini
```
