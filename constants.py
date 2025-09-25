"""
ثوابت خدمة البوابة - منصة نائبك
"""

# معلومات التطبيق
APP_NAME = "naebak-gateway"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "بوابة API مركزية لمنصة نائبك - منصة التواصل مع النواب"

# أرقام المنافذ للخدمات المصغرة
PORTS = {
    "AUTH_SERVICE": 8001,
    "ADMIN_SERVICE": 8002,
    "COMPLAINTS_SERVICE": 8003,
    "MESSAGING_SERVICE": 8004,
    "RATINGS_SERVICE": 8005,
    "VISITOR_SERVICE": 8006,
    "NEWS_SERVICE": 8007,
    "NOTIFICATIONS_SERVICE": 8008,
    "BANNER_SERVICE": 8009,
    "CONTENT_SERVICE": 8010,
    "STATISTICS_SERVICE": 8012,
    "GATEWAY_SERVICE": 8013,
    "THEME_SERVICE": 8014
}

# أسماء الخدمات
SERVICE_NAMES = {
    "AUTH": "naebak-auth-service",
    "ADMIN": "naebak-admin-service",
    "COMPLAINTS": "naebak-complaints-service",
    "MESSAGING": "naebak-messaging-service",
    "RATINGS": "naebak-ratings-service",
    "VISITOR": "naebak-visitor-counter-service",
    "NEWS": "naebak-news-service",
    "NOTIFICATIONS": "naebak-notifications-service",
    "BANNER": "naebak-banner-service",
    "CONTENT": "naebak-content-service",
    "STATISTICS": "naebak-statistics-service",
    "GATEWAY": "naebak-gateway",
    "THEME": "naebak-theme-service"
}

# مهل زمنية افتراضية للخدمات (بالثواني)
DEFAULT_TIMEOUTS = {
    "AUTH_SERVICE": 10,
    "ADMIN_SERVICE": 15,
    "COMPLAINTS_SERVICE": 20,
    "MESSAGING_SERVICE": 10,
    "RATINGS_SERVICE": 5,
    "VISITOR_SERVICE": 3,
    "NEWS_SERVICE": 5,
    "NOTIFICATIONS_SERVICE": 8,
    "BANNER_SERVICE": 10,
    "CONTENT_SERVICE": 15,
    "STATISTICS_SERVICE": 10,
    "THEME_SERVICE": 5,
    "DEFAULT": 30
}

# حدود معدل الطلبات
RATE_LIMITS = {
    "PUBLIC": "50/hour",
    "USER": "100/hour",
    "ADMIN": "200/hour",
    "SYSTEM": "1000/hour"
}

# رموز الأخطاء
ERROR_CODES = {
    "SERVICE_NOT_FOUND": "SERVICE_NOT_FOUND",
    "AUTHENTICATION_FAILED": "AUTHENTICATION_FAILED",
    "SERVICE_TIMEOUT": "SERVICE_TIMEOUT",
    "SERVICE_UNAVAILABLE": "SERVICE_UNAVAILABLE",
    "GATEWAY_ERROR": "GATEWAY_ERROR",
    "VALIDATION_ERROR": "VALIDATION_ERROR",
    "PERMISSION_DENIED": "PERMISSION_DENIED"
}

# أنواع المستخدمين
USER_ROLES = {
    "ADMIN": "admin",
    "MODERATOR": "moderator",
    "USER": "user",
    "GUEST": "guest"
}

# حالات الخدمات
SERVICE_STATUS = {
    "HEALTHY": "healthy",
    "UNHEALTHY": "unhealthy",
    "MAINTENANCE": "maintenance",
    "UNKNOWN": "unknown"
}

# إعدادات التزامن والتحديث
SYNC_SETTINGS = {
    "WEBHOOK_RETRY_ATTEMPTS": 3,
    "WEBHOOK_TIMEOUT": 10,
    "SYNC_INTERVAL_SECONDS": 300,  # 5 دقائق
    "HEALTH_CHECK_INTERVAL": 30    # 30 ثانية
}
