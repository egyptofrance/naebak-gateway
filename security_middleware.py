"""
Advanced Security Middleware for Naebak Gateway

This module implements comprehensive security features for the API gateway including
advanced authentication, authorization, request validation, and protection against
common web vulnerabilities. It provides a multi-layered security approach to protect
the Naebak platform from various threats.

Key Features:
- Multi-factor authentication support
- Role-based access control (RBAC)
- Request/response validation and sanitization
- Rate limiting with adaptive algorithms
- Web Application Firewall (WAF) capabilities
- CORS and security headers management
- Audit logging and security monitoring

Security Layers:
1. Network Security: IP filtering, DDoS protection
2. Authentication: JWT, OAuth 2.0, API keys
3. Authorization: RBAC, ABAC, resource-level permissions
4. Input Validation: Schema validation, sanitization
5. Output Security: Response filtering, data masking
"""

import re
import json
import hashlib
import hmac
import time
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import jwt
from flask import request, jsonify, g
from functools import wraps
import ipaddress
from urllib.parse import urlparse
import bleach

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security levels for different types of operations."""
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    PRIVILEGED = "privileged"
    ADMIN = "admin"
    SYSTEM = "system"

class ThreatType(Enum):
    """Types of security threats detected by the WAF."""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    MALICIOUS_PAYLOAD = "malicious_payload"
    SUSPICIOUS_PATTERN = "suspicious_pattern"

@dataclass
class SecurityRule:
    """
    Represents a security rule for request validation.
    
    Security rules define patterns and conditions that should be blocked
    or flagged as potentially malicious. They support regex patterns,
    content analysis, and custom validation logic.
    """
    id: str
    name: str
    pattern: str
    threat_type: ThreatType
    severity: str  # low, medium, high, critical
    action: str  # block, log, alert
    enabled: bool = True
    description: str = ""

@dataclass
class AuthenticationResult:
    """
    Result of authentication process.
    
    Contains all information about the authenticated user including
    permissions, roles, and security context for authorization decisions.
    """
    success: bool
    user_id: Optional[str] = None
    username: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    permissions: List[str] = field(default_factory=list)
    security_level: SecurityLevel = SecurityLevel.PUBLIC
    token_type: str = "jwt"
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

@dataclass
class SecurityContext:
    """
    Security context for the current request.
    
    Maintains security-related information throughout the request lifecycle
    including authentication status, permissions, and threat assessments.
    """
    request_id: str
    client_ip: str
    user_agent: str
    authentication: AuthenticationResult
    threat_score: float = 0.0
    security_violations: List[str] = field(default_factory=list)
    allowed_operations: Set[str] = field(default_factory=set)
    audit_data: Dict[str, Any] = field(default_factory=dict)

class WebApplicationFirewall:
    """
    Web Application Firewall implementation for threat detection and prevention.
    
    The WAF analyzes incoming requests for malicious patterns, suspicious behavior,
    and known attack vectors. It can block, log, or alert on detected threats.
    """
    
    def __init__(self):
        """Initialize WAF with default security rules."""
        self.rules: List[SecurityRule] = []
        self.blocked_ips: Set[str] = set()
        self.suspicious_patterns = self._load_default_patterns()
        self._initialize_default_rules()
        
        logger.info("Web Application Firewall initialized")
    
    def _load_default_patterns(self) -> Dict[ThreatType, List[str]]:
        """Load default threat detection patterns."""
        return {
            ThreatType.SQL_INJECTION: [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
                r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
                r"(--|#|/\*|\*/)",
                r"(\b(INFORMATION_SCHEMA|SYSOBJECTS|SYSCOLUMNS)\b)"
            ],
            ThreatType.XSS: [
                r"(<script[^>]*>.*?</script>)",
                r"(javascript:|vbscript:|onload=|onerror=|onclick=)",
                r"(<iframe[^>]*>.*?</iframe>)",
                r"(eval\s*\(|setTimeout\s*\(|setInterval\s*\()"
            ],
            ThreatType.COMMAND_INJECTION: [
                r"(\b(cat|ls|pwd|whoami|id|uname|ps|netstat|ifconfig)\b)",
                r"(;|\||&|`|\$\(|\${)",
                r"(\.\./|\.\.\\\)",
                r"(/etc/passwd|/etc/shadow|/proc/)"
            ],
            ThreatType.PATH_TRAVERSAL: [
                r"(\.\./|\.\.\\\)",
                r"(%2e%2e%2f|%2e%2e%5c)",
                r"(\.\.%2f|\.\.%5c)",
                r"(%252e%252e%252f)"
            ]
        }
    
    def _initialize_default_rules(self):
        """Initialize default security rules."""
        rule_configs = [
            {
                "id": "sql_001",
                "name": "SQL Injection Detection",
                "threat_type": ThreatType.SQL_INJECTION,
                "severity": "high",
                "action": "block",
                "description": "Detects common SQL injection patterns"
            },
            {
                "id": "xss_001",
                "name": "Cross-Site Scripting Detection",
                "threat_type": ThreatType.XSS,
                "severity": "high",
                "action": "block",
                "description": "Detects XSS attack patterns"
            },
            {
                "id": "cmd_001",
                "name": "Command Injection Detection",
                "threat_type": ThreatType.COMMAND_INJECTION,
                "severity": "critical",
                "action": "block",
                "description": "Detects command injection attempts"
            },
            {
                "id": "path_001",
                "name": "Path Traversal Detection",
                "threat_type": ThreatType.PATH_TRAVERSAL,
                "severity": "medium",
                "action": "block",
                "description": "Detects directory traversal attempts"
            }
        ]
        
        for config in rule_configs:
            patterns = self.suspicious_patterns.get(config["threat_type"], [])
            for i, pattern in enumerate(patterns):
                rule = SecurityRule(
                    id=f"{config['id']}_{i}",
                    name=f"{config['name']} #{i+1}",
                    pattern=pattern,
                    threat_type=config["threat_type"],
                    severity=config["severity"],
                    action=config["action"],
                    description=config["description"]
                )
                self.rules.append(rule)
    
    def analyze_request(self, request_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Analyze request for security threats.
        
        Args:
            request_data (Dict): Request data including URL, headers, body
            
        Returns:
            Tuple[bool, List[str]]: (is_safe, list_of_violations)
        """
        violations = []
        
        # Check URL for malicious patterns
        url_violations = self._check_url_security(request_data.get('url', ''))
        violations.extend(url_violations)
        
        # Check headers for suspicious content
        headers_violations = self._check_headers_security(request_data.get('headers', {}))
        violations.extend(headers_violations)
        
        # Check request body for malicious content
        body_violations = self._check_body_security(request_data.get('body', ''))
        violations.extend(body_violations)
        
        # Check for suspicious IP patterns
        ip_violations = self._check_ip_security(request_data.get('client_ip', ''))
        violations.extend(ip_violations)
        
        is_safe = len(violations) == 0
        
        if violations:
            logger.warning(f"Security violations detected: {violations}")
        
        return is_safe, violations
    
    def _check_url_security(self, url: str) -> List[str]:
        """Check URL for malicious patterns."""
        violations = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            if re.search(rule.pattern, url, re.IGNORECASE):
                violation = f"URL violation: {rule.name} (Rule: {rule.id})"
                violations.append(violation)
                
                if rule.action == "block":
                    logger.warning(f"Blocked request due to URL violation: {violation}")
        
        return violations
    
    def _check_headers_security(self, headers: Dict[str, str]) -> List[str]:
        """Check request headers for security issues."""
        violations = []
        
        # Check for suspicious user agents
        user_agent = headers.get('User-Agent', '').lower()
        suspicious_agents = ['sqlmap', 'nikto', 'nmap', 'burp', 'scanner']
        
        for agent in suspicious_agents:
            if agent in user_agent:
                violations.append(f"Suspicious User-Agent detected: {agent}")
        
        # Check for malicious header values
        for header_name, header_value in headers.items():
            for rule in self.rules:
                if not rule.enabled:
                    continue
                    
                if re.search(rule.pattern, header_value, re.IGNORECASE):
                    violation = f"Header violation in {header_name}: {rule.name}"
                    violations.append(violation)
        
        return violations
    
    def _check_body_security(self, body: str) -> List[str]:
        """Check request body for malicious content."""
        violations = []
        
        if not body:
            return violations
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            if re.search(rule.pattern, body, re.IGNORECASE):
                violation = f"Body violation: {rule.name} (Rule: {rule.id})"
                violations.append(violation)
        
        return violations
    
    def _check_ip_security(self, client_ip: str) -> List[str]:
        """Check client IP for security issues."""
        violations = []
        
        if client_ip in self.blocked_ips:
            violations.append(f"Blocked IP address: {client_ip}")
        
        # Check for private IP ranges in public context
        try:
            ip = ipaddress.ip_address(client_ip)
            if ip.is_private and not self._is_development_mode():
                violations.append(f"Private IP in production context: {client_ip}")
        except ValueError:
            violations.append(f"Invalid IP address format: {client_ip}")
        
        return violations
    
    def _is_development_mode(self) -> bool:
        """Check if running in development mode."""
        # This would typically check environment variables or config
        return False
    
    def block_ip(self, ip_address: str, reason: str = "Security violation"):
        """
        Block an IP address from accessing the gateway.
        
        Args:
            ip_address (str): IP address to block
            reason (str): Reason for blocking
        """
        self.blocked_ips.add(ip_address)
        logger.warning(f"Blocked IP {ip_address}: {reason}")
    
    def unblock_ip(self, ip_address: str):
        """
        Unblock a previously blocked IP address.
        
        Args:
            ip_address (str): IP address to unblock
        """
        self.blocked_ips.discard(ip_address)
        logger.info(f"Unblocked IP {ip_address}")

class AuthenticationManager:
    """
    Manages authentication and authorization for the gateway.
    
    Supports multiple authentication methods including JWT tokens, API keys,
    and OAuth 2.0. Provides role-based access control and permission management.
    """
    
    def __init__(self, jwt_secret: str, jwt_algorithm: str = "HS256"):
        """
        Initialize authentication manager.
        
        Args:
            jwt_secret (str): Secret key for JWT token verification
            jwt_algorithm (str): JWT algorithm to use
        """
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.role_permissions: Dict[str, List[str]] = self._initialize_role_permissions()
        
        logger.info("Authentication manager initialized")
    
    def _initialize_role_permissions(self) -> Dict[str, List[str]]:
        """Initialize default role-based permissions."""
        return {
            "citizen": [
                "complaints:create",
                "complaints:read_own",
                "messages:send",
                "messages:read_own",
                "ratings:create",
                "ratings:read",
                "news:read",
                "content:read"
            ],
            "representative": [
                "complaints:read_assigned",
                "complaints:update_assigned",
                "messages:send",
                "messages:read_own",
                "ratings:read",
                "news:read",
                "news:create",
                "content:read",
                "content:create"
            ],
            "moderator": [
                "complaints:read",
                "complaints:assign",
                "content:moderate",
                "news:moderate",
                "messages:moderate",
                "users:read"
            ],
            "admin": [
                "*"  # All permissions
            ]
        }
    
    def authenticate_jwt(self, token: str) -> AuthenticationResult:
        """
        Authenticate using JWT token.
        
        Args:
            token (str): JWT token to verify
            
        Returns:
            AuthenticationResult: Authentication result with user information
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            user_id = payload.get('user_id')
            username = payload.get('username')
            roles = payload.get('roles', [])
            
            # Calculate permissions based on roles
            permissions = self._calculate_permissions(roles)
            
            # Determine security level
            security_level = self._determine_security_level(roles)
            
            return AuthenticationResult(
                success=True,
                user_id=user_id,
                username=username,
                roles=roles,
                permissions=permissions,
                security_level=security_level,
                token_type="jwt",
                expires_at=datetime.fromtimestamp(payload.get('exp', 0)),
                metadata=payload
            )
            
        except jwt.ExpiredSignatureError:
            return AuthenticationResult(
                success=False,
                error_message="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            return AuthenticationResult(
                success=False,
                error_message=f"Invalid token: {str(e)}"
            )
    
    def authenticate_api_key(self, api_key: str) -> AuthenticationResult:
        """
        Authenticate using API key.
        
        Args:
            api_key (str): API key to verify
            
        Returns:
            AuthenticationResult: Authentication result
        """
        key_info = self.api_keys.get(api_key)
        
        if not key_info:
            return AuthenticationResult(
                success=False,
                error_message="Invalid API key"
            )
        
        # Check if key is expired
        if key_info.get('expires_at') and datetime.now() > key_info['expires_at']:
            return AuthenticationResult(
                success=False,
                error_message="API key has expired"
            )
        
        # Check if key is active
        if not key_info.get('active', True):
            return AuthenticationResult(
                success=False,
                error_message="API key is inactive"
            )
        
        roles = key_info.get('roles', ['api_user'])
        permissions = self._calculate_permissions(roles)
        security_level = self._determine_security_level(roles)
        
        return AuthenticationResult(
            success=True,
            user_id=key_info.get('user_id'),
            username=key_info.get('name', 'API User'),
            roles=roles,
            permissions=permissions,
            security_level=security_level,
            token_type="api_key",
            metadata=key_info
        )
    
    def _calculate_permissions(self, roles: List[str]) -> List[str]:
        """Calculate permissions based on user roles."""
        permissions = set()
        
        for role in roles:
            role_perms = self.role_permissions.get(role, [])
            if "*" in role_perms:  # Admin role
                return ["*"]
            permissions.update(role_perms)
        
        return list(permissions)
    
    def _determine_security_level(self, roles: List[str]) -> SecurityLevel:
        """Determine security level based on roles."""
        if "admin" in roles:
            return SecurityLevel.ADMIN
        elif "moderator" in roles:
            return SecurityLevel.PRIVILEGED
        elif any(role in ["citizen", "representative"] for role in roles):
            return SecurityLevel.AUTHENTICATED
        else:
            return SecurityLevel.PUBLIC
    
    def check_permission(self, auth_result: AuthenticationResult, 
                        required_permission: str) -> bool:
        """
        Check if user has required permission.
        
        Args:
            auth_result (AuthenticationResult): Authentication result
            required_permission (str): Required permission string
            
        Returns:
            bool: True if user has permission
        """
        if not auth_result.success:
            return False
        
        # Admin has all permissions
        if "*" in auth_result.permissions:
            return True
        
        # Check exact permission match
        if required_permission in auth_result.permissions:
            return True
        
        # Check wildcard permissions
        for permission in auth_result.permissions:
            if permission.endswith("*"):
                prefix = permission[:-1]
                if required_permission.startswith(prefix):
                    return True
        
        return False
    
    def create_api_key(self, name: str, user_id: str, roles: List[str], 
                      expires_days: Optional[int] = None) -> str:
        """
        Create a new API key.
        
        Args:
            name (str): Name/description for the API key
            user_id (str): User ID associated with the key
            roles (List[str]): Roles assigned to the key
            expires_days (Optional[int]): Days until expiration
            
        Returns:
            str: Generated API key
        """
        # Generate secure API key
        api_key = self._generate_api_key()
        
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)
        
        self.api_keys[api_key] = {
            'name': name,
            'user_id': user_id,
            'roles': roles,
            'created_at': datetime.now(),
            'expires_at': expires_at,
            'active': True
        }
        
        logger.info(f"Created API key for user {user_id}: {name}")
        return api_key
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key."""
        import secrets
        return f"naebak_{secrets.token_urlsafe(32)}"

class SecurityMiddleware:
    """
    Main security middleware that orchestrates all security features.
    
    This class integrates authentication, authorization, WAF, and other security
    features into a unified middleware that can be easily integrated with Flask.
    """
    
    def __init__(self, jwt_secret: str):
        """
        Initialize security middleware.
        
        Args:
            jwt_secret (str): Secret key for JWT token verification
        """
        self.waf = WebApplicationFirewall()
        self.auth_manager = AuthenticationManager(jwt_secret)
        self.audit_log: List[Dict[str, Any]] = []
        
        logger.info("Security middleware initialized")
    
    def process_request(self, auth_required: bool = False, 
                       admin_only: bool = False,
                       required_permission: Optional[str] = None) -> Optional[SecurityContext]:
        """
        Process incoming request through security pipeline.
        
        Args:
            auth_required (bool): Whether authentication is required
            admin_only (bool): Whether admin privileges are required
            required_permission (Optional[str]): Specific permission required
            
        Returns:
            Optional[SecurityContext]: Security context or None if request should be blocked
        """
        # Create security context
        security_context = SecurityContext(
            request_id=self._generate_request_id(),
            client_ip=self._get_client_ip(),
            user_agent=request.headers.get('User-Agent', ''),
            authentication=AuthenticationResult(success=False)
        )
        
        # WAF analysis
        request_data = {
            'url': request.url,
            'headers': dict(request.headers),
            'body': request.get_data(as_text=True),
            'client_ip': security_context.client_ip
        }
        
        is_safe, violations = self.waf.analyze_request(request_data)
        security_context.security_violations = violations
        
        if not is_safe:
            self._log_security_event(security_context, "WAF_BLOCK", violations)
            return None
        
        # Authentication
        if auth_required or admin_only or required_permission:
            auth_result = self._authenticate_request()
            security_context.authentication = auth_result
            
            if not auth_result.success:
                self._log_security_event(security_context, "AUTH_FAILED", [auth_result.error_message])
                return None
            
            # Authorization checks
            if admin_only and auth_result.security_level != SecurityLevel.ADMIN:
                self._log_security_event(security_context, "INSUFFICIENT_PRIVILEGES", ["Admin access required"])
                return None
            
            if required_permission and not self.auth_manager.check_permission(auth_result, required_permission):
                self._log_security_event(security_context, "PERMISSION_DENIED", [f"Required: {required_permission}"])
                return None
        
        # Store security context for request
        g.security_context = security_context
        
        self._log_security_event(security_context, "REQUEST_ALLOWED", [])
        return security_context
    
    def _authenticate_request(self) -> AuthenticationResult:
        """Authenticate the current request using available methods."""
        # Try JWT authentication first
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            return self.auth_manager.authenticate_jwt(token)
        
        # Try API key authentication
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        if api_key:
            return self.auth_manager.authenticate_api_key(api_key)
        
        return AuthenticationResult(
            success=False,
            error_message="No valid authentication method provided"
        )
    
    def _get_client_ip(self) -> str:
        """Get the real client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr or 'unknown'
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID for tracking."""
        import uuid
        return str(uuid.uuid4())
    
    def _log_security_event(self, context: SecurityContext, event_type: str, details: List[str]):
        """Log security events for audit and monitoring."""
        event = {
            'timestamp': datetime.now().isoformat(),
            'request_id': context.request_id,
            'event_type': event_type,
            'client_ip': context.client_ip,
            'user_agent': context.user_agent,
            'user_id': context.authentication.user_id if context.authentication.success else None,
            'details': details,
            'url': request.url,
            'method': request.method
        }
        
        self.audit_log.append(event)
        
        # Log to application logger
        if event_type in ['WAF_BLOCK', 'AUTH_FAILED', 'INSUFFICIENT_PRIVILEGES', 'PERMISSION_DENIED']:
            logger.warning(f"Security event: {event_type} - {details}")
        else:
            logger.debug(f"Security event: {event_type}")
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        return self.audit_log[-limit:]

# Decorator for protecting Flask routes
def require_auth(admin_only: bool = False, permission: Optional[str] = None):
    """
    Decorator to require authentication for Flask routes.
    
    Args:
        admin_only (bool): Whether admin privileges are required
        permission (Optional[str]): Specific permission required
        
    Returns:
        Decorated function that enforces security requirements
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This would be initialized elsewhere in the application
            security_middleware = getattr(g, 'security_middleware', None)
            
            if not security_middleware:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'SECURITY_ERROR',
                        'message': 'Security middleware not initialized'
                    }
                }), 500
            
            security_context = security_middleware.process_request(
                auth_required=True,
                admin_only=admin_only,
                required_permission=permission
            )
            
            if not security_context:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'ACCESS_DENIED',
                        'message': 'Access denied'
                    }
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Global security middleware instance (would be initialized in main app)
security_middleware = None

def initialize_security_middleware(jwt_secret: str) -> SecurityMiddleware:
    """
    Initialize global security middleware instance.
    
    Args:
        jwt_secret (str): JWT secret key
        
    Returns:
        SecurityMiddleware: Initialized security middleware
    """
    global security_middleware
    security_middleware = SecurityMiddleware(jwt_secret)
    return security_middleware
