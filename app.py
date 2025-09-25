
"""
خدمة البوابة - Naebak Gateway Service
"""
from flask import Flask, request, jsonify, redirect, url_for, abort, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import logging
import os

from config import Config
from constants import APP_NAME, APP_VERSION, AUTH_SERVICE_BASE_URL, VISITOR_SERVICE_BASE_URL

# إعداد التطبيق
app = Flask(__name__)
app.config.from_object(Config)

# إعداد CORS
CORS(app, resources={r"/*": {"origins": Config.CORS_ORIGINS}})

# إعداد Rate Limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["1000 per hour", "50 per minute"]
)

# إعداد Logging
logging.basicConfig(
    level=logging.INFO if not Config.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# تعريف مسارات الخدمات
SERVICE_ROUTES = {
    "auth": Config.AUTH_SERVICE_URL,
    "user": Config.USER_SERVICE_URL,
    "product": Config.PRODUCT_SERVICE_URL,
    "order": Config.ORDER_SERVICE_URL,
    "payment": Config.PAYMENT_SERVICE_URL,
    "notification": Config.NOTIFICATION_SERVICE_URL,
    "visitor": VISITOR_SERVICE_BASE_URL # Using constant for visitor service
}

@app.route("/health", methods=["GET"])
def health_check():
    """فحص صحة خدمة البوابة"""
    return jsonify({
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100 per minute") # Apply rate limit to all proxied requests
def proxy_request(path):
    """وكيل عام لإعادة توجيه الطلبات إلى الخدمات المناسبة"""
    logger.debug(f"Incoming request for path: {path}")
    
    # تحديد الخدمة المستهدفة من المسار
    parts = path.split("/")
    if len(parts) < 2:
        abort(404, description="Invalid service path")
        
    service_name = parts[0]
    service_url = SERVICE_ROUTES.get(service_name)
    
    if not service_url:
        abort(404, description=f"Service '{service_name}' not found")
        
    # بناء المسار الجديد للخدمة المستهدفة
    target_path = "/".join(parts[1:])
    target_url = f"{service_url}/{target_path}"
    
    logger.info(f"Proxying request to {service_name}: {request.method} {target_url}")
    
    try:
        headers = dict(request.headers)
        # إزالة Header الخاص بالـ Host لتجنب مشاكل التوجيه
        if "Host" in headers: del headers["Host"]
        
        # إعادة توجيه الطلب
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False, # لا تتبع عمليات إعادة التوجيه تلقائيًا
            timeout=Config.CACHE_DEFAULT_TIMEOUT # استخدام مهلة من الإعدادات
        )
        
        # بناء الاستجابة من الخدمة المستهدفة
        response = Response(resp.content, status=resp.status_code)
        for key, value in resp.headers.items():
            # تجنب Headers التي قد تسبب مشاكل في البوابة
            if key.lower() not in ["content-encoding", "content-length", "transfer-encoding", "connection"]:
                response.headers[key] = value
        
        return response
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout connecting to {service_name} at {target_url}")
        return jsonify({"error": f"Service {service_name} unavailable (timeout)"}), 504
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error to {service_name} at {target_url}")
        return jsonify({"error": f"Service {service_name} unavailable (connection error)"}), 503
    except Exception as e:
        logger.error(f"Error proxying request to {service_name}: {str(e)}")
        return jsonify({"error": "Internal gateway error"}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": error.description or "Not Found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error"}), 500


if __name__ == "__main__":
    from datetime import datetime # Import datetime here for health_check
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )

