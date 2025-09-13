# db/database.py
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Load environment variables from the .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Read the database URL from the environment variable
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Database connection pool settings - optimized for Supabase production
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "8"))  # Reduced for Supabase Nano tier stability
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "3"))  # Conservative overflow for Nano tier
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "60"))  # Increased timeout for better reliability
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour recycle for stability
DB_POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"

# Create engine with connection pooling
connect_args = {}
if "postgresql" in SQLALCHEMY_DATABASE_URL:
    connect_args.update({
        "sslmode": "require",
        "options": "-c default_transaction_isolation=read_committed",
        "application_name": "custard-backend",
        "connect_timeout": 60,  # Increased to 60 seconds for better reliability
    })

# Set isolation level based on database type
isolation_level = "READ_COMMITTED"
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    isolation_level = "SERIALIZABLE"  # SQLite doesn't support READ_COMMITTED

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=DB_POOL_RECYCLE,
    pool_pre_ping=DB_POOL_PRE_PING,  # Verify connections before use
    echo=os.getenv("DEBUG", "false").lower() == "true",
    connect_args=connect_args,
    # Production optimizations
    pool_reset_on_return="commit",
    isolation_level=isolation_level,
)

# A SessionLocal class is a factory for creating new database sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# We get the Base class from here now, which our models will inherit.
Base = declarative_base()


# Add connection event listeners for monitoring
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set database pragmas for better performance and security."""
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
    elif "postgresql" in SQLALCHEMY_DATABASE_URL:
        # PostgreSQL specific settings
        cursor = dbapi_connection.cursor()
        cursor.execute("SET timezone TO 'UTC'")
        cursor.close()


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log database connection checkout."""
    # Removed debug logging to reduce Railway log rate limit issues
    pass


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Log database connection checkin."""
    # Removed debug logging to reduce Railway log rate limit issues
    pass
