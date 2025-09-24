"""
خدمة عداد الزوار - Naebak Visitor Counter Service
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
import os
from datetime import datetime, timedelta
import json
import logging
from functools import wraps

# إعداد التطبيق
app = Flask(__name__)
app.config.from_object('config.Config')

# إعداد CORS
CORS(app, origins=app.config['CORS_ORIGINS'])

# إعداد Redis
redis_client = redis.Redis(
    host=app.config['REDIS_HOST'],
    port=app.config['REDIS_PORT'],
    db=app.config['REDIS_DB'],
    decode_responses=True
)

# إعداد Rate Limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

# إعداد Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def require_api_key(f):
    """Decorator للتحقق من API Key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != app.config['API_KEY']:
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function


@app.route('/health', methods=['GET'])
def health_check():
    """فحص صحة الخدمة"""
    try:
        # اختبار اتصال Redis
        redis_client.ping()
        return jsonify({
            'status': 'healthy',
            'service': 'naebak-visitor-counter',
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/api/visitor/count', methods=['POST'])
@limiter.limit("10 per minute")
def count_visitor():
    """تسجيل زيارة جديدة"""
    try:
        data = request.get_json() or {}
        
        # الحصول على معلومات الزائر
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        page_url = data.get('page_url', '/')
        user_id = data.get('user_id')  # اختياري للمستخدمين المسجلين
        
        # إنشاء مفتاح فريد للزائر
        visitor_key = f"visitor:{ip_address}:{user_agent[:50]}"
        
        # التحقق من الزيارة المكررة (خلال 30 دقيقة)
        if redis_client.exists(f"recent:{visitor_key}"):
            return jsonify({
                'message': 'Visit already counted recently',
                'counted': False
            }), 200
        
        # تسجيل الزيارة
        now = datetime.now()
        visit_data = {
            'ip_address': ip_address,
            'user_agent': user_agent,
            'page_url': page_url,
            'user_id': user_id,
            'timestamp': now.isoformat(),
            'date': now.strftime('%Y-%m-%d'),
            'hour': now.strftime('%H')
        }
        
        # حفظ بيانات الزيارة
        visit_id = f"visit:{now.timestamp()}"
        redis_client.setex(visit_id, 86400 * 30, json.dumps(visit_data))  # 30 يوم
        
        # تحديث العدادات
        redis_client.incr('total_visitors')
        redis_client.incr(f"daily_visitors:{now.strftime('%Y-%m-%d')}")
        redis_client.incr(f"hourly_visitors:{now.strftime('%Y-%m-%d:%H')}")
        redis_client.incr(f"page_visitors:{page_url}")
        
        # منع الزيارات المكررة لمدة 30 دقيقة
        redis_client.setex(f"recent:{visitor_key}", 1800, "1")
        
        # إحصائيات إضافية
        if user_id:
            redis_client.incr('registered_visitors')
            redis_client.incr(f"user_visits:{user_id}")
        else:
            redis_client.incr('anonymous_visitors')
        
        logger.info(f"New visit recorded: {ip_address} -> {page_url}")
        
        return jsonify({
            'message': 'Visit counted successfully',
            'counted': True,
            'visit_id': visit_id
        }), 201
        
    except Exception as e:
        logger.error(f"Error counting visitor: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/visitor/stats', methods=['GET'])
@require_api_key
def get_visitor_stats():
    """الحصول على إحصائيات الزوار"""
    try:
        # إحصائيات عامة
        total_visitors = redis_client.get('total_visitors') or 0
        registered_visitors = redis_client.get('registered_visitors') or 0
        anonymous_visitors = redis_client.get('anonymous_visitors') or 0
        
        # إحصائيات اليوم
        today = datetime.now().strftime('%Y-%m-%d')
        today_visitors = redis_client.get(f"daily_visitors:{today}") or 0
        
        # إحصائيات الساعة الحالية
        current_hour = datetime.now().strftime('%Y-%m-%d:%H')
        hour_visitors = redis_client.get(f"hourly_visitors:{current_hour}") or 0
        
        # أكثر الصفحات زيارة
        page_keys = redis_client.keys('page_visitors:*')
        popular_pages = []
        for key in page_keys[:10]:  # أول 10 صفحات
            page_url = key.replace('page_visitors:', '')
            count = redis_client.get(key) or 0
            popular_pages.append({
                'page_url': page_url,
                'visits': int(count)
            })
        
        popular_pages.sort(key=lambda x: x['visits'], reverse=True)
        
        # إحصائيات آخر 7 أيام
        daily_stats = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            count = redis_client.get(f"daily_visitors:{date}") or 0
            daily_stats.append({
                'date': date,
                'visits': int(count)
            })
        
        return jsonify({
            'total_visitors': int(total_visitors),
            'registered_visitors': int(registered_visitors),
            'anonymous_visitors': int(anonymous_visitors),
            'today_visitors': int(today_visitors),
            'current_hour_visitors': int(hour_visitors),
            'popular_pages': popular_pages,
            'daily_stats': daily_stats,
            'last_updated': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting visitor stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/visitor/live', methods=['GET'])
@require_api_key
def get_live_visitors():
    """الحصول على عدد الزوار المتصلين حالياً"""
    try:
        # الزوار النشطين خلال آخر 5 دقائق
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        active_visitors = 0
        
        # البحث في الزيارات الحديثة
        recent_keys = redis_client.keys('recent:visitor:*')
        active_visitors = len(recent_keys)
        
        return jsonify({
            'live_visitors': active_visitors,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting live visitors: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/visitor/reset', methods=['POST'])
@require_api_key
def reset_visitor_stats():
    """إعادة تعيين إحصائيات الزوار (للإدارة فقط)"""
    try:
        admin_key = request.headers.get('X-Admin-Key')
        if admin_key != app.config['ADMIN_KEY']:
            return jsonify({'error': 'Admin access required'}), 403
        
        # حذف جميع الإحصائيات
        keys_to_delete = []
        keys_to_delete.extend(redis_client.keys('total_visitors'))
        keys_to_delete.extend(redis_client.keys('daily_visitors:*'))
        keys_to_delete.extend(redis_client.keys('hourly_visitors:*'))
        keys_to_delete.extend(redis_client.keys('page_visitors:*'))
        keys_to_delete.extend(redis_client.keys('visit:*'))
        keys_to_delete.extend(redis_client.keys('recent:visitor:*'))
        
        if keys_to_delete:
            redis_client.delete(*keys_to_delete)
        
        logger.info("Visitor statistics reset by admin")
        
        return jsonify({
            'message': 'Visitor statistics reset successfully',
            'deleted_keys': len(keys_to_delete)
        }), 200
        
    except Exception as e:
        logger.error(f"Error resetting visitor stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
