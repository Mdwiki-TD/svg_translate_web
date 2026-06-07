---
name: wikitextparser
description: >
    Parse, extract, and manipulate MediaWiki wikitext using the wikitextparser
    Python library. Use this skill whenever the user works with wikitext,
    Wikipedia/MediaWiki markup, infoboxes, templates, wikilinks, categories,
    files/images, galleries, tables, sections, lists, refs/citations, parser
    functions, or any pipeline that reads, edits, cleans, or rewrites
    MediaWiki-formatted text. Triggers include phrases like "parse wikitext",
    "extract templates", "get all wikilinks", "convert table to CSV", "remove
    wiki markup", "find categories", "rename a section", "modify infobox",
    "extract citations", "list all refs", "find files in article", or any task
    involving `{{ }}`, `[[ ]]`, `{| |}`, `<ref>`, `<gallery>`, `<!-- -->`, etc.
---

# WikiTextParser Skill

A modular guide for parsing and manipulating MediaWiki wikitext with the
[`wikitextparser`](https://pypi.org/project/wikitextparser/) Python library.

> **This skill is split into focused sub-skills.** Read `SKILL.md` first, then
> open only the sub-skill files that apply to your task. The sub-skills under
> `skills/` are self-contained: each one explains one element type end-to-end.

---

## 1. Install & import

```bash
pip install wikitextparser
```

```python
import wikitextparser as wtp

parsed = wtp.parse(wikitext_string)   # returns a WikiText object
```

`wtp.parse` is an alias of `wtp.WikiText`. The library has zero required
runtime dependencies beyond the regex backport and `wcwidth` (auto-installed).

---

## 2. "I want to ..." — pick a sub-skill

| Goal                                                              | Open                                                             |
| ----------------------------------------------------------------- | ---------------------------------------------------------------- |
| Understand `parse`, `string`, `plain_text`, `pformat`             | [`skills/01-wikitext-basics.md`](skills/01-wikitext-basics.md)   |
| Read or modify `{{template\|args}}` calls                         | [`skills/02-templates.md`](skills/02-templates.md)               |
| Work with `{{{param\|default}}}` declarations (template `/doc`)   | [`skills/03-parameters.md`](skills/03-parameters.md)             |
| Read or modify `[[wikilinks]]`                                    | [`skills/04-wikilinks.md`](skills/04-wikilinks.md)               |
| Extract or add `[[Category:...]]`, `[[File:...]]`, `<gallery>`    | [`skills/05-categories-files.md`](skills/05-categories-files.md) |
| Read tables, get cell data, export to CSV                         | [`skills/06-tables.md`](skills/06-tables.md)                     |
| Read `[url text]` and bare URLs                                   | [`skills/07-external-links.md`](skills/07-external-links.md)     |
| Navigate or rename headings (`== Section ==`)                     | [`skills/08-sections.md`](skills/08-sections.md)                 |
| Work with `*`, `#`, `:`, `;` lists                                | [`skills/09-wikilists.md`](skills/09-wikilists.md)               |
| Work with `<ref>`, `<gallery>`, `<nowiki>`, comments, bold/italic | [`skills/10-tags-comments.md`](skills/10-tags-comments.md)       |
| Inspect parser functions like `{{#if:}}` and `{{#switch:}}`       | [`skills/11-parser-functions.md`](skills/11-parser-functions.md) |
| Walk parents/ancestors; understand the in-place mutation model    | [`skills/12-tree-navigation.md`](skills/12-tree-navigation.md)   |
| Copy-paste recipes: infobox→dict, refs, link graphs, validation   | [`skills/13-common-patterns.md`](skills/13-common-patterns.md)   |
| Need full method signatures and edge cases                        | [`references/reference.md`](references/reference.md)             |
| Need long end-to-end pipelines                                    | [`references/examples.md`](references/examples.md)               |

---

## 3. Object map

Every parsed string is a tree of objects sharing one underlying string.

| Class             | How to obtain                                        | Sub-skill                |
| ----------------- | ---------------------------------------------------- | ------------------------ |
| `WikiText`        | `wtp.parse(s)`                                       | `01-wikitext-basics.md`  |
| `Template`        | `parsed.templates`                                   | `02-templates.md`        |
| `Argument`        | `template.arguments`, `template.get_arg(name)`       | `02-templates.md`        |
| `Parameter`       | `parsed.parameters`                                  | `03-parameters.md`       |
| `WikiLink`        | `parsed.wikilinks`                                   | `04-wikilinks.md`        |
| `ExternalLink`    | `parsed.external_links`                              | `07-external-links.md`   |
| `Section`         | `parsed.sections`, `parsed.get_sections(...)`        | `08-sections.md`         |
| `Table`           | `parsed.tables`, `parsed.get_tables(recursive=True)` | `06-tables.md`           |
| `Cell`            | `table.cells(row, column)`                           | `06-tables.md`           |
| `WikiList`        | `parsed.get_lists(pattern=...)`                      | `09-wikilists.md`        |
| `Tag`             | `parsed.get_tags(name)`                              | `10-tags-comments.md`    |
| `Comment`         | `parsed.comments`                                    | `10-tags-comments.md`    |
| `Bold` / `Italic` | `parsed.get_bolds()`, `parsed.get_italics()`         | `10-tags-comments.md`    |
| `ParserFunction`  | `parsed.parser_functions`                            | `11-parser-functions.md` |

All classes ultimately inherit from `WikiText`, which means **every property
access returns objects that are still attached to the same root**. Editing a
child mutates the root in place. See `12-tree-navigation.md` for details.

---

## 4. 30-second cheat sheet

```python
import wikitextparser as wtp

parsed = wtp.parse(article)

# Basic enumeration
parsed.templates         # all {{templates}}
parsed.wikilinks         # all [[wikilinks]]
parsed.tables            # all {| tables |} (recursive)
parsed.external_links    # all [url text] and bare URLs
parsed.sections          # all sections (lead at index 0)
parsed.comments          # all <!-- comments -->
parsed.get_tags('ref')   # all <ref> tags

# Read a template
t = parsed.templates[0]
t.name                   # 'Infobox person'
t.normal_name()          # canonicalized name
t.get_arg('name').value  # value of |name=

# Modify in place — the change is reflected in str(parsed)
t.set_arg('birth_date', '1990-01-01')
str(parsed)              # full updated wikitext

# Strip all wiki markup
clean = parsed.plain_text()

# Or use the standalone helper
from wikitextparser import remove_markup
clean = remove_markup(article)
```

---

## 5. Mental model in one paragraph

A `WikiText` object holds a single mutable string list shared with every
descendant. `parsed.templates` gives you `Template` objects whose `string`
property points into that same buffer. When you write `t.set_arg(...)`, the
buffer changes; `str(parsed)` reflects the change instantly. There is no
re-parse and no copy. This is why sub-skills emphasise "edits propagate to the
root" — it is not a side effect, it is the core design.

---

## 6. Known limitations (universal)

-   **Not an evaluator.** `{{#if:}}`, `{{ucfirst:}}`, and template expansion are
    _not_ executed. You get the parse tree only.
-   **Localized namespaces** like `[[Categoría:X]]` or `[[ملف:X]]` are valid
    wikilinks, but the library has no built-in localization table — you must
    match namespace prefixes yourself (see `05-categories-files.md`).
-   **Templates inside link targets.** In `[[{{name}}]]` the parser cannot know
    what the template expands to, so it guesses based on syntax.
-   **`Table.data()` does not look inside templates.** Use `table.cells(...)` or
    parse the cell value separately. See `06-tables.md`.
-   **Extension tag list** is based on English Wikipedia; rarely-used tags from
    other wikis may parse as plain HTML. See `10-tags-comments.md`.
-   **No `ast.walk()` equivalent.** Traversal is via `.parent()` and
    `.ancestors()`, plus list properties on each node. See `12-tree-navigation.md`.

---

## 7. Quick decision tree

```text
Need to extract data?         →  list properties (parsed.templates, .wikilinks, ...)
Need exact metadata?          →  use .normal_name(), .get_arg(), .attrs, ...
Need to modify and re-emit?   →  setters + str(parsed); never rebuild by hand
Need clean text?              →  parsed.plain_text(...)  or  remove_markup(s)
Need a CSV/dict?              →  table.data() or {arg.name: arg.value for ...}
Need to find context?         →  node.parent(type_=...), node.ancestors(...)
Need recursive structure?     →  parsed.get_tables(recursive=True), .get_lists(...)
```

---

## 8. Reference files

-   **`references/reference.md`** — full API surface, every method signature,
    parameter, return type, and edge case (~600 lines).
-   **`references/examples.md`** — 15+ end-to-end scripts covering common
    workflows from start to finish.

Open these only when a sub-skill points you to them or when you need a detail
that is not in the focused sub-skill files.
