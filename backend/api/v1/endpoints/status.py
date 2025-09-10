# File: backend/api/v1/endpoints/status.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.dependencies import get_db
from db.models import Connection
from ws.connection_manager import manager
from typing import List, Dict, Any

router = APIRouter()

@router.get("/status")
async def get_system_status(db: Session = Depends(get_db)):
    """
    Get the current system status including connected agents and database connections.
    """
    try:
        # Get connected agents from WebSocket manager
        connected_agents = manager.get_connected_agents()
        connection_stats = manager.get_connection_stats()
        
        # Get all connections from database
        db_connections = db.query(Connection).all()
        
        # Build status response
        status = {
            "system": "healthy",
            "connected_agents": connected_agents,
            "agent_count": len(connected_agents),
            "connection_stats": connection_stats,
            "database_connections": [
                {
                    "id": str(conn.id),
                    "name": conn.name,
                    "agent_id": conn.agent_id,
                    "is_agent_connected": conn.agent_id in connected_agents if conn.agent_id else False,
                    "has_schema_cache": bool(conn.db_schema_cache)
                }
                for conn in db_connections
            ]
        }
        
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {e}")

@router.get("/status/agents")
async def get_agent_status():
    """
    Get detailed status of all connected agents.
    """
    try:
        connected_agents = manager.get_connected_agents()
        agent_details = []
        
        for agent_id in connected_agents:
            connection_info = manager.get_connection_info(agent_id)
            agent_details.append({
                "agent_id": agent_id,
                "connected_at": connection_info.get("connected_at") if connection_info else None,
                "last_activity": connection_info.get("last_activity") if connection_info else None,
                "message_count": connection_info.get("message_count", 0) if connection_info else 0
            })
        
        return {
            "agents": agent_details,
            "total_agents": len(connected_agents)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {e}")
