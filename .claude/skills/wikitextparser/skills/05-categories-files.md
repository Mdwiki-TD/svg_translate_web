---
name: wikitextparser-categories-files
description: >
  Extract and modify [[Category:...]] and [[File:...]]/[[Image:...]] links,
  parse image parameters (thumb, right, 200px, caption), and read
  <gallery> contents. Includes a multilingual prefix table for category
  and file namespaces, since wikitextparser does not localize them.
applies_to:
  - "[[Category:Name]]"
  - "[[File:image.jpg|thumb|right|caption]]"
  - "[[Image:image.jpg]]"
  - "<gallery>"
  - "categorias"
  - "categories"
---

# 05 — Categories, Files & Galleries

> Open this file when you need to extract or rewrite category links, file or
> image links, and `<gallery>` blocks. These are *not* separate classes in
> `wikitextparser` — they are wikilinks (or extension tags) with a special
> namespace. You filter them yourself.

## When to use this file

Use this file for:

- Listing all categories on a page.
- Adding or removing a category.
- Listing all files / images, with their parameters.
- Reading `<gallery>...</gallery>` contents.
- Working across wikis that use localized namespace names.

For the generic `[[link]]` API, see `04-wikilinks.md`.
For the generic `<tag>` API, see `10-tags-comments.md`.

## Mental model

In MediaWiki:

- `[[Category:X]]` is a wikilink to a page in the **Category** namespace.
- `[[File:X.jpg]]` is a wikilink to a page in the **File** namespace, but
  rendered as an embedded image.
- `<gallery>` is an extension tag whose contents are a list of file names,
  one per line.

`wikitextparser` does **not** know which namespace prefix means "category"
or "file" on a given wiki. You must match the prefix yourself, ideally
against a localization table.

## Multilingual namespace table

A reasonable subset for filtering. You can extend with Pywikibot's namespace
data when accuracy matters across all 300+ MediaWiki languages.

| Concept   | Common prefixes                                                                |
| --------- | ------------------------------------------------------------------------------ |
| Category  | `Category`, `CAT`, `Categoría`, `Categorie`, `Catégorie`, `Kategorie`, `Kategori`, `Категория`, `Категорія`, `קטגוריה`, `تصنيف`, `رده`, `श्रेणी`, `分类`, `分類`, `カテゴリ`, `범주`, `Κατηγορία` |
| File      | `File`, `Image`, `Archivo`, `Datei`, `Fichier`, `Файл`, `ファイル`, `파일`, `文件`, `ملف`, `קובץ`, `Plik`, `Bestand`, `Tệp`, `อิมเมจ`, `Mynd` |

Define them once and reuse:

```python
CATEGORY_NS = {
    'category', 'cat',
    'categoría', 'categorie', 'catégorie', 'kategorie', 'kategori',
    'категория', 'категорія',
    'קטגוריה',
    'تصنيف', 'رده',
    'श्रेणी',
    '分类', '分類', 'カテゴリ', '범주',
    'κατηγορία',
}

FILE_NS = {
    'file', 'image',
    'archivo', 'datei', 'fichier',
    'файл',
    'ファイル', '파일', '文件',
    'ملف',
    'קובץ', 'plik', 'bestand', 'tệp',
}
```

## Categories

### List all categories

```python
def get_categories(wikitext: str) -> list[dict]:
    parsed = wtp.parse(wikitext)
    out = []
    for wl in parsed.wikilinks:
        head, sep, tail = wl.title.partition(':')
        if sep and head.strip().lower() in CATEGORY_NS:
            out.append({
                'name'   : tail.strip(),
                'sortkey': (wl.text or '').strip(),  # [[Cat:X|sortkey]]
                'raw'    : str(wl),
            })
    return out
```

`wl.text` for a category link is the **sort key** — the value MediaWiki uses
for ordering on the category page. `None`/empty means "use the article title".

### Add a category

```python
def add_category(wikitext: str, name: str, sortkey: str = None) -> str:
    parsed = wtp.parse(wikitext)
    link = f'[[Category:{name}]]' if not sortkey else f'[[Category:{name}|{sortkey}]]'
    parsed.string = str(parsed).rstrip() + '\n' + link + '\n'
    return parsed.string
```

(Categories are placed at the bottom by convention.)

### Remove a category

```python
def remove_category(wikitext: str, name: str) -> str:
    parsed = wtp.parse(wikitext)
    name = name.strip().lower()
    for wl in parsed.wikilinks:
        head, sep, tail = wl.title.partition(':')
        if sep and head.strip().lower() in CATEGORY_NS and tail.strip().lower() == name:
            del wl[:]
    return str(parsed)
```

### Rename a category globally

```python
def rename_category(wikitext, old_name, new_name):
    parsed = wtp.parse(wikitext)
    old_lc = old_name.strip().lower()
    for wl in parsed.wikilinks:
        head, sep, tail = wl.title.partition(':')
        if sep and head.strip().lower() in CATEGORY_NS and tail.strip().lower() == old_lc:
            wl.title = head + ':' + new_name
    return str(parsed)
```

### Change a sort key

```python
for wl in parsed.wikilinks:
    head, sep, tail = wl.title.partition(':')
    if sep and head.lower() in CATEGORY_NS and tail.strip() == 'Living people':
        wl.text = 'Smith, John'        # adds or replaces |sortkey
```

## Files / Images

### List all files

```python
def get_files(wikitext: str) -> list[dict]:
    parsed = wtp.parse(wikitext)
    out = []
    for wl in parsed.wikilinks:
        head, sep, tail = wl.title.partition(':')
        if sep and head.strip().lower() in FILE_NS:
            out.append({
                'filename': tail.strip(),
                'params'  : (wl.text or '').strip(),
                'raw'     : str(wl),
            })
    return out
```

### Parse image parameters

`wl.text` for a file link contains pipe-separated image parameters:
`thumb|right|200px|caption`. Parse them yourself:

```python
ALIGN     = {'left', 'right', 'center', 'centre', 'none'}
FORMAT    = {'thumb', 'thumbnail', 'frame', 'framed', 'frameless'}
SPECIALS  = {'border', 'upright'}

def parse_image_params(text: str | None) -> dict:
    """Split 'thumb|right|200px|caption' into structured fields."""
    if not text:
        return {'caption': None}
    parts = text.split('|')
    result = {
        'format'  : None,
        'align'   : None,
        'size'    : None,
        'border'  : False,
        'caption' : None,
        'extras'  : [],
    }
    for p in parts:
        s = p.strip().lower()
        if s in FORMAT:
            result['format'] = s
        elif s in ALIGN:
            result['align'] = s
        elif s == 'border':
            result['border'] = True
        elif s.endswith('px') and s[:-2].replace('x', '').isdigit():
            result['size'] = s
        elif s.startswith(('alt=', 'link=', 'lang=', 'page=', 'class=', 'upright')):
            result['extras'].append(p.strip())
        else:
            # First non-keyword token wins as caption
            if result['caption'] is None:
                result['caption'] = p.strip()
            else:
                result['extras'].append(p.strip())
    return result
```

Example:

```python
parse_image_params('thumb|right|200px|alt=Alice|A portrait of Alice')
# {'format': 'thumb', 'align': 'right', 'size': '200px',
#  'border': False, 'caption': 'A portrait of Alice',
#  'extras': ['alt=Alice']}
```

This is intentionally simple — the full MediaWiki spec has more options
(`upright=1.2`, `link=`, etc.). Extend `SPECIALS`/handling as needed.

### Add a file

```python
def add_file(wikitext, filename, options='thumb|right'):
    parsed = wtp.parse(wikitext)
    link = f'[[File:{filename}|{options}]]'
    return str(parsed) + '\n' + link
```

### Detect images in a `plain_text()` cleanup

`plain_text()` already removes file links — so by the time you have the
plain text, images are gone. To preserve a placeholder, use a callable on
`replace_wikilinks=False` and filter manually:

```python
parsed = wtp.parse(wikitext)
files = get_files(wikitext)
for f in files:
    print('IMAGE:', f['filename'])
clean = parsed.plain_text()
```

## Galleries

`<gallery>` is an *extension tag*. Its contents are not parsed as wikitext;
they are a newline-separated list of file references.

### List images in a gallery

```python
def parse_galleries(wikitext: str) -> list[list[dict]]:
    parsed = wtp.parse(wikitext)
    galleries = []
    for tag in parsed.get_tags('gallery'):
        items = []
        for raw_line in (tag.contents or '').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('<!--'):
                continue
            filename, sep, options = line.partition('|')
            items.append({
                'filename': filename.strip(),
                'caption' : options.strip() if sep else None,
            })
        galleries.append(items)
    return galleries
```

### Read gallery attributes

```python
for g in parsed.get_tags('gallery'):
    g.attrs           # e.g. {'mode': 'packed', 'widths': '180px'}
    g.get_attr('mode')
```

### Add an image to an existing gallery

```python
for g in parsed.get_tags('gallery'):
    text = g.contents or ''
    text = text.rstrip() + '\nNew_image.jpg|A new caption\n'
    g.contents = text
    break
```

## Edge cases & gotchas

- **Localized namespaces are case-insensitive but NOT
  underscore/space-insensitive on prefix detection.** Compare via
  `head.strip().lower()`. Treat underscores in the *body* of the name
  separately — `wl.title` keeps them.
- **`Image:` is an alias of `File:`** on most wikis; both should be in
  `FILE_NS`.
- **`<gallery>` contents are not wikitext-parsed**; that's why nested
  `[[wl]]` parsing on `tag.contents` won't yield anything. You must split
  manually on `|` per line.
- **A category with leading `:` like `[[:Category:X]]`** is a *link* to the
  category page, *not* a categorization. Filter `wl.title.startswith(':')`
  separately if needed.
- **Some wikis place categories anywhere**, not just at the end. Don't
  assume position when extracting.
- **An image inside an infobox parameter** is usually just a filename, not a
  full `[[File:...]]` link. Those values won't appear in `parsed.wikilinks`
  — read them via the template argument:

  ```python
  for t in parsed.templates:
      if 'infobox' in t.normal_name().lower():
          img = t.get_arg('image')
          if img:
              print(img.value.strip())
  ```

## Recipes

### Recipe A: collect all media references in any form

```python
def all_media(parsed):
    media = set()
    # 1. [[File:...]]
    for f in get_files(str(parsed)):
        media.add(f['filename'])
    # 2. <gallery>...</gallery>
    for items in parse_galleries(str(parsed)):
        for it in items:
            media.add(it['filename'])
    # 3. infobox image fields
    for t in parsed.templates:
        for arg in t.arguments:
            v = arg.value.strip()
            if v.lower().endswith(('.jpg', '.jpeg', '.png', '.svg', '.gif', '.webp', '.tif', '.tiff', '.ogv')):
                media.add(v)
    return media
```

### Recipe B: ensure every page has a category

```python
cats = get_categories(wikitext)
if not cats:
    wikitext = add_category(wikitext, 'Uncategorized')
```

### Recipe C: replace every category with a tracking version

```python
parsed = wtp.parse(wikitext)
for wl in parsed.wikilinks:
    head, sep, tail = wl.title.partition(':')
    if sep and head.lower() in CATEGORY_NS:
        wl.title = head + ':Reviewed/' + tail
```

### Recipe D: count files per gallery

```python
for i, items in enumerate(parse_galleries(wikitext), 1):
    print(f'Gallery {i}: {len(items)} files')
```

## See also

- `04-wikilinks.md` — generic wikilink behaviour
- `10-tags-comments.md` — `<gallery>` and other extension tags
- `02-templates.md` — image fields inside infobox arguments
- `references/examples.md` — recipe 12 has another category-extraction
  variant
