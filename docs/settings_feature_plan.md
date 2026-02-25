# خطة تطوير ميزة إدارة الإعدادات (Settings Management) للوحة التحكم

تهدف هذه الخطة إلى إضافة قسم مركزي في لوحة التحكم (Admin Panel) لإدارة الإعدادات المتغيرة للتطبيق بكل سهولة، بحيث يتم الاعتماد على قاعدة البيانات بدلاً من كتابة الإعدادات برمجياً (Hardcoding).

## الخطوة 1: تحديث بنية قاعدة البيانات

- تنفيذ ال SQL Script لإنشاء جدول الإعدادات الجديد الذي سيتضمن هيكلة المفاتيح (keys) وأنواع القيم (types).
- الاستعلام:

```sql
CREATE TABLE IF NOT EXISTS `settings` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `key` VARCHAR(190) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` VARCHAR(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` TEXT COLLATE utf8mb4_unicode_ci NULL,
  `value_type` ENUM('boolean','string','integer','json')
      COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'boolean',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_key` (`key`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
```

## الخطوة 2: تحديث القائمة الجانبية (Sidebar)

- تحديد مسار ملف القلاب (Template) الخاص بالقائمة الجانبية للوحة التحكم.
- إضافة قسم (Group Element) جديد للروابط باسم **"Settings"**.
- إدراج نقطة وصول (Menu Item/Link) داخله تحمل الاسم **"Settings"** لتقوم بتوجيه مدير النظام (Admin) إلى المسار الجديد (مثل `/admin/settings`).

## الخطوة 3: تطوير الوظائف البرمجية (Backend Controllers & Routes)

- **مسار العرض (GET Route)**: إنشاء دالة لجلب جميع السجلات المعرفة مسبقًا من جدول `settings`، بالإضافة إلى إرسالها لملف القالب الجديد.
- **مسار الإضافة (Create Route)**: نقطة لاستقبال طلبات إضافة إعداد جديد وتمرير ال (key, title, value_type, value) وحفظه في الجدول، مع ضمان عدم تكرار ال `key`.
- **مسار التحديث (Update Route)**: مسار لاستقبال التحديثات من واجهة الإعدادات. يقوم بمعالجة الحقول بحسب نوعها وتحديث ال `value` لكل `key` موجود في الجدول.

## الخطوة 4: تطوير واجهة الإعدادات (Settings Page Frontend)

- إنشاء ملف قالب مخصص للإعدادات (مثلاً `settings.html`).
- **نموذج الإضافة (Add New Setting)**:
  - حقول إدخال لإضافة (Key الإعداد المجرد, Title المعروض للإدارة).
  - قائمة منسدلة (Drop-down) لاختيار نوع القيمة (`boolean`, `string`, `integer`, `json`).
- **قائمة الإعدادات الحالية (List & Edit Settings)**:
  - سيتم جلب الإعدادات في الواجهة وعرض كل `title` بجواره حقل تعديل ال `value` يتغير نوعه ديناميكياً بناءً على حقل `value_type`:
    - **للنوع `boolean`**: استخدام أزرار التبديل عن طريق `Bootstrap form-switch` كالتالي:
      ```html
      <div class="form-check form-switch">
        <input
          class="form-check-input"
          type="checkbox"
          id="setting_..."
          checked
        />
      </div>
      ```
    - **للنوع `string`**: `<input type="text" class="form-control" />`
    - **للنوع `integer`**: `<input type="number" class="form-control" />`
    - **للنوع `json`**: `<textarea class="form-control"></textarea>`

## الخطوة 5: تكامل الإعدادات والتطبيق (System Integration)

- **التحميل عند البدء (Bootstrapping)**: جلب جميع الإعدادات من قاعدة البيانات أثناء تحميل التطبيق وحقنها في المكونات المركزية.
- **إضافة للإعدادات المركزية (Config)**: دمج هذه الإعدادات مباشرة في مصفوفة/كائن `config` الخاص بالتطبيق (مثلاً في جزء مخصص مثل `config.settings` أو إضافتها لملف الإعدادات) لكي يمكن الوصول لها واستخدامها بسهولة وسرعة من أي مكان في الكود دون الحاجة لإجراء استعلامات إضافية.
- **التخزين المؤقت (Caching)**: تفعيل نظام التخزين المؤقت للإعدادات بحيث يتم قراءتها من ה Cache أثناء تشغيل التطبيق بدلاً من الجدول باستمرار، ولا يُفرَّغ التخزين (Cache Invalidation) إلا بعد قيام الأدمن بالتعديل في صفحة الإعدادات وحفظها.
