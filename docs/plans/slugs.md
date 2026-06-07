# Improved Prompt
You are a senior Python/Flask/SQLAlchemy engineer working on an existing OWID charts application.
## Goal
The current implementation automatically replaces chart slugs when originalChartUrl indicates a redirect. This is causing issues because some redirected slugs should not be replaced.
Instead of immediately changing slugs, introduce a **database-backed slug redirect review workflow**.
## Existing Logic
### Block 1
```python
original_chart_url = metadata.get("chart", {}).get("originalChartUrl", "") 
if original_chart_url and "/grapher/" in original_chart_url: 
    original_slug = original_chart_url.split("/grapher/", maxsplit=1)[1].split("?")[0] 
    if original_slug != chart.slug: 
        data["slug"] = original_slug 

```
### Block 2
```python
if _slug_to_check: 
    metadata = fetch_grapher_metadata(_slug_to_check) 
    if metadata: 
        original_chart_url = metadata.get("chart", {}).get("originalChartUrl", "") 
        if original_chart_url and "/grapher/" in original_chart_url: 
            original_slug = original_chart_url.split("/grapher/", maxsplit=1)[1].split("?")[0] 
            if original_slug != _slug_to_check: 
                _slug = original_slug 

```
## Required Changes
### 1. Create New Database Table
Create a new SQLAlchemy model named OwidSlugRedirectRecord inside the table owid_slug_redirects.
```python
class OwidSlugRedirectRecord(db.Model):
    # Model definition goes here

```
#### Table Schema
| Column | Type | Notes |
|---|---|---|
| **id** | Integer | PK, Auto Increment |
| **slug** | String(255) | Original slug found in our system |
| **redirect_to** | String(255) | Redirect target slug |
| **should_be_replaced** | Boolean | Default: False |
| **created_at** | DateTime | Default: current timestamp |
> **Note:** Add appropriate indexes where useful.
> 
### 2. Create Service Layer
Create the file path: src/main_app/db/services/owid_slugs_redirects_service.py
Implement the following function:
```python
def add_new_slug_redirect(slug: str, redirect_to: str) -> None: 

```
**Requirements:**
 * Prevent duplicate records.
 * If (slug, redirect_to) already exists, do nothing.
 * Commit only when a new record is created.
### 3. Update Existing Redirect Detection Logic
Replace the automatic slug replacement behavior with logging to the new service.
Instead of:
```python
if original_slug != chart.slug: 
    data["slug"] = original_slug 

```
Use:
```python
if original_slug != chart.slug: 
    add_new_slug_redirect(slug=chart.slug, redirect_to=original_slug) 

```
Similarly, replace:
```python
_slug = original_slug 

```
With:
```python
add_new_slug_redirect(slug=_slug_to_check, redirect_to=original_slug) 

```
> ⚠️ **Important:** Do not modify owid_charts.slug or templates.slug, and do not perform automatic replacements. Only record the redirect for later manual review.
> 
### 4. Admin Dashboard
Create a new admin section to manage slug redirects.
 * **Route File:** src/main_app/app_routes/admin_routes/slug_redirects.py
 * **Registration:** Register the blueprint inside src/main_app/app_routes/admin/routes.py
### 5. Admin Features
Create administrative views to manage records with the following criteria:
 * **List Redirects:**
   * Display: slug, redirect_to, should_be_replaced, and created_at.
   * Features: Pagination and sorting by created_at DESC.
 * **Edit Redirect:**
   * Allow administrators to toggle the should_be_replaced boolean flag.
 * **Bulk Actions (Optional):**
   * Support marking selected items as "replace" or "do not replace".
### 6. Templates
Create the following admin templates:
 * templates/admin/slug_redirects/list.html
 * templates/admin/slug_redirects/edit.html
> **Note:** Use styling and structural UI patterns consistent with existing admin sub-pages.
> 
### 7. Existing Models for Reference
Use the following project models as examples for codebase style and conventions:
 * TemplateRecord
 * OwidChartRecord
 * TemplateNeedUpdateRecord
 * OwidChartTemplateRecord
Ensure you follow the existing project architecture for SQLAlchemy models, the service layer, admin blueprints, and templates.
## Deliverables
Provide the following production-ready components:
 1. **SQLAlchemy model** (OwidSlugRedirectRecord)
 2. **Migration SQL** script
 3. **Service implementation** (add_new_slug_redirect)
 4. **Code modifications** applied to both existing logic blocks
 5. **Admin blueprint and routing** definitions
 6. **Admin HTML templates** (list.html and edit.html)
 7. **Imports & blueprint registration** updates
