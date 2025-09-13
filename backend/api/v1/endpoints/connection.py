# File: backend/api/v1/endpoints/connection.py
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging

# Import database models, schemas, and dependencies
from db import models
from schemas import connection as connection_schema
from db.dependencies import get_db
from ws.connection_manager import manager
from core.api_key_service import APIKeyService
from core.jwt_handler import get_current_user
from schemas.user import User


class RefreshSchemaRequest(BaseModel):
    agent_id: str


class ConnectionStatusResponse(BaseModel):
    connection_id: str
    agent_connected: bool
    agent_id: str
    last_activity: Optional[float] = None
    connection_metadata: Optional[dict] = None


# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=connection_schema.Connection, status_code=201)
def create_connection(
    connection_in: connection_schema.ConnectionCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    """
    Create a new connection record in the database with a generated API key.

    Args:
        connection_in: Connection creation data
        db: Database session
        current_user: Authenticated user

    Returns:
        Created connection object with API key

    Raises:
        HTTPException: If connection creation fails
    """
    try:
        # Get organization ID from the authenticated user
        org_id = current_user.organization_id
        logger.info(f"Creating connection for organization: {org_id}")

        # Generate API key for the agent
        plain_api_key, hashed_api_key = APIKeyService.generate_api_key()

        # Generate unique agent ID based on connection name and timestamp
        import time

        agent_id = f"agent-{connection_in.name.lower().replace(' ', '-')}-{int(time.time())}"

        # Create a new SQLAlchemy model instance
        new_connection = models.Connection(
            name=connection_in.name,
            db_type=connection_in.db_type,
            organization_id=org_id,
            hashed_api_key=hashed_api_key,
            agent_id=agent_id,
        )

        # Add to database
        db.add(new_connection)
        db.commit()
        db.refresh(new_connection)

        # Add the plain API key to the response (this is the only time it's returned)
        new_connection.api_key = plain_api_key

        # Generate WebSocket URL for the agent
        from core.config import settings

        # Convert http to ws, https to wss
        if settings.backend_url.startswith("https"):
            base_url = settings.backend_url.replace("https", "wss")
        else:
            base_url = settings.backend_url.replace("http", "ws")
        websocket_url = f"{base_url}/api/v1/connections/ws/{agent_id}"
        new_connection.websocket_url = websocket_url

        logger.info(
            f"Created new connection: {new_connection.name} (ID: {new_connection.id}) with API key and WebSocket URL"
        )
        return new_connection

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create connection: {e}")
        raise HTTPException(status_code=500, detail="Failed to create connection")


@router.get("", response_model=List[dict])
def list_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    """
    Retrieve a list of connection records for the authenticated user's organization.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        List of connection objects with basic info (name, db_type, status)
    """
    try:
        # Filter connections by user's organization
        connections = db.query(models.Connection).filter(
            models.Connection.organization_id == current_user.organization_id
        ).all()
        logger.info(f"Retrieved {len(connections)} connections for organization {current_user.organization_id}")

        # Return only the essential fields
        result = []
        for conn in connections:
            result.append(
                {
                    "id": str(conn.id),
                    "name": conn.name,
                    "db_type": conn.db_type,
                    "status": conn.status or "PENDING",  # Default to PENDING if NULL
                    "agent_id": conn.agent_id,  # Include agent_id for query functionality
                    "db_schema_cache": conn.db_schema_cache is not None,  # Boolean indicating if schema is cached
                    "created_at": conn.created_at.isoformat() if conn.created_at else None,
                }
            )

        return result
    except Exception as e:
        logger.error(f"Failed to retrieve connections: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve connections")


@router.get("/{connection_id}", response_model=connection_schema.Connection)
def get_connection(
    connection_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    """
    Retrieve a specific connection by ID, ensuring user has access to it.

    Args:
        connection_id: UUID of the connection
        db: Database session
        current_user: Authenticated user

    Returns:
        Connection object

    Raises:
        HTTPException: If connection not found or user doesn't have access
    """
    connection = db.query(models.Connection).filter(
        models.Connection.id == connection_id,
        models.Connection.organization_id == current_user.organization_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    return connection


@router.post("/{connection_id}/refresh-schema", response_model=dict)
async def refresh_schema(
    connection_id: uuid.UUID,
    request_body: RefreshSchemaRequest,  # <-- CHANGE 1: Accept the new model
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    """
    Trigger database schema refresh for a specific connection.

    This endpoint:
    1. Validates the connection exists in the database and user has access
    2. Checks if the specified agent is connected
    3. Sends a schema discovery request to that agent

    Args:
        connection_id: UUID of the connection
        request_body: Contains the agent_id to target
        db: Database session
        current_user: Authenticated user

    Returns:
        Success message with connection details

    Raises:
        HTTPException: If connection not found or user doesn't have access
    """
    try:
        # Find the connection in the database, ensuring user has access
        db_connection = db.query(models.Connection).filter(
            models.Connection.id == connection_id,
            models.Connection.organization_id == current_user.organization_id
        ).first()

        if not db_connection:
            raise HTTPException(status_code=404, detail="Connection not found")

        # --- CHANGE 2: Use the agent_id from the request body ---
        agent_id = request_body.agent_id

        # Check if the specified agent is connected
        if not manager.is_agent_connected(agent_id):
            raise HTTPException(
                status_code=503, detail=f"Agent '{agent_id}' is not currently connected"
            )

        # Create the schema discovery command
        import uuid
        command = {
            "type": "SCHEMA_DISCOVERY_REQUEST",
            "query_id": str(uuid.uuid4()),  # Add query_id for agent compatibility
            "payload": {"connection_id": str(connection_id)},
        }

        # Send command to the agent and wait for a response
        response = await manager.send_query_to_agent(command, agent_id, timeout=30)

        if not response or response.get("status") != "success":
            error_detail = response.get("error", "Agent did not return a valid schema.")
            raise HTTPException(
                status_code=502, detail=f"Agent failed to process schema request: {error_detail}"
            )

        # --- CHANGE 3: Save the schema to the database ---
        schema_data = response.get("schema")
        db_connection.db_schema_cache = schema_data
        db.commit()
        db.refresh(db_connection)

        logger.info(f"Successfully refreshed and saved schema for connection {db_connection.name}")

        return {
            "message": "Schema refresh command sent to agent successfully",
            "connection_id": str(connection_id),
            "connection_name": db_connection.name,
            "agent_id": agent_id,
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in refresh_schema: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")




@router.delete("/{connection_id}", status_code=204)
def delete_connection(
    connection_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    """
    Delete a connection record.

    Args:
        connection_id: UUID of the connection to delete
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException: If connection not found or user doesn't have access
    """
    connection = db.query(models.Connection).filter(
        models.Connection.id == connection_id,
        models.Connection.organization_id == current_user.organization_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        db.delete(connection)
        db.commit()
        logger.info(f"Deleted connection: {connection.name} (ID: {connection_id})")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete connection {connection_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete connection")


@router.get("/{connection_id}/status", response_model=ConnectionStatusResponse)
def get_connection_status(
    connection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    """
    Get the connection status including agent connectivity.

    Args:
        connection_id: Connection UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        Connection status information

    Raises:
        HTTPException: If connection not found or user doesn't have access
    """
    try:
        connection_uuid = uuid.UUID(connection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid connection ID format")
    
    connection = db.query(models.Connection).filter(
        models.Connection.id == connection_uuid,
        models.Connection.organization_id == current_user.organization_id
    ).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Check if agent is connected
    agent_connected = False
    connection_metadata = None
    
    if connection.agent_id:
        agent_connected = manager.is_agent_connected(connection.agent_id)
        connection_metadata = manager.get_connection_info(connection.agent_id)

    return ConnectionStatusResponse(
        connection_id=connection_id,
        agent_connected=agent_connected,
        agent_id=connection.agent_id or "",
        last_activity=connection_metadata.get("last_activity") if connection_metadata else None,
        connection_metadata=connection_metadata or {}
    )
