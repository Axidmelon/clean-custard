# File: backend/core/redis_service.py

import json
import logging
import os
import redis
import time
from typing import Optional, Dict, Any, Union, List
from datetime import datetime, timedelta, timezone
from core.config import settings
from functools import wraps

logger = logging.getLogger(__name__)


def redis_retry(max_retries=3, delay=0.1):
    """
    Decorator to retry Redis operations with exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (redis.ConnectionError, redis.TimeoutError, redis.RedisError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        logger.warning(f"Redis operation failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Redis operation failed after {max_retries} attempts: {e}")
            
            # If all retries failed, raise the last exception
            raise last_exception
        return wrapper
    return decorator


class RedisService:
    """
    Redis service for caching authentication data and user sessions.
    
    This service provides:
    - User data caching to reduce database load
    - Session management for persistent logins
    - Token blacklisting for security
    - Cache invalidation strategies
    - Graceful fallback when Redis is unavailable
    """
    
    def __init__(self):
        self.redis_client = None
        self.redis_binary_client = None  # Separate client for binary data
        self.is_available = False
        self._connect()
    
    def _connect(self):
        """Establish connection to Redis with fallback handling."""
        try:
            # Use Redis URL from environment or default to localhost
            redis_url = os.getenv('REDIS_URL') or getattr(settings, 'redis_url', 'redis://localhost:6379/0')
            
            # Use redis.from_url() for proper URL parsing (handles auth, cloud URLs, etc.)
            redis_config = {
                'decode_responses': True,
                'socket_timeout': 10.0,  # Increased timeout for stability
                'socket_connect_timeout': 5.0,  # Increased connection timeout
                'retry_on_timeout': True,  # Enable retry on timeout for reliability
                'health_check_interval': 30,  # More frequent health checks
                'max_connections': 20,  # Reasonable connection pool size
                'socket_keepalive': True,  # Keep connections alive
            }
            
            self.redis_client = redis.from_url(redis_url, **redis_config)
            
            # Create separate Redis client for binary data (CSV caching)
            binary_redis_config = {
                'decode_responses': False,  # Keep binary data as bytes
                'socket_timeout': 15.0,  # Longer timeout for binary data operations
                'socket_connect_timeout': 5.0,  # Increased connection timeout
                'retry_on_timeout': True,  # Enable retry on timeout for reliability
                'health_check_interval': 30,  # More frequent health checks
                'max_connections': 20,  # Reasonable connection pool size
                'socket_keepalive': True,  # Keep connections alive
            }
            
            self.redis_binary_client = redis.from_url(redis_url, **binary_redis_config)
            
            # Test connection with timeout
            self.redis_client.ping()
            self.redis_binary_client.ping()
            self.is_available = True
            
            # Warm up connection pool
            self._warmup_connections()
            
            logger.info(f"🚀 Redis connected successfully using URL: {redis_url} (ultra-fast config)")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Falling back to database-only mode.")
            self.is_available = False
            self.redis_client = None
            self.redis_binary_client = None
    
    def _warmup_connections(self):
        """Warm up Redis connection pool for faster operations."""
        try:
            # Pre-create connections in the pool
            for _ in range(5):
                self.redis_client.ping()
                self.redis_binary_client.ping()
            logger.info("🔥 Redis connection pool warmed up")
        except Exception as e:
            logger.warning(f"Redis warmup failed: {e}")
    
    def _ensure_connection(self):
        """Ensure Redis connection is active, reconnect if needed."""
        if not self.is_available:
            self._connect()
        elif self.redis_client and self.redis_binary_client:
            try:
                # Test connection with timeout
                self.redis_client.ping()
                self.redis_binary_client.ping()
            except (redis.ConnectionError, redis.TimeoutError, redis.RedisError) as e:
                logger.warning(f"Redis connection lost: {e}, attempting to reconnect...")
                self._connect()
            except Exception as e:
                logger.warning(f"Unexpected Redis error: {e}, attempting to reconnect...")
                self._connect()
    
    def _serialize_data(self, data: Any) -> str:
        """Serialize data for Redis storage."""
        if isinstance(data, dict):
            # Add timestamp for cache invalidation
            data['_cached_at'] = datetime.now(timezone.utc).isoformat()
        return json.dumps(data, default=str)
    
    def _deserialize_data(self, data: str) -> Any:
        """Deserialize data from Redis storage."""
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return None
    
    # User Data Caching Methods
    
    def cache_user_data(self, user_id: str, user_data: Dict[str, Any], ttl: int = 3600) -> bool:
        """
        Cache user data in Redis.
        
        Args:
            user_id: User identifier
            user_data: User data dictionary
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            self._ensure_connection()
            key = f"user:{user_id}"
            serialized_data = self._serialize_data(user_data)
            
            # Set with expiration
            result = self.redis_client.setex(key, ttl, serialized_data)
            logger.debug(f"Cached user data for user {user_id}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to cache user data for {user_id}: {e}")
            return False
    
    def get_cached_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached user data from Redis.
        
        Args:
            user_id: User identifier
            
        Returns:
            User data dictionary if found, None otherwise
        """
        if not self.is_available:
            return None
        
        try:
            self._ensure_connection()
            key = f"user:{user_id}"
            data = self.redis_client.get(key)
            
            if data:
                user_data = self._deserialize_data(data)
                logger.debug(f"Retrieved cached user data for user {user_id}")
                return user_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached user data for {user_id}: {e}")
            return None
    
    def invalidate_user_cache(self, user_id: str) -> bool:
        """
        Invalidate cached user data.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            self._ensure_connection()
            key = f"user:{user_id}"
            result = self.redis_client.delete(key)
            logger.debug(f"Invalidated user cache for user {user_id}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to invalidate user cache for {user_id}: {e}")
            return False
    
    # Session Management Methods
    
    def create_user_session(self, user_id: str, session_data: Dict[str, Any], ttl: int = 86400) -> str:
        """
        Create a persistent user session.
        
        Args:
            user_id: User identifier
            session_data: Session data dictionary
            ttl: Session time to live in seconds (default: 24 hours)
            
        Returns:
            Session ID if created successfully, empty string otherwise
        """
        if not self.is_available:
            return ""
        
        try:
            self._ensure_connection()
            import uuid
            session_id = str(uuid.uuid4())
            
            # Store session data
            session_key = f"session:{session_id}"
            session_data['user_id'] = user_id
            session_data['created_at'] = datetime.now(timezone.utc).isoformat()
            
            serialized_data = self._serialize_data(session_data)
            self.redis_client.setex(session_key, ttl, serialized_data)
            
            # Store user's active sessions
            user_sessions_key = f"user_sessions:{user_id}"
            self.redis_client.sadd(user_sessions_key, session_id)
            self.redis_client.expire(user_sessions_key, ttl)
            
            logger.info(f"Created session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create session for user {user_id}: {e}")
            return ""
    
    def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dictionary if found, None otherwise
        """
        if not self.is_available:
            return None
        
        try:
            self._ensure_connection()
            session_key = f"session:{session_id}"
            data = self.redis_client.get(session_key)
            
            if data:
                session_data = self._deserialize_data(data)
                logger.debug(f"Retrieved session {session_id}")
                return session_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            return None
    
    def invalidate_user_session(self, session_id: str) -> bool:
        """
        Invalidate a user session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            self._ensure_connection()
            session_key = f"session:{session_id}"
            
            # Get session data to find user_id
            session_data = self.get_user_session(session_id)
            if session_data:
                user_id = session_data.get('user_id')
                if user_id:
                    # Remove from user's active sessions
                    user_sessions_key = f"user_sessions:{user_id}"
                    self.redis_client.srem(user_sessions_key, session_id)
            
            # Delete session
            result = self.redis_client.delete(session_key)
            logger.info(f"Invalidated session {session_id}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to invalidate session {session_id}: {e}")
            return False
    
    def invalidate_all_user_sessions(self, user_id: str) -> bool:
        """
        Invalidate all sessions for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            self._ensure_connection()
            user_sessions_key = f"user_sessions:{user_id}"
            session_ids = self.redis_client.smembers(user_sessions_key)
            
            # Delete all sessions
            for session_id in session_ids:
                session_key = f"session:{session_id}"
                self.redis_client.delete(session_key)
            
            # Clear user sessions set
            self.redis_client.delete(user_sessions_key)
            
            logger.info(f"Invalidated all sessions for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invalidate all sessions for user {user_id}: {e}")
            return False
    
    # Token Blacklisting Methods
    
    def blacklist_token(self, token: str, ttl: int = 86400) -> bool:
        """
        Add a token to the blacklist.
        
        Args:
            token: JWT token to blacklist
            ttl: Time to live in seconds (default: 24 hours)
            
        Returns:
            True if blacklisted successfully, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            self._ensure_connection()
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            key = f"blacklist:{token_hash}"
            
            result = self.redis_client.setex(key, ttl, "blacklisted")
            logger.debug(f"Blacklisted token {token_hash[:8]}...")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
            return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if a token is blacklisted.
        
        Args:
            token: JWT token to check
            
        Returns:
            True if token is blacklisted, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            self._ensure_connection()
            import hashlib
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            key = f"blacklist:{token_hash}"
            
            result = self.redis_client.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to check token blacklist: {e}")
            return False
    
    # Cache Statistics and Health
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get Redis cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.is_available:
            return {"status": "unavailable", "error": "Redis not connected"}
        
        try:
            self._ensure_connection()
            info = self.redis_client.info()
            
            return {
                "status": "available",
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def health_check(self) -> bool:
        """
        Perform Redis health check.
        
        Returns:
            True if Redis is healthy, False otherwise
        """
        try:
            self._ensure_connection()
            if self.redis_client:
                self.redis_client.ping()
                return True
            return False
        except Exception:
            return False
    
    # CSV Data Caching Methods
    
    @redis_retry(max_retries=3, delay=0.2)
    def cache_csv_data(self, user_id: str, file_id: str, csv_content: str, ttl: int = 7200) -> bool:
        """
        Cache CSV file content in Redis for processing.
        
        Args:
            user_id: User identifier
            file_id: File identifier
            csv_content: Raw CSV content as string
            ttl: Time to live in seconds (default: 2 hours)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            self._ensure_connection()
            key = f"csv_data:{user_id}:{file_id}"
            
            # Validate input data
            if not csv_content:
                logger.error(f"Empty CSV content for user {user_id}, file {file_id}")
                return False
            
            # Ensure content is string
            if isinstance(csv_content, bytes):
                csv_content = csv_content.decode('utf-8')
            elif not isinstance(csv_content, str):
                logger.error(f"Invalid CSV content type {type(csv_content)} for user {user_id}, file {file_id}")
                return False
            
            # Check Redis availability before attempting operation
            if not self.is_available or not self.redis_binary_client:
                logger.warning(f"Redis not available for caching CSV data for user {user_id}, file {file_id}")
                return False
            
            # Compress CSV content to save memory
            import gzip
            try:
                compressed_content = gzip.compress(csv_content.encode('utf-8'))
                logger.debug(f"Compressed CSV data: {len(csv_content)} -> {len(compressed_content)} bytes")
            except Exception as compress_error:
                logger.error(f"Failed to compress CSV data for user {user_id}, file {file_id}: {compress_error}")
                return False
            
            # Store compressed binary data using binary client with timeout handling
            try:
                result = self.redis_binary_client.setex(key, ttl, compressed_content)
                
                if result:
                    logger.info(f"Cached CSV data for user {user_id}, file {file_id}, size: {len(csv_content)} bytes (compressed: {len(compressed_content)} bytes)")
                    return True
                else:
                    logger.warning(f"Failed to store CSV data in Redis for user {user_id}, file {file_id}")
                    return False
                    
            except redis.TimeoutError as timeout_error:
                logger.error(f"Redis timeout while caching CSV data for user {user_id}, file {file_id}: {timeout_error}")
                return False
            except redis.ConnectionError as conn_error:
                logger.error(f"Redis connection error while caching CSV data for user {user_id}, file {file_id}: {conn_error}")
                # Mark Redis as unavailable for future operations
                self.is_available = False
                return False
            
        except Exception as e:
            logger.error(f"Failed to cache CSV data for user {user_id}, file {file_id}: {e}")
            return False
    
    @redis_retry(max_retries=3, delay=0.2)
    def get_cached_csv_data(self, user_id: str, file_id: str) -> Optional[str]:
        """
        Retrieve cached CSV data from Redis.
        
        Args:
            user_id: User identifier
            file_id: File identifier
            
        Returns:
            CSV content as string if found, None otherwise
        """
        if not self.is_available:
            return None
        
        try:
            self._ensure_connection()
            key = f"csv_data:{user_id}:{file_id}"
            
            # Check Redis availability before attempting operation
            if not self.is_available or not self.redis_binary_client:
                logger.warning(f"Redis not available for retrieving CSV data for user {user_id}, file {file_id}")
                return None
            
            # Retrieve compressed binary data using binary client with timeout handling
            try:
                compressed_data = self.redis_binary_client.get(key)
                
                if compressed_data:
                    # Validate that we got binary data
                    if not isinstance(compressed_data, bytes):
                        logger.error(f"Expected binary data but got {type(compressed_data)} for user {user_id}, file {file_id}")
                        return None
                    
                    # Decompress the data
                    import gzip
                    try:
                        csv_content = gzip.decompress(compressed_data).decode('utf-8')
                        logger.debug(f"Retrieved cached CSV data for user {user_id}, file {file_id}, size: {len(csv_content)} bytes")
                        return csv_content
                    except gzip.BadGzipFile as gzip_error:
                        logger.error(f"Invalid gzip data for user {user_id}, file {file_id}: {gzip_error}")
                        # Invalidate corrupted cache entry
                        self.invalidate_csv_cache(user_id, file_id)
                        return None
                    except UnicodeDecodeError as decode_error:
                        logger.error(f"UTF-8 decode error for user {user_id}, file {file_id}: {decode_error}")
                        # Invalidate corrupted cache entry
                        self.invalidate_csv_cache(user_id, file_id)
                        return None
                
                logger.debug(f"No cached CSV data found for user {user_id}, file {file_id}")
                return None
                
            except redis.TimeoutError as timeout_error:
                logger.error(f"Redis timeout while retrieving CSV data for user {user_id}, file {file_id}: {timeout_error}")
                return None
            except redis.ConnectionError as conn_error:
                logger.error(f"Redis connection error while retrieving CSV data for user {user_id}, file {file_id}: {conn_error}")
                # Mark Redis as unavailable for future operations
                self.is_available = False
                return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached CSV data for user {user_id}, file {file_id}: {e}")
            return None
    
    def invalidate_csv_cache(self, user_id: str, file_id: str) -> bool:
        """
        Invalidate cached CSV data.
        
        Args:
            user_id: User identifier
            file_id: File identifier
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            self._ensure_connection()
            key = f"csv_data:{user_id}:{file_id}"
            
            if not self.redis_binary_client:
                logger.error("Redis binary client is not available")
                return False
            
            result = self.redis_binary_client.delete(key)
            logger.info(f"Invalidated CSV cache for user {user_id}, file {file_id}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to invalidate CSV cache for user {user_id}, file {file_id}: {e}")
            return False
    
    def get_csv_cache_stats(self) -> Dict[str, Any]:
        """
        Get CSV cache statistics.
        
        Returns:
            Dictionary with CSV cache statistics
        """
        if not self.is_available:
            return {"status": "unavailable", "error": "Redis not connected"}
        
        try:
            self._ensure_connection()
            
            if not self.redis_binary_client:
                return {"status": "error", "error": "Redis binary client not available"}
            
            # Count CSV cache keys using binary client
            csv_keys = self.redis_binary_client.keys("csv_data:*")
            total_csv_files = len(csv_keys)
            
            # Calculate total memory usage for CSV data
            total_size = 0
            for key in csv_keys:
                try:
                    size = self.redis_binary_client.memory_usage(key)
                    total_size += size
                except Exception:
                    continue
            
            return {
                "status": "available",
                "total_csv_files": total_csv_files,
                "total_memory_bytes": total_size,
                "total_memory_mb": round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    # Proactive Cache Refresh Methods
    
    def track_user_activity(self, user_id: str, file_id: str) -> bool:
        """
        Track user activity for proactive cache refresh.
        
        Args:
            user_id: User identifier
            file_id: File identifier
            
        Returns:
            True if tracked successfully, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            self._ensure_connection()
            
            if not self.redis_client:
                logger.error("Redis client is not available")
                return False
            
            activity_key = f"user_activity:{user_id}:{file_id}"
            current_time = int(time.time())
            
            # Store activity timestamp (expires in 1 hour)
            result = self.redis_client.setex(activity_key, 3600, current_time)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to track user activity for user {user_id}, file {file_id}: {e}")
            return False
    
    def get_user_activity(self, user_id: str, file_id: str) -> Optional[int]:
        """
        Get user's last activity timestamp.
        
        Args:
            user_id: User identifier
            file_id: File identifier
            
        Returns:
            Unix timestamp of last activity, or None if not found
        """
        if not self.is_available:
            return None
        
        try:
            self._ensure_connection()
            
            if not self.redis_client:
                logger.error("Redis client is not available")
                return None
            
            activity_key = f"user_activity:{user_id}:{file_id}"
            activity_time = self.redis_client.get(activity_key)
            
            if activity_time:
                return int(activity_time)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user activity for user {user_id}, file {file_id}: {e}")
            return None
    
    def get_expiring_caches(self, minutes_before_expiry: int = 5) -> List[Dict[str, Any]]:
        """
        Get CSV caches that are expiring soon and need proactive refresh.
        
        Args:
            minutes_before_expiry: How many minutes before expiry to consider
            
        Returns:
            List of cache information for expiring caches
        """
        if not self.is_available:
            return []
        
        try:
            self._ensure_connection()
            
            if not self.redis_client:
                logger.error("Redis client is not available")
                return []
            
            import time
            
            if not self.redis_binary_client:
                logger.error("Redis binary client is not available")
                return []
            
            expiring_caches = []
            csv_keys = self.redis_binary_client.keys("csv_data:*")
            current_time = int(time.time())
            expiry_threshold = minutes_before_expiry * 60  # Convert to seconds
            
            for key in csv_keys:
                try:
                    # Get TTL for this key
                    ttl = self.redis_binary_client.ttl(key)
                    
                    # TTL returns -1 if key exists but has no expiry, -2 if key doesn't exist
                    # We only want keys with positive TTL (expiring keys)
                    if isinstance(ttl, int) and ttl > 0 and ttl <= expiry_threshold:
                        # Parse key to extract user_id and file_id
                        key_parts = key.split(":")
                        if len(key_parts) >= 3:
                            user_id = key_parts[1]
                            file_id = key_parts[2]
                            
                            # Check if user has recent activity (within last 30 minutes)
                            activity_time = self.get_user_activity(user_id, file_id)
                            if activity_time and (current_time - activity_time) <= 1800:  # 30 minutes
                                expiring_caches.append({
                                    "key": key,
                                    "user_id": user_id,
                                    "file_id": file_id,
                                    "ttl": ttl,
                                    "expires_in_minutes": ttl // 60,
                                    "last_activity_minutes_ago": (current_time - activity_time) // 60
                                })
                                
                except Exception as e:
                    logger.warning(f"Error processing cache key {key}: {e}")
                    continue
            
            return expiring_caches
            
        except Exception as e:
            logger.error(f"Failed to get expiring caches: {e}")
            return []
    
    def refresh_expiring_cache(self, user_id: str, file_id: str) -> bool:
        """
        Proactively refresh an expiring cache by extending its TTL.
        
        Args:
            user_id: User identifier
            file_id: File identifier
            
        Returns:
            True if refreshed successfully, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            self._ensure_connection()
            
            if not self.redis_binary_client:
                logger.error("Redis binary client is not available")
                return False
            
            key = f"csv_data:{user_id}:{file_id}"
            
            # Check if cache exists
            if not self.redis_binary_client.exists(key):
                logger.warning(f"Cache key {key} does not exist for refresh")
                return False
            
            # Extend TTL by 2 hours (7200 seconds)
            result = self.redis_binary_client.expire(key, 7200)
            
            if result:
                logger.info(f"Successfully refreshed cache for user {user_id}, file {file_id}")
                return True
            else:
                logger.warning(f"Failed to refresh cache for user {user_id}, file {file_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to refresh cache for user {user_id}, file {file_id}: {e}")
            return False

    # Generic Caching Methods (for signed URLs and other data)
    
    def cache_data(self, key: str, data: Any, ttl: int = 3600) -> bool:
        """
        Cache arbitrary data in Redis with a custom key.
        
        Args:
            key: Custom cache key
            data: Data to cache (will be serialized)
            ttl: Time to live in seconds (default: 1 hour)
            
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            # Skip _ensure_connection() for speed - assume connection is good
            serialized_data = self._serialize_data(data)
            
            # Use pipeline for faster operations
            pipe = self.redis_client.pipeline()
            pipe.setex(key, ttl, serialized_data)
            results = pipe.execute()
            result = results[0]
            
            logger.debug(f"🚀 FAST Redis cache write: {key}, TTL: {ttl}s")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to cache data with key {key}: {e}")
            return False
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """
        Retrieve arbitrary cached data from Redis with ultra-fast optimization.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data if found, None otherwise
        """
        if not self.is_available:
            return None
        
        try:
            # Skip _ensure_connection() for speed - assume connection is good
            import time
            start_time = time.time()
            
            # Use pipeline for faster operations
            pipe = self.redis_client.pipeline()
            pipe.get(key)
            results = pipe.execute()
            cached_data = results[0]
            
            end_time = time.time()
            
            if cached_data:
                deserialized_data = self._deserialize_data(cached_data)
                logger.info(f"🚀 FAST Redis lookup: {key} ({(end_time - start_time)*1000:.1f}ms)")
                return deserialized_data
            
            logger.debug(f"No cached data found for key: {key} (Redis lookup: {(end_time - start_time)*1000:.1f}ms)")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached data with key {key}: {e}")
            return None
    
    def invalidate_cached_data(self, key: str) -> bool:
        """
        Invalidate cached data by key.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if invalidated successfully, False otherwise
        """
        if not self.is_available:
            return False
        
        try:
            self._ensure_connection()
            result = self.redis_client.delete(key)
            logger.debug(f"Invalidated cached data with key: {key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to invalidate cached data with key {key}: {e}")
            return False


# Global Redis service instance
redis_service = RedisService()
