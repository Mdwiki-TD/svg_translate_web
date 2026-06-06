---
name: wikitextparser-parameters
description: >
  Work with template parameter declarations of the form {{{name|default}}}.
  These are NOT the same as template arguments. Used inside template bodies
  and on /doc subpages to declare what arguments a template accepts. Covers
  the Parameter class, name/default/pipe properties, and append_default.
applies_to:
  - "Parameter"
  - "{{{name|default}}}"
  - "{{{1|}}}"
  - "append_default"
---

# 03 — Parameters (`{{{name|default}}}`)

> Open this file when you see triple braces `{{{...}}}` and need to read or
> rewrite them. **These are not template calls** — they are parameter
> declarations used inside the body of a template definition.

## When to use this file

Use this file for:

- Parsing a template body that contains `{{{1|}}}`, `{{{name|default}}}`,
  `{{{a|{{{b|}}}}}}`, etc.
- Adding or changing default values.
- Wrapping defaults with fallback layers.

If you are working with **calls** like `{{Template|arg=val}}`, see
`02-templates.md` instead.

## Mental model

`{{{x|y}}}` declares "use the argument named `x`, or the literal `y` if not
provided". Triple-brace constructs only resolve at template-expansion time.
`wikitextparser` exposes them as `Parameter` objects:

```text
{{{ name | default }}}
   ^^^^   ^^^^^^^
   name   default (optional; pipe = '|' if present, '' otherwise)
```

## Quick reference

| Attribute / method                     | Description                                              |
| -------------------------------------- | -------------------------------------------------------- |
| `p.name`                               | Parameter name. Get/set                                  |
| `p.default`                            | Default value or `None`. Get/set/delete                  |
| `p.pipe`                               | `'\|'` if a default exists, `''` otherwise. Read-only    |
| `p.append_default(new_default_name)`   | Wrap current default in another `{{{name\|...}}}` layer  |
| `p.parameters`                         | Nested parameters (excludes self)                        |

## Step by step

### 1. Find all parameter declarations

```python
parsed = wtp.parse(template_body)
for p in parsed.parameters:
    print(p.name, '→', p.default)
```

### 2. Inspect a single parameter

```python
p = wtp.parse('{{{name|Alice}}}').parameters[0]
p.name         # 'name'
p.default      # 'Alice'
p.pipe         # '|'

p2 = wtp.parse('{{{name}}}').parameters[0]
p2.default     # None
p2.pipe        # ''
```

### 3. Set or change the default

```python
p = wtp.parse('{{{name}}}').parameters[0]
p.default = 'unknown'         # adds the pipe and the value
str(p)                         # '{{{name|unknown}}}'

p.default = 'anonymous'        # overwrites
str(p)                         # '{{{name|anonymous}}}'
```

### 4. Remove the default

```python
p = wtp.parse('{{{name|Alice}}}').parameters[0]
del p.default
str(p)        # '{{{name}}}'
```

`del p.default` removes both the `|` separator and the default content.
Setting `p.default = None` does **not** behave the same — assigning `None`
will write the string `'None'` into the buffer. Always use `del`.

### 5. Rename a parameter

```python
p = wtp.parse('{{{old|x}}}').parameters[0]
p.name = 'new'
str(p)        # '{{{new|x}}}'
```

### 6. Append a fallback default layer

`append_default` wraps the *innermost* default in another parameter
declaration, creating a fallback chain:

```python
p = wtp.parse('{{{p1|}}}').parameters[0]
p.append_default('p2')
str(p)        # '{{{p1|{{{p2|}}}}}}'

p.append_default('p3')
str(p)        # '{{{p1|{{{p2|{{{p3|}}}}}}}}}'
```

Use case: making a template fall back to a secondary parameter name without
breaking existing usages.

```python
# {{{first_name|}}}  →  also accept |firstname=
p.append_default('firstname')
# Now: {{{first_name|{{{firstname|}}}}}}
```

If `new_default_name` is already among the chained defaults, `append_default`
is a no-op.

### 7. Walk nested parameters

```python
parsed = wtp.parse('{{{a|{{{b|{{{c|x}}}}}}}}}')
parsed.parameters                # [outer, mid, inner] (3 entries)
parsed.parameters[0].parameters  # [mid, inner]  — excludes self
```

## Edge cases & gotchas

- **No-default vs empty-default**: `{{{x}}}` (no pipe) and `{{{x|}}}` (empty
  default) are different. The first has `p.default == None`; the second has
  `p.default == ''`. Both render as empty when unset, but only the second has
  `p.pipe == '|'`.
- **`p.default = None`** does **not** remove the default. It writes the
  literal string `'None'`. Always use `del p.default`.
- **Parameters cannot exist outside a template body** in normal usage, but
  `wikitextparser` will still parse them in any context. Don't rely on
  finding parameters in plain article wikitext.
- **`append_default` modifies the innermost layer**, not the outermost.
  Reading `p.default` after appending shows the new wrapper.
- **`p.parameters[0]`** of a parameter returns its first **nested** parameter,
  not itself. The list-property convention (exclude self) is consistent across
  all wikitextparser classes.

## Recipes

### Recipe A: list every parameter used in a template body

```python
def used_parameters(template_body: str) -> set[str]:
    parsed = wtp.parse(template_body)
    return {p.name.strip() for p in parsed.parameters}
```

### Recipe B: add an alias parameter as fallback

```python
def add_alias(template_body: str, primary: str, alias: str) -> str:
    parsed = wtp.parse(template_body)
    for p in parsed.parameters:
        if p.name.strip() == primary:
            p.append_default(alias)
    return str(parsed)
```

### Recipe C: change every empty default to a placeholder

```python
parsed = wtp.parse(template_body)
for p in parsed.parameters:
    if p.default == '':
        p.default = '{{{1|}}}'   # echo positional 1 if set
```

### Recipe D: remove all defaults (force callers to provide values)

```python
for p in parsed.parameters:
    if p.default is not None:
        del p.default
```

## See also

- `02-templates.md` — for `{{Template|arg=val}}` calls (different syntax)
- `11-parser-functions.md` — `{{#if:{{{x|}}}|...}}` is a common combo
- `references/reference.md` — full Parameter API
