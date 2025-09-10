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
            "message_count": 0,
        }
        logger.info(f"Agent '{agent_id}' connected. Total agents: {len(self.active_connections)}")
        
        # Emit agent connected event
        await self.handle_message(agent_id, {"type": "AGENT_CONNECTED"})

    def disconnect(self, agent_id: str) -> None:
        """
        Remove an agent's WebSocket connection.

        Args:
            agent_id: Unique identifier for the agent
        """
        if agent_id in self.active_connections:
            del self.active_connections[agent_id]
            self.connection_metadata.pop(agent_id, None)
            logger.info(
                f"Agent '{agent_id}' disconnected. Total agents: {len(self.active_connections)}"
            )
            
            # Emit agent disconnected event
            import asyncio
            asyncio.create_task(self.handle_message(agent_id, {"type": "AGENT_DISCONNECTED"}))

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
            logger.info(f"Currently connected agents: {list(self.active_connections.keys())}")
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

        # Handle PING messages directly (common agent health check)
        if message_type == "PING":
            await self.handle_ping(agent_id, message)
            return

        # Handle AGENT_CONNECTED messages directly (trigger automatic schema refresh)
        if message_type == "AGENT_CONNECTED":
            await self.handle_agent_connected(agent_id, message)
            # Don't return here - continue to call registered handlers too

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

    async def handle_ping(self, agent_id: str, message: Dict[str, Any]) -> None:
        """
        Handle a PING message from an agent by responding with PONG.

        Args:
            agent_id: ID of the agent that sent the ping
            message: The PING message data
        """
        logger.debug(f"Received PING from agent '{agent_id}'")
        
        # Create PONG response
        pong_response = {
            "type": "PONG",
            "payload": {
                "status": "healthy",
                "timestamp": time.time(),
                "agent_id": agent_id
            }
        }
        
        # Send PONG response back to agent
        success = await self.send_json_to_agent(pong_response, agent_id)
        if success:
            logger.debug(f"Sent PONG response to agent '{agent_id}'")
        else:
            logger.warning(f"Failed to send PONG response to agent '{agent_id}'")

    async def handle_agent_connected(self, agent_id: str, message: Dict[str, Any]) -> None:
        """
        Handle an AGENT_CONNECTED message by triggering automatic schema refresh.

        Args:
            agent_id: ID of the agent that connected
            message: The AGENT_CONNECTED message data
        """
        logger.info(f"Agent '{agent_id}' connected - triggering automatic schema refresh")
        
        # Add a small delay to ensure the WebSocket connection is fully established
        import asyncio
        await asyncio.sleep(1)
        
        try:
            # Import here to avoid circular imports
            from db.dependencies import get_db
            from db.models import Connection
            from sqlalchemy.orm import Session
            import uuid
            
            # Check if agent is still connected after the delay
            if not self.is_agent_connected(agent_id):
                logger.warning(f"Agent '{agent_id}' disconnected before schema refresh could start")
                return
            
            # Get database session
            db_gen = get_db()
            db: Session = next(db_gen)
            
            try:
                # Find the connection by agent_id
                connection = db.query(Connection).filter(Connection.agent_id == agent_id).first()
                
                if not connection:
                    logger.warning(f"No connection found for agent '{agent_id}' - skipping schema refresh")
                    return
                
                logger.info(f"Found connection '{connection.name}' for agent '{agent_id}' - starting schema refresh")
                
                # Create the schema discovery command
                command = {
                    "type": "SCHEMA_DISCOVERY_REQUEST",
                    "query_id": str(uuid.uuid4()),
                    "payload": {"connection_id": str(connection.id)},
                }
                
                # Send command to the agent and wait for a response
                # Use a generous timeout for schema discovery (no timeout on agent side)
                response = await self.send_query_to_agent(command, agent_id, timeout=120)
                
                if not response or response.get("status") != "success":
                    error_detail = response.get("error", "Agent did not return a valid schema.")
                    logger.error(f"Schema discovery failed for agent '{agent_id}': {error_detail}")
                    return
                
                # Now handle the database save with retry logic and progressive timeouts
                schema_data = response.get("schema")
                logger.info(f"Schema data received from agent: {type(schema_data)} - {schema_data}")
                
                if schema_data:
                    logger.info(f"Schema discovered successfully, saving to database...")
                    
                    # Try to save with progressive timeouts and retries
                    success = await self._save_schema_with_retry(db, connection, schema_data, agent_id)
                    
                    if success:
                        logger.info(f"Successfully cached schema for connection '{connection.name}' (agent: {agent_id})")
                    else:
                        logger.error(f"Failed to save schema for connection '{connection.name}' (agent: {agent_id}) after all retries")
                else:
                    logger.warning(f"No schema data received from agent '{agent_id}' - response: {response}")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error during automatic schema refresh for agent '{agent_id}': {e}")

    async def _save_schema_with_retry(self, db, connection, schema_data, agent_id):
        """
        Save schema data to the database with retry logic and progressive timeouts.
        
        Args:
            db: Database session
            connection: Connection object to update
            schema_data: Schema data to save
            agent_id: Agent identifier for logging
            
        Returns:
            bool: True if successful, False if all retries failed
        """
        # Progressive timeouts: 5s, 15s, 30s
        timeouts = [5.0, 15.0, 30.0]
        max_retries = len(timeouts)
        
        for attempt in range(max_retries):
            timeout = timeouts[attempt]
            logger.info(f"Attempt {attempt + 1}/{max_retries} to save schema (timeout: {timeout}s)")
            
            try:
                # Use asyncio.wait_for to timeout the database save operation
                await asyncio.wait_for(
                    self._save_schema_to_database(db, connection, schema_data, agent_id),
                    timeout=timeout
                )
                logger.info(f"Schema saved successfully on attempt {attempt + 1}")
                return True
                
            except asyncio.TimeoutError:
                logger.warning(f"Database save timed out on attempt {attempt + 1} (timeout: {timeout}s)")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in 2 seconds...")
                    await asyncio.sleep(2)
                else:
                    logger.error(f"All {max_retries} attempts timed out")
                    
            except Exception as e:
                logger.error(f"Database save failed on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in 2 seconds...")
                    await asyncio.sleep(2)
                else:
                    logger.error(f"All {max_retries} attempts failed")
        
        return False

    async def _save_schema_to_database(self, db, connection, schema_data, agent_id):
        """
        Save schema data to the database with proper error handling.
        
        Args:
            db: Database session
            connection: Connection object to update
            schema_data: Schema data to save
            agent_id: Agent identifier for logging
        """
        try:
            # Convert schema data to JSON string if it's a dict
            if isinstance(schema_data, dict):
                import json
                schema_json = json.dumps(schema_data)
            else:
                schema_json = schema_data
                
            # Update the connection with the schema data
            connection.db_schema_cache = schema_json
            db.commit()
            db.refresh(connection)
            
            logger.info(f"Schema saved to database for connection '{connection.name}' (agent: {agent_id})")
            
        except Exception as e:
            logger.error(f"Failed to save schema to database: {e}")
            db.rollback()
            raise

    def handle_response(self, query_id: str, data: Any) -> None:
        """
        Handle a response from an agent for a specific query.

        Args:
            query_id: Unique identifier for the query
            data: Response data from the agent
        """
        logger.info(f"Processing response for query '{query_id}': {data}")
        self.response_data[query_id] = data
        if query_id in self.response_events:
            self.response_events[query_id].set()
            logger.info(f"Response received for query '{query_id}': {data}")
        else:
            logger.warning(f"No event listener found for query '{query_id}' - response may be lost")

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
            response_data = self.response_data.pop(query_id, {"error": "No response data found"})
            logger.info(f"Response received for query '{query_id}': {response_data}")
            return response_data
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

    async def send_query_to_agent(
        self, query: Dict[str, Any], agent_id: str, timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Send a query to an agent and wait for the response.

        Args:
            query: Query data to send (should already contain query_id)
            agent_id: Target agent identifier
            timeout: Maximum time to wait for response

        Returns:
            Response from the agent or error message
        """
        # Extract query_id from the query (should already be set by caller)
        query_id = query.get("query_id")
        if not query_id:
            return {"error": "Query must contain a query_id"}

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

        avg_connection_time = (
            total_connection_time / total_connections if total_connections > 0 else 0
        )

        return {
            "total_connections": total_connections,
            "connected_agents": list(self.active_connections.keys()),
            "average_connection_time": avg_connection_time,
            "total_messages_received": sum(
                metadata.get("message_count", 0) for metadata in self.connection_metadata.values()
            ),
        }


# Create a singleton instance for the application
manager = ConnectionManager()
