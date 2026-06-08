```
src/
├── main_app/
│   ├── api_services/
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── commons_client.py
│   │   │   ├── owid_client.py
│   │   │   └── wiki_client.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── download_file_utils.py
│   │   ├── __init__.py
│   │   ├── category.py
│   │   ├── mwclient_page.py
│   │   ├── pages_api.py
│   │   ├── query_api.py
│   │   └── upload_bot.py
│   ├── app_routes/
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── admins_required.py
│   │   │   ├── routes.py
│   │   │   └── sidebar.py
│   │   ├── admin_routes/
│   │   │   ├── __init__.py
│   │   │   ├── coordinators.py
│   │   │   ├── jobs.py
│   │   │   ├── owid_charts.py
│   │   │   ├── results_utils.py
│   │   │   ├── settings.py
│   │   │   └── templates.py
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── cookie.py
│   │   │   ├── oauth.py
│   │   │   ├── rate_limit.py
│   │   │   ├── routes.py
│   │   │   └── utils.py
│   │   ├── main_routes/
│   │   │   ├── __init__.py
│   │   │   ├── explorer_routes.py
│   │   │   ├── extract_routes.py
│   │   │   ├── owid_charts_routes.py
│   │   │   └── routes.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── compare.py
│   │   │   ├── explorer_utils.py
│   │   │   ├── routes_utils.py
│   │   │   └── thumbnail_utils.py
│   │   ├── __init__.py
│   │   ├── api_routes.py
│   │   └── public_jobs.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── classes.py
│   │   ├── flask_config.py
│   │   └── main_settings.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── cookies.py
│   │   ├── crypto.py
│   │   └── jinja_filters.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── owid_charts.csv
│   │   ├── templates_slugs_topics.json
│   │   └── topics_categories.json
│   ├── db/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── jobs.py
│   │   │   ├── owid_charts.py
│   │   │   ├── settings.py
│   │   │   ├── templates.py
│   │   │   ├── users.py
│   │   │   └── views.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── admin_service.py
│   │   │   ├── jobs_service.py
│   │   │   ├── owid_charts_service.py
│   │   │   ├── settings_service.py
│   │   │   ├── template_need_update_service.py
│   │   │   ├── template_service.py
│   │   │   ├── user_token_service.py
│   │   │   └── utils.py
│   │   ├── __init__.py
│   │   └── exceptions.py
│   ├── jobs_workers/
│   │   ├── add_svglanguages_template/
│   │   │   ├── __init__.py
│   │   │   ├── utils.py
│   │   │   └── worker.py
│   │   ├── collect_templates_data/
│   │   │   ├── __init__.py
│   │   │   └── worker.py
│   │   ├── create_owid_pages/
│   │   │   ├── __init__.py
│   │   │   ├── owid_template_converter.py
│   │   │   └── worker.py
│   │   ├── crop_main_files/
│   │   │   ├── __init__.py
│   │   │   ├── crop_file.py
│   │   │   ├── crop_utils.py
│   │   │   ├── download.py
│   │   │   ├── objects.py
│   │   │   ├── upload.py
│   │   │   └── worker.py
│   │   ├── download_main_files/
│   │   │   ├── __init__.py
│   │   │   └── worker.py
│   │   ├── fix_nested_main_files/
│   │   │   ├── __init__.py
│   │   │   └── worker.py
│   │   ├── rename_owid_pages/
│   │   │   ├── __init__.py
│   │   │   └── worker.py
│   │   ├── update_owid_charts/
│   │   │   ├── __init__.py
│   │   │   └── worker.py
│   │   ├── utils/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── base_worker.py
│   │   ├── base_worker_object.py
│   │   ├── cli_jobs.py
│   │   ├── jobs_worker.py
│   │   ├── shared_objects.py
│   │   └── workers_list.py
│   ├── public_jobs/workers/
│   │   ├── copy_svg_langs/
│   │   │   ├── steps/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── download.py
│   │   │   │   ├── extract_text.py
│   │   │   │   ├── extract_titles.py
│   │   │   │   ├── extract_translations.py
│   │   │   │   ├── fix_nested.py
│   │   │   │   ├── inject.py
│   │   │   │   └── upload.py
│   │   │   ├── __init__.py
│   │   │   └── worker.py
│   │   ├── fix_nested_jobs/
│   │   │   ├── __init__.py
│   │   │   └── worker.py
│   │   ├── __init__.py
│   │   └── workers_list_public.py
│   ├── shared/
│   │   ├── fix_nested/
│   │   │   ├── __init__.py
│   │   │   └── worker.py
│   │   ├── __init__.py
│   │   └── decode_bytes.py
│   ├── su_services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── current_user.py
│   │   ├── jobs_files_service.py
│   │   └── users_service.py
│   ├── utils/
│   │   ├── wikitext/
│   │   │   ├── titles_utils/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── last_world_file_utils.py
│   │   │   │   └── main_file.py
│   │   │   ├── __init__.py
│   │   │   ├── before_methods.py
│   │   │   ├── categories_utils.py
│   │   │   ├── files_text.py
│   │   │   ├── other_versions.py
│   │   │   ├── temp_source.py
│   │   │   ├── template_page.py
│   │   │   └── temps_bot.py
│   │   ├── __init__.py
│   │   └── verify.py
│   ├── __init__.py
│   └── extensions.py
├── offline/
│   ├── owid_metadata/
│   ├── __init__.py
│   ├── collect_templates_data.py
│   ├── error.txt
│   └── sitemap.py
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
├── templates/
│   ├── admins/
│   │   ├── jobs_templates/
│   │   │   ├── _help_templates/
│   │   │   ├── add_svglanguages_template/
│   │   │   ├── collect_templates_data/
│   │   │   ├── create_owid_pages/
│   │   │   ├── crop_main_files/
│   │   │   ├── download_main_files/
│   │   │   ├── fix_nested_main_files/
│   │   │   ├── rename_owid_pages/
│   │   │   └── update_owid_charts/
│   │   └── owid_charts/
│   ├── explorer/
│   ├── extract/
│   ├── jobs_templates/
│   │   ├── copy_svg_langs/
│   │   └── fix_nested_jobs/
│   └── owid_charts/
├── __init__.py
├── app.py
├── import_owid_charts.py
├── logger_config.py
└── uwsgi.ini

```
