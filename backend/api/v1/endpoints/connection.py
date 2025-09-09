# File: backend/api/v1/endpoints/connection.py
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging

# Import database models, schemas, and dependencies
from db import models
from schemas import connection as connection_schema
from db.dependencies import get_db
from ws.connection_manager import manager
from core.api_key_service import APIKeyService


class RefreshSchemaRequest(BaseModel):
    agent_id: str


# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=connection_schema.Connection, status_code=201)
def create_connection(
    connection_in: connection_schema.ConnectionCreate, db: Session = Depends(get_db)
):
    """
    Create a new connection record in the database with a generated API key.

    Args:
        connection_in: Connection creation data
        db: Database session

    Returns:
        Created connection object with API key

    Raises:
        HTTPException: If connection creation fails
    """
    try:
        # For now, assume one organization for simplicity
        # TODO: In a real multi-tenant app, get the org_id from the logged-in user
        org_id = "9a4857ae-5f33-4e4d-8fea-663b05bfc35b"

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
def list_connections(db: Session = Depends(get_db)):
    """
    Retrieve a list of all connection records from the database.

    Args:
        db: Database session

    Returns:
        List of connection objects with basic info (name, db_type, status)
    """
    try:
        connections = db.query(models.Connection).all()
        logger.info(f"Retrieved {len(connections)} connections")

        # Return only the essential fields
        result = []
        for conn in connections:
            result.append(
                {
                    "id": str(conn.id),
                    "name": conn.name,
                    "db_type": conn.db_type,
                    "status": conn.status or "PENDING",  # Default to PENDING if NULL
                    "created_at": conn.created_at.isoformat() if conn.created_at else None,
                }
            )

        return result
    except Exception as e:
        logger.error(f"Failed to retrieve connections: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve connections")


@router.get("/{connection_id}", response_model=connection_schema.Connection)
def get_connection(connection_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve a specific connection by ID.

    Args:
        connection_id: UUID of the connection
        db: Database session

    Returns:
        Connection object

    Raises:
        HTTPException: If connection not found
    """
    connection = db.query(models.Connection).filter(models.Connection.id == connection_id).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    return connection


@router.post("/{connection_id}/refresh-schema", response_model=dict)
async def refresh_schema(
    connection_id: uuid.UUID,
    request_body: RefreshSchemaRequest,  # <-- CHANGE 1: Accept the new model
    db: Session = Depends(get_db),
):
    """
    Trigger database schema refresh for a specific connection.

    This endpoint:
    1. Validates the connection exists in the database
    2. Checks if the specified agent is connected
    3. Sends a schema discovery request to that agent

    Args:
        connection_id: UUID of the connection
        request_body: Contains the agent_id to target
        db: Database session

    Returns:
        Success message with connection details

    Raises:
        HTTPException: If connection not found or agent not connected
    """
    try:
        # Find the connection in the database
        db_connection = (
            db.query(models.Connection).filter(models.Connection.id == connection_id).first()
        )

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
        command = {
            "type": "SCHEMA_DISCOVERY_REQUEST",
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


@router.get("/{connection_id}/status", response_model=dict)
def get_connection_status(connection_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get the connection status including agent connectivity.

    Args:
        connection_id: UUID of the connection
        db: Database session

    Returns:
        Connection status information
    """
    # Get the connection from database to find its agent_id
    connection = db.query(models.Connection).filter(models.Connection.id == connection_id).first()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Use the agent_id from the database
    agent_id = connection.agent_id
    is_connected = manager.is_agent_connected(agent_id) if agent_id else False

    return {
        "connection_id": str(connection_id),
        "agent_id": agent_id,
        "agent_connected": is_connected,
        "status": "active" if is_connected else "disconnected",
    }


@router.delete("/{connection_id}", status_code=204)
def delete_connection(connection_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a connection record.

    Args:
        connection_id: UUID of the connection to delete
        db: Database session

    Raises:
        HTTPException: If connection not found
    """
    connection = db.query(models.Connection).filter(models.Connection.id == connection_id).first()

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
