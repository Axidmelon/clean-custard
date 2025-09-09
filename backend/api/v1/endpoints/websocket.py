# File: backend/api/v1/endpoints/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ws.connection_manager import manager  # Import our global manager

router = APIRouter()

# ... (imports) ...
import json


@router.websocket("/connections/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for agent connections.

    This endpoint handles:
    - Agent connection establishment
    - Message routing and processing
    - Connection cleanup on disconnect

    Args:
        websocket: WebSocket connection object
        agent_id: Unique identifier for the agent
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"WebSocket connection attempt from agent: {agent_id}")

    try:
        # Accept the connection
        await manager.connect(agent_id, websocket)

        # Listen for messages from the agent
        await manager.listen_for_messages(agent_id)

    except WebSocketDisconnect:
        logger.info(f"Agent {agent_id} disconnected")
        manager.disconnect(agent_id)
    except Exception as e:
        logger.error(f"Error in WebSocket connection for agent {agent_id}: {e}")
        manager.disconnect(agent_id)
    finally:
        # Ensure cleanup
        if manager.is_agent_connected(agent_id):
            manager.disconnect(agent_id)
