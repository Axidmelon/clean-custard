# File: backend/core/working_memory.py

import json
import logging
import time
import hashlib
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from core.redis_service import redis_service

logger = logging.getLogger(__name__)


class WorkingMemoryService:
    """
    Working Memory service for AI agents to store and retrieve request-specific context.
    
    This service provides:
    - Request-scoped memory storage with automatic cleanup
    - Operation deduplication to prevent duplicate work
    - Context sharing between services during a single request
    - Automatic expiration and cleanup
    - Fallback to in-memory storage when Redis is unavailable
    
    Key Features:
    - Ultra-fast access (sub-millisecond)
    - Request isolation (no cross-request data leakage)
    - Automatic cleanup (prevents memory leaks)
    - Operation deduplication (prevents duplicate expensive operations)
    """
    
    def __init__(self):
        self.logger = logger
        self.redis_client = redis_service.redis_client
        self.is_available = redis_service.is_available
        
        # In-memory fallback cache
        self._fallback_cache = {}
        self._fallback_lock = threading.Lock()
        
        # Configuration
        self.default_ttl = 300  # 5 minutes
        self.max_fallback_entries = 1000
        
        # Cleanup thread for fallback cache
        self._cleanup_thread = threading.Thread(target=self._cleanup_fallback_cache, daemon=True)
        self._cleanup_thread.start()
        
        self.logger.info("🧠 Working Memory service initialized")
    
    def _generate_context_hash(self, data: Any) -> str:
        """Generate a hash for context data to use as cache key."""
        try:
            # Create a deterministic hash from the data
            if isinstance(data, (list, tuple)):
                # Sort lists to ensure consistent hashing
                data_str = json.dumps(sorted(data), sort_keys=True)
            elif isinstance(data, dict):
                # Sort dict keys to ensure consistent hashing
                data_str = json.dumps(data, sort_keys=True)
            else:
                data_str = str(data)
            
            return hashlib.md5(data_str.encode('utf-8')).hexdigest()[:16]
        except Exception as e:
            self.logger.warning(f"Failed to generate context hash: {e}")
            return hashlib.md5(str(time.time()).encode('utf-8')).hexdigest()[:16]
    
    def _get_redis_key(self, request_id: str, operation_type: str, context_hash: str) -> str:
        """Generate Redis key for working memory entry."""
        return f"working_memory:{request_id}:{operation_type}:{context_hash}"
    
    def _get_fallback_key(self, request_id: str, operation_type: str, context_hash: str) -> str:
        """Generate fallback cache key."""
        return f"{request_id}:{operation_type}:{context_hash}"
    
    def store_request_context(self, request_id: str, operation_type: str, 
                            context_data: Any, data: Dict[str, Any], 
                            ttl: Optional[int] = None) -> bool:
        """
        Store working memory entry for a specific request and operation.
        
        Args:
            request_id: Unique request identifier
            operation_type: Type of operation (e.g., 'schema_analysis', 'routing_decision')
            context_data: Data used to generate context hash (e.g., file_ids, question)
            data: Actual data to store
            ttl: Time to live in seconds (default: 5 minutes)
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            context_hash = self._generate_context_hash(context_data)
            ttl = ttl or self.default_ttl
            
            # Add metadata
            entry_data = {
                "request_id": request_id,
                "operation_type": operation_type,
                "context_hash": context_hash,
                "data": data,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "ttl": ttl
            }
            
            # Try Redis first
            if self.is_available and self.redis_client:
                redis_key = self._get_redis_key(request_id, operation_type, context_hash)
                serialized_data = json.dumps(entry_data, default=str)
                
                result = self.redis_client.setex(redis_key, ttl, serialized_data)
                if result:
                    self.logger.debug(f"🧠 Stored working memory: {operation_type} for request {request_id}")
                    return True
            
            # Fallback to in-memory cache
            with self._fallback_lock:
                fallback_key = self._get_fallback_key(request_id, operation_type, context_hash)
                self._fallback_cache[fallback_key] = {
                    "data": entry_data,
                    "expires_at": time.time() + ttl
                }
                
                # Cleanup if cache is too large
                if len(self._fallback_cache) > self.max_fallback_entries:
                    self._cleanup_fallback_cache()
                
                self.logger.debug(f"🧠 Stored working memory (fallback): {operation_type} for request {request_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to store working memory: {e}")
            return False
    
    def get_request_context(self, request_id: str, operation_type: str, 
                           context_data: Any) -> Optional[Dict[str, Any]]:
        """
        Retrieve working memory entry for a specific request and operation.
        
        Args:
            request_id: Unique request identifier
            operation_type: Type of operation
            context_data: Data used to generate context hash
            
        Returns:
            Stored data if found, None otherwise
        """
        try:
            context_hash = self._generate_context_hash(context_data)
            
            # Try Redis first
            if self.is_available and self.redis_client:
                redis_key = self._get_redis_key(request_id, operation_type, context_hash)
                cached_data = self.redis_client.get(redis_key)
                
                if cached_data:
                    entry_data = json.loads(cached_data)
                    self.logger.debug(f"🧠 Retrieved working memory: {operation_type} for request {request_id}")
                    return entry_data.get("data")
            
            # Fallback to in-memory cache
            with self._fallback_lock:
                fallback_key = self._get_fallback_key(request_id, operation_type, context_hash)
                cached_entry = self._fallback_cache.get(fallback_key)
                
                if cached_entry and cached_entry["expires_at"] > time.time():
                    self.logger.debug(f"🧠 Retrieved working memory (fallback): {operation_type} for request {request_id}")
                    return cached_entry["data"].get("data")
                elif cached_entry:
                    # Expired entry, remove it
                    del self._fallback_cache[fallback_key]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve working memory: {e}")
            return None
    
    def has_request_context(self, request_id: str, operation_type: str, 
                           context_data: Any) -> bool:
        """
        Check if working memory entry exists for a specific request and operation.
        
        Args:
            request_id: Unique request identifier
            operation_type: Type of operation
            context_data: Data used to generate context hash
            
        Returns:
            True if entry exists, False otherwise
        """
        return self.get_request_context(request_id, operation_type, context_data) is not None
    
    def deduplicate_operation(self, request_id: str, operation_type: str, 
                             context_data: Any) -> bool:
        """
        Check if an operation is already in progress or completed.
        This prevents duplicate expensive operations within the same request.
        
        Args:
            request_id: Unique request identifier
            operation_type: Type of operation
            context_data: Data used to generate context hash
            
        Returns:
            True if operation is already done/in progress, False if can proceed
        """
        return self.has_request_context(request_id, operation_type, context_data)
    
    def cleanup_request(self, request_id: str) -> bool:
        """
        Clean up all working memory entries for a specific request.
        
        Args:
            request_id: Unique request identifier
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            cleaned_count = 0
            
            # Cleanup Redis entries
            if self.is_available and self.redis_client:
                pattern = f"working_memory:{request_id}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    cleaned_count += self.redis_client.delete(*keys)
            
            # Cleanup fallback cache entries
            with self._fallback_lock:
                keys_to_remove = [
                    key for key in self._fallback_cache.keys() 
                    if key.startswith(f"{request_id}:")
                ]
                for key in keys_to_remove:
                    del self._fallback_cache[key]
                    cleaned_count += 1
            
            self.logger.debug(f"🧠 Cleaned up {cleaned_count} working memory entries for request {request_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup working memory for request {request_id}: {e}")
            return False
    
    def _cleanup_fallback_cache(self):
        """Clean up expired entries from fallback cache."""
        try:
            current_time = time.time()
            with self._fallback_lock:
                expired_keys = [
                    key for key, entry in self._fallback_cache.items()
                    if entry["expires_at"] <= current_time
                ]
                for key in expired_keys:
                    del self._fallback_cache[key]
                
                if expired_keys:
                    self.logger.debug(f"🧠 Cleaned up {len(expired_keys)} expired fallback entries")
        except Exception as e:
            self.logger.error(f"Failed to cleanup fallback cache: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get working memory statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        try:
            stats = {
                "redis_available": self.is_available,
                "fallback_entries": len(self._fallback_cache),
                "default_ttl": self.default_ttl
            }
            
            if self.is_available and self.redis_client:
                # Count Redis entries
                pattern = "working_memory:*"
                keys = self.redis_client.keys(pattern)
                stats["redis_entries"] = len(keys)
                
                # Get Redis memory usage
                try:
                    info = self.redis_client.info()
                    stats["redis_memory_usage"] = info.get("used_memory_human", "0B")
                except Exception:
                    stats["redis_memory_usage"] = "unknown"
            else:
                stats["redis_entries"] = 0
                stats["redis_memory_usage"] = "unavailable"
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}
    
    # Convenience methods for common operations
    
    def store_schema_analysis(self, request_id: str, file_ids: List[str], 
                             analysis_result: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store schema analysis results in standardized format."""
        try:
            # Convert to standardized format if needed
            from schemas.schema_interface import SchemaConverter
            
            # Determine source format and convert to standard
            file_schemas = analysis_result.get('file_schemas', {})
            if not file_schemas:
                # No file schemas to standardize
                return self.store_request_context(
                    request_id=request_id,
                    operation_type="schema_analysis",
                    context_data=file_ids,
                    data=analysis_result,
                    ttl=ttl
                )
            
            # Check if already standardized
            first_schema = list(file_schemas.values())[0]
            if 'file_info' in first_schema and 'row_count' in first_schema['file_info']:
                # Already in standardized format, don't convert again
                return self.store_request_context(
                    request_id=request_id,
                    operation_type="schema_analysis",
                    context_data=file_ids,
                    data=analysis_result,
                    ttl=ttl
                )
            else:
                # CSV schema analyzer format
                source_format = 'csv_schema_analyzer'
            
            # Convert file schemas to standard format
            standardized_schemas = {}
            for file_id, file_schema in file_schemas.items():
                try:
                    standard_schema = SchemaConverter.convert_to_standard(file_schema, source_format)
                    standardized_schemas[file_id] = standard_schema.to_dict()
                except Exception as e:
                    self.logger.warning(f"Failed to standardize schema for {file_id}: {e}")
                    standardized_schemas[file_id] = file_schema  # Keep original if conversion fails
            
            # Create standardized analysis result
            standardized_result = {
                **analysis_result,
                "file_schemas": standardized_schemas,
                "standardized": True,
                "source_format": source_format
            }
            
            return self.store_request_context(
                request_id=request_id,
                operation_type="schema_analysis",
                context_data=file_ids,
                data=standardized_result,
                ttl=ttl
            )
            
        except Exception as e:
            self.logger.error(f"Failed to store standardized schema analysis: {e}")
            # Fallback to original method
            return self.store_request_context(
                request_id=request_id,
                operation_type="schema_analysis",
                context_data=file_ids,
                data=analysis_result,
                ttl=ttl
            )
    
    def get_schema_analysis(self, request_id: str, file_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Retrieve schema analysis results."""
        return self.get_request_context(
            request_id=request_id,
            operation_type="schema_analysis",
            context_data=file_ids
        )
    
    def store_routing_decision(self, request_id: str, question: str, 
                              routing_result: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store AI routing decision."""
        return self.store_request_context(
            request_id=request_id,
            operation_type="routing_decision",
            context_data=question,
            data=routing_result,
            ttl=ttl
        )
    
    def get_routing_decision(self, request_id: str, question: str) -> Optional[Dict[str, Any]]:
        """Retrieve AI routing decision."""
        return self.get_request_context(
            request_id=request_id,
            operation_type="routing_decision",
            context_data=question
        )
    
    def store_langsmith_metadata(self, request_id: str, metadata_key: str, 
                                sanitized_metadata: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store sanitized LangSmith metadata."""
        return self.store_request_context(
            request_id=request_id,
            operation_type="langsmith_metadata",
            context_data=metadata_key,
            data=sanitized_metadata,
            ttl=ttl
        )
    
    def get_langsmith_metadata(self, request_id: str, metadata_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve sanitized LangSmith metadata."""
        return self.get_request_context(
            request_id=request_id,
            operation_type="langsmith_metadata",
            context_data=metadata_key
        )


# Global working memory service instance
working_memory_service = WorkingMemoryService()


def get_working_memory() -> WorkingMemoryService:
    """Get the global working memory service instance."""
    return working_memory_service
