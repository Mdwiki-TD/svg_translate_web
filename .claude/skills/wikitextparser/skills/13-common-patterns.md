---
name: wikitextparser-common-patterns
description: >
  18+ ready-to-use recipes for common wikitext processing tasks: extracting
  infoboxes as dicts, exporting tables to CSV, building link graphs, cleaning
  text for NLP, auditing duplicate arguments, extracting citations, renaming
  sections, converting list types, validating template fields, collecting
  categories, pretty-printing, navigating nested templates, detecting empty
  links, extracting images with parameters, organizing references, and
  bulk-replacing templates.
applies_to:
  - "recipe"
  - "infobox to dict"
  - "table to CSV"
  - "link graph"
  - "NLP cleanup"
  - "duplicate arguments"
  - "extract refs"
  - "rename section"
  - "convert list"
  - "validate fields"
  - "collect categories"
  - "pretty-print"
  - "nested templates"
  - "empty links"
  - "extract images"
  - "bulk replace template"
---

# 13 — Common Patterns & Recipes

> Open this file when you need a ready-made snippet for a real-world wikitext
> processing task. Each recipe is self-contained, ~10–25 lines, and can be
> copy-pasted directly.

All recipes assume:

```python
import wikitextparser as wtp
```

---

## Recipe 1: Extract an infobox as a dict

```python
def infobox_to_dict(wikitext: str, name_hint: str = 'infobox') -> dict | None:
    """Return the first matching infobox's keyword args as {name: value}."""
    parsed = wtp.parse(wikitext)
    for t in parsed.templates:
        if name_hint.lower() in t.normal_name().lower():
            return {
                a.name.strip(): a.value.strip()
                for a in t.arguments
                if not a.positional
            }
    return None
```

---

## Recipe 2: Modify a template argument across the article

```python
def set_template_arg(wikitext: str, tpl_name: str, arg_name: str, new_value: str) -> str:
    parsed = wtp.parse(wikitext)
    for t in parsed.templates:
        if t.normal_name().lower() == tpl_name.lower():
            if t.has_arg(arg_name):
                t.set_arg(arg_name, new_value)
    return str(parsed)
```

---

## Recipe 3: Delete a template entirely

```python
def delete_template(wikitext: str, tpl_name: str) -> str:
    parsed = wtp.parse(wikitext)
    for t in reversed(parsed.templates):
        if t.normal_name().lower() == tpl_name.lower():
            del t[:]
    return str(parsed)
```

Always iterate in reverse when deleting to avoid invalidating spans.

---

## Recipe 4: Export every table to CSV

```python
import csv
import io

def tables_to_csv(wikitext: str) -> list[str]:
    """Return one CSV string per table in the article."""
    parsed = wtp.parse(wikitext)
    csvs = []
    for t in parsed.tables:
        rows = t.data()
        if not rows:
            continue
        buf = io.StringIO()
        csv.writer(buf).writerows(rows)
        csvs.append(buf.getvalue())
    return csvs
```

---

## Recipe 5: Build a wikilink graph (outbound links)

```python
def outbound_links(wikitext: str) -> list[str]:
    """Return unique article titles linked from this page."""
    parsed = wtp.parse(wikitext)
    seen = set()
    out = []
    for wl in parsed.wikilinks:
        title = wl.title.strip().split('#')[0]
        if title and title not in seen and ':' not in title:
            seen.add(title)
            out.append(title)
    return out
```

Extend to a full graph by iterating over multiple pages.

---

## Recipe 6: NLP-friendly text cleanup

```python
def clean_for_nlp(wikitext: str) -> str:
    """Strip all markup, collapse whitespace, return lowercase."""
    text = wtp.parse(wikitext).plain_text(
        replace_templates=True,
        replace_parser_functions=True,
        replace_parameters=True,
        replace_tags=True,
        replace_external_links=True,
        replace_wikilinks=True,
        unescape_html_entities=True,
        replace_bolds_and_italics=True,
    )
    import re
    text = re.sub(r'\s+', ' ', text).strip()
    return text
```

---

## Recipe 7: Audit duplicate arguments

```python
def find_dup_args(wikitext: str) -> list[dict]:
    """Find templates with duplicate argument names."""
    parsed = wtp.parse(wikitext)
    issues = []
    for t in parsed.templates:
        names = [a.name.strip() for a in t.arguments]
        seen = set()
        dups = set()
        for n in names:
            if n in seen:
                dups.add(n)
            seen.add(n)
        if dups:
            issues.append({
                'template': t.normal_name(),
                'duplicates': sorted(dups),
            })
    return issues
```

---

## Recipe 8: Extract all `<ref>` citations

```python
def extract_refs(wikitext: str) -> list[dict]:
    parsed = wtp.parse(wikitext)
    refs = []
    for tag in parsed.get_tags('ref'):
        refs.append({
            'name': tag.get_attr('name'),
            'group': tag.get_attr('group'),
            'content': (tag.contents or '').strip() or None,
            'is_reuse': tag.contents is None,
        })
    return refs
```

---

## Recipe 9: Rename sections / promote heading levels

```python
def rename_section(wikitext: str, old_title: str, new_title: str) -> str:
    parsed = wtp.parse(wikitext)
    for s in parsed.sections:
        if s.title and s.title.strip() == old_title:
            s.title = new_title
    return str(parsed)

def promote_all_headings(wikitext: str) -> str:
    """Decrease every heading level by 1 (=== → ==)."""
    parsed = wtp.parse(wikitext)
    for s in parsed.sections:
        if s.level >= 2:
            s.level -= 1
    return str(parsed)
```

---

## Recipe 10: Convert list types

```python
def bullets_to_numbers(wikitext: str) -> str:
    parsed = wtp.parse(wikitext)
    for wl in parsed.get_lists(r'\*'):
        wl.convert('#')
    return str(parsed)
```

---

## Recipe 11: Validate required fields in templates

```python
REQUIRED_FIELDS = {
    'infobox person': ['name', 'birth_date', 'nationality'],
    'cite web': ['url', 'title'],
}

def validate_templates(wikitext: str) -> list[dict]:
    parsed = wtp.parse(wikitext)
    issues = []
    for t in parsed.templates:
        name = t.normal_name().lower()
        required = REQUIRED_FIELDS.get(name)
        if not required:
            continue
        missing = [f for f in required if not t.has_arg(f)]
        if missing:
            issues.append({'template': name, 'missing': missing})
    return issues
```

---

## Recipe 12: Collect all categories

```python
CATEGORY_NS = {
    'category', 'cat', 'categoría', 'catégorie', 'kategorie', 'kategori',
    'категория', 'تصنيف', '分类', '分類', 'κατηγορία',
}

def get_categories(wikitext: str) -> list[str]:
    parsed = wtp.parse(wikitext)
    cats = []
    for wl in parsed.wikilinks:
        head, sep, tail = wl.title.partition(':')
        if sep and head.strip().lower() in CATEGORY_NS:
            cats.append(tail.strip())
    return cats
```

---

## Recipe 13: Pretty-print every template in an article

```python
def pretty_print_all(wikitext: str) -> str:
    """Replace every template with its pretty-printed form."""
    parsed = wtp.parse(wikitext)
    for t in parsed.templates:
        if t.nesting_level == 0:
            t[:] = t.pformat()
    return str(parsed)
```

Only top-level templates are replaced to avoid double-formatting nested ones.

---

## Recipe 14: Navigate nested templates

```python
def nested_template_tree(wikitext: str) -> list[dict]:
    """Return a list of {name, level, children} for each template."""
    parsed = wtp.parse(wikitext)
    return [
        {
            'name': t.normal_name(),
            'level': t.nesting_level,
            'child_count': len(t.templates),
        }
        for t in parsed.templates
    ]
```

---

## Recipe 15: Detect empty / self-referencing wikilinks

```python
def broken_links(wikitext: str, page_title: str = '') -> list[str]:
    parsed = wtp.parse(wikitext)
    bad = []
    for wl in parsed.wikilinks:
        title = wl.title.strip()
        if not title:
            bad.append(f'empty link: {str(wl)!r}')
        elif title.lower() == page_title.lower():
            bad.append(f'self-link: {str(wl)!r}')
    return bad
```

---

## Recipe 16: Extract all images with parameters

```python
FILE_NS = {'file', 'image', 'archivo', 'datei', 'fichier', 'файл', 'ملف'}

def extract_images(wikitext: str) -> list[dict]:
    parsed = wtp.parse(wikitext)
    images = []
    for wl in parsed.wikilinks:
        head, sep, tail = wl.title.partition(':')
        if sep and head.strip().lower() in FILE_NS:
            params = (wl.text or '').split('|') if wl.text else []
            images.append({
                'filename': tail.strip(),
                'params': [p.strip() for p in params],
                'raw': str(wl),
            })
    return images
```

---

## Recipe 17: Organize references into a structured list

```python
def organize_refs(wikitext: str) -> dict[str, list[str]]:
    """Group ref contents by their group attribute."""
    parsed = wtp.parse(wikitext)
    groups: dict[str, list[str]] = {}
    for tag in parsed.get_tags('ref'):
        if tag.contents is None:
            continue
        group = tag.get_attr('group') or 'default'
        groups.setdefault(group, []).append(tag.contents.strip())
    return groups
```

---

## Recipe 18: Bulk-replace one template with another

```python
def replace_template(wikitext: str, old_name: str, new_name: str,
                     arg_renames: dict[str, str] = None) -> str:
    """Replace template name and optionally rename arguments."""
    parsed = wtp.parse(wikitext)
    arg_renames = arg_renames or {}
    for t in parsed.templates:
        if t.normal_name().lower() != old_name.lower():
            continue
        # Rename arguments first (before changing name — order matters)
        for old_arg, new_arg in arg_renames.items():
            a = t.get_arg(old_arg)
            if a is not None:
                value = a.value
                t.del_arg(old_arg)
                t.set_arg(new_arg, value)
        # Replace template name in the buffer
        # t.name includes leading/trailing whitespace — preserve it
        ws_before = len(t.name) - len(t.name.lstrip())
        ws_after = len(t.name) - len(t.name.rstrip())
        prefix = t.name[:ws_before]
        suffix = t.name[len(t.name) - ws_after:] if ws_after else ''
        t.name = prefix + new_name + suffix
    return str(parsed)
```

Example:

```python
result = replace_template(
    wikitext,
    old_name='Cite web',
    new_name='Cite news',
    arg_renames={'url': 'newspaper_url', 'website': 'newspaper'},
)
```

---

## Bonus: Combine multiple recipes in a pipeline

```python
def full_audit(wikitext: str) -> dict:
    parsed = wtp.parse(wikitext)
    return {
        'categories': get_categories(wikitext),
        'images': extract_images(wikitext),
        'external_links': len(parsed.external_links),
        'templates': [t.normal_name() for t in parsed.templates],
        'duplicate_args': find_dup_args(wikitext),
        'broken_links': broken_links(wikitext),
        'ref_count': len(parsed.get_tags('ref')),
        'tables': len(parsed.tables),
        'sections': [(s.level, s.title) for s in parsed.sections if s.title],
    }
```

---

## See also

- Each recipe's sub-skill for deeper API details (e.g. `02-templates.md`
  for template manipulation, `06-tables.md` for table data)
- `references/examples.md` — longer multi-step pipelines
- `references/reference.md` — when you need precise method signatures
