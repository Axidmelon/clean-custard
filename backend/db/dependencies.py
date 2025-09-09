# db/dependencies.py

from db.database import SessionLocal


def get_db():
    """
    FastAPI dependency that provides a database session.
    It ensures the database session is always closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
