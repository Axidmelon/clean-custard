# In backend/api/v1/endpoints/auth.py
import os
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from db.dependencies import get_db
from schemas.user import UserCreate, User as UserSchema
from services import user_services as user_service 
from core.email_service import send_verification_email, send_password_reset_email
from core.jwt_handler import create_access_token, verify_token
from core.rate_limiter import check_rate_limit
import uuid
from datetime import datetime, timedelta, timezone

class LoginRequest(BaseModel):
    email: str
    password: str

class PasswordResetRequest(BaseModel):
    token: uuid.UUID
    new_password: str

class ProfileUpdateRequest(BaseModel):
    first_name: str = None
    last_name: str = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserSchema

router = APIRouter()

@router.options("/auth/signup")
def signup_options():
    """Handle preflight OPTIONS request for signup endpoint"""
    return {"message": "OK"}

@router.options("/auth/login")
def login_options():
    """Handle preflight OPTIONS request for login endpoint"""
    return {"message": "OK"}

@router.options("/auth/reset-password")
def reset_password_options():
    """Handle preflight OPTIONS request for reset-password endpoint"""
    return {"message": "OK"}

@router.post("/auth/signup", response_model=UserSchema)
def signup_user(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    # Apply rate limiting
    check_rate_limit(request, "auth")
    
    try:
        # Check if user already exists
        db_user = user_service.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    except Exception as e:
        print(f"Error in signup_user: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    # Get or create default organization
    default_org = user_service.get_or_create_default_organization(db)
    
    # Update user with default organization ID
    user.organization_id = default_org.id

    # Create the user but DO NOT verify them yet
    new_user = user_service.create_user(db=db, user=user)

    # Generate a new verification token upon creation
    new_user.verification_token = uuid.uuid4()
    db.commit()
    db.refresh(new_user)
    
    # Construct the verification link
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
    verification_link = f"{frontend_url}/verify-email?token={new_user.verification_token}"
    
    # Send the verification email
    send_verification_email(
        to_email=new_user.email,
        verification_link=verification_link
    )
    
    return new_user

@router.post("/auth/login", response_model=TokenResponse)
def login_user(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    """
    # Apply rate limiting
    check_rate_limit(request, "auth")
    
    # Find user by email
    user = user_service.get_user_by_email(db, email=login_data.email)
    
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Invalid email or password"
        )
    
    # Verify password
    if not user_service.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401, 
            detail="Invalid email or password"
        )
    
    # Check if user is verified
    if not user.is_verified:
        raise HTTPException(
            status_code=403, 
            detail="Please verify your email before logging in"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

# Still in backend/api/v1/endpoints/auth.py

@router.get("/auth/verify", response_model=TokenResponse)
def verify_user_email(token: uuid.UUID, db: Session = Depends(get_db)):
    # Find the user by the verification token
    user = user_service.get_user_by_verification_token(db, token=token)
    
    if not user:
        raise HTTPException(
            status_code=404, 
            detail="Invalid or expired verification token."
        )
        
    # Mark the user as verified and clear the token
    user.is_verified = True
    user.verification_token = None # Invalidate the token after use
    db.commit()
    db.refresh(user)
    
    # Create access token for automatic login
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.post("/auth/forgot-password")
def forgot_password(email: str = Body(..., embed=True), db: Session = Depends(get_db)):
    user = user_service.get_user_by_email(db, email=email)

    # SECURITY NOTE: We do not throw a 404 error if the user is not found.
    # This prevents attackers from using this endpoint to discover registered emails.
    if user:
        # Generate token and set expiry (e.g., 1 hour from now)
        token = uuid.uuid4()
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        
        user.password_reset_token = token
        user.password_reset_expires_at = expires
        db.commit()
        
        # Send the email
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
        reset_link = f"{frontend_url}/auth/reset-password?token={token}"
        send_password_reset_email(to_email=user.email, reset_link=reset_link)

    return {"message": "If an account with that email exists, a password reset link has been sent."}

@router.post("/auth/reset-password")
def reset_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    user = user_service.get_user_by_reset_token(db, token=request.token)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid token.")
    
    # Check if the token has expired
    if user.password_reset_expires_at is None or user.password_reset_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token has expired.")
        
    # Hash the new password and update the user
    hashed_password = user_service.get_password_hash(request.new_password)
    user.hashed_password = hashed_password
    
    # Invalidate the token after use
    user.password_reset_token = None
    user.password_reset_expires_at = None
    
    db.commit()
    
    return {"message": "Password has been reset successfully."}

@router.put("/auth/update-profile", response_model=UserSchema)
def update_user_profile(
    profile_data: ProfileUpdateRequest, 
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(verify_token)
):
    """
    Update user profile information.
    """
    # Get the user from database
    user = user_service.get_user_by_id(db, user_id=current_user.id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update the fields that were provided
    if profile_data.first_name is not None:
        user.first_name = profile_data.first_name
    if profile_data.last_name is not None:
        user.last_name = profile_data.last_name
    
    # Update the updated_at timestamp
    user.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(user)
    
    return user