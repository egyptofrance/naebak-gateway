# دليل الإعداد السريع - تمبلت مايكروسيرفس "نائبك"

## 🚀 البدء السريع (5 دقائق)

### 1. استنساخ التمبلت
```bash
# استنساخ التمبلت
git clone <your-repo-url> my-naibak-service
cd my-naibak-service

# إنشاء مستودع جديد
rm -rf .git
git init
git add .
git commit -m "Initial commit from Naibak template"
```

### 2. إعداد البيئة المحلية
```bash
# إنشاء بيئة افتراضية
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate     # Windows

# تثبيت التبعيات
pip install -r requirements.txt

# نسخ ملف البيئة
cp .env.example .env
# عدل .env حسب إعداداتك
```

### 3. إعداد قاعدة البيانات
```bash
# PostgreSQL (مُوصى به)
createdb naibak_dev
createdb test_naibak

# أو SQLite (للتطوير السريع)
# عدل DATABASE_URL في .env إلى:
# DATABASE_URL=sqlite:///db.sqlite3

# تشغيل الهجرات
python manage.py migrate
```

### 4. إعداد Pre-commit Hooks
```bash
# تثبيت pre-commit
pip install pre-commit

# تفعيل hooks
pre-commit install

# اختبار الـ hooks
pre-commit run --all-files
```

### 5. تشغيل الاختبارات
```bash
# تشغيل جميع الاختبارات
pytest

# تشغيل اختبارات محددة
pytest tests/unit/
pytest tests/governance/
pytest -m "not slow"
```

### 6. تشغيل الخدمة
```bash
# تشغيل خادم التطوير
python manage.py runserver

# أو باستخدام Docker
docker-compose up -d
```

## 🔧 إعداد GitHub Repository

### 1. إنشاء مستودع GitHub
```bash
# إنشاء مستودع جديد على GitHub
gh repo create my-naibak-service --public
# أو
gh repo create my-naibak-service --private

# ربط المستودع المحلي
git remote add origin https://github.com/username/my-naibak-service.git
git push -u origin main
```

### 2. إعداد GitHub Secrets
اتبع الدليل في `.github/SETUP_SECRETS.md` لإعداد الأسرار المطلوبة:

**الأسرار الأساسية:**
- `SECRET_KEY` - مفتاح Django السري
- `DATABASE_URL` - رابط قاعدة البيانات
- `GCP_PROJECT_ID` - معرف مشروع Google Cloud
- `GCP_SA_KEY` - مفتاح حساب الخدمة

```bash
# إضافة الأسرار عبر GitHub CLI
gh secret set SECRET_KEY --body "your-secret-key"
gh secret set DATABASE_URL --body "postgresql://..."
```

### 3. تفعيل GitHub Actions
```bash
# دفع الكود لتشغيل أول pipeline
git add .
git commit -m "Setup GitHub Actions"
git push origin main

# مراقبة النتائج
gh run list
gh run view --log
```

## 🐳 إعداد Docker (اختياري)

### 1. بناء الصورة
```bash
# بناء صورة Docker
docker build -t my-naibak-service .

# تشغيل الحاوية
docker run -p 8000:8000 my-naibak-service
```

### 2. استخدام Docker Compose
```bash
# تشغيل جميع الخدمات
docker-compose up -d

# عرض السجلات
docker-compose logs -f

# إيقاف الخدمات
docker-compose down
```

## ☁️ النشر على Google Cloud Run

### 1. إعداد Google Cloud
```bash
# تسجيل الدخول
gcloud auth login

# تعيين المشروع
gcloud config set project YOUR_PROJECT_ID

# تفعيل APIs المطلوبة
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. النشر اليدوي (للاختبار)
```bash
# بناء ورفع الصورة
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/my-naibak-service

# النشر على Cloud Run
gcloud run deploy my-naibak-service \
  --image gcr.io/YOUR_PROJECT_ID/my-naibak-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### 3. النشر التلقائي
النشر التلقائي سيحدث عبر GitHub Actions عند:
- Push على فرع `main` → نشر إنتاج
- Push على فرع `develop` → نشر staging

## 🔍 التحقق من الإعداد

### 1. فحص الصحة العامة
```bash
# فحص Django
python manage.py check

# فحص الهجرات
python manage.py makemigrations --check

# فحص الأمان
python manage.py check --deploy
```

### 2. فحص AI Governance
```bash
# فحص قواعد الحوكمة
python scripts/ai_governance_hook.py app/

# فحص نسبة الكود للاختبارات
python scripts/code_test_ratio_check.py

# فحص التغطية
python scripts/coverage_check.py
```

### 3. فحص الأمان
```bash
# فحص الثغرات الأمنية
bandit -r app/

# فحص التبعيات
safety check

# فحص الأسرار
detect-secrets scan --baseline .secrets.baseline
```

## 🎯 الخطوات التالية

### 1. تخصيص الخدمة
- عدل `app/` لإضافة منطق عملك
- أضف نماذج البيانات في `app/models.py`
- أضف APIs في `app/views.py`
- أضف اختبارات في `tests/`

### 2. إعداد المراقبة
```bash
# تشغيل Prometheus
docker-compose -f monitoring/docker-compose.yml up -d

# الوصول للـ dashboards
# Grafana: http://localhost:3000
# Prometheus: http://localhost:9090
```

### 3. إعداد التوثيق
- عدل `README.md` ليناسب خدمتك
- أضف مخطط OpenAPI في `docs/openapi.yaml`
- وثق APIs باستخدام Django REST framework

## 🆘 استكشاف الأخطاء

### مشاكل شائعة:

**1. فشل pre-commit hooks**
```bash
# تحديث hooks
pre-commit autoupdate

# تشغيل hook محدد
pre-commit run black --all-files
```

**2. فشل الاختبارات**
```bash
# تشغيل اختبار محدد
pytest tests/unit/test_specific.py -v

# تجاهل الاختبارات البطيئة
pytest -m "not slow"
```

**3. مشاكل قاعدة البيانات**
```bash
# إعادة تعيين قاعدة البيانات
python manage.py flush
python manage.py migrate
```

**4. مشاكل Docker**
```bash
# إعادة بناء الصورة
docker-compose build --no-cache

# تنظيف الحاويات
docker-compose down -v
```

## 📞 الدعم

- **التوثيق الكامل**: `README.md`
- **قواعد الحوكمة**: `governance/ai_governance_rules.yaml`
- **إعداد الأسرار**: `.github/SETUP_SECRETS.md`
- **نظام الحوكمة**: `README_GOVERNANCE.md`

للمساعدة الإضافية، راجع الملفات المذكورة أو أنشئ issue في المستودع.
