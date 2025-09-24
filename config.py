"""
إعدادات خدمة عداد الزوار
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """إعدادات التطبيق"""
    
    # إعدادات الخادم
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8008))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # إعدادات الأمان
    API_KEY = os.getenv('API_KEY', 'naebak-visitor-counter-api-key-change-me')
    ADMIN_KEY = os.getenv('ADMIN_KEY', 'naebak-admin-key-change-me')
    
    # إعدادات Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 2))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    
    # إعدادات CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # إعدادات Rate Limiting
    RATE_LIMIT_STORAGE_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    
    # إعدادات Google Cloud
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT', 'naebak-472518')
    
    # إعدادات الخدمات الأخرى
    AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:8001')
    ADMIN_SERVICE_URL = os.getenv('ADMIN_SERVICE_URL', 'http://localhost:8002')
    
    # إعدادات التخزين المؤقت
    CACHE_TTL = int(os.getenv('CACHE_TTL', 300))  # 5 دقائق
    
    # إعدادات الإحصائيات
    STATS_RETENTION_DAYS = int(os.getenv('STATS_RETENTION_DAYS', 90))  # 90 يوم
    VISITOR_SESSION_TIMEOUT = int(os.getenv('VISITOR_SESSION_TIMEOUT', 1800))  # 30 دقيقة
