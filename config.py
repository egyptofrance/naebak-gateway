
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
    PORT = int(os.getenv("GATEWAY_PORT", 8000))
    DEBUG = os.getenv("DEBUG_MODE", "True").lower() == "true"
    
    # إعدادات الأمان (يمكن توسيعها لاحقًا)
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-gateway-key")
    
    # إعدادات CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # إعدادات Rate Limiting (مثال)
    RATE_LIMIT_STORAGE_URL = os.getenv("RATE_LIMIT_STORAGE_URL", "memory://")
    
    # عناوين URL للخدمات الخلفية
    AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8002")
    PRODUCT_SERVICE_URL = os.getenv("PRODUCT_SERVICE_URL", "http://localhost:8003")
    ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8004")
    PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8005")
    NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8006")
    
    # إعدادات التخزين المؤقت (إذا لزم الأمر)
    CACHE_TYPE = os.getenv("CACHE_TYPE", "simple")
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", 300))

