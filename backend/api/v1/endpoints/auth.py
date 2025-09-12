# In backend/api/v1/endpoints/auth.py
import os
import logging
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from db.dependencies import get_db
from schemas.user import UserCreate, User as UserSchema
from services import user_services as user_service
from core.email_service import send_verification_email, send_password_reset_email
from core.jwt_handler import create_access_token, get_current_user
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


class SessionValidationRequest(BaseModel):
    session_id: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserSchema
    session_id: str = None  # Optional session ID for persistent sessions


router = APIRouter()


@router.options("/auth/signup")
def signup_options():
    """Handle preflight OPTIONS request for signup endpoint"""
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
            "Access-Control-Max-Age": "86400"
        }
    )


@router.options("/auth/login")
def login_options():
    """Handle preflight OPTIONS request for login endpoint"""
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
            "Access-Control-Max-Age": "86400"
        }
    )


@router.options("/auth/reset-password")
def reset_password_options():
    """Handle preflight OPTIONS request for reset-password endpoint"""
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
            "Access-Control-Max-Age": "86400"
        }
    )


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

    # Create a unique organization for this user
    logger = logging.getLogger(__name__)
    logger.info(f"Creating unique organization for new user: {user.email}")
    
    # Debug: Check if create_user_organization function exists
    if not hasattr(user_service, 'create_user_organization'):
        logger.error("create_user_organization function not found in user_service!")
        raise HTTPException(status_code=500, detail="Organization creation function not available")
    
    user_org = user_service.create_user_organization(db, user.email)
    logger.info(f"Created organization: {user_org.name} with ID: {user_org.id}")

    # Update user with their unique organization ID
    user.organization_id = user_org.id
    logger.info(f"Assigned organization ID {user_org.id} to user: {user.email}")

    # Create the user but DO NOT verify them yet
    new_user = user_service.create_user(db=db, user=user)

    # Generate a new verification token upon creation
    verification_token = uuid.uuid4()
    new_user.verification_token = verification_token
    db.commit()
    db.refresh(new_user)
    
    # Debug logging
    logger.info(f"Generated verification token for user {new_user.email}: {verification_token}")
    logger.info(f"Token stored in DB: {new_user.verification_token}")

    # Construct the verification link
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
    verification_link = f"{frontend_url}/verify-email?token={new_user.verification_token}"

    # Send the verification email
    send_verification_email(to_email=new_user.email, verification_link=verification_link)

    return new_user


@router.post("/auth/login", response_model=TokenResponse)
def login_user(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token with Redis caching and persistent sessions.
    """
    # Apply rate limiting
    check_rate_limit(request, "auth")

    # Find user by email
    user = user_service.get_user_by_email(db, email=login_data.email)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check if user is verified first (before password verification for better UX)
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before logging in")

    # Verify password
    if not user_service.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    # Cache user data in Redis for future requests
    from core.redis_service import redis_service
    from core.jwt_handler import create_persistent_session
    
    user_data = {
        'id': str(user.id),
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_verified': user.is_verified,
        'organization_id': str(user.organization_id),
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'updated_at': user.updated_at.isoformat() if user.updated_at else None
    }
    
    # Cache user data with 1 hour TTL
    redis_service.cache_user_data(str(user.id), user_data, ttl=3600)
    
    # Create persistent session for seamless subsequent logins
    session_id = create_persistent_session(str(user.id), user_data)
    
    logger = logging.getLogger(__name__)
    logger.info(f"User {user.email} logged in successfully. Session: {session_id}")
    
    # Add session_id to response for frontend to store
    response_data = TokenResponse(access_token=access_token, token_type="bearer", user=user)
    response_data.session_id = session_id  # Add session_id to response
    
    return response_data


# Still in backend/api/v1/endpoints/auth.py


@router.get("/auth/verify", response_model=TokenResponse)
def verify_user_email(token: uuid.UUID, db: Session = Depends(get_db)):
    # Find the user by the verification token
    user = user_service.get_user_by_verification_token(db, token=token)
    
    # Debug logging
    logger = logging.getLogger(__name__)
    logger.info(f"Verification attempt for token: {token}")
    logger.info(f"User found: {user is not None}")
    if user:
        logger.info(f"User email: {user.email}, is_verified: {user.is_verified}")

    if not user:
        raise HTTPException(status_code=404, detail="Invalid or expired verification token.")

    # Mark the user as verified and clear the token
    user.is_verified = True
    user.verification_token = None  # Invalidate the token after use
    db.commit()
    db.refresh(user)

    # Create access token for automatic login
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})

    return TokenResponse(access_token=access_token, token_type="bearer", user=user)


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
    if user.password_reset_expires_at is None or user.password_reset_expires_at < datetime.now(
        timezone.utc
    ):
        raise HTTPException(status_code=400, detail="Token has expired.")

    # Hash the new password and update the user
    hashed_password = user_service.get_password_hash(request.new_password)
    user.hashed_password = hashed_password

    # Invalidate the token after use
    user.password_reset_token = None
    user.password_reset_expires_at = None

    db.commit()

    return {"message": "Password has been reset successfully."}


@router.post("/auth/logout")
def logout_user(
    request: Request,
    current_user: UserSchema = Depends(get_current_user())
):
    """
    Logout user and blacklist their JWT token.
    """
    from fastapi.security import HTTPBearer
    from core.jwt_handler import blacklist_token
    
    # Extract token from request
    oauth2_scheme = HTTPBearer()
    credentials = oauth2_scheme(request)
    token = credentials.credentials
    
    # Blacklist the token
    success = blacklist_token(token)
    
    if success:
        logger = logging.getLogger(__name__)
        logger.info(f"User {current_user.email} logged out successfully")
        return {"message": "Logged out successfully"}
    else:
        logger.warning(f"Failed to blacklist token for user {current_user.email}")
        return {"message": "Logged out (token blacklisting failed)"}


@router.post("/auth/validate-session", response_model=TokenResponse)
def validate_session(session_data: SessionValidationRequest):
    """
    Validate a persistent session and return a new JWT token.
    This enables seamless login for returning users.
    """
    from core.jwt_handler import validate_persistent_session, create_access_token
    
    # Validate the session
    session_info = validate_persistent_session(session_data.session_id)
    
    if not session_info:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    user_data = session_info.get('user_data')
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid session data")
    
    # Create new access token
    access_token = create_access_token(data={
        "sub": user_data['id'], 
        "email": user_data['email']
    })
    
    # Convert user_data back to User object for response
    from db.models import User
    user = User()
    for key, value in user_data.items():
        if key != '_cached_at':  # Skip cache metadata
            setattr(user, key, value)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Validated session for user {user_data['email']}")
    
    return TokenResponse(
        access_token=access_token, 
        token_type="bearer", 
        user=user,
        session_id=session_data.session_id
    )


@router.post("/auth/logout-all-devices")
def logout_all_devices(
    current_user: UserSchema = Depends(get_current_user())
):
    """
    Logout user from all devices by revoking all sessions.
    """
    from core.jwt_handler import revoke_user_sessions
    
    success = revoke_user_sessions(str(current_user.id))
    
    if success:
        logger = logging.getLogger(__name__)
        logger.info(f"Revoked all sessions for user {current_user.email}")
        return {"message": "Logged out from all devices successfully"}
    else:
        logger.warning(f"Failed to revoke sessions for user {current_user.email}")
        return {"message": "Logout from all devices failed"}


@router.put("/auth/update-profile", response_model=UserSchema)
def update_user_profile(
    profile_data: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(get_current_user()),
):
    """
    Update user profile information and invalidate cache.
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
    
    # Invalidate cached user data since profile was updated
    from core.redis_service import redis_service
    redis_service.invalidate_user_cache(str(user.id))
    
    logger = logging.getLogger(__name__)
    logger.info(f"Updated profile for user {user.email} and invalidated cache")

    return user
