# db/dependencies.py

import logging
from sqlalchemy.exc import OperationalError, DisconnectionError, InvalidRequestError
from sqlalchemy.orm.exc import StaleDataError
from db.database import SessionLocal, engine
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def get_db():
    """
    FastAPI dependency that provides a database session.
    It ensures the database session is always closed after the request is finished.
    Includes comprehensive error handling for connection pool exhaustion and timeouts.
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
        
        # Check if it's a timeout error and provide more specific error message
        error_str = str(e).lower()
        if "timeout" in error_str or "expired" in error_str:
            logger.error("Database connection timeout - this may indicate Supabase connection pool exhaustion")
            raise HTTPException(
                status_code=503, 
                detail="Database connection timeout. Please try again in a moment."
            )
        elif "connection" in error_str and "failed" in error_str:
            logger.error("Database connection failed - this may indicate network issues")
            raise HTTPException(
                status_code=503, 
                detail="Database connection failed. Please try again in a moment."
            )
        else:
            raise HTTPException(
                status_code=503, 
                detail="Database connection error. Please try again in a moment."
            )
    except (InvalidRequestError, StaleDataError) as e:
        logger.error(f"Database session error: {e}")
        # Rollback any pending transaction
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {rollback_error}")
        raise HTTPException(
            status_code=500, 
            detail="Database session error. Please try again."
        )
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        # Rollback any pending transaction
        try:
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Error during rollback: {rollback_error}")
        raise HTTPException(
            status_code=500, 
            detail="Internal database error. Please try again."
        )
    finally:
        try:
            db.close()
        except Exception as close_error:
            logger.error(f"Error closing database session: {close_error}")
