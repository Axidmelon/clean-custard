from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import Response
from typing import List
import logging
import httpx
from datetime import datetime
from pydantic import BaseModel
from db.dependencies import get_db
from db.models import User, UploadedFile
from services.cloudinary_upload_service import cloudinary_upload_service
from sqlalchemy.orm import Session
from core.jwt_handler import get_current_user

class CsvCacheRequest(BaseModel):
    csv_data: str

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Upload a single file to Cloudinary and save metadata to database with atomic transaction
    """
    uploaded_file = None
    cloudinary_upload_success = False
    
    try:
        logger.info(f"Starting file upload for user {current_user.id}: {file.filename}")
        
        # Upload file to Cloudinary first
        file_info = await cloudinary_upload_service.upload_file(file, str(current_user.id))
        cloudinary_upload_success = True
        logger.info(f"File uploaded to Cloudinary successfully: {file_info['original_filename']}")
        
        # Create database record with proper error handling
        uploaded_file = UploadedFile(
            original_filename=file_info['original_filename'],
            file_size=str(file_info['file_size']),
            file_path=file_info['file_path'],
            file_url=file_info['file_url'],
            content_type=file_info['content_type'],
            cloudinary_public_id=file_info.get('cloudinary_public_id'),
            organization_id=current_user.organization_id,
            user_id=current_user.id
        )
        
        # Add to database and commit atomically
        db.add(uploaded_file)
        db.commit()
        db.refresh(uploaded_file)
        
        logger.info(f"File uploaded successfully: {file_info['original_filename']} by user {current_user.id}, file_id: {uploaded_file.id}")
        
        return {
            "success": True,
            "message": "File uploaded successfully",
            "file_info": {
                **file_info,
                "id": str(uploaded_file.id),
                "created_at": uploaded_file.created_at.isoformat()
            }
        }
        
    except HTTPException:
        # Rollback database transaction if HTTPException occurs
        try:
            db.rollback()
            logger.info("Database transaction rolled back due to HTTPException")
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {rollback_error}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}")
        
        # Rollback database transaction
        try:
            db.rollback()
            logger.info("Database transaction rolled back due to unexpected error")
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {rollback_error}")
        
        # If Cloudinary upload succeeded but database failed, try to clean up Cloudinary
        if cloudinary_upload_success and uploaded_file and uploaded_file.cloudinary_public_id:
            try:
                await cloudinary_upload_service.delete_file(uploaded_file.cloudinary_public_id)
                logger.info(f"Cleaned up Cloudinary file: {uploaded_file.cloudinary_public_id}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup Cloudinary file: {cleanup_error}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during file upload"
        )

@router.post("/upload-multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Upload multiple files to Cloudinary and save metadata to database
    """
    if len(files) > 10:  # Limit to 10 files per request
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per request"
        )
    
    uploaded_files = []
    failed_files = []
    
    for file in files:
        try:
            # Upload file to Cloudinary
            file_info = await cloudinary_upload_service.upload_file(file, str(current_user.id))
            
            # Save file metadata to database
            uploaded_file = UploadedFile(
                original_filename=file_info['original_filename'],
                file_size=str(file_info['file_size']),
                file_path=file_info['file_path'],
                file_url=file_info['file_url'],
                content_type=file_info['content_type'],
                cloudinary_public_id=file_info.get('cloudinary_public_id'),
                organization_id=current_user.organization_id,
                user_id=current_user.id
            )
            
            db.add(uploaded_file)
            db.commit()
            db.refresh(uploaded_file)
            
            uploaded_files.append({
                **file_info,
                "id": str(uploaded_file.id),
                "created_at": uploaded_file.created_at.isoformat()
            })
            logger.info(f"File uploaded successfully: {file_info['original_filename']} by user {current_user.id}")
        except Exception as e:
            failed_files.append({
                "filename": file.filename,
                "error": str(e)
            })
            logger.error(f"Failed to upload file {file.filename}: {e}")
            db.rollback()
    
    return {
        "success": len(uploaded_files) > 0,
        "message": f"Uploaded {len(uploaded_files)} files successfully",
        "uploaded_files": uploaded_files,
        "failed_files": failed_files
    }

@router.delete("/delete/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Delete a file from Cloudinary and remove from database
    """
    try:
        # Find the file in database
        uploaded_file = db.query(UploadedFile).filter(
            UploadedFile.id == file_id,
            UploadedFile.user_id == current_user.id
        ).first()
        
        if not uploaded_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Delete from Cloudinary (if public_id exists)
        cloudinary_success = True
        if uploaded_file.cloudinary_public_id:
            try:
                cloudinary_success = await cloudinary_upload_service.delete_file(uploaded_file.cloudinary_public_id)
                if not cloudinary_success:
                    logger.warning(f"Failed to delete file from Cloudinary: {uploaded_file.cloudinary_public_id}")
            except Exception as cloudinary_error:
                logger.warning(f"Error deleting from Cloudinary: {cloudinary_error}")
                cloudinary_success = False
        
        # Always remove from database, even if Cloudinary deletion fails
        # This ensures the file is removed from the user's view
        db.delete(uploaded_file)
        db.commit()
        
        logger.info(f"File deleted successfully: {uploaded_file.original_filename} by user {current_user.id}")
        return {
            "success": True,
            "message": "File deleted successfully"
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file deletion: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during file deletion"
        )

@router.get("/info/{file_path:path}")
async def get_file_info(
    file_path: str,
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Get information about a file in Cloudinary
    """
    try:
        # Verify the file belongs to the user
        if not file_path.startswith(f"uploads/") or str(current_user.id) not in file_path:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this file"
            )
        
        file_info = await cloudinary_upload_service.get_file_info(file_path)
        
        if file_info:
            return {
                "success": True,
                "file_info": file_info
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting file info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.get("/list")
async def list_uploaded_files(
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Get list of uploaded files for the current user
    """
    try:
        logger.info(f"Listing files for user {current_user.id}")
        
        # Validate user and organization
        if not current_user:
            logger.error("No current user found in request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if not current_user.id:
            logger.error("User ID is missing")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user session"
            )
        
        # Test database connection first with more robust error handling
        try:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
            logger.debug("Database connection test successful")
        except Exception as db_error:
            logger.error(f"Database connection test failed: {db_error}")
            # Try to rollback any pending transaction
            try:
                db.rollback()
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection error. Please try again in a moment."
            )
        
        # Query uploaded files with better error handling
        try:
            uploaded_files = db.query(UploadedFile).filter(
                UploadedFile.user_id == current_user.id
            ).order_by(UploadedFile.created_at.desc()).all()
            
            logger.info(f"Found {len(uploaded_files)} files for user {current_user.id}")
            
        except Exception as query_error:
            logger.error(f"Database query failed: {query_error}")
            try:
                db.rollback()
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve files from database"
            )
        
        # Process files data with enhanced error handling
        files_data = []
        for file in uploaded_files:
            try:
                # Safely convert file_size to int, handle potential string issues
                try:
                    file_size = int(file.file_size) if file.file_size else 0
                except (ValueError, TypeError):
                    # If conversion fails, use 0 as default
                    file_size = 0
                    logger.warning(f"Could not convert file_size to int for file {file.id}: {file.file_size}")
                
                # Safely handle datetime fields
                created_at = file.created_at.isoformat() if file.created_at else None
                updated_at = file.updated_at.isoformat() if file.updated_at else None
                
                files_data.append({
                    "id": str(file.id),
                    "original_filename": file.original_filename or "Unknown",
                    "file_size": file_size,
                    "file_path": file.file_path or "",
                    "file_url": file.file_url or "",
                    "content_type": file.content_type or "application/octet-stream",
                    "cloudinary_public_id": file.cloudinary_public_id,
                    "created_at": created_at,
                    "updated_at": updated_at
                })
                
            except Exception as file_error:
                logger.error(f"Error processing file {file.id}: {file_error}")
                # Continue processing other files instead of failing completely
                continue
        
        logger.info(f"Successfully processed {len(files_data)} files")
        
        return {
            "success": True,
            "files": files_data,
            "count": len(files_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving uploaded files: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Try to rollback any pending transaction
        try:
            db.rollback()
        except Exception:
            pass
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving files. Please try again."
        )

@router.get("/status")
async def get_upload_service_status():
    """
    Check if the file upload service is available
    """
    return {
        "available": cloudinary_upload_service.is_available(),
        "cloud_name": cloudinary_upload_service.cloud_name,
        "configured": cloudinary_upload_service.configured
    }

@router.get("/health")
async def files_health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for the files service
    """
    health_status = {
        "service": "files",
        "status": "healthy",
        "timestamp": None,
        "checks": {}
    }
    
    try:
        from datetime import datetime
        health_status["timestamp"] = datetime.utcnow().isoformat()
        
        # Check database connection
        try:
            db.execute("SELECT 1")
            health_status["checks"]["database"] = {"status": "healthy", "message": "Database connection successful"}
        except Exception as e:
            health_status["checks"]["database"] = {"status": "unhealthy", "message": f"Database error: {str(e)}"}
            health_status["status"] = "unhealthy"
        
        # Check Cloudinary service
        try:
            cloudinary_available = cloudinary_upload_service.is_available()
            if cloudinary_available:
                health_status["checks"]["cloudinary"] = {"status": "healthy", "message": "Cloudinary service available"}
            else:
                health_status["checks"]["cloudinary"] = {"status": "unhealthy", "message": "Cloudinary service unavailable"}
                health_status["status"] = "unhealthy"
        except Exception as e:
            health_status["checks"]["cloudinary"] = {"status": "unhealthy", "message": f"Cloudinary error: {str(e)}"}
            health_status["status"] = "unhealthy"
        
        # Check if we can query uploaded files table
        try:
            file_count = db.query(UploadedFile).count()
            health_status["checks"]["files_table"] = {"status": "healthy", "message": f"Files table accessible, {file_count} files"}
        except Exception as e:
            health_status["checks"]["files_table"] = {"status": "unhealthy", "message": f"Files table error: {str(e)}"}
            health_status["status"] = "unhealthy"
        
        return health_status
        
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["general"] = {"status": "unhealthy", "message": f"General error: {str(e)}"}
        return health_status

@router.get("/signed-url/{file_id}")
async def get_signed_url(
    file_id: str,
    expiration_hours: float = 4.0,  # Increased default from 2 to 4 hours
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Generate a signed URL for direct access to a file with Redis caching optimization
    """
    import time
    total_start_time = time.time()
    
    try:
        # Validate expiration hours (max 24 hours, min 0.1 hours)
        if expiration_hours > 24:
            expiration_hours = 24.0
        elif expiration_hours < 0.1:
            expiration_hours = 0.1
        
        # Generate signed URL directly - no caching needed for temporary URLs
        
        # Find the file in database
        uploaded_file = db.query(UploadedFile).filter(
            UploadedFile.id == file_id,
            UploadedFile.user_id == current_user.id
        ).first()
        
        if not uploaded_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check if cloudinary_public_id exists
        if not uploaded_file.cloudinary_public_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File does not have a valid Cloudinary public ID. Cannot generate signed URL."
            )
        
        # Generate signed URL using the file's cloudinary_public_id with user context
        cloudinary_start_time = time.time()
        signed_url_data = cloudinary_upload_service.generate_signed_url(
            uploaded_file.cloudinary_public_id, 
            expiration_hours,
            str(current_user.id)  # Include user ID for enhanced security
        )
        cloudinary_end_time = time.time()
        logger.info(f"Cloudinary signed URL generation for file {file_id} took: {(cloudinary_end_time - cloudinary_start_time)*1000:.1f}ms")
        
        # Prepare response data
        response_data = {
            "success": True,
            "signed_url": signed_url_data["signed_url"],
            "expires_at": signed_url_data["expires_at"],
            "expires_in_hours": signed_url_data["expires_in_hours"],
            "file_info": {
                "filename": uploaded_file.original_filename,
                "size": int(uploaded_file.file_size),
                "content_type": uploaded_file.content_type,
                "created_at": uploaded_file.created_at.isoformat()
            },
            "cached": False
        }
        
        # No caching needed for temporary signed URLs - they're fast to generate
        
        # Log the request for audit purposes
        total_end_time = time.time()
        logger.info(f"🚀 Generated signed URL for file {file_id} by user {current_user.id}, expires in {expiration_hours} hours (total time: {(total_end_time - total_start_time)*1000:.1f}ms)")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating signed URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating signed URL"
        )

@router.get("/metadata/{file_id}")
async def get_file_metadata(
    file_id: str,
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Get file metadata by ID for frontend state management
    """
    try:
        logger.info(f"Getting file metadata for file_id: {file_id}, user: {current_user.id}")
        
        # Find the file in database
        uploaded_file = db.query(UploadedFile).filter(
            UploadedFile.id == file_id,
            UploadedFile.user_id == current_user.id
        ).first()
        
        if not uploaded_file:
            logger.warning(f"File not found in database: {file_id} for user: {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        logger.info(f"File metadata retrieved successfully for file_id: {file_id}")
        
        return {
            "success": True,
            "file_info": {
                "id": str(uploaded_file.id),
                "original_filename": uploaded_file.original_filename,
                "file_size": int(uploaded_file.file_size) if uploaded_file.file_size else 0,
                "file_path": uploaded_file.file_path,
                "file_url": uploaded_file.file_url,
                "content_type": uploaded_file.content_type,
                "cloudinary_public_id": uploaded_file.cloudinary_public_id,
                "created_at": uploaded_file.created_at.isoformat(),
                "updated_at": uploaded_file.updated_at.isoformat() if uploaded_file.updated_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting file metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving file metadata"
        )

@router.get("/validate/{file_id}")
async def validate_file_exists(
    file_id: str,
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Validate that a file exists and is accessible by the current user
    """
    try:
        logger.info(f"Validating file existence for file_id: {file_id}, user: {current_user.id}")
        
        # Find the file in database
        uploaded_file = db.query(UploadedFile).filter(
            UploadedFile.id == file_id,
            UploadedFile.user_id == current_user.id
        ).first()
        
        if not uploaded_file:
            logger.warning(f"File not found in database: {file_id} for user: {current_user.id}")
            return {
                "exists": False,
                "file_id": file_id,
                "message": "File not found in database"
            }
        
        # Verify file is accessible via Cloudinary URL
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.head(uploaded_file.file_url)
                
                if response.status_code == 200:
                    logger.info(f"File validation successful for file_id: {file_id}")
                    return {
                        "exists": True,
                        "file_id": file_id,
                        "file_info": {
                            "original_filename": uploaded_file.original_filename,
                            "file_size": uploaded_file.file_size,
                            "content_type": uploaded_file.content_type,
                            "created_at": uploaded_file.created_at.isoformat()
                        },
                        "message": "File exists and is accessible"
                    }
                else:
                    logger.warning(f"File not accessible via URL: {file_id}, status: {response.status_code}")
                    return {
                        "exists": False,
                        "file_id": file_id,
                        "message": f"File exists in database but not accessible via URL (status: {response.status_code})"
                    }
        except Exception as url_error:
            logger.error(f"Error checking file URL accessibility: {url_error}")
            return {
                "exists": False,
                "file_id": file_id,
                "message": f"Error checking file accessibility: {str(url_error)}"
            }
                
    except Exception as e:
        logger.error(f"Unexpected error validating file: {e}")
        return {
            "exists": False,
            "file_id": file_id,
            "message": f"Error validating file: {str(e)}"
        }

@router.post("/cache-csv/{file_id}")
async def cache_csv_file(
    file_id: str,
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Cache CSV file content in Redis for faster processing
    """
    try:
        logger.info(f"Caching CSV file for file_id: {file_id}, user: {current_user.id}")
        
        # Find the file in database
        uploaded_file = db.query(UploadedFile).filter(
            UploadedFile.id == file_id,
            UploadedFile.user_id == current_user.id
        ).first()
        
        if not uploaded_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check if file is already cached
        from core.redis_service import redis_service
        cached_data = redis_service.get_cached_csv_data(str(current_user.id), file_id)
        
        if cached_data:
            logger.info(f"CSV file {file_id} already cached for user {current_user.id}")
            return {
                "success": True,
                "message": "File already cached",
                "cached": True,
                "file_info": {
                    "filename": uploaded_file.original_filename,
                    "size": len(cached_data),
                    "cached_at": "Already cached"
                }
            }
        
        # Generate signed URL for downloading
        if not uploaded_file.cloudinary_public_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File does not have a valid Cloudinary public ID"
            )
        
        # Generate short-lived signed URL (10 minutes)
        signed_url_data = cloudinary_upload_service.generate_signed_url(
            uploaded_file.cloudinary_public_id, 
            0.167,  # 10 minutes
            str(current_user.id)
        )
        
        # Download CSV content
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(signed_url_data["signed_url"])
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to download file content"
                )
            
            csv_content = response.text
        
        # Cache the CSV content in Redis (2 hours)
        cache_success = redis_service.cache_csv_data(
            str(current_user.id), 
            file_id, 
            csv_content, 
            ttl=7200  # 2 hours
        )
        
        if not cache_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cache file content"
            )
        
        logger.info(f"Successfully cached CSV file {file_id} for user {current_user.id}")
        
        return {
            "success": True,
            "message": "File cached successfully",
            "cached": True,
            "file_info": {
                "filename": uploaded_file.original_filename,
                "size": len(csv_content),
                "cached_at": datetime.now().isoformat(),
                "expires_in_hours": 2
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error caching CSV file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while caching file"
        )

@router.post("/cache-csv-from-data/{file_id}")
async def cache_csv_from_data(
    file_id: str,
    request: CsvCacheRequest,
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Cache CSV data received from frontend (optimized flow)
    """
    try:
        logger.info(f"Caching CSV data from frontend for file_id: {file_id}, user: {current_user.id}")
        
        # Find the file in database
        uploaded_file = db.query(UploadedFile).filter(
            UploadedFile.id == file_id,
            UploadedFile.user_id == current_user.id
        ).first()
        
        if not uploaded_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Check if file is already cached
        from core.redis_service import redis_service
        cached_data = redis_service.get_cached_csv_data(str(current_user.id), file_id)
        
        if cached_data:
            logger.info(f"CSV file {file_id} already cached for user {current_user.id}")
            return {
                "success": True,
                "message": "File already cached",
                "cached": True,
                "file_info": {
                    "filename": uploaded_file.original_filename,
                    "size": len(cached_data),
                    "cached_at": "Already cached"
                }
            }
        
        # Cache the CSV content received from frontend (2 hours)
        cache_success = redis_service.cache_csv_data(
            str(current_user.id), 
            file_id, 
            request.csv_data, 
            ttl=7200  # 2 hours
        )
        
        if not cache_success:
            # Log the Redis caching failure but don't fail the entire request
            logger.warning(f"Failed to cache CSV data in Redis for user {current_user.id}, file {file_id}. Continuing without cache.")
            # Note: We continue processing even if caching fails - the application can work without Redis cache
        
        logger.info(f"CSV data processing completed for file_id: {file_id}, user: {current_user.id}")
        
        return {
            "success": True,
            "message": "File processed successfully from frontend data",
            "cached": cache_success,  # Indicate whether caching was successful
            "file_info": {
                "filename": uploaded_file.original_filename,
                "size": len(request.csv_data),
                "cached_at": datetime.now().isoformat() if cache_success else None,
                "expires_in_hours": 2 if cache_success else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error caching CSV data from frontend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while caching file data"
        )

@router.post("/refresh-cache/{file_id}")
async def refresh_csv_cache(
    file_id: str,
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Manually refresh CSV cache for a specific file
    """
    try:
        logger.info(f"Manual cache refresh requested for file_id: {file_id}, user: {current_user.id}")
        
        from services.cache_refresh_service import cache_refresh_service
        
        # Attempt manual refresh
        success = await cache_refresh_service.manual_refresh_cache(str(current_user.id), file_id)
        
        if success:
            return {
                "success": True,
                "message": "Cache refreshed successfully",
                "file_id": file_id,
                "refreshed_at": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "Cache refresh failed or user not active recently",
                "file_id": file_id
            }
        
    except Exception as e:
        logger.error(f"Unexpected error refreshing cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while refreshing cache"
        )

@router.get("/cache-status")
async def get_cache_status(
    current_user: User = Depends(get_current_user())
):
    """
    Get CSV cache status and statistics
    """
    try:
        from core.redis_service import redis_service
        from services.cache_refresh_service import cache_refresh_service
        
        # Get Redis cache stats
        cache_stats = redis_service.get_csv_cache_stats()
        
        # Get refresh service status
        service_status = cache_refresh_service.get_service_status()
        
        return {
            "success": True,
            "cache_stats": cache_stats,
            "refresh_service": service_status,
            "user_id": str(current_user.id)
        }
        
    except Exception as e:
        logger.error(f"Unexpected error getting cache status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while getting cache status"
        )

@router.get("/content/{file_id}")
async def get_file_content(
    file_id: str,
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Get the content of a file by its ID (fallback method)
    """
    try:
        # Find the file in database
        uploaded_file = db.query(UploadedFile).filter(
            UploadedFile.id == file_id,
            UploadedFile.user_id == current_user.id
        ).first()
        
        if not uploaded_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        # Fetch file content from Cloudinary URL
        async with httpx.AsyncClient() as client:
            response = await client.get(uploaded_file.file_url)
            
            if response.status_code == 200:
                # Return the file content as plain text
                return Response(
                    content=response.text,
                    media_type="text/plain",
                    headers={
                        "Content-Disposition": f"inline; filename={uploaded_file.original_filename}"
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File content not found"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting file content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving file content"
        )
