import uuid
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from db.dependencies import get_db
from db.models import Connection
from llm.services import TextToSQLService
from ws.connection_manager import manager, ConnectionManager
from schemas.connection import Connection as ConnectionSchema  # Import your Pydantic schema

router = APIRouter()

# --- Pydantic Models for Request and Response ---
from pydantic import BaseModel


class QueryRequest(BaseModel):
    connection_id: str
    question: str


class QueryResponse(BaseModel):
    answer: str
    sql_query: str


# --- Helper Function to format the agent's response ---
def format_agent_result(result: list) -> str:
    """
    Takes the raw list-of-lists result from the agent and formats it
    into a simple, user-friendly string.
    """
    if not result or not result[0]:
        return "The query returned no results."

    # For Phase 1, we expect a single value (e.g., [[1452]])
    # This logic can be expanded later for tables.
    final_value = result[0][0]
    return f"The result is: {final_value}"


# --- The Main API Endpoint ---
@router.post("/query", response_model=QueryResponse)
async def ask_question(request: QueryRequest = Body(...), db: Session = Depends(get_db)):
    """
    This endpoint orchestrates the entire "question-to-answer" flow.
    """
    # 1. Fetch the Connection and its Schema from our database
    # Convert string connection_id to UUID for database query
    try:
        connection_uuid = uuid.UUID(request.connection_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid connection ID format")
    
    db_connection = db.query(Connection).filter(Connection.id == connection_uuid).first()

    if not db_connection:
        raise HTTPException(status_code=404, detail="Connection not found.")

    if not db_connection.agent_id:
        raise HTTPException(status_code=400, detail="No agent ID found for this connection.")

    if not db_connection.db_schema_cache:
        raise HTTPException(
            status_code=400,
            detail="Database schema has not been cached for this connection yet. Please refresh the schema.",
        )

    # 2. Use the LLM service to generate the SQL query
    try:
        sql_service = TextToSQLService()
        generated_sql = sql_service.generate_sql(
            question=request.question,
            schema=str(db_connection.db_schema_cache),  # Convert schema to string
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate SQL: {e}")

    # 3. Send the generated SQL to the correct agent via the ConnectionManager
    query_payload = {
        "type": "SQL_QUERY_REQUEST",
        "query_id": str(uuid.uuid4()),
        "sql": generated_sql,
    }

    # Check if agent is connected before sending query
    if not manager.is_agent_connected(db_connection.agent_id):
        raise HTTPException(
            status_code=503, 
            detail=f"Agent '{db_connection.agent_id}' is not connected. Please ensure the agent is running and connected."
        )

    try:
        agent_response = await manager.send_query_to_agent(
            query=query_payload, agent_id=db_connection.agent_id
        )
    except Exception as e:
        # This could be a timeout or if the agent is not connected
        raise HTTPException(status_code=504, detail=f"Failed to get response from agent: {e}")

    if agent_response.get("status") != "success":
        error_detail = agent_response.get("error", "Unknown agent error.")
        raise HTTPException(status_code=502, detail=f"Agent returned an error: {error_detail}")

    # 4. Format the raw result from the agent into a human-readable answer
    final_answer = format_agent_result(agent_response.get("result", []))

    # 5. Return the final response to the user
    return QueryResponse(answer=final_answer, sql_query=generated_sql)
