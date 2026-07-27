# دراسة جدوى وخطة شاملة للانتقال من استخدام الخيوط (Threads) إلى Celery

تستعرض هذه الوثيقة دراسة جدوى تفصيلية وبنية برمجية مقترحة للانتقال بنظام المعالجة الخلفية (Background Job Processing) في تطبيق **SVG Translate Web** من استخدام الخيوط المحلية (`threading.Thread`) إلى نظام إدارة المهام الموزع **Celery**، مع التركيز على بيئة التشغيل الخاصة بـ **Wikimedia Toolforge**.

---

## 1. المقدمة والخلفية العامة (Introduction)

تطبيق **SVG Translate Web** هو تطبيق مبني على Flask لتسهيل عملية نقل الترجمات البرمجية لملفات SVG عبر مستودع ويكيبيديا كومنز (Wikimedia Commons). يتطلب التطبيق تشغيل عمليات خلفية طويلة المدى (مثل تنزيل الملفات، ومعالجة XML/SVG، واستدعاء واجهات برمجة تطبيقات ميدياويكي مع التعامل مع قيود معدل الطلبات Rate-limiting).

حالياً، تعتمد المنظومة على خيوط برمجية محلية (`Daemon Threads`) عبر مكتبة `threading` الخاصة بلغة بايثون لتنفيذ هذه المهام بشكل غير متزامن. وعلى الرغم من أن هذا الأسلوب بسيط ولا يتطلب خوادم أو خدمات إضافية، إلا أنه يفرض قيوداً جوهرية على مستويات التدرج والاستقرار والأمان، خاصة عند التشغيل ضمن بيئة حاويات مثل Kubernetes على Wikimedia Toolforge.

---

## 2. تحليل البنية الحالية والعيوب (Current Architecture & Limitations)

### 2.1 البنية الحالية
عندما يطلب المستخدم بدء مهمة خلفية (مثلاً: `collect_templates_data` أو `crop_main_files`):
1. يستقبل خادم Flask الطلب ويقوم بإنشاء سجل للمهمة في قاعدة البيانات (`JobRecord`) بحالة `pending`.
2. يتم تشغيل خيط محلي (`threading.Thread`) كخيط خفي (`daemon=True`) يلتف حول الدالة المطلوبة.
3. يقوم الخيط بتهيئة سياق Flask (`app_context`) للوصول إلى قاعدة البيانات والخدمات المشتركة.
4. يتم تتبع الإلغاء محلياً عبر قاموس مشترك في الذاكرة `JOBS_CANCEL_EVENTS` يحتوي على كائنات `threading.Event` لكل مهمة، أو عالمياً عبر فحص قاعدة البيانات ووجود ملفات `.cancelled`.

### 2.2 عيوب البنية الحالية
1. **تأثير قفل بايثون العام (GIL - Global Interpreter Lock):**
   تتشارك جميع الخيوط في عملية بايثون واحدة (OS Process). عند تنفيذ مهام كثيفة الاستهلاك للمعالج (مثل تحليل SVG كبير ومعالجة نصوص XML)، يتسبب قفل الـ GIL في إعاقة الأداء الفعلي للخادم ومشاركة المعالج، مما قد يؤدي إلى بطء في استجابة واجهة المستخدم الرسومية لـ Flask للمستخدمين الآخرين.
2. **غياب عزل العمليات (Lack of Process Isolation):**
   أي خطأ قاتل غير معالج (كاستهلاك مفرط للذاكرة - Out Of Memory، أو انهيار في المكتبات المبنية على C مثل `lxml`) سيؤدي إلى انهيار العملية بأكملها (Process Crash)، وبالتالي توقف خادم الويب بالكامل عن العمل وفقدان جميع الخيوط الأخرى الجارية.
3. **فقدان المهام عند إعادة تشغيل الخادم:**
   بما أن المهام تُخزن وتُدار في ذاكرة العملية النشطة فقط، فإن أي عملية إعادة نشر (Deployment) للتطبيق، أو إعادة تشغيل حاوية Kubernetes في Toolforge، ستؤدي فوراً إلى قتل جميع المهام الجارية دون إمكانية استئنافها أو إعادة محاولتها تلقائياً.
4. **صعوبة التدرج الأفقي (Horizontal Scaling):**
   لا يمكن توزيع المهام على خوادم أو حاويات متعددة. يجب أن تُنفذ المهمة على نفس الخادم الذي استقبل طلب الويب. في بيئة Toolforge، يمنعنا هذا من الاستفادة من توزيع الأحمال عبر حاويات متعددة (Replicas).
5. **تعقيد آلية الإلغاء والتنسيق:**
   إلغاء المهام يتطلب التحقق دورياً من الذاكرة المحلية أو فحص القرص الصلب بحثاً عن ملفات الإلغاء، وهو أمر غير عملي ويسبب عبئاً إضافياً على نظام الملفات.

---

## 3. البنية المقترحة باستخدام Celery (Proposed Architecture)

يتكون نظام **Celery** من ثلاثة أجزاء رئيسية:
1. **المنتج (Producer):** تطبيق Flask، الذي يقوم بإرسال المهام إلى الطابور.
2. **الوسيط (Message Broker):** خادم وسيط لتخزين وتمرير الرسائل (مثل **Redis** أو **RabbitMQ**).
3. **المستهلك (Worker):** عمليات بايثون مستقلة تماماً (Celery Workers) تقوم بسحب المهام من الوسيط وتنفيذها.

```
┌─────────────────┐       توجيه المهمة        ┌────────────────┐
│   Flask App     ├──────────────────────────>│ Message Broker │
│   (Producer)    │  celery_app.send_task()  │ (Redis/RMQ)    │
└─────────────────┘                           └───────┬────────┘
                                                      │
                                                      │ سحب المهام
                                                      v
                                              ┌────────────────┐
                                              │ Celery Worker  │
                                              │   (Consumer)   │
                                              └───────┬────────┘
                                                      │
                                                      v
                                              ┌────────────────┐
                                              │  قاعدة البيانات │
                                              │  ونظام الملفات  │
                                              └────────────────┘
```

### 3.1 ملاءمة البيئة لـ Wikimedia Toolforge
تدعم منصة **Wikimedia Toolforge** تشغيل الخدمات المستمرة والمهام الخلفية بكفاءة عالية:
* **الوسيط (Broker):** يمكن استخدام خادم **Redis** المتاح كخدمة مشتركة أو تشغيل حاوية Redis مخصصة داخل بيئة الأدوات (Toolforge Kubernetes).
* **العمال (Workers):** يتم تشغيل عمال Celery كخدمة مستمرة (Continuous Service) عبر حاويات Kubernetes مستقلة باستخدام ملف إعداد `service.template` مخصص.
* **قاعدة البيانات ونظام الملفات:** يتشارك تطبيق الويب وعمال Celery نفس قاعدة البيانات المشتركة (ToolsDB) ونظام الملفات المشترك عبر المجلدات الرئيسية للأداة (`/data/project/copy-svg-langs/`).

---

## 4. دراسة الجدوى: المميزات والعيوب (Feasibility Analysis: Pros & Cons)

### 4.1 المميزات والفوائد الجوهرية (Pros)

| الميزة | التفاصيل والفوائد لمشروع SVG Translate |
| :--- | :--- |
| **استقرار كامل للويب** | فصل تام بين عمليات معالجة الويب وعمليات المعالجة الخلفية. انهيار أي مهمة أو استهلاكها للذاكرة لن يؤثر على تصفح المستخدمين. |
| **تجاوز قفل GIL** | يقوم Celery بتشغيل العمال كعمليات منفصلة (Forked Processes)، مما يتيح استغلالاً حقيقياً لجميع النوى (Multi-core CPUs) المتوفرة في الخادم لعمليات الـ XML والـ SVG. |
| **إعادة المحاولة التلقائية (Autoretry)** | إمكانية إعداد المهام لتعيد المحاولة تلقائياً في حال فشل طلبات ويكيبيديا كومنز بسبب حدود الـ Rate Limit أو مشاكل الشبكة المؤقتة. |
| **التدرج المرن (Scalability)** | إمكانية زيادة عدد العمال (Workers) بسهولة عبر سطر أوامر Toolforge لمعالجة آلاف المهام بالتوازي دون إرهاق خادم الويب. |
| **المراقبة والتحكم (Monitoring)** | إمكانية دمج أداة **Flower** لمراقبة المهام في الوقت الفعلي، ومعرفة نسبة التقدم، وإلغاء المهام من لوحة تحكم رسومية متميزة. |
| **جدولة المهام (Celery Beat)** | استبدال جدولة المهام التقليدية (Cron Jobs) بجدولة مركزية مرنة لإعادة فحص القوالب وتحديث بيانات الرسوم البيانية دورياً. |

### 4.2 التحديات والعيوب (Cons & Challenges)

1. **زيادة استهلاك الموارد (Resource Overhead):**
   يتطلب تشغيل خادم Redis وتشغيل عمليات Celery Worker مستقلة مساحة ذاكرة إضافية (RAM) ضمن حدود الـ Quotas المحددة للأداة في Toolforge (بشكل عام، تمنح Toolforge موارد جيدة للخدمات الخلفية تصل إلى عدة جيجابايت).
2. **زيادة تعقيد البنية التحتية:**
   إضافة Redis كجزء ثالث في النظام يتطلب مراقبة مستمرة وضمان تشغيله الدائم.
3. **تحديث إدارة السياق (Context Management):**
   يجب إعادة تهيئة تطبيق Flask وسياق قاعدة البيانات ونموذج الاتصال ميدياويكي (MwClient) بشكل صحيح داخل العمال المستقلين لكل مهمة.

---

## 5. خطة الانتقال البرمجية بالتفصيل (Migration Blueprint)

لتطبيق هذا الانتقال بأمان ودون تعطيل الخدمة الحالية، يُقترح اتباع الخطوات التالية:

### الخطوة 1: تثبيت الحزم البرمجية الجديدة
إضافة المكتبات المطلوبة إلى ملف `requirements.txt`:
```ini
celery>=5.3.0
redis>=5.0.0
```

### الخطوة 2: تهيئة وتكامل Celery مع Flask
إنشاء ملف تهيئة مخصص لـ Celery داخل المجلد الرئيسي للتطبيق (مثلاً: `src/main_app/extensions/celery_init.py`):

```python
from __future__ import annotations

from celery import Celery
from flask import Flask

def make_celery(app: Flask) -> Celery:
    celery = Celery(
        app.import_name,
        backend=app.config.get("CELERY_RESULT_BACKEND"),
        broker=app.config.get("CELERY_BROKER_URL")
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
```

إضافة إعدادات الاتصال في `src/main_app/config/flask_config.py`:
```python
# إعدادات التطوير المحلي
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6373/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6373/0")
```

### الخطوة 3: تحويل مشغل المهام (Job Trigger)
تحديث `src/main_app/jobs_workers/jobs_worker.py` ليرسل المهمة إلى Celery بدلاً من إنشاء خيط محلي:

```python
# في البنية الحالية:
# thread = threading.Thread(target=_runner, args=...)
# thread.start()

# البنية المقترحة:
from .tasks import run_background_job_task

def start_job(
    auth_payload: dict[str, Any] | None,
    job_type: str,
    args: dict[str, Any] | None = None,
) -> int:
    # 1. إنشاء سجل المهمة في قاعدة البيانات للحصول على المعرف ID
    job = JobsService().create_job(job_type, auth_payload.get("username"))

    # 2. إرسال المهمة إلى Celery بشكل غير متزامن
    run_background_job_task.delay(
        job_id=job.id,
        auth_payload=auth_payload,
        job_type=job_type,
        args=args
    )
    return job.id
```

### الخطوة 4: كتابة مهمة Celery الموحدة (Celery Task Wrapper)
إنشاء ملف `src/main_app/jobs_workers/tasks.py` ليكون الجسر بين Celery والـ Workers الحاليين:

```python
from __future__ import annotations

from celery import shared_task
from flask import current_app
from .jobs_worker import load_job_data

@shared_task(bind=True)
def run_background_job_task(self, job_id: int, auth_payload: dict, job_type: str, args: dict | None = None):
    """مهمة Celery المشتركة لتشغيل جميع أنواع المهام الخلفية."""
    job_data = load_job_data(job_type)
    if not job_data or not job_data.job_callable:
        raise ValueError(f"Unknown job type: {job_type}")

    # الحصول على دالة التشغيل
    target_func = job_data.job_callable

    # استخدام معرف مهمة Celery لتتبعها إذا لزم الأمر
    celery_task_id = self.request.id

    # تشغيل الدالة مع تمرير السياق والموانع
    # يمكننا استخدام ميزة التحقق من الإلغاء عبر سياق Celery أو كائن الإلغاء
    target_func(
        job_id=job_id,
        user=auth_payload,
        cancel_event=None,  # سيتم استبداله بفحص إلغاء Celery أو ملفات الإلغاء
        args=args,
    )
```

### الخطوة 5: تحديث منطق الإلغاء (Cancellation)
بما أن المهام تعمل في عمليات منفصلة، لا يمكن استخدام كائن `threading.Event` المشترك في الذاكرة. بدلاً من ذلك، سنعتمد كلياً على الآليات الفعالة المتوفرة حالياً بالبنية الأساسية لـ `BaseObjectsJobWorker`:
1. **فحص قاعدة البيانات (`check_db=True`):** فحص عمود الإلغاء في سجل `JobRecord` دورياً عبر `JobsService`.
2. **ملف الإلغاء (`result_file_cancelled`):** التحقق من وجود ملف `.cancelled` الخاص بالمهمة على القرص المشترك.
3. **أمر الإلغاء من Celery (اختياري إضافي):**
   ```python
   # لإلغاء المهمة في Celery مباشرة فوراً:
   from celery.task.control import revoke
   revoke(celery_task_id, terminate=True, signal="SIGTERM")
   ```

### الخطوة 6: إعداد التشغيل على بيئة Toolforge
تعديل ملف `service.template` لتشغيل خادم ويب Celery Worker كـ Continuous Service مرافقة لـ Flask:

```yaml
# إضافة قسم خادم الويب وعامل Celery
backend: kubernetes
cpu: 3
mem: 6Gi
replicas: 2
type: python3.13

# لتشغيل الـ Celery Worker في Toolforge:
# سنقوم بتشغيله كـ continuous job باستخدام سطر الأوامر:
# toolforge jobs run celery-worker --command "celery -A src.app.celery_app worker --loglevel=info" --image python3.13 --continuous
```

---

## 6. خطة اختبار الانتقال وضمان عدم التراجع (Testing & Verification Plan)

لضمان سلامة الكود بنسبة 100%، ستتضمن خطة الاختبار الخطوات التالية:

1. **كتابة اختبارات وحدة (Unit Tests) لـ Celery integration:**
   - استخدام ميزة `celery_always_eager` في بيئة الاختبار لتبسيط عملية الاختبار بحيث تُنفذ مهام Celery بشكل متزامن كدوال عادية أثناء تشغيل `pytest`.
   - التأكد من تعافي قاعدة البيانات وملفات النتائج بالشكل المعتاد.
2. **محاكاة عملية الإلغاء عبر العمليات:**
   - اختبار كتابة ملف `.cancelled` والتأكد من توقف العامل عن العمل وحفظ حالته كـ `cancelled` فورياً.
3. **مراقبة تسريبات الذاكرة:**
   - تشغيل محاكي لمهام ثقيلة ومقارنة استهلاك الذاكرة في العمليات الفرعية للـ Celery Worker والتأكد من تحرير الذاكرة فور انتهاء العملية.

---

## 7. الخلاصة والتوصية (Conclusion & Recommendation)

### التوصية النهائية: **مجدية بشدة ويُنصح بجدولتها للمستقبل القريب.**

* **الجدوى التقنية:** ممتازة جداً. التطبيق مبني بالأساس على هيكلية `BaseObjectsJobWorker` المنفصلة تماماً، مما يجعل فصل منطق العمل عن الخيوط وتوجيهه لـ Celery أمراً غاية في السهولة وبأقل تعديل ممكن على الكود البرمجي الحالي (Loosely Coupled).
* **استقرار المنظومة:** سينقل التطبيق إلى مستوى احترافي من الاستقرار (Enterprise-grade stability)، ويمنع تماماً انهيار خوادم الويب بسبب مهام الترجمة الفاشلة أو الكثيفة.
* **البدء التدريجي:** يُنصح بتطبيق هذا التعديل على بيئة تطويرية أولاً (Staging)، واختبار كفاءة الاتصال بـ Redis في Toolforge قبل النشر النهائي على الفرع الرئيسي لضمان الاستقرار التام للمستخدمين.
