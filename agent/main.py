# File: agent/main.py

import os
import asyncio
import time
import websockets
import json
import psycopg2
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Import the SchemaDiscoverer tool
from schema_discoverer import SchemaDiscoverer

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
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "sslmode": os.getenv("DB_SSLMODE", "prefer"),  # Default to 'prefer' if not set
}

# Validate required environment variables
required_vars = [
    "BACKEND_WEBSOCKET_URI",
    "CONNECTION_ID",
    "AGENT_ID",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
]

missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.error("Please check your .env file and ensure all required variables are set")
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# --- Database Security and Query Functions ---


def is_readonly_query(sql_query: str) -> bool:
    """
    Check if a SQL query is safe and read-only.

    Args:
        sql_query: SQL query string to validate

    Returns:
        True if query is safe and read-only, False otherwise
    """
    query_clean = sql_query.strip().lower()

    # Only allow SELECT statements
    if not query_clean.startswith("select"):
        return False

    # Block dangerous keywords - configurable via environment variable
    dangerous_keywords_str = os.getenv(
        "DANGEROUS_KEYWORDS",
        "drop,delete,insert,update,alter,create,truncate,grant,revoke,exec,execute,"
        "sp_,xp_,--,/*,*/",
    )
    dangerous_keywords = [keyword.strip() for keyword in dangerous_keywords_str.split(",")]

    for keyword in dangerous_keywords:
        if keyword in query_clean:
            logger.warning(f"Blocked query containing dangerous keyword: {keyword}")
            return False

    return True


def execute_sql_query(sql_query: str) -> Dict[str, Any]:
    """
    Execute a read-only SQL query safely.

    Args:
        sql_query: SQL query to execute

    Returns:
        Dictionary containing query results or error information
    """
    if not is_readonly_query(sql_query):
        return {"error": "SECURITY VIOLATION: Non-read-only query blocked", "query": sql_query}

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                logger.info(f"Executing query: {sql_query[:100]}...")
                cur.execute(sql_query)
                results = cur.fetchall()

                # Get column names
                column_names = [desc[0] for desc in cur.description] if cur.description else []

                return {"data": results, "columns": column_names, "row_count": len(results)}

    except psycopg2.Error as e:
        logger.error(f"Database query failed: {e}")
        return {"error": f"Database query failed: {e}", "query": sql_query}
    except Exception as e:
        logger.error(f"Unexpected error executing query: {e}")
        return {"error": f"Unexpected error: {e}", "query": sql_query}


def discover_database_schema() -> str:
    """
    Discover the database schema using SchemaDiscoverer.

    Returns:
        String representation of the database schema
    """
    try:
        logger.info("Starting database schema discovery...")
        
        # Validate database configuration first
        missing_config = [key for key, value in DB_CONFIG.items() if not value]
        if missing_config:
            error_msg = f"Missing database configuration: {missing_config}"
            logger.error(error_msg)
            return f"Schema discovery failed: {error_msg}"
        
        # Test database connection before schema discovery
        logger.info("Testing database connection...")
        try:
            with psycopg2.connect(**DB_CONFIG) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    logger.info("✓ Database connection successful")
        except psycopg2.Error as e:
            error_msg = f"Database connection failed: {e}"
            logger.error(error_msg)
            return f"Schema discovery failed: {error_msg}"
        
        # Get schema configuration from environment variables
        schema_name = os.getenv("SCHEMA_NAME", "public")
        table_filter = os.getenv("TABLE_FILTER")
        if table_filter:
            table_filter = [table.strip() for table in table_filter.split(",")]
            logger.info(f"Using table filter: {table_filter}")

        logger.info(f"Discovering schema for database: {DB_CONFIG['dbname']}, schema: {schema_name}")
        
        discoverer = SchemaDiscoverer(
            **DB_CONFIG, schema_name=schema_name, table_filter=table_filter
        )
        
        # No timeout - let schema discovery take as long as needed
        # The backend will handle timeouts for the save operation
        start_time = time.time()
        schema = discoverer.discover_schema()
        discovery_time = time.time() - start_time
        
        logger.info(f"✓ Database schema discovery completed successfully in {discovery_time:.2f} seconds")
        return schema
            
    except Exception as e:
        logger.error(f"Schema discovery failed: {e}")
        return f"Schema discovery failed: {e}"


# --- Command Handler Functions ---


async def handle_sql_query(
    websocket: websockets.WebSocketServerProtocol, command: Dict[str, Any]
) -> None:
    """
    Handle a SQL query request from the backend.

    Args:
        websocket: WebSocket connection
        command: Command dictionary containing query details
    """
    logger.info("Handling SQL query request")

    sql = command.get("sql")
    query_id = command.get("query_id")

    if not sql or not query_id:
        logger.error("Missing 'sql' or 'query_id' in request")
        response = {
            "type": "SQL_QUERY_RESPONSE",
            "query_id": query_id,
            "payload": {"error": "Missing required fields: sql or query_id"},
        }
        await websocket.send(json.dumps(response, default=str))
        return

    # Execute the query
    result_payload = execute_sql_query(sql)

    response = {"query_id": query_id, "status": "success", "result": result_payload.get("data", [])}

    await websocket.send(json.dumps(response, default=str))
    logger.info(f"SQL query response sent for query_id: {query_id}")


async def handle_schema_discovery(
    websocket: websockets.WebSocketServerProtocol, command: Dict[str, Any]
) -> None:
    """
    Handle a schema discovery request from the backend.

    Args:
        websocket: WebSocket connection
        command: Command dictionary
    """
    logger.info("Handling schema discovery request")
    query_id = command.get("query_id")
    connection_id = command.get("payload", {}).get("connection_id")

    try:
        logger.info(f"Starting schema discovery for connection: {connection_id}")
        
        # Discover the schema using our updated discoverer
        schema_data = discover_database_schema()

        # Check if schema discovery was successful
        if isinstance(schema_data, str) and schema_data.startswith("Schema discovery failed"):
            # Schema discovery failed, return error
            logger.error(f"Schema discovery failed: {schema_data}")
            response = {
                "query_id": query_id,
                "status": "error",
                "error": schema_data
            }
        else:
            # Schema discovery successful
            logger.info("Schema discovery successful, sending response.")
            response = {
                "query_id": query_id,
                "status": "success",
                "schema": schema_data,  # This will be the dictionary
            }

    except Exception as e:
        # If anything goes wrong, build an error response
        logger.error(f"Schema discovery failed during handling: {e}")
        response = {
            "query_id": query_id,
            "status": "error",
            "error": f"Schema discovery failed: {str(e)}"
        }

    # Send the response back to the backend
    try:
        await websocket.send(json.dumps(response, default=str))
        logger.info(f"Schema discovery response sent for query_id: {query_id}")
    except Exception as e:
        logger.error(f"Failed to send schema discovery response: {e}")


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


class CustardAgent:
    """
    Main agent class that handles WebSocket communication with the backend.
    """

    def __init__(self):
        self.connection_id = CONNECTION_ID  # Database UUID for identification
        self.agent_id = AGENT_ID  # Agent ID for WebSocket routing
        self.backend_url = BACKEND_WS_URL
        self.running = False

        # Command handlers
        self.handlers = {
            "SQL_QUERY_REQUEST": handle_sql_query,
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
            logger.info(f"✅ Successfully connected to Custard backend as agent: {self.agent_id}")
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
        logger.info(f"Starting Custard Agent: {self.agent_id} (Connection: {self.connection_id})")

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
        logger.info("Agent stop requested")


async def main():
    """Main entry point."""
    agent = CustardAgent()

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
