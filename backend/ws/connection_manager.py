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
        
        # Also directly trigger status broadcast to ensure frontend gets updated
        await self._broadcast_agent_status_update(agent_id, True)

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
            
            # Also directly trigger status broadcast to ensure frontend gets updated
            asyncio.create_task(self._broadcast_agent_status_update(agent_id, False))

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
        logger.info(f"Handling message from '{agent_id}': {message_type}")
        logger.info(f"Message content: {message}")

        # Handle PING messages directly (common agent health check)
        if message_type == "PING":
            await self.handle_ping(agent_id, message)
            return

        # Handle AGENT_CONNECTED messages directly (trigger automatic schema refresh)
        if message_type == "AGENT_CONNECTED":
            await self.handle_agent_connected(agent_id, message)
            # Don't return here - continue to call registered handlers too

        # Check for response to a specific query - THIS IS CRITICAL FOR SCHEMA DISCOVERY
        if "query_id" in message:
            query_id = message["query_id"]
            logger.info(f"Processing response for query_id '{query_id}' from agent '{agent_id}'")
            self.handle_response(query_id, message)
            
            # Special handling for late schema discovery responses
            if (message.get("status") == "success" and 
                "schema" in message and 
                query_id not in self.response_events):
                logger.warning(f"Late schema discovery response received for query '{query_id}' - attempting to process")
                # Try to process the schema even if the original request timed out
                await self._handle_late_schema_response(agent_id, message)
        else:
            logger.debug(f"No query_id in message from agent '{agent_id}': {message}")

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
        
        # Check if agent is still connected after the delay
        if not self.is_agent_connected(agent_id):
            logger.warning(f"Agent '{agent_id}' disconnected before schema refresh could start")
            return
        
        # Import here to avoid circular imports
        from db.dependencies import get_db
        from db.models import Connection
        from sqlalchemy.orm import Session
        import uuid
        
        # Get database session with proper error handling
        db_gen = None
        db: Session = None
        
        try:
            db_gen = get_db()
            db = next(db_gen)
            logger.info(f"Database session created for agent '{agent_id}'")
            
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
            
            logger.info(f"Sending schema discovery command: {command}")
            
            # Send command to the agent and wait for a response
            # Use a reasonable timeout for schema discovery (agent responds in ~3 seconds, but allow buffer)
            response = await self.send_query_to_agent(command, agent_id, timeout=15)
            
            logger.info(f"Schema discovery response received: {response}")
            
            if not response or response.get("status") != "success":
                error_detail = response.get("error", "Agent did not return a valid schema.")
                logger.error(f"Schema discovery failed for agent '{agent_id}': {error_detail}")
                return
            
            # Now handle the database save with retry logic and progressive timeouts
            schema_data = response.get("schema")
            logger.info(f"Schema data received from agent: type={type(schema_data)}")
            
            if schema_data:
                logger.info(f"Schema discovered successfully, saving to database...")
                
                # Try to save with progressive timeouts and retries
                success = await self._save_schema_with_retry(db, connection, schema_data, agent_id)
                
                if success:
                    logger.info(f"Successfully cached schema for connection '{connection.name}' (agent: {agent_id})")
                else:
                    logger.error(f"Failed to save schema for connection '{connection.name}' (agent: {agent_id}) after all retries")
                    
                    # Try fallback save mechanism
                    logger.info(f"Attempting fallback schema save for agent '{agent_id}'")
                    fallback_success = await self.save_schema_fallback(agent_id, schema_data)
                    
                    if fallback_success:
                        logger.info(f"Fallback schema save successful for agent '{agent_id}'")
                    else:
                        logger.error(f"Both main and fallback schema save failed for agent '{agent_id}'")
            else:
                logger.warning(f"No schema data received from agent '{agent_id}' - response: {response}")
                
        except Exception as e:
            logger.error(f"Error during automatic schema refresh for agent '{agent_id}': {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        finally:
            # Ensure database session is properly closed
            if db:
                try:
                    db.close()
                    logger.info(f"Database session closed for agent '{agent_id}'")
                except Exception as e:
                    logger.error(f"Error closing database session for agent '{agent_id}': {e}")
            elif db_gen:
                try:
                    db_gen.close()
                    logger.info(f"Database generator closed for agent '{agent_id}'")
                except Exception as e:
                    logger.error(f"Error closing database generator for agent '{agent_id}': {e}")

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
        
        logger.info(f"Starting schema save with retry logic for connection '{connection.name}' (agent: {agent_id})")
        logger.info(f"Schema data type: {type(schema_data)}, size: {len(str(schema_data)) if schema_data else 0}")
        
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
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in 2 seconds...")
                    await asyncio.sleep(2)
                else:
                    logger.error(f"All {max_retries} attempts failed")
        
        logger.error(f"Schema save failed after all {max_retries} attempts for connection '{connection.name}' (agent: {agent_id})")
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
            logger.info(f"Starting database save for connection '{connection.name}' (agent: {agent_id})")
            logger.info(f"Connection ID: {connection.id}, Current schema cache: {connection.db_schema_cache}")
            
            # The db_schema_cache column is JSON type, so we need to ensure proper JSON format
            # Convert to JSON string if it's a dict, or validate if it's already a string
            if isinstance(schema_data, str):
                import json
                try:
                    # Validate that it's proper JSON by parsing it
                    schema_dict = json.loads(schema_data)
                    logger.info(f"Validated schema JSON string: type={type(schema_dict)}")
                    # Store as the original JSON string since database expects JSON format
                    schema_to_store = schema_data
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse schema JSON string: {e}")
                    raise
            elif isinstance(schema_data, dict):
                import json
                # Convert dict to JSON string for database storage
                schema_to_store = json.dumps(schema_data)
                logger.info(f"Converted schema dict to JSON string: length={len(schema_to_store)}")
            else:
                logger.error(f"Invalid schema data type: {type(schema_data)}")
                raise ValueError(f"Invalid schema data type: {type(schema_data)}")
            
            # Validate schema data before saving
            if not schema_to_store:
                logger.error("Schema data is empty or None")
                raise ValueError("Schema data is empty or None")
            
            # Update the connection with the schema data (store as JSON string)
            logger.info(f"Updating connection '{connection.name}' with schema data...")
            connection.db_schema_cache = schema_to_store
            
            # Commit the changes
            logger.info(f"Committing schema changes to database...")
            db.commit()
            
            # Refresh the connection object to get updated data
            logger.info(f"Refreshing connection object...")
            db.refresh(connection)
            
            # Verify the save was successful
            if connection.db_schema_cache:
                logger.info(f"Schema successfully saved to database for connection '{connection.name}' (agent: {agent_id})")
                logger.info(f"Schema cache now contains: {type(connection.db_schema_cache)} with length {len(connection.db_schema_cache) if isinstance(connection.db_schema_cache, str) else 'unknown'}")
                # Log a preview of the stored JSON
                if isinstance(connection.db_schema_cache, str) and len(connection.db_schema_cache) > 100:
                    logger.info(f"Schema JSON preview: {connection.db_schema_cache[:100]}...")
                else:
                    logger.info(f"Schema JSON content: {connection.db_schema_cache}")
            else:
                logger.error(f"Schema save verification failed - db_schema_cache is still None")
                raise ValueError("Schema save verification failed")
            
        except Exception as e:
            logger.error(f"Failed to save schema to database: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                db.rollback()
                logger.info("Database transaction rolled back")
            except Exception as rollback_error:
                logger.error(f"Failed to rollback database transaction: {rollback_error}")
            raise

    def handle_response(self, query_id: str, data: Any) -> None:
        """
        Handle a response from an agent for a specific query.

        Args:
            query_id: Unique identifier for the query
            data: Response data from the agent
        """
        logger.info(f"Processing response for query '{query_id}': {data}")
        
        # Validate response data structure
        if not isinstance(data, dict):
            logger.error(f"Invalid response data type for query '{query_id}': {type(data)}")
            return
            
        # Check for required fields in response
        if "status" not in data:
            logger.warning(f"Response missing 'status' field for query '{query_id}': {data}")
        
        # Log response details for debugging
        response_status = data.get("status", "unknown")
        logger.info(f"Response status for query '{query_id}': {response_status}")
        
        if response_status == "success":
            schema_data = data.get("schema")
            if schema_data:
                logger.info(f"Schema data received for query '{query_id}': type={type(schema_data)}, size={len(str(schema_data)) if schema_data else 0}")
            else:
                logger.warning(f"No schema data in successful response for query '{query_id}'")
        elif response_status == "error":
            error_msg = data.get("error", "Unknown error")
            logger.error(f"Error response for query '{query_id}': {error_msg}")
        
        # Store response data
        self.response_data[query_id] = data
        
        # Notify waiting coroutines
        if query_id in self.response_events:
            self.response_events[query_id].set()
            logger.info(f"Response event set for query '{query_id}' - waiting coroutines will be notified")
        else:
            logger.warning(f"No event listener found for query '{query_id}' - response may be lost")
            logger.info(f"Currently tracked queries: {list(self.response_events.keys())}")
            logger.info(f"Currently stored responses: {list(self.response_data.keys())}")

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
        
        logger.info(f"Setting up response tracking for query '{query_id}' (timeout: {timeout}s)")
        logger.info(f"Current tracked queries before wait: {list(self.response_events.keys())}")

        try:
            logger.info(f"Waiting for response for query '{query_id}' (timeout: {timeout}s)...")
            await asyncio.wait_for(event.wait(), timeout=timeout)
            
            # Get response data
            response_data = self.response_data.pop(query_id, {"error": "No response data found"})
            
            # Validate response
            if "error" in response_data and response_data["error"] == "No response data found":
                logger.error(f"Response data not found for query '{query_id}' despite event being set")
                logger.info(f"Available response data keys: {list(self.response_data.keys())}")
                return response_data
            
            logger.info(f"Response received for query '{query_id}': status={response_data.get('status', 'unknown')}")
            
            # Log schema data details if present
            if response_data.get("status") == "success" and "schema" in response_data:
                schema = response_data["schema"]
                logger.info(f"Schema data in response: type={type(schema)}, keys={list(schema.keys()) if isinstance(schema, dict) else 'N/A'}")
            
            return response_data
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for response to query '{query_id}' after {timeout}s")
            logger.info(f"Response events still active: {list(self.response_events.keys())}")
            logger.info(f"Response data still available: {list(self.response_data.keys())}")
            return {"error": "Request timed out"}
        finally:
            # Clean up tracking data
            self.response_events.pop(query_id, None)
            self.response_data.pop(query_id, None)
            logger.info(f"Cleaned up tracking data for query '{query_id}'")

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
            logger.error("Query must contain a query_id")
            return {"error": "Query must contain a query_id"}

        logger.info(f"Sending query to agent '{agent_id}': query_id={query_id}, type={query.get('type')}")
        logger.info(f"Query payload: {query}")

        # Send the query
        success = await self.send_json_to_agent(query, agent_id)
        if not success:
            logger.error(f"Failed to send query to agent '{agent_id}'")
            return {"error": "Failed to send query to agent"}

        logger.info(f"Query sent successfully to agent '{agent_id}', waiting for response...")

        # Wait for response
        response = await self.wait_for_response(query_id, timeout)
        
        logger.info(f"Query '{query_id}' completed with status: {response.get('status', 'unknown')}")
        return response

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

    async def _broadcast_agent_status_update(self, agent_id: str, agent_connected: bool):
        """
        Broadcast agent status update to all connected status WebSocket clients.
        This is a direct method to ensure status updates are sent immediately.
        """
        try:
            # Import here to avoid circular imports
            from api.v1.endpoints.status_websocket import broadcast_agent_status_update
            await broadcast_agent_status_update(agent_id, agent_connected)
        except Exception as e:
            logger.error(f"Failed to broadcast agent status update for {agent_id}: {e}")

    async def _handle_late_schema_response(self, agent_id: str, message: Dict[str, Any]) -> None:
        """
        Handle a late schema discovery response that arrived after timeout.
        
        Args:
            agent_id: Agent identifier
            message: The late response message containing schema data
        """
        try:
            logger.info(f"Processing late schema response for agent '{agent_id}'")
            
            schema_data = message.get("schema")
            if not schema_data:
                logger.warning(f"No schema data in late response for agent '{agent_id}'")
                return
            
            # Try to save the schema using fallback method
            success = await self.save_schema_fallback(agent_id, schema_data)
            
            if success:
                logger.info(f"Successfully processed late schema response for agent '{agent_id}'")
            else:
                logger.error(f"Failed to process late schema response for agent '{agent_id}'")
                
        except Exception as e:
            logger.error(f"Error handling late schema response for agent '{agent_id}': {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    async def save_schema_fallback(self, agent_id: str, schema_data: Dict[str, Any]) -> bool:
        """
        Fallback method to save schema data directly to the database.
        This can be called when the automatic schema refresh fails.
        
        Args:
            agent_id: Agent identifier
            schema_data: Schema data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Using fallback schema save for agent '{agent_id}'")
        
        try:
            # Import here to avoid circular imports
            from db.dependencies import get_db
            from db.models import Connection
            
            # Get database session
            db_gen = get_db()
            db = next(db_gen)
            
            try:
                # Find the connection by agent_id
                connection = db.query(Connection).filter(Connection.agent_id == agent_id).first()
                
                if not connection:
                    logger.error(f"No connection found for agent '{agent_id}' in fallback save")
                    return False
                
                logger.info(f"Found connection '{connection.name}' for fallback schema save")
                
                # Ensure schema data is in proper JSON format for database storage
                if isinstance(schema_data, dict):
                    import json
                    schema_to_store = json.dumps(schema_data)
                    logger.info(f"Converted schema dict to JSON string for fallback save")
                elif isinstance(schema_data, str):
                    # Validate JSON format
                    import json
                    try:
                        json.loads(schema_data)
                        schema_to_store = schema_data
                        logger.info(f"Using validated JSON string for fallback save")
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON string in fallback save: {e}")
                        return False
                else:
                    logger.error(f"Invalid schema data type for fallback save: {type(schema_data)}")
                    return False
                
                # Save schema data directly
                connection.db_schema_cache = schema_to_store
                db.commit()
                db.refresh(connection)
                
                # Verify save
                if connection.db_schema_cache:
                    logger.info(f"Fallback schema save successful for connection '{connection.name}'")
                    return True
                else:
                    logger.error(f"Fallback schema save verification failed for connection '{connection.name}'")
                    return False
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Fallback schema save failed for agent '{agent_id}': {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False


# Create a singleton instance for the application
manager = ConnectionManager()
