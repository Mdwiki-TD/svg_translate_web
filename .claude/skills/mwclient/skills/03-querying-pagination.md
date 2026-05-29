---
name: mwclient-querying-pagination
description: Querying, listing, searching, and paginating MediaWiki pages with mwclient — allpages(), search(), recentchanges(), lazy iteration, max_items, api_chunk_size, generators.
applies_to:
    - "allpages"
    - "search"
    - "recentchanges"
    - "pagination"
    - "iteration"
    - "generator"
    - "max_items"
    - "api_chunk_size"
    - "List"
    - "GeneratorList"
---

# Querying and Pagination

## When to use this file

When the user needs to list pages, search content, iterate over results, or understand how mwclient handles large result sets.

## Mental model

All listing methods return lazy iterators (`List` or `GeneratorList`). No API call is made until you consume items. The iterator fetches results in chunks, following MediaWiki's continuation tokens automatically. Two parameters control behavior: `api_chunk_size` (items per API call) and `max_items` (total items before stopping).

## Quick reference

| Task                              | Code                                             |
| --------------------------------- | ------------------------------------------------ |
| List pages by prefix              | `site.allpages(prefix='Python/', max_items=50)`  |
| Search content                    | `site.search('query', namespace=0)`              |
| Recent changes                    | `site.recentchanges(max_items=20)`               |
| Random pages                      | `site.random(max_items=5)`                       |
| User contributions                | `site.usercontributions('Username')`             |
| Log events                        | `site.logevents(type='delete')`                  |
| All categories                    | `site.allcategories(prefix='A')`                 |
| All users                         | `site.allusers(prefix='Admin')`                  |
| External URL usage                | `site.exturlusage(query='example.com')`          |
| Page backlinks                    | `page.backlinks(max_items=100)`                  |
| Page links                        | `page.links()`                                   |
| Page revisions                    | `page.revisions(max_items=10)`                   |
| Control chunk size                | `site.allpages(api_chunk_size=10, max_items=30)` |
| Raw dicts instead of Page objects | `site.allpages(generator=False)`                 |

## Site-level listing methods

### allpages — List all pages

```python
# All pages (lazy, fetches in chunks of 500)
for page in site.allpages():
    print(page.name)

# With filters
for page in site.allpages(prefix='Python/', namespace=0, max_items=50):
    print(page.name)

# Redirects only
for page in site.allpages(filterredir='redirects', prefix='Redirect/'):
    print(page.name)

# By protection level
for page in site.allpages(prtype='edit', prlevel='sysop'):
    print(page.name)
```

### search — Full-text search

```python
for result in site.search('mwclient mediawiki', namespace=0, max_items=20):
    print(result['title'], result.get('snippet', ''))
```

`generator=True` (default) returns Page objects. `generator=False` returns raw dicts with search metadata.

### recentchanges — Recent changes feed

```python
for change in site.recentchanges(
    prop='title|timestamp|user|comment|sizes',
    show='!bot',         # Exclude bot edits
    namespace=0,
    max_items=20,
):
    print(f"{change['timestamp']} {change['user']}: {change['title']}")
```

### random — Random pages

```python
for page in site.random(namespace=0, max_items=5):
    print(page.name, page.exists)
```

### usercontributions — User's edits

```python
for contrib in site.usercontributions('SomeUser', max_items=20):
    print(contrib['title'], contrib['timestamp'])
```

### logevents — Log entries

```python
for event in site.logevents(type='delete', max_items=10):
    print(event['title'], event.get('action'), event.get('user'))
```

Types: `'delete'`, `'move'`, `'protect'`, `'upload'`, `'block'`, `'patrol'`, etc.

### allcategories — List categories

```python
for cat in site.allcategories(prefix='Prog', max_items=50):
    print(cat['*'])  # Category name
```

### allusers — List users

```python
for user in site.allusers(prefix='Admin', max_items=20):
    print(user['name'])
```

### exturlusage — External links (LinkSearch)

```python
for entry in site.exturlusage(query='example.com', max_items=20):
    print(entry['title'], entry.get('url'))
```

### blocks — Active blocks

```python
for block in site.blocks(max_items=10):
    print(block.get('user'), block.get('reason'))
```

### deletedrevisions — Deleted revisions

```python
for rev in site.deletedrevisions(user='SomeUser', max_items=10):
    print(rev.get('title'), rev.get('revid'))
```

### watchlist — Current user's watchlist

```python
for entry in site.watchlist(max_items=20):
    print(entry['title'])
```

## Page-level listing methods

All return lazy iterators. Common params: `max_items`, `api_chunk_size`, `generator`.

### backlinks — Pages linking to this page

```python
page = site.pages['Python (programming language)']
for link in page.backlinks(max_items=100):
    print(link.name)
```

### categories — Categories on this page

```python
for cat in page.categories():
    print(cat.name)  # Category objects

for cat in page.categories(generator=False):
    print(cat)       # Title strings
```

### embeddedin — Pages transcluding this page

```python
template = site.pages['Template:Infobox']
for page in template.embeddedin(max_items=50):
    print(page.name)
```

### links — Internal links from this page

```python
for link in page.links(max_items=50):
    print(link.name)
```

### templates — Templates used by this page

```python
for tmpl in page.templates():
    print(tmpl.name)
```

### revisions — Revision history

```python
for rev in page.revisions(prop='ids|timestamp|user|comment', max_items=10):
    print(rev['revid'], rev.get('user'), rev['timestamp'])
```

To get content in revisions:

```python
for rev in page.revisions(prop='ids|timestamp|content', api_chunk_size=1):
    print(rev['*'][:200])  # Content in '*' key
    break
```

### Other page iterators

```python
page.extlinks()    # External links
page.images()      # Embedded files
page.iwlinks()     # Interwiki links
page.langlinks()   # Interlanguage links
```

## Pagination control

### api_chunk_size vs max_items

| Parameter        | Scope           | Effect                            |
| ---------------- | --------------- | --------------------------------- |
| `api_chunk_size` | Per API request | Items fetched per round-trip      |
| `max_items`      | Total iteration | Stops after this many total items |

```python
# Fetch 2 items total, 1 per API call (2 round-trips)
for page in site.allpages(max_items=2, api_chunk_size=1):
    print(page.name)

# Fetch all items, 10 per API call
for page in site.allpages(api_chunk_size=10):
    print(page.name)

# Fetch exactly 5 items in one API call
for page in site.allpages(max_items=5):
    print(page.name)
```

### The generator parameter

Most listing methods accept `generator` (default `True`):

```python
# Yields Page objects (uses MediaWiki generator mechanism)
for page in site.allpages(generator=True):
    print(page.name, page.exists)

# Yields raw dicts (uses list mechanism)
for page in site.allpages(generator=False):
    print(page['title'])
```

`generator=True` is preferred when you need page attributes (existence, revision, protection) because the data comes with the listing response — no extra API calls.

### Consuming iterators

```python
# For loop (most common)
for page in site.allpages(max_items=10):
    print(page.name)

# Convert to list (causes all API calls immediately)
pages = list(site.allpages(max_items=10))

# First item only
first = next(iter(site.allpages(max_items=1)), None)

# Count items
count = sum(1 for _ in site.allpages(max_items=100))
```

## The deprecated limit parameter

The `limit` parameter is deprecated. Use `api_chunk_size` + `max_items` instead:

```python
# OLD (deprecated)
for page in site.allpages(limit=10):
    ...

# NEW
for page in site.allpages(max_items=10):
    ...
```

## Edge cases and gotchas

-   **Miser mode**: Some wikis return a `continue` token but zero items. The iterator handles this transparently — it keeps fetching until it finds items or reaches the end.
-   **`max_items=1` on revisions** fetches 50 revisions and yields 1. Use `api_chunk_size=1` instead to fetch only 1 from the API.
-   **Generator vs. list mode**: `generator=True` returns richer objects but uses a different API mechanism. If you only need titles, `generator=False` is more efficient.
-   **Lazy means lazy**: Nothing is fetched until you start consuming. `pages = site.allpages()` makes zero API calls. `list(pages)` makes all of them.
-   **Iterators are single-use**: Once consumed, you can't re-iterate. Create a new listing call if you need to iterate again.

## See also

-   [02-page-operations.md](02-page-operations.md) — Working with individual pages
-   [05-categories-templates.md](05-categories-templates.md) — Category and template queries
-   [../references/reference.md](../references/reference.md) — Full listing method signatures
