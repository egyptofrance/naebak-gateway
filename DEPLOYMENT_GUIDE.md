# دليل النشر التلقائي لتطبيق "نائبك"

## نظرة عامة

التمبلت الآن يدعم **النشر التلقائي الكامل** إلى Google Cloud Run بدون تدخل يدوي من Manus أو أي طرف ثالث.

## 🚀 كيف يعمل النشر التلقائي

### التشغيل التلقائي
النشر يحدث تلقائياً عند:
- **Push على فرع `main`** → نشر إنتاج (Production)
- **Push على فرع `develop`** → نشر تجريبي (Staging)
- **تشغيل يدوي** → اختيار البيئة المطلوبة

### مراحل النشر التلقائي

#### 1. **مرحلة الاختبارات الشاملة**
- اختبارات الوحدة (Unit Tests)
- اختبارات التكامل (Integration Tests)
- اختبارات الأمان (Security Tests)
- اختبارات حوكمة الذكاء الاصطناعي
- فحص التغطية (90% إجباري)
- فحص جودة الكود

#### 2. **مرحلة البناء والأمان**
- بناء Docker image
- فحص أمني للصورة باستخدام Trivy
- رفع الصورة إلى Google Container Registry

#### 3. **مرحلة النشر الذكي**
- نشر الخدمة على Google Cloud Run
- فحص صحة الخدمة (Health Check)
- **نشر تدريجي للإنتاج:**
  - 10% من الترافيك → فحص صحة
  - 50% من الترافيك → فحص صحة
  - 100% من الترافيك → اكتمال النشر
- **استرجاع تلقائي** في حالة فشل أي فحص

#### 4. **مرحلة التنظيف والمراقبة**
- حذف النسخ القديمة (الاحتفاظ بآخر 5 نسخ)
- فحص حوكمة الذكاء الاصطناعي بعد النشر
- إرسال إشعارات النجاح/الفشل

## ⚙️ الإعداد المطلوب (مرة واحدة فقط)

### 1. إعداد Google Cloud Project
```bash
# إنشاء مشروع جديد
gcloud projects create your-naibak-project-id

# تفعيل APIs المطلوبة
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

### 2. إنشاء حساب خدمة
```bash
# إنشاء حساب خدمة
gcloud iam service-accounts create naibak-deployer \
    --description="Service account for Naibak deployments" \
    --display-name="Naibak Deployer"

# منح الصلاحيات المطلوبة
gcloud projects add-iam-policy-binding your-naibak-project-id \
    --member="serviceAccount:naibak-deployer@your-naibak-project-id.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding your-naibak-project-id \
    --member="serviceAccount:naibak-deployer@your-naibak-project-id.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding your-naibak-project-id \
    --member="serviceAccount:naibak-deployer@your-naibak-project-id.iam.gserviceaccount.com" \
    --role="roles/secretmanager.admin"

# إنشاء مفتاح JSON
gcloud iam service-accounts keys create naibak-deployer-key.json \
    --iam-account=naibak-deployer@your-naibak-project-id.iam.gserviceaccount.com
```

### 3. إعداد قواعد البيانات
```bash
# إنشاء PostgreSQL instance
gcloud sql instances create naibak-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1

# إنشاء قواعد البيانات
gcloud sql databases create naibak_production --instance=naibak-db
gcloud sql databases create naibak_staging --instance=naibak-db

# إنشاء Redis instance
gcloud redis instances create naibak-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_6_x
```

### 4. إعداد الأسرار في Google Secret Manager
```bash
# Django Secret Key
echo -n "your-super-secret-django-key" | gcloud secrets create django-secret-key --data-file=-

# Database URLs
echo -n "postgresql://user:password@host:5432/naibak_production" | gcloud secrets create database-url-production --data-file=-
echo -n "postgresql://user:password@host:5432/naibak_staging" | gcloud secrets create database-url-staging --data-file=-

# Redis URLs
echo -n "redis://redis-host:6379/0" | gcloud secrets create redis-url-production --data-file=-
echo -n "redis://redis-host:6379/1" | gcloud secrets create redis-url-staging --data-file=-

# OpenAI API Key
echo -n "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-

# JWT Secret Key
echo -n "your-jwt-secret-key" | gcloud secrets create jwt-secret-key --data-file=-
```

### 5. إعداد GitHub Secrets
في مستودع GitHub، أضف الأسرار التالية:

```
GCP_PROJECT_ID = your-naibak-project-id
GCP_SA_KEY = [محتوى ملف naibak-deployer-key.json كاملاً]
SLACK_WEBHOOK_URL = https://hooks.slack.com/... (اختياري)
```

## 🔄 كيفية استخدام النشر التلقائي

### النشر التلقائي (الطريقة المُوصى بها)
```bash
# للنشر على الإنتاج
git checkout main
git add .
git commit -m "Add new feature"
git push origin main
# ← النشر سيحدث تلقائياً

# للنشر على التجريبي
git checkout develop
git add .
git commit -m "Test new feature"
git push origin develop
# ← النشر سيحدث تلقائياً
```

### النشر اليدوي (عند الحاجة)
```bash
# من واجهة GitHub
# اذهب إلى Actions → Auto Deploy to Google Cloud Run → Run workflow
# اختر البيئة المطلوبة (staging/production)
```

### مراقبة النشر
```bash
# مراقبة عبر GitHub Actions
gh run list
gh run view --log

# مراقبة عبر Google Cloud
gcloud run services list
gcloud run services describe naibak-gateway --region=us-central1

# فحص الصحة
curl https://your-service-url/health/
```

## 📊 مراقبة ما بعد النشر

### URLs مهمة بعد النشر
- **الخدمة الرئيسية:** `https://naibak-gateway-xxx.a.run.app`
- **فحص الصحة:** `https://naibak-gateway-xxx.a.run.app/health/`
- **توثيق API:** `https://naibak-gateway-xxx.a.run.app/api/docs/`
- **مقاييس الحوكمة:** `https://naibak-gateway-xxx.a.run.app/api/ai-governance/metrics/`

### مراقبة الأداء
```bash
# عرض logs الخدمة
gcloud logs read "resource.type=cloud_run_revision" --limit=50

# مراقبة المقاييس
gcloud monitoring metrics list --filter="resource.type=cloud_run_revision"
```

## 🛠️ استكشاف الأخطاء

### مشاكل شائعة وحلولها

#### 1. فشل المصادقة مع Google Cloud
```bash
# التحقق من صحة Service Account Key
echo $GCP_SA_KEY | base64 -d | jq .

# التأكد من الصلاحيات
gcloud projects get-iam-policy your-naibak-project-id
```

#### 2. فشل الاتصال بقاعدة البيانات
```bash
# التحقق من الأسرار
gcloud secrets versions access latest --secret="database-url-production"

# اختبار الاتصال
gcloud sql connect naibak-db --user=postgres
```

#### 3. فشل فحص الصحة
```bash
# فحص logs الخدمة
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=naibak-gateway" --limit=20

# اختبار محلي
docker run -p 8000:8000 gcr.io/your-project/naibak-gateway:latest
curl http://localhost:8000/health/
```

#### 4. فشل اختبارات الحوكمة
```bash
# تشغيل اختبارات الحوكمة محلياً
python scripts/ai_governance_hook.py app/
python scripts/coverage_check.py

# فحص إعدادات الحوكمة
cat governance/ai_governance_rules.yaml
```

## 🔄 الاسترجاع (Rollback)

### استرجاع تلقائي
النظام يسترجع تلقائياً في حالة:
- فشل فحص الصحة
- ارتفاع معدل الأخطاء
- فشل اختبارات ما بعد النشر

### استرجاع يدوي
```bash
# عبر Google Cloud Console
gcloud run services update-traffic naibak-gateway \
    --to-revisions=naibak-gateway-previous-revision=100 \
    --region=us-central1

# أو استخدام السكريبت
./scripts/deploy.sh rollback
```

## 📈 تحسين الأداء

### إعدادات الإنتاج المُحسنة
- **الذاكرة:** 2GB
- **المعالج:** 2 CPU
- **الحد الأقصى للمثيلات:** 100
- **الحد الأدنى للمثيلات:** 1
- **التزامن:** 80 طلب لكل مثيل

### إعدادات التجريبي
- **الذاكرة:** 1GB
- **المعالج:** 1 CPU
- **الحد الأقصى للمثيلات:** 10
- **الحد الأدنى للمثيلات:** 0
- **التزامن:** 40 طلب لكل مثيل

## 🔐 الأمان

### الأمان المُطبق تلقائياً
- فحص أمني للكود قبل النشر
- فحص أمني لصورة Docker
- استخدام Google Secret Manager للأسرار
- تشفير البيانات في النقل والتخزين
- تطبيق قواعد حوكمة الذكاء الاصطناعي

### مراجعة أمنية دورية
```bash
# فحص الثغرات الأمنية
bandit -r app/
safety check

# فحص صورة Docker
trivy image gcr.io/your-project/naibak-gateway:latest
```

## 📞 الدعم والمساعدة

### في حالة مواجهة مشاكل:
1. **تحقق من GitHub Actions logs**
2. **راجع Google Cloud Run logs**
3. **تأكد من صحة الأسرار والإعدادات**
4. **اختبر محلياً قبل النشر**

### موارد مفيدة:
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

## ✅ الخلاصة

**نعم، التمبلت يضمن النشر التلقائي الكامل** بدون الحاجة لتدخل Manus أو أي طرف ثالث. بمجرد الإعداد الأولي (مرة واحدة)، كل push على الفروع المحددة سيؤدي إلى نشر تلقائي مع جميع الفحوصات والضمانات المطلوبة.
