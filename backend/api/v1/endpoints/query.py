import uuid
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from db.dependencies import get_db
from db.models import Connection, User
from llm.services import TextToSQLService
from ws.connection_manager import manager, ConnectionManager
from schemas.connection import Connection as ConnectionSchema  # Import your Pydantic schema
from core.langsmith_service import langsmith_service
from core.jwt_handler import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Pydantic Models for Request and Response ---
from pydantic import BaseModel


class QueryRequest(BaseModel):
    connection_id: Optional[str] = None
    file_id: Optional[str] = None
    file_ids: Optional[List[str]] = None  # Support for multiple files
    question: str
    data_source: str = "auto"  # "auto", "database", "csv", or "csv_sql"
    user_preference: Optional[str] = None  # "sql" or "python" for user preference


class QueryResponse(BaseModel):
    answer: str
    sql_query: str
    data: list = []
    columns: list = []
    row_count: int = 0
    ai_routing: Optional[dict] = None  # AI routing information for CSV queries


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
async def ask_question(
    request: QueryRequest = Body(...), 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user())
):
    """
    This endpoint orchestrates the entire "question-to-answer" flow.
    Automatic intelligent routing:
    - If file_id is provided (CSV data): AI agent automatically decides between csv_to_sql_converter and data_analysis_service
    - If no file_id (database data): Goes directly to agent-postgresql (no AI routing)
    """
    with langsmith_service.create_trace("query_endpoint") as trace_obj:
        # Add initial metadata
        trace_obj.metadata = {
            "endpoint": "query",
            "data_source": request.data_source,
            "has_file_id": bool(request.file_id),
            "has_file_ids": bool(request.file_ids),
            "file_count": len(request.file_ids) if request.file_ids else 0,
            "has_connection_id": bool(request.connection_id),
            "question_length": len(request.question),
            "user_preference": request.user_preference
        }

        try:
            logger.info(f"Processing query request: {request.question[:100]}...")
            
            # Automatic AI routing: If CSV file(s) are provided, AI agent decides the best service
            if request.file_id or request.file_ids:
                # Handle both single file (file_id) and multiple files (file_ids)
                if request.file_id and request.file_ids:
                    # If both are provided, combine them and remove duplicates
                    all_file_ids = list(set([request.file_id] + request.file_ids))
                    request.file_ids = all_file_ids
                    request.file_id = None  # Clear single file_id to avoid confusion
                elif request.file_id and not request.file_ids:
                    # Convert single file_id to file_ids for consistent handling
                    request.file_ids = [request.file_id]
                    request.file_id = None
                
                result = await handle_ai_routing(request, db, current_user)
            else:
                # No CSV file: Go directly to database analysis (no AI routing)
                result = await handle_database_query(request, db)
            
            # Add success metadata
            langsmith_service.add_metadata(trace_obj, {
                "success": True,
                "response_type": type(result).__name__,
                "row_count": result.row_count,
                "has_sql_query": bool(result.sql_query),
                "answer_length": len(result.answer)
            })
            
            logger.info(f"Query processed successfully: {result.row_count} rows returned")
            langsmith_service.log_trace_event("query_endpoint", f"Successfully processed query: {request.question[:100]}...")
            
            return result
            
        except Exception as e:
            # Add error metadata
            langsmith_service.add_metadata(trace_obj, {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            logger.error(f"Error processing query: {e}")
            langsmith_service.log_trace_event("query_endpoint_error", f"Failed to process query: {str(e)}")
            raise

async def handle_ai_routing(request: QueryRequest, db: Session, current_user) -> QueryResponse:
    """
    Handle automatic AI-powered intelligent routing using the AI routing agent.
    This uses the multi-file intelligent routing to select optimal files and services.
    """
    from services.ai_routing_agent import ai_routing_agent, AnalysisContext
    from db.models import UploadedFile
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🤖 AI Agent processing question: {request.question[:100]}...")
        logger.info(f"📁 Available files: {request.file_ids}")
        
        # Get file information for context
        file_size = None
        if request.file_ids and len(request.file_ids) > 0:
            # Get size of first file for context (AI will decide which files to use)
            uploaded_file = db.query(UploadedFile).filter(
                UploadedFile.id == request.file_ids[0]
            ).first()
            
            if uploaded_file:
                file_size = uploaded_file.file_size if hasattr(uploaded_file, 'file_size') else None
        
        # Create analysis context
        context = AnalysisContext(
            question=request.question,
            file_size=file_size,
            data_source="csv",
            user_preference=request.user_preference
        )
        
        # Use intelligent multi-file routing - AI will select which files to use
        ai_result = await ai_routing_agent.route_intelligent_multi_file_analysis(
            question=request.question,
            file_ids=request.file_ids,
            context=context
        )
        
        recommended_service = ai_result["recommended_service"]
        required_files = ai_result["required_files"]
        reasoning = ai_result["reasoning"]
        confidence = ai_result["confidence"]
        ai_analysis = ai_result.get("ai_analysis", "unknown")
        optimization_applied = ai_result.get("optimization_applied", False)
        
        logger.info(f"🤖 AI Agent recommendation: {recommended_service} (confidence: {confidence:.2f})")
        logger.info(f"🧠 AI Analysis: {ai_analysis}")
        logger.info(f"💭 AI Reasoning: {reasoning}")
        logger.info(f"📁 Files selected by AI: {required_files}")
        if optimization_applied:
            logger.info(f"⚡ AI optimization: Using {len(required_files)} files instead of {len(request.file_ids)}")
        
        # Update request with AI-selected files
        request.file_ids = required_files
        
        # Route to the AI-recommended service with selected files
        if recommended_service == "data_analysis_service":
            logger.info("🤖 AI routing to data analysis service (pandas)")
            return await handle_data_analysis_query(request, db, current_user)
        elif recommended_service == "csv_to_sql_converter":
            logger.info("🤖 AI routing to CSV to SQL converter")
            return await handle_csv_sql_query(request, db, current_user)
        else:
            # Fallback to CSV to SQL converter for unknown recommendations
            logger.warning(f"🤖 Unknown AI recommendation: {recommended_service}, falling back to CSV to SQL converter")
            return await handle_csv_sql_query(request, db, current_user)
            
    except Exception as e:
        logger.error(f"🤖 Error in AI routing: {e}")
        # Fallback to CSV to SQL converter on error
        logger.info("🤖 Falling back to CSV to SQL converter due to AI routing error")
        return await handle_csv_sql_query(request, db, current_user)

async def handle_data_analysis_query(request: QueryRequest, db: Session, current_user) -> QueryResponse:
    """
    Handle data analysis queries using the data analysis service with intelligent multi-file support.
    """
    from services.data_analysis_service import data_analysis_service
    from db.models import UploadedFile
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Support both single file (file_id) and multiple files (file_ids)
    file_ids = []
    if request.file_ids:
        file_ids = request.file_ids
    elif request.file_id:
        file_ids = [request.file_id]
    else:
        raise HTTPException(status_code=400, detail="Either file_id or file_ids is required for data analysis queries")
    
    try:
        logger.info(f"Processing intelligent data analysis query for {len(file_ids)} files: {file_ids}")
        
        # Validate all files exist in database first
        uploaded_files = []
        for file_id in file_ids:
            uploaded_file = db.query(UploadedFile).filter(
                UploadedFile.id == file_id
            ).first()
            
            if not uploaded_file:
                logger.error(f"File not found in database: {file_id}")
                raise HTTPException(
                    status_code=404, 
                    detail=f"File with ID {file_id} not found. Please ensure the file was uploaded successfully."
                )
            
            # Validate file URL exists
            if not uploaded_file.file_url:
                logger.error(f"File URL is empty for file_id: {file_id}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"File URL is not available for {uploaded_file.original_filename}. Please re-upload the file."
                )
            
            uploaded_files.append(uploaded_file)
            logger.info(f"File validated: {uploaded_file.original_filename}")
        
        # Track user activity for proactive cache refresh
        from core.redis_service import redis_service
        for file_id in file_ids:
            redis_service.track_user_activity(str(current_user.id), file_id)
        
        # Use intelligent multi-file processing
        result = await data_analysis_service.process_intelligent_query(
            file_ids=file_ids,
            question=request.question,
            user_id=str(current_user.id),
            user_preference=request.user_preference
        )
        
        # Convert to QueryResponse format
        return QueryResponse(
            answer=result["natural_response"],
            sql_query="",  # Data analysis queries don't generate SQL
            data=result["data"],
            columns=result["columns"],
            row_count=result["row_count"],
            ai_routing={
                "service_used": "data_analysis_service",
                "reasoning": result.get("ai_routing_info", {}).get("reasoning", "Intelligent multi-file analysis"),
                "confidence": result.get("ai_routing_info", {}).get("confidence", 0.9)
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing data analysis query for files {file_ids}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process data analysis query: {str(e)}")

async def handle_csv_sql_query(request: QueryRequest, db: Session, current_user) -> QueryResponse:
    """
    Handle SQL queries on CSV data using in-memory SQLite.
    Now supports both single-file and multi-file analysis with JOINs.
    """
    from services.csv_to_sql_converter import csv_to_sql_converter
    from services.data_analysis_service import data_analysis_service
    from llm.services import text_to_sql_service
    from db.models import UploadedFile
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Support both single file (file_id) and multiple files (file_ids)
    # Now we process ALL selected files for multi-file SQL operations
    file_ids = []
    if request.file_ids and len(request.file_ids) > 0:
        file_ids = request.file_ids
        logger.info(f"Multi-file SQL query requested for {len(file_ids)} files: {file_ids}")
    elif request.file_id:
        file_ids = [request.file_id]
        logger.info(f"Single-file SQL query requested for file: {request.file_id}")
    else:
        raise HTTPException(status_code=400, detail="Either file_id or file_ids is required for CSV SQL queries")
    
    try:
        logger.info(f"Processing CSV SQL query for {len(file_ids)} files: {file_ids}")
        
        # Validate all files exist in database first
        uploaded_files = []
        for file_id in file_ids:
            uploaded_file = db.query(UploadedFile).filter(
                UploadedFile.id == file_id
            ).first()
            
            if not uploaded_file:
                logger.error(f"File not found in database: {file_id}")
                raise HTTPException(
                    status_code=404, 
                    detail=f"File with ID {file_id} not found. Please ensure the file was uploaded successfully."
                )
            
            if not uploaded_file.file_url:
                logger.error(f"File URL is empty for file_id: {file_id}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"File URL is not available for {uploaded_file.original_filename}. Please re-upload the file."
                )
            
            uploaded_files.append(uploaded_file)
        
        logger.info(f"All {len(uploaded_files)} files validated successfully")
        
        # Track user activity for proactive cache refresh
        from core.redis_service import redis_service
        for file_id in file_ids:
            redis_service.track_user_activity(str(current_user.id), file_id)
        
        # Determine if this is single-file or multi-file operation
        if len(file_ids) == 1:
            # Single file operation (existing logic)
            file_id = file_ids[0]
            logger.info(f"Processing single-file SQL query for: {uploaded_files[0].original_filename}")
            
            # Get CSV data using existing DataAnalysisService with Redis caching
            df = await data_analysis_service._get_csv_data(file_id, str(current_user.id))
            if df is None:
                raise HTTPException(status_code=404, detail="CSV file not found or could not be loaded")
            
            # Convert CSV to SQLite table with Redis caching
            table_name = await csv_to_sql_converter.convert_csv_to_sql(file_id, df.to_csv(), str(current_user.id))
            
            # Get schema information for SQL generation
            schema_info = await csv_to_sql_converter.get_table_schema(file_id)
            
            # Generate SQL query using existing TextToSQLService
            schema_string = f"Table: {table_name}\nColumns:\n"
            for col in schema_info["columns"]:
                schema_string += f"- {col['name']} ({col['type']})\n"
            
            # Add sample data for better context
            if schema_info["sample_data"]:
                schema_string += "\nSample data:\n"
                for i, row in enumerate(schema_info["sample_data"][:3]):
                    schema_string += f"Row {i+1}: {row}\n"
            
            sql_query = text_to_sql_service.generate_sql(request.question, schema_string)
            
            # Execute SQL on CSV data
            result = await csv_to_sql_converter.execute_sql_query(file_id, sql_query)
            
        else:
            # Multi-file operation (new logic)
            logger.info(f"Processing multi-file SQL query across {len(file_ids)} files")
            
            # Get CSV data for all files
            csv_data_dict = {}
            for file_id in file_ids:
                df = await data_analysis_service._get_csv_data(file_id, str(current_user.id))
                if df is None:
                    raise HTTPException(status_code=404, detail=f"CSV file {file_id} not found or could not be loaded")
                csv_data_dict[file_id] = df.to_csv()
            
            # Convert multiple CSVs to SQLite tables in single database
            conversion_result = await csv_to_sql_converter.convert_multiple_csvs_to_sql(
                file_ids, csv_data_dict, str(current_user.id)
            )
            
            session_id = conversion_result["session_id"]
            table_names = conversion_result["table_names"]
            
            logger.info(f"Created multi-file session {session_id} with tables: {list(table_names.values())}")
            
            # Get comprehensive schema information for all tables
            multi_file_schema = await csv_to_sql_converter.get_multi_file_schema(session_id)
            
            # Generate comprehensive schema string for multi-file SQL generation
            schema_string = f"Multi-file database with {len(table_names)} tables:\n\n"
            
            for file_id, table_info in multi_file_schema["tables"].items():
                table_name = table_info["table_name"]
                schema_string += f"Table: {table_name} (File: {uploaded_files[0].original_filename if file_id == file_ids[0] else '...'})\n"
                schema_string += f"Rows: {table_info['row_count']}\nColumns:\n"
                
                for col in table_info["columns"]:
                    schema_string += f"  - {col['name']} ({col['type']})\n"
                
                # Add sample data for better context
                if table_info["sample_data"]:
                    schema_string += f"Sample data from {table_name}:\n"
                    for i, row in enumerate(table_info["sample_data"][:2]):  # First 2 rows per table
                        schema_string += f"  Row {i+1}: {row}\n"
                
                schema_string += "\n"
            
            # Add relationship hints for multi-file queries
            schema_string += "Note: You can JOIN tables using common column names or create cross-table comparisons.\n"
            
            sql_query = text_to_sql_service.generate_sql(request.question, schema_string)
            
            # Execute SQL on multi-file data
            result = await csv_to_sql_converter.execute_multi_file_sql_query(session_id, sql_query)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Generate natural language response using TextToSQLService
        answer = text_to_sql_service.generate_natural_response(request.question, sql_query, result["data"])
        
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
        logger.error(f"Unexpected error processing CSV SQL query for files {file_ids}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process CSV SQL query: {str(e)}")

async def handle_database_query(request: QueryRequest, db: Session) -> QueryResponse:
    """
    Handle database-based queries using the existing agent system.
    """
    import logging
    logger = logging.getLogger(__name__)
    
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
        from llm.services import text_to_sql_service
        generated_sql = text_to_sql_service.generate_sql(
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
    
    # 5. Generate natural language response using TextToSQLService
    try:
        final_answer = text_to_sql_service.generate_natural_response(request.question, generated_sql, raw_data)
    except Exception as e:
        logger.warning(f"Failed to generate natural response: {e}")
        # Fallback to simple response
        if len(raw_data) == 1 and len(raw_data[0]) == 1:
            final_answer = f"The result is: {raw_data[0][0]}"
        elif row_count > 0:
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
