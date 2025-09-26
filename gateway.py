#!/usr/bin/env python3
"""
البوابة الرئيسية المبسطة - نائبك
===============================

بوابة API مبسطة وموثوقة باستخدام Flask.
تقوم بتوجيه الطلبات للخدمات المختلفة مع التحقق من الهوية.

الميزات:
- توجيه الطلبات للخدمات (auth, complaints, messaging, notifications)
- التحقق من JWT tokens
- CORS support
- معالجة الأخطاء
- إحصائيات بسيطة
- فحص صحة الخدمات
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt_identity
import requests
import logging
import os
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['JWT_SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['CORS_HEADERS'] = 'Content-Type'

# Initialize extensions
CORS(app)
jwt = JWTManager(app)

# Service configuration - easy to update
SERVICES = {
    'auth': {
        'url': os.environ.get('AUTH_SERVICE_URL', 'http://localhost:8001'),
        'timeout': 10,
        'auth_required': False
    },
    'complaints': {
        'url': os.environ.get('COMPLAINTS_SERVICE_URL', 'http://localhost:8004'),
        'timeout': 15,
        'auth_required': True
    },
    'messaging': {
        'url': os.environ.get('MESSAGING_SERVICE_URL', 'http://localhost:8002'),
        'timeout': 10,
        'auth_required': True
    },
    'notifications': {
        'url': os.environ.get('NOTIFICATIONS_SERVICE_URL', 'http://localhost:8003'),
        'timeout': 10,
        'auth_required': True
    }
}

# Route mapping - simple and clear
ROUTE_MAP = {
    '/api/auth/': 'auth',
    '/api/complaints/': 'complaints',
    '/api/messaging/': 'messaging',
    '/api/notifications/': 'notifications'
}

# Statistics tracking
stats = {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'service_requests': {service: 0 for service in SERVICES.keys()},
    'start_time': datetime.utcnow()
}

def get_service_for_path(path):
    """تحديد الخدمة المناسبة للمسار"""
    for route_prefix, service_name in ROUTE_MAP.items():
        if path.startswith(route_prefix):
            return service_name, route_prefix
    return None, None

def check_auth_if_required(service_name):
    """التحقق من المصادقة إذا كانت مطلوبة"""
    service_config = SERVICES.get(service_name)
    if not service_config:
        return False, "خدمة غير موجودة"
    
    if service_config.get('auth_required', False):
        try:
            verify_jwt_in_request()
            return True, None
        except Exception as e:
            return False, "مطلوب تسجيل الدخول"
    
    return True, None

def forward_request(service_name, target_path, route_prefix):
    """توجيه الطلب للخدمة المناسبة"""
    service_config = SERVICES[service_name]
    service_url = service_config['url']
    timeout = service_config['timeout']
    
    # إنشاء URL الهدف
    # إزالة البادئة من المسار
    clean_path = target_path[len(route_prefix)-1:]  # نحتفظ بـ /
    if not clean_path.startswith('/'):
        clean_path = '/' + clean_path
    
    target_url = f"{service_url}{clean_path}"
    
    # إعداد headers
    headers = {}
    if request.headers.get('Authorization'):
        headers['Authorization'] = request.headers.get('Authorization')
    if request.headers.get('Content-Type'):
        headers['Content-Type'] = request.headers.get('Content-Type')
    
    # إعداد البيانات
    data = None
    if request.method in ['POST', 'PUT', 'PATCH']:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.get_data()
    
    # إعداد query parameters
    params = request.args.to_dict()
    
    try:
        # إرسال الطلب
        if request.method == 'GET':
            response = requests.get(target_url, headers=headers, params=params, timeout=timeout)
        elif request.method == 'POST':
            if request.is_json:
                response = requests.post(target_url, json=data, headers=headers, params=params, timeout=timeout)
            else:
                response = requests.post(target_url, data=data, headers=headers, params=params, timeout=timeout)
        elif request.method == 'PUT':
            if request.is_json:
                response = requests.put(target_url, json=data, headers=headers, params=params, timeout=timeout)
            else:
                response = requests.put(target_url, data=data, headers=headers, params=params, timeout=timeout)
        elif request.method == 'DELETE':
            response = requests.delete(target_url, headers=headers, params=params, timeout=timeout)
        elif request.method == 'PATCH':
            if request.is_json:
                response = requests.patch(target_url, json=data, headers=headers, params=params, timeout=timeout)
            else:
                response = requests.patch(target_url, data=data, headers=headers, params=params, timeout=timeout)
        else:
            return jsonify({'error': 'طريقة HTTP غير مدعومة'}), 405
        
        # إرجاع الاستجابة
        return Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
        
    except requests.exceptions.Timeout:
        logger.error(f"انتهت مهلة الاتصال بالخدمة {service_name}")
        return jsonify({'error': 'انتهت مهلة الاتصال بالخدمة'}), 504
    
    except requests.exceptions.ConnectionError:
        logger.error(f"فشل الاتصال بالخدمة {service_name}")
        return jsonify({'error': 'الخدمة غير متاحة حالياً'}), 503
    
    except Exception as e:
        logger.error(f"خطأ في توجيه الطلب للخدمة {service_name}: {str(e)}")
        return jsonify({'error': 'خطأ داخلي في الخادم'}), 500

@app.before_request
def before_request():
    """معالجة ما قبل الطلب"""
    stats['total_requests'] += 1
    
    # تسجيل الطلب
    logger.info(f"{request.method} {request.path} من {request.remote_addr}")

@app.after_request
def after_request(response):
    """معالجة ما بعد الطلب"""
    if response.status_code < 400:
        stats['successful_requests'] += 1
    else:
        stats['failed_requests'] += 1
    
    return response

@app.route('/', methods=['GET'])
def root():
    """الصفحة الرئيسية"""
    return jsonify({
        'service': 'naebak-gateway',
        'version': '2.0.0',
        'status': 'running',
        'message': 'البوابة الرئيسية لتطبيق نائبك',
        'timestamp': datetime.utcnow().isoformat(),
        'available_services': list(SERVICES.keys())
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """فحص صحة البوابة والخدمات"""
    gateway_health = {
        'status': 'healthy',
        'service': 'naebak-gateway',
        'version': '2.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime_seconds': (datetime.utcnow() - stats['start_time']).total_seconds()
    }
    
    # فحص الخدمات
    services_health = {}
    for service_name, config in SERVICES.items():
        try:
            response = requests.get(f"{config['url']}/health", timeout=5)
            if response.status_code == 200:
                services_health[service_name] = {
                    'status': 'healthy',
                    'response_time_ms': response.elapsed.total_seconds() * 1000
                }
            else:
                services_health[service_name] = {
                    'status': 'unhealthy',
                    'error': f'HTTP {response.status_code}'
                }
        except Exception as e:
            services_health[service_name] = {
                'status': 'unreachable',
                'error': str(e)
            }
    
    return jsonify({
        'gateway': gateway_health,
        'services': services_health
    }), 200

@app.route('/stats', methods=['GET'])
def get_stats():
    """إحصائيات البوابة"""
    uptime = datetime.utcnow() - stats['start_time']
    
    return jsonify({
        'total_requests': stats['total_requests'],
        'successful_requests': stats['successful_requests'],
        'failed_requests': stats['failed_requests'],
        'success_rate': (stats['successful_requests'] / max(stats['total_requests'], 1)) * 100,
        'service_requests': stats['service_requests'],
        'uptime_seconds': uptime.total_seconds(),
        'uptime_human': str(uptime),
        'start_time': stats['start_time'].isoformat(),
        'current_time': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def api_proxy(path):
    """توجيه طلبات API للخدمات المناسبة"""
    full_path = f"/api/{path}"
    
    # تحديد الخدمة المناسبة
    service_name, route_prefix = get_service_for_path(full_path)
    
    if not service_name:
        return jsonify({'error': 'مسار API غير موجود'}), 404
    
    # التحقق من المصادقة إذا كانت مطلوبة
    auth_valid, auth_error = check_auth_if_required(service_name)
    if not auth_valid:
        return jsonify({'error': auth_error}), 401
    
    # تحديث إحصائيات الخدمة
    stats['service_requests'][service_name] += 1
    
    # توجيه الطلب
    return forward_request(service_name, full_path, route_prefix)

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'الصفحة غير موجودة'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'خطأ داخلي في الخادم'}), 500

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'طلب غير صحيح'}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'غير مصرح لك بالوصول'}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'ممنوع الوصول'}), 403

@app.errorhandler(503)
def service_unavailable(error):
    return jsonify({'error': 'الخدمة غير متاحة'}), 503

@app.errorhandler(504)
def gateway_timeout(error):
    return jsonify({'error': 'انتهت مهلة الاتصال'}), 504

if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("🚀 بدء تشغيل البوابة الرئيسية المبسطة v2.0")
    logger.info("=" * 50)
    logger.info("✅ توجيه الطلبات: 4 خدمات رئيسية")
    logger.info("✅ المصادقة: JWT tokens")
    logger.info("✅ CORS: مدعوم")
    logger.info("✅ الإحصائيات: متاحة على /stats")
    logger.info("✅ فحص الصحة: متاح على /health")
    logger.info("=" * 50)
    logger.info("📋 الخدمات المتاحة:")
    for service_name, config in SERVICES.items():
        logger.info(f"   - {service_name}: {config['url']}")
    logger.info("=" * 50)
    
    app.run(host='0.0.0.0', port=8000, debug=True)
