---
name: wikitextparser-tables
description: >
    Extract data from MediaWiki tables ({| |}) and modify them. Covers
    Table.data() with row/column/span/strip arguments, Table.cells() returning
    Cell objects with HTML attributes, table caption and per-row attributes,
    recursive table discovery, and exporting to CSV or list-of-dicts.
applies_to:
    - "Table"
    - "Cell"
    - "{| ... |}"
    - "wikitable"
    - "data()"
    - "cells()"
---

# 06 — Tables

> Open this file when you need to read or modify any wiki table — the
> `{| ... |}` syntax. The library has rich support for cell data, spans,
> attributes, and captions.

## When to use this file

Use this file for:

-   Converting wiki tables to CSV / list-of-lists / list-of-dicts.
-   Reading or modifying cell HTML attributes (`colspan`, `rowspan`, `style`).
-   Working with nested tables.
-   Setting captions or row-level attributes.

## Mental model

A `Table` is bounded by `{|` ... `|}` and contains:

```text
{| <table-attrs>
|+ <caption>
|- <row-attrs>
| cell || cell
|- <row-attrs>
! header !! header
| cell
|}
```

The library provides two ways to read cell content:

1. **`table.data()`** — returns nested lists of strings. Fast and convenient,
   but values are stripped, and templates inside cells are _not_ expanded —
   they are returned verbatim as the cell text. **Good for plain tables.**
2. **`table.cells()`** — returns nested lists of `Cell` objects. Each cell
   exposes `.value`, `.attrs`, `.is_header`, and the full `WikiText` API.
   **Use when you need attributes or want to mutate cells.**

Spans (`colspan`, `rowspan`) are honoured by default and produce a
"flattened" rectangular grid where spanned cells are duplicated.

## Quick reference

### Table

| Attribute / method                                         | Description                               |
| ---------------------------------------------------------- | ----------------------------------------- |
| `parsed.tables`                                            | All tables, recursive                     |
| `parsed.get_tables(recursive=False)`                       | Only top-level tables                     |
| `table.data(row=None, column=None, span=True, strip=True)` | Cell **strings** (2D list)                |
| `table.cells(row=None, column=None, span=True)`            | Cell **objects** (2D list)                |
| `table.caption`                                            | Caption text (`None` if missing). Get/set |
| `table.caption_attrs`                                      | Caption attribute string. Get/set         |
| `table.attrs`                                              | Table-level HTML attributes               |
| `table.row_attrs`                                          | List of attribute dicts per row. Get/set  |
| `table.nesting_level`                                      | 0 = top-level; +1 per enclosing table     |
| `table.get_attr/set_attr/has_attr/del_attr`                | Modify table-level attributes             |

### Cell

| Attribute / method                                          | Description                      |
| ----------------------------------------------------------- | -------------------------------- |
| `cell.value`                                                | Cell content. Get/set            |
| `cell.attrs`                                                | Dict of HTML attributes          |
| `cell.is_header`                                            | True if the cell is `!` (header) |
| `cell.set_attr(name, value)` / `set('name', 'val')`         | Add or update a cell attribute   |
| `cell.get_attr(name)` / `has_attr(name)` / `del_attr(name)` | Read / check / delete            |

## Step by step

### 1. Get a table's data as a 2D list

```python
parsed = wtp.parse("""
{| class="wikitable"
|+ Capitals
! Country !! Capital
|-
| France || Paris
|-
| Japan || Tokyo
|}
""")

table = parsed.tables[0]
table.data()
# [['Country', 'Capital'],
#  ['France', 'Paris'],
#  ['Japan', 'Tokyo']]
```

`data()` includes header rows (the `!` rows). Strings are stripped by
default; pass `strip=False` to keep raw whitespace.

### 2. Read just one row or column

```python
table.data(row=0)              # ['Country', 'Capital']
table.data(column=1)           # ['Capital', 'Paris', 'Tokyo']
table.data(row=1, column=0)    # 'France'
```

### 3. Caption

```python
table.caption        # ' Capitals'
table.caption = 'Major Capitals'   # set
```

If the table has no caption, the setter creates the `|+` line.

### 4. Read header rows specifically

There is no separate `headers` API — header rows look like data rows with
`!` separators. To distinguish, use `cells()`:

```python
for row in table.cells():
    if all(c.is_header for c in row):
        print('header:', [c.value.strip() for c in row])
```

### 5. List of dicts (assuming first row is header)

```python
def table_to_dicts(table) -> list[dict]:
    rows = table.data()
    if len(rows) < 2:
        return []
    headers, *body = rows
    return [dict(zip(headers, r)) for r in body]
```

### 6. Span behaviour

```python
parsed = wtp.parse("""
{|
| A || colspan="2" | B
|-
| C || D || E
|}
""")
table = parsed.tables[0]
table.data()
# [['A', 'B', 'B'],   ← B duplicated by colspan
#  ['C', 'D', 'E']]

table.data(span=False)
# [['A', 'B'],
#  ['C', 'D', 'E']]
```

Set `span=False` when you want the literal cell layout instead of a
rectangular flattened grid. `colspan="0"` and `rowspan="0"` are normalised
to `1` (the library does not implement HTML's "span to end of group").

### 7. Cell attributes (read)

```python
cell = table.cells(row=0, column=0)
cell.value           # ' A '
cell.attrs           # {'colspan': '2'} for the B cell
cell.is_header       # False
cell.get_attr('colspan')   # '2' or None
```

Note that `cell.attrs` keys may be **bytes** in some library internals when
read via `data()` with span=True; the `Cell` API exposes `str` keys via
`get_attr`. Stick with `cell.attrs` and `cell.get_attr()` for safety.

### 8. Cell attributes (write)

```python
cell = table.cells(row=1, column=0)
cell.set_attr('style', 'background:#fee;')
cell.set('colspan', '2')   # shorthand
cell.del_attr('rowspan')
```

If the cell had no attribute placeholder before, `set_attr` adds one with
the proper `|` separator: a cell like `| A` becomes `| style="x" | A`.

### 9. Modify cell value

```python
cell = table.cells(row=1, column=0)
cell.value = ' Updated '
str(parsed)   # full table buffer reflects the change
```

### 10. Per-row attributes

```python
table.row_attrs
# [{}, {'class': 'highlight'}, {}]
```

Setter overwrites every row's attributes:

```python
table.row_attrs = [{}, {'class': 'highlight'}, {'style': 'color:red'}]
```

If you only want to modify one row, copy and re-assign:

```python
attrs = table.row_attrs
attrs[1]['class'] = 'highlight'
table.row_attrs = attrs
```

### 11. Recursive nested tables

```python
parsed = wtp.parse(article)
top    = parsed.get_tables(recursive=False)   # only outer tables
all_t  = parsed.get_tables(recursive=True)    # outer + nested
nesting = [t.nesting_level for t in all_t]    # 0, 1, 1, 2, ...
```

`parsed.tables` is a property equivalent to `get_tables(recursive=True)`.

## Edge cases & gotchas

-   **`data()` does not look inside templates.** A cell containing
    `{{convert|10|km}}` returns the literal text `{{convert|10|km}}`, not
    `10 km`. To extract structured data from such cells, parse the cell value:

    ```python
    raw = table.data(row=1, column=0)         # '{{convert|10|km}}'
    inner = wtp.parse(raw)                # treat as new wikitext
    ```

-   **`!!` in header rows** is treated as a cell separator inside a header row,
    matching the MediaWiki parser's behaviour. Don't rely on it elsewhere.
-   **Empty cells** appear as `''` in `data()`. Use `if v` to filter.
-   **`row_attrs`** for the very first row (the one before any `|-`) is
    represented separately — it is the row containing the table's first cells
    immediately after `{|`. Inspect the result before assuming a length.
-   **`table.nesting_level`** is 0 for top-level tables. A table inside a table
    is 1, and so on.
-   **Captions vs `|+` lines mid-table** — only the _first_ `|+` after `{|`
    and before the first row is recognised as the caption.
-   **Tables inside parsable extension tags** (e.g. `<onlyinclude>`) are
    found by `get_tables(recursive=True)` because the library re-parses
    inside such tags.
-   **`data()` with `strip=True` (the default)** removes leading and trailing
    whitespace (spaces, tabs, and newlines) from raw cell strings. Pass
    `strip=False` to preserve the original raw cell content unchanged.

## Recipes

### Recipe A: export every table to CSV

```python
import csv, io

def tables_to_csv(wikitext: str) -> list[str]:
    parsed = wtp.parse(wikitext)
    out = []
    for table in parsed.tables:
        rows = table.data()
        if not rows:
            continue
        buf = io.StringIO()
        csv.writer(buf).writerows(rows)
        out.append(buf.getvalue())
    return out
```

### Recipe B: convert to records (list of dicts)

```python
def first_table_records(wikitext: str) -> list[dict]:
    parsed = wtp.parse(wikitext)
    if not parsed.tables:
        return []
    rows = parsed.tables[0].data()
    if len(rows) < 2:
        return []
    headers = [h.strip() for h in rows[0]]
    return [dict(zip(headers, r)) for r in rows[1:]]
```

### Recipe C: bold every cell containing 'TODO'

```python
for table in parsed.tables:
    for row in table.cells():
        for cell in row:
            if 'TODO' in cell.value:
                cell.value = "'''" + cell.value.strip() + "'''"
```

### Recipe D: clear all colspans / rowspans

```python
for table in parsed.tables:
    for row in table.cells(span=False):
        for cell in row:
            cell.del_attr('colspan')
            cell.del_attr('rowspan')
```

### Recipe E: add a caption if missing

```python
for table in parsed.tables:
    if table.caption is None:
        table.caption = 'Untitled table'
```

### Recipe F: count cells by content type

```python
from collections import Counter

def cell_kinds(table) -> Counter:
    c = Counter()
    for row in table.cells(span=False):
        for cell in row:
            v = cell.value.strip()
            if not v:
                kind = 'empty'
            elif v.startswith('{{') and v.endswith('}}'):
                kind = 'template-only'
            elif '[[' in v:
                kind = 'has-wikilink'
            else:
                kind = 'plain'
            c[kind] += 1
    return c
```

## See also

-   `01-wikitext-basics.md` — `plain_text(replace_tables=...)` for cleanup
-   `10-tags-comments.md` — `<table>` HTML-style tags (different syntax)
-   `12-tree-navigation.md` — find a cell's parent table
-   `references/reference.md` — full Table/Cell API
