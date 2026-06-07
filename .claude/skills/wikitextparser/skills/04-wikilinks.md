---
name: wikitextparser-wikilinks
description: >
    Read and modify [[wikilinks]] — the [[target#fragment|display text]] syntax.
    Covers WikiLink target/title/fragment/text properties, how setters and
    deleters affect the pipe and hash separators, nested wikilinks, and the
    filtering pattern for namespace-specific links (Categories, Files,
    interwiki).
applies_to:
    - "WikiLink"
    - "[[Article]]"
    - "[[Article|text]]"
    - "[[Article#section|text]]"
    - "[[File:...]]"
    - "[[Category:...]]"
---

# 04 — WikiLinks (`[[ ... ]]`)

> Open this file when you need to read or edit any `[[wikilink]]`. For the
> specific topics of category and file/image links, also see
> `05-categories-files.md`.

## When to use this file

Use this file for:

-   Listing every internal link in an article.
-   Renaming a link target globally.
-   Changing or removing display text.
-   Distinguishing the title, fragment, and text parts.

## Mental model

A wikilink has up to four logical parts:

```
[[ target | display text ]]
   ^^^^^^   ^^^^^^^^^^^^
   title + fragment        text

target  =  "title#fragment"   (everything before the pipe)
title   =  "title"            (everything before the optional '#')
fragment=  "fragment"          (everything after '#'; None if no '#')
text    =  "display text"      (everything after '|';   None if no '|')
```

`wikitextparser` parses every part lazily. Each property supports get / set /
delete with very specific behaviour about which separators are added or
removed — read the rules carefully, because they are easy to get wrong.

## Quick reference

| Property       | Type             | Get              | Set                 | Delete                        |
| -------------- | ---------------- | ---------------- | ------------------- | ----------------------------- |
| `wl.target`    | `str`            | "title#fragment" | Replaces target     | Removes target _and_ the pipe |
| `wl.title`     | `str`            | before `#`       | Replaces title      | Removes title and the `#`     |
| `wl.fragment`  | `str` or `None`  | after `#`        | Adds `#` if absent  | Removes `#` and fragment      |
| `wl.text`      | `str` or `None`  | after `\|`       | Adds `\|` if absent | Removes `\|` and text         |
| `wl.wikilinks` | `list[WikiLink]` | nested only      | —                   | —                             |

## Step by step

### 1. Inspect parts

```python
wl = wtp.parse('[[Earth#Geography|our planet]]').wikilinks[0]
wl.target     # 'Earth#Geography'
wl.title      # 'Earth'
wl.fragment   # 'Geography'
wl.text       # 'our planet'

wl2 = wtp.parse('[[Earth]]').wikilinks[0]
wl2.target    # 'Earth'
wl2.title     # 'Earth'
wl2.fragment  # None
wl2.text      # None
```

### 2. Modify title / target

```python
wl = wtp.parse('[[Earth#Geography|home]]').wikilinks[0]

wl.title = 'Mars'             # [[Mars#Geography|home]]
wl.fragment = 'Surface'       # [[Mars#Surface|home]]
wl.text = 'red planet'        # [[Mars#Surface|red planet]]
```

Replacing the **whole target** (title + fragment together):

```python
wl.target = 'Venus#Atmosphere'
# Result: [[Venus#Atmosphere|red planet]]
```

### 3. Add parts that didn't exist

Setters automatically insert separators (`#` or `|`) when the target part was
missing:

```python
wl = wtp.parse('[[Earth]]').wikilinks[0]
wl.fragment = 'Geography'    # adds '#': [[Earth#Geography]]
wl.text = 'home'             # adds '|': [[Earth#Geography|home]]
```

### 4. Delete parts (and their separators)

```python
wl = wtp.parse('[[Earth#Geography|home]]').wikilinks[0]

del wl.text                  # [[Earth#Geography]]
del wl.fragment              # [[Earth]]
```

`del wl.text` removes the `|`. `del wl.fragment` removes the `#`. Setting
`wl.text = ''` or `wl.fragment = ''` would keep an empty separator
(`[[Earth#|]]`), which is rarely what you want.

### 5. The difference between `target = ''` and `del target`

```python
wl = wtp.parse('[[Earth|home]]').wikilinks[0]

wl.target = ''
str(wl)              # '[[|home]]'   — kept the pipe

wl = wtp.parse('[[Earth|home]]').wikilinks[0]
del wl.target
str(wl)              # '[[home]]'    — pipe removed too
```

### 6. Filter wikilinks by namespace

```python
def by_namespace(parsed, ns: str):
    ns_lower = ns.lower()
    out = []
    for wl in parsed.wikilinks:
        head = wl.title.partition(':')[0].strip().lower()
        if head == ns_lower:
            out.append(wl)
    return out

files = by_namespace(parsed, 'File')
cats  = by_namespace(parsed, 'Category')
```

For category and file links specifically — including localized namespace
names like `Catégorie:`, `Archivo:`, `ملف:` — see `05-categories-files.md`.

### 7. Nested wikilinks

```python
parsed = wtp.parse('[[A|inner [[B]] text]]')
parsed.wikilinks                  # [outer-link, B]
parsed.wikilinks[0].wikilinks     # [B]   — excludes self
```

The outer link's `text` includes the raw nested `[[B]]` substring. If you
want only the visible text, parse `wl.text` again:

```python
inner = wtp.parse(parsed.wikilinks[0].text)
inner.plain_text()   # 'inner B text'
```

### 8. Bulk rename a link target

```python
def rename_target(wikitext, old_title, new_title):
    parsed = wtp.parse(wikitext)
    for wl in parsed.wikilinks:
        if wl.title.strip() == old_title:
            wl.title = new_title
    return str(parsed)
```

### 9. Convert a piped link to a bare link (or vice versa)

```python
# Bare → piped
wl = wtp.parse('[[Earth]]').wikilinks[0]
wl.text = 'home'            # [[Earth|home]]

# Piped → bare (drop display text)
wl = wtp.parse('[[Earth|home]]').wikilinks[0]
del wl.text                 # [[Earth]]
```

## Edge cases & gotchas

-   **Templates inside link targets** are guessed: `[[{{name}}]]` is treated
    as a wikilink. The library has no way to expand the template — your code
    may want to skip such links.
-   **Trailing characters after `]]`** (the wikilink "trail") — words like
    `[[fish]]es` rendering as "fishes" — are _not_ part of `wl.text`. They sit
    in the surrounding string.
-   **`wl.title` strips fragment, but not whitespace.** `'  Earth  '` is a
    valid title with surrounding spaces. Compare with `.strip()`.
-   **Setting `wl.text = ''`** keeps the `|`, producing `[[Earth|]]` — sometimes
    rendered as a "pipe trick". Use `del wl.text` if you want the bare link.
-   **`wl.fragment = ''`** keeps the `#`, producing `[[Earth#]]`. Use
    `del wl.fragment` to drop it.
-   **`wl.wikilinks`** excludes `wl` itself — all "list" properties on
    wikitextparser nodes follow this convention.
-   **Self-links and red-links** look identical to normal links here. The
    library has no online index. To detect them, post-process `wl.title`
    against a list you maintain.
-   **Interwiki links** like `[[en:Earth]]` are normal wikilinks; the namespace
    prefix logic does not strip them. Check `wl.title.startswith('en:')` etc.
    yourself, or consult Pywikibot for canonical namespace tables.

## Recipes

### Recipe A: graph of outbound links

```python
def outbound_links(wikitext: str) -> list[str]:
    parsed = wtp.parse(wikitext)
    out = []
    for wl in parsed.wikilinks:
        title = wl.title.strip()
        if title and not title.startswith('#'):
            out.append(title.split('#')[0])
    return out
```

### Recipe B: rewrite all links in a section to a new prefix

```python
def reprefix_links(wikitext, old_prefix, new_prefix):
    parsed = wtp.parse(wikitext)
    for wl in parsed.wikilinks:
        if wl.title.startswith(old_prefix):
            wl.title = new_prefix + wl.title[len(old_prefix):]
    return str(parsed)
```

### Recipe C: find broken / empty wikilinks

```python
empties = [wl for wl in parsed.wikilinks if not wl.title.strip()]
```

### Recipe D: count display text usage

```python
from collections import Counter
counts = Counter(
    (wl.text or wl.title).strip() for wl in parsed.wikilinks
)
```

### Recipe E: drop fragments from every link

```python
for wl in parsed.wikilinks:
    if wl.fragment is not None:
        del wl.fragment
```

## See also

-   `05-categories-files.md` — categories and files (also wikilinks)
-   `07-external-links.md` — `[url text]` (different syntax)
-   `12-tree-navigation.md` — find a link's containing template/section
-   `references/reference.md` — full WikiLink API
