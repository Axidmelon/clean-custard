import os
import secrets
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SECRET_KEY environment variable is required and must be set to a secure random string"
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)  # Increased to 60 minutes
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Create a JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    """
    Create a JWT refresh token with longer expiration.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access"):
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")

    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Verify token type
        if payload.get("type") != token_type:
            return None

        return payload
    except JWTError:
        return None


def get_current_user():
    """
    FastAPI dependency to get the current authenticated user with Redis caching.
    
    This function implements intelligent caching to reduce database load:
    1. Check Redis cache for user data first
    2. If cache miss, fetch from database and cache the result
    3. Graceful fallback to database-only mode if Redis is unavailable
    
    Returns:
        User data from token payload
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    from fastapi import HTTPException, Depends
    from fastapi.security import HTTPBearer
    from services import user_services as user_service
    from db.dependencies import get_db
    from sqlalchemy.orm import Session
    from core.redis_service import redis_service
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Create OAuth2 scheme
    oauth2_scheme = HTTPBearer()
    
    def _get_current_user(
        credentials = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
    ):
        try:
            # Extract token from credentials
            token = credentials.credentials
            
            # Check if token is blacklisted
            if redis_service.is_token_blacklisted(token):
                logger.warning("Attempted to use blacklisted token")
                raise HTTPException(status_code=401, detail="Token has been revoked")
            
            # Verify the token
            payload = verify_token(token, "access")
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Get user ID from token
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token payload")
            
            # Try to get user from Redis cache first
            cached_user_data = redis_service.get_cached_user_data(user_id)
            
            if cached_user_data:
                logger.debug(f"User {user_id} retrieved from Redis cache")
                # Convert cached data back to User object-like structure
                from db.models import User
                user = User()
                for key, value in cached_user_data.items():
                    if key != '_cached_at':  # Skip cache metadata
                        setattr(user, key, value)
                return user
            
            # Cache miss - fetch from database
            logger.debug(f"Cache miss for user {user_id}, fetching from database")
            user = user_service.get_user_by_id(db, user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Cache the user data for future requests
            user_data = {
                'id': str(user.id),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_verified': user.is_verified,
                'organization_id': str(user.organization_id),
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }
            
            # Cache with 1 hour TTL (3600 seconds)
            redis_service.cache_user_data(user_id, user_data, ttl=3600)
            logger.debug(f"Cached user data for user {user_id}")
            
            return user
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=401, detail="Token validation failed")
    
    return _get_current_user


def create_persistent_session(user_id: str, user_data: dict) -> str:
    """
    Create a persistent session for a user.
    
    Args:
        user_id: User identifier
        user_data: User data dictionary
        
    Returns:
        Session ID if created successfully, empty string otherwise
    """
    from core.redis_service import redis_service
    
    session_data = {
        'user_data': user_data,
        'login_time': datetime.now(timezone.utc).isoformat(),
        'last_activity': datetime.now(timezone.utc).isoformat()
    }
    
    # Create session with 7-day TTL (604800 seconds)
    session_id = redis_service.create_user_session(user_id, session_data, ttl=604800)
    
    if session_id:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Created persistent session {session_id} for user {user_id}")
    
    return session_id


def validate_persistent_session(session_id: str) -> dict:
    """
    Validate a persistent session and return user data.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session data dictionary if valid, None otherwise
    """
    from core.redis_service import redis_service
    
    session_data = redis_service.get_user_session(session_id)
    
    if session_data:
        # Update last activity
        session_data['last_activity'] = datetime.now(timezone.utc).isoformat()
        redis_service.cache_user_data(
            session_data['user_id'], 
            session_data, 
            ttl=604800  # 7 days
        )
        
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Validated persistent session {session_id}")
    
    return session_data


def revoke_user_sessions(user_id: str) -> bool:
    """
    Revoke all sessions for a user (logout from all devices).
    
    Args:
        user_id: User identifier
        
    Returns:
        True if sessions revoked successfully, False otherwise
    """
    from core.redis_service import redis_service
    
    success = redis_service.invalidate_all_user_sessions(user_id)
    
    if success:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Revoked all sessions for user {user_id}")
    
    return success


def blacklist_token(token: str) -> bool:
    """
    Blacklist a JWT token (for logout).
    
    Args:
        token: JWT token to blacklist
        
    Returns:
        True if blacklisted successfully, False otherwise
    """
    from core.redis_service import redis_service
    
    # Get token expiration time to set appropriate TTL
    payload = verify_token(token, "access")
    if payload and 'exp' in payload:
        # Calculate TTL based on token expiration
        exp_timestamp = payload['exp']
        current_timestamp = datetime.now(timezone.utc).timestamp()
        ttl = max(int(exp_timestamp - current_timestamp), 3600)  # At least 1 hour
    else:
        ttl = 86400  # Default 24 hours
    
    success = redis_service.blacklist_token(token, ttl=ttl)
    
    if success:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Token blacklisted successfully")
    
    return success


def generate_secure_secret():
    """
    Generate a secure random secret key for JWT signing.
    Use this to generate a new SECRET_KEY for production.
    """
    return secrets.token_urlsafe(32)
