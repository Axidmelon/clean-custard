import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from google.cloud import storage
from google.cloud.exceptions import NotFound
import logging

logger = logging.getLogger(__name__)

class FileUploadService:
    def __init__(self):
        self.bucket_name = os.getenv("GOOGLE_CLOUD_BUCKET_NAME")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        
        if not self.bucket_name or not self.project_id:
            logger.warning("Google Cloud Storage not configured. File uploads will be disabled.")
            self.client = None
            self.bucket = None
        else:
            try:
                self.client = storage.Client(project=self.project_id)
                self.bucket = self.client.bucket(self.bucket_name)
                logger.info(f"Google Cloud Storage initialized with bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Google Cloud Storage: {e}")
                self.client = None
                self.bucket = None

    def is_available(self) -> bool:
        """Check if Google Cloud Storage is available"""
        return self.client is not None and self.bucket is not None

    def generate_file_path(self, original_filename: str, user_id: str) -> str:
        """Generate a unique file path for the uploaded file"""
        # Get current date for organization
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        
        # Generate unique filename
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Organize by year/month/user
        return f"uploads/{year}/{month}/{user_id}/{unique_filename}"

    async def upload_file(self, file: UploadFile, user_id: str) -> Dict[str, Any]:
        """Upload a file to Google Cloud Storage"""
        if not self.is_available():
            raise HTTPException(
                status_code=503, 
                detail="File upload service is not available"
            )

        try:
            # Validate file
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            # Check file size (limit to 100MB)
            file_size = 0
            content = await file.read()
            file_size = len(content)
            
            if file_size > 100 * 1024 * 1024:  # 100MB
                raise HTTPException(status_code=413, detail="File too large. Maximum size is 100MB")
            
            # Reset file pointer
            await file.seek(0)
            
            # Generate file path
            file_path = self.generate_file_path(file.filename, user_id)
            
            # Upload to GCS
            blob = self.bucket.blob(file_path)
            blob.upload_from_file(file.file, content_type=file.content_type)
            
            # Generate public URL (optional - you might want to keep files private)
            blob.make_public()
            
            # Return file information
            return {
                "file_id": str(uuid.uuid4()),
                "original_filename": file.filename,
                "file_size": file_size,
                "file_path": file_path,
                "file_url": blob.public_url,
                "content_type": file.content_type,
                "upload_date": datetime.now().isoformat(),
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Failed to upload file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from Google Cloud Storage"""
        if not self.is_available():
            raise HTTPException(
                status_code=503, 
                detail="File upload service is not available"
            )

        try:
            blob = self.bucket.blob(file_path)
            blob.delete()
            logger.info(f"Successfully deleted file: {file_path}")
            return True
        except NotFound:
            logger.warning(f"File not found for deletion: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a file in Google Cloud Storage"""
        if not self.is_available():
            return None

        try:
            blob = self.bucket.blob(file_path)
            blob.reload()
            
            return {
                "file_path": file_path,
                "file_size": blob.size,
                "content_type": blob.content_type,
                "created": blob.time_created.isoformat() if blob.time_created else None,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "public_url": blob.public_url
            }
        except NotFound:
            return None
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return None

# Global instance
file_upload_service = FileUploadService()
