# قالب المايكروسيرفس المتقدم لتطبيق "نائبك" مع نظام حاكم للذكاء الاصطناعي

## نظرة عامة

هذا القالب هو نقطة انطلاق شاملة لبناء خدمات مايكروسيرفس قوية وآمنة وقابلة للتطوير لتطبيق "نائبك"، مع تركيز خاص على **حوكمة الذكاء الاصطناعي (AI Governance)**. تم تصميم القالب لتوفير هيكل محدد يوجه نماذج الذكاء الاصطناعي المساعدة في البرمجة، مع دمج اختبارات تلقائية لمنع المبالغة في التقارير وضمان جودة الكود.

### الميزات الرئيسية:

- **هيكل موجه للخدمات**: تصميم مرن يسمح بإضافة خدمات جديدة بسهولة.
- **نظام حاكم للذكاء الاصطناعي**: وحدة متكاملة للتحكم في استخدام نماذج الذكاء الاصطناعي ومراقبته.
- **أمان متقدم**: إعدادات أمان قوية باستخدام JWT، CORS، وإدارة الأسرار عبر Google Cloud Secret Manager.
- **اختبارات شاملة**: إطار عمل متكامل للاختبارات (unit, integration, security, performance) باستخدام `pytest`.
- **CI/CD متكامل**: خط أنابيب CI/CD جاهز للاستخدام مع GitHub Actions للنشر على Google Cloud Run.
- **مراقبة وأداء (Observability)**: تكامل مع Prometheus, Grafana, و ELK/EFK للمراقبة وتحليل السجلات.
- **توثيق تلقائي**: إنشاء توثيق للـ API تلقائياً باستخدام OpenAPI (Swagger).

---

## هيكل المشروع

تم تصميم هيكل المشروع ليكون قابلاً للتطوير وواضحاً، حيث يتم فصل كل جزء من التطبيق في مجلده الخاص.

```
/naibak-gateway-template
├── .github/                    # GitHub Actions CI/CD workflows
│   └── workflows/
│       └── ci-cd.yml
├── app/                        # مجلد التطبيقات الأساسية
│   ├── ai_governance/          # وحدة التحكم في الذكاء الاصطناعي
│   │   ├── filters.py          # فلاتر المحتوى (تحيز، ألفاظ نابية، ...)
│   │   ├── middleware.py       # ميدل وير للتحقق من الطلبات
│   │   ├── models.py           # نماذج لتتبع استخدام الـ AI
│   │   ├── serializers.py      # سيريلايزرز للـ API
│   │   ├── urls.py             # روابط الـ API الخاصة بالـ AI
│   │   ├── utils/              # أدوات مساعدة (rate limiter, quota checker)
│   │   └── views.py            # واجهات الـ API
│   ├── core/                   # التطبيق الأساسي (مصادقة، مستخدمين، ...)
│   └── monitoring/             # تطبيق المراقبة (health checks, metrics)
├── config/                     # إعدادات المشروع (Django)
│   ├── settings.py             # الإعدادات الرئيسية
│   ├── urls.py                 # الروابط الرئيسية
│   └── wsgi.py                 # إعدادات WSGI
├── deployment/                 # ملفات وإعدادات النشر
├── docs/                       # التوثيق
├── governance/                 # ملفات حاكمة لنموذج الذكاء الاصطناعي
├── monitoring/                 # إعدادات المراقبة (Prometheus, Grafana)
├── nginx/                      # إعدادات Nginx
├── scripts/                    # سكريبتات مساعدة (deploy.sh)
├── tests/                      # الاختبارات
│   ├── unit/                   # اختبارات الوحدات
│   ├── integration/            # اختبارات التكامل
│   ├── security/               # اختبارات الأمان
│   ├── performance/            # اختبارات الأداء
│   └── governance/             # اختبارات نظام الحوكمة
├── .env.example                # مثال لملف متغيرات البيئة
├── Dockerfile                  # ملف بناء حاوية Docker
├── docker-compose.yml          # إعدادات Docker Compose للتطوير المحلي
├── manage.py                   # أداة إدارة Django
├── pytest.ini                  # إعدادات Pytest
└── requirements.txt            # الاعتماديات
```

---

## البدء السريع (Quick Start)

اتبع هذه الخطوات لتشغيل المشروع محلياً باستخدام Docker.

### المتطلبات:

- Docker
- Docker Compose

### خطوات التشغيل:

1.  **نسخ المشروع:**
    ```bash
    git clone <repository_url>
    cd naibak-gateway-template
    ```

2.  **إعداد متغيرات البيئة:**
    انسخ ملف `.env.example` إلى `.env` واملأ المتغيرات المطلوبة.
    ```bash
    cp .env.example .env
    ```
    تأكد من تعيين `SECRET_KEY` وقيم أخرى.

3.  **بناء وتشغيل الحاويات:**
    ```bash
    docker-compose up --build -d
    ```
    هذا الأمر سيقوم ببناء وتشغيل جميع الخدمات (app, postgres, redis, ...).

4.  **تشغيل الـ Migrations:**
    ```bash
    docker-compose exec app python manage.py migrate
    ```

5.  **إنشاء مستخدم أدمن:**
    ```bash
    docker-compose exec app python manage.py createsuperuser
    ```

6.  **الوصول للتطبيق:**
    - **API:** `http://localhost:8000/api/v1/`
    - **Admin:** `http://localhost:8000/admin/`
    - **Swagger Docs:** `http://localhost:8000/api/docs/`
    - **Grafana:** `http://localhost:3000` (user: `admin`, pass: `admin123`)
    - **Kibana:** `http://localhost:5601`

---

## نظام حوكمة الذكاء الاصطناعي (AI Governance)

هذا هو الجزء المركزي من القالب، وهو مصمم لتوفير تحكم كامل في كيفية استخدام نماذج الذكاء الاصطناعي داخل التطبيق.

### المكونات:

- **تتبع الطلبات (`AIRequest` model):** يتم تسجيل كل طلب يتم إرساله إلى أي نموذج ذكاء اصطناعي، بما في ذلك الـ prompt، الـ response، عدد الـ tokens، والتكلفة.
- **تحديد الحصص (`AIUsageQuota` model):** يمكنك تحديد حصص استخدام (rate limits) لكل مستخدم أو جلسة (session) أو على مستوى النظام ككل (يومياً، شهرياً، ...).
- **فلاتر المحتوى (`Content Filters`):**
    - **فلتر الألفاظ النابية (`ProfanityFilter`):** يمنع استخدام الألفاظ غير اللائقة في الـ prompts والـ responses.
    - **فلتر التحيز (`BiasDetectionFilter`):** يكتشف ويحاول التخفيف من التحيز (الجنسي، العرقي، الديني) في المحتوى.
    - **فلتر التحقق من الحقائق (`FactCheckFilter`):** يضيف تنبيهات للمحتوى الذي يبدو أنه يقدم حقائق غير موثوقة أو مبالغ فيها.
- **سجل تدقيق (`AIAuditLog`):** يسجل جميع الإجراءات المتعلقة بالحوكمة (مثل حظر طلب، تجاوز الحصة، ...) لأغراض المراجعة والأمان.
- **Middleware:** يتم تطبيق جميع قواعد الحوكمة تلقائياً عبر middleware خاص بالـ AI.

### كيف يعمل؟

1.  عندما يتم إرسال طلب إلى endpoint خاص بالـ AI، يقوم `AIGovernanceMiddleware` باعتراضه.
2.  يتم التحقق من الـ rate limits وحصص الاستخدام.
3.  يتم تمرير الـ prompt عبر فلاتر المحتوى لتنظيفه والتحقق منه.
4.  يتم إرسال الـ prompt إلى نموذج الذكاء الاصطناعي.
5.  يتم تمرير الـ response المستلم من النموذج عبر فلاتر المحتوى مرة أخرى.
6.  يتم تسجيل الطلب والرد والتكلفة ونتائج الفلاتر في قاعدة البيانات.
7.  يتم إرسال الرد النهائي إلى المستخدم.

---

## الاختبارات

يحتوي القالب على مجموعة شاملة من الاختبارات لضمان جودة الكود واستقراره.

### أنواع الاختبارات:

- **Unit Tests:** لاختبار المكونات الفردية بشكل معزول.
- **Integration Tests:** لاختبار تفاعل المكونات مع بعضها البعض.
- **Security Tests:** لاختبار الثغرات الأمنية الشائعة (SQL injection, XSS, ...).
- **Governance Tests:** لاختبار فعالية نظام حوكمة الذكاء الاصطناعي.

### كيفية تشغيل الاختبارات:

```bash
# تشغيل جميع الاختبارات
docker-compose exec app pytest

# تشغيل نوع معين من الاختبارات (e.g., unit)
docker-compose exec app pytest tests/unit/

# تشغيل الاختبارات مع تقرير تغطية الكود
docker-compose exec app pytest --cov=app
```

---

## CI/CD و النشر

يستخدم القالب **GitHub Actions** لأتمتة عمليات الاختبار والنشر على **Google Cloud Run**.

### خطوات الـ CI/CD Pipeline:

1.  **Security Scan:** فحص الكود بحثاً عن ثغرات أمنية باستخدام `Bandit`, `Safety`, `Semgrep`.
2.  **Code Quality:** التحقق من جودة الكود وتنسيقه باستخدام `Black`, `Flake8`, `isort`.
3.  **Unit Tests:** تشغيل اختبارات الوحدات.
4.  **Integration & Security Tests:** تشغيل اختبارات التكامل والأمان.
5.  **Build & Push:** بناء حاوية Docker ودفعها إلى Google Container Registry (GCR).
6.  **Deploy to Staging:** نشر الإصدار الجديد على بيئة الـ Staging (عند الدفع إلى فرع `develop`).
7.  **Deploy to Production:** نشر الإصدار الجديد على بيئة الـ Production (عند الدفع إلى فرع `main`) مع ترحيل تدريجي للحركة (gradual traffic migration).

### كيفية النشر:

1.  **إعداد Google Cloud:**
    - قم بإنشاء مشروع على Google Cloud.
    - قم بتفعيل APIs: Cloud Run, Cloud Build, Secret Manager.
    - قم بإنشاء Service Account مع الصلاحيات اللازمة (Cloud Run Admin, Storage Admin, Secret Manager Accessor).
    - قم بإنشاء مفتاح JSON للـ Service Account.

2.  **إعداد GitHub Secrets:**
    أضف المتغيرات التالية كـ secrets في مستودع GitHub:
    - `GCP_PROJECT_ID`: معرف مشروعك على Google Cloud.
    - `GCP_SA_KEY`: محتوى ملف الـ JSON الخاص بالـ Service Account.

3.  **النشر:**
    - **Staging:** قم بالدفع (push) إلى فرع `develop`.
    - **Production:** قم بدمج التغييرات في فرع `main` وقم بالدفع.

يمكنك أيضاً استخدام السكريبت اليدوي للنشر:
```bash
./scripts/deploy.sh
```

---

## المراقبة والأداء (Observability)

تم إعداد القالب مع أدوات مراقبة قوية للمساعدة في تتبع أداء التطبيق وتشخيص المشكلات.

- **Prometheus:** لجمع المقاييس (metrics) من التطبيق وقاعدة البيانات والخدمات الأخرى.
- **Grafana:** لعرض المقاييس في لوحات تحكم (dashboards) تفاعلية.
- **ELK/EFK Stack (Elasticsearch, Fluentd, Kibana):** لتحليل السجلات (logs) والبحث فيها.

### Endpoints:

- **Metrics:** `http://localhost:8000/metrics` (يتم جمعها بواسطة Prometheus)
- **Health Check:** `http://localhost:8000/health`

---

## التوثيق

- **API Documentation:** يتم إنشاء توثيق OpenAPI (Swagger) تلقائياً. يمكنك الوصول إليه عبر `/api/docs/`.
- **README:** هذا الملف يوفر نظرة شاملة على المشروع.
- **Code Comments:** تم إضافة تعليقات توضيحية للكود لشرح الأجزاء المعقدة.

---

## المساهمة

نرحب بالمساهمات لتحسين هذا القالب. يرجى اتباع الخطوات التالية:

1.  قم بعمل Fork للمستودع.
2.  قم بإنشاء فرع جديد (`git checkout -b feature/your-feature`).
3.  قم بإجراء التغييرات المطلوبة.
4.  تأكد من أن جميع الاختبارات تعمل بنجاح.
5.  قم بإنشاء Pull Request.

