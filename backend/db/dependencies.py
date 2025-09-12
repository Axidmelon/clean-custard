# db/dependencies.py

import logging
from sqlalchemy.exc import OperationalError, DisconnectionError
from db.database import SessionLocal

logger = logging.getLogger(__name__)


def get_db():
    """
    FastAPI dependency that provides a database session.
    It ensures the database session is always closed after the request is finished.
    Includes error handling for connection pool exhaustion.
    """
    db = SessionLocal()
    try:
        yield db
    except (OperationalError, DisconnectionError) as e:
        logger.error(f"Database connection error: {e}")
        # Rollback any pending transaction
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {rollback_error}")
        # Re-raise the original error
        raise
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        # Rollback any pending transaction
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {rollback_error}")
        raise
    finally:
        try:
            db.close()
        except Exception as close_error:
            logger.error(f"Error closing database session: {close_error}")
