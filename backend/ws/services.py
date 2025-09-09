# ws/services.py
from sqlalchemy.orm import Session
from db.models import Connection  # Import your Connection model
import uuid


class ConnectionService:
    def __init__(self, db: Session):
        """
        Initializes the service with a database session.
        """
        self.db = db

    def store_schema(self, connection_id: str, schema_data: str):
        """
        Finds a connection by its ID and stores the provided schema.
        """
        print(f"Attempting to store schema for connection_id: {connection_id}")

        # Find the connection record in the database
        connection_record = (
            self.db.query(Connection).filter(Connection.id == uuid.UUID(connection_id)).first()
        )

        if not connection_record:
            print(f"Error: Connection with id '{connection_id}' not found.")
            return

        # Update the schema cache column
        connection_record.db_schema_cache = {"schema": schema_data}

        # Commit the change to the database
        self.db.commit()

        print(f"Successfully stored schema for connection '{connection_id}'.")
