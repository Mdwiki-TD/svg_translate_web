```
src/
├── main_app/
│   ├── admin/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── coordinators.py
│   │   │   ├── errors_route.py
│   │   │   ├── jobs.py
│   │   │   ├── owid_charts.py
│   │   │   ├── settings.py
│   │   │   ├── slug_redirects.py
│   │   │   ├── templates.py
│   │   │   └── users.py
│   │   ├── __init__.py
│   │   ├── admin_panel.py
│   │   ├── decorators.py
│   │   └── sidebar.py
│   ├── api_services/
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── commons_client.py
│   │   │   ├── owid_client.py
│   │   │   └── wiki_client.py
│   │   ├── files_service/
│   │   │   ├── __init__.py
│   │   │   ├── download_file_utils.py
│   │   │   ├── files_helpers.py
│   │   │   └── upload_bot.py
│   │   ├── mwclient_page/
│   │   │   ├── __init__.py
│   │   │   ├── mwclient_error.py
│   │   │   └── mwclient_wraper.py
│   │   ├── utils/
│   │   ├── __init__.py
│   │   ├── category.py
│   │   ├── query_api.py
│   │   └── README.md
│   ├── config/
│   │   ├── __init__.py
│   │   ├── classes.py
│   │   ├── flask_config.py
│   │   └── main_settings.py
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
│   │   │   ├── owid_slug_redirects.py
│   │   │   ├── settings.py
│   │   │   ├── templates.py
│   │   │   ├── users.py
│   │   │   └── views.py
│   │   ├── services/
│   │   │   ├── utils/
│   │   │   │   ├── __init__.py
│   │   │   │   └── retry_on_disconnect.py
│   │   │   ├── __init__.py
│   │   │   ├── admin_service.py
│   │   │   ├── charts_and_templates_service.py
│   │   │   ├── crud_service.py
│   │   │   ├── jobs_service.py
│   │   │   ├── owid_charts_service.py
│   │   │   ├── owid_slug_redirects_service.py
│   │   │   ├── settings_service.py
│   │   │   ├── template_service.py
│   │   │   ├── user_token_service.py
│   │   │   ├── users_service.py
│   │   │   └── views_service.py
│   │   ├── __init__.py
│   │   ├── create_helper.py
│   │   ├── exceptions.py
│   │   └── templates_utils.py
│   ├── extensions/
│   │   ├── __init__.py
│   │   ├── _csrf.py
│   │   └── data_base.py
│   ├── jobs_workers/
│   │   ├── admin_jobs_workers/
│   │   │   ├── add_lang_categories_to_owid_pages/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── runner.py
│   │   │   │   ├── utils.py
│   │   │   │   └── worker.py
│   │   │   ├── add_svglanguages_template/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── runner.py
│   │   │   │   ├── utils.py
│   │   │   │   └── worker.py
│   │   │   ├── collect_templates_data/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── runner.py
│   │   │   │   └── worker.py
│   │   │   ├── create_owid_pages/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── owid_template_converter.py
│   │   │   │   ├── runner.py
│   │   │   │   └── worker.py
│   │   │   ├── crop_main_files/
│   │   │   │   ├── steps/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── crop_file.py
│   │   │   │   │   ├── crop_utils.py
│   │   │   │   │   ├── download.py
│   │   │   │   │   └── upload.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── runner.py
│   │   │   │   └── worker.py
│   │   │   ├── download_main_files/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── download_helper.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── runner.py
│   │   │   │   └── worker.py
│   │   │   ├── fix_nested_main_files/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── runner.py
│   │   │   │   └── worker.py
│   │   │   ├── rename_owid_pages/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── runner.py
│   │   │   │   └── worker.py
│   │   │   ├── update_owid_charts/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── runner.py
│   │   │   │   └── worker.py
│   │   │   ├── __init__.py
│   │   │   ├── slugs_helpers.py
│   │   │   └── workers_list.py
│   │   ├── public_jobs_workers/
│   │   │   ├── copy_svg_langs/
│   │   │   │   ├── steps/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── extract_text.py
│   │   │   │   │   ├── extract_titles.py
│   │   │   │   │   ├── extract_translations.py
│   │   │   │   │   └── inject_one_file.py
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── runner.py
│   │   │   │   └── worker.py
│   │   │   ├── fix_nested_jobs/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── objects.py
│   │   │   │   ├── runner.py
│   │   │   │   └── worker.py
│   │   │   ├── __init__.py
│   │   │   └── workers_list_public.py
│   │   ├── utils/
│   │   │   └── __init__.py
│   │   ├── __init__.py
│   │   ├── base_worker.py
│   │   ├── cli_jobs.py
│   │   ├── jobs_worker.py
│   │   ├── objects.py
│   │   └── shared_objects.py
│   ├── public/
│   │   ├── auth/
│   │   │   ├── __init__.py
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
│   │   ├── shared_jobs_routes.py
│   │   ├── jobs_utils_bp.py
│   │   ├── profile.py
│   │   └── public_jobs.py
│   ├── services/
│   │   ├── auth/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── auth_users_service.py
│   │   │   ├── current_user.py
│   │   │   └── mwoauth_handshake.py
│   │   ├── core/
│   │   │   ├── cookies/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── cookie.py
│   │   │   │   └── cookie_header_client.py
│   │   │   ├── __init__.py
│   │   │   ├── crypto.py
│   │   │   └── jinja_filters.py
│   │   ├── fix_nested/
│   │   │   ├── __init__.py
│   │   │   └── worker.py
│   │   ├── __init__.py
│   │   ├── decode_bytes.py
│   │   └── owid_charts_utils.py
│   ├── io/
│   │   ├── __init__.py
│   │   └── jobs_files_service.py
│   ├── utils/
│   │   ├── wikitext/
│   │   │   ├── owid_sliders_rcs/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── main_file.py
│   │   │   │   └── owidslidersrcs_utils.py
│   │   │   ├── __init__.py
│   │   │   ├── before_methods.py
│   │   │   ├── categories_utils.py
│   │   │   ├── files_text.py
│   │   │   ├── other_versions.py
│   │   │   ├── temp_source.py
│   │   │   ├── template_page.py
│   │   │   └── temps_bot.py
│   │   ├── __init__.py
│   │   ├── file_langs.py
│   │   └── verify.py
│   └── __init__.py
├── offline/
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
│   │   ├── auto-refresh.js
│   │   ├── autocomplete.js
│   │   ├── card-tools.js
│   │   ├── dark-mode.js
│   │   ├── sidebar.js
│   │   └── SVGLanguages.js
│   └── favicon.ico
├── templates/
│   ├── _macros/
│   ├── admin/
│   │   └── admin/
│   │       ├── file/
│   │       │   └── modals/
│   │       ├── model/
│   │       │   └── modals/
│   │       └── rediscli/
│   ├── admins/
│   │   ├── owid_charts/
│   │   └── slug_redirects/
│   ├── explorer/
│   ├── extract/
│   ├── jobs_templates/
│   │   ├── _help_templates/
│   │   ├── admin_templates/
│   │   │   ├── add_lang_categories_to_owid_pages/
│   │   │   ├── add_svglanguages_template/
│   │   │   ├── collect_templates_data/
│   │   │   ├── create_owid_pages/
│   │   │   ├── crop_main_files/
│   │   │   ├── download_main_files/
│   │   │   ├── fix_nested_main_files/
│   │   │   ├── rename_owid_pages/
│   │   │   └── update_owid_charts/
│   │   └── public/
│   │       ├── copy_svg_langs/
│   │       └── fix_nested_jobs/
│   └── owid_charts/
├── __init__.py
├── app.py
├── import_owid_charts.py
├── logger_config.py
└── uwsgi.ini

```
