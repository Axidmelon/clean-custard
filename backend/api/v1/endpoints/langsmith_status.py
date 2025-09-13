# File: backend/api/v1/endpoints/langsmith_status.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from db.dependencies import get_db
from core.langsmith_service import langsmith_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/langsmith/status")
async def get_langsmith_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get LangSmith service status and configuration.
    
    Returns:
        Dictionary containing LangSmith status information
    """
    try:
        # Get LangSmith project information
        project_info = langsmith_service.get_project_info()
        
        # Add additional status information
        status_info = {
            "langsmith_service": project_info,
            "tracing_enabled": langsmith_service.is_enabled,
            "client_available": langsmith_service.client is not None,
            "tracer_available": langsmith_service.tracer is not None,
            "service_initialized": langsmith_service._initialized
        }
        
        logger.info("LangSmith status retrieved successfully")
        return status_info
        
    except Exception as e:
        logger.error(f"Error retrieving LangSmith status: {e}")
        return {
            "error": str(e),
            "langsmith_service": {"enabled": False, "error": str(e)},
            "tracing_enabled": False,
            "client_available": False,
            "tracer_available": False,
            "service_initialized": False
        }


@router.get("/langsmith/health")
async def langsmith_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Perform a health check on LangSmith service.
    
    Returns:
        Dictionary containing health check results
    """
    try:
        health_info = {
            "status": "healthy" if langsmith_service.is_enabled else "disabled",
            "tracing_enabled": langsmith_service.is_enabled,
            "client_status": "connected" if langsmith_service.client else "not_connected",
            "tracer_status": "active" if langsmith_service.tracer else "inactive",
            "service_status": "initialized" if langsmith_service._initialized else "not_initialized"
        }
        
        # Test trace creation if enabled
        if langsmith_service.is_enabled:
            try:
                with langsmith_service.create_trace("health_check") as trace:
                    trace.metadata = {"test": True}
                health_info["trace_test"] = "success"
            except Exception as trace_error:
                health_info["trace_test"] = f"failed: {str(trace_error)}"
                health_info["status"] = "degraded"
        
        logger.info("LangSmith health check completed")
        return health_info
        
    except Exception as e:
        logger.error(f"Error performing LangSmith health check: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "tracing_enabled": False,
            "client_status": "error",
            "tracer_status": "error",
            "service_status": "error"
        }
