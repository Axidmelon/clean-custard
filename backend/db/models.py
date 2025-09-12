import uuid
from sqlalchemy import Column, String, ForeignKey, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func  # Import the func library for SQL functions like NOW()

from .database import Base


class Organization(Base):
    """Represents a customer's organization or team."""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)

    # --- Production-Ready Improvement: Timestamps ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    users = relationship("User", back_populates="organization")
    connections = relationship("Connection", back_populates="organization")


class User(Base):
    """Represents an individual user within an organization."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    # --- Fields for Phase B & C (Authentication Flow) ---
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(
        UUID(as_uuid=True), unique=True, nullable=True
    )  # Nullable because it will be cleared
    password_reset_token = Column(UUID(as_uuid=True), unique=True, nullable=True)
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)

    # --- Production-Ready Improvement: Timestamps ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", back_populates="users")


class Connection(Base):
    """Represents a data source connection for an organization."""

    __tablename__ = "connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    db_type = Column(String, default="POSTGRESQL")
    status = Column(String, default="PENDING")
    hashed_api_key = Column(String, nullable=True)
    db_schema_cache = Column(JSON, nullable=True)
    agent_id = Column(
        String, unique=True, index=True, nullable=True
    )  # Unique agent identifier for WebSocket routing

    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)

    # --- Production-Ready Improvement: Timestamps ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization", back_populates="connections")


class UploadedFile(Base):
    """Represents an uploaded file for an organization."""

    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String, nullable=False)
    file_size = Column(String, nullable=False)  # Store as string to handle large numbers
    file_path = Column(String, nullable=False)  # Cloudinary public_id or file path
    file_url = Column(String, nullable=False)  # Public URL to access the file
    content_type = Column(String, nullable=True)
    cloudinary_public_id = Column(String, nullable=True)  # Cloudinary specific ID
    
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # --- Production-Ready Improvement: Timestamps ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organization = relationship("Organization")
    user = relationship("User")
