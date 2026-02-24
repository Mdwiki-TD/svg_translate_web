# Templates Page Optimization Plan

## Problem Statement

The current [`templates.html`](src/templates/admins/templates.html:69-102) renders **2 HTML forms per template entry** multiplied by ~1500 templates in the database. This causes:

-   Excessive DOM elements (3000+ forms, 6000+ inputs)
-   Slow page load times
-   Browser performance degradation
-   Potential crashes on lower-end devices

## Current Implementation

```html
<!-- Current: Forms inside table rows -->
{% for template in templates %}
<tr>
    <form
        method="post"
        action="{{ url_for('admin.update_template') }}">
        <!-- 4 hidden/input fields + csrf token -->
        <td>...</td>
        <td>
            <input
                name="title"
                value="{{ template.title }}" />
        </td>
        <td>
            <input
                name="main_file"
                value="{{ template.main_file }}" />
        </td>
        <td>
            <input
                name="last_world_file"
                value="{{ template.last_world_file }}" />
        </td>
        <td><button type="submit">Save</button></td>
    </form>
    <td>
        <form
            method="post"
            action="{{ url_for('admin.delete_template', template_id=template.id) }}">
            <button type="submit">Delete</button>
        </form>
    </td>
</tr>
{% endfor %}
```

## Proposed Solution

Replace inline edit forms with a **popup window editing approach**:

1. Display templates as read-only data
2. Single "Edit" button per row that opens a popup
3. Edit form moved to a separate page/template

---

## Implementation Steps

### Phase 1: Frontend - Update Templates List Page

**File:** [`src/templates/admins/templates.html`](src/templates/admins/templates.html)

#### 1.1 Remove Forms from Table Rows

Replace the form-based row with display-only data:

```html
{% for template in templates %}
<tr>
    <td>{{ template.id }}</td>
    <td>{{ template.title }}</td>
    <td class="text-center">{{ template.main_file or '-' }}</td>
    <td class="text-center">{{ template.last_world_file or '-' }}</td>
    <td class="text-center">
        <button
            type="button"
            class="btn btn-outline-primary btn-sm"
            pup-target="{{ url_for('admin.edit_template', template_id=template.id) }}"
            onclick="pup_window_new(this)">
            <i class="bi bi-pencil"></i> Edit
        </button>
    </td>
</tr>
{% endfor %}
```

#### 1.2 Update Table Headers

Change headers from:

```html
<th>Save</th>
<th>Delete</th>
```

To:

```html
<th>Actions</th>
```

#### 1.3 Add JavaScript Function

Add to the page (or external JS file):

```javascript
function pup_window_new(element) {
    var target = $(element).attr("pup-target");
    window.open(
        target,
        "",
        "width=600,height=400,left=100,top=100,location=no"
    );
}
```

---

### Phase 2: Backend - Add Edit Template Route

**File:** [`src/main_app/app_routes/admin/admin_routes/templates.py`](src/main_app/app_routes/admin/admin_routes/templates.py)

#### 2.1 Add GET Route for Edit Page

```python
def _edit_template(template_id: int) -> ResponseReturnValue:
    """Render the edit template popup page."""
    try:
        template = template_service.get_template(template_id)
    except LookupError:
        return render_template(
            "admins/template_edit.html",
            error="Template not found",
            template=None,
        )

    return render_template(
        "admins/template_edit.html",
        template=template,
        error=None,
    )
```

#### 2.2 Add Service Method (if not exists)

**File:** [`src/main_app/template_service.py`](src/main_app/template_service.py)

Add or verify existence of:

```python
def get_template(template_id: int) -> TemplateRecord:
    """Fetch a single template by ID."""
    db = _templates_db()
    return db.fetch_by_id(template_id)
```

#### 2.3 Register New Route

In the [`Templates`](src/main_app/app_routes/admin/admin_routes/templates.py:111) class:

```python
@bp_admin.get("/templates/<int:template_id>/edit")
@admin_required
def edit_template(template_id: int) -> ResponseReturnValue:
    return _edit_template(template_id)
```

---

### Phase 3: Create Edit Template Popup Page

**New File:** `src/templates/admins/template_edit.html`

```html
{% extends "admins/base.html" %} {% block title %}Edit Template · Copy SVG
Translation{% endblock %} {% block contents %}
<div class="container mt-4">
    {% if error %}
    <div
        class="alert alert-danger"
        role="alert">
        {{ error }}
    </div>
    {% else %}
    <div class="card">
        <div class="card-header">
            <h5 class="mb-0">Edit Template: {{ template.title }}</h5>
        </div>
        <div class="card-body">
            <form
                method="post"
                action="{{ url_for('admin.update_template') }}">
                <input
                    type="hidden"
                    name="csrf_token"
                    value="{{ csrf_token() }}" />
                <input
                    type="hidden"
                    name="id"
                    value="{{ template.id }}" />

                <div class="mb-3">
                    <label
                        for="title"
                        class="form-label"
                        >Template Name</label
                    >
                    <input
                        type="text"
                        class="form-control"
                        id="title"
                        name="title"
                        value="{{ template.title }}"
                        required />
                </div>

                <div class="mb-3">
                    <label
                        for="main_file"
                        class="form-label"
                        >Main File</label
                    >
                    <input
                        type="text"
                        class="form-control"
                        id="main_file"
                        name="main_file"
                        value="{{ template.main_file or '' }}" />
                </div>

                <div class="mb-3">
                    <label
                        for="last_world_file"
                        class="form-label"
                        >Last World File</label
                    >
                    <input
                        type="text"
                        class="form-control"
                        id="last_world_file"
                        name="last_world_file"
                        value="{{ template.last_world_file or '' }}" />
                </div>

                <div class="d-flex justify-content-between">
                    <button
                        type="submit"
                        class="btn btn-primary">
                        <i class="bi bi-save"></i> Save Changes
                    </button>

                    <form
                        method="post"
                        action="{{ url_for('admin.delete_template', template_id=template.id) }}"
                        class="d-inline"
                        onsubmit="return confirm('Are you sure you want to delete {{ template.title }}?');">
                        <input
                            type="hidden"
                            name="csrf_token"
                            value="{{ csrf_token() }}" />
                        <button
                            type="submit"
                            class="btn btn-outline-danger">
                            <i class="bi bi-trash"></i> Delete
                        </button>
                    </form>
                </div>
            </form>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}
```

---

### Phase 4: Update Database Layer (if needed)

**File:** [`src/main_app/db/db_Templates.py`](src/main_app/db/db_Templates.py)

Verify [`fetch_by_id()`](src/main_app/db/db_Templates.py:75) is public or create a wrapper:

```python
def fetch_by_id(self, template_id: int) -> TemplateRecord:
    """Fetch a single template by its ID."""
    return self._fetch_by_id(template_id)
```

---

### Phase 5: Update Routes Registration

**File:** [`src/main_app/app_routes/admin/admin_routes/templates.py`](src/main_app/app_routes/admin/admin_routes/templates.py:111)

Add the new route registration in the [`Templates.__init__()`](src/main_app/app_routes/admin/admin_routes/templates.py:112) method.

---

## File Changes Summary

| File                                                                                                                 | Action            | Description                                      |
| -------------------------------------------------------------------------------------------------------------------- | ----------------- | ------------------------------------------------ |
| [`src/templates/admins/templates.html`](src/templates/admins/templates.html)                                         | Modify            | Remove forms, add Edit buttons with `pup-target` |
| `src/templates/admins/template_edit.html`                                                                            | Create            | New popup page for editing templates             |
| [`src/main_app/app_routes/admin/admin_routes/templates.py`](src/main_app/app_routes/admin/admin_routes/templates.py) | Modify            | Add `_edit_template()` function and route        |
| [`src/main_app/template_service.py`](src/main_app/template_service.py)                                               | Modify (optional) | Add `get_template()` if not exists               |
| [`src/main_app/db/db_Templates.py`](src/main_app/db/db_Templates.py)                                                 | Modify (optional) | Make `fetch_by_id()` public if needed            |

---

## Expected Performance Improvement

| Metric         | Before     | After             |
| -------------- | ---------- | ----------------- |
| DOM Elements   | ~15,000+   | ~500              |
| Forms          | 3,000      | 1 (add form only) |
| Input Fields   | 6,000+     | 3 (add form only) |
| CSRF Tokens    | 3,000      | 1                 |
| Page Load Time | Slow (>5s) | Fast (<1s)        |

---

## Testing Checklist

-   [ ] Edit button opens popup window with correct dimensions
-   [ ] Popup loads template data correctly
-   [ ] Save changes updates the template
-   [ ] Delete button works in popup
-   [ ] CSRF protection works correctly
-   [ ] Non-existent template ID shows error
-   [ ] Main templates list refreshes after popup close (manual refresh)
-   [ ] Responsive design works on different screen sizes

---

## Notes

1. **jQuery Dependency**: The [`pup_window_new()`](src/templates/admins/templates.html:69) function uses `$(element)` which requires jQuery. Ensure jQuery is loaded in the base template.

2. **Popup Window**: The popup opens as a new window (not modal dialog) for simplicity. Consider upgrading to a Bootstrap modal for better UX.

3. **Page Refresh**: After editing in popup, the main list won't auto-refresh. User needs to manually refresh or implement `window.opener.location.reload()` after successful save.

4. **Mobile Considerations**: Popup windows may be blocked on mobile browsers. Consider an alternative mobile-friendly approach.

---

_Plan Created: 2026-02-24_
_Status: Ready for Implementation_
