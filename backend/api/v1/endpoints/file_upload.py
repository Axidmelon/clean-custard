from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import Response
from typing import List
import logging
import httpx
from db.dependencies import get_db
from db.models import User, UploadedFile
from services.cloudinary_upload_service import cloudinary_upload_service
from sqlalchemy.orm import Session
from core.jwt_handler import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Upload a single file to Cloudinary and save metadata to database
    """
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
        
        logger.info(f"File uploaded successfully: {file_info['original_filename']} by user {current_user.id}")
        
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
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {e}")
        db.rollback()
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
        
        # Delete from Cloudinary
        success = await cloudinary_upload_service.delete_file(uploaded_file.file_path)
        
        if success:
            # Remove from database
            db.delete(uploaded_file)
            db.commit()
            
            logger.info(f"File deleted successfully: {uploaded_file.original_filename} by user {current_user.id}")
            return {
                "success": True,
                "message": "File deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file from storage"
            )
            
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
            db.execute("SELECT 1")
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
    expiration_hours: int = 2,
    current_user: User = Depends(get_current_user()),
    db: Session = Depends(get_db)
):
    """
    Generate a signed URL for direct access to a file
    """
    try:
        # Validate expiration hours (max 24 hours)
        if expiration_hours > 24:
            expiration_hours = 24
        elif expiration_hours < 1:
            expiration_hours = 1
        
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
        signed_url_data = cloudinary_upload_service.generate_signed_url(
            uploaded_file.cloudinary_public_id, 
            expiration_hours,
            str(current_user.id)  # Include user ID for enhanced security
        )
        
        # Log the request for audit purposes
        logger.info(f"Generated signed URL for file {file_id} by user {current_user.id}, expires in {expiration_hours} hours")
        
        return {
            "success": True,
            "signed_url": signed_url_data["signed_url"],
            "expires_at": signed_url_data["expires_at"],
            "expires_in_hours": signed_url_data["expires_in_hours"],
            "file_info": {
                "filename": uploaded_file.original_filename,
                "size": int(uploaded_file.file_size),
                "content_type": uploaded_file.content_type,
                "created_at": uploaded_file.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating signed URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating signed URL"
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
