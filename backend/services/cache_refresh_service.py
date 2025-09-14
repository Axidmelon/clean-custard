# File: backend/services/cache_refresh_service.py

import asyncio
import logging
from typing import List, Dict, Any
from core.redis_service import redis_service

logger = logging.getLogger(__name__)

class CacheRefreshService:
    """
    Background service for proactive CSV cache refresh.
    
    This service monitors Redis for expiring CSV caches and proactively
    refreshes them for active users to prevent cache misses during work sessions.
    """
    
    def __init__(self):
        self.is_running = False
        self.refresh_interval = 180  # Check every 3 minutes
        self.minutes_before_expiry = 5  # Refresh 5 minutes before expiry
        self.activity_threshold_minutes = 30  # Only refresh for users active within 30 minutes
        
        logger.info("CacheRefreshService initialized")
    
    async def start_background_refresh(self):
        """
        Start the background cache refresh service.
        """
        if self.is_running:
            logger.warning("Cache refresh service is already running")
            return
        
        self.is_running = True
        logger.info("Starting background cache refresh service")
        
        try:
            while self.is_running:
                await self._check_and_refresh_caches()
                await asyncio.sleep(self.refresh_interval)
        except Exception as e:
            logger.error(f"Error in background cache refresh service: {e}")
        finally:
            self.is_running = False
            logger.info("Background cache refresh service stopped")
    
    def stop_background_refresh(self):
        """
        Stop the background cache refresh service.
        """
        self.is_running = False
        logger.info("Stopping background cache refresh service")
    
    async def _check_and_refresh_caches(self):
        """
        Check for expiring caches and refresh them for active users.
        """
        try:
            # Get caches that are expiring soon
            expiring_caches = redis_service.get_expiring_caches(self.minutes_before_expiry)
            
            if not expiring_caches:
                logger.debug("No expiring caches found")
                return
            
            logger.info(f"Found {len(expiring_caches)} expiring caches")
            
            # Refresh each expiring cache
            refresh_count = 0
            for cache_info in expiring_caches:
                try:
                    user_id = cache_info["user_id"]
                    file_id = cache_info["file_id"]
                    expires_in_minutes = cache_info["expires_in_minutes"]
                    last_activity_minutes_ago = cache_info["last_activity_minutes_ago"]
                    
                    logger.info(f"Refreshing cache for user {user_id}, file {file_id} "
                              f"(expires in {expires_in_minutes}min, last activity {last_activity_minutes_ago}min ago)")
                    
                    # Refresh the cache
                    success = redis_service.refresh_expiring_cache(user_id, file_id)
                    
                    if success:
                        refresh_count += 1
                        logger.info(f"Successfully refreshed cache for user {user_id}, file {file_id}")
                    else:
                        logger.warning(f"Failed to refresh cache for user {user_id}, file {file_id}")
                        
                except Exception as e:
                    logger.error(f"Error refreshing cache {cache_info}: {e}")
                    continue
            
            if refresh_count > 0:
                logger.info(f"Successfully refreshed {refresh_count} out of {len(expiring_caches)} expiring caches")
            
        except Exception as e:
            logger.error(f"Error in cache refresh check: {e}")
    
    async def manual_refresh_cache(self, user_id: str, file_id: str) -> bool:
        """
        Manually refresh a specific cache.
        
        Args:
            user_id: User identifier
            file_id: File identifier
            
        Returns:
            True if refreshed successfully, False otherwise
        """
        try:
            logger.info(f"Manual cache refresh requested for user {user_id}, file {file_id}")
            
            # Check if user has recent activity
            activity_time = redis_service.get_user_activity(user_id, file_id)
            if not activity_time:
                logger.warning(f"No activity found for user {user_id}, file {file_id}")
                return False
            
            import time
            current_time = int(time.time())
            if (current_time - activity_time) > (self.activity_threshold_minutes * 60):
                logger.warning(f"User {user_id} not active recently for file {file_id}")
                return False
            
            # Refresh the cache
            success = redis_service.refresh_expiring_cache(user_id, file_id)
            
            if success:
                logger.info(f"Manual refresh successful for user {user_id}, file {file_id}")
            else:
                logger.warning(f"Manual refresh failed for user {user_id}, file {file_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in manual cache refresh: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get the current status of the cache refresh service.
        
        Returns:
            Dictionary with service status information
        """
        return {
            "is_running": self.is_running,
            "refresh_interval_seconds": self.refresh_interval,
            "minutes_before_expiry": self.minutes_before_expiry,
            "activity_threshold_minutes": self.activity_threshold_minutes
        }

# Global cache refresh service instance
cache_refresh_service = CacheRefreshService()
