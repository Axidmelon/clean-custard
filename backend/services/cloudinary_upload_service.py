import os
import uuid
import time
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
import cloudinary
import cloudinary.uploader
import logging

logger = logging.getLogger(__name__)

class CloudinaryUploadService:
    def __init__(self):
        self.cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        self.api_key = os.getenv("CLOUDINARY_API_KEY")
        self.api_secret = os.getenv("CLOUDINARY_API_SECRET")
        
        if not all([self.cloud_name, self.api_key, self.api_secret]):
            logger.warning("Cloudinary not configured. File uploads will be disabled.")
            self.configured = False
        else:
            try:
                cloudinary.config(
                    cloud_name=self.cloud_name,
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    secure=True
                )
                self.configured = True
                logger.info(f"Cloudinary initialized with cloud: {self.cloud_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Cloudinary: {e}")
                self.configured = False

    def is_available(self) -> bool:
        """Check if Cloudinary is available"""
        return self.configured

    def generate_public_id(self, original_filename: str, user_id: str) -> str:
        """Generate a unique public ID for the uploaded file"""
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
        """Upload a file to Cloudinary"""
        if not self.is_available():
            raise HTTPException(
                status_code=503, 
                detail="File upload service is not available"
            )

        try:
            # Validate file
            if not file.filename:
                raise HTTPException(status_code=400, detail="No filename provided")
            
            # Check file size (Cloudinary free tier limit: 10MB per file)
            file_size = 0
            content = await file.read()
            file_size = len(content)
            
            if file_size > 10 * 1024 * 1024:  # 10MB
                raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
            
            # Reset file pointer
            await file.seek(0)
            
            # Generate public ID
            public_id = self.generate_public_id(file.filename, user_id)
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file.file,
                public_id=public_id,
                resource_type="auto",  # Automatically detect file type
                folder="custard-uploads"
            )
            
            # Return file information
            return {
                "file_id": str(uuid.uuid4()),
                "original_filename": file.filename,
                "file_size": file_size,
                "file_path": public_id,
                "file_url": result["secure_url"],
                "content_type": file.content_type,
                "upload_date": datetime.now().isoformat(),
                "user_id": user_id,
                "cloudinary_public_id": result["public_id"]
            }
            
        except Exception as e:
            logger.error(f"Failed to upload file {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

    async def delete_file(self, public_id: str) -> bool:
        """Delete a file from Cloudinary"""
        if not self.is_available():
            raise HTTPException(
                status_code=503, 
                detail="File upload service is not available"
            )

        try:
            result = cloudinary.uploader.destroy(public_id)
            if result.get("result") == "ok":
                logger.info(f"Successfully deleted file: {public_id}")
                return True
            else:
                logger.warning(f"Failed to delete file: {public_id}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete file {public_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

    async def get_file_info(self, public_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a file in Cloudinary"""
        if not self.is_available():
            return None

        try:
            result = cloudinary.api.resource(public_id)
            
            return {
                "file_path": public_id,
                "file_size": result["bytes"],
                "content_type": result.get("format", "application/octet-stream"),
                "created": result["created_at"],
                "updated": result["updated_at"],
                "public_url": result["secure_url"]
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {public_id}: {e}")
            return None

    def generate_signed_url(self, public_id: str, expiration_hours: float = 0.5, user_id: str = None) -> Dict[str, Any]:
        """Generate a signed URL for direct access to a file"""
        if not self.is_available():
            raise HTTPException(
                status_code=503, 
                detail="File upload service is not available"
            )

        try:
            # Calculate expiration time (support fractional hours for shorter expiration)
            expires_at = int(time.time()) + int(expiration_hours * 3600)
            
            # Create signature string with user context for enhanced security
            if user_id:
                signature_string = f"expires={expires_at}~public_id={public_id}~user_id={user_id}"
            else:
                signature_string = f"expires={expires_at}~public_id={public_id}"
            
            # Generate HMAC signature using SHA256 for enhanced security
            signature = hmac.new(
                self.api_secret.encode(),
                signature_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Construct signed URL (correct format for Cloudinary raw files)
            signed_url = f"https://res.cloudinary.com/{self.cloud_name}/raw/upload/v{int(time.time())}/{public_id}?{signature}~{signature_string}"
            
            logger.info(f"Generated signed URL for {public_id}, expires at {expires_at}")
            
            return {
                "signed_url": signed_url,
                "expires_at": expires_at,
                "expires_in_hours": expiration_hours,
                "public_id": public_id
            }
            
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {public_id}: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate signed URL: {str(e)}"
            )

# Global instance
cloudinary_upload_service = CloudinaryUploadService()
