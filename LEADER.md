# 🌐 LEADER - دليل خدمة البوابة (API Gateway)

**اسم الخدمة:** naebak-gateway-service  
**المنفذ:** 8013  
**الإطار:** Flask 2.3  
**قاعدة البيانات:** SQLite (للتسجيل والمراقبة)  
**النوع:** API Gateway (بوابة واجهات برمجة التطبيقات)  

---

## 📋 **نظرة عامة على الخدمة**

### **🎯 الغرض الأساسي:**
خدمة البوابة هي **النقطة المركزية للتنسيق** بين جميع الخدمات المصغرة في منصة نائبك، تعمل كـ **API Gateway** موحد يربط جميع الخدمات ويخرج التطبيق ككتلة واحدة متماسكة. كما تعمل كـ **مدير البيانات المرجعية المشتركة** مثل الأحزاب والمجالس والدوائر الانتخابية.

### **📝 كيف يعمل التطبيق بالضبط:**

**للمطور - فهم التنسيق:**
1. **جميع الطلبات** من الواجهة الأمامية تمر عبر البوابة أولاً
2. البوابة **تحلل الطلب** وتحدد الخدمة المناسبة
3. **توجه الطلب** للخدمة المحددة مع إضافة headers مطلوبة
4. **تستقبل الاستجابة** من الخدمة وتعيد تنسيقها
5. **ترسل الاستجابة الموحدة** للواجهة الأمامية

**للأدمن - إدارة البيانات المرجعية المشتركة:**
1. **يدخل لوحة إدارة Gateway** لتعديل البيانات المشتركة
2. **يضيف/يعدل/يحذف** الأحزاب، المجالس، الدوائر الانتخابية، الرموز
3. **Gateway تحفظ التغييرات** في قاعدة بياناتها المركزية
4. **تُرسل تحديثات فورية** لجميع الخدمات المتأثرة
5. **جميع الخدمات تستقبل البيانات المحدثة** تلقائياً

**مثال عملي لإدارة البيانات المشتركة:**
```
الأدمن يضيف حزب جديد "حزب المستقبل" في Gateway
↓
Gateway تحفظ الحزب الجديد في قاعدة بياناتها
↓
Gateway ترسل تحديث لجميع الخدمات:
- خدمة المصادقة (لتسجيل المرشحين)
- خدمة الشكاوى (لتصنيف الشكاوى حسب الحزب)
- خدمة التقييمات (لمقارنة أداء الأحزاب)
- خدمة الإحصائيات (لإحصائيات الأحزاب)
↓
جميع الخدمات تحدث قوائمها المحلية فوراً
↓
المستخدمون يرون الحزب الجديد في جميع أنحاء المنصة
```

**مثال عملي للتوجيه:**
```
طلب من الواجهة: GET /api/complaints/list/
↓
البوابة تحلل: /api/complaints/* → خدمة الشكاوى (8003)
↓
توجيه: GET http://naebak-complaints-service:8003/api/complaints/list/
↓
استقبال الاستجابة وإعادة تنسيقها
↓
إرسال للواجهة: استجابة موحدة مع headers مناسبة
```

**للواجهة الأمامية - نقطة دخول واحدة:**
1. **عنوان واحد فقط:** `https://api.naebak.com` (البوابة)
2. **لا تحتاج معرفة** عناوين الخدمات الفردية
3. **مصادقة موحدة** عبر البوابة
4. **استجابات متسقة** بنفس التنسيق
5. **معالجة أخطاء موحدة** من جميع الخدمات

**مثال للواجهة الأمامية:**
```javascript
// بدلاً من التعامل مع خدمات متعددة:
// http://auth-service:8001/api/login/
// http://complaints-service:8003/api/complaints/
// http://ratings-service:8005/api/ratings/

// الواجهة تتعامل مع البوابة فقط:
const API_BASE = 'https://api.naebak.com';
fetch(`${API_BASE}/api/auth/login/`);
fetch(`${API_BASE}/api/complaints/list/`);
fetch(`${API_BASE}/api/ratings/rate/`);
```

---

## 🌐 **دور الخدمة في منصة نائبك**

### **🏛️ المكانة في النظام:**
البوابة هي **القلب التقني** للمنصة - النقطة التي تربط جميع الخدمات المصغرة وتوحد تفاعلها مع الواجهة الأمامية.

### **📡 العلاقات مع جميع الخدمات:**

#### **🔗 الخدمات المُدارة (جميع الخدمات):**
- **خدمة المصادقة (8001)** - توجيه طلبات تسجيل الدخول والحسابات
- **خدمة الإدارة (8002)** - توجيه طلبات لوحة الإدارة
- **خدمة الشكاوى (8003)** - توجيه طلبات الشكاوى والمتابعة
- **خدمة الرسائل (8004)** - توجيه طلبات المراسلات
- **خدمة التقييمات (8005)** - توجيه طلبات تقييم النواب
- **خدمة عداد الزوار (8006)** - توجيه طلبات العداد
- **خدمة الأخبار (8007)** - توجيه طلبات الشريط الإخباري
- **خدمة الإشعارات (8008)** - توجيه طلبات الإشعارات
- **خدمة البنرات (8009)** - توجيه طلبات إدارة البنرات
- **خدمة المحتوى (8010)** - توجيه طلبات المحتوى
- **خدمة الإحصائيات (8012)** - توجيه طلبات الإحصائيات
- **خدمة الثيمات (8014)** - توجيه طلبات الألوان والثيمات

#### **🔄 الوظائف التنسيقية:**
- **توحيد المصادقة** - فحص JWT tokens مرة واحدة
- **توحيد معالجة الأخطاء** - تنسيق رسائل الخطأ
- **توحيد التسجيل** - تسجيل جميع الطلبات مركزياً
- **توزيع الأحمال** - توجيه الطلبات لأفضل instance متاح

---

## 📊 **البيانات الأساسية من مستودع المخزن**

### **🏛️ البيانات المرجعية المشتركة (مُدارة مركزياً):**
```python
# البيانات التي يديرها Gateway ويوزعها على جميع الخدمات

POLITICAL_PARTIES = [
    {"id": 1, "name": "حزب الوفد", "abbreviation": "الوفد", "founded": 1919, "active": True},
    {"id": 2, "name": "الحزب الوطني الديمقراطي", "abbreviation": "الوطني", "founded": 1978, "active": False},
    {"id": 3, "name": "حزب النور", "abbreviation": "النور", "founded": 2011, "active": True},
    {"id": 4, "name": "حزب المصريين الأحرار", "abbreviation": "المصريين الأحرار", "founded": 2011, "active": True},
    {"id": 5, "name": "حزب مستقبل وطن", "abbreviation": "مستقبل وطن", "founded": 2014, "active": True},
    {"id": 6, "name": "حزب المؤتمر", "abbreviation": "المؤتمر", "founded": 2012, "active": True},
    {"id": 7, "name": "حزب الشعب الجمهوري", "abbreviation": "الشعب الجمهوري", "founded": 2012, "active": True},
    {"id": 8, "name": "حزب التجمع الوطني التقدمي الوحدوي", "abbreviation": "التجمع", "founded": 1976, "active": True},
    {"id": 9, "name": "حزب الغد", "abbreviation": "الغد", "founded": 2004, "active": True},
    {"id": 10, "name": "حزب الدستور", "abbreviation": "الدستور", "founded": 2012, "active": True},
    {"id": 11, "name": "حزب الإصلاح والتنمية", "abbreviation": "الإصلاح والتنمية", "founded": 2011, "active": True},
    {"id": 12, "name": "حزب العدالة", "abbreviation": "العدالة", "founded": 2011, "active": True},
    {"id": 13, "name": "حزب الأصالة", "abbreviation": "الأصالة", "founded": 2011, "active": True},
    {"id": 14, "name": "حزب المحافظين", "abbreviation": "المحافظين", "founded": 2006, "active": True},
    {"id": 15, "name": "حزب الحرية المصري", "abbreviation": "الحرية المصري", "founded": 2011, "active": True},
    {"id": 16, "name": "مستقل", "abbreviation": "مستقل", "founded": None, "active": True}
]

COUNCILS = [
    {
        "id": 1,
        "name": "مجلس النواب",
        "name_en": "House of Representatives", 
        "total_seats": 596,
        "term_years": 5,
        "current_session": "2020-2025",
        "active": True
    },
    {
        "id": 2,
        "name": "مجلس الشيوخ",
        "name_en": "Senate",
        "total_seats": 300,
        "term_years": 5, 
        "current_session": "2020-2025",
        "active": True
    }
]

GOVERNORATES = [
    {"id": 1, "name": "القاهرة", "name_en": "Cairo", "code": "C", "region": "القاهرة الكبرى", "population": 10230350},
    {"id": 2, "name": "الجيزة", "name_en": "Giza", "code": "GZ", "region": "القاهرة الكبرى", "population": 9200000},
    {"id": 3, "name": "القليوبية", "name_en": "Qalyubia", "code": "KB", "region": "القاهرة الكبرى", "population": 5627420},
    {"id": 4, "name": "الإسكندرية", "name_en": "Alexandria", "code": "ALX", "region": "الإسكندرية", "population": 5450000},
    {"id": 5, "name": "البحيرة", "name_en": "Beheira", "code": "BH", "region": "الدلتا", "population": 6200000},
    {"id": 6, "name": "الغربية", "name_en": "Gharbia", "code": "GH", "region": "الدلتا", "population": 5000000},
    {"id": 7, "name": "المنوفية", "name_en": "Monufia", "code": "MN", "region": "الدلتا", "population": 4500000},
    {"id": 8, "name": "الدقهلية", "name_en": "Dakahlia", "code": "DK", "region": "الدلتا", "population": 6500000},
    {"id": 9, "name": "دمياط", "name_en": "Damietta", "code": "DT", "region": "الدلتا", "population": 1500000},
    {"id": 10, "name": "الشرقية", "name_en": "Sharqia", "code": "SH", "region": "الدلتا", "population": 7000000},
    {"id": 11, "name": "كفر الشيخ", "name_en": "Kafr el-Sheikh", "code": "KFS", "region": "الدلتا", "population": 3200000},
    {"id": 12, "name": "البحر الأحمر", "name_en": "Red Sea", "code": "BA", "region": "البحر الأحمر", "population": 400000},
    {"id": 13, "name": "الوادي الجديد", "name_en": "New Valley", "code": "WJ", "region": "الصحراء الغربية", "population": 250000},
    {"id": 14, "name": "مطروح", "name_en": "Matrouh", "code": "MT", "region": "الصحراء الغربية", "population": 450000},
    {"id": 15, "name": "شمال سيناء", "name_en": "North Sinai", "code": "NS", "region": "سيناء", "population": 450000},
    {"id": 16, "name": "جنوب سيناء", "name_en": "South Sinai", "code": "JS", "region": "سيناء", "population": 100000},
    {"id": 17, "name": "السويس", "name_en": "Suez", "code": "SUZ", "region": "القناة", "population": 750000},
    {"id": 18, "name": "الإسماعيلية", "name_en": "Ismailia", "code": "IS", "region": "القناة", "population": 1300000},
    {"id": 19, "name": "بورسعيد", "name_en": "Port Said", "code": "PTS", "region": "القناة", "population": 750000},
    {"id": 20, "name": "المنيا", "name_en": "Minya", "code": "MNA", "region": "الصعيد", "population": 5500000},
    {"id": 21, "name": "بني سويف", "name_en": "Beni Suef", "code": "BNS", "region": "الصعيد", "population": 3200000},
    {"id": 22, "name": "الفيوم", "name_en": "Faiyum", "code": "FYM", "region": "الصعيد", "population": 3600000},
    {"id": 23, "name": "أسيوط", "name_en": "Asyut", "code": "AST", "region": "الصعيد", "population": 4400000},
    {"id": 24, "name": "سوهاج", "name_en": "Sohag", "code": "SHG", "region": "الصعيد", "population": 5200000},
    {"id": 25, "name": "قنا", "name_en": "Qena", "code": "QNA", "region": "الصعيد", "population": 3200000},
    {"id": 26, "name": "الأقصر", "name_en": "Luxor", "code": "LXR", "region": "الصعيد", "population": 1250000},
    {"id": 27, "name": "أسوان", "name_en": "Aswan", "code": "ASW", "region": "الصعيد", "population": 1500000}
]

ELECTORAL_DISTRICTS = [
    # سيتم إضافتها وإدارتها من قبل الأدمن
    {"id": 1, "name": "القاهرة الأولى", "governorate_id": 1, "seats": 15, "active": True},
    {"id": 2, "name": "القاهرة الثانية", "governorate_id": 1, "seats": 12, "active": True},
    # ... المزيد حسب التقسيم الانتخابي
]

ELECTORAL_SYMBOLS = [
    # سيتم إضافتها وإدارتها من قبل الأدمن
    {"id": 1, "name": "الميزان", "image_url": "/symbols/balance.png", "available": True},
    {"id": 2, "name": "النخلة", "image_url": "/symbols/palm.png", "available": False},
    {"id": 3, "name": "الهلال", "image_url": "/symbols/crescent.png", "available": True},
    # ... المزيد من الرموز
]
```

### **🔄 آلية التحديث المركزي:**
```python
UPDATE_MECHANISM = {
    "trigger": "admin_action",  # عند تعديل الأدمن
    "affected_services": [
        "naebak-auth-service",      # لتسجيل المرشحين
        "naebak-complaints-service", # لتصنيف الشكاوى
        "naebak-ratings-service",   # لمقارنة الأداء
        "naebak-statistics-service", # للإحصائيات
        "naebak-content-service",   # لعرض المحتوى
        "naebak-admin-service"      # للوحات الإدارة
    ],
    "update_method": "webhook_notification",
    "fallback_method": "periodic_sync",
    "sync_interval": "every_5_minutes"
}
```

### **🗺️ خريطة توجيه الخدمات:**
```python
SERVICE_ROUTES = {
    "/api/auth/": {
        "service": "naebak-auth-service",
        "port": 8001,
        "description": "خدمة المصادقة والحسابات",
        "health_check": "/health",
        "timeout": 10
    },
    "/api/admin/": {
        "service": "naebak-admin-service", 
        "port": 8002,
        "description": "خدمة الإدارة",
        "health_check": "/health",
        "timeout": 15
    },
    "/api/complaints/": {
        "service": "naebak-complaints-service",
        "port": 8003, 
        "description": "خدمة الشكاوى",
        "health_check": "/health",
        "timeout": 20
    },
    "/api/messages/": {
        "service": "naebak-messaging-service",
        "port": 8004,
        "description": "خدمة الرسائل", 
        "health_check": "/health",
        "timeout": 10
    },
    "/api/ratings/": {
        "service": "naebak-ratings-service",
        "port": 8005,
        "description": "خدمة التقييمات",
        "health_check": "/health", 
        "timeout": 5
    },
    "/api/visitors/": {
        "service": "naebak-visitor-counter-service",
        "port": 8006,
        "description": "خدمة عداد الزوار",
        "health_check": "/health",
        "timeout": 3
    },
    "/api/news/": {
        "service": "naebak-news-service",
        "port": 8007,
        "description": "خدمة الأخبار",
        "health_check": "/health",
        "timeout": 5
    },
    "/api/notifications/": {
        "service": "naebak-notifications-service", 
        "port": 8008,
        "description": "خدمة الإشعارات",
        "health_check": "/health",
        "timeout": 8
    },
    "/api/banners/": {
        "service": "naebak-banner-service",
        "port": 8009,
        "description": "خدمة البنرات",
        "health_check": "/health",
        "timeout": 10
    },
    "/api/content/": {
        "service": "naebak-content-service",
        "port": 8010,
        "description": "خدمة المحتوى", 
        "health_check": "/health",
        "timeout": 15
    },
    "/api/statistics/": {
        "service": "naebak-statistics-service",
        "port": 8012,
        "description": "خدمة الإحصائيات",
        "health_check": "/health",
        "timeout": 10
    },
    "/api/themes/": {
        "service": "naebak-theme-service",
        "port": 8014,
        "description": "خدمة الثيمات",
        "health_check": "/health", 
        "timeout": 5
    }
}
```

### **⚙️ إعدادات التوجيه:**
```python
ROUTING_CONFIG = {
    "default_timeout": 30,
    "retry_attempts": 3,
    "circuit_breaker_enabled": True,
    "rate_limit_default": "100/hour",
    "rate_limit_auth": "200/hour",
    "rate_limit_public": "50/hour",
    "health_check_interval": 30,
    "load_balancer_algorithm": "round_robin"
}
```

### **🔐 مستويات المصادقة:**
```python
AUTH_LEVELS = {
    "public": {
        "description": "متاح للجميع",
        "routes": ["/api/news/", "/api/visitors/", "/api/statistics/overall/"],
        "rate_limit": "50/hour"
    },
    "user": {
        "description": "يتطلب تسجيل دخول",
        "routes": ["/api/complaints/", "/api/ratings/", "/api/messages/"],
        "rate_limit": "100/hour"
    },
    "admin": {
        "description": "يتطلب صلاحيات إدارية",
        "routes": ["/api/admin/", "/api/banners/admin/", "/api/news/admin/"],
        "rate_limit": "200/hour"
    },
    "system": {
        "description": "للخدمات الداخلية فقط",
        "routes": ["/api/internal/", "/api/health/"],
        "rate_limit": "1000/hour"
    }
}
```

### **📊 أنواع الاستجابات الموحدة:**
```python
RESPONSE_FORMATS = {
    "success": {
        "structure": {
            "success": True,
            "data": "{}",
            "message": "string",
            "timestamp": "ISO8601"
        }
    },
    "error": {
        "structure": {
            "success": False,
            "error": {
                "code": "string",
                "message": "string",
                "details": "{}"
            },
            "timestamp": "ISO8601"
        }
    },
    "validation": {
        "structure": {
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "بيانات غير صحيحة",
                "fields": "{}"
            },
            "timestamp": "ISO8601"
        }
    }
}
```

---

## ⚙️ **إعدادات Google Cloud Run**

### **🔧 بيئة التطوير:**
```yaml
Environment: development
Port: 8013
Database: SQLite (local file)
Resources:
  CPU: 0.3
  Memory: 128Mi
  Max Instances: 2
  Min Instances: 1

Environment Variables:
  FLASK_ENV=development
  DATABASE_URL=sqlite:///gateway.db
  JWT_SECRET_KEY=dev_secret_key_123
  RATE_LIMIT_DEFAULT=1000/hour
  TIMEOUT_SECONDS=60
  RETRY_ATTEMPTS=2
  CIRCUIT_BREAKER_ENABLED=false
  DEBUG=true
  
Service Discovery:
  - All services on localhost with different ports
  - No load balancing (single instance each)
```

### **🚀 بيئة الإنتاج:**
```yaml
Environment: production
Port: 8013
Database: SQLite (persistent volume)
Resources:
  CPU: 0.5
  Memory: 256Mi
  Max Instances: 10
  Min Instances: 2

Environment Variables:
  FLASK_ENV=production
  DATABASE_URL=sqlite:///data/gateway.db
  JWT_SECRET_KEY=${JWT_SECRET_FROM_SECRET_MANAGER}
  RATE_LIMIT_DEFAULT=100/hour
  TIMEOUT_SECONDS=30
  RETRY_ATTEMPTS=3
  CIRCUIT_BREAKER_ENABLED=true
  DEBUG=false
  
Service Discovery:
  - All services via Cloud Run internal URLs
  - Load balancing enabled
  - Health checks every 30 seconds
  
Security:
  - HTTPS only
  - CORS configured for naebak.com
  - Rate limiting per IP
  - Request logging enabled
```

### **🧪 بيئة الاختبار:**
```yaml
Environment: testing
Port: 8013
Database: SQLite (in-memory)
Resources:
  CPU: 0.2
  Memory: 64Mi
  Max Instances: 1
  Min Instances: 1

Environment Variables:
  FLASK_ENV=testing
  DATABASE_URL=sqlite:///:memory:
  JWT_SECRET_KEY=test_secret_key
  RATE_LIMIT_DEFAULT=10000/hour
  TIMEOUT_SECONDS=10
  RETRY_ATTEMPTS=1
  CIRCUIT_BREAKER_ENABLED=false
  DEBUG=true
  
Service Discovery:
  - Mock services for testing
  - No external dependencies
```

---

## 🔐 **الأمان والصلاحيات**

### **👥 مستويات الوصول:**

#### **🔴 مستوى النظام:**
- **إدارة التوجيه** - تعديل خريطة الخدمات
- **مراقبة الصحة** - فحص حالة جميع الخدمات
- **إدارة Circuit Breakers** - تفعيل/إلغاء الحماية
- **عرض السجلات** - الوصول لجميع logs

#### **🟡 مستوى المراقبة:**
- **عرض الإحصائيات** - مقاييس الأداء والاستخدام
- **عرض حالة الخدمات** - صحة الخدمات فقط
- **لا يمكن التعديل** في الإعدادات

#### **🟢 مستوى التطبيق:**
- **استخدام البوابة** - إرسال الطلبات فقط
- **لا يمكن الوصول** للإعدادات الداخلية

### **🛡️ آليات الحماية:**
1. **Rate Limiting** - حدود مختلفة حسب نوع المستخدم
2. **Circuit Breaker** - إيقاف الطلبات للخدمات المعطلة
3. **JWT Validation** - فحص صحة tokens
4. **Request Sanitization** - تنظيف البيانات الواردة
5. **CORS Protection** - حماية من الطلبات غير المصرحة
6. **Request Logging** - تسجيل جميع الطلبات للمراجعة
7. **Health Monitoring** - مراقبة مستمرة لصحة الخدمات

---

## 📡 **واجهات برمجة التطبيقات (APIs)**

### **🌐 توجيه الطلبات:**

#### **1. توجيه عام لجميع الخدمات**
```http
ANY /{service_path}
```

**مثال:**
```http
GET /api/complaints/list/
→ يوجه إلى: naebak-complaints-service:8003/api/complaints/list/

POST /api/auth/login/
→ يوجه إلى: naebak-auth-service:8001/api/auth/login/
```

#### **2. فحص صحة جميع الخدمات**
```http
GET /api/gateway/health/all/
```

**الاستجابة:**
```json
{
    "success": true,
    "data": {
        "gateway_status": "healthy",
        "services": {
            "naebak-auth-service": {
                "status": "healthy",
                "response_time": "45ms",
                "last_check": "2024-01-01T10:00:00Z"
            },
            "naebak-complaints-service": {
                "status": "healthy", 
                "response_time": "67ms",
                "last_check": "2024-01-01T10:00:00Z"
            },
            "naebak-ratings-service": {
                "status": "degraded",
                "response_time": "234ms", 
                "last_check": "2024-01-01T10:00:00Z"
            }
        },
        "total_services": 12,
        "healthy_services": 11,
        "degraded_services": 1,
        "failed_services": 0
    }
}
```

#### **3. إحصائيات البوابة**
```http
GET /api/gateway/statistics/
Authorization: Bearer {admin_token}
```

**الاستجابة:**
```json
{
    "success": true,
    "data": {
        "requests_today": 15847,
        "requests_per_service": {
            "naebak-auth-service": 3421,
            "naebak-complaints-service": 5632,
            "naebak-ratings-service": 2156
        },
        "average_response_time": "89ms",
        "error_rate": "0.3%",
        "rate_limited_requests": 23,
        "circuit_breaker_trips": 0
    }
}
```

#### **4. إدارة Circuit Breakers**
```http
POST /api/gateway/circuit-breaker/{service_name}/reset/
Authorization: Bearer {admin_token}
```

#### **5. تحديث خريطة التوجيه**
```http
PUT /api/gateway/routes/
Authorization: Bearer {admin_token}
Content-Type: application/json

{
    "route": "/api/new-service/",
    "service": "naebak-new-service",
    "port": 8015,
    "timeout": 10
}
```

### **🔧 APIs المساعدة:**

#### **6. فحص صحة البوابة**
```http
GET /health
```

#### **7. معلومات الإصدار**
```http
GET /api/gateway/version/
```

#### **8. إعادة تحميل الإعدادات**
```http
POST /api/gateway/reload/
Authorization: Bearer {admin_token}
```

### **🏛️ إدارة البيانات المرجعية المشتركة:**

#### **9. إدارة الأحزاب السياسية**
```http
GET /api/gateway/reference/parties/
POST /api/gateway/reference/parties/
PUT /api/gateway/reference/parties/{party_id}/
DELETE /api/gateway/reference/parties/{party_id}/
Authorization: Bearer {admin_token}
```

**مثال إضافة حزب جديد:**
```http
POST /api/gateway/reference/parties/
Authorization: Bearer {admin_token}
Content-Type: application/json

{
    "name": "حزب المستقبل",
    "abbreviation": "المستقبل",
    "founded": 2024,
    "active": true
}
```

**الاستجابة:**
```json
{
    "success": true,
    "data": {
        "party": {
            "id": 17,
            "name": "حزب المستقبل",
            "abbreviation": "المستقبل",
            "founded": 2024,
            "active": true
        },
        "updated_services": [
            "naebak-auth-service",
            "naebak-complaints-service", 
            "naebak-ratings-service",
            "naebak-statistics-service"
        ],
        "update_status": "completed"
    }
}
```

#### **10. إدارة المجالس**
```http
GET /api/gateway/reference/councils/
POST /api/gateway/reference/councils/
PUT /api/gateway/reference/councils/{council_id}/
```

#### **11. إدارة الدوائر الانتخابية**
```http
GET /api/gateway/reference/districts/
POST /api/gateway/reference/districts/
PUT /api/gateway/reference/districts/{district_id}/
DELETE /api/gateway/reference/districts/{district_id}/
```

#### **12. إدارة الرموز الانتخابية**
```http
GET /api/gateway/reference/symbols/
POST /api/gateway/reference/symbols/
PUT /api/gateway/reference/symbols/{symbol_id}/
DELETE /api/gateway/reference/symbols/{symbol_id}/
```

#### **13. إدارة المحافظات**
```http
GET /api/gateway/reference/governorates/
PUT /api/gateway/reference/governorates/{gov_id}/
```

#### **14. تحديث جميع الخدمات فوراً**
```http
POST /api/gateway/reference/sync-all/
Authorization: Bearer {admin_token}
```

**الاستجابة:**
```json
{
    "success": true,
    "data": {
        "sync_started": "2024-01-01T10:00:00Z",
        "services_updated": 6,
        "services_failed": 0,
        "details": {
            "naebak-auth-service": "success",
            "naebak-complaints-service": "success",
            "naebak-ratings-service": "success",
            "naebak-statistics-service": "success",
            "naebak-content-service": "success",
            "naebak-admin-service": "success"
        }
    }
}
```

---

## 🔄 **الفروق بين البيئات**

| **الخاصية** | **التطوير** | **الإنتاج** | **الاختبار** |
|-------------|-------------|-------------|-------------|
| **قاعدة البيانات** | SQLite محلي | SQLite مستمر | في الذاكرة |
| **Rate Limiting** | 1000/ساعة | 100/ساعة | 10000/ساعة |
| **Timeout** | 60 ثانية | 30 ثانية | 10 ثواني |
| **Circuit Breaker** | معطل | مفعل | معطل |
| **Retry Attempts** | 2 محاولات | 3 محاولات | 1 محاولة |
| **Health Checks** | كل دقيقة | كل 30 ثانية | معطل |
| **التسجيل** | مفصل | أساسي | مفصل |
| **الموارد** | 128Mi | 256Mi | 64Mi |
| **Instances** | 1-2 | 2-10 | 1 |

---

## 📊 **المراقبة والتحليلات**

### **📈 مقاييس الأداء:**
1. **عدد الطلبات** - إجمالي الطلبات المُوجهة
2. **وقت الاستجابة** - متوسط زمن التوجيه والاستجابة
3. **معدل الأخطاء** - نسبة الطلبات الفاشلة
4. **توزيع الخدمات** - استخدام كل خدمة
5. **Rate Limiting** - عدد الطلبات المحجوبة
6. **Circuit Breaker** - عدد مرات التفعيل
7. **صحة الخدمات** - حالة كل خدمة مُدارة

### **🚨 التنبيهات:**
- **خدمة معطلة** - إذا فشلت خدمة في الاستجابة
- **استجابة بطيئة** - إذا تجاوز وقت الاستجابة 1 ثانية
- **معدل أخطاء عالي** - إذا تجاوزت الأخطاء 5%
- **Rate limiting مفرط** - إذا تم حجب أكثر من 10% من الطلبات
- **ذاكرة ممتلئة** - إذا تجاوز استخدام الذاكرة 80%
- **Circuit breaker مفعل** - عند إيقاف خدمة تلقائياً

---

## 🛠️ **خطة التطوير**

### **المرحلة الأولى (2 أسبوع):**
- إعداد Flask وخريطة التوجيه الأساسية
- تطوير آلية توجيه الطلبات للخدمات
- تطبيق Rate Limiting الأساسي
- ربط مع خدمة المصادقة للتحقق من JWT

### **المرحلة الثانية (2 أسبوع):**
- تطوير Circuit Breaker للحماية
- تطبيق Health Checks لجميع الخدمات
- تطوير لوحة مراقبة الإحصائيات
- تطبيق Load Balancing للخدمات

### **المرحلة الثالثة (1 أسبوع):**
- تطبيق المراقبة والتنبيهات
- تحسين الأداء والتخزين المؤقت
- اختبارات شاملة ونشر
- توثيق APIs وإرشادات الاستخدام

---

## 📚 **الموارد والمراجع**

### **🔧 التبعيات:**
```python
DEPENDENCIES = [
    "Flask==2.3.3",
    "requests==2.31.0",  # للتواصل مع الخدمات
    "flask-limiter==3.5.0",  # لـ Rate Limiting
    "PyJWT==2.8.0",  # للتحقق من JWT tokens
    "circuitbreaker==1.4.0"  # لـ Circuit Breaker pattern
]
```

### **🔗 الروابط المهمة:**
- **مستودع المخزن:** `/naebak-almakhzan/`
- **جميع الخدمات المُدارة:** `naebak-*-service:80XX`
- **وثائق Flask:** https://flask.palletsprojects.com/
- **Circuit Breaker Pattern:** https://martinfowler.com/bliki/CircuitBreaker.html

---

## 🎯 **الخلاصة**

خدمة البوابة هي **العمود الفقري التقني** لمنصة نائبك - تربط جميع الخدمات المصغرة وتوحد تفاعلها مع الواجهة الأمامية. الخدمة تركز على **التنسيق والموثوقية** مع حماية شاملة وإدارة ذكية للطلبات.

**النقاط الرئيسية:**
- ✅ نقطة دخول موحدة لجميع APIs
- ✅ توجيه ذكي للطلبات حسب المسار
- ✅ مصادقة مركزية وRate Limiting
- ✅ Circuit Breaker للحماية من الأعطال
- ✅ مراقبة مستمرة لصحة جميع الخدمات
- ✅ استجابات موحدة ومعالجة أخطاء متسقة

الخدمة الآن **جاهزة للتطوير** مع جميع المتطلبات التقنية والتنسيقية محددة بوضوح.
