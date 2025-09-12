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
        logger.info(f"Sending initial status for {len(connected_agents)} agents: {connected_agents}")
        
        # Send status for each agent
        for agent_id in connected_agents:
            message = {
                "type": "AGENT_STATUS_UPDATE",
                "agent_id": agent_id,
                "agentConnected": True
            }
            await websocket.send_text(json.dumps(message))
            logger.debug(f"Sent initial status for agent {agent_id}: connected")
            
        logger.info(f"Successfully sent initial status for {len(connected_agents)} agents")
        
        # If no agents are connected, send a status update indicating this
        if len(connected_agents) == 0:
            logger.info("No agents currently connected - sending empty status")
            empty_message = {
                "type": "AGENT_STATUS_UPDATE",
                "agent_id": "system",
                "agentConnected": False,
                "message": "No agents currently connected"
            }
            await websocket.send_text(json.dumps(empty_message))
        
    except Exception as e:
        logger.error(f"Error sending initial agent status: {e}")

async def broadcast_agent_status_update(agent_id: str, agent_connected: bool):
    """Broadcast agent status update to all connected status WebSocket clients."""
    logger.info(f"Broadcasting agent status update for {agent_id}: {agent_connected} to {len(status_connections)} clients")
    
    if not status_connections:
        logger.warning("No status WebSocket connections available for broadcasting")
        return
        
    message = {
        "type": "AGENT_STATUS_UPDATE",
        "agent_id": agent_id,
        "agentConnected": agent_connected
    }
    
    message_text = json.dumps(message)
    disconnected_connections = set()
    successful_sends = 0
    
    for websocket in status_connections.copy():
        try:
            await websocket.send_text(message_text)
            successful_sends += 1
            logger.debug(f"Sent status update to WebSocket client: {agent_id} -> {agent_connected}")
        except WebSocketDisconnect:
            logger.debug(f"WebSocket client disconnected during broadcast")
            disconnected_connections.add(websocket)
        except Exception as e:
            logger.error(f"Error sending status update to WebSocket: {e}")
            disconnected_connections.add(websocket)
    
    # Clean up disconnected connections
    for websocket in disconnected_connections:
        status_connections.discard(websocket)
    
    logger.info(f"Successfully broadcasted agent status update for {agent_id}: {agent_connected} to {successful_sends} clients (cleaned up {len(disconnected_connections)} disconnected)")

# Register handlers with the connection manager
def register_status_handlers():
    """Register handlers to broadcast status updates when agents connect/disconnect."""
    
    async def on_agent_connect(agent_id: str, message: Dict):
        """Handle agent connection."""
        logger.info(f"Status handler: Agent {agent_id} connected - broadcasting status update")
        await broadcast_agent_status_update(agent_id, True)
    
    async def on_agent_disconnect(agent_id: str, message: Dict):
        """Handle agent disconnection."""
        logger.info(f"Status handler: Agent {agent_id} disconnected - broadcasting status update")
        await broadcast_agent_status_update(agent_id, False)
    
    # Register the handlers
    manager.register_message_handler("AGENT_CONNECTED", on_agent_connect)
    manager.register_message_handler("AGENT_DISCONNECTED", on_agent_disconnect)
    logger.info("Status handlers registered for AGENT_CONNECTED and AGENT_DISCONNECTED")

# Initialize handlers when module is imported
register_status_handlers()
