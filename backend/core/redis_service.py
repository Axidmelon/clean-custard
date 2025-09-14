# File: backend/core/redis_service.py

import json
import logging
import os
import redis
import time
from typing import Optional, Dict, Any, Union, List
from datetime import datetime, timedelta, timezone
from core.config import settings

logger = logging.getLogger(__name__)


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
        self.is_available = False
        self._connect()
    
    def _connect(self):
        """Establish connection to Redis with fallback handling."""
        try:
            # Use Redis URL from environment or default to localhost
            redis_url = os.getenv('REDIS_URL') or getattr(settings, 'redis_url', 'redis://localhost:6379/0')
            
            # Parse Redis URL for connection parameters
            if redis_url.startswith('redis://'):
                # Extract host, port, db from URL
                url_parts = redis_url.replace('redis://', '').split('/')
                host_port = url_parts[0].split(':')
                host = host_port[0] if host_port[0] else 'localhost'
                port = int(host_port[1]) if len(host_port) > 1 else 6379
                db = int(url_parts[1]) if len(url_parts) > 1 else 0
            else:
                host, port, db = 'localhost', 6379, 0
            
            # Create Redis connection with timeout settings
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            self.is_available = True
            logger.info(f"Redis connected successfully to {host}:{port}/{db}")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Falling back to database-only mode.")
            self.is_available = False
            self.redis_client = None
    
    def _ensure_connection(self):
        """Ensure Redis connection is active, reconnect if needed."""
        if not self.is_available:
            self._connect()
        elif self.redis_client:
            try:
                self.redis_client.ping()
            except Exception:
                logger.warning("Redis connection lost, attempting to reconnect...")
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
            
            # Compress CSV content to save memory
            import gzip
            compressed_content = gzip.compress(csv_content.encode('utf-8'))
            
            if not self.redis_client:
                logger.error("Redis client is not available")
                return False
                
            result = self.redis_client.setex(key, ttl, compressed_content)
            logger.info(f"Cached CSV data for user {user_id}, file {file_id}, size: {len(csv_content)} bytes")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to cache CSV data for user {user_id}, file {file_id}: {e}")
            return False
    
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
            compressed_data = self.redis_client.get(key)
            
            if compressed_data:
                # Decompress the data
                import gzip
                csv_content = gzip.decompress(compressed_data).decode('utf-8')
                logger.debug(f"Retrieved cached CSV data for user {user_id}, file {file_id}")
                return csv_content
            
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
            result = self.redis_client.delete(key)
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
            
            # Count CSV cache keys
            csv_keys = self.redis_client.keys("csv_data:*")
            total_csv_files = len(csv_keys)
            
            # Calculate total memory usage for CSV data
            total_size = 0
            for key in csv_keys:
                try:
                    size = self.redis_client.memory_usage(key)
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
            
            expiring_caches = []
            csv_keys = self.redis_client.keys("csv_data:*")
            current_time = int(time.time())
            expiry_threshold = minutes_before_expiry * 60  # Convert to seconds
            
            for key in csv_keys:
                try:
                    # Get TTL for this key
                    ttl = self.redis_client.ttl(key)
                    
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
            
            if not self.redis_client:
                logger.error("Redis client is not available")
                return False
            
            key = f"csv_data:{user_id}:{file_id}"
            
            # Check if cache exists
            if not self.redis_client.exists(key):
                logger.warning(f"Cache key {key} does not exist for refresh")
                return False
            
            # Extend TTL by 2 hours (7200 seconds)
            result = self.redis_client.expire(key, 7200)
            
            if result:
                logger.info(f"Successfully refreshed cache for user {user_id}, file {file_id}")
                return True
            else:
                logger.warning(f"Failed to refresh cache for user {user_id}, file {file_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to refresh cache for user {user_id}, file {file_id}: {e}")
            return False


# Global Redis service instance
redis_service = RedisService()
