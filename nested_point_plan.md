
## **Implementation Plan:  Fix Nested File Endpoint**

### **Overview**
Create a new route endpoint that allows users to submit a file name (e.g., `File: Dengue_fever_deaths,_2000_to_2021,_AGO.svg`), downloads it, fixes nested tags, and uploads it back to Wikimedia Commons.

---

### **Step 1: Create New Blueprint Route Module**

**Location**: `src/app/app_routes/fix_nested/`

Create the following files:

1. **`src/app/app_routes/fix_nested/__init__.py`**
   - Export the blueprint `bp_fix_nested`

2. **`src/app/app_routes/fix_nested/routes. py`**
   - Contains the main route handlers
   - Two endpoints:
     - `GET /fix_nested` - Display form to input file name
     - `POST /fix_nested` - Process the file fix request

---

### **Step 2: Route Handler Logic**

**File**:  `src/app/app_routes/fix_nested/routes.py`

#### **GET Route** (`/fix_nested`)
- Render a template with a form
- Form fields:
  - Text input for file name (with placeholder:  "File:Example.svg")
  - Submit button

#### **POST Route** (`/fix_nested`)
```python
from pathlib import Path
from flask import Blueprint, render_template, request, flash, redirect, url_for
from ... tasks.downloads. download import download_one_file
from CopySVGTranslation import match_nested_tags, fix_nested_file
from ...tasks.uploads.upload_bot import upload_file
from ...users.current import get_current_user
import logging

bp_fix_nested = Blueprint("fix_nested", __name__, url_prefix="/fix_nested")
logger = logging.getLogger("svg_translate")

@bp_fix_nested.route("/", methods=["GET", "POST"])
def fix_nested():
    if request.method == "GET":
        return render_template("fix_nested/form.html")

    # POST logic
    filename = request.form.get("filename", "").strip()

    # Remove "File:" prefix if present
    if filename.lower().startswith("file:"):
        filename = filename. split(":", 1)[1].strip()

    if not filename:
        flash("Please provide a file name", "danger")
        return redirect(url_for("fix_nested.fix_nested"))

    # Call processing function
    result = process_fix_nested(filename)

    if result["success"]:
        flash(result["message"], "success")
    else:
        flash(result["message"], "danger")

    return redirect(url_for("fix_nested.fix_nested"))
```

---

### **Step 3: Processing Function**

**File**: `src/app/app_routes/fix_nested/fix_utils.py`

```python

from pathlib import Path
from ...tasks.downloads.download import download_one_file
from CopySVGTranslation import match_nested_tags, fix_nested_file
from ...tasks.uploads.upload_bot import upload_file
import logging
import tempfile

logger = logging.getLogger("svg_translate")


def download_svg_file(filename: str, temp_dir: Path) -> dict:
    """Download SVG file and return file path or error info."""
    logger.info(f"Downloading file: {filename}")

    file_data = download_one_file(
        title=filename,
        out_dir=temp_dir,
        i=1,
        overwrite=True,
    )

    if file_data.get("result") != "success":
        return {
            "ok": False,
            "error": "download_failed",
            "details": file_data,
        }

    return {
        "ok": True,
        "path": Path(file_data["path"]),
    }


def detect_nested_tags(file_path: Path) -> dict:
    """Detect nested tags in SVG file."""
    nested = match_nested_tags(str(file_path))
    return {
        "count": len(nested),
        "tags": nested,
    }


def fix_nested_tags(file_path: Path) -> bool:
    """Fix nested tags in-place."""
    logger.info(f"Fixing nested tags in: {file_path.name}")
    return bool(fix_nested_file(file_path, file_path))


def verify_fix(file_path: Path, before_count: int) -> dict:
    """Verify nested tags count after fix."""
    after = match_nested_tags(str(file_path))
    after_count = len(after)

    return {
        "before": before_count,
        "after": after_count,
        "fixed": max(0, before_count - after_count),
    }


def upload_fixed_svg(
    filename: str,
    file_path: Path,
    tags_fixed: int,
) -> dict:
    """Upload fixed SVG file to Commons."""
    from ...users.current import get_current_user

    user = get_current_user()
    if not user:
        return {
            "ok": False,
            "error": "unauthenticated",
        }

    site = get_user_site(user)

    logger.info(f"Uploading fixed file: {filename}")

    result = upload_file(
        file_name=filename,
        file_path=file_path,
        site=site,
        summary=f"Fixed {tags_fixed} nested tag(s) using svg_translate_web",
    )

    if not result:
        return {
            "ok": False,
            "error": "upload_failed",
        }

    return {
        "ok": True,
        "result": result,
    }


def process_fix_nested(filename: str) -> dict:
    """High-level orchestration for fixing nested SVG tags."""
    temp_dir = Path(tempfile.mkdtemp())

    download = download_svg_file(filename, temp_dir)
    if not download["ok"]:
        return {
            "success": False,
            "message": f"Failed to download file: {filename}",
            "details": download,
        }

    file_path = download["path"]

    detect_before = detect_nested_tags(file_path)
    if detect_before["count"] == 0:
        return {
            "success": False,
            "message": f"No nested tags found in {filename}",
            "details": {"nested_count": 0},
        }

    if not fix_nested_tags(file_path):
        return {
            "success": False,
            "message": f"Failed to fix nested tags in {filename}",
            "details": {"nested_count": detect_before["count"]},
        }

    verify = verify_fix(file_path, detect_before["count"])
    if verify["fixed"] == 0:
        return {
            "success": False,
            "message": f"No nested tags were fixed in {filename}",
            "details": verify,
        }

    upload = upload_fixed_svg(filename, file_path, verify["fixed"])
    if not upload["ok"]:
        return {
            "success": False,
            "message": f"Upload failed for {filename}",
            "details": {**verify, **upload},
        }

    return {
        "success": True,
        "message": f"Successfully fixed and uploaded {filename}",
        "details": {
            **verify,
            "upload_result": upload["result"],
        },
    }

```

---

### **Step 4: Create Template**

**File**: `src/templates/fix_nested/form.html`

```html
{% extends "base.html" %}

{% block title %}Fix Nested SVG Tags{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0">
                        <i class="bi bi-wrench-adjustable"></i> Fix Nested SVG Tags
                    </h3>
                </div>
                <div class="card-body">
                    <p class="text-muted">
                        Enter a file name to download, fix nested tags, and upload back to Wikimedia Commons.
                    </p>

                    <form method="POST" action="{{ url_for('fix_nested.fix_nested') }}">
                        <div class="mb-3">
                            <label for="filename" class="form-label">
                                File Name <span class="text-danger">*</span>
                            </label>
                            <input
                                type="text"
                                class="form-control"
                                id="filename"
                                name="filename"
                                placeholder="File: Dengue_fever_deaths,_2000_to_2021,_AGO.svg"
                                required
                            >
                            <div class="form-text">
                                You can include or omit the "File:" prefix
                            </div>
                        </div>

                        <div class="d-grid gap-2">
                            <button type="submit" class="btn btn-primary">
                                <i class="bi bi-tools"></i> Fix Nested Tags
                            </button>
                        </div>
                    </form>

                    <hr class="my-4">

                    <div class="alert alert-info">
                        <h5 class="alert-heading">
                            <i class="bi bi-info-circle"></i> What does this do?
                        </h5>
                        <ol class="mb-0">
                            <li>Downloads the specified SVG file</li>
                            <li>Analyzes it for nested tags</li>
                            <li>Fixes any nested tags found (up to 10 levels)</li>
                            <li>Uploads the fixed file back to Commons</li>
                        </ol>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

### **Step 5: Register Blueprint**

**Update**: `src/app/app_routes/__init__.py`

```python
from .auth. routes import bp_auth
from .main.routes import bp_main
from .explorer.routes import bp_explorer
from .templates.routes import bp_templates
from .cancel_restart.routes import bp_tasks_managers
from .tasks.routes import bp_tasks, close_task_store
from .admin.routes import bp_admin
from .fix_nested.routes import bp_fix_nested  # Add this

__all__ = [
    "bp_auth",
    "bp_main",
    "bp_explorer",
    "bp_templates",
    "bp_tasks",
    "bp_tasks_managers",
    "bp_admin",
    "bp_fix_nested",  # Add this
    "close_task_store",
]
```

**Update**: `src/app/__init__.py`

```python
from .app_routes import (
    bp_admin,
    bp_auth,
    bp_main,
    bp_tasks,
    bp_explorer,
    bp_templates,
    bp_tasks_managers,
    bp_fix_nested,  # Add this
    close_task_store,
)

# ... later in create_app() ...
app.register_blueprint(bp_fix_nested)  # Add this line
```

---

### **Step 6: Add Navigation Link (Optional)**

Add a link to the main navigation or admin panel to access `/fix_nested`.

---

### **Step 7: Error Handling Enhancements**

Add specific flash messages for:
- File not found on Commons
- Download failures
- No nested tags found
- Fix failed (file too complex, >10 nested levels)
- Upload failures (permissions, rate limits)
- Authentication errors

---

### **Step 8: Testing Plan**

1. **Unit Tests** (`tests/test_fix_nested.py`):
   - Test with valid file name
   - Test with "File:" prefix
   - Test with non-existent file
   - Test with file without nested tags
   - Test with file having nested tags

2. **Integration Tests**:
   - Mock download, fix, and upload functions
   - Test error scenarios

3. **Manual Testing**:
   - Test with actual Commons files
   - Verify upload permissions
   - Check flash messages

---

### **Summary of Files to Create/Modify**

#### **New Files**:
1. `src/app/app_routes/fix_nested/__init__.py`
2. `src/app/app_routes/fix_nested/routes.py`
3. `src/app/app_routes/fix_nested/fix_utils.py`
4. `src/templates/fix_nested/form.html`
5. `tests/test_fix_nested.py` (optional)

#### **Modified Files**:
1. `src/app/app_routes/__init__.py`
2. `src/app/__init__.py`

---

### **Additional Considerations**

1. **Rate Limiting**: Add rate limiting to prevent abuse
2. **Logging**: Comprehensive logging at each step
3. **User Authentication**: Ensure user is logged in before allowing fixes
4. **File Size Limits**: Consider adding max file size checks
5. **Queue System**: For large files, consider async processing
6. **Result History**: Store fix results in database for audit trail
