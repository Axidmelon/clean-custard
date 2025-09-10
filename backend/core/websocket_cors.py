# File: backend/core/websocket_cors.py

import logging
from typing import List, Optional
from urllib.parse import urlparse
from core.config import settings

logger = logging.getLogger(__name__)


class WebSocketCORSValidator:
    """
    Centralized CORS validation for WebSocket connections.
    
    This class provides consistent CORS validation for WebSocket endpoints
    that works across development and production environments.
    """
    
    def __init__(self):
        self.allowed_origins = settings.allowed_origins
        self.environment = settings.environment
        self._setup_environment_specific_origins()
    
    def _setup_environment_specific_origins(self):
        """Setup environment-specific allowed origins."""
        if self.environment == "development":
            # Add common development origins if not already present
            dev_origins = [
                "http://localhost:3000",
                "http://localhost:8080", 
                "http://localhost:5173",
                "https://localhost:3000",
                "https://localhost:8080",
                "https://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080",
                "http://127.0.0.1:5173"
            ]
            
            # Merge with configured origins, avoiding duplicates
            for origin in dev_origins:
                if origin not in self.allowed_origins:
                    self.allowed_origins.append(origin)
        
        logger.info(f"WebSocket CORS configured for {self.environment} environment")
        logger.debug(f"Allowed origins: {self.allowed_origins}")
    
    def is_origin_allowed(self, origin: Optional[str]) -> bool:
        """
        Check if an origin is allowed for WebSocket connections.
        
        Args:
            origin: The origin header value from the WebSocket request
            
        Returns:
            True if origin is allowed, False otherwise
        """
        if not origin:
            # Allow connections without origin header (e.g., from agents, mobile apps)
            logger.debug("WebSocket connection without origin header - allowing")
            return True
        
        # Check exact match first
        if origin in self.allowed_origins:
            logger.debug(f"WebSocket origin allowed (exact match): {origin}")
            return True
        
        # Check for subdomain matches in production
        if self.environment == "production":
            if self._is_subdomain_allowed(origin):
                logger.debug(f"WebSocket origin allowed (subdomain match): {origin}")
                return True
        
        logger.warning(f"WebSocket origin rejected: {origin}")
        return False
    
    def _is_subdomain_allowed(self, origin: str) -> bool:
        """
        Check if origin is allowed as a subdomain of configured domains.
        
        Args:
            origin: The origin to check
            
        Returns:
            True if origin is a subdomain of allowed domains
        """
        try:
            origin_parsed = urlparse(origin)
            origin_domain = origin_parsed.netloc.lower()
            
            for allowed_origin in self.allowed_origins:
                allowed_parsed = urlparse(allowed_origin)
                allowed_domain = allowed_parsed.netloc.lower()
                
                # Check if origin is a subdomain of allowed domain
                if origin_domain.endswith(f".{allowed_domain}") or origin_domain == allowed_domain:
                    return True
                    
        except Exception as e:
            logger.error(f"Error parsing origin for subdomain check: {e}")
            
        return False
    
    def get_connection_context(self, origin: Optional[str]) -> dict:
        """
        Get connection context information for logging and monitoring.
        
        Args:
            origin: The origin header value
            
        Returns:
            Dictionary with connection context information
        """
        return {
            "origin": origin,
            "environment": self.environment,
            "allowed": self.is_origin_allowed(origin),
            "total_allowed_origins": len(self.allowed_origins)
        }


# Global instance for use across the application
cors_validator = WebSocketCORSValidator()


async def validate_websocket_cors(websocket, endpoint_name: str = "websocket") -> bool:
    """
    Validate CORS for a WebSocket connection.
    
    Args:
        websocket: FastAPI WebSocket object
        endpoint_name: Name of the endpoint for logging
        
    Returns:
        True if CORS validation passes, False otherwise
    """
    origin = websocket.headers.get("origin")
    context = cors_validator.get_connection_context(origin)
    
    logger.info(f"{endpoint_name} connection attempt from origin: {origin}")
    
    if not context["allowed"]:
        logger.warning(f"{endpoint_name} connection rejected - origin not allowed: {origin}")
        await websocket.close(code=1008, reason="Origin not allowed")
        return False
    
    logger.debug(f"{endpoint_name} connection allowed for origin: {origin}")
    return True
