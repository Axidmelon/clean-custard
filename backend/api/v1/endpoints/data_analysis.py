# File: backend/api/v1/endpoints/data_analysis.py

from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import uuid

from db.dependencies import get_db
from db.models import User, UploadedFile
from core.jwt_handler import get_current_user
from services.data_analysis_service import data_analysis_service

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Pydantic Models ---
from pydantic import BaseModel

class DataAnalysisRequest(BaseModel):
    file_id: str
    question: str

class DataAnalysisResponse(BaseModel):
    success: bool
    question: str
    natural_response: str
    data: list = []
    columns: list = []
    row_count: int = 0
    result_type: str
    display_type: str
    timestamp: str

class DataSchemaResponse(BaseModel):
    success: bool
    file_id: str
    schema_info: Dict[str, Any]
    message: str

# --- Helper Functions ---

def validate_file_access(file_id: str, user_id: str, db: Session) -> UploadedFile:
    """
    Validate that the user has access to the specified file.
    
    Args:
        file_id: ID of the file
        user_id: ID of the current user
        db: Database session
        
    Returns:
        UploadedFile object if valid
        
    Raises:
        HTTPException: If file not found or access denied
    """
    try:
        # Convert string file_id to UUID
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format"
        )
    
    # Find the file in database
    uploaded_file = db.query(UploadedFile).filter(
        UploadedFile.id == file_uuid,
        UploadedFile.user_id == user_id
    ).first()
    
    if not uploaded_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found or access denied"
        )
    
    return uploaded_file

# --- API Endpoints ---

@router.post("/analyze", response_model=DataSchemaResponse)
async def analyze_data_schema(
    request: DataAnalysisRequest = Body(...),
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Analyze uploaded data file and return detailed schema information.
    
    This endpoint:
    1. Validates user access to the file
    2. Analyzes data structure and data types
    3. Caches schema information for future queries
    4. Returns comprehensive schema analysis
    """
    try:
        logger.info(f"Data schema analysis requested for file_id: {request.file_id} by user: {current_user.id}")
        
        # Validate file access
        uploaded_file = validate_file_access(request.file_id, str(current_user.id), db)
        
        # Check if file is CSV
        if not uploaded_file.original_filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is not a CSV file"
            )
        
        # Analyze data schema
        schema_info = await data_analysis_service.analyze_data_schema(request.file_id)
        
        logger.info(f"Data schema analysis completed for file_id: {request.file_id}")
        
        return DataSchemaResponse(
            success=True,
            file_id=request.file_id,
            schema_info=schema_info,
            message="Data schema analyzed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing CSV schema for file_id {request.file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze CSV schema: {str(e)}"
        )

@router.post("/query", response_model=DataAnalysisResponse)
async def analyze_data(
    request: DataAnalysisRequest = Body(...),
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Process a natural language question on uploaded data.
    
    This endpoint:
    1. Validates user access to the file
    2. Converts natural language to pandas operations
    3. Executes data analysis operations
    4. Returns formatted results with natural language response
    """
    try:
        logger.info(f"Data analysis requested: '{request.question}' for file_id: {request.file_id} by user: {current_user.id}")
        
        # Validate file access
        uploaded_file = validate_file_access(request.file_id, str(current_user.id), db)
        
        # Check if file is CSV
        if not uploaded_file.original_filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is not a CSV file"
            )
        
        # Process the analysis
        result = await data_analysis_service.process_query(request.question, request.file_id)
        
        logger.info(f"Data analysis processed successfully for file_id: {request.file_id}")
        
        return DataAnalysisResponse(
            success=True,
            question=result["question"],
            natural_response=result["natural_response"],
            data=result["data"],
            columns=result["columns"],
            row_count=result["row_count"],
            result_type=result["result_type"],
            display_type=result["display_type"],
            timestamp=result["timestamp"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing CSV query for file_id {request.file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CSV query: {str(e)}"
        )

@router.get("/schema/{file_id}", response_model=DataSchemaResponse)
async def get_csv_schema(
    file_id: str,
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Get cached schema information for a CSV file.
    
    This endpoint returns previously analyzed schema information
    without re-analyzing the file.
    """
    try:
        logger.info(f"CSV schema retrieval requested for file_id: {file_id} by user: {current_user.id}")
        
        # Validate file access
        uploaded_file = validate_file_access(file_id, str(current_user.id), db)
        
        # Check if file is CSV
        if not uploaded_file.original_filename.lower().endswith('.csv'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is not a CSV file"
            )
        
        # Get schema from cache (this will analyze if not cached)
        schema_info = await data_analysis_service.analyze_data_schema(file_id)
        
        logger.info(f"CSV schema retrieved for file_id: {file_id}")
        
        return DataSchemaResponse(
            success=True,
            file_id=file_id,
            schema_info=schema_info,
            message="Data schema retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving CSV schema for file_id {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve CSV schema: {str(e)}"
        )

@router.delete("/cache/{file_id}")
async def clear_csv_cache(
    file_id: str,
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Clear cached data for a specific CSV file.
    
    This endpoint clears both CSV data and schema cache for the specified file.
    """
    try:
        logger.info(f"CSV cache clear requested for file_id: {file_id} by user: {current_user.id}")
        
        # Validate file access
        uploaded_file = validate_file_access(file_id, str(current_user.id), db)
        
        # Clear cache
        data_analysis_service.clear_cache(file_id)
        
        logger.info(f"CSV cache cleared for file_id: {file_id}")
        
        return {
            "success": True,
            "message": f"Cache cleared for file {uploaded_file.original_filename}",
            "file_id": file_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing CSV cache for file_id {file_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear CSV cache: {str(e)}"
        )

@router.get("/status")
async def get_csv_service_status():
    """
    Get the status of the CSV query service.
    
    This endpoint returns information about the service status,
    cache size, and available operations.
    """
    try:
        cache_size = len(data_analysis_service.csv_cache)
        schema_cache_size = len(data_analysis_service.schema_cache)
        
        return {
            "success": True,
            "service_status": "running",
            "cache_info": {
                "csv_data_cache_size": cache_size,
                "schema_cache_size": schema_cache_size
            },
            "available_operations": [
                "schema_analysis",
                "natural_language_query",
                "data_filtering",
                "aggregation",
                "statistical_analysis"
            ],
            "supported_file_types": ["csv"],
            "max_file_size": "10MB",
            "max_preview_rows": 100
        }
        
    except Exception as e:
        logger.error(f"Error getting CSV service status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service status: {str(e)}"
        )
