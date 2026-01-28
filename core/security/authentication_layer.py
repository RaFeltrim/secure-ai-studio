#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - Authentication Layer
API Key and JWT authentication for access control

Features:
- API Key authentication
- JWT token generation and validation
- Role-based access control
- Rate limiting integration
- Session management
"""

import jwt
import hashlib
import secrets
import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from cryptography.fernet import Fernet

@dataclass
class User:
    """User data structure"""
    user_id: str
    username: str
    role: str  # admin, user, guest
    api_key: str
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True

@dataclass
class AuthToken:
    """Authentication token data"""
    token: str
    user_id: str
    expires_at: datetime
    scope: List[str]  # permissions: generate, read, admin
    issued_at: datetime

class AuthenticationManager:
    """
    Central authentication management system
    """
    
    def __init__(self, config_path: str = "config/auth.conf"):
        """Initialize authentication manager"""
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        
        # Secret keys
        self.jwt_secret = self.config.get('jwt_secret', secrets.token_urlsafe(32))
        self.api_key_salt = self.config.get('api_key_salt', secrets.token_urlsafe(16))
        
        # User storage (in production, use database)
        self.users = {}
        self.api_keys = {}
        self.active_tokens = {}
        
        # Rate limiting
        self.request_history = {}
        self.rate_limits = self.config.get('rate_limits', {
            'user': 100,  # requests per hour
            'guest': 10,
            'admin': 1000
        })
        
        self.logger.info("🔐 Authentication Manager initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('AuthManager')
        logger.setLevel(logging.INFO)
        return logger
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load authentication configuration"""
        default_config = {
            'jwt_secret': secrets.token_urlsafe(32),
            'api_key_salt': secrets.token_urlsafe(16),
            'token_expiry_hours': 24,
            'rate_limits': {
                'user': 100,
                'guest': 10,
                'admin': 1000
            },
            'require_https': True
        }
        
        try:
            if False:  # os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                return default_config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return default_config
    
    def create_user(self, username: str, role: str = "user") -> User:
        """Create a new user with API key"""
        user_id = f"user_{secrets.token_urlsafe(8)}"
        
        # Generate API key
        api_key_raw = secrets.token_urlsafe(32)
        api_key_hash = hashlib.sha256(
            (api_key_raw + self.api_key_salt).encode()
        ).hexdigest()
        
        user = User(
            user_id=user_id,
            username=username,
            role=role,
            api_key=api_key_hash,
            created_at=datetime.now().isoformat()
        )
        
        # Store user
        self.users[user_id] = user
        self.api_keys[api_key_hash] = user_id
        
        self.logger.info(f"👤 Created user: {username} ({user_id}) with role: {role}")
        
        # Return user with plain API key (only shown once)
        return User(
            user_id=user_id,
            username=username,
            role=role,
            api_key=api_key_raw,  # Plain key for initial return
            created_at=user.created_at
        )
    
    def authenticate_api_key(self, api_key: str) -> Optional[User]:
        """Authenticate user by API key"""
        # Hash the provided API key
        api_key_hash = hashlib.sha256(
            (api_key + self.api_key_salt).encode()
        ).hexdigest()
        
        # Check if API key exists
        if api_key_hash in self.api_keys:
            user_id = self.api_keys[api_key_hash]
            user = self.users.get(user_id)
            
            if user and user.is_active:
                # Update last login
                user.last_login = datetime.now().isoformat()
                return user
        
        return None
    
    def generate_jwt_token(self, user: User, scope: List[str] = None) -> str:
        """Generate JWT token for authenticated user"""
        if scope is None:
            scope = self._get_role_scopes(user.role)
        
        payload = {
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role,
            'scope': scope,
            'exp': datetime.utcnow() + timedelta(hours=self.config['token_expiry_hours']),
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(16)  # JWT ID
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        
        # Store active token
        auth_token = AuthToken(
            token=token,
            user_id=user.user_id,
            expires_at=datetime.utcnow() + timedelta(hours=self.config['token_expiry_hours']),
            scope=scope,
            issued_at=datetime.utcnow()
        )
        self.active_tokens[token] = auth_token
        
        self.logger.info(f"🎫 Generated JWT token for user: {user.username}")
        return token
    
    def validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token"""
        try:
            # Check if token is still active
            if token not in self.active_tokens:
                return None
            
            auth_token = self.active_tokens[token]
            
            # Check expiration
            if datetime.utcnow() > auth_token.expires_at:
                del self.active_tokens[token]
                return None
            
            # Decode and validate token
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Verify user still exists and is active
            user = self.users.get(payload['user_id'])
            if not user or not user.is_active:
                del self.active_tokens[token]
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            if token in self.active_tokens:
                del self.active_tokens[token]
            return None
        except jwt.InvalidTokenError:
            return None
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a JWT token"""
        if token in self.active_tokens:
            del self.active_tokens[token]
            self.logger.info("🎫 Token revoked")
            return True
        return False
    
    def _get_role_scopes(self, role: str) -> List[str]:
        """Get scopes/permissions for a role"""
        role_scopes = {
            'admin': ['generate', 'read', 'admin', 'delete'],
            'user': ['generate', 'read'],
            'guest': ['read']
        }
        return role_scopes.get(role, [])
    
    def check_permission(self, user: User, required_scope: str) -> bool:
        """Check if user has required permission"""
        user_scopes = self._get_role_scopes(user.role)
        return required_scope in user_scopes
    
    def check_rate_limit(self, user: User) -> Tuple[bool, int]:
        """Check if user has exceeded rate limit"""
        now = time.time()
        window_start = now - 3600  # 1 hour window
        
        if user.user_id not in self.request_history:
            self.request_history[user.user_id] = []
        
        # Clean old requests
        self.request_history[user.user_id] = [
            req_time for req_time in self.request_history[user.user_id]
            if req_time > window_start
        ]
        
        # Check limit
        limit = self.rate_limits.get(user.role, 10)
        current_requests = len(self.request_history[user.user_id])
        
        if current_requests >= limit:
            return False, limit - current_requests
        
        # Add current request
        self.request_history[user.user_id].append(now)
        return True, limit - current_requests - 1
    
    def get_user_info(self, user_id: str) -> Optional[User]:
        """Get user information"""
        return self.users.get(user_id)
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users (admin only)"""
        return [
            {
                'user_id': user.user_id,
                'username': user.username,
                'role': user.role,
                'created_at': user.created_at,
                'last_login': user.last_login,
                'is_active': user.is_active
            }
            for user in self.users.values()
        ]

# FastAPI Authentication Middleware
class FastAPIAuthMiddleware:
    """Authentication middleware for FastAPI"""
    
    def __init__(self, auth_manager: AuthenticationManager):
        self.auth_manager = auth_manager
    
    async def __call__(self, request, call_next):
        """Process authentication for each request"""
        # Skip authentication for certain endpoints
        skip_paths = ['/docs', '/redoc', '/openapi.json', '/health']
        if request.url.path in skip_paths:
            return await call_next(request)
        
        # Extract API key or JWT token
        api_key = request.headers.get('X-API-Key')
        auth_header = request.headers.get('Authorization')
        
        user = None
        
        # Try API key authentication
        if api_key:
            user = self.auth_manager.authenticate_api_key(api_key)
            if user:
                request.state.user = user
                request.state.auth_method = 'api_key'
        
        # Try JWT authentication
        elif auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = self.auth_manager.validate_jwt_token(token)
            if payload:
                user = self.auth_manager.get_user_info(payload['user_id'])
                if user:
                    request.state.user = user
                    request.state.auth_method = 'jwt'
                    request.state.token_payload = payload
        
        # Check rate limiting
        if user:
            allowed, remaining = self.auth_manager.check_rate_limit(user)
            request.state.rate_limit_allowed = allowed
            request.state.rate_limit_remaining = remaining
            
            if not allowed:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. {remaining} requests remaining."
                )
        
        response = await call_next(request)
        return response

# Decorators for route protection
def require_auth(scope: str = None):
    """Decorator to require authentication"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would be implemented in the FastAPI route
            # For now, it's a placeholder
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(required_role: str):
    """Decorator to require specific role"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Implementation would check user role
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Example usage and testing
def main():
    """Demo authentication system"""
    print("🔐 AUTHENTICATION SYSTEM DEMO")
    print("=" * 35)
    
    # Initialize auth manager
    auth_manager = AuthenticationManager()
    
    try:
        # Create test users
        print("👤 Creating test users...")
        
        admin_user = auth_manager.create_user("admin_user", "admin")
        regular_user = auth_manager.create_user("regular_user", "user")
        guest_user = auth_manager.create_user("guest_user", "guest")
        
        print(f"Admin API Key: {admin_user.api_key}")
        print(f"User API Key: {regular_user.api_key}")
        print(f"Guest API Key: {guest_user.api_key}")
        
        # Test API key authentication
        print("\n🔍 Testing API key authentication...")
        
        authenticated_user = auth_manager.authenticate_api_key(regular_user.api_key)
        if authenticated_user:
            print(f"✅ Authenticated user: {authenticated_user.username}")
        else:
            print("❌ Authentication failed")
        
        # Test JWT token generation
        print("\n🎫 Testing JWT token generation...")
        
        if authenticated_user:
            token = auth_manager.generate_jwt_token(authenticated_user)
            print(f"Generated JWT token: {token[:50]}...")
            
            # Test token validation
            payload = auth_manager.validate_jwt_token(token)
            if payload:
                print(f"✅ Token validated for user: {payload['username']}")
            else:
                print("❌ Token validation failed")
        
        # Test permissions
        print("\n🛡️  Testing permissions...")
        
        if authenticated_user:
            can_generate = auth_manager.check_permission(authenticated_user, 'generate')
            can_admin = auth_manager.check_permission(authenticated_user, 'admin')
            print(f"User can generate: {can_generate}")
            print(f"User can admin: {can_admin}")
        
        # Test rate limiting
        print("\n⏱️  Testing rate limiting...")
        
        if authenticated_user:
            for i in range(5):
                allowed, remaining = auth_manager.check_rate_limit(authenticated_user)
                print(f"Request {i+1}: Allowed={allowed}, Remaining={remaining}")
        
        # List users (admin function)
        print("\n📋 User list:")
        users = auth_manager.list_users()
        for user in users:
            print(f"  - {user['username']} ({user['role']})")
        
        print("\n✅ Authentication system demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)