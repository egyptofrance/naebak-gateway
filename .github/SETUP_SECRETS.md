# إعداد GitHub Secrets للمشروع

## الأسرار المطلوبة

لضمان عمل CI/CD pipeline بشكل صحيح، يجب إعداد الأسرار التالية في مستودع GitHub:

### 1. أسرار Google Cloud Platform

```
GCP_PROJECT_ID
```
- **الوصف**: معرف مشروع Google Cloud
- **المثال**: `naibak-production-123456`
- **الاستخدام**: نشر الخدمات على Google Cloud Run

```
GCP_SA_KEY
```
- **الوصف**: مفتاح حساب الخدمة لـ Google Cloud (JSON format)
- **كيفية الحصول عليه**:
  1. اذهب إلى Google Cloud Console
  2. IAM & Admin > Service Accounts
  3. أنشئ حساب خدمة جديد أو استخدم موجود
  4. أنشئ مفتاح JSON جديد
  5. انسخ محتوى ملف JSON كاملاً
- **الصلاحيات المطلوبة**:
  - Cloud Run Admin
  - Storage Admin
  - Container Registry Service Agent

### 2. أسرار قاعدة البيانات

```
DATABASE_URL
```
- **الوصف**: رابط الاتصال بقاعدة البيانات للإنتاج
- **المثال**: `postgresql://user:password@host:5432/database`
- **الاستخدام**: الاتصال بقاعدة البيانات في بيئة الإنتاج

```
REDIS_URL
```
- **الوصف**: رابط الاتصال بـ Redis للإنتاج
- **المثال**: `redis://user:password@host:6379/0`
- **الاستخدام**: التخزين المؤقت والجلسات

### 3. أسرار الأمان

```
SECRET_KEY
```
- **الوصف**: مفتاح سري لـ Django
- **كيفية إنشاؤه**:
  ```python
  from django.core.management.utils import get_random_secret_key
  print(get_random_secret_key())
  ```
- **الاستخدام**: تشفير الجلسات والتوقيعات

```
JWT_SECRET_KEY
```
- **الوصف**: مفتاح سري لـ JWT tokens
- **المثال**: مفتاح عشوائي طويل (256 bit)
- **الاستخدام**: توقيع وتحقق JWT tokens

### 4. أسرار الخدمات الخارجية

```
OPENAI_API_KEY
```
- **الوصف**: مفتاح API لـ OpenAI (إذا كان مستخدماً)
- **الاستخدام**: خدمات الذكاء الاصطناعي

```
SENTRY_DSN
```
- **الوصف**: رابط Sentry لمراقبة الأخطاء
- **الاستخدام**: تتبع الأخطاء في الإنتاج

### 5. أسرار التنبيهات

```
SLACK_WEBHOOK_URL
```
- **الوصف**: رابط webhook لإرسال تنبيهات Slack
- **الاستخدام**: إشعارات CI/CD والنشر

```
DISCORD_WEBHOOK_URL
```
- **الوصف**: رابط webhook لإرسال تنبيهات Discord
- **الاستخدام**: إشعارات CI/CD والنشر

## كيفية إعداد الأسرار

### 1. عبر واجهة GitHub

1. اذهب إلى مستودع GitHub الخاص بك
2. انقر على **Settings**
3. في القائمة الجانبية، انقر على **Secrets and variables** > **Actions**
4. انقر على **New repository secret**
5. أدخل اسم السر والقيمة
6. انقر على **Add secret**

### 2. عبر GitHub CLI

```bash
# تثبيت GitHub CLI إذا لم يكن مثبتاً
# https://cli.github.com/

# تسجيل الدخول
gh auth login

# إضافة سر
gh secret set SECRET_NAME --body "secret_value"

# إضافة سر من ملف
gh secret set GCP_SA_KEY < path/to/service-account-key.json

# عرض قائمة الأسرار
gh secret list
```

### 3. عبر GitHub API

```bash
# إضافة سر عبر API
curl -X PUT \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/actions/secrets/SECRET_NAME \
  -d '{"encrypted_value":"ENCRYPTED_VALUE","key_id":"KEY_ID"}'
```

## متغيرات البيئة للتطوير المحلي

أنشئ ملف `.env` في جذر المشروع (لا تضعه في Git):

```bash
# .env
DEBUG=True
SECRET_KEY=your-local-secret-key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/naibak_dev
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-openai-key
AI_GOVERNANCE_ENABLED=True
MINIMUM_TEST_COVERAGE=90
```

## التحقق من الإعداد

بعد إعداد الأسرار، يمكنك التحقق من صحة الإعداد:

### 1. تشغيل GitHub Actions

```bash
# إنشاء commit جديد لتشغيل pipeline
git add .
git commit -m "Test CI/CD setup"
git push origin main
```

### 2. فحص logs

1. اذهب إلى تبويب **Actions** في مستودع GitHub
2. انقر على آخر workflow run
3. تحقق من logs كل job
4. تأكد من عدم وجود أخطاء متعلقة بالأسرار

### 3. اختبار النشر

```bash
# للفروع المسموحة (main/develop)
git checkout main
git push origin main
# تحقق من نجاح النشر على Google Cloud Run
```

## أمان الأسرار

### أفضل الممارسات:

1. **لا تضع أسرار في الكود أبداً**
2. **استخدم أسرار مختلفة لكل بيئة** (development, staging, production)
3. **قم بتدوير الأسرار بانتظام**
4. **استخدم أقل الصلاحيات المطلوبة**
5. **راقب استخدام الأسرار**

### فحص الأمان:

```bash
# فحص الكود للأسرار المكشوفة
git secrets --scan
truffleHog --regex --entropy=False .
```

## استكشاف الأخطاء

### مشاكل شائعة:

**1. "Secret not found"**
- تأكد من كتابة اسم السر بشكل صحيح
- تأكد من أن السر موجود في repository secrets

**2. "Invalid GCP credentials"**
- تأكد من صحة ملف JSON
- تأكد من صلاحيات حساب الخدمة

**3. "Database connection failed"**
- تأكد من صحة DATABASE_URL
- تأكد من إمكانية الوصول للقاعدة من GitHub Actions

**4. "Permission denied"**
- تأكد من صلاحيات حساب الخدمة
- تأكد من تفعيل APIs المطلوبة في Google Cloud

## مراقبة الأسرار

### إعداد تنبيهات:

1. **GitHub Security Alerts** - لمراقبة تسريب الأسرار
2. **Google Cloud Audit Logs** - لمراقبة استخدام حسابات الخدمة
3. **Sentry** - لمراقبة أخطاء الاتصال

### مراجعة دورية:

- راجع قائمة الأسرار شهرياً
- احذف الأسرار غير المستخدمة
- حدث الأسرار المنتهية الصلاحية
- راجع logs الوصول للأسرار
