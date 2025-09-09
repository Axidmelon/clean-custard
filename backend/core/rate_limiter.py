# File: backend/core/rate_limiter.py

import time
import logging
from typing import Optional
from fastapi import Request, HTTPException
from core.config import settings

# Import RedisError at module level for exception handling
try:
    from redis.exceptions import RedisError
except ImportError:
    RedisError = Exception

logger = logging.getLogger(__name__)

# Rate limiting configuration
RATE_LIMITS = {
    "auth": {"requests": 10, "window": 60},  # 10 requests per minute
    "api": {"requests": 100, "window": 60},  # 100 requests per minute
    "query": {"requests": 20, "window": 60}, # 20 queries per minute
}

# In-memory rate limiting store (fallback when Redis is not available)
_rate_limit_store = {}

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check for forwarded headers first (for reverse proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"

def check_rate_limit_memory(client_ip: str, endpoint: str) -> bool:
    """
    Check rate limit using in-memory storage (fallback method).
    
    Args:
        client_ip: Client IP address
        endpoint: Endpoint identifier (auth, api, query)
        
    Returns:
        True if request is allowed, False if rate limited
    """
    if endpoint not in RATE_LIMITS:
        return True
    
    limit_config = RATE_LIMITS[endpoint]
    current_time = time.time()
    window_start = current_time - limit_config["window"]
    
    # Clean up old entries
    if client_ip in _rate_limit_store:
        _rate_limit_store[client_ip] = [
            timestamp for timestamp in _rate_limit_store[client_ip]
            if timestamp > window_start
        ]
    else:
        _rate_limit_store[client_ip] = []
    
    # Check if under limit
    if len(_rate_limit_store[client_ip]) >= limit_config["requests"]:
        return False
    
    # Add current request
    _rate_limit_store[client_ip].append(current_time)
    return True

def check_rate_limit_redis(client_ip: str, endpoint: str) -> bool:
    """
    Check rate limit using Redis (preferred method).
    
    Args:
        client_ip: Client IP address
        endpoint: Endpoint identifier (auth, api, query)
        
    Returns:
        True if request is allowed, False if rate limited
    """
    try:
        import redis
        
        # Connect to Redis
        redis_client = redis.from_url(settings.rate_limit_redis_url)
        
        if endpoint not in RATE_LIMITS:
            return True
        
        limit_config = RATE_LIMITS[endpoint]
        current_time = int(time.time())
        window_start = current_time - limit_config["window"]
        
        # Create Redis key for this client and endpoint
        redis_key = f"rate_limit:{endpoint}:{client_ip}"
        
        # Use Redis pipeline for atomic operations
        pipe = redis_client.pipeline()
        
        # Remove old entries (older than window)
        pipe.zremrangebyscore(redis_key, 0, window_start)
        
        # Count current requests in window
        pipe.zcard(redis_key)
        
        # Add current request
        pipe.zadd(redis_key, {str(current_time): current_time})
        
        # Set expiration
        pipe.expire(redis_key, limit_config["window"])
        
        # Execute pipeline
        results = pipe.execute()
        current_count = results[1]
        
        # Check if under limit
        if current_count >= limit_config["requests"]:
            return False
        
        return True
        
    except (ImportError, RedisError, Exception) as e:
        logger.warning(f"Redis rate limiting failed, falling back to memory: {e}")
        return check_rate_limit_memory(client_ip, endpoint)

def check_rate_limit(request: Request, endpoint: str) -> None:
    """
    Check if request is within rate limits.
    
    Args:
        request: FastAPI request object
        endpoint: Endpoint identifier (auth, api, query)
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    # Skip rate limiting if disabled
    if not settings.rate_limit_enabled:
        return
    
    # Get client IP
    client_ip = get_client_ip(request)
    
    # Check rate limit
    if settings.rate_limit_redis_url:
        allowed = check_rate_limit_redis(client_ip, endpoint)
    else:
        allowed = check_rate_limit_memory(client_ip, endpoint)
    
    if not allowed:
        limit_config = RATE_LIMITS.get(endpoint, {"requests": 10, "window": 60})
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {limit_config['requests']} requests per {limit_config['window']} seconds",
                "retry_after": limit_config["window"]
            }
        )

def get_rate_limit_info(client_ip: str, endpoint: str) -> dict:
    """
    Get current rate limit information for a client.
    
    Args:
        client_ip: Client IP address
        endpoint: Endpoint identifier
        
    Returns:
        Dictionary with rate limit information
    """
    if endpoint not in RATE_LIMITS:
        return {"limit": 0, "remaining": 0, "reset_time": 0}
    
    limit_config = RATE_LIMITS[endpoint]
    
    if settings.rate_limit_redis_url:
        try:
            import redis
            redis_client = redis.from_url(settings.rate_limit_redis_url)
            redis_key = f"rate_limit:{endpoint}:{client_ip}"
            current_count = redis_client.zcard(redis_key)
        except Exception:
            current_count = len(_rate_limit_store.get(client_ip, []))
    else:
        current_count = len(_rate_limit_store.get(client_ip, []))
    
    remaining = max(0, limit_config["requests"] - current_count)
    reset_time = int(time.time()) + limit_config["window"]
    
    return {
        "limit": limit_config["requests"],
        "remaining": remaining,
        "reset_time": reset_time,
        "window": limit_config["window"]
    }
