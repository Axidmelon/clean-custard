# in backend/services/user_service.py

from sqlalchemy.orm import Session
import uuid
from db.models import User, Organization  # Assuming your User model is in db/models.py
from schemas.user import UserCreate  # Assuming your Pydantic schema for user creation is here

# We should also put our password hashing logic here to keep it centralized
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """
    Verifies a plain password against its hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db: Session, user_id: int):
    """
    Retrieves a single user by their ID.
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    """
    Retrieves a single user by their email address.
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: uuid.UUID):
    """
    Retrieves a single user by their ID.
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_verification_token(db: Session, token: uuid.UUID):
    """
    Retrieves a single user by their verification token.
    (This is the function we need for Phase B, Step 3)
    """
    return db.query(User).filter(User.verification_token == token).first()


def create_user(db: Session, user: UserCreate):
    """
    Creates a new user in the database.
    """
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        organization_id=user.organization_id,
        is_verified=False,  # Explicitly set as unverified
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_reset_token(db: Session, token: uuid.UUID):
    """
    Retrieves a single user by their password reset token.
    """
    return db.query(User).filter(User.password_reset_token == token).first()


def create_user_organization(db: Session, user_email: str):
    """
    Creates a unique organization for a new user.
    Each user gets their own organization for true multi-tenancy.
    
    Args:
        db: Database session
        user_email: Email address of the user
        
    Returns:
        Organization: The newly created organization with unique ID
        
    Note:
        The organization ID is automatically generated as a UUID by the database
        and is guaranteed to be unique due to the primary key constraint.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Create organization name based on user email
    # Extract domain or use email prefix for organization name
    if '@' in user_email:
        email_prefix = user_email.split('@')[0]
        domain = user_email.split('@')[1]
        org_name = f"{email_prefix}'s Organization"
    else:
        org_name = f"{user_email}'s Organization"
    
    logger.info(f"Creating unique organization for user: {user_email}")
    
    # Create a new unique organization for this user
    # The ID will be automatically generated as a UUID by the database
    user_org = Organization(name=org_name)
    db.add(user_org)
    db.commit()
    db.refresh(user_org)
    
    logger.info(f"Created organization '{org_name}' with ID: {user_org.id} for user: {user_email}")
    
    return user_org
