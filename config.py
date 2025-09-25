"""
إعدادات خدمة البوابة - Naebak Gateway Service
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """إعدادات التطبيق"""
    
    # إعدادات الخادم
    HOST = os.getenv("GATEWAY_HOST", "0.0.0.0")
    PORT = int(os.getenv("GATEWAY_PORT", 8013))
    DEBUG = os.getenv("DEBUG_MODE", "True").lower() == "true"
    
    # إعدادات الأمان
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-gateway-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-for-naebak")
    
    # إعدادات CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # إعدادات Rate Limiting
    RATE_LIMIT_STORAGE_URL = os.getenv("RATE_LIMIT_STORAGE_URL", "memory://")
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "100/hour")
    RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "200/hour")
    RATE_LIMIT_PUBLIC = os.getenv("RATE_LIMIT_PUBLIC", "50/hour")
    
    # إعدادات التوجيه
    DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", 30))
    RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", 3))
    CIRCUIT_BREAKER_ENABLED = os.getenv("CIRCUIT_BREAKER_ENABLED", "true").lower() == "true"
    HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", 30))
    
    # عناوين URL للخدمات المصغرة - منصة نائبك
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://naebak-auth-service:8001")
    ADMIN_SERVICE_URL = os.getenv("ADMIN_SERVICE_URL", "http://naebak-admin-service:8002")
    COMPLAINTS_SERVICE_URL = os.getenv("COMPLAINTS_SERVICE_URL", "http://naebak-complaints-service:8003")
    MESSAGING_SERVICE_URL = os.getenv("MESSAGING_SERVICE_URL", "http://naebak-messaging-service:8004")
    RATINGS_SERVICE_URL = os.getenv("RATINGS_SERVICE_URL", "http://naebak-ratings-service:8005")
    VISITOR_SERVICE_URL = os.getenv("VISITOR_SERVICE_URL", "http://naebak-visitor-counter-service:8006")
    NEWS_SERVICE_URL = os.getenv("NEWS_SERVICE_URL", "http://naebak-news-service:8007")
    NOTIFICATIONS_SERVICE_URL = os.getenv("NOTIFICATIONS_SERVICE_URL", "http://naebak-notifications-service:8008")
    BANNER_SERVICE_URL = os.getenv("BANNER_SERVICE_URL", "http://naebak-banner-service:8009")
    CONTENT_SERVICE_URL = os.getenv("CONTENT_SERVICE_URL", "http://naebak-content-service:8010")
    STATISTICS_SERVICE_URL = os.getenv("STATISTICS_SERVICE_URL", "http://naebak-statistics-service:8012")
    THEME_SERVICE_URL = os.getenv("THEME_SERVICE_URL", "http://naebak-theme-service:8014")
    
    # إعدادات قاعدة البيانات للبيانات المرجعية المشتركة
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///gateway.db")
    
    # إعدادات التخزين المؤقت
    CACHE_TYPE = os.getenv("CACHE_TYPE", "simple")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", 300))
    
    # إعدادات Redis للتزامن
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # إعدادات Webhook للتحديثات المركزية
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "webhook-secret-key")
    SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL", 300))  # 5 minutes
