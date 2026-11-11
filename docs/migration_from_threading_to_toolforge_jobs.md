# تقرير الانتقال من threading إلى Toolforge Jobs

> مبني على الملفات: `jobs_worker.py` و`toolforge_jobs_api_service.py` و`toolforge_api_service.py` و`toolforge_jobs_types.py` و`jobs.py` (JobRecord) و`jobs_service.py` و`__init__.py` (AppFactory) و`objects.py` و`cli_jobs.py`، ومن جهة الهوية: نماذج المستخدمين (`UserRecord` و`UserTokenRecord`) و`TokenManager` و`CurrentUser` وخطافات المصادقة، إضافة إلى سكربت التشغيل الحالي لمهمة `collect_templates_data`. لم أطّلع بعد على الفئة الأساسية للمهام وأي مهمة فعلية ولا `jobs_files_service.py` ولا `http_client.py` ولا `get_authenticated_user_token`؛ ما يعتمد عليها مُعلَّم بكلمة «تحقق».

## 1. الملخص التنفيذي

- **الوضع الحالي:** كل مهمة تعمل في خيط (thread) داخل عملية Flask نفسها، وتشارك الذاكرة مع التطبيق (`flask_app`, `threading.Event`, `JobsRunner`).
- **الوضع الجديد:** كل مهمة تعمل في حاوية مستقلة على Kubernetes عبر Toolforge Jobs API، وتُشغَّل بأمر (command) وصورة (image) وحدود موارد.
- **الفرق الجوهري:** لا يمكن تمرير كائنات Python إلى الحاوية. يجب تمرير `job_id` فقط، ثم إعادة بناء التطبيق والمعاملات داخل العملية الجديدة من قاعدة البيانات.
- **المكاسب:** المهام تنجو من إعادة تشغيل الـ webservice، وتخرج من حدود ذاكرة التطبيق، ويمكن إيقافها فعلاً (قتل الحاوية)، ولها سجلات وحالة من النظام نفسه.
- **أهم خمسة تعديلات:**
  1. نقطة دخول CLI تشغّل مهمة واحدة بمعرّفها.
  2. حفظ معاملات المهمة (`args` و`form_data` منظَّفًا) في قاعدة البيانات بدل تمريرها في الذاكرة، أما هوية المستخدم وتوكناته فتُبنى في الحاوية من `JobRecord.username` (القسم 6.6).
  3. استبدال `threading.Event` بكائن يستعلم من قاعدة البيانات، أو بـ `Event` عادي يُضبط عند SIGTERM إن ثبت أن الفئة الأساسية تفحص القاعدة والملف (القسم 6.3).
  4. طبقة تجريد `JobBackend` لها تنفيذان: threads وToolforge.
  5. مزامنة دورية للحالة (reconcile) تكشف المهام التي ماتت دون تحديث قاعدة البيانات.

## 2. مراجعة jobs\_worker.py (نموذج threading)

### 2.1 كيف يعمل اليوم

- `_start_job_impl` يتحقق من نوع المهمة والمستخدم، ويدمج المعاملات (إعدادات النظام ثم معاملات المستدعي)، وينشئ سجل `JobRecord`، ثم ينشئ `threading.Event` ويسجله في قاموس عام `JOBS_CANCEL_EVENTS` محمي بـ Lock.
- يبني `JobsRunner` ويشغّل `_runner` في خيط. داخل `_runner` يُفتح `app_context` ثم يُنشأ كائن المهمة ويُستدعى `run()`، وفي `finally` يُحذف حدث الإلغاء.
- الإلغاء في `cancel_job_worker` ثلاثي: حدث محلي، وملف `.cancelled` بجانب ملف النتيجة، وتحديث قاعدة البيانات. وهذا تصميم جيد لأنه مهّد للإلغاء عبر عمليات مختلفة.
- `start_job` و`start_job_form` يشغّلان خيطًا daemon، أما `start_job_cli` فخيطه غير daemon (تنتظره العملية).

### 2.2 الملاحظات والمشاكل

1. **سجلات عالقة تقفل نوع المهمة كله (حرجة):** جدول `jobs` فيه قيد فريد `idx_unique_active_job` على `(job_type, is_running)`، أي مهمة نشطة واحدة فقط لكل نوع على مستوى التطبيق كله. تبقى `is_running = 1` حتى تمر الحالة عبر `update_job_status` بحالة نهائية أو عبر `cancel_job_db`. إذا قُتل الخيط بإعادة تشغيل الـ webservice يبقى الصف عالقًا، وكل محاولة بدء جديدة لهذا النوع تفشل بـ `DuplicateRecordError` إلى أن يُصلح الصف يدويًا. لا يوجد تنظيف عند الإقلاع.
2. **لا معالجة للاستثناءات في `_runner` (عالية):** يوجد `try/finally` فقط. إن رمى `run()` استثناءً ولم تعالجه فئة المهمة يضيع الخطأ في stderr الخاص بالخيط وتبقى الحالة running مع `is_running = 1` (يتصل بالنقطة 1). تحقق من أن فئات المهام تضبط failed بنفسها.
3. **حدث الإلغاء محلي لكل عملية (عالية):** مع عدة workers لا يصل `cancel_event.set()` إلا إن كان الطلب في نفس العملية. التعويض موجود: `JobsService.is_job_cancelled` يقرأ الحالة من قاعدة البيانات مع `refresh`، وهناك ملف `.cancelled`. لكنهما يعملان فقط إن كانت فئة المهمة تستطلعهما.
4. **سباق بين الإلغاء والاكتمال (متوسطة):** `_update_job_status` يكتب الحالة المطلوبة دون النظر إلى الحالة الحالية. إن أُلغيت المهمة (`cancelled` و`is_running = NULL`) ثم أنهت عملها قبل أن ترصد الإلغاء، تُكتب `completed` فوق `cancelled`.
5. **سجل يتيم إذا فشل بدء الخيط (متوسطة):** `create_job` يُنفَّذ (ويضع `is_running = 1`) قبل `thread.start()`، فإن فشل البدء يبقى السجل وحدث الإلغاء المسجَّل، ويُقفل النوع كما في النقطة 1.
6. **لا حد للموارد (متوسطة):** كل خيط يستهلك ذاكرة وCPU من حدود الـ webservice ويتنافس مع الطلبات على GIL. القيد الفريد يحد من التوازي لكل نوع فقط، وليس لمجموع الأنواع.
7. **أولوية المعاملات (متوسطة، أمنية):** `resolved_args.update(args)` يجعل معاملات المستدعي تتجاوز القيم القادمة من `SettingsService`، ولا يُحذف سوى `csrf_token`. الأفضل قائمة بيضاء من المفاتيح.
8. **نجاح الإلغاء مضلل (منخفضة):** `cancel_job_worker` يُرجع True إذا أُنشئ ملف `.cancelled` حتى لو فشل تحديث قاعدة البيانات (`cancel_job_db` يبتلع الاستثناء ويرجع False).
9. **تكرار وتحديد الأنواع (منخفضة):** ثلاث دوال start شبه متطابقة، و`Callable[[JobsRunner]]` غير صحيح (المطلوب `Callable[[JobsRunner], Any]`)، وحقل `JobsRunner.cancel_event` معرَّف في `objects.py` كـ `threading.Event | None` فلا يقبل بديلًا بين العمليات دون تعديل.
10. **المسار الموجود في `cli_jobs.py` (ملاحظة):** الأمر `flask run-job <job_type>` يستدعي `start_job_cli` ويعمل في خيط غير daemon داخل عملية الأمر نفسها، أي أن المهام المجدولة تعمل على الأرجح بهذه الطريقة اليوم. لكنه ينشئ سجلًا جديدًا باسم مستخدم `Background job` ويمرر `update_all` فقط، فلا يشغّل سجلًا موجودًا بمعرّفه. وحدث الإلغاء فيه محلي أيضًا، فلا يصله إلا الإلغاء عبر قاعدة البيانات أو الملف.

## 3. مراجعة toolforge\_jobs\_api\_service.py

### 3.1 نقاط القوة

- عميل رفيع خالٍ من Flask، كل دالة تقابل نقطة نهاية واحدة، وفيه `quote()` لاسم المهمة وتوثيق واضح للاستجابات.
- يغطي كل ما نحتاجه: `create_job`, `list_jobs`, `show_job`, `delete_job`, `restart_job`, `get_logs`, `quotas`, `images`.

### 3.2 الملاحظات

1. **`job_id` هنا اسم المهمة (نص)، وليس رقم قاعدة البيانات:** في Toolforge الاسم من 1 إلى 52 حرفًا: أحرف صغيرة وأرقام و`-` و`.` فقط (حسب `toolforge_jobs_types.py`). أنواع المهام عندكم على الأرجح تحوي `_` فلا بد من تحويلها. الأنسب اسم مشتق ثابت مثل `<job_type>-<job_id>` يُحسب عند الحاجة، فلا يلزم عمود إضافي.
2. **`restart_job` لا يصلح للمهام العادية (one-off):** تعليق `_json` نفسه يذكر الخطأ `Unable to restart a one-off job`. إعادة التشغيل تعمل على المهام المجدولة والمستمرة فقط. إعادة تشغيل one-off = إنشاء مهمة جديدة.
3. **`flush_jobs` خطر:** يحذف كل مهام الأداة (وليس مهام هذا التطبيق فقط). احذفه أو ضعه خلف علم صريح.
4. **`list_jobs_test` داخل الصنف الإنتاجي:** بيانات ثابتة ومسار `/data/project/mdw/...` مكتوب فيها. انقلها إلى الاختبارات. (تصحيح لما ذكرته سابقًا: `JobListResponse` هو `TypedDict` فقيمة `.load()` هي dict عادي ولا يوجد تضارب في النوع، لكن وجود `classmethod` داخل `TypedDict` غير قياسي وتعترض عليه أدوات فحص الأنواع.)
5. **أخطاء HTTP:** `ToolforgeApiService.request` ينفّذ `raise_for_status()` عند `check=True` (الافتراضي في `ToolforgeJobsService`)، فيُرفع `requests.HTTPError` قبل أن تصل `_json` إلى قراءة الجسم، وفرع «غير 200» داخل `_json` لا يُنفَّذ عمليًا. رسالة Toolforge (مثل `{'error': [...]}`) متاحة فقط عبر `e.response.json()`. الأفضل استثناء مخصص يلتقطها.
6. **ليست وراثة بل تركيب:** `ToolforgeJobsService` لا يرث `ToolforgeApiService` (يحمله كـ `self.api`)، فتعليق «healthcheck() and metrics() are inherited» قديم. الدوال المعرّفة صراحة تفويض صحيح.
7. **لا فلترة:** `list_jobs` تُرجع كل مهام الأداة، فيلزم بادئة (prefix) لاسم المهمة.
8. **`get_logs`** تُرجع النص كاملًا بلا tail، فاقتطعه عند العرض.
9. **لا إعادة محاولة ولا backoff:** المهلة الافتراضية 15 ثانية (`REQUEST_TIMEOUT`)، وأي إعادة محاولة مسؤولية `HttpClient` (لم أطّلع عليه).
10. **وضع المصادقة:** إذا وُجد المتغير `TOOLS_DEPLOY_TOKEN` يعمل الصنف في الوضع الخارجي (التوكن داخل الرابط)، وإلا يعمل داخليًا بشهادة `~/.toolskube/client.crt` مع `verify=False`. تأكد ألا يكون التوكن معرّفًا في بيئة الـ webservice ولا بيئة المهام، ولا تسجّل `response.url` أبدًا. اسم الأداة الافتراضي `mdw` من `TOOL_NAME`.
11. **قيود من الأنواع:** حالة `status.short` من الجدول `pending/running/succeeded/failed/unknown` (وليس completed)، و`retry` من 0 إلى 5، و`timeout` للمهام المجدولة فقط، ولا يوجد حقل `ttl` في `NewJob`، أي لا يظهر ما يحذف المهام العادية المنتهية تلقائيًا (تحقق)، فيلزم تنظيف.

## 4. التصميم المستهدف

**مبدأ:** قاعدة البيانات مصدر الحقيقة لحالة منطق المهمة، وToolforge مصدر الحقيقة لحالة الحاوية (لكشف الانهيار، OOM، أو فقدان المهمة).

- **البدء:** واجهة الويب تستدعي `start_job` فتنشئ سجل DB (pending) وتحفظ المعاملات (بلا مستخدم أو توكنات)، ثم تستدعي `create_job` في Toolforge بأمر `bash ~/shs/flask_cmd.sh run-job-id <job_id>`، وتبقى الحالة pending حتى تبدأ الحاوية.
- **التنفيذ:** الحاوية تشغّل أمر CLI فتبني التطبيق وتقرأ المعاملات من DB وتبني هوية المستخدم من `JobRecord.username` ثم تضع الحالة running وتشغّل `run()` وتكتب الحالة النهائية.
- **الإلغاء:** يُسجَّل الإلغاء في DB أولًا، ثم `delete_job`. الحاوية تتلقى SIGTERM فتضع حدث الإلغاء وتنهي بأمان.
- **المراقبة:** مهمة reconcile دورية تقارن DB بـ `list_jobs`.

## 5. خطة الانتقال المرحلية

### المرحلة 0: إصلاحات في النظام الحالي قبل أي انتقال

- **تنظيف عند الإقلاع:** حوّل كل صف `pending/running` قديم (backend = thread) إلى `failed` عبر `update_job_status`، لأنه يحرر `is_running`. بدون هذا يبقى النوع مقفلًا بعد كل إعادة تشغيل.
- في `_runner`: التقط الاستثناء واضبط `failed`، وحرّر `is_running` دائمًا.
- امنع الكتابة فوق حالة نهائية في `_update_job_status` (القسم 6.1).
- انقل `list_jobs_test` إلى الاختبارات، واحذف `flush_jobs` أو احمِها بعلم، وأضف استثناء مخصصًا لأخطاء Toolforge (النقطة 5 في 3.2).
- **معيار الإنجاز:** إعادة تشغيل التطبيق أثناء مهمة لا تترك النوع مقفلًا.

### المرحلة 1: فصل المنطق عن التنفيذ (طبقة تجريد)

- عرّف `JobBackend` بالدوال `start` و`cancel` و`status` و`logs`.
- انقل كود الخيوط الحالي إلى `ThreadBackend` دون تغيير سلوكه.
- أضف إعداد `JOBS_BACKEND` (`thread` أو `toolforge`) مع إمكانية الاستثناء لكل `job_type`.
- **معيار الإنجاز:** كل الاختبارات الحالية تمر وكل الاستدعاءات تمر عبر الواجهة.

### المرحلة 2: جعل المهمة قابلة للتشغيل خارج عملية الويب

- هجرة قاعدة بيانات (Alembic) تضيف `backend` و`payload` إلى جدول `jobs` (القسم 6.1). `init_db` ينشئ الجداول الناقصة فقط ولا يضيف أعمدة لجدول موجود.
- أضف الأمر `flask run-job-id` داخل `register_cli_jobs` مع `run_job_by_id` و`build_job_user` (القسم 6.2)، وسكربت الغلاف `flask_cmd.sh` (القسم 6.7).
- أضف إلى `JobData` الحقول `image` و`memory` و`cpu`، وقرر الإلغاء: `DbCancelEvent` (القسم 6.3) أو `threading.Event` عادي يُضبط عند SIGTERM إن ثبت أن الفئة الأساسية تفحص قاعدة البيانات والملف.
- سجلات الأمر الحالي `flask run-job` تُسجَّل بـ `backend = 'cli'` لتمييزها.
- **معيار الإنجاز:** `bash ~/shs/flask_cmd.sh run-job-id 123` يشغّل مهمة أنشأتها الواجهة بهوية صاحبها ويحترم الإلغاء.

### المرحلة 3: ToolforgeBackend

- نفّذ `start` عبر `create_job` (القسم 6.4) بعد فحص `quotas()`.
- إن فشل الإنشاء في Toolforge فاضبط الصف `failed` فورًا لتحرير `is_running`.
- **معيار الإنجاز:** مهمة واحدة غير حرجة تعمل على Toolforge من الواجهة.

### المرحلة 4: الاستعلام والمزامنة

- نفّذ `status` وقائمة المهام النشطة والسجلات (القسم 7).
- أنشئ مهمة `reconcile` مجدولة كل دقيقة تكشف المهام الضائعة وتحذف مهام Toolforge المنتهية.
- **معيار الإنجاز:** مهمة تُقتل يدويًا تظهر failed خلال دقيقتين ويتحرر نوعها.

### المرحلة 5: الإلغاء وإعادة التشغيل

- وسّع `cancel_job_worker` ليستدعي `delete_job` (القسم 8).
- إعادة التشغيل = سجل جديد بنفس الحمولة (one-off).

### المرحلة 6: الإطلاق التدريجي

- فعّل Toolforge لنوع واحد أولًا ثم لبقية الأنواع تدريجيًا عبر الإعداد، وأبقِ `thread` كخيار رجوع.
- بعد أسبوعين من الاستقرار أزل خيار الرجوع من الإنتاج. يبقى `ThreadBackend` (و`JOBS_CANCEL_EVENTS`) للتطوير المحلي والاختبارات فقط.

## 6. التعديلات المطلوبة على الكود

### 6.1 قاعدة البيانات وJobsService

جدول `jobs` الحالي لا يحمل مكانًا للمعاملات ولا نوع التنفيذ. أضف عمودين بهجرة Alembic (Flask-Migrate موجود)، لأن `init_db` لا يعدّل الجداول القائمة:

```python
# migrations/versions/xxxx_jobs_backend_payload.py
def upgrade():
    op.add_column("jobs", sa.Column("backend", sa.String(20), nullable=False, server_default="thread"))
    op.add_column("jobs", sa.Column("payload", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("jobs", "payload")
    op.drop_column("jobs", "backend")
```

```python
# models/jobs.py (JobRecord): أضف الحقلين، واستورد Text، وأضف backend إلى to_json
backend: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'thread'"))
payload: Mapped[str | None] = mapped_column(Text, nullable=True)
```

اسم مهمة Toolforge لا يحتاج عمودًا: يُشتق من النوع والرقم (القسم 6.4).

**لا تخزّن في `payload` أي بيانات مستخدم أو توكنات.** التوكنات موجودة أصلًا مشفرة في `user_tokens`، وتبني الحاوية `auth_payload` من `JobRecord.username` وقت التنفيذ (القسم 6.6)، فيصلها أحدث توكن. نظّف `form_data` من `csrf_token` وأي حقل حساس قبل حفظه.

دوال جديدة في `JobsService` بنفس أسلوب الصنف الحالي (لا توجد فيه الآن `save_payload` ولا `list_active` ولا `mark_failed`):

```python
FINAL_STATUSES = ("completed", "failed", "cancelled", "skipped")


class JobsService(CRUDService[JobRecord]):
    def save_payload(self, job_id: int, backend: str, payload: dict) -> None:
        job = self.get_by(id=job_id)
        job.backend = backend
        job.payload = json.dumps(payload, default=str)
        self.session.commit()

    @staticmethod
    def load_payload(job: JobRecord) -> dict:
        return json.loads(job.payload) if job.payload else {}

    def list_active(self, backend: str | None = None) -> list[JobRecord]:
        query = self.session.query(JobRecord).filter(JobRecord.status.in_(["pending", "running"]))
        if backend:
            query = query.filter(JobRecord.backend == backend)
        return query.all()

    def mark_failed(self, job: JobRecord, reason: str = "") -> JobRecord:
        logger.warning("Job %s failed: %s", job.id, reason)
        # update_job_status يضبط is_running = None فيتحرر قفل النوع
        return self.update_job_status(job.id, "failed", job_type=job.job_type)
```

وإصلاح السباق بين الإلغاء والاكتمال داخل `_update_job_status` (أول سطور الدالة بعد حساب `status_lower`):

```python
current = (job.status or "").lower()
if current in FINAL_STATUSES and status_lower != current:
    logger.info("Job %s is already %s; ignoring %s", job.id, current, status_lower)
    return job
```

### 6.2 نقطة دخول تشغيل مهمة واحدة

الأمر الحالي `flask run-job <job_type>` في `cli_jobs.py` ينشئ سجلًا جديدًا ويشغّله في خيط داخل عملية الأمر، وهو ما يستدعيه سكربت `collect_templates_data` المجدول اليوم. يبقى كما هو (مستخدمه `Background job` لا يحتاج توكنات). نضيف أمرًا مكمّلًا `run-job-id <job_id>` يشغّل سجلًا أنشأته الواجهة بالفعل. أوامر `app.cli.command` تُنفَّذ داخل `app_context` تلقائيًا، فلا حاجة لاستدعاء `AppFactory.create()` مرة أخرى.

```python
# cli_jobs.py: أضف داخل register_cli_jobs(app) بجانب run-job
@app.cli.command("run-job-id")
@click.argument("job_id", type=int)
def _run_job_id(job_id: int) -> None:
    """flask --app $HOME/www/python/src/app.py run-job-id 123"""
    sys.exit(run_job_by_id(job_id))


@app.cli.command("reconcile-jobs")
def _reconcile_jobs() -> None:
    reconcile()  # القسم 7.4


# jobs_worker.py
def build_job_user(username: str) -> dict | None:
    """نفس شكل auth_payload في وضع threading (انظر القسم 6.6)."""
    token = UserTokenService().get_user_token_by_username(username)
    if token is None:
        return None
    user = TokenManager().get_authenticated_user(token.user_id)  # تحقق من مسار الاستيراد
    return user.to_auth_payload() if user else None


def run_job_by_id(job_id: int) -> int:
    svc = JobsService()
    job = svc.get_by(id=job_id)
    if job is None:
        logger.error("Job %s not found", job_id)
        return 2
    if job.status == "cancelled":  # أُلغيت قبل أن تبدأ الحاوية
        return 0

    job_data = load_job_data(job.job_type)
    if not job_data or not job_data.job_class:
        svc.mark_failed(job, f"unknown job type {job.job_type}")
        return 2

    user = build_job_user(job.username)
    if user is None:
        svc.mark_failed(job, f"no token for user {job.username}")
        return 3

    payload = svc.load_payload(job)
    svc.update_job_status(job_id, "running", job_type=job.job_type)

    cancel_event = DbCancelEvent(job_id, job.job_type)  # أو threading.Event() انظر 6.3
    signal.signal(signal.SIGTERM, lambda *_: cancel_event.set())

    runner_data = JobsRunner(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=payload.get("args") or {},
        form_data=payload.get("form_data"),
    )
    try:
        job_data.job_class(runner_data).run()
    except Exception:
        logger.exception("Job %s crashed", job_id)  # لا تسجّل runner_data: فيه التوكنات
        svc.mark_failed(svc.get_by(id=job_id), "unhandled exception")
        return 1

    # شبكة أمان إن لم تضبط الفئة حالة نهائية (تحقق من سلوك الفئات)
    job = svc.get_by(id=job_id)
    if job.status in ("pending", "running"):
        svc.mark_as_completed(job)
    return 0
```

ملاحظات: (1) أمر flask يهيّئ التطبيق كاملًا (`init_db` وتسجيل المسارات) فيزيد زمن بدء كل مهمة؛ أضف وضعًا خفيفًا إن لزم. (2) المعاملات تُحل في الواجهة (`_load_job_args`) وتُخزَّن في `payload`، فلا تُعاد قراءتها في الحاوية. (3) فحص `can_run_jobs` و`can_run_bg_jobs` يبقى في مسار البدء قبل الإرسال ولا يتكرر هنا، لكن غياب التوكن يُنهي المهمة failed. (4) سجلات الأمر القديم `run-job` لا تُراقَب بالاسم في Toolforge، فاعتمد لها مهلة زمنية في `reconcile`.

### 6.3 حدث إلغاء يعمل بين العمليات

```python
# src/main_app/jobs_workers/cancel.py
import time


class DbCancelEvent:
    """بديل threading.Event: يقرأ الحالة من قاعدة البيانات بفاصل زمني."""

    def __init__(self, job_id: int, job_type: str, interval: float = 2.0):
        self.job_id, self.job_type, self.interval = job_id, job_type, interval
        self._set, self._last = False, 0.0

    def set(self) -> None:
        self._set = True

    def is_set(self) -> bool:
        if self._set:
            return True
        now = time.monotonic()
        if now - self._last >= self.interval:
            self._last = now
            from ..database.services import JobsService

            self._set = JobsService().is_job_cancelled(self.job_id, self.job_type)
        return self._set

    def wait(self, timeout: float | None = None) -> bool:
        end = None if timeout is None else time.monotonic() + timeout
        while not self.is_set():
            if end is not None and time.monotonic() >= end:
                break
            time.sleep(0.5)
        return self._set
```

`JobsService.is_job_cancelled` يعمل `session.refresh` فيرى تغييرات العمليات الأخرى، ويستجيب الحدث لـ SIGTERM الذي يرسله `delete_job`. في `objects.py` بدّل نوع `cancel_event` في `JobsRunner` من `threading.Event | None` إلى Protocol بالدوال `is_set` و`set` و`wait` حتى يقبل `DbCancelEvent`. **تبسيط محتمل:** إن ثبت أن الفئة الأساسية للمهام تفحص `cancel_event.is_set()` وملف `.cancelled` وقاعدة البيانات دوريًا (كما ورد في التقرير الآخر، ولم أتحقق منه)، فيكفي `threading.Event()` عادي يُضبط عند SIGTERM، ويمكن تخطي هذا القسم وإبقاء نوع `JobsRunner.cancel_event` كما هو.

### 6.4 ToolforgeBackend

```python
# src/main_app/jobs_workers/backends/toolforge_backend.py
import re
from pathlib import Path
from ...api_services.clients.toolforge_jobs_api_service import ToolforgeJobsService

IMAGE = "python3.13"  # مأخوذ من بيانات الاختبار في الملف، تحقق من الصور عبر svc.images()
CMD = "bash ~/shs/flask_cmd.sh run-job-id {job_id}"  # تحقق من المسارات


def tf_job_name(job_type: str, job_id: int) -> str:
    slug = re.sub(r"[^a-z0-9.-]+", "-", job_type.lower()).strip("-")[:40]
    return f"{slug}-{job_id}"  # حد Toolforge: 52 حرفًا


class ToolforgeBackend:
    def __init__(self, svc: ToolforgeJobsService | None = None):
        self.svc = svc or ToolforgeJobsService()

    def start(self, job, job_data) -> str:
        name = tf_job_name(job.job_type, job.id)
        body = {
            "name": name,
            "imagename": getattr(job_data, "image", None) or IMAGE,
            "cmd": CMD.format(job_id=job.id),
            "job_type": "one-off",
            "mount": "all",
            "memory": getattr(job_data, "memory", None) or "1Gi",
            "cpu": getattr(job_data, "cpu", None) or "0.5",
            "retry": 0,
            "emails": "none",
            "filelog": True,
            "filelog_stdout": f"{Path.home()}/logs/jobs/{name}.out",
            "filelog_stderr": f"{Path.home()}/logs/jobs/{name}.err",
        }
        self.svc.create_job(body)
        return name
```

`JobData` في `objects.py` لا يحوي صورة ولا موارد (حقوله: `job_type` و`job_name` و`job_list_template` و`job_class` و`job_args` وما يخص الواجهة). أضف في آخره حقولًا افتراضية `image: str | None = None` و`memory: str | None = None` و`cpu: str | None = None`؛ الإضافة بقيم افتراضية آمنة لأنه dataclass. `cmd` يظهر في استجابة `list_jobs`، فلا تضع فيه سوى `job_id`. الأمر يمر عبر سكربت الغلاف في القسم 6.7.

### 6.5 الواجهة الموحدة في jobs\_worker.py

```python
# داخل _start_job_impl: نفس التحقق الحالي (بما فيه صلاحيات المستخدم) وبناء resolved_args،
# ثم بدل إنشاء الخيط:
job = JobsService().create_job(job_type, username)  # يضع is_running = 1
backend_name = get_backend_name(job_type)  # من الإعدادات، اختيار صريح
JobsService().save_payload(
    job.id,
    backend_name,
    {
        "args": resolved_args,
        "form_data": sanitize_form_data(form_data),  # بلا csrf_token ولا حقول حساسة
    },
)  # لا مستخدم ولا توكنات هنا
try:
    get_backend(backend_name).start(job, job_data)
except Exception as exc:
    JobsService().mark_failed(job, f"start failed: {exc}")  # يحرر القفل
    raise
return job.id
```

التوقيعات العامة (`start_job` و`start_job_form` و`start_job_cli`) تبقى كما هي، فلا يتغير كود الواجهة.

### 6.6 هوية المستخدم داخل الحاوية

في وضع threading قيمة `JobsRunner.user` هي `CurrentUser.to_auth_payload()`: الحقول `id` و`username` و`access_token` و`access_secret`، والتوكنان بالبايتات المشفرة كما في `UserTokenRecord` (تُفك عند الاستخدام عبر `CryptoService`). في الحاوية لا يوجد طلب HTTP فلا يعمل hook `set_logged_in_user`، و`g._current_user` فارغ، وهذا حاله في الخيوط اليوم لأن `_runner` يفتح `app_context` جديدًا.

- تُبنى الهوية من `JobRecord.username` عبر `UserTokenService.get_user_token_by_username` ثم `TokenManager.get_authenticated_user` (الدالة `build_job_user` في 6.2)، فتحصل الفئات على نفس الشكل الذي تعرفه.
- متغيرات البيئة (ومنها مفتاح التشفير) متاحة في مهام Toolforge، فلا إجراء إضافي.
- ضبط `g._current_user` اختياري: نفّذ `grep -rn 'get_current_user\|_current_user' src/main_app/jobs_workers src/main_app/services`، فإن لم يستخدمه كود المهام فلا حاجة له، وإلا فاضبطه في `run_job_by_id` للتكافؤ.
- لا تسجّل `runner_data` ولا `user` في أي لوج.

### 6.7 سكربت الغلاف

السكربت الحالي لمهمة `collect_templates_data` موجود على Toolforge فقط وليس في المستودع. أقترح سكربتًا عامًا يوضع في المستودع (`scripts/flask_cmd.sh`) ويُنسخ إلى `~/shs/` عند النشر، ويبقى القديم كما هو:

```bash
#!/bin/bash
set -euo pipefail
source "$HOME/www/python/venv/bin/activate"
exec flask --app "$HOME/www/python/src/app.py" "$@"
```

- **`exec` ضروري:** بدونه يبقى bash هو العملية الأولى في الحاوية فقد لا يمرر SIGTERM إلى Python، فلا يستجيب `delete_job` استجابة لطيفة. السكربت الحالي لا يستخدم `exec`، فلا يصلح كما هو للمهام القابلة للإلغاء.
- الاستعمال: `bash ~/shs/flask_cmd.sh run-job-id 123` و`bash ~/shs/flask_cmd.sh reconcile-jobs`.
- ملف التطبيق هو `src/app.py` (و`app1.py` الوارد في تعليق `cli_jobs.py` للتشغيل المحلي).

### 6.8 إضافات اختيارية

- يبقى `ThreadBackend` دائمًا للتطوير المحلي والاختبارات (Toolforge API يحتاج شهادات العميل)، والاختيار في الإنتاج بإعداد صريح `JOBS_BACKEND` بلا اكتشاف تلقائي، حتى لا تعود المهام إلى الخيوط بصمت إن غابت الشهادات.
- حفظ رسالة الحالة مثل `exitcode 137 (OOMKilled)` كسبب فشل واضح.
- واجهة: تبويب سجلات حية (`get_logs`) وصفحة حصص للمشرف، وإعدادات مثل `TOOLFORGE_JOB_IMAGE` و`TOOLFORGE_JOB_DEFAULT_MEMORY`.
- اختبارات وحدة لـ `ToolforgeBackend` بـ `http_client` وهمي.

## 7. الاستعلام عن المهام وحالتها

مصدر الحقيقة لحالة المنطق هو جدول `jobs`، ومصدر الحقيقة لحالة الحاوية هو Toolforge. الاستعلام يقارن الاثنين.

### 7.1 جدول ربط الحالات

| `status.short` في Toolforge | حالة `jobs` | ملاحظة |
| --- | --- | --- |
| pending | pending | الحاوية بانتظار الجدولة |
| running | running | ويضعها `run_job` نفسه أيضًا |
| succeeded | completed | عادةً سبقت DB إلى ذلك؛ للأمان `mark_as_completed` |
| failed | failed | السبب في `status.messages` (مثل `exitcode 127`)، ونص أطول في `status_long` |
| unknown | بلا تغيير | سجّل تحذيرًا فقط |
| 404 والصف نشط | failed | المهمة حُذفت أو ضاعت، بعد مهلة سماح قصيرة |

حالات DB الفعلية في الكود: `pending` و`running` و`completed` و`failed` و`cancelled` و`skipped`. الأربع الأخيرة نهائية، وبوصول الصف إليها يُصفَّر `is_running` فيتحرر النوع.

### 7.2 حالة مهمة واحدة والمهام الجارية

```python
from requests import HTTPError

tf = ToolforgeJobsService()


def get_live_status(job) -> dict | None:
    try:
        tf_job = tf.show_job(tf_job_name(job.job_type, job.id))["job"]
    except HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return None  # غير موجودة في Toolforge
        raise
    status = tf_job["status"]
    return {
        "short": status["short"],  # pending/running/succeeded/failed/unknown
        "duration": status.get("duration"),  # نص مثل 24d24h59m45s
        "messages": status.get("messages", []),
        "detail": tf_job.get("status_long"),
    }


def running_jobs():
    """الصفوف النشطة في DB مقرونة بحالتها الحية (طلب API واحد)."""
    live = {j["name"]: j for j in tf.list_jobs()["jobs"]}
    rows = JobsService().list_active(backend="toolforge")
    return [(row, live.get(tf_job_name(row.job_type, row.id))) for row in rows]
```

لا حاجة لبادئة اسم للفلترة: أسماء مهام التطبيق مشتقة من صفوف DB، فنبحث عنها بالاسم المشتق ونتجاهل بقية مهام الأداة.

### 7.3 مزامنة صف مع Toolforge

```python
from datetime import UTC, datetime, timedelta

GRACE = timedelta(seconds=90)  # مهلة قبل اعتبار المهمة ضائعة


def sync_job(job) -> None:
    svc = JobsService()
    live = get_live_status(job)
    if live is None:
        created = job.created_at.replace(tzinfo=UTC)  # تحقق من المنطقة الزمنية للعمود
        if datetime.now(UTC) - created > GRACE:
            svc.mark_failed(job, "job is missing in Toolforge")
    elif live["short"] == "failed":
        svc.mark_failed(job, "; ".join(live["messages"]))
    elif live["short"] == "succeeded" and job.status in ("pending", "running"):
        svc.mark_as_completed(job)
    elif live["short"] == "running" and job.status == "pending":
        svc.update_job_status(job.id, "running", job_type=job.job_type)
```

استدعِها في مكانين: عند عرض قائمة المهام في الواجهة لكل صف نشط (طلب API واحد لكل صف، والقيد الفريد يجعل العدد صغيرًا)، وفي مهمة `reconcile` الدورية.

### 7.4 reconcile والتنظيف

المهام العادية المنتهية لا تُحذف تلقائيًا (لا حقل `ttl` في `NewJob`، تحقق)، وبقاؤها يشغل الحصة. احذف المنتهية بعد أن تستقر حالتها في DB:

```python
def reconcile() -> None:
    svc = JobsService()
    for job in svc.list_active(backend="toolforge"):
        sync_job(job)

    for tf_job in tf.list_jobs()["jobs"]:
        if tf_job["status"]["short"] in ("succeeded", "failed"):
            job_id = int(tf_job["name"].rsplit("-", 1)[-1])  # الاسم النوع-الرقم
            row = svc.get_by(id=job_id)
            if row and row.status in FINAL_STATUSES:
                try:
                    tf.delete_job(tf_job["name"])
                except HTTPError:
                    logger.exception("cleanup failed for %s", tf_job["name"])
```

تنبّه: هذا يحذف مهامًا بأسماء تنتهي برقم فقط إن وُجدت لدى الأداة مهام أخرى بنفس النمط، فالأفضل الاقتصار على أسماء تبدأ بنوع معروف من `jobs_data_admins` و`jobs_data_public`.

جدولة `reconcile` نفسها (إنشاء أو تحديث بلا تكرار عبر `update_job`):

```python
tf.update_job(
    {
        "name": "reconcile-jobs",
        "imagename": IMAGE,
        "job_type": "scheduled",
        "schedule": "*/5 * * * *",  # تحقق من أدنى فاصل تسمح به Toolforge
        "cmd": "bash ~/shs/flask_cmd.sh reconcile-jobs",
        "mount": "all",
        "memory": "512Mi",
        "cpu": "0.2",
    }
)
```

### 7.5 السجلات

- `tf.get_logs(name)` تعيد النص كاملًا؛ اقتطع آخر N سطرًا قبل العرض. تعمل فقط ما دامت المهمة موجودة في Toolforge.
- مع `filelog: True` تبقى ملفات `.out` و`.err` على NFS بعد حذف المهمة. استخدم مسارًا مطلقًا (كما في بيانات الاختبار: `/data/project/<tool>/...`) أو `Path.home()`، وتأكد من وجود المجلد، ثم اقرأ الملف إن لم تعد المهمة موجودة.
- قبل كل بدء: `tf.quotas()` للتأكد من توفر الحصة، و`tf.images()` عند تغيير الصورة.

## 8. التشغيل والإيقاف وإعادة التشغيل

### تشغيل مهمة

التوقيع العام لم يتغير:

```python
job_id = start_job(auth_payload, "my_job_type", args={"wiki": "ar"})
```

ما يحدث داخليًا: `create_job` يُنشئ الصف ويضع `is_running = 1` (فإن كان النوع نشطًا يُرفع `DuplicateRecordError` كما اليوم)، ثم تُحفظ الحمولة، ثم يُنشأ في Toolforge مهمة one-off باسم مثل `my-job-type-123` تشغّل `bash ~/shs/flask_cmd.sh run-job-id 123`. لاختبار الحاوية يدويًا قبل الربط شغّل `flask --app src/app.py run-job-id 123` محليًا، ثم جرّبه بأمر `toolforge jobs run` مع نفس الصورة و`--mount all`.

### إيقاف مهمة

أضف الفرع الجديد إلى `cancel_job_worker` بعد خطواته الحالية (الحدث المحلي وملف `.cancelled` وقاعدة البيانات):

```python
job = job or JobsService().get_by(id=job_id)
if job and job.backend == "toolforge":
    try:
        ToolforgeJobsService().delete_job(tf_job_name(job.job_type, job.id))
    except HTTPError as exc:
        if exc.response is None or exc.response.status_code != 404:
            logger.exception("Failed to delete Toolforge job for %s", job_id)
```

الترتيب مهم: تسجيل الإلغاء في DB أولًا (`cancel_job_db`) ثم `delete_job`. عندها تتلقى الحاوية SIGTERM فيصبح `DbCancelEvent` مضبوطًا وتنتهي كمهمة ملغاة بدل failed، ويمنع الإصلاح في 6.1 تحويلها إلى completed. نقطة انتباه: `cancel_job_db` يحرر `is_running` فورًا، فقد تبدأ مهمة جديدة من نفس النوع بينما القديمة تُنهي عملها لثوانٍ.

### إعادة تشغيل مهمة

- **مهمة one-off (حالة هذا التطبيق):** لا يصح `restart_job`. أنشئ سجلًا جديدًا بنفس المعاملات بعد انتهاء القديم أو إلغائه:

```python
def restart(old_job) -> int:
    if old_job.status in ("pending", "running"):
        raise ValueError("Cancel the running job first")
    payload = JobsService.load_payload(old_job)
    return start_job({"username": old_job.username}, old_job.job_type, args=payload.get("args"))
```

- **مهمة مجدولة أو مستمرة (مثل `reconcile-jobs`):** `ToolforgeJobsService().restart_job('reconcile-jobs')`.

## 9. المخاطر والتخفيف

| الخطر | التخفيف |
| --- | --- |
| قفل نوع المهمة بسبب سجل عالق | تنظيف عند الإقلاع، وreconcile، وضبط failed عند فشل البدء |
| تعارض اسم المهمة (409) | اسم مشتق من النوع والرقم، والرقم فريد |
| تجاوز حصة Toolforge | فحص `quotas()` قبل البدء، والقيد الفريد يحد النشط بمهمة لكل نوع |
| مهام منتهية تشغل الحصة | حذفها في reconcile بعد استقرار الحالة في DB |
| تشغيل الصنف في الوضع الخارجي بالخطأ | لا يُعرَّف `TOOLS_DEPLOY_TOKEN` في بيئة الإنتاج |
| زمن بدء الحاوية و`AppFactory.create()` | إظهار pending في الواجهة، ووضع تطبيق خفيف عند الحاجة |
| اختلاف الاعتمادات والحزم بين الويب والمهام | نفس venv أو صورة موحدة، واختبار `run-job-id` يدويًا |
| أسرار داخل `payload` أو `cmd` | `payload` بلا مستخدم ولا توكنات، و`cmd` فيه `job_id` فقط، ولا يُسجَّل `runner_data` |
| المستخدم بلا توكن أو حُذف بعد إرسال المهمة | `build_job_user` يعيد None فتُضبط المهمة failed برسالة واضحة |
| SIGTERM لا يصل إلى Python فلا يعمل الإلغاء الرشيق | سكربت الغلاف بـ `exec` (6.7) واختبار الإلغاء |
| عودة صامتة إلى threading في الإنتاج | `JOBS_BACKEND` صريح بلا اكتشاف تلقائي، وفشل عند الإقلاع إن اختير toolforge دون شهادات |
| مهمتان من نفس النوع لحظة الإلغاء | قبول ذلك، أو انتظار اختفاء المهمة قبل تحرير القفل |
| مهمة طويلة تفقد اتصال قاعدة البيانات | استخدام `update_job_status_with_retry` (موجود) داخل فئات المهام |
| الإلغاء لا يعمل لأن الفئة لا تستطلع `cancel_event` | مراجعة فئات المهام والتأكد من استدعاء `is_set` في الحلقات الطويلة |

## 10. قائمة الاختبار قبل التحويل الكامل

- تشغيل `bash ~/shs/flask_cmd.sh run-job-id <id>` يدويًا لكل `job_type` والتأكد من اكتماله وتحرر `is_running`.
- مستخدم بلا توكن (أو محذوف): تنتهي المهمة failed برسالة واضحة ولا يبقى النوع مقفلًا.
- إلغاء أثناء التنفيذ عبر الواجهة والتأكد أن الحالة النهائية cancelled وليست completed.
- التأكد أن SIGTERM يصل إلى Python عبر سكربت الغلاف (`exec`): `delete_job` ينهي المهمة بإنهاء رشيق وليس بقتل مباشر.
- قتل الحاوية يدويًا (`delete_job`) والتأكد أن reconcile يضبط failed ويتحرر النوع.
- إعادة تشغيل الـ webservice أثناء مهمة والتأكد أنها تكمل.
- فشل `create_job` في Toolforge (اسم مكرر، حصة، API متوقف): يظهر خطأ مفهوم ولا يبقى سجل نشط.
- مهمة `Background job` المجدولة الحالية (`run-job`) تعمل كما كانت دون تغيير.
- التطوير المحلي والاختبارات تعمل بـ `ThreadBackend` دون شهادات Toolforge.
- اختبارات وحدة للـ backend مع `http_client` وهمي (الصنف يقبل حقنه).
- اختبار تكامل على Toolforge لمهمة واحدة غير حرجة قبل التعميم.

## 11. ما زلت أحتاجه للتدقيق النهائي

- الفئة الأساسية للمهام (`BaseObjectsJobWorker`) وفئة مهمة واحدة: من يضبط الحالة النهائية، وهل تفحص `cancel_event` والملف وقاعدة البيانات، وهل تستخدم `runner.user` أو `g`.
- `jobs_files_service.py` (ملف `.cancelled`) و`http_client.py` (المهلة وإعادة المحاولة).
- ناتج `toolforge jobs list` الحالي، وتأكيد أن `~/shs/` هو مكان السكربتات وأن `~` تُحَل في `cmd`.
- مسار استيراد `TokenManager` و`UserTokenService` داخل `jobs_workers` (قد يسبب استيرادًا دائريًا).
