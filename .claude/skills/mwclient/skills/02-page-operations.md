---
name: mwclient-page-operations
description: Reading, editing, moving, deleting, and managing MediaWiki pages with mwclient — text(), edit(), save(), append(), prepend(), move(), delete(), purge().
applies_to:
    - "Page"
    - "text"
    - "edit"
    - "save"
    - "append"
    - "prepend"
    - "move"
    - "delete"
    - "purge"
    - "touch"
    - "wikitext"
---

# Page Operations

## When to use this file

When the user needs to read page content, edit pages, move/delete pages, or manage page state.

## Mental model

A `Page` object represents a single wiki page. It's obtained from `site.pages['Title']` (no API call yet — just a handle). Content is fetched lazily on `page.text()`. Edits use `page.edit()`/`page.save()` with automatic edit conflict detection. The library checks permissions (`can('edit')`) and auth state before sending the API request.

## Quick reference

| Task             | Code                                      |
| ---------------- | ----------------------------------------- |
| Get page handle  | `page = site.pages['Title']`              |
| Read wikitext    | `text = page.text()`                      |
| Read a section   | `text = page.text(section=2)`             |
| Check existence  | `if page.exists:`                         |
| Full edit        | `page.save('new text', summary='reason')` |
| Append           | `page.append('text', summary='reason')`   |
| Prepend          | `page.prepend('text', summary='reason')`  |
| Null edit        | `page.touch()`                            |
| Move page        | `page.move('New Title', reason='why')`    |
| Delete page      | `page.delete(reason='why')`               |
| Purge cache      | `page.purge()`                            |
| Check permission | `if page.can('edit'):`                    |
| Resolve redirect | `target = page.resolve_redirect()`        |

## Reading page content

### Basic read

```python
page = site.pages['Python (programming language)']
if page.exists:
    text = page.text()
    print(text[:500])
```

`page.text()` returns `''` for non-existent pages — no exception raised. Check `page.exists` if you need to distinguish between empty and missing.

### Read a specific section

```python
text = page.text(section=2)        # By section number
text = page.text(section='History')  # By section heading
```

### Expand templates

```python
text = page.text(expandtemplates=True)
```

### Content slots (MW >= 1.32)

```python
text = page.text(slot='main')  # Default
```

### Force fresh read

```python
text = page.text(cache=False)  # Bypasses the in-memory cache
```

The text cache is keyed by `(section, expandtemplates)` and cleared automatically after edits.

### Read by page ID

```python
import mwclient.page
page = mwclient.page.Page(site, 12345)
print(page.name, page.text()[:100])
```

## Page attributes

After construction (or first API interaction), a Page has these attributes:

```python
page.name             # Full title, e.g. "Talk:Foo"
page.page_title       # Title without namespace prefix
page.namespace        # Namespace number (0=main, 1=talk, etc.)
page.exists           # bool
page.pageid           # int (0 if not exists)
page.revision         # dict with current revision info
page.length           # Size in bytes
page.touched          # Last touched timestamp
page.protection       # list of protection settings
page.redirect         # bool
page.contentmodel     # e.g. "wikitext"
page.pagelanguage     # Language code
```

## Editing pages

### Full page replacement

```python
page = site.pages['User:MyBot/Sandbox']
page.save('New content here', summary='Replaced content')
```

`save()` is an alias for `edit()`. Both do the same thing.

### Edit a section

```python
page.edit('New section content', summary='Updating section', section='2')
```

### Append text

```python
page.append('\n* New list item', summary='Adding item')
```

Uses the `appendtext` API parameter — no need to read the page first.

### Prepend text

```python
page.prepend('{{Notice}}\n', summary='Adding notice')
```

Uses the `prependtext` API parameter.

### Edit flags

```python
page.save(
    'content',
    summary='edit summary',
    minor=True,     # Mark as minor edit
    bot=True,       # Mark as bot edit (default: True)
)
```

### Additional edit parameters

Extra `**kwargs` are passed directly to the API:

```python
page.save('content', summary='edit',
    recreate=True,       # Recreate if previously deleted
    createonly=False,    # Don't fail if page exists
    nocreate=False,      # Don't fail if page doesn't exist
    watchlist='nochange',
)
```

## Edit conflict detection

The library automatically sends two timestamps to detect edit conflicts:

-   `basetimestamp`: The timestamp of the revision you read (set by `page.text()`)
-   `starttimestamp`: When you started editing (set when the Page object was created or `text()` was called)

If someone edits the page between your `text()` and `save()` calls, the API returns an `editconflict` error and mwclient raises `EditError`.

```python
page = site.pages['Some Page']
old_text = page.text()  # Sets basetimestamp

new_text = old_text.replace('old', 'new')
try:
    page.save(new_text, summary='Updating')
except mwclient.errors.EditError:
    print("Edit conflict — someone else edited this page")
```

## Page management

### Move a page

```python
page.move('New Title', reason='Renaming')
page.move('New Title', reason='Renaming', no_redirect=True)
page.move('New Title', reason='Renaming', move_talk=False, move_subpages=True)
```

Checks `can('move')` first. Raises `InsufficientPermission` if not allowed.

### Delete a page

```python
page.delete(reason='Removing spam')
page.delete(reason='Cleanup', watch=True)
```

Checks `can('delete')` first. Sets `page.exists = False` on success.

### Purge parser cache

```python
page.purge()
```

Forces re-rendering of templates and dynamic content.

### Null edit

```python
page.touch()
```

Appends empty string. Useful for updating cached data (e.g., Semantic MediaWiki properties).

## Permissions

```python
if page.can('edit'):
    page.save('content', summary='edit')
else:
    print(f"Page is protected at a level you can't edit")
```

`can(action)` checks the page's protection level against the current user's rights. Maps `'sysop'` to `'editprotected'`.

## Redirects

```python
page = site.pages['Some Redirect']
target = page.redirects_to()      # Returns target Page or None
target = page.resolve_redirect()  # Follows chain, returns self if not redirect
```

## Edge cases and gotchas

-   **Empty vs. nonexistent**: `page.text()` returns `''` for both empty pages and non-existent pages. Use `page.exists` to distinguish.
-   **Page names are case-sensitive** for the first character (MediaWiki convention). `site.pages['python']` and `site.pages['Python']` may be the same page depending on the wiki's `$wgCapitalLinks` setting.
-   **`page.text()` must be called before `page.edit()`** if you want edit conflict detection. Without it, `basetimestamp` is not set.
-   **Cache invalidation**: After `page.edit()`, the text cache is cleared automatically. But page attributes (like `page.length`) are updated from the edit response, not re-fetched.
-   **`section=None`** (default) replaces the entire page. Passing `section=0` edits the lead section only.

## See also

-   [01-connection-auth.md](01-connection-auth.md) — Setting up the connection
-   [03-querying-pagination.md](03-querying-pagination.md) — Listing and searching pages
-   [06-error-handling.md](06-error-handling.md) — Edit errors and protection errors
-   [../references/reference.md](../references/reference.md) — Full Page API signature
