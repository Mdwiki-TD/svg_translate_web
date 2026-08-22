
اكتب خطة بالانجليزي لتعديل كافة ملفات:

src/templates/jobs_templates/admin_templates/<job_type>/details.html

لتستخدم DataTables ajax

عبر

```js
function initServerTable(
    tableId,
    columns,
)
```
من
src/static/js/data_table_ajax/table.js
src/static/js/data_table_ajax/macros.js


أمثلة:

```
src/templates/jobs_templates/public/copy_svg_langs/details_new.html
src/templates/jobs_templates/public/extract_files_translations/details_new.html
```


لنبدأ مثلًا بـ pages_skipped_table
حيث أنه الأبسط ويعرض فقط 3 صفوف

```html
<th>#</th>
<th>Title</th>
<th>Reason</th>
```
