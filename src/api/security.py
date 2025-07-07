"""
Urbanclear - Enhanced Security Module
"""

import os
import jwt
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps
from fastapi import HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel
from enum import Enum
from loguru import logger


class UserRole(str, Enum):
    """User roles for RBAC"""

    ADMIN = "admin"
    TRAFFIC_MANAGER = "traffic_manager"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_USER = "api_user"


class SecurityConfig:
    """Security configuration"""

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    API_KEY_PREFIX = "uk_"
    RATE_LIMIT_WINDOW = 60
    RATE_LIMIT_MAX_REQUESTS = 100
    SESSION_TIMEOUT_HOURS = 8

    # Password policy
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SYMBOLS = True


class User(BaseModel):
    """User model"""

    id: str
    username: str
    email: str
    role: UserRole
    permissions: List[str]
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None


class TokenData(BaseModel):
    """Token payload data"""

    user_id: str
    username: str
    role: str
    exp: int
    iat: int
    jti: str  # JWT ID for token revocation


class SecurityManager:
    """Enhanced security manager"""

    def __init__(self, redis_client=None):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.redis_client = redis_client
        self.security_config = SecurityConfig()

    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role,
            "permissions": user.permissions,
            "exp": datetime.utcnow()
            + timedelta(hours=self.security_config.JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow(),
            "jti": hashlib.sha256(
                f"{user.id}:{datetime.utcnow()}".encode()
            ).hexdigest()[:16],
        }

        token = jwt.encode(
            payload,
            self.security_config.JWT_SECRET_KEY,
            algorithm=self.security_config.JWT_ALGORITHM,
        )

        # Store token in Redis for revocation capability
        if self.redis_client:
            self.redis_client.setex(
                f"token:{payload['jti']}",
                timedelta(hours=self.security_config.JWT_EXPIRATION_HOURS),
                user.id,
            )

        return token

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                self.security_config.JWT_SECRET_KEY,
                algorithms=[self.security_config.JWT_ALGORITHM],
            )

            # Check if token is revoked
            if self.redis_client and not self.redis_client.exists(
                f"token:{payload['jti']}"
            ):
                return None

            return TokenData(**payload)
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

    def revoke_token(self, jti: str) -> bool:
        """Revoke a token"""
        if self.redis_client:
            return self.redis_client.delete(f"token:{jti}")
        return False

    def generate_api_key(self, user_id: str, description: str = "") -> str:
        """Generate API key for user"""
        key_data = f"{user_id}:{datetime.utcnow().isoformat()}:{description}"
        api_key = (
            self.security_config.API_KEY_PREFIX
            + hashlib.sha256(key_data.encode()).hexdigest()
        )

        # Store API key mapping in Redis
        if self.redis_client:
            self.redis_client.setex(
                f"api_key:{api_key}",
                timedelta(days=365),  # API keys expire after 1 year
                user_id,
            )

        return api_key

    def verify_api_key(self, api_key: str) -> Optional[str]:
        """Verify API key and return user ID"""
        if not api_key.startswith(self.security_config.API_KEY_PREFIX):
            return None

        if self.redis_client:
            user_id = self.redis_client.get(f"api_key:{api_key}")
            return user_id

        return None

    def check_rate_limit(self, user_id: str, endpoint: str) -> bool:
        """Check rate limit for user and endpoint"""
        if not self.redis_client:
            return True

        key = f"rate_limit:{user_id}:{endpoint}"
        current = self.redis_client.get(key)

        if current is None:
            self.redis_client.setex(key, self.security_config.RATE_LIMIT_WINDOW, 1)
            return True

        if int(current) >= self.security_config.RATE_LIMIT_MAX_REQUESTS:
            return False

        self.redis_client.incr(key)
        return True

    def log_security_event(
        self, event_type: str, user_id: str, details: Dict[str, Any]
    ):
        """Log security-related events"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
        }

        # Store in Redis for short-term analysis
        if self.redis_client:
            self.redis_client.lpush("security_events", str(event))
            self.redis_client.ltrim("security_events", 0, 10000)  # Keep last 10k events

        logger.info(f"Security event: {event_type} for user {user_id}")


# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: ["read:all", "write:all", "delete:all", "admin:all"],
    UserRole.TRAFFIC_MANAGER: [
        "read:traffic",
        "write:traffic",
        "read:signals",
        "write:signals",
        "read:incidents",
        "write:incidents",
        "read:analytics",
    ],
    UserRole.ANALYST: [
        "read:traffic",
        "read:analytics",
        "read:predictions",
        "read:incidents",
    ],
    UserRole.VIEWER: ["read:traffic", "read:analytics"],
    UserRole.API_USER: ["read:traffic", "read:predictions", "read:routes"],
}


def require_permission(permission: str):
    """Decorator to require specific permission"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs (should be injected by FastAPI dependency)
            user = kwargs.get("current_user")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            user_permissions = user.get("permissions", [])
            if (
                permission not in user_permissions
                and "admin:all" not in user_permissions
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{permission}' required",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(role: UserRole):
    """Decorator to require specific role"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get("current_user")
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if (
                user.get("role") != role.value
                and user.get("role") != UserRole.ADMIN.value
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{role.value}' required",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
