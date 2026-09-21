---
name: flask-methodview-refactoring
description: Refactor traditional function-based Flask routes into Object-Oriented Class-Based Views (MethodView) with strict type hints, backward compatibility, and English documentation.
---

# Flask MethodView Refactoring Skill

This skill guides the AI agent through refactoring legacy function-based Flask routes into clean, maintainable, Object-Oriented `flask.views.MethodView` structures.

## Core Rules & Directives

1. **Architecture & Design Pattern:**

    - Convert handlers to `flask.views.MethodView` to separate HTTP methods (`get`, `post`, `put`, `delete`).
    - For single-view modules or direct view bindings, implement a `@classmethod def register(cls, bp: Blueprint)` method directly inside the `MethodView` class.
    - For complex multi-view modules, abstract shared logic into base view classes or dedicated route registrar classes.

2. **Backward Compatibility & Legacy Endpoints:**

    - When merging separate POST handlers (e.g., `edit_post`, `add_post`) into a unified `MethodView` POST method:
        - Register the primary routes using standard endpoint names (e.g., `edit`, `add`).
        - Provide temporary legacy aliases via `bp.add_url_rule` for old endpoints (e.g., `edit_post`) if existing templates or JavaScript files still depend on them via `url_for()`.
        - Always annotate temporary rules with a explicit `# TODO: Backward Compatibility` comment.

3. **Language & Comments (STRICT):**

    - Write **ALL** code comments, docstrings, and module documentation exclusively in **ENGLISH**.

4. **Type Safety & Standards:**
    - Include `from __future__ import annotations` at the top of every file.
    - Use explicit type annotations for parameters and return types (e.g., `flask.typing.ResponseReturnValue`).
    - Standardize logging with Python's built-in `logging` module (`logger = logging.getLogger(__name__)`).
    - Define explicit `__all__` exports at the end of each module.

---

## Refactoring Workflow

1. **Analyze Input:** Identify request parameters, HTTP methods, service dependencies, and template rendering targets.
2. **Design View Classes:** Inherit from `MethodView` and map logic into explicit HTTP methods (`get`, `post`).
3. **Self-Registration Pattern:** Implement `@classmethod def register(cls, bp: Blueprint)` directly inside the view class for standalone/single MethodViews.
4. **Ensure Backward Compatibility:** Create temporary aliases for historical endpoints when merging handlers.

---

## Standard Reference Examples

### Example 1: Standalone View with Classmethod Self-Registration

#### ❌ Before (Legacy Function-Based Route)

```python
@bp.route("/translate", methods=["GET"])
def translate():
    title = request.args.get("title")
    return render_template("translate.html", title=title)

```

#### ✅ After (MethodView Refactored with `@classmethod register`)

```python
"""Module for handling translation HTTP requests using MethodView."""

from __future__ import annotations

import logging
from flask import Blueprint, render_template, request
from flask.views import MethodView
from flask.typing import ResponseReturnValue

logger = logging.getLogger(__name__)


class TranslateView(MethodView):
    """View handler for translation requests."""

    def get(self) -> ResponseReturnValue:
        """Handle GET requests for page translation."""
        title = (request.args.get("title") or "").strip()
        logger.info("Processing translation request for title: %s", title)
        return render_template("translate.html", title=title)

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        """Register view routes directly on the blueprint."""
        bp.add_url_rule("/translate", view_func=cls.as_view("translate"))


__all__ = [
    "TranslateView",
]

```

---

### Example 2: Merging GET/POST with Legacy Endpoints Aliases

```python
"""Module handling edit operations with backward-compatible aliases."""

from __future__ import annotations

import logging
from flask import Blueprint, render_template, request, redirect, url_for
from flask.views import MethodView
from flask.typing import ResponseReturnValue

logger = logging.getLogger(__name__)


class EditItemView(MethodView):
    """View handler for viewing and submitting item edits."""

    def get(self) -> ResponseReturnValue:
        """Render the item edit form."""
        item_id = request.args.get("id")
        return render_template("edit.html", item_id=item_id)

    def post(self) -> ResponseReturnValue:
        """Process item update form submission."""
        item_id = request.form.get("id")
        logger.info("Updating item %s", item_id)
        return redirect(url_for("adminpanel.index"))

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        """Register primary endpoint and legacy aliases on the blueprint."""
        # Primary unified MethodView endpoint
        bp.add_url_rule("/edit", view_func=cls.as_view("edit"))

        # ------------------------------------------------------------------
        # TODO: Backward Compatibility / Temporary Aliases
        # Legacy POST endpoint 'edit_post' merged into EditItemView POST handler.
        # Remove this rule once all template forms and url_for calls are updated.
        # ------------------------------------------------------------------
        bp.add_url_rule(
            "/edit",
            endpoint="edit_post",
            view_func=cls.as_view("legacy_edit_post"),
            methods=["POST"],
        )


__all__ = [
    "EditItemView",
]

```

---

## Execution Target

When provided with any Python/Flask code file:

-   Apply the rules and workflow above.
-   Prefer self-registration (`@classmethod def register`) for standalone/single MethodViews.
-   Handle legacy endpoint aliases cleanly with `# TODO: Backward Compatibility` blocks where applicable.
-   Output clean, fully refactored Python code.

```

```
