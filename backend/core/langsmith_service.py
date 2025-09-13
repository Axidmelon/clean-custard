# File: backend/core/langsmith_service.py

import os
import logging
from typing import Dict, Any, Optional
from contextlib import contextmanager

from langsmith import Client, trace
from langchain.callbacks import LangChainTracer
from core.config import settings

logger = logging.getLogger(__name__)


class LangSmithService:
    """
    LangSmith service for AI observability and evaluation.
    
    This service provides:
    - LangSmith client initialization
    - Tracing utilities and helpers
    - Project configuration management
    - Error handling and fallback mechanisms
    """
    
    def __init__(self):
        """Initialize LangSmith service with client and tracer."""
        self._client = None
        self._tracer = None
        self._initialized = False
        
        # Initialize if tracing is enabled
        if settings.langsmith_tracing_enabled:
            self._initialize()
    
    def _initialize(self):
        """Initialize LangSmith client and tracer."""
        try:
            # Initialize LangSmith client
            self._client = Client(
                api_key=settings.langsmith_api_key,
                api_url=settings.langsmith_endpoint
            )
            
            # Initialize LangChain tracer
            self._tracer = LangChainTracer(project_name=settings.langsmith_project)
            
            self._initialized = True
            logger.info(f"LangSmith service initialized successfully for project: {settings.langsmith_project}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangSmith service: {e}")
            self._initialized = False
    
    @property
    def client(self) -> Optional[Client]:
        """Get LangSmith client."""
        return self._client if self._initialized else None
    
    @property
    def tracer(self) -> Optional[LangChainTracer]:
        """Get LangChain tracer."""
        return self._tracer if self._initialized else None
    
    @property
    def is_enabled(self) -> bool:
        """Check if LangSmith tracing is enabled and initialized."""
        return settings.langsmith_tracing_enabled and self._initialized
    
    def get_tracer(self) -> Optional[LangChainTracer]:
        """Get tracer for LangChain callbacks."""
        return self.tracer
    
    @contextmanager
    def create_trace(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Create a LangSmith trace context manager.
        
        Args:
            name: Name of the trace
            metadata: Optional metadata to attach to the trace
            
        Yields:
            Trace object for adding metadata
        """
        if not self.is_enabled:
            # Return a dummy context manager if tracing is disabled
            class DummyTrace:
                def __init__(self):
                    self.metadata = metadata or {}
                
                def __enter__(self):
                    return self
                
                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass
            
            dummy = DummyTrace()
            try:
                yield dummy
            finally:
                pass
            return
        
        try:
            # Create trace with LangSmith
            with trace(name, metadata=metadata or {}) as trace_obj:
                yield trace_obj
        except Exception as e:
            logger.error(f"Error creating LangSmith trace '{name}': {e}")
            # Fallback to dummy trace
            class DummyTrace:
                def __init__(self):
                    self.metadata = metadata or {}
                
                def __enter__(self):
                    return self
                
                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass
            
            dummy = DummyTrace()
            try:
                yield dummy
            finally:
                pass
    
    def add_metadata(self, trace_obj, metadata: Dict[str, Any]):
        """
        Add metadata to a trace object.
        
        Args:
            trace_obj: Trace object to add metadata to
            metadata: Metadata dictionary to add
        """
        try:
            if hasattr(trace_obj, 'metadata') and trace_obj.metadata is not None:
                trace_obj.metadata.update(metadata)
            else:
                trace_obj.metadata = metadata
        except Exception as e:
            logger.error(f"Error adding metadata to trace: {e}")
    
    def log_trace_event(self, event_type: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Log a trace event for debugging and monitoring.
        
        Args:
            event_type: Type of event (e.g., 'sql_generation', 'pandas_analysis')
            message: Event message
            metadata: Optional metadata
        """
        if self.is_enabled:
            logger.info(f"LangSmith Trace Event [{event_type}]: {message}")
            if metadata:
                logger.debug(f"Trace Metadata: {metadata}")
        else:
            logger.debug(f"Trace Event [{event_type}]: {message}")
    
    def get_project_info(self) -> Dict[str, Any]:
        """
        Get information about the current LangSmith project.
        
        Returns:
            Dictionary containing project information
        """
        if not self.is_enabled:
            return {"enabled": False, "message": "LangSmith tracing is disabled"}
        
        try:
            # Get project information from LangSmith
            project_info = {
                "enabled": True,
                "project_name": settings.langsmith_project,
                "endpoint": settings.langsmith_endpoint,
                "client_initialized": self._client is not None,
                "tracer_initialized": self._tracer is not None
            }
            
            return project_info
            
        except Exception as e:
            logger.error(f"Error getting LangSmith project info: {e}")
            return {
                "enabled": True,
                "error": str(e),
                "project_name": settings.langsmith_project
            }


# Global instance
langsmith_service = LangSmithService()


def get_langsmith_service() -> LangSmithService:
    """Get the global LangSmith service instance."""
    return langsmith_service


def is_langsmith_enabled() -> bool:
    """Check if LangSmith tracing is enabled."""
    return langsmith_service.is_enabled


def create_trace(name: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Convenience function to create a LangSmith trace.
    
    Args:
        name: Name of the trace
        metadata: Optional metadata to attach to the trace
        
    Returns:
        Context manager for the trace
    """
    return langsmith_service.create_trace(name, metadata)
