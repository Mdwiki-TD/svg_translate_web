---
name: wikitextparser-api-reference
description: >
  Complete API reference for all wikitextparser classes, methods, properties,
  and edge-case behaviors. Load this file when a sub-skill points you here
  for exact method signatures, return types, or obscure parameter details.
applies_to:
  - "API"
  - "method signature"
  - "full reference"
  - "all classes"
---

# wikitextparser — Full API Reference

> Load this file when you need complete method signatures, property details, or edge-case behavior not covered in SKILL.md.

## Table of Contents

1. [WikiText (root class)](#wikitext)
2. [Template](#template)
3. [Argument](#argument)
4. [Parameter](#parameter)
5. [ParserFunction](#parserfunction)
6. [WikiLink](#wikilink)
7. [ExternalLink](#externallink)
8. [Section](#section)
9. [Table & Cell](#table--cell)
10. [WikiList](#wikilist)
11. [Tag](#tag)
12. [Comment](#comment)
13. [Bold & Italic](#bold--italic)
14. [SubWikiText internals](#subwikitext-internals)

---

## WikiText

The root class returned by `wtp.parse(string)`. All other objects inherit from it.

### Properties

| Property           | Type                   | Description                                    |
| ------------------ | ---------------------- | ---------------------------------------------- |
| `string`           | `str`                  | Full wikitext string. Supports get/set/delete. |
| `span`             | `tuple`                | Position of self relative to root node.        |
| `templates`        | `list[Template]`       | All templates (outermost first).               |
| `wikilinks`        | `list[WikiLink]`       | All `[[wikilinks]]`.                           |
| `external_links`   | `list[ExternalLink]`   | All `[url text]` and bare URLs.                |
| `parameters`       | `list[Parameter]`      | All `{{{parameters}}}`.                        |
| `parser_functions` | `list[ParserFunction]` | All `{{#func:…}}`.                             |
| `sections`         | `list[Section]`        | All sections (lead + headed).                  |
| `tables`           | `list[Table]`          | All top-level tables.                          |
| `comments`         | `list[Comment]`        | All `<!-- … -->` comments.                     |

### Methods

#### `get_sections(include_subsections=True, level=None, top_levels_only=False)`

-   `level`: int — filter by heading level (1–6). `None` = all.
-   `include_subsections`: bool — if False, exclude nested section text.
-   `top_levels_only`: bool — only return top-level sections; cannot combine with `level`.

#### `get_tables(recursive=False)`

-   `recursive=False` — only top-level tables.
-   `recursive=True` — includes nested tables.

#### `get_lists(pattern='\\#|\\*|[:;]')`

-   `pattern`: regex string or iterable of patterns for list item starters.
-   `'\\#'` = ordered, `'\\*'` = unordered, `'[:;]'` = definition lists.

#### `get_tags(name=None)`

-   `name`: str — filter by tag name (e.g. `'ref'`, `'gallery'`). `None` = all tags.

#### `get_bolds(recursive=True)` / `get_italics(recursive=True)`

-   Returns `list[Bold]` / `list[Italic]`.
-   `recursive`: also look inside templates, parser functions, tags.

#### `get_bolds_and_italics(recursive=True, filter_cls=None)`

-   `filter_cls`: `Bold`, `Italic`, or `None` (both).
-   More efficient than calling both separately.

#### `insert(index, string)`

-   Insert `string` before position `index`.
-   Equivalent to `self[index:index] = string` but faster.

#### `pformat(indent='    ', remove_comments=False)`

-   Pretty-print templates and parser functions with alignment.
-   Returns a string; does **not** mutate self.

#### `plain_text(**kwargs)`

All kwargs default to `True` unless noted:

-   `replace_templates` — replace `{{t|a}}` with `''` (or pass a callable `Template → str|None`).
-   `replace_parser_functions` — same for `{{#if:…}}`.
-   `replace_parameters` — `{{{a|b}}}` → `b`, `{{{a}}}` → `''`.
-   `replace_tags` — `<s>text</s>` → `text`.
-   `replace_external_links` — `[url text]` → `text`.
-   `replace_wikilinks` — `[[a|b]]` → `b`, `[[a]]` → `a`.
-   `unescape_html_entities` — `&amp;` → `&`.
-   `replace_bolds_and_italics` — strips `'''` and `''`. **Deprecated alias** — prefer the granular flags below.
-   `replace_bolds` — strips `'''…'''` only. Default `True`.
-   `replace_italics` — strips `''…''` only. Default `True`.
-   `replace_tables` — callable `Table → str|None`, or `True` (default converter), or `False`.

#### `ancestors(type_=None)` / `parent(type_=None)`

-   `type_`: `'Template'`, `'ParserFunction'`, `'WikiLink'`, `'Comment'`, `'Parameter'`, `'ExtensionTag'`.
-   Root node `ancestors()` always returns `[]`; `parent()` returns `None`.

#### `__contains__(value)`

-   `value in parsed` — True if value's span is inside parsed's span (same root object required).

#### `__call__(start, stop=False, step=None)`

-   `parsed(0)` → `parsed.string[0]`
-   `parsed(0, 5)` → `parsed.string[0:5]`

---

## Template

Inherits: `SubWikiTextWithArgs` → `SubWikiText` → `WikiText`

String must start with `{{` and end with `}}`.

### Properties

| Property        | Type             | Description                                               |
| --------------- | ---------------- | --------------------------------------------------------- |
| `name`          | `str`            | Template name (may include whitespace). Supports get/set. |
| `arguments`     | `list[Argument]` | All arguments in order.                                   |
| `nesting_level` | `int`            | 0 = top-level; +1 per enclosing template/parser function. |
| `templates`     | `list[Template]` | Nested templates.                                         |

### Methods

#### `get_arg(name) → Argument | None`

Returns last argument with that name, or `None`.

#### `set_arg(name, value, positional=None, before=None, after=None, preserve_spacing=False)`

-   Creates argument if missing; updates last one if exists.
-   `before` / `after`: name of another arg — insert relative to it.
-   `positional=True`: add as positional arg.
-   `preserve_spacing`: keep surrounding whitespace.

#### `has_arg(name, value=None) → bool`

-   With `value`: checks both name and value match.

#### `del_arg(name)`

Deletes all arguments with that name.

#### `normal_name(rm_namespaces=('Template',), code=None, capitalize=False) → str`

-   Strips comments, language code prefix, namespace, extra spaces, underscores, `#anchor`.
-   `capitalize=True`: uppercase first letter (per `$wgCapitalLinks`).

#### `rm_dup_args_safe(tag=None)`

Removes duplicate args only when safe (same name+value, or one is empty). Optional `tag` string appended to kept arg's value.

#### `rm_first_of_dup_args()`

Removes first occurrence of duplicate args. Rendered output unchanged; source data may be lost.

#### `pformat(indent='    ', remove_comments=False)`

Returns pretty-printed string with aligned `=` signs.

---

## Argument

Represents `|name=value` or `|positional_value` inside a template/parser function.

### Properties

| Property     | Type   | Description                                                                                                           |
| ------------ | ------ | --------------------------------------------------------------------------------------------------------------------- |
| `name`       | `str`  | Arg name; for positional args returns position as string (`'1'`, `'2'`, …). Setter converts positional → keyword.     |
| `value`      | `str`  | Arg value. Supports get/set.                                                                                          |
| `positional` | `bool` | True if no `=` sign. Setting to `False` converts to keyword (raises `ValueError` if already positional without name). |

---

## Parameter

Represents `{{{name|default}}}` (template parameter declaration).

### Properties

| Property  | Type          | Description                                                |
| --------- | ------------- | ---------------------------------------------------------- |
| `name`    | `str`         | Parameter name. Supports get/set.                          |
| `default` | `str \| None` | Default value. `None` if no pipe. Supports get/set/delete. |
| `pipe`    | `str`         | `'\|'` if default exists, else `''`. Read-only.            |

### Methods

#### `append_default(new_default_name)`

Wraps current default in another parameter layer:

```
{{{p|x}}}  →  append_default('q')  →  {{{p|{{{q|x}}}}}}
```

No-op if `new_default_name` already appears among defaults.

---

## ParserFunction

Inherits: `SubWikiTextWithArgs` → `SubWikiText` → `WikiText`

Represents `{{#if:condition|then|else}}`, `{{#switch:…}}`, `{{ucfirst:…}}`, and
other parser functions and magic words that use `:` as the first separator.

### Properties

| Property           | Type                    | Description                                                             |
| ------------------ | ----------------------- | ----------------------------------------------------------------------- |
| `name`             | `str`                   | Function name (e.g. `'#if'`, `'#switch'`, `'lc'`). Supports get/set.   |
| `arguments`        | `list[Argument]`        | All arguments (first one is the condition/expression). Same as Template.|
| `nesting_level`    | `int`                   | 0 = top-level; +1 per enclosing template/parser function.               |
| `templates`        | `list[Template]`        | Templates nested inside this parser function.                            |
| `parser_functions` | `list[ParserFunction]`  | Parser functions nested inside (excludes self).                          |

### Methods

All methods inherited from `SubWikiTextWithArgs` — same as Template:

#### `get_arg(name) → Argument | None`

Returns last argument with that name, or `None`.

#### `set_arg(name, value, positional=None, before=None, after=None, preserve_spacing=False)`

Same semantics as `Template.set_arg()`.

#### `has_arg(name, value=None) → bool`

#### `del_arg(name)`

#### `get_lists(pattern=...)`

Returns WikiList objects across all arguments.

### Argument layout for common parser functions

| Function      | `arguments[0]`         | `arguments[1]`  | `arguments[2]`   |
| ------------- | ---------------------- | --------------- | ----------------- |
| `#if`         | condition expression   | then-branch     | else-branch       |
| `#ifeq`       | value A                | value B         | then / else       |
| `#switch`     | expression             | `key=value` pairs (keyword args) | `#default=...` |
| `#ifexist`    | page title             | then-branch     | else-branch       |
| `#expr`       | math expression        | —               | —                 |
| `lc` / `uc`   | text to transform      | —               | —                 |
| `ucfirst`     | text to transform      | —               | —                 |

### Disambiguation from Template

The library distinguishes parser functions from templates by the presence of
`:` as the first separator (instead of `|`). A template whose name contains a
colon (e.g. `{{en:Article}}`) is still a `Template` if it has no `|`-separated
args or if the colon is part of a known namespace prefix.

### Key difference from Template

- `pf.name` often starts with `#` (e.g. `'#if'`, `'#switch'`).
- Magic words (`lc`, `uc`, `ucfirst`, `formatnum`, etc.) do **not** start with `#`.
- The library does **not** evaluate parser functions — it only exposes the structure.

---

## WikiLink

Represents `[[target#fragment|display text]]`.

### Properties

All support get, set, and delete:

| Property    | Type             | Description                                                             |
| ----------- | ---------------- | ----------------------------------------------------------------------- |
| `target`    | `str`            | Full target including fragment. Delete removes target + pipe.           |
| `title`     | `str`            | Target without fragment.                                                |
| `fragment`  | `str \| None`    | Anchor after `#`. Delete removes `#` and fragment.                      |
| `text`      | `str \| None`    | Display text after `\|`. `None` if no pipe. Delete removes pipe + text. |
| `wikilinks` | `list[WikiLink]` | Nested wikilinks inside this one.                                       |

**Note:** Setting `target = ''` keeps the pipe; `del wl.target` removes both.

---

## ExternalLink

Represents `[https://url Display text]` or bare `https://url`.

### Properties

| Property      | Type          | Description                                                                                                                                |
| ------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `url`         | `str`         | URL. Setter auto-adds brackets for bare links.                                                                                             |
| `text`        | `str \| None` | Text part after space. `None` for bare links or bracket links with no text. Setter auto-brackets bare links. Deleter removes space + text. |
| `in_brackets` | `bool`        | True if wrapped in `[…]`. Read-only.                                                                                                       |

**Edge case:** Templates adjacent to external links may be included in the URL:

```python
wtp.parse('http://example.com{{dead link}}').external_links[0].url
# → 'http://example.com{{dead link}}'
```

---

## Section

Represents a wikitext section (lead or headed).

### Properties

| Property   | Type          | Description                                                                                                       |
| ---------- | ------------- | ----------------------------------------------------------------------------------------------------------------- |
| `title`    | `str \| None` | Heading text (no `=` signs). `None` for lead section. Supports get/set/delete (delete removes heading + newline). |
| `level`    | `int`         | Heading level 1–6; `0` for lead section. Supports get/set.                                                        |
| `contents` | `str`         | Body text (excludes heading line). Supports get/set.                                                              |

---

## Table & Cell

### Table Properties

| Property        | Type          | Description                                             |
| --------------- | ------------- | ------------------------------------------------------- |
| `caption`       | `str \| None` | Table caption text. Supports get/set.                   |
| `caption_attrs` | `str \| None` | Caption attribute string. Supports get/set.             |
| `row_attrs`     | `list[dict]`  | List of attribute dicts per row. Setter overwrites all. |
| `nesting_level` | `int`         | 0 = top-level; +1 per enclosing table.                  |
| `attrs`         | `dict`        | Table-level HTML attributes.                            |

### Table Methods

#### `data(row=None, column=None, span=True, strip=True) → str | list | list[list]`

-   No args: returns full 2D list.
-   `row=N`: returns list for that row.
-   `column=N`: returns list for that column.
-   `row=N, column=M`: returns single cell string.
-   `span=False`: ignores colspan/rowspan.
-   `strip=True`: strips whitespace from values.
-   **Does not look inside templates** — use Cell objects for that.

#### `cells(row=None, column=None, span=True) → Cell | list | list[list]`

Same signature as `data()` but returns `Cell` objects instead of strings.

#### Attribute methods (inherited from `SubWikiTextWithAttrs`)

`get_attr(name)`, `set_attr(name, value)`, `has_attr(name)`, `del_attr(name)`

### Cell Methods

Same attribute methods as Table, plus:

-   `cell.attrs` — dict of all attributes.
-   `cell.set('colspan', '3')` — shorthand for `set_attr`.

---

## WikiList

Represents ordered (`#`), unordered (`*`), or definition (`:` / `;`) lists.

**Constructor:** `WikiList(string, pattern, ...)` — `pattern` is required (regex for list item prefix).

### Properties

| Property    | Type        | Description                                            |
| ----------- | ----------- | ------------------------------------------------------ |
| `items`     | `list[str]` | Item text only (no prefix, no sub-items).              |
| `fullitems` | `list[str]` | Full item strings including prefix and sub-item lines. |
| `level`     | `int`       | Nesting depth, 1-based.                                |

### Methods

#### `sublists(i=None, pattern='\\#|\\*|[:;]') → list[WikiList]`

-   `i`: index of parent item (0-based). `None` = all sub-lists.
-   `pattern`: regex for desired sub-list type. Current list's pattern auto-prefixed.

#### `convert(newstart)`

Replaces current list prefix pattern with `newstart` in-place.

```python
wl.convert('#')   # * → #  (unordered → ordered)
wl.convert(':')   # → definition list
```

#### `get_lists(pattern=...)`

Returns nested `WikiList` objects matching `pattern`.

---

## Tag

Represents HTML or MediaWiki extension tags: `<ref>…</ref>`, `<gallery/>`, etc.

### Properties

| Property          | Type          | Description                                                                                         |
| ----------------- | ------------- | --------------------------------------------------------------------------------------------------- |
| `name`            | `str`         | Tag name. Supports get/set.                                                                         |
| `contents`        | `str \| None` | Inner content. Supports get/set. Setting on self-closing tag expands it: `<t/>` → `<t>content</t>`. |
| `parsed_contents` | `SubWikiText` | Contents as a parseable WikiText object.                                                            |
| `attrs`           | `dict`        | All HTML attributes.                                                                                |

### Methods

`get_attr`, `set_attr`, `has_attr`, `del_attr` — same as Table.
`get_tags(name=None)` — nested tags.

---

## Comment

Represents `<!-- comment text -->`.

### Properties

| Property   | Type  | Description                               |
| ---------- | ----- | ----------------------------------------- |
| `contents` | `str` | Text between `<!--` and `-->`. Read-only. |

---

## Bold & Italic

`Bold` wraps `'''text'''`; `Italic` wraps `''text''`.

### Properties

| Property | Type  | Description                                                     |
| -------- | ----- | --------------------------------------------------------------- |
| `text`   | `str` | Content without surrounding quote tokens. Supports get/**set**. |

Setting `b.text = 'new'` replaces the inner content between the quote tokens
in-place — the surrounding `'''` / `''` delimiters are preserved.

```python
parsed = wtp.parse("This is '''important''' text")
b = parsed.get_bolds()[0]
b.text                 # 'important'
b.text = 'critical'
str(parsed)            # "This is '''critical''' text"
```

### Additional notes

- **`Bold`** and **`Italic`** inherit from `SubWikiText` and share the root buffer.
- `del b[:]` removes the bold/italic span (including the quote tokens) from the buffer.
- `b[:] = 'replacement'` replaces the entire span (including quotes) with arbitrary text.
- **Italic-specific:** `__init__` accepts `end_token=True/False` to handle cases where the italic doesn't end with `''` (unclosed italic at end-of-line).
- **Bold-italic (`'''''text'''''`)** may appear as either Bold or Italic depending on parsing context. Use `get_bolds_and_italics()` to capture both.

---

## SubWikiText Internals

Most objects inherit `SubWikiText`. Key behaviors:

-   All objects in a parsed tree **share the same underlying string list** — modifying any child modifies the root.
-   `ancestors(type_=None)` / `parent(type_=None)` traverse up the parse tree.
-   Supported `type_` values: `'Template'`, `'ParserFunction'`, `'WikiLink'`, `'Comment'`, `'Parameter'`, `'ExtensionTag'`.
-   `del obj[:]` or `del obj.string` removes the node from its parent.
-   `__setitem__` / `__delitem__` on slices for in-place string surgery.

### `SubWikiTextWithAttrs`

Adds HTML attribute access to `Table`, `Cell`, `Tag`:

-   `attrs` property → `dict[str, str]`
-   `get_attr(name)` → last value or `None`
-   `set_attr(name, value)` → sets last occurrence; creates if missing
-   `has_attr(name)` → `bool`
-   `del_attr(name)` → removes all with that name

### `SubWikiTextWithArgs`

Shared by `Template` and `ParserFunction`:

-   `name` property
-   `arguments` property
-   `nesting_level` property
-   `get_lists(pattern)` — lists across all arguments
