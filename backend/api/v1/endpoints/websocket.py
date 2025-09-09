# File: backend/api/v1/endpoints/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ws.connection_manager import manager  # Import our global manager

router = APIRouter()

# ... (imports) ...
import json


@router.websocket("/connections/ws/{agent_id}")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    await manager.connect(agent_id, websocket)
    try:
        # This loop now actively listens for responses from the agent.
        while True:
            response_str = await websocket.receive_text()
            response_data = json.loads(response_str)
            query_id = response_data.get("query_id")
            if query_id:
                print(f"<<< Received response for query_id '{query_id}' from agent '{agent_id}'")
                # Pass the response to the manager to be handled.
                manager.handle_response(query_id, response_data)
    except WebSocketDisconnect:
        manager.disconnect(agent_id)
