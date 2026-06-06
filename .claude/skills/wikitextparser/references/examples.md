---
name: wikitextparser-examples
description: >
  19 end-to-end scripts demonstrating real-world wikitext processing
  pipelines: parsing dumps, extracting infoboxes, building link graphs,
  exporting tables to CSV, validating templates, auditing duplicates,
  cleaning markup for NLP, full article audits, template migration with
  argument transforms, media/gallery extraction, and batch processing
  multiple articles. Load this file when a sub-skill or recipe points
  you here for a full working script.
applies_to:
  - "end-to-end"
  - "full script"
  - "pipeline"
  - "real-world"
  - "workflow"
---

# wikitextparser — Practical Examples

> Load this file when the user needs end-to-end scripts, real-world patterns, or multi-step workflows beyond quick snippets.

## Table of Contents

1. [Parse a Wikipedia article dump](#1-parse-a-wikipedia-article-dump)
2. [Extract all Infobox data as a dict](#2-extract-all-infobox-data-as-a-dict)
3. [Find and replace template arguments at scale](#3-find-and-replace-template-arguments-at-scale)
4. [Export all wiki tables to CSV](#4-export-all-wiki-tables-to-csv)
5. [Build a wikilink graph](#5-build-a-wikilink-graph)
6. [Strip markup for NLP / full-text search](#6-strip-markup-for-nlp--full-text-search)
7. [Audit duplicate template arguments](#7-audit-duplicate-template-arguments)
8. [Extract citations (ref tags)](#8-extract-citations-ref-tags)
9. [Rewrite section headings](#9-rewrite-section-headings)
10. [Convert list types across an article](#10-convert-list-types-across-an-article)
11. [Validate template required fields](#11-validate-template-required-fields)
12. [Collect all categories from an article](#12-collect-all-categories-from-an-article)
13. [Pretty-print all templates in a page](#13-pretty-print-all-templates-in-a-page)
14. [Nested template traversal](#14-nested-template-traversal)
15. [Find broken / empty wikilinks](#15-find-broken--empty-wikilinks)
16. [Full article audit pipeline](#16-full-article-audit-pipeline)
17. [Template migration pipeline](#17-template-migration-pipeline)
18. [Media extraction pipeline](#18-media-extraction-pipeline)
19. [Batch processing multiple articles](#19-batch-processing-multiple-articles)

---

## 1. Parse a Wikipedia article dump

```python
import wikitextparser as wtp

# From a string (e.g. loaded from a .xml dump or API response)
with open('article.txt', encoding='utf-8') as f:
    raw = f.read()

parsed = wtp.parse(raw)

print(f"Templates  : {len(parsed.templates)}")
print(f"Wikilinks  : {len(parsed.wikilinks)}")
print(f"Tables     : {len(parsed.tables)}")
print(f"Sections   : {len(parsed.sections)}")
print(f"Ext. links : {len(parsed.external_links)}")
```

---

## 2. Extract all Infobox data as a dict

```python
import wikitextparser as wtp

def extract_infobox(wikitext: str, template_name: str = None) -> dict:
    """
    Return {arg_name: arg_value} for the first matching infobox template.
    If template_name is None, returns the first template found.
    """
    parsed = wtp.parse(wikitext)
    for t in parsed.templates:
        name = t.normal_name().lower()
        if template_name is None or template_name.lower() in name:
            return {
                arg.name.strip(): arg.value.strip()
                for arg in t.arguments
                if not arg.positional
            }
    return {}

# Usage
data = extract_infobox(raw, template_name='infobox person')
print(data.get('birth_date'))
print(data.get('nationality'))
```

---

## 3. Find and replace template arguments at scale

```python
import wikitextparser as wtp

def rename_template_arg(wikitext: str, template: str, old_arg: str, new_arg: str) -> str:
    """Rename an argument across all instances of a template."""
    parsed = wtp.parse(wikitext)
    for t in parsed.templates:
        if t.normal_name().lower() == template.lower():
            arg = t.get_arg(old_arg)
            if arg:
                value = arg.value
                t.del_arg(old_arg)
                t.set_arg(new_arg, value)
    return str(parsed)

# Usage
updated = rename_template_arg(raw, 'Infobox person', 'birth_place', 'birthplace')
```

---

## 4. Export all wiki tables to CSV

```python
import csv
import io
import wikitextparser as wtp

def tables_to_csv(wikitext: str) -> list[str]:
    """Return list of CSV strings, one per table."""
    parsed = wtp.parse(wikitext)
    results = []
    for table in parsed.tables:
        rows = table.data()
        if not rows:
            continue
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerows(rows)
        results.append(buf.getvalue())
    return results

# Usage
csvs = tables_to_csv(raw)
for i, csv_str in enumerate(csvs):
    with open(f'table_{i}.csv', 'w') as f:
        f.write(csv_str)
```

---

## 5. Build a wikilink graph

```python
import wikitextparser as wtp
from collections import defaultdict

def build_link_graph(pages: dict[str, str]) -> dict[str, list[str]]:
    """
    pages: {page_title: wikitext}
    Returns: {page_title: [linked_titles]}
    """
    graph = defaultdict(list)
    for title, wikitext in pages.items():
        parsed = wtp.parse(wikitext)
        for wl in parsed.wikilinks:
            # Normalize: strip fragment, strip leading/trailing spaces
            target = wl.title.strip().split('#')[0]
            if target:
                graph[title].append(target)
    return dict(graph)

# Usage
pages = {
    'Python': raw_python,
    'Guido van Rossum': raw_guido,
}
graph = build_link_graph(pages)
```

---

## 6. Strip markup for NLP / full-text search

```python
import wikitextparser as wtp

def to_plain_text(wikitext: str, keep_links: bool = False) -> str:
    """
    Convert wikitext to clean plain text.
    keep_links=True: preserve [[link]] display text but remove markup.
    """
    parsed = wtp.parse(wikitext)
    return parsed.plain_text(
        replace_templates=True,
        replace_parser_functions=True,
        replace_parameters=True,
        replace_tags=True,
        replace_external_links=True,
        replace_wikilinks=True,
        unescape_html_entities=True,
        replace_bolds_and_italics=True,
    ).strip()

# Usage
text = to_plain_text(raw)
words = text.split()
```

---

## 7. Audit duplicate template arguments

```python
import wikitextparser as wtp
from collections import Counter

def find_duplicate_args(wikitext: str) -> list[dict]:
    """Return list of {template, arg, count} for any duplicate arguments."""
    parsed = wtp.parse(wikitext)
    duplicates = []
    for t in parsed.templates:
        names = [arg.name.strip() for arg in t.arguments if not arg.positional]
        counts = Counter(names)
        for name, count in counts.items():
            if count > 1:
                duplicates.append({
                    'template': t.normal_name(),
                    'arg': name,
                    'count': count,
                })
    return duplicates

# Usage
dupes = find_duplicate_args(raw)
for d in dupes:
    print(f"  {d['template']}: '{d['arg']}' appears {d['count']}×")
```

---

## 8. Extract citations (ref tags)

```python
import wikitextparser as wtp

def extract_refs(wikitext: str) -> list[dict]:
    """Return list of {name, content} for all <ref> tags."""
    parsed = wtp.parse(wikitext)
    refs = []
    for tag in parsed.get_tags('ref'):
        refs.append({
            'name': tag.get_attr('name'),
            'content': (tag.contents or '').strip(),
        })
    return refs

# Usage
citations = extract_refs(raw)
named = [r for r in citations if r['name']]
inline = [r for r in citations if r['content']]
```

---

## 9. Rewrite section headings

```python
import wikitextparser as wtp

def rename_section(wikitext: str, old_title: str, new_title: str) -> str:
    """Rename a section heading (exact match, case-sensitive)."""
    parsed = wtp.parse(wikitext)
    for section in parsed.sections:
        if section.title and section.title.strip() == old_title:
            section.title = new_title
    return str(parsed)

def promote_sections(wikitext: str) -> str:
    """Promote all section levels by 1 (h3 → h2, etc.)."""
    parsed = wtp.parse(wikitext)
    for section in parsed.sections:
        if section.level > 1:
            section.level -= 1
    return str(parsed)
```

---

## 10. Convert list types across an article

```python
import wikitextparser as wtp

def convert_all_lists(wikitext: str, from_type: str, to_type: str) -> str:
    """
    Convert list items from one type to another across the whole article.
    from_type / to_type: '*' (unordered), '#' (ordered), ':' (definition)
    """
    import re
    parsed = wtp.parse(wikitext)
    pattern = re.escape(from_type)
    for wl in parsed.get_lists(pattern=pattern):
        wl.convert(to_type)
    return str(parsed)

# Usage: convert all unordered lists to ordered
result = convert_all_lists(raw, '*', '#')
```

---

## 11. Validate template required fields

```python
import wikitextparser as wtp

REQUIRED_FIELDS = {
    'infobox person': ['name', 'birth_date', 'nationality'],
    'infobox film':   ['name', 'director', 'released'],
}

def validate_templates(wikitext: str) -> list[dict]:
    """Return list of {template, missing_fields} for validation failures."""
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

## 12. Collect all categories from an article

```python
import wikitextparser as wtp

CATEGORY_NS = {"category", "catégorie", "kategorie", "categoría", "κατηγορία"}

def get_categories(wikitext: str) -> list[str]:
    """Return list of category names (without 'Category:' prefix)."""
    parsed = wtp.parse(wikitext)
    categories = []
    for wl in parsed.wikilinks:
        ns, _, rest = wl.title.partition(':')
        if ns.strip().lower() in CATEGORY_NS:
            categories.append(rest.strip())
    return categories

# Usage
cats = get_categories(raw)
print(cats)  # ['Living people', 'American scientists', ...]
```

---

## 13. Pretty-print all templates in a page

```python
import wikitextparser as wtp

def pretty_print_templates(wikitext: str) -> str:
    """Return a report of all templates, pretty-printed."""
    parsed = wtp.parse(wikitext)
    lines = []
    for i, t in enumerate(parsed.templates, 1):
        lines.append(f"=== Template {i}: {t.normal_name()} ===")
        lines.append(t.pformat())
        lines.append('')
    return '\n'.join(lines)
```

---

## 14. Nested template traversal

```python
import wikitextparser as wtp

def find_templates_inside(wikitext: str, outer_name: str) -> list:
    """Find all templates nested directly inside a named template."""
    parsed = wtp.parse(wikitext)
    results = []
    for t in parsed.templates:
        if t.normal_name().lower() == outer_name.lower():
            # templates property on a Template returns its nested templates
            results.extend(t.templates)
    return results

# Using ancestors to find context
def which_template_contains(wikitext: str, target_name: str) -> list[str]:
    """Return names of all templates that directly contain target_name."""
    parsed = wtp.parse(wikitext)
    containers = []
    for t in parsed.templates:
        if t.normal_name().lower() == target_name.lower():
            parent = t.parent(type_='Template')
            if parent:
                containers.append(parent.normal_name())
    return containers
```

---

## 15. Find broken / empty wikilinks

```python
import wikitextparser as wtp

def find_empty_links(wikitext: str) -> list[str]:
    """Return all wikilinks with empty or whitespace-only titles."""
    parsed = wtp.parse(wikitext)
    return [
        str(wl) for wl in parsed.wikilinks
        if not wl.title.strip()
    ]

def find_self_links(wikitext: str, page_title: str) -> list[str]:
    """Return wikilinks that point back to the current page (self-links)."""
    parsed = wtp.parse(wikitext)
    return [
        str(wl) for wl in parsed.wikilinks
        if wl.title.strip().lower() == page_title.lower()
    ]
```


---

## 16. Full article audit pipeline

Combines multiple extraction techniques into a single pass that produces a
comprehensive report about an article's structure, quality, and content.

```python
import wikitextparser as wtp
from collections import Counter

CATEGORY_NS = {'category', 'catégorie', 'kategorie', 'categoría', 'تصنيف', '分类'}
FILE_NS = {'file', 'image', 'archivo', 'datei', 'fichier', 'ملف'}


def audit_article(wikitext: str, page_title: str = '') -> dict:
    """Run a comprehensive audit on a single article's wikitext."""
    parsed = wtp.parse(wikitext)

    # --- Templates ---
    template_names = [t.normal_name() for t in parsed.templates]
    template_counts = Counter(template_names)

    # Duplicate argument check
    dup_args = []
    for t in parsed.templates:
        names = [a.name.strip() for a in t.arguments if not a.positional]
        seen = set()
        for n in names:
            if n in seen:
                dup_args.append({'template': t.normal_name(), 'arg': n})
            seen.add(n)

    # --- Wikilinks ---
    all_links = []
    broken_links = []
    self_links = []
    for wl in parsed.wikilinks:
        title = wl.title.strip()
        if not title:
            broken_links.append(str(wl))
        elif title.lower() == page_title.lower():
            self_links.append(str(wl))
        else:
            all_links.append(title)

    # --- Categories ---
    categories = []
    for wl in parsed.wikilinks:
        head, sep, tail = wl.title.partition(':')
        if sep and head.strip().lower() in CATEGORY_NS:
            categories.append(tail.strip())

    # --- Files / Images ---
    files = []
    for wl in parsed.wikilinks:
        head, sep, tail = wl.title.partition(':')
        if sep and head.strip().lower() in FILE_NS:
            files.append(tail.strip())

    # --- Gallery images ---
    gallery_images = []
    for tag in parsed.get_tags('gallery'):
        if tag.contents:
            for line in tag.contents.splitlines():
                line = line.strip()
                if line and not line.startswith('<!--'):
                    gallery_images.append(line.partition('|')[0].strip())

    # --- References ---
    refs = parsed.get_tags('ref')
    named_refs = [r for r in refs if r.get_attr('name')]
    reused_refs = [r for r in refs if r.contents is None]

    # --- Sections ---
    sections = [(s.level, s.title.strip()) for s in parsed.sections if s.title]

    # --- Tables ---
    tables_info = []
    for t in parsed.tables:
        rows = t.data()
        tables_info.append({
            'caption': t.caption,
            'rows': len(rows),
            'cols': len(rows[0]) if rows else 0,
        })

    # --- External links ---
    ext_domains = Counter()
    for el in parsed.external_links:
        try:
            from urllib.parse import urlparse
            ext_domains[urlparse(el.url).netloc.lower()] += 1
        except (ValueError, AttributeError):
            pass

    # --- Plain text stats ---
    plain = parsed.plain_text()
    word_count = len(plain.split())

    return {
        'word_count': word_count,
        'template_count': len(parsed.templates),
        'top_templates': template_counts.most_common(10),
        'duplicate_args': dup_args,
        'wikilink_count': len(all_links),
        'broken_links': broken_links,
        'self_links': self_links,
        'categories': categories,
        'files': files,
        'gallery_images': gallery_images,
        'ref_total': len(refs),
        'ref_named': len(named_refs),
        'ref_reused': len(reused_refs),
        'sections': sections,
        'tables': tables_info,
        'ext_link_domains': ext_domains.most_common(10),
    }


# Usage
report = audit_article(raw, page_title='Albert Einstein')
print(f"Words: {report['word_count']}")
print(f"Templates: {report['template_count']}")
print(f"Categories: {len(report['categories'])}")
print(f"References: {report['ref_total']} ({report['ref_named']} named)")
print(f"Issues: {len(report['broken_links'])} broken links, "
      f"{len(report['self_links'])} self-links, "
      f"{len(report['duplicate_args'])} duplicate args")
```

---

## 17. Template migration pipeline

A complete workflow for migrating from one template to another: rename the
template, rename/transform arguments, add defaults for new required fields,
and validate the result.

```python
import wikitextparser as wtp


def migrate_template(
    wikitext: str,
    old_name: str,
    new_name: str,
    arg_renames: dict[str, str] = None,
    arg_transforms: dict[str, callable] = None,
    new_defaults: dict[str, str] = None,
    remove_args: list[str] = None,
) -> tuple[str, list[str]]:
    """
    Migrate all instances of old_name to new_name with full argument handling.

    Returns: (updated_wikitext, list_of_warnings)
    """
    arg_renames = arg_renames or {}
    arg_transforms = arg_transforms or {}
    new_defaults = new_defaults or {}
    remove_args = remove_args or []
    warnings = []

    parsed = wtp.parse(wikitext)

    for t in parsed.templates:
        if t.normal_name().lower() != old_name.lower():
            continue

        # Step 1: Remove deprecated arguments
        for rm in remove_args:
            if t.has_arg(rm):
                t.del_arg(rm)

        # Step 2: Rename arguments (collect values first to avoid conflicts)
        for old_arg, new_arg in arg_renames.items():
            a = t.get_arg(old_arg)
            if a is not None:
                value = a.value
                t.del_arg(old_arg)
                t.set_arg(new_arg, value, preserve_spacing=True)

        # Step 3: Transform argument values
        for arg_name, transform_fn in arg_transforms.items():
            a = t.get_arg(arg_name)
            if a is not None:
                try:
                    a.value = transform_fn(a.value)
                except Exception as e:
                    warnings.append(
                        f"Transform failed for {arg_name}: {e}"
                    )

        # Step 4: Add defaults for new required fields
        for field, default in new_defaults.items():
            if not t.has_arg(field):
                t.set_arg(field, default, preserve_spacing=True)

        # Step 5: Rename the template itself
        # Preserve any leading/trailing whitespace in the name
        raw_name = t.name
        ws_before = len(raw_name) - len(raw_name.lstrip())
        ws_after = len(raw_name) - len(raw_name.rstrip())
        if ws_after:
            t.name = raw_name[:ws_before] + new_name + raw_name[len(raw_name) - ws_after:]
        else:
            t.name = raw_name[:ws_before] + new_name

    return str(parsed), warnings


# Usage: migrate {{Cite web}} to {{Cite news}} with argument changes
updated, warns = migrate_template(
    wikitext=raw,
    old_name='Cite web',
    new_name='Cite news',
    arg_renames={
        'website': 'newspaper',
        'url': 'article-url',
    },
    arg_transforms={
        'date': lambda v: v.strip().replace('/', '-'),  # normalize date format
        'access-date': lambda v: v.strip().replace('/', '-'),
    },
    new_defaults={
        'language': 'en',
    },
    remove_args=['archive-url', 'archive-date', 'url-status'],
)

for w in warns:
    print(f"WARNING: {w}")
```

---

## 18. Media extraction pipeline

Extract all media references from an article (file links, gallery entries,
infobox image fields), parse image parameters, and produce a structured
manifest.

```python
import wikitextparser as wtp

FILE_NS = {'file', 'image', 'archivo', 'datei', 'fichier', 'файл', 'ملف'}
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.tif', '.tiff'}
KNOWN_FORMATS = {'thumb', 'thumbnail', 'frame', 'framed', 'frameless'}
KNOWN_ALIGNS = {'left', 'right', 'center', 'centre', 'none'}


def parse_image_options(text: str | None) -> dict:
    """Parse the |options in [[File:name|options]] into structured fields."""
    if not text:
        return {'format': None, 'align': None, 'size': None, 'caption': None}
    parts = [p.strip() for p in text.split('|')]
    result = {'format': None, 'align': None, 'size': None, 'caption': None, 'extras': []}
    for p in parts:
        low = p.lower()
        if low in KNOWN_FORMATS:
            result['format'] = low
        elif low in KNOWN_ALIGNS:
            result['align'] = low
        elif low.endswith('px') and low[:-2].replace('x', '').isdigit():
            result['size'] = low
        elif low.startswith(('alt=', 'link=', 'lang=', 'page=', 'class=', 'border', 'upright')):
            result['extras'].append(p)
        elif result['caption'] is None:
            result['caption'] = p
        else:
            result['extras'].append(p)
    return result


def extract_all_media(wikitext: str) -> dict:
    """
    Extract every media reference in the article from all sources.
    Returns a dict with 'file_links', 'gallery_items', 'infobox_images'.
    """
    parsed = wtp.parse(wikitext)

    # 1. [[File:...]] wikilinks
    file_links = []
    for wl in parsed.wikilinks:
        head, sep, tail = wl.title.partition(':')
        if sep and head.strip().lower() in FILE_NS:
            options = parse_image_options(wl.text)
            file_links.append({
                'filename': tail.strip(),
                'options': options,
                'raw': str(wl),
            })

    # 2. <gallery> tags
    gallery_items = []
    for tag in parsed.get_tags('gallery'):
        gallery_attrs = {
            'mode': tag.get_attr('mode'),
            'widths': tag.get_attr('widths'),
            'heights': tag.get_attr('heights'),
            'perrow': tag.get_attr('perrow'),
        }
        items = []
        for line in (tag.contents or '').splitlines():
            line = line.strip()
            if not line or line.startswith('<!--'):
                continue
            filename, sep, caption = line.partition('|')
            items.append({
                'filename': filename.strip(),
                'caption': caption.strip() if sep else None,
            })
        gallery_items.append({
            'attrs': gallery_attrs,
            'items': items,
        })

    # 3. Infobox image fields (common parameter names)
    IMAGE_FIELDS = {'image', 'image_file', 'img', 'photo', 'picture',
                    'logo', 'cover', 'map_image', 'flag_image', 'coat_image'}
    infobox_images = []
    for t in parsed.templates:
        if 'infobox' not in t.normal_name().lower():
            continue
        for arg in t.arguments:
            name_lower = arg.name.strip().lower()
            if name_lower in IMAGE_FIELDS or name_lower.startswith('image'):
                value = arg.value.strip()
                if value:
                    # Check if it looks like a filename
                    if any(value.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
                        infobox_images.append({
                            'template': t.normal_name(),
                            'field': arg.name.strip(),
                            'filename': value,
                        })

    # Summary
    all_filenames = set()
    for f in file_links:
        all_filenames.add(f['filename'])
    for g in gallery_items:
        for item in g['items']:
            all_filenames.add(item['filename'])
    for img in infobox_images:
        all_filenames.add(img['filename'])

    return {
        'file_links': file_links,
        'gallery_items': gallery_items,
        'infobox_images': infobox_images,
        'total_unique_files': len(all_filenames),
        'all_filenames': sorted(all_filenames),
    }


# Usage
media = extract_all_media(raw)
print(f"Total unique media files: {media['total_unique_files']}")
print(f"  File links: {len(media['file_links'])}")
print(f"  Gallery entries: {sum(len(g['items']) for g in media['gallery_items'])}")
print(f"  Infobox images: {len(media['infobox_images'])}")
for f in media['file_links'][:5]:
    print(f"    {f['filename']} — {f['options']['format']}, {f['options']['size']}")
```

---

## 19. Batch processing multiple articles

Process a collection of articles (from a dump, API, or file system),
applying transformations and collecting statistics across all pages.

```python
import wikitextparser as wtp
from pathlib import Path
from collections import Counter, defaultdict

CATEGORY_NS = {'category', 'catégorie', 'kategorie', 'categoría', 'تصنيف'}


def batch_process(
    articles: dict[str, str],
    transforms: list[callable] = None,
    collect_stats: bool = True,
) -> dict:
    """
    Process multiple articles with optional transforms and statistics.

    articles: {page_title: wikitext}
    transforms: list of functions (parsed, title) -> None that mutate parsed
    Returns: {results: {title: updated_wikitext}, stats: {...}}
    """
    transforms = transforms or []
    results = {}
    stats = {
        'total_articles': len(articles),
        'total_templates': Counter(),
        'total_categories': Counter(),
        'articles_with_issues': [],
        'link_graph': defaultdict(list),
        'template_usage': defaultdict(int),
    }

    for title, wikitext in articles.items():
        parsed = wtp.parse(wikitext)

        # Collect stats before transforms
        if collect_stats:
            # Template usage
            for t in parsed.templates:
                name = t.normal_name()
                stats['total_templates'][name] += 1
                stats['template_usage'][name] += 1

            # Categories
            for wl in parsed.wikilinks:
                head, sep, tail = wl.title.partition(':')
                if sep and head.strip().lower() in CATEGORY_NS:
                    stats['total_categories'][tail.strip()] += 1

            # Link graph
            for wl in parsed.wikilinks:
                target = wl.title.strip().split('#')[0]
                if target and ':' not in target:
                    stats['link_graph'][title].append(target)

            # Quality issues
            issues = []
            # Check for broken links
            broken = [wl for wl in parsed.wikilinks if not wl.title.strip()]
            if broken:
                issues.append(f"{len(broken)} broken links")
            # Check for duplicate args
            for t in parsed.templates:
                names = [a.name.strip() for a in t.arguments if not a.positional]
                if len(names) != len(set(names)):
                    issues.append(f"dup args in {t.normal_name()}")
                    break
            if issues:
                stats['articles_with_issues'].append((title, issues))

        # Apply transforms
        for transform_fn in transforms:
            transform_fn(parsed, title)

        results[title] = str(parsed)

    if collect_stats:
        stats['most_used_templates'] = stats['total_templates'].most_common(20)
        stats['most_common_categories'] = stats['total_categories'].most_common(20)
        stats['issue_count'] = len(stats['articles_with_issues'])

    return {'results': results, 'stats': stats}


# --- Example transforms ---

def remove_deprecated_templates(parsed, title):
    """Remove {{Cleanup}} and {{Stub}} templates."""
    deprecated = {'cleanup', 'stub', 'unreferenced'}
    for t in reversed(parsed.templates):
        if t.normal_name().lower() in deprecated:
            del t[:]


def normalize_categories(parsed, title):
    """Sort categories alphabetically at end of article."""
    cats = []
    for wl in reversed(parsed.wikilinks):
        head, sep, tail = wl.title.partition(':')
        if sep and head.strip().lower() in CATEGORY_NS:
            cats.append(str(wl))
            del wl[:]
    if cats:
        cats.sort()
        text = str(parsed).rstrip()
        parsed.string = text + '\n\n' + '\n'.join(cats) + '\n'


def add_missing_references_section(parsed, title):
    """Add == References == section if article has <ref> but no References heading."""
    has_refs = bool(parsed.get_tags('ref'))
    has_section = any(
        s.title and s.title.strip().lower() == 'references'
        for s in parsed.sections
    )
    if has_refs and not has_section:
        text = str(parsed).rstrip()
        parsed.string = text + '\n\n== References ==\n{{Reflist}}\n'


# Usage
articles = {
    'Article A': wikitext_a,
    'Article B': wikitext_b,
    'Article C': wikitext_c,
}

output = batch_process(
    articles,
    transforms=[
        remove_deprecated_templates,
        normalize_categories,
        add_missing_references_section,
    ],
    collect_stats=True,
)

# Print stats
s = output['stats']
print(f"Processed {s['total_articles']} articles")
print(f"Top templates: {s['most_used_templates'][:5]}")
print(f"Articles with issues: {s['issue_count']}")
for title, issues in s['articles_with_issues']:
    print(f"  {title}: {', '.join(issues)}")

# Save results
for title, updated in output['results'].items():
    Path(f'output/{title}.txt').write_text(updated, encoding='utf-8')
```
