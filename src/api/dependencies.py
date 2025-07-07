"""
FastAPI dependencies for the traffic system
"""

from typing import Optional
import redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from functools import lru_cache
from loguru import logger
from jose import jwt, JWTError

from src.core.config import get_settings as _get_settings

# Initialize security
security = HTTPBearer(auto_error=False)

# Global connections (will be initialized when first accessed)
_db_engine = None
_redis_client = None
_session_local = None


@lru_cache()
def get_app_settings():
    """Get application settings"""
    return _get_settings()


def get_database_engine():
    """Get or create database engine"""
    global _db_engine
    if _db_engine is None:
        settings = _get_settings()
        database_url = (
            f"postgresql://{settings.database.postgres.username}:"
            f"{settings.database.postgres.password}@"
            f"{settings.database.postgres.host}:"
            f"{settings.database.postgres.port}/"
            f"{settings.database.postgres.database}"
        )
        _db_engine = create_async_engine(
            database_url,
            pool_size=settings.database.postgres.pool_size,
            max_overflow=settings.database.postgres.max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _db_engine


def get_session_local():
    """Get or create session local"""
    global _session_local
    if _session_local is None:
        engine = get_database_engine()
        _session_local = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    return _session_local


async def get_db() -> AsyncSession:
    """
    Dependency to get database session
    """
    async with get_session_local()() as db:
        try:
            yield db
        except Exception as e:
            logger.error(f"Database error: {e}")
            await db.rollback()
            raise
        finally:
            await db.close()


def get_redis_client():
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        settings = _get_settings()
        _redis_client = redis.Redis(
            host=settings.database.redis.host,
            port=settings.database.redis.port,
            db=settings.database.redis.database,
            password=settings.database.redis.password,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    return _redis_client


def get_cache():
    """
    Dependency to get cache client
    """
    try:
        client = get_redis_client()
        # Test connection
        client.ping()
        yield client
    except redis.ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        # Return a mock cache that does nothing if Redis is unavailable
        yield MockCache()
    except Exception as e:
        logger.error(f"Cache error: {e}")
        yield MockCache()


class MockCache:
    """Mock cache for when Redis is unavailable"""

    def get(self, key: str) -> Optional[str]:
        return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        return True

    def delete(self, key: str) -> int:
        return 0

    def exists(self, key: str) -> bool:
        return False

    def keys(self, pattern: str = "*") -> list:
        return []


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[dict]:
    """
    Extract and validate user from JWT token
    """
    try:
        # Validate JWT token
        payload = jwt.decode(
            credentials.credentials, get_app_settings().SECRET_KEY, algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # For demo purposes, return a mock user
        return {
            "id": user_id,
            "username": f"user_{user_id}",
            "role": "admin",
            "permissions": ["read", "write", "admin"]
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_permission(permission: str):
    """
    Dependency factory to require specific permissions
    """

    def permission_dependency(
        user: dict = Depends(get_current_user),
    ) -> dict:
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )

        # Check if user has required permission
        user_permissions = user.get("permissions", [])
        if permission not in user_permissions and "admin" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )

        return user

    return permission_dependency


async def health_check_database(db: AsyncSession) -> bool:
    """
    Check database connectivity
    """
    try:
        await db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def get_database_health() -> dict:
    """Check database health"""
    try:
        engine = get_database_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
            return {
                "status": "healthy",
                "connection": "active",
                "response_time": "< 100ms",
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "connection": "failed", "error": str(e)}


def get_cache_health() -> dict:
    """Check cache health"""
    try:
        client = get_redis_client()
        client.ping()
        info = client.info()
        return {
            "status": "healthy",
            "connection": "active",
            "memory_used": info.get("used_memory_human", "unknown"),
            "uptime": info.get("uptime_in_seconds", 0),
        }
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {"status": "unhealthy", "connection": "failed", "error": str(e)}


async def get_system_health() -> dict:
    """Get overall system health"""
    return {
        "database": get_database_health(),
        "cache": get_cache_health(),
        "timestamp": "2024-01-01T12:00:00Z",  # This would be dynamic
        "overall_status": "healthy",  # This would be calculated based on components
    }


class RateLimiter:
    """Simple rate limiter using Redis"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client or get_redis_client()

    async def is_allowed(self, key: str, limit: int, window: int = 60) -> bool:
        """
        Check if request is allowed based on rate limit

        Args:
            key: Unique identifier for the client
            limit: Maximum number of requests allowed
            window: Time window in seconds
        """
        try:
            current = self.redis_client.get(key)
            if current is None:
                # First request
                self.redis_client.setex(key, window, 1)
                return True

            current_count = int(current)
            if current_count >= limit:
                return False

            # Increment counter
            self.redis_client.incr(key)
            return True

        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # If rate limiting fails, allow the request
            return True


def get_rate_limiter():
    """Dependency to get rate limiter"""
    return RateLimiter()


def create_rate_limit_dependency(limit: int, window: int = 60):
    """
    Create a rate limiting dependency

    Args:
        limit: Maximum requests allowed
        window: Time window in seconds
    """

    async def rate_limit_dependency(
        request,  # FastAPI request object
        rate_limiter: RateLimiter = Depends(get_rate_limiter),
    ):
        # Use client IP as the key (in production, consider using user ID)
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"

        if not await rate_limiter.is_allowed(key, limit, window):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {limit} requests per {window} seconds",
            )

    return rate_limit_dependency
