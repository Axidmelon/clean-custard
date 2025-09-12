# File: agent-postgresql/main.py

import os
import asyncio
import time
import websockets
from websockets.protocol import State
import json
import psycopg2
import logging
from typing import Dict, Any, Optional, Union
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
    "sslmode": os.getenv("DB_SSLMODE", "require"),  # Use 'require' for Supabase
    "connect_timeout": 10,  # Connection timeout
    "application_name": "agent-postgresql",  # Application name for connection identification
    "gssencmode": "disable",  # Disable GSS encryption mode
    "options": "-c default_transaction_isolation=read committed",  # Set transaction isolation
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


def discover_database_schema() -> Union[Dict[str, Any], str]:
    """
    Discover the database schema using SchemaDiscoverer with SASL authentication fixes.

    Returns:
        Dictionary representation of the database schema on success,
        or error string on failure
    """
    try:
        logger.info("Starting database schema discovery...")
        
        # Validate database configuration first
        missing_config = [key for key, value in DB_CONFIG.items() if not value]
        if missing_config:
            error_msg = f"Missing database configuration: {missing_config}"
            logger.error(error_msg)
            return f"Schema discovery failed: {error_msg}"
        
        # Get schema configuration from environment variables
        schema_name = os.getenv("SCHEMA_NAME", "public")
        table_filter = os.getenv("TABLE_FILTER")
        if table_filter:
            table_filter = [table.strip() for table in table_filter.split(",")]
            logger.info(f"Using table filter: {table_filter}")

        logger.info(f"Discovering schema for database: {DB_CONFIG['dbname']}, schema: {schema_name}")
        
        # Use a single connection for schema discovery with retry logic to avoid SASL issues
        logger.info("Connecting to database for schema discovery...")
        max_retries = 3
        current_config = DB_CONFIG.copy()
        
        for attempt in range(max_retries):
            try:
                with psycopg2.connect(**current_config) as conn:
                    with conn.cursor() as cur:
                        # Test connection first
                        cur.execute("SELECT 1")
                        logger.info("✓ Database connection successful")
                        
                        # Use SchemaDiscoverer with existing connection to avoid multiple connections
                        discoverer = SchemaDiscoverer(
                            host=DB_CONFIG["host"],
                            port=DB_CONFIG["port"],
                            dbname=DB_CONFIG["dbname"],
                            user=DB_CONFIG["user"],
                            password=DB_CONFIG["password"],
                            schema_name=schema_name,
                            table_filter=table_filter
                        )
                        
                        start_time = time.time()
                        schema = discoverer.discover_schema_with_connection(conn)
                        discovery_time = time.time() - start_time
                        
                        logger.info(f"✓ Database schema discovery completed successfully in {discovery_time:.2f} seconds")
                        return schema
                            
            except psycopg2.OperationalError as e:
                error_str = str(e)
                if "duplicate SASL authentication request" in error_str:
                    logger.warning(f"Connection attempt {attempt + 1} failed with SASL error: {error_str}")
                    if attempt < max_retries - 1:
                        # Try alternative configuration on first retry
                        if attempt == 0:
                            logger.info("Trying alternative configuration...")
                            current_config = DB_CONFIG.copy()
                            current_config.update({
                                "sslmode": "prefer",
                                "gssencmode": "disable",
                                "connect_timeout": 30,
                            })
                        logger.warning("Retrying connection in 2 seconds...")
                        time.sleep(2)  # Wait 2 seconds before retry
                        continue
                    else:
                        logger.error("All connection attempts failed with SASL error")
                        raise
                else:
                    logger.error(f"Operational error: {error_str}")
                    raise
            except psycopg2.DatabaseError as e:
                logger.error(f"Database error: {e}")
                raise
            except psycopg2.Error as e:
                error_msg = f"Database connection failed: {e}"
                logger.error(error_msg)
                return f"Schema discovery failed: {error_msg}"
            
    except Exception as e:
        logger.error(f"Schema discovery failed: {e}")
        return f"Schema discovery failed: {e}"


# --- Command Handler Functions ---


async def handle_sql_query(
    websocket: Any, command: Dict[str, Any]
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
            "query_id": query_id,
            "status": "error",
            "error": "Missing required fields: sql or query_id",
        }
        await websocket.send(json.dumps(response, default=str))
        return

    # Execute the query
    result_payload = execute_sql_query(sql)

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
            "columns": result_payload.get("columns", []),
            "row_count": result_payload.get("row_count", 0)
        }

    await websocket.send(json.dumps(response, default=str))
    logger.info(f"SQL query response sent for query_id: {query_id}")


async def handle_schema_discovery(
    websocket: Any, command: Dict[str, Any]
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
    websocket: Any, command: Dict[str, Any]
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


class AgentPostgreSQL:
    """
    Main agent class that handles WebSocket communication with the backend.
    """

    def __init__(self):
        self.connection_id = CONNECTION_ID  # Database UUID for identification
        self.agent_id = AGENT_ID  # Agent ID for WebSocket routing
        self.backend_url = BACKEND_WS_URL
        self.running = False
        self.websocket = None
        self.heartbeat_task = None
        self.connection_retry_count = 0
        self.max_retry_count = 10
        self.retry_delay = 5  # Start with 5 seconds
        self.last_heartbeat = time.time()

        # Initialize schema discoverer
        self.schema_discoverer = SchemaDiscoverer(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            dbname=DB_CONFIG["dbname"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )

        # Command handlers
        self.handlers = {
            "SQL_QUERY_REQUEST": handle_sql_query,
            "SCHEMA_DISCOVERY_REQUEST": handle_schema_discovery,
            "PING": handle_ping,
        }

    async def connect_to_backend(self) -> Optional[Any]:
        """
        Establish connection to the backend with exponential backoff retry.

        Returns:
            WebSocket connection or None if failed
        """
        try:
            # Use agent_id for WebSocket URL routing
            websocket_url = self.backend_url.replace("{agent_id}", self.agent_id)
            logger.info(f"Connecting to backend at: {websocket_url}")
            
            # Set connection options for better stability
            websocket = await websockets.connect(
                websocket_url,
                ping_interval=20,  # Send ping every 20 seconds
                ping_timeout=10,   # Wait 10 seconds for pong
                close_timeout=10,  # Wait 10 seconds for close
                max_size=2**20,    # 1MB max message size
                max_queue=2**5     # 32 message queue size
            )
            
            self.websocket = websocket
            self.connection_retry_count = 0
            self.last_heartbeat = time.time()
            
            logger.info(f"✅ Successfully connected to Custard backend as agent: {self.agent_id}")
            return websocket
        except Exception as e:
            self.connection_retry_count += 1
            logger.error(f"Failed to connect to backend (attempt {self.connection_retry_count}): {e}")
            return None

    async def send_heartbeat(self) -> None:
        """
        Send periodic heartbeat to maintain connection.
        """
        while self.running and self.websocket:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                
                if self.websocket and self.websocket.state != State.CLOSED:
                    heartbeat_message = {
                        "type": "HEARTBEAT",
                        "agent_id": self.agent_id,
                        "timestamp": time.time(),
                        "connection_id": self.connection_id
                    }
                    
                    await self.websocket.send(json.dumps(heartbeat_message))
                    self.last_heartbeat = time.time()
                    logger.debug(f"Heartbeat sent for agent {self.agent_id}")
                else:
                    logger.warning("WebSocket closed, stopping heartbeat")
                    break
                    
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                break

    async def check_connection_health(self) -> bool:
        """
        Check if the WebSocket connection is healthy.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        if not self.websocket or self.websocket.state == State.CLOSED:
            return False
            
        # Check if we haven't received a response in too long
        time_since_heartbeat = time.time() - self.last_heartbeat
        if time_since_heartbeat > 60:  # 1 minute timeout
            logger.warning(f"No heartbeat response for {time_since_heartbeat:.1f} seconds")
            return False
            
        return True

    async def process_message(
        self, websocket: Any, message: str
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

            # Handle heartbeat responses
            if command_type == "PONG" or command_type == "HEARTBEAT_RESPONSE":
                self.last_heartbeat = time.time()
                logger.debug(f"Heartbeat response received for agent {self.agent_id}")
                return

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
        Main agent loop that connects and listens for commands with improved stability.
        """
        self.running = True
        logger.info(f"Starting Custard Agent: {self.agent_id} (Connection: {self.connection_id})")

        while self.running:
            try:
                # Connect to backend with exponential backoff
                websocket = await self.connect_to_backend()

                if websocket is None:
                    # Exponential backoff for connection failures
                    delay = min(self.retry_delay * (2 ** min(self.connection_retry_count, 5)), 300)  # Max 5 minutes
                    logger.warning(f"Connection failed, retrying in {delay} seconds... (attempt {self.connection_retry_count + 1})")
                    await asyncio.sleep(delay)
                    continue

                # Reset retry count on successful connection
                self.connection_retry_count = 0
                self.retry_delay = 5

                # Start heartbeat task
                self.heartbeat_task = asyncio.create_task(self.send_heartbeat())
                
                logger.info(f"Agent {self.agent_id} is now online and ready to receive commands")

                try:
                    # Listen for messages with timeout
                    while self.running:
                        try:
                            # Use asyncio.wait_for to add timeout to message receiving
                            message = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                            await self.process_message(websocket, message)
                            
                            # Check connection health periodically
                            if not await self.check_connection_health():
                                logger.warning("Connection health check failed, reconnecting...")
                                break
                                
                        except asyncio.TimeoutError:
                            logger.debug("No messages received in 60 seconds, checking connection health...")
                            if not await self.check_connection_health():
                                logger.warning("Connection appears unhealthy, reconnecting...")
                                break
                            continue

                except websockets.exceptions.ConnectionClosed as e:
                    logger.info(f"WebSocket connection closed: {e}")
                except Exception as e:
                    logger.error(f"Error in message loop: {e}")
                finally:
                    # Clean up heartbeat task
                    if self.heartbeat_task:
                        self.heartbeat_task.cancel()
                        try:
                            await self.heartbeat_task
                        except asyncio.CancelledError:
                            pass
                        self.heartbeat_task = None

                    # Close websocket connection
                    if websocket and websocket.state != State.CLOSED:
                        await websocket.close()
                    self.websocket = None

                # Brief delay before reconnecting
                if self.running:
                    logger.info("Preparing to reconnect...")
                    await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Fatal error in main loop: {e}")
                if self.running:
                    await asyncio.sleep(10)  # Wait longer on fatal errors

    def stop(self) -> None:
        """Stop the agent."""
        self.running = False
        logger.info("Agent stop requested")


async def main():
    """Main entry point."""
    agent = AgentPostgreSQL()

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
