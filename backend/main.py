# File: backend/main.py

import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv

# Import API routers
from api.v1.endpoints import connection, websocket, status_websocket, status
from api.v1.endpoints import query as query_router
from api.v1.endpoints import test, auth, file_upload, data_analysis, langsmith_status

# Import connection manager
from ws.connection_manager import manager

# Import configuration
from core.config import settings, validate_production_readiness

# Load environment variables
load_dotenv()

# Set up logging
def setup_logging():
    """Configure logging for production and development."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    if settings.environment == "production":
        # Production logging configuration - optimized for Railway rate limits
        logging.basicConfig(
            level=getattr(logging, settings.log_level),
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("/app/logs/app.log", mode="a"),
            ]
        )
        
        # Reduce noise from third-party libraries and frequent operations
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)
        logging.getLogger("websockets").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
    else:
        # Development logging configuration
        logging.basicConfig(
            level=getattr(logging, settings.log_level),
            format=log_format,
        )

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Custard Backend API...")
    # Perform startup validation
    try:
        await startup_validation()
        logger.info("Startup validation completed successfully")
    except Exception as e:
        logger.error(f"Startup validation failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Custard Backend API...")
    try:
        await graceful_shutdown()
        logger.info("Graceful shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


async def startup_validation():
    """
    Validate that all required services are available at startup.
    """
    logger.info("Performing startup validation...")

    # Test database connectivity
    try:
        from db.dependencies import get_db
        from sqlalchemy import text

        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✓ Database connection validated")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        raise Exception(f"Database startup validation failed: {e}")

    # Test WebSocket manager
    try:
        manager.get_connection_stats()
        logger.info("✓ WebSocket manager initialized")
    except Exception as e:
        logger.error(f"✗ WebSocket manager initialization failed: {e}")
        raise Exception(f"WebSocket manager startup validation failed: {e}")

    # Validate critical configuration
    if settings.environment == "production":
        validation_errors = validate_production_readiness()
        if validation_errors:
            logger.error("✗ Production readiness check failed:")
            for error in validation_errors:
                logger.error(f"  - {error}")
            raise Exception("Production readiness validation failed")
        logger.info("✓ Production readiness validated")

    logger.info("✓ All startup validations passed")
    
    # Start background cache refresh service
    try:
        from services.cache_refresh_service import cache_refresh_service
        import asyncio
        
        # Start the background service in a separate task
        asyncio.create_task(cache_refresh_service.start_background_refresh())
        logger.info("✓ Background cache refresh service started")
    except Exception as e:
        logger.error(f"Failed to start background cache refresh service: {e}")
        # Don't fail startup if cache refresh service fails


async def graceful_shutdown():
    """
    Perform graceful shutdown of all services.
    """
    logger.info("Initiating graceful shutdown...")

    # Disconnect all WebSocket connections
    try:
        connected_agents = manager.get_connected_agents()
        for agent_id in connected_agents:
            manager.disconnect(agent_id)
        logger.info(f"✓ Disconnected {len(connected_agents)} WebSocket connections")
    except Exception as e:
        logger.error(f"Error disconnecting WebSocket connections: {e}")

    # Close database connections
    try:
        from db.database import engine

        engine.dispose()
        logger.info("✓ Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")

    # Stop background cache refresh service
    try:
        from services.cache_refresh_service import cache_refresh_service
        cache_refresh_service.stop_background_refresh()
        logger.info("✓ Background cache refresh service stopped")
    except Exception as e:
        logger.error(f"Error stopping background cache refresh service: {e}")
    
    logger.info("✓ Graceful shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="Custard Backend API",
    version="1.0.0",
    description="The backend service for the Custard AI Data Agent platform",
    lifespan=lifespan,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins if settings.allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
)

# Production middleware
if settings.environment == "production":
    # Trusted host middleware for security
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure with your actual domains in production
    )

# Gzip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    
    # HSTS header for HTTPS (only in production)
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    # Content Security Policy - Enhanced for production
    if settings.environment == "production":
        csp = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss: ws:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    else:
        csp = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'"
    
    response.headers["Content-Security-Policy"] = csp
    
    return response

# Global OPTIONS handler for CORS preflight requests
@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handle all OPTIONS requests for CORS preflight"""
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, Origin, X-Requested-With, Access-Control-Request-Method, Access-Control-Request-Headers",
            "Access-Control-Max-Age": "86400"
        }
    )

# Include API routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(connection.router, prefix="/api/v1/connections", tags=["Connections"])
app.include_router(websocket.router, prefix="/api/v1", tags=["WebSocket"])
app.include_router(status_websocket.router, prefix="/api/v1", tags=["Status WebSocket"])
app.include_router(status.router, prefix="/api/v1", tags=["Status"])
app.include_router(query_router.router, prefix="/api/v1", tags=["query"])
app.include_router(file_upload.router, prefix="/api/v1/files", tags=["File Upload"])
app.include_router(data_analysis.router, prefix="/api/v1/data", tags=["Data Analysis"])
app.include_router(langsmith_status.router, prefix="/api/v1", tags=["LangSmith"])
app.include_router(test.router, prefix="/api/v1", tags=["test"])


# --- Health and Status Endpoints ---


@app.get("/", tags=["Health Check"])
def read_root():
    """
    Root endpoint to check if the server is running.

    Returns:
        Welcome message and basic API information
    """
    return {
        "message": "Welcome to the Custard Backend API!",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health Check"])
def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        Detailed health status information
    """
    import datetime
    
    health_data = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "environment": settings.environment,
        "services": {},
        "connections": {},
        "uptime": "running",
    }
    
    # Test database connectivity
    try:
        from db.dependencies import get_db
        from sqlalchemy import text
        import time
        
        start_time = time.time()
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        db_response_time = time.time() - start_time
        
        health_data["services"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_response_time * 1000, 2)
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_data["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "unhealthy"

    # WebSocket manager check
    try:
        connection_stats = manager.get_connection_stats()
        health_data["services"]["websocket_manager"] = {
            "status": "healthy",
            "total_connections": connection_stats["total_connections"],
            "connected_agents": connection_stats["connected_agents"]
        }
        health_data["connections"] = {
            "total": connection_stats["total_connections"],
            "agents": connection_stats["connected_agents"],
        }
    except Exception as e:
        logger.error(f"WebSocket manager health check failed: {e}")
        health_data["services"]["websocket_manager"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_data["status"] = "unhealthy"

    # Redis cache check
    try:
        from core.redis_service import redis_service
        redis_stats = redis_service.get_cache_stats()
        health_data["services"]["redis_cache"] = redis_stats
    except Exception as e:
        logger.error(f"Redis cache health check failed: {e}")
        health_data["services"]["redis_cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # External services check
    if settings.openai_api_key and settings.openai_api_key != "your-openai-api-key-here":
        health_data["services"]["openai"] = {"status": "configured"}
    else:
        health_data["services"]["openai"] = {"status": "not_configured"}

    if settings.resend_api_key and settings.resend_api_key != "your-resend-api-key-here":
        health_data["services"]["resend"] = {"status": "configured"}
    else:
        health_data["services"]["resend"] = {"status": "not_configured"}

    return health_data


@app.get("/status", tags=["Health Check"])
def get_status():
    """
    Get detailed system status including agent connections.

    Returns:
        Comprehensive system status
    """
    connection_stats = manager.get_connection_stats()

    return {
        "api_status": "healthy",
        "version": "1.0.0",
        "environment": settings.environment,
        "agents": {
            "connected": connection_stats["total_connections"],
            "list": connection_stats["connected_agents"],
            "average_connection_time": connection_stats["average_connection_time"],
            "total_messages_received": connection_stats["total_messages_received"],
        },
        "endpoints": {
            "connections": "/api/v1/connections",
            "websocket": "/api/v1/connections/ws/{agent_id}",
            "docs": "/docs" if settings.enable_docs else "disabled",
        },
    }


@app.get("/ready", tags=["Health Check"])
def readiness_check():
    """
    Kubernetes-style readiness probe endpoint.

    This endpoint checks if the application is ready to serve traffic.
    Returns 200 if ready, 503 if not ready.

    Returns:
        Readiness status with detailed service checks
    """
    checks = {}
    all_healthy = True

    # Database connectivity check
    try:
        from db.dependencies import get_db
        from sqlalchemy import text

        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = {"status": "healthy", "message": "Database connection successful"}
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }
        all_healthy = False

    # WebSocket manager check
    try:
        manager.get_connection_stats()
        checks["websocket_manager"] = {
            "status": "healthy",
            "message": "WebSocket manager operational",
        }
    except Exception as e:
        checks["websocket_manager"] = {
            "status": "unhealthy",
            "message": f"WebSocket manager error: {str(e)}",
        }
        all_healthy = False

    # External services check (if configured)
    if settings.openai_api_key and settings.openai_api_key != "your-openai-api-key-here":
        checks["openai"] = {"status": "configured", "message": "OpenAI API key configured"}
    else:
        checks["openai"] = {"status": "not_configured", "message": "OpenAI API key not configured"}

    if settings.resend_api_key and settings.resend_api_key != "your-resend-api-key-here":
        checks["resend"] = {"status": "configured", "message": "Resend API key configured"}
    else:
        checks["resend"] = {"status": "not_configured", "message": "Resend API key not configured"}

    status_code = 200 if all_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "ready": all_healthy,
            "timestamp": "2025-09-10T00:00:00Z",
            "checks": checks,
            "environment": settings.environment,
        },
    )


@app.get("/metrics", tags=["Monitoring"])
def get_metrics():
    """
    Get application metrics for monitoring and observability.

    Returns:
        Application metrics and performance data
    """
    import datetime
    import os
    
    # Get system metrics (with fallback if psutil not available)
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_usage_mb = round(memory_info.rss / 1024 / 1024, 2)
        memory_percent = round(process.memory_percent(), 2)
        cpu_percent = round(process.cpu_percent(), 2)
        threads = process.num_threads()
        uptime_seconds = time.time() - process.create_time()
    except ImportError:
        # Fallback if psutil is not available
        memory_usage_mb = 0
        memory_percent = 0
        cpu_percent = 0
        threads = 0
        uptime_seconds = 0
    
    # Get database connection pool stats
    from db.database import engine
    pool = engine.pool
    pool_stats = {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid(),
    }
    
    # Get WebSocket connection stats
    ws_stats = manager.get_connection_stats()
    
    return {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "environment": settings.environment,
        "version": "1.0.0",
        "system": {
            "memory_usage_mb": memory_usage_mb,
            "memory_percent": memory_percent,
            "cpu_percent": cpu_percent,
            "threads": threads,
        },
        "database_pool": pool_stats,
        "websocket_connections": ws_stats,
        "uptime_seconds": uptime_seconds,
    }


@app.get("/production-readiness", tags=["Health Check"])
def check_production_readiness():
    """
    Check if the application is ready for production deployment.

    Returns:
        Production readiness status and validation results
    """
    validation_errors = validate_production_readiness()

    return {
        "production_ready": len(validation_errors) == 0,
        "environment": settings.environment,
        "validation_errors": validation_errors,
        "recommendations": (
            [
                "Set ENVIRONMENT=production",
                "Set DEBUG=false",
                "Set ENABLE_DOCS=false",
                "Configure ALLOWED_ORIGINS with production domains",
                "Use HTTPS for FRONTEND_URL",
                "Configure SENTRY_DSN for monitoring",
                "Set up Redis for rate limiting",
            ]
            if validation_errors
            else []
        ),
    }


# --- WebSocket Endpoints ---
# Note: WebSocket endpoint is defined in api/v1/endpoints/websocket.py


# --- Test and Development Endpoints ---


@app.post("/test/send-command/{agent_id}", tags=["Testing"])
async def test_send_command(agent_id: str, command: dict):
    """
    Test endpoint to send commands to agents.

    This is primarily for development and testing purposes.

    Args:
        agent_id: Target agent identifier
        command: Command dictionary to send

    Returns:
        Success status and response
    """
    if not manager.is_agent_connected(agent_id):
        raise HTTPException(status_code=404, detail="Agent not connected")

    try:
        success = await manager.send_json_to_agent(command, agent_id)
        if success:
            return {
                "status": "success",
                "message": f"Command sent to agent {agent_id}",
                "command": command,
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send command")
    except Exception as e:
        logger.error(f"Error sending command to agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test/agents", tags=["Testing"])
def list_connected_agents():
    """
    List all currently connected agents.

    Returns:
        List of connected agent information
    """
    agents = manager.get_connected_agents()
    agent_info = []

    for agent_id in agents:
        info = manager.get_connection_info(agent_id)
        agent_info.append(
            {
                "agent_id": agent_id,
                "connected_at": info.get("connected_at") if info else None,
                "last_activity": info.get("last_activity") if info else None,
                "message_count": info.get("message_count", 0) if info else 0,
            }
        )

    return {"total_agents": len(agents), "agents": agent_info}


# --- Error Handlers ---

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with custom response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with custom response."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors(),
            "path": str(request.url.path),
        },
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors with custom response."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors with custom response."""
    logger.error(f"Internal server error: {exc}")
    
    # In production, don't expose internal error details
    if settings.environment == "production":
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error", 
                "message": "An unexpected error occurred",
                "request_id": getattr(request.state, "request_id", None)
            },
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error", 
                "message": str(exc),
                "request_id": getattr(request.state, "request_id", None)
            },
        )


# --- Application Startup ---

if __name__ == "__main__":
    import uvicorn

    # Check production readiness
    validation_errors = validate_production_readiness()
    if validation_errors and settings.environment == "production":
        logger.error("Production readiness check failed:")
        for error in validation_errors:
            logger.error(f"  - {error}")
        logger.error("Please fix these issues before starting in production mode.")
        exit(1)

    logger.info(f"Starting server on {settings.host}:{settings.port}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"API docs enabled: {settings.enable_docs}")

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
