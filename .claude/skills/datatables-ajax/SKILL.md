---
name: datatables-ajax
description: >
    Expert guidance for implementing DataTables with Ajax data sources. Use this skill whenever
    the user mentions DataTables with Ajax, server-side processing, DataTables JSON endpoints,
    `ajax` option, `dataSrc`, `serverSide`, or is building a table that loads data from an API
    or backend. Also trigger when the user asks about DataTables pagination/search/sort with
    a remote data source, or troubleshooting DataTables AJAX issues (empty tables, wrong data
    format, POST vs GET, custom headers, reload). Covers both client-side Ajax loading and
    full server-side processing (SSP).
---

# DataTables AJAX Skill

## Overview

DataTables supports two distinct Ajax patterns — know which one is needed before writing code:

| Pattern                          | When to use                                                                   | Key option                  |
| -------------------------------- | ----------------------------------------------------------------------------- | --------------------------- |
| **Client-side Ajax**             | Load all data once via Ajax, DataTables handles paging/sort/search in browser | `ajax: '/url'`              |
| **Server-side Processing (SSP)** | Millions of rows; every page/sort/search hits the server                      | `serverSide: true` + `ajax` |

---

## Pattern 1 — Client-side Ajax (simple)

DataTables fetches all data once; browser handles filtering, sorting, paging.

### Minimal setup

```js
$("#myTable").DataTable({
    ajax: "/api/myData", // expects { "data": [...] } by default
    columns: [{ data: "name" }, { data: "position" }, { data: "salary" }],
});
```

### JSON response shape & `dataSrc`

DataTables looks for `data` key by default. Use `dataSrc` to point elsewhere:

```js
// Response: [ {...}, {...} ]  — bare array
ajax: { url: '/api/data', dataSrc: '' }

// Response: { "data": [...] }  — default, dataSrc not needed
ajax: '/api/data'

// Response: { "staff": [...] }
ajax: { url: '/api/data', dataSrc: 'staff' }

// Response: { "response": { "rows": [...] } }  — nested
ajax: { url: '/api/data', dataSrc: 'response.rows' }

// Transform data before DataTables sees it
ajax: {
    url: '/api/data',
    dataSrc: function(json) {
        return json.items.map(item => ({ ...item, fullName: item.first + ' ' + item.last }));
    }
}
```

### Column data binding

```js
columns: [
    { data: "name" }, // object key
    { data: 0 }, // array index
    { data: "hr.position" }, // nested dot notation
    { data: "contact.email", defaultContent: "N/A" }, // safe fallback
    {
        data: null, // computed column
        render: (row) => `<a href="/user/${row.id}">${row.name}</a>`,
    },
];
```

### Useful client-side Ajax options

```js
$('#myTable').DataTable({
    ajax: {
        url: '/api/data',
        type: 'POST',           // GET is default
        headers: { 'X-Auth': token },
        data: { filter: 'active' },   // extra params
        dataSrc: 'results'
    },
    deferRender: true,          // big perf win — render rows only when drawn
    columns: [ ... ]
});
```

### Reload / refresh

```js
const table = $('#myTable').DataTable({ ... });

// Reload and reset to page 1
table.ajax.reload();

// Reload keeping current page
table.ajax.reload(null, false);
```

---

## Pattern 2 — Server-side Processing (SSP)

Every interaction (page, sort, search) fires a new Ajax request. Server does all the work.

### Init

```js
$("#myTable").DataTable({
    serverSide: true,
    ajax: {
        url: "/api/ssp",
        type: "POST",
    },
    columns: [
        { data: "name", name: "name" },
        { data: "position", name: "position" },
        { data: "salary", name: "salary", searchable: false },
    ],
});
```

### Parameters DataTables sends to server

| Param                       | Type   | Meaning                                      |
| --------------------------- | ------ | -------------------------------------------- |
| `draw`                      | int    | Echo back as-is (cast to int for XSS safety) |
| `start`                     | int    | Row offset (0-based)                         |
| `length`                    | int    | Page size (-1 = all)                         |
| `search[value]`             | string | Global search string                         |
| `search[regex]`             | bool   | Treat search as regex?                       |
| `order[i][column]`          | int    | Column index to sort                         |
| `order[i][dir]`             | string | `asc` / `desc`                               |
| `order[i][name]`            | string | Column name (from `columns.name`)            |
| `columns[i][data]`          | string | Column data field                            |
| `columns[i][name]`          | string | Column name                                  |
| `columns[i][searchable]`    | bool   | Column is searchable?                        |
| `columns[i][orderable]`     | bool   | Column is orderable?                         |
| `columns[i][search][value]` | string | Per-column search value                      |

### Required JSON response from server

```json
{
    "draw": 1,
    "recordsTotal": 57,
    "recordsFiltered": 42,
    "data": [
        { "name": "Tiger Nixon", "position": "Architect", "salary": "$320,800" },
        ...
    ],
    "error": "optional error message"
}
```

**Critical:** always cast `draw` to integer before echoing back (XSS prevention).

### Example SSP server handler (Node/Express)

```js
app.post("/api/ssp", async (req, res) => {
    const { draw, start, length, search, order, columns } = req.body;

    const searchVal = search?.value || "";
    const orderCol = columns[order[0].column].data;
    const orderDir = order[0].dir === "asc" ? 1 : -1;

    const filter = searchVal
        ? {
              $or: ["name", "position"].map((f) => ({
                  [f]: new RegExp(searchVal, "i"),
              })),
          }
        : {};

    const [recordsFiltered, recordsTotal, data] = await Promise.all([
        MyModel.countDocuments(filter),
        MyModel.countDocuments({}),
        MyModel.find(filter)
            .sort({ [orderCol]: orderDir })
            .skip(+start)
            .limit(+length),
    ]);

    res.json({
        draw: parseInt(draw), // CAST — never echo raw string
        recordsTotal,
        recordsFiltered,
        data,
    });
});
```

### Example SSP server handler (PHP/PDO)

```php
$draw   = (int)$_POST['draw'];
$start  = (int)$_POST['start'];
$length = (int)$_POST['length'];
$search = $_POST['search']['value'] ?? '';

$where  = $search ? "WHERE name LIKE :s OR position LIKE :s" : "";
$params = $search ? [':s' => "%$search%"] : [];

$total    = $pdo->query("SELECT COUNT(*) FROM staff")->fetchColumn();
$filtered = $pdo->prepare("SELECT COUNT(*) FROM staff $where");
$filtered->execute($params);
$filtered = $filtered->fetchColumn();

$stmt = $pdo->prepare("SELECT * FROM staff $where LIMIT :len OFFSET :start");
$stmt->bindValue(':len',   $length, PDO::PARAM_INT);
$stmt->bindValue(':start', $start,  PDO::PARAM_INT);
foreach ($params as $k => $v) $stmt->bindValue($k, $v);
$stmt->execute();

echo json_encode([
    'draw'            => $draw,
    'recordsTotal'    => (int)$total,
    'recordsFiltered' => (int)$filtered,
    'data'            => $stmt->fetchAll(PDO::FETCH_ASSOC)
]);
```

---

## Optional Row Metadata

Include these keys in each row object for automatic behaviour:

| Key           | Effect                               |
| ------------- | ------------------------------------ |
| `DT_RowId`    | Sets `id` attribute on `<tr>`        |
| `DT_RowClass` | Adds CSS class to `<tr>`             |
| `DT_RowData`  | Attaches jQuery `.data()` to the row |
| `DT_RowAttr`  | Sets arbitrary attributes on `<tr>`  |

```json
{
    "DT_RowId": "row_42",
    "DT_RowClass": "highlight",
    "DT_RowData": { "pkey": 42 },
    "DT_RowAttr": { "data-status": "active" },
    "name": "Tiger Nixon",
    "salary": "$320,800"
}
```

---

## Common Mistakes & Fixes

| Symptom                          | Cause                                   | Fix                                                          |
| -------------------------------- | --------------------------------------- | ------------------------------------------------------------ |
| Empty table, no error            | Wrong `dataSrc`                         | Check network tab → response shape, set `dataSrc` correctly  |
| "Invalid JSON" error             | Server returning HTML error page        | Check server logs; ensure Content-Type is `application/json` |
| SSP ignores search/sort          | Not reading `columns`/`order` params    | Parse all SSP params on server                               |
| Table resets to page 1 on reload | Using `ajax.reload()` default           | Use `ajax.reload(null, false)` to keep page                  |
| CORS error                       | Cross-origin Ajax                       | Add `Access-Control-Allow-Origin` header server-side         |
| XSS warning                      | Echoing raw `draw` string               | Cast: `"draw": parseInt(draw)`                               |
| Wrong record count shown         | `recordsFiltered` not updated on search | Return correct filtered count, not total                     |

---

## Performance Tips

-   Set `deferRender: true` for large client-side datasets (renders DOM only when rows are visible)
-   Use SSP for any dataset over ~10k rows
-   Index database columns used in search/sort
-   For SSP, name columns with `columns.name` and use that for SQL ORDER BY (safer than index)
-   Avoid `render` functions that do heavy DOM work — use them sparingly

---

## See also

-   Full reference: https://datatables.net/reference/option/ajax
-   SSP examples: https://datatables.net/examples/server_side/
-   `ajax.dataSrc`: https://datatables.net/reference/option/ajax.dataSrc
-   `columns.data`: https://datatables.net/reference/option/columns.data
