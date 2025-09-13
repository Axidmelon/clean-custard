import uuid
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional

from db.dependencies import get_db
from db.models import Connection
from llm.services import TextToSQLService
from ws.connection_manager import manager, ConnectionManager
from schemas.connection import Connection as ConnectionSchema  # Import your Pydantic schema

router = APIRouter()

# --- Pydantic Models for Request and Response ---
from pydantic import BaseModel


class QueryRequest(BaseModel):
    connection_id: Optional[str] = None
    file_id: Optional[str] = None
    question: str
    data_source: str = "auto"  # "auto", "database", "csv", or "csv_sql"
    user_preference: Optional[str] = None  # "sql" or "python" for user preference


class QueryResponse(BaseModel):
    answer: str
    sql_query: str
    data: list = []
    columns: list = []
    row_count: int = 0


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
    Supports AI-powered intelligent routing with these data sources:
    - "auto": AI agent decides the best service automatically
    - "database": Traditional database queries via agents
    - "csv": CSV data analysis using pandas operations
    - "csv_sql": CSV data analysis using SQL queries on in-memory SQLite
    """
    # Use AI agent for intelligent routing if data_source is "auto"
    if request.data_source == "auto":
        return await handle_ai_routing(request, db)
    
    # Route to appropriate handler based on explicit data source
    if request.data_source == "csv":
        return await handle_data_analysis_query(request, db)
    elif request.data_source == "csv_sql":
        return await handle_csv_sql_query(request, db)
    else:
        return await handle_database_query(request, db)

async def handle_ai_routing(request: QueryRequest, db: Session) -> QueryResponse:
    """
    Handle AI-powered intelligent routing using the AI routing agent.
    """
    from services.ai_routing_agent import ai_routing_agent, AnalysisContext
    from db.models import UploadedFile
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🤖 AI Agent processing question: {request.question[:100]}...")
        
        # Get file information if file_id is provided
        file_size = None
        if request.file_id:
            uploaded_file = db.query(UploadedFile).filter(
                UploadedFile.id == request.file_id
            ).first()
            
            if uploaded_file:
                # Estimate file size (this is approximate)
                file_size = uploaded_file.file_size if hasattr(uploaded_file, 'file_size') else None
        
        # Create analysis context
        context = AnalysisContext(
            question=request.question,
            file_size=file_size,
            data_source="csv" if request.file_id else "database",
            user_preference=request.user_preference
        )
        
        # Get AI recommendation
        ai_result = await ai_routing_agent.analyze_and_route(request.question, context)
        
        recommended_service = ai_result["recommended_service"]
        reasoning = ai_result["reasoning"]
        confidence = ai_result["confidence"]
        ai_analysis = ai_result.get("ai_analysis", "unknown")
        
        logger.info(f"🤖 AI Agent recommendation: {recommended_service} (confidence: {confidence:.2f})")
        logger.info(f"🧠 AI Analysis: {ai_analysis}")
        logger.info(f"💭 AI Reasoning: {reasoning}")
        
        # Route to the AI-recommended service
        if recommended_service == "csv":
            logger.info("🤖 AI routing to CSV pandas analysis")
            return await handle_data_analysis_query(request, db)
        elif recommended_service == "csv_sql":
            logger.info("🤖 AI routing to CSV SQL analysis")
            return await handle_csv_sql_query(request, db)
        elif recommended_service == "database":
            logger.info("🤖 AI routing to database analysis")
            return await handle_database_query(request, db)
        else:
            # Fallback to CSV SQL for unknown recommendations
            logger.warning(f"🤖 Unknown AI recommendation: {recommended_service}, falling back to CSV SQL")
            return await handle_csv_sql_query(request, db)
            
    except Exception as e:
        logger.error(f"🤖 Error in AI routing: {e}")
        # Fallback to CSV SQL on error
        logger.info("🤖 Falling back to CSV SQL due to AI routing error")
        return await handle_csv_sql_query(request, db)

async def handle_data_analysis_query(request: QueryRequest, db: Session) -> QueryResponse:
    """
    Handle data analysis queries using the data analysis service with file validation.
    """
    from services.data_analysis_service import data_analysis_service
    from db.models import UploadedFile
    import logging
    
    logger = logging.getLogger(__name__)
    
    if not request.file_id:
        raise HTTPException(status_code=400, detail="file_id is required for data analysis queries")
    
    try:
        logger.info(f"Processing data analysis query for file_id: {request.file_id}")
        
        # Validate file exists in database first
        uploaded_file = db.query(UploadedFile).filter(
            UploadedFile.id == request.file_id
        ).first()
        
        if not uploaded_file:
            logger.error(f"File not found in database: {request.file_id}")
            raise HTTPException(
                status_code=404, 
                detail=f"File with ID {request.file_id} not found. Please ensure the file was uploaded successfully."
            )
        
        logger.info(f"File found in database: {uploaded_file.original_filename}")
        
        # Validate file URL exists
        if not uploaded_file.file_url:
            logger.error(f"File URL is empty for file_id: {request.file_id}")
            raise HTTPException(
                status_code=400, 
                detail="File URL is not available. Please re-upload the file."
            )
        
        # Process data analysis query
        result = await data_analysis_service.process_query(request.question, request.file_id)
        
        # Convert to QueryResponse format
        return QueryResponse(
            answer=result["natural_response"],
            sql_query="",  # Data analysis queries don't generate SQL
            data=result["data"],
            columns=result["columns"],
            row_count=result["row_count"]
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing data analysis query for file_id {request.file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process data analysis query: {str(e)}")

async def handle_csv_sql_query(request: QueryRequest, db: Session) -> QueryResponse:
    """
    Handle SQL queries on CSV data using in-memory SQLite.
    """
    from services.csv_to_sql_converter import csv_to_sql_converter
    from services.data_analysis_service import data_analysis_service
    from llm.services import TextToSQLService
    from db.models import UploadedFile
    import logging
    
    logger = logging.getLogger(__name__)
    
    if not request.file_id:
        raise HTTPException(status_code=400, detail="file_id is required for CSV SQL queries")
    
    try:
        logger.info(f"Processing CSV SQL query for file_id: {request.file_id}")
        
        # Validate file exists in database first
        uploaded_file = db.query(UploadedFile).filter(
            UploadedFile.id == request.file_id
        ).first()
        
        if not uploaded_file:
            logger.error(f"File not found in database: {request.file_id}")
            raise HTTPException(
                status_code=404, 
                detail=f"File with ID {request.file_id} not found. Please ensure the file was uploaded successfully."
            )
        
        logger.info(f"File found in database: {uploaded_file.original_filename}")
        
        # Validate file URL exists
        if not uploaded_file.file_url:
            logger.error(f"File URL is empty for file_id: {request.file_id}")
            raise HTTPException(
                status_code=400, 
                detail="File URL is not available. Please re-upload the file."
            )
        
        # Get CSV data using existing DataAnalysisService
        df = await data_analysis_service._get_csv_data(request.file_id)
        if df is None:
            raise HTTPException(status_code=404, detail="CSV file not found or could not be loaded")
        
        # Convert CSV to SQLite table
        table_name = await csv_to_sql_converter.convert_csv_to_sql(request.file_id, df.to_csv())
        
        # Get schema information for SQL generation
        schema_info = await csv_to_sql_converter.get_table_schema(request.file_id)
        
        # Generate SQL query using existing TextToSQLService
        # Create a schema string that TextToSQLService can understand
        schema_string = f"Table: {table_name}\nColumns:\n"
        for col in schema_info["columns"]:
            schema_string += f"- {col['name']} ({col['type']})\n"
        
        # Add sample data for better context
        if schema_info["sample_data"]:
            schema_string += "\nSample data:\n"
            for i, row in enumerate(schema_info["sample_data"][:3]):  # First 3 rows
                schema_string += f"Row {i+1}: {row}\n"
        
        text_to_sql = TextToSQLService()
        sql_query = text_to_sql.generate_sql(request.question, schema_string)
        
        # Execute SQL on CSV data
        result = await csv_to_sql_converter.execute_sql_query(request.file_id, sql_query)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Format the answer
        answer = format_agent_result(result["data"])
        
        return QueryResponse(
            answer=answer,
            sql_query=sql_query,
            data=result["data"],
            columns=result["columns"],
            row_count=result["row_count"]
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing CSV SQL query for file_id {request.file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process CSV SQL query: {str(e)}")

async def handle_database_query(request: QueryRequest, db: Session) -> QueryResponse:
    """
    Handle database-based queries using the existing agent system.
    """
    if not request.connection_id:
        raise HTTPException(status_code=400, detail="connection_id is required for database queries")
    
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

    # 4. Get the raw data from the agent response
    raw_data = agent_response.get("data", [])
    columns = agent_response.get("columns", [])
    row_count = agent_response.get("row_count", 0)
    
    # 5. Create a human-readable answer for simple queries
    if len(raw_data) == 1 and len(raw_data[0]) == 1:
        # Single value result
        final_answer = f"The result is: {raw_data[0][0]}"
    elif row_count > 0:
        # Multiple rows result - show count
        final_answer = f"Query returned {row_count} rows. Showing results in table below."
    else:
        final_answer = "The query returned no results."

    # 6. Return the structured response to the user
    return QueryResponse(
        answer=final_answer, 
        sql_query=generated_sql,
        data=raw_data,
        columns=columns,
        row_count=row_count
    )
