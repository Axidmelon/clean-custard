# File: agent-mongodb/main.py

import os
import asyncio
import time
import websockets
import json
import pymongo
from pymongo import MongoClient
import logging
from typing import Dict, Any, Optional, Union
from dotenv import load_dotenv

# Import the MongoSchemaDiscoverer tool
from schema_discoverer import MongoSchemaDiscoverer


# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Configuration ---
load_dotenv()

# Configuration from environment variables - no hardcoded defaults
BACKEND_WS_URL = os.getenv("BACKEND_WEBSOCKET_URI")
CONNECTION_ID = os.getenv("CONNECTION_ID")  # Database UUID for identification
AGENT_ID = os.getenv("AGENT_ID")  # Agent ID for WebSocket routing
MONGODB_CONFIG = {
    "connection_string": os.getenv("MONGODB_CONNECTION_STRING"),
    "database_name": os.getenv("MONGODB_DATABASE_NAME"),
    "collection_filter": os.getenv("MONGODB_COLLECTION_FILTER"),
}

# Validate required environment variables
required_vars = [
    "BACKEND_WEBSOCKET_URI",
    "CONNECTION_ID",
    "AGENT_ID",
    "MONGODB_CONNECTION_STRING",
    "MONGODB_DATABASE_NAME",
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.error("Please check your .env file and ensure all required variables are set")
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# --- Database Security and Query Functions ---


def is_safe_mongo_query(query: Dict[str, Any]) -> bool:
    """
    Check if a MongoDB query is safe and read-only.

    Args:
        query: MongoDB query dictionary to validate

    Returns:
        True if query is safe and read-only, False otherwise
    """
    # Block dangerous operations
    dangerous_operations = [
        'insert', 'update', 'delete', 'remove', 'drop', 'createIndex',
        'dropIndex', 'createCollection', 'dropCollection', 'renameCollection',
        'createUser', 'dropUser', 'grantRolesToUser', 'revokeRolesFromUser'
    ]
    
    # Check if query contains any dangerous operations
    query_str = str(query).lower()
    for operation in dangerous_operations:
        if operation in query_str:
            logger.warning(f"Blocked query containing dangerous operation: {operation}")
            return False
    
    # Block dangerous MongoDB operators
    dangerous_operators = [
        '$where', '$eval', '$regex', '$text', '$near', '$nearSphere',
        '$geoWithin', '$geoIntersects', '$geoNear'
    ]
    
    for operator in dangerous_operators:
        if operator in query_str:
            logger.warning(f"Blocked query containing dangerous operator: {operator}")
            return False
    
    return True


def execute_mongo_query(query: Dict[str, Any], collection_name: str) -> Dict[str, Any]:
    """
    Execute a read-only MongoDB query safely.

    Args:
        query: MongoDB query dictionary
        collection_name: Name of the collection to query

    Returns:
        Dictionary containing query results or error information
    """
    if not is_safe_mongo_query(query):
        return {"error": "SECURITY VIOLATION: Non-read-only query blocked", "query": query}

    try:
        client = MongoClient(MONGODB_CONFIG["connection_string"])
        db = client[MONGODB_CONFIG["database_name"]]
        collection = db[collection_name]
        
        logger.info(f"Executing MongoDB query on collection: {collection_name}")
        
        # Execute the query based on its type
        if "find" in query:
            # Find query
            find_query = query["find"]
            projection = query.get("projection", None)
            limit = query.get("limit", 100)  # Default limit for safety
            skip = query.get("skip", 0)
            sort = query.get("sort", None)
            
            cursor = collection.find(find_query, projection)
            
            if sort:
                cursor = cursor.sort(sort)
            if skip:
                cursor = cursor.skip(skip)
            if limit:
                cursor = cursor.limit(limit)
            
            results = list(cursor)
            
        elif "aggregate" in query:
            # Aggregation pipeline
            pipeline = query["aggregate"]
            cursor = collection.aggregate(pipeline)
            results = list(cursor)
            
        elif "count" in query:
            # Count query
            count_query = query["count"]
            result = collection.count_documents(count_query)
            results = [{"count": result}]
            
        elif "distinct" in query:
            # Distinct query
            field = query["distinct"]
            distinct_query = query.get("query", {})
            results = collection.distinct(field, distinct_query)
            results = [{"distinct_values": results}]
            
        else:
            return {"error": "Unsupported query type", "query": query}
        
        # Convert ObjectId to string for JSON serialization
        def convert_objectid(obj):
            if isinstance(obj, dict):
                return {k: convert_objectid(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_objectid(item) for item in obj]
            elif isinstance(obj, pymongo.ObjectId):
                return str(obj)
            else:
                return obj
        
        results = convert_objectid(results)
        
        return {
            "data": results,
            "row_count": len(results),
            "collection": collection_name
        }

    except pymongo.errors.PyMongoError as e:
        logger.error(f"MongoDB query failed: {e}")
        return {"error": f"MongoDB query failed: {e}", "query": query}
    except Exception as e:
        logger.error(f"Unexpected error executing query: {e}")
        return {"error": f"Unexpected error: {e}", "query": query}


def discover_database_schema() -> Union[Dict[str, Any], str]:
    """
    Discover the MongoDB database schema using MongoSchemaDiscoverer.

    Returns:
        Dictionary representation of the database schema on success,
        or error string on failure
    """
    try:
        logger.info("Starting MongoDB schema discovery...")
        
        # Validate MongoDB configuration first
        missing_config = [key for key, value in MONGODB_CONFIG.items() if not value and key != "collection_filter"]
        if missing_config:
            error_msg = f"Missing MongoDB configuration: {missing_config}"
            logger.error(error_msg)
            return f"Schema discovery failed: {error_msg}"
        
        # Get collection filter from environment variables
        collection_filter = MONGODB_CONFIG.get("collection_filter")
        if collection_filter:
            collection_filter = [name.strip() for name in collection_filter.split(",")]
            logger.info(f"Using collection filter: {collection_filter}")

        logger.info(f"Discovering schema for database: {MONGODB_CONFIG['database_name']}")
        
        # Use MongoSchemaDiscoverer
        discoverer = MongoSchemaDiscoverer(
            connection_string=MONGODB_CONFIG["connection_string"],
            database_name=MONGODB_CONFIG["database_name"],
            collection_filter=collection_filter
        )
        
        start_time = time.time()
        schema = discoverer.discover_schema()
        discovery_time = time.time() - start_time
        
        logger.info(f"✓ MongoDB schema discovery completed successfully in {discovery_time:.2f} seconds")
        return schema
            
    except Exception as e:
        logger.error(f"MongoDB schema discovery failed: {e}")
        return f"Schema discovery failed: {e}"


# --- Command Handler Functions ---


async def handle_mongo_query(
    websocket: websockets.WebSocketServerProtocol, command: Dict[str, Any]
) -> None:
    """
    Handle a MongoDB query request from the backend.

    Args:
        websocket: WebSocket connection
        command: Command dictionary containing query details
    """
    logger.info("Handling MongoDB query request")

    query = command.get("query")
    collection_name = command.get("collection_name")
    query_id = command.get("query_id")

    if not query or not collection_name or not query_id:
        logger.error("Missing 'query', 'collection_name', or 'query_id' in request")
        response = {
            "query_id": query_id,
            "status": "error",
            "error": "Missing required fields: query, collection_name, or query_id",
        }
        await websocket.send(json.dumps(response, default=str))
        return

    # Execute the query
    result_payload = execute_mongo_query(query, collection_name)

    # Check if query execution failed
    if "error" in result_payload:
        response = {
            "query_id": query_id,
            "status": "error",
            "error": result_payload["error"]
        }
    else:
        response = {
            "query_id": query_id,
            "status": "success",
            "data": result_payload.get("data", []),
            "row_count": result_payload.get("row_count", 0),
            "collection": result_payload.get("collection", collection_name)
        }

    await websocket.send(json.dumps(response, default=str))
    logger.info(f"MongoDB query response sent for query_id: {query_id}")


async def handle_schema_discovery(
    websocket: websockets.WebSocketServerProtocol, command: Dict[str, Any]
) -> None:
    """
    Handle a schema discovery request from the backend.

    Args:
        websocket: WebSocket connection
        command: Command dictionary
    """
    logger.info("Handling MongoDB schema discovery request")
    query_id = command.get("query_id")
    connection_id = command.get("payload", {}).get("connection_id")

    try:
        logger.info(f"Starting MongoDB schema discovery for connection: {connection_id}")
        
        # Discover the schema using our MongoDB discoverer
        schema_data = discover_database_schema()

        # Check if schema discovery was successful
        if isinstance(schema_data, str) and schema_data.startswith("Schema discovery failed"):
            # Schema discovery failed, return error
            logger.error(f"MongoDB schema discovery failed: {schema_data}")
            response = {
                "query_id": query_id,
                "status": "error",
                "error": schema_data
            }
        else:
            # Schema discovery successful
            logger.info("MongoDB schema discovery successful, sending response.")
            response = {
                "query_id": query_id,
                "status": "success",
                "schema": schema_data,  # This will be the dictionary
            }

    except Exception as e:
        # If anything goes wrong, build an error response
        logger.error(f"MongoDB schema discovery failed during handling: {e}")
        response = {
            "query_id": query_id,
            "status": "error",
            "error": f"MongoDB schema discovery failed: {str(e)}"
        }

    # Send the response back to the backend
    try:
        await websocket.send(json.dumps(response, default=str))
        logger.info(f"MongoDB schema discovery response sent for query_id: {query_id}")
    except Exception as e:
        logger.error(f"Failed to send MongoDB schema discovery response: {e}")


async def handle_ping(
    websocket: websockets.WebSocketServerProtocol, command: Dict[str, Any]
) -> None:
    """
    Handle a ping request to check agent health.

    Args:
        websocket: WebSocket connection
        command: Command dictionary
    """
    logger.debug("Handling ping request")

    response = {
        "type": "PONG",
        "payload": {
            "status": "healthy",
            "connection_id": CONNECTION_ID,
            "timestamp": asyncio.get_event_loop().time(),
        },
    }

    await websocket.send(json.dumps(response))
    logger.debug("Pong response sent")


# --- Main Agent Logic ---


class CustardMongoAgent:
    """
    Main MongoDB agent class that handles WebSocket communication with the backend.
    """

    def __init__(self):
        self.connection_id = CONNECTION_ID  # Database UUID for identification
        self.agent_id = AGENT_ID  # Agent ID for WebSocket routing
        self.backend_url = BACKEND_WS_URL
        self.running = False

        # Command handlers
        self.handlers = {
            "MONGO_QUERY_REQUEST": handle_mongo_query,
            "SCHEMA_DISCOVERY_REQUEST": handle_schema_discovery,
            "PING": handle_ping,
        }

    async def connect_to_backend(self) -> Optional[websockets.WebSocketServerProtocol]:
        """
        Establish connection to the backend.

        Returns:
            WebSocket connection or None if failed
        """
        try:
            # Use agent_id for WebSocket URL routing
            websocket_url = self.backend_url.replace("{agent_id}", self.agent_id)
            logger.info(f"Connecting to backend at: {websocket_url}")
            websocket = await websockets.connect(websocket_url)
            logger.info(f"✅ Successfully connected to Custard backend as MongoDB agent: {self.agent_id}")
            return websocket
        except Exception as e:
            logger.error(f"Failed to connect to backend: {e}")
            return None

    async def process_message(
        self, websocket: websockets.WebSocketServerProtocol, message: str
    ) -> None:
        """
        Process an incoming message from the backend.

        Args:
            websocket: WebSocket connection
            message: Raw message string
        """
        try:
            command = json.loads(message)
            command_type = command.get("type")

            logger.info(f"Received command: {command_type}")

            # Route to appropriate handler
            if command_type in self.handlers:
                await self.handlers[command_type](websocket, command)
            else:
                logger.warning(f"Unknown command type: {command_type}")
                # Send error response
                error_response = {
                    "query_id": command.get("query_id"),
                    "status": "error",
                    "error": f"Unknown command type: {command_type}",
                }
                await websocket.send(json.dumps(error_response))

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def run(self) -> None:
        """
        Main agent loop that connects and listens for commands.
        """
        self.running = True
        logger.info(f"Starting Custard MongoDB Agent: {self.agent_id} (Connection: {self.connection_id})")

        while self.running:
            websocket = await self.connect_to_backend()

            if websocket is None:
                logger.warning("Connection failed, retrying in 5 seconds...")
                await asyncio.sleep(5)
                continue

            try:
                # Listen for messages
                async for message in websocket:
                    await self.process_message(websocket, message)

            except websockets.exceptions.ConnectionClosed:
                logger.info("Connection to backend closed")
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
            finally:
                if websocket:
                    await websocket.close()

            # Wait before reconnecting
            if self.running:
                logger.info("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    def stop(self) -> None:
        """Stop the agent."""
        self.running = False
        logger.info("MongoDB Agent stop requested")


async def main():
    """Main entry point."""
    agent = CustardMongoAgent()

    try:
        await agent.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        agent.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
