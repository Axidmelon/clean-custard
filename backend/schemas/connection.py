# schemas/connection.py
import uuid
from pydantic import BaseModel
from typing import Optional

# --- Schema for creating a connection (INPUT) ---
# The user provides a name and database type.
class ConnectionCreate(BaseModel):
    name: str
    db_type: str

# --- Base schema for a connection (shared properties) ---
class ConnectionBase(ConnectionCreate):
    id: uuid.UUID
    db_type: str
    status: str

# --- Main schema for a connection (OUTPUT) ---
# This is the full model that we will send back to the user.
# It includes all the fields from the database.
class Connection(ConnectionBase):
    api_key: Optional[str] = None  # Only included when creating a new connection
    agent_id: Optional[str] = None  # Unique agent identifier for WebSocket routing
    websocket_url: Optional[str] = None  # WebSocket URL for agent connection
    
    class Config:
        # This tells Pydantic to read the data even if it's not a dict,
        # but a SQLAlchemy model object.
        from_attributes = True