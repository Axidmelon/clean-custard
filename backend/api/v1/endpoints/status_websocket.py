# File: backend/api/v1/endpoints/status_websocket.py

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
from ws.connection_manager import manager
from core.websocket_cors import validate_websocket_cors

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Store WebSocket connections for status updates
status_connections: Set[WebSocket] = set()

@router.websocket("/status/ws")
async def status_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time status updates.
    
    This endpoint:
    - Accepts frontend connections for status updates
    - Broadcasts agent connection/disconnection events
    - Handles connection cleanup on disconnect
    - Validates CORS for both development and production environments
    """
    # Validate CORS using centralized validator
    if not await validate_websocket_cors(websocket, "status-websocket"):
        return
    
    await websocket.accept()
    status_connections.add(websocket)
    logger.info(f"Status WebSocket connected. Total status connections: {len(status_connections)}")
    
    try:
        # Send initial status of all agents
        await send_all_agent_status(websocket)
        
        # Keep connection alive
        while True:
            # Just keep the connection alive - we'll send updates when agents connect/disconnect
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        logger.info("Status WebSocket disconnected")
        status_connections.discard(websocket)
    except Exception as e:
        logger.error(f"Error in status WebSocket: {e}")
        status_connections.discard(websocket)
    finally:
        status_connections.discard(websocket)

async def send_all_agent_status(websocket: WebSocket):
    """Send current status of all agents to a specific WebSocket connection."""
    try:
        connected_agents = manager.get_connected_agents()
        
        # Send status for each agent
        for agent_id in connected_agents:
            message = {
                "type": "AGENT_STATUS_UPDATE",
                "agent_id": agent_id,
                "agentConnected": True
            }
            await websocket.send_text(json.dumps(message))
            
        logger.debug(f"Sent initial status for {len(connected_agents)} agents")
        
    except Exception as e:
        logger.error(f"Error sending initial agent status: {e}")

async def broadcast_agent_status_update(agent_id: str, agent_connected: bool):
    """Broadcast agent status update to all connected status WebSocket clients."""
    if not status_connections:
        return
        
    message = {
        "type": "AGENT_STATUS_UPDATE",
        "agent_id": agent_id,
        "agentConnected": agent_connected
    }
    
    message_text = json.dumps(message)
    disconnected_connections = set()
    
    for websocket in status_connections.copy():
        try:
            await websocket.send_text(message_text)
        except WebSocketDisconnect:
            disconnected_connections.add(websocket)
        except Exception as e:
            logger.error(f"Error sending status update to WebSocket: {e}")
            disconnected_connections.add(websocket)
    
    # Clean up disconnected connections
    for websocket in disconnected_connections:
        status_connections.discard(websocket)
    
    logger.info(f"Broadcasted agent status update for {agent_id}: {agent_connected} to {len(status_connections)} clients")

# Register handlers with the connection manager
def register_status_handlers():
    """Register handlers to broadcast status updates when agents connect/disconnect."""
    
    async def on_agent_connect(agent_id: str, message: Dict):
        """Handle agent connection."""
        await broadcast_agent_status_update(agent_id, True)
    
    async def on_agent_disconnect(agent_id: str, message: Dict):
        """Handle agent disconnection."""
        await broadcast_agent_status_update(agent_id, False)
    
    # Register the handlers
    manager.register_message_handler("AGENT_CONNECTED", on_agent_connect)
    manager.register_message_handler("AGENT_DISCONNECTED", on_agent_disconnect)

# Initialize handlers when module is imported
register_status_handlers()
