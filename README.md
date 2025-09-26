# 🏷️ البوابة الرئيسية (naebak-gateway)

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/egyptofrance/naebak-gateway/actions)
[![Coverage](https://img.shields.io/badge/coverage-N/A-lightgrey)](https://github.com/egyptofrance/naebak-gateway)
[![Version](https://img.shields.io/badge/version-0.8.0-blue)](https://github.com/egyptofrance/naebak-gateway/releases)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

## 📝 الوصف

البوابة الرئيسية (API Gateway) لتطبيق نائبك. تعمل كنقطة دخول واحدة لجميع الطلبات من الواجهة الأمامية، وتقوم بتوجيهها إلى الخدمات المصغرة المناسبة. كما أنها مسؤولة عن المصادقة وتحديد الصلاحيات.

---

## ✨ الميزات الرئيسية

- **نقطة دخول واحدة**: توجيه جميع الطلبات إلى الخدمات المصغرة.
- **المصادقة والترخيص**: التحقق من هوية المستخدم وصلاحياته.
- **تحديد معدل الطلبات (Rate Limiting)**: حماية الخدمات من الاستخدام المفرط.
- **التخزين المؤقت (Caching)**: تحسين أداء الاستجابات المتكررة.

---

## 🛠️ التقنيات المستخدمة

| التقنية | الإصدار | الغرض |
|---------|---------|-------|
| **Flask** | 2.3.2 | إطار العمل الأساسي |
| **Flask-RESTX** | 0.5.1 | تطوير APIs |
| **PyJWT** | 2.8.0 | التعامل مع JWT |

---

## 🚀 التثبيت والتشغيل

```bash
git clone https://github.com/egyptofrance/naebak-gateway.git
cd naebak-gateway

# اتبع خطوات التثبيت والتشغيل لخدمات Flask
```

---

## 📚 توثيق الـ API

- **Swagger UI**: [http://localhost:5000/api/docs/](http://localhost:5000/api/docs/)

---

## 🤝 المساهمة

يرجى مراجعة [دليل المساهمة](CONTRIBUTING.md) و [معايير التوثيق الموحدة](../../naebak-almakhzan/DOCUMENTATION_STANDARDS.md).

---

## 📄 الترخيص

هذا المشروع مرخص تحت [رخصة MIT](LICENSE).

