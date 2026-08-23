# تقرير موحّد: تكرار دوال إنشاء الأعمدة في DataTable

> يدمج هذا التقرير تحليلين مستقلين لكود إنشاء الأعمدة المستخدَم في كل استدعاء لـ
> `initServerTable(...)` داخل المستودع (`data_table_column_duplication_audit.md` و
> `datatable_columns_dedup_report.md`). فحص التحليلان نفس ملفات `details.html` الإحدى عشر
> الموجودة تحت `src/templates/jobs_templates/` وكود JS المشترك في `src/static/js/data_table_ajax/`.
> لم يُعدَّل أي ملف مصدري في أيٍّ من التحليلين — هذا تقرير تحليل فقط.

---

## 1. النطاق والحقائق المتفق عليها

يتفق التحليلان على النقاط الجوهرية التالية:

-   **11 ملف HTML** تستدعي `initServerTable(...)` — والدالة `initServerTable` نفسها مركزية بالفعل
    (تعريف واحد في `src/static/js/data_table_ajax/table.js`) و**غير** مكررة.
-   توجد **16 دالة مستقلة لإنشاء الأعمدة**، كل واحدة معرَّفة داخل `<script>` مضمّن ضمن
    `{% block extra_js %}` في كل قالب. لا توجد أي منها حاليًا في وحدة مشتركة.
-   بما أن كل قالب يعرض صفحة مستقلة، فإن الدوال التي تحمل **نفس الاسم** (`createColumns`،
    `createTableColumns`، `createUpdatedColumns`، `createSkippedColumns`) لا تتعارض أثناء التشغيل —
    لكنها تبقى منطقًا مكررًا وخطرًا على قابلية الصيانة.
-   **عمود الترقيم `#`** (`{ data: null, render: (d,t,r,meta) => meta.row + 1 }`) هو أكبر مصدر تكرار
    منفرد، وهو منسوخ ولصيق في معظم دوال الأعمدة باستثناء دالتَي `download_main_files` اللتين تستخدمان
    عمدًا `data: 'template_id'` (معرّف ثابت من قاعدة البيانات، وليس ترقيم صف) ويجب **عدم** دمجهما في
    نفس الدالة المساعدة.
-   الدوال المساعدة للعرض المشتركة موجودة بالفعل ومُعاد استخدامها بشكل صحيح (وليست مكررة):
    `renderStatus`، `renderWikiLink`، `renderCommonsLink`، `renderCommonsFileLink` /
    `renderCommonsFileLinkShort`، `renderStep`، `diffLink`.

### ملاحظة حول اختلاف الأرقام بين التحليلين المصدريين

يختلف التحليلان قليلًا في عدّ تكرارات كتلة عمود `#`: أحدهما يذكر "17 من أصل 16" (وهو تناقض داخلي في
ذلك المستند نفسه)، والآخر يذكر "9 من أصل 10" في عنوان قسم ثم يسرد لاحقًا 11 دالة في موضع آخر. بمطابقة
جردَي الدوال في كلا التقريرين، الرقم الموثوق هو: **14 من أصل 16 دالة** تحتوي كتلة `meta.row + 1`
(كل الدوال باستثناء دالتَي `download_main_files` اللتين تستخدمان `template_id`). اعتمد الرقم "14"
للتخطيط؛ يبدو أن الأرقام "17" و"10" في المستندين الأصليين ناتجة عن أخطاء عدّ/تصنيف وليست خلافًا
جوهريًا في الحقائق.

---

## 2. الجرد الكامل (مدمج)

| #   | الملف / الدالة                                                                                                               | عدد الأعمدة | تُستخدم في الجداول                                                          | ملاحظات                                                     |
| --- | ---------------------------------------------------------------------------------------------------------------------------- | ----------- | --------------------------------------------------------------------------- | ----------------------------------------------------------- |
| 1   | `public/extract_files_translations/details.html`<br>`createTableColumns(show_download, show_nested, err_colmn, show_status)` | 7           | files_success، files_processed، files_failed (+ skipped معطّل بتعليق)       | `#`، File، Status، Download، Translations، Languages، Error |
| 2   | `public/copy_svg_langs/details.html`<br>`createTableColumns(show_download, show_nested, err_colmn, show_status)`             | 10          | files_success، files_processed، files_skipped، files_failed                 | نفس توقيع الدالة رقم 1، بأعمدة وسطى مبنية على steps         |
| 3   | `admin/crop_main_files/details.html`<br>`createColumns()`                                                                    | 12          | pages_uploaded، pages_updated، files_processed، pages_skipped، pages_failed | تستخدم `renderCropTemplate` المحلية                         |
| 4   | `admin/add_svglanguages_template/details.html`<br>`createProcessedColumns()`                                                 | 6           | pages_processed، pages_success، pages_failed                                | Template + خطوات النص/الحفظ                                 |
| 5   | `admin/add_svglanguages_template/details.html`<br>`createSkippedColumns()`                                                   | 3           | pages_skipped                                                               | `#`، Title، Reason (`reason\|\|error\|\|msg`)               |
| 6   | `admin/update_owid_charts/details.html`<br>`createUpdatedColumns()`                                                          | 7           | updated_charts                                                              | فروقات حقول رسم OWID البياني                                |
| 7   | `admin/update_owid_charts/details.html`<br>`createFailedColumns()`                                                           | 3           | failed_charts                                                               | `#`، Slug، Error                                            |
| 8   | `admin/update_owid_charts/details.html`<br>`createSkippedColumns()`                                                          | 3           | skipped_charts                                                              | `#`، Slug، Reason (`skip_reason`)                           |
| 9   | `admin/collect_templates_data/details.html`<br>`createAddedColumns()`                                                        | 2           | pages_added                                                                 | `#`، Title (عبر `renderOwidTemplate`)                       |
| 10  | `admin/collect_templates_data/details.html`<br>`createUpdatedColumns()`                                                      | 10          | pages_updated، pages_skipped، pages_failed                                  | حقول ملف/سنة/مصدر القالب                                    |
| 11  | `admin/rename_owid_pages/details.html`<br>`createColumns(old_title_label, new_title_label)`                                  | 4           | pages_renamed، pages_skipped، pages_redirected، pages_failed                | الدالة الوحيدة المُعامَلة (parameterized)                   |
| 12  | `admin/create_owid_pages/details.html`<br>`createColumns()`                                                                  | 7           | pages_created، pages_updated، pages_processed، pages_skipped، pages_failed  | تستخدم `renderOwidTemplate` المحلية                         |
| 13  | `admin/download_main_files/details.html`<br>`createDownloadedColumns()`                                                      | 4           | files_downloaded                                                            | `#` = `template_id` (وليس ترقيم صف)                         |
| 14  | `admin/download_main_files/details.html`<br>`createResultColumns()`                                                          | 4           | files_skipped، files_failed                                                 | `#` = `template_id`؛ Reason (`reason\|\|error`)             |
| 15  | `admin/add_lang_categories_to_owid_pages/details.html`<br>`createColumns()`                                                  | 12          | pages_success، pages_skipped، pages_failed                                  | سلسلة خطوات اللغة/التصنيف                                   |
| 16  | `admin/fix_nested_main_files/details.html`<br>`createTableColumns(show_reason, show_result)`                                 | 5           | pages_success، pages_failed، pages_skipped                                  | أعمدة Result/Reason شرطية                                   |

**الإجمالي: 16 دالة موزعة على 11 ملفًا.**

---

## 3. الأنماط المكررة / الفائضة

### 3.2 عمود ترقيم الصف `#` — مكرر في 14 من أصل 16 دالة (ثقة عالية)

نفس التعبير حرفيًا (`{ data: null, title: '#', render: (d,t,r,meta) => meta.row + 1 }`، وأحيانًا
بصيغة دالة مسمّاة بدل arrow function). **استخراجه إلى `indexColumn()`** في `macros.js`. يجب أن تحتفظ
دالتا `download_main_files` بـ `data: 'template_id'` — لا تُدمَج هذه الحالة مع البقية.

### 3.3 عمود "السبب / رسالة الخطأ" — مكرر 5 مرات بأربع سلاسل احتياطية مختلفة قليلًا (ثقة متوسطة)

يظهر في `add_svglanguages_template` (skipped)، و`update_owid_charts` (skipped)، و`download_main_files`
(result)، و`fix_nested_main_files`، و`collect_templates_data` (عمود "Msg")، وكل واحد يقرأ توليفة
مختلفة من `reason || error || msg || message`. **استخراج دالة `messageColumn(title, dataKey)`
معاملة** تتحقق من الحقول الأربعة بترتيب ثابت.

### 3.4 عمود "العنوان" عبر `renderCommonsLink` — مكرر 6 مرات (ثقة متوسطة)

نفس دالة العرض، ويختلف فقط مفتاح `data` وتسمية `title`، في `add_svglanguages_template`،
و`collect_templates_data`، و`rename_owid_pages` (مرتين)، و`download_main_files`،
و`add_lang_categories`، و`fix_nested_main_files`. **استخراج `titleColumn(dataKey, label)`.**

### 3.5 عمود رابط "الملف" — شبه مكرر 4 مرات (ثقة متوسطة)

تختلف `renderCommonsFileLink` و`renderCommonsFileLinkShort` فقط في التسمية الافتراضية، وتُستخدمان في
`extract` و`copy` و`crop` و`download` و`fix_nested`. **دمجهما في دالة عرض واحدة بمعامل `label`**، ثم
استخراج `fileLinkColumn(dataKey, label)`.

### 3.6 `createTableColumns` (extract) ↔ `createTableColumns` (copy) — تداخل بنيوي كبير (ثقة متوسطة)

نفس التوقيع ونفس الهيكل الاستهلالي والختامي (`#`، File، Status، Download، Error)؛ تختلف فقط الأعمدة
الوسطى (extract: Translations/Languages؛ copy: أعمدة مبنية على steps مثل Nested/Inject/Upload/
Translations). **استخراج `baseFileColumns(opts)`**، مع إضافة كل صفحة لأعمدتها الوسطى الخاصة. لا يجب
دمجهما في دالة واحدة غير شرطية — فالأعمدة الوسطى مختلفة فعليًا.

### 3.7 `createSkippedColumns` (svglang) ↔ `createSkippedColumns` (charts) — نفس الشكل، بيانات مختلفة (ثقة متوسطة)

كلاهما `#` + عمود رابط + Reason، لكن كيان الرابط (عنوان Commons مقابل slug في OWID) وحقل السبب
(`reason||error||msg` مقابل `skip_reason`) مختلفان. **معاملتها ضمن دالة مشتركة
`skippedColumns({ linkData, linkRender, reasonData })`.**

### 3.8 `add_svglanguages_template::createProcessedColumns` ↔ `create_owid_pages::createColumns` — تداخل جزئي (ثقة متوسطة)

يشتركان في ثلاثية Template + "Load Text" + "Generate Text" تصبح متطابقة بنيويًا بعد إصلاح البند 3.1.
**استخراج `templateStepColumns()`** لهذه الثلاثية المشتركة، مع إضافة كل صفحة لبقية خطواتها الخاصة.

### 3.9 دوال `update_owid_charts` الثلاث تشترك في عمود Slug (ثقة متوسطة)

تبدأ الدوال `createUpdatedColumns` و`createFailedColumns` و`createSkippedColumns` في نفس الملف كلها
بـ `#` + `Slug → renderOwidSlug`. **استخراج `slugColumn()`**؛ وتحتفظ كل دالة فقط بأعمدتها المتبقية
المختلفة.

### 3.10 تعارض الأسماء — نفس المعرّف، أعمدة مختلفة (ثقة منخفضة — تسمية فقط، وليس دمج منطق)

-   `createColumns()` معرَّفة في 4 ملفات (`crop_main_files`، `rename_owid_pages`، `create_owid_pages`،
    `add_lang_categories_to_owid_pages`) — وكل مجموعة أعمدة مختلفة جوهريًا عن الأخرى.
-   `createUpdatedColumns()` معرَّفة في `update_owid_charts` و`collect_templates_data` — بيانات رسوم
    بيانية مقابل بيانات قوالب، غير مترابطة.
-   `createTableColumns()` معرَّفة في `extract` و`copy` و`fix_nested` — توقيعات/أعمدة مختلفة.
-   `createSkippedColumns()` معرَّفة في `add_svglanguages_template` و`update_owid_charts` — انظر البند 3.7.

**التوصية: إعادة التسمية فقط، دون الدمج.** مثل: `cropColumns()`، `renameColumns()`،
`createOwidPagesColumns()`، `collectTemplateUpdatedColumns()`، `fixNestedColumns()`.

---

## 4. دوال يجب عدم دمجها

1. تطبيقات `createColumns()` الأربعة — رغم تشارك الاسم، مجموعات أعمدتها مختلفة جوهريًا (خطوات
   القص/المقارنة مقابل إنشاء صفحة جديدة مقابل خطوات SVG/اللغة/التصنيف مقابل العنوان القديم/الجديد).
   إعادة تسمية فقط.
2. `createUpdatedColumns` (الرسوم البيانية) مقابل `createUpdatedColumns` (القوالب) — مجالان غير
   مترابطين (فروقات وقت/متغير الرسم البياني مقابل بيانات ملف/سنة/مصدر القالب).
3. `createSkippedColumns` (svglang) مقابل `createSkippedColumns` (charts) — كيان رابط وحقل سبب
   مختلفان؛ استخدم المعاملة (parameterize) بدل الدمج الحرفي.
4. عمود `#` في `download_main_files` (`template_id`) — معرّف ثابت من قاعدة البيانات وليس ترقيم صف؛
   يبقى منفصلًا عن `indexColumn()`، أو يُضاف متغيّر صريح `idIndexColumn('template_id')` إذا رُغب بذلك.
5. `createTableColumns` (fix_nested) مقابل extract/copy — توقيع ومجموعة أعمدة مختلفة؛ يمكن اتباع
   قواعد تسمية/هيكلة مشتركة إن أمكن، لكن ليست حالة دمج مباشر.

---

## 5. الهيكل المستهدف المقترح

يتفق التحليلان المصدريان على نفس الفكرة الأساسية — مركزة أشكال الأعمدة والدوال المساعدة المتكررة في
وحدات مشتركة — لكنهما يقترحان مستويين مختلفين من التفصيل. تعتمد هذه التوصية الموحدة التقسيم الأكثر
تفصيلًا (الأقرب إلى `datatable_columns_dedup_report.md`) لأنه يزيل تكرارًا أكبر، مع الإبقاء على
التجميع الأبسط من `data_table_column_duplication_audit.md` كبديل أخف قابل للقبول.

**`src/static/js/data_table_ajax/macros.js`** (مشتركة/عامة بالفعل) — إضافة:

-   `indexColumn(title = '#')` — خلية ترقيم الصف (البند 3.2)
-   `titleColumn(dataKey, label)` — خلية عنوان برابط Commons (البند 3.4)
-   `fileLinkColumn(dataKey, label)` — خلية رابط ملف موحدة، تحل محل الانقسام بين
    `renderCommonsFileLink`/`renderCommonsFileLinkShort` (البند 3.5)
-   `messageColumn(title, dataKey)` — خلية سبب/خطأ احتياطية (البند 3.3)
-   `slugColumn()` — خلية رابط slug في OWID (البند 3.9)
-   `templateColumn(dataKey, label)` — خلية عنوان قالب OWID، تحل محل `renderOwidTemplate`/

**وحدة مشتركة جديدة `src/static/js/data_table_ajax/column_helpers.js`** (تُحمَّل في `base.html`
بجانب `table.js`/`macros.js`) — إضافة:

-   `baseFileColumns(opts)` — الهيكل المشترك `#`/File/Status/Download/Error لـ extract وcopy (البند 3.6)
-   `templateStepColumns(opts)` — ثلاثية Template/Load Text/Generate Text المشتركة (البند 3.8)
-   `skippedColumns({ linkData, linkRender, reasonData })` — تغطي جداول skipped في svglang والرسوم
    البيانية (البند 3.7)
-   اختياري: `idIndexColumn(dataKey)` لمتغيّر `template_id` في `download_main_files`

**قوالب الصفحات:** الإبقاء فقط على استدعاءات رفيعة (thin callers) تمرر مفاتيح البيانات/الدوال
الخاصة بكل صفحة إلى الدوال المساعدة المشتركة. إعادة تسمية الأسماء العامة المتعارضة
(`createColumns`، `createTableColumns`، `createUpdatedColumns`، `createSkippedColumns`) بأسماء خاصة
بكل صفحة لمزيد من الوضوح (البند 3.10). أما دوال العرض المحلية الفريدة فعلًا
(`renderCropTemplate`، `renderOwidSlug`، `renderOwidVariableLink`) فتبقى محلية.

هذا يحافظ على `initServerTable` كنقطة الربط الوحيدة، ويمركز شكل الأعمدة والدوال المساعدة المشتركة،
ويزيل تعارض الأسماء دون دمج جداول مختلفة السلوك.

---

## 6. أثر عملية الترحيل (Migration)

| الملف                                            | الإجراء                                                                                                                                  |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `macros.js`                                      | إضافة `indexColumn`، `titleColumn`، `fileLinkColumn`، `messageColumn`، `slugColumn`، `templateColumn`؛ توحيد دوال رابط الملف وعنوان OWID |
| ملف جديد `column_helpers.js`                     | إضافة `baseFileColumns`، `templateStepColumns`، `skippedColumns`                                                                         |
| `base.html`                                      | إضافة وسم `<script>` لتحميل `column_helpers.js` قبل أي قالب يستخدمه                                                                      |
| `extract_files_translations/details.html`        | استبدال `createTableColumns` بـ `baseFileColumns` + إضافات                                                                               |
| `copy_svg_langs/details.html`                    | استبدال `createTableColumns` بـ `baseFileColumns` + إضافات                                                                               |
| `crop_main_files/details.html`                   | `createColumns` ← `indexColumn` + دوال مشتركة؛ إعادة تسمية الدالة                                                                        |
| `add_svglanguages_template/details.html`         | `createProcessedColumns`/`createSkippedColumns` ← دوال مشتركة                                                                            |
| `update_owid_charts/details.html`                | 3 دوال ← `indexColumn` + `slugColumn` + `messageColumn`                                                                                  |
| `rename_owid_pages/details.html`                 | `createColumns` ← `indexColumn` + `titleColumn`؛ إعادة تسمية الدالة                                                                      |
| `create_owid_pages/details.html`                 | `createColumns` ← دوال قالب مشتركة؛ حذف `renderOwidTemplate` المحلية؛ إعادة تسمية الدالة                                                 |
| `download_main_files/details.html`               | دالتان ← `titleColumn`/`messageColumn`، مع الإبقاء على ترقيم `template_id`                                                               |
| `add_lang_categories_to_owid_pages/details.html` | `createColumns` ← `indexColumn` + `titleColumn` + أعمدة ملف/خطوة مشتركة؛ إعادة تسمية الدالة                                              |
| `fix_nested_main_files/details.html`             | `createTableColumns` ← `indexColumn` + `titleColumn` + `fileLinkColumn` + `messageColumn`؛ إعادة تسمية الدالة                            |

**لا حاجة لتعديل أي من مواضع استدعاء `initServerTable(...)` الإحدى عشر نفسها** — تبقى معرّفات الجداول
وعدد الاستدعاءات كما هي؛ يُعاد بناء أجسام دوال الأعمدة فقط.

---

## 7. ملخص الحذف / الدمج

| الفئة                                                                                                 | عدد التكرارات | الإجراء                                |
| ----------------------------------------------------------------------------------------------------- | ------------- | -------------------------------------- |
| كتل عمود الترقيم `#`                                                                                  | 14            | ← دالة مشتركة واحدة `indexColumn()`    |
| كتل عمود السبب/رسالة الخطأ                                                                            | 5             | ← دالة مشتركة واحدة `messageColumn()`  |
| عمود العنوان عبر `renderCommonsLink`                                                                  | 6             | ← دالة مشتركة واحدة `titleColumn()`    |
| كتل عمود رابط الملف                                                                                   | 4             | ← دالة مشتركة واحدة `fileLinkColumn()` |
| `renderCommonsFileLink` / `renderCommonsFileLinkShort`                                                | 2             | ← دالة عرض موحدة واحدة                 |
| أعمدة الأساس في `extract` مقابل `copy`                                                                | 2             | ← دالة مشتركة `baseFileColumns()`      |
| ثلاثية Template/Load Text/Generate Text                                                               | 2             | ← دالة مشتركة `templateStepColumns()`  |
| `createSkippedColumns` × 2                                                                            | 2             | ← دالة مشتركة `skippedColumns()`       |
| تعارض الأسماء (`createColumns`، `createTableColumns`، `createUpdatedColumns`، `createSkippedColumns`) | 11 تعريفًا    | إعادة تسمية بأسماء فريدة خاصة بكل مجال |

**الأثر الصافي التقديري:** يتقلّص نحو 30 كتلة عمود مضمّنة شبه متطابقة إلى نحو 8–9 دوال مساعدة قابلة
لإعادة الاستخدام، مما يزيل ما يقارب 85–100+ سطر من الإعدادات المكررة ويُنهي جميع مجموعات الأسماء
الأربع المتعارضة — دون تغيير أي سلوك ظاهر لأي جدول.

---

## 8. قائمة التحقق النهائية

-   [ ] تم حصر جميع مواضع استدعاء `initServerTable(` الإحدى عشر.
-   [ ] تم حصر جميع دوال إنشاء الأعمدة الست عشرة.
-   [ ] تمت مراجعة كل حالة تكرار/شبه تكرار أعلاه مقابل السلوك الفعلي قبل الدمج.
-   [ ] تم تحديد مواضع الاستدعاء قبل الحذف — لا حاجة لتغيير معاملات `initServerTable`.
-   [ ] الدوال المختلفة سلوكيًا (البند 4) **لم** تُدمَج خطأً.
-   [ ] الحفاظ على ترقيم `template_id` في `download_main_files` دون طيّه ضمن `indexColumn()`.
-   [ ] تحميل الدوال المساعدة المشتركة الجديدة بشكل صحيح عبر `base.html` قبل أي قالب يستخدمها.
-   [ ] فحص انحدار بصري/سلوكي على جميع صفحات تفاصيل المهام الإحدى عشر بعد إعادة الهيكلة (ترتيب
        الأعمدة، أعلام الظهور، وقيم `#`/الترقيم محفوظة).

---

## 9. الخلاصة

يصل التحليلان المصدريان إلى نفس الاستنتاج عبر مسارين مختلفين: تحتوي الدوال الست عشرة لإنشاء الأعمدة
عبر القوالب الإحدى عشر على كمّ كبير من المنطق المنسوخ واللصيق (وليس فقط المتشابه بالاسم) — أبرزها دالة
مساعدة تكرارية تامة واحدة وكتلة ترقيم صف مكررة 14 مرة — ويمكن دمج ذلك في 6 دوال خلية مشتركة داخل
`macros.js` بالإضافة إلى 3 دوال بناء هيكل جدول مشتركة في وحدة جديدة `column_helpers.js`، دون الحاجة
لأي تغيير في مواضع استدعاء `initServerTable`، ودون أي مخاطرة على مجموعات الدوال الأربع التي تتشارك
الاسم فقط دون السلوك.
