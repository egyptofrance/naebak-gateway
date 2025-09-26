
"""
Naebak Gateway Service - Central API Gateway

This is the main application file for the Naebak Gateway Service, which serves as the central
entry point for all microservices in the Naebak platform. The gateway handles request routing,
authentication, rate limiting, and provides a unified API interface for frontend applications.

Key Features:
- Centralized request routing to microservices
- JWT-based authentication and authorization
- Rate limiting and security controls
- Service discovery and health monitoring
- CORS handling for web applications
- Comprehensive error handling and logging

Architecture:
The gateway implements a reverse proxy pattern, routing incoming requests to appropriate
microservices based on URL patterns while handling cross-cutting concerns like authentication,
logging, and error handling centrally.
"""

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import requests
import logging
import os
from datetime import datetime
import jwt
import json

from config import Config
from constants import APP_NAME, APP_VERSION
from utils.load_balancer import LoadBalancer
from utils.rate_limiter import init_limiter

# Setup application
app = Flask(__name__)
app.config.from_object(Config)

# Setup database for shared reference data
app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Setup CORS
CORS(app, resources={r"/*": {"origins": Config.CORS_ORIGINS}})

# Setup Rate Limiting
init_limiter(app)

# Setup Logging
logging.basicConfig(
    level=logging.INFO if not Config.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Service routing map for Naebak platform
SERVICE_ROUTES = {
    "/api/auth/": {
        "service": "naebak-auth-service",
        "urls": Config.AUTH_SERVICE_URLS,
        "timeout": 10,
        "auth_required": False
    },
    "/api/admin/": {
        "service": "naebak-admin-service",
        "urls": Config.ADMIN_SERVICE_URLS,
        "timeout": 15,
        "auth_required": True,
        "admin_only": True
    },
    "/api/complaints/": {
        "service": "naebak-complaints-service",
        "urls": Config.COMPLAINTS_SERVICE_URLS,
        "timeout": 20,
        "auth_required": True
    },
    "/api/messages/": {
        "service": "naebak-messaging-service",
        "urls": Config.MESSAGING_SERVICE_URLS,
        "timeout": 10,
        "auth_required": True
    },
    "/api/ratings/": {
        "service": "naebak-ratings-service",
        "urls": Config.RATINGS_SERVICE_URLS,
        "timeout": 5,
        "auth_required": True
    },
    "/api/visitors/": {
        "service": "naebak-visitor-counter-service",
        "urls": Config.VISITOR_SERVICE_URLS,
        "timeout": 3,
        "auth_required": False
    },
    "/api/news/": {
        "service": "naebak-news-service",
        "urls": Config.NEWS_SERVICE_URLS,
        "timeout": 5,
        "auth_required": False
    },
    "/api/notifications/": {
        "service": "naebak-notifications-service",
        "urls": Config.NOTIFICATIONS_SERVICE_URLS,
        "timeout": 8,
        "auth_required": True
    },
    "/api/banners/": {
        "service": "naebak-banner-service",
        "urls": Config.BANNER_SERVICE_URLS,
        "timeout": 10,
        "auth_required": False
    },
    "/api/content/": {
        "service": "naebak-content-service",
        "urls": Config.CONTENT_SERVICE_URLS,
        "timeout": 15,
        "auth_required": False
    },
    "/api/statistics/": {
        "service": "naebak-statistics-service",
        "urls": Config.STATISTICS_SERVICE_URLS,
        "timeout": 10,
        "auth_required": False
    },
    "/api/themes/": {
        "service": "naebak-theme-service",
        "urls": Config.THEME_SERVICE_URLS,
        "timeout": 5,
        "auth_required": True
    }
}

# Initialize load balancers for each service
for config in SERVICE_ROUTES.values():
    config['load_balancer'] = LoadBalancer(config['urls'])

def verify_jwt_token(token):
    """
    Verify the validity of a JWT token.
    
    This function validates JWT tokens used for authentication across the platform.
    It checks token signature, expiration, and extracts user information for
    authorization decisions.
    
    Args:
        token (str): The JWT token to verify.
        
    Returns:
        dict or None: Token payload if valid, None if invalid or expired.
        
    Security Notes:
        - Uses platform-wide secret key for token verification
        - Handles both expired and malformed tokens gracefully
        - Returns user information for downstream authorization
    """
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def check_authentication(route_config):
    """
    Check authentication requirements for protected routes.
    
    This function implements the gateway's authentication and authorization logic,
    verifying JWT tokens and checking role-based permissions for protected endpoints.
    
    Args:
        route_config (dict): Route configuration including auth requirements.
        
    Returns:
        tuple: (is_valid, result) where is_valid is boolean and result is either
               error message (if invalid) or user payload (if valid).
               
    Authorization Levels:
        - Public routes: No authentication required
        - Protected routes: Valid JWT token required
        - Admin routes: Valid JWT token with admin role required
    """
    if not route_config.get('auth_required', False):
        return True, None
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False, "Missing or invalid authorization header"
    
    token = auth_header.split(' ')[1]
    payload = verify_jwt_token(token)
    
    if not payload:
        return False, "Invalid or expired token"
    
    # Check admin privileges if required
    if route_config.get('admin_only', False):
        if not payload.get('is_admin', False):
            return False, "Admin privileges required"
    
    return True, payload

@app.route("/health", methods=["GET"])
def health_check():
    """
    Gateway health check endpoint.
    
    This endpoint provides health status information for the gateway service,
    including service version, timestamp, and the number of configured routes.
    It's used by load balancers and monitoring systems.
    
    Returns:
        JSON response with gateway health information.
    """
    return jsonify({
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "services_count": len(SERVICE_ROUTES)
    }), 200

@app.route("/api/gateway/services", methods=["GET"])
def list_services():
    """
    List all available services and their configurations.
    
    This endpoint provides service discovery information, listing all microservices
    accessible through the gateway along with their authentication requirements.
    It's useful for frontend applications and API documentation.
    
    Returns:
        JSON response with service list including:
        - Route patterns for each service
        - Authentication requirements
        - Admin-only restrictions
        - Total service count
    """
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
    """
    Find the matching service route for a given request path.
    
    This function implements the routing logic that determines which microservice
    should handle a given request based on URL patterns defined in SERVICE_ROUTES.
    
    Args:
        path (str): The request path to match against service routes.
        
    Returns:
        tuple: (route_pattern, route_config) if match found, (None, None) otherwise.
        
    Routing Logic:
        - Uses prefix matching for flexible route handling
        - Returns the first matching route (order matters)
        - Supports nested paths within service routes
    """
    for route_pattern, config in SERVICE_ROUTES.items():
        if path.startswith(route_pattern.rstrip('/')):
            return route_pattern, config
    return None, None

@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def proxy_request(path):
    """
    General proxy endpoint for routing requests to appropriate microservices.
    
    This is the core gateway functionality that handles request routing, authentication,
    and proxying to backend microservices. It implements a reverse proxy pattern with
    comprehensive error handling and security controls.
    
    Args:
        path (str): The API path to be routed to the appropriate microservice.
        
    Returns:
        Response: Proxied response from the target microservice or error response.
        
    Request Flow:
        1. Parse incoming request path
        2. Find matching service route
        3. Verify authentication if required
        4. Build target URL and headers
        5. Proxy request to microservice
        6. Return response with proper error handling
        
    Security Features:
        - JWT token validation for protected routes
        - Role-based access control for admin endpoints
        - Request timeout protection
        - Header sanitization and user context injection
    """
    full_path = f"/api/{path}"
    logger.debug(f"Incoming request for path: {full_path}")
    
    # Find matching service
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
    
    # Check authentication
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
    
    # Build target URL
    service_path = full_path[len(route_pattern.rstrip('/')):]
    if not service_path.startswith('/'):
        service_path = '/' + service_path
    
    base_url = route_config['load_balancer'].get_next_service_url()
    target_url = f"{base_url}{service_path}"
    
    logger.info(f"Proxying request to {route_config['service']}: {request.method} {target_url}")
    
    try:
        # Setup headers
        headers = dict(request.headers)
        if "Host" in headers:
            del headers["Host"]
        
        # Add user information if authenticated
        if auth_result and isinstance(auth_result, dict):
            headers['X-User-ID'] = str(auth_result.get('user_id', ''))
            headers['X-User-Role'] = auth_result.get('role', 'user')
        
        # Proxy the request
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=route_config.get('timeout', Config.DEFAULT_TIMEOUT)
        )
        
        # Build response
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
    """
    Handle 404 Not Found errors with consistent JSON response format.
    
    Args:
        error: Flask error object.
        
    Returns:
        JSON response with standardized error format.
    """
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
    """
    Handle 500 Internal Server errors with consistent JSON response format.
    
    Args:
        error: Flask error object.
        
    Returns:
        JSON response with standardized error format.
    """
    return jsonify({
        "success": False,
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Internal Server Error"
        },
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == "__main__":
    # Create database tables
    with app.app_context():
        db.create_all()
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )

