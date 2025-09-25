"""
خدمة البوابة - Naebak Gateway Service
نقطة الدخول المركزية لجميع الخدمات المصغرة في منصة نائبك
"""
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
import requests
import logging
import os
from datetime import datetime
import jwt
import json

from config import Config
from constants import APP_NAME, APP_VERSION

# إعداد التطبيق
app = Flask(__name__)
app.config.from_object(Config)

# إعداد قاعدة البيانات للبيانات المرجعية المشتركة
app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# إعداد CORS
CORS(app, resources={r"/*": {"origins": Config.CORS_ORIGINS}})

# إعداد Rate Limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=[Config.RATE_LIMIT_DEFAULT]
)

# إعداد Logging
logging.basicConfig(
    level=logging.INFO if not Config.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# خريطة توجيه الخدمات - منصة نائبك
SERVICE_ROUTES = {
    "/api/auth/": {
        "service": "naebak-auth-service",
        "url": Config.AUTH_SERVICE_URL,
        "timeout": 10,
        "auth_required": False
    },
    "/api/admin/": {
        "service": "naebak-admin-service",
        "url": Config.ADMIN_SERVICE_URL,
        "timeout": 15,
        "auth_required": True,
        "admin_only": True
    },
    "/api/complaints/": {
        "service": "naebak-complaints-service",
        "url": Config.COMPLAINTS_SERVICE_URL,
        "timeout": 20,
        "auth_required": True
    },
    "/api/messages/": {
        "service": "naebak-messaging-service",
        "url": Config.MESSAGING_SERVICE_URL,
        "timeout": 10,
        "auth_required": True
    },
    "/api/ratings/": {
        "service": "naebak-ratings-service",
        "url": Config.RATINGS_SERVICE_URL,
        "timeout": 5,
        "auth_required": True
    },
    "/api/visitors/": {
        "service": "naebak-visitor-counter-service",
        "url": Config.VISITOR_SERVICE_URL,
        "timeout": 3,
        "auth_required": False
    },
    "/api/news/": {
        "service": "naebak-news-service",
        "url": Config.NEWS_SERVICE_URL,
        "timeout": 5,
        "auth_required": False
    },
    "/api/notifications/": {
        "service": "naebak-notifications-service",
        "url": Config.NOTIFICATIONS_SERVICE_URL,
        "timeout": 8,
        "auth_required": True
    },
    "/api/banners/": {
        "service": "naebak-banner-service",
        "url": Config.BANNER_SERVICE_URL,
        "timeout": 10,
        "auth_required": False
    },
    "/api/content/": {
        "service": "naebak-content-service",
        "url": Config.CONTENT_SERVICE_URL,
        "timeout": 15,
        "auth_required": False
    },
    "/api/statistics/": {
        "service": "naebak-statistics-service",
        "url": Config.STATISTICS_SERVICE_URL,
        "timeout": 10,
        "auth_required": False
    },
    "/api/themes/": {
        "service": "naebak-theme-service",
        "url": Config.THEME_SERVICE_URL,
        "timeout": 5,
        "auth_required": True
    }
}

def verify_jwt_token(token):
    """التحقق من صحة JWT Token"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def check_authentication(route_config):
    """فحص المصادقة للمسارات التي تتطلب ذلك"""
    if not route_config.get('auth_required', False):
        return True, None
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False, "Missing or invalid authorization header"
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    
    if not payload:
        return False, "Invalid or expired token"
    
    # فحص الصلاحيات الإدارية إذا لزم الأمر
    if route_config.get('admin_only', False):
        if not payload.get('is_admin', False):
            return False, "Admin privileges required"
    
    return True, payload

@app.route("/health", methods=["GET"])
def health_check():
    """فحص صحة خدمة البوابة"""
    return jsonify({
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "services_count": len(SERVICE_ROUTES)
    }), 200

@app.route("/api/gateway/services", methods=["GET"])
def list_services():
    """قائمة بجميع الخدمات المتاحة"""
    services = []
    for route, config in SERVICE_ROUTES.items():
        services.append({
            "route": route,
            "service": config["service"],
            "auth_required": config.get("auth_required", False),
            "admin_only": config.get("admin_only", False)
        })
    
    return jsonify({
        "success": True,
        "data": {
            "services": services,
            "total_count": len(services)
        },
        "timestamp": datetime.now().isoformat()
    }), 200

def find_matching_route(path):
    """العثور على المسار المطابق للخدمة"""
    for route_pattern, config in SERVICE_ROUTES.items():
        if path.startswith(route_pattern.rstrip('/')):
            return route_pattern, config
    return None, None

@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def proxy_request(path):
    """وكيل عام لإعادة توجيه الطلبات إلى الخدمات المناسبة"""
    full_path = f"/api/{path}"
    logger.debug(f"Incoming request for path: {full_path}")
    
    # العثور على الخدمة المطابقة
    route_pattern, route_config = find_matching_route(full_path)
    
    if not route_config:
        return jsonify({
            "success": False,
            "error": {
                "code": "SERVICE_NOT_FOUND",
                "message": f"No service found for path: {full_path}"
            },
            "timestamp": datetime.now().isoformat()
        }), 404
    
    # فحص المصادقة
    auth_valid, auth_result = check_authentication(route_config)
    if not auth_valid:
        return jsonify({
            "success": False,
            "error": {
                "code": "AUTHENTICATION_FAILED",
                "message": auth_result
            },
            "timestamp": datetime.now().isoformat()
        }), 401
    
    # بناء URL الهدف
    service_path = full_path[len(route_pattern.rstrip('/')):]
    if not service_path.startswith('/'):
        service_path = '/' + service_path
    
    target_url = f"{route_config['url']}{service_path}"
    
    logger.info(f"Proxying request to {route_config['service']}: {request.method} {target_url}")
    
    try:
        # إعداد Headers
        headers = dict(request.headers)
        if "Host" in headers:
            del headers["Host"]
        
        # إضافة معلومات المستخدم إذا كان مصادق
        if auth_result and isinstance(auth_result, dict):
            headers['X-User-ID'] = str(auth_result.get('user_id', ''))
            headers['X-User-Role'] = auth_result.get('role', 'user')
        
        # إعادة توجيه الطلب
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=route_config.get('timeout', Config.DEFAULT_TIMEOUT)
        )
        
        # بناء الاستجابة
        response = Response(resp.content, status=resp.status_code)
        for key, value in resp.headers.items():
            if key.lower() not in ["content-encoding", "content-length", "transfer-encoding", "connection"]:
                response.headers[key] = value
        
        return response
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout connecting to {route_config['service']} at {target_url}")
        return jsonify({
            "success": False,
            "error": {
                "code": "SERVICE_TIMEOUT",
                "message": f"Service {route_config['service']} unavailable (timeout)"
            },
            "timestamp": datetime.now().isoformat()
        }), 504
        
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error to {route_config['service']} at {target_url}")
        return jsonify({
            "success": False,
            "error": {
                "code": "SERVICE_UNAVAILABLE",
                "message": f"Service {route_config['service']} unavailable (connection error)"
            },
            "timestamp": datetime.now().isoformat()
        }), 503
        
    except Exception as e:
        logger.error(f"Error proxying request to {route_config['service']}: {str(e)}")
        return jsonify({
            "success": False,
            "error": {
                "code": "GATEWAY_ERROR",
                "message": "Internal gateway error"
            },
            "timestamp": datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": {
            "code": "NOT_FOUND",
            "message": error.description or "Not Found"
        },
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Internal Server Error"
        },
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == "__main__":
    # إنشاء جداول قاعدة البيانات
    with app.app_context():
        db.create_all()
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
