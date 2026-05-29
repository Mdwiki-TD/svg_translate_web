---
name: mwclient
description: >-
    Use the mwclient Python library to interact with MediaWiki sites via the API.
    Covers reading/writing pages, authentication (OAuth, bot passwords, clientlogin),
    file uploads, category and template operations, pagination, and error handling.
    Trigger this skill when the user mentions mwclient, MediaWiki API, wiki bot,
    wiki automation, editing wiki pages, uploading to a wiki, querying wiki data,
    wiki categories, wiki templates, wiki page deletion, wiki page moves,
    or any task that involves programmatically reading or modifying a MediaWiki site.
    Also trigger when code imports mwclient, uses Site(), site.pages, site.login,
    site.upload, page.edit, page.text, page.save, page.delete, page.move,
    or references MediaWiki's api.php. Covers mwclient 0.11.0.
---

# mwclient

A Python library for interacting with MediaWiki sites through the MediaWiki API. It provides a clean object-oriented interface around `api.php`, handling authentication, pagination, retries, and edit conflict detection automatically.

**Version**: 0.11.0 · **License**: MIT · **Requires**: Python 3.8+, `requests`

## Install

```bash
pip install mwclient
```

## Quick Start

```python
import mwclient

# Read a page
site = mwclient.Site('en.wikipedia.org')
page = site.pages['Python (programming language)']
print(page.text()[:200])

# Edit a page (requires authentication)
site = mwclient.Site('en.wikipedia.org')
site.login('MyBot', 'bot_password')
page = site.pages['Sandbox']
page.save('New content', summary='Test edit via mwclient')
```

## Core Concepts

**Entry point**: `mwclient.Site(host, path='/w/', ...)` — connects to a MediaWiki wiki. All operations flow through the Site object.

**Pages**: `site.pages['Title']` returns a `Page` object (no API call yet). `page.text()` fetches wikitext; `page.edit()` / `page.save()` writes it.

**Lazy iteration**: Methods like `site.allpages()`, `page.backlinks()`, `page.revisions()` return lazy iterators that fetch data in chunks from the API. No request is made until you consume items.

**Namespace dispatch**: `site.categories['Name']` returns a `Category`, `site.images['Name.jpg']` returns an `Image`. Both extend `Page` with extra methods.

## Routing Table

| Goal                                | Read                                                                   |
| ----------------------------------- | ---------------------------------------------------------------------- |
| Connect to a wiki, authenticate     | [skills/01-connection-auth.md](skills/01-connection-auth.md)           |
| Read, edit, move, delete pages      | [skills/02-page-operations.md](skills/02-page-operations.md)           |
| List pages, search, iterate results | [skills/03-querying-pagination.md](skills/03-querying-pagination.md)   |
| Upload/download files and images    | [skills/04-file-operations.md](skills/04-file-operations.md)           |
| Work with categories and templates  | [skills/05-categories-templates.md](skills/05-categories-templates.md) |
| Handle errors, retries, edge cases  | [skills/06-error-handling.md](skills/06-error-handling.md)             |
| Full API signature reference        | [references/reference.md](references/reference.md)                     |
| End-to-end example scripts          | [references/examples.md](references/examples.md)                       |

## Object Model

```
Site                          — Entry point, session, auth, API calls
  .pages / .categories / .images  — PageList (namespace-scoped)
  .allpages() / .search() / ...   — Lazy listing methods

Page                          — Single wiki page
  .text() / .edit() / .save()     — Read/write wikitext
  .backlinks() / .links() / ...   — Lazy property iterators
  ├── Image                       — File pages (ns 6), adds .download(), .imageinfo
  └── Category                    — Category pages (ns 14), iterable of members
```

## Anti-Patterns to Avoid

-   **`mwclient.Site('https://en.wikipedia.org/w/')`** — Don't include scheme or path in host. Use `Site('en.wikipedia.org')`.
-   **`site = mwclient.Site('wiki.org'); site.login(...)`** on private wikis — Use `do_init=False` first.
-   **`page.revisions(max_items=1)`** when you need one revision — Use `api_chunk_size=1` instead (avoids fetching 50).
-   **`image.download()` without a destination** for large files — Use `image.download(file_handle)` to stream.
-   **Using deprecated `limit` parameter** — Use `api_chunk_size` + `max_items` instead.

## See Also

-   [references/reference.md](references/reference.md) — Full API signatures for all classes
-   [references/examples.md](references/examples.md) — Copy-paste example scripts
-   Subskills in [skills/](skills/) for focused topic guides
