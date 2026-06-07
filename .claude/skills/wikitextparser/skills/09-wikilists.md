---
name: wikitextparser-wikilists
description: >
    Work with bullet (*), numbered (#), and definition (:;) lists. Covers
    WikiList items vs fullitems, level/sublists/convert, multi-pattern
    retrieval, definition-list handling, and constructing a WikiList directly
    from a string.
applies_to:
    - "WikiList"
    - "* item"
    - "# item"
    - ": item"
    - "; term"
    - "get_lists"
    - "sublists"
    - "convert"
---

# 09 — Wiki Lists (`*`, `#`, `:`, `;`)

> Open this file when you need to read or rewrite bullet, numbered, or
> definition lists.

## When to use this file

Use this file for:

-   Counting or extracting list items.
-   Converting between list types (bullet ↔ numbered).
-   Walking sub-lists.
-   Working with definition lists (`;` term and `:` definition).

## Mental model

MediaWiki has three list flavours, all line-prefixed:

| Prefix  | Meaning            | Example                   |
| ------- | ------------------ | ------------------------- |
| `*`     | unordered (bullet) | `* item`                  |
| `#`     | ordered (numbered) | `# item`                  |
| `;`/`:` | definition list    | `; term` / `: definition` |

Nesting is by repeating the prefix: `**` is a sub-bullet, `*#` mixes types.
A `WikiList` represents one consecutive block sharing the same starting
character.

`wikitextparser` does _not_ enumerate these automatically; you ask for them
by passing a regex pattern.

## Quick reference

| Operation                          | Description                              |
| ---------------------------------- | ---------------------------------------- |
| `parsed.get_lists()`               | All lists (default pattern matches all)  |
| `parsed.get_lists(r'\*')`          | Only `*` bullet lists                    |
| `parsed.get_lists(r'\#')`          | Only `#` numbered lists                  |
| `parsed.get_lists('[:;]')`         | Only definition lists                    |
| `parsed.get_lists((r'\*', r'\#'))` | Multiple patterns                        |
| `wl.items`                         | Item text (no prefix, no sub-items)      |
| `wl.fullitems`                     | Item text including prefix and sub-items |
| `wl.level`                         | Nesting depth (1-based)                  |
| `wl.sublists(i=None, pattern=...)` | Sub-lists; `i=N` restricts to item N     |
| `wl.convert(newstart)`             | In-place: replace prefix pattern         |
| `wtp.WikiList(text, pattern)`      | Build directly from a fragment           |

## Step by step

### 1. Get all lists

```python
parsed = wtp.parse("""
* alpha
* beta
*# nested numbered
* gamma

# step 1
# step 2

; Term : Definition
""")

parsed.get_lists()           # 3 WikiList objects
parsed.get_lists(r'\*')      # only the bullet block
```

The default pattern is `(r'\#', r'\*', '[:;]')` — note that `:` and `;` are
grouped together because they form a single definition list.

### 2. Items vs fullitems

```python
wl = parsed.get_lists(r'\*')[0]
wl.items
# [' alpha', ' beta', ' gamma']    ← only top-level items, no `*` prefix

wl.fullitems
# ['* alpha\n', '* beta\n*# nested numbered\n', '* gamma\n']
#                       ↑ sub-list folded into item 2's full text
```

`items` is for "give me the displayed text"; `fullitems` is for "give me
each item's full source including any nested sub-list".

### 3. Walk sub-lists

```python
wl.sublists()
# every nested list under any item

wl.sublists(1)
# only sub-lists belonging to item index 1

wl.sublists(1, pattern=r'\#')
# only the numbered sub-lists under item 1
```

`pattern` here is the _child_ pattern. The current list's pattern is
prepended automatically — you don't repeat it.

### 4. Convert list types

```python
wl = parsed.get_lists(r'\*')[0]
wl.convert('#')
# All `* item` become `# item` (in place)

wl.convert(':')
# Now they become definition entries (no term)
```

After `convert`, the list's `pattern` attribute is updated automatically.

### 5. Definition lists

```python
parsed = wtp.parse(";Apple : red fruit\n;Banana : yellow fruit")
wl = parsed.get_lists('[:;]')[0]
wl.items
# ['Apple ', ' red fruit', 'Banana ', ' yellow fruit']
```

The pattern `[:;]` returns _both_ terms and definitions interleaved.
To pair them, walk in pairs:

```python
def def_list_pairs(wl):
    return list(zip(wl.items[::2], wl.items[1::2]))
```

Note: due to MediaWiki's line-folding rules, a single-line
`; term : definition` is also recognised — `wikitextparser` treats both
parts as separate items.

### 6. Build a list directly

```python
ol = wtp.WikiList("# step 1\n# step 2\n", r'\#')
ol.items                # [' step 1', ' step 2']
ol.convert(':')
str(ol)                 # ': step 1\n: step 2\n'
```

This is useful when you have a fragment of wikitext that _is_ a list (no
surrounding article), and you want the WikiList API directly.

### 7. Multiple sub-list patterns at once

```python
wl.sublists(pattern=(r'\#', r'\*'))   # all sub-lists of either type
```

## Edge cases & gotchas

-   **Patterns are regex literals.** Always escape `*`, `+`, `#`, `?`, etc.
    Use `r'\*'` not `'*'`.
-   **Fragment lists** that don't start at a line boundary may not be matched.
    Add a leading `\n` before parsing if needed.
-   **Definition lists with external links** containing `:` look ambiguous to
    the parser. The library shadows `[url]` regions before matching list
    patterns, so `: see [https://example.com link]` works correctly.
-   **`fullitems` may differ in order from `items`** for definition lists
    because MediaWiki allows `;A : B` on one line. The library normalises
    this internally and `fullitems` is sorted; don't rely on positional
    parity between `items[i]` and `fullitems[i]`.
-   **`level` is 1-based**, not 0-based. The outermost list is `level == 1`.
-   **Converting a sub-list does not touch its parent.** If you want to
    convert a whole tree, recurse via `sublists()`.
-   **`convert` does not adjust nested patterns.** A `**` sub-bullet stays
    `**` even after `convert('#')` on the parent. Convert sub-lists
    separately.

## Recipes

### Recipe A: extract a flat list of bullet items

```python
def all_bullets(parsed) -> list[str]:
    out = []
    for wl in parsed.get_lists(r'\*'):
        out.extend(item.strip() for item in wl.items)
    return out
```

### Recipe B: convert all unordered to ordered

```python
def bullets_to_numbers(parsed):
    for wl in parsed.get_lists(r'\*'):
        wl.convert('#')
```

### Recipe C: count by list type

```python
def list_counts(parsed) -> dict[str, int]:
    return {
        'bullet'    : sum(len(wl.items) for wl in parsed.get_lists(r'\*')),
        'numbered'  : sum(len(wl.items) for wl in parsed.get_lists(r'\#')),
        'definition': sum(len(wl.items) for wl in parsed.get_lists('[:;]')),
    }
```

### Recipe D: extract definition pairs

```python
def def_pairs(parsed) -> list[tuple[str, str]]:
    pairs = []
    for wl in parsed.get_lists('[:;]'):
        items = [i.strip() for i in wl.items]
        # pair odd→even after the leading `;` term
        for i in range(0, len(items) - 1, 2):
            pairs.append((items[i], items[i + 1]))
    return pairs
```

### Recipe E: flatten nested bullets with depth markers

```python
def flatten_with_depth(wl, depth=1, out=None):
    out = out if out is not None else []
    for i, item in enumerate(wl.items):
        out.append((depth, item.strip()))
        for sub in wl.sublists(i):
            flatten_with_depth(sub, depth + 1, out)
    return out
```

## See also

-   `02-templates.md` — lists inside template arguments are reachable via
    `template.get_lists(...)`
-   `references/reference.md` — full WikiList API
