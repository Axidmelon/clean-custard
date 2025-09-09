# in backend/services/user_service.py

from sqlalchemy.orm import Session
import uuid
from db.models import User  # Assuming your User model is in db/models.py
from schemas.user import UserCreate # Assuming your Pydantic schema for user creation is here

# We should also put our password hashing logic here to keep it centralized
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

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
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_reset_token(db: Session, token: uuid.UUID):
    """
    Retrieves a single user by their password reset token.
    """
    return db.query(User).filter(User.password_reset_token == token).first()
