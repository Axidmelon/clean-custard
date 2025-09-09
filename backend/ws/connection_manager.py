# File: backend/ws/connection_manager.py

import asyncio
import json
import logging
import time
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any, Optional, Callable
from contextlib import asynccontextmanager

# Set up logging
logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for agents and handles request-response patterns.
    
    This class provides:
    - WebSocket connection management
    - Message sending to agents
    - Asynchronous request-response handling with timeouts
    - Response tracking and cleanup
    - Message routing and event handling
    """
    
    def __init__(self):
        # Active WebSocket connections: {agent_id: websocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Response tracking for async request-response patterns
        self.response_events: Dict[str, asyncio.Event] = {}
        self.response_data: Dict[str, Any] = {}
        
        # Message handlers for different message types
        self.message_handlers: Dict[str, Callable] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, agent_id: str, websocket: WebSocket) -> None:
        """
        Accept a new WebSocket connection from an agent.
        
        Args:
            agent_id: Unique identifier for the agent
            websocket: WebSocket connection object
        """
        await websocket.accept()
        self.active_connections[agent_id] = websocket
        self.connection_metadata[agent_id] = {
            "connected_at": time.time(),
            "last_activity": time.time(),
            "message_count": 0
        }
        logger.info(f"Agent '{agent_id}' connected. Total agents: {len(self.active_connections)}")
    
    def disconnect(self, agent_id: str) -> None:
        """
        Remove an agent's WebSocket connection.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
            self.connection_metadata.pop(agent_id, None)
            logger.info(f"Agent '{agent_id}' disconnected. Total agents: {len(self.active_connections)}")
    
    async def send_json_to_agent(self, message: Dict[str, Any], agent_id: str) -> bool:
        """
        Send a JSON message to a specific agent.
        
        Args:
            message: Dictionary to send as JSON
            agent_id: Target agent identifier
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if agent_id not in self.active_connections:
            logger.warning(f"Agent '{agent_id}' not found for message sending")
            return False
        
        try:
            websocket = self.active_connections[agent_id]
            await websocket.send_json(message)
            logger.debug(f"Sent JSON to '{agent_id}': {message}")
            return True
        except WebSocketDisconnect:
            logger.warning(f"WebSocket disconnected for agent '{agent_id}' during send")
            self.disconnect(agent_id)
            return False
        except Exception as e:
            logger.error(f"Error sending message to '{agent_id}': {e}")
            return False
    
    async def send_text_to_agent(self, message: str, agent_id: str) -> bool:
        """
        Send a text message to a specific agent.
        
        Args:
            message: Text message to send
            agent_id: Target agent identifier
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        if agent_id not in self.active_connections:
            logger.warning(f"Agent '{agent_id}' not found for text sending")
            return False
        
        try:
            websocket = self.active_connections[agent_id]
            await websocket.send_text(message)
            logger.debug(f"Sent text to '{agent_id}': {message}")
            return True
        except WebSocketDisconnect:
            logger.warning(f"WebSocket disconnected for agent '{agent_id}' during text send")
            self.disconnect(agent_id)
            return False
        except Exception as e:
            logger.error(f"Error sending text to '{agent_id}': {e}")
            return False
    
    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Function to call when message is received
        """
        self.message_handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    async def handle_message(self, agent_id: str, message: Dict[str, Any]) -> None:
        """
        Handle an incoming message from an agent.
        
        Args:
            agent_id: ID of the agent that sent the message
            message: Parsed message data
        """
        # Update connection metadata
        if agent_id in self.connection_metadata:
            self.connection_metadata[agent_id]["last_activity"] = time.time()
            self.connection_metadata[agent_id]["message_count"] += 1
        
        message_type = message.get("type")
        logger.debug(f"Handling message from '{agent_id}': {message_type}")
        
        # Check for response to a specific query
        if "query_id" in message:
            self.handle_response(message["query_id"], message)
        
        # Route to specific handler if registered
        if message_type in self.message_handlers:
            try:
                await self.message_handlers[message_type](agent_id, message)
            except Exception as e:
                logger.error(f"Error in message handler for '{message_type}': {e}")
        else:
            logger.debug(f"No handler registered for message type: {message_type}")
    
    def handle_response(self, query_id: str, data: Any) -> None:
        """
        Handle a response from an agent for a specific query.
        
        Args:
            query_id: Unique identifier for the query
            data: Response data from the agent
        """
        self.response_data[query_id] = data
        if query_id in self.response_events:
            self.response_events[query_id].set()
            logger.info(f"Response received for query '{query_id}': {data}")
    
    async def wait_for_response(self, query_id: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Wait for a response from an agent for a specific query.
        
        Args:
            query_id: Unique identifier for the query
            timeout: Maximum time to wait in seconds
            
        Returns:
            Response data or error message if timeout occurs
        """
        event = asyncio.Event()
        self.response_events[query_id] = event
        
        try:
            logger.info(f"Waiting for response for query '{query_id}' (timeout: {timeout}s)...")
            await asyncio.wait_for(event.wait(), timeout=timeout)
            return self.response_data.pop(query_id, {"error": "No response data found"})
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for response to query '{query_id}'")
            return {"error": "Request timed out"}
        finally:
            # Clean up tracking data
            self.response_events.pop(query_id, None)
            self.response_data.pop(query_id, None)
    
    async def listen_for_messages(self, agent_id: str) -> None:
        """
        Listen for incoming messages from a specific agent.
        
        Args:
            agent_id: ID of the agent to listen to
        """
        websocket = self.active_connections.get(agent_id)
        if not websocket:
            logger.warning(f"No WebSocket connection found for agent '{agent_id}'")
            return

        try:
            while True:
                # Receive message from agent
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle the message
                await self.handle_message(agent_id, message)
                
        except WebSocketDisconnect:
            logger.info(f"Agent '{agent_id}' disconnected")
            self.disconnect(agent_id)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received from agent '{agent_id}': {e}")
        except Exception as e:
            logger.error(f"Error listening to agent '{agent_id}': {e}")
            self.disconnect(agent_id)
    
    def get_connected_agents(self) -> list[str]:
        """
        Get a list of currently connected agent IDs.
        
        Returns:
            List of connected agent identifiers
        """
        return list(self.active_connections.keys())
    
    def is_agent_connected(self, agent_id: str) -> bool:
        """
        Check if a specific agent is connected.
        
        Args:
            agent_id: Agent identifier to check
            
        Returns:
            True if agent is connected, False otherwise
        """
        return agent_id in self.active_connections
    
    def get_connection_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get connection metadata for a specific agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Connection metadata or None if not found
        """
        return self.connection_metadata.get(agent_id)
    
    async def broadcast_message(self, message: Dict[str, Any]) -> int:
        """
        Send a message to all connected agents.
        
        Args:
            message: Message to broadcast
            
        Returns:
            Number of agents the message was sent to
        """
        sent_count = 0
        for agent_id in list(self.active_connections.keys()):
            if await self.send_json_to_agent(message, agent_id):
                sent_count += 1
        logger.info(f"Broadcast message sent to {sent_count} agents")
        return sent_count
    
    async def send_query_to_agent(self, query: Dict[str, Any], agent_id: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Send a query to an agent and wait for the response.
        
        Args:
            query: Query data to send
            agent_id: Target agent identifier
            timeout: Maximum time to wait for response
            
        Returns:
            Response from the agent or error message
        """
        # Generate unique query ID
        query_id = f"query_{time.time()}_{agent_id}"
        query["query_id"] = query_id
        
        # Send the query
        success = await self.send_json_to_agent(query, agent_id)
        if not success:
            return {"error": "Failed to send query to agent"}
        
        # Wait for response
        return await self.wait_for_response(query_id, timeout)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about current connections.
        
        Returns:
            Dictionary with connection statistics
        """
        current_time = time.time()
        total_connections = len(self.active_connections)
        
        # Calculate average connection time
        total_connection_time = 0
        for metadata in self.connection_metadata.values():
            total_connection_time += current_time - metadata["connected_at"]
        
        avg_connection_time = total_connection_time / total_connections if total_connections > 0 else 0
        
        return {
            "total_connections": total_connections,
            "connected_agents": list(self.active_connections.keys()),
            "average_connection_time": avg_connection_time,
            "total_messages_received": sum(
                metadata.get("message_count", 0) 
                for metadata in self.connection_metadata.values()
            )
        }


# Create a singleton instance for the application
manager = ConnectionManager()