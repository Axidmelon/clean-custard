# schemas/user.py
import uuid
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# --- Schema for creating a user (INPUT) ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str = ""
    last_name: str = ""
    organization_id: uuid.UUID


# --- Schema for user login (INPUT) ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# --- Base schema for a user (shared properties) ---
class UserBase(BaseModel):
    email: str
    is_verified: bool
    organization_id: uuid.UUID


# --- Main schema for a user (OUTPUT) ---
# This is the full model that we will send back to the user.
# It includes all the fields from the database.
class User(UserBase):
    id: uuid.UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        # This tells Pydantic to read the data even if it's not a dict,
        # but a SQLAlchemy model object.
        from_attributes = True


# --- Schema for user response (without sensitive data) ---
class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_verified: bool
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
