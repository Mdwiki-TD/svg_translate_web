---
name: mwclient-categories-templates
description: Working with MediaWiki categories and templates using mwclient — listing members, finding pages by category, template transclusion, expanding templates, and parsing wikitext.
applies_to:
    - "Category"
    - "members"
    - "categories"
    - "templates"
    - "embeddedin"
    - "expandtemplates"
    - "parse"
    - "transclusion"
---

# Categories and Templates

## When to use this file

When the user needs to work with categories (listing members, finding pages by category) or templates (finding usage, expanding, parsing).

## Mental model

`Category` is a dual-nature class: it's both a `Page` (has content, can be edited) and a `GeneratorList` (iterable over its members). Templates are just pages in namespace 10 — `site.pages['Template:Name']` gives you a regular Page. Template usage is found via `embeddedin()` (pages that transclude a template) and `templates()` (templates used by a page). Expansion and parsing are site-level methods.

## Quick reference

| Task                 | Code                                       |
| -------------------- | ------------------------------------------ |
| Get category         | `cat = site.categories['Category Name']`   |
| Iterate members      | `for m in cat: print(m.name)`              |
| Members with filter  | `cat.members(namespace=0, max_items=50)`   |
| Categories on page   | `page.categories()`                        |
| Templates on page    | `page.templates()`                         |
| Pages using template | `template.embeddedin()`                    |
| Expand templates     | `site.expandtemplates('{{TemplateName}}')` |
| Parse wikitext       | `site.parse('{{TemplateName}}')`           |
| All categories       | `site.allcategories(prefix='A')`           |

## Categories

### Get a Category object

```python
cat = site.categories['Python']  # No API call yet
print(cat.exists)                 # True if category page exists
print(cat.name)                   # "Category:Python"
```

### Iterate category members

```python
# Yields Page/Image/Category objects
for member in cat:
    print(member.name)

# With limits
for member in cat.members(max_items=50):
    print(member.name)

# Filter by namespace
for page in cat.members(namespace=0, max_items=50):
    print(page.name)  # Only main-namespace pages

# Raw dicts instead of page objects
for entry in cat.members(generator=False):
    print(entry['title'])
```

### Sort and filter members

```python
# Sort by sortkey (default)
for member in cat.members(sort='sortkey', dir='asc'):
    print(member.name)

# Sort by timestamp (recently added first)
for member in cat.members(sort='timestamp', dir='desc'):
    print(member.name)

# Alphabetical range
for member in cat.members(start='A', end='B'):
    print(member.name)
```

### Get categories on a page

```python
page = site.pages['Python (programming language)']
for cat in page.categories():
    print(cat.name)  # Category objects

for cat in page.categories(generator=False):
    print(cat)       # Title strings like "Category:Programming languages"
```

### List all categories on the wiki

```python
for cat in site.categories:  # PageList for namespace 14
    print(cat.name)

# With prefix filter
for cat_data in site.allcategories(prefix='Prog', max_items=50):
    print(cat_data['*'])  # Category name string
```

### Check if a page is in a category

```python
page = site.pages['Some Page']
cats = [cat.name for cat in page.categories()]
if 'Category:Living people' in cats:
    print("Page is in 'Living people' category")
```

## Templates

### Get a template page

```python
template = site.pages['Template:Infobox']
print(template.exists)
print(template.text()[:200])  # Template wikitext
```

### List templates used by a page

```python
page = site.pages['Python (programming language)']
for tmpl in page.templates():
    print(tmpl.name)  # Page objects

for tmpl in page.templates(generator=False):
    print(tmpl)       # Title strings
```

### Find pages that transclude a template

```python
template = site.pages['Template:Infobox']
for page in template.embeddedin(max_items=50):
    print(page.name)
```

This answers "which pages use this template?"

### Expand templates

```python
# Simple expansion
expanded = site.expandtemplates('{{CURRENTTIMESTAMP}}')
print(expanded)

# With arguments
expanded = site.expandtemplates('{{TemplateName|arg1|arg2}}')
print(expanded)

# With parse tree (MW < 1.32)
expanded, tree = site.expandtemplates('{{TemplateName}}', generatexml=True)
```

### Parse wikitext to HTML

```python
result = site.parse('Some '''wikitext''' with {{template}}')
html = result.get('text', {}).get('*', '')
print(html)
```

The `parse()` method returns a rich dict with sections, links, categories, and more.

### Edit a template

```python
template = site.pages['Template:MyTemplate']
template.save('{{Notice|Updated content}}', summary='Updating template')
# All transcluding pages will show the updated template on next render
```

### Purge template cache

After editing a template, pages that transclude it may show stale cached content:

```python
template = site.pages['Template:MyTemplate']
template.purge()  # Purge the template page itself

# Or purge specific pages that use it
for page in template.embeddedin(max_items=10):
    page.purge()
```

## Edge cases and gotchas

-   **Category iteration yields objects**: `for member in cat` yields `Page`, `Image`, or `Category` objects based on namespace. Each requires an API call for attributes — use `generator=False` if you only need titles.
-   **Template namespace prefix**: Templates are in namespace 10. Use `site.pages['Template:Name']`, not `site.pages['Name']` (unless the wiki has custom namespace configuration).
-   **`expandtemplates` vs `text(expandtemplates=True)`**: `site.expandtemplates()` operates on arbitrary wikitext. `page.text(expandtemplates=True)` expands templates within a page's content. Different use cases.
-   **Category sort keys**: `cat.members(sort='sortkey')` sorts by the category sort key (which defaults to the page title). Custom sort keys are set via `[[Category:Name|Sort key]]`.
-   **Module transclusions**: `page.templates()` includes `Module:` transclusions (Scribunto), not just `Template:` namespace.

## See also

-   [02-page-operations.md](02-page-operations.md) — Editing category and template pages
-   [03-querying-pagination.md](03-querying-pagination.md) — Pagination for category/template listings
-   [../references/reference.md](../references/reference.md) — Category and template method signatures
