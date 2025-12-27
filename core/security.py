"""
Security and Authentication System for VT ULTRA PRO
"""
import hashlib
import hmac
import base64
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import jwt
from cryptography.fernet import Fernet
import bcrypt
import re
import ipaddress
from functools import wraps
import time

class SecuritySystem:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
        self.fernet = Fernet(Fernet.generate_key())
        
        # Security configurations
        self.config = {
            'jwt_expiry_hours': 24,
            'max_login_attempts': 5,
            'password_min_length': 8,
            'session_timeout_minutes': 30,
            'rate_limit_requests': 100,
            'rate_limit_period': 3600  # 1 hour
        }
        
        # Security logs
        self.security_logs = []
        self.failed_attempts = {}
        self.ip_blacklist = set()
        
    # JWT Authentication
    def create_jwt_token(self, user_id: str, user_data: Dict = None) -> str:
        """Create JWT token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=self.config['jwt_expiry_hours']),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        if user_data:
            payload.update(user_data)
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            self.log_security_event('jwt_expired', {'token': token[:20]})
            return None
        except jwt.InvalidTokenError:
            self.log_security_event('jwt_invalid', {'token': token[:20]})
            return None
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create refresh token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=30),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token"""
        payload = self.verify_jwt_token(refresh_token)
        if payload and payload.get('type') == 'refresh':
            return self.create_jwt_token(payload['user_id'])
        return None
    
    # Password Security
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed.decode()
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode(), hashed_password.encode())
        except:
            return False
    
    def generate_strong_password(self, length: int = 12) -> str:
        """Generate strong password"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(characters) for _ in range(length))
        return password
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < self.config['password_min_length']:
            errors.append(f"Password must be at least {self.config['password_min_length']} characters")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    # Encryption/Decryption
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        encrypted = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            encrypted = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted)
            return decrypted.decode()
        except:
            return ""
    
    def encrypt_dict(self, data: Dict) -> str:
        """Encrypt dictionary"""
        json_str = json.dumps(data)
        return self.encrypt_data(json_str)
    
    def decrypt_dict(self, encrypted_data: str) -> Optional[Dict]:
        """Decrypt to dictionary"""
        try:
            decrypted = self.decrypt_data(encrypted_data)
            return json.loads(decrypted)
        except:
            return None
    
    # API Security
    def create_api_key(self, user_id: str, permissions: List[str]) -> str:
        """Create API key"""
        key_data = {
            'user_id': user_id,
            'permissions': permissions,
            'created_at': datetime.utcnow().isoformat(),
            'key_id': secrets.token_hex(16)
        }
        
        encrypted = self.encrypt_dict(key_data)
        return f"vtpro_{encrypted}"
    
    def validate_api_key(self, api_key: str, required_permission: str = None) -> bool:
        """Validate API key"""
        if not api_key.startswith('vtpro_'):
            return False
        
        try:
            encrypted = api_key[6:]  # Remove prefix
            key_data = self.decrypt_dict(encrypted)
            
            if not key_data:
                return False
            
            # Check expiration (30 days)
            created_at = datetime.fromisoformat(key_data['created_at'])
            if datetime.utcnow() - created_at > timedelta(days=30):
                return False
            
            # Check permission
            if required_permission:
                if required_permission not in key_data.get('permissions', []):
                    return False
            
            return True
        except:
            return False
    
    # Rate Limiting
    def check_rate_limit(self, ip_address: str, endpoint: str) -> Tuple[bool, Dict]:
        """Check rate limit for IP and endpoint"""
        key = f"{ip_address}_{endpoint}"
        
        if key in self.failed_attempts:
            attempts = self.failed_attempts[key]
            
            # Check if IP is blacklisted
            if ip_address in self.ip_blacklist:
                return False, {
                    'allowed': False,
                    'reason': 'ip_blacklisted',
                    'retry_after': None
                }
            
            # Check rate limit
            window_start = time.time() - self.config['rate_limit_period']
            recent_attempts = [t for t in attempts if t > window_start]
            
            if len(recent_attempts) >= self.config['rate_limit_requests']:
                # Auto-blacklist if excessive
                if len(recent_attempts) > self.config['rate_limit_requests'] * 2:
                    self.ip_blacklist.add(ip_address)
                    self.log_security_event('ip_auto_blacklisted', {'ip': ip_address})
                
                retry_after = int(window_start + self.config['rate_limit_period'] - time.time())
                return False, {
                    'allowed': False,
                    'reason': 'rate_limit_exceeded',
                    'retry_after': retry_after
                }
        
        return True, {'allowed': True, 'reason': 'ok'}
    
    def record_request(self, ip_address: str, endpoint: str):
        """Record API request for rate limiting"""
        key = f"{ip_address}_{endpoint}"
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = []
        
        self.failed_attempts[key].append(time.time())
        
        # Clean old entries
        window_start = time.time() - (self.config['rate_limit_period'] * 2)
        self.failed_attempts[key] = [t for t in self.failed_attempts[key] if t > window_start]
    
    # Input Validation
    def sanitize_input(self, input_str: str, input_type: str = 'general') -> str:
        """Sanitize user input"""
        if not input_str:
            return ""
        
        # Remove null bytes
        input_str = input_str.replace('\0', '')
        
        if input_type == 'sql':
            # Basic SQL injection prevention
            sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION', 'OR', 'AND']
            for keyword in sql_keywords:
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                input_str = pattern.sub('', input_str)
        
        elif input_type == 'html':
            # HTML/JS injection prevention
            input_str = input_str.replace('<', '&lt;').replace('>', '&gt;')
            input_str = input_str.replace('"', '&quot;').replace("'", '&#39;')
            input_str = input_str.replace('(', '&#40;').replace(')', '&#41;')
        
        elif input_type == 'url':
            # URL validation
            if not re.match(r'^https?://', input_str):
                input_str = f'https://{input_str}'
        
        # Remove control characters
        input_str = ''.join(char for char in input_str if ord(char) >= 32)
        
        return input_str.strip()
    
    def validate_email(self, email: str) -> bool:
        """Validate email address"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def validate_url(self, url: str) -> bool:
        """Validate URL"""
        try:
            result = re.match(r'^https?://', url)
            return bool(result)
        except:
            return False
    
    def validate_ip_address(self, ip: str) -> bool:
        """Validate IP address"""
        try:
            ipaddress.ip_address(ip)
            return True
        except:
            return False
    
    # CSRF Protection
    def generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        return secrets.token_hex(32)
    
    def validate_csrf_token(self, token: str, stored_token: str) -> bool:
        """Validate CSRF token"""
        return hmac.compare_digest(token, stored_token)
    
    # Two-Factor Authentication
    def generate_2fa_code(self, length: int = 6) -> str:
        """Generate 2FA code"""
        return ''.join(str(secrets.randbelow(10)) for _ in range(length))
    
    def verify_2fa_code(self, code: str, stored_code: str, 
                       expiry_minutes: int = 5) -> bool:
        """Verify 2FA code"""
        # In production, store code with expiry in database
        return code == stored_code
    
    # Security Headers
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for HTTP responses"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }
    
    # Security Logging
    def log_security_event(self, event_type: str, details: Dict):
        """Log security event"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details,
            'ip_address': details.get('ip', 'unknown')
        }
        
        self.security_logs.append(log_entry)
        
        # Keep only last 1000 logs
        if len(self.security_logs) > 1000:
            self.security_logs = self.security_logs[-1000:]
    
    def get_security_logs(self, hours: int = 24) -> List[Dict]:
        """Get security logs for period"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            log for log in self.security_logs
            if datetime.fromisoformat(log['timestamp']) > cutoff
        ]
    
    # Session Management
    def create_session(self, user_id: str, user_agent: str, 
                      ip_address: str) -> Dict:
        """Create user session"""
        session_id = secrets.token_hex(32)
        
        session = {
            'session_id': session_id,
            'user_id': user_id,
            'user_agent': user_agent,
            'ip_address': ip_address,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'is_active': True
        }
        
        # Encrypt session data
        encrypted_session = self.encrypt_dict(session)
        
        return {
            'session_id': session_id,
            'encrypted_data': encrypted_session,
            'expires_in': self.config['session_timeout_minutes'] * 60
        }
    
    def validate_session(self, session_id: str, encrypted_data: str,
                        user_agent: str, ip_address: str) -> bool:
        """Validate user session"""
        try:
            session = self.decrypt_dict(encrypted_data)
            if not session:
                return False
            
            # Check session ID match
            if session.get('session_id') != session_id:
                return False
            
            # Check if active
            if not session.get('is_active', False):
                return False
            
            # Check timeout
            last_activity = datetime.fromisoformat(session['last_activity'])
            timeout = timedelta(minutes=self.config['session_timeout_minutes'])
            
            if datetime.utcnow() - last_activity > timeout:
                session['is_active'] = False
                return False
            
            # Update last activity
            session['last_activity'] = datetime.utcnow().isoformat()
            
            return True
        except:
            return False
    
    def invalidate_session(self, session_id: str):
        """Invalidate session"""
        # In production, mark as inactive in database
        pass
    
    # Security Decorators
    def require_auth(self, func):
        """Decorator for requiring authentication"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request:
                return {'error': 'Unauthorized'}, 401
            
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return {'error': 'Unauthorized'}, 401
            
            token = auth_header[7:]
            payload = self.verify_jwt_token(token)
            
            if not payload:
                return {'error': 'Invalid token'}, 401
            
            # Add user to kwargs
            kwargs['user'] = payload
            
            return func(*args, **kwargs)
        return wrapper
    
    def require_api_key(self, permission: str = None):
        """Decorator for requiring API key"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                request = kwargs.get('request')
                if not request:
                    return {'error': 'Unauthorized'}, 401
                
                api_key = request.headers.get('X-API-Key')
                if not api_key:
                    return {'error': 'API key required'}, 401
                
                if not self.validate_api_key(api_key, permission):
                    return {'error': 'Invalid API key'}, 401
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def rate_limit(self, func):
        """Decorator for rate limiting"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request:
                return func(*args, **kwargs)
            
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            endpoint = request.path
            
            allowed, info = self.check_rate_limit(ip_address, endpoint)
            
            if not allowed:
                return {
                    'error': 'Rate limit exceeded',
                    'retry_after': info.get('retry_after')
                }, 429
            
            self.record_request(ip_address, endpoint)
            
            return func(*args, **kwargs)
        return wrapper
    
    # File Security
    def validate_file_upload(self, file_data: bytes, 
                           allowed_extensions: List[str],
                           max_size_mb: int = 10) -> Tuple[bool, str]:
        """Validate file upload"""
        # Check size
        max_size = max_size_mb * 1024 * 1024
        if len(file_data) > max_size:
            return False, f"File too large. Maximum size: {max_size_mb}MB"
        
        # Check file type by magic bytes
        file_type = self._detect_file_type(file_data)
        
        if not file_type:
            return False, "Invalid file type"
        
        # Check extension
        if allowed_extensions and file_type not in allowed_extensions:
            return False, f"File type not allowed. Allowed: {', '.join(allowed_extensions)}"
        
        return True, file_type
    
    def _detect_file_type(self, file_data: bytes) -> Optional[str]:
        """Detect file type from magic bytes"""
        magic_numbers = {
            b'\xff\xd8\xff': 'jpg',
            b'\x89PNG\r\n\x1a\n': 'png',
            b'GIF87a': 'gif',
            b'GIF89a': 'gif',
            b'%PDF': 'pdf',
            b'PK\x03\x04': 'zip',
            b'\x1f\x8b\x08': 'gz'
        }
        
        for magic, file_type in magic_numbers.items():
            if file_data.startswith(magic):
                return file_type
        
        return None
    
    # Data Masking
    def mask_sensitive_data(self, data: str, data_type: str) -> str:
        """Mask sensitive data for logging"""
        if data_type == 'email':
            if '@' in data:
                local, domain = data.split('@', 1)
                if len(local) > 2:
                    return f"{local[0]}***{local[-1]}@{domain}"
                else:
                    return f"***@{domain}"
        
        elif data_type == 'phone':
            if len(data) >= 10:
                return f"{data[:3]}***{data[-4:]}"
        
        elif data_type == 'credit_card':
            if len(data) >= 16:
                return f"**** **** **** {data[-4:]}"
        
        elif data_type == 'ip':
            if '.' in data:
                parts = data.split('.')
                return f"{parts[0]}.***.***.{parts[-1]}"
        
        # Default: show first and last 2 characters
        if len(data) > 4:
            return f"{data[:2]}***{data[-2:]}"
        else:
            return "***"
    
    # Security Audit
    def run_security_audit(self) -> Dict:
        """Run security audit"""
        audit_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'checks': [],
            'overall_score': 0,
            'recommendations': []
        }
        
        # Check password policy
        pass_policy = self.config['password_min_length'] >= 8
        audit_results['checks'].append({
            'name': 'password_policy',
            'passed': pass_policy,
            'details': f"Minimum length: {self.config['password_min_length']}"
        })
        
        # Check rate limiting
        rate_limit = self.config['rate_limit_requests'] > 0
        audit_results['checks'].append({
            'name': 'rate_limiting',
            'passed': rate_limit,
            'details': f"Limit: {self.config['rate_limit_requests']} per hour"
        })
        
        # Check session timeout
        session_timeout = self.config['session_timeout_minutes'] > 0
        audit_results['checks'].append({
            'name': 'session_timeout',
            'passed': session_timeout,
            'details': f"Timeout: {self.config['session_timeout_minutes']} minutes"
        })
        
        # Check JWT expiry
        jwt_expiry = self.config['jwt_expiry_hours'] > 0
        audit_results['checks'].append({
            'name': 'jwt_expiry',
            'passed': jwt_expiry,
            'details': f"Expiry: {self.config['jwt_expiry_hours']} hours"
        })
        
        # Calculate score
        passed = sum(1 for check in audit_results['checks'] if check['passed'])
        total = len(audit_results['checks'])
        audit_results['overall_score'] = int((passed / total) * 100)
        
        # Generate recommendations
        if not pass_policy:
            audit_results['recommendations'].append(
                "Increase minimum password length to 12 characters"
            )
        
        if not rate_limit:
            audit_results['recommendations'].append(
                "Implement rate limiting for API endpoints"
            )
        
        return audit_results