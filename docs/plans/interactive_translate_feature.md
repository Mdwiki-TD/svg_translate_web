# Interactive SVG Translation Plan

This plan details the design and implementation of the Interactive SVG Translation feature. This feature allows logged-in users to interactively translate or edit SVG translation strings directly through the web UI and upload the modified SVG back to Wikimedia Commons.

## 1. Overview
Currently, the application allows users to extract translations to JSON and inject full JSON translation datasets. This feature closes the loop by providing a user-friendly interface similar to the standard SVGTranslate tool:
- The user enters a Commons SVG file and a target language code.
- The tool extracts all English (original) text strings from the SVG.
- For each English string, the user is shown the existing translation (if any) and a textbox to add/edit the translation for the selected language.
- Upon saving, the tool compiles the translations, injects them into the SVG file, and uploads the updated SVG to Wikimedia Commons on behalf of the user using OAuth.

## 2. Endpoints & Flow
The feature is exposed through a new blueprint under the `/translate` URL prefix:

- **`GET /translate/`** (`TranslateRoutes.dashboard`)
  - Displays a search/selection form.
  - Inputs:
    - `filename`: Wikimedia Commons SVG file (e.g., `File:Example.svg`).
    - `lang`: Target language code (e.g., `ar`, `fr`, `es`).
  - Required: User must be logged in via OAuth (`@oauth_required`).

- **`GET /translate/edit`** (`TranslateRoutes.edit_get`)
  - Processes the filename and language.
  - Downloads the original SVG file to a temporary directory.
  - Extracts current translation structure using `extract_from_path()`.
  - Identifies all original (English) source strings.
  - Pre-fills input fields with existing translations for the selected language if they exist.
  - Renders the interactive translation editor template (`translate/edit.html`).

- **`POST /translate/save`** (`TranslateRoutes.save_post`)
  - Receives the submitted translations.
  - Re-downloads the SVG file to ensure we are working on the freshest copy.
  - Integrates the newly entered/edited translations into the extracted translations mapping.
  - Performs SVG translation injection into the SVG file using `inject_step_one_file()`.
  - Connects to MediaWiki Commons using the user's OAuth credentials (`get_user_site`).
  - Uploads the translated SVG back to Wikimedia Commons with an automated, descriptive edit summary.
  - Redirects back or displays a success confirmation.

## 3. UI/Templates
- `src/templates/translate/form.html`: Simple select form with filename and language fields, extending `base.html`.
- `src/templates/translate/edit.html`: Editor page.
  - Table or card-based list of source English strings.
  - Parallel textboxes for entering translation in the target language.
  - Standard bootstrap/responsive design.

## 4. Dependencies
- `@oauth_required` from `src.main_app.public.auth.utils` to protect all routes.
- `FilesService` from `src.main_app.api_services` for downloading files.
- `UploadService` from `src.main_app.api_services` for uploading files to Commons.
- `extract_from_path` & `inject_step_one_file` from `src.main_app.shared.copysvg_wrapper` for SVG translation processing.
