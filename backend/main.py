# File: backend/main.py

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Import API routers
from api.v1.endpoints import connection, websocket, status_websocket, status
from api.v1.endpoints import query as query_router
from api.v1.endpoints import test, auth

# Import connection manager
from ws.connection_manager import manager

# Import configuration
from core.config import settings, validate_production_readiness

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
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
    allow_origins=settings.allowed_origins,
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

# Include API routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(connection.router, prefix="/api/v1/connections", tags=["Connections"])
app.include_router(websocket.router, prefix="/api/v1", tags=["WebSocket"])
app.include_router(status_websocket.router, prefix="/api/v1", tags=["Status WebSocket"])
app.include_router(status.router, prefix="/api/v1", tags=["Status"])
app.include_router(query_router.router, prefix="/api/v1", tags=["query"])
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
    try:
        # Test database connectivity
        from db.dependencies import get_db
        from sqlalchemy import text

        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    connection_stats = manager.get_connection_stats()

    # Determine overall health status
    overall_status = "healthy" if db_status == "healthy" else "unhealthy"

    return {
        "status": overall_status,
        "version": "1.0.0",
        "timestamp": "2025-09-10T00:00:00Z",
        "services": {"database": db_status, "websocket_manager": "healthy"},
        "connections": {
            "total": connection_stats["total_connections"],
            "agents": connection_stats["connected_agents"],
        },
        "uptime": "running",
    }


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
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred"},
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
